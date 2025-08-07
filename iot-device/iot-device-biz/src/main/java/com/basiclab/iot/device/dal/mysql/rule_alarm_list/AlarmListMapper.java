package com.basiclab.iot.device.dal.mysql.rule_alarm_list;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.mybatis.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.common.mybatis.core.mapper.BaseMapperX;
import com.basiclab.iot.device.dal.dataobject.rule_alarm_list.RuleAlarmListDO;
import org.apache.ibatis.annotations.Mapper;
import com.basiclab.iot.device.controller.admin.rule_alarm_list.vo.*;

/**
 * 告警列 Mapper
 *
 * @author BasicLab
 */
@Mapper
public interface AlarmListMapper extends BaseMapperX<RuleAlarmListDO> {

    default PageResult<RuleAlarmListDO> selectPage(RuleAlarmListPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<RuleAlarmListDO>()
                .betweenIfPresent(RuleAlarmListDO::getAlarmTime, reqVO.getAlarmTime())
                .likeIfPresent(RuleAlarmListDO::getAlarmName, reqVO.getAlarmName())
                .eqIfPresent(RuleAlarmListDO::getAlarmLevel, reqVO.getAlarmLevel())
                .eqIfPresent(RuleAlarmListDO::getAlarmDescribe, reqVO.getAlarmDescribe())
                .eqIfPresent(RuleAlarmListDO::getProcessingResult, reqVO.getProcessingResult())
                .eqIfPresent(RuleAlarmListDO::getProcessingOpinions, reqVO.getProcessingOpinions())
                .eqIfPresent(RuleAlarmListDO::getAlarmContent, reqVO.getAlarmContent())
                .eqIfPresent(RuleAlarmListDO::getProcessingPeople, reqVO.getProcessingPeople())
                .betweenIfPresent(RuleAlarmListDO::getProcessingTime, reqVO.getProcessingTime())
                .orderByDesc(RuleAlarmListDO::getId));
    }

}