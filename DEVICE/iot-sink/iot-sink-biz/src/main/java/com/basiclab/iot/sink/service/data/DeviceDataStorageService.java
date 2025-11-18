package com.basiclab.iot.sink.service.data;

import com.basiclab.iot.sink.enums.IotDeviceTopicEnum;
import com.basiclab.iot.sink.enums.IotDeviceTopicMethodMapping;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;
import com.basiclab.iot.sink.service.tdengine.TdEngineService;
import com.basiclab.iot.tdengine.domain.Fields;
import com.basiclab.iot.tdengine.domain.model.TableDTO;
import cn.hutool.core.util.StrUtil;
import cn.hutool.json.JSONUtil;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.ArrayList;
import java.util.List;

/**
 * DeviceDataStorageService
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Slf4j
@Service
public class DeviceDataStorageService {

    /**
     * TDEngine数据库名称
     */
    private static final String TD_DATABASE_NAME = "iot_device";

    @Resource
    private TdEngineService tdEngineService;

    @Resource
    private DeviceRedisStorageService deviceRedisStorageService;

    /**
     * 存储设备消息数据
     * <p>
     * 同时将数据存储到TDEngine（历史数据）和Redis（设备数据缓存）
     * <p>
     * 在入库前会根据 Topic 标准映射验证并标准化 method 字段
     *
     * @param message   设备消息
     * @param topicEnum Topic枚举
     */
    public void storeDeviceData(IotDeviceMessage message, IotDeviceTopicEnum topicEnum) {
        if (message == null || topicEnum == null) {
            log.warn("[storeDeviceData][消息或Topic枚举为空，跳过存储]");
            return;
        }

        try {
            // 0. 根据 Topic 标准映射验证并标准化 method 字段
            normalizeMethodByTopic(message, topicEnum);

            // 1. 存储到TDEngine（历史数据）
            storeToTdEngine(message, topicEnum);

            // 2. 存储到Redis（设备数据缓存）
            deviceRedisStorageService.storeDeviceData(message, topicEnum);

            log.debug("[storeDeviceData][数据存储成功，messageId: {}, topic: {}, method: {}]", 
                    message.getId(), topicEnum.name(), message.getMethod());
        } catch (Exception e) {
            log.error("[storeDeviceData][数据存储失败，messageId: {}, topic: {}]", message.getId(), topicEnum.name(), e);
        }
    }

    /**
     * 根据 Topic 标准映射验证并标准化 method 字段
     * <p>
     * 如果消息中的 method 与 Topic 标准映射不一致，会使用标准映射中的 method
     * 如果消息中没有 method，会根据 Topic 标准映射自动设置
     *
     * @param message   设备消息
     * @param topicEnum Topic枚举
     */
    private void normalizeMethodByTopic(IotDeviceMessage message, IotDeviceTopicEnum topicEnum) {
        // 获取 Topic 对应的标准 Method
        String standardMethod = IotDeviceTopicMethodMapping.getMethodByTopic(topicEnum);
        
        if (StrUtil.isBlank(standardMethod)) {
            // 如果该 Topic 没有标准 Method 映射，保持原有 method 不变
            if (StrUtil.isBlank(message.getMethod())) {
                log.debug("[normalizeMethodByTopic][Topic {} 没有标准 Method 映射，且消息中 method 为空，保持为空]", 
                        topicEnum.name());
            }
            return;
        }

        // 如果消息中的 method 为空，使用标准 Method
        if (StrUtil.isBlank(message.getMethod())) {
            message.setMethod(standardMethod);
            log.debug("[normalizeMethodByTopic][消息 method 为空，根据 Topic {} 标准映射设置为: {}]", 
                    topicEnum.name(), standardMethod);
            return;
        }

        // 如果消息中的 method 与标准 Method 不一致，记录警告并使用标准 Method
        if (!standardMethod.equals(message.getMethod())) {
            log.warn("[normalizeMethodByTopic][消息 method ({}) 与 Topic {} 标准映射 ({}) 不一致，使用标准 Method]", 
                    message.getMethod(), topicEnum.name(), standardMethod);
            message.setMethod(standardMethod);
        } else {
            log.debug("[normalizeMethodByTopic][消息 method ({}) 与 Topic {} 标准映射一致]", 
                    message.getMethod(), topicEnum.name());
        }
    }

    /**
     * 存储数据到TDEngine
     *
     * @param message   设备消息
     * @param topicEnum Topic枚举
     */
    private void storeToTdEngine(IotDeviceMessage message, IotDeviceTopicEnum topicEnum) {
        try {
            // 获取超级表名称
            String superTableName = getSuperTableName(topicEnum);
            if (StrUtil.isBlank(superTableName)) {
                log.warn("[storeToTdEngine][未找到对应的超级表，topic: {}]", topicEnum.name());
                return;
            }

            // 构建子表名称（使用设备标识）
            String tableName = buildTableName(superTableName, message.getDeviceId());

            // 构建字段值列表
            List<Fields> schemaFieldValues = buildSchemaFieldValues(message, topicEnum);
            List<Fields> tagsFieldValues = buildTagsFieldValues(message, topicEnum);

            // 构建TableDTO
            TableDTO tableDTO = new TableDTO();
            tableDTO.setDataBaseName(TD_DATABASE_NAME);
            tableDTO.setSuperTableName(superTableName);
            tableDTO.setTableName(tableName);
            tableDTO.setSchemaFieldValues(schemaFieldValues);
            tableDTO.setTagsFieldValues(tagsFieldValues);

            // 调用TDEngine服务插入数据
            tdEngineService.insertTableData(tableDTO);

            log.debug("[storeToTdEngine][TDEngine数据插入成功，tableName: {}]", tableName);
        } catch (Exception e) {
            log.error("[storeToTdEngine][TDEngine数据插入失败，messageId: {}, topic: {}]", message.getId(), topicEnum.name(), e);
        }
    }

    /**
     * 获取超级表名称
     *
     * @param topicEnum Topic枚举
     * @return 超级表名称
     */
    private String getSuperTableName(IotDeviceTopicEnum topicEnum) {
        switch (topicEnum) {
            case PROPERTY_UPSTREAM_REPORT:
                return "st_property_upstream_report";
            case PROPERTY_UPSTREAM_DESIRED_SET_ACK:
                return "st_property_upstream_desired_set_ack";
            case PROPERTY_UPSTREAM_DESIRED_QUERY_RESPONSE:
                return "st_property_upstream_desired_query_response";
            case EVENT_UPSTREAM_REPORT:
                return "st_event_upstream_report";
            case SERVICE_UPSTREAM_INVOKE_RESPONSE:
                return "st_service_upstream_invoke_response";
            case DEVICE_TAG_UPSTREAM_REPORT:
                return "st_device_tag_upstream_report";
            case DEVICE_TAG_UPSTREAM_DELETE:
                return "st_device_tag_upstream_delete";
            case SHADOW_UPSTREAM_REPORT:
                return "st_shadow_upstream_report";
            case CONFIG_UPSTREAM_QUERY:
                return "st_config_upstream_query";
            case NTP_UPSTREAM_REQUEST:
                return "st_ntp_upstream_request";
            case OTA_UPSTREAM_VERSION_REPORT:
                return "st_ota_upstream_version_report";
            case OTA_UPSTREAM_PROGRESS_REPORT:
                return "st_ota_upstream_progress_report";
            case OTA_UPSTREAM_FIRMWARE_QUERY:
                return "st_ota_upstream_firmware_query";
            case LOG_UPSTREAM_REPORT:
                return "st_log_upstream_report";
            default:
                return null;
        }
    }

    /**
     * 构建子表名称
     *
     * @param superTableName 超级表名称
     * @param deviceId       设备ID
     * @return 子表名称
     */
    private String buildTableName(String superTableName, Long deviceId) {
        return superTableName + "_" + deviceId;
    }

    /**
     * 构建Schema字段值列表
     *
     * @param message   设备消息
     * @param topicEnum Topic枚举
     * @return 字段值列表
     */
    private List<Fields> buildSchemaFieldValues(IotDeviceMessage message, IotDeviceTopicEnum topicEnum) {
        List<Fields> fields = new ArrayList<>();

        // 时间戳字段（TDEngine要求第一个字段必须是timestamp）
        long timestamp = message.getReportTime() != null
                ? message.getReportTime().atZone(ZoneId.systemDefault()).toInstant().toEpochMilli()
                : Instant.now().toEpochMilli();
        fields.add(new Fields("ts", timestamp, null, null));

        // report_time
        fields.add(new Fields("report_time", message.getReportTime() != null
                ? message.getReportTime().atZone(ZoneId.systemDefault()).toInstant().toEpochMilli()
                : timestamp, null, null));

        // device_id
        fields.add(new Fields("device_id", message.getDeviceId(), null, null));

        // tenant_id
        fields.add(new Fields("tenant_id", message.getTenantId(), null, null));

        // product_identification（从topic中提取或从设备信息中获取）
        String productIdentification = extractProductIdentification(message);
        fields.add(new Fields("product_identification", productIdentification, null, null));

        // device_identification（从topic中提取或从设备信息中获取）
        String deviceIdentification = extractDeviceIdentification(message);
        fields.add(new Fields("device_identification", deviceIdentification, null, null));

        // server_id
        fields.add(new Fields("server_id", message.getServerId(), null, null));

        // request_id
        fields.add(new Fields("request_id", message.getRequestId(), null, null));

        // method
        fields.add(new Fields("method", message.getMethod(), null, null));

        // params（JSON格式）
        if (message.getParams() != null) {
            fields.add(new Fields("params", JSONUtil.toJsonStr(message.getParams()), null, null));
        }

        // data（JSON格式）
        if (message.getData() != null) {
            fields.add(new Fields("data", JSONUtil.toJsonStr(message.getData()), null, null));
        }

        // code
        fields.add(new Fields("code", message.getCode(), null, null));

        // msg
        fields.add(new Fields("msg", message.getMsg(), null, null));

        // topic
        fields.add(new Fields("topic", message.getTopic(), null, null));

        // identifier（用于事件上报和服务调用）
        if (topicEnum == IotDeviceTopicEnum.EVENT_UPSTREAM_REPORT
                || topicEnum == IotDeviceTopicEnum.SERVICE_UPSTREAM_INVOKE_RESPONSE) {
            String identifier = extractIdentifier(message.getTopic());
            fields.add(new Fields("identifier", identifier, null, null));
        }

        return fields;
    }

    /**
     * 构建Tags字段值列表
     *
     * @param message   设备消息
     * @param topicEnum Topic枚举
     * @return Tags字段值列表
     */
    private List<Fields> buildTagsFieldValues(IotDeviceMessage message, IotDeviceTopicEnum topicEnum) {
        List<Fields> tags = new ArrayList<>();

        // device_identification
        String deviceIdentification = extractDeviceIdentification(message);
        tags.add(new Fields("device_identification", deviceIdentification, null, null));

        // tenant_id
        tags.add(new Fields("tenant_id", message.getTenantId(), null, null));

        // product_identification
        String productIdentification = extractProductIdentification(message);
        tags.add(new Fields("product_identification", productIdentification, null, null));

        // identifier（用于事件上报和服务调用）
        if (topicEnum == IotDeviceTopicEnum.EVENT_UPSTREAM_REPORT
                || topicEnum == IotDeviceTopicEnum.SERVICE_UPSTREAM_INVOKE_RESPONSE) {
            String identifier = extractIdentifier(message.getTopic());
            tags.add(new Fields("identifier", identifier, null, null));
        }

        return tags;
    }

    /**
     * 从Topic中提取产品标识
     *
     * @param message 设备消息
     * @return 产品标识
     */
    private String extractProductIdentification(IotDeviceMessage message) {
        if (StrUtil.isNotBlank(message.getTopic())) {
            String[] parts = message.getTopic().split("/");
            if (parts.length >= 2) {
                return parts[1];
            }
        }
        return "";
    }

    /**
     * 从Topic中提取设备标识
     *
     * @param message 设备消息
     * @return 设备标识
     */
    private String extractDeviceIdentification(IotDeviceMessage message) {
        if (StrUtil.isNotBlank(message.getTopic())) {
            String[] parts = message.getTopic().split("/");
            if (parts.length >= 3) {
                return parts[2];
            }
        }
        return "";
    }

    /**
     * 从Topic中提取identifier（用于事件上报和服务调用）
     *
     * @param topic Topic字符串
     * @return identifier
     */
    private String extractIdentifier(String topic) {
        if (StrUtil.isNotBlank(topic)) {
            String[] parts = topic.split("/");
            // 查找包含identifier的部分
            for (String part : parts) {
                if (StrUtil.isNotBlank(part) && !part.equals("iot") && !part.matches("^[a-zA-Z0-9]{20}$")) {
                    // 可能是identifier
                    if (parts.length > 5) {
                        return part;
                    }
                }
            }
        }
        return "";
    }
}

