package com.basiclab.iot.flow.service.instance;

import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.exception.util.ServiceExceptionUtil;
import com.basiclab.iot.common.utils.json.JsonUtils;
import com.basiclab.iot.flow.controller.admin.processinstance.FlowProcessInstanceVOs.ActivityNode;
import com.basiclab.iot.flow.controller.admin.processinstance.FlowProcessInstanceVOs.ApprovalDetail;
import com.basiclab.iot.flow.controller.admin.processinstance.FlowProcessInstanceVOs.BpmnModelView;
import com.basiclab.iot.flow.controller.admin.processinstance.FlowProcessInstanceVOs.CreateReq;
import com.basiclab.iot.flow.controller.admin.processinstance.FlowProcessInstanceVOs.Instance;
import com.basiclab.iot.flow.controller.admin.processinstance.FlowProcessInstanceVOs.NextApprovalNode;
import com.basiclab.iot.flow.controller.admin.processinstance.FlowProcessInstanceVOs.TaskItem;
import com.basiclab.iot.flow.controller.admin.vo.FlowUserVO;
import com.basiclab.iot.flow.dal.dataobject.FlowProcessInstanceCopyDO;
import com.basiclab.iot.flow.dal.pgsql.FlowProcessInstanceCopyMapper;
import com.basiclab.iot.flow.framework.flowable.core.SimpleFlowNodeVO;
import com.basiclab.iot.flow.service.candidate.FlowCandidateService;
import com.basiclab.iot.flow.service.model.FlowModelService;
import com.basiclab.iot.system.api.user.AdminUserApi;
import lombok.extern.slf4j.Slf4j;
import org.flowable.engine.HistoryService;
import org.flowable.engine.IdentityService;
import org.flowable.engine.RepositoryService;
import org.flowable.engine.RuntimeService;
import org.flowable.engine.TaskService;
import org.flowable.engine.history.HistoricProcessInstance;
import org.flowable.engine.history.HistoricProcessInstanceQuery;
import org.flowable.engine.repository.Model;
import org.flowable.engine.repository.ProcessDefinition;
import org.flowable.engine.runtime.ProcessInstance;
import org.flowable.task.api.Task;
import org.flowable.task.api.history.HistoricTaskInstance;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import javax.annotation.Resource;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

import static com.basiclab.iot.flow.enums.FlowEnums.PROCESS_REASON_VAR;
import static com.basiclab.iot.flow.enums.FlowEnums.PROCESS_START_USER_VAR;
import static com.basiclab.iot.flow.enums.FlowEnums.PROCESS_STATUS_VAR;

/**
 * 流程实例 Service 实现
 */
@Slf4j
@Service
public class FlowProcessInstanceServiceImpl implements FlowProcessInstanceService {

    /** 实例名称变量（监听器/抄送委托读取） */
    public static final String INSTANCE_NAME_VAR = "PROCESS_INSTANCE_NAME";

    @Resource
    private RuntimeService runtimeService;
    @Resource
    private HistoryService historyService;
    @Resource
    private RepositoryService repositoryService;
    @Resource
    private TaskService taskService;
    @Resource
    private IdentityService identityService;
    @Resource
    private FlowCandidateService candidateService;
    @Resource
    private FlowModelService modelService;
    @Resource
    private AdminUserApi adminUserApi;
    @Resource
    private FlowProcessInstanceCopyMapper copyMapper;

    // ==================== 发起 ====================

    @Override
    @Transactional(rollbackFor = Exception.class)
    public String createProcessInstance(Long startUserId, CreateReq reqVO) {
        String definition = reqVO.getProcessDefinitionId() != null ? reqVO.getProcessDefinitionId()
                : reqVO.getProcessDefinitionKey();
        return startProcess(startUserId, definition, null, null, reqVO.getVariables(),
                reqVO.getStartUserSelectAssignees());
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public String startProcess(Long startUserId, String processDefinitionIdOrKey, String businessKey,
                               String instanceName, Map<String, Object> variables,
                               Map<String, List<Long>> startUserSelectAssignees) {
        ProcessDefinition definition = resolveDefinition(processDefinitionIdOrKey);
        if (definition == null) {
            throw ServiceExceptionUtil.exception(
                    com.basiclab.iot.flow.enums.FlowErrorCodeConstants.PROCESS_DEFINITION_NOT_EXISTS);
        }
        Map<String, Object> vars = variables == null ? new HashMap<>() : new HashMap<>(variables);
        vars.put(PROCESS_START_USER_VAR, startUserId);
        // 实例名先放入启动变量：TASK_CREATED 全局事件（如待办站内信）在 startProcessInstanceById 内触发，之后的 setVariable 它读不到
        if (instanceName != null) {
            vars.put(INSTANCE_NAME_VAR, instanceName);
        }
        if (startUserSelectAssignees != null && !startUserSelectAssignees.isEmpty()) {
            vars.put("startUserSelectAssignees", startUserSelectAssignees);
        }
        // 多实例（会签/依次）候选人需要启动前解析为集合变量
        preResolveMultiInstanceAssignees(definition, startUserId, vars);

        try {
            identityService.setAuthenticatedUserId(String.valueOf(startUserId));
            ProcessInstance instance = runtimeService.startProcessInstanceById(definition.getId(), businessKey, vars);
            String name = instanceName == null ? definition.getName() : instanceName;
            if (name != null) {
                runtimeService.setProcessInstanceName(instance.getId(), name);
                runtimeService.setVariable(instance.getId(), INSTANCE_NAME_VAR, name);
            }
            log.info("[startProcess] 流程发起成功, instanceId={}, definition={}, businessKey={}, startUser={}",
                    instance.getId(), definition.getKey(), businessKey, startUserId);
            return instance.getId();
        }
        finally {
            identityService.setAuthenticatedUserId(null);
        }
    }

    private ProcessDefinition resolveDefinition(String idOrKey) {
        if (idOrKey == null || idOrKey.isEmpty()) {
            return null;
        }
        ProcessDefinition definition = repositoryService.getProcessDefinition(idOrKey);
        if (definition == null) {
            definition = repositoryService.createProcessDefinitionQuery()
                    .processDefinitionKey(idOrKey).latestVersion().active().singleResult();
        }
        return definition;
    }

    /** 会签/依次审批节点：启动前解析候选人注入 mi_assignees_{nodeId} 集合变量 */
    private void preResolveMultiInstanceAssignees(ProcessDefinition definition, Long startUserId,
                                                  Map<String, Object> vars) {
        List<SimpleFlowNodeVO> miNodes = findMultiInstanceNodes(definition);
        for (SimpleFlowNodeVO node : miNodes) {
            var conf = toCandidateConf(node);
            List<Long> userIds = candidateService.resolve(conf, startUserId, vars, node.getId());
            if (userIds.isEmpty()) {
                userIds = candidateService.resolveAssignEmpty(conf, startUserId);
            }
            if (userIds.isEmpty()) {
                // 多实例集合为空会抛引擎异常，用发起人兜底
                userIds = startUserId == null ? List.of(1L) : List.of(startUserId);
            }
            vars.put("mi_assignees_" + node.getId(), userIds);
        }
    }

    private List<SimpleFlowNodeVO> findMultiInstanceNodes(ProcessDefinition definition) {
        List<SimpleFlowNodeVO> result = new ArrayList<>();
        SimpleFlowNodeVO root = readSimpleModel(definition);
        if (root == null) {
            return result;
        }
        walkNodes(root, result);
        return result;
    }

    private void walkNodes(SimpleFlowNodeVO node, List<SimpleFlowNodeVO> acc) {
        while (node != null) {
            if (node.getType() != null && node.getType() == 11
                    && node.getApproveMethod() != null && (node.getApproveMethod() == 2 || node.getApproveMethod() == 4)) {
                acc.add(node);
            }
            if (node.getConditionNodes() != null) {
                for (SimpleFlowNodeVO branch : node.getConditionNodes()) {
                    walkNodes(branch.getChildNode(), acc);
                }
            }
            node = node.getChildNode();
        }
    }

    private SimpleFlowNodeVO readSimpleModel(ProcessDefinition definition) {
        Model model = repositoryService.createModelQuery()
                .modelKey(definition.getKey()).latestVersion().singleResult();
        if (model == null) {
            return null;
        }
        Object simpleModel = modelService.getModelSimple(model.getId());
        if (simpleModel == null) {
            return null;
        }
        return JsonUtils.parseObject2(JsonUtils.toJsonString(simpleModel), SimpleFlowNodeVO.class);
    }

    private com.basiclab.iot.flow.framework.flowable.core.TaskCandidateConf toCandidateConf(SimpleFlowNodeVO node) {
        var conf = new com.basiclab.iot.flow.framework.flowable.core.TaskCandidateConf();
        conf.setCandidateStrategy(node.getCandidateStrategy());
        conf.setCandidateParam(node.getCandidateParam());
        conf.setApproveMethod(node.getApproveMethod());
        if (node.getAssignEmptyHandler() != null) {
            conf.setAssignEmptyHandlerType(node.getAssignEmptyHandler().getType());
            conf.setAssignEmptyUserIds(node.getAssignEmptyHandler().getUserIds());
        }
        conf.setAssignStartUserHandlerType(node.getAssignStartUserHandlerType());
        return conf;
    }

    // ==================== 查询 ====================

    @Override
    public PageResult<Instance> getMyProcessInstancePage(Long userId, PageParam pageParam, String name,
                                                         String processDefinitionKey, String category, Integer status) {
        HistoricProcessInstanceQuery query = basePageQuery(pageParam, name, processDefinitionKey, category, status);
        query.startedBy(String.valueOf(userId));
        return executePageQuery(pageParam, query);
    }

    @Override
    public PageResult<Instance> getManagerProcessInstancePage(PageParam pageParam, String name,
                                                              String processDefinitionKey, String category, Integer status) {
        HistoricProcessInstanceQuery query = basePageQuery(pageParam, name, processDefinitionKey, category, status);
        return executePageQuery(pageParam, query);
    }

    private HistoricProcessInstanceQuery basePageQuery(PageParam pageParam, String name,
                                                       String processDefinitionKey, String category, Integer status) {
        HistoricProcessInstanceQuery query = historyService.createHistoricProcessInstanceQuery();
        if (name != null && !name.isEmpty()) {
            query.processInstanceNameLike("%" + name + "%");
        }
        if (processDefinitionKey != null && !processDefinitionKey.isEmpty()) {
            query.processDefinitionKey(processDefinitionKey);
        }
        if (category != null && !category.isEmpty()) {
            query.processDefinitionCategory(category);
        }
        if (status != null) {
            if (status == 1) {
                query.unfinished();
            }
            else {
                query.finished();
            }
        }
        query.includeProcessVariables().orderByProcessInstanceStartTime().desc();
        return query;
    }

    private PageResult<Instance> executePageQuery(PageParam pageParam, HistoricProcessInstanceQuery query) {
        long total = query.count();
        List<HistoricProcessInstance> instances = query.listPage(
                (pageParam.getPageNo() - 1) * pageParam.getPageSize(), pageParam.getPageSize());
        List<Instance> result = new ArrayList<>();
        for (HistoricProcessInstance instance : instances) {
            Instance vo = buildInstance(instance);
            // status 过滤的尾筛（2/3/4 需要读变量）
            result.add(vo);
        }
        return new PageResult<>(result, total);
    }

    @Override
    public Instance getProcessInstance(String id) {
        HistoricProcessInstance instance = historyService.createHistoricProcessInstanceQuery()
                .processInstanceId(id).includeProcessVariables().singleResult();
        if (instance == null) {
            throw ServiceExceptionUtil.exception(
                    com.basiclab.iot.flow.enums.FlowErrorCodeConstants.PROCESS_INSTANCE_NOT_EXISTS);
        }
        return buildInstance(instance);
    }

    private Instance buildInstance(HistoricProcessInstance historic) {
        Instance vo = new Instance();
        vo.setId(historic.getId());
        vo.setName(historic.getName());
        vo.setStartTime(historic.getStartTime());
        vo.setEndTime(historic.getEndTime());
        vo.setDurationInMillis(historic.getDurationInMillis());
        vo.setBusinessKey(historic.getBusinessKey());
        vo.setProcessDefinitionId(historic.getProcessDefinitionId());
        vo.setProcessDefinitionKey(historic.getProcessDefinitionKey());
        vo.setProcessDefinitionName(historic.getProcessDefinitionName());
        vo.setStartUserId(parseLong(historic.getStartUserId()));
        Map<String, Object> vars = historic.getProcessVariables();
        if (vars == null) {
            vars = Map.of();
        }
        vo.setProcessVariables(vars);
        if (vo.getStartUserId() == null) {
            vo.setStartUserId(toLong(vars.get(PROCESS_START_USER_VAR)));
        }
        // 状态
        vo.setStatus(resolveStatus(historic.getId(), vars));
        Object reason = vars.get(PROCESS_REASON_VAR);
        vo.setReason(reason == null ? null : String.valueOf(reason));
        // 当前 / 最后节点
        if (Integer.valueOf(1).equals(vo.getStatus())) {
            List<Task> activeTasks = taskService.createTaskQuery()
                    .processInstanceId(historic.getId()).active().list();
            vo.setTaskName(activeTasks.stream().map(Task::getName).distinct()
                    .reduce((a, b) -> a + "、" + b).orElse(null));
        }
        else {
            List<HistoricTaskInstance> finished = historyService.createHistoricTaskInstanceQuery()
                    .processInstanceId(historic.getId()).finished().orderByHistoricTaskInstanceEndTime().desc()
                    .listPage(0, 1);
            vo.setTaskName(finished.isEmpty() ? null : finished.get(0).getName());
        }
        // 发起人昵称
        if (vo.getStartUserId() != null) {
            Map<Long, com.basiclab.iot.system.api.user.dto.AdminUserRespDTO> users =
                    adminUserApi.getUserMap(List.of(vo.getStartUserId()));
            com.basiclab.iot.system.api.user.dto.AdminUserRespDTO user = users.get(vo.getStartUserId());
            if (user != null) {
                vo.setStartUserNickname(user.getNickname());
            }
        }
        // 分类（定义 category 即分类 code）
        ProcessDefinition definition = repositoryService.createProcessDefinitionQuery()
                .processDefinitionId(historic.getProcessDefinitionId()).singleResult();
        vo.setCategoryId(definition == null ? null : definition.getCategory());
        return vo;
    }

    private Integer resolveStatus(String instanceId, Map<String, Object> vars) {
        Object status = vars.get(PROCESS_STATUS_VAR);
        if (status instanceof Number number) {
            return number.intValue();
        }
        if (runtimeService.createProcessInstanceQuery().processInstanceId(instanceId).count() > 0) {
            return 1;
        }
        return 2;
    }

    // ==================== 审批详情聚合 ====================

    @Override
    public ApprovalDetail getApprovalDetail(String id, String taskId) {
        ApprovalDetail detail = new ApprovalDetail();
        detail.setProcessInstance(getProcessInstance(id));
        Integer instanceStatus = detail.getProcessInstance().getStatus();

        List<HistoricTaskInstance> tasks = historyService.createHistoricTaskInstanceQuery()
                .processInstanceId(id).includeProcessVariables().includeTaskLocalVariables()
                .orderByTaskCreateTime().asc().list();
        Map<String, ActivityNode> nodeMap = new LinkedHashMap<>();
        List<ActivityNode> nodes = new ArrayList<>();
        for (HistoricTaskInstance his : tasks) {
            String nodeKey = his.getTaskDefinitionKey() == null ? his.getId() : his.getTaskDefinitionKey();
            ActivityNode node = nodeMap.get(nodeKey);
            if (node == null) {
                node = new ActivityNode();
                node.setId(nodeKey);
                node.setName(his.getName());
                node.setNodeType(11);
                node.setTasks(new ArrayList<>());
                nodeMap.put(nodeKey, node);
                nodes.add(node);
            }
            node.getTasks().add(buildTaskItem(his, instanceStatus));
        }
        detail.setActivityNodes(nodes);
        return detail;
    }

    private TaskItem buildTaskItem(HistoricTaskInstance his, Integer instanceStatus) {
        TaskItem item = new TaskItem();
        item.setId(his.getId());
        item.setName(his.getName());
        item.setCreateTime(his.getCreateTime());
        item.setEndTime(his.getEndTime());
        item.setStatus(deriveTaskStatus(his, instanceStatus));
        Object reason = his.getTaskLocalVariables() == null ? null : his.getTaskLocalVariables().get("reason");
        if (reason != null && !String.valueOf(reason).isEmpty()) {
            item.setReason(String.valueOf(reason));
        }
        if (his.getAssignee() != null) {
            Long assignee = parseLong(his.getAssignee());
            if (assignee != null) {
                Map<Long, com.basiclab.iot.system.api.user.dto.AdminUserRespDTO> users =
                        adminUserApi.getUserMap(List.of(assignee));
                com.basiclab.iot.system.api.user.dto.AdminUserRespDTO user = users.get(assignee);
                item.setAssigneeUser(new FlowUserVO(assignee, user == null ? his.getAssignee() : user.getNickname()));
            }
        }
        return item;
    }

    /** 任务状态推导（依赖服务侧可控的 deleteReason 前缀约定） */
    private Integer deriveTaskStatus(HistoricTaskInstance his, Integer instanceStatus) {
        if (his.getEndTime() == null) {
            return his.getAssignee() == null ? 0 : 7;
        }
        String deleteReason = his.getDeleteReason();
        if (deleteReason == null || deleteReason.isEmpty()) {
            return 2;
        }
        String lower = deleteReason.toLowerCase();
        if (deleteReason.startsWith("reject:")) {
            return 3;
        }
        if (deleteReason.startsWith("cancel:")) {
            return 4;
        }
        if (lower.contains("change")) {
            return 5;
        }
        if (Integer.valueOf(3).equals(instanceStatus)) {
            return 3;
        }
        if (Integer.valueOf(4).equals(instanceStatus)) {
            return 4;
        }
        return 2;
    }

    // ==================== Simple 模型运行视图 ====================

    @Override
    public BpmnModelView getBpmnModelView(String id) {
        Instance instance = getProcessInstance(id);
        ProcessDefinition definition = repositoryService.createProcessDefinitionQuery()
                .processDefinitionId(instance.getProcessDefinitionId()).singleResult();

        BpmnModelView view = new BpmnModelView();
        view.setId(instance.getId());
        view.setName(instance.getName());
        view.setProcessDefinitionId(instance.getProcessDefinitionId());
        if (definition != null) {
            SimpleFlowNodeVO root = readSimpleModel(definition);
            view.setSimpleModel(root);
        }

        Set<String> finished = new HashSet<>();
        Set<String> rejected = new HashSet<>();
        List<HistoricTaskInstance> finishedTasks = historyService.createHistoricTaskInstanceQuery()
                .processInstanceId(id).finished().list();
        for (HistoricTaskInstance his : finishedTasks) {
            if (his.getTaskDefinitionKey() == null) {
                continue;
            }
            int status = deriveTaskStatus(his, instance.getStatus());
            if (status == 2) {
                finished.add(his.getTaskDefinitionKey());
            }
            else if (status == 3) {
                rejected.add(his.getTaskDefinitionKey());
            }
        }
        Set<String> unfinished = new HashSet<>();
        for (Task task : taskService.createTaskQuery().processInstanceId(id).active().list()) {
            if (task.getTaskDefinitionKey() != null) {
                unfinished.add(task.getTaskDefinitionKey());
            }
        }
        view.setFinishedTaskActivityIds(new ArrayList<>(finished));
        view.setRejectedTaskActivityIds(new ArrayList<>(rejected));
        view.setUnfinishedTaskActivityIds(new ArrayList<>(unfinished));
        return view;
    }

    // ==================== 下一审批节点预测 ====================

    @Override
    public List<NextApprovalNode> getNextApprovalNodes(String processDefinitionId, String activityId,
                                                       Map<String, Object> variables) {
        ProcessDefinition definition = resolveDefinition(processDefinitionId);
        if (definition == null) {
            return List.of();
        }
        SimpleFlowNodeVO root = readSimpleModel(definition);
        if (root == null) {
            return List.of();
        }
        List<NextApprovalNode> result = new ArrayList<>();
        SimpleFlowNodeVO node = root.getChildNode();
        boolean skip = activityId != null && !activityId.isEmpty();
        Map<String, Object> vars = variables == null ? Map.of() : variables;
        while (node != null) {
            if (skip) {
                if (activityId.equals(node.getId())) {
                    skip = false;
                }
                node = nextNode(node);
                continue;
            }
            if (node.getType() != null && node.getType() == 11) {
                NextApprovalNode vo = new NextApprovalNode();
                vo.setId(node.getId());
                vo.setName(node.getName());
                vo.setNodeType(11);
                var conf = toCandidateConf(node);
                List<Long> userIds = candidateService.resolve(conf, null, vars, node.getId());
                Map<Long, com.basiclab.iot.system.api.user.dto.AdminUserRespDTO> userMap =
                        adminUserApi.getUserMap(userIds);
                List<FlowUserVO> users = new ArrayList<>();
                for (Long userId : userIds) {
                    com.basiclab.iot.system.api.user.dto.AdminUserRespDTO user = userMap.get(userId);
                    users.add(new FlowUserVO(userId, user == null ? String.valueOf(userId) : user.getNickname()));
                }
                vo.setCandidateUsers(users);
                result.add(vo);
                return result;
            }
            node = nextNode(node);
        }
        return result;
    }

    /** 条件分支走第一条分支（预测精度以顺序链为主，分支场景返回分支首节点） */
    private SimpleFlowNodeVO nextNode(SimpleFlowNodeVO node) {
        if (node.getChildNode() != null) {
            return node.getChildNode();
        }
        return null;
    }

    // ==================== 取消 ====================

    @Override
    public void cancelProcessInstanceByStartUser(Long userId, String id, String reason) {
        Instance instance = getProcessInstance(id);
        if (!userId.equals(instance.getStartUserId())) {
            throw ServiceExceptionUtil.exception(
                    com.basiclab.iot.flow.enums.FlowErrorCodeConstants.PROCESS_INSTANCE_CANCEL_FAIL_NOT_OWNER);
        }
        doCancel(id, reason);
    }

    @Override
    public void cancelProcessInstanceByAdmin(Long userId, String id, String reason) {
        getProcessInstance(id);
        doCancel(id, reason);
    }

    private void doCancel(String id, String reason) {
        ProcessInstance instance = runtimeService.createProcessInstanceQuery()
                .processInstanceId(id).singleResult();
        if (instance == null) {
            throw ServiceExceptionUtil.exception(
                    com.basiclab.iot.flow.enums.FlowErrorCodeConstants.PROCESS_INSTANCE_CANCEL_FAIL_NOT_EXISTS);
        }
        String cancelReason = "cancel:" + (reason == null ? "" : reason);
        runtimeService.setVariable(id, PROCESS_STATUS_VAR, 4);
        runtimeService.setVariable(id, PROCESS_REASON_VAR, reason);
        runtimeService.deleteProcessInstance(id, cancelReason);
        log.info("[doCancel] 流程取消, instanceId={}, reason={}", id, reason);
    }

    // ==================== 抄送 ====================

    @Override
    public PageResult<FlowProcessInstanceCopyDO> getProcessInstanceCopyPage(Long userId, PageParam pageParam,
                                                                            String processInstanceName) {
        return copyMapper.selectPageByUserId(pageParam, userId, processInstanceName);
    }

    // ==================== 工具 ====================

    private Long parseLong(String value) {
        if (value == null || !value.matches("\\d+")) {
            return null;
        }
        return Long.valueOf(value);
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
