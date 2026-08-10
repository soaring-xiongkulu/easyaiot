package com.basiclab.iot.video.support;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.util.ArrayList;
import java.util.List;

public final class JsonFields {

    private static final ObjectMapper MAPPER = new ObjectMapper();

    private JsonFields() {
    }

    public static List<Object> parseJsonList(String raw) {
        if (raw == null || raw.isBlank()) {
            return new ArrayList<>();
        }
        try {
            List<Object> parsed = MAPPER.readValue(raw, new TypeReference<>() {});
            return parsed != null ? parsed : new ArrayList<>();
        } catch (Exception ignored) {
            return new ArrayList<>();
        }
    }

    public static Object parseJsonObject(String raw) {
        if (raw == null || raw.isBlank()) {
            return null;
        }
        try {
            return MAPPER.readValue(raw, Object.class);
        } catch (Exception ignored) {
            return null;
        }
    }
}
