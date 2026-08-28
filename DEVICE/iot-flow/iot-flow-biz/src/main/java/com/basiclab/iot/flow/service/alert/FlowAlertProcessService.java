package com.basiclab.iot.flow.service.alert;

import com.basiclab.iot.flow.dal.dataobject.FlowAlertRecordDO;

import java.util.Map;

/**
 * 告警触发流程 Service 接口（Kafka 事件 / 手动补触发共用）
 */
public interface FlowAlertProcessService {

    /**
     * 按告警快照触发处理流程：匹配路由规则 → 发起流程 → 写 flow_alert_record
     *
     * @param snapshot    告警快照（iot-alert-created 消息字段平铺）
     * @param alertSource 告警来源（VIDEO_TASK 等）
     * @return 处理记录（未命中规则 / 重复告警返回 null）
     */
    FlowAlertRecordDO triggerBySnapshot(Map<String, Object> snapshot, String alertSource);

    /**
     * 手动为存量告警发起处理流程（跳过规则匹配，直接按 processDefinitionKey 发起）
     */
    FlowAlertRecordDO manualTrigger(Long alertId, String processDefinitionKey);

}
