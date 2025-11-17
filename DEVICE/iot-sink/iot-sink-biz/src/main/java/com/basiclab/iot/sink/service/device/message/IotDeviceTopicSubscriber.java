package com.basiclab.iot.sink.service.device.message;

import cn.hutool.core.util.StrUtil;
import com.basiclab.iot.sink.enums.IotDeviceTopicEnum;
import com.basiclab.iot.sink.messagebus.core.IotMessageBus;
import com.basiclab.iot.sink.messagebus.core.IotMessageSubscriber;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import javax.annotation.PostConstruct;
import javax.annotation.Resource;
import java.util.ArrayList;
import java.util.List;

/**
 * IoT 设备 Topic 消息订阅器
 * <p>
 * 订阅所有标准 IoT Topic，并处理消息
 *
 * @author 翱翔的雄库鲁
 */
@Slf4j
@Component
public class IotDeviceTopicSubscriber implements IotMessageSubscriber<IotDeviceMessage> {

    @Resource
    private IotMessageBus messageBus;

    @Resource
    private IotDeviceMessageService deviceMessageService;

    /**
     * 订阅的 Topic 列表
     */
    private final List<String> subscribedTopics = new ArrayList<>();

    @PostConstruct
    public void init() {
        // 注册订阅器
        messageBus.register(this);
        log.info("[init][IoT 设备 Topic 消息订阅器初始化完成，订阅主题: {}]", getTopic());
    }

    @Override
    public String getTopic() {
        // 使用通配符订阅所有标准 IoT Topic
        // 注意：实际的消息总线实现需要支持通配符订阅
        return "iot/#";
    }

    @Override
    public String getGroup() {
        // 使用固定的 Group，确保所有实例使用同一个 Group 进行负载均衡
        return "iot-device-topic-subscriber";
    }

    @Override
    public void onMessage(IotDeviceMessage message) {
        try {
            log.debug("[onMessage][接收到设备消息，messageId: {}, topic: {}, method: {}, deviceId: {}]",
                    message.getId(), message.getTopic(), message.getMethod(), message.getDeviceId());

            // 1. 校验消息
            if (message == null) {
                log.warn("[onMessage][消息为空]");
                return;
            }

            String topic = message.getTopic();
            if (StrUtil.isBlank(topic)) {
                log.warn("[onMessage][消息 Topic 为空，messageId: {}]", message.getId());
                return;
            }

            // 2. 匹配 Topic 枚举
            IotDeviceTopicEnum topicEnum = IotDeviceTopicEnum.matchTopic(topic);
            if (topicEnum == null) {
                log.warn("[onMessage][未匹配到 Topic 枚举，topic: {}, messageId: {}]", topic, message.getId());
                return;
            }

            // 3. 处理消息
            handleMessage(message, topicEnum);

        } catch (Exception e) {
            log.error("[onMessage][处理设备消息失败，messageId: {}, topic: {}]",
                    message != null ? message.getId() : "unknown",
                    message != null ? message.getTopic() : "unknown", e);
        }
    }

    /**
     * 处理消息
     *
     * @param message   消息
     * @param topicEnum Topic 枚举
     */
    private void handleMessage(IotDeviceMessage message, IotDeviceTopicEnum topicEnum) {
        log.info("[handleMessage][处理消息，topic: {}, 类型: {}, 描述: {}]",
                message.getTopic(), topicEnum.name(), topicEnum.getDescription());

        // 根据不同的 Topic 类型进行不同的处理
        switch (topicEnum) {
            // 配置管理相关
            case CONFIG_DOWNSTREAM_PUSH:
            case CONFIG_DOWNSTREAM_QUERY_ACK:
            case CONFIG_UPSTREAM_QUERY:
                handleConfigMessage(message, topicEnum);
                break;

            // 设备标签管理相关
            case DEVICE_TAG_DOWNSTREAM_REPORT_ACK:
            case DEVICE_TAG_UPSTREAM_DELETE:
            case DEVICE_TAG_UPSTREAM_REPORT:
            case DEVICE_TAG_DOWNSTREAM_DELETE_ACK:
                handleDeviceInfoMessage(message, topicEnum);
                break;

            // 设备影子相关
            case SHADOW_DOWNSTREAM_DESIRED:
            case SHADOW_UPSTREAM_REPORT:
                handleShadowMessage(message, topicEnum);
                break;

            // 时钟同步相关
            case NTP_UPSTREAM_REQUEST:
            case NTP_DOWNSTREAM_RESPONSE:
                handleNtpMessage(message, topicEnum);
                break;

            // 广播相关
            case BROADCAST_DOWNSTREAM:
                handleBroadcastMessage(message, topicEnum);
                break;

            // OTA 固件升级相关
            case OTA_DOWNSTREAM_UPGRADE_TASK:
            case OTA_UPSTREAM_VERSION_REPORT:
            case OTA_UPSTREAM_PROGRESS_REPORT:
            case OTA_UPSTREAM_FIRMWARE_QUERY:
                handleOtaMessage(message, topicEnum);
                break;

            // 服务调用相关
            case SERVICE_DOWNSTREAM_INVOKE:
            case SERVICE_UPSTREAM_INVOKE_RESPONSE:
                handleServiceMessage(message, topicEnum);
                break;

            // 属性相关
            case PROPERTY_DOWNSTREAM_DESIRED_SET:
            case PROPERTY_UPSTREAM_DESIRED_SET_ACK:
            case PROPERTY_DOWNSTREAM_DESIRED_QUERY:
            case PROPERTY_UPSTREAM_DESIRED_QUERY_RESPONSE:
            case PROPERTY_UPSTREAM_REPORT:
            case PROPERTY_DOWNSTREAM_REPORT_ACK:
                handlePropertyMessage(message, topicEnum);
                break;

            // 事件相关
            case EVENT_UPSTREAM_REPORT:
            case EVENT_DOWNSTREAM_REPORT_ACK:
                handleEventMessage(message, topicEnum);
                break;

            default:
                log.warn("[handleMessage][未处理的 Topic 类型，topic: {}, 类型: {}]",
                        message.getTopic(), topicEnum.name());
                break;
        }
    }

    /**
     * 处理配置消息
     */
    private void handleConfigMessage(IotDeviceMessage message, IotDeviceTopicEnum topicEnum) {
        log.debug("[handleConfigMessage][处理配置消息，topic: {}]", topicEnum.name());
        // TODO: 实现配置消息处理逻辑
    }

    /**
     * 处理设备标签消息
     */
    private void handleDeviceInfoMessage(IotDeviceMessage message, IotDeviceTopicEnum topicEnum) {
        log.debug("[handleDeviceInfoMessage][处理设备标签消息，topic: {}]", topicEnum.name());
        // TODO: 实现设备标签消息处理逻辑
    }

    /**
     * 处理设备影子消息
     */
    private void handleShadowMessage(IotDeviceMessage message, IotDeviceTopicEnum topicEnum) {
        log.debug("[handleShadowMessage][处理设备影子消息，topic: {}]", topicEnum.name());
        // TODO: 实现设备影子消息处理逻辑
    }

    /**
     * 处理 NTP 消息
     */
    private void handleNtpMessage(IotDeviceMessage message, IotDeviceTopicEnum topicEnum) {
        log.debug("[handleNtpMessage][处理 NTP 消息，topic: {}]", topicEnum.name());
        // TODO: 实现 NTP 消息处理逻辑
    }

    /**
     * 处理广播消息
     */
    private void handleBroadcastMessage(IotDeviceMessage message, IotDeviceTopicEnum topicEnum) {
        log.debug("[handleBroadcastMessage][处理广播消息，topic: {}]", topicEnum.name());
        // TODO: 实现广播消息处理逻辑
    }

    /**
     * 处理 OTA 消息
     */
    private void handleOtaMessage(IotDeviceMessage message, IotDeviceTopicEnum topicEnum) {
        log.debug("[handleOtaMessage][处理 OTA 消息，topic: {}]", topicEnum.name());
        // TODO: 实现 OTA 消息处理逻辑
    }

    /**
     * 处理服务调用消息
     */
    private void handleServiceMessage(IotDeviceMessage message, IotDeviceTopicEnum topicEnum) {
        log.debug("[handleServiceMessage][处理服务调用消息，topic: {}]", topicEnum.name());
        // TODO: 实现服务调用消息处理逻辑
    }

    /**
     * 处理属性消息
     */
    private void handlePropertyMessage(IotDeviceMessage message, IotDeviceTopicEnum topicEnum) {
        log.debug("[handlePropertyMessage][处理属性消息，topic: {}]", topicEnum.name());
        // TODO: 实现属性消息处理逻辑
    }

    /**
     * 处理事件消息
     */
    private void handleEventMessage(IotDeviceMessage message, IotDeviceTopicEnum topicEnum) {
        log.debug("[handleEventMessage][处理事件消息，topic: {}]", topicEnum.name());
        // TODO: 实现事件消息处理逻辑
    }
}

