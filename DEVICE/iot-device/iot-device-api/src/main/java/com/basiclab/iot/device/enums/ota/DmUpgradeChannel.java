package com.basiclab.iot.device.enums.ota;

import com.basiclab.iot.common.exception.Status;
import lombok.Getter;

/**
 * 升级通道
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public enum DmUpgradeChannel implements Status {

    TEST(1, "测试通道"),
    RELEASE(2, "正式通道");

    @Getter
    private final Integer code;
    @Getter
    private final String msg;

    DmUpgradeChannel(int code, String msg) {
        this.code = code;
        this.msg = msg;
    }

    public static DmUpgradeChannel of(Integer code) {
        if (code == null) {
            return null;
        }
        for (DmUpgradeChannel channel : values()) {
            if (channel.code.equals(code)) {
                return channel;
            }
        }
        return null;
    }
}
