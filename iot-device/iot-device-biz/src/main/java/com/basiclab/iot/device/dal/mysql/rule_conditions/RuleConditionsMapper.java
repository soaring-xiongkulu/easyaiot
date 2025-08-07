package com.basiclab.iot.device.dal.mysql.rule_conditions;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.mybatis.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.common.mybatis.core.mapper.BaseMapperX;
import com.basiclab.iot.device.dal.dataobject.rule_conditions.RuleConditionsDO;
import org.apache.ibatis.annotations.Mapper;
import com.basiclab.iot.device.controller.admin.rule_conditions.vo.*;

/**
 * 规则条件 Mapper
 *
 * @author BasicLab
 */
@Mapper
public interface RuleConditionsMapper extends BaseMapperX<RuleConditionsDO> {

    default PageResult<RuleConditionsDO> selectPage(RuleConditionsPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<RuleConditionsDO>()
                .eqIfPresent(RuleConditionsDO::getRuleId, reqVO.getRuleId())
                .eqIfPresent(RuleConditionsDO::getConditionType, reqVO.getConditionType())
                .eqIfPresent(RuleConditionsDO::getDid, reqVO.getDid())
                .eqIfPresent(RuleConditionsDO::getPid, reqVO.getPid())
                .eqIfPresent(RuleConditionsDO::getServiceId, reqVO.getServiceId())
                .eqIfPresent(RuleConditionsDO::getPropertiesId, reqVO.getPropertiesId())
                .eqIfPresent(RuleConditionsDO::getComparisonMode, reqVO.getComparisonMode())
                .eqIfPresent(RuleConditionsDO::getComparisonValue, reqVO.getComparisonValue())
                .eqIfPresent(RuleConditionsDO::getCreateBy, reqVO.getCreateBy())
                .betweenIfPresent(RuleConditionsDO::getCreateTime, reqVO.getCreateTime())
                .eqIfPresent(RuleConditionsDO::getUpdateBy, reqVO.getUpdateBy())
                .orderByDesc(RuleConditionsDO::getId));
    }

}