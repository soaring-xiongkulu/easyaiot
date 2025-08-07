package com.basiclab.iot.device.service.rule;

import org.springframework.stereotype.Service;
import javax.annotation.Resource;
import org.springframework.validation.annotation.Validated;

import com.basiclab.iot.device.controller.admin.rule.vo.*;
import com.basiclab.iot.device.dal.dataobject.rule.RuleDO;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.object.BeanUtils;

import com.basiclab.iot.device.dal.mysql.rule.RuleMapper;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.device.enums.ErrorCodeConstants.*;

/**
 * 规则信息 Service 实现类
 *
 * @author BasicLab
 */
@Service
@Validated
public class RuleServiceImpl implements RuleService {

    @Resource
    private RuleMapper ruleMapper;

    @Override
    public Long create(RuleSaveReqVO createReqVO) {
        // 插入
        RuleDO ruleDO = BeanUtils.toBean(createReqVO, RuleDO.class);
        ruleMapper.insert(ruleDO);
        // 返回
        return ruleDO.getId();
    }

    @Override
    public void update(RuleSaveReqVO updateReqVO) {
        // 校验存在
        validateExists(updateReqVO.getId());
        // 更新
        RuleDO updateObj = BeanUtils.toBean(updateReqVO, RuleDO.class);
        ruleMapper.updateById(updateObj);
    }

    @Override
    public void delete(Long id) {
        // 校验存在
        validateExists(id);
        // 删除
        ruleMapper.deleteById(id);
    }

    private void validateExists(Long id) {
        if (ruleMapper.selectById(id) == null) {
            throw exception(RULE_NOT_EXISTS);
        }
    }

    @Override
    public RuleDO get(Long id) {
        return ruleMapper.selectById(id);
    }

    @Override
    public PageResult<RuleDO> getPage(RulePageReqVO pageReqVO) {
        return ruleMapper.selectPage(pageReqVO);
    }

}