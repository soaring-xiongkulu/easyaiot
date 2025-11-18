package com.basiclab.iot.sink.biz;

import cn.hutool.core.util.StrUtil;
import cn.hutool.extra.spring.SpringUtil;
import com.basiclab.iot.sink.enums.IotDeviceTopicEnum;
import com.basiclab.iot.sink.enums.IotDeviceTopicMethodMapping;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;
import com.basiclab.iot.sink.mq.producer.IotDeviceMessageProducer;
import com.basiclab.iot.sink.protocol.mqtt.manager.IotMqttConnectionManager;
import com.basiclab.iot.sink.service.DeviceServerIdService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnBean;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.stereotype.Service;

import java.util.List;

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

        // 数据下行前置处理：根据 Topic 标准映射验证并标准化 method 字段
        normalizeDownstreamMethodByTopic(message);

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

        // 数据下行前置处理：根据 Topic 标准映射验证并标准化 method 字段
        normalizeDownstreamMethodByTopic(message);

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

        // 数据下行前置处理：根据 Topic 标准映射验证并标准化 method 字段
        normalizeDownstreamMethodByTopic(message);

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

    @Override
    public int closeConnection(List<String> clientIds) {
        if (clientIds == null || clientIds.isEmpty()) {
            log.warn("[closeConnection][客户端 ID 列表为空，忽略关闭]");
            return 0;
        }

        int successCount = 0;
        // 尝试从 Spring 容器中获取 IotMqttConnectionManager
        try {
            IotMqttConnectionManager connectionManager =
                    SpringUtil.getBean(IotMqttConnectionManager.class);
            
            if (connectionManager != null) {
                for (String clientId : clientIds) {
                    if (StrUtil.isNotBlank(clientId)) {
                        if (connectionManager.closeConnectionByClientId(clientId)) {
                            successCount++;
                        }
                    }
                }
            } else {
                log.warn("[closeConnection][IotMqttConnectionManager 不存在，无法关闭连接]");
            }
        } catch (Exception e) {
            log.error("[closeConnection][关闭连接异常，错误: {}]", e.getMessage(), e);
        }

        log.info("[closeConnection][关闭连接完成，客户端 ID 列表: {}，成功关闭: {}]", clientIds, successCount);
        return successCount;
    }

    /**
     * 根据 Topic 标准映射验证并标准化下行消息的 method 字段
     * <p>
     * 下行消息标准：
     * - 如果消息中的 method 与 Topic 标准映射不一致，会使用标准映射中的 method
     * - 如果消息中没有 method，会根据 Topic 标准映射自动设置
     * - 如果消息中没有 topic，则无法进行转换，保持原有 method 不变
     *
     * @param message 设备消息
     */
    private void normalizeDownstreamMethodByTopic(IotDeviceMessage message) {
        if (message == null) {
            return;
        }

        String topic = message.getTopic();
        if (StrUtil.isBlank(topic)) {
            // 如果消息中没有 topic，无法进行转换，保持原有 method 不变
            if (StrUtil.isBlank(message.getMethod())) {
                log.debug("[normalizeDownstreamMethodByTopic][消息中没有 topic 和 method，无法进行标准化转换]");
            } else {
                log.debug("[normalizeDownstreamMethodByTopic][消息中没有 topic，保持原有 method: {}]", 
                        message.getMethod());
            }
            return;
        }

        // 匹配 Topic 枚举
        IotDeviceTopicEnum topicEnum = IotDeviceTopicEnum.matchTopic(topic);
        if (topicEnum == null) {
            // 如果无法匹配到 Topic 枚举，保持原有 method 不变
            log.debug("[normalizeDownstreamMethodByTopic][无法匹配到 Topic 枚举，topic: {}，保持原有 method: {}]", 
                    topic, message.getMethod());
            return;
        }

        // 只处理下行 Topic（needReply = true 表示下行消息）
        if (!topicEnum.isNeedReply()) {
            // 如果不是下行 Topic，跳过转换
            log.debug("[normalizeDownstreamMethodByTopic][Topic {} 不是下行 Topic，跳过转换]", topicEnum.name());
            return;
        }

        // 获取 Topic 对应的标准 Method
        String standardMethod = IotDeviceTopicMethodMapping.getMethodByTopic(topicEnum);
        
        if (StrUtil.isBlank(standardMethod)) {
            // 如果该 Topic 没有标准 Method 映射，保持原有 method 不变
            if (StrUtil.isBlank(message.getMethod())) {
                log.debug("[normalizeDownstreamMethodByTopic][下行 Topic {} 没有标准 Method 映射，且消息中 method 为空，保持为空]", 
                        topicEnum.name());
            } else {
                log.debug("[normalizeDownstreamMethodByTopic][下行 Topic {} 没有标准 Method 映射，保持原有 method: {}]", 
                        topicEnum.name(), message.getMethod());
            }
            return;
        }

        // 如果消息中的 method 为空，使用标准 Method
        if (StrUtil.isBlank(message.getMethod())) {
            message.setMethod(standardMethod);
            log.debug("[normalizeDownstreamMethodByTopic][下行消息 method 为空，根据 Topic {} 标准映射设置为: {}]", 
                    topicEnum.name(), standardMethod);
            return;
        }

        // 如果消息中的 method 与标准 Method 不一致，记录警告并使用标准 Method
        if (!standardMethod.equals(message.getMethod())) {
            log.warn("[normalizeDownstreamMethodByTopic][下行消息 method ({}) 与 Topic {} 标准映射 ({}) 不一致，使用标准 Method]", 
                    message.getMethod(), topicEnum.name(), standardMethod);
            message.setMethod(standardMethod);
        } else {
            log.debug("[normalizeDownstreamMethodByTopic][下行消息 method ({}) 与 Topic {} 标准映射一致]", 
                    message.getMethod(), topicEnum.name());
        }
    }

}

