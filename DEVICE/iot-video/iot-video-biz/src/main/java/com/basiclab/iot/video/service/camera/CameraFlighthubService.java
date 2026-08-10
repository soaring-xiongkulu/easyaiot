package com.basiclab.iot.video.service.camera;

import com.basiclab.iot.video.dal.DeviceRepository;
import com.basiclab.iot.video.domain.DeviceRow;
import com.basiclab.iot.video.exception.VideoBusinessException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.LinkedHashMap;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class CameraFlighthubService {

    private final CameraAdminService cameraAdminService;
    private final DeviceRepository deviceRepository;

    public Map<String, Object> publicConfig() {
        Map<String, Object> config = new LinkedHashMap<>();
        config.put("api_host", env("FLIGHTHUB_OPENAPI_HOST", ""));
        config.put("project_uuid", env("FLIGHTHUB_PROJECT_UUID", ""));
        config.put("has_user_token", !env("FLIGHTHUB_USER_TOKEN", "").isEmpty());
        return config;
    }

    public Map<String, Object> registerDjiLive(Map<String, Object> data) {
        String source = str(data.get("source"));
        if (source.isEmpty()) {
            throw new VideoBusinessException(400, "source is required");
        }
        Map<String, Object> registerInfo = new LinkedHashMap<>(data);
        registerInfo.put("manufacturer", "DJI");
        registerInfo.putIfAbsent("model", "DJI Dock Live");
        String deviceId = cameraAdminService.registerDevice(registerInfo);
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("id", deviceId);
        result.put("device_type", registerInfo.getOrDefault("device_type", "dock"));
        result.put("model", registerInfo.get("model"));
        return result;
    }

    public Map<String, Object> startLiveStream(Map<String, Object> data) {
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("provider", null);
        payload.put("url_type", null);
        payload.put("suggestion", "FlightHub OpenAPI not integrated in Java candidate");
        return Map.of(
                "ok", false,
                "code", 500,
                "msg", "FlightHub live start failed",
                "payload", payload
        );
    }

    public Map<String, Object> refreshLiveByDevice(String deviceId, Map<String, Object> data) {
        DeviceRow device = deviceRepository.findById(deviceId)
                .orElseThrow(() -> new VideoBusinessException(404, "device not found"));
        Map<String, Object> merged = new LinkedHashMap<>(data);
        merged.putIfAbsent("name", device.getName());
        merged.putIfAbsent("serial_number", device.getSerialNumber());
        return startLiveStream(merged);
    }

    private static String env(String name, String defaultValue) {
        String value = System.getenv(name);
        return value != null && !value.isBlank() ? value.trim() : defaultValue;
    }

    private static String str(Object value) {
        return value != null ? String.valueOf(value).trim() : "";
    }
}
