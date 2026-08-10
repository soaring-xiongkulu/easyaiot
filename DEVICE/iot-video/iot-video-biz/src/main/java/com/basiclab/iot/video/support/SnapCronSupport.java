package com.basiclab.iot.video.support;

import org.springframework.scheduling.support.CronExpression;

import java.util.ArrayList;
import java.util.List;

/**
 * Cron normalization for snap tasks — aligned with Python {@code cron_utils.normalize_cron_for_croniter}.
 */
public final class SnapCronSupport {

    private SnapCronSupport() {
    }

    /**
     * Normalize Python/APScheduler cron (5 or 6 fields, Quartz {@code ?}) to Spring 6-field cron.
     */
    public static String normalizeForSpring(String expression) {
        String raw = expression == null ? "" : expression.trim();
        if (raw.isEmpty()) {
            throw new IllegalArgumentException("Cron 表达式不能为空");
        }
        List<String> parts = new ArrayList<>(List.of(raw.split("\\s+")));
        if (parts.size() == 7) {
            parts = parts.subList(0, 6);
        }
        if (parts.size() == 5) {
            parts.add(0, "0");
        }
        if (parts.size() != 6) {
            throw new IllegalArgumentException("无效的 cron 表达式: " + expression);
        }
        List<String> normalized = new ArrayList<>(6);
        for (int i = 0; i < 6; i++) {
            String part = parts.get(i);
            if ("?".equals(part)) {
                normalized.add("*");
            } else if (i == 4 && parts.size() >= 6 && parts.get(5).equals("?") && part.startsWith("*/")) {
                // Quartz 6-field with wildcard week: keep day-of-month as given
                normalized.add(part);
            } else {
                normalized.add(part);
            }
        }
        String springCron = String.join(" ", normalized);
        if (!CronExpression.isValidExpression(springCron)) {
            throw new IllegalArgumentException("无效的 cron 表达式: " + expression);
        }
        return springCron;
    }
}
