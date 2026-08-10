package com.basiclab.iot.video.service.camera.hardware;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.net.InetSocketAddress;
import java.net.Socket;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Slf4j
@Service
@RequiredArgsConstructor
public class HikScanService {

    private static final String DEVICE_INFO_PATH = "/ISAPI/System/deviceInfo";
    private static final String INPUT_PROXY_CHANNELS = "/ISAPI/ContentMgmt/InputProxy/channels";
    private static final String INPUT_PROXY_STATUS = "/ISAPI/ContentMgmt/InputProxy/channels/status";
    private static final String VIDEO_INPUT_CHANNELS = "/ISAPI/System/Video/inputs/channels";
    private static final Pattern GENERIC_CAMERA_NAME = Pattern.compile("^camera\\s*0*\\d+\\s*$", Pattern.CASE_INSENSITIVE);

    private final IsapiHttpClient isapiHttpClient;

    public List<Map<String, Object>> scanSegment(
            String targetsRaw,
            String portsSpec,
            String username,
            String password,
            List<Map<String, Object>> credentials,
            int concurrency,
            double timeoutSeconds,
            boolean onlyHits,
            boolean nvrOnly,
            boolean excludeNvr) {
        List<String> targets = parseTargets(targetsRaw);
        List<Integer> ports = parsePorts(portsSpec);
        if (targets.isEmpty()) {
            throw new IllegalArgumentException("解析后目标列表为空，请填写有效网段或 IP");
        }
        List<IsapiHttpClient.Credential> creds = IsapiHttpClient.parseCredentials(username, password, credentials);
        int workers = Math.max(1, Math.min(concurrency, 2000));
        ExecutorService executor = Executors.newFixedThreadPool(workers);
        try {
            List<CompletableFuture<Map<String, Object>>> futures = new ArrayList<>();
            for (String ip : targets) {
                for (int port : ports) {
                    futures.add(CompletableFuture.supplyAsync(
                            () -> probeEndpoint(ip, port, creds, timeoutSeconds, onlyHits),
                            executor));
                }
            }
            List<Map<String, Object>> devices = new ArrayList<>();
            for (CompletableFuture<Map<String, Object>> future : futures) {
                try {
                    Map<String, Object> row = future.get((long) (timeoutSeconds * 1000) + 2000, TimeUnit.MILLISECONDS);
                    if (row != null) {
                        devices.add(row);
                    }
                } catch (Exception ignored) {
                }
            }
            return aggregateByIp(devices, nvrOnly, excludeNvr);
        } finally {
            executor.shutdownNow();
        }
    }

    public Map<String, Object> enumerateNvrChannels(
            String ip,
            int port,
            String username,
            String password,
            List<Map<String, Object>> credentials,
            double timeoutSeconds,
            String vendor,
            boolean probeCameras,
            boolean onlyMounted) {
        List<IsapiHttpClient.Credential> creds = IsapiHttpClient.parseCredentials(username, password, credentials);
        if (creds.isEmpty()) {
            throw new IllegalArgumentException("枚举 NVR 通道需要至少一组用户名和密码");
        }
        String scheme = IsapiHttpClient.schemeForPort(port);
        String baseUrl = scheme + "://" + ip + ":" + port;
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("nvr_ip", ip);
        result.put("nvr_port", port);
        result.put("scheme", scheme);
        result.put("scanned_at", Instant.now().toString());
        result.put("channels", List.of());

        IsapiHttpClient.Result info = isapiHttpClient.get(baseUrl, DEVICE_INFO_PATH, creds, timeoutSeconds);
        if (info.usedCredential() != null) {
            result.put("auth_username", info.usedCredential().username());
        }
        if (info.ok()) {
            result.put("nvr_model", IsapiHttpClient.xmlText(info.body(), "model"));
            result.put("nvr_serial", IsapiHttpClient.xmlText(info.body(), "serialNumber"));
            result.put("nvr_firmware", IsapiHttpClient.xmlText(info.body(), "firmwareVersion"));
            result.put("nvr_device_name", IsapiHttpClient.xmlText(info.body(), "deviceName"));
            result.put("nvr_device_type", IsapiHttpClient.xmlText(info.body(), "deviceType"));
            result.put("nvr_vendor", "hikvision");
        } else {
            result.put("error", info.error() != null ? info.error() : "unable to detect NVR vendor (need valid -c credentials)");
            return result;
        }

        List<Map<String, Object>> rows = fetchHikvisionChannels(baseUrl, creds, timeoutSeconds);
        if (onlyMounted) {
            rows = rows.stream().filter(this::isMountedChannelRow).toList();
        }
        result.put("channels", rows);
        if (rows.isEmpty()) {
            result.put("error", "未枚举到可登记通道，请确认 NVR 已添加摄像头且凭证正确");
        }
        return result;
    }

    private List<Map<String, Object>> fetchHikvisionChannels(String baseUrl, List<IsapiHttpClient.Credential> creds, double timeoutSeconds) {
        for (String path : List.of(INPUT_PROXY_CHANNELS, VIDEO_INPUT_CHANNELS)) {
            IsapiHttpClient.Result channels = isapiHttpClient.get(baseUrl, path, creds, timeoutSeconds);
            if (!channels.ok()) {
                continue;
            }
            List<Map<String, Object>> rows = parseChannelBlocks(channels.body());
            IsapiHttpClient.Result status = isapiHttpClient.get(baseUrl, INPUT_PROXY_STATUS, creds, timeoutSeconds);
            if (status.ok()) {
                rows = mergeChannelStatus(rows, status.body());
            }
            if (!rows.isEmpty()) {
                return rows;
            }
        }
        return List.of();
    }

    private Map<String, Object> probeEndpoint(String ip, int port, List<IsapiHttpClient.Credential> creds,
                                              double timeoutSeconds, boolean onlyHits) {
        if (!tcpOpen(ip, port, timeoutSeconds)) {
            return onlyHits ? null : emptyDeviceRow(ip, port, "port closed");
        }
        String scheme = IsapiHttpClient.schemeForPort(port);
        String baseUrl = scheme + "://" + ip + ":" + port;
        IsapiHttpClient.Result info = isapiHttpClient.get(baseUrl, DEVICE_INFO_PATH, creds, timeoutSeconds);
        if (!info.ok()) {
            return onlyHits ? null : emptyDeviceRow(ip, port, info.error());
        }
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("ip", ip);
        row.put("port", port);
        row.put("scheme", scheme);
        row.put("vendor", "hikvision");
        row.put("vendor_label", "海康");
        row.put("device_role", "nvr");
        row.put("role_label", "NVR");
        row.put("is_nvr", true);
        row.put("is_recognized", true);
        row.put("confidence", 90);
        row.put("model", IsapiHttpClient.xmlText(info.body(), "model"));
        row.put("serial", IsapiHttpClient.xmlText(info.body(), "serialNumber"));
        row.put("firmware", IsapiHttpClient.xmlText(info.body(), "firmwareVersion"));
        row.put("device_name", IsapiHttpClient.xmlText(info.body(), "deviceName"));
        row.put("device_type", IsapiHttpClient.xmlText(info.body(), "deviceType"));
        row.put("mac", IsapiHttpClient.xmlText(info.body(), "macAddress"));
        row.put("url", baseUrl);
        if (info.usedCredential() != null) {
            row.put("auth_username", info.usedCredential().username());
        }
        return row;
    }

    private static Map<String, Object> emptyDeviceRow(String ip, int port, String error) {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("ip", ip);
        row.put("port", port);
        row.put("is_recognized", false);
        row.put("error", error);
        return row;
    }

    private List<Map<String, Object>> aggregateByIp(List<Map<String, Object>> devices, boolean nvrOnly, boolean excludeNvr) {
        Map<String, List<Map<String, Object>>> byIp = new LinkedHashMap<>();
        for (Map<String, Object> device : devices) {
            String ip = String.valueOf(device.getOrDefault("ip", ""));
            byIp.computeIfAbsent(ip, ignored -> new ArrayList<>()).add(device);
        }
        List<Map<String, Object>> rows = new ArrayList<>();
        for (Map.Entry<String, List<Map<String, Object>>> entry : byIp.entrySet()) {
            List<Map<String, Object>> group = new ArrayList<>(entry.getValue());
            group.sort(Comparator.comparingInt(d -> ((Number) d.getOrDefault("port", 0)).intValue()));
            Map<String, Object> primary = group.stream().filter(d -> Boolean.TRUE.equals(d.get("is_recognized"))).findFirst().orElse(group.get(0));
            Map<String, Object> row = new LinkedHashMap<>(primary);
            row.put("ports", group.stream().map(d -> d.get("port")).toList());
            row.put("devices", group);
            boolean isNvr = Boolean.TRUE.equals(primary.get("is_nvr"));
            if (nvrOnly && !isNvr) {
                continue;
            }
            if (excludeNvr && isNvr) {
                continue;
            }
            rows.add(row);
        }
        return rows;
    }

    private List<Map<String, Object>> parseChannelBlocks(String xml) {
        List<Map<String, Object>> rows = new ArrayList<>();
        for (String tag : List.of("InputProxyChannel", "VideoInputChannel", "InputProxyChannelStatus")) {
            Matcher matcher = Pattern.compile("<" + tag + "\\b[^>]*>(.*?)</" + tag + ">", Pattern.CASE_INSENSITIVE | Pattern.DOTALL)
                    .matcher(xml);
            while (matcher.find()) {
                Map<String, Object> row = parseChannelBlock(matcher.group(1));
                if (row.get("channel_id") instanceof Integer id && id > 0) {
                    rows.add(row);
                }
            }
            if (!rows.isEmpty()) {
                break;
            }
        }
        return rows;
    }

    private Map<String, Object> parseChannelBlock(String block) {
        Map<String, Object> row = new LinkedHashMap<>();
        String channelIdRaw = firstXml(block, "id", "videoInputChannelID", "srcInputPort", "inputPort");
        int channelId = 0;
        try {
            channelId = channelIdRaw != null ? Integer.parseInt(channelIdRaw) : 0;
        } catch (NumberFormatException ignored) {
        }
        row.put("channel_id", channelId);
        String cameraIp = firstXml(block, "ipAddress");
        row.put("ip", cameraIp);
        row.put("camera_ip", cameraIp);
        String rawName = firstXml(block, "name", "channelName");
        row.put("name", effectiveChannelName(rawName, channelId, cameraIp));
        String portRaw = firstXml(block, "managePortNo", "srcInputPort");
        row.put("port", parseIntOrNull(portRaw));
        row.put("camera_port", row.get("port"));
        row.put("protocol", firstXml(block, "proxyProtocol"));
        row.put("username", firstXml(block, "userName"));
        row.put("device_id", firstXml(block, "deviceID"));
        row.put("stream_type", firstXml(block, "streamType"));
        String onlineRaw = firstXml(block, "online");
        if (onlineRaw != null) {
            row.put("online", "true".equalsIgnoreCase(onlineRaw));
        }
        String enabledRaw = firstXml(block, "enabled");
        if (enabledRaw != null) {
            row.put("enabled", "true".equalsIgnoreCase(enabledRaw));
        }
        row.put("connection_status", firstXml(block, "chanDetectResult"));
        row.put("vendor", "hikvision");
        return row;
    }

    private List<Map<String, Object>> mergeChannelStatus(List<Map<String, Object>> channels, String statusXml) {
        Map<Integer, Map<String, Object>> statusById = new LinkedHashMap<>();
        for (Map<String, Object> row : parseChannelBlocks(statusXml)) {
            Object cid = row.get("channel_id");
            if (cid instanceof Integer id) {
                statusById.put(id, row);
            }
        }
        List<Map<String, Object>> merged = new ArrayList<>();
        for (Map<String, Object> channel : channels) {
            Map<String, Object> row = new LinkedHashMap<>(channel);
            Object cid = channel.get("channel_id");
            if (cid instanceof Integer id) {
                Map<String, Object> status = statusById.get(id);
                if (status != null) {
                    for (String key : List.of("online", "enabled", "connection_status", "ip", "port", "protocol", "username", "device_id")) {
                        if (status.get(key) != null) {
                            row.put(key, status.get(key));
                        }
                    }
                }
            }
            merged.add(row);
        }
        return merged;
    }

    private boolean isMountedChannelRow(Map<String, Object> row) {
        if (Boolean.FALSE.equals(row.get("online"))) {
            return false;
        }
        String conn = String.valueOf(row.getOrDefault("connection_status", "")).toLowerCase(Locale.ROOT);
        if (!conn.isBlank() && (conn.contains("offline") || conn.contains("disconnect") || conn.contains("netunreachable"))) {
            return false;
        }
        String ip = String.valueOf(row.getOrDefault("ip", row.getOrDefault("camera_ip", ""))).trim();
        if (!ip.isBlank()) {
            return true;
        }
        return !String.valueOf(row.getOrDefault("device_id", "")).trim().isBlank();
    }

    private static String effectiveChannelName(String rawName, int channelId, String cameraIp) {
        String name = rawName != null ? rawName.trim() : "";
        if (!name.isBlank() && !GENERIC_CAMERA_NAME.matcher(name).matches()) {
            return name;
        }
        if (cameraIp != null && !cameraIp.isBlank()) {
            return "CH" + channelId + "-" + cameraIp;
        }
        return "CH" + channelId;
    }

    private static boolean tcpOpen(String ip, int port, double timeoutSeconds) {
        try (Socket socket = new Socket()) {
            socket.connect(new InetSocketAddress(ip, port), (int) (timeoutSeconds * 1000));
            return true;
        } catch (Exception ex) {
            return false;
        }
    }

    static List<String> parseTargets(String raw) {
        Set<String> targets = new LinkedHashSet<>();
        for (String part : raw.split("[,\\s;]+")) {
            String token = part.trim();
            if (token.isEmpty()) {
                continue;
            }
            if (token.contains("/")) {
                targets.addAll(expandCidr(token));
            } else if (token.contains("-")) {
                targets.addAll(expandRange(token));
            } else {
                targets.add(token);
            }
        }
        return new ArrayList<>(targets);
    }

    static List<Integer> parsePorts(String portsSpec) {
        Set<Integer> ports = new LinkedHashSet<>();
        for (String part : portsSpec.split(",")) {
            String token = part.trim();
            if (token.isEmpty()) {
                continue;
            }
            ports.add(Integer.parseInt(token));
        }
        return ports.isEmpty() ? List.of(80, 443, 8000, 8443) : new ArrayList<>(ports);
    }

    private static List<String> expandCidr(String cidr) {
        String[] parts = cidr.split("/");
        if (parts.length != 2) {
            return List.of(cidr);
        }
        String[] octets = parts[0].split("\\.");
        if (octets.length != 4) {
            return List.of(parts[0]);
        }
        int prefix = Integer.parseInt(parts[1]);
        if (prefix < 24) {
            throw new IllegalArgumentException("暂仅支持 /24 及以上网段，请缩小扫描范围");
        }
        int base = (Integer.parseInt(octets[0]) << 24)
                | (Integer.parseInt(octets[1]) << 16)
                | (Integer.parseInt(octets[2]) << 8);
        int hostBits = 32 - prefix;
        int count = Math.min(1 << hostBits, 256);
        List<String> ips = new ArrayList<>();
        for (int i = 1; i < count - 1; i++) {
            int value = base + i;
            ips.add(((value >> 24) & 0xFF) + "." + ((value >> 16) & 0xFF) + "." + ((value >> 8) & 0xFF) + "." + (value & 0xFF));
        }
        return ips;
    }

    private static List<String> expandRange(String token) {
        String[] bounds = token.split("-");
        if (bounds.length != 2) {
            return List.of(token);
        }
        String[] start = bounds[0].trim().split("\\.");
        String[] end = bounds[1].trim().split("\\.");
        if (start.length != 4 || end.length != 4) {
            return List.of(bounds[0].trim());
        }
        int startLast = Integer.parseInt(start[3]);
        int endLast = Integer.parseInt(end[3]);
        List<String> ips = new ArrayList<>();
        String prefix = start[0] + "." + start[1] + "." + start[2] + ".";
        for (int i = startLast; i <= endLast; i++) {
            ips.add(prefix + i);
        }
        return ips;
    }

    private static String firstXml(String block, String... tags) {
        for (String tag : tags) {
            String value = IsapiHttpClient.xmlText(block, tag);
            if (value != null && !value.isBlank()) {
                return value;
            }
        }
        return null;
    }

    private static Integer parseIntOrNull(String raw) {
        if (raw == null || raw.isBlank()) {
            return null;
        }
        try {
            return Integer.parseInt(raw);
        } catch (NumberFormatException ex) {
            return null;
        }
    }
}
