package com.basiclab.iot.flow.service.task;

import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.exception.util.ServiceExceptionUtil;
import com.basiclab.iot.flow.controller.admin.task.FlowTaskVOs.ApproveReq;
import com.basiclab.iot.flow.controller.admin.task.FlowTaskVOs.AssignReq;
import com.basiclab.iot.flow.controller.admin.task.FlowTaskVOs.CopyReq;
import com.basiclab.iot.flow.controller.admin.task.FlowTaskVOs.CreateSignReq;
import com.basiclab.iot.flow.controller.admin.task.FlowTaskVOs.ReasonReq;
import com.basiclab.iot.flow.controller.admin.task.FlowTaskVOs.RejectReq;
import com.basiclab.iot.flow.controller.admin.task.FlowTaskVOs.ReturnReq;
import com.basiclab.iot.flow.controller.admin.task.FlowTaskVOs.TaskVO;
import com.basiclab.iot.flow.controller.admin.vo.FlowUserVO;
import com.basiclab.iot.flow.dal.dataobject.FlowProcessInstanceCopyDO;
import com.basiclab.iot.flow.dal.pgsql.FlowProcessInstanceCopyMapper;
import com.basiclab.iot.flow.framework.flowable.core.SimpleModelConverter;
import com.basiclab.iot.flow.framework.flowable.core.TaskCandidateConf;
import com.basiclab.iot.flow.service.instance.FlowProcessInstanceServiceImpl;
import com.basiclab.iot.system.api.user.AdminUserApi;
import com.basiclab.iot.system.api.user.dto.AdminUserRespDTO;
import lombok.extern.slf4j.Slf4j;
import org.flowable.bpmn.model.BpmnModel;
import org.flowable.bpmn.model.FlowElement;
import org.flowable.bpmn.model.UserTask;
import org.flowable.engine.HistoryService;
import org.flowable.engine.RepositoryService;
import org.flowable.engine.RuntimeService;
import org.flowable.engine.TaskService;
import org.flowable.task.api.Task;
import org.flowable.task.api.TaskQuery;
import org.flowable.task.api.history.HistoricTaskInstance;
import org.flowable.task.api.history.HistoricTaskInstanceQuery;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import javax.annotation.Resource;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import static com.basiclab.iot.flow.enums.FlowEnums.PROCESS_REASON_VAR;
import static com.basiclab.iot.flow.enums.FlowEnums.PROCESS_START_USER_VAR;
import static com.basiclab.iot.flow.enums.FlowEnums.PROCESS_STATUS_VAR;
import static com.basiclab.iot.flow.enums.FlowErrorCodeConstants.TASK_ALREADY_FINISHED;
import static com.basiclab.iot.flow.enums.FlowErrorCodeConstants.TASK_NOT_ASSIGNEE;
import static com.basiclab.iot.flow.enums.FlowErrorCodeConstants.TASK_NOT_EXISTS;
import static com.basiclab.iot.flow.enums.FlowErrorCodeConstants.TASK_RETURN_TARGET_INVALID;
import static com.basiclab.iot.flow.enums.FlowErrorCodeConstants.TASK_WITHDRAW_FAIL;

/**
 * 流程任务 Service 实现
 */
@Slf4j
@Service
public class FlowTaskServiceImpl implements FlowTaskService {

    @Resource
    private TaskService taskService;
    @Resource
    private HistoryService historyService;
    @Resource
    private RuntimeService runtimeService;
    @Resource
    private RepositoryService repositoryService;
    @Resource
    private AdminUserApi adminUserApi;
    @Resource
    private FlowProcessInstanceCopyMapper copyMapper;
    @Resource
    private FlowProcessInstanceServiceImpl processInstanceService;

    // ==================== 查询 ====================

    @Override
    public PageResult<TaskVO> getTaskTodoPage(Long userId, PageParam pageParam, String name, String processInstanceName) {
        TaskQuery query = taskService.createTaskQuery()
                .taskCandidateOrAssigned(String.valueOf(userId))
                .active()
                .includeProcessVariables();
        applyTaskFilter(query, name, processInstanceName);
        query.orderByTaskCreateTime().desc();
        long total = query.count();
        List<Task> tasks = query.listPage((pageParam.getPageNo() - 1) * pageParam.getPageSize(),
                pageParam.getPageSize());
        return new PageResult<>(buildTasks(tasks, true), total);
    }

    @Override
    public PageResult<TaskVO> getTaskDonePage(Long userId, PageParam pageParam, String name, String processInstanceName) {
        HistoricTaskInstanceQuery query = historyService.createHistoricTaskInstanceQuery()
                .taskAssignee(String.valueOf(userId))
                .finished()
                .includeProcessVariables()
                .includeTaskLocalVariables();
        applyHistoricFilter(query, name, processInstanceName);
        query.orderByHistoricTaskInstanceEndTime().desc();
        long total = query.count();
        List<HistoricTaskInstance> tasks = query.listPage((pageParam.getPageNo() - 1) * pageParam.getPageSize(),
                pageParam.getPageSize());
        return new PageResult<>(buildHistoricTasks(tasks, 2), total);
    }

    @Override
    public PageResult<TaskVO> getTaskManagerPage(PageParam pageParam, String name, String processInstanceName) {
        HistoricTaskInstanceQuery query = historyService.createHistoricTaskInstanceQuery()
                .includeProcessVariables()
                .includeTaskLocalVariables();
        applyHistoricFilter(query, name, processInstanceName);
        query.orderByTaskCreateTime().desc();
        long total = query.count();
        List<HistoricTaskInstance> tasks = query.listPage((pageParam.getPageNo() - 1) * pageParam.getPageSize(),
                pageParam.getPageSize());
        return new PageResult<>(buildHistoricTasks(tasks, null), total);
    }

    @Override
    public Long getTaskTodoCount(Long userId) {
        return taskService.createTaskQuery()
                .taskCandidateOrAssigned(String.valueOf(userId))
                .active()
                .count();
    }

    private void applyTaskFilter(TaskQuery query, String name, String processInstanceName) {
        if (name != null && !name.isEmpty()) {
            query.taskNameLike("%" + name + "%");
        }
        if (processInstanceName != null && !processInstanceName.isEmpty()) {
            query.processVariableValueLike(FlowProcessInstanceServiceImpl.INSTANCE_NAME_VAR,
                    "%" + processInstanceName + "%");
        }
    }

    private void applyHistoricFilter(HistoricTaskInstanceQuery query, String name, String processInstanceName) {
        if (name != null && !name.isEmpty()) {
            query.taskNameLike("%" + name + "%");
        }
        if (processInstanceName != null && !processInstanceName.isEmpty()) {
            query.processVariableValueLike(FlowProcessInstanceServiceImpl.INSTANCE_NAME_VAR,
                    "%" + processInstanceName + "%");
        }
    }

    // ==================== 审批动作 ====================

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void approveTask(Long userId, ApproveReq reqVO) {
        Task task = validateActiveTask(reqVO.getId());
        validateAssignee(task, userId);
        claimIfUnassigned(task, userId);
        if (reqVO.getReason() != null && !reqVO.getReason().isEmpty()) {
            taskService.setVariableLocal(task.getId(), "reason", reqVO.getReason());
        }
        // 清理加签子任务
        deleteSignChildren(task.getId());
        if (reqVO.getVariables() != null && !reqVO.getVariables().isEmpty()) {
            taskService.complete(task.getId(), reqVO.getVariables());
        }
        else {
            taskService.complete(task.getId());
        }
        log.info("[approveTask] 任务审批通过, taskId={}, user={}", task.getId(), userId);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void rejectTask(Long userId, RejectReq reqVO) {
        Task task = validateActiveTask(reqVO.getId());
        validateAssignee(task, userId);
        claimIfUnassigned(task, userId);
        String reason = reqVO.getReason() == null ? "" : reqVO.getReason();
        taskService.setVariableLocal(task.getId(), "reason", reason);

        TaskCandidateConf conf = loadCandidateConf(task);
        Integer rejectType = conf == null || conf.getRejectHandlerType() == null ? 1 : conf.getRejectHandlerType();
        String pid = task.getProcessInstanceId();
        if (rejectType == 2 && conf.getRejectReturnNodeId() != null && !conf.getRejectReturnNodeId().isEmpty()) {
            // 退回到指定节点重新审批
            runtimeService.setVariable(pid, PROCESS_REASON_VAR, reason);
            runtimeService.createChangeActivityStateBuilder()
                    .processInstanceId(pid)
                    .moveActivityIdTo(task.getTaskDefinitionKey(), conf.getRejectReturnNodeId())
                    .changeState();
            log.info("[rejectTask] 拒绝并退回节点, taskId={}, target={}", task.getId(), conf.getRejectReturnNodeId());
            return;
        }
        // 直接结束流程（拒绝）
        runtimeService.setVariable(pid, PROCESS_STATUS_VAR, 3);
        runtimeService.setVariable(pid, PROCESS_REASON_VAR, reason);
        runtimeService.deleteProcessInstance(pid, "reject:" + reason);
        log.info("[rejectTask] 拒绝结束流程, taskId={}, instanceId={}, user={}", task.getId(), pid, userId);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void returnTask(Long userId, ReturnReq reqVO) {
        Task task = validateActiveTask(reqVO.getId());
        validateAssignee(task, userId);
        String target = reqVO.getTargetTaskDefinitionKey();
        BpmnModel bpmnModel = repositoryService.getBpmnModel(task.getProcessDefinitionId());
        FlowElement targetElement = target == null ? null : bpmnModel.getFlowElement(target);
        if (!(targetElement instanceof UserTask) || target.equals(task.getTaskDefinitionKey())) {
            throw ServiceExceptionUtil.exception(TASK_RETURN_TARGET_INVALID);
        }
        if (reqVO.getReason() != null && !reqVO.getReason().isEmpty()) {
            runtimeService.setVariable(task.getProcessInstanceId(), PROCESS_REASON_VAR, reqVO.getReason());
        }
        runtimeService.createChangeActivityStateBuilder()
                .processInstanceId(task.getProcessInstanceId())
                .moveActivityIdTo(task.getTaskDefinitionKey(), target)
                .changeState();
        log.info("[returnTask] 任务退回, taskId={}, target={}, user={}", task.getId(), target, userId);
    }

    @Override
    public void delegateTask(Long userId, AssignReq reqVO) {
        Task task = validateActiveTask(reqVO.getId());
        validateAssignee(task, userId);
        taskService.setVariableLocal(task.getId(), "reason",
                reqVO.getReason() == null ? "" : "委派给用户 " + reqVO.getAssigneeUserId() + "：" + reqVO.getReason());
        taskService.delegateTask(task.getId(), String.valueOf(reqVO.getAssigneeUserId()));
    }

    @Override
    public void transferTask(Long userId, AssignReq reqVO) {
        Task task = validateActiveTask(reqVO.getId());
        validateAssignee(task, userId);
        taskService.setAssignee(task.getId(), String.valueOf(reqVO.getAssigneeUserId()));
    }

    @Override
    public void copyTask(Long userId, CopyReq reqVO) {
        Task task = taskService.createTaskQuery().taskId(reqVO.getId()).includeProcessVariables().singleResult();
        if (task == null) {
            HistoricTaskInstance his = historyService.createHistoricTaskInstanceQuery()
                    .taskId(reqVO.getId()).includeProcessVariables().singleResult();
            if (his == null) {
                throw ServiceExceptionUtil.exception(TASK_NOT_EXISTS);
            }
            insertCopies(his.getId(), his.getName(), his.getTaskDefinitionKey(), his.getProcessInstanceId(),
                    his.getProcessVariables(), reqVO.getUserIds(), reqVO.getReason());
            return;
        }
        insertCopies(task.getId(), task.getName(), task.getTaskDefinitionKey(), task.getProcessInstanceId(),
                task.getProcessVariables(), reqVO.getUserIds(), reqVO.getReason());
    }

    private void insertCopies(String taskId, String taskName, String activityId, String instanceId,
                              Map<String, Object> vars, List<Long> userIds, String reason) {
        if (userIds == null || userIds.isEmpty()) {
            return;
        }
        FlowProcessInstanceCopyDO proto = new FlowProcessInstanceCopyDO();
        proto.setProcessInstanceId(instanceId);
        proto.setProcessInstanceName(vars == null ? null : (String) vars.get(
                FlowProcessInstanceServiceImpl.INSTANCE_NAME_VAR));
        proto.setTaskId(taskId);
        proto.setTaskName(taskName);
        proto.setActivityId(activityId);
        proto.setStartUserId(vars == null ? null : toLong(vars.get(PROCESS_START_USER_VAR)));
        proto.setReason(reason);
        for (Long targetUserId : userIds) {
            FlowProcessInstanceCopyDO copy = new FlowProcessInstanceCopyDO();
            copy.setProcessInstanceId(proto.getProcessInstanceId());
            copy.setProcessInstanceName(proto.getProcessInstanceName());
            copy.setTaskId(proto.getTaskId());
            copy.setTaskName(proto.getTaskName());
            copy.setActivityId(proto.getActivityId());
            copy.setStartUserId(proto.getStartUserId());
            copy.setUserId(targetUserId);
            copy.setReason(reason);
            copyMapper.insert(copy);
        }
    }

    @Override
    public void createSignTask(Long userId, CreateSignReq reqVO) {
        Task task = validateActiveTask(reqVO.getId());
        validateAssignee(task, userId);
        if (reqVO.getUserIds() == null || reqVO.getUserIds().isEmpty()) {
            return;
        }
        for (Long signUserId : reqVO.getUserIds()) {
            Task signTask = taskService.newTask();
            signTask.setParentTaskId(task.getId());
            signTask.setName(task.getName() + "【加签】");
            signTask.setAssignee(String.valueOf(signUserId));
            signTask.setTenantId(task.getTenantId());
            taskService.saveTask(signTask);
        }
        log.info("[createSignTask] 加签完成, taskId={}, users={}", task.getId(), reqVO.getUserIds());
    }

    @Override
    public void deleteSignTask(Long userId, ReasonReq reqVO) {
        List<Task> signTasks = taskService.getSubTasks(reqVO.getId());
        for (Task signTask : signTasks) {
            taskService.deleteTask(signTask.getId());
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void withdrawTask(Long userId, ReasonReq reqVO) {
        HistoricTaskInstance his = historyService.createHistoricTaskInstanceQuery()
                .taskId(reqVO.getId()).singleResult();
        if (his == null || his.getEndTime() == null) {
            throw ServiceExceptionUtil.exception(TASK_ALREADY_FINISHED);
        }
        if (!String.valueOf(userId).equals(his.getAssignee())) {
            throw ServiceExceptionUtil.exception(TASK_NOT_ASSIGNEE);
        }
        String pid = his.getProcessInstanceId();
        List<Task> activeTasks = taskService.createTaskQuery().processInstanceId(pid).active().list();
        if (activeTasks.isEmpty()) {
            throw ServiceExceptionUtil.exception(TASK_WITHDRAW_FAIL);
        }
        // 后续节点已有任务完成则不允许撤回
        long finishedAfter = historyService.createHistoricTaskInstanceQuery()
                .processInstanceId(pid).finished()
                .taskCompletedAfter(his.getEndTime()).count();
        if (finishedAfter > 0) {
            throw ServiceExceptionUtil.exception(TASK_WITHDRAW_FAIL);
        }
        String target = his.getTaskDefinitionKey();
        if (target == null || activeTasks.stream().anyMatch(t -> target.equals(t.getTaskDefinitionKey()))) {
            throw ServiceExceptionUtil.exception(TASK_WITHDRAW_FAIL);
        }
        if (reqVO.getReason() != null && !reqVO.getReason().isEmpty()) {
            runtimeService.setVariable(pid, PROCESS_REASON_VAR, reqVO.getReason());
        }
        runtimeService.createChangeActivityStateBuilder()
                .processInstanceId(pid)
                .moveActivityIdTo(activeTasks.get(0).getTaskDefinitionKey(), target)
                .changeState();
        log.info("[withdrawTask] 任务撤回, taskId={}, target={}, user={}", reqVO.getId(), target, userId);
    }

    // ==================== 实例任务列表 / 可退回节点 ====================

    @Override
    public List<TaskVO> getTaskListByProcessInstanceId(String processInstanceId) {
        List<HistoricTaskInstance> tasks = historyService.createHistoricTaskInstanceQuery()
                .processInstanceId(processInstanceId)
                .includeProcessVariables()
                .includeTaskLocalVariables()
                .orderByTaskCreateTime().asc()
                .list();
        return buildHistoricTasks(tasks, null);
    }

    @Override
    public List<TaskVO> getTaskListByReturn(Long userId, String taskId) {
        Task task = validateActiveTask(taskId);
        Set<String> visited = new HashSet<>();
        List<TaskVO> result = new ArrayList<>();
        List<HistoricTaskInstance> hisTasks = historyService.createHistoricTaskInstanceQuery()
                .processInstanceId(task.getProcessInstanceId())
                .finished()
                .orderByHistoricTaskInstanceStartTime().asc()
                .list();
        for (HistoricTaskInstance his : hisTasks) {
            String key = his.getTaskDefinitionKey();
            if (key == null || key.equals(task.getTaskDefinitionKey()) || !visited.add(key)) {
                continue;
            }
            TaskVO vo = new TaskVO();
            vo.setId(key);
            vo.setName(his.getName());
            vo.setProcessInstanceId(task.getProcessInstanceId());
            result.add(vo);
        }
        return result;
    }

    // ==================== 内部 ====================

    private Task validateActiveTask(String taskId) {
        Task task = taskService.createTaskQuery().taskId(taskId).singleResult();
        if (task == null) {
            throw ServiceExceptionUtil.exception(TASK_ALREADY_FINISHED);
        }
        return task;
    }

    /** 服务端二次校验：当前登录人 ∈ 任务 assignee/candidate（管理员跳过由网关层角色控制） */
    private void validateAssignee(Task task, Long userId) {
        Long count = taskService.createTaskQuery()
                .taskId(task.getId())
                .taskCandidateOrAssigned(String.valueOf(userId))
                .count();
        if (count == 0) {
            throw ServiceExceptionUtil.exception(TASK_NOT_ASSIGNEE);
        }
    }

    /** 候选任务完成前认领：否则历史任务 assignee 为空，已办列表/审批进度查不到经办人 */
    private void claimIfUnassigned(Task task, Long userId) {
        if (task.getAssignee() == null) {
            taskService.setAssignee(task.getId(), String.valueOf(userId));
            task.setAssignee(String.valueOf(userId));
        }
    }

    private void deleteSignChildren(String taskId) {
        List<Task> signTasks = taskService.getSubTasks(taskId);
        for (Task signTask : signTasks) {
            taskService.deleteTask(signTask.getId());
        }
    }

    private TaskCandidateConf loadCandidateConf(Task task) {
        try {
            BpmnModel bpmnModel = repositoryService.getBpmnModel(task.getProcessDefinitionId());
            FlowElement element = bpmnModel.getFlowElement(task.getTaskDefinitionKey());
            if (element instanceof UserTask userTask) {
                List<org.flowable.bpmn.model.ExtensionElement> exts = userTask.getExtensionElements()
                        .get(SimpleModelConverter.EXT_CANDIDATE_CONF);
                return TaskCandidateConf.parse(exts == null || exts.isEmpty() ? null : exts.get(0));
            }
        }
        catch (Exception e) {
            log.warn("[loadCandidateConf] 读取候选人配置失败, task={}", task.getId(), e);
        }
        return null;
    }

    private List<TaskVO> buildTasks(List<Task> tasks, boolean todo) {
        Set<Long> userIds = new HashSet<>();
        for (Task task : tasks) {
            Long assignee = toLong(task.getAssignee());
            if (assignee != null) {
                userIds.add(assignee);
            }
            // 发起人从流程变量读取（toTaskBase），一并进入批量昵称查询
            Long startUser = toLong(task.getProcessVariables() == null ? null
                    : task.getProcessVariables().get(PROCESS_START_USER_VAR));
            if (startUser != null) {
                userIds.add(startUser);
            }
        }
        Map<Long, AdminUserRespDTO> userMap = adminUserApi.getUserMap(userIds);
        List<TaskVO> result = new ArrayList<>();
        for (Task task : tasks) {
            TaskVO vo = toTaskBase(task.getId(), task.getName(), task.getProcessInstanceId(), task.getCreateTime(),
                    task.getProcessVariables(), task.getProcessDefinitionId());
            Long assignee = toLong(task.getAssignee());
            vo.setStatus(todo ? (assignee == null ? 0 : 7) : 2);
            if (assignee != null) {
                AdminUserRespDTO user = userMap.get(assignee);
                vo.setAssigneeUser(new FlowUserVO(assignee, user == null ? null : user.getNickname()));
            }
            if (vo.getStartUser() != null) {
                AdminUserRespDTO user = userMap.get(vo.getStartUser().getId());
                vo.getStartUser().setNickname(user == null ? null : user.getNickname());
            }
            result.add(vo);
        }
        return result;
    }

    private List<TaskVO> buildHistoricTasks(List<HistoricTaskInstance> tasks, Integer fixedStatus) {
        Set<Long> userIds = new HashSet<>();
        for (HistoricTaskInstance his : tasks) {
            Long assignee = toLong(his.getAssignee());
            if (assignee != null) {
                userIds.add(assignee);
            }
            Object startUserId = his.getProcessVariables() == null ? null
                    : his.getProcessVariables().get(PROCESS_START_USER_VAR);
            Long startUser = toLong(startUserId);
            if (startUser != null) {
                userIds.add(startUser);
            }
        }
        Map<Long, AdminUserRespDTO> userMap = adminUserApi.getUserMap(userIds);
        List<TaskVO> result = new ArrayList<>();
        for (HistoricTaskInstance his : tasks) {
            TaskVO vo = toTaskBase(his.getId(), his.getName(), his.getProcessInstanceId(), his.getCreateTime(),
                    his.getProcessVariables(), his.getProcessDefinitionId());
            vo.setEndTime(his.getEndTime());
            vo.setDurationInMillis(his.getDurationInMillis());
            Object reason = his.getTaskLocalVariables() == null ? null : his.getTaskLocalVariables().get("reason");
            vo.setReason(reason == null ? null : String.valueOf(reason));
            vo.setStatus(fixedStatus != null ? fixedStatus : (his.getEndTime() == null ? 7 : 2));
            if (his.getEndTime() != null && his.getDeleteReason() != null && !his.getDeleteReason().isEmpty()) {
                // 已完成任务默认按通过展示，删除原因区分拒绝/取消/退回（reject: / cancel: / Change parent）
                String deleteReason = his.getDeleteReason();
                if (deleteReason.startsWith("reject:")) {
                    vo.setStatus(3);
                }
                else if (deleteReason.startsWith("cancel")) {
                    vo.setStatus(4);
                }
                else if (deleteReason.startsWith("Change parent")) {
                    vo.setStatus(5);
                }
            }
            Long assignee = toLong(his.getAssignee());
            if (assignee != null) {
                AdminUserRespDTO user = userMap.get(assignee);
                vo.setAssigneeUser(new FlowUserVO(assignee, user == null ? null : user.getNickname()));
            }
            if (vo.getStartUser() != null) {
                AdminUserRespDTO user = userMap.get(vo.getStartUser().getId());
                vo.getStartUser().setNickname(user == null ? null : user.getNickname());
            }
            result.add(vo);
        }
        return result;
    }

    private TaskVO toTaskBase(String id, String name, String processInstanceId,
                            java.util.Date createTime, Map<String, Object> vars, String processDefinitionId) {
        TaskVO vo = new TaskVO();
        vo.setId(id);
        vo.setName(name);
        vo.setProcessInstanceId(processInstanceId);
        vo.setCreateTime(createTime);
        if (vars != null) {
            Object instanceName = vars.get(FlowProcessInstanceServiceImpl.INSTANCE_NAME_VAR);
            vo.setProcessInstanceName(instanceName == null ? null : String.valueOf(instanceName));
            Long startUserId = toLong(vars.get(PROCESS_START_USER_VAR));
            if (startUserId != null) {
                vo.setStartUser(new FlowUserVO(startUserId, null));
            }
        }
        if (processDefinitionId != null) {
            var definition = repositoryService.createProcessDefinitionQuery()
                    .processDefinitionId(processDefinitionId).singleResult();
            if (definition != null) {
                vo.setProcessDefinitionKey(definition.getKey());
                vo.setProcessDefinitionName(definition.getName());
            }
        }
        return vo;
    }

    private Long toLong(String value) {
        if (value == null || !value.matches("\\d+")) {
            return null;
        }
        return Long.valueOf(value);
    }

    private Long toLong(Object value) {
        if (value instanceof Number number) {
            return number.longValue();
        }
        return value == null ? null : toLong(String.valueOf(value));
    }

}
