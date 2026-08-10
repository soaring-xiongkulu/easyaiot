package com.basiclab.iot.video.service.camera;

import com.basiclab.iot.video.dal.DeviceRepository;
import com.basiclab.iot.video.domain.DeviceRow;
import com.basiclab.iot.video.exception.VideoBusinessException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Service
@RequiredArgsConstructor
public class CameraHardwareService {

    private final DeviceRepository deviceRepository;
    private final Map<String, CaptureTaskState> rtspTasks = new ConcurrentHashMap<>();
    private final Map<String, CaptureTaskState> onvifTasks = new ConcurrentHashMap<>();

    public List<Map<String, Object>> discoverDevices() {
        return Collections.emptyList();
    }

    public void refreshDevices() {
        // no-op background refresh in Java candidate
    }

    public List<Map<String, Object>> scanSegment(Map<String, Object> data) {
        String targets = str(data.get("targets"));
        if (targets.isEmpty()) {
            throw new VideoBusinessException(400, "请填写扫描目标（网段 / IP / 范围）");
        }
        return Collections.emptyList();
    }

    public Map<String, Object> scanNvrChannels(Map<String, Object> data) {
        String ip = str(data.get("ip"));
        if (ip.isEmpty()) {
            throw new VideoBusinessException(400, "NVR IP 不能为空");
        }
        Map<String, Object> inv = new LinkedHashMap<>();
        inv.put("channels", List.of());
        inv.put("error", "Java 端暂未集成 NVR 通道枚举");
        return inv;
    }

    public Map<String, Object> ptz(String deviceId, Map<String, Object> data) {
        if (data == null || data.isEmpty()) {
            throw new VideoBusinessException(400, "No data provided");
        }
        DeviceRow device = deviceRepository.findById(deviceId).orElse(null);
        if (device == null) {
            throw new VideoBusinessException(400, "Camera not found");
        }
        throw new VideoBusinessException(500, "Internal server error");
    }

    public Map<String, Object> startRtspCapture(String deviceId, Map<String, Object> data) {
        requireDevice(deviceId);
        if (rtspTasks.containsKey(deviceId) && rtspTasks.get(deviceId).running) {
            throw new VideoBusinessException(400, "该设备的截图任务已在运行");
        }
        rtspTasks.put(deviceId, new CaptureTaskState(true));
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("task_id", Thread.currentThread().getId());
        return result;
    }

    public void stopRtspCapture(String deviceId) {
        CaptureTaskState state = rtspTasks.get(deviceId);
        if (state == null) {
            throw new VideoBusinessException(400, "未找到运行的RTSP截图任务");
        }
        state.running = false;
    }

    public String rtspStatus(String deviceId) {
        CaptureTaskState state = rtspTasks.get(deviceId);
        return state != null && state.running ? "running" : "stopped";
    }

    public Map<String, Object> startOnvifCapture(String deviceId, Map<String, Object> data) {
        requireDevice(deviceId);
        if (onvifTasks.containsKey(deviceId) && onvifTasks.get(deviceId).running) {
            throw new VideoBusinessException(400, "该设备的ONVIF截图任务已在运行");
        }
        onvifTasks.put(deviceId, new CaptureTaskState(true));
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("task_id", Thread.currentThread().getId());
        return result;
    }

    public void stopOnvifCapture(String deviceId) {
        CaptureTaskState state = onvifTasks.get(deviceId);
        if (state == null) {
            throw new VideoBusinessException(400, "未找到运行的ONVIF截图任务");
        }
        state.running = false;
    }

    public String onvifStatus(String deviceId) {
        CaptureTaskState state = onvifTasks.get(deviceId);
        return state != null && state.running ? "running" : "stopped";
    }

    public List<Map<String, Object>> listOnvifPresets(String deviceId) {
        requireDevice(deviceId);
        throw new VideoBusinessException(500, "设备未配置 ONVIF 连接信息或 ONVIF SDK 不可用");
    }

    public Map<String, Object> setOnvifPreset(String deviceId, String name, String presetToken) {
        requireDevice(deviceId);
        throw new VideoBusinessException(500, "保存预置点失败: ONVIF SDK 不可用");
    }

    public void callOnvifPreset(String deviceId, String presetToken) {
        requireDevice(deviceId);
        throw new VideoBusinessException(500, "调用预置点失败: ONVIF SDK 不可用");
    }

    public void deleteOnvifPreset(String deviceId, String presetToken) {
        requireDevice(deviceId);
        throw new VideoBusinessException(500, "删除预置点失败: ONVIF SDK 不可用");
    }

    public Map<String, Object> captureSnapshot(String deviceId) {
        DeviceRow device = requireDevice(deviceId);
        if (device.getSource() == null || device.getSource().isBlank()) {
            throw new VideoBusinessException(400, "设备源地址为空");
        }
        throw new VideoBusinessException(500, "无法获取可播放的视频流地址（国标点播失败或设备离线）");
    }

    private DeviceRow requireDevice(String deviceId) {
        return deviceRepository.findById(deviceId)
                .orElseThrow(() -> new VideoBusinessException(400, "设备不存在: ID=" + deviceId));
    }

    private static String str(Object value) {
        return value != null ? String.valueOf(value).trim() : "";
    }

    private static final class CaptureTaskState {
        private boolean running;

        private CaptureTaskState(boolean running) {
            this.running = running;
        }
    }
}
