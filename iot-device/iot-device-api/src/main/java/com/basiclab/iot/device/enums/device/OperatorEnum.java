package com.basiclab.iot.device.enums.device;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * 比较值
 *
 * @author EasyAIoT
 * @date 2025-8-7
 */
@Getter
@AllArgsConstructor
public enum OperatorEnum {

    eq("=="),
    not("!="),
    gt(">"),
    lt("<"),
    gte(">="),
    lte("<="),
    between("between");

    private String symbol;

    public static OperatorEnum getBySymbol(String symbol) {
        for (OperatorEnum operatorEnum : values()) {
            if (operatorEnum.getSymbol().equals(symbol)) {
                //获取指定的枚举
                return operatorEnum;
            }
        }
        return null;
    }

}
