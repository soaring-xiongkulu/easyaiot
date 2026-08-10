package com.basiclab.iot.video.service.camera;

import com.basiclab.iot.video.dal.DeviceRepository;
import com.basiclab.iot.video.domain.DeviceRow;
import com.basiclab.iot.video.exception.VideoBusinessException;
import com.fasterxml.jackson.databind.JsonNode;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;

@Slf4j
@Service
@RequiredArgsConstructor
public class CameraFlighthubService {

    private final CameraAdminService cameraAdminService;
    private final DeviceRepository deviceRepository;
    private final HttpClient httpClient = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(10))
            .build();

    public Map<String, Object> publicConfig() {
        return FlighthubSourceSupport.publicConfig();
    }

    public Map<String, Object> registerDjiLive(Map<String, Object> data) {
        String source = str(data.get("source"));
        if (source.isEmpty()) {
            throw new VideoBusinessException(400, "source is required");
        }
        Map<String, Object> registerInfo = FlighthubSourceSupport.buildRegisterInfo(data, source);
        String deviceId = registerFlighthubDevice(registerInfo);
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("id", deviceId);
        result.put("device_type", registerInfo.get("device_type"));
        result.put("model", registerInfo.get("model"));
        return result;
    }

    public Map<String, Object> startLiveStream(Map<String, Object> data) {
        String apiHost = FlighthubSourceSupport.normalizeHost(firstNonBlank(
                data,
                "api_host",
                "platform_host",
                env("FLIGHTHUB_OPENAPI_HOST", "")
        ));
        String apiPath = firstNonBlank(data, "api_path") != null
                ? firstNonBlank(data, "api_path")
                : FlighthubSourceSupport.env("FLIGHTHUB_LIVE_START_PATH", FlighthubSourceSupport.DEFAULT_LIVE_START_PATH);
        String projectUuid = firstNonBlank(
                data,
                "project_uuid",
                "workspace_id",
                env("FLIGHTHUB_WORKSPACE_ID", "")
        );
        String userToken = firstNonBlank(
                data,
                "user_token",
                "skylink_token",
                env("FLIGHTHUB_USER_TOKEN", "")
        );

        if (apiHost.isBlank() || apiPath.isBlank() || projectUuid == null || userToken == null) {
            return failure(400, "api_host, api_path, project_uuid and user_token are required", null);
        }

        String url = apiHost + (apiPath.startsWith("/") ? apiPath : "/" + apiPath);
        Map<String, Object> requestBody = FlighthubSourceSupport.skylinkRequestPayload(data);
        try {
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(url))
                    .timeout(Duration.ofSeconds(20))
                    .header("X-Project-Uuid", projectUuid)
                    .header("X-User-Token", userToken)
                    .header("Content-Type", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(
                            FlighthubSourceSupport.mapper().writeValueAsString(requestBody)
                    ))
                    .build();
            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            JsonNode body;
            try {
                body = FlighthubSourceSupport.mapper().readTree(response.body());
            } catch (Exception ex) {
                body = FlighthubSourceSupport.mapper().createObjectNode().put("raw", response.body());
            }

            if (response.statusCode() >= 400) {
                return failure(response.statusCode(), "FlightHub request failed", body);
            }

            JsonNode provider = FlighthubSourceSupport.findLiveProvider(body);
            String playUrl = FlighthubSourceSupport.providerUrl(provider);
            String urlType = provider != null && provider.has("url_type")
                    ? provider.get("url_type").asText("").toLowerCase(Locale.ROOT)
                    : provider != null && provider.has("type")
                    ? provider.get("type").asText("").toLowerCase(Locale.ROOT)
                    : "";

            if (playUrl.isBlank()) {
                return failure(502, "FlightHub did not return a live url", body);
            }
            if (FlighthubSourceSupport.isSdkLiveProvider(provider, playUrl)) {
                Map<String, Object> payload = new LinkedHashMap<>();
                payload.put("provider", provider);
                payload.put("url_type", urlType.isBlank() && provider != null && provider.has("type")
                        ? provider.get("type").asText("") : urlType);
                payload.put("suggestion",
                        "请在司空侧切换为 RTMP/HTTP-FLV/HLS 等可直拉供应商，"
                                + "或由前端 SDK / 直播桥接服务接入后再转本地 SRS。");
                payload.put("raw", body);
                Map<String, Object> result = failure(409, "FlightHub returned SDK live provider", payload);
                result.put("provider", provider);
                result.put("url_type", payload.get("url_type"));
                result.put("suggestion", payload.get("suggestion"));
                return result;
            }

            Map<String, Object> registerInfo = FlighthubSourceSupport.buildRegisterInfo(data, playUrl);
            if (!data.containsKey("enable_forward")) {
                registerInfo.put("enable_forward", true);
            }
            String deviceId = registerFlighthubDevice(registerInfo);
            Map<String, Object> successData = new LinkedHashMap<>();
            successData.put("id", deviceId);
            successData.put("source", playUrl);
            successData.put("provider", provider);
            successData.put("device_type", registerInfo.get("device_type"));
            successData.put("model", registerInfo.get("model"));
            successData.put("raw", body);
            Map<String, Object> result = new LinkedHashMap<>();
            result.put("ok", true);
            result.put("code", 0);
            result.put("data", successData);
            return result;
        } catch (Exception ex) {
            log.error("FlightHub OpenAPI request failed: {}", ex.getMessage(), ex);
            return failure(502, "FlightHub request failed: " + ex.getMessage(), null);
        }
    }

    public Map<String, Object> refreshLiveByDevice(String deviceId, Map<String, Object> data) {
        DeviceRow device = deviceRepository.findById(deviceId)
                .orElseThrow(() -> new VideoBusinessException(404, "device not found"));
        Map<String, Object> merged = new LinkedHashMap<>(data != null ? data : Map.of());
        String[] parsed = FlighthubSourceSupport.parseConnectionStatus(device.getConnectionStatus());
        String deviceType = FlighthubSourceSupport.normalizeDeviceType(
                merged.get("device_type"),
                device.getModel(),
                device.getName()
        );
        if (!parsed[0].isBlank()) {
            deviceType = parsed[0];
        }
        String cameraIndex = FlighthubSourceSupport.resolveCameraIndex(
                merged,
                device.getSource(),
                device.getConnectionStatus()
        );
        merged.putIfAbsent("name", device.getName());
        merged.putIfAbsent("serial_number", device.getSerialNumber());
        String hardwareId = device.getHardwareId() != null ? device.getHardwareId() : "";
        String projectUuid = hardwareId.replace("flighthub:", "").split("\\|")[0];
        if (projectUuid.isBlank()) {
            projectUuid = device.getUsername() != null ? device.getUsername() : "";
        }
        merged.putIfAbsent("project_uuid", projectUuid);
        String token = firstNonBlank(merged, "user_token", "skylink_token");
        if (token == null) {
            token = FlighthubSourceSupport.env("FLIGHTHUB_USER_TOKEN", "");
        }
        if (token.isBlank()) {
            deviceRepository.findPasswordById(deviceId).ifPresent(pw -> merged.putIfAbsent("user_token", pw));
        } else {
            merged.putIfAbsent("user_token", token);
        }
        merged.putIfAbsent("api_host", device.getFirmwareVersion() != null && !device.getFirmwareVersion().isBlank()
                ? device.getFirmwareVersion()
                : FlighthubSourceSupport.env("FLIGHTHUB_OPENAPI_HOST", ""));
        merged.putIfAbsent("sn", device.getSerialNumber());
        merged.putIfAbsent("camera_index", cameraIndex);
        merged.putIfAbsent("device_type", deviceType);
        merged.putIfAbsent("model", device.getModel() != null ? device.getModel()
                : FlighthubSourceSupport.modelForDeviceType(deviceType));
        merged.putIfAbsent("enable_forward", Boolean.TRUE.equals(device.getEnableForward()));
        merged.putIfAbsent("address", device.getAddress());
        merged.putIfAbsent("longitude", device.getLongitude());
        merged.putIfAbsent("latitude", device.getLatitude());
        merged.putIfAbsent("altitude", device.getAltitude());
        return merged;
    }

    private String registerFlighthubDevice(Map<String, Object> registerInfo) {
        String deviceId = cameraAdminService.registerDevice(registerInfo);
        Map<String, Object> fields = new LinkedHashMap<>();
        putIfPresent(fields, "firmware_version", registerInfo.get("firmware_version"));
        putIfPresent(fields, "connection_status", registerInfo.get("connection_status"));
        putIfPresent(fields, "hardware_id", registerInfo.get("hardware_id"));
        putIfPresent(fields, "address", registerInfo.get("address"));
        putIfPresent(fields, "longitude", registerInfo.get("longitude"));
        putIfPresent(fields, "latitude", registerInfo.get("latitude"));
        putIfPresent(fields, "altitude", registerInfo.get("altitude"));
        if (!fields.isEmpty()) {
            deviceRepository.updateFields(deviceId, fields);
        }
        Object token = registerInfo.get("skylink_token");
        if (token != null && !String.valueOf(token).isBlank()) {
            deviceRepository.updatePassword(deviceId, String.valueOf(token));
        }
        return deviceId;
    }

    private static Map<String, Object> failure(int code, String msg, Object raw) {
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("provider", null);
        payload.put("url_type", null);
        payload.put("raw", raw);
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("ok", false);
        result.put("code", code);
        result.put("msg", msg);
        result.put("payload", payload);
        return result;
    }

    private static void putIfPresent(Map<String, Object> fields, String key, Object value) {
        if (value != null && !String.valueOf(value).isBlank()) {
            fields.put(key, value);
        }
    }

    private static String env(String name, String defaultValue) {
        return FlighthubSourceSupport.env(name, defaultValue);
    }

    private static String firstNonBlank(Map<String, Object> data, String... keys) {
        for (String key : keys) {
            Object value = data.get(key);
            if (value != null && !String.valueOf(value).trim().isEmpty()) {
                return String.valueOf(value).trim();
            }
        }
        return null;
    }

    private static String str(Object value) {
        return value != null ? String.valueOf(value).trim() : "";
    }
}
