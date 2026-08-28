package com.basiclab.iot.flow.enums;

/**
 * Flow 流程通用常量
 */
public final class FlowEnums {

    /** 流程状态变量：1 审批中 / 2 审批通过 / 3 审批拒绝 / 4 已取消（终态回写 flow_alert_record） */
    public static final String PROCESS_STATUS_VAR = "PROCESS_STATUS";

    /** 流程状态原因变量（拒绝/取消理由，供审批详情展示） */
    public static final String PROCESS_REASON_VAR = "PROCESS_REASON";

    /** 发起人变量（监听器指派候选人、发起人相同审批策略依赖） */
    public static final String PROCESS_START_USER_VAR = "PROCESS_START_USER_ID";

    private FlowEnums() {
    }
}
