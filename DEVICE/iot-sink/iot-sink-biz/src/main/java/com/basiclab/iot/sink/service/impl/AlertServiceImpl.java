package com.basiclab.iot.sink.service.impl;

import com.baomidou.dynamic.datasource.toolkit.DynamicDataSourceContextHolder;
import com.basiclab.iot.sink.dal.dataobject.AlertDO;
import com.basiclab.iot.sink.dal.mapper.AlertMapper;
import com.basiclab.iot.sink.domain.model.AlertNotificationMessage;
import com.basiclab.iot.sink.service.AlertService;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.minio.*;
import io.minio.errors.*;
import io.minio.messages.Item;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.FileInputStream;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Map;
import java.util.concurrent.locks.ReentrantLock;

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

    @Autowired(required = false)
    private ObjectMapper objectMapper;

    @Autowired(required = false)
    private JdbcTemplate jdbcTemplate;

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

            // 1. 检查告警是否在检测区域内
            String matchedRegionName = checkAlertRegion(notificationMessage);
            if (matchedRegionName == null && hasDetectionRegions(deviceId)) {
                // 如果配置了检测区域但没有匹配到，跳过处理
                log.info("告警未匹配到检测区域，跳过处理: deviceId={}", deviceId);
                return null;
            }
            
            // 2. 如果匹配到区域，更新alert中的region字段
            if (matchedRegionName != null) {
                alert.setRegion(matchedRegionName);
            }
            
            // 3. 检查是否在布防时段内
            if (!checkDefenseSchedule(deviceId, alert.getTime())) {
                log.info("告警不在布防时段内，跳过处理: deviceId={}", deviceId);
                return null;
            }

            // 获取告警ID（如果消息中已有alertId，说明Python端已插入数据库）
            Integer alertId = notificationMessage.getAlertId();
            
            // 如果没有alertId，需要先存储告警到数据库（无论是否开启通知，都要存储）
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

            // 上传图片到MinIO（无论是否开启通知，都要上传）
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
                    // 如果是对象，转换为JSON字符串
                    try {
                        if (objectMapper != null) {
                            alertDO.setInformation(objectMapper.writeValueAsString(information));
                        } else {
                            alertDO.setInformation(information.toString());
                        }
                    } catch (Exception e) {
                        log.warn("转换information为JSON失败，使用toString: {}", e.getMessage());
                        alertDO.setInformation(information.toString());
                    }
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

    /**
     * 检查告警是否在检测区域内
     * 使用DynamicDataSourceContextHolder切换到VIDEO数据库
     * 
     * @param notificationMessage 告警通知消息
     * @return 匹配的区域名称，如果没有匹配到区域但配置了区域则返回null，如果没有配置区域则返回空字符串
     */
    private String checkAlertRegion(AlertNotificationMessage notificationMessage) {
        try {
            if (jdbcTemplate == null) {
                log.warn("JdbcTemplate不可用，跳过区域检测");
                return ""; // 默认通过
            }

            String deviceId = notificationMessage.getDeviceId();
            AlertNotificationMessage.AlertInfo alert = notificationMessage.getAlert();
            Object information = alert.getInformation();

            // 解析information字段获取bbox
            if (information == null) {
                return ""; // 没有information，默认通过
            }

            JsonNode infoNode;
            if (information instanceof String) {
                try {
                    infoNode = objectMapper != null ? objectMapper.readTree((String) information) : null;
                } catch (Exception e) {
                    log.warn("解析information失败: {}", e.getMessage());
                    return ""; // 解析失败，默认通过
                }
            } else if (information instanceof Map) {
                infoNode = objectMapper != null ? objectMapper.valueToTree(information) : null;
            } else {
                return ""; // 未知格式，默认通过
            }

            if (infoNode == null || !infoNode.has("bbox")) {
                return ""; // 没有bbox，默认通过
            }

            JsonNode bboxNode = infoNode.get("bbox");
            if (!bboxNode.isArray() || bboxNode.size() != 4) {
                return ""; // bbox格式错误，默认通过
            }

            double x1 = bboxNode.get(0).asDouble();
            double y1 = bboxNode.get(1).asDouble();
            double x2 = bboxNode.get(2).asDouble();
            double y2 = bboxNode.get(3).asDouble();

            // 计算bbox中心点（归一化坐标）
            double bboxCenterX, bboxCenterY;
            if (x1 <= 1.0 && y1 <= 1.0 && x2 <= 1.0 && y2 <= 1.0) {
                // 已经是归一化坐标
                bboxCenterX = (x1 + x2) / 2.0;
                bboxCenterY = (y1 + y2) / 2.0;
            } else {
                // 绝对坐标，需要归一化（使用默认帧尺寸640x360）
                double frameWidth = 640.0;
                double frameHeight = 360.0;
                bboxCenterX = (x1 + x2) / 2.0 / frameWidth;
                bboxCenterY = (y1 + y2) / 2.0 / frameHeight;
            }

            // 切换到video数据源
            DynamicDataSourceContextHolder.push("video");
            try {
                // 查询设备的检测区域列表
                String sql = "SELECT id, region_name, region_type, points, model_ids, is_enabled " +
                        "FROM device_detection_region " +
                        "WHERE device_id = ? AND is_enabled = true " +
                        "ORDER BY sort_order";
                List<Map<String, Object>> regions = jdbcTemplate.queryForList(sql, deviceId);

                if (regions == null || regions.isEmpty()) {
                    return ""; // 没有配置检测区域，默认通过
                }

                // 获取算法任务的模型ID列表（用于匹配区域）
                List<Integer> modelIds = getAlgorithmTaskModelIds(deviceId);

                // 遍历所有区域，检查bbox是否在区域内
                for (Map<String, Object> region : regions) {
                    // 检查区域是否关联了模型（如果配置了model_ids）
                    String modelIdsStr = (String) region.get("model_ids");
                    if (modelIdsStr != null && !modelIdsStr.isEmpty() && modelIds != null && !modelIds.isEmpty()) {
                        try {
                            JsonNode regionModelIdsNode = objectMapper.readTree(modelIdsStr);
                            if (regionModelIdsNode.isArray()) {
                                boolean matched = false;
                                for (JsonNode modelIdNode : regionModelIdsNode) {
                                    if (modelIds.contains(modelIdNode.asInt())) {
                                        matched = true;
                                        break;
                                    }
                                }
                                if (!matched) {
                                    continue; // 区域关联的模型与任务模型不匹配，跳过
                                }
                            }
                        } catch (Exception e) {
                            log.warn("解析区域模型ID列表失败: {}", e.getMessage());
                        }
                    }

                    // 解析区域坐标点
                    String pointsStr = (String) region.get("points");
                    if (pointsStr == null || pointsStr.isEmpty()) {
                        continue;
                    }

                    try {
                        JsonNode pointsNode = objectMapper.readTree(pointsStr);
                        if (!pointsNode.isArray() || pointsNode.size() < 2) {
                            continue;
                        }

                        String regionType = (String) region.get("region_type");
                        if (isPointInRegion(bboxCenterX, bboxCenterY, pointsNode, regionType)) {
                            String regionName = (String) region.get("region_name");
                            log.info("告警匹配到检测区域: deviceId={}, regionName={}", deviceId, regionName);
                            return regionName;
                        }
                    } catch (Exception e) {
                        log.warn("解析区域坐标失败: regionId={}, error={}", region.get("id"), e.getMessage());
                    }
                }

                // 没有匹配到任何区域，但配置了区域，返回null表示不通过
                log.info("告警未匹配到任何检测区域: deviceId={}, bbox=[{},{},{},{}]", deviceId, x1, y1, x2, y2);
                return null;
            } finally {
                // 恢复数据源
                DynamicDataSourceContextHolder.clear();
            }

        } catch (Exception e) {
            log.error("检查告警区域失败: deviceId={}, error={}", 
                    notificationMessage != null ? notificationMessage.getDeviceId() : null, e.getMessage(), e);
            // 出错时默认通过，避免影响正常流程
            return "";
        }
    }

    /**
     * 检查是否配置了检测区域
     * 使用DynamicDataSourceContextHolder切换到VIDEO数据库
     */
    private boolean hasDetectionRegions(String deviceId) {
        try {
            if (jdbcTemplate == null) {
                return false;
            }
            // 切换到video数据源
            DynamicDataSourceContextHolder.push("video");
            try {
                String sql = "SELECT COUNT(*) FROM device_detection_region WHERE device_id = ? AND is_enabled = true";
                Integer count = jdbcTemplate.queryForObject(sql, Integer.class, deviceId);
                return count != null && count > 0;
            } finally {
                // 恢复数据源
                DynamicDataSourceContextHolder.clear();
            }
        } catch (Exception e) {
            log.warn("检查检测区域配置失败: deviceId={}, error={}", deviceId, e.getMessage());
            return false;
        }
    }

    /**
     * 判断点是否在区域内
     */
    private boolean isPointInRegion(double x, double y, JsonNode pointsNode, String regionType) {
        if (pointsNode == null || !pointsNode.isArray() || pointsNode.size() < 2) {
            return false;
        }

        if ("polygon".equals(regionType)) {
            // 多边形区域：使用射线法判断点是否在多边形内
            return isPointInPolygon(x, y, pointsNode);
        } else if ("line".equals(regionType)) {
            // 线条区域：简化为判断点是否在多边形内（可以扩展为更精确的线段判断）
            return isPointInPolygon(x, y, pointsNode);
        } else {
            log.warn("未知的区域类型: {}", regionType);
            return false;
        }
    }

    /**
     * 使用射线法判断点是否在多边形内
     */
    private boolean isPointInPolygon(double x, double y, JsonNode polygon) {
        if (polygon == null || !polygon.isArray() || polygon.size() < 3) {
            return false;
        }

        boolean inside = false;
        int j = polygon.size() - 1;

        for (int i = 0; i < polygon.size(); i++) {
            JsonNode pi = polygon.get(i);
            JsonNode pj = polygon.get(j);

            double xi = pi.has("x") ? pi.get("x").asDouble() : (pi.isArray() ? pi.get(0).asDouble() : 0);
            double yi = pi.has("y") ? pi.get("y").asDouble() : (pi.isArray() ? pi.get(1).asDouble() : 0);
            double xj = pj.has("x") ? pj.get("x").asDouble() : (pj.isArray() ? pj.get(0).asDouble() : 0);
            double yj = pj.has("y") ? pj.get("y").asDouble() : (pj.isArray() ? pj.get(1).asDouble() : 0);

            if (((yi > y) != (yj > y)) && (x < (xj - xi) * (y - yi) / (yj - yi) + xi)) {
                inside = !inside;
            }
            j = i;
        }

        return inside;
    }

    /**
     * 获取算法任务的模型ID列表
     * 使用DynamicDataSourceContextHolder切换到VIDEO数据库
     */
    private List<Integer> getAlgorithmTaskModelIds(String deviceId) {
        try {
            if (jdbcTemplate == null) {
                return null;
            }
            // 切换到video数据源
            DynamicDataSourceContextHolder.push("video");
            try {
                String sql = "SELECT at.model_ids " +
                        "FROM algorithm_task at " +
                        "INNER JOIN algorithm_task_device atd ON at.id = atd.task_id " +
                        "WHERE atd.device_id = ? AND at.alert_event_enabled = true AND at.is_enabled = true " +
                        "LIMIT 1";
                String modelIdsStr = jdbcTemplate.queryForObject(sql, String.class, deviceId);
                if (modelIdsStr == null || modelIdsStr.isEmpty()) {
                    return null;
                }
                JsonNode modelIdsNode = objectMapper.readTree(modelIdsStr);
                if (modelIdsNode.isArray()) {
                    return objectMapper.convertValue(modelIdsNode, 
                            objectMapper.getTypeFactory().constructCollectionType(List.class, Integer.class));
                }
                return null;
            } finally {
                // 恢复数据源
                DynamicDataSourceContextHolder.clear();
            }
        } catch (Exception e) {
            log.warn("获取算法任务模型ID列表失败: deviceId={}, error={}", deviceId, e.getMessage());
            return null;
        }
    }

    /**
     * 检查是否在布防时段内
     * 使用DynamicDataSourceContextHolder切换到VIDEO数据库
     */
    private boolean checkDefenseSchedule(String deviceId, String alertTimeStr) {
        try {
            if (jdbcTemplate == null) {
                log.warn("JdbcTemplate不可用，跳过布防时段检测");
                return true; // 默认通过
            }

            // 切换到video数据源
            DynamicDataSourceContextHolder.push("video");
            try {
                // 获取设备的算法任务
                String sql = "SELECT at.defense_mode, at.defense_schedule " +
                        "FROM algorithm_task at " +
                        "INNER JOIN algorithm_task_device atd ON at.id = atd.task_id " +
                        "WHERE atd.device_id = ? AND at.alert_event_enabled = true AND at.is_enabled = true " +
                        "LIMIT 1";
                Map<String, Object> task = jdbcTemplate.queryForMap(sql, deviceId);

                if (task == null || task.isEmpty()) {
                    return true; // 没有算法任务，默认通过
                }

                String defenseMode = (String) task.get("defense_mode");
                if ("full".equals(defenseMode)) {
                    // 全防模式：全天布防
                    return true;
                }

                String defenseScheduleStr = (String) task.get("defense_schedule");
                if (defenseScheduleStr == null || defenseScheduleStr.isEmpty()) {
                    return true; // 没有配置布防时段，默认通过
                }

                // 解析布防时段配置
                JsonNode scheduleNode = objectMapper.readTree(defenseScheduleStr);
                if (!scheduleNode.isArray() || scheduleNode.size() != 7) {
                    log.warn("布防时段配置格式错误");
                    return true;
                }

                // 解析告警时间
                LocalDateTime alertTime;
                if (StringUtils.hasText(alertTimeStr)) {
                    try {
                        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
                        alertTime = LocalDateTime.parse(alertTimeStr, formatter);
                    } catch (Exception e) {
                        log.warn("解析告警时间失败，使用当前时间: timeStr={}, error={}", alertTimeStr, e.getMessage());
                        alertTime = LocalDateTime.now();
                    }
                } else {
                    alertTime = LocalDateTime.now();
                }

                // 获取当前是星期几（0=周一，6=周日）
                int weekday = alertTime.getDayOfWeek().getValue() - 1; // Java的DayOfWeek: 1=Monday, 7=Sunday
                // 获取当前小时
                int hour = alertTime.getHour();

                // 检查该时段是否布防
                if (weekday < scheduleNode.size() && hour < scheduleNode.get(weekday).size()) {
                    int isDefense = scheduleNode.get(weekday).get(hour).asInt();
                    if (isDefense != 1) {
                        log.info("告警不在布防时段内: deviceId={}, weekday={}, hour={}", deviceId, weekday, hour);
                        return false;
                    }
                }

                return true;
            } finally {
                // 恢复数据源
                DynamicDataSourceContextHolder.clear();
            }

        } catch (Exception e) {
            log.error("检查布防时段失败: deviceId={}, error={}", deviceId, e.getMessage(), e);
            // 出错时默认通过，避免影响正常流程
            return true;
        }
    }
}

