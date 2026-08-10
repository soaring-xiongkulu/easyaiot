package com.basiclab.iot.video.service;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.dal.DeviceRepository;
import com.basiclab.iot.video.domain.DeviceRow;
import com.basiclab.iot.video.process.ViewForwardSupervisor;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Locale;

/**
 * Mirrors Python {@code auto_start_streaming()} for devices with {@code enable_forward=true}.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class ViewForwardAutoResumeService {

    private final DeviceRepository deviceRepository;
    private final ViewForwardService viewForwardService;
    private final ViewForwardSupervisor supervisor;
    private final VideoProperties videoProperties;

    public int resumeEnabledDevices() {
        if (videoProperties.isSkipBackgroundTasks()) {
            return 0;
        }
        List<DeviceRow> devices = deviceRepository.findByEnableForwardTrue();
        int resumed = 0;
        for (DeviceRow device : devices) {
            String deviceId = device.getId();
            try {
                if (supervisor.isAlive(deviceId)) {
                    continue;
                }
                String source = device.getSource() != null ? device.getSource().trim() : "";
                if (source.toLowerCase(Locale.ROOT).startsWith("rtmp://")) {
                    log.info("view-forward auto-resume skip rtmp device_id={}", deviceId);
                    continue;
                }
                if (!viewForwardService.isDeviceAvailableForStream(device)) {
                    log.info("view-forward auto-resume skip offline device_id={}", deviceId);
                    continue;
                }
                viewForwardService.startStream(deviceId);
                resumed++;
                log.info("view-forward auto-resume started device_id={}", deviceId);
            } catch (Exception e) {
                log.error("view-forward auto-resume failed device_id={}: {}", deviceId, e.getMessage(), e);
            }
        }
        if (resumed > 0) {
            log.info("view-forward auto-resume complete: resumed={}", resumed);
        }
        return resumed;
    }
}
