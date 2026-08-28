package com.basiclab.iot.flow.dal.pgsql;

import com.basiclab.iot.common.core.mapper.BaseMapperX;
import com.basiclab.iot.common.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.flow.dal.dataobject.FlowAlertRecordDO;
import org.apache.ibatis.annotations.Mapper;

import java.util.Collection;
import java.util.List;

/**
 * 告警处理记录 Mapper
 */
@Mapper
public interface FlowAlertRecordMapper extends BaseMapperX<FlowAlertRecordDO> {

    default PageResult<FlowAlertRecordDO> selectPage(PageParam pageParam, Long alertId, String alertSource,
                                                     Integer processInstanceStatus) {
        return selectPage(pageParam, new LambdaQueryWrapperX<FlowAlertRecordDO>()
                .eqIfPresent(FlowAlertRecordDO::getAlertId, alertId)
                .eqIfPresent(FlowAlertRecordDO::getAlertSource, alertSource)
                .eqIfPresent(FlowAlertRecordDO::getProcessInstanceStatus, processInstanceStatus)
                .orderByDesc(FlowAlertRecordDO::getId));
    }

    default FlowAlertRecordDO selectByInstance(String processInstanceId) {
        return selectOne(FlowAlertRecordDO::getProcessInstanceId, processInstanceId);
    }

    default List<FlowAlertRecordDO> selectListByAlertIds(Collection<Long> alertIds) {
        return selectList(FlowAlertRecordDO::getAlertId, alertIds);
    }

}
