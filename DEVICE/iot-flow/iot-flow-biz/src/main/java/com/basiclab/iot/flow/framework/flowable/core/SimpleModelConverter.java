package com.basiclab.iot.flow.framework.flowable.core;

import com.basiclab.iot.flow.enums.FlowNodeType;

import org.flowable.bpmn.model.BoundaryEvent;
import org.flowable.bpmn.model.BpmnModel;
import org.flowable.bpmn.model.EndEvent;
import org.flowable.bpmn.model.ExclusiveGateway;
import org.flowable.bpmn.model.ExtensionAttribute;
import org.flowable.bpmn.model.ExtensionElement;
import org.flowable.bpmn.model.FlowElement;
import org.flowable.bpmn.model.Gateway;
import org.flowable.bpmn.model.ImplementationType;
import org.flowable.bpmn.model.IntermediateCatchEvent;
import org.flowable.bpmn.model.MultiInstanceLoopCharacteristics;
import org.flowable.bpmn.model.ParallelGateway;
import org.flowable.bpmn.model.Process;
import org.flowable.bpmn.model.SequenceFlow;
import org.flowable.bpmn.model.ServiceTask;
import org.flowable.bpmn.model.StartEvent;
import org.flowable.bpmn.model.TimerEventDefinition;
import org.flowable.bpmn.model.UserTask;

import java.util.ArrayList;
import java.util.List;

import static org.flowable.bpmn.constants.BpmnXMLConstants.FLOWABLE_EXTENSIONS_NAMESPACE;
import static org.flowable.bpmn.constants.BpmnXMLConstants.FLOWABLE_EXTENSIONS_PREFIX;

/**
 * Simple 设计器节点树 -> Flowable BpmnModel 转换器
 *
 * 节点子集：发起人 / 审批 / 抄送 / 延迟器 / 条件分支（排他网关）/ 并行分支（并行网关）。
 * 审批节点的候选人策略、超时、拒绝处理等配置通过扩展元素（candidateConf）写入 BPMN，
 * 运行期由 {@code FlowTaskCandidateListener} / {@code FlowTimeoutDelegate} / {@code FlowCopyDelegate} 读取执行。
 *
 * 多实例（会签/依次审批）候选人集合变量 mi_assignees_{nodeId} 在流程启动前由服务层解析注入。
 */
public class SimpleModelConverter {

    // ---------- 扩展元素契约（运行期依赖） ----------
    public static final String EXT_CANDIDATE_CONF = "candidateConf";
    public static final String EXT_CONF_STRATEGY = "candidateStrategy";
    public static final String EXT_CONF_PARAM = "candidateParam";
    public static final String EXT_CONF_METHOD = "approveMethod";
    public static final String EXT_CONF_RATIO = "approveRatio";
    public static final String EXT_CONF_REASON_REQUIRE = "reasonRequire";
    public static final String EXT_CONF_ASSIGN_EMPTY = "assignEmptyHandler";
    public static final String EXT_CONF_ASSIGN_EMPTY_USERS = "assignEmptyUserIds";
    public static final String EXT_CONF_ASSIGN_START_USER = "assignStartUserHandlerType";
    public static final String EXT_CONF_REJECT_TYPE = "rejectHandlerType";
    public static final String EXT_CONF_REJECT_RETURN = "rejectReturnNodeId";
    public static final String MI_ASSIGNEE_VAR_PREFIX = "mi_assignees_";
    /** 流程变量：发起人 ID */
    public static final String START_USER_VAR = "PROCESS_START_USER_ID";

    private final BpmnModel bpmnModel = new BpmnModel();
    private final Process process = new Process();

    public SimpleModelConverter(String processId, String processName) {
        process.setId(processId);
        process.setName(processName);
        bpmnModel.addProcess(process);
    }

    /** 转换主入口：root 为发起人节点（root 自身不产生元素，从其 childNode 开始） */
    public BpmnModel convert(SimpleFlowNodeVO root) {
        StartEvent start = new StartEvent();
        start.setId("start_event");
        start.setName("开始");
        process.addFlowElement(start);

        if (root != null && root.getChildNode() != null) {
            convertChain(root.getChildNode(), start.getId());
        }
        return bpmnModel;
    }

    /**
     * 转换一条链；链尾自动接结束事件（链尾已是 END / 已有汇聚元素时按元素语义处理）
     */
    private void convertChain(SimpleFlowNodeVO node, String sourceId) {
        convertNode(node, sourceId, true);
    }

    /**
     * @param incomingFlow 是否由本方法创建 sourceId -> 本节点的连线（分支首元素由分支线提供连线）
     * @return 链尾元素（不接结束事件的场景由调用方继续处理）
     */
    private FlowElement convertNode(SimpleFlowNodeVO node, String sourceId, boolean incomingFlow) {
        Integer type = node.getType();
        if (FlowNodeType.END_EVENT_NODE.getType().equals(type)) {
            EndEvent end = new EndEvent();
            end.setId(node.getId());
            end.setName(node.getName() == null ? "结束" : node.getName());
            process.addFlowElement(end);
            if (incomingFlow) {
                process.addFlowElement(flow("flow_" + node.getId(), sourceId, end.getId()));
            }
            return end;
        }
        if (FlowNodeType.USER_TASK_NODE.getType().equals(type)) {
            // convertUserTask 内部已通过 appendRest 接好后继链（超时自动通过路径需要后继 id），此处不能再 append
            return convertUserTask(node, sourceId, incomingFlow);
        }
        if (FlowNodeType.COPY_TASK_NODE.getType().equals(type)) {
            FlowElement copy = convertCopyTask(node, sourceId, incomingFlow);
            convertRest(node, copy);
            return copy;
        }
        if (FlowNodeType.DELAY_TIMER_NODE.getType().equals(type)) {
            FlowElement timer = convertDelayTimer(node, sourceId, incomingFlow);
            convertRest(node, timer);
            return timer;
        }
        if (FlowNodeType.CONDITION_BRANCH_NODE.getType().equals(type)
                || FlowNodeType.PARALLEL_BRANCH_NODE.getType().equals(type)) {
            FlowElement join = convertBranch(node, sourceId, incomingFlow);
            convertRest(node, join);
            return join;
        }
        // START_USER_NODE（不应出现在链中）等：直通，不产生元素
        if (node.getChildNode() != null) {
            return convertNode(node.getChildNode(), sourceId, incomingFlow);
        }
        return process.getFlowElement(sourceId);
    }

    /** 链的后继处理：有后继则递归，否则接结束事件 */
    private void convertRest(SimpleFlowNodeVO node, FlowElement current) {
        appendRest(node, current.getId());
    }

    /** 追加后继（或自动接唯一结束事件），返回后继元素 id */
    private String appendRest(SimpleFlowNodeVO node, String currentId) {
        SimpleFlowNodeVO child = node.getChildNode();
        if (child == null) {
            String endId = "end_" + currentId;
            EndEvent end = new EndEvent();
            end.setId(endId);
            end.setName("结束");
            process.addFlowElement(end);
            process.addFlowElement(flow("flow_end_" + currentId, currentId, endId));
            return endId;
        }
        return convertNode(child, currentId, true).getId();
    }

    // ==================== 审批节点 ====================

    private FlowElement convertUserTask(SimpleFlowNodeVO node, String sourceId, boolean incomingFlow) {
        UserTask task = new UserTask();
        task.setId(node.getId());
        task.setName(node.getName());
        applyCandidateConf(task, node);

        int method = node.getApproveMethod() == null ? 3 : node.getApproveMethod();
        if (method == 2 || method == 4) {
            // 会签（按比例，并行多实例）/ 依次审批（顺序多实例）
            MultiInstanceLoopCharacteristics mi = new MultiInstanceLoopCharacteristics();
            mi.setSequential(method == 4);
            mi.setInputDataItem(MI_ASSIGNEE_VAR_PREFIX + node.getId());
            mi.setElementVariable("assignee");
            int ratio = node.getApproveRatio() == null ? 100 : node.getApproveRatio();
            mi.setCompletionCondition("${nrOfCompletedInstances == nrOfInstances"
                    + " || nrOfCompletedInstances * 100 >= nrOfInstances * " + ratio + "}");
            task.setLoopCharacteristics(mi);
            task.setAssignee("${assignee}");
        }

        process.addFlowElement(task);
        if (incomingFlow) {
            process.addFlowElement(flow("flow_" + node.getId(), sourceId, task.getId()));
        }
        // 先接后继链，拿到后继元素 id，供超时自动通过路径复用
        String nextId = appendRest(node, task.getId());
        applyTimeout(task, node, nextId);
        return task;
    }

    private void applyCandidateConf(UserTask task, SimpleFlowNodeVO node) {
        ExtensionElement ext = confElement();
        putAttr(ext, EXT_CONF_STRATEGY, node.getCandidateStrategy());
        putAttr(ext, EXT_CONF_PARAM, node.getCandidateParam());
        putAttr(ext, EXT_CONF_METHOD, node.getApproveMethod());
        putAttr(ext, EXT_CONF_RATIO, node.getApproveRatio());
        putAttr(ext, EXT_CONF_REASON_REQUIRE, node.getReasonRequire());
        putAttr(ext, EXT_CONF_ASSIGN_START_USER, node.getAssignStartUserHandlerType());
        if (node.getAssignEmptyHandler() != null) {
            putAttr(ext, EXT_CONF_ASSIGN_EMPTY, node.getAssignEmptyHandler().getType());
            putAttr(ext, EXT_CONF_ASSIGN_EMPTY_USERS, joinIds(node.getAssignEmptyHandler().getUserIds()));
        }
        if (node.getRejectHandler() != null) {
            putAttr(ext, EXT_CONF_REJECT_TYPE, node.getRejectHandler().getType());
            putAttr(ext, EXT_CONF_REJECT_RETURN, node.getRejectHandler().getReturnNodeId());
        }
        task.getExtensionElements().put(EXT_CANDIDATE_CONF, new ArrayList<>(List.of(ext)));
    }

    /** 审批超时：边界定时器。提醒 = 非中断；通过 = 中断后接原后继；拒绝 = 中断后接独立结束事件 */
    private void applyTimeout(UserTask task, SimpleFlowNodeVO node, String nextId) {
        SimpleFlowNodeVO.TimeoutHandlerVO timeout = node.getTimeoutHandler();
        if (timeout == null || !Boolean.TRUE.equals(timeout.getEnable())
                || timeout.getTimeDuration() == null || timeout.getTimeDuration().isEmpty()) {
            return;
        }
        Integer timeoutType = timeout.getType() == null ? 2 : timeout.getType();
        boolean reminder = timeoutType == 1;

        BoundaryEvent boundary = new BoundaryEvent();
        boundary.setId("timeout_" + node.getId());
        boundary.setAttachedToRef(task);
        boundary.setCancelActivity(!reminder);
        TimerEventDefinition def = new TimerEventDefinition();
        def.setTimeDuration(timeout.getTimeDuration());
        boundary.addEventDefinition(def);
        process.addFlowElement(boundary);

        ServiceTask handler = new ServiceTask();
        handler.setId("timeout_task_" + node.getId());
        handler.setName(reminder ? "超时提醒" : timeoutType == 2 ? "超时自动通过" : "超时自动拒绝");
        handler.setImplementationType(ImplementationType.IMPLEMENTATION_TYPE_EXPRESSION);
        handler.setImplementation("${flowTimeoutDelegate.apply(execution, '" + node.getId() + "', " + timeoutType + ")}");
        process.addFlowElement(handler);
        process.addFlowElement(flow("flow_" + boundary.getId(), boundary.getId(), handler.getId()));

        if (reminder) {
            // 非中断提醒：令牌在 handler 终止即可，原任务继续
            return;
        }
        if (timeoutType == 2) {
            // 自动通过：接到原任务的后继，等价于“审批通过后继续走”
            process.addFlowElement(flow("flow_timeout_go_" + node.getId(), handler.getId(), nextId));
        }
        else {
            // 自动拒绝：以拒绝状态走到独立结束事件（delegate 写 PROCESS_STATUS=3）
            EndEvent end = new EndEvent();
            end.setId("timeout_end_" + node.getId());
            end.setName("超时结束");
            process.addFlowElement(end);
            process.addFlowElement(flow("flow_timeout_end_" + node.getId(), handler.getId(), end.getId()));
        }
    }

    // ==================== 抄送节点 ====================

    private FlowElement convertCopyTask(SimpleFlowNodeVO node, String sourceId, boolean incomingFlow) {
        ServiceTask copy = new ServiceTask();
        copy.setId(node.getId());
        copy.setName(node.getName());
        copy.setImplementationType(ImplementationType.IMPLEMENTATION_TYPE_EXPRESSION);
        copy.setImplementation("${flowCopyDelegate.apply(execution, '" + node.getId() + "')}");
        // 抄送目标复用候选人策略，配置挂扩展元素
        ExtensionElement ext = confElement();
        putAttr(ext, EXT_CONF_STRATEGY, node.getCandidateStrategy());
        putAttr(ext, EXT_CONF_PARAM, node.getCandidateParam());
        copy.getExtensionElements().put(EXT_CANDIDATE_CONF, new ArrayList<>(List.of(ext)));

        process.addFlowElement(copy);
        if (incomingFlow) {
            process.addFlowElement(flow("flow_" + node.getId(), sourceId, copy.getId()));
        }
        return copy;
    }

    // ==================== 延迟器 ====================

    private FlowElement convertDelayTimer(SimpleFlowNodeVO node, String sourceId, boolean incomingFlow) {
        SimpleFlowNodeVO.DelaySettingVO delay = node.getDelaySetting();
        IntermediateCatchEvent catchEvent = new IntermediateCatchEvent();
        catchEvent.setId(node.getId());
        catchEvent.setName(node.getName());
        TimerEventDefinition def = new TimerEventDefinition();
        if (delay != null && delay.getDelayType() != null && delay.getDelayType() == 2
                && delay.getDelayTime() != null && !delay.getDelayTime().isEmpty()) {
            def.setTimeDate(delay.getDelayTime());
        }
        else {
            def.setTimeDuration(delay == null || delay.getDelayTime() == null || delay.getDelayTime().isEmpty()
                    ? "PT1H" : delay.getDelayTime());
        }
        catchEvent.addEventDefinition(def);
        process.addFlowElement(catchEvent);
        if (incomingFlow) {
            process.addFlowElement(flow("flow_" + node.getId(), sourceId, catchEvent.getId()));
        }
        return catchEvent;
    }

    // ==================== 分支 ====================

    /**
     * 条件分支 = 排他网关（按条件走一条路，支持默认分支兜底）；
     * 并行分支 = 并行网关（全部分支执行）。分支汇聚到独立合并网关后继续主链。
     */
    private FlowElement convertBranch(SimpleFlowNodeVO node, String sourceId, boolean incomingFlow) {
        boolean parallel = FlowNodeType.PARALLEL_BRANCH_NODE.getType().equals(node.getType());
        String splitId = node.getId();
        String joinId = node.getId() + "_join";

        if (parallel) {
            ParallelGateway split = new ParallelGateway();
            split.setId(splitId);
            split.setName(node.getName());
            process.addFlowElement(split);
            if (incomingFlow) {
                process.addFlowElement(flow("flow_" + splitId, sourceId, splitId));
            }
        }
        else {
            ExclusiveGateway split = new ExclusiveGateway();
            split.setId(splitId);
            split.setName(node.getName());
            process.addFlowElement(split);
            if (incomingFlow) {
                process.addFlowElement(flow("flow_" + splitId, sourceId, splitId));
            }
        }

        List<SimpleFlowNodeVO> branches = node.getConditionNodes() == null ? new ArrayList<>() : node.getConditionNodes();
        for (int i = 0; i < branches.size(); i++) {
            SimpleFlowNodeVO branch = branches.get(i);
            SimpleFlowNodeVO child = branch.getChildNode();
            String branchEndId;
            if (child != null) {
                // 分支首元素不自建入线，由下面的分支线（可带条件）连接
                FlowElement first = convertNode(child, splitId, false);
                branchEndId = findBranchTail(child);
                process.addFlowElement(flow("flow_" + splitId + "_" + i, splitId, first.getId(),
                        parallel ? null : buildConditionExpression(branch.getConditionSetting()),
                        parallel ? null : defaultBranch(branch.getConditionSetting(), splitId)));
            }
            else {
                branchEndId = joinId;
                process.addFlowElement(flow("flow_" + splitId + "_" + i, splitId, joinId,
                        parallel ? null : buildConditionExpression(branch.getConditionSetting()),
                        parallel ? null : defaultBranch(branch.getConditionSetting(), splitId)));
            }
            if (!parallel && child != null) {
                // 分支子链尾 -> 汇聚网关
                if (!branchEndId.equals(joinId)) {
                    process.addFlowElement(flow("flow_join_" + node.getId() + "_" + i, branchEndId, joinId));
                }
            }
        }

        FlowElement join = parallel ? new ParallelGateway() : new ExclusiveGateway();
        join.setId(joinId);
        join.setName(node.getName() + "汇聚");
        process.addFlowElement(join);
        return join;
    }

    /** 条件分支：defaultFlow=true 的分支不写条件表达式，改挂在网关 defaultFlow 属性上 */
    private String defaultBranch(SimpleFlowNodeVO.ConditionSettingVO condition, String splitId) {
        if (condition != null && Boolean.TRUE.equals(condition.getDefaultFlow())) {
            return splitId;
        }
        return null;
    }

    /** 找分支子链尾元素 id：沿树走到底；若尾巴是嵌套分支，返回其汇聚网关 */
    private String findBranchTail(SimpleFlowNodeVO chainStart) {
        SimpleFlowNodeVO cur = chainStart;
        while (true) {
            Integer type = cur.getType();
            boolean isBranch = FlowNodeType.CONDITION_BRANCH_NODE.getType().equals(type)
                    || FlowNodeType.PARALLEL_BRANCH_NODE.getType().equals(type);
            if (isBranch) {
                return cur.getId() + "_join";
            }
            SimpleFlowNodeVO child = cur.getChildNode();
            if (child == null || FlowNodeType.END_EVENT_NODE.getType().equals(child.getType())) {
                return cur.getId();
            }
            cur = child;
        }
    }

    // ==================== 工具 ====================

    private SequenceFlow flow(String id, String source, String target) {
        return flow(id, source, target, null, null);
    }

    private SequenceFlow flow(String id, String source, String target, String conditionExpression, String defaultFor) {
        SequenceFlow sf = new SequenceFlow();
        sf.setId(id);
        sf.setSourceRef(source);
        sf.setTargetRef(target);
        if (conditionExpression != null) {
            sf.setConditionExpression(conditionExpression);
        }
        if (defaultFor != null) {
            FlowElement gateway = process.getFlowElement(defaultFor);
            if (gateway instanceof ExclusiveGateway) {
                ((ExclusiveGateway) gateway).setDefaultFlow(id);
            }
        }
        return sf;
    }

    private ExtensionElement confElement() {
        ExtensionElement ext = new ExtensionElement();
        ext.setName(EXT_CANDIDATE_CONF);
        ext.setNamespace(FLOWABLE_EXTENSIONS_NAMESPACE);
        ext.setNamespacePrefix(FLOWABLE_EXTENSIONS_PREFIX);
        return ext;
    }

    private void putAttr(ExtensionElement ext, String name, Object value) {
        if (value == null) {
            return;
        }
        ExtensionAttribute attr = new ExtensionAttribute(name);
        attr.setNamespace(FLOWABLE_EXTENSIONS_NAMESPACE);
        attr.setNamespacePrefix(FLOWABLE_EXTENSIONS_PREFIX);
        attr.setValue(String.valueOf(value));
        ext.getAttributes().put(name, new ArrayList<>(List.of(attr)));
    }

    private String joinIds(List<Long> ids) {
        if (ids == null || ids.isEmpty()) {
            return null;
        }
        StringBuilder sb = new StringBuilder();
        for (Long id : ids) {
            if (sb.length() > 0) {
                sb.append(',');
            }
            sb.append(id);
        }
        return sb.toString();
    }

    /** 条件设置 -> Flowable EL；规则与表达式两种形态 */
    public static String buildConditionExpression(SimpleFlowNodeVO.ConditionSettingVO condition) {
        if (condition == null) {
            return "${true}";
        }
        if (condition.getConditionType() != null && condition.getConditionType() == 1
                && condition.getConditionExpression() != null && !condition.getConditionExpression().isEmpty()) {
            return "${" + stripEl(condition.getConditionExpression()) + "}";
        }
        SimpleFlowNodeVO.ConditionGroupVO group = condition.getConditionGroups();
        if (group == null || group.getConditions() == null || group.getConditions().isEmpty()) {
            return "${true}";
        }
        List<String> parts = new ArrayList<>();
        for (SimpleFlowNodeVO.ConditionVO item : group.getConditions()) {
            String expr = joinRules(item);
            if (expr != null && !expr.isEmpty()) {
                parts.add(expr);
            }
        }
        return parts.isEmpty() ? "${true}" : "${" + String.join(" || ", parts) + "}";
    }

    private static String joinRules(SimpleFlowNodeVO.ConditionVO condition) {
        if (condition == null || condition.getRules() == null || condition.getRules().isEmpty()) {
            return null;
        }
        boolean and = condition.getAnd() == null || condition.getAnd();
        List<String> ruleExprs = new ArrayList<>();
        for (SimpleFlowNodeVO.ConditionRuleVO rule : condition.getRules()) {
            String expr = ruleToExpression(rule);
            if (expr != null) {
                ruleExprs.add(expr);
            }
        }
        if (ruleExprs.isEmpty()) {
            return null;
        }
        return "(" + String.join(and ? " && " : " || ", ruleExprs) + ")";
    }

    private static String ruleToExpression(SimpleFlowNodeVO.ConditionRuleVO rule) {
        if (rule == null || rule.getLeftSide() == null || rule.getOpCode() == null) {
            return null;
        }
        String left = rule.getLeftSide();
        String right = rule.getRightSide() == null ? "" : rule.getRightSide();
        String rightLiteral = "'" + right.replace("'", "\\'") + "'";
        return switch (rule.getOpCode()) {
            case "!=" -> left + " != " + rightLiteral;
            case ">" -> left + " > " + numericOrLiteral(right);
            case ">=" -> left + " >= " + numericOrLiteral(right);
            case "<" -> left + " < " + numericOrLiteral(right);
            case "<=" -> left + " <= " + numericOrLiteral(right);
            case "contain" -> "(" + left + " != null && " + left + ".toString().contains(" + rightLiteral + "))";
            case "!contain" -> "(" + left + " == null || !" + left + ".toString().contains(" + rightLiteral + "))";
            default -> left + " == " + rightLiteral;
        };
    }

    private static String numericOrLiteral(String value) {
        try {
            Double.parseDouble(value);
            return value;
        }
        catch (NumberFormatException e) {
            return "'" + value.replace("'", "\\'") + "'";
        }
    }

    private static String stripEl(String expression) {
        String expr = expression.trim();
        if (expr.startsWith("${") && expr.endsWith("}")) {
            expr = expr.substring(2, expr.length() - 1);
        }
        return expr;
    }

}
