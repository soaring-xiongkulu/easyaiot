package com.basiclab.iot.sink.messagebus.publisher.message;

import cn.hutool.core.util.StrUtil;
import com.basiclab.iot.sink.config.IotGatewayProperties;
import com.basiclab.iot.sink.enums.IotDeviceTopicEnum;
import com.basiclab.iot.sink.messagebus.core.IotMessageBus;
import com.basiclab.iot.sink.messagebus.core.IotMessageSubscriber;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;
import com.basiclab.iot.sink.messagebus.publisher.event.*;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.stereotype.Component;

import org.springframework.beans.factory.SmartInitializingSingleton;
import org.springframework.context.annotation.Lazy;

import javax.annotation.Resource;

/**
 * IotDeviceTopicSubscriber
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Slf4j
@Component
public class IotDeviceTopicSubscriber implements IotMessageSubscriber<IotDeviceMessage>, SmartInitializingSingleton {

    @Resource
    @Lazy
    private IotMessageBus messageBus;

    @Resource
    private ApplicationEventPublisher eventPublisher;

    @Resource
    private IotGatewayProperties gatewayProperties;

    @Override
    public void afterSingletonsInstantiated() {
        // 在所有单例 bean 初始化完成后注册订阅器，避免循环依赖
        messageBus.register(this);
        log.info("[afterSingletonsInstantiated][IoT 设备 Topic 消息订阅器初始化完成，订阅主题: {}]", getTopic());
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
            // 1. 校验消息
            if (message == null) {
                log.warn("[onMessage][消息为空]");
                return;
            }

            log.debug("[onMessage][接收到设备消息，messageId: {}, topic: {}, method: {}, deviceId: {}]",
                    message.getId(), message.getTopic(), message.getMethod(), message.getDeviceId());

            String topic = message.getTopic();
            if (StrUtil.isBlank(topic)) {
                // 如果消息的 topic 为空，说明该消息不应该被此订阅器处理
                // 使用 debug 级别避免无限打印警告日志
                log.debug("[onMessage][消息 Topic 为空，跳过处理，messageId: {}]", message.getId());
                return;
            }

            // 2. 匹配 Topic 枚举
            IotDeviceTopicEnum topicEnum = IotDeviceTopicEnum.matchTopic(topic);
            if (topicEnum == null) {
                log.warn("[onMessage][未匹配到 Topic 枚举，topic: {}, messageId: {}]", topic, message.getId());
                return;
            }

            // 3. 检查 Topic 是否应该被处理
            if (gatewayProperties != null && gatewayProperties.getTopic() != null) {
                boolean shouldProcess = gatewayProperties.getTopic().shouldProcess(topicEnum);
                if (!shouldProcess) {
                    log.debug("[onMessage][Topic 不在订阅列表中，跳过处理，topic: {}, topicEnum: {}, messageId: {}]",
                            topic, topicEnum.name(), message.getId());
                    return;
                }
            }

            // 4. 发布事件，由对应的 EventListener 异步处理
            publishEvent(message, topicEnum);

        } catch (Exception e) {
            log.error("[onMessage][处理设备消息失败，messageId: {}, topic: {}]",
                    message != null ? message.getId() : "unknown",
                    message != null ? message.getTopic() : "unknown", e);
        }
    }

    /**
     * 发布事件，由对应的 EventListener 异步处理
     *
     * @param message   消息
     * @param topicEnum Topic 枚举
     */
    private void publishEvent(IotDeviceMessage message, IotDeviceTopicEnum topicEnum) {
        log.debug("[publishEvent][发布事件，topic: {}, 类型: {}, 描述: {}]",
                message.getTopic(), topicEnum.name(), topicEnum.getDescription());

        // 根据不同的 Topic 类型发布对应的事件
        switch (topicEnum) {
            // 配置管理相关
            case CONFIG_DOWNSTREAM_PUSH:
            case CONFIG_DOWNSTREAM_QUERY_ACK:
            case CONFIG_UPSTREAM_QUERY:
                eventPublisher.publishEvent(new ConfigEvent(this, message, topicEnum));
                break;

            // 设备标签管理相关
            case DEVICE_TAG_DOWNSTREAM_REPORT_ACK:
            case DEVICE_TAG_UPSTREAM_DELETE:
            case DEVICE_TAG_UPSTREAM_REPORT:
            case DEVICE_TAG_DOWNSTREAM_DELETE_ACK:
                eventPublisher.publishEvent(new DeviceInfoEvent(this, message, topicEnum));
                break;

            // 设备影子相关
            case SHADOW_DOWNSTREAM_DESIRED:
            case SHADOW_UPSTREAM_REPORT:
                eventPublisher.publishEvent(new ShadowEvent(this, message, topicEnum));
                break;

            // 时钟同步相关
            case NTP_UPSTREAM_REQUEST:
            case NTP_DOWNSTREAM_RESPONSE:
                eventPublisher.publishEvent(new NtpEvent(this, message, topicEnum));
                break;

            // 广播相关
            case BROADCAST_DOWNSTREAM:
                eventPublisher.publishEvent(new BroadcastEvent(this, message, topicEnum));
                break;

            // OTA 固件升级相关
            case OTA_DOWNSTREAM_UPGRADE_TASK:
            case OTA_UPSTREAM_VERSION_REPORT:
            case OTA_UPSTREAM_PROGRESS_REPORT:
            case OTA_UPSTREAM_FIRMWARE_QUERY:
                eventPublisher.publishEvent(new OtaEvent(this, message, topicEnum));
                break;

            // 服务调用相关
            case SERVICE_DOWNSTREAM_INVOKE:
            case SERVICE_UPSTREAM_INVOKE_RESPONSE:
                eventPublisher.publishEvent(new ServiceEvent(this, message, topicEnum));
                break;

            // 属性相关
            case PROPERTY_DOWNSTREAM_DESIRED_SET:
            case PROPERTY_UPSTREAM_DESIRED_SET_ACK:
            case PROPERTY_DOWNSTREAM_DESIRED_QUERY:
            case PROPERTY_UPSTREAM_DESIRED_QUERY_RESPONSE:
            case PROPERTY_UPSTREAM_REPORT:
            case PROPERTY_DOWNSTREAM_REPORT_ACK:
                eventPublisher.publishEvent(new PropertyEvent(this, message, topicEnum));
                break;

            // 事件相关
            case EVENT_UPSTREAM_REPORT:
            case EVENT_DOWNSTREAM_REPORT_ACK:
                eventPublisher.publishEvent(new EventMessageEvent(this, message, topicEnum));
                break;

            // 日志相关
            case LOG_UPSTREAM_REPORT:
            case LOG_DOWNSTREAM_REPORT_ACK:
                eventPublisher.publishEvent(new LogEvent(this, message, topicEnum));
                break;

            default:
                log.warn("[publishEvent][未处理的 Topic 类型，topic: {}, 类型: {}]",
                        message.getTopic(), topicEnum.name());
                break;
        }
    }
}

