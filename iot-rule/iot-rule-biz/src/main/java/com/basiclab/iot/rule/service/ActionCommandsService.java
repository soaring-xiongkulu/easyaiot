package com.basiclab.iot.rule.service;

import java.util.List;

import com.baomidou.mybatisplus.extension.service.IService;
import com.basiclab.iot.rule.domain.RuleActionCommands;
import com.basiclab.iot.rule.domain.model.ActionCommandsModel;

/**
 * @program: EasyAIoT
 * @description: ${description}
 * @packagename: com.mqttsnet.iot.rule.service.impl
 * @author EasyAIoT
 * @date: 2025-12-04 21:39
 **/
public interface ActionCommandsService extends IService<RuleActionCommands> {


    int deleteByPrimaryKey(Integer id);

    int insert(RuleActionCommands record);

    int insertOrUpdate(RuleActionCommands record);

    int insertOrUpdateSelective(RuleActionCommands record);

    int insertSelective(RuleActionCommands record);

    RuleActionCommands selectByPrimaryKey(Integer id);

    int updateByPrimaryKeySelective(RuleActionCommands record);

    int updateByPrimaryKey(RuleActionCommands record);

    int updateBatch(List<RuleActionCommands> list);

    int updateBatchSelective(List<RuleActionCommands> list);

    int batchInsert(List<RuleActionCommands> list);

    List<RuleActionCommands> selectByActionCommandsSelective(RuleActionCommands ruleActionCommands);

    List<RuleActionCommands> actionCommandsByRuleId(String ruleIdentification);

    int deleteBatchByIds(Long[] ids);

    /**
     * 通过规则id获取动作
     * @param id    规则id
     * @return
     */
    List<RuleActionCommands> selectByRuleId(Long id);

    /**
     * 对象转化
     * @param ruleActionCommandsList 动作指令集合
     * @return
     */
    List<ActionCommandsModel> actionCommandsToActionCommandsModelList(List<RuleActionCommands> ruleActionCommandsList);

    /**
     * 通过规则id删除
     * @param id
     */
    void removeByRuleId(Long id);
}
