package com.basiclab.iot.rule.service;

import com.baomidou.mybatisplus.extension.service.IService;
import com.basiclab.iot.rule.domain.Rule;
import com.basiclab.iot.rule.domain.model.RuleModel;

import java.util.List;

/**
 * @program: EasyAIoT
 * @description: ${description}
 * @packagename: com.mqttsnet.iot.rule.service
 * @author EasyAIoT
 * @date: 2025-07-21 18:47
 **/
public interface RuleService extends IService<Rule> {


    int deleteByPrimaryKey(Long id);

    Rule selectByRuleIdentification(String ruleIdentification);

    Rule insert(Rule record);

    int insertOrUpdate(Rule record);

    int insertOrUpdateSelective(Rule record);

    int insertSelective(Rule record);

    Rule selectByPrimaryKey(Long id);

    int updateByPrimaryKeySelective(Rule record);

    int updateByPrimaryKey(Rule record);

    int updateBatch(List<Rule> list);

    int updateBatchSelective(List<Rule> list);

    int batchInsert(List<Rule> list);

    List<Rule> selectRuleList(Rule rule);

    RuleModel selectFullRuleById(Long id);
}


