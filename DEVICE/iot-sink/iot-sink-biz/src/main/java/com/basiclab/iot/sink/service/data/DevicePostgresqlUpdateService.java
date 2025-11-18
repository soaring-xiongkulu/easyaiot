package com.basiclab.iot.sink.service.data;

import cn.hutool.core.util.StrUtil;
import cn.hutool.json.JSONUtil;
import com.basiclab.iot.sink.dal.mapper.DeviceMapper;
import com.basiclab.iot.sink.enums.IotDeviceTopicEnum;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

/**
 * 设备PostgreSQL更新服务
 * <p>
 * 根据不同Topic更新PostgreSQL设备表的不同字段
 *
 * @author 翱翔的雄库鲁
 */
@Slf4j
@Service
public class DevicePostgresqlUpdateService {

    @Resource
    private DeviceMapper deviceMapper;

    /**
     * 更新PostgreSQL设备表
     *
     * @param message   设备消息
     * @param topicEnum Topic枚举
     */
    public void updateDeviceTable(IotDeviceMessage message, IotDeviceTopicEnum topicEnum) {
        if (message == null || message.getDeviceId() == null || topicEnum == null) {
            log.warn("[updateDeviceTable][消息、设备ID或Topic枚举为空，跳过更新]");
            return;
        }

        try {
            switch (topicEnum) {
                case PROPERTY_UPSTREAM_REPORT:
                    // 属性上报：更新扩展信息中的属性数据
                    updateDeviceExtension(message, "properties", message.getParams());
                    // 更新连接状态和最后在线时间
                    updateDeviceConnectStatus(message);
                    break;

                case PROPERTY_UPSTREAM_DESIRED_SET_ACK:
                case PROPERTY_UPSTREAM_DESIRED_QUERY_RESPONSE:
                    // 属性期望值相关：更新扩展信息
                    updateDeviceExtension(message, "desired", message.getData());
                    break;

                case EVENT_UPSTREAM_REPORT:
                    // 事件上报：更新扩展信息中的事件数据
                    updateDeviceExtension(message, "events", message.getParams());
                    // 更新连接状态和最后在线时间
                    updateDeviceConnectStatus(message);
                    break;

                case SERVICE_UPSTREAM_INVOKE_RESPONSE:
                    // 服务调用响应：更新扩展信息中的服务响应数据
                    updateDeviceExtension(message, "serviceResponse", message.getData());
                    break;

                case DEVICE_TAG_UPSTREAM_REPORT:
                    // 标签上报：更新设备标签
                    updateDeviceTags(message, message.getParams());
                    break;

                case DEVICE_TAG_UPSTREAM_DELETE:
                    // 标签删除：更新设备标签
                    updateDeviceTags(message, message.getParams());
                    break;

                case SHADOW_UPSTREAM_REPORT:
                    // 影子上报：更新影子状态
                    updateDeviceShadow(message, message.getParams());
                    break;

                case CONFIG_UPSTREAM_QUERY:
                    // 配置查询：更新配置信息
                    updateDeviceConfig(message, message.getData());
                    break;

                case NTP_UPSTREAM_REQUEST:
                    // NTP请求：更新连接状态和最后在线时间
                    updateDeviceConnectStatus(message);
                    break;

                case OTA_UPSTREAM_VERSION_REPORT:
                    // OTA版本上报：更新设备版本
                    updateDeviceVersion(message, message.getParams());
                    break;

                case OTA_UPSTREAM_PROGRESS_REPORT:
                    // OTA进度上报：更新OTA进度
                    updateDeviceOtaProgress(message, message.getParams());
                    break;

                case OTA_UPSTREAM_FIRMWARE_QUERY:
                    // OTA固件查询：更新扩展信息
                    updateDeviceExtension(message, "otaQuery", message.getData());
                    break;

                default:
                    // 默认：只更新连接状态和最后在线时间
                    updateDeviceConnectStatus(message);
                    break;
            }

            log.debug("[updateDeviceTable][PostgreSQL设备表更新成功，messageId: {}, topic: {}]", message.getId(), topicEnum.name());
        } catch (Exception e) {
            log.error("[updateDeviceTable][PostgreSQL设备表更新失败，messageId: {}, topic: {}]", message.getId(), topicEnum.name(), e);
        }
    }

    /**
     * 更新设备连接状态和最后在线时间
     *
     * @param message 设备消息
     */
    private void updateDeviceConnectStatus(IotDeviceMessage message) {
        try {
            deviceMapper.updateDeviceConnectStatus(
                    message.getDeviceId(),
                    "ONLINE",
                    message.getReportTime() != null ? message.getReportTime() : LocalDateTime.now()
            );
        } catch (Exception e) {
            log.error("[updateDeviceConnectStatus][更新设备连接状态失败，deviceId: {}]", message.getDeviceId(), e);
        }
    }

    /**
     * 更新设备扩展信息
     *
     * @param message 设备消息
     * @param key     扩展信息键
     * @param value   扩展信息值
     */
    private void updateDeviceExtension(IotDeviceMessage message, String key, Object value) {
        try {
            Map<String, Object> extension = new HashMap<>();
            extension.put(key, value);
            String extensionJson = JSONUtil.toJsonStr(extension);
            deviceMapper.updateDeviceExtension(message.getDeviceId(), extensionJson);
        } catch (Exception e) {
            log.error("[updateDeviceExtension][更新设备扩展信息失败，deviceId: {}, key: {}]", message.getDeviceId(), key, e);
        }
    }

    /**
     * 更新设备版本信息
     *
     * @param message 设备消息
     * @param params  参数（包含版本信息）
     */
    private void updateDeviceVersion(IotDeviceMessage message, Object params) {
        try {
            if (params instanceof Map) {
                Map<String, Object> paramsMap = (Map<String, Object>) params;
                String version = (String) paramsMap.get("version");
                if (StrUtil.isNotBlank(version)) {
                    deviceMapper.updateDeviceVersion(message.getDeviceId(), version);
                }
            }
        } catch (Exception e) {
            log.error("[updateDeviceVersion][更新设备版本失败，deviceId: {}]", message.getDeviceId(), e);
        }
    }

    /**
     * 更新设备标签信息
     *
     * @param message 设备消息
     * @param params  参数（包含标签信息）
     */
    private void updateDeviceTags(IotDeviceMessage message, Object params) {
        try {
            Map<String, Object> tags = new HashMap<>();
            tags.put("tags", params);
            String tagsJson = JSONUtil.toJsonStr(tags);
            deviceMapper.updateDeviceTags(message.getDeviceId(), tagsJson);
        } catch (Exception e) {
            log.error("[updateDeviceTags][更新设备标签失败，deviceId: {}]", message.getDeviceId(), e);
        }
    }

    /**
     * 更新设备影子状态
     *
     * @param message 设备消息
     * @param params  参数（包含影子状态）
     */
    private void updateDeviceShadow(IotDeviceMessage message, Object params) {
        try {
            String shadowJson = JSONUtil.toJsonStr(params);
            deviceMapper.updateDeviceShadow(message.getDeviceId(), shadowJson);
        } catch (Exception e) {
            log.error("[updateDeviceShadow][更新设备影子状态失败，deviceId: {}]", message.getDeviceId(), e);
        }
    }

    /**
     * 更新设备配置信息
     *
     * @param message 设备消息
     * @param data    数据（包含配置信息）
     */
    private void updateDeviceConfig(IotDeviceMessage message, Object data) {
        try {
            String configJson = JSONUtil.toJsonStr(data);
            deviceMapper.updateDeviceConfig(message.getDeviceId(), configJson);
        } catch (Exception e) {
            log.error("[updateDeviceConfig][更新设备配置失败，deviceId: {}]", message.getDeviceId(), e);
        }
    }

    /**
     * 更新设备OTA进度
     *
     * @param message 设备消息
     * @param params  参数（包含OTA进度信息）
     */
    private void updateDeviceOtaProgress(IotDeviceMessage message, Object params) {
        try {
            String otaProgressJson = JSONUtil.toJsonStr(params);
            deviceMapper.updateDeviceOtaProgress(message.getDeviceId(), otaProgressJson);
        } catch (Exception e) {
            log.error("[updateDeviceOtaProgress][更新设备OTA进度失败，deviceId: {}]", message.getDeviceId(), e);
        }
    }
}

