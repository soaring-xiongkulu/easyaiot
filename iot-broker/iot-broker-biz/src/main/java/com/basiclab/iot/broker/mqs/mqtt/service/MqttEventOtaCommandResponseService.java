package com.basiclab.iot.broker.mqs.mqtt.service;

import com.alibaba.fastjson.JSON;
import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.device.RemoteDeviceOpenAnyService;
import com.basiclab.iot.device.domain.device.vo.DeviceCacheVO;
import com.basiclab.iot.device.domain.device.vo.OtaCommandResponseParam;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

/**
 * -----------------------------------------------------------------------------
 * File Name: MqttEventOtaCommandResponseService
 * -----------------------------------------------------------------------------
 * Description:
 * OTA 远程升级  mqtt事件业务层
 * -----------------------------------------------------------------------------
 *
 * @author EasyAIoT
 * @version 1.0
 * -----------------------------------------------------------------------------
 * Revision History:
 * Date         Author          Version     Description
 * --------      --------     -------   --------------------
 * 2024/1/18       xiaonannet        1.0        Initial creation
 * -----------------------------------------------------------------------------
 * @date 2024/1/18 22:38
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class MqttEventOtaCommandResponseService {

    @Autowired
    private RemoteDeviceOpenAnyService remoteDeviceOpenAnyService;


    /**
     * Saves the OTA command response from MQTT events.
     *
     * @param deviceCacheVO Device cache information for the device receiving the OTA command.
     * @param dataBody      The message body containing the OTA command response.
     */
    public void saveMqttEventOtaCommandResponse(DeviceCacheVO deviceCacheVO, String dataBody) {
        try {
            // Convert the JSON data body to an OtaCommandResponseParam object
            OtaCommandResponseParam otaCommandResponseParam = JSON.parseObject(dataBody, OtaCommandResponseParam.class);

            // Assuming a method that handles the actual saving of the response
            saveOtaCommandResponse(otaCommandResponseParam);

            // Log the successfully saved command response
            log.info("OTA command response successfully saved: {}", JSON.toJSONString(otaCommandResponseParam));

        } catch (Exception e) {
            // Log the error along with the stack trace for debugging
            log.error("Failed to process OTA command response: {}", dataBody, e);

            // Re-throw the exception to maintain the flow (can be customized as needed)
            throw new IllegalStateException("Failed to save OTA command response", e);
        }
    }

    // This is a placeholder for the actual saving logic
    private void saveOtaCommandResponse(OtaCommandResponseParam responseParam) {
        // Implementation for saving the response in your system
        R<OtaCommandResponseParam> otaCommandResponseParamR = remoteDeviceOpenAnyService.saveUpgradeRecordByMqtt(responseParam);
        log.info("otaCommandResponseParamR:{}", JSON.toJSONString(otaCommandResponseParamR));
    }


}
