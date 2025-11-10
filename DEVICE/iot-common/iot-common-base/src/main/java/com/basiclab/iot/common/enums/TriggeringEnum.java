package com.basiclab.iot.common.enums;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * 触发机制
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @date 2025-8-7
 */
@Getter
@AllArgsConstructor
public enum TriggeringEnum {
    // 触发机制 0:全部，1:任意一个
    ALL(0),
    ANY(1);

    private Integer symbol;

    public static TriggeringEnum getBySymbol(Integer symbol) {
        for (TriggeringEnum triggeringEnum : values()) {
            if (triggeringEnum.getSymbol().equals(symbol)) {
                //获取指定的枚举
                return triggeringEnum;
            }
        }
        return null;
    }
}
