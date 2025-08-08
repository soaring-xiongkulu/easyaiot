package com.basiclab.iot.device.enums.device;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * 字符类型
 *
 * @author EasyAIoT
 * @date 2025-8-7
 */
@Getter
@AllArgsConstructor
public enum FieldTypeEnum {

    INT("int"),
    STRING("string"),
    DECIMAL("decimal"),
    TIMESTAMP("timestamp"),
    BOOL("bool");
    private String symbol;

    public static FieldTypeEnum getBySymbol(String symbol) {
        for (FieldTypeEnum fieldTypeEnum : values()) {
            if (fieldTypeEnum.getSymbol().equals(symbol)) {
                //获取指定的枚举
                return fieldTypeEnum;
            }
        }
        return null;
    }

}
