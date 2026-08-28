package com.basiclab.iot.flow.enums;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * Simple 设计器节点类型（与前端 simple-process-design/consts.ts 的 NodeType 数值对齐）
 */
@AllArgsConstructor
@Getter
public enum FlowNodeType {

    /** 结束节点 */
    END_EVENT_NODE(1, "结束"),
    /** 发起人节点 */
    START_USER_NODE(10, "发起人"),
    /** 审批人节点 */
    USER_TASK_NODE(11, "审批人"),
    /** 抄送人节点 */
    COPY_TASK_NODE(12, "抄送人"),
    /** 延迟器节点 */
    DELAY_TIMER_NODE(14, "延迟器"),
    /** 条件分支节点（分支内的条件，type=50 的子节点承载条件表达式） */
    CONDITION_NODE(50, "条件"),
    /** 条件分支（排他网关） */
    CONDITION_BRANCH_NODE(51, "条件分支"),
    /** 并行分支（并行网关） */
    PARALLEL_BRANCH_NODE(52, "并行分支");

    private final Integer type;
    private final String name;

}
