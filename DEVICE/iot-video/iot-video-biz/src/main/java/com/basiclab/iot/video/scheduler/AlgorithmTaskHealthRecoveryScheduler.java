package com.basiclab.iot.video.scheduler;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.service.AlgorithmTaskHealthRecoveryService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.core.annotation.Order;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

/**
 * Periodic health recovery aligned with Python {@code algorithm_task_health} APScheduler job
 * ({@code ALGORITHM_HEALTH_INTERVAL_SECONDS}, default 60s) plus one-shot recovery on startup.
 */
@Slf4j
@Component
@Order(40)
@RequiredArgsConstructor
@ConditionalOnProperty(prefix = "video", name = "skip-background-tasks", havingValue = "false", matchIfMissing = true)
public class AlgorithmTaskHealthRecoveryScheduler {

    private final AlgorithmTaskHealthRecoveryService recoveryService;
    private final VideoProperties videoProperties;

    @Scheduled(fixedDelayString = "${video.health-monitor.interval-ms:60000}")
    public void scheduledRecovery() {
        if (!videoProperties.getHealthMonitor().isEnabled()) {
            return;
        }
        recoveryService.recoverUnhealthyEnabledLocalTasks();
    }

    @EventListener(ApplicationReadyEvent.class)
    public void recoverOnStartup() {
        if (videoProperties.isSkipBackgroundTasks() || !videoProperties.getHealthMonitor().isEnabled()) {
            return;
        }
        try {
            int recovered = recoveryService.recoverUnhealthyEnabledLocalTasks();
            if (recovered > 0) {
                log.info("算法任务启动恢复: recovered={}", recovered);
            }
        } catch (Exception e) {
            log.error("算法任务启动恢复失败: {}", e.getMessage(), e);
        }
    }
}
