package com.basiclab.iot.broker.mqs.mqtt.handler;

import com.alibaba.fastjson.JSON;
import com.basiclab.iot.broker.RemoteMqttBrokerOpenApi;
import com.basiclab.iot.broker.mqs.mqtt.handler.factory.AbstractMessageHandler;
import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.common.factory.ProtocolMessageAdapter;
import com.basiclab.iot.common.model.EncryptionDetailsDTO;
import com.basiclab.iot.common.model.ProtocolDataMessageDTO;
import com.basiclab.iot.common.service.RedisService;
import com.basiclab.iot.device.RemoteDeviceOpenAnyService;
import com.basiclab.iot.device.domain.device.vo.DeviceCacheVO;
import com.basiclab.iot.device.domain.device.vo.TopoDeleteSubDeviceParam;
import com.basiclab.iot.device.domain.device.vo.TopoDeviceOperationResultVO;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.Map;

/**
 * @program: basiclab
 * @description: 处理DELETE_SUB_DEVICE主题
 * @packagename: com.basiclab.iot.mqtt.handler
 * @author: EasyAIoT
 * @email: andywebjava@163.com
 * @date: 2023-05-05 22:59
 **/
@Slf4j
@Service
public class DeleteSubDeviceHandler extends AbstractMessageHandler implements TopicHandler {

    private static final ObjectMapper objectMapper = new ObjectMapper();

    public DeleteSubDeviceHandler(RedisService redisService,
                                  RemoteDeviceOpenAnyService remoteDeviceOpenAnyService,
                                  RemoteMqttBrokerOpenApi remoteMqttBrokerOpenApi,
                                  ProtocolMessageAdapter protocolMessageAdapter) {
        super(redisService, remoteDeviceOpenAnyService, remoteMqttBrokerOpenApi, protocolMessageAdapter);
    }

    /**
     * @param topic the MQTT topic the message was received on.
     * @param qos   the quality of service level of the message.
     * @param body  the payload of the message.
     */
    @Override
    public void handle(String topic, String qos, String body) {
        if (!protocolMessageAdapter.validateProtocolData(body)) {
            log.warn("The protocol format is incorrect");
            return;
        }

        // Extract variables from the topic
        Map<String, String> stringStringMap = protocolMessageAdapter.extractVariables(topic);
        String version = stringStringMap.get("version");
        String deviceId = stringStringMap.get("deviceId");

        DeviceCacheVO deviceCacheVO = getDeviceCacheVO(deviceId);
        if (deviceCacheVO == null) {
            return;
        }

        try {
            ProtocolDataMessageDTO protocolDataMessageDTO = protocolMessageAdapter.parseProtocolDataMessage(body);
            // 构造 EncryptionDetails 对象
            EncryptionDetailsDTO encryptionDetailsDTO = EncryptionDetailsDTO.builder()
                    .signKey(deviceCacheVO.getSignKey())
                    .encryptKey(deviceCacheVO.getEncryptKey())
                    .encryptVector(deviceCacheVO.getEncryptVector())
                    .build();
            String dataBody = protocolMessageAdapter.decryptMessage(body, encryptionDetailsDTO);

            // Parse body
            TopoDeleteSubDeviceParam topoDeleteSubDeviceParam = JSON.toJavaObject(JSON.parseObject(dataBody), TopoDeleteSubDeviceParam.class);
            topoDeleteSubDeviceParam.setGatewayIdentification(deviceId);
            String resultDataBody = processingTopicMessage(topoDeleteSubDeviceParam);

            // Handle result
            ProtocolDataMessageDTO handleResult = protocolMessageAdapter.buildResponse(protocolDataMessageDTO, resultDataBody, encryptionDetailsDTO);

            // Determine response topic based on request topic
            String responseTopic = "/topo/deleteResponse";
            // Generate response topic string
            String responseTopicStr = generateResponseTopic(version, deviceId, responseTopic);

            // 序列化 handleResult 对象为 JSON 字符串
            String resultData = objectMapper.writeValueAsString(handleResult);

            // Push message to MQTT to notify device of successful/failed sub-device deletion
            sendMessage(responseTopicStr, qos, resultData, String.valueOf(deviceCacheVO.getAppId()));
        } catch (Exception e) {
            log.error("Failed to decrypt the message", e);
        }
    }

    /**
     * Process /topo/delete Topic for gateway device to delete sub-device
     *
     * @param topoDeleteSubDeviceParam delete device data
     * @return Processing result json
     */
    @Override
    protected String processingTopicMessage(Object topoDeleteSubDeviceParam) throws Exception {
        R<TopoDeviceOperationResultVO> mqttTopoDeleteDeviceResultVOR = remoteDeviceOpenAnyService.deleteSubDeviceByMqtt((TopoDeleteSubDeviceParam) topoDeleteSubDeviceParam);
        log.info("processingTopoDeleteTopic Processing result:{}", JSON.toJSONString(mqttTopoDeleteDeviceResultVOR));
        return JSON.toJSONString(mqttTopoDeleteDeviceResultVOR.getData());
    }
}

