package com.basiclab.iot.video.scheduler;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.service.camera.NvrLinkRepairService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;

/**
 * Boot NVR channel link repair — mirrors Python {@code _init_all_cameras} / {@code repair_nvr_channel_links}.
 */
@Slf4j
@Component
@Order(6)
@RequiredArgsConstructor
@ConditionalOnProperty(prefix = "video", name = "skip-background-tasks", havingValue = "false", matchIfMissing = true)
public class NvrRepairBootScheduler {

    private final NvrLinkRepairService nvrLinkRepairService;
    private final VideoProperties videoProperties;

    @EventListener(ApplicationReadyEvent.class)
    public void repairOnStartup() {
        if (videoProperties.isSkipBackgroundTasks()) {
            return;
        }
        try {
            int fixed = nvrLinkRepairService.repairNvrChannelLinks();
            log.info("NVR 通道关联修复完成: fixed={}", fixed);
        } catch (Exception ex) {
            log.warn("NVR 通道关联修复失败: {}", ex.getMessage());
        }
    }
}
