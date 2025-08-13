package com.basiclab.iot.device.constant;


import com.basiclab.iot.common.exception.Status;

/**
 * @author EasyAIoT
 * @desc
 * @created 2025-06-03
 */
public enum OpsErrorStatus implements Status {

    DR_CONFIG_NOT_EXIST(50001, "Device record config does not exist"),

    SEND_COMMAND_ERROR(50002, "send device upload file command error"),

    PARAMS_ERROR(50003, "device upload file params error"),

    TEMP_FILE_PARSE_ERROR(50003, "The temperature file parsing error"),

    ;
    private int code;
    private String msg;

    OpsErrorStatus(int code, String msg) {
        this.code = code;
        this.msg = msg;
    }

    public Integer getCode() {
        return code;
    }

    public String getMsg() {
        return msg;
    }
}
