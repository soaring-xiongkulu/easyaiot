package com.basiclab.iot.device.enums.ota;

import com.basiclab.iot.common.exception.Status;
import lombok.Getter;

/**
 * 升级包状态（统一状态机，四类包共用）
 * <p>
 * 未验证 → 测试中 → 已发布 → 已撤回 → 未验证（重新编辑）
 * 测试不通过：测试中 → 未验证
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @created 2025-05-28
 */
public enum DmPackageStatus implements Status {
    UNVERIFIED(0, "未验证"),
    TESTING(1, "测试中"),
    PUBLISHED(2, "已发布"),
    WAIT_PUBLISHED(3, "待发布"),
    WITHDRAWN(4, "已撤回");

    @Getter
    private final Integer code;
    @Getter
    private final String msg;

    DmPackageStatus(int code, String msg) {
        this.code = code;
        this.msg = msg;
    }

    public static DmPackageStatus of(Integer code) {
        if (code == null) {
            return null;
        }
        for (DmPackageStatus status : values()) {
            if (status.code.equals(code)) {
                return status;
            }
        }
        return null;
    }
}
