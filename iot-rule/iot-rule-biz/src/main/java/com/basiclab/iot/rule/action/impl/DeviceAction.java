package com.basiclab.iot.rule.action.impl;

import com.alibaba.fastjson.JSONObject;
import com.basiclab.iot.device.RemoteProductService;
import com.basiclab.iot.device.domain.device.vo.CommandWrapperParamReq;
import com.basiclab.iot.rule.action.AbstractAction;
import com.basiclab.iot.rule.domain.RuleActionCommands;
import com.basiclab.iot.rule.domain.model.enums.ActionEnum;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import javax.annotation.Resource;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * @author EasyAIoT
 * @desc   设备动作
 * @created 2025-07-10
 */
@Slf4j
@Component
public class DeviceAction extends AbstractAction {

    @Resource
    private RemoteProductService remoteProductService;

    @Override
    public String getType() {
        return ActionEnum.TYPE_DEVICE.getCode();
    }

    @Override
    public boolean execute(RuleActionCommands ruleActionCommands, ConcurrentHashMap<String, Map<String, String>> newDataMap) {
        String actionContent = ruleActionCommands.getActionContent();
        CommandWrapperParamReq commandWrapperParamReq = JSONObject.parseObject(actionContent, CommandWrapperParamReq.class);
        remoteProductService.issueCommands(commandWrapperParamReq);
        return true;
    }




}
