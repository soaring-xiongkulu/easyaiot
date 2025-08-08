package com.basiclab.iot.rule.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.basiclab.iot.rule.domain.RuleLog;
import com.basiclab.iot.rule.mapper.RuleLogMapper;
import com.basiclab.iot.rule.service.RuleLogService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * @author EasyAIoT
 * @desc
 * @created 2025-07-11
 */
@Service
@Slf4j
public class RuleLogServiceImpl extends ServiceImpl<RuleLogMapper, RuleLog> implements RuleLogService {


    @Override
    public RuleLog getByRuleId(String ruleId) {
        LambdaQueryWrapper<RuleLog> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(RuleLog::getRuleId, ruleId);
        queryWrapper.orderByDesc(RuleLog::getCreateTime);
        return list(queryWrapper).get(0);
    }

    @Override
    public List<RuleLog> selectListByRuleId(Long ruleId) {
        LambdaQueryWrapper<RuleLog> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(RuleLog::getRuleId, ruleId);
        queryWrapper.orderByDesc(RuleLog::getCreateTime);
        return list(queryWrapper);
    }
}
