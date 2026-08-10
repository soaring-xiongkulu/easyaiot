package com.basiclab.iot.video.support;

import java.sql.ResultSet;
import java.sql.SQLException;

public final class JdbcValues {

    private JdbcValues() {
    }

    public static Integer getInteger(ResultSet rs, String column) throws SQLException {
        Object value = rs.getObject(column);
        if (value == null || rs.wasNull()) {
            return null;
        }
        if (value instanceof Number number) {
            return number.intValue();
        }
        return Integer.parseInt(String.valueOf(value));
    }

    public static Long getLong(ResultSet rs, String column) throws SQLException {
        Object value = rs.getObject(column);
        if (value == null || rs.wasNull()) {
            return null;
        }
        if (value instanceof Number number) {
            return number.longValue();
        }
        return Long.parseLong(String.valueOf(value));
    }

    public static Float getFloat(ResultSet rs, String column) throws SQLException {
        Object value = rs.getObject(column);
        if (value == null || rs.wasNull()) {
            return null;
        }
        if (value instanceof Number number) {
            return number.floatValue();
        }
        return Float.parseFloat(String.valueOf(value));
    }

    public static Double getDouble(ResultSet rs, String column) throws SQLException {
        Object value = rs.getObject(column);
        if (value == null || rs.wasNull()) {
            return null;
        }
        if (value instanceof Number number) {
            return number.doubleValue();
        }
        return Double.parseDouble(String.valueOf(value));
    }

    public static Boolean getBoolean(ResultSet rs, String column) throws SQLException {
        Object value = rs.getObject(column);
        if (value == null || rs.wasNull()) {
            return null;
        }
        if (value instanceof Boolean bool) {
            return bool;
        }
        return Boolean.parseBoolean(String.valueOf(value));
    }
}
