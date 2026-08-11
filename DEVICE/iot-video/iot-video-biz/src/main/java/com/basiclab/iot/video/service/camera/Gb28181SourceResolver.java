package com.basiclab.iot.video.service.camera;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import javax.annotation.PostConstruct;
import java.net.URI;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Optional;
import java.util.Set;

/**
 * Mirrors retired Python {@code app.utils.gb28181_source} resolve + play URL selection.
 */
@Slf4j
@Service
public class Gb28181SourceResolver {

    private static final ObjectMapper JSON = new ObjectMapper();
    private static final TypeReference<Map<String, Object>> MAP_TYPE = new TypeReference<>() {};

    private RestTemplate restTemplate;

    @PostConstruct
    void initRestTemplate() {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(Gb28181SourceSupport.connectTimeoutMs());
        factory.setReadTimeout(Gb28181SourceSupport.playReadTimeoutMs());
        this.restTemplate = new RestTemplate(factory);
    }

    public static boolean isGb28181Source(String source) {
        return source != null && source.strip().toLowerCase(Locale.ROOT).startsWith(Gb28181SourceSupport.SOURCE_PREFIX);
    }

    public static Optional<ParsedSource> parseGb28181Source(String source) {
        if (!isGb28181Source(source)) {
            return Optional.empty();
        }
        try {
            URI uri = URI.create(source.strip());
            String deviceId = uri.getHost() != null ? uri.getHost().strip() : "";
            String path = uri.getPath() != null ? uri.getPath().strip() : "";
            String channelId = path.replaceAll("^/+", "").replaceAll("/+$", "").strip();
            if (deviceId.isEmpty() || channelId.isEmpty()) {
                return Optional.empty();
            }
            return Optional.of(new ParsedSource(deviceId, channelId));
        } catch (Exception e) {
            return Optional.empty();
        }
    }

    public static Optional<ParsedSource> parseVirtualDeviceId(String deviceId) {
        String id = deviceId != null ? deviceId.strip() : "";
        String prefix = "gb28181_";
        if (!id.startsWith(prefix)) {
            return Optional.empty();
        }
        String rest = id.substring(prefix.length());
        int split = rest.lastIndexOf('_');
        if (split <= 0 || split >= rest.length() - 1) {
            return Optional.empty();
        }
        String sipDeviceId = rest.substring(0, split).strip();
        String channelId = rest.substring(split + 1).strip();
        if (sipDeviceId.isEmpty() || channelId.isEmpty()) {
            return Optional.empty();
        }
        return Optional.of(new ParsedSource(sipDeviceId, channelId));
    }

    public String resolve(String source) {
        return resolve(source, null, null);
    }

    public String resolve(String source, String authorization, String xAuthorization) {
        Optional<ParsedSource> parsed = parseGb28181Source(source);
        if (parsed.isEmpty()) {
            return source;
        }
        String src = source.strip();
        String fixture = fixtureResolveMap().get(src);
        if (fixture != null && !fixture.isBlank()) {
            ParsedSource p = parsed.get();
            log.info("GB28181源解析成功(夹具映射): {}/{} -> {} | CAP-GB28181-SRC", p.deviceId(), p.channelId(), fixture);
            return fixture.strip();
        }

        HttpHeaders headers = new HttpHeaders();
        String auth = Gb28181SourceSupport.normalizeAuthHeader(authorization, xAuthorization);
        if (auth != null) {
            headers.set("X-Authorization", auth);
        }

        List<String> errors = new ArrayList<>();
        for (String baseUrl : Gb28181SourceSupport.candidateBases()) {
            String playUrl = buildPlayUrl(baseUrl, parsed.get().deviceId(), parsed.get().channelId());
            try {
                ResponseEntity<String> response = restTemplate.exchange(
                        playUrl,
                        HttpMethod.GET,
                        new HttpEntity<>(headers),
                        String.class
                );
                Map<String, Object> payload = JSON.readValue(response.getBody(), MAP_TYPE);
                ExtractResult result = extractStreamUrlAndMeta(payload);
                if (result.url() != null && !result.url().isBlank()) {
                    ParsedSource p = parsed.get();
                    log.info(
                            "GB28181源解析成功: {}/{} -> {} | {} (via {})",
                            p.deviceId(),
                            p.channelId(),
                            result.url(),
                            formatChoiceLog(result.url(), result.meta()),
                            baseUrl
                    );
                    return result.url();
                }
                Object wvpErr = result.meta().get("wvp_error");
                errors.add(baseUrl + ": " + (wvpErr != null ? wvpErr : "未返回可播放流地址"));
            } catch (Exception exc) {
                errors.add(baseUrl + ": " + exc.getMessage());
            }
        }

        ParsedSource p = parsed.get();
        log.error("GB28181源解析失败: {}/{}, errors={}", p.deviceId(), p.channelId(), String.join("; ", errors));
        return null;
    }

    static Map<String, String> fixtureResolveMap() {
        String raw = trimEnv("GB28181_FIXTURE_MAP");
        if (raw == null) {
            return Map.of();
        }
        if (raw.startsWith("{")) {
            try {
                Map<String, Object> data = JSON.readValue(raw, MAP_TYPE);
                Map<String, String> out = new LinkedHashMap<>();
                for (Map.Entry<String, Object> entry : data.entrySet()) {
                    String key = String.valueOf(entry.getKey()).strip();
                    String val = entry.getValue() != null ? String.valueOf(entry.getValue()).strip() : "";
                    if (!key.isEmpty() && !val.isEmpty()) {
                        out.put(key, val);
                    }
                }
                return out;
            } catch (Exception e) {
                return Map.of();
            }
        }
        Map<String, String> out = new LinkedHashMap<>();
        for (String part : raw.split(";")) {
            String piece = part.strip();
            if (piece.isEmpty() || !piece.contains("=")) {
                continue;
            }
            int eq = piece.indexOf('=');
            String key = piece.substring(0, eq).strip();
            String val = piece.substring(eq + 1).strip();
            if (!key.isEmpty() && !val.isEmpty()) {
                out.put(key, val);
            }
        }
        return out;
    }

    static String buildPlayUrl(String baseUrl, String deviceId, String channelId) {
        String base = baseUrl.strip().replaceAll("/+$", "");
        return base + "/play/start/" + deviceId + "/" + channelId;
    }

    static ExtractResult extractStreamUrlAndMeta(Map<String, Object> payload) {
        UnwrapResult unwrap = unwrapWvpPlayBody(payload);
        if (unwrap.body() == null) {
            Map<String, Object> meta = new LinkedHashMap<>();
            if (unwrap.error() != null) {
                meta.put("wvp_error", unwrap.error());
            }
            return new ExtractResult(null, meta);
        }
        PlayCandidates candidates = gb28181PlayCandidates(unwrap.body());
        String chosen = candidates.candidates().stream()
                .filter(url -> url != null && !url.isBlank())
                .findFirst()
                .orElse(null);
        Map<String, Object> meta = new LinkedHashMap<>(candidates.meta());
        if (unwrap.error() != null) {
            meta.put("wvp_error", unwrap.error());
        }
        return new ExtractResult(chosen, meta);
    }

    private static UnwrapResult unwrapWvpPlayBody(Map<String, Object> payload) {
        if (payload == null || payload.isEmpty()) {
            return new UnwrapResult(null, "invalid payload");
        }
        Object dataObj = payload.get("data");
        Map<String, Object> body = dataObj instanceof Map<?, ?> dataMap
                ? castMap(dataMap)
                : payload;
        if (body == null || body.isEmpty()) {
            return new UnwrapResult(null, "empty play response");
        }

        Object innerCode = body.get("code");
        if (innerCode != null) {
            int code = parseInt(innerCode, Integer.MIN_VALUE);
            if (code != Integer.MIN_VALUE && code != 0 && code != 200) {
                String msg = body.get("msg") != null ? String.valueOf(body.get("msg")).strip() : ("WVP play code=" + code);
                return new UnwrapResult(null, msg);
            }
        }

        Object nested = body.get("data");
        if (nested instanceof Map<?, ?> nestedMap && !allPlayUrlsFromBody(castMap(nestedMap)).isEmpty()) {
            return new UnwrapResult(castMap(nestedMap), null);
        }
        if (!allPlayUrlsFromBody(body).isEmpty()) {
            return new UnwrapResult(body, null);
        }
        return new UnwrapResult(null, null);
    }

    static PlayCandidates gb28181PlayCandidates(Map<String, Object> body) {
        List<String> flvBlock = List.of(
                str(body.get("flv")),
                str(body.get("https_flv")),
                str(body.get("ws_flv"))
        );
        List<String> other = List.of(
                str(body.get("fmp4")),
                str(body.get("hls")),
                str(body.get("rtc")),
                str(body.get("rtcs"))
        );
        String mode = envOr("GB28181_PLAY_PROTOCOL", "rtmp_first").toLowerCase(Locale.ROOT);
        boolean hevcRtspFirst = !isDisabledEnv("GB28181_HEVC_RTSP_FIRST", true);
        boolean hevcHint = bodySuggestsHevcRtmp(body);

        Map<String, Object> meta = new LinkedHashMap<>();
        meta.put("play_protocol", mode);
        meta.put("hevc_rtsp_first_env_on", hevcRtspFirst);
        meta.put("hevc_hint", hevcHint);
        meta.put("branch", "rtmp_first");

        List<String> candidates;
        if (mode.equals("rtsp_first") || mode.equals("rtsp") || mode.equals("legacy")) {
            meta.put("branch", "rtsp_first");
            candidates = concat(
                    body.get("rtsp"), body.get("rtsps"), body.get("rtmp"), body.get("rtmps"),
                    flvBlock, other
            );
        } else if (hevcRtspFirst && hevcHint) {
            meta.put("branch", "hevc_rtsp_first");
            candidates = concat(
                    body.get("rtsp"), body.get("rtsps"), body.get("rtmp"), body.get("rtmps"),
                    flvBlock, other
            );
        } else {
            candidates = concat(
                    body.get("rtmp"), body.get("rtmps"), body.get("rtsp"), body.get("rtsps"),
                    flvBlock, other
            );
        }
        return new PlayCandidates(candidates, meta);
    }

    private static boolean bodySuggestsHevcRtmp(Map<String, Object> body) {
        for (String key : List.of("rtmp", "rtmps")) {
            Object value = body.get(key);
            if (!(value instanceof String url) || url.isBlank()) {
                continue;
            }
            String lower = url.toLowerCase(Locale.ROOT);
            if (lower.contains("h265") || lower.contains("hevc")) {
                return true;
            }
        }
        return false;
    }

    private static List<String> allPlayUrlsFromBody(Map<String, Object> body) {
        if (body == null || body.isEmpty()) {
            return List.of();
        }
        Set<String> seen = new java.util.LinkedHashSet<>();
        List<String> out = new ArrayList<>();
        for (String key : List.of(
                "rtmp", "rtmps", "rtsp", "rtsps",
                "flv", "https_flv", "ws_flv",
                "fmp4", "hls", "rtc", "rtcs"
        )) {
            Object val = body.get(key);
            if (!(val instanceof String url)) {
                continue;
            }
            String trimmed = url.strip();
            if (!trimmed.isEmpty() && seen.add(trimmed)) {
                out.add(trimmed);
            }
        }
        return out;
    }

    private static String formatChoiceLog(String chosenUrl, Map<String, Object> meta) {
        String scheme = "";
        try {
            scheme = URI.create(chosenUrl).getScheme();
            if (scheme != null) {
                scheme = scheme.toLowerCase(Locale.ROOT);
            }
        } catch (Exception ignored) {
            // keep empty
        }
        String branch = String.valueOf(meta.getOrDefault("branch", ""));
        String branchTip = switch (branch) {
            case "rtsp_first" -> "接口顺序优先RTSP";
            case "rtmp_first" -> "接口顺序优先RTMP(占读者保活)";
            case "hevc_rtsp_first" -> "HEVC+RTMP线索则优先RTSP(OpenCV兼容)";
            default -> branch;
        };
        String hevcOn = Boolean.TRUE.equals(meta.get("hevc_rtsp_first_env_on")) ? "开启" : "关闭";
        String hint = Boolean.TRUE.equals(meta.get("hevc_hint")) ? "是" : "否";
        return String.format(
                Locale.ROOT,
                "选用=%s | %s | PLAY_PROTOCOL=%s | HEVC线索=%s | HEVC_RTSP_FIRST=%s",
                scheme.isEmpty() ? "?" : scheme,
                branchTip,
                meta.get("play_protocol"),
                hint,
                hevcOn
        );
    }

    private static List<String> concat(Object first, Object second, Object third, Object fourth,
                                       List<String> block, List<String> other) {
        List<String> out = new ArrayList<>();
        for (Object value : List.of(first, second, third, fourth)) {
            String text = str(value);
            if (!text.isEmpty()) {
                out.add(text);
            }
        }
        for (String value : block) {
            if (!value.isEmpty()) {
                out.add(value);
            }
        }
        for (String value : other) {
            if (!value.isEmpty()) {
                out.add(value);
            }
        }
        return out;
    }

    @SuppressWarnings("unchecked")
    private static Map<String, Object> castMap(Map<?, ?> map) {
        return (Map<String, Object>) map;
    }

    private static String str(Object value) {
        return value != null ? String.valueOf(value).strip() : "";
    }

    private static String trimEnv(String key) {
        String value = System.getenv(key);
        if (value == null) {
            return null;
        }
        String trimmed = value.strip();
        return trimmed.isEmpty() ? null : trimmed;
    }

    private static String envOr(String key, String defaultValue) {
        String value = trimEnv(key);
        return value != null ? value : defaultValue;
    }

    private static boolean isDisabledEnv(String key, boolean defaultEnabled) {
        String raw = trimEnv(key);
        if (raw == null) {
            return !defaultEnabled;
        }
        return raw.toLowerCase(Locale.ROOT).matches("0|false|no|off");
    }

    private static int parseInt(Object value, int defaultValue) {
        if (value instanceof Number number) {
            return number.intValue();
        }
        if (value == null) {
            return defaultValue;
        }
        try {
            return Integer.parseInt(String.valueOf(value));
        } catch (NumberFormatException e) {
            return defaultValue;
        }
    }

    public record ParsedSource(String deviceId, String channelId) {
    }

    private record ExtractResult(String url, Map<String, Object> meta) {
    }

    private record UnwrapResult(Map<String, Object> body, String error) {
    }

    private record PlayCandidates(List<String> candidates, Map<String, Object> meta) {
    }
}
