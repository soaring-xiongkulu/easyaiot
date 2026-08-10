package com.basiclab.iot.video.scheduler;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.service.ops.RecordSpaceCleanupService;
import com.basiclab.iot.video.service.ops.SnapSpaceCleanupService;
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
 * Snap/record space cleanup aligned with Python {@code auto_cleanup_snap_spaces} /
 * {@code auto_cleanup_record_spaces} (30 min + startup boot cleanup).
 */
@Slf4j
@Component
@Order(50)
@RequiredArgsConstructor
@ConditionalOnProperty(prefix = "video", name = "skip-background-tasks", havingValue = "false", matchIfMissing = true)
public class SpaceCleanupScheduler {

    private final SnapSpaceCleanupService snapSpaceCleanupService;
    private final RecordSpaceCleanupService recordSpaceCleanupService;
    private final VideoProperties videoProperties;

    @Scheduled(fixedDelayString = "${video.space-cleanup.interval-ms:1800000}")
    public void scheduledCleanup() {
        if (!videoProperties.getSpaceCleanup().isEnabled()) {
            return;
        }
        runCleanup("scheduled");
    }

    @EventListener(ApplicationReadyEvent.class)
    public void cleanupOnStartup() {
        if (videoProperties.isSkipBackgroundTasks() || !videoProperties.getSpaceCleanup().isEnabled()) {
            return;
        }
        runCleanup("startup");
    }

    private void runCleanup(String phase) {
        try {
            Map<String, Object> snapStats = snapSpaceCleanupService.cleanupAllSpaces();
            log.info("{} 抓拍空间清理完成: {}", phase, snapStats);
        } catch (Exception e) {
            log.error("{} 抓拍空间清理失败: {}", phase, e.getMessage(), e);
        }
        try {
            Map<String, Object> recordStats = recordSpaceCleanupService.cleanupAllSpaces();
            log.info("{} 录像空间清理完成: {}", phase, recordStats);
        } catch (Exception e) {
            log.error("{} 录像空间清理失败: {}", phase, e.getMessage(), e);
        }
    }
}
