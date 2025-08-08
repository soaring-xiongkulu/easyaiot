package com.basiclab.iot.rule.service;

import com.baomidou.mybatisplus.extension.service.IService;
import com.basiclab.iot.rule.domain.RuleLog;

import java.util.List;

/**
 * @author IoT
 * @desc
 * @created 2024-07-11
 */
public interface RuleLogService extends IService<RuleLog> {
    /**
     * 通过规则id获取日志信息 获取最新那条日志记录
     * @param ruleId    规则id
     * @return
     */
    RuleLog getByRuleId(String ruleId);

    /**
     * 通过规则id获取日志列表
     * @param ruleId    规则id
     * @return
     */
    List<RuleLog> selectListByRuleId(Long ruleId);
}
