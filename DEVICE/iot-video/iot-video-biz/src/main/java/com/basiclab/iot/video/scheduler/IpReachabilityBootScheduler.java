package com.basiclab.iot.video.scheduler;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.service.camera.IpReachabilityMonitorService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;

@Slf4j
@Component
@Order(8)
@RequiredArgsConstructor
@ConditionalOnProperty(prefix = "video", name = "skip-background-tasks", havingValue = "false", matchIfMissing = true)
public class IpReachabilityBootScheduler {

    private final IpReachabilityMonitorService ipReachabilityMonitorService;
    private final VideoProperties videoProperties;

    @EventListener(ApplicationReadyEvent.class)
    public void startIpMonitor() {
        if (videoProperties.isSkipBackgroundTasks()) {
            return;
        }
        int registered = ipReachabilityMonitorService.registerDevicesOnStartup();
        log.info("IP 在线监控启动: registered={}", registered);
    }
}
