package com.basiclab.iot.video.service;

import com.basiclab.iot.video.dal.DeviceRepository;
import com.basiclab.iot.video.domain.DeviceRow;
import com.basiclab.iot.video.exception.VideoBusinessException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class CameraService {

    private static final DateTimeFormatter ISO_INSTANT = DateTimeFormatter.ISO_INSTANT;

    private final DeviceRepository deviceRepository;

    public Map<String, Object> listDevices(int pageNo, int pageSize, String search) {
        if (pageNo < 1 || pageSize < 1) {
            throw new VideoBusinessException(400, "参数错误：pageNo和pageSize必须为正整数");
        }
        List<Map<String, Object>> items = deviceRepository.list(pageNo, pageSize, search).stream()
                .map(this::toMap)
                .toList();
        return Map.of(
                "items", items,
                "total", deviceRepository.count(search)
        );
    }

    public Map<String, Object> getDevice(String deviceId) {
        DeviceRow row = deviceRepository.findById(deviceId)
                .orElseThrow(() -> new VideoBusinessException(400, "设备不存在: " + deviceId));
        return toDeviceMap(row);
    }

    public Map<String, Object> toDeviceMap(DeviceRow camera) {
        return toMap(camera);
    }

    private Map<String, Object> toMap(DeviceRow camera) {
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("id", camera.getId());
        payload.put("name", camera.getName());
        payload.put("source", camera.getSource());
        payload.put("rtmp_stream", camera.getRtmpStream());
        payload.put("http_stream", camera.getHttpStream());
        payload.put("ai_rtmp_stream", camera.getAiRtmpStream());
        payload.put("ai_http_stream", camera.getAiHttpStream());
        payload.put("enable_forward", camera.getEnableForward());
        payload.put("stream", camera.getStream() != null ? camera.getStream() : 0);
        payload.put("ip", camera.getIp());
        payload.put("port", camera.getPort());
        payload.put("username", camera.getUsername());
        payload.put("mac", camera.getMac());
        payload.put("manufacturer", camera.getManufacturer());
        payload.put("model", camera.getModel());
        payload.put("firmware_version", camera.getFirmwareVersion());
        payload.put("serial_number", camera.getSerialNumber());
        payload.put("hardware_id", camera.getHardwareId());
        payload.put("support_move", camera.getSupportMove());
        payload.put("support_zoom", camera.getSupportZoom());
        payload.put("directory_id", camera.getDirectoryId());
        payload.put("rtsp_direct", camera.getRtspDirect());
        payload.put("channel_online", camera.getChannelOnline());
        payload.put("connection_status", camera.getConnectionStatus());
        payload.put("online", resolveOnline(camera));
        payload.putAll(locationFields(camera));
        payload.putAll(nvrFields(camera));
        String source = camera.getSource() != null ? camera.getSource().trim() : "";
        if (source.toLowerCase().startsWith("gb28181://")) {
            payload.put("device_kind", "gb28181");
        }
        return payload;
    }

    private boolean resolveOnline(DeviceRow camera) {
        String source = camera.getSource() != null ? camera.getSource().trim() : "";
        if (source.toLowerCase().startsWith("rtmp://")) {
            return true;
        }
        if (isCustomCamera(camera)) {
            return true;
        }
        if (Boolean.TRUE.equals(camera.getChannelOnline())) {
            return true;
        }
        String conn = camera.getConnectionStatus() != null ? camera.getConnectionStatus().trim().toLowerCase() : "";
        if ("online".equals(conn)) {
            return true;
        }
        if (Boolean.TRUE.equals(camera.getEnableForward())
                && (isNonBlank(camera.getHttpStream()) || isNonBlank(camera.getRtmpStream()))) {
            return true;
        }
        String streamSource = isNonBlank(camera.getSource()) ? camera.getSource().trim()
                : (camera.getRtspDirect() != null ? camera.getRtspDirect().trim() : "");
        String lower = streamSource.toLowerCase();
        return lower.startsWith("rtsp://") || lower.startsWith("http://") || lower.startsWith("https://")
                || lower.startsWith("gb28181://");
    }

    private boolean isCustomCamera(DeviceRow camera) {
        if (camera.getNvrId() != null || camera.getNvrChannel() > 0) {
            return true;
        }
        String source = camera.getSource() != null ? camera.getSource().trim() : "";
        if (usesDirectStream(source)) {
            return true;
        }
        if (source.isEmpty()) {
            return false;
        }
        return camera.getIp() == null || camera.getIp().isBlank();
    }

    private boolean usesDirectStream(String source) {
        String lower = source.toLowerCase();
        return lower.startsWith("rtsp://") || lower.startsWith("rtmp://") || lower.startsWith("gb28181://");
    }

    private Map<String, Object> locationFields(DeviceRow camera) {
        boolean hasLocation = camera.getLongitude() != null && camera.getLatitude() != null;
        String updatedAt = camera.getLocationUpdatedAt() != null
                ? ISO_INSTANT.format(camera.getLocationUpdatedAt().atOffset(ZoneOffset.UTC))
                : null;
        Map<String, Object> fields = new HashMap<>();
        fields.put("longitude", camera.getLongitude());
        fields.put("latitude", camera.getLatitude());
        fields.put("altitude", camera.getAltitude());
        fields.put("address", camera.getAddress());
        fields.put("heading", camera.getHeading());
        fields.put("location_source", camera.getLocationSource());
        fields.put("location_updated_at", updatedAt);
        fields.put("has_location", hasLocation);
        return fields;
    }

    private Map<String, Object> nvrFields(DeviceRow camera) {
        int channel = camera.getNvrChannel();
        if (camera.getNvrId() == null) {
            Map<String, Object> direct = new HashMap<>();
            direct.put("nvr_id", null);
            direct.put("nvr_channel", channel);
            direct.put("nvr_label", null);
            direct.put("nvr", null);
            direct.put("device_kind", "direct");
            return direct;
        }
        Map<String, Object> linked = new HashMap<>();
        linked.put("nvr_id", camera.getNvrId());
        linked.put("nvr_channel", channel);
        linked.put("nvr_label", null);
        linked.put("nvr", null);
        linked.put("device_kind", "nvr_channel");
        return linked;
    }

    private static boolean isNonBlank(String value) {
        return value != null && !value.isBlank();
    }
}
