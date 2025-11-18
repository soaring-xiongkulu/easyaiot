package com.basiclab.iot.sink.service.data;

import cn.hutool.core.util.StrUtil;
import cn.hutool.json.JSONUtil;
import com.basiclab.iot.common.service.RedisService;
import com.basiclab.iot.sink.enums.IotDeviceTopicEnum;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;
import com.basiclab.iot.sink.util.IotSinkRedisKeyConstants;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.TimeUnit;

/**
 * 设备Redis存储服务
 * <p>
 * 根据不同Topic将设备数据存储到Redis Hash结构中
 * <p>
 * Redis Key格式：使用 {@link IotSinkRedisKeyConstants#buildDeviceDataKey(Long)} 构建
 * Hash字段包括：connect_status, last_online_time, extension, version, tags, shadow, config, ota_progress
 *
 * @author 翱翔的雄库鲁
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class DeviceRedisStorageService {

    /**
     * 数据过期时间：30天（设备数据需要长期保存）
     */
    private static final long EXPIRE_TIME = IotSinkRedisKeyConstants.DEVICE_DATA_EXPIRE_DAYS;
    private static final TimeUnit EXPIRE_TIME_UNIT = TimeUnit.DAYS;

    /**
     * 日期时间格式化器
     */
    private static final DateTimeFormatter DATE_TIME_FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    private final RedisService redisService;

    /**
     * 存储设备数据到Redis
     *
     * @param message   设备消息
     * @param topicEnum Topic枚举
     */
    public void storeDeviceData(IotDeviceMessage message, IotDeviceTopicEnum topicEnum) {
        if (message == null || message.getDeviceId() == null || topicEnum == null) {
            log.warn("[storeDeviceData][消息、设备ID或Topic枚举为空，跳过存储]");
            return;
        }

        try {
            String redisKey = IotSinkRedisKeyConstants.buildDeviceDataKey(message.getDeviceId());

            switch (topicEnum) {
                case PROPERTY_UPSTREAM_REPORT:
                    // 属性上报：更新扩展信息中的属性数据
                    updateDeviceExtension(redisKey, "properties", message.getParams());
                    // 更新连接状态和最后在线时间
                    updateDeviceConnectStatus(redisKey, message);
                    break;

                case PROPERTY_UPSTREAM_DESIRED_SET_ACK:
                case PROPERTY_UPSTREAM_DESIRED_QUERY_RESPONSE:
                    // 属性期望值相关：更新扩展信息
                    updateDeviceExtension(redisKey, "desired", message.getData());
                    break;

                case EVENT_UPSTREAM_REPORT:
                    // 事件上报：更新扩展信息中的事件数据
                    updateDeviceExtension(redisKey, "events", message.getParams());
                    // 更新连接状态和最后在线时间
                    updateDeviceConnectStatus(redisKey, message);
                    break;

                case SERVICE_UPSTREAM_INVOKE_RESPONSE:
                    // 服务调用响应：更新扩展信息中的服务响应数据
                    updateDeviceExtension(redisKey, "serviceResponse", message.getData());
                    break;

                case DEVICE_TAG_UPSTREAM_REPORT:
                    // 标签上报：更新设备标签
                    updateDeviceTags(redisKey, message.getParams());
                    break;

                case DEVICE_TAG_UPSTREAM_DELETE:
                    // 标签删除：更新设备标签
                    updateDeviceTags(redisKey, message.getParams());
                    break;

                case SHADOW_UPSTREAM_REPORT:
                    // 影子上报：更新影子状态
                    updateDeviceShadow(redisKey, message.getParams());
                    break;

                case CONFIG_UPSTREAM_QUERY:
                    // 配置查询：更新配置信息
                    updateDeviceConfig(redisKey, message.getData());
                    break;

                case NTP_UPSTREAM_REQUEST:
                    // NTP请求：更新连接状态和最后在线时间
                    updateDeviceConnectStatus(redisKey, message);
                    break;

                case OTA_UPSTREAM_VERSION_REPORT:
                    // OTA版本上报：更新设备版本
                    updateDeviceVersion(redisKey, message.getParams());
                    break;

                case OTA_UPSTREAM_PROGRESS_REPORT:
                    // OTA进度上报：更新OTA进度
                    updateDeviceOtaProgress(redisKey, message.getParams());
                    break;

                case OTA_UPSTREAM_FIRMWARE_QUERY:
                    // OTA固件查询：更新扩展信息
                    updateDeviceExtension(redisKey, "otaQuery", message.getData());
                    break;

                default:
                    // 默认：只更新连接状态和最后在线时间
                    updateDeviceConnectStatus(redisKey, message);
                    break;
            }

            // 设置过期时间（如果key不存在则设置，如果已存在则更新过期时间）
            redisService.expire(redisKey, EXPIRE_TIME, EXPIRE_TIME_UNIT);

            log.debug("[storeDeviceData][Redis设备数据存储成功，messageId: {}, topic: {}, deviceId: {}]",
                    message.getId(), topicEnum.name(), message.getDeviceId());
        } catch (Exception e) {
            log.error("[storeDeviceData][Redis设备数据存储失败，messageId: {}, topic: {}, deviceId: {}]",
                    message.getId(), topicEnum.name(), message.getDeviceId(), e);
        }
    }

    /**
     * 更新设备连接状态和最后在线时间
     *
     * @param redisKey Redis Key
     * @param message  设备消息
     */
    private void updateDeviceConnectStatus(String redisKey, IotDeviceMessage message) {
        try {
            // 更新连接状态
            redisService.setCacheMapValue(redisKey, IotSinkRedisKeyConstants.DEVICE_DATA_FIELD_CONNECT_STATUS, "ONLINE");

            // 更新最后在线时间
            LocalDateTime lastOnlineTime = message.getReportTime() != null
                    ? message.getReportTime()
                    : LocalDateTime.now();
            String lastOnlineTimeStr = lastOnlineTime.format(DATE_TIME_FORMATTER);
            redisService.setCacheMapValue(redisKey, IotSinkRedisKeyConstants.DEVICE_DATA_FIELD_LAST_ONLINE_TIME, lastOnlineTimeStr);
        } catch (Exception e) {
            log.error("[updateDeviceConnectStatus][更新设备连接状态失败，deviceId: {}]", message.getDeviceId(), e);
        }
    }

    /**
     * 更新设备扩展信息
     * <p>
     * 扩展信息存储在 extension 字段中，格式为 JSON 对象
     * 每次更新会合并到现有的扩展信息中
     *
     * @param redisKey Redis Key
     * @param key      扩展信息键
     * @param value    扩展信息值
     */
    private void updateDeviceExtension(String redisKey, String key, Object value) {
        try {
            // 获取现有的扩展信息
            String existingExtensionJson = redisService.getCacheMapValue(redisKey, IotSinkRedisKeyConstants.DEVICE_DATA_FIELD_EXTENSION);
            Map<String, Object> extension = new HashMap<>();

            // 如果存在现有扩展信息，则解析并合并
            if (StrUtil.isNotBlank(existingExtensionJson)) {
                try {
                    extension = JSONUtil.toBean(existingExtensionJson, Map.class);
                } catch (Exception e) {
                    log.warn("[updateDeviceExtension][解析现有扩展信息失败，将创建新的扩展信息，deviceId: {}]", redisKey, e);
                    extension = new HashMap<>();
                }
            }

            // 更新或添加新的扩展信息
            extension.put(key, value);

            // 保存更新后的扩展信息
            String extensionJson = JSONUtil.toJsonStr(extension);
            redisService.setCacheMapValue(redisKey, IotSinkRedisKeyConstants.DEVICE_DATA_FIELD_EXTENSION, extensionJson);
        } catch (Exception e) {
            log.error("[updateDeviceExtension][更新设备扩展信息失败，redisKey: {}, key: {}]", redisKey, key, e);
        }
    }

    /**
     * 更新设备版本信息
     *
     * @param redisKey Redis Key
     * @param params   参数（包含版本信息）
     */
    private void updateDeviceVersion(String redisKey, Object params) {
        try {
            if (params instanceof Map) {
                Map<String, Object> paramsMap = (Map<String, Object>) params;
                String version = (String) paramsMap.get("version");
                if (StrUtil.isNotBlank(version)) {
                    redisService.setCacheMapValue(redisKey, IotSinkRedisKeyConstants.DEVICE_DATA_FIELD_VERSION, version);
                }
            }
        } catch (Exception e) {
            log.error("[updateDeviceVersion][更新设备版本失败，redisKey: {}]", redisKey, e);
        }
    }

    /**
     * 更新设备标签信息
     *
     * @param redisKey Redis Key
     * @param params   参数（包含标签信息）
     */
    private void updateDeviceTags(String redisKey, Object params) {
        try {
            String tagsJson = JSONUtil.toJsonStr(params);
            redisService.setCacheMapValue(redisKey, IotSinkRedisKeyConstants.DEVICE_DATA_FIELD_TAGS, tagsJson);
        } catch (Exception e) {
            log.error("[updateDeviceTags][更新设备标签失败，redisKey: {}]", redisKey, e);
        }
    }

    /**
     * 更新设备影子状态
     *
     * @param redisKey Redis Key
     * @param params   参数（包含影子状态）
     */
    private void updateDeviceShadow(String redisKey, Object params) {
        try {
            String shadowJson = JSONUtil.toJsonStr(params);
            redisService.setCacheMapValue(redisKey, IotSinkRedisKeyConstants.DEVICE_DATA_FIELD_SHADOW, shadowJson);
        } catch (Exception e) {
            log.error("[updateDeviceShadow][更新设备影子状态失败，redisKey: {}]", redisKey, e);
        }
    }

    /**
     * 更新设备配置信息
     *
     * @param redisKey Redis Key
     * @param data     数据（包含配置信息）
     */
    private void updateDeviceConfig(String redisKey, Object data) {
        try {
            String configJson = JSONUtil.toJsonStr(data);
            redisService.setCacheMapValue(redisKey, IotSinkRedisKeyConstants.DEVICE_DATA_FIELD_CONFIG, configJson);
        } catch (Exception e) {
            log.error("[updateDeviceConfig][更新设备配置失败，redisKey: {}]", redisKey, e);
        }
    }

    /**
     * 更新设备OTA进度
     *
     * @param redisKey Redis Key
     * @param params   参数（包含OTA进度信息）
     */
    private void updateDeviceOtaProgress(String redisKey, Object params) {
        try {
            String otaProgressJson = JSONUtil.toJsonStr(params);
            redisService.setCacheMapValue(redisKey, IotSinkRedisKeyConstants.DEVICE_DATA_FIELD_OTA_PROGRESS, otaProgressJson);
        } catch (Exception e) {
            log.error("[updateDeviceOtaProgress][更新设备OTA进度失败，redisKey: {}]", redisKey, e);
        }
    }
}

