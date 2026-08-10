package com.basiclab.iot.video.service.camera;

import com.basiclab.iot.video.dal.DeviceRepository;
import com.basiclab.iot.video.dal.DeviceSpaceRepository;
import com.basiclab.iot.video.dal.DeviceDirectoryRepository;
import com.basiclab.iot.video.domain.DeviceRow;
import com.basiclab.iot.video.exception.VideoBusinessException;
import com.basiclab.iot.video.service.CameraService;
import com.basiclab.iot.video.service.StreamUrlSupport;
import com.basiclab.iot.video.service.ViewForwardService;
import com.basiclab.iot.video.service.minio.VideoMinioService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.net.InetAddress;
import java.time.Instant;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class CameraAdminService {

    private final DeviceRepository deviceRepository;
    private final DeviceDirectoryRepository directoryRepository;
    private final DeviceSpaceRepository deviceSpaceRepository;
    private final CameraService cameraService;
    private final ViewForwardService viewForwardService;
    private final VideoMinioService videoMinioService;
    private final CameraHardwareService cameraHardwareService;
    private final StreamUrlSupport streamUrlSupport;

    public String registerDevice(Map<String, Object> data) {
        String id = data.get("id") != null ? String.valueOf(data.get("id")).trim() : String.valueOf(System.nanoTime());
        if (deviceRepository.existsById(id)) {
            throw new VideoBusinessException(400, "设备ID已存在，请使用唯一标识符");
        }
        String source = data.get("source") != null ? String.valueOf(data.get("source")).trim() : "";
        if (source.isEmpty()) {
            throw new VideoBusinessException(400, "请提供 source（RTSP/RTMP 取流地址）；若需 ONVIF 发现请调用 /register/device/onvif");
        }
        String cameraType = data.get("cameraType") != null ? String.valueOf(data.get("cameraType")) : "";
        String manufacturer = strOrDefault(data.get("manufacturer"), "EasyAIoT");
        String model = strOrDefault(data.get("model"), "Camera-EasyAIoT");
        if ("custom".equals(cameraType)) {
            if (isBlank(data.get("manufacturer"))) {
                manufacturer = "EasyAIoT";
            }
            if (isBlank(data.get("model"))) {
                model = "Camera-EasyAIoT";
            }
        }
        String[] streams = streamUrlSupport.defaultStreamUrls(id);
        DeviceRow row = new DeviceRow();
        row.setId(id);
        row.setName(strOrDefault(data.get("name"), "Camera-" + id.substring(0, Math.min(6, id.length()))));
        row.setSource(source);
        row.setRtmpStream(streams[0]);
        row.setHttpStream(streams[1]);
        row.setAiRtmpStream(streams[2]);
        row.setAiHttpStream(streams[3]);
        row.setIp(str(data.get("ip")));
        row.setPort(intOr(data.get("port"), 554));
        row.setUsername(str(data.get("username")));
        row.setManufacturer(manufacturer);
        row.setModel(model);
        row.setSerialNumber(str(data.get("serial_number")));
        row.setHardwareId(str(data.get("hardware_id")));
        row.setSupportMove(bool(data.get("support_move")));
        row.setSupportZoom(bool(data.get("support_zoom")));
        row.setEnableForward(boolOr(data.get("enable_forward"), false));
        row.setNvrChannel(intOr(data.get("nvr_channel"), 0));
        row.setNvrId(intOrNull(data.get("nvr_id")));
        row.setDirectoryId(directoryIdForNewDevice(data));
        deviceRepository.insert(row);
        ensureSpacesQuiet(id, row.getName());
        return id;
    }

    public String registerByOnvif(String ip, int port, String password, String username) {
        if (ip == null || ip.isBlank()) {
            throw new VideoBusinessException(400, "摄像头IP地址不能为空");
        }
        if (password == null || password.isBlank()) {
            throw new VideoBusinessException(400, "摄像头密码不能为空");
        }
        if (port <= 0) {
            throw new VideoBusinessException(400, "摄像头端口必须大于0");
        }
        Map<String, Object> info = cameraHardwareService.connectOnvif(ip, port, password, username);
        String mac = str(info.get("mac"));
        String source = str(info.get("source"));
        Optional<DeviceRow> existing = deviceRepository.findExistingForRegister(ip, mac, str(info.get("serial_number")), null, 0, source);
        if (existing.isPresent()) {
            String deviceId = existing.get().getId();
            Map<String, Object> fields = new LinkedHashMap<>();
            fields.put("ip", ip);
            fields.put("port", port);
            fields.put("username", info.get("username"));
            fields.put("source", source);
            fields.put("mac", mac);
            fields.put("manufacturer", info.get("manufacturer"));
            fields.put("model", info.get("model"));
            fields.put("firmware_version", info.get("firmware_version"));
            fields.put("serial_number", info.get("serial_number"));
            deviceRepository.updateFields(deviceId, fields);
            deviceRepository.updatePassword(deviceId, password);
            return deviceId;
        }
        String deviceId = String.valueOf(System.nanoTime());
        String[] streams = streamUrlSupport.defaultStreamUrls(deviceId);
        DeviceRow row = new DeviceRow();
        row.setId(deviceId);
        row.setName(strOrDefault(info.get("model"), "Camera-" + deviceId.substring(0, Math.min(6, deviceId.length()))));
        row.setSource(source);
        row.setRtmpStream(streams[0]);
        row.setHttpStream(streams[1]);
        row.setAiRtmpStream(streams[2]);
        row.setAiHttpStream(streams[3]);
        row.setIp(ip);
        row.setPort(port);
        row.setUsername(str(info.get("username")));
        row.setMac(mac);
        row.setManufacturer(strOrDefault(info.get("manufacturer"), "EasyAIoT"));
        row.setModel(strOrDefault(info.get("model"), "Camera-EasyAIoT"));
        row.setFirmwareVersion(str(info.get("firmware_version")));
        row.setSerialNumber(str(info.get("serial_number")));
        row.setHardwareId(str(info.get("hardware_id")));
        row.setSupportMove(bool(info.get("support_move")));
        row.setSupportZoom(bool(info.get("support_zoom")));
        row.setEnableForward(false);
        row.setDirectoryId(directoryIdForNewDevice(Map.of()));
        deviceRepository.insert(row);
        deviceRepository.updatePassword(deviceId, password);
        ensureSpacesQuiet(deviceId, row.getName());
        return deviceId;
    }

    public void updateDevice(String deviceId, Map<String, Object> data) {
        DeviceRow existing = deviceRepository.findById(deviceId)
                .orElseThrow(() -> new VideoBusinessException(400, "设备不存在: " + deviceId));
        Map<String, Object> fields = new LinkedHashMap<>();
        putIfPresent(fields, "name", data.get("name"));
        putIfPresent(fields, "source", data.get("source"));
        putIfPresent(fields, "ip", data.get("ip"));
        putIfPresent(fields, "port", intOrNull(data.get("port")));
        putIfPresent(fields, "username", data.get("username"));
        putIfPresent(fields, "manufacturer", normalizeManufacturer(data.get("manufacturer")));
        putIfPresent(fields, "model", normalizeModel(data.get("model")));
        putIfPresent(fields, "serial_number", data.get("serial_number"));
        putIfPresent(fields, "hardware_id", data.get("hardware_id"));
        putIfPresent(fields, "support_move", normalizeBool(data.get("support_move")));
        putIfPresent(fields, "support_zoom", normalizeBool(data.get("support_zoom")));
        putIfPresent(fields, "enable_forward", normalizeBool(data.get("enable_forward")));
        putIfPresent(fields, "directory_id", intOrNull(data.get("directory_id")));
        if (fields.isEmpty()) {
            return;
        }
        deviceRepository.updateFields(deviceId, fields);
        Object ef = data.get("enable_forward");
        if (isFalse(ef)) {
            viewForwardService.stopStream(deviceId);
        }
    }

    public void deleteDevice(String deviceId) {
        if (!deviceRepository.findById(deviceId).isPresent()) {
            throw new VideoBusinessException(400, "设备不存在: " + deviceId);
        }
        try {
            viewForwardService.stopStream(deviceId);
        } catch (Exception ignored) {
        }
        deviceRepository.delete(deviceId);
    }

    public Map<String, Object> batchDelete(List<?> deviceIds) {
        int deleted = 0;
        List<String> errors = new java.util.ArrayList<>();
        for (Object raw : deviceIds) {
            String id = String.valueOf(raw).trim();
            if (id.isEmpty()) {
                continue;
            }
            try {
                deleteDevice(id);
                deleted++;
            } catch (Exception e) {
                errors.add(id + ": " + e.getMessage());
            }
        }
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("deleted", deleted);
        result.put("errors", errors);
        return result;
    }

    public Map<String, Object> ensureSpaces(String deviceId) {
        DeviceRow device = deviceRepository.findById(deviceId)
                .orElseThrow(() -> new VideoBusinessException(404, "设备不存在: " + deviceId));
        ensureSpacesQuiet(deviceId, device.getName());
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("snap_space", deviceSpaceRepository.findSnapSpaceByDeviceId(deviceId).orElse(null));
        data.put("record_space", deviceSpaceRepository.findRecordSpaceByDeviceId(deviceId).orElse(null));
        return data;
    }

    public Map<String, Object> resolveInferenceInput(String deviceId) {
        DeviceRow device = deviceRepository.findById(deviceId)
                .orElseThrow(() -> new VideoBusinessException(400, "设备不存在: " + deviceId));
        String source = device.getSource() != null ? device.getSource().trim() : "";
        String rtspDirect = device.getRtspDirect() != null ? device.getRtspDirect().trim() : "";
        String[] streams = streamUrlSupport.resolveDeviceStreamUrls(
                deviceId,
                device.getRtmpStream(),
                device.getHttpStream(),
                device.getAiRtmpStream(),
                device.getAiHttpStream()
        );
        String rtmpStream = firstNonBlank(streams[0], device.getRtmpStream());
        String httpStream = firstNonBlank(streams[1], device.getHttpStream());
        boolean isGb28181 = source.toLowerCase(Locale.ROOT).startsWith("gb28181://");
        String resolvedSource = null;
        if (isGb28181) {
            resolvedSource = source;
        } else if (source.toLowerCase(Locale.ROOT).startsWith("rtsp://")
                || source.toLowerCase(Locale.ROOT).startsWith("rtmp://")) {
            resolvedSource = source;
        } else if (rtspDirect.toLowerCase(Locale.ROOT).startsWith("rtsp://")
                || rtspDirect.toLowerCase(Locale.ROOT).startsWith("rtmp://")) {
            resolvedSource = rtspDirect;
        }
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("device_id", deviceId);
        data.put("source", source.isEmpty() ? null : source);
        data.put("rtsp_direct", rtspDirect.isEmpty() ? null : rtspDirect);
        data.put("rtmp_stream", rtmpStream.isEmpty() ? null : rtmpStream);
        data.put("http_stream", httpStream.isEmpty() ? null : httpStream);
        data.put("resolved_source", resolvedSource == null || resolvedSource.isBlank() ? null : resolvedSource.trim());
        data.put("is_gb28181", isGb28181);
        data.put("input_url", resolvedSource != null && !resolvedSource.isBlank() ? resolvedSource : source);
        data.put("kind", isGb28181 ? "gb28181" : "direct");
        return data;
    }

    public Map<String, Object> getDevice(String deviceId, String ensureName) {
        return cameraService.getDevice(deviceId);
    }

    private void ensureSpacesQuiet(String deviceId, String name) {
        try {
            if (deviceSpaceRepository.findSnapSpaceByDeviceId(deviceId).isEmpty()) {
                deviceSpaceRepository.createSnapSpace(deviceId, name);
            }
            if (deviceSpaceRepository.findRecordSpaceByDeviceId(deviceId).isEmpty()) {
                deviceSpaceRepository.createRecordSpace(deviceId, name);
            }
            videoMinioService.ensureDeviceDirectoryForSpace(videoMinioService.snapBucket(), deviceId, false);
            videoMinioService.ensureDeviceDirectoryForSpace(videoMinioService.recordBucket(), deviceId, true);
        } catch (Exception ignored) {
        }
    }

    private int directoryIdForNewDevice(Map<String, Object> data) {
        Object raw = data.get("directory_id");
        if (raw != null && !"".equals(String.valueOf(raw)) && !"0".equals(String.valueOf(raw))) {
            return Integer.parseInt(String.valueOf(raw));
        }
        return directoryRepository.ensureDefaultDirectory();
    }

    static String[] defaultStreamUrls(String deviceId) {
        // Kept for tests; production paths use injected StreamUrlSupport.
        String host = resolveHostIp();
        return new String[]{
                "rtmp://" + host + ":1935/live/" + deviceId,
                "http://" + host + ":8080/live/" + deviceId + ".flv",
                "rtmp://" + host + ":1935/ai/" + deviceId,
                "http://" + host + ":8080/ai/" + deviceId + ".flv"
        };
    }

    private static String resolveHostIp() {
        String podIp = System.getenv("POD_IP");
        if (podIp != null && !podIp.isBlank()) {
            return podIp.trim();
        }
        try {
            return InetAddress.getLocalHost().getHostAddress();
        } catch (Exception e) {
            return "127.0.0.1";
        }
    }

    private static void putIfPresent(Map<String, Object> fields, String key, Object value) {
        if (value != null) {
            fields.put(key, value);
        }
    }

    private static String str(Object value) {
        return value != null ? String.valueOf(value).trim() : null;
    }

    private static String strOrDefault(Object value, String defaultValue) {
        String s = str(value);
        return s == null || s.isEmpty() ? defaultValue : s;
    }

    private static boolean isBlank(Object value) {
        return value == null || String.valueOf(value).trim().isEmpty();
    }

    private static Integer intOrNull(Object value) {
        if (value == null || "".equals(String.valueOf(value))) {
            return null;
        }
        return Integer.parseInt(String.valueOf(value));
    }

    private static int intOr(Object value, int defaultValue) {
        if (value == null || "".equals(String.valueOf(value))) {
            return defaultValue;
        }
        return Integer.parseInt(String.valueOf(value));
    }

    private static Boolean bool(Object value) {
        return normalizeBool(value);
    }

    private static boolean boolOr(Object value, boolean defaultValue) {
        Boolean b = normalizeBool(value);
        return b != null ? b : defaultValue;
    }

    private static Boolean normalizeBool(Object value) {
        if (value == null || "".equals(value)) {
            return false;
        }
        if (value instanceof Boolean b) {
            return b;
        }
        String s = String.valueOf(value).trim().toLowerCase(Locale.ROOT);
        return "true".equals(s) || "1".equals(s) || "yes".equals(s) || "on".equals(s);
    }

    private static boolean isFalse(Object value) {
        if (value == null) {
            return false;
        }
        if (value instanceof Boolean b) {
            return !b;
        }
        String s = String.valueOf(value).trim().toLowerCase(Locale.ROOT);
        return "false".equals(s) || "0".equals(s) || "no".equals(s) || "off".equals(s);
    }

    private static Object normalizeManufacturer(Object value) {
        String s = str(value);
        return (s == null || s.isEmpty()) ? "EasyAIoT" : s;
    }

    private static Object normalizeModel(Object value) {
        String s = str(value);
        return (s == null || s.isEmpty()) ? "Camera-EasyAIoT" : s;
    }

    private static String firstNonBlank(String... values) {
        for (String value : values) {
            if (value != null && !value.isBlank()) {
                return value.trim();
            }
        }
        return "";
    }
}
