
package com.basiclab.iot.rule.action;

import com.basiclab.iot.rule.domain.RuleActionCommands;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * @author IoT
 * @desc    规则动作定义
 * @created 2024-07-10
 */
public interface IAction {

    /**
     * 动作类型
     * @return
     */
    String getType();

    /**
     * 执行动作返回执行动作内容
     * @param ruleActionCommands    执行动作
     * @param newDataMap        单个规则下 涉及所有的设备下的属性值
     * @return
     */
    boolean execute(RuleActionCommands ruleActionCommands, ConcurrentHashMap<String, Map<String, String>> newDataMap);

}
