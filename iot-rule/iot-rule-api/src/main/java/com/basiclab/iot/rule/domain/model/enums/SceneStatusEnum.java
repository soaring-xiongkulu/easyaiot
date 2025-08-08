package com.basiclab.iot.rule.domain.model.enums;

/**
 * @author IoT
 * @desc    场景状态
 * @created 2024-07-10
 */
public enum SceneStatusEnum {
    STATE_STOPPED("stopped"),
    STATE_RUNNING("running"),


    ;

    private String code;

    SceneStatusEnum(String code) {
        this.code = code;
    }

    public String getCode() {
        return code;
    }

    public void setCode(String code) {
        this.code = code;
    }
}
