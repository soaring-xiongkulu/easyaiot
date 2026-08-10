package com.basiclab.iot.video.service.camera;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * 大疆司空 FlightHub 直播接入（对照 Python {@code flighthub_source.py}）。
 */
public final class FlighthubSourceSupport {

    static final String DJI_MANUFACTURER = "DJI";
    static final String DJI_MODEL_DOCK = "DJI Dock Live";
    static final String DJI_MODEL_DRONE = "DJI Drone Live";
    static final String DEFAULT_LIVE_START_PATH = "/openapi/v0.1/live-stream/start";

    private static final Pattern CONNECTION_STATUS_RE = Pattern.compile(
            "^dji_live\\|(?<deviceType>dock|drone)\\|cam=(?<cameraIndex>.+)$"
    );
    private static final ObjectMapper MAPPER = new ObjectMapper();

    private FlighthubSourceSupport() {
    }

    public static String env(String name, String defaultValue) {
        String value = System.getenv(name);
        return value != null && !value.isBlank() ? value.trim() : (defaultValue != null ? defaultValue : "");
    }

    public static String normalizeHost(String host) {
        String normalized = host != null ? host.trim() : "";
        if (normalized.endsWith("/")) {
            normalized = normalized.replaceAll("/+$", "");
        }
        if (normalized.isEmpty()) {
            return "";
        }
        if (!normalized.startsWith("http://") && !normalized.startsWith("https://")) {
            normalized = "https://" + normalized;
        }
        return normalized;
    }

    public static String normalizeDeviceType(Object value, String model, String name) {
        String raw = value != null ? String.valueOf(value).trim().toLowerCase(Locale.ROOT) : "";
        if (raw.equals("dock") || raw.equals("airport") || raw.equals("hangar")) {
            return "dock";
        }
        if (raw.equals("drone") || raw.equals("uav") || raw.equals("aircraft")) {
            return "drone";
        }
        String text = (model != null ? model : "") + " " + (name != null ? name : "");
        if (text.matches("(?i).*(drone|无人机|Drone\\s*Live).*")) {
            return "drone";
        }
        if (text.matches("(?i).*(dock|机场|Dock\\s*Live).*")) {
            return "dock";
        }
        return "dock";
    }

    public static String modelForDeviceType(String deviceType) {
        return "dock".equals(normalizeDeviceType(deviceType, "", "")) ? DJI_MODEL_DOCK : DJI_MODEL_DRONE;
    }

    public static String buildConnectionStatus(String deviceType, String cameraIndex) {
        String dtype = normalizeDeviceType(deviceType, "", "");
        String cam = cameraIndex != null ? cameraIndex.trim() : "";
        return "dji_live|" + dtype + "|cam=" + cam;
    }

    public static String[] parseConnectionStatus(String value) {
        Matcher matcher = CONNECTION_STATUS_RE.matcher(value != null ? value.trim() : "");
        if (!matcher.matches()) {
            return new String[]{"", ""};
        }
        return new String[]{matcher.group("deviceType"), matcher.group("cameraIndex")};
    }

    public static String resolveCameraIndex(Map<String, Object> data, String source, String connectionStatus) {
        for (String key : new String[]{"camera_index", "cameraIndex"}) {
            Object value = data != null ? data.get(key) : null;
            if (value != null && !String.valueOf(value).trim().isEmpty()) {
                return String.valueOf(value).trim();
            }
        }
        String[] parsed = parseConnectionStatus(connectionStatus);
        if (!parsed[1].isBlank()) {
            return parsed[1];
        }
        return extractCameraIndexFromSource(source);
    }

    public static Map<String, Object> buildRegisterInfo(Map<String, Object> data, String source) {
        String projectUuid = firstNonBlank(data, "project_uuid", "workspace_id");
        String deviceType = normalizeDeviceType(
                data.get("device_type"),
                str(data.get("model")),
                str(data.get("name"))
        );
        String cameraIndex = resolveCameraIndex(data, source, str(data.get("connection_status")));
        String serial = firstNonBlank(data, "serial_number", "sn", "dock_sn", "drone_sn");
        Map<String, Object> info = new LinkedHashMap<>();
        info.put("name", firstNonBlank(data, "name") != null ? firstNonBlank(data, "name")
                : ("dock".equals(deviceType) ? "大疆机场直播" : "大疆无人机直播"));
        info.put("source", source);
        info.put("cameraType", "custom");
        info.put("username", projectUuid != null ? projectUuid : "");
        info.put("password", "");
        info.put("skylink_token", firstNonBlank(data, "skylink_token", "user_token", "x_user_token"));
        info.put("manufacturer", data.get("manufacturer") != null ? data.get("manufacturer") : DJI_MANUFACTURER);
        info.put("model", data.get("model") != null ? data.get("model") : modelForDeviceType(deviceType));
        info.put("serial_number", serial != null ? serial : "");
        info.put("hardware_id", data.get("hardware_id") != null ? data.get("hardware_id")
                : (projectUuid != null && !projectUuid.isBlank() ? "flighthub:" + projectUuid : ""));
        info.put("firmware_version", firstNonBlank(data, "api_host", "platform_host"));
        info.put("enable_forward", boolOr(data.get("enable_forward"), false));
        info.put("port", data.getOrDefault("port", 554));
        info.put("address", data.get("address"));
        info.put("longitude", data.get("longitude"));
        info.put("latitude", data.get("latitude"));
        info.put("altitude", data.get("altitude"));
        info.put("connection_status", buildConnectionStatus(deviceType, cameraIndex));
        info.put("device_type", deviceType);
        info.put("camera_index", cameraIndex);
        return info;
    }

    public static Map<String, Object> publicConfig() {
        Map<String, Object> config = new LinkedHashMap<>();
        String allowedIps = env("FLIGHTHUB_ALLOWED_IPS", "");
        config.put("allowed_ips", allowedIps.isBlank()
                ? List.of()
                : Arrays.stream(allowedIps.split(",")).map(String::trim).filter(s -> !s.isEmpty()).toList());
        config.put("workspace_id", env("FLIGHTHUB_WORKSPACE_ID", ""));
        config.put("workspace_name", env("FLIGHTHUB_WORKSPACE_NAME", ""));
        config.put("platform_name", env("FLIGHTHUB_PLATFORM_NAME", ""));
        String openapiHost = env("FLIGHTHUB_OPENAPI_HOST", "");
        config.put("platform_host", env("FLIGHTHUB_PLATFORM_HOST", openapiHost));
        config.put("openapi_host", openapiHost);
        config.put("live_start_path", env("FLIGHTHUB_LIVE_START_PATH", DEFAULT_LIVE_START_PATH));
        config.put("mqtt_enabled", "true".equalsIgnoreCase(env("FLIGHTHUB_MQTT_ENABLED", "false")));
        config.put("mqtt_broker_uri", env("FLIGHTHUB_MQTT_BROKER_URI", ""));
        config.put("mqtt_client_id", env("FLIGHTHUB_MQTT_CLIENT_ID", ""));
        config.put("mqtt_username", env("FLIGHTHUB_MQTT_USERNAME", ""));
        return config;
    }

    public static Map<String, Object> skylinkRequestPayload(Map<String, Object> data) {
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("sn", firstNonBlank(data, "sn", "serial_number"));
        payload.put("camera_index", str(data.get("camera_index")));
        payload.put("video_expire", intOr(data.get("video_expire"), 3600));
        payload.put("quality_type", data.getOrDefault("quality_type", "adaptive"));
        return payload;
    }

    public static JsonNode findLiveProvider(JsonNode payload) {
        if (payload == null || payload.isNull()) {
            return null;
        }
        if (payload.isObject()) {
            for (String key : new String[]{"provider", "live", "live_info", "liveStream", "live_stream", "data", "result"}) {
                JsonNode found = findLiveProvider(payload.get(key));
                if (found != null) {
                    return found;
                }
            }
            for (String key : new String[]{"url", "play_url", "live_url", "stream_url"}) {
                if (payload.hasNonNull(key) && !payload.get(key).asText("").isBlank()) {
                    return payload;
                }
            }
            var fields = payload.fields();
            while (fields.hasNext()) {
                JsonNode found = findLiveProvider(fields.next().getValue());
                if (found != null) {
                    return found;
                }
            }
        } else if (payload.isArray()) {
            for (JsonNode item : payload) {
                JsonNode found = findLiveProvider(item);
                if (found != null) {
                    return found;
                }
            }
        }
        return null;
    }

    public static String providerUrl(JsonNode provider) {
        if (provider == null || !provider.isObject()) {
            return "";
        }
        for (String key : new String[]{"url", "play_url", "live_url", "stream_url", "rtmp_url", "flv_url", "hls_url"}) {
            if (provider.hasNonNull(key) && !provider.get(key).asText("").isBlank()) {
                return provider.get(key).asText("").trim();
            }
        }
        return "";
    }

    public static boolean isDirectLiveUrl(String url) {
        String lower = url != null ? url.trim().toLowerCase(Locale.ROOT) : "";
        return (lower.startsWith("rtmp://") || lower.startsWith("rtsp://")
                || lower.startsWith("http://") || lower.startsWith("https://"))
                && !lower.startsWith("volc://");
    }

    public static boolean isSdkLiveProvider(JsonNode provider, String url) {
        String urlType = provider != null && provider.has("url_type")
                ? provider.get("url_type").asText("").toLowerCase(Locale.ROOT)
                : provider != null && provider.has("type")
                ? provider.get("type").asText("").toLowerCase(Locale.ROOT)
                : "";
        String effectiveUrl = url != null && !url.isBlank() ? url : providerUrl(provider);
        return !isDirectLiveUrl(effectiveUrl)
                || Set.of("volc", "agora", "webrtc", "sdk").contains(urlType);
    }

    public static ObjectMapper mapper() {
        return MAPPER;
    }

    private static String extractCameraIndexFromSource(String source) {
        String value = source != null ? source.trim() : "";
        if (!value.startsWith("volc://")) {
            return "";
        }
        try {
            String query = URLDecoder.decode(value.substring("volc://".length()), StandardCharsets.UTF_8);
            String roomId = "";
            for (String part : query.split("&")) {
                if (part.startsWith("room_id=")) {
                    roomId = part.substring("room_id=".length());
                    break;
                }
            }
            int underscore = roomId.indexOf('_');
            if (underscore >= 0) {
                return roomId.substring(underscore + 1).trim();
            }
        } catch (Exception ignored) {
            return "";
        }
        return "";
    }

    private static String firstNonBlank(Map<String, Object> data, String... keys) {
        if (data == null) {
            return null;
        }
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

    private static int intOr(Object value, int defaultValue) {
        if (value == null || "".equals(String.valueOf(value))) {
            return defaultValue;
        }
        return Integer.parseInt(String.valueOf(value));
    }

    private static boolean boolOr(Object value, boolean defaultValue) {
        if (value == null) {
            return defaultValue;
        }
        if (value instanceof Boolean bool) {
            return bool;
        }
        String text = String.valueOf(value).trim().toLowerCase(Locale.ROOT);
        if ("false".equals(text) || "0".equals(text) || "no".equals(text)) {
            return false;
        }
        if ("true".equals(text) || "1".equals(text) || "yes".equals(text)) {
            return true;
        }
        return defaultValue;
    }
}
