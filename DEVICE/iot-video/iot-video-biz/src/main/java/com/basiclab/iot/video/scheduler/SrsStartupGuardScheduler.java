package com.basiclab.iot.video.scheduler;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.service.ops.SrsStartupGuardService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;

@Slf4j
@Component
@Order(7)
@RequiredArgsConstructor
@ConditionalOnProperty(prefix = "video", name = "skip-background-tasks", havingValue = "false", matchIfMissing = true)
public class SrsStartupGuardScheduler {

    private final SrsStartupGuardService srsStartupGuardService;
    private final VideoProperties videoProperties;

    @EventListener(ApplicationReadyEvent.class)
    public void checkSrsOnStartup() {
        if (videoProperties.isSkipBackgroundTasks()) {
            return;
        }
        try {
            srsStartupGuardService.checkOnStartup();
        } catch (Exception ex) {
            log.warn("SRS 启动自检失败（可忽略）: {}", ex.getMessage());
        }
    }
}
