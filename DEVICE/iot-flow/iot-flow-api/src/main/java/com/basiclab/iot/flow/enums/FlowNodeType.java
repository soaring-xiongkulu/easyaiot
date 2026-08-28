package com.basiclab.iot.flow.enums;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * Simple 流程节点类型（与前端 simple-process-design consts.ts 的 NodeType 完全一致）
 */
@Getter
@AllArgsConstructor
public enum FlowNodeType {

    END_EVENT_NODE(1, "结束"),
    START_USER_NODE(10, "发起人"),
    USER_TASK_NODE(11, "审批"),
    COPY_TASK_NODE(12, "抄送"),
    DELAY_TIMER_NODE(14, "延迟器"),
    CONDITION_NODE(50, "条件"),
    CONDITION_BRANCH_NODE(51, "条件分支"),
    PARALLEL_BRANCH_NODE(52, "并行分支");

    private final Integer type;
    private final String name;

}
