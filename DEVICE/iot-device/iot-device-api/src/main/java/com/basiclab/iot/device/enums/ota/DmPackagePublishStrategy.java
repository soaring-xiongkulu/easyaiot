package com.basiclab.iot.device.enums.ota;

import com.basiclab.iot.common.exception.Status;
import lombok.Getter;

/**
 * 发布策略（四类包统一）
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public enum DmPackagePublishStrategy implements Status {

    FULL(0, "全量发布"),
    GRAY(1, "灰度发布");

    @Getter
    private final Integer code;
    @Getter
    private final String msg;

    DmPackagePublishStrategy(int code, String msg) {
        this.code = code;
        this.msg = msg;
    }

    public static DmPackagePublishStrategy of(Integer code) {
        if (code == null) {
            return null;
        }
        for (DmPackagePublishStrategy strategy : values()) {
            if (strategy.code.equals(code)) {
                return strategy;
            }
        }
        return null;
    }
}
