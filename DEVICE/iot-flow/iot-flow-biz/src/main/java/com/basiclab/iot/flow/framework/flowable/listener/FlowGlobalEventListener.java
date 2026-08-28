package com.basiclab.iot.flow.framework.flowable.listener;

import com.basiclab.iot.flow.dal.dataobject.FlowAlertRecordDO;
import com.basiclab.iot.flow.dal.pgsql.FlowAlertRecordMapper;
import com.basiclab.iot.flow.framework.flowable.core.SimpleModelConverter;
import com.basiclab.iot.flow.framework.flowable.core.TaskCandidateConf;
import com.basiclab.iot.flow.service.candidate.FlowCandidateService;
import com.basiclab.iot.flow.service.notify.FlowNotifyService;
import lombok.extern.slf4j.Slf4j;
import org.flowable.bpmn.model.BpmnModel;
import org.flowable.bpmn.model.ExtensionElement;
import org.flowable.bpmn.model.FlowElement;
import org.flowable.bpmn.model.UserTask;
import org.flowable.common.engine.api.delegate.event.FlowableEngineEvent;
import org.flowable.common.engine.api.delegate.event.FlowableEngineEventType;
import org.flowable.common.engine.api.delegate.event.FlowableEntityEvent;
import org.flowable.common.engine.api.delegate.event.FlowableEvent;
import org.flowable.common.engine.api.delegate.event.FlowableEventListener;
import org.flowable.engine.HistoryService;
import org.flowable.engine.RepositoryService;
import org.flowable.engine.RuntimeService;
import org.flowable.engine.TaskService;
import org.flowable.task.service.impl.persistence.entity.TaskEntity;
import org.springframework.context.ApplicationContext;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import static com.basiclab.iot.flow.enums.FlowEnums.PROCESS_REASON_VAR;
import static com.basiclab.iot.flow.enums.FlowEnums.PROCESS_STATUS_VAR;
import static com.basiclab.iot.flow.enums.FlowEnums.PROCESS_START_USER_VAR;

/**
 * Flow 全局事件监听：
 *  1. TASK_CREATED：按 BPMN 扩展元素 candidateConf 解析候选人并指派（含发起人相同处理、审批人为空兜底）；
 *  2. PROCESS_COMPLETED / PROCESS_CANCELLED：回写 flow_alert_record 终态。
 *
 * 以普通对象注册进引擎（见 FlowableConfiguration），业务 Bean 延迟获取。
 */
@Slf4j
public class FlowGlobalEventListener implements FlowableEventListener {

    private final ApplicationContext applicationContext;

    public FlowGlobalEventListener(ApplicationContext applicationContext) {
        this.applicationContext = applicationContext;
    }

    @Override
    public void onEvent(FlowableEvent event) {
        try {
            FlowableEngineEventType type = (FlowableEngineEventType) event.getType();
            if (FlowableEngineEventType.TASK_CREATED.equals(type)) {
                handleTaskCreated((FlowableEntityEvent) event);
            }
            else if (FlowableEngineEventType.PROCESS_COMPLETED.equals(type)
                    || FlowableEngineEventType.PROCESS_CANCELLED.equals(type)) {
                handleProcessEnd((FlowableEngineEvent) event,
                        FlowableEngineEventType.PROCESS_CANCELLED.equals(type));
            }
        }
        catch (Exception e) {
            // 全局监听失败不阻断引擎事务
            log.error("[onEvent] Flow 事件处理失败: {}", event.getType(), e);
        }
    }

    // ==================== 任务创建：指派候选人 ====================

    private void handleTaskCreated(FlowableEntityEvent event) {
        if (!(event.getEntity() instanceof TaskEntity task)) {
            return;
        }
        RepositoryService repositoryService = bean(RepositoryService.class);
        RuntimeService runtimeService = bean(RuntimeService.class);
        TaskService taskService = bean(TaskService.class);

        List<Long> assigned;
        if (task.getAssignee() != null) {
            // 多实例任务：候选人由集合变量已指派（assignee 非空）
            Long assignee = toLong(task.getAssignee());
            assigned = assignee == null ? List.of() : List.of(assignee);
        }
        else {
            Map<String, Object> variables = runtimeService.getVariables(task.getProcessInstanceId());
            Long startUserId = toLong(variables.get(PROCESS_START_USER_VAR));
            TaskCandidateConf conf = loadConf(repositoryService, task);
            List<Long> candidates = candidateService().resolve(conf, startUserId, variables, task.getTaskDefinitionKey());
            candidates = candidateService().applyAssignStartUserHandler(conf, candidates, startUserId);
            if (candidates.isEmpty()) {
                candidates = candidateService().resolveAssignEmpty(conf, startUserId);
            }
            if (candidates.isEmpty()) {
                assignEmptyFallback(taskService, runtimeService, task, conf, startUserId);
                return;
            }
            Integer method = conf == null ? null : conf.getApproveMethod();
            if (method != null && method == 1) {
                // 随机挑选一人（resolve 已排序，取首位）
                taskService.setAssignee(task.getId(), String.valueOf(candidates.get(0)));
                candidates = List.of(candidates.get(0));
            }
            else {
                for (Long userId : candidates) {
                    taskService.addCandidateUser(task.getId(), String.valueOf(userId));
                }
            }
            assigned = candidates;
        }
        syncAlertRecordRunning(task, assigned);
        notifyTaskTodo(task, assigned);
    }

    /** 待办站内信（含 deepLink），失败不影响流程 */
    private void notifyTaskTodo(TaskEntity task, List<Long> userIds) {
        if (userIds == null || userIds.isEmpty()) {
            return;
        }
        try {
            bean(FlowNotifyService.class)
                    .notifyTaskTodo(task.getProcessInstanceId(), task.getId(), task.getName(), userIds);
        }
        catch (Exception e) {
            log.warn("[notifyTaskTodo] 站内信发送异常, task={}", task.getId(), e);
        }
    }

    /** 候选人为空兜底：1 自动通过 / 2 自动拒绝 / 其它转发起人，保证流程不卡死 */
    private void assignEmptyFallback(TaskService taskService, RuntimeService runtimeService, TaskEntity task,
                                     TaskCandidateConf conf, Long startUserId) {
        Integer handler = conf == null ? null : conf.getAssignEmptyHandlerType();
        log.warn("[assignEmptyFallback] 任务无候选人, task={}({}), assignEmptyHandler={}",
                task.getName(), task.getId(), handler);
        if (handler != null && handler == 1) {
            runtimeService.setVariable(task.getProcessInstanceId(), PROCESS_REASON_VAR, "审批人为空，自动通过");
            taskService.complete(task.getId());
            return;
        }
        if (handler != null && handler == 2) {
            runtimeService.setVariable(task.getProcessInstanceId(), PROCESS_STATUS_VAR, 3);
            runtimeService.setVariable(task.getProcessInstanceId(), PROCESS_REASON_VAR, "审批人为空，自动拒绝");
            runtimeService.deleteProcessInstance(task.getProcessInstanceId(), "审批人为空自动拒绝");
            return;
        }
        if (startUserId != null) {
            taskService.setAssignee(task.getId(), String.valueOf(startUserId));
            syncAlertRecordRunning(task, List.of(startUserId));
            notifyTaskTodo(task, List.of(startUserId));
        }
    }

    private TaskCandidateConf loadConf(RepositoryService repositoryService, TaskEntity task) {
        try {
            BpmnModel bpmnModel = repositoryService.getBpmnModel(task.getProcessDefinitionId());
            FlowElement element = bpmnModel.getFlowElement(task.getTaskDefinitionKey());
            if (!(element instanceof UserTask userTask)) {
                return null;
            }
            List<ExtensionElement> exts = userTask.getExtensionElements()
                    .get(SimpleModelConverter.EXT_CANDIDATE_CONF);
            return TaskCandidateConf.parse(exts == null || exts.isEmpty() ? null : exts.get(0));
        }
        catch (Exception e) {
            log.warn("[loadConf] 读取候选人配置失败, taskDefinitionKey={}", task.getTaskDefinitionKey(), e);
            return null;
        }
    }

    /** 告警记录冗余列同步：当前节点 + 当前责任人（无记录时忽略，说明非告警流程） */
    private void syncAlertRecordRunning(TaskEntity task, List<Long> userIds) {
        FlowAlertRecordMapper mapper = bean(FlowAlertRecordMapper.class);
        FlowAlertRecordDO record = mapper.selectByInstance(task.getProcessInstanceId());
        if (record == null) {
            return;
        }
        record.setCurrentTaskName(task.getName());
        Map<Long, String> nicknameMap = candidateService().getUserNicknameMap(userIds);
        record.setCurrentAssignees(userIds.stream()
                .map(id -> nicknameMap.getOrDefault(id, String.valueOf(id)))
                .collect(Collectors.joining(",")));
        mapper.updateById(record);
    }

    // ==================== 实例结束：回写告警记录终态 ====================

    private void handleProcessEnd(FlowableEngineEvent event, boolean cancelled) {
        String instanceId = event.getProcessInstanceId();
        FlowAlertRecordMapper mapper = bean(FlowAlertRecordMapper.class);
        FlowAlertRecordDO record = mapper.selectByInstance(instanceId);
        if (record == null) {
            return;
        }
        Integer status = readFinalStatus(instanceId, cancelled);
        // updateById 会忽略 null 字段，这里用 UpdateWrapper 显式清空"当前节点/责任人"冗余列
        mapper.update(null, new com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper<FlowAlertRecordDO>()
                .eq(FlowAlertRecordDO::getId, record.getId())
                .set(FlowAlertRecordDO::getProcessInstanceStatus, status)
                .set(FlowAlertRecordDO::getFinishTime, LocalDateTime.now())
                .set(FlowAlertRecordDO::getCurrentTaskName, null)
                .set(FlowAlertRecordDO::getCurrentAssignees, null));
        log.info("[handleProcessEnd] 告警流程结束, instanceId={}, alertId={}, status={}",
                instanceId, record.getAlertId(), status);
    }

    /** 终态：PROCESS_STATUS 变量优先（拒绝/取消在结束前写入），缺失时按事件类型给默认值 */
    private Integer readFinalStatus(String instanceId, boolean cancelled) {
        try {
            Object status = bean(RuntimeService.class).getVariable(instanceId, PROCESS_STATUS_VAR);
            if (status instanceof Number number) {
                return number.intValue();
            }
        }
        catch (Exception ignore) {
            // 实例已销毁，走历史查询
        }
        try {
            var instance = bean(HistoryService.class).createHistoricProcessInstanceQuery()
                    .processInstanceId(instanceId).includeProcessVariables().singleResult();
            if (instance != null && instance.getProcessVariables().get(PROCESS_STATUS_VAR) instanceof Number number) {
                return number.intValue();
            }
        }
        catch (Exception e) {
            log.warn("[readFinalStatus] 历史变量读取失败, instanceId={}", instanceId, e);
        }
        return cancelled ? 4 : 2;
    }

    // ==================== 工具 ====================

    private FlowCandidateService candidateService() {
        return bean(FlowCandidateService.class);
    }

    private <T> T bean(Class<T> clazz) {
        return applicationContext.getBean(clazz);
    }

    private Long toLong(Object value) {
        if (value instanceof Number number) {
            return number.longValue();
        }
        if (value instanceof String str && str.matches("\\d+")) {
            return Long.valueOf(str);
        }
        return null;
    }

    @Override
    public boolean isFailOnException() {
        return false;
    }

    @Override
    public boolean isFireOnTransactionLifecycleEvent() {
        return false;
    }

    @Override
    public String getOnTransaction() {
        return null;
    }

}
