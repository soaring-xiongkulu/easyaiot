package com.basiclab.iot.video.scheduler;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.service.StreamForwardHealthService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.core.annotation.Order;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.util.Map;

/**
 * Periodic stream_forward cluster health migration aligned with Python APScheduler job
 * ({@code STREAM_FORWARD_HEALTH_INTERVAL_SECONDS}, default 60s) plus one-shot on startup.
 */
@Slf4j
@Component
@Order(45)
@RequiredArgsConstructor
@ConditionalOnProperty(prefix = "video", name = "skip-background-tasks", havingValue = "false", matchIfMissing = true)
public class StreamForwardHealthScheduler {

    private final StreamForwardHealthService healthService;
    private final VideoProperties videoProperties;

    @Scheduled(fixedDelayString = "${video.stream-forward-health.interval-ms:60000}")
    public void scheduledHealthCycle() {
        if (!healthService.isHealthMonitorEnabled()) {
            return;
        }
        healthService.runHealthCycle();
    }

    @EventListener(ApplicationReadyEvent.class)
    public void healthCycleOnStartup() {
        if (videoProperties.isSkipBackgroundTasks() || !healthService.isHealthMonitorEnabled()) {
            return;
        }
        try {
            Map<String, Integer> stats = healthService.runHealthCycle();
            int migrated = stats.getOrDefault("migrated", 0);
            if (migrated > 0) {
                log.info("推流转发启动健康恢复: migrated={}", migrated);
            }
        } catch (Exception e) {
            log.error("推流转发启动健康恢复失败: {}", e.getMessage(), e);
        }
    }
}
