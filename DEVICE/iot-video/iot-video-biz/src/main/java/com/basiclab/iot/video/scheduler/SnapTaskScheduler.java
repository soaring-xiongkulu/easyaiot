package com.basiclab.iot.video.scheduler;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.service.snap.SnapTaskSchedulerService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;

/**
 * Startup hook for snap task cron scheduling — aligned with Python {@code run.py}
 * {@code init_all_tasks()} after app context is ready.
 */
@Slf4j
@Component
@Order(55)
@RequiredArgsConstructor
@ConditionalOnProperty(prefix = "video", name = "skip-background-tasks", havingValue = "false", matchIfMissing = true)
public class SnapTaskScheduler {

    private final SnapTaskSchedulerService schedulerService;
    private final VideoProperties videoProperties;

    @EventListener(ApplicationReadyEvent.class)
    public void initOnStartup() {
        if (videoProperties.isSkipBackgroundTasks() || !videoProperties.getSnapTaskScheduler().isEnabled()) {
            return;
        }
        try {
            int scheduled = schedulerService.initAllTasks();
            if (scheduled > 0) {
                log.info("抓拍任务调度器初始化成功: scheduled={}", scheduled);
            }
        } catch (Exception e) {
            log.error("初始化抓拍任务调度器失败: {}", e.getMessage(), e);
        }
    }
}
