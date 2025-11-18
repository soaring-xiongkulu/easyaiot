package com.basiclab.iot.device.messagebus;

import cn.hutool.core.util.StrUtil;
import com.basiclab.iot.sink.enums.IotDeviceTopicEnum;
import com.basiclab.iot.sink.messagebus.core.IotMessageBus;
import com.basiclab.iot.sink.messagebus.core.IotMessageSubscriber;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnBean;
import org.springframework.stereotype.Component;

import javax.annotation.PostConstruct;
import javax.annotation.Resource;

/**
 * DeviceEventSubscriber
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Slf4j
@Component
@ConditionalOnBean(IotMessageBus.class)
public class DeviceEventSubscriber implements IotMessageSubscriber<IotDeviceMessage> {

    @Resource
    private IotMessageBus messageBus;

    @Resource
    private DeviceEventHandler handler;

    @PostConstruct
    public void subscribe() {
        messageBus.register(this);
        log.info("[subscribe][设备事件上报消息订阅器注册成功，主题：{}]", getTopic());
    }

    @Override
    public String getTopic() {
        // 订阅通用设备消息主题
        return IotDeviceMessage.MESSAGE_BUS_DEVICE_MESSAGE_TOPIC;
    }

    @Override
    public String getGroup() {
        // 使用独立的Group，确保iot-device模块独立消费
        return "iot-device-event-subscriber";
    }

    @Override
    public void onMessage(IotDeviceMessage message) {
        try {
            // 1. 基础校验
            if (message == null) {
                log.warn("[onMessage][消息为空，跳过处理]");
                return;
            }

            String topic = message.getTopic();
            if (StrUtil.isBlank(topic)) {
                log.warn("[onMessage][消息Topic为空，messageId: {}]", message.getId());
                return;
            }

            // 2. 匹配Topic，只处理设备事件上报消息
            IotDeviceTopicEnum topicEnum = IotDeviceTopicEnum.matchTopic(topic);
            if (topicEnum != IotDeviceTopicEnum.EVENT_UPSTREAM_REPORT) {
                // 不是设备事件上报消息，跳过
                return;
            }

            // 3. 校验method，确保是事件上报相关
            String method = message.getMethod();
            if (StrUtil.isBlank(method) || !"thing.event.post".equals(method)) {
                log.debug("[onMessage][消息method不是事件上报，跳过处理，method: {}, messageId: {}]",
                        method, message.getId());
                return;
            }

            log.info("[onMessage][收到设备事件上报消息，messageId: {}, topic: {}, deviceId: {}]",
                    message.getId(), topic, message.getDeviceId());

            // 4. 委托给处理器处理
            handler.handle(message);

        } catch (Exception e) {
            log.error("[onMessage][处理设备事件上报消息失败，messageId: {}, topic: {}]",
                    message != null ? message.getId() : "unknown",
                    message != null ? message.getTopic() : "unknown", e);
        }
    }
}

