package com.basiclab.iot.device.enums.ota;

import com.basiclab.iot.common.exception.Status;
import lombok.Getter;

/**
 * @author EasyAIoT
 * @desc
 * @created 2025-05-28
 */
public enum DmDeviceVersionStatus implements Status {
    UNVERIFIED(0, "未验证"),
    VERIFIED(1, "已验证"),
    PUBLISHED(2, "已发布"),
    WAIT_PUBLISHED(3, "待发布"),
    CANCELLED(4, "已撤销");

    @Getter
    private Integer code;
    @Getter
    private String msg;

    DmDeviceVersionStatus(int code, String msg) {
        this.code = code;
        this.msg = msg;
    }
}
