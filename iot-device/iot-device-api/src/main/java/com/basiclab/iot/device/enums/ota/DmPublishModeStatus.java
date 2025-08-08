package com.basiclab.iot.device.enums.ota;

import com.basiclab.iot.common.exception.Status;
import lombok.Getter;

/**
 * @author EasyAIoT
 * @desc
 * @created 2025-05-28
 */
public enum DmPublishModeStatus implements Status {
    PUBLISH_NOW(0,"立即发布"),
    PUBLISH_TIMING(1,"定时发布")
    ;
    @Getter
    private Integer code;
    @Getter
    private String msg;

    DmPublishModeStatus(int code, String desc) {
        this.code = code;
        this.msg = msg;
    }
}
