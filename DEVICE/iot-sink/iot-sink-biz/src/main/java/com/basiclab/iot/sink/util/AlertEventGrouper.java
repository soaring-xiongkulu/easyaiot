package com.basiclab.iot.sink.util;

import org.springframework.util.StringUtils;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

/**
 * 多模型告警按模型和类别拆分工具。
 */
public final class AlertEventGrouper {

    private AlertEventGrouper() {
    }

    /**
     * 按模型ID和归一化类别拆分检测结果，保持首次出现顺序。
     */
    public static Map<String, List<Map<String, Object>>> groupDetections(
            List<Map<String, Object>> detections) {
        Map<String, List<Map<String, Object>>> groups = new LinkedHashMap<>();
        if (detections == null) {
            return groups;
        }
        for (Map<String, Object> detection : detections) {
            if (detection == null) {
                continue;
            }
            Object modelId = detection.get("model_id") != null
                    ? detection.get("model_id") : detection.get("modelId");
            String modelIdentity = modelId != null && StringUtils.hasText(String.valueOf(modelId))
                    ? String.valueOf(modelId).trim() : "unknown";
            Object rawClassName = detection.get("class_name") != null
                    ? detection.get("class_name") : detection.get("className");
            String classIdentity = normalizeClassName(rawClassName);
            String eventIdentity = modelIdentity + ":" + classIdentity;
            groups.computeIfAbsent(eventIdentity, key -> new ArrayList<>()).add(detection);
        }
        return groups;
    }

    /**
     * 汇总单个事件分组中的有效模型ID。
     */
    public static List<Integer> collectModelIds(List<Map<String, Object>> detections) {
        Set<Integer> modelIds = new LinkedHashSet<>();
        if (detections != null) {
            for (Map<String, Object> detection : detections) {
                if (detection == null) {
                    continue;
                }
                Object value = detection.get("model_id") != null
                        ? detection.get("model_id") : detection.get("modelId");
                if (value == null || !StringUtils.hasText(String.valueOf(value))) {
                    continue;
                }
                try {
                    modelIds.add(Integer.valueOf(String.valueOf(value).trim()));
                } catch (NumberFormatException ignored) {
                    // 非数据库模型标识不进入所有权校验列表。
                }
            }
        }
        List<Integer> result = new ArrayList<>(modelIds);
        result.sort(Comparator.naturalOrder());
        return result;
    }

    private static String normalizeClassName(Object value) {
        String normalized = value == null ? "" : String.valueOf(value).trim().toLowerCase(Locale.ROOT);
        normalized = normalized.replace('-', '_').replace(' ', '_');
        return StringUtils.hasText(normalized) ? normalized : "unknown";
    }
}
