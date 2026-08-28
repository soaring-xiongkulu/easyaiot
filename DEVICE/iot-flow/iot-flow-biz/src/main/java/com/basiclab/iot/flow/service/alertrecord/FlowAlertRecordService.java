package com.basiclab.iot.flow.service.alertrecord;

import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.flow.dal.dataobject.FlowAlertRecordDO;

import java.util.Collection;
import java.util.List;

/**
 * 告警处理记录 Service 接口
 */
public interface FlowAlertRecordService {

    PageResult<FlowAlertRecordDO> getAlertRecordPage(PageParam pageParam, Long alertId, String alertSource,
                                                     Integer processInstanceStatus);

    /** 我负责的记录：当前登录人是运行中任务的审批人/候选人 */
    PageResult<FlowAlertRecordDO> getMyAlertRecordPage(Long userId, PageParam pageParam, Long alertId,
                                                       String alertSource, Integer processInstanceStatus);

    List<FlowAlertRecordDO> getAlertRecordListByAlertIds(Collection<Long> alertIds);

    FlowAlertRecordDO getAlertRecord(Long id);

    /** 手动补触发（存量告警） */
    FlowAlertRecordDO triggerAlertRecord(Long alertId, String processDefinitionKey);

}
