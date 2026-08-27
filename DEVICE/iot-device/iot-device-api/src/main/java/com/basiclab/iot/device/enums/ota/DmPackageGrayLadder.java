package com.basiclab.iot.device.enums.ota;

import com.basiclab.iot.common.exception.Status;
import lombok.Getter;

/**
 * 灰度阶梯（四类包统一，仅升阶，需相邻）
 * <p>
 * 1 设备级 → 2 产品级 → 3 全量
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public enum DmPackageGrayLadder implements Status {

    DEVICE(1, "设备级", DmGrayScopeType.DEVICE),
    PRODUCT(2, "产品级", DmGrayScopeType.PRODUCT),
    FULL(3, "全量", null);

    @Getter
    private final Integer code;
    @Getter
    private final String msg;

    /**
     * 该阶梯对应的灰度范围类型，全量阶梯无范围
     */
    @Getter
    private final DmGrayScopeType scopeType;

    DmPackageGrayLadder(int code, String msg, DmGrayScopeType scopeType) {
        this.code = code;
        this.msg = msg;
        this.scopeType = scopeType;
    }

    public static DmPackageGrayLadder of(Integer code) {
        if (code == null) {
            return null;
        }
        for (DmPackageGrayLadder ladder : values()) {
            if (ladder.code.equals(code)) {
                return ladder;
            }
        }
        return null;
    }

    /**
     * 下一阶梯
     */
    public DmPackageGrayLadder next() {
        for (DmPackageGrayLadder ladder : values()) {
            if (ladder.code == this.code + 1) {
                return ladder;
            }
        }
        return null;
    }

    /**
     * 是否为目标阶梯的相邻下一阶
     */
    public boolean isAdjacentNext(DmPackageGrayLadder target) {
        return target != null && target.code == this.code + 1;
    }
}
