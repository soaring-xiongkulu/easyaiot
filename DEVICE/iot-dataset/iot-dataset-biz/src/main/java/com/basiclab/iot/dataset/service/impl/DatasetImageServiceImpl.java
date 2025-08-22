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
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetImagePageReqVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetImageSaveReqVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetTagPageReqVO;
import com.basiclab.iot.dataset.service.DatasetImageService;
import com.basiclab.iot.dataset.service.DatasetTagService;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.minio.*;
import io.minio.http.Method;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.env.Environment;
import org.springframework.stereotype.Service;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.multipart.MultipartFile;
import org.yaml.snakeyaml.Yaml;

import javax.annotation.Resource;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigDecimal;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.*;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;
import java.util.zip.ZipOutputStream;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.dataset.enums.ErrorCodeConstants.*;


/**
 * 图片数据集 Service 实现类
 *
 * @author EasyAIoT
 */
@Service
@Validated
public class DatasetImageServiceImpl implements DatasetImageService {

    private final static Logger logger = LoggerFactory.getLogger(DatasetImageServiceImpl.class);

    @Resource
    private DatasetImageMapper datasetImageMapper;

    @Resource
    private DatasetMapper datasetMapper;

    @Resource
    private DatasetTagService datasetTagService;

    @Resource
    private MinioClient minioClient;

    @Resource
    private Environment environment;

    @Value("${minio.bucket}") // MinIO存储桶名称
    private String minioBucket;

    @Override
    public Long createDatasetImage(DatasetImageSaveReqVO createReqVO) {
        // 插入
        DatasetImageDO image = BeanUtils.toBean(createReqVO, DatasetImageDO.class);
        datasetImageMapper.insert(image);
        // 返回
        return image.getId();
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
        // 删除MinIO中的文件
        deleteMinioFiles(ids);
        // 批量删除数据库记录
        datasetImageMapper.deleteBatchIds(ids);
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

    // DatasetImageServiceImpl.java
    @Override
    public boolean checkSyncCondition(Long datasetId) {
        // 1. 检查数据集是否已划分用途
        long count = datasetImageMapper.selectCount(new LambdaQueryWrapper<DatasetImageDO>()
                .eq(DatasetImageDO::getDatasetId, datasetId)
                .eq(DatasetImageDO::getIsTrain, 0)
                .eq(DatasetImageDO::getIsValidation, 0)
                .eq(DatasetImageDO::getIsTest, 0));

        if (count > 0) {
            return false; // 存在未划分用途的图片
        }

        // 2. 检查所有图片是否已完成标注
        count = datasetImageMapper.selectCount(new LambdaQueryWrapper<DatasetImageDO>()
                .eq(DatasetImageDO::getDatasetId, datasetId)
                .eq(DatasetImageDO::getCompleted, 0));

        return count == 0; // 所有图片都已标注
    }

    @Override
    public String syncToMinio(Long datasetId) {
        List<DatasetImageDO> images = datasetImageMapper.selectList(
                new LambdaQueryWrapper<DatasetImageDO>()
                        .eq(DatasetImageDO::getDatasetId, datasetId));
        Path tempDir = createTempDirectoryStructure(datasetId);
        for (DatasetImageDO image : images) {
            String usageType = getUsageType(image);
            String imageName = image.getName();
            Path imagePath = tempDir.resolve("images/" + usageType + "/" + imageName);
            String labelFileName = imageName.substring(0, imageName.lastIndexOf('.')) + ".txt";
            Path labelPath = tempDir.resolve("labels/" + usageType + "/" + labelFileName);
            downloadImageToTemp(image, imagePath);
            createLabelFile(image, labelPath);
        }
        generateDataYaml(datasetId, tempDir);
        Path zipPath = compressDirectory(tempDir, datasetId);
        String zipUrl = uploadZipToMinio(zipPath, datasetId);
        cleanupTempFiles(tempDir, zipPath);
        // 更新数据集压缩包地址
        DatasetDO updateDO = new DatasetDO();
        updateDO.setId(datasetId);
        updateDO.setZipUrl(zipUrl);
        datasetMapper.updateById(updateDO);
        return zipUrl;
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
                Files.copy(in, targetPath, StandardCopyOption.REPLACE_EXISTING);
            }
        } catch (Exception e) {
            throw new RuntimeException("下载图片失败: " + image.getPath(), e);
        }
    }

    private void createLabelFile(DatasetImageDO image, Path labelPath) {
        try {
            String labelContent = generateLabelContent(image.getAnnotations());
            Files.write(labelPath, labelContent.getBytes(StandardCharsets.UTF_8),
                    StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING);
        } catch (Exception e) {
            throw new RuntimeException("生成标签文件失败", e);
        }
    }

    private String generateLabelContent(String annotationsJson) {
        try {
            // 解析标注信息
            List<Map<String, Object>> annotations = parseAnnotations(annotationsJson);
            StringBuilder labelContent = new StringBuilder();

            for (Map<String, Object> annotation : annotations) {
                // 获取标签ID（类别）
                Object labelObj = annotation.get("label");
                Integer label = null;
                if (labelObj instanceof Integer) {
                    label = (Integer) labelObj;
                } else if (labelObj instanceof String) {
                    label = Integer.parseInt((String) labelObj);
                } else {
                    // 处理无法识别的标签类型
                    logger.warn("无法识别的标签类型: {}", labelObj);
                    continue;
                }

                // 获取矩形框的四个顶点（归一化坐标）
                List<Map<String, Double>> points = (List<Map<String, Double>>) annotation.get("points");
                if (points == null || points.size() != 4) {
                    logger.warn("无效的标注点数量: {}", points != null ? points.size() : 0);
                    continue;
                }

                // 提取四个顶点的坐标
                double[] xCoords = new double[4];
                double[] yCoords = new double[4];
                for (int i = 0; i < 4; i++) {
                    Map<String, Double> point = points.get(i);
                    xCoords[i] = point.get("x");
                    yCoords[i] = point.get("y");
                }

                // 计算边界框的最小/最大坐标
                double minX = Arrays.stream(xCoords).min().getAsDouble();
                double minY = Arrays.stream(yCoords).min().getAsDouble();
                double maxX = Arrays.stream(xCoords).max().getAsDouble();
                double maxY = Arrays.stream(yCoords).max().getAsDouble();

                // 计算YOLO格式的中心点坐标和宽高（归一化值）
                double centerX = (minX + maxX) / 2.0;
                double centerY = (minY + maxY) / 2.0;
                double width = maxX - minX;
                double height = maxY - minY;

                // 格式化边界框信息 (保留5位小数)
                // YOLO格式: <class_id> <center_x> <center_y> <width> <height>
                labelContent.append(String.format("%d %.5f %.5f %.5f %.5f\n",
                        label, centerX, centerY, width, height));
            }

            return labelContent.toString();
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
            yamlData.put("path", tempDir.toAbsolutePath().toString());
            yamlData.put("train", "images/train");
            yamlData.put("val", "images/val");
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
        Path zipPath = Paths.get(sourceDir.getParent().toString(), "dataset-" + datasetId + ".zip");

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
            throw new RuntimeException("压缩目录失败", e);
        }
    }

    private void cleanupTempFiles(Path tempDir, Path zipPath) {
        try {
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
            Files.deleteIfExists(zipPath);
        } catch (IOException e) {
            logger.error("清理临时文件失败: {}", e.getMessage());
        }
    }

    private String uploadZipToMinio(Path zipPath, Long datasetId) {
        try (InputStream is = Files.newInputStream(zipPath)) {
            String objectName = "datasets/dataset-" + datasetId + ".zip";

            minioClient.putObject(
                    PutObjectArgs.builder()
                            .bucket(minioBucket)
                            .object(objectName)
                            .stream(is, Files.size(zipPath), -1)
                            .contentType("application/zip")
                            .build());

            // 返回公开访问URL（需配置存储桶策略）
            int expirySeconds = 10 * 365 * 24 * 60 * 60;
            return minioClient.getPresignedObjectUrl(
                    GetPresignedObjectUrlArgs.builder()
                            .method(Method.GET)
                            .bucket(minioBucket)
                            .object(objectName)
                            .expiry(expirySeconds, TimeUnit.DAYS) // 7天有效
                            .build());
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
        if (image.getIsValidation() == 1) return "valid";
        if (image.getIsTest() == 1) return "test";
        throw new IllegalStateException("图片未划分用途");
    }

    private String parseObjectNameFromPath(String path) {
        // 获取当前激活的profile
        String env = environment.getActiveProfiles().length > 0 ?
                environment.getActiveProfiles()[0] :
                environment.getDefaultProfiles()[0];
        // 根据环境添加前缀
        String fullPath = path;
        if (env.contains("local") || env.contains("dev")) {
            fullPath = "http://iot.basiclab.top:9001" + path;
        } else if (env.contains("prod")) {
            fullPath = "http://10.0.0.87:9001" + path;
        }
        try {
            // 解析URI获取查询参数
            URI uri = URI.create(fullPath);
            String query = uri.getQuery();
            if (query != null) {
                for (String param : query.split("&")) {
                    if (param.startsWith("prefix=")) {
                        return param.substring(7);
                    }
                }
            }
        } catch (Exception e) {
            logger.warn("解析URI失败，使用后备方案: {}", e.getMessage());
        }
        // 后备方案：直接提取prefix值
        int start = path.indexOf("prefix=");
        if (start != -1) {
            return path.substring(start + 7);
        }
        return path;
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
    public void processUpload(MultipartFile file, Long datasetId, Boolean isZip) {
        try {
            if (isZip) {
                processZipUpload(file, datasetId);
            } else {
                processImageUpload(file, datasetId);
            }
        } catch (Exception e) {
            logger.error("文件上传处理失败: {}", e.getMessage());
            throw exception(FILE_UPLOAD_FAILED, e.getMessage());
        }
    }

    /**
     * 处理压缩包上传并解压
     */
    private void processZipUpload(MultipartFile file, Long datasetId)
            throws IOException {

        try (ZipInputStream zis = new ZipInputStream(file.getInputStream())) {
            ZipEntry zipEntry;
            byte[] buffer = new byte[1024];
            int fileCount = 0;

            while ((zipEntry = zis.getNextEntry()) != null) {
                if (zipEntry.isDirectory() || !isValidImageFile(zipEntry.getName())) {
                    continue;
                }

                // 处理每个图片文件
                String originalFilename = zipEntry.getName();
                ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
                int len;
                while ((len = zis.read(buffer)) > 0) {
                    outputStream.write(buffer, 0, len);
                }

                byte[] fileData = outputStream.toByteArray();
                saveToMinioAndDB(fileData, originalFilename, datasetId);
                fileCount++;
            }
            logger.info("成功解压并上传 {} 个文件", fileCount);
        }
    }

    /**
     * 处理单个图片上传
     */
    private void processImageUpload(MultipartFile file, Long datasetId)
            throws IOException {

        if (!isValidImageFile(file.getOriginalFilename())) {
            throw exception(INVALID_FILE_TYPE);
        }

        saveToMinioAndDB(file.getBytes(), file.getOriginalFilename(), datasetId);
    }

    /**
     * 保存到MinIO并插入数据库记录
     */
    private void saveToMinioAndDB(byte[] fileData, String originalFilename, Long datasetId) {
        try {
            // 1. 生成唯一存储路径
            String fileExtension = getFileExtension(originalFilename);
            String storagePath = String.format("%s/%s.%s",
                    datasetId,
                    UUID.randomUUID(),
                    fileExtension);

            // 2. 上传到MinIO
            uploadToMinio(fileData, storagePath, getContentType(fileExtension));

            // 3. 保存到数据库
            DatasetImageDO image = new DatasetImageDO();
            image.setDatasetId(datasetId);
            image.setName(originalFilename);
            image.setPath("/api/v1/buckets/" + minioBucket + "/objects/download?prefix=" + storagePath);
            image.setSize((long) fileData.length);
            image.setIsTrain(0);
            image.setIsValidation(0);
            image.setIsTest(0);
            datasetImageMapper.insert(image);
        } catch (Exception e) {
            logger.error("文件保存失败: {}", e.getMessage());
            throw exception(FILE_UPLOAD_FAILED, "文件保存失败");
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