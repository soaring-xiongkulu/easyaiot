package com.basiclab.iot.rule.action.impl;

import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONObject;
import com.basiclab.iot.common.domain.AjaxResult;
import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.device.RemoteDeviceService;
import com.basiclab.iot.device.constant.FunctionTypeConstant;
import com.basiclab.iot.device.constant.TdengineConstant;
import com.basiclab.iot.device.domain.device.vo.Device;
import com.basiclab.iot.message.RemoteMessageSendService;
import com.basiclab.iot.message.domain.model.dto.MessageMailSendDto;
import com.basiclab.iot.rule.action.IAction;
import com.basiclab.iot.rule.domain.AlarmRecord;
import com.basiclab.iot.rule.domain.RuleActionCommands;
import com.basiclab.iot.rule.domain.model.alarm.AlarmMessage;
import com.basiclab.iot.rule.domain.model.enums.ActionEnum;
import com.basiclab.iot.rule.service.AlarmRecordService;
import com.basiclab.iot.tdengine.RemoteTdEngineService;
import com.basiclab.iot.tdengine.domain.DeviceData;
import com.basiclab.iot.tdengine.domain.query.TDDeviceDataRequest;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import javax.annotation.Resource;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * @author EasyAIoT
 * @desc 告警动作
 * @created 2025-07-10
 */
@Component
@Slf4j
public class AlarmAction /*extends AbstractAction */ implements IAction {

    @Autowired
    private AlarmRecordService alarmRecordService;

    @Resource
    private RemoteDeviceService remoteDeviceService;
    @Resource
    private RemoteMessageSendService remoteMessageSendService;

    @Resource
    private RemoteTdEngineService remoteTdEngineService;

    @Override
    public String getType() {
        return ActionEnum.TYPE_ALARM.getCode();
    }

    @Override
    @SuppressWarnings("unchecked")
    public boolean execute(RuleActionCommands ruleActionCommands, ConcurrentHashMap<String, Map<String, String>> newDataMap) {
        String actionContent = ruleActionCommands.getActionContent();
        AlarmMessage alarmMessage = JSON.parseObject(actionContent, AlarmMessage.class);
        AlarmMessage.AlarmInfo alarmInfo = alarmMessage.getAlarmInfo();
        List<String> propertyCodeList = alarmInfo.getPropertyCodeList();
        String deviceIdentification = alarmInfo.getDeviceIdentification();
        String productIdentification = alarmInfo.getProductIdentification();

        //告警实时数据处理
        HashMap<String, Object> alarmMap = null;
        if ("ALL".equals(deviceIdentification)) {
            //匹配所有设备
            AjaxResult ajaxResult = remoteDeviceService.selectByProductIdentification(productIdentification);
            List<Device> deviceList = (List<Device>) ajaxResult.get("data");
            for (Device device : deviceList) {
                String singleDeviceIdentification = device.getDeviceIdentification();
                List<DeviceData> deviceDataList = getLatestData(singleDeviceIdentification, propertyCodeList);
                alarmMap = putLastDataToAlarmMap(deviceDataList);
            }
        } else {
            List<DeviceData> deviceDataList = getLatestData(deviceIdentification, propertyCodeList);
            alarmMap = putLastDataToAlarmMap(deviceDataList);
        }
        //处理告警信息逻辑(新增告警信息)  todo 创建时间 每隔5分钟记录一次 否则不记录
        AlarmRecord alarmRecord = AlarmRecord.builder()
                .alarmIdentification(String.valueOf(System.nanoTime()))
                .alarmLevel(alarmInfo.getAlarmLevel())
                .alarmName(alarmInfo.getAlarmName())
                .handledStatus(0)
                .content(alarmInfo.getContent())
                .alarmData(JSONObject.toJSONString(alarmMap))
                .build();
        alarmRecordService.save(alarmRecord);

        //处理通知逻辑
        List<AlarmMessage.NotifyAction> notifyActionList = alarmMessage.getNotifyAction();
        for (AlarmMessage.NotifyAction notifyAction : notifyActionList) {
            String msgId = notifyAction.getMsgId();
            int msgType = notifyAction.getMsgType();
            MessageMailSendDto messageMailSendDto = new MessageMailSendDto();
            messageMailSendDto.setMsgId(msgId);
            messageMailSendDto.setMsgType(msgType);
            if (msgType == 3) {
                //邮件需要内容
                messageMailSendDto.setContent(notifyAction.getContent());
                remoteMessageSendService.messageMailSend(messageMailSendDto);
            } else {
                remoteMessageSendService.messageSend(messageMailSendDto);
            }
        }
        return true;
    }

    /**
     * 将最新数据放到map中
     *
     * @param deviceDataList
     */
    private HashMap<String, Object> putLastDataToAlarmMap(List<DeviceData> deviceDataList) {
        HashMap<String, Object> alarmMap = new HashMap<>();
        for (DeviceData deviceData : deviceDataList) {
            String deviceIdentification = deviceData.getDeviceIdentification();
            String identifier = deviceData.getIdentifier();
            String dataValue = deviceData.getDataValue();
            HashMap<Object, Object> propertyValueMap = new HashMap<>();
            propertyValueMap.put(identifier, dataValue);
            alarmMap.put(deviceIdentification, propertyValueMap);
        }
        return alarmMap;
    }


    /**
     * TD查询最新设备属性
     *
     * @param deviceIdentification 设备标识
     * @param propertyCodeList     属性编码集合
     * @return
     */
    private List<DeviceData> getLatestData(String deviceIdentification, List<String> propertyCodeList) {
        TDDeviceDataRequest request = new TDDeviceDataRequest();
        request.setDeviceIdentification(deviceIdentification);
        request.setIdentifierList(propertyCodeList);
        request.setFunctionType(FunctionTypeConstant.PROPERTIES);
        request.setTdDatabaseName(TdengineConstant.IOT_DEVICE);
        request.setTdSuperTableName(TdengineConstant.DEVICE_DATA);
        R<List<DeviceData>> deviceDataListR = remoteTdEngineService.getLastRowsListByIdentifier(request);
        List<DeviceData> deviceDataList = null;
        if (deviceDataListR != null && deviceDataListR.getData() != null) {
            deviceDataList = deviceDataListR.getData();
        }
        return deviceDataList;
    }


}
