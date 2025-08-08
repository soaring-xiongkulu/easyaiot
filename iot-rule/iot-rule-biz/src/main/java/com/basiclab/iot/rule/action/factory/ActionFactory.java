package com.basiclab.iot.rule.action.factory;

import cn.hutool.extra.spring.SpringUtil;
import com.basiclab.iot.rule.action.IAction;
import com.basiclab.iot.rule.action.impl.AlarmAction;
import com.basiclab.iot.rule.action.impl.DeviceAction;
import com.basiclab.iot.rule.domain.model.enums.ActionEnum;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.annotation.Bean;
import org.springframework.stereotype.Component;

import javax.annotation.PostConstruct;
import java.util.concurrent.ConcurrentHashMap;

/**
 * @author EasyAIoT
 * @desc    场景规则处理实例工厂
 * @created 2025-07-10
 */
@Component
@Slf4j
public class ActionFactory {

    private ConcurrentHashMap<String, IAction> actionMap = new ConcurrentHashMap<>();



    @PostConstruct
    public void init() {
//        actionMap.put(ActionEnum.TYPE_DEVICE.getCode(), new DeviceAction());
//        actionMap.put(ActionEnum.TYPE_ALARM.getCode(), new AlarmAction());
        actionMap.put(ActionEnum.TYPE_DEVICE.getCode(), SpringUtil.getBean(DeviceAction.class));
        actionMap.put(ActionEnum.TYPE_ALARM.getCode(), SpringUtil.getBean(AlarmAction.class));
    }


    public IAction getActionByType(String type) {
        return actionMap.get(type);
    }



}
