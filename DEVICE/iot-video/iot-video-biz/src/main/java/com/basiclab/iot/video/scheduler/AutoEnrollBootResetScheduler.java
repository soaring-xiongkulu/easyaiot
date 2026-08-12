package com.basiclab.iot.video.scheduler;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.dal.AlgorithmTaskRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;

/**
 * Mirrors Python boot reset of stale auto-enroll running flags ({@code run.py} L1448–1454).
 */
@Slf4j
@Component
@Order(5)
@RequiredArgsConstructor
@ConditionalOnProperty(prefix = "video", name = "skip-background-tasks", havingValue = "false", matchIfMissing = true)
public class AutoEnrollBootResetScheduler {

    private final AlgorithmTaskRepository taskRepository;
    private final VideoProperties videoProperties;

    @EventListener(ApplicationReadyEvent.class)
    public void resetStaleAutoEnrollTasks() {
        if (videoProperties.isSkipBackgroundTasks()) {
            return;
        }
        int reset = taskRepository.resetAllAutoEnrollRunning();
        if (reset > 0) {
            log.info("已重置遗留自动录入任务 is_running=false: count={}", reset);
        } else {
            log.info("自动录入 boot reset 完成: count=0");
        }
    }
}
