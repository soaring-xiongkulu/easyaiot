package com.basiclab.iot.broker.mqs.mqtt.handler;

import com.basiclab.iot.common.factory.ProtocolMessageAdapter;
import com.basiclab.iot.common.model.EncryptionDetailsDTO;
import com.basiclab.iot.broker.RemoteMqttBrokerOpenApi;
import com.basiclab.iot.broker.mqs.mqtt.handler.factory.AbstractMessageHandler;
import com.basiclab.iot.broker.mqs.mqtt.service.MqttEventCommandService;
import com.basiclab.iot.common.service.RedisService;
import com.basiclab.iot.device.RemoteDeviceOpenAnyService;
import com.basiclab.iot.device.domain.device.vo.DeviceCacheVO;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.Map;

/**
 * @program: basiclab
 * @description: 处理COMMAND_RESPONSE主题
 * @packagename: com.basiclab.iot.mqtt.handler
 * @author: EasyAIoT
 * @email: andywebjava@163.com
 * @date: 2023-05-05 23:00
 **/
@Slf4j
@Service
public class CommandResponseHandler extends AbstractMessageHandler implements TopicHandler {
    public CommandResponseHandler(RedisService redisService,
                                  RemoteDeviceOpenAnyService remoteDeviceOpenAnyService,
                                  RemoteMqttBrokerOpenApi remoteMqttBrokerOpenApi,
                                  ProtocolMessageAdapter protocolMessageAdapter) {
        super(redisService, remoteDeviceOpenAnyService, remoteMqttBrokerOpenApi, protocolMessageAdapter);
    }

    @Autowired
    private MqttEventCommandService mqttEventCommandService;

    /**
     * Handles MQTT messages, decrypts them, and processes the command.
     *
     * @param topic The topic the message was published to.
     * @param qos   The Quality of Service level of the message.
     * @param body  The raw body of the MQTT message.
     */
    @Override
    public void handle(String topic, String qos, String body) {
        if (!protocolMessageAdapter.validateProtocolData(body)) {
            log.warn("The protocol format is incorrect");
            return;
        }

        Map<String, String> variables = protocolMessageAdapter.extractVariables(topic);
        String deviceId = variables.get("deviceId");

        DeviceCacheVO deviceCacheVO = getDeviceCacheVO(deviceId);
        if (deviceCacheVO == null) {
            log.warn("Device with ID {} not found.", deviceId);
            return;
        }

        try {
            EncryptionDetailsDTO encryptionDetailsDTO = EncryptionDetailsDTO.builder()
                    .signKey(deviceCacheVO.getSignKey())
                    .encryptKey(deviceCacheVO.getEncryptKey())
                    .encryptVector(deviceCacheVO.getEncryptVector())
                    .build();
            String decryptedBody = protocolMessageAdapter.decryptMessage(body, encryptionDetailsDTO);
            mqttEventCommandService.processCommand(deviceCacheVO, decryptedBody);
        } catch (Exception e) {
            log.error("Failed to decrypt the message", e);
        }
    }


    @Override
    protected String processingTopicMessage(Object messageParam) throws Exception {
        return null;
    }

}
