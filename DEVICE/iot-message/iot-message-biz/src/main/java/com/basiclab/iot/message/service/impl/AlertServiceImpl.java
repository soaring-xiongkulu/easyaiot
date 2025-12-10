package com.basiclab.iot.message.service.impl;

import com.basiclab.iot.message.domain.model.AlertNotificationMessage;
import com.basiclab.iot.message.domain.entity.AlertDO;
import com.basiclab.iot.message.mapper.AlertMapper;
import com.basiclab.iot.message.service.AlertService;
import io.minio.*;
import io.minio.errors.*;
import io.minio.messages.Item;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.FileInputStream;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Map;
import java.util.concurrent.locks.ReentrantLock;
import com.fasterxml.jackson.databind.ObjectMapper;

/**
 * 告警处理服务实现
 * 负责：存储告警到数据库、上传图片到MinIO
 * 
 * 支持两种消息格式（兼容Python端和Java端）：
 * 1. 通知消息格式（来自alert_hook_service）：
 *    {
 *        'alertId': ...,
 *        'alert': {
 *            'imagePath': ...,
 *            ...
 *        },
 *        'deviceId': ...
 *    }
 * 2. 告警消息格式（旧格式）：
 *    {
 *        'id': ...,
 *        'image_path': ...,
 *        'device_id': ...
 *    }
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Slf4j
@Service
public class AlertServiceImpl implements AlertService {

    @Autowired(required = false)
    private MinioClient minioClient;

    @Autowired(required = false)
    private AlertMapper alertMapper;

    // MinIO清空后的等待时间控制（兼容Python端逻辑）
    private volatile long lastMinioCleanupTime = 0; // 上次清空MinIO的时间戳
    private static final int MINIO_CLEANUP_WAIT_SECONDS = 5; // 清空后等待5秒才能再次上传
    private final ReentrantLock minioCleanupLock = new ReentrantLock(); // 保护清空时间变量的锁

    @Override
    public Integer processAlert(AlertNotificationMessage notificationMessage) {
        try {
            if (notificationMessage == null || notificationMessage.getAlert() == null) {
                log.warn("告警消息为空，跳过处理");
                return null;
            }

            AlertNotificationMessage.AlertInfo alert = notificationMessage.getAlert();
            String deviceId = notificationMessage.getDeviceId();
            String deviceName = notificationMessage.getDeviceName();
            String imagePath = alert.getImagePath();

            log.info("开始处理告警: deviceId={}, deviceName={}, imagePath={}", 
                    deviceId, deviceName, imagePath);

            // 获取告警ID（如果消息中已有alertId，说明Python端已插入数据库）
            Integer alertId = notificationMessage.getAlertId();
            
            // 如果没有alertId，需要先存储告警到数据库
            if (alertId == null) {
                alertId = saveAlertToDatabase(notificationMessage);
                if (alertId == null) {
                    log.warn("告警存储到数据库失败，跳过后续处理");
                    return null;
                }
                log.info("告警已存储到数据库: alertId={}", alertId);
            }
            
            // 如果没有图片路径，跳过图片上传
            if (imagePath == null || imagePath.isEmpty()) {
                log.debug("告警 {} 没有图片路径，跳过图片上传", alertId);
                return alertId;
            }

            // 检查是否在清空后的等待期内（在数据库查询前检查，避免不必要的操作）
            if (isInCleanupWaitPeriod()) {
                log.debug("告警 {} 图片上传跳过：MinIO清空后等待期内", alertId);
                return alertId;
            }

            // 上传图片到MinIO
            String minioPath = uploadImageToMinio(imagePath, alertId, deviceId);
            
            if (minioPath != null && alertId != null) {
                // 更新数据库中的图片路径
                updateAlertImagePath(alertId, minioPath);
                log.debug("告警 {} 图片路径已更新: {}", alertId, minioPath);
            } else if (minioPath == null) {
                log.warn("告警 {} 图片上传失败，保留原始路径: {}", alertId, imagePath);
            }

            log.info("告警处理完成: alertId={}", alertId);
            return alertId;

        } catch (Exception e) {
            log.error("处理告警失败: deviceId={}, error={}", 
                    notificationMessage != null ? notificationMessage.getDeviceId() : null, 
                    e.getMessage(), e);
            // 不抛出异常，避免影响消息确认
            return null;
        }
    }

    /**
     * 上传图片到MinIO的alert-images存储桶
     * 如果最近5秒内清空过MinIO，将跳过上传
     * 
     * @param imagePath 本地图片路径
     * @param alertId 告警ID
     * @param deviceId 设备ID
     * @return MinIO中的对象路径，如果失败返回null
     */
    private String uploadImageToMinio(String imagePath, Integer alertId, String deviceId) {
        // 检查是否在清空后的等待期内
        if (isInCleanupWaitPeriod()) {
            return null;
        }

        if (minioClient == null) {
            log.warn("MinIO客户端不可用，跳过图片上传: imagePath={}", imagePath);
            return null;
        }

        try {
            // 检查本地文件是否存在
            File imageFile = new File(imagePath);
            if (!imageFile.exists() || !imageFile.isFile()) {
                log.warn("告警图片文件不存在: imagePath={}", imagePath);
                return null;
            }

            // 等待文件写入完成（文件大小稳定）
            long fileSize = waitForFileStable(imageFile);
            if (fileSize <= 0) {
                log.warn("告警图片文件不可用或大小为0: imagePath={} (等待文件稳定后)", imagePath);
                return null;
            }

            // 存储桶名称
            String bucketName = "alert-images";

            // 确保存储桶存在
            try {
                boolean exists = minioClient.bucketExists(BucketExistsArgs.builder().bucket(bucketName).build());
                if (!exists) {
                    minioClient.makeBucket(MakeBucketArgs.builder().bucket(bucketName).build());
                    log.info("创建MinIO存储桶: {}", bucketName);
                }
            } catch (Exception e) {
                log.error("检查或创建MinIO存储桶失败: bucket={}, error={}", bucketName, e.getMessage(), e);
                return null;
            }

            // 生成对象名称：使用日期目录结构，格式：YYYY/MM/DD/alert_{alertId}_{deviceId}_{timestamp}.jpg
            String fileName = imageFile.getName();
            String fileExt = "";
            int lastDotIndex = fileName.lastIndexOf('.');
            if (lastDotIndex > 0) {
                fileExt = fileName.substring(lastDotIndex);
            } else {
                fileExt = ".jpg"; // 默认扩展名
            }

            LocalDateTime now = LocalDateTime.now();
            String dateDir = now.format(DateTimeFormatter.ofPattern("yyyy/MM/dd"));
            String timestamp = now.format(DateTimeFormatter.ofPattern("yyyyMMddHHmmss"));
            String objectName = String.format("%s/alert_%s_%s_%s%s", 
                    dateDir, 
                    alertId != null ? alertId : "unknown",
                    deviceId != null ? deviceId : "unknown",
                    timestamp,
                    fileExt);

            // 读取文件内容到内存，确保文件完整性
            // 使用二进制模式读取，在文件大小稳定后读取，避免文件在读取过程中被修改
            byte[] fileContent = null;
            int maxRetries = 3;
            int retryCount = 0;

            while (retryCount < maxRetries) {
                try (FileInputStream fileInputStream = new FileInputStream(imageFile)) {
                    // 读取完整文件内容到内存
                    fileContent = new byte[(int) fileSize];
                    int bytesRead = 0;
                    int totalBytesRead = 0;
                    while (totalBytesRead < fileSize && (bytesRead = fileInputStream.read(
                            fileContent, totalBytesRead, (int) fileSize - totalBytesRead)) != -1) {
                        totalBytesRead += bytesRead;
                    }

                    // 验证读取的数据大小是否与文件大小一致
                    if (totalBytesRead == fileSize) {
                        // 读取成功，跳出重试循环
                        break;
                    } else {
                        retryCount++;
                        if (retryCount < maxRetries) {
                            log.debug("告警图片文件读取大小不匹配（重试 {}/{}）: 期望 {} 字节，实际读取 {} 字节，等待文件稳定后重试...",
                                    retryCount, maxRetries, fileSize, totalBytesRead);
                            Thread.sleep(200); // 等待200ms后重试
                            // 重新等待文件稳定（文件可能还在写入）
                            long newSize = waitForFileStable(imageFile);
                            if (newSize > 0 && newSize != fileSize) {
                                fileSize = newSize;
                                fileContent = null; // 重置，重新读取
                                retryCount = 0; // 重置重试计数，因为文件大小变化了
                            }
                        } else {
                            log.warn("告警图片文件读取不完整（已重试 {} 次）: 期望 {} 字节，实际读取 {} 字节",
                                    maxRetries, fileSize, totalBytesRead);
                            return null;
                        }
                    }
                } catch (Exception e) {
                    retryCount++;
                    if (retryCount < maxRetries) {
                        log.debug("告警图片文件读取失败（重试 {}/{}）: {}，等待后重试...",
                                retryCount, maxRetries, e.getMessage());
                        Thread.sleep(200);
                    } else {
                        log.warn("告警图片文件读取失败（已重试 {} 次）: {}", maxRetries, e.getMessage());
                        return null;
                    }
                }
            }

            if (fileContent == null || fileContent.length != fileSize) {
                log.warn("告警图片文件读取失败: imagePath={}", imagePath);
                return null;
            }

            // 确定Content-Type
            String contentType = "application/octet-stream";
            String lowerExt = fileExt.toLowerCase();
            if (lowerExt.equals(".jpg") || lowerExt.equals(".jpeg")) {
                contentType = "image/jpeg";
            } else if (lowerExt.equals(".png")) {
                contentType = "image/png";
            }

            // 使用putObject上传文件内容（从内存流上传，避免文件被修改的问题）
            try (ByteArrayInputStream dataStream = new ByteArrayInputStream(fileContent)) {
                minioClient.putObject(
                        PutObjectArgs.builder()
                                .bucket(bucketName)
                                .object(objectName)
                                .stream(dataStream, fileContent.length, -1)
                                .contentType(contentType)
                                .build()
                );

                log.debug("告警图片上传成功: bucket={}/{}, 大小: {} 字节", bucketName, objectName, fileSize);

                // 返回MinIO下载URL（用于存储到数据库）
                // 格式：/api/v1/buckets/{bucketName}/objects/download?prefix={url_encoded_object_name}
                String encodedObjectName = URLEncoder.encode(objectName, StandardCharsets.UTF_8.toString());
                String downloadUrl = String.format("/api/v1/buckets/%s/objects/download?prefix=%s",
                        bucketName, encodedObjectName);
                return downloadUrl;
            }

        } catch (ErrorResponseException e) {
            String errorMsg = e.getMessage();
            log.error("MinIO上传错误: {}", errorMsg, e);

            // 检查是否是 "stream having not enough data" 错误
            if (errorMsg != null && errorMsg.toLowerCase().contains("stream having not enough data")) {
                log.warn("检测到MinIO数据流错误，将删除alert-images存储桶下的所有图片");
                int deletedCount = deleteAllAlertImagesFromMinio();
                log.info("已清理告警图片存储桶，删除了 {} 张图片", deletedCount);
            }

            return null;
        } catch (Exception e) {
            String errorMsg = e.getMessage();
            log.error("上传告警图片到MinIO失败: {}", errorMsg, e);

            // 检查是否是 "stream having not enough data" 错误
            if (errorMsg != null && errorMsg.toLowerCase().contains("stream having not enough data")) {
                log.warn("检测到MinIO数据流错误，将删除alert-images存储桶下的所有图片");
                int deletedCount = deleteAllAlertImagesFromMinio();
                log.info("已清理告警图片存储桶，删除了 {} 张图片", deletedCount);
            }

            return null;
        }
    }

    /**
     * 删除MinIO的alert-images存储桶下的所有图片
     * 清空后会记录时间，后续5秒内的上传请求将被跳过
     * 
     * @return 删除的图片数量，如果失败返回0
     */
    private int deleteAllAlertImagesFromMinio() {
        if (minioClient == null) {
            log.warn("MinIO客户端不可用，跳过删除操作");
            return 0;
        }

        try {
            String bucketName = "alert-images";

            // 检查存储桶是否存在
            boolean exists = minioClient.bucketExists(BucketExistsArgs.builder().bucket(bucketName).build());
            if (!exists) {
                log.info("MinIO存储桶不存在，无需删除: {}", bucketName);
                return 0;
            }

            // 列出所有对象并删除
            int deletedCount = 0;
            Iterable<Result<Item>> results = minioClient.listObjects(
                    ListObjectsArgs.builder().bucket(bucketName).prefix("").recursive(true).build());

            for (Result<Item> result : results) {
                try {
                    Item item = result.get();
                    // 跳过文件夹标记（以/结尾的对象）
                    if (item.objectName().endsWith("/")) {
                        continue;
                    }

                    minioClient.removeObject(
                            RemoveObjectArgs.builder().bucket(bucketName).object(item.objectName()).build());
                    deletedCount++;
                    log.debug("删除告警图片: {}/{}", bucketName, item.objectName());
                } catch (Exception e) {
                    log.warn("删除告警图片失败: {}/{}, error={}", bucketName,
                            result.get().objectName(), e.getMessage());
                }
            }

            // 记录清空时间（使用锁保护）
            minioCleanupLock.lock();
            try {
                lastMinioCleanupTime = System.currentTimeMillis();
            } finally {
                minioCleanupLock.unlock();
            }

            log.info("已删除MinIO告警图片存储桶下的所有图片，共 {} 张，将在 {} 秒内跳过所有上传请求",
                    deletedCount, MINIO_CLEANUP_WAIT_SECONDS);
            return deletedCount;

        } catch (Exception e) {
            log.error("删除MinIO告警图片失败: {}", e.getMessage(), e);
            return 0;
        }
    }

    /**
     * 检查是否在清空后的等待期内
     */
    private boolean isInCleanupWaitPeriod() {
        minioCleanupLock.lock();
        try {
            if (lastMinioCleanupTime > 0) {
                long currentTime = System.currentTimeMillis();
                long elapsed = (currentTime - lastMinioCleanupTime) / 1000; // 转换为秒
                if (elapsed < MINIO_CLEANUP_WAIT_SECONDS) {
                    long waitRemaining = MINIO_CLEANUP_WAIT_SECONDS - elapsed;
                    log.debug("告警图片上传跳过：MinIO清空后等待期内（还需等待 {} 秒）", waitRemaining);
                    return true;
                }
            }
            return false;
        } finally {
            minioCleanupLock.unlock();
        }
    }

    /**
     * 等待文件写入完成（文件大小稳定）
     * 
     * @param file 文件对象
     * @return 稳定的文件大小（字节），如果超时或文件不存在返回0
     */
    private long waitForFileStable(File file) {
        if (!file.exists()) {
            return 0;
        }

        long startTime = System.currentTimeMillis();
        long lastSize = 0;
        int stableCount = 0;
        int maxWaitSeconds = 5;
        int checkInterval = 100; // 毫秒
        int requiredStableChecks = 3; // 需要连续3次大小相同才认为稳定

        while ((System.currentTimeMillis() - startTime) < maxWaitSeconds * 1000) {
            try {
                if (!file.exists()) {
                    return 0;
                }

                long currentSize = file.length();

                if (currentSize == 0) {
                    // 文件大小为0，可能还在写入，继续等待
                    Thread.sleep(checkInterval);
                    continue;
                }

                if (lastSize == 0) {
                    lastSize = currentSize;
                    stableCount = 1;
                } else if (currentSize == lastSize) {
                    stableCount++;
                    if (stableCount >= requiredStableChecks) {
                        // 文件大小已稳定
                        return currentSize;
                    }
                } else {
                    // 文件大小变化了，重置计数
                    lastSize = currentSize;
                    stableCount = 1;
                }

                Thread.sleep(checkInterval);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                return 0;
            } catch (Exception e) {
                // 文件可能被删除或无法访问
                log.warn("检查文件大小失败: file={}, error={}", file.getPath(), e.getMessage());
                return 0;
            }
        }

        // 超时，返回最后一次检测到的大小（如果存在）
        return lastSize > 0 ? lastSize : 0;
    }

    /**
     * 存储告警到数据库
     * 使用@DS("video")注解切换到VIDEO数据库
     *
     * @param notificationMessage 告警通知消息
     * @return 告警ID（如果存储成功）
     */
    private Integer saveAlertToDatabase(AlertNotificationMessage notificationMessage) {
        if (alertMapper == null) {
            log.warn("AlertMapper不可用，跳过数据库存储");
            return null;
        }

        try {
            AlertNotificationMessage.AlertInfo alert = notificationMessage.getAlert();
            
            // 构建AlertDO对象
            AlertDO alertDO = new AlertDO();
            alertDO.setObject(alert.getObject());
            alertDO.setEvent(alert.getEvent());
            alertDO.setRegion(alert.getRegion());
            
            // 处理information字段（可能是对象，需要转换为JSON字符串）
            Object information = alert.getInformation();
            if (information != null) {
                if (information instanceof String) {
                    alertDO.setInformation((String) information);
                } else {
                    // 如果是对象，转换为JSON字符串（这里简化处理，直接调用toString）
                    // 如果需要完整的JSON序列化，可以使用Jackson或Gson
                    alertDO.setInformation(information.toString());
                }
            }
            
            // 处理时间字段
            String timeStr = alert.getTime();
            LocalDateTime alertTime;
            if (StringUtils.hasText(timeStr)) {
                try {
                    // 尝试解析时间字符串，格式：YYYY-MM-DD HH:MM:SS
                    DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
                    alertTime = LocalDateTime.parse(timeStr, formatter);
                } catch (Exception e) {
                    log.warn("解析告警时间失败，使用当前时间: timeStr={}, error={}", timeStr, e.getMessage());
                    alertTime = LocalDateTime.now();
                }
            } else {
                alertTime = LocalDateTime.now();
            }
            alertDO.setTime(alertTime);
            
            alertDO.setDeviceId(notificationMessage.getDeviceId());
            alertDO.setDeviceName(notificationMessage.getDeviceName());
            alertDO.setImagePath(alert.getImagePath());
            alertDO.setRecordPath(alert.getRecordPath());
            
            // 提取并设置 task_type（优先从 alert.taskType 获取，如果没有则从 information 中提取）
            String taskType = alert.getTaskType();
            if (taskType == null || taskType.isEmpty()) {
                // 如果 alert.taskType 为空，尝试从 information 中提取
                if (information != null) {
                    try {
                        if (information instanceof String) {
                            // 尝试解析JSON字符串
                            ObjectMapper mapper = new ObjectMapper();
                            Map<String, Object> infoMap = mapper.readValue((String) information, Map.class);
                            if (infoMap != null && infoMap.containsKey("task_type")) {
                                taskType = (String) infoMap.get("task_type");
                            }
                        } else if (information instanceof Map) {
                            Map<String, Object> infoMap = (Map<String, Object>) information;
                            if (infoMap.containsKey("task_type")) {
                                taskType = (String) infoMap.get("task_type");
                            }
                        }
                    } catch (Exception e) {
                        log.warn("从information中提取task_type失败: {}", e.getMessage());
                    }
                }
            }
            // 兼容 'snapshot' 值，统一转换为 'snap'
            if ("snapshot".equals(taskType)) {
                taskType = "snap";
            }
            // 如果仍然为空，设置默认值
            if (taskType == null || taskType.isEmpty()) {
                taskType = "realtime";
            }
            alertDO.setTaskType(taskType);
            
            // 插入数据库（使用@DS("video")注解的Mapper会自动切换到VIDEO数据库）
            int result = alertMapper.insert(alertDO);
            if (result > 0 && alertDO.getId() != null) {
                log.info("告警存储成功: alertId={}, deviceId={}", alertDO.getId(), alertDO.getDeviceId());
                return alertDO.getId();
            } else {
                log.warn("告警存储失败: result={}, alertId={}", result, alertDO.getId());
                return null;
            }
            
        } catch (Exception e) {
            log.error("存储告警到数据库失败: deviceId={}, error={}", 
                    notificationMessage.getDeviceId(), e.getMessage(), e);
            return null;
        }
    }

    /**
     * 更新数据库中的图片路径
     * 使用@DS("video")注解切换到VIDEO数据库
     *
     * @param alertId 告警ID
     * @param minioPath MinIO路径
     */
    private void updateAlertImagePath(Integer alertId, String minioPath) {
        if (alertMapper == null) {
            log.warn("AlertMapper不可用，跳过数据库更新");
            return;
        }

        if (alertId == null || minioPath == null || minioPath.isEmpty()) {
            log.warn("参数无效，跳过数据库更新: alertId={}, minioPath={}", alertId, minioPath);
            return;
        }

        try {
            // 更新数据库（使用@DS("video")注解的Mapper会自动切换到VIDEO数据库）
            int result = alertMapper.updateImagePath(alertId, minioPath);
            if (result > 0) {
                log.debug("告警图片路径更新成功: alertId={}, minioPath={}", alertId, minioPath);
            } else {
                log.warn("告警图片路径更新失败（可能记录不存在）: alertId={}, minioPath={}", alertId, minioPath);
            }
        } catch (Exception e) {
            log.error("更新告警图片路径失败: alertId={}, minioPath={}, error={}", 
                    alertId, minioPath, e.getMessage(), e);
        }
    }
}

