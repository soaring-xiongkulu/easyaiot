package com.basiclab.iot.device.dal.mysql.rule_alarm;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.mybatis.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.common.mybatis.core.mapper.BaseMapperX;
import com.basiclab.iot.device.dal.dataobject.rule_alarm.RuleAlarmDO;
import org.apache.ibatis.annotations.Mapper;
import com.basiclab.iot.device.controller.admin.rule_alarm.vo.*;

/**
 * 规则告警 Mapper
 *
 * @author BasicLab
 */
@Mapper
public interface RuleAlarmMapper extends BaseMapperX<RuleAlarmDO> {

    default PageResult<RuleAlarmDO> selectPage(RuleAlarmPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<RuleAlarmDO>()
                .eqIfPresent(RuleAlarmDO::getRuleId, reqVO.getRuleId())
                .likeIfPresent(RuleAlarmDO::getRuleAlarmName, reqVO.getRuleAlarmName())
                .eqIfPresent(RuleAlarmDO::getRuleAlarmStatus, reqVO.getRuleAlarmStatus())
                .eqIfPresent(RuleAlarmDO::getRuleAlarmRemark, reqVO.getRuleAlarmRemark())
                .eqIfPresent(RuleAlarmDO::getRuleLevel, reqVO.getRuleLevel())
                .eqIfPresent(RuleAlarmDO::getNoticeType, reqVO.getNoticeType())
                .eqIfPresent(RuleAlarmDO::getCreateBy, reqVO.getCreateBy())
                .betweenIfPresent(RuleAlarmDO::getCreateTime, reqVO.getCreateTime())
                .eqIfPresent(RuleAlarmDO::getUpdateBy, reqVO.getUpdateBy())
                .orderByDesc(RuleAlarmDO::getId));
    }

}