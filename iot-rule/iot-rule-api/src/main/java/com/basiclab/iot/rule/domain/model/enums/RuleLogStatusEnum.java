package com.basiclab.iot.rule.domain.model.enums;

/**
 * @author IoT
 * @desc
 * @created 2024-07-30
 */
public enum RuleLogStatusEnum {

    /**
     * 初始状态
     */
    INITIAL("initial"),
    /**
     * 未成功匹配条件
     */
    UNMATCHED_CONDITION("unmatched_condition"),
    /**
     * 成功匹配条件
     */
    MATCHED_CONDITION("matched_condition"),
    /**
     * 执行动作中
     */
    EXECUTING_ACTION("executing_action"),
    /**
     * 执行动作完成
     */
    EXECUTED_ACTION("executed_action"),
    /**
     * 执行动作失败
     */
    EXECUTED_FAIL("executed_fail"),

    ;

    private String code;

    RuleLogStatusEnum(String code) {
        this.code = code;
    }

    public String getCode() {
        return code;
    }

    public void setCode(String code) {
        this.code = code;
    }

}
