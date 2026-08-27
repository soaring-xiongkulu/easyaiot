package com.basiclab.iot.device.enums.ota;

import com.basiclab.iot.common.exception.Status;
import lombok.Getter;

/**
 * 升级包类型（四类包统一管理）
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public enum DmPackageType implements Status {

    SOFTWARE(0, "软件包"),
    FIRMWARE(1, "固件包"),
    APP(2, "APP包"),
    PC(3, "PC包");

    @Getter
    private final Integer code;
    @Getter
    private final String msg;

    DmPackageType(int code, String msg) {
        this.code = code;
        this.msg = msg;
    }

    public static DmPackageType of(Integer code) {
        if (code == null) {
            return null;
        }
        for (DmPackageType type : values()) {
            if (type.code.equals(code)) {
                return type;
            }
        }
        return null;
    }

    public static boolean isValid(Integer code) {
        return of(code) != null;
    }
}
