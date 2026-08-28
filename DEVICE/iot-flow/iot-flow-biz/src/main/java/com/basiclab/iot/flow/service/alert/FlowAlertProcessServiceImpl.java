package com.basiclab.iot.flow.service.alert;

import com.basiclab.iot.common.utils.json.JsonUtils;
import com.basiclab.iot.flow.dal.dataobject.FlowAlertRecordDO;
import com.basiclab.iot.flow.dal.pgsql.FlowAlertRecordMapper;
import com.basiclab.iot.flow.service.alertrule.FlowAlertRouteRuleService;
import com.basiclab.iot.flow.service.candidate.FlowCandidateService;
import com.basiclab.iot.flow.service.instance.FlowProcessInstanceService;
import lombok.extern.slf4j.Slf4j;
import org.flowable.engine.RepositoryService;
import org.flowable.engine.TaskService;
import org.flowable.engine.repository.ProcessDefinition;
import org.flowable.identitylink.api.IdentityLink;
import org.flowable.task.api.Task;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import javax.annotation.Resource;
import java.util.HashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.flow.enums.FlowErrorCodeConstants.ALERT_RECORD_DUPLICATE;
import static com.basiclab.iot.flow.enums.FlowErrorCodeConstants.ALERT_TRIGGER_DEFINITION_NOT_FOUND;

/**
 * 告警触发流程 Service 实现
 *
 * 告警变量约定（前端详情页读取）：alertId / alertEvent / alertObject / taskName /
 * deviceId / deviceName / imageUrl / alertTime / nodeId / edgeNodeId / taskId / taskType。
 */
@Slf4j
@Service
public class FlowAlertProcessServiceImpl implements FlowAlertProcessService {

    public static final String ALERT_SOURCE_VIDEO_TASK = "VIDEO_TASK";

    @Resource
    private FlowAlertRouteRuleService routeRuleService;
    @Resource
    private FlowAlertRecordMapper alertRecordMapper;
    @Resource
    private FlowProcessInstanceService processInstanceService;
    @Resource
    private RepositoryService repositoryService;
    @Resource
    private TaskService taskService;
    @Resource
    private FlowCandidateService candidateService;

    @Override
    @Transactional(rollbackFor = Exception.class)
    public FlowAlertRecordDO triggerBySnapshot(Map<String, Object> snapshot, String alertSource) {
        Long alertId = toLong(snapshot.get("alertId"));
        if (alertId == null) {
            log.warn("[triggerBySnapshot] 告警快照缺少 alertId，跳过: {}", snapshot);
            return null;
        }
        // 规则匹配（优先级大者先命中）
        com.basiclab.iot.flow.dal.dataobject.FlowAlertRouteRuleDO rule = routeRuleService.previewMatch(snapshot);
        if (rule == null) {
            log.info("[triggerBySnapshot] 告警未命中任何路由规则, alertId={}", alertId);
            return null;
        }
        return doTrigger(alertId, alertSource, rule.getProcessDefinitionKey(), snapshot,
                rule.getStartUserId(), false);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public FlowAlertRecordDO manualTrigger(Long alertId, String processDefinitionKey) {
        Map<String, Object> snapshot = new HashMap<>();
        snapshot.put("alertId", alertId);
        snapshot.put("manualTrigger", true);
        return doTrigger(alertId, ALERT_SOURCE_VIDEO_TASK, processDefinitionKey, snapshot, null, true);
    }

    private FlowAlertRecordDO doTrigger(Long alertId, String alertSource, String processDefinitionKey,
                                        Map<String, Object> snapshot, Long ruleStartUserId, boolean strict) {
        // 幂等：同 告警+流程 已有记录则跳过（唯一索引兜底）
        List<FlowAlertRecordDO> existing = alertRecordMapper.selectListByAlertIds(List.of(alertId));
        for (FlowAlertRecordDO record : existing) {
            if (processDefinitionKey.equals(record.getProcessDefinitionKey())) {
                if (strict) {
                    throw exception(ALERT_RECORD_DUPLICATE);
                }
                log.info("[doTrigger] 告警已有同流程处理记录，跳过, alertId={}, key={}", alertId, processDefinitionKey);
                return record;
            }
        }
        ProcessDefinition definition = repositoryService.createProcessDefinitionQuery()
                .processDefinitionKey(processDefinitionKey).latestVersion().active().singleResult();
        if (definition == null) {
            if (strict) {
                throw exception(ALERT_TRIGGER_DEFINITION_NOT_FOUND);
            }
            log.warn("[doTrigger] 流程定义不存在或未启用, alertId={}, key={}", alertId, processDefinitionKey);
            return null;
        }

        Long startUserId = ruleStartUserId == null ? 1L : ruleStartUserId;
        String businessKey = "alert:" + alertId;
        String instanceName = definition.getName() + "（告警#" + alertId + "）";
        String instanceId = processInstanceService.startProcess(startUserId, definition.getId(), businessKey,
                instanceName, buildVariables(snapshot), null);

        FlowAlertRecordDO record = new FlowAlertRecordDO();
        record.setAlertId(alertId);
        record.setAlertSource(alertSource == null ? ALERT_SOURCE_VIDEO_TASK : alertSource);
        record.setAlertSnapshot(JsonUtils.toJsonString(snapshot));
        record.setProcessInstanceId(instanceId);
        record.setProcessDefinitionKey(processDefinitionKey);
        record.setProcessInstanceStatus(FlowAlertRecordDO.STATUS_RUNNING);
        alertRecordMapper.insert(record);
        syncRecordCurrentNode(record);
        log.info("[doTrigger] 告警处理流程已发起, alertId={}, instanceId={}, recordId={}",
                alertId, instanceId, record.getId());
        return record;
    }

    /** 冗余列回填：首个节点的 TASK_CREATED 先于记录入库（监听器同步不到），启动后从引擎活动任务补齐当前节点/责任人 */
    private void syncRecordCurrentNode(FlowAlertRecordDO record) {
        try {
            List<Task> tasks = taskService.createTaskQuery()
                    .processInstanceId(record.getProcessInstanceId()).active().list();
            if (tasks.isEmpty()) {
                return;
            }
            record.setCurrentTaskName(tasks.stream().map(Task::getName)
                    .collect(Collectors.joining("、")));
            Set<Long> userIds = new LinkedHashSet<>();
            for (Task task : tasks) {
                if (task.getAssignee() != null && task.getAssignee().matches("\\d+")) {
                    userIds.add(Long.valueOf(task.getAssignee()));
                    continue;
                }
                for (IdentityLink link : taskService.getIdentityLinksForTask(task.getId())) {
                    if (link.getUserId() != null && link.getUserId().matches("\\d+")) {
                        userIds.add(Long.valueOf(link.getUserId()));
                    }
                }
            }
            if (!userIds.isEmpty()) {
                Map<Long, String> nicknameMap = candidateService.getUserNicknameMap(userIds);
                record.setCurrentAssignees(userIds.stream()
                        .map(id -> nicknameMap.getOrDefault(id, String.valueOf(id)))
                        .collect(Collectors.joining(",")));
            }
            alertRecordMapper.updateById(record);
        }
        catch (Exception e) {
            log.warn("[syncRecordCurrentNode] 回填当前节点失败, instanceId={}", record.getProcessInstanceId(), e);
        }
    }

    /** 告警快照 → 流程变量（前端审批详情页展示的告警信息卡字段） */
    private Map<String, Object> buildVariables(Map<String, Object> snapshot) {
        Map<String, Object> vars = new HashMap<>();
        putIfPresent(vars, "alertId", snapshot.get("alertId"));
        putIfPresent(vars, "taskId", snapshot.get("taskId"));
        putIfPresent(vars, "taskName", snapshot.get("taskName"));
        putIfPresent(vars, "deviceId", snapshot.get("deviceId"));
        putIfPresent(vars, "deviceName", snapshot.get("deviceName"));
        putIfPresent(vars, "nodeId", snapshot.get("nodeId"));
        putIfPresent(vars, "edgeNodeId", snapshot.get("edgeNodeId"));
        putIfPresent(vars, "alertTime", snapshot.get("timestamp"));
        Object alert = snapshot.get("alert");
        if (alert instanceof Map<?, ?> alertMap) {
            putIfPresent(vars, "alertEvent", alertMap.get("event"));
            putIfPresent(vars, "alertObject", alertMap.get("object"));
            putIfPresent(vars, "imageUrl", alertMap.get("imagePath"));
            putIfPresent(vars, "recordPath", alertMap.get("recordPath"));
            if (!vars.containsKey("alertTime")) {
                putIfPresent(vars, "alertTime", alertMap.get("time"));
            }
            putIfPresent(vars, "taskType", alertMap.get("taskType"));
        }
        return vars;
    }

    private void putIfPresent(Map<String, Object> vars, String key, Object value) {
        if (value != null && !String.valueOf(value).isEmpty()) {
            vars.put(key, value);
        }
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

}
