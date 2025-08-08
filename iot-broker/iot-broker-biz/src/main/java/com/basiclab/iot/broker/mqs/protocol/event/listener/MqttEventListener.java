package com.basiclab.iot.broker.mqs.protocol.event.listener;

import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONObject;
import com.basiclab.iot.broker.domain.enumeration.MqttEventEnum;
import com.basiclab.iot.broker.domain.protocol.MqttEvent;
import com.basiclab.iot.broker.mqs.mqtt.event.publisher.MqttEventPublisher;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.lang3.StringUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.event.EventListener;
import org.springframework.retry.annotation.Backoff;
import org.springframework.retry.annotation.Retryable;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;

import java.util.Optional;

/**
 * -----------------------------------------------------------------------------
 * File Name: MqttEventListener
 * -----------------------------------------------------------------------------
 * Description:
 * MQTT事件监听器
 * -----------------------------------------------------------------------------
 *
 * @author EasyAIoT
 * @version 1.0
 * -----------------------------------------------------------------------------
 * Revision History:
 * Date         Author          Version     Description
 * --------      --------     -------   --------------------
 * 2024/3/11       xiaonannet        1.0        Initial creation
 * -----------------------------------------------------------------------------
 * @date 2024/3/11 15:47
 */

@Component
@Slf4j
public class MqttEventListener {


    @Autowired
    private MqttEventPublisher eventPublisher;

    /**
     * 发布MQTT事件
     *
     * @param event 事件消息
     */
    @EventListener
    @Async("brokerAsync-mqttMsg")
    @Retryable(value = {Exception.class}, maxAttempts = 3, backoff = @Backoff(delay = 1000))
    public void handleMqttEvent(MqttEvent event) {
        log.info("处理MQTT事件: 消息={}", event.getMessage());
        try {
            JSONObject iotMessage = JSON.parseObject(String.valueOf(event.getMessage()));
            String eventStr = Optional.ofNullable(iotMessage.getString("event"))
                    .orElse("");
            Optional<String> tenantId = Optional.ofNullable(iotMessage.getString("tenantId"))
                    .filter(StringUtils::isNotBlank)
                    .map(String::valueOf);
            if (StringUtils.isEmpty(eventStr) || !tenantId.isPresent()) {
                log.warn("event or tenantId cannot be empty {}", eventStr);
                return;
            }
            Optional<MqttEventEnum> optionalEvent = MqttEventEnum.getMqttEventEnum(iotMessage.get("event").toString());
            optionalEvent.ifPresent(eventEnum -> {
                switch (eventEnum) {
                    case CONNECT:
                        eventPublisher.publishMqttConnectEvent(MqttEventEnum.CONNECT, iotMessage.toJSONString());
                        break;
                    case CLOSE:
                        eventPublisher.publishMqttCloseEvent(MqttEventEnum.CLOSE, iotMessage.toJSONString());
                        break;
                    case DISCONNECT:
                        eventPublisher.publishMqttDisconnectEvent(MqttEventEnum.DISCONNECT, iotMessage.toJSONString());
                        break;
                    case PUBLISH:
                        eventPublisher.publishMqttPublishEvent(MqttEventEnum.PUBLISH, iotMessage.toJSONString());
                        break;
                    case SUBSCRIBE:
                        eventPublisher.publishMqttSubscribeEvent(MqttEventEnum.SUBSCRIBE, iotMessage.toJSONString());
                        break;
                    case UNSUBSCRIBE:
                        eventPublisher.publishMqttUnsubscribeEvent(MqttEventEnum.UNSUBSCRIBE, iotMessage.toJSONString());
                        break;
                    case PING:
                        eventPublisher.publishMqttPingEvent(MqttEventEnum.PING, iotMessage.toJSONString());
                        break;
                    default:
                        break;
                }
            });
        } catch (Exception e) {
            log.error("处理MQTT事件-->处理失败，失败原因：{}", e.getMessage());
        }
    }

}
