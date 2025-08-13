package com.basiclab.iot.broker.mqs.mqtt.service;

import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.common.enums.ResultEnum;
import com.basiclab.iot.device.RemoteDeviceActionService;
import com.basiclab.iot.device.domain.device.vo.DeviceEvent;
import com.basiclab.iot.device.enums.device.DeviceEventTypeEnum;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;

/**
 * @description: MqttEventActionHandler
 * @packagename: com.basiclab.iot.mqtt.handler
 * @author: EasyAIoT
 * @email: andywebjava@163.com
 * @date: 2023-08-20 16:09
 **/
@Slf4j
@Service
@RequiredArgsConstructor
public class MqttEventActionService {

    @Resource
    private RemoteDeviceActionService remoteDeviceActionService;

    /**
     * 保存MQTT事件动作
     *
     * @param deviceIdentification 设备标识
     * @param eventMessage         事件消息
     * @param actionType           动作类型
     * @param describable          描述
     */
    public void saveMqttEventAction(String deviceIdentification, String eventMessage, DeviceEventTypeEnum actionType, String describable) {
        log.info("Save MQTT event action: deviceIdentification={}, actionType={}, describable={}", deviceIdentification, actionType, describable);

        // save device action
        DeviceEvent deviceEvent = new DeviceEvent()
                .setDeviceIdentification(deviceIdentification)
                .setEventType(actionType.getEvent())
                .setStatus(ResultEnum.SUCCESS.getMessage())
                .setMessage(eventMessage);

        R deviceActionR = remoteDeviceActionService.add(deviceEvent);
        if (ResultEnum.SUCCESS.getCode() != deviceActionR.getCode()) {
            log.info("Save device action success: deviceEvent={}", deviceActionR.getData());
        } else {
            log.error("Save device action failed: deviceEvent={}", deviceActionR.getData());
        }
    }
}