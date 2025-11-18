package com.basiclab.iot.sink.enums;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * IoT 设备 Topic 枚举
 * <p>
 * 专业化的 Topic 命名规范：
 * - 使用 report 表示上报，invoke 表示调用，desired 表示期望值
 * - 使用 upstream 表示上行（设备->云端），downstream 表示下行（云端->设备）
 * - 使用 ack 表示确认回复，response 表示响应
 * - 统一命名风格，便于理解和维护
 *
 * @author 翱翔的雄库鲁
 */
@Getter
@AllArgsConstructor
public enum IotDeviceTopicEnum {

    // ========== 配置管理 ==========
    /**
     * 云端下行推送配置（设备订阅）
     */
    CONFIG_DOWNSTREAM_PUSH("/iot/${productIdentification}/${deviceIdentification}/config/downstream/push", true, "云端下行推送配置信息"),
    /**
     * 云端下行回复配置查询（设备订阅）
     */
    CONFIG_DOWNSTREAM_QUERY_ACK("/iot/${productIdentification}/${deviceIdentification}/config/downstream/query/ack", true, "云端下行回复配置查询"),
    /**
     * 设备上行查询配置（设备发布）
     */
    CONFIG_UPSTREAM_QUERY("/iot/${productIdentification}/${deviceIdentification}/config/upstream/query", false, "设备上行查询配置信息"),

    // ========== 设备标签管理 ==========
    /**
     * 云端下行回复标签上报（设备订阅）
     */
    DEVICE_TAG_DOWNSTREAM_REPORT_ACK("/iot/${productIdentification}/${deviceIdentification}/device/tag/downstream/report/ack", true, "云端下行回复标签上报"),
    /**
     * 设备上行删除标签（设备发布）
     */
    DEVICE_TAG_UPSTREAM_DELETE("/iot/${productIdentification}/${deviceIdentification}/device/tag/upstream/delete", false, "设备上行删除标签信息"),
    /**
     * 设备上行上报标签（设备发布）
     */
    DEVICE_TAG_UPSTREAM_REPORT("/iot/${productIdentification}/${deviceIdentification}/device/tag/upstream/report", false, "设备上行上报标签数据"),
    /**
     * 云端下行回复标签删除（设备订阅）
     */
    DEVICE_TAG_DOWNSTREAM_DELETE_ACK("/iot/${productIdentification}/${deviceIdentification}/device/tag/downstream/delete/ack", true, "云端下行回复标签删除"),

    // ========== 设备影子 ==========
    /**
     * 云端下行推送影子期望值（设备订阅）
     */
    SHADOW_DOWNSTREAM_DESIRED("/iot/${productIdentification}/${deviceIdentification}/shadow/downstream/desired", true, "云端下行推送影子期望值变更"),
    /**
     * 设备上行上报影子状态（设备发布）
     */
    SHADOW_UPSTREAM_REPORT("/iot/${productIdentification}/${deviceIdentification}/shadow/upstream/report", false, "设备上行上报影子状态"),

    // ========== 时钟同步 ==========
    /**
     * 云端下行回复 NTP 同步请求（设备订阅）
     */
    NTP_DOWNSTREAM_RESPONSE("/iot/${productIdentification}/${deviceIdentification}/ntp/downstream/response", true, "云端下行回复 NTP 时钟同步请求"),
    /**
     * 设备上行请求 NTP 同步（设备发布）
     */
    NTP_UPSTREAM_REQUEST("/iot/${productIdentification}/${deviceIdentification}/ntp/upstream/request", false, "设备上行请求 NTP 时钟同步"),

    // ========== 广播消息 ==========
    /**
     * 云端下行广播消息（设备订阅）
     */
    BROADCAST_DOWNSTREAM("/iot/${productIdentification}/${deviceIdentification}/broadcast/downstream/${identifier}", true, "云端下行广播消息，identifier 为用户自定义字符串"),

    // ========== OTA 固件升级 ==========
    /**
     * 云端下行推送固件升级任务（设备订阅）
     */
    OTA_DOWNSTREAM_UPGRADE_TASK("/iot/${productIdentification}/${deviceIdentification}/ota/downstream/upgrade/task", true, "云端下行推送固件升级任务"),
    /**
     * 设备上行上报固件版本信息（设备发布）
     */
    OTA_UPSTREAM_VERSION_REPORT("/iot/${productIdentification}/${deviceIdentification}/ota/upstream/version/report", false, "设备上行上报固件版本信息"),
    /**
     * 设备上行上报升级进度（设备发布）
     */
    OTA_UPSTREAM_PROGRESS_REPORT("/iot/${productIdentification}/${deviceIdentification}/ota/upstream/progress/report", false, "设备上行上报固件升级进度"),
    /**
     * 设备上行查询固件信息（设备发布）
     */
    OTA_UPSTREAM_FIRMWARE_QUERY("/iot/${productIdentification}/${deviceIdentification}/ota/upstream/firmware/query", false, "设备上行查询固件信息"),

    // ========== 服务调用 ==========
    /**
     * 云端下行调用设备服务（设备订阅）
     */
    SERVICE_DOWNSTREAM_INVOKE("/iot/${productIdentification}/${deviceIdentification}/service/downstream/invoke/${identifier}", true, "云端下行调用设备服务"),
    /**
     * 设备上行响应服务调用（设备发布）
     */
    SERVICE_UPSTREAM_INVOKE_RESPONSE("/iot/${productIdentification}/${deviceIdentification}/service/upstream/invoke/${identifier}/response", false, "设备上行响应服务调用"),

    // ========== 属性期望值设置 ==========
    /**
     * 云端下行设置属性期望值（设备订阅）
     */
    PROPERTY_DOWNSTREAM_DESIRED_SET("/iot/${productIdentification}/${deviceIdentification}/property/downstream/desired/set", true, "云端下行设置属性期望值"),
    /**
     * 设备上行回复属性期望值设置（设备发布）
     */
    PROPERTY_UPSTREAM_DESIRED_SET_ACK("/iot/${productIdentification}/${deviceIdentification}/property/upstream/desired/set/ack", false, "设备上行回复属性期望值设置"),

    // ========== 属性期望值获取 ==========
    /**
     * 云端下行查询属性期望值（设备订阅）
     */
    PROPERTY_DOWNSTREAM_DESIRED_QUERY("/iot/${productIdentification}/${deviceIdentification}/property/downstream/desired/query", true, "云端下行查询属性期望值"),
    /**
     * 设备上行回复属性期望值查询（设备发布）
     */
    PROPERTY_UPSTREAM_DESIRED_QUERY_RESPONSE("/iot/${productIdentification}/${deviceIdentification}/property/upstream/desired/query/response", false, "设备上行回复属性期望值查询"),

    // ========== 属性上报 ==========
    /**
     * 云端下行回复属性上报（设备订阅）
     */
    PROPERTY_DOWNSTREAM_REPORT_ACK("/iot/${productIdentification}/${deviceIdentification}/property/downstream/report/ack", true, "云端下行回复属性上报"),
    /**
     * 设备上行上报属性（设备发布）
     */
    PROPERTY_UPSTREAM_REPORT("/iot/${productIdentification}/${deviceIdentification}/property/upstream/report", false, "设备上行上报属性数据"),

    // ========== 事件上报 ==========
    /**
     * 云端下行回复事件上报（设备订阅）
     */
    EVENT_DOWNSTREAM_REPORT_ACK("/iot/${productIdentification}/${deviceIdentification}/event/downstream/report/${identifier}/ack", true, "云端下行回复事件上报"),
    /**
     * 设备上行上报事件（设备发布）
     */
    EVENT_UPSTREAM_REPORT("/iot/${productIdentification}/${deviceIdentification}/event/upstream/report/${identifier}", false, "设备上行上报事件数据"),

    // ========== 日志上报 ==========
    /**
     * 云端下行回复日志上报（设备订阅，通常不需要回复）
     */
    LOG_DOWNSTREAM_REPORT_ACK("/iot/${productIdentification}/${deviceIdentification}/log/downstream/report/ack", true, "云端下行回复日志上报"),
    /**
     * 设备上行上报日志（设备发布）
     * <p>
     * 设备一条一条回传日志数据，用于设备日志入库
     */
    LOG_UPSTREAM_REPORT("/iot/${productIdentification}/${deviceIdentification}/log/upstream/report", false, "设备上行上报日志数据");

    /**
     * Topic 模板
     * 支持占位符：${productIdentification}、${deviceIdentification}、${identifier}
     */
    private final String topicTemplate;

    /**
     * 是否需要回复
     * true: 设备订阅，云端发布（下行消息）
     * false: 设备发布，云端订阅（上行消息）
     */
    private final boolean needReply;

    /**
     * 描述信息
     */
    private final String description;

    /**
     * 构建实际的 Topic
     *
     * @param productIdentification 产品唯一标识
     * @param deviceIdentification   设备唯一标识
     * @param identifier             标识符（可选，用于服务调用、事件上报等）
     * @return 实际的 Topic
     */
    public String buildTopic(String productIdentification, String deviceIdentification, String identifier) {
        String topic = topicTemplate
                .replace("${productIdentification}", productIdentification)
                .replace("${deviceIdentification}", deviceIdentification);
        if (identifier != null) {
            topic = topic.replace("${identifier}", identifier);
        }
        return topic;
    }

    /**
     * 构建实际的 Topic（不带 identifier）
     *
     * @param productIdentification 产品唯一标识
     * @param deviceIdentification   设备唯一标识
     * @return 实际的 Topic
     */
    public String buildTopic(String productIdentification, String deviceIdentification) {
        return buildTopic(productIdentification, deviceIdentification, null);
    }

    /**
     * 根据 Topic 匹配枚举
     *
     * @param topic 实际的 Topic
     * @return 匹配的枚举，如果未匹配到则返回 null
     */
    public static IotDeviceTopicEnum matchTopic(String topic) {
        if (topic == null || topic.isEmpty()) {
            return null;
        }

        // 将实际的 topic 转换为模板格式进行匹配
        for (IotDeviceTopicEnum topicEnum : values()) {
            String pattern = topicEnum.topicTemplate
                    .replace("${productIdentification}", "[^/]+")
                    .replace("${deviceIdentification}", "[^/]+")
                    .replace("${identifier}", "[^/]+")
                    .replace("/", "\\/");
            if (topic.matches("^" + pattern + "$")) {
                return topicEnum;
            }
        }
        return null;
    }

    /**
     * 判断是否需要回复
     *
     * @return 是否需要回复
     */
    public boolean isNeedReply() {
        return needReply;
    }
}

