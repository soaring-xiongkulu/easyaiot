package com.basiclab.iot.video.service.talk;

import com.basiclab.iot.video.dal.DeviceRepository;
import com.basiclab.iot.video.domain.DeviceRow;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

@Slf4j
@Service
@RequiredArgsConstructor
public class AudioTalkService {

    private static final long CAPABILITIES_CACHE_TTL_MS = 120_000L;

    private final DeviceRepository deviceRepository;
    private final Map<String, AudioTalkSession> sessions = new ConcurrentHashMap<>();
    private final Map<String, CacheEntry> capabilitiesCache = new ConcurrentHashMap<>();

    public Map<String, Object> getCapabilities(String deviceId) {
        DeviceRow camera = resolveCamera(deviceId).orElse(null);
        if (camera == null) {
            return Map.of("status", 404, "code", 404, "msg", "设备不存在");
        }
        int rtspPort = camera.getPort() != null && camera.getPort() > 0 ? camera.getPort() : 554;
        String username = camera.getUsername() != null ? camera.getUsername() : "admin";
        String password = deviceRepository.findPasswordById(deviceId).orElse("");
        String cacheKey = deviceId + ":" + camera.getIp() + ":" + rtspPort;
        long now = System.currentTimeMillis();
        CacheEntry cached = capabilitiesCache.get(cacheKey);
        Map<String, Object> probe;
        if (cached != null && now - cached.timestampMs < CAPABILITIES_CACHE_TTL_MS) {
            probe = cached.result;
        } else {
            probe = probeCapabilities(camera.getIp(), rtspPort, username, password);
            capabilitiesCache.put(cacheKey, new CacheEntry(now, probe));
        }
        Map<String, Object> capabilities = new LinkedHashMap<>();
        boolean supported = Boolean.TRUE.equals(probe.get("audio_backchannel_supported"));
        capabilities.put("supported", supported);
        capabilities.put("audio_backchannel_supported", supported);
        capabilities.put("codecs", List.of("PCMU", "PCMA"));
        capabilities.put("sample_rate", 8000);
        capabilities.put("channels", 1);
        capabilities.put("onvif_supported", isOnvifAudioAvailable());
        capabilities.put("audio_tracks", probe.getOrDefault("audio_tracks", List.of()));
        return Map.of(
                "status", 200,
                "code", 0,
                "msg", "ok",
                "data", Map.of("success", true, "capabilities", capabilities)
        );
    }

    public Map<String, Object> startSession(Map<String, Object> body) {
        if (!isAudioTalkAvailable()) {
            return error(500, "ONVIF 语音对讲服务未安装");
        }
        String deviceId = firstString(body, "device_id", "camera_id");
        if (deviceId.isEmpty()) {
            return error(400, "缺少设备 ID");
        }
        DeviceRow camera = resolveCamera(deviceId).orElse(null);
        if (camera == null) {
            return error(404, "设备不存在");
        }
        if (camera.getIp() == null || camera.getIp().isBlank()) {
            return actionFailure("Audio Back Channel 建立失败，设备可能不支持");
        }
        String sessionId = "audio_talk_" + deviceId + "_" + UUID.randomUUID().toString().substring(0, 8);
        int rtspPort = camera.getPort() != null && camera.getPort() > 0 ? camera.getPort() : 554;
        String audioCodec = firstString(body, "audio_codec");
        if (audioCodec.isEmpty()) {
            audioCodec = "PCMU";
        }
        int sampleRate = toInt(body.get("sample_rate"), 8000);
        float volumeGain = toFloat(body.get("volume_gain"), 1.0f);
        boolean noiseSuppression = toBool(body.get("noise_suppression"), true);
        boolean echoCancellation = toBool(body.get("echo_cancellation"), true);
        String username = camera.getUsername() != null ? camera.getUsername() : "admin";
        String password = deviceRepository.findPasswordById(deviceId).orElse("");
        AudioTalkSession session = new AudioTalkSession(
                sessionId,
                deviceId,
                camera.getIp(),
                rtspPort,
                username,
                password,
                audioCodec,
                sampleRate,
                volumeGain,
                noiseSuppression,
                echoCancellation
        );
        sessions.put(sessionId, session);
        if (!session.start()) {
            sessions.remove(sessionId);
            return actionFailure("Audio Back Channel 建立失败，设备可能不支持");
        }
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("status", 200);
        payload.put("code", 0);
        payload.put("msg", "ONVIF 语音对讲已启动");
        payload.put("data", session.toStartPayload());
        return payload;
    }

    public Map<String, Object> stopSession(String sessionId) {
        if (sessionId == null || sessionId.isBlank()) {
            return error(400, "缺少 session_id");
        }
        AudioTalkSession session = sessions.remove(sessionId);
        if (session != null) {
            session.stop();
        }
        return Map.of(
                "status", 200,
                "code", 0,
                "msg", "已停止",
                "data", Map.of("success", true, "session_id", sessionId)
        );
    }

    public Map<String, Object> sendAudio(String sessionId, String audioB64) {
        if (sessionId == null || sessionId.isBlank() || audioB64 == null || audioB64.isBlank()) {
            return error(400, "缺少 session_id 或 audio_data");
        }
        AudioTalkSession session = sessions.get(sessionId);
        if (session == null || !session.sendAudio(java.util.Base64.getDecoder().decode(audioB64))) {
            return actionFailure("发送失败");
        }
        return Map.of(
                "status", 200,
                "code", 0,
                "msg", "ok",
                "data", Map.of("success", true)
        );
    }

    public Map<String, Object> health() {
        boolean onvifAvailable = isOnvifAudioAvailable();
        return Map.of(
                "status", 200,
                "code", 0,
                "data", Map.of(
                        "status", "ok",
                        "onvif_available", onvifAvailable,
                        "audio_talk_available", onvifAvailable && isAudioTalkAvailable()
                )
        );
    }

    private boolean isOnvifAudioAvailable() {
        try {
            Class.forName("com.basiclab.iot.video.service.talk.OnvifAudioBackchannelClient");
            return true;
        } catch (ClassNotFoundException ex) {
            return false;
        }
    }

    private boolean isAudioTalkAvailable() {
        return isOnvifAudioAvailable();
    }

    private Map<String, Object> probeCapabilities(String cameraIp, int cameraPort, String username, String password) {
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("audio_backchannel_supported", false);
        result.put("audio_tracks", List.of());
        try (OnvifAudioBackchannelClient client = new OnvifAudioBackchannelClient(
                cameraIp, cameraPort, username, password, "PCMA", 8000, 3000)) {
            if (!client.connect()) {
                return result;
            }
            return client.describeAudioBackchannel("/audio");
        } catch (Exception ex) {
            log.warn("ONVIF talk probe failed {}:{} - {}", cameraIp, cameraPort, ex.getMessage());
            return result;
        }
    }

    private Optional<DeviceRow> resolveCamera(String deviceId) {
        if (deviceId == null || deviceId.isBlank()) {
            return Optional.empty();
        }
        return deviceRepository.findById(deviceId);
    }

    private Map<String, Object> error(int code, String msg) {
        return Map.of("status", code, "code", code, "msg", msg);
    }

    private Map<String, Object> actionFailure(String msg) {
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("status", 500);
        payload.put("code", 500);
        payload.put("msg", msg);
        payload.put("data", Map.of("success", false));
        return payload;
    }

    private String firstString(Map<String, Object> body, String... keys) {
        if (body == null) {
            return "";
        }
        for (String key : keys) {
            Object value = body.get(key);
            if (value != null) {
                String text = String.valueOf(value).trim();
                if (!text.isEmpty()) {
                    return text;
                }
            }
        }
        return "";
    }

    private int toInt(Object value, int defaultValue) {
        if (value == null) {
            return defaultValue;
        }
        try {
            return Integer.parseInt(String.valueOf(value));
        } catch (NumberFormatException ex) {
            return defaultValue;
        }
    }

    private float toFloat(Object value, float defaultValue) {
        if (value == null) {
            return defaultValue;
        }
        try {
            return Float.parseFloat(String.valueOf(value));
        } catch (NumberFormatException ex) {
            return defaultValue;
        }
    }

    private boolean toBool(Object value, boolean defaultValue) {
        if (value == null) {
            return defaultValue;
        }
        if (value instanceof Boolean bool) {
            return bool;
        }
        String text = String.valueOf(value).trim().toLowerCase();
        if (text.isEmpty()) {
            return defaultValue;
        }
        return "1".equals(text) || "true".equals(text) || "yes".equals(text) || "on".equals(text);
    }

    private record CacheEntry(long timestampMs, Map<String, Object> result) {
    }
}
