package com.basiclab.iot.rule.service;

import com.baomidou.mybatisplus.extension.service.IService;
import com.basiclab.iot.rule.domain.RuleConditions;
import com.basiclab.iot.rule.domain.model.RuleConditionsModel;
import com.basiclab.iot.rule.domain.model.vo.RuleConditionActionVo;

import java.util.List;

/**
 * @program: EasyAIoT
 * @description: ${description}
 * @packagename: com.mqttsnet.iot.rule.service
 * @author EasyAIoT
 * @date: 2025-07-21 18:47
 **/
public interface RuleConditionsService extends IService<RuleConditions> {


    int deleteByPrimaryKey(Long id);

    int insert(RuleConditions record);

    int insertOrUpdate(RuleConditions record);

    int insertOrUpdateSelective(RuleConditions record);

    int insertSelective(RuleConditions record);

    RuleConditions selectByPrimaryKey(Long id);

    List<RuleConditions> selectByRuleId(Long ruleId);

    int updateByPrimaryKeySelective(RuleConditions record);

    int updateByPrimaryKey(RuleConditions record);

    Boolean updateBatch(List<RuleConditions> list);

    int updateBatchSelective(List<RuleConditions> list);

    List<RuleConditions> batchInsert(List<RuleConditions> list);

    int deleteBatchByIds(Long[] ids);

    /**
     * 更新规则条件和动作动作
     *
     * @param ruleConditionVo 规则条件对象
     * @return
     */
    RuleConditions updateRuleConditionAction(RuleConditionActionVo ruleConditionVo);

    /**
     * 通过ruleId获取条件
     *
     * @param ruleId
     * @return
     */
    RuleConditions getOneByRuleId(Long ruleId);

    /**
     * 条件列表获取详情
     *
     * @param ruleConditionsList
     * @return
     */
    List<RuleConditionsModel> ruleConditionsListToRuleConditionsModelList(List<RuleConditions> ruleConditionsList);

    /**
     * 通过规则id删除
     *
     * @param id 规则id
     */
    void removeByRuleId(Long id);
}

