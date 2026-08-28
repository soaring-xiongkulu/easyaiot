package com.basiclab.iot.flow.enums;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * 审批相关枚举合集（与前端 consts.ts 完全一致，字段按需裁剪）
 */
public final class FlowEnums {

    private FlowEnums() {
    }

    /** 多人审批方式 */
    @Getter
    @AllArgsConstructor
    public enum ApproveMethod {
        /** 随机挑选一人 */
        RANDOM(1),
        /** 会签（按通过比例） */
        BY_RATIO(2),
        /** 或签（一人通过即可） */
        ANY_OF(3),
        /** 依次审批 */
        SEQUENTIAL(4);

        private final Integer method;
    }

    /** 审批类型 */
    @Getter
    @AllArgsConstructor
    public enum ApproveType {
        USER(1),
        AUTO_APPROVE(2),
        AUTO_REJECT(3);

        private final Integer type;
    }

    /** 拒绝处理类型 */
    @Getter
    @AllArgsConstructor
    public enum RejectHandlerType {
        FINISH_PROCESS(1),
        RETURN_USER_TASK(2);

        private final Integer type;
    }

    /** 超时处理类型 */
    @Getter
    @AllArgsConstructor
    public enum TimeoutHandlerType {
        REMINDER(1),
        APPROVE(2),
        REJECT(3);

        private final Integer type;
    }

    /** 审批人为空处理类型 */
    @Getter
    @AllArgsConstructor
    public enum AssignEmptyHandlerType {
        APPROVE(1),
        REJECT(2),
        ASSIGN_USER(3),
        ASSIGN_ADMIN(4);

        private final Integer type;
    }

    /** 审批人与发起人相同时的处理类型 */
    @Getter
    @AllArgsConstructor
    public enum AssignStartUserHandlerType {
        START_USER_AUDIT(1),
        SKIP(2),
        ASSIGN_DEPT_LEADER(3);

        private final Integer type;
    }

    /** 条件配置类型 */
    @Getter
    @AllArgsConstructor
    public enum ConditionType {
        EXPRESSION(1),
        RULE(2);

        private final Integer type;
    }

    /** 流程实例状态（对齐前端 ProcessInstanceStatus） */
    @Getter
    @AllArgsConstructor
    public enum ProcessInstanceStatus {
        RUNNING(1),
        APPROVE(2),
        REJECT(3),
        CANCEL(4);

        private final Integer status;
    }

    /** 流程实例相关流程变量名 */
    public static final String PROCESS_STATUS_VAR = "PROCESS_STATUS";
    public static final String PROCESS_REASON_VAR = "PROCESS_REASON";
    public static final String PROCESS_START_USER_VAR = "PROCESS_START_USER_ID";

}
