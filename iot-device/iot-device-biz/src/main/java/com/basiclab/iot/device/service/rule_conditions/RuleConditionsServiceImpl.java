package com.basiclab.iot.device.service.rule_conditions;

import org.springframework.stereotype.Service;
import javax.annotation.Resource;
import org.springframework.validation.annotation.Validated;

import com.basiclab.iot.device.controller.admin.rule_conditions.vo.*;
import com.basiclab.iot.device.dal.dataobject.rule_conditions.RuleConditionsDO;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.object.BeanUtils;

import com.basiclab.iot.device.dal.mysql.rule_conditions.RuleConditionsMapper;

import static com.basiclab.iot.device.enums.ErrorCodeConstants.RULE_CONDITIONS_NOT_EXISTS;
import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;

/**
 * 规则条件 Service 实现类
 *
 * @author BasicLab
 */
@Service
@Validated
public class RuleConditionsServiceImpl implements RuleConditionsService {

    @Resource
    private RuleConditionsMapper conditionsMapper;

    @Override
    public Long createConditions(RuleConditionsSaveReqVO createReqVO) {
        // 插入
        RuleConditionsDO conditions = BeanUtils.toBean(createReqVO, RuleConditionsDO.class);
        conditionsMapper.insert(conditions);
        // 返回
        return conditions.getId();
    }

    @Override
    public void updateConditions(RuleConditionsSaveReqVO updateReqVO) {
        // 校验存在
        validateConditionsExists(updateReqVO.getId());
        // 更新
        RuleConditionsDO updateObj = BeanUtils.toBean(updateReqVO, RuleConditionsDO.class);
        conditionsMapper.updateById(updateObj);
    }

    @Override
    public void deleteConditions(Long id) {
        // 校验存在
        validateConditionsExists(id);
        // 删除
        conditionsMapper.deleteById(id);
    }

    private void validateConditionsExists(Long id) {
        if (conditionsMapper.selectById(id) == null) {
            throw exception(RULE_CONDITIONS_NOT_EXISTS);
        }
    }

    @Override
    public RuleConditionsDO getConditions(Long id) {
        return conditionsMapper.selectById(id);
    }

    @Override
    public PageResult<RuleConditionsDO> getConditionsPage(RuleConditionsPageReqVO pageReqVO) {
        return conditionsMapper.selectPage(pageReqVO);
    }

}