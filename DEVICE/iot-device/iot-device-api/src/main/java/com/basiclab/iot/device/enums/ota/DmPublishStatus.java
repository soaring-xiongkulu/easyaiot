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
public enum DmPublishStatus implements Status {
    REVOKED(0,"已撤消"),
    PUBLISHED(1,"已发布"),
    AWAIT_PUBLISH(2,"待发布"),
    ;
    @Getter
    private Integer code;
    @Getter
    private String msg;

    DmPublishStatus(int code, String msg) {
        this.code = code;
        this.msg = msg;
    }
}
