package com.basiclab.iot.flow.mq.consumer;

import com.basiclab.iot.common.core.context.TenantContextHolder;
import com.basiclab.iot.common.utils.json.JsonUtils;
import com.basiclab.iot.flow.dal.dataobject.FlowAlertRecordDO;
import com.basiclab.iot.flow.service.alert.FlowAlertProcessService;
import com.basiclab.iot.flow.service.alert.FlowAlertProcessServiceImpl;
import lombok.extern.slf4j.Slf4j;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.Acknowledgment;
import org.springframework.stereotype.Component;

import javax.annotation.Resource;
import java.util.Map;

/**
 * iot-alert-created 事件消费者：告警产生 → 匹配路由规则 → 自动发起处理流程。
 *
 * FLOW 宕机不阻断告警主链路：本消费者任何异常都照常 ack，仅记录日志，
 * 存量告警可通过 /flow/alert-record/trigger 手动补触发。
 */
@Slf4j
@Component
public class AlertCreatedConsumer {

    /** 告警链路与租户无关，规则表/记录表为 BaseDO；发起人上下文用默认租户 */
    private static final Long DEFAULT_TENANT_ID = 1L;

    @Resource
    private FlowAlertProcessService alertProcessService;

    @KafkaListener(
            topics = "${spring.kafka.alert-created.topic:iot-alert-created}",
            groupId = "${spring.kafka.alert-created.group-id:flow-server-alert-created-consumer}"
    )
    public void onMessage(String message, Acknowledgment acknowledgment) {
        try {
            if (message == null || message.isEmpty()) {
                return;
            }
            Map<String, Object> snapshot = JsonUtils.parseObject(message, Map.class);
            if (snapshot == null || snapshot.isEmpty()) {
                log.warn("[onMessage] 告警事件解析为空: {}", message);
                return;
            }
            TenantContextHolder.setTenantId(DEFAULT_TENANT_ID);
            FlowAlertRecordDO record = alertProcessService.triggerBySnapshot(
                    snapshot, FlowAlertProcessServiceImpl.ALERT_SOURCE_VIDEO_TASK);
            log.debug("[onMessage] 告警事件处理完成: alertId={}, recordId={}",
                    snapshot.get("alertId"), record == null ? null : record.getId());
        }
        catch (Exception e) {
            // 尽力而为：失败不重投（避免告警风暴时无限循环），留日志对账 + 手动补触发
            log.error("[onMessage] 告警事件处理失败（已忽略，可手动补触发）: {}", message, e);
        }
        finally {
            TenantContextHolder.clear();
            if (acknowledgment != null) {
                acknowledgment.acknowledge();
            }
        }
    }

}
