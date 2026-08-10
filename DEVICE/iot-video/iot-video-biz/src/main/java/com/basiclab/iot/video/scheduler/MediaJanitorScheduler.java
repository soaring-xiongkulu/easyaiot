package com.basiclab.iot.video.scheduler;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.service.ops.MediaJanitorService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

/**
 * Media janitor aligned with Python {@code media_janitor} APScheduler job
 * ({@code JANITOR_INTERVAL_SECONDS}, default 60s).
 */
@Slf4j
@Component
@RequiredArgsConstructor
@ConditionalOnProperty(prefix = "video", name = "skip-background-tasks", havingValue = "false", matchIfMissing = true)
public class MediaJanitorScheduler {

    private final MediaJanitorService mediaJanitorService;
    private final VideoProperties videoProperties;

    @Scheduled(fixedDelayString = "${video.media-janitor.interval-ms:60000}")
    public void scheduledJanitor() {
        if (!videoProperties.getMediaJanitor().isEnabled()) {
            return;
        }
        mediaJanitorService.runCycle();
    }
}
