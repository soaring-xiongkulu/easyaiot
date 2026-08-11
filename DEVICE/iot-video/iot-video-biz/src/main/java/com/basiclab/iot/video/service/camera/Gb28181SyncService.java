package com.basiclab.iot.video.service.camera;

import com.basiclab.iot.video.dal.DeviceDirectoryRepository;
import com.basiclab.iot.video.dal.DeviceRepository;
import com.basiclab.iot.video.domain.DeviceRow;
import com.basiclab.iot.video.exception.VideoBusinessException;
import com.basiclab.iot.video.service.StreamUrlSupport;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.util.UriComponentsBuilder;

import javax.annotation.PostConstruct;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;

/**
 * Mirrors retired Python {@code app.services.gb28181_sync_service}.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class Gb28181SyncService {

    private final DeviceRepository deviceRepository;
    private final DeviceDirectoryRepository directoryRepository;
    private final StreamUrlSupport streamUrlSupport;
    private RestTemplate restTemplate;

    @PostConstruct
    void initRestTemplate() {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(Gb28181SourceSupport.connectTimeoutMs());
        factory.setReadTimeout(Gb28181SourceSupport.readTimeoutMs());
        this.restTemplate = new RestTemplate(factory);
    }

    public void ensureDirectoryLayout() {
        try {
            syncUnassignedDevicesToDefaultDirectory();
        } catch (Exception e) {
            log.warn("未分组设备归入默认目录失败: {}", e.getMessage());
        }
    }

    public Map<String, Object> syncFromWvp(boolean strict, String authorization, String xAuthorization) {
        List<String> apiRoots = Gb28181SourceSupport.queryApiRoots(Gb28181SourceSupport.candidateBases());
        Map<String, Object> stats = new LinkedHashMap<>();
        stats.put("created", 0);
        stats.put("wvp_device_count", 0);
        stats.put("channels_seen", 0);
        stats.put("api_base", null);
        stats.put("errors", new ArrayList<String>());
        stats.put("upsert_errors", new ArrayList<String>());

        if (apiRoots.isEmpty()) {
            String msg = "未配置国标服务地址，请设置 GATEWAY_URL（如 http://127.0.0.1:48080）"
                    + " 或 GB28181_SERVICE_URL（如 http://127.0.0.1:48088/api）";
            log.warn(msg);
            appendError(stats, msg);
            if (strict) {
                throw new VideoBusinessException(500, msg);
            }
            return stats;
        }

        HttpHeaders headers = buildHeaders(authorization, xAuthorization);
        List<String> fetchErrors = new ArrayList<>();
        List<Map<String, Object>> gbDevices = List.of();
        String apiRoot = null;

        for (String root : apiRoots) {
            try {
                List<Map<String, Object>> batch = fetchJsonList(root + "/devices", headers,
                        Map.of("page", 1, "count", 10000));
                if (!batch.isEmpty()) {
                    gbDevices = batch;
                    apiRoot = root;
                    break;
                }
                fetchErrors.add(root + ": 设备列表为空");
            } catch (Exception e) {
                fetchErrors.add(root + ": " + e.getMessage());
            }
        }

        stats.put("errors", fetchErrors);
        stats.put("api_base", apiRoot);

        if (gbDevices.isEmpty()) {
            String msg = "拉取国标设备列表失败或列表为空";
            if (!fetchErrors.isEmpty()) {
                msg = msg + "（" + String.join("; ", fetchErrors) + "）";
            }
            log.warn(msg);
            if (fetchErrors.isEmpty()) {
                appendError(stats, msg);
            }
            if (strict) {
                throw new VideoBusinessException(500, msg);
            }
            return stats;
        }

        int defaultDirId = directoryRepository.ensureDefaultDirectory();
        int created = 0;
        int channelsSeen = 0;

        for (Map<String, Object> gbDev : gbDevices) {
            String sipId = firstNonBlank(
                    gbDev.get("deviceId"),
                    gbDev.get("deviceIdentification"),
                    gbDev.get("id")
            );
            if (sipId == null || apiRoot == null) {
                continue;
            }

            List<Map<String, Object>> channels;
            try {
                channels = fetchJsonList(apiRoot + "/devices/" + sipId + "/channels", headers,
                        Map.of("page", 1, "count", 10000));
            } catch (Exception e) {
                log.debug("拉取国标设备 {} 通道失败: {}", sipId, e.getMessage());
                channels = List.of();
            }

            int channelCount = parseInt(gbDev.get("channelCount"), 0);
            if (channels.isEmpty() && channelCount > 0) {
                triggerWvpChannelSync(apiRoot, sipId, headers);
                try {
                    channels = fetchJsonList(apiRoot + "/devices/" + sipId + "/channels", headers,
                            Map.of("page", 1, "count", 10000));
                } catch (Exception e) {
                    log.debug("WVP 通道同步后重拉 {} 失败: {}", sipId, e.getMessage());
                }
            }

            for (Map<String, Object> ch : channels) {
                NormalizedChannel normalized = normalizeChannel(ch, sipId);
                if (normalized == null) {
                    continue;
                }
                channelsSeen++;
                try {
                    if (upsertGbDevice(normalized, defaultDirId, extractLocation(ch))) {
                        created++;
                    }
                } catch (Exception e) {
                    String err = normalized.parentId() + "/" + normalized.channelId() + ": " + e.getMessage();
                    log.warn("同步国标通道失败 {}", err);
                    appendUpsertError(stats, err);
                }
            }
        }

        syncUnassignedDevicesToDefaultDirectory();
        stats.put("created", created);
        stats.put("wvp_device_count", gbDevices.size());
        stats.put("channels_seen", channelsSeen);
        if (created > 0) {
            log.info("国标通道同步完成，新增 {} 个，WVP 设备 {} 个，通道 {} 条",
                    created, gbDevices.size(), channelsSeen);
        }
        return stats;
    }

    public Map<String, Object> syncFromPayload(List<?> channels, boolean strict) {
        Map<String, Object> stats = new LinkedHashMap<>();
        stats.put("created", 0);
        stats.put("wvp_device_count", 0);
        stats.put("channels_seen", 0);
        stats.put("api_base", "frontend-wvp");
        stats.put("errors", new ArrayList<String>());
        stats.put("upsert_errors", new ArrayList<String>());

        if (channels == null || channels.isEmpty()) {
            String msg = "未收到国标通道数据";
            appendError(stats, msg);
            if (strict) {
                throw new VideoBusinessException(500, msg);
            }
            return stats;
        }

        int defaultDirId = directoryRepository.ensureDefaultDirectory();
        int created = 0;
        int channelsSeen = 0;
        java.util.Set<String> sipIds = new java.util.LinkedHashSet<>();

        for (Object item : channels) {
            if (!(item instanceof Map<?, ?> raw)) {
                continue;
            }
            @SuppressWarnings("unchecked")
            Map<String, Object> channel = (Map<String, Object>) raw;
            String sip = firstNonBlank(
                    channel.get("sipDeviceId"),
                    channel.get("sip_device_id"),
                    channel.get("deviceIdentification")
            );
            String chId = firstNonBlank(
                    channel.get("channelId"),
                    channel.get("channel_id"),
                    channel.get("gbDeviceId")
            );
            String name = str(channel.get("name"));
            if (name.isEmpty()) {
                name = str(channel.get("channelName"));
            }
            if (name.isEmpty()) {
                name = chId != null ? chId : "";
            }
            if (sip == null || chId == null) {
                continue;
            }
            sipIds.add(sip);
            channelsSeen++;
            try {
                NormalizedChannel normalized = new NormalizedChannel(sip, chId, name);
                if (upsertGbDevice(normalized, defaultDirId, extractLocation(channel))) {
                    created++;
                }
            } catch (Exception e) {
                String err = sip + "/" + chId + ": " + e.getMessage();
                log.warn("同步国标通道失败 {}", err);
                appendUpsertError(stats, err);
            }
        }

        syncUnassignedDevicesToDefaultDirectory();
        stats.put("created", created);
        stats.put("channels_seen", channelsSeen);
        stats.put("wvp_device_count", sipIds.size());
        if (created > 0) {
            log.info("国标通道（前端 WVP）同步完成，新增 {}", created);
        }
        return stats;
    }

    public int backfillAiStreamUrls() {
        int updated = 0;
        for (DeviceRow device : deviceRepository.listBySourcePrefix(Gb28181SourceSupport.SOURCE_PREFIX)) {
            boolean needAi = isBlank(device.getAiRtmpStream()) || isBlank(device.getAiHttpStream());
            if (!needAi) {
                continue;
            }
            String[] urls = streamUrlSupport.gb28181DeviceStreamUrls(device.getId());
            Map<String, Object> fields = new LinkedHashMap<>();
            if (isBlank(device.getAiRtmpStream())) {
                fields.put("ai_rtmp_stream", urls[2]);
            }
            if (isBlank(device.getAiHttpStream())) {
                fields.put("ai_http_stream", urls[3]);
            }
            deviceRepository.updateFields(device.getId(), fields);
            updated++;
        }
        if (updated > 0) {
            log.info("国标设备 AI 推流地址回填完成，更新 {} 条", updated);
        }
        return updated;
    }

    public long countGbDevices() {
        return deviceRepository.countBySourcePrefix(Gb28181SourceSupport.SOURCE_PREFIX);
    }

    public DeviceRow ensureGb28181VirtualDevice(String deviceId, String name) {
        Optional<Gb28181SourceResolver.ParsedSource> parsed =
                Gb28181SourceResolver.parseVirtualDeviceId(deviceId);
        if (parsed.isEmpty()) {
            throw new VideoBusinessException(400, "无效的国标虚拟设备 ID: " + deviceId);
        }
        return deviceRepository.findById(deviceId).orElseGet(() -> {
            int defaultDirId = directoryRepository.ensureDefaultDirectory();
            Gb28181SourceResolver.ParsedSource channel = parsed.get();
            String displayName = (name != null && !name.isBlank())
                    ? name.strip()
                    : (channel.channelId() != null ? channel.channelId() : deviceId);
            NormalizedChannel normalized = new NormalizedChannel(
                    channel.deviceId(),
                    channel.channelId(),
                    displayName
            );
            upsertGbDevice(normalized, defaultDirId, Location.empty());
            return deviceRepository.findById(deviceId)
                    .orElseThrow(() -> new VideoBusinessException(500, "创建国标设备 " + deviceId + " 失败"));
        });
    }

    public String buildSyncMessage(Map<String, Object> stats) {
        int wvpCount = toInt(stats.get("wvp_device_count"));
        int channelsSeen = toInt(stats.get("channels_seen"));
        long totalGb = countGbDevices();
        if (wvpCount > 0 && totalGb == 0) {
            return "WVP 发现 " + wvpCount + " 个国标设备、解析 " + channelsSeen
                    + " 个通道，但未写入设备库，请检查 VIDEO 日志与数据库";
        }
        if (wvpCount == 0) {
            return "未从 WVP 拉取到国标设备，请检查 GATEWAY_URL / GB28181_SERVICE_URL 与 WVP 服务";
        }
        return "国标设备同步成功";
    }

    public Map<String, Object> buildSyncResponse(Map<String, Object> stats) {
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("created", toInt(stats.get("created")));
        data.put("total_gb_devices", countGbDevices());
        data.put("wvp_device_count", toInt(stats.get("wvp_device_count")));
        data.put("channels_seen", toInt(stats.get("channels_seen")));
        data.put("api_base", stats.get("api_base"));
        data.put("upsert_errors", stats.getOrDefault("upsert_errors", List.of()));
        return data;
    }

    private void syncUnassignedDevicesToDefaultDirectory() {
        int defaultDirId = directoryRepository.ensureDefaultDirectory();
        deviceRepository.assignUnassignedToDefaultDirectory(defaultDirId);
    }

    private boolean upsertGbDevice(NormalizedChannel channel, int defaultDirId, Location location) {
        String mappedId = Gb28181SourceSupport.virtualDeviceId(channel.parentId(), channel.channelId());
        String source = Gb28181SourceSupport.buildSource(channel.parentId(), channel.channelId());
        String[] streams = streamUrlSupport.gb28181DeviceStreamUrls(mappedId);

        return deviceRepository.findById(mappedId).map(existing -> {
            Map<String, Object> fields = new LinkedHashMap<>();
            if (!Objects.equals(existing.getName(), channel.name())) {
                fields.put("name", channel.name());
            }
            if (!Objects.equals(existing.getSource(), source)) {
                fields.put("source", source);
            }
            if (existing.getDirectoryId() == null) {
                fields.put("directory_id", defaultDirId);
            }
            if (!isBlank(existing.getRtmpStream()) || !isBlank(existing.getHttpStream())) {
                fields.put("rtmp_stream", streams[0]);
                fields.put("http_stream", streams[1]);
            }
            if (isBlank(existing.getAiRtmpStream())) {
                fields.put("ai_rtmp_stream", streams[2]);
            }
            if (isBlank(existing.getAiHttpStream())) {
                fields.put("ai_http_stream", streams[3]);
            }
            applyLocationFields(existing, location, fields);
            if (!fields.isEmpty()) {
                deviceRepository.updateFields(mappedId, fields);
            }
            return false;
        }).orElseGet(() -> {
            DeviceRow row = new DeviceRow();
            row.setId(mappedId);
            row.setName(channel.name().isEmpty() ? mappedId : channel.name());
            row.setSource(source);
            row.setRtmpStream(streams[0]);
            row.setHttpStream(streams[1]);
            row.setAiRtmpStream(streams[2]);
            row.setAiHttpStream(streams[3]);
            row.setManufacturer("GB28181");
            row.setModel("GB28181-Channel");
            row.setSerialNumber(channel.parentId());
            row.setHardwareId(channel.channelId());
            row.setNvrChannel(0);
            row.setDirectoryId(defaultDirId);
            if (location != null && location.longitude() != null && location.latitude() != null) {
                row.setLongitude(location.longitude());
                row.setLatitude(location.latitude());
                row.setAddress(location.address());
                row.setLocationSource("gb28181");
                row.setLocationUpdatedAt(Instant.now());
            }
            deviceRepository.insert(row);
            return true;
        });
    }

    private void applyLocationFields(DeviceRow device, Location location, Map<String, Object> fields) {
        if (location == null || location.isEmpty()) {
            return;
        }
        if ("manual".equals(device.getLocationSource())) {
            return;
        }
        if (location.longitude() != null && location.latitude() != null) {
            if (!Objects.equals(device.getLongitude(), location.longitude())
                    || !Objects.equals(device.getLatitude(), location.latitude())) {
                fields.put("longitude", location.longitude());
                fields.put("latitude", location.latitude());
                fields.put("location_source", "gb28181");
                fields.put("location_updated_at", java.sql.Timestamp.from(Instant.now()));
            }
        }
        if (location.address() != null && !Objects.equals(device.getAddress(), location.address())) {
            fields.put("address", location.address());
            fields.put("location_source", "gb28181");
            fields.put("location_updated_at", java.sql.Timestamp.from(Instant.now()));
        }
    }

    private Location extractLocation(Map<String, Object> item) {
        Double lng = firstCoord(item.get("gbLongitude"), item.get("longitude"));
        Double lat = firstCoord(item.get("gbLatitude"), item.get("latitude"));
        if (lng == null || lat == null) {
            Double[] pair = coordPair(item, "gbLongitude", "gbLatitude");
            if (pair == null) {
                pair = coordPair(item, "longitude", "latitude");
            }
            if (pair != null) {
                lng = pair[0];
                lat = pair[1];
            }
        }
        String address = firstNonBlank(item.get("address"), item.get("gbAddress"));
        if (lng == null && lat == null && address == null) {
            return Location.empty();
        }
        return new Location(lng, lat, address);
    }

    private Double[] coordPair(Map<String, Object> item, String lngKey, String latKey) {
        Double lng = parseDouble(item.get(lngKey));
        Double lat = parseDouble(item.get(latKey));
        if (lng == null || lat == null) {
            return null;
        }
        if (lng == 0.0 && lat == 0.0) {
            return null;
        }
        return new Double[]{lng, lat};
    }

    private Double firstCoord(Object primary, Object fallback) {
        Double value = parseDouble(primary);
        if (value != null) {
            return value;
        }
        return parseDouble(fallback);
    }

    private NormalizedChannel normalizeChannel(Map<String, Object> item, String sipDeviceId) {
        String sip = sipDeviceId.trim();
        String parent = firstNonBlank(
                item.get("parentDeviceId"),
                item.get("parentId"),
                item.get("gbParentId"),
                sip
        );
        String channelId = firstNonBlank(
                item.get("channelId"),
                item.get("deviceChannelId"),
                item.get("gbDeviceId")
        );
        if (channelId == null) {
            String devId = str(item.get("deviceId"));
            if (!devId.isEmpty() && !devId.equals(parent) && !devId.equals(sip)) {
                channelId = devId;
            }
        }
        if (channelId == null && item.get("id") != null) {
            String rawId = str(item.get("id"));
            if (!rawId.isEmpty() && !rawId.equals(parent) && !rawId.equals(sip)) {
                channelId = rawId;
            }
        }
        if (parent == null || channelId == null) {
            return null;
        }
        String name = firstNonBlank(
                item.get("name"),
                item.get("channelName"),
                item.get("deviceName"),
                item.get("gbName"),
                channelId
        );
        return new NormalizedChannel(parent, channelId, name != null ? name : channelId);
    }

    @SuppressWarnings("unchecked")
    private List<Map<String, Object>> fetchJsonList(
            String url,
            HttpHeaders headers,
            Map<String, Object> params
    ) {
        UriComponentsBuilder builder = UriComponentsBuilder.fromHttpUrl(url);
        params.forEach((key, value) -> builder.queryParam(key, value));
        HttpEntity<Void> entity = new HttpEntity<>(headers);
        ResponseEntity<Map> response = restTemplate.exchange(
                builder.toUriString(),
                HttpMethod.GET,
                entity,
                Map.class
        );
        Object body = response.getBody();
        return extractList(body);
    }

    @SuppressWarnings("unchecked")
    private List<Map<String, Object>> extractList(Object body) {
        if (body instanceof List<?> list) {
            return castMapList(list);
        }
        if (!(body instanceof Map<?, ?> map)) {
            return List.of();
        }
        Object page = map.get("data") != null ? map.get("data") : map;
        if (page instanceof List<?> list) {
            return castMapList(list);
        }
        if (page instanceof Map<?, ?> pageMap) {
            Object inner = pageMap.get("data") != null ? pageMap.get("data") : pageMap;
            if (inner instanceof List<?> list) {
                return castMapList(list);
            }
            if (inner instanceof Map<?, ?> innerMap) {
                Object rows = firstPresent(innerMap, "list", "records", "rows");
                if (rows instanceof List<?> list) {
                    return castMapList(list);
                }
            }
            Object rows = firstPresent(pageMap, "list", "records", "rows");
            if (rows instanceof List<?> list) {
                return castMapList(list);
            }
        }
        return List.of();
    }

    @SuppressWarnings("unchecked")
    private List<Map<String, Object>> castMapList(List<?> list) {
        List<Map<String, Object>> out = new ArrayList<>();
        for (Object item : list) {
            if (item instanceof Map<?, ?> map) {
                out.add((Map<String, Object>) map);
            }
        }
        return out;
    }

    private Object firstPresent(Map<?, ?> map, String... keys) {
        for (String key : keys) {
            if (map.containsKey(key) && map.get(key) != null) {
                return map.get(key);
            }
        }
        return null;
    }

    private void triggerWvpChannelSync(String apiRoot, String sipId, HttpHeaders headers) {
        try {
            restTemplate.exchange(
                    apiRoot + "/devices/" + sipId + "/sync",
                    HttpMethod.GET,
                    new HttpEntity<>(headers),
                    String.class
            );
        } catch (RestClientException e) {
            log.debug("触发 WVP 通道同步 {} 失败: {}", sipId, e.getMessage());
        }
    }

    private HttpHeaders buildHeaders(String authorization, String xAuthorization) {
        HttpHeaders headers = new HttpHeaders();
        String auth = Gb28181SourceSupport.normalizeAuthHeader(authorization, xAuthorization);
        if (auth != null) {
            headers.set("X-Authorization", auth);
        }
        return headers;
    }

    private static void appendError(Map<String, Object> stats, String msg) {
        Object current = stats.get("errors");
        if (current instanceof List<?> list) {
            @SuppressWarnings("unchecked")
            List<String> errors = (List<String>) list;
            errors.add(msg);
        }
    }

    private static void appendUpsertError(Map<String, Object> stats, String msg) {
        Object current = stats.get("upsert_errors");
        if (current instanceof List<?> list) {
            @SuppressWarnings("unchecked")
            List<String> errors = (List<String>) list;
            errors.add(msg);
        }
    }

    private static String firstNonBlank(Object... values) {
        for (Object value : values) {
            String text = str(value);
            if (!text.isEmpty()) {
                return text;
            }
        }
        return null;
    }

    private static String str(Object value) {
        return value != null ? String.valueOf(value).trim() : "";
    }

    private static boolean isBlank(String value) {
        return value == null || value.trim().isEmpty();
    }

    private static int toInt(Object value) {
        if (value instanceof Number number) {
            return number.intValue();
        }
        if (value == null) {
            return 0;
        }
        try {
            return Integer.parseInt(String.valueOf(value));
        } catch (NumberFormatException e) {
            return 0;
        }
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

    private static Double parseDouble(Object value) {
        if (value == null || "".equals(String.valueOf(value))) {
            return null;
        }
        try {
            return Double.parseDouble(String.valueOf(value));
        } catch (NumberFormatException e) {
            return null;
        }
    }

    private record NormalizedChannel(String parentId, String channelId, String name) {
    }

    private record Location(Double longitude, Double latitude, String address) {
        static Location empty() {
            return new Location(null, null, null);
        }

        boolean isEmpty() {
            return longitude == null && latitude == null && address == null;
        }
    }
}
