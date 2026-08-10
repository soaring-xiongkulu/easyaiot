package com.basiclab.iot.video.service.camera.hardware;

import lombok.extern.slf4j.Slf4j;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.TreeSet;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * 大华 NVR CGI 通道枚举（对照 Python {@code hiktools/core/nvr.py} + {@code dahua_cgi.py}）。
 */
@Slf4j
public final class DahuaNvrSupport {

    private static final String DAHUA_DEVICE_CLASS = "/cgi-bin/magicBox.cgi?action=getDeviceClass";
    private static final String DAHUA_SYSTEM_INFO = "/cgi-bin/magicBox.cgi?action=getSystemInfo";
    private static final String DAHUA_DEVICE_TYPE = "/cgi-bin/magicBox.cgi?action=getDeviceType";
    private static final Pattern TABLE_ROW_RE = Pattern.compile(
            "table\\.(\\w+)\\[(\\d+)\\]\\.([^=]+)=(.*)",
            Pattern.CASE_INSENSITIVE
    );

    private static final List<String> DAHUA_CHANNEL_CONFIGS = List.of(
            "RemoteDevice",
            "RemoteVideoInput",
            "NetCamera",
            "LogicDevice"
    );

    private DahuaNvrSupport() {
    }

    public static String detectVendor(
            IsapiHttpClient client,
            String baseUrl,
            List<IsapiHttpClient.Credential> creds,
            double timeoutSeconds
    ) {
        IsapiHttpClient.Result isapi = client.get(baseUrl, "/ISAPI/System/deviceInfo", creds, timeoutSeconds);
        if (isapi.ok() && isapi.body() != null && isapi.body().toLowerCase(Locale.ROOT).contains("<devicetype>")) {
            return "hikvision";
        }
        if (isapi.status() == 200 || isapi.status() == 401 || isapi.status() == 403) {
            if (isapi.status() != 404) {
                return "hikvision";
            }
        }

        for (String path : List.of(DAHUA_DEVICE_CLASS, DAHUA_DEVICE_TYPE, DAHUA_SYSTEM_INFO)) {
            IsapiHttpClient.Result res = client.get(baseUrl, path, creds, timeoutSeconds);
            if (res.ok() && res.body() != null) {
                String deviceClass = parseDeviceClass(res.body());
                String bodyUpper = res.body().toUpperCase(Locale.ROOT);
                if (Set.of("NVR", "DVR", "XVR", "HCVR", "SDVR").contains(deviceClass.toUpperCase(Locale.ROOT))
                        || bodyUpper.contains("NVR")) {
                    return "dahua";
                }
                Map<String, String> parsed = parseKeyValueBody(res.body());
                String model = parsed.getOrDefault("model", parsed.getOrDefault("type", ""));
                String modelUpper = model.toUpperCase(Locale.ROOT);
                if (modelUpper.contains("NVR") || modelUpper.contains("XVR")
                        || modelUpper.contains("DVR") || modelUpper.contains("HCVR")) {
                    return "dahua";
                }
            }
        }
        return null;
    }

    public static List<Map<String, Object>> fetchChannels(
            IsapiHttpClient client,
            String baseUrl,
            List<IsapiHttpClient.Credential> creds,
            double timeoutSeconds
    ) {
        Map<Integer, Map<String, String>> remoteRows = new LinkedHashMap<>();
        for (String cfgName : DAHUA_CHANNEL_CONFIGS) {
            String path = "/cgi-bin/configManager.cgi?action=getConfig&name=" + cfgName;
            IsapiHttpClient.Result res = client.get(baseUrl, path, creds, timeoutSeconds);
            if (res.ok() && res.body() != null && res.body().contains("table.")) {
                Map<Integer, Map<String, String>> rows = parseTableRows(res.body(), cfgName);
                if (!rows.isEmpty()) {
                    remoteRows = rows;
                    break;
                }
            }
        }

        IsapiHttpClient.Result titleRes = client.get(
                baseUrl,
                "/cgi-bin/configManager.cgi?action=getConfig&name=ChannelTitle",
                creds,
                timeoutSeconds
        );
        Map<Integer, Map<String, String>> titleRows = titleRes.ok() && titleRes.body() != null
                ? parseTableRows(titleRes.body(), "ChannelTitle")
                : Map.of();

        if (remoteRows.isEmpty() && titleRows.isEmpty()) {
            return List.of();
        }
        if (remoteRows.isEmpty()) {
            for (Integer idx : titleRows.keySet()) {
                remoteRows.put(idx, new LinkedHashMap<>());
            }
        }
        return parseChannelRows(remoteRows, titleRows);
    }

    static Map<Integer, Map<String, String>> parseTableRows(String text, String tableName) {
        Map<Integer, Map<String, String>> rows = new LinkedHashMap<>();
        for (String line : text.split("\\R")) {
            Matcher matcher = TABLE_ROW_RE.matcher(line.trim());
            if (!matcher.matches()) {
                continue;
            }
            String tname = matcher.group(1);
            if (tableName != null && !tableName.equalsIgnoreCase(tname)) {
                continue;
            }
            int idx;
            try {
                idx = Integer.parseInt(matcher.group(2));
            } catch (NumberFormatException ex) {
                continue;
            }
            String field = matcher.group(3);
            String val = matcher.group(4).trim().replace("\"", "");
            rows.computeIfAbsent(idx, ignored -> new LinkedHashMap<>()).put(field, val);
        }
        return rows;
    }

    private static List<Map<String, Object>> parseChannelRows(
            Map<Integer, Map<String, String>> remoteRows,
            Map<Integer, Map<String, String>> titleRows
    ) {
        Set<Integer> indices = new TreeSet<>();
        indices.addAll(remoteRows.keySet());
        indices.addAll(titleRows.keySet());
        List<Map<String, Object>> out = new ArrayList<>();
        for (int idx : indices) {
            Map<String, String> remote = remoteRows.getOrDefault(idx, Map.of());
            Map<String, String> title = titleRows.getOrDefault(idx, Map.of());
            String enableRaw = firstNonBlank(remote.get("Enable"), remote.get("enable"));
            Boolean enabled = enableRaw != null ? "true".equalsIgnoreCase(enableRaw) : null;
            Boolean online = enabled;
            String portRaw = firstNonBlank(remote.get("Port"), remote.get("HttpPort"), remote.get("ManagePort"));
            Integer port = portRaw != null && portRaw.chars().allMatch(Character::isDigit)
                    ? Integer.parseInt(portRaw) : 37777;
            String ip = firstNonBlank(remote.get("Address"), remote.get("HostName"), remote.get("IP"));
            Map<String, Object> row = new LinkedHashMap<>();
            row.put("channel_id", idx + 1);
            row.put("name", firstNonBlank(title.get("Name"), remote.get("Name"), "Channel " + (idx + 1)));
            row.put("ip", ip);
            row.put("camera_ip", ip);
            row.put("port", ip != null && !ip.isBlank() ? port : null);
            row.put("camera_port", row.get("port"));
            row.put("protocol", firstNonBlank(remote.get("Protocol"), remote.get("DeviceType")));
            row.put("username", firstNonBlank(remote.get("UserName"), remote.get("User")));
            row.put("device_id", firstNonBlank(remote.get("SerialNo"), remote.get("SerialNumber")));
            row.put("online", online);
            row.put("enabled", enabled);
            row.put("connection_status", null);
            row.put("vendor", "dahua");
            out.add(row);
        }
        return out;
    }

    private static String parseDeviceClass(String body) {
        Map<String, String> parsed = parseKeyValueBody(body);
        return firstNonBlank(parsed.get("class"), parsed.get("device_class"), parsed.get("type"));
    }

    private static Map<String, String> parseKeyValueBody(String body) {
        Map<String, String> out = new LinkedHashMap<>();
        for (String line : body.split("\\R")) {
            int eq = line.indexOf('=');
            if (eq <= 0) {
                continue;
            }
            out.put(line.substring(0, eq).trim(), line.substring(eq + 1).trim());
        }
        return out;
    }

    private static String firstNonBlank(String... values) {
        for (String value : values) {
            if (value != null && !value.isBlank()) {
                return value.trim();
            }
        }
        return null;
    }
}
