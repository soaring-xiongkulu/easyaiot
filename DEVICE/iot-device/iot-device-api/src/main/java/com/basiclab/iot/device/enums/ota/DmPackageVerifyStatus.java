package com.basiclab.iot.device.enums.ota;

import com.basiclab.iot.common.exception.Status;
import lombok.Getter;

/**
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @desc
 * @created 2025-05-28
 */
public enum DmPackageVerifyStatus implements Status {
    UNVERIFIED(0,"未验证"),
    VERIFICATION_IN_PROGRESS(1,"验证中"),
    VALIDATION_SUCCESSFUL(2,"验证成功"),
    VALIDATION_FAILED(3,"验证失败")
    ;

    @Getter
    private Integer code;
    @Getter
    private String msg;

    DmPackageVerifyStatus(int code, String msg) {
        this.code = code;
        this.msg = msg;
    }
}
