package com.basiclab.iot.sink.service.impl;

import com.baomidou.dynamic.datasource.toolkit.DynamicDataSourceContextHolder;
import com.basiclab.iot.common.core.util.TenantUtils;
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
import org.springframework.beans.factory.annotation.Value;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.FileInputStream;
import java.net.URLDecoder;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDateTime;
import java.time.OffsetDateTime;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.HashMap;
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

    /** 与 realtime_algorithm_service、docker 挂载约定一致（ALERT_IMAGES_DIR=/app/alert_images） */
    private static final ZoneId ALERT_EVENT_ZONE = ZoneId.of("Asia/Shanghai");

    @Autowired(required = false)
    private MinioClient minioClient;

    @Autowired(required = false)
    private AlertMapper alertMapper;

    @Autowired(required = false)
    private ObjectMapper objectMapper;

    @Autowired(required = false)
    private JdbcTemplate jdbcTemplate;

    /**
     * 告警图片根前缀（默认 /app）。算法若写相对路径或路径被截断时，可辅助拼接可读路径。
     */
    @Value("${alert.images.base-dir:/app}")
    private String alertImagesBaseDir;

    // MinIO清空后的等待时间控制（兼容Python端逻辑）
    private volatile long lastMinioCleanupTime = 0; // 上次清空MinIO的时间戳
    private static final int MINIO_CLEANUP_WAIT_SECONDS = 5; // 清空后等待5秒才能再次上传
    private final ReentrantLock minioCleanupLock = new ReentrantLock(); // 保护清空时间变量的锁

    @Override
    public Integer processAlert(AlertNotificationMessage notificationMessage) {
        // Kafka 消费线程无 HTTP 租户上下文；alert 表在 VIDEO 库且无 tenant_id 列
        final Integer[] result = new Integer[1];
        TenantUtils.executeIgnore(() -> result[0] = processAlertInternal(notificationMessage));
        return result[0];
    }

    private Integer processAlertInternal(AlertNotificationMessage notificationMessage) {
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

            // 检查是否在布防时段内
            if (!checkDefenseSchedule(notificationMessage.getTaskId(), deviceId, alert.getTime())) {
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
                // 同步写入抓拍空间元数据，否则「抓拍图库」为空（算法告警 Tab 仍可读 alert 表）
                upsertSnapImage(deviceId, minioPath, "algorithm");
                // 将 MinIO 下载地址回写到消息，使下游通知（HTTP/Webhook 等）推送可访问的图片 URL，而非本地磁盘路径
                alert.setImagePath(minioPath);
                log.debug("告警 {} 图片路径已更新: {}", alertId, minioPath);
            } else if (minioPath == null) {
                // uploadImageToMinio 已在内部区分：文件不存在、未就绪、桶创建失败、putObject 异常等；此处勿统称「MinIO 失败」以免误导
                log.warn("告警 {} 未写入 MinIO 访问路径(image_url 未更新): imagePath={}, minioClient已初始化={}。"
                                + "请结合上一条相关 WARN：若为「告警图片文件不存在/不可用」则多为目录挂载、Kafka 积压或算法侧清理导致，未必是 MinIO；"
                                + "若无前置 WARN 且怀疑对象存储，再检查 iot-sink 告警目录挂载、MINIO_URL、桶 alert-images 权限",
                        alertId, imagePath, minioClient != null);
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

    @Override
    public Integer processSnapshotAlert(AlertNotificationMessage notificationMessage) {
        final Integer[] result = new Integer[1];
        TenantUtils.executeIgnore(() -> result[0] = processSnapshotAlertInternal(notificationMessage));
        return result[0];
    }

    private Integer processSnapshotAlertInternal(AlertNotificationMessage notificationMessage) {
        try {
            if (notificationMessage == null || notificationMessage.getAlert() == null) {
                log.warn("抓拍算法任务告警消息为空，跳过处理");
                return null;
            }

            AlertNotificationMessage.AlertInfo alert = notificationMessage.getAlert();
            String deviceId = notificationMessage.getDeviceId();
            String deviceName = notificationMessage.getDeviceName();
            String imagePath = alert.getImagePath();

            log.info("开始处理抓拍算法任务告警: deviceId={}, deviceName={}, imagePath={}", 
                    deviceId, deviceName, imagePath);

            // 检查是否在布防时段内
            if (!checkDefenseSchedule(notificationMessage.getTaskId(), deviceId, alert.getTime())) {
                log.info("抓拍算法任务告警不在布防时段内，跳过处理: deviceId={}", deviceId);
                return null;
            }

            // 确保information中包含task_type='snapshot'（抓拍算法任务）
            Object information = alert.getInformation();
            if (information != null) {
                try {
                    Map<String, Object> informationMap = null;
                    if (information instanceof String) {
                        // 如果是字符串，尝试解析为JSON对象
                        if (objectMapper != null) {
                            informationMap = objectMapper.readValue((String) information, Map.class);
                        }
                    } else if (information instanceof Map) {
                        informationMap = (Map<String, Object>) information;
                    }
                    
                    // 如果成功解析为Map，确保包含task_type='snapshot'
                    if (informationMap != null) {
                        informationMap.put("task_type", "snapshot");
                        // 更新alert中的information
                        alert.setInformation(informationMap);
                    } else if (information instanceof String) {
                        // 如果解析失败，创建一个新的Map包含task_type
                        informationMap = new HashMap<>();
                        informationMap.put("task_type", "snapshot");
                        informationMap.put("original", information);
                        alert.setInformation(informationMap);
                    }
                } catch (Exception e) {
                    log.warn("处理抓拍算法任务告警的information字段失败，将使用原始值: {}", e.getMessage());
                    // 如果处理失败，创建一个新的Map包含task_type
                    Map<String, Object> informationMap = new HashMap<>();
                    informationMap.put("task_type", "snapshot");
                    if (information != null) {
                        informationMap.put("original", information.toString());
                    }
                    alert.setInformation(informationMap);
                }
            } else {
                // 如果information为空，创建一个包含task_type的Map
                Map<String, Object> informationMap = new HashMap<>();
                informationMap.put("task_type", "snapshot");
                alert.setInformation(informationMap);
            }

            // 获取告警ID（如果消息中已有alertId，说明Python端已插入数据库）
            Integer alertId = notificationMessage.getAlertId();
            
            // 如果没有alertId，需要先存储告警到数据库（无论是否开启通知，都要存储）
            if (alertId == null) {
                alertId = saveAlertToDatabase(notificationMessage);
                if (alertId == null) {
                    log.warn("抓拍算法任务告警存储到数据库失败，跳过后续处理");
                    return null;
                }
                log.info("抓拍算法任务告警已存储到数据库: alertId={}", alertId);
            }
            
            // 如果没有图片路径，跳过图片上传
            if (imagePath == null || imagePath.isEmpty()) {
                log.debug("抓拍算法任务告警 {} 没有图片路径，跳过图片上传", alertId);
                return alertId;
            }

            // 检查是否在清空后的等待期内（在数据库查询前检查，避免不必要的操作）
            if (isInCleanupWaitPeriod()) {
                log.debug("抓拍算法任务告警 {} 图片上传跳过：MinIO清空后等待期内", alertId);
                return alertId;
            }

            // 上传图片到MinIO抓拍空间（无论是否开启通知，都要上传）
            String minioPath = uploadImageToSnapSpace(imagePath, alertId, deviceId);
            
            if (minioPath != null && alertId != null) {
                // 更新数据库中的图片路径
                updateAlertImagePath(alertId, minioPath);
                // 同步写入抓拍图库元数据（snap_image），与 MinIO 对象对应
                upsertSnapImage(deviceId, minioPath, "snap");
                // 将 MinIO 下载地址回写到消息，使下游通知（HTTP/Webhook 等）推送可访问的图片 URL，而非本地磁盘路径
                alert.setImagePath(minioPath);
                log.debug("抓拍算法任务告警 {} 图片路径已更新: {}", alertId, minioPath);
            } else if (minioPath == null) {
                log.warn("抓拍算法任务告警 {} 图片上传失败，保留原始路径: {}", alertId, imagePath);
            }

            log.info("抓拍算法任务告警处理完成: alertId={}", alertId);
            return alertId;

        } catch (Exception e) {
            log.error("处理抓拍算法任务告警失败: deviceId={}, error={}", 
                    notificationMessage != null ? notificationMessage.getDeviceId() : null, 
                    e.getMessage(), e);
            // 不抛出异常，避免影响消息确认
            return null;
        }
    }

    /**
     * 解析告警图片在本机的可读路径：先按消息中的路径；若为相对路径则与 alert.images.base-dir（默认 /app）拼接。
     * 不使用「去掉首字符 / 再拼到 base 下」的方式处理绝对路径，避免 /app/alert_images 被错解析为 /app/app/alert_images。
     */
    private File resolveLocalAlertImageFile(String imagePath) {
        if (!StringUtils.hasText(imagePath)) {
            return new File("");
        }
        String trimmed = imagePath.trim();
        Path path = Paths.get(trimmed);
        try {
            if (Files.isRegularFile(path)) {
                return path.toFile();
            }
        } catch (Exception ignored) {
            // 路径非法等：交给后续返回默认 File 供上层 exists() 判断
        }

        String base = StringUtils.hasText(alertImagesBaseDir) ? alertImagesBaseDir.trim() : "/app";
        while (base.endsWith("/") || base.endsWith("\\")) {
            base = base.substring(0, base.length() - 1);
        }
        Path basePath = Paths.get(base);

        if (!path.isAbsolute()) {
            Path resolved = basePath.resolve(path).normalize();
            try {
                if (Files.isRegularFile(resolved)) {
                    log.debug("告警图片路径解析成功: raw={}, resolved={}", imagePath, resolved);
                    return resolved.toFile();
                }
            } catch (Exception ignored) {
            }
        }

        return path.toFile();
    }

    /**
     * Python 与 realtime 算法约定：time 为 Asia/Shanghai 墙钟（无时区后缀）；入库为带 +08 的 OffsetDateTime，避免 PG timestamptz 等组合产生 ±8h。
     */
    private OffsetDateTime parseAlertEventTime(String timeStr) {
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
        if (!StringUtils.hasText(timeStr)) {
            return OffsetDateTime.now(ALERT_EVENT_ZONE);
        }
        try {
            LocalDateTime naive = LocalDateTime.parse(timeStr.trim(), formatter);
            return naive.atZone(ALERT_EVENT_ZONE).toOffsetDateTime();
        } catch (Exception e) {
            log.warn("解析告警时间失败，使用当前时间(Asia/Shanghai): timeStr={}, error={}", timeStr, e.getMessage());
            return OffsetDateTime.now(ALERT_EVENT_ZONE);
        }
    }

    /**
     * 上传图片到MinIO的抓拍空间存储桶
     * 根据device_id查询snap_space获取bucket_name
     * 如果最近5秒内清空过MinIO，将跳过上传
     * 
     * @param imagePath 本地图片路径
     * @param alertId 告警ID
     * @param deviceId 设备ID
     * @return MinIO中的对象路径，如果失败返回null
     */
    private String uploadImageToSnapSpace(String imagePath, Integer alertId, String deviceId) {
        // 检查是否在清空后的等待期内
        if (isInCleanupWaitPeriod()) {
            return null;
        }

        if (minioClient == null) {
            log.warn("MinIO客户端不可用，跳过图片上传: imagePath={}", imagePath);
            return null;
        }

        if (jdbcTemplate == null) {
            log.warn("JdbcTemplate不可用，无法查询抓拍空间，跳过图片上传: imagePath={}", imagePath);
            return null;
        }

        try {
            File imageFile = resolveLocalAlertImageFile(imagePath);
            if (!imageFile.exists() || !imageFile.isFile()) {
                log.warn("抓拍图片文件不存在: imagePath={}, resolved={}", imagePath, imageFile.getAbsolutePath());
                return null;
            }

            // 等待文件写入完成（文件大小稳定）
            long fileSize = waitForFileStable(imageFile);
            if (fileSize <= 0) {
                log.warn("抓拍图片文件不可用或大小为0: imagePath={} (等待文件稳定后)", imagePath);
                return null;
            }

            // 查询设备的抓拍空间bucket_name（从VIDEO数据库的snap_space表）
            String bucketName = null;
            try {
                // 使用@DS("video")注解切换到VIDEO数据库
                DynamicDataSourceContextHolder.push("video");
                try {
                    String sql = "SELECT bucket_name FROM snap_space WHERE device_id = ? LIMIT 1";
                    List<String> results = jdbcTemplate.queryForList(sql, String.class, deviceId);
                    if (results != null && !results.isEmpty()) {
                        bucketName = results.get(0);
                        log.info("查询到设备的抓拍空间bucket: deviceId={}, bucketName={}", deviceId, bucketName);
                    } else {
                        log.warn("设备没有关联的抓拍空间: deviceId={}", deviceId);
                        return null;
                    }
                } finally {
                    DynamicDataSourceContextHolder.clear();
                }
            } catch (Exception e) {
                log.error("查询抓拍空间失败: deviceId={}, error={}", deviceId, e.getMessage(), e);
                return null;
            }

            if (bucketName == null || bucketName.isEmpty()) {
                log.warn("设备没有配置抓拍空间bucket: deviceId={}", deviceId);
                return null;
            }

            // 确保存储桶存在
            try {
                boolean exists = minioClient.bucketExists(BucketExistsArgs.builder().bucket(bucketName).build());
                if (!exists) {
                    minioClient.makeBucket(MakeBucketArgs.builder().bucket(bucketName).build());
                    log.info("创建MinIO抓拍空间存储桶: {}", bucketName);
                }
            } catch (Exception e) {
                log.error("检查或创建MinIO抓拍空间存储桶失败: bucket={}, error={}", bucketName, e.getMessage(), e);
                return null;
            }

            // 生成对象名称：使用设备ID目录结构，格式：deviceId/YYYY/MM/DD/snapshot_{alertId}_{timestamp}.jpg
            String fileName = imageFile.getName();
            String fileExt = "";
            int lastDotIndex = fileName.lastIndexOf('.');
            if (lastDotIndex > 0) {
                fileExt = fileName.substring(lastDotIndex);
            } else {
                fileExt = ".jpg"; // 默认扩展名
            }

            LocalDateTime now = LocalDateTime.now(ALERT_EVENT_ZONE);
            String dateDir = now.format(DateTimeFormatter.ofPattern("yyyy/MM/dd"));
            String timestamp = now.format(DateTimeFormatter.ofPattern("yyyyMMddHHmmss"));
            String objectName = String.format("%s/%s/snapshot_%s_%s%s", 
                    deviceId,
                    dateDir, 
                    alertId != null ? alertId : "unknown",
                    timestamp,
                    fileExt);

            // 读取文件内容到内存，确保文件完整性（复用uploadImageToMinio的逻辑）
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
                            log.debug("抓拍图片文件读取大小不匹配（重试 {}/{}）: 期望 {} 字节，实际读取 {} 字节，等待文件稳定后重试...",
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
                            log.warn("抓拍图片文件读取不完整（已重试 {} 次）: 期望 {} 字节，实际读取 {} 字节",
                                    maxRetries, fileSize, totalBytesRead);
                            return null;
                        }
                    }
                } catch (Exception e) {
                    retryCount++;
                    if (retryCount < maxRetries) {
                        log.debug("抓拍图片文件读取失败（重试 {}/{}）: {}，等待后重试...",
                                retryCount, maxRetries, e.getMessage());
                        Thread.sleep(200);
                    } else {
                        log.warn("抓拍图片文件读取失败（已重试 {} 次）: {}", maxRetries, e.getMessage());
                        return null;
                    }
                }
            }

            if (fileContent == null || fileContent.length != fileSize) {
                log.warn("抓拍图片文件读取失败: imagePath={}", imagePath);
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
                                .stream(dataStream, fileSize, -1)
                                .contentType(contentType)
                                .build());
                
                // 构建MinIO路径（格式：/api/v1/buckets/{bucketName}/objects/download?prefix={objectName}）
                String minioPath = String.format("/api/v1/buckets/%s/objects/download?prefix=%s", 
                        bucketName, 
                        URLEncoder.encode(objectName, StandardCharsets.UTF_8.toString()));
                
                log.info("抓拍图片上传到MinIO成功: bucket={}, object={}, minioPath={}", 
                        bucketName, objectName, minioPath);
                
                // 上传成功后删除本地文件，避免撑爆硬盘
                deleteLocalImageFile(imageFile);
                
                return minioPath;
            }

        } catch (Exception e) {
            log.error("上传抓拍图片到MinIO失败: imagePath={}, deviceId={}, error={}", 
                    imagePath, deviceId, e.getMessage(), e);
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
            log.debug("告警图片上传跳过：MinIO 清空后等待期内，imagePath={}", imagePath);
            return null;
        }

        if (minioClient == null) {
            log.warn("MinIO客户端不可用，跳过图片上传: imagePath={}", imagePath);
            return null;
        }

        try {
            File imageFile = resolveLocalAlertImageFile(imagePath);
            if (!imageFile.exists() || !imageFile.isFile()) {
                log.warn("告警图片文件不存在: imagePath={}, resolved={}", imagePath, imageFile.getAbsolutePath());
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

            LocalDateTime now = LocalDateTime.now(ALERT_EVENT_ZONE);
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
                
                // 上传成功后删除本地文件，避免撑爆硬盘
                deleteLocalImageFile(imageFile);
                
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
            throw new IllegalStateException("AlertMapper不可用，无法存储告警");
        }

        try {
            AlertNotificationMessage.AlertInfo alert = notificationMessage.getAlert();
            String correlationId = StringUtils.hasText(notificationMessage.getCorrelationId())
                    ? notificationMessage.getCorrelationId() : notificationMessage.getEventId();
            if (StringUtils.hasText(correlationId)) {
                AlertDO existingAlert = alertMapper.selectByCorrelationId(correlationId.trim());
                if (existingAlert != null && existingAlert.getId() != null) {
                    log.info("告警幂等命中: correlationId={}, alertId={}", correlationId, existingAlert.getId());
                    return existingAlert.getId();
                }
            }
            
            // 构建AlertDO对象
            AlertDO alertDO = new AlertDO();
            alertDO.setObject(alert.getObject());
            alertDO.setEvent(alert.getEvent());
            alertDO.setRegion(alert.getRegion());
            
            // 处理information字段（可能是对象，需要转换为JSON字符串）
            Object information = alert.getInformation();
            Map<String, Object> informationMap = null;
            
            if (information != null) {
                if (information instanceof String) {
                    // 如果是字符串，尝试解析为JSON对象
                    try {
                        if (objectMapper != null) {
                            informationMap = objectMapper.readValue((String) information, Map.class);
                        } else {
                            // 如果没有objectMapper，直接使用字符串
                            alertDO.setInformation((String) information);
                        }
                    } catch (Exception e) {
                        // 解析失败，直接使用字符串
                        alertDO.setInformation((String) information);
                    }
                } else if (information instanceof Map) {
                    informationMap = (Map<String, Object>) information;
                } else {
                    // 其他类型，尝试转换为JSON字符串
                    try {
                        if (objectMapper != null) {
                            String jsonStr = objectMapper.writeValueAsString(information);
                            informationMap = objectMapper.readValue(jsonStr, Map.class);
                        } else {
                            alertDO.setInformation(information.toString());
                        }
                    } catch (Exception e) {
                        log.warn("转换information为JSON失败，使用toString: {}", e.getMessage());
                        alertDO.setInformation(information.toString());
                    }
                }
            } else {
                // 如果information为空，创建一个新的Map
                informationMap = new HashMap<>();
            }
            
            // 确保information中包含task_type
            if (informationMap != null) {
                // 如果information中没有task_type，尝试从其他地方获取
                if (!informationMap.containsKey("task_type")) {
                    // 检查是否是抓拍算法任务告警（通过方法名或消息来源判断）
                    // 如果是在processSnapshotAlert中调用，应该已经包含task_type
                    // 如果没有，默认为'realtime'（实时算法任务）
                    // 注意：抓拍算法任务的task_type应该在Python端就已经设置好了
                    informationMap.put("task_type", "realtime");
                } else {
                    // 如果已经有task_type，确保值正确（'snapshot' 或 'realtime'）
                    String taskType = (String) informationMap.get("task_type");
                    if (taskType == null || (!taskType.equals("snapshot") && !taskType.equals("realtime"))) {
                        // 如果task_type值不正确，根据消息来源判断
                        // 这里可以根据实际情况调整逻辑
                        log.warn("告警信息中的task_type值不正确: {}, 将保持原值", taskType);
                    }
                }
                
                // 将Map转换为JSON字符串
                try {
                    if (objectMapper != null) {
                        alertDO.setInformation(objectMapper.writeValueAsString(informationMap));
                    } else {
                        alertDO.setInformation(informationMap.toString());
                    }
                } catch (Exception e) {
                    log.warn("转换information Map为JSON失败: {}", e.getMessage());
                    alertDO.setInformation(informationMap.toString());
                }
            }
            
            // 处理时间字段（与 Python BEIJING_TZ 输出语义一致：东八区墙钟）
            alertDO.setTime(parseAlertEventTime(alert.getTime()));
            
            alertDO.setDeviceId(notificationMessage.getDeviceId());
            alertDO.setDeviceName(notificationMessage.getDeviceName());
            alertDO.setImagePath(alert.getImagePath());
            alertDO.setRecordPath(alert.getRecordPath());
            
            // 提取并设置 task_type（优先从 alert.taskType 获取，如果没有则从 information 中提取）
            String taskType = alert.getTaskType();
            if (taskType == null || taskType.isEmpty()) {
                // 如果 alert.taskType 为空，尝试从 information 中提取
                if (informationMap != null && informationMap.containsKey("task_type")) {
                    taskType = (String) informationMap.get("task_type");
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
            
            // 保存通知人信息
            List<Map<String, Object>> notifyUsers = notificationMessage.getNotifyUsers();
            if (notifyUsers != null && !notifyUsers.isEmpty()) {
                try {
                    if (objectMapper != null) {
                        alertDO.setNotifyUsers(objectMapper.writeValueAsString(notifyUsers));
                    } else {
                        alertDO.setNotifyUsers(notifyUsers.toString());
                    }
                } catch (Exception e) {
                    log.warn("转换notifyUsers为JSON失败: {}", e.getMessage());
                    alertDO.setNotifyUsers(notifyUsers.toString());
                }
            }
            
            // 保存通知渠道配置
            List<Map<String, Object>> channels = notificationMessage.getChannels();
            if (channels != null && !channels.isEmpty()) {
                try {
                    if (objectMapper != null) {
                        alertDO.setChannels(objectMapper.writeValueAsString(channels));
                    } else {
                        alertDO.setChannels(channels.toString());
                    }
                } catch (Exception e) {
                    log.warn("转换channels为JSON失败: {}", e.getMessage());
                    alertDO.setChannels(channels.toString());
                }
            }
            
            // 设置通知发送状态（初始为false，后续由iot-message服务更新）
            alertDO.setNotificationSent(false);
            alertDO.setNotificationSentTime(null);
            alertDO.setCorrelationId(StringUtils.hasText(correlationId) ? correlationId.trim() : null);
            alertDO.setTaskId(notificationMessage.getTaskId());
            alertDO.setTaskName(notificationMessage.getTaskName());
            alertDO.setEdgeNodeId(notificationMessage.getEdgeNodeId());
            alertDO.setEdgeNodeName(notificationMessage.getEdgeNodeName());
            alertDO.setEdgeNodeHost(notificationMessage.getEdgeNodeHost());
            alertDO.setNodeId(notificationMessage.getNodeId());
            
            // 插入数据库（使用@DS("video")注解的Mapper会自动切换到VIDEO数据库）
            int result = alertMapper.insert(alertDO);
            if (result > 0 && alertDO.getId() != null) {
                log.info("告警存储成功: alertId={}, deviceId={}", alertDO.getId(), alertDO.getDeviceId());
                return alertDO.getId();
            } else {
                if (StringUtils.hasText(correlationId)) {
                    AlertDO existingAlert = alertMapper.selectByCorrelationId(correlationId.trim());
                    if (existingAlert != null && existingAlert.getId() != null) {
                        log.info("并发告警幂等命中: correlationId={}, alertId={}", correlationId, existingAlert.getId());
                        return existingAlert.getId();
                    }
                }
                throw new IllegalStateException("告警写入未生效且未命中幂等记录");
            }
            
        } catch (Exception e) {
            log.error("存储告警到数据库失败: deviceId={}, error={}", 
                    notificationMessage.getDeviceId(), e.getMessage(), e);
            throw new IllegalStateException("存储告警到数据库失败", e);
        }
    }

    /**
     * 将 MinIO 下载地址写入 alert.image_url（与库表字段一致；方法名 updateImagePath 为历史保留）
     * 使用@DS("video")注解切换到VIDEO数据库
     *
     * @param alertId 告警ID
     * @param minioPath MinIO 对象下载 API 路径
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
     * 将告警/抓拍图片登记到 snap_image，供抓拍空间「抓拍图库」分页查询。
     * minioPath 形如 /api/v1/buckets/{bucket}/objects/download?prefix={objectName}
     */
    private void upsertSnapImage(String deviceId, String minioPath, String source) {
        if (jdbcTemplate == null || !StringUtils.hasText(deviceId) || !StringUtils.hasText(minioPath)) {
            return;
        }
        try {
            String bucketName = null;
            String objectName = null;
            // /api/v1/buckets/{bucket}/objects/download?prefix=...
            String marker = "/api/v1/buckets/";
            int bStart = minioPath.indexOf(marker);
            if (bStart >= 0) {
                int bEnd = minioPath.indexOf('/', bStart + marker.length());
                if (bEnd > bStart) {
                    bucketName = minioPath.substring(bStart + marker.length(), bEnd);
                }
            }
            int pIdx = minioPath.indexOf("prefix=");
            if (pIdx >= 0) {
                String encoded = minioPath.substring(pIdx + "prefix=".length());
                int amp = encoded.indexOf('&');
                if (amp >= 0) {
                    encoded = encoded.substring(0, amp);
                }
                objectName = URLDecoder.decode(encoded, StandardCharsets.UTF_8);
            }
            if (!StringUtils.hasText(bucketName) || !StringUtils.hasText(objectName)) {
                log.warn("无法从 minioPath 解析 bucket/object，跳过 snap_image: {}", minioPath);
                return;
            }

            DynamicDataSourceContextHolder.push("video");
            Integer spaceId = jdbcTemplate.query(
                    "SELECT id FROM snap_space WHERE device_id = ? LIMIT 1",
                    rs -> rs.next() ? rs.getInt(1) : null,
                    deviceId);
            if (spaceId == null) {
                log.warn("设备无抓拍空间，跳过 snap_image device={}", deviceId);
                return;
            }
            String filename = objectName.contains("/")
                    ? objectName.substring(objectName.lastIndexOf('/') + 1)
                    : objectName;
            Integer existing = jdbcTemplate.query(
                    "SELECT id FROM snap_image WHERE bucket_name = ? AND object_name = ? LIMIT 1",
                    rs -> rs.next() ? rs.getInt(1) : null,
                    bucketName, objectName);
            if (existing != null) {
                jdbcTemplate.update(
                        "UPDATE snap_image SET space_id = ?, device_id = ?, filename = ?, url = ?, source = ?, "
                                + "captured_at = COALESCE(captured_at, NOW()) WHERE id = ?",
                        spaceId, deviceId, filename, minioPath, source, existing);
            } else {
                jdbcTemplate.update(
                        "INSERT INTO snap_image (space_id, device_id, object_name, bucket_name, filename, "
                                + "content_type, url, captured_at, source, created_at) "
                                + "VALUES (?, ?, ?, ?, ?, ?, ?, NOW(), ?, NOW())",
                        spaceId, deviceId, objectName, bucketName, filename,
                        "image/jpeg", minioPath, source);
            }
        } catch (Exception e) {
            log.warn("写入 snap_image 失败 device={}: {}", deviceId, e.getMessage());
        } finally {
            DynamicDataSourceContextHolder.clear();
        }
    }

    /**
     * 删除本地告警图片文件
     * 上传成功后调用，避免本地文件堆积撑爆硬盘
     * 
     * @param imageFile 本地图片文件对象
     */
    private void deleteLocalImageFile(File imageFile) {
        if (imageFile == null) {
            return;
        }
        
        try {
            if (imageFile.exists() && imageFile.isFile()) {
                boolean deleted = imageFile.delete();
                if (deleted) {
                    log.info("本地告警图片已删除: {}", imageFile.getAbsolutePath());
                } else {
                    log.warn("本地告警图片删除失败（文件可能被占用）: {}", imageFile.getAbsolutePath());
                }
            } else {
                log.debug("本地告警图片文件不存在，无需删除: {}", imageFile.getAbsolutePath());
            }
        } catch (Exception e) {
            // 删除失败不影响主流程，只记录日志
            log.warn("删除本地告警图片文件异常: path={}, error={}", 
                    imageFile.getAbsolutePath(), e.getMessage());
        }
    }

    /**
     * 检查是否在布防时段内
     * 使用DynamicDataSourceContextHolder切换到VIDEO数据库
     */
    private boolean checkDefenseSchedule(Integer taskId, String deviceId, String alertTimeStr) {
        try {
            if (alertMapper == null) {
                log.warn("AlertMapper不可用，跳过布防时段检测");
                // 默认通过，避免基础设施异常阻断告警主链路。
                return true;
            }

            // 优先按消息携带的任务ID读取布防配置，旧消息才退回设备唯一任务。
            Map<String, Object> task = alertMapper.selectDefenseConfig(taskId, deviceId);

            if (task == null || task.isEmpty()) {
                // 没有匹配任务时默认通过。
                return true;
            }

            String defenseMode = (String) task.get("defense_mode");
            if ("full".equals(defenseMode)) {
                // 全防模式：全天布防
                return true;
            }

            String defenseScheduleStr = (String) task.get("defense_schedule");
            if (defenseScheduleStr == null || defenseScheduleStr.isEmpty()) {
                // 没有配置布防时段时默认通过。
                return true;
            }

            // 解析布防时段配置
            JsonNode scheduleNode = objectMapper.readTree(defenseScheduleStr);
            if (!scheduleNode.isArray() || scheduleNode.size() != 7) {
                log.warn("布防时段配置格式错误");
                return true;
            }

            // 解析告警时间（布防按东八区墙钟小时/星期）
            LocalDateTime alertTime;
            if (StringUtils.hasText(alertTimeStr)) {
                try {
                    DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
                    alertTime = LocalDateTime.parse(alertTimeStr.trim(), formatter);
                } catch (Exception e) {
                    log.warn("解析告警时间失败，使用当前时间(Asia/Shanghai): timeStr={}, error={}", alertTimeStr, e.getMessage());
                    alertTime = ZonedDateTime.now(ALERT_EVENT_ZONE).toLocalDateTime();
                }
            } else {
                alertTime = ZonedDateTime.now(ALERT_EVENT_ZONE).toLocalDateTime();
            }

            // 获取当前是星期几（0=周一，6=周日）
            int weekday = alertTime.getDayOfWeek().getValue() - 1;
            // 获取当前小时
            int hour = alertTime.getHour();

            // 检查该时段是否布防
            if (weekday < scheduleNode.size() && hour < scheduleNode.get(weekday).size()) {
                int isDefense = scheduleNode.get(weekday).get(hour).asInt();
                if (isDefense != 1) {
                    log.info("告警不在布防时段内: taskId={}, deviceId={}, weekday={}, hour={}",
                            taskId, deviceId, weekday, hour);
                    return false;
                }
            }

            return true;

        } catch (Exception e) {
            log.error("检查布防时段失败: taskId={}, deviceId={}, error={}", taskId, deviceId, e.getMessage(), e);
            // 出错时默认通过，避免影响正常流程
            return true;
        }
    }
}
