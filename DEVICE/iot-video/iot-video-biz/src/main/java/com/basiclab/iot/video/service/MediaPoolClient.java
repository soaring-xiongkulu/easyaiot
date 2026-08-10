package com.basiclab.iot.video.service;

import com.basiclab.iot.video.config.VideoProperties;
import javax.annotation.PostConstruct;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.util.UriComponentsBuilder;

import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;

/**
 * Mirrors retired Python {@code app.utils.media_client} — iot-node media pool HTTP client.
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class MediaPoolClient {

    private static final int REQUEST_TIMEOUT_MS = 30_000;

    private final VideoProperties videoProperties;
    private RestTemplate restTemplate;

    @PostConstruct
    void initRestTemplate() {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(REQUEST_TIMEOUT_MS);
        factory.setReadTimeout(REQUEST_TIMEOUT_MS);
        this.restTemplate = new RestTemplate(factory);
    }

    public boolean isMediaPoolEnabled() {
        String env = trimToNull(System.getenv("MEDIA_NODE_POOL_ENABLED"));
        if (env != null) {
            return isTruthy(env);
        }
        Boolean configured = videoProperties.getMediaPool().getEnabled();
        return configured != null && configured;
    }

    public Map<String, Object> allocateDeviceMedia(
            String deviceId,
            boolean needSrsLive,
            boolean needSrsAi,
            boolean needZlm,
            String region,
            String httpPlayHost
    ) {
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("deviceId", deviceId);
        payload.put("needSrsLive", needSrsLive);
        payload.put("needSrsAi", needSrsAi);
        payload.put("needZlm", needZlm);
        payload.put("region", firstNonBlank(region, trimToNull(System.getenv("MEDIA_NODE_REGION")),
                trimToNull(videoProperties.getMediaPool().getRegion())));
        payload.put("httpPlayHost", firstNonBlank(httpPlayHost, trimToNull(System.getenv("MEDIA_HTTP_PLAY_HOST")),
                trimToNull(videoProperties.getMediaPool().getHttpPlayHost())));
        return postJson("/allocate", payload);
    }

    public Map<String, Object> allocateDeviceMedia(String deviceId) {
        return allocateDeviceMedia(deviceId, true, true, false, null, null);
    }

    public Map<String, Object> getDeviceMediaBinding(String deviceId) {
        String url = UriComponentsBuilder.fromHttpUrl(mediaApiBase() + "/binding")
                .queryParam("deviceId", deviceId)
                .toUriString();
        try {
            HttpHeaders headers = buildHeaders();
            HttpEntity<Void> entity = new HttpEntity<>(headers);
            ResponseEntity<Map> response = restTemplate.exchange(url, HttpMethod.GET, entity, Map.class);
            return ensureSuccess(response);
        } catch (RestClientException ex) {
            throw new MediaPoolException("查询媒体绑定失败: " + ex.getMessage(), ex);
        }
    }

    public String[] streamUrlsFromBinding(Map<String, Object> binding) {
        if (binding == null || binding.isEmpty()) {
            return new String[]{"", "", "", ""};
        }
        return new String[]{
                stringOrEmpty(binding.get("rtmpStream")),
                stringOrEmpty(binding.get("httpStream")),
                stringOrEmpty(binding.get("aiRtmpStream")),
                stringOrEmpty(binding.get("aiHttpStream"))
        };
    }

    String mediaApiBase() {
        String base = trimToNull(System.getenv("JAVA_BACKEND_URL"));
        if (base == null) {
            base = trimToNull(System.getenv("GATEWAY_URL"));
        }
        if (base == null) {
            base = trimToNull(videoProperties.getNodeRemote().getGatewayUrl());
        }
        if (base == null) {
            base = "http://localhost:48080";
        }
        return base.replaceAll("/+$", "") + "/admin-api/node/media";
    }

    private Map<String, Object> postJson(String path, Map<String, Object> payload) {
        String url = mediaApiBase() + path;
        try {
            HttpHeaders headers = buildHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<Map<String, Object>> entity = new HttpEntity<>(payload, headers);
            ResponseEntity<Map> response = restTemplate.postForEntity(url, entity, Map.class);
            return ensureSuccess(response);
        } catch (RestClientException ex) {
            throw new MediaPoolException("媒体绑定失败 " + path + ": " + ex.getMessage(), ex);
        }
    }

    private HttpHeaders buildHeaders() {
        HttpHeaders headers = new HttpHeaders();
        String token = trimToNull(System.getenv("JWT_TOKEN"));
        if (token != null) {
            if (!token.toLowerCase(Locale.ROOT).startsWith("bearer ")) {
                token = "Bearer " + token;
            }
            headers.set("X-Authorization", token);
        }
        return headers;
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> ensureSuccess(ResponseEntity<Map> response) {
        if (!response.getStatusCode().is2xxSuccessful()) {
            throw new MediaPoolException("媒体池 HTTP " + response.getStatusCode().value());
        }
        Map<?, ?> body = response.getBody();
        if (body == null) {
            throw new MediaPoolException("媒体池空响应");
        }
        Object code = body.get("code");
        if (code instanceof Number number && number.intValue() != 0) {
            Object msg = body.get("msg") != null ? body.get("msg") : body.get("message");
            throw new MediaPoolException(String.valueOf(msg != null ? msg : body));
        }
        Object data = body.get("data");
        if (data instanceof Map<?, ?> map) {
            Map<String, Object> out = new LinkedHashMap<>();
            map.forEach((k, v) -> out.put(String.valueOf(k), v));
            return out;
        }
        return new LinkedHashMap<>();
    }

    private static String stringOrEmpty(Object value) {
        return value != null ? String.valueOf(value).trim() : "";
    }

    private static String firstNonBlank(String... values) {
        for (String value : values) {
            if (value != null && !value.isBlank()) {
                return value.trim();
            }
        }
        return null;
    }

    private static boolean isTruthy(String value) {
        String normalized = value.trim().toLowerCase(Locale.ROOT);
        return normalized.equals("1") || normalized.equals("true") || normalized.equals("yes");
    }

    private static String trimToNull(String value) {
        if (value == null) {
            return null;
        }
        String trimmed = value.trim();
        return trimmed.isEmpty() ? null : trimmed;
    }

    public static class MediaPoolException extends RuntimeException {
        public MediaPoolException(String message) {
            super(message);
        }

        public MediaPoolException(String message, Throwable cause) {
            super(message, cause);
        }
    }
}
