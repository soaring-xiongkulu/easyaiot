package com.basiclab.iot.video.scheduler;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.service.StreamForwardAutoStartService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;

/**
 * One-shot stream-forward auto_start on startup, aligned with Python {@code stream_forward auto_start_all_tasks}.
 */
@Slf4j
@Component
@Order(30)
@RequiredArgsConstructor
@ConditionalOnProperty(prefix = "video", name = "skip-background-tasks", havingValue = "false", matchIfMissing = true)
public class StreamForwardAutoStartScheduler {

    private final StreamForwardAutoStartService autoStartService;
    private final VideoProperties videoProperties;

    @EventListener(ApplicationReadyEvent.class)
    public void autoStartOnStartup() {
        if (videoProperties.isSkipBackgroundTasks()) {
            return;
        }
        try {
            int started = autoStartService.startAllEnabledLocalTasks();
            if (started > 0) {
                log.info("推流转发任务服务自动启动完成: started={}", started);
            }
        } catch (Exception e) {
            log.error("自动启动推流转发任务服务失败: {}", e.getMessage(), e);
        }
    }
}
