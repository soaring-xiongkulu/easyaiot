package com.basiclab.iot.video.service.camera;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Duration;
import java.util.Base64;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.regex.Pattern;

@Service
@RequiredArgsConstructor
public class CameraStreamTicketService {

    private static final Pattern STREAM_PATH = Pattern.compile("^/(ai|live|rtp)/");
    private static final String AUTH_CHECK_PATH = "/admin-api/system/auth/get-permission-info";

    private final ObjectMapper objectMapper;
    private final HttpClient httpClient = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(5))
            .build();

    public Map<String, Object> signTicket(String authorization, String tenantId, Map<String, Object> body) {
        if (!checkLogin(authorization, tenantId)) {
            return Map.of("httpStatus", 401, "code", 401, "msg", "unauthorized");
        }
        String path = body.get("path") != null ? String.valueOf(body.get("path")).trim() : "";
        if (!STREAM_PATH.matcher(path).find()) {
            return Map.of("httpStatus", 400, "code", 400, "msg", "invalid stream path");
        }
        String secret = System.getenv("STREAM_TICKET_SECRET");
        if (secret == null || secret.isBlank()) {
            return Map.of("httpStatus", 500, "code", 500, "msg", "stream ticket secret not configured");
        }
        int ttl = 90;
        Object ttlRaw = body.get("ttl");
        if (ttlRaw != null) {
            try {
                ttl = Integer.parseInt(String.valueOf(ttlRaw));
            } catch (NumberFormatException ignored) {
                ttl = 90;
            }
        }
        ttl = Math.max(15, Math.min(ttl, 600));
        long e = System.currentTimeMillis() / 1000L + ttl;
        String raw = e + path + " " + secret;
        try {
            MessageDigest md5 = MessageDigest.getInstance("MD5");
            byte[] digest = md5.digest(raw.getBytes(StandardCharsets.UTF_8));
            String st = Base64.getUrlEncoder().withoutPadding().encodeToString(digest);
            Map<String, Object> data = new LinkedHashMap<>();
            data.put("e", e);
            data.put("st", st);
            return Map.of("httpStatus", 200, "code", 0, "msg", "success", "data", data);
        } catch (Exception ex) {
            return Map.of("httpStatus", 500, "code", 500, "msg", "stream ticket sign failed");
        }
    }

    private boolean checkLogin(String authorization, String tenantId) {
        if (authorization == null || authorization.isBlank()) {
            return false;
        }
        String base = resolveAuthCheckUrl();
        try {
            HttpRequest.Builder builder = HttpRequest.newBuilder()
                    .uri(URI.create(base))
                    .timeout(Duration.ofSeconds(5))
                    .header("Authorization", authorization);
            if (tenantId != null && !tenantId.isBlank()) {
                builder.header("tenant-id", tenantId);
            }
            HttpResponse<String> response = httpClient.send(builder.GET().build(), HttpResponse.BodyHandlers.ofString());
            if (response.statusCode() != 200) {
                return false;
            }
            JsonNode body = objectMapper.readTree(response.body());
            return body.has("code") && body.get("code").asInt() == 0;
        } catch (Exception e) {
            return false;
        }
    }

    private static String resolveAuthCheckUrl() {
        String explicit = System.getenv("AUTH_CHECK_URL");
        if (explicit != null && !explicit.isBlank()) {
            return explicit.trim();
        }
        String base = System.getenv("JAVA_BACKEND_URL");
        if (base == null || base.isBlank()) {
            base = System.getenv("GATEWAY_URL");
        }
        if (base == null || base.isBlank()) {
            base = "http://127.0.0.1:48099";
        }
        return base.replaceAll("/+$", "") + AUTH_CHECK_PATH;
    }
}
