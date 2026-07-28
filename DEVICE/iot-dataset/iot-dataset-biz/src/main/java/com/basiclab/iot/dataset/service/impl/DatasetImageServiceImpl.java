package com.basiclab.iot.dataset.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.text.UUID;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.dataset.dal.dataobject.DatasetDO;
import com.basiclab.iot.dataset.dal.dataobject.DatasetImageDO;
import com.basiclab.iot.dataset.dal.dataobject.DatasetTagDO;
import com.basiclab.iot.dataset.dal.pgsql.DatasetImageMapper;
import com.basiclab.iot.dataset.dal.pgsql.DatasetMapper;
import com.basiclab.iot.common.enums.CommonStatusEnum;
import com.basiclab.iot.common.exception.ServiceException;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetImageImportItem;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetImagePageReqVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetImageSaveReqVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetImageUploadRespVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetSyncCheckRespVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetTagPageReqVO;
import com.basiclab.iot.dataset.service.DatasetImageService;
import com.basiclab.iot.dataset.service.DatasetTagService;
import com.basiclab.iot.dataset.service.annotation.DatasetAnnotationParseUtil;
import com.basiclab.iot.dataset.service.annotation.YoloLabelContentBuilder;
import com.basiclab.iot.dataset.service.ImportCancelChecker;
import com.basiclab.iot.dataset.service.DatasetSyncTaskManager;
import com.basiclab.iot.file.RemoteFileService;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.minio.*;
import io.minio.errors.ErrorResponseException;
import io.minio.http.Method;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.env.Environment;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.stereotype.Service;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.multipart.MultipartFile;
import org.yaml.snakeyaml.Yaml;

import javax.annotation.Resource;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.math.BigDecimal;
import java.net.URI;
import java.net.URISyntaxException;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.*;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executor;
import java.util.concurrent.TimeUnit;
import java.util.function.IntConsumer;
import java.util.stream.Collectors;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;
import java.util.zip.ZipOutputStream;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.dataset.enums.ErrorCodeConstants.*;

/**
 * 图片数据集 Service 实现类
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Service
@Validated
public class DatasetImageServiceImpl implements DatasetImageService {

    private final static Logger logger = LoggerFactory.getLogger(DatasetImageServiceImpl.class);
    private static final int IMPORT_ZIP_BATCH_SIZE = 100;
    private static final long IMPORT_ZIP_BATCH_MAX_BYTES = 64L * 1024 * 1024;
    private static final long IMPORT_ZIP_ENTRY_MAX_BYTES = 50L * 1024 * 1024;
    private static final int MINIO_UPLOAD_PARALLEL = 12;
    private static final int MAX_BATCH_DELETE_SIZE = 100;
    private static final int SYNC_EXPORT_BATCH_SIZE = 100;

    @Resource
    @Qualifier("uploadExecutor")
    private Executor uploadExecutor;

    @Resource
    private DatasetSyncTaskManager datasetSyncTaskManager;

    @Resource
    private DatasetImageMapper datasetImageMapper;

    @Resource
    private DatasetMapper datasetMapper;

    @Resource
    private DatasetTagService datasetTagService;

    @Resource
    private RemoteFileService remoteFileService;

    @Resource
    private MinioClient minioClient;

    @Resource
    private Environment environment;

    @Value("${minio.bucket}")
    private String minioBucket;

    private static final String minioDatasetsBucket = "datasets";

    @Override
    public Long createDatasetImage(DatasetImageSaveReqVO createReqVO) {
        DatasetImageDO image = BeanUtils.toBean(createReqVO, DatasetImageDO.class);
        insertDatasetImageWithSequenceRecovery(image);
        return image.getId();
    }

    /**
     * 插入图片记录；若 PostgreSQL 序列落后于已有主键则自动同步后重试一次。
     */
    private void insertDatasetImageWithSequenceRecovery(DatasetImageDO image) {
        try {
            datasetImageMapper.insert(image);
        } catch (DuplicateKeyException ex) {
            logger.warn("dataset_image 主键冲突，尝试同步序列后重试: id={}", image.getId());
            datasetImageMapper.syncIdSequence();
            image.setId(null);
            datasetImageMapper.insert(image);
        }
    }

    private void insertBatchWithSequenceRecovery(List<DatasetImageDO> images) {
        if (images == null || images.isEmpty()) {
            return;
        }
        try {
            datasetImageMapper.insertBatch(images, 500);
        } catch (DuplicateKeyException ex) {
            logger.warn("dataset_image 批量主键冲突，尝试同步序列后重试");
            datasetImageMapper.syncIdSequence();
            for (DatasetImageDO image : images) {
                image.setId(null);
            }
            datasetImageMapper.insertBatch(images, 500);
        }
    }

    @Override
    public void updateDatasetImage(DatasetImageSaveReqVO updateReqVO) {
        // 校验存在
        validateDatasetImageExists(updateReqVO.getId());
        // 更新
        DatasetImageDO updateObj = BeanUtils.toBean(updateReqVO, DatasetImageDO.class);
        datasetImageMapper.updateById(updateObj);
    }

    @Override
    public void deleteDatasetImage(Long id) {
        // 校验存在
        validateDatasetImageExists(id);
        // 删除MinIO中的文件
        deleteMinioFiles(Collections.singletonList(id));
        // 删除
        datasetImageMapper.deleteById(id);
    }

    @Override
    public void deleteDatasetImages(List<Long> ids) {
        if (ids == null || ids.isEmpty()) {
            return;
        }
        List<Long> uniqueIds = new ArrayList<>(new LinkedHashSet<>(ids));
        if (uniqueIds.size() > MAX_BATCH_DELETE_SIZE) {
            throw exception(DATASET_IMAGE_BATCH_DELETE_LIMIT_EXCEEDED);
        }
        // 删除MinIO中的文件
        deleteMinioFiles(uniqueIds);
        // 批量删除数据库记录
        datasetImageMapper.deleteBatchIds(uniqueIds);
    }

    private void deleteMinioFiles(List<Long> ids) {
        List<DatasetImageDO> images = datasetImageMapper.selectBatchIds(ids);
        for (DatasetImageDO image : images) {
            try {
                String objectPath = parseObjectNameFromPath(image.getPath());
                minioClient.removeObject(
                        RemoveObjectArgs.builder()
                                .bucket(minioBucket)
                                .object(objectPath)
                                .build()
                );
            } catch (Exception e) {
                logger.error("删除MinIO文件失败: {}", e.getMessage());
            }
        }
    }

    private void validateDatasetImageExists(Long id) {
        if (datasetImageMapper.selectById(id) == null) {
            throw exception(DATASET_IMAGE_NOT_EXISTS);
        }
    }

    @Override
    public DatasetImageDO getDatasetImage(Long id) {
        return datasetImageMapper.selectById(id);
    }

    @Override
    public PageResult<DatasetImageDO> getDatasetImagePage(DatasetImagePageReqVO pageReqVO) {
        return datasetImageMapper.selectPage(pageReqVO);
    }

    @Override
    public void splitDataset(Long datasetId, BigDecimal trainRatio,
                             BigDecimal valRatio, BigDecimal testRatio) {
        // 1. 验证比例总和为100%
        if (trainRatio.add(valRatio).add(testRatio).compareTo(BigDecimal.ONE) != 0) {
            throw exception(TOTAL_DATASET_PARTITION_MUST_100_PERCENT);
        }

        // 2. 获取数据集所有图片ID（随机排序）
        List<Long> imageIds = datasetImageMapper.selectImageIdsByDatasetId(datasetId);

        // 3. 计算各集合样本数
        int total = imageIds.size();
        int trainCount = trainRatio.multiply(BigDecimal.valueOf(total)).intValue();
        int valCount = valRatio.multiply(BigDecimal.valueOf(total)).intValue();
        int testCount = total - trainCount - valCount;

        // 4. 划分数据集
        List<Long> trainIds = imageIds.subList(0, trainCount);
        List<Long> valIds = imageIds.subList(trainCount, trainCount + valCount);
        List<Long> testIds = imageIds.subList(trainCount + valCount, total);

        // 5. 批量更新用途字段
        updateImageUsage(trainIds, 1, 0, 0); // 训练集[3](@ref)
        updateImageUsage(valIds, 0, 1, 0);   // 验证集
        updateImageUsage(testIds, 0, 0, 1);  // 测试集[5](@ref)
    }

    @Override
    public void resetUsageByDatasetId(Long datasetId) {
        // 重置所有样本的用途字段为0
        datasetImageMapper.resetUsageByDatasetId(datasetId);
    }

    @Override
    public DatasetSyncCheckRespVO checkSyncCondition(Long datasetId) {
        DatasetDO dataset = datasetMapper.selectById(datasetId);
        if (dataset == null) {
            throw exception(DATASET_NOT_EXISTS);
        }
        long totalImages = datasetImageMapper.selectCount(new LambdaQueryWrapper<DatasetImageDO>()
                .eq(DatasetImageDO::getDatasetId, datasetId));

        long unallocatedCount = datasetImageMapper.selectCount(new LambdaQueryWrapper<DatasetImageDO>()
                .eq(DatasetImageDO::getDatasetId, datasetId)
                .eq(DatasetImageDO::getIsTrain, 0)
                .eq(DatasetImageDO::getIsValidation, 0)
                .eq(DatasetImageDO::getIsTest, 0));

        long unannotatedCount = datasetImageMapper.selectCount(new LambdaQueryWrapper<DatasetImageDO>()
                .eq(DatasetImageDO::getDatasetId, datasetId)
                .eq(DatasetImageDO::getCompleted, 0));

        boolean usageAllocated = totalImages > 0 && unallocatedCount == 0;
        boolean annotationCompleted = totalImages > 0 && unannotatedCount == 0;
        boolean syncReady = usageAllocated && annotationCompleted;
        boolean syncedToMinio = CommonStatusEnum.YES.getStatus().equals(dataset.getIsSyncMinio())
                || (dataset.getZipUrl() != null && !dataset.getZipUrl().isBlank());
        DatasetSyncTaskManager.TaskSnapshot snapshot = datasetSyncTaskManager.getSnapshot(datasetId);
        String syncStatus = syncedToMinio
                ? DatasetSyncTaskManager.SyncStatus.SUCCEEDED.name()
                : snapshot == null ? "IDLE" : snapshot.status().name();
        String syncStage = syncedToMinio
                ? DatasetSyncTaskManager.SyncStage.COMPLETED.name()
                : snapshot == null ? null : snapshot.stage().name();
        int syncProgress = syncedToMinio ? 100 : snapshot == null ? 0 : snapshot.progress();
        int processedImages = syncedToMinio
                ? (int) totalImages
                : snapshot == null ? 0 : snapshot.processedImages();

        return DatasetSyncCheckRespVO.builder()
                .usageAllocated(usageAllocated)
                .annotationCompleted(annotationCompleted)
                .syncReady(syncReady)
                .syncing(DatasetSyncTaskManager.SyncStatus.QUEUED.name().equals(syncStatus)
                        || DatasetSyncTaskManager.SyncStatus.RUNNING.name().equals(syncStatus))
                .syncedToMinio(syncedToMinio)
                .syncError(snapshot == null ? null : snapshot.error())
                .syncStatus(syncStatus)
                .syncStage(syncStage)
                .syncProgress(syncProgress)
                .processedImages(processedImages)
                .syncSubmittedAt(snapshot == null ? null : snapshot.submittedAt())
                .syncStartedAt(snapshot == null ? null : snapshot.startedAt())
                .syncFinishedAt(snapshot == null ? null : snapshot.finishedAt())
                .totalImages((int) totalImages)
                .unallocatedCount((int) unallocatedCount)
                .unannotatedCount((int) unannotatedCount)
                .build();
    }

    @Override
    public String syncToMinio(Long datasetId) {
        DatasetSyncCheckRespVO check = checkSyncCondition(datasetId);
        if (Boolean.TRUE.equals(check.getSyncedToMinio())) {
            return "already-synced";
        }
        validateSyncCondition(check);
        if (!datasetSyncTaskManager.submit(datasetId, check.getTotalImages(), () -> doSyncToMinio(datasetId))) {
            throw exception(DATASET_SYNC_IN_PROGRESS);
        }
        return "accepted";
    }

    private String doSyncToMinio(Long datasetId) {
        DatasetSyncCheckRespVO check = checkSyncCondition(datasetId);
        if (Boolean.TRUE.equals(check.getSyncedToMinio())) {
            return "already-synced";
        }
        validateSyncCondition(check);
        datasetSyncTaskManager.updateProgress(
                datasetId, DatasetSyncTaskManager.SyncStage.PREPARING, 3, 0);
        Path tempDir = createTempDirectoryStructure(datasetId);
        Path zipPath = null;
        try {
            int skippedCount = 0;
            int processedCount = 0;
            int totalImages = check.getTotalImages() == null ? 0 : check.getTotalImages();
            long lastImageId = 0L;
            while (true) {
                List<DatasetImageDO> images = datasetImageMapper.selectSyncBatch(
                        datasetId, lastImageId, SYNC_EXPORT_BATCH_SIZE);
                if (images.isEmpty()) {
                    break;
                }
                for (DatasetImageDO image : images) {
                    String usageType = getUsageType(image);
                    String imageName = image.getName();
                    Path imagePath = tempDir.resolve("images/" + usageType + "/" + imageName);
                    String labelFileName = stripImageExtension(imageName) + ".txt";
                    Path labelPath = tempDir.resolve("labels/" + usageType + "/" + labelFileName);
                    try {
                        downloadImageToTemp(image, imagePath);
                        createLabelFile(image, labelPath, datasetId);
                    } catch (Exception e) {
                        skippedCount++;
                        logger.warn("跳过文件 {}: {}", image.getName(), e.getMessage());
                    }
                    processedCount++;
                }
                int exportProgress = totalImages == 0
                        ? 70
                        : 5 + (int) Math.round((processedCount * 65.0) / totalImages);
                datasetSyncTaskManager.updateProgress(
                        datasetId, DatasetSyncTaskManager.SyncStage.EXPORTING,
                        Math.min(exportProgress, 70), processedCount);
                lastImageId = images.get(images.size() - 1).getId();
            }
            if (skippedCount > 0) {
                logger.warn("数据集 {} 打包完成，跳过 {} 个缺失文件", datasetId, skippedCount);
            }
            generateDataYaml(datasetId, tempDir);
            datasetSyncTaskManager.updateProgress(
                    datasetId, DatasetSyncTaskManager.SyncStage.PACKAGING, 75, processedCount);
            zipPath = compressDirectory(tempDir, datasetId);
            datasetSyncTaskManager.updateProgress(
                    datasetId, DatasetSyncTaskManager.SyncStage.UPLOADING, 88, processedCount);
            String zipUrl = uploadZipToMinio(zipPath, datasetId);
            datasetSyncTaskManager.updateProgress(
                    datasetId, DatasetSyncTaskManager.SyncStage.FINALIZING, 97, processedCount);
            DatasetDO updateDO = new DatasetDO();
            updateDO.setId(datasetId);
            updateDO.setZipUrl(zipUrl);
            updateDO.setIsSyncMinio(CommonStatusEnum.YES.getStatus());
            datasetMapper.updateById(updateDO);
            return zipUrl;
        } finally {
            cleanupTempFiles(tempDir, zipPath);
        }
    }

    private void validateSyncCondition(DatasetSyncCheckRespVO check) {
        if (check.getTotalImages() == null || check.getTotalImages() == 0) {
            throw exception(DATASET_NO_IMAGES);
        }
        if (!Boolean.TRUE.equals(check.getUsageAllocated())) {
            throw exception(DATASET_USAGE_NOT_ALLOCATED);
        }
        if (!Boolean.TRUE.equals(check.getAnnotationCompleted())) {
            throw exception(DATASET_ANNOTATION_INCOMPLETE);
        }
    }

    private Path createTempDirectoryStructure(Long datasetId) {
        try {
            Path tempDir = Files.createTempDirectory("dataset-" + datasetId);
            Files.createDirectories(tempDir.resolve("images/train"));
            Files.createDirectories(tempDir.resolve("images/val"));
            Files.createDirectories(tempDir.resolve("images/test"));
            Files.createDirectories(tempDir.resolve("labels/train"));
            Files.createDirectories(tempDir.resolve("labels/val"));
            Files.createDirectories(tempDir.resolve("labels/test"));
            return tempDir;
        } catch (IOException e) {
            throw new RuntimeException("创建临时目录失败", e);
        }
    }

    private void downloadImageToTemp(DatasetImageDO image, Path targetPath) {
        try {
            String sourceObject = parseObjectNameFromPath(image.getPath());
            try (InputStream in = minioClient.getObject(
                    GetObjectArgs.builder()
                            .bucket(minioBucket)
                            .object(sourceObject)
                            .build())) {
                Files.createDirectories(targetPath.getParent()); // 确保目录存在
                Files.copy(in, targetPath, StandardCopyOption.REPLACE_EXISTING);
            }
        } catch (ErrorResponseException e) {
            if ("NoSuchKey".equals(e.errorResponse().code())) {
                logger.warn("文件不存在，跳过下载: {}", image.getPath());
            } else {
                logger.error("MinIO访问异常: {}", image.getPath(), e);
            }
        } catch (Exception e) {
            logger.error("下载图片失败: {}", image.getPath(), e);
        }
    }

    private void createLabelFile(DatasetImageDO image, Path labelPath, Long datasetId) {
        try {
            Files.createDirectories(labelPath.getParent());
            String labelContent = generateLabelContent(image.getAnnotations(), datasetId);
            Files.write(labelPath, labelContent.getBytes(StandardCharsets.UTF_8),
                    StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING);
        } catch (Exception e) {
            logger.error("生成标签文件失败: {}", labelPath, e);
        }
    }

    private String stripImageExtension(String imageName) {
        int dot = imageName.lastIndexOf('.');
        return dot > 0 ? imageName.substring(0, dot) : imageName;
    }

    private String generateLabelContent(String annotationsJson, Long datasetId) {
        try {
            List<String> classNames = getClassNames(datasetId);
            Map<String, Integer> nameToIndex = new LinkedHashMap<>();
            for (int i = 0; i < classNames.size(); i++) {
                nameToIndex.put(classNames.get(i), i);
            }
            List<DatasetTagDO> tags = datasetTagService.listTagsByDatasetId(datasetId);
            Map<String, String> shortcutToName = YoloLabelContentBuilder.buildShortcutToName(tags);
            Map<String, String> nameToShortcut = YoloLabelContentBuilder.buildNameToShortcut(tags);
            return YoloLabelContentBuilder.build(
                    annotationsJson, nameToIndex, shortcutToName, nameToShortcut, null, null);
        } catch (Exception e) {
            throw new RuntimeException("生成标注文件内容失败", e);
        }
    }

    private void generateDataYaml(Long datasetId, Path tempDir) {
        try {
            List<String> classNames = getClassNames(datasetId);
            Map<String, Object> yamlData = new LinkedHashMap<>();
            yamlData.put("names", classNames);
            yamlData.put("nc", classNames.size());
            yamlData.put("train", "images/train");
            yamlData.put("val", "images/val");  // 注意此处保持为val
            yamlData.put("test", "images/test");
            Yaml yaml = new Yaml();
            String yamlContent = yaml.dump(yamlData);
            Files.write(tempDir.resolve("data.yaml"), yamlContent.getBytes(StandardCharsets.UTF_8));
        } catch (Exception e) {
            throw new RuntimeException("生成data.yaml失败", e);
        }
    }

    private List<String> getClassNames(Long datasetId) {
        DatasetTagPageReqVO reqVO = new DatasetTagPageReqVO();
        reqVO.setDatasetId(datasetId);
        PageResult<DatasetTagDO> result = datasetTagService.getDatasetTagPage(reqVO);

        return result.getList().stream()
                .map(DatasetTagDO::getName)
                .sorted().collect(Collectors.toList());
    }

    private Path compressDirectory(Path sourceDir, Long datasetId) {
        Path zipPath;
        try {
            zipPath = Files.createTempFile(sourceDir.getParent(), "dataset-" + datasetId + "-", ".zip");
        } catch (IOException e) {
            throw new RuntimeException("创建临时ZIP失败", e);
        }

        try (ZipOutputStream zos = new ZipOutputStream(Files.newOutputStream(zipPath))) {
            Files.walkFileTree(sourceDir, new SimpleFileVisitor<Path>() {
                @Override
                public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) throws IOException {
                    Path relativePath = sourceDir.relativize(file);
                    ZipEntry zipEntry = new ZipEntry(relativePath.toString().replace("\\", "/"));
                    zos.putNextEntry(zipEntry);
                    Files.copy(file, zos);
                    zos.closeEntry();
                    return FileVisitResult.CONTINUE;
                }
            });
            return zipPath;
        } catch (IOException e) {
            try {
                Files.deleteIfExists(zipPath);
            } catch (IOException cleanupError) {
                logger.warn("清理压缩失败的临时ZIP失败: {}", cleanupError.getMessage());
            }
            throw new RuntimeException("压缩目录失败", e);
        }
    }

    private void cleanupTempFiles(Path tempDir, Path zipPath) {
        try {
            if (tempDir != null && Files.exists(tempDir)) {
                Files.walkFileTree(tempDir, new SimpleFileVisitor<Path>() {
                    @Override
                    public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) throws IOException {
                        Files.delete(file);
                        return FileVisitResult.CONTINUE;
                    }

                    @Override
                    public FileVisitResult postVisitDirectory(Path dir, IOException exc) throws IOException {
                        Files.delete(dir);
                        return FileVisitResult.CONTINUE;
                    }
                });
            }
            if (zipPath != null) {
                Files.deleteIfExists(zipPath);
            }
        } catch (IOException e) {
            logger.error("清理临时文件失败: {}", e.getMessage());
        }
    }

    private String uploadZipToMinio(Path zipPath, Long datasetId) {
        try (InputStream is = Files.newInputStream(zipPath)) {
            String objectName = "dataset-" + datasetId + ".zip";
            minioClient.putObject(
                    PutObjectArgs.builder()
                            .bucket(minioDatasetsBucket)
                            .object(objectName)
                            .stream(is, Files.size(zipPath), -1)
                            .contentType("application/zip")
                            .build());

            return "/api/v1/buckets/" + minioDatasetsBucket + "/objects/download?prefix=" + objectName;
        } catch (Exception e) {
            throw new RuntimeException("上传ZIP到MinIO失败", e);
        }
    }

    private void createBucketIfNotExists(String bucketName) {
        try {
            boolean exists = minioClient.bucketExists(BucketExistsArgs.builder()
                    .bucket(bucketName)
                    .build());

            if (!exists) {
                // 1. 创建存储桶
                minioClient.makeBucket(MakeBucketArgs.builder()
                        .bucket(bucketName)
                        .build());

                // 2. 设置读写策略（核心修改）[6,7](@ref)
                String policyJson = "{" +
                        "\"Version\":\"2012-10-17\"," +
                        "\"Statement\":[{" +
                        "\"Effect\":\"Allow\"," +
                        "\"Principal\":\"*\"," +
                        "\"Action\":[" +
                        "\"s3:GetBucketLocation\"," +
                        "\"s3:ListBucket\"," +
                        "\"s3:ListBucketMultipartUploads\"," +
                        "\"s3:ListMultipartUploadParts\"," +
                        "\"s3:PutObject\"," +
                        "\"s3:GetObject\"," +
                        "\"s3:DeleteObject\"," +
                        "\"s3:AbortMultipartUpload\"" +
                        "]," +
                        "\"Resource\":[\"arn:aws:s3:::" + bucketName + "/*\"]" +
                        "}]" +
                        "}";

                minioClient.setBucketPolicy(
                        SetBucketPolicyArgs.builder()
                                .bucket(bucketName)
                                .config(policyJson)
                                .build()
                );
            }
        } catch (Exception e) {
            throw new RuntimeException("创建Minio存储桶失败", e);
        }
    }

    private String getUsageType(DatasetImageDO image) {
        if (image.getIsTrain() == 1) return "train";
        if (image.getIsValidation() == 1) return "val";
        if (image.getIsTest() == 1) return "test";
        throw new IllegalStateException("图片未划分用途");
    }

    private String parseObjectNameFromPath(String path) {
        try {
            URI uri = new URI(path);
            String query = uri.getQuery();
            if (query != null) {
                return Arrays.stream(query.split("&"))
                        .filter(param -> param.startsWith("prefix="))
                        .map(param -> param.substring(7))
                        .findFirst()
                        .orElseThrow(() -> new IllegalArgumentException("Invalid path format"));
            }
        } catch (URISyntaxException e) {
            logger.warn("路径解析异常: {}", path, e);
        }
        // 兼容旧逻辑
        int start = path.indexOf("prefix=") + 7;
        return start >= 7 ? path.substring(start) : path;
    }

    private List<Map<String, Object>> parseAnnotations(String annotationsJson) {
        try {
            ObjectMapper mapper = new ObjectMapper();
            return mapper.readValue(annotationsJson,
                    new TypeReference<List<Map<String, Object>>>() {
                    });
        } catch (Exception e) {
            throw new RuntimeException("解析标注信息失败", e);
        }
    }

    private void updateImageUsage(List<Long> imageIds,
                                  int isTrain, int isValidation, int isTest) {
        if (!imageIds.isEmpty()) {
            datasetImageMapper.batchUpdateUsage(
                    imageIds, isTrain, isValidation, isTest
            );
        }
    }

    @Override
    public DatasetImageUploadRespVO processUpload(MultipartFile file, Long datasetId, Boolean isZip) {
        try {
            if (Boolean.TRUE.equals(isZip)) {
                return processZipUpload(file, datasetId);
            }
            return processImageUpload(file, datasetId);
        } catch (ServiceException e) {
            throw e;
        } catch (Exception e) {
            logger.error("文件上传处理失败: {}", e.getMessage(), e);
            throw exception(FILE_UPLOAD_FAILED, e.getMessage());
        }
    }

    @Override
    public DatasetImageUploadRespVO processUploadFromPath(Path filePath, String originalFilename,
                                                          Long datasetId, Boolean isZip) {
        try {
            if (Boolean.TRUE.equals(isZip)) {
                return processZipUploadFromPath(filePath, datasetId);
            }
            return processImageUploadFromPath(filePath, originalFilename, datasetId);
        } catch (ServiceException e) {
            throw e;
        } catch (Exception e) {
            logger.error("文件处理失败: {}", e.getMessage(), e);
            throw exception(FILE_UPLOAD_FAILED, e.getMessage());
        }
    }

    /**
     * 上传文件
     */
    @Override
    public String uploadFile(MultipartFile file) throws Exception {
        return remoteFileService.upload(file).getData().getUrl();
    }

    /**
     * 处理压缩包上传并解压（批量入库，同名覆盖）
     */
    private DatasetImageUploadRespVO processZipUpload(MultipartFile file, Long datasetId)
            throws IOException {
        DatasetImageUploadRespVO total = new DatasetImageUploadRespVO();
        List<DatasetImageImportItem> batch = new ArrayList<>(IMPORT_ZIP_BATCH_SIZE);
        long batchBytes = 0;
        byte[] buffer = new byte[8192];

        try (ZipInputStream zis = openZipInputStream(file)) {
            ZipEntry zipEntry;
            while ((zipEntry = zis.getNextEntry()) != null) {
                if (zipEntry.isDirectory()) {
                    continue;
                }
                String entryName = zipEntry.getName();
                String originalFilename = Paths.get(entryName).getFileName().toString();
                if (!isValidImageFile(originalFilename)) {
                    continue;
                }

                byte[] fileData = readZipEntryBytes(zis, buffer, originalFilename);
                if (fileData.length == 0) {
                    continue;
                }

                if (!batch.isEmpty() && shouldFlushZipBatch(batch, batchBytes, fileData.length)) {
                    mergeImportResult(total, batchImportImages(datasetId, batch));
                    batch.clear();
                    batchBytes = 0;
                }

                DatasetImageImportItem item = new DatasetImageImportItem();
                item.setFilename(originalFilename);
                item.setData(fileData);
                batch.add(item);
                batchBytes += fileData.length;
            }
        }
        if (!batch.isEmpty()) {
            mergeImportResult(total, batchImportImages(datasetId, batch));
        }
        return total;
    }

    private DatasetImageUploadRespVO processZipUploadFromPath(Path zipPath, Long datasetId) throws IOException {
        return importZipFromPath(datasetId, zipPath, null);
    }

    private ZipInputStream openZipInputStream(MultipartFile file) throws IOException {
        return new ZipInputStream(file.getInputStream(), StandardCharsets.UTF_8);
    }

    private byte[] readZipEntryBytes(ZipInputStream zis, byte[] buffer, String filename) throws IOException {
        ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
        long entryBytes = 0;
        int len;
        while ((len = zis.read(buffer)) > 0) {
            entryBytes += len;
            if (entryBytes > IMPORT_ZIP_ENTRY_MAX_BYTES) {
                throw exception(FILE_SIZE_EXCEEDED, "压缩包内单张图片超过 50MB: " + filename);
            }
            outputStream.write(buffer, 0, len);
        }
        return outputStream.toByteArray();
    }

    private boolean shouldFlushZipBatch(List<DatasetImageImportItem> batch, long batchBytes, int nextFileBytes) {
        return batch.size() >= IMPORT_ZIP_BATCH_SIZE
                || batchBytes + nextFileBytes > IMPORT_ZIP_BATCH_MAX_BYTES;
    }

    /**
     * 处理单个图片上传
     */
    private DatasetImageUploadRespVO processImageUpload(MultipartFile file, Long datasetId)
            throws IOException {
        if (!isValidImageFile(file.getOriginalFilename())) {
            throw exception(INVALID_FILE_TYPE);
        }

        DatasetImageImportItem item = new DatasetImageImportItem();
        item.setFilename(file.getOriginalFilename());
        item.setData(file.getBytes());
        return batchImportImages(datasetId, Collections.singletonList(item));
    }

    private DatasetImageUploadRespVO processImageUploadFromPath(Path filePath, String originalFilename,
                                                                Long datasetId) throws IOException {
        if (!isValidImageFile(originalFilename)) {
            throw exception(INVALID_FILE_TYPE);
        }
        DatasetImageImportItem item = new DatasetImageImportItem();
        item.setFilename(originalFilename);
        item.setData(Files.readAllBytes(filePath));
        return batchImportImages(datasetId, Collections.singletonList(item));
    }

    @Override
    public Long saveImportedImage(Long datasetId, String filename, byte[] fileData,
                                  String annotationsJson, Integer width, Integer height, Integer completed) {
        DatasetImageImportItem item = new DatasetImageImportItem();
        item.setFilename(filename);
        item.setData(fileData);
        item.setAnnotationsJson(annotationsJson);
        item.setWidth(width);
        item.setHeight(height);
        item.setCompleted(completed);
        DatasetImageUploadRespVO result = batchImportImages(datasetId, Collections.singletonList(item));
        if (result.getSuccessCount() <= 0) {
            throw exception(FILE_UPLOAD_FAILED, "图片导入失败");
        }
        List<DatasetImageDO> saved = datasetImageMapper.selectByDatasetIdAndNames(
                datasetId, Collections.singletonList(filename));
        return saved.isEmpty() ? null : saved.get(0).getId();
    }

    @Override
    public DatasetImageUploadRespVO importZipFromPath(Long datasetId, Path zipPath, IntConsumer progressCallback) {
        return importZipFromPath(datasetId, zipPath, progressCallback, ImportCancelChecker.NONE);
    }

    @Override
    public DatasetImageUploadRespVO importZipFromPath(Long datasetId, Path zipPath, IntConsumer progressCallback,
                                                    ImportCancelChecker cancelChecker) {
        if (cancelChecker == null) {
            cancelChecker = ImportCancelChecker.NONE;
        }
        DatasetImageUploadRespVO total = new DatasetImageUploadRespVO();
        List<DatasetImageImportItem> batch = new ArrayList<>(IMPORT_ZIP_BATCH_SIZE);
        int processed = 0;
        long batchBytes = 0;
        byte[] buffer = new byte[8192];

        try (ZipInputStream zis = new ZipInputStream(Files.newInputStream(zipPath), StandardCharsets.UTF_8)) {
            ZipEntry zipEntry;
            while ((zipEntry = zis.getNextEntry()) != null) {
                cancelChecker.throwIfCancelled();
                if (zipEntry.isDirectory()) {
                    continue;
                }
                String entryName = zipEntry.getName();
                String originalFilename = Paths.get(entryName).getFileName().toString();
                if (!isValidImageFile(originalFilename)) {
                    continue;
                }

                byte[] fileData = readZipEntryBytes(zis, buffer, originalFilename);
                if (fileData.length == 0) {
                    continue;
                }

                if (!batch.isEmpty() && shouldFlushZipBatch(batch, batchBytes, fileData.length)) {
                    cancelChecker.throwIfCancelled();
                    mergeImportResult(total, batchImportImages(datasetId, batch));
                    processed += batch.size();
                    if (progressCallback != null) {
                        progressCallback.accept(processed);
                    }
                    batch.clear();
                    batchBytes = 0;
                }

                DatasetImageImportItem item = new DatasetImageImportItem();
                item.setFilename(originalFilename);
                item.setData(fileData);
                batch.add(item);
                batchBytes += fileData.length;
            }
            if (!batch.isEmpty()) {
                cancelChecker.throwIfCancelled();
                mergeImportResult(total, batchImportImages(datasetId, batch));
                processed += batch.size();
                if (progressCallback != null) {
                    progressCallback.accept(processed);
                }
            }
        } catch (IOException e) {
            throw exception(FILE_UPLOAD_FAILED, e.getMessage());
        }
        logger.info("ZIP 流式导入完成: 成功 {}，覆盖 {}，失败 {}，跳过 {}",
                total.getSuccessCount(), total.getOverwrittenCount(), total.getFailedCount(), total.getSkippedCount());
        return total;
    }

    @Override
    public DatasetImageUploadRespVO batchImportImages(Long datasetId, List<DatasetImageImportItem> items) {
        if (items == null || items.isEmpty()) {
            return new DatasetImageUploadRespVO();
        }
        Map<String, DatasetImageDO> existingByName = loadExistingByNames(datasetId, items);
        return batchImportImagesInternal(datasetId, items, existingByName);
    }

    @Override
    public DatasetImageUploadRespVO batchImportImages(Long datasetId, List<DatasetImageImportItem> items,
                                                      Map<String, DatasetImageDO> existingByName) {
        if (items == null || items.isEmpty()) {
            return new DatasetImageUploadRespVO();
        }
        Map<String, DatasetImageDO> index = existingByName != null
                ? existingByName
                : loadExistingByNames(datasetId, items);
        return batchImportImagesInternal(datasetId, items, index);
    }

    private Map<String, DatasetImageDO> loadExistingByNames(
            Long datasetId, List<DatasetImageImportItem> items) {
        List<String> names = items.stream()
                .filter(Objects::nonNull)
                .map(DatasetImageImportItem::getFilename)
                .filter(Objects::nonNull)
                .map(name -> Paths.get(name).getFileName().toString())
                .distinct()
                .collect(Collectors.toList());
        if (names.isEmpty()) {
            return new LinkedHashMap<>();
        }
        return datasetImageMapper.selectImportIndexByDatasetIdAndNames(datasetId, names).stream()
                .collect(Collectors.toMap(
                        DatasetImageDO::getName,
                        img -> img,
                        (a, b) -> a,
                        LinkedHashMap::new));
    }

    private void mergeImportResult(DatasetImageUploadRespVO total, DatasetImageUploadRespVO batch) {
        total.setSuccessCount(total.getSuccessCount() + batch.getSuccessCount());
        total.setFailedCount(total.getFailedCount() + batch.getFailedCount());
        total.setSkippedCount(total.getSkippedCount() + batch.getSkippedCount());
        total.setOverwrittenCount(total.getOverwrittenCount() + batch.getOverwrittenCount());
        if (batch.getFailedFiles() != null && !batch.getFailedFiles().isEmpty()) {
            List<String> merged = total.getFailedFiles();
            for (String failed : batch.getFailedFiles()) {
                if (merged.size() >= 20) {
                    break;
                }
                merged.add(failed);
            }
        }
    }

    private DatasetImageUploadRespVO batchImportImagesInternal(Long datasetId, List<DatasetImageImportItem> items,
                                                               Map<String, DatasetImageDO> existingByName) {
        DatasetImageUploadRespVO result = new DatasetImageUploadRespVO();
        if (items == null || items.isEmpty()) {
            return result;
        }

        Map<String, DatasetImageImportItem> deduped = new LinkedHashMap<>();
        int skipped = 0;
        for (DatasetImageImportItem item : items) {
            if (item == null || item.getFilename() == null) {
                skipped++;
                continue;
            }
            String filename = Paths.get(item.getFilename()).getFileName().toString();
            if (!isValidImageFile(filename)) {
                skipped++;
                continue;
            }
            if (item.getData() == null || item.getData().length == 0) {
                skipped++;
                continue;
            }
            item.setFilename(filename);
            deduped.put(filename, item);
        }
        result.setSkippedCount(skipped);

        if (deduped.isEmpty()) {
            return result;
        }

        createBucketIfNotExists(minioBucket);

        List<DatasetImageImportItem> itemList = new ArrayList<>(deduped.values());
        List<ImportItemResult> importResults = new ArrayList<>(itemList.size());
        for (int i = 0; i < itemList.size(); i += MINIO_UPLOAD_PARALLEL) {
            int end = Math.min(i + MINIO_UPLOAD_PARALLEL, itemList.size());
            List<DatasetImageImportItem> chunk = itemList.subList(i, end);
            List<CompletableFuture<ImportItemResult>> futures = chunk.stream()
                    .map(item -> CompletableFuture.supplyAsync(
                            () -> uploadImportItem(datasetId, item), uploadExecutor))
                    .collect(Collectors.toList());
            CompletableFuture.allOf(futures.toArray(new CompletableFuture[0])).join();
            for (CompletableFuture<ImportItemResult> future : futures) {
                importResults.add(future.join());
            }
        }

        List<DatasetImageDO> toInsert = new ArrayList<>();
        List<DatasetImageDO> toUpdate = new ArrayList<>();
        List<String> oldMinioObjects = new ArrayList<>();
        List<String> failedFiles = new ArrayList<>();
        int overwritten = 0;

        for (ImportItemResult importResult : importResults) {
            if (!importResult.success) {
                result.setFailedCount(result.getFailedCount() + 1);
                if (failedFiles.size() < 20) {
                    failedFiles.add(importResult.filename + ": " + importResult.errorMessage);
                }
                continue;
            }

            DatasetImageDO existing = existingByName.get(importResult.filename);
            if (existing != null) {
                String oldObject = parseObjectNameFromPath(existing.getPath());
                if (oldObject != null) {
                    oldMinioObjects.add(oldObject);
                }
                applyImportFields(existing, importResult.filename, importResult.storagePath,
                        importResult.fileSize, importResult.item);
                toUpdate.add(existing);
                overwritten++;
            } else {
                DatasetImageDO image = buildNewImage(datasetId, importResult.filename,
                        importResult.storagePath, importResult.fileSize, importResult.item);
                toInsert.add(image);
                existingByName.put(importResult.filename, image);
            }
            result.setSuccessCount(result.getSuccessCount() + 1);
        }

        removeMinioObjectsQuietly(oldMinioObjects);

        if (!toInsert.isEmpty()) {
            insertBatchWithSequenceRecovery(toInsert);
        }
        if (!toUpdate.isEmpty()) {
            datasetImageMapper.updateBatch(toUpdate, 500);
        }

        if (result.getSuccessCount() > 0) {
            invalidateDatasetAllocationIfNeeded(datasetId);
        }

        result.setOverwrittenCount(overwritten);
        result.setFailedFiles(failedFiles);
        return result;
    }

    private ImportItemResult uploadImportItem(Long datasetId, DatasetImageImportItem item) {
        ImportItemResult result = new ImportItemResult();
        result.filename = item.getFilename();
        result.item = item;
        try {
            byte[] fileData = item.getData();
            String fileExtension = getFileExtension(item.getFilename());
            String storagePath = String.format("%s/%s.%s", datasetId, UUID.randomUUID(), fileExtension);
            uploadToMinio(fileData, storagePath, getContentType(fileExtension));
            result.success = true;
            result.storagePath = storagePath;
            result.fileSize = fileData.length;
        } catch (Exception e) {
            result.success = false;
            result.errorMessage = e.getMessage();
            logger.warn("图片导入失败: {}", item.getFilename(), e);
        }
        return result;
    }

    private static class ImportItemResult {
        private boolean success;
        private String filename;
        private String storagePath;
        private long fileSize;
        private DatasetImageImportItem item;
        private String errorMessage;
    }

    private DatasetImageDO buildNewImage(Long datasetId, String filename, String storagePath, long size,
                                         DatasetImageImportItem item) {
        DatasetImageDO image = new DatasetImageDO();
        image.setDatasetId(datasetId);
        image.setName(filename);
        image.setPath(buildMinioDownloadPath(storagePath));
        image.setSize(size);
        image.setIsTrain(0);
        image.setIsValidation(0);
        image.setIsTest(0);
        applyOptionalImportFields(image, item);
        return image;
    }

    private void applyImportFields(DatasetImageDO image, String filename, String storagePath, long size,
                                   DatasetImageImportItem item) {
        image.setName(filename);
        image.setPath(buildMinioDownloadPath(storagePath));
        image.setSize(size);
        applyOptionalImportFields(image, item);
    }

    private void applyOptionalImportFields(DatasetImageDO image, DatasetImageImportItem item) {
        if (item.getAnnotationsJson() != null && !item.getAnnotationsJson().isEmpty()) {
            image.setAnnotations(item.getAnnotationsJson());
        } else {
            image.setAnnotations(null);
        }
        if (item.getWidth() != null) {
            image.setWidth(item.getWidth());
        }
        if (item.getHeight() != null) {
            image.setHeigh(item.getHeight());
        }
        if (item.getCompleted() != null) {
            image.setCompleted(item.getCompleted());
            image.setModificationCount(item.getCompleted() == 1 ? 1 : 0);
        } else {
            image.setCompleted(0);
            image.setModificationCount(0);
        }
        if (item.getIsTrain() != null) {
            image.setIsTrain(item.getIsTrain());
        }
        if (item.getIsValidation() != null) {
            image.setIsValidation(item.getIsValidation());
        }
        if (item.getIsTest() != null) {
            image.setIsTest(item.getIsTest());
        }
    }

    private String buildMinioDownloadPath(String storagePath) {
        return "/api/v1/buckets/" + minioBucket + "/objects/download?prefix=" + storagePath;
    }

    private void removeMinioObjectsQuietly(List<String> objectNames) {
        for (String objectName : objectNames) {
            try {
                minioClient.removeObject(
                        RemoveObjectArgs.builder()
                                .bucket(minioBucket)
                                .object(objectName)
                                .build());
            } catch (Exception e) {
                logger.warn("删除旧 MinIO 文件失败: {}", objectName, e);
            }
        }
    }

    /**
     * 上传文件到MinIO
     */
    private void uploadToMinio(byte[] content, String objectName, String contentType)
            throws Exception {

        try (InputStream inputStream = new ByteArrayInputStream(content)) {
            minioClient.putObject(
                    PutObjectArgs.builder()
                            .bucket(minioBucket)
                            .object(objectName)
                            .stream(inputStream, content.length, -1)
                            .contentType(contentType)
                            .build());
        }
    }

    private void uploadToMinioFromStream(InputStream inputStream, long size, String objectName, String contentType)
            throws Exception {
        minioClient.putObject(
                PutObjectArgs.builder()
                        .bucket(minioBucket)
                        .object(objectName)
                        .stream(inputStream, size, -1)
                        .contentType(contentType)
                        .build());
    }

    /**
     * 新增图片后，若此前已划分用途或已同步训练包，则作废并需重新划分、同步
     */
    private void invalidateDatasetAllocationIfNeeded(Long datasetId) {
        DatasetDO dataset = datasetMapper.selectById(datasetId);
        if (dataset == null) {
            return;
        }
        boolean wasAllocated = Objects.equals(dataset.getIsAllocated(), CommonStatusEnum.YES.getStatus());
        boolean wasSynced = Objects.equals(dataset.getIsSyncMinio(), CommonStatusEnum.YES.getStatus())
                || dataset.getZipUrl() != null;
        if (!wasAllocated && !wasSynced) {
            return;
        }
        resetUsageByDatasetId(datasetId);
        datasetMapper.updateById(new DatasetDO().setId(datasetId)
                .setIsAllocated(CommonStatusEnum.NO.getStatus())
                .setIsSyncMinio(CommonStatusEnum.NO.getStatus())
                .setZipUrl(null));
    }

    // 辅助方法
    private boolean isValidImageFile(String filename) {
        if (filename == null) return false;
        String ext = getFileExtension(filename).toLowerCase();
        return ext.equals("jpg") || ext.equals("jpeg") || ext.equals("png");
    }

    private String getFileExtension(String filename) {
        int dotIndex = filename.lastIndexOf(".");
        return (dotIndex == -1) ? "" : filename.substring(dotIndex + 1);
    }

    private String getContentType(String extension) {
        String contentType = null;
        switch (extension.toLowerCase()) {
            case "jpg":
                contentType = "image/jpeg";
                break;
            case "jpeg":
                contentType = "image/jpeg";
                break;
            case "png":
                contentType = "image/png";
                break;
            default:
                contentType = "application/octet-stream";
                break;
        }
        return contentType;
    }
}
