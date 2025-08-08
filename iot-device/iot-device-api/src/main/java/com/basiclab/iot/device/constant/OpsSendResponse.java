package com.basiclab.iot.device.constant;

import lombok.Getter;
/**
 * @author EasyAIoT
 * @desc
 * @created 2025-06-03
 */
public enum OpsSendResponse {

    SUCCESS(0, "成功"),
    PARAMS_ERROR(1, "参数不存在"),
    NULL_ERROR(2, "设备不存在"),
    OFFLINE_ERROR(3, "设备不在线"),
    REPEATED_ERROR(4, "重复拉取"),
    ;

    @Getter
    private Integer code;
    @Getter
    private String desc;

    OpsSendResponse(int code, String desc){
        this.code = code;
        this.desc = desc;
    }
}
