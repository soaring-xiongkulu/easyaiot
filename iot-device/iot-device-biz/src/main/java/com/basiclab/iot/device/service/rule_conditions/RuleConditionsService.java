package com.basiclab.iot.device.service.rule_conditions;

import javax.validation.*;
import com.basiclab.iot.device.controller.admin.rule_conditions.vo.*;
import com.basiclab.iot.device.dal.dataobject.rule_conditions.RuleConditionsDO;
import com.basiclab.iot.common.domain.PageResult;

/**
 * 规则条件 Service 接口
 *
 * @author BasicLab
 */
public interface RuleConditionsService {

    /**
     * 创建规则条件
     *
     * @param createReqVO 创建信息
     * @return 编号
     */
    Long createConditions(@Valid RuleConditionsSaveReqVO createReqVO);

    /**
     * 更新规则条件
     *
     * @param updateReqVO 更新信息
     */
    void updateConditions(@Valid RuleConditionsSaveReqVO updateReqVO);

    /**
     * 删除规则条件
     *
     * @param id 编号
     */
    void deleteConditions(Long id);

    /**
     * 获得规则条件
     *
     * @param id 编号
     * @return 规则条件
     */
    RuleConditionsDO getConditions(Long id);

    /**
     * 获得规则条件分页
     *
     * @param pageReqVO 分页查询
     * @return 规则条件分页
     */
    PageResult<RuleConditionsDO> getConditionsPage(RuleConditionsPageReqVO pageReqVO);

}