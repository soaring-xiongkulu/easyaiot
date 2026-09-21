package com.basiclab.iot.visualize.enums;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * 可视化项目类型：大屏 / 组态（FUXA）/ 数字孪生
 */
@Getter
@AllArgsConstructor
public enum VisualizeProjectTypeEnum {

    /** GoView 风格低代码大屏 */
    DASHBOARD("dashboard", "大屏"),
    /** FUXA Web 组态（SCADA/HMI） */
    SCADA("scada", "组态"),
    /** Three.js / glTF 数字孪生运行时 */
    TWIN("twin", "数字孪生");

    private final String type;
    private final String name;

    public static boolean isValid(String type) {
        if (type == null || type.isEmpty()) {
            return false;
        }
        for (VisualizeProjectTypeEnum value : values()) {
            if (value.type.equals(type)) {
                return true;
            }
        }
        return false;
    }

    public static boolean isScada(String type) {
        return SCADA.type.equals(type);
    }

    public static boolean isTwin(String type) {
        return TWIN.type.equals(type);
    }

    public static String normalize(String type) {
        return isValid(type) ? type : DASHBOARD.type;
    }

}
