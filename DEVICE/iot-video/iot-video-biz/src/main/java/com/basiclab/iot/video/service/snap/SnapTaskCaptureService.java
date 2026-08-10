package com.basiclab.iot.video.service.snap;

import com.basiclab.iot.video.dal.DeviceRepository;
import com.basiclab.iot.video.dal.SnapSpaceRepository;
import com.basiclab.iot.video.domain.DeviceRow;
import com.basiclab.iot.video.exception.VideoBusinessException;
import com.basiclab.iot.video.service.camera.CameraHardwareService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.Map;
import java.util.Optional;

/**
 * Snap task capture pipeline — structural parity with Python {@code capture_image}.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class SnapTaskCaptureService {

    private final DeviceRepository deviceRepository;
    private final SnapSpaceRepository snapSpaceRepository;
    private final CameraHardwareService cameraHardwareService;

    public boolean captureImage(Map<String, Object> task, String deviceId, int spaceId) {
        Optional<DeviceRow> deviceOpt = deviceRepository.findById(deviceId);
        Optional<Map<String, Object>> spaceOpt = snapSpaceRepository.findById(spaceId);
        if (deviceOpt.isEmpty() || spaceOpt.isEmpty()) {
            log.error("任务 {} 关联的设备或空间不存在", task.get("id"));
            return false;
        }
        DeviceRow device = deviceOpt.get();

        int captureType = task.get("capture_type") instanceof Number n ? n.intValue() : 0;
        if (captureType == 0) {
            String source = device.getSource() != null ? device.getSource().trim() : "";
            if (source.isEmpty()) {
                log.error("设备 {} 源地址为空", deviceId);
                return false;
            }
            try {
                cameraHardwareService.captureSnapshot(deviceId);
                return true;
            } catch (VideoBusinessException ex) {
                log.warn("设备 {} RTSP/RTMP 抓拍失败: {}", deviceId, ex.getMessage());
                return false;
            }
        }

        try {
            cameraHardwareService.captureSnapshot(deviceId);
            return true;
        } catch (VideoBusinessException ex) {
            log.warn("设备 {} ONVIF 抓拍失败: {}", deviceId, ex.getMessage());
            return false;
        }
    }
}
