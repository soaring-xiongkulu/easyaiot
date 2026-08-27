package com.basiclab.iot.device.enums.ota;

import com.basiclab.iot.common.exception.Status;
import lombok.Getter;

/**
 * 升级阶段（全链路漏斗，四类包统一）
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public enum DmPackageUpgradePhase implements Status {

    CHECK(0, "检测"),
    CHECK_HIT(1, "命中升级"),
    DOWNLOAD_OK(2, "下载完成"),
    DOWNLOAD_FAIL(3, "下载失败"),
    MD5_FAIL(4, "MD5校验失败"),
    INSTALL_RESULT(5, "安装结果"),
    LAUNCH_OK(6, "启动成功");

    @Getter
    private final Integer code;
    @Getter
    private final String msg;

    DmPackageUpgradePhase(int code, String msg) {
        this.code = code;
        this.msg = msg;
    }

    public static DmPackageUpgradePhase of(Integer code) {
        if (code == null) {
            return null;
        }
        for (DmPackageUpgradePhase phase : values()) {
            if (phase.code.equals(code)) {
                return phase;
            }
        }
        return null;
    }

    public static boolean isValid(Integer code) {
        return of(code) != null;
    }
}
