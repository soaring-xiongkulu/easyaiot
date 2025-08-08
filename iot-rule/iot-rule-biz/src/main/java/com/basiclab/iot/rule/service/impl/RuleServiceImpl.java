package com.basiclab.iot.rule.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.basiclab.iot.common.exception.ServiceException;
import com.basiclab.iot.common.exception.job.TaskException;
import com.basiclab.iot.common.utils.bean.BeanUtils;
import com.basiclab.iot.job.RemoteJobService;
import com.basiclab.iot.job.domain.SysJob;
import com.basiclab.iot.rule.domain.Rule;
import com.basiclab.iot.rule.domain.RuleActionCommands;
import com.basiclab.iot.rule.domain.RuleConditions;
import com.basiclab.iot.rule.domain.model.RuleModel;
import com.basiclab.iot.rule.mapper.RuleMapper;
import com.basiclab.iot.rule.service.ActionCommandsService;
import com.basiclab.iot.rule.service.RuleConditionsService;
import com.basiclab.iot.rule.service.RuleService;
import com.basiclab.iot.rule.service.RuleLogService;
import lombok.extern.slf4j.Slf4j;
import org.quartz.SchedulerException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import javax.annotation.Resource;
import java.util.List;
import java.util.Objects;

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
@Transactional
public class RuleServiceImpl extends ServiceImpl<RuleMapper, Rule> implements RuleService {

   
    @Resource
    private RuleMapper ruleMapper;
    @Resource
    private RuleConditionsService ruleConditionsService;
    @Resource
    private RemoteJobService remoteJobService;

    @Resource
    private RuleLogService ruleLogService;

    @Resource
    private ActionCommandsService actionCommandsService;


    @Override
    public int deleteByPrimaryKey(Long id) {

        //删除关联条件
        return ruleMapper.deleteByPrimaryKey(id);
    }

    @Override
    public Rule selectByRuleIdentification(String ruleIdentification) {
        return ruleMapper.selectByRuleIdentification(ruleIdentification);
    }

    @Override
    public Rule insert(Rule rule) {
        //判断name重复
        Rule ruleQuery = new Rule();
        ruleQuery.setRuleName(rule.getRuleName());
        List<Rule> ruleList = ruleMapper.selectRuleList(ruleQuery);
        if (!ruleList.isEmpty()) {
            throw new ServiceException("规则名称重复");
        }
        String ruleIdentification = String.valueOf(System.nanoTime());
        rule.setRuleIdentification(ruleIdentification);
        //定时任务id与规则标识保持一致
        rule.setJobIdentification(ruleIdentification);
        boolean save = this.save(rule);
        if(save){
            // 状态开启的情况下创建定时任务轮询规则执行
            try {
                SysJob sysJob = new SysJob();
                sysJob.setJobName(rule.getRuleName() + "-job");
                sysJob.setJobGroup("RULE_TRIGGER");
                sysJob.setInvokeTarget("ruleConditionsTask.parsingRuleConditions('" + rule.getId() + "')");
                sysJob.setStatus("0".equals(rule.getStatus()) ?  "0" : "1");
                sysJob.setCronExpression(rule.getCronExpression());
                sysJob.setMisfirePolicy(rule.getMisfirePolicy());
                sysJob.setConcurrent(rule.getConcurrent());
                remoteJobService.add(sysJob);
            } catch (SchedulerException | TaskException e) {
                throw new RuntimeException(e);
            }
            return rule;
        }
        throw new ServiceException("添加规则失败");
    }


    @Override
    public int insertOrUpdate(Rule record) {
        return ruleMapper.insertOrUpdate(record);
    }

    @Override
    public int insertOrUpdateSelective(Rule record) {
        return ruleMapper.insertOrUpdateSelective(record);
    }

    @Override
    public int insertSelective(Rule record) {
        return ruleMapper.insertSelective(record);
    }

    @Override
    public Rule selectByPrimaryKey(Long id) {
        return ruleMapper.selectByPrimaryKey(id);
    }

    @Override
    public int updateByPrimaryKeySelective(Rule record) {
        //job-todo
        record.setJobIdentification(String.valueOf(System.nanoTime()));
        record.setUpdateBy(getSysUserName());
        return ruleMapper.updateByPrimaryKeySelective(record);
    }

    @Override
    public int updateByPrimaryKey(Rule record) {
        return ruleMapper.updateByPrimaryKey(record);
    }

    @Override
    public int updateBatch(List<Rule> list) {
        return ruleMapper.updateBatch(list);
    }

    @Override
    public int updateBatchSelective(List<Rule> list) {
        return ruleMapper.updateBatchSelective(list);
    }

    @Override
    public int batchInsert(List<Rule> list) {
        return ruleMapper.batchInsert(list);
    }
    @Override
    public List<Rule> selectRuleList(Rule rule){
        LambdaQueryWrapper<Rule> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(Objects.nonNull(rule.getRuleIdentification()) && !rule.getRuleIdentification().isEmpty(),Rule::getRuleIdentification, rule.getRuleIdentification());
        queryWrapper.eq(Objects.nonNull(rule.getRuleName()) && !rule.getRuleName().isEmpty(),Rule::getRuleName, rule.getRuleName());
        queryWrapper.eq(Objects.nonNull(rule.getAppId()) && !rule.getAppId().isEmpty(),Rule::getAppId, rule.getAppId());
        queryWrapper.eq(Objects.nonNull(rule.getStatus()) && !rule.getStatus().isEmpty(),Rule::getStatus, rule.getStatus());
        queryWrapper.eq(Objects.nonNull(rule.getMisfirePolicy()) && !rule.getMisfirePolicy().isEmpty(),Rule::getMisfirePolicy, rule.getMisfirePolicy());
        queryWrapper.eq(Objects.nonNull(rule.getJobIdentification()) && !rule.getJobIdentification().isEmpty(),Rule::getJobIdentification, rule.getJobIdentification());
        return this.list(queryWrapper);
    }

    @Override
    public RuleModel selectFullRuleById(Long id){
        Rule rule = ruleMapper.selectByPrimaryKey(id);
        if(null == rule){
            throw new ServiceException("rule not exist");
        }
        RuleModel  ruleModel = new RuleModel();
        BeanUtils.copyProperties(rule,ruleModel);
        List<RuleConditions> ruleConditionsList = ruleConditionsService.selectByRuleId(id);
        ruleModel.setRuleConditionsModelList(ruleConditionsService.ruleConditionsListToRuleConditionsModelList(ruleConditionsList));
        List<RuleActionCommands> ruleActionCommandsList = actionCommandsService.selectByRuleId(id);
        ruleModel.setActionCommandsModelList(actionCommandsService.actionCommandsToActionCommandsModelList(ruleActionCommandsList));
        return ruleModel;
    }


    private String getSysUserName(){
        return "admin";
    }
}


