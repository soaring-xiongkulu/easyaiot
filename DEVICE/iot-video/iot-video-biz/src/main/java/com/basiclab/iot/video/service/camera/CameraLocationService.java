package com.basiclab.iot.video.service.camera;

import com.basiclab.iot.video.dal.DeviceRepository;
import com.basiclab.iot.video.domain.DeviceRow;
import com.basiclab.iot.video.exception.VideoBusinessException;
import com.basiclab.iot.video.service.CameraService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class CameraLocationService {

    private final DeviceRepository deviceRepository;
    private final CameraService cameraService;

    public List<Map<String, Object>> listLocations(Integer directoryId, boolean hasLocationOnly) {
        List<DeviceRow> devices = deviceRepository.listForMap(directoryId, hasLocationOnly);
        List<Map<String, Object>> items = new ArrayList<>();
        for (DeviceRow device : devices) {
            items.add(cameraService.toDeviceMap(device));
        }
        return items;
    }

    public Map<String, Object> getLocation(String deviceId) {
        DeviceRow device = deviceRepository.findById(deviceId)
                .orElseThrow(() -> new VideoBusinessException(400, "设备不存在: " + deviceId));
        Map<String, Object> info = cameraService.toDeviceMap(device);
        info.put("id", device.getId());
        return info;
    }

    public Map<String, Object> updateLocation(String deviceId, Map<String, Object> data) {
        if (!deviceRepository.findById(deviceId).isPresent()) {
            throw new VideoBusinessException(400, "设备不存在: " + deviceId);
        }
        Double longitude = parseOptionalDouble(data.get("longitude"));
        Double latitude = parseOptionalDouble(data.get("latitude"));
        validateLocationPair(longitude, latitude);
        Double altitude = parseOptionalDouble(data.get("altitude"));
        Double heading = parseOptionalDouble(data.get("heading"));
        validateHeading(heading);
        String address = data.get("address") != null ? String.valueOf(data.get("address")).trim() : null;
        if (address != null && address.isEmpty()) {
            address = null;
        }
        String locationSource = data.get("location_source") != null
                ? String.valueOf(data.get("location_source")).trim()
                : "manual";
        deviceRepository.updateLocation(deviceId, longitude, latitude, altitude, address, heading, locationSource);
        return getLocation(deviceId);
    }

    public Map<String, Object> batchUpdateLocations(List<Map<String, Object>> items) {
        int updated = 0;
        List<String> errors = new ArrayList<>();
        for (Map<String, Object> item : items) {
            String deviceId = item.get("device_id") != null
                    ? String.valueOf(item.get("device_id"))
                    : String.valueOf(item.get("id"));
            try {
                updateLocation(deviceId, item);
                updated++;
            } catch (Exception e) {
                errors.add(deviceId + ": " + e.getMessage());
            }
        }
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("updated", updated);
        result.put("errors", errors);
        return result;
    }

    private static Double parseOptionalDouble(Object value) {
        if (value == null || "".equals(value)) {
            return null;
        }
        return Double.parseDouble(String.valueOf(value));
    }

    private static void validateLocationPair(Double longitude, Double latitude) {
        if (longitude == null && latitude == null) {
            return;
        }
        if (longitude == null || latitude == null) {
            throw new VideoBusinessException(400, "经纬度需同时填写或同时留空");
        }
        if (longitude < -180 || longitude > 180) {
            throw new VideoBusinessException(400, "经度范围应在 -180 至 180 之间");
        }
        if (latitude < -90 || latitude > 90) {
            throw new VideoBusinessException(400, "纬度范围应在 -90 至 90 之间");
        }
    }

    private static void validateHeading(Double heading) {
        if (heading == null) {
            return;
        }
        if (heading < 0 || heading > 360) {
            throw new VideoBusinessException(400, "朝向应在 0 至 360 度之间");
        }
    }
}
