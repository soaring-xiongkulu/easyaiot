package com.basiclab.iot.rule.domain.model.enums;

/**
 * @author EasyAIoT
 * @desc    场景动作类型枚举
 * @created 2025-07-10
 */
public enum ActionEnum {
    /**
     * 设备控制
     */
    TYPE_DEVICE("DEVICE"),
    /**
     * 告警
     */
    TYPE_ALARM("ALARM"),

    ;

    private String code;

    ActionEnum(String code) {
        this.code = code;
    }

    public String getCode() {
        return code;
    }

    public void setCode(String code) {
        this.code = code;
    }
}
