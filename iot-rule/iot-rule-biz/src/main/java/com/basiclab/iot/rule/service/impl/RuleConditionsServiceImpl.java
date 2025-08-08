package com.basiclab.iot.rule.service.impl;


import cn.hutool.core.collection.CollectionUtil;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.basiclab.iot.common.utils.bean.BeanUtils;
import com.basiclab.iot.rule.domain.RuleActionCommands;
import com.basiclab.iot.rule.domain.RuleConditions;
import com.basiclab.iot.rule.domain.model.RuleConditionsModel;
import com.basiclab.iot.rule.domain.model.vo.ActionScheme;
import com.basiclab.iot.rule.domain.model.vo.RuleConditionActionVo;
import com.basiclab.iot.rule.mapper.RuleConditionsMapper;
import com.basiclab.iot.rule.service.ActionCommandsService;
import com.basiclab.iot.rule.service.RuleConditionsService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Objects;
import java.util.stream.Collectors;

/**
 * @program: basiclab
 * @description: ${description}
 * @packagename: com.mqttsnet.iot.rule.service.impl
 * @Author: Basiclab
 * @e-mainl: 853017739@qq.com
 * @date: 2024-07-21 18:47
 **/
@Slf4j
@Service
public class RuleConditionsServiceImpl extends ServiceImpl<RuleConditionsMapper, RuleConditions> implements RuleConditionsService {

    @Resource
    private RuleConditionsMapper ruleConditionsMapper;

    @Resource
    private ActionCommandsService actionCommandsService;

    @Override
    public int deleteByPrimaryKey(Long id) {
        return ruleConditionsMapper.deleteByPrimaryKey(id);
    }

    @Override
    public int insert(RuleConditions record) {
        return ruleConditionsMapper.insert(record);
    }

    @Override
    public int insertOrUpdate(RuleConditions record) {
        return ruleConditionsMapper.insertOrUpdate(record);
    }

    @Override
    public int insertOrUpdateSelective(RuleConditions record) {
        return ruleConditionsMapper.insertOrUpdateSelective(record);
    }

    @Override
    public int insertSelective(RuleConditions record) {
        return ruleConditionsMapper.insertSelective(record);
    }

    @Override
    public RuleConditions selectByPrimaryKey(Long id) {
        return ruleConditionsMapper.selectByPrimaryKey(id);
    }

    @Override
    public List<RuleConditions> selectByRuleId(Long ruleId) {
        return ruleConditionsMapper.selectByRuleId(ruleId);
    }

    @Override
    public int updateByPrimaryKeySelective(RuleConditions record) {
        return ruleConditionsMapper.updateByPrimaryKeySelective(record);
    }

    @Override
    public int updateByPrimaryKey(RuleConditions record) {
        return ruleConditionsMapper.updateByPrimaryKey(record);
    }

    @Override
    public Boolean updateBatch(List<RuleConditions> list) {
        return super.updateBatchById(list);
    }

    @Override
    public int updateBatchSelective(List<RuleConditions> list) {

        String sysUserName = getSysUserName();
        List<RuleConditions> updateRuleConditionsList = list.stream().map(s -> {
            s.setCreateBy(sysUserName);
            return s;
        }).collect(Collectors.toList());

        return ruleConditionsMapper.updateBatchSelective(updateRuleConditionsList);
    }

    @Override
    public List<RuleConditions> batchInsert(List<RuleConditions> list) {

        String sysUserName = getSysUserName();
        List<RuleConditions> insertList = list.stream().map(s -> {
            s.setCreateBy(sysUserName);
            s.setUpdateBy(sysUserName);
            return s;
        }).collect(Collectors.toList());
        ruleConditionsMapper.batchInsert(insertList);
        return insertList;
    }

    public int deleteBatchByIds(Long[] ids) {
        return ruleConditionsMapper.deleteBatchByIds(ids);
    }

    /**
     * 更新条件和动作信息
     *
     * @param ruleConditionActionVo 规则条件动作对象
     * @return
     */
    @Override
    public RuleConditions updateRuleConditionAction(RuleConditionActionVo ruleConditionActionVo) {
        //处理规则条件
        RuleConditions ruleConditions = RuleConditions.builder()
                .ruleId(ruleConditionActionVo.getRuleId())
                .conditionScheme(ruleConditionActionVo.getConditionScheme())
                .conditionType(ruleConditionActionVo.getConditionType())
                .updateBy("admin")
                .createBy("admin")
                .updateTime(LocalDateTime.now())
                .build();
        super.saveOrUpdate(ruleConditions);
        //处理规则动作
        List<ActionScheme> conditionActionUpdateVos = ruleConditionActionVo.getConditionActionUpdateVos();
        if (CollectionUtil.isEmpty(conditionActionUpdateVos)) {
            return ruleConditions;
        }
        List<RuleActionCommands> ruleActionCommandsList = conditionActionUpdateVos.stream().map(actionScheme -> {
            RuleActionCommands ruleActionCommands = new RuleActionCommands();
            BeanUtils.copyProperties(actionScheme, ruleActionCommands, "id");
            return ruleActionCommands;
        }).collect(Collectors.toList());
        actionCommandsService.saveOrUpdateBatch(ruleActionCommandsList);
        return ruleConditions;
    }

    @Override
    public RuleConditions getOneByRuleId(Long ruleId) {
        LambdaQueryWrapper<RuleConditions> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(Objects.nonNull(ruleId), RuleConditions::getRuleId, ruleId);
        return getOne(queryWrapper);
    }

    @Override
    public List<RuleConditionsModel> ruleConditionsListToRuleConditionsModelList(List<RuleConditions> ruleConditionsList) {
        return ruleConditionsList.stream().map(
                ruleConditions -> {
                    RuleConditionsModel ruleConditionsModel = new RuleConditionsModel();
                    BeanUtils.copyProperties(ruleConditions, ruleConditionsModel);
                    return ruleConditionsModel;
                }
        ).collect(Collectors.toList());
    }

    @Override
    public void removeByRuleId(Long id) {
        LambdaQueryWrapper<RuleConditions> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(RuleConditions::getRuleId, id);
        this.remove(queryWrapper);
    }

    private String getSysUserName() {
        return "admin";
    }
}

