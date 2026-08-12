package com.basiclab.iot.sink.messagebus.subscriber.listener;

import cn.hutool.core.util.StrUtil;
import cn.hutool.extra.spring.SpringUtil;
import com.basiclab.iot.sink.enums.IotDeviceTopicEnum;
import com.basiclab.iot.sink.messagebus.subscriber.event.IotMessageBusEvent;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;
import com.basiclab.iot.sink.mq.producer.IotDeviceMessageProducer;
import com.basiclab.iot.sink.service.DeviceServerIdService;
import com.basiclab.iot.sink.util.IotDeviceMessageUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.event.EventListener;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;

/**
 * PropertyDownstreamDesiredSetListener
 * <p>
 * 通用下行 Topic 收到属性期望设置时，若设备已绑定工业/MQTT 网关 serverId，
 * 则转发到网关专属 Topic，供轮询协议或 MQTT 下行订阅者执行写入。
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Slf4j
@Component
public class PropertyDownstreamDesiredSetListener {

    @Async("iotMessageBusSubscriberExecutor")
    @EventListener
    public void handlePropertyDownstreamDesiredSetEvent(IotMessageBusEvent event) {
        try {
            if (event.getTopicEnum() != IotDeviceTopicEnum.PROPERTY_DOWNSTREAM_DESIRED_SET
                    && event.getTopicEnum() != IotDeviceTopicEnum.SUB_PROPERTY_DOWNSTREAM_DESIRED_SET) {
                return;
            }

            IotDeviceMessage message = event.getMessage();
            log.debug("[handlePropertyDownstreamDesiredSetEvent][处理属性期望值设置下行消息，messageId: {}, topic: {}, deviceId: {}]",
                    message.getId(), message.getTopic(), message.getDeviceId());

            // 已带 serverId 说明调用方已路由到网关 Topic，此处无需再转发
            if (StrUtil.isNotBlank(message.getServerId())) {
                return;
            }

            Long deviceId = IotDeviceMessageUtils.parseLongDeviceIdOrNull(message.getDeviceId());
            if (deviceId == null) {
                return;
            }

            DeviceServerIdService deviceServerIdService;
            IotDeviceMessageProducer producer;
            try {
                deviceServerIdService = SpringUtil.getBean(DeviceServerIdService.class);
                producer = SpringUtil.getBean(IotDeviceMessageProducer.class);
            } catch (Exception e) {
                log.debug("[handlePropertyDownstreamDesiredSetEvent][依赖 Bean 不可用，跳过网关转发]");
                return;
            }
            if (deviceServerIdService == null || producer == null) {
                return;
            }

            String serverId = deviceServerIdService.getDeviceServerId(deviceId);
            if (StrUtil.isBlank(serverId)) {
                log.warn("[handlePropertyDownstreamDesiredSetEvent][设备未绑定 serverId，无法转发工业/网关写入，deviceId: {}]",
                        deviceId);
                return;
            }

            message.setServerId(serverId);
            producer.sendDeviceMessageToGateway(serverId, message);
            log.debug("[handlePropertyDownstreamDesiredSetEvent][已转发到网关 Topic，deviceId: {}, serverId: {}]",
                    deviceId, serverId);
        } catch (Exception e) {
            log.error("[handlePropertyDownstreamDesiredSetEvent][处理属性期望值设置下行消息失败，messageId: {}, topic: {}]",
                    event.getMessage() != null ? event.getMessage().getId() : null,
                    event.getMessage() != null ? event.getMessage().getTopic() : null, e);
        }
    }
}
