package com.basiclab.iot.device.constant;

import lombok.Getter;
/**
 * @author EasyAIoT
 * @desc
 * @created 2025-06-25
 */
public enum UploadLogType {
    UPLOAD("1","上传日志"),
    UPLOAD_SUCCESS("2","日志上报存储成功"),
    UPLoAD_FAILED("3","日志上报失败"),
    ;
    @Getter
    private String code;
    @Getter
    private String desc;

    UploadLogType(String code, String desc){
        this.code = code;
        this.desc = desc;
    }
}
