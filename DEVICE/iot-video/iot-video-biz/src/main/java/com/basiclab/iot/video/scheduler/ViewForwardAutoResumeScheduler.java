package com.basiclab.iot.video.scheduler;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.service.ViewForwardAutoResumeService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Component;

/**
 * One-shot view-forward resume on startup, aligned with Python {@code auto_start_streaming()}.
 */
@Slf4j
@Component
@RequiredArgsConstructor
@ConditionalOnProperty(prefix = "video", name = "skip-background-tasks", havingValue = "false", matchIfMissing = true)
public class ViewForwardAutoResumeScheduler {

    private final ViewForwardAutoResumeService autoResumeService;
    private final VideoProperties videoProperties;

    @EventListener(ApplicationReadyEvent.class)
    public void resumeOnStartup() {
        if (videoProperties.isSkipBackgroundTasks()) {
            return;
        }
        try {
            int resumed = autoResumeService.resumeEnabledDevices();
            if (resumed > 0) {
                log.info("view-forward startup auto-resume: resumed={}", resumed);
            }
        } catch (Exception e) {
            log.error("view-forward startup auto-resume failed: {}", e.getMessage(), e);
        }
    }
}
