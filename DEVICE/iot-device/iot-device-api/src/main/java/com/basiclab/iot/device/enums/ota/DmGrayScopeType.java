package com.basiclab.iot.device.enums.ota;

import com.basiclab.iot.common.exception.Status;
import lombok.Getter;

/**
 * 灰度范围类型
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public enum DmGrayScopeType implements Status {

    DEVICE(1, "设备"),
    PRODUCT(2, "产品");

    @Getter
    private final Integer code;
    @Getter
    private final String msg;

    DmGrayScopeType(int code, String msg) {
        this.code = code;
        this.msg = msg;
    }

    public static DmGrayScopeType of(Integer code) {
        if (code == null) {
            return null;
        }
        for (DmGrayScopeType type : values()) {
            if (type.code.equals(code)) {
                return type;
            }
        }
        return null;
    }
}
