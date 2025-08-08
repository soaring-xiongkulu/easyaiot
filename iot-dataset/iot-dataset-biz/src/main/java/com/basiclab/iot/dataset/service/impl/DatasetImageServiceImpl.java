package com.basiclab.iot.dataset.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.text.UUID;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.dataset.dal.dataobject.DatasetImageDO;
import com.basiclab.iot.dataset.dal.pgsql.DatasetImageMapper;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetImagePageReqVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetImageSaveReqVO;
import com.basiclab.iot.dataset.service.DatasetImageService;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.minio.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.multipart.MultipartFile;

import javax.annotation.Resource;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigDecimal;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.dataset.enums.ErrorCodeConstants.*;


/**
 * 图片数据集 Service 实现类
 *
 * @author IoT
 */
@Service
@Validated
public class DatasetImageServiceImpl implements DatasetImageService {

    private final static Logger logger = LoggerFactory.getLogger(DatasetImageServiceImpl.class);

    @Resource
    private DatasetImageMapper datasetImageMapper;

    @Resource
    private MinioClient minioClient; // 注入Minio客户端[2,4](@ref)

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
    public void syncToMinio(Long datasetId) {
        // 1. 查询数据集下所有图片
        List<DatasetImageDO> images = datasetImageMapper.selectList(
                new LambdaQueryWrapper<DatasetImageDO>()
                        .eq(DatasetImageDO::getDatasetId, datasetId));

        // 2. 创建Minio存储桶
        String bucketName = "dataset-" + datasetId;
        createBucketIfNotExists(bucketName);

        // 3. 遍历所有图片并同步
        for (DatasetImageDO image : images) {
            // 确定存储路径
            String usageType = getUsageType(image);
            String imageName = image.getName();

            // 图片存储路径
            String imagePath = String.format("%s/images/%s", usageType, imageName);
            // 标注文件存储路径
            String labelPath = String.format("%s/labels/%s.txt", usageType,
                    imageName.substring(0, imageName.lastIndexOf('.')));

            // 复制图片到新位置
            copyImageToMinio(image.getPath(), bucketName, imagePath);

            // 生成并上传标注文件
            createAndUploadLabelFile(image, bucketName, labelPath);
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

    private void copyImageToMinio(String sourcePath, String bucketName, String objectName) {
        try {
            // 解析原始路径获取对象信息
            String sourceObject = parseObjectNameFromPath(sourcePath);

            // 执行复制操作
            minioClient.copyObject(CopyObjectArgs.builder()
                    .source(CopySource.builder()
                            .bucket(minioBucket)
                            .object(sourceObject)
                            .build())
                    .bucket(bucketName)
                    .object(objectName)
                    .build());
        } catch (Exception e) {
            throw new RuntimeException("复制图片到Minio失败", e);
        }
    }

    private String parseObjectNameFromPath(String path) {
        // 实际项目中根据存储路径格式解析
        // 这里简化处理，假设路径格式为 /api/v1/buckets/{bucket}/objects/download?prefix={object}
        int start = path.indexOf("prefix=") + 7;
        return path.substring(start);
    }

    private void createAndUploadLabelFile(DatasetImageDO image, String bucketName, String objectName) {
        try {
            // 解析标注信息
            List<Map<String, Object>> annotations = parseAnnotations(image.getAnnotations());

            // 生成标注文件内容
            StringBuilder labelContent = new StringBuilder();
            for (Map<String, Object> annotation : annotations) {
                Object labelObj = annotation.get("label");
                Integer label = null;
                if (labelObj instanceof Integer) {
                    label = (Integer) labelObj;
                } else if (labelObj instanceof String) {
                    label = Integer.parseInt((String) labelObj);
                }
                List<Map<String, Double>> points = (List<Map<String, Double>>) annotation.get("points");
                // 计算边界框
                double minX = Double.MAX_VALUE;
                double minY = Double.MAX_VALUE;
                double maxX = Double.MIN_VALUE;
                double maxY = Double.MIN_VALUE;

                for (Map<String, Double> point : points) {
                    double x = point.get("x");
                    double y = point.get("y");
                    minX = Math.min(minX, x);
                    minY = Math.min(minY, y);
                    maxX = Math.max(maxX, x);
                    maxY = Math.max(maxY, y);
                }

                // 格式化边界框信息 (保留5位小数)
                labelContent.append(String.format("%s %.5f %.5f %.5f %.5f\n",
                        label, minX, minY, maxX, maxY));
            }

            // 上传标注文件
            minioClient.putObject(PutObjectArgs.builder()
                    .bucket(bucketName)
                    .object(objectName)
                    .stream(new ByteArrayInputStream(labelContent.toString().getBytes()),
                            labelContent.length(), -1)
                    .contentType("text/plain")
                    .build());
        } catch (Exception e) {
            throw new RuntimeException("生成标注文件失败", e);
        }
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