package com.basiclab.iot.flow.framework.flowable.delegate;

import lombok.extern.slf4j.Slf4j;
import org.flowable.engine.delegate.DelegateExecution;
import org.springframework.stereotype.Component;

import static com.basiclab.iot.flow.enums.FlowEnums.PROCESS_REASON_VAR;
import static com.basiclab.iot.flow.enums.FlowEnums.PROCESS_STATUS_VAR;

/**
 * 审批超时委托（BPMN 边界定时的 handler service task）。
 *
 * 1 提醒（非中断）：打变量 + 日志，原任务继续；
 * 2 自动通过：converter 已把 handler 接到原任务的后继，令牌自动续走，这里只留痕；
 * 3 自动拒绝：写拒绝状态变量，handler 流向独立结束事件，结束时由全局监听回写告警记录。
 *
 * BPMN 表达式：${flowTimeoutDelegate.apply(execution, '&lt;nodeId&gt;', &lt;type&gt;)}
 */
@Slf4j
@Component
public class FlowTimeoutDelegate {

    /** 超时类型：提醒 */
    public static final int TYPE_REMINDER = 1;
    /** 超时类型：自动通过 */
    public static final int TYPE_APPROVE = 2;
    /** 超时类型：自动拒绝 */
    public static final int TYPE_REJECT = 3;

    public void apply(DelegateExecution execution, String nodeId, Integer type) {
        int timeoutType = type == null ? TYPE_APPROVE : type;
        String instanceId = execution.getProcessInstanceId();
        switch (timeoutType) {
            case TYPE_REMINDER -> {
                execution.setVariable("timeout_reminded_" + nodeId, Boolean.TRUE);
                log.info("[apply] 审批超时提醒, instanceId={}, nodeId={}", instanceId, nodeId);
            }
            case TYPE_APPROVE -> {
                execution.setVariable("timeout_auto_approved_" + nodeId, Boolean.TRUE);
                log.info("[apply] 审批超时自动通过, instanceId={}, nodeId={}", instanceId, nodeId);
            }
            case TYPE_REJECT -> {
                execution.setVariable(PROCESS_STATUS_VAR, 3);
                execution.setVariable(PROCESS_REASON_VAR, "审批超时，自动拒绝");
                log.info("[apply] 审批超时自动拒绝, instanceId={}, nodeId={}", instanceId, nodeId);
            }
            default -> log.warn("[apply] 未支持的超时类型: {}", timeoutType);
        }
    }

}
