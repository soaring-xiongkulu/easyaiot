package com.basiclab.iot.video.support;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

public final class RequestParams {

    private RequestParams() {
    }

    public static Object first(Map<String, Object> data, String... keys) {
        if (data == null) {
            return null;
        }
        for (String key : keys) {
            if (data.containsKey(key) && data.get(key) != null) {
                return data.get(key);
            }
        }
        return null;
    }

    public static String str(Map<String, Object> data, String... keys) {
        Object value = first(data, keys);
        return value == null ? "" : String.valueOf(value).trim();
    }

    public static String strOrNull(Map<String, Object> data, String... keys) {
        String text = str(data, keys);
        return text.isEmpty() ? null : text;
    }

    public static boolean bool(Map<String, Object> data, String key, boolean defaultValue) {
        Object value = data.get(key);
        if (value == null) {
            return defaultValue;
        }
        if (value instanceof Boolean b) {
            return b;
        }
        String text = String.valueOf(value).trim().toLowerCase();
        if (text.isEmpty()) {
            return defaultValue;
        }
        return "1".equals(text) || "true".equals(text) || "yes".equals(text) || "on".equals(text);
    }

    public static int toInt(Object value, int defaultValue) {
        if (value == null || String.valueOf(value).isBlank()) {
            return defaultValue;
        }
        try {
            return Integer.parseInt(String.valueOf(value));
        } catch (NumberFormatException ex) {
            return defaultValue;
        }
    }

    public static double toDouble(Object value, double defaultValue) {
        if (value == null || String.valueOf(value).isBlank()) {
            return defaultValue;
        }
        try {
            return Double.parseDouble(String.valueOf(value));
        } catch (NumberFormatException ex) {
            return defaultValue;
        }
    }

    @SuppressWarnings("unchecked")
    public static List<Object> list(Map<String, Object> data, String... keys) {
        Object raw = first(data, keys);
        if (raw instanceof List<?> list) {
            return new ArrayList<>(list);
        }
        return new ArrayList<>();
    }

    public static Boolean matchedFilter(String raw) {
        if (raw == null || raw.isBlank()) {
            return null;
        }
        return "1".equals(raw) || "true".equalsIgnoreCase(raw) || "yes".equalsIgnoreCase(raw);
    }
}
