package com.basiclab.iot.rule.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.basiclab.iot.rule.domain.RuleActionCommands;
import com.basiclab.iot.rule.domain.model.ActionCommandsModel;
import com.basiclab.iot.rule.mapper.ActionCommandsMapper;
import com.basiclab.iot.rule.service.ActionCommandsService;
import org.springframework.beans.BeanUtils;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.util.List;
import java.util.stream.Collectors;

/**
 * @program: EasyAIoT
 * @description: ${description}
 * @packagename: com.mqttsnet.iot.rule.service
 * @author EasyAIoT
 * @date: 2025-12-04 21:39
 **/
@Service
public class ActionCommandsServiceImpl extends ServiceImpl<ActionCommandsMapper, RuleActionCommands> implements ActionCommandsService {


    @Resource
    private ActionCommandsMapper actionCommandsMapper;

    @Override
    public int deleteByPrimaryKey(Integer id) {
        return actionCommandsMapper.deleteByPrimaryKey(id);
    }

    @Override
    public int insert(RuleActionCommands record) {
        return actionCommandsMapper.insert(record);
    }

    @Override
    public int insertOrUpdate(RuleActionCommands record) {
        return actionCommandsMapper.insertOrUpdate(record);
    }

    @Override
    public int insertOrUpdateSelective(RuleActionCommands record) {
        return actionCommandsMapper.insertOrUpdateSelective(record);
    }

    @Override
    public int insertSelective(RuleActionCommands record) {
        return actionCommandsMapper.insertSelective(record);
    }

    @Override
    public RuleActionCommands selectByPrimaryKey(Integer id) {
        return actionCommandsMapper.selectByPrimaryKey(id);
    }

    @Override
    public int updateByPrimaryKeySelective(RuleActionCommands record) {
        return actionCommandsMapper.updateByPrimaryKeySelective(record);
    }

    @Override
    public int updateByPrimaryKey(RuleActionCommands record) {
        return actionCommandsMapper.updateByPrimaryKey(record);
    }

    @Override
    public int updateBatch(List<RuleActionCommands> list) {
        return actionCommandsMapper.updateBatch(list);
    }

    @Override
    public int updateBatchSelective(List<RuleActionCommands> list) {
        String sysUserName = getSysUserName();
        List<RuleActionCommands> insertList = list.stream().map(s -> {
            s.setUpdateBy(sysUserName);
            return s;
        }).collect(Collectors.toList());
        return actionCommandsMapper.updateBatchSelective(list);
    }

    @Override
    public int batchInsert(List<RuleActionCommands> list) {

        String sysUserName = getSysUserName();
        List<RuleActionCommands> insertList = list.stream().map(s -> {
            s.setCreateBy(sysUserName);
            s.setUpdateBy(sysUserName);
            return s;
        }).collect(Collectors.toList());

        return actionCommandsMapper.batchInsert(insertList);
    }

    @Override
    public List<RuleActionCommands> selectByActionCommandsSelective(RuleActionCommands ruleActionCommands) {
        return actionCommandsMapper.selectByActionCommandsSelective(ruleActionCommands);
    }

    @Override
    public List<RuleActionCommands> actionCommandsByRuleId(String ruleId) {
        return actionCommandsMapper.actionCommandsByRuleId(ruleId);
    }

    @Override
    public int deleteBatchByIds(Long[] ids) {
        return actionCommandsMapper.deleteBatchByIds(ids);
    }

    @Override
    public List<RuleActionCommands> selectByRuleId(Long id) {
        LambdaQueryWrapper<RuleActionCommands> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(RuleActionCommands::getRuleId, id);
        return list(queryWrapper);
    }

    @Override
    public List<ActionCommandsModel> actionCommandsToActionCommandsModelList(List<RuleActionCommands> ruleActionCommandsList) {
        return ruleActionCommandsList.stream().map(actionCommands -> {
            ActionCommandsModel actionCommandsModel = new ActionCommandsModel();
            BeanUtils.copyProperties(actionCommands, actionCommandsModel);
            return actionCommandsModel;
        }).collect(Collectors.toList());
    }

    @Override
    public void removeByRuleId(Long id) {
        LambdaQueryWrapper<RuleActionCommands> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(RuleActionCommands::getRuleId, id);
        this.remove(queryWrapper);
    }


    private String getSysUserName() {
        return "admin";
    }

}
