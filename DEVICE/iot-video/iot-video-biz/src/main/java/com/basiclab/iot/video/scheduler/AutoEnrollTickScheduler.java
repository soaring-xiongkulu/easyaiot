package com.basiclab.iot.video.scheduler;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.service.autoenroll.AutoEnrollTickService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

/**
 * Mirrors Python {@code _ensure_scheduler_job} interval tick (5s) for face/plate auto-enroll.
 */
@Slf4j
@Component
@RequiredArgsConstructor
@ConditionalOnProperty(prefix = "video", name = "skip-background-tasks", havingValue = "false", matchIfMissing = true)
public class AutoEnrollTickScheduler {

    private final AutoEnrollTickService autoEnrollTickService;
    private final VideoProperties videoProperties;

    @Scheduled(fixedDelayString = "${video.auto-enroll.tick-interval-ms:5000}")
    public void tickAutoEnrollTasks() {
        if (videoProperties.isSkipBackgroundTasks()) {
            return;
        }
        autoEnrollTickService.runTick();
    }
}
