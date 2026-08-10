package com.basiclab.iot.video.service.camera;

import java.net.Inet4Address;
import java.net.NetworkInterface;
import java.util.ArrayList;
import java.util.Enumeration;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

/**
 * Mirrors retired Python {@code app.utils.gb28181_source} candidate bases and stream URL helpers.
 */
final class Gb28181SourceSupport {

    static final String SOURCE_PREFIX = "gb28181://";
    private static final int GB28181_API_PORT = 48088;

    private Gb28181SourceSupport() {
    }

    static String virtualDeviceId(String sipDeviceId, String channelId) {
        return "gb28181_" + sipDeviceId + "_" + channelId;
    }

    static String buildSource(String sipDeviceId, String channelId) {
        return SOURCE_PREFIX + sipDeviceId + "/" + channelId;
    }

    static List<String> candidateBases() {
        Set<String> seen = new LinkedHashSet<>();
        List<String> ordered = new ArrayList<>();

        addBase(ordered, seen, trimEnv("GB28181_SERVICE_URL"));

        String gatewayUrl = trimEnv("GATEWAY_URL");
        if (gatewayUrl != null) {
            if (gatewayUrl.endsWith("/admin-api")) {
                addBase(ordered, seen, gatewayUrl + "/gb28181");
            } else {
                addBase(ordered, seen, gatewayUrl + "/admin-api/gb28181");
            }
        }

        String host = hostIpForGb28181Api();
        for (String base : List.of(
                "http://127.0.0.1:" + GB28181_API_PORT + "/api",
                "http://localhost:" + GB28181_API_PORT + "/api",
                "http://" + host + ":" + GB28181_API_PORT + "/api"
        )) {
            addBase(ordered, seen, base);
        }
        return ordered;
    }

    static List<String> queryApiRoots(List<String> bases) {
        Set<String> seen = new LinkedHashSet<>();
        List<String> roots = new ArrayList<>();
        for (String base : bases) {
            String b = base == null ? "" : base.trim().replaceAll("/+$", "");
            if (b.isEmpty()) {
                continue;
            }
            String root;
            if (b.endsWith("/device/query")) {
                root = b;
            } else if (b.endsWith("/gb28181")) {
                root = b + "/device/query";
            } else if (b.endsWith("/api")) {
                root = b + "/device/query";
            } else {
                root = b + "/device/query";
            }
            if (seen.add(root)) {
                roots.add(root);
            }
        }
        return roots;
    }

  /** Legacy local SRS AI URLs — use {@link com.basiclab.iot.video.service.StreamUrlSupport} when media pool may apply. */
    static String[] legacyGb28181AiStreamUrls(String deviceId) {
        String host = hostIpForStreamUrls();
        String aiRtmp = "rtmp://" + host + ":1935/ai/" + deviceId;
        String aiHttp = "http://" + host + ":8080/ai/" + deviceId + ".flv";
        return new String[]{"", "", aiRtmp, aiHttp};
    }

    static String hostIpForStreamUrls() {
        return detectHostIpv4();
    }

    private static void addBase(List<String> ordered, Set<String> seen, String base) {
        if (base == null || base.isBlank()) {
            return;
        }
        String normalized = base.trim().replaceAll("/+$", "");
        if (seen.add(normalized)) {
            ordered.add(normalized);
        }
    }

    private static String trimEnv(String key) {
        String value = System.getenv(key);
        if (value == null) {
            return null;
        }
        String trimmed = value.trim();
        return trimmed.isEmpty() ? null : trimmed.replaceAll("/+$", "");
    }

    private static String hostIpForGb28181Api() {
        for (String key : List.of("POD_IP", "HOST_IP")) {
            String ip = trimEnv(key);
            if (ip != null && !"127.0.0.1".equals(ip)) {
                return ip;
            }
        }
        return detectHostIpv4();
    }

    private static String detectHostIpv4() {
        for (String key : List.of("POD_IP", "HOST_IP")) {
            String ip = trimEnv(key);
            if (ip != null && !ip.startsWith("169.254.")) {
                return ip;
            }
        }
        try {
            Enumeration<NetworkInterface> interfaces = NetworkInterface.getNetworkInterfaces();
            while (interfaces != null && interfaces.hasMoreElements()) {
                NetworkInterface ni = interfaces.nextElement();
                if (!ni.isUp() || ni.isLoopback() || ni.isVirtual()) {
                    continue;
                }
                Enumeration<java.net.InetAddress> addresses = ni.getInetAddresses();
                while (addresses.hasMoreElements()) {
                    java.net.InetAddress addr = addresses.nextElement();
                    if (!(addr instanceof Inet4Address ipv4) || ipv4.isLoopbackAddress()) {
                        continue;
                    }
                    String host = ipv4.getHostAddress();
                    if (host != null && !host.startsWith("169.254.")) {
                        return host;
                    }
                }
            }
        } catch (Exception ignored) {
            // fall through
        }
        return "127.0.0.1";
    }

    static int connectTimeoutMs() {
        return parsePositiveInt(System.getenv("GB28181_HTTP_CONNECT_TIMEOUT"), 3) * 1000;
    }

    static int readTimeoutMs() {
        return parsePositiveInt(System.getenv("GB28181_HTTP_READ_TIMEOUT"), 15) * 1000;
    }

    private static int parsePositiveInt(String raw, int defaultValue) {
        if (raw == null || raw.isBlank()) {
            return defaultValue;
        }
        try {
            return Math.max(1, Integer.parseInt(raw.trim()));
        } catch (NumberFormatException e) {
            return defaultValue;
        }
    }

    static String normalizeAuthHeader(String authorization, String xAuthorization) {
        String auth = xAuthorization != null && !xAuthorization.isBlank() ? xAuthorization.trim() : null;
        if (auth == null && authorization != null && !authorization.isBlank()) {
            auth = authorization.trim();
        }
        if (auth == null || auth.isEmpty()) {
            String jwt = trimEnv("JWT_TOKEN");
            if (jwt == null) {
                return null;
            }
            auth = jwt.toLowerCase(Locale.ROOT).startsWith("bearer ") ? jwt : "Bearer " + jwt;
        } else if (!auth.toLowerCase(Locale.ROOT).startsWith("bearer ")) {
            auth = "Bearer " + auth;
        }
        return auth;
    }
}
