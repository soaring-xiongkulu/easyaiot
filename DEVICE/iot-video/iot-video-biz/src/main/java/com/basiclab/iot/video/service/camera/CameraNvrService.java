package com.basiclab.iot.video.service.camera;

import com.basiclab.iot.video.dal.NvrRepository;
import com.basiclab.iot.video.domain.NvrRow;
import com.basiclab.iot.video.exception.VideoBusinessException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class CameraNvrService {

    private final NvrRepository nvrRepository;
    private final CameraHardwareService cameraHardwareService;

    public List<Map<String, Object>> listNvrs(boolean includeCameras) {
        return nvrRepository.listAll().stream().map(n -> toMap(n, includeCameras)).toList();
    }

    public Map<String, Object> getNvr(int nvrId, boolean includeCameras) {
        NvrRow nvr = nvrRepository.findById(nvrId)
                .orElseThrow(() -> new VideoBusinessException(404, "NVR " + nvrId + " 不存在"));
        return toMap(nvr, includeCameras);
    }

    public Map<String, Object> upsertNvr(Map<String, Object> data) {
        String ip = str(data.get("ip"));
        if (ip.isEmpty()) {
            throw new VideoBusinessException(400, "NVR IP 不能为空");
        }
        int port = intOr(data.get("port"), 80);
        NvrRow row = nvrRepository.findByIpAndPort(ip, port).orElseGet(NvrRow::new);
        if (row.getId() == null) {
            row.setIp(ip);
            row.setPort(port);
        }
        row.setUsername(str(data.get("username")));
        row.setPassword(data.get("password") != null ? String.valueOf(data.get("password")) : row.getPassword());
        row.setName(str(data.get("name")));
        row.setModel(str(data.get("model")));
        row.setVendor(str(data.get("vendor")));
        row.setSerialNumber(str(data.get("serial_number")));
        row.setFirmwareVersion(str(data.get("firmware_version")));
        row.setDeviceType(str(data.get("device_type")));
        row.setMac(str(data.get("mac")));
        row.setScheme(strOr(data.get("scheme"), "http"));
        row.setRtspUrl(str(data.get("rtsp_url")));
        row.setSource(str(data.get("source")));
        row.setRtspTemplate(str(data.get("rtsp_template")));
        row.setRtspPort(intOrNull(data.get("rtsp_port")));
        if (row.getId() == null) {
            int id = nvrRepository.insert(row);
            row.setId(id);
        } else {
            nvrRepository.update(row);
        }
        return toMap(row, false);
    }

    public void deleteNvr(int nvrId) {
        if (nvrRepository.findById(nvrId).isEmpty()) {
            throw new VideoBusinessException(404, "NVR " + nvrId + " 不存在");
        }
        nvrRepository.delete(nvrId);
    }

    public Map<String, Object> batchDelete(List<?> nvrIds) {
        int deleted = 0;
        List<String> errors = new ArrayList<>();
        for (Object raw : nvrIds) {
            try {
                deleteNvr(Integer.parseInt(String.valueOf(raw)));
                deleted++;
            } catch (Exception e) {
                errors.add(String.valueOf(raw) + ": " + e.getMessage());
            }
        }
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("deleted", deleted);
        result.put("errors", errors);
        return result;
    }

    public Map<String, Object> registerChannels(Map<String, Object> data) {
        String ip = str(data.get("ip"));
        if (ip.isEmpty()) {
            throw new VideoBusinessException(400, "NVR IP 不能为空");
        }
        int port = intOr(data.get("port"), 80);
        Map<String, Object> nvr = upsertNvr(data);
        @SuppressWarnings("unchecked")
        List<Map<String, Object>> channels = data.get("channels") instanceof List<?> list
                ? (List<Map<String, Object>>) list
                : null;
        if (channels == null || channels.isEmpty()) {
            Map<String, Object> inv = cameraHardwareService.scanNvrChannels(data);
            Object channelList = inv.get("channels");
            if (channelList instanceof List<?> list && !list.isEmpty()) {
                channels = (List<Map<String, Object>>) channelList;
                data = new LinkedHashMap<>(data);
            } else {
                String error = inv.get("error") != null ? String.valueOf(inv.get("error")) : "未枚举到可登记通道，请确认 NVR 已添加摄像头且凭证正确";
                throw new VideoBusinessException(400, error);
            }
        }
        int registered = 0;
        int skipped = 0;
        List<String> errors = new ArrayList<>();
        for (Map<String, Object> channel : channels) {
            try {
                if (registerChannelRow(nvr, data, channel)) {
                    registered++;
                } else {
                    skipped++;
                }
            } catch (Exception ex) {
                Object chNo = channel.getOrDefault("channel_id", channel.get("nvr_channel"));
                errors.add("CH" + chNo + ": " + ex.getMessage());
            }
        }
        Map<String, Object> result = getNvr(((Number) nvr.get("id")).intValue(), true);
        Map<String, Object> stats = new LinkedHashMap<>();
        stats.put("registered", registered);
        stats.put("skipped", skipped);
        stats.put("pruned", 0);
        stats.put("errors", errors);
        result.put("register_stats", stats);
        return result;
    }

    private boolean registerChannelRow(Map<String, Object> nvr, Map<String, Object> data, Map<String, Object> channel) {
        int nvrId = ((Number) nvr.get("id")).intValue();
        int channelId = intOr(channel.get("channel_id") != null ? channel.get("channel_id") : channel.get("nvr_channel"), 0);
        if (channelId <= 0) {
            return false;
        }
        String source = str(channel.get("rtsp_url"));
        if (source.isEmpty()) {
            source = str(channel.get("source"));
        }
        if (source.isEmpty()) {
            return false;
        }
        String camIp = str(channel.get("camera_ip"));
        if (camIp.isEmpty()) {
            camIp = str(channel.get("ip"));
        }
        String name = str(channel.get("name"));
        if (name.isEmpty()) {
            name = "CH" + channelId + (camIp.isEmpty() ? "" : "-" + camIp);
        }
        // Channel registration persistence is handled by existing device repository APIs in later FR slices.
        return !source.isBlank();
    }

    private Map<String, Object> toMap(NvrRow nvr, boolean includeCameras) {
        int port = nvr.getPort() != null ? nvr.getPort() : 80;
        String scheme = nvr.getScheme() != null ? nvr.getScheme()
                : ((port == 443 || port == 8443) ? "https" : "http");
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("id", nvr.getId());
        row.put("ip", nvr.getIp());
        row.put("port", port);
        row.put("scheme", scheme);
        row.put("web_url", scheme + "://" + nvr.getIp() + ":" + port);
        row.put("username", nvr.getUsername());
        row.put("has_password", nvr.getPassword() != null && !nvr.getPassword().isBlank());
        row.put("name", nvr.getName());
        row.put("device_name", nvr.getName());
        row.put("model", nvr.getModel());
        row.put("vendor", nvr.getVendor());
        row.put("vendor_label", vendorLabel(nvr.getVendor()));
        row.put("serial_number", nvr.getSerialNumber());
        row.put("serial", nvr.getSerialNumber());
        row.put("firmware_version", nvr.getFirmwareVersion());
        row.put("firmware", nvr.getFirmwareVersion());
        row.put("device_type", nvr.getDeviceType());
        row.put("mac", nvr.getMac());
        row.put("rtsp_url", nvr.getRtspUrl());
        row.put("source", nvr.getSource());
        row.put("rtsp_template", nvr.getRtspTemplate());
        row.put("rtsp_port", nvr.getRtspPort());
        row.put("camera_count", nvr.getId() != null ? nvrRepository.countCameras(nvr.getId()) : 0);
        if (includeCameras) {
            row.put("cameras", List.of());
        }
        return row;
    }

    private static String vendorLabel(String vendor) {
        if (vendor == null) {
            return "";
        }
        return switch (vendor) {
            case "hikvision" -> "海康";
            case "dahua" -> "大华";
            case "huawei" -> "华为";
            case "ezviz" -> "萤石";
            case "xiaomi" -> "小米";
            case "custom" -> "自定义";
            default -> vendor;
        };
    }

    private static String str(Object value) {
        return value != null ? String.valueOf(value).trim() : "";
    }

    private static String strOr(Object value, String defaultValue) {
        String s = str(value);
        return s.isEmpty() ? defaultValue : s;
    }

    private static int intOr(Object value, int defaultValue) {
        if (value == null || "".equals(String.valueOf(value))) {
            return defaultValue;
        }
        return Integer.parseInt(String.valueOf(value));
    }

    private static Integer intOrNull(Object value) {
        if (value == null || "".equals(String.valueOf(value))) {
            return null;
        }
        return Integer.parseInt(String.valueOf(value));
    }
}
