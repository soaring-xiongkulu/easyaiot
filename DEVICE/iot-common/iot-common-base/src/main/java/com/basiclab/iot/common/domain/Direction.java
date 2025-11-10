package com.basiclab.iot.common.domain;

import java.util.EnumSet;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @desc
 * @created 2025-05-27
 */
public enum Direction {
    ASC("ASC", "升序"),
    DESC("DESC", "降序");

    private String code;
    private String desc;

    Direction(String code, String desc) {
        this.code = code;
        this.desc = desc;
    }

    private static final Map<String, Direction> codeLookup = new ConcurrentHashMap<>(2);

    static {
        for (Direction direction : EnumSet.allOf(Direction.class)) {
            codeLookup.put(direction.code, direction);
        }
    }

    public boolean isAscending() {
        return this.equals(ASC);
    }

    public boolean isDescending() {
        return this.equals(DESC);
    }

    public static Direction fromString(String value) {

        try {
            return Direction.valueOf(value.toUpperCase(Locale.US));
        } catch (Exception e) {
            throw new IllegalArgumentException(String.format(
                    "Invalid value '%s' for orders given! Has to be either 'desc' or 'asc' (case insensitive).", value), e);
        }
    }

    public static Direction fromStringOrNull(String value) {

        try {
            return fromString(value);
        } catch (IllegalArgumentException e) {
            return null;
        }
    }

    public String getCode() {
        return code;
    }

    public String getDesc() {
        return desc;
    }

    public static Direction fromCode(String code) {
        return codeLookup.get(code);
    }

}
