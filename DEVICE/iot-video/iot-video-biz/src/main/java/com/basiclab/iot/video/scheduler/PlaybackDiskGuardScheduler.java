package com.basiclab.iot.video.scheduler;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.service.ops.PlaybackDiskGuardService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.core.annotation.Order;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

/**
 * SRS playback disk guard aligned with Python {@code playback_disk_guard} APScheduler job
 * ({@code PLAYBACK_GUARD_INTERVAL_MINUTES}, default 10 min) plus startup first run.
 */
@Slf4j
@Component
@Order(51)
@RequiredArgsConstructor
@ConditionalOnProperty(prefix = "video", name = "skip-background-tasks", havingValue = "false", matchIfMissing = true)
public class PlaybackDiskGuardScheduler {

    private final PlaybackDiskGuardService playbackDiskGuardService;
    private final VideoProperties videoProperties;

    @Scheduled(fixedDelayString = "${video.playback-disk-guard.interval-ms:600000}")
    public void scheduledGuard() {
        if (!videoProperties.getPlaybackDiskGuard().isEnabled()) {
            return;
        }
        playbackDiskGuardService.runGuard();
    }

    @EventListener(ApplicationReadyEvent.class)
    public void guardOnStartup() {
        if (videoProperties.isSkipBackgroundTasks() || !videoProperties.getPlaybackDiskGuard().isEnabled()) {
            return;
        }
        try {
            playbackDiskGuardService.runGuard();
            log.info("SRS回放磁盘守护已执行启动时首次清理");
        } catch (Exception e) {
            log.warn("SRS回放磁盘守护启动清理失败: {}", e.getMessage(), e);
        }
    }
}
