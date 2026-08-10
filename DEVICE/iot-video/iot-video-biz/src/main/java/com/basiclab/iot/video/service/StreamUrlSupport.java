package com.basiclab.iot.video.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.net.Inet4Address;
import java.net.NetworkInterface;
import java.util.Enumeration;
import java.util.List;
import java.util.Map;

/**
 * Device stream URL resolution — mirrors Python {@code camera_service._default_stream_urls},
 * {@code gb28181_device_stream_urls}, and {@code stream_url_sync_service.build_stream_urls_for_host}.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class StreamUrlSupport {

    private final MediaPoolClient mediaPoolClient;

    public String[] defaultStreamUrls(String deviceId) {
        if (mediaPoolClient.isMediaPoolEnabled()) {
            try {
                Map<String, Object> binding = mediaPoolClient.allocateDeviceMedia(deviceId);
                return mediaPoolClient.streamUrlsFromBinding(binding);
            } catch (Exception e) {
                log.warn("媒体节点池分配失败 device_id={}，回退本机地址: {}", deviceId, e.getMessage());
            }
        }
        return legacyLocalStreamUrls(deviceId);
    }

    public String[] gb28181DeviceStreamUrls(String deviceId) {
        if (mediaPoolClient.isMediaPoolEnabled()) {
            try {
                Map<String, Object> binding = mediaPoolClient.allocateDeviceMedia(
                        deviceId,
                        false,
                        true,
                        true,
                        null,
                        null
                );
                String[] urls = mediaPoolClient.streamUrlsFromBinding(binding);
                return new String[]{"", "", urls[2], urls[3]};
            } catch (Exception e) {
                log.warn("国标设备媒体节点池分配失败 device_id={}，回退本机地址: {}", deviceId, e.getMessage());
            }
        }
        return legacyGb28181AiStreamUrls(deviceId);
    }

    public String[] resolveDeviceStreamUrls(String deviceId, String rtmpFallback, String httpFallback,
                                            String aiRtmpFallback, String aiHttpFallback) {
        if (mediaPoolClient.isMediaPoolEnabled()) {
            try {
                Map<String, Object> binding = mediaPoolClient.getDeviceMediaBinding(deviceId);
                if (binding != null && !binding.isEmpty()) {
                    return mediaPoolClient.streamUrlsFromBinding(binding);
                }
            } catch (Exception e) {
                log.debug("媒体绑定查询失败 device_id={}: {}", deviceId, e.getMessage());
            }
        }
        return new String[]{
                rtmpFallback != null ? rtmpFallback : "",
                httpFallback != null ? httpFallback : "",
                aiRtmpFallback != null ? aiRtmpFallback : "",
                aiHttpFallback != null ? aiHttpFallback : ""
        };
    }

    public String[] buildStreamUrlsForHost(
            String host,
            String deviceId,
            Map<String, Object> tags,
            String httpPlayHost
    ) {
        int rtmpPort = tagInt(tags, "srs_rtmp_port", 1935);
        int httpPort = tagInt(tags, "srs_http_port", 8080);
        String playHost = httpPlayHost != null && !httpPlayHost.isBlank()
                ? httpPlayHost.trim()
                : firstNonBlank(trimToNull(System.getenv("MEDIA_HTTP_PLAY_HOST")), host);
        String rtmpStream = "rtmp://" + host + ":" + rtmpPort + "/live/" + deviceId;
        String httpStream = "http://" + playHost + ":" + httpPort + "/live/" + deviceId + ".flv";
        String aiRtmpStream = "rtmp://" + host + ":" + rtmpPort + "/ai/" + deviceId;
        String aiHttpStream = "http://" + playHost + ":" + httpPort + "/ai/" + deviceId + ".flv";
        return new String[]{rtmpStream, httpStream, aiRtmpStream, aiHttpStream};
    }

    public String[] legacyLocalStreamUrls(String deviceId) {
        String host = detectHostIpv4();
        return new String[]{
                "rtmp://" + host + ":1935/live/" + deviceId,
                "http://" + host + ":8080/live/" + deviceId + ".flv",
                "rtmp://" + host + ":1935/ai/" + deviceId,
                "http://" + host + ":8080/ai/" + deviceId + ".flv"
        };
    }

    private static int tagInt(Map<String, Object> tags, String key, int defaultValue) {
        if (tags == null || !tags.containsKey(key) || tags.get(key) == null) {
            return defaultValue;
        }
        try {
            return Integer.parseInt(String.valueOf(tags.get(key)).trim());
        } catch (NumberFormatException e) {
            return defaultValue;
        }
    }

    private static String firstNonBlank(String... values) {
        for (String value : values) {
            if (value != null && !value.isBlank()) {
                return value.trim();
            }
        }
        return "";
    }

    private static String trimToNull(String value) {
        if (value == null) {
            return null;
        }
        String trimmed = value.trim();
        return trimmed.isEmpty() ? null : trimmed;
    }

    private String[] legacyGb28181AiStreamUrls(String deviceId) {
        String host = detectHostIpv4();
        String aiRtmp = "rtmp://" + host + ":1935/ai/" + deviceId;
        String aiHttp = "http://" + host + ":8080/ai/" + deviceId + ".flv";
        return new String[]{"", "", aiRtmp, aiHttp};
    }

    private static String detectHostIpv4() {
        for (String key : List.of("POD_IP", "HOST_IP")) {
            String ip = trimToNull(System.getenv(key));
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
}
