package com.basiclab.iot.sink.biz;

import cn.hutool.core.util.StrUtil;
import cn.hutool.extra.spring.SpringUtil;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;
import com.basiclab.iot.sink.mq.producer.IotDeviceMessageProducer;
import com.basiclab.iot.sink.service.DeviceServerIdService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnBean;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.stereotype.Service;

/**
 * IoT 下行消息发送 API 实现类
 * <p>
 * 此实现类在 sink-api 中，可以被其他模块直接使用
 * <p>
 * 需要 IotDeviceMessageProducer 和 DeviceServerIdService（可选）存在
 *
 * @author 翱翔的雄库鲁
 */
@Service
@Slf4j
@RequiredArgsConstructor
@ConditionalOnBean(IotDeviceMessageProducer.class)
@ConditionalOnMissingBean(IotDownstreamMessageApi.class)
public class IotDownstreamMessageApiImpl implements IotDownstreamMessageApi {

    private final IotDeviceMessageProducer deviceMessageProducer;

    @Override
    public void sendDownstreamMessage(IotDeviceMessage message) {
        if (message == null) {
            log.warn("[sendDownstreamMessage][消息为空，忽略发送]");
            return;
        }

        if (message.getDeviceId() == null) {
            log.warn("[sendDownstreamMessage][设备 ID 为空，忽略发送，消息 ID: {}]", message.getId());
            return;
        }

        // 如果消息中指定了 serverId，则发送到对应的网关
        String serverId = message.getServerId();
        if (StrUtil.isNotBlank(serverId)) {
            log.debug("[sendDownstreamMessage][发送下行消息到指定网关，设备 ID: {}，serverId: {}，消息 ID: {}]",
                    message.getDeviceId(), serverId, message.getId());
            deviceMessageProducer.sendDeviceMessageToGateway(serverId, message);
        } else {
            // 如果未指定 serverId，则发送到通用 Topic，由所有网关实例处理
            log.debug("[sendDownstreamMessage][发送下行消息到通用 Topic，设备 ID: {}，消息 ID: {}]",
                    message.getDeviceId(), message.getId());
            deviceMessageProducer.sendDeviceMessage(message);
        }
    }

    @Override
    public void sendDownstreamMessageToGateway(String serverId, IotDeviceMessage message) {
        if (StrUtil.isBlank(serverId)) {
            log.warn("[sendDownstreamMessageToGateway][serverId 为空，忽略发送，消息 ID: {}]", 
                    message != null ? message.getId() : null);
            return;
        }

        if (message == null) {
            log.warn("[sendDownstreamMessageToGateway][消息为空，忽略发送，serverId: {}]", serverId);
            return;
        }

        if (message.getDeviceId() == null) {
            log.warn("[sendDownstreamMessageToGateway][设备 ID 为空，忽略发送，serverId: {}，消息 ID: {}]",
                    serverId, message.getId());
            return;
        }

        log.debug("[sendDownstreamMessageToGateway][发送下行消息到指定网关，设备 ID: {}，serverId: {}，消息 ID: {}]",
                message.getDeviceId(), serverId, message.getId());
        deviceMessageProducer.sendDeviceMessageToGateway(serverId, message);
    }

    @Override
    public void sendDownstreamMessageByDeviceId(Long deviceId, IotDeviceMessage message) {
        if (deviceId == null) {
            log.warn("[sendDownstreamMessageByDeviceId][设备 ID 为空，忽略发送]");
            return;
        }

        if (message == null) {
            log.warn("[sendDownstreamMessageByDeviceId][消息为空，忽略发送，设备 ID: {}]", deviceId);
            return;
        }

        // 设置设备 ID
        message.setDeviceId(deviceId);

        // 从 Redis 中查找设备对应的 serverId（如果 DeviceServerIdService 存在）
        DeviceServerIdService deviceServerIdService = null;
        try {
            deviceServerIdService = SpringUtil.getBean(DeviceServerIdService.class);
        } catch (Exception e) {
            log.debug("[sendDownstreamMessageByDeviceId][DeviceServerIdService 不存在，将发送到通用 Topic，设备 ID: {}]", deviceId);
        }

        String serverId = null;
        if (deviceServerIdService != null) {
            serverId = deviceServerIdService.getDeviceServerId(deviceId);
        }

        if (StrUtil.isNotBlank(serverId)) {
            log.debug("[sendDownstreamMessageByDeviceId][找到设备 serverId，发送到指定网关，设备 ID: {}，serverId: {}，消息 ID: {}]",
                    deviceId, serverId, message.getId());
            deviceMessageProducer.sendDeviceMessageToGateway(serverId, message);
        } else {
            // 如果找不到 serverId，则发送到通用 Topic，由所有网关实例处理
            log.debug("[sendDownstreamMessageByDeviceId][未找到设备 serverId，发送到通用 Topic，设备 ID: {}，消息 ID: {}]",
                    deviceId, message.getId());
            deviceMessageProducer.sendDeviceMessage(message);
        }
    }

}

