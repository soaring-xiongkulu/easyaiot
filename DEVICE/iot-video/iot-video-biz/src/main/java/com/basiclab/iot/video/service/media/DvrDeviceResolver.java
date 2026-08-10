package com.basiclab.iot.video.service.media;

import com.basiclab.iot.video.dal.DeviceRepository;
import com.basiclab.iot.video.domain.DeviceRow;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

@Slf4j
@Service
@RequiredArgsConstructor
public class DvrDeviceResolver {

    private final DeviceRepository deviceRepository;

    public record ResolvedDevice(String deviceId, DeviceRow device) {}

    public ResolvedDevice resolve(String stream, String filePath) {
        String normalizedStream = stream != null ? stream.trim() : "";
        String normalizedFile = filePath != null ? filePath.trim() : "";
        if (normalizedStream.isEmpty() && normalizedFile.isEmpty()) {
            return new ResolvedDevice(null, null);
        }

        String deviceId = normalizedStream;
        Optional<DeviceRow> device = deviceId.isEmpty()
                ? Optional.empty()
                : deviceRepository.findById(deviceId);

        if (device.isEmpty() && !normalizedStream.isEmpty()) {
            String inferId = parseInferStreamDeviceId(normalizedStream);
            if (inferId != null) {
                device = deviceRepository.findById(inferId);
                if (device.isPresent()) {
                    deviceId = inferId;
                }
            }
        }

        if (device.isEmpty() && normalizedStream.startsWith("live/")) {
            String potentialId = normalizedStream.substring(5);
            device = deviceRepository.findById(potentialId);
            if (device.isPresent()) {
                deviceId = potentialId;
            }
        }

        if (device.isEmpty() && !normalizedStream.isEmpty()) {
            for (String pattern : streamPatterns(normalizedStream)) {
                device = deviceRepository.findFirstByRtmpStreamLike(pattern);
                if (device.isPresent()) {
                    deviceId = device.get().getId();
                    break;
                }
            }
        }

        if (device.isEmpty() && !normalizedFile.isEmpty()) {
            ResolvedDevice fromFile = resolveFromFilePath(normalizedFile, deviceId);
            deviceId = fromFile.deviceId();
            device = Optional.ofNullable(fromFile.device());
        }

        return device.map(row -> new ResolvedDevice(deviceId, row)).orElseGet(() -> new ResolvedDevice(null, null));
    }

    static String parseInferStreamDeviceId(String stream) {
        if (stream == null || !stream.startsWith("infer_")) {
            return null;
        }
        String rest = stream.substring(6);
        int sep = rest.lastIndexOf("_m");
        if (sep <= 0) {
            return null;
        }
        String id = rest.substring(0, sep);
        return id.isEmpty() ? null : id;
    }

    private static List<String> streamPatterns(String stream) {
        List<String> patterns = new ArrayList<>();
        patterns.add("live/" + stream);
        patterns.add(stream);
        patterns.add("/live/" + stream);
        patterns.add("/" + stream);
        patterns.add("live/" + stream + "/");
        patterns.add(stream + "/");
        return patterns;
    }

    private ResolvedDevice resolveFromFilePath(String filePath, String fallbackId) {
        try {
            String[] parts = filePath.replace('\\', '/').split("/");
            List<String> pathParts = new ArrayList<>();
            for (String part : parts) {
                if (!part.isEmpty()) {
                    pathParts.add(part);
                }
            }
            int pi = pathParts.indexOf("playbacks");
            if (pi < 0 || pi + 2 >= pathParts.size()) {
                return new ResolvedDevice(fallbackId, null);
            }
            String potentialId = pathParts.get(pi + 2);
            String inferId = parseInferStreamDeviceId(potentialId);
            if (inferId != null) {
                Optional<DeviceRow> device = deviceRepository.findById(inferId);
                if (device.isPresent()) {
                    return new ResolvedDevice(inferId, device.get());
                }
            }
            Optional<DeviceRow> device = deviceRepository.findById(potentialId);
            if (device.isPresent()) {
                return new ResolvedDevice(potentialId, device.get());
            }
            String appName = pi + 1 < pathParts.size() ? pathParts.get(pi + 1) : "";
            for (String pattern : List.of(
                    appName + "/" + potentialId,
                    "live/" + potentialId,
                    potentialId,
                    "/live/" + potentialId,
                    "/" + potentialId
            )) {
                device = deviceRepository.findFirstByRtmpStreamLike(pattern);
                if (device.isPresent()) {
                    return new ResolvedDevice(device.get().getId(), device.get());
                }
            }
        } catch (Exception ex) {
            log.debug("从文件路径解析设备失败 file_path={} error={}", filePath, ex.getMessage());
        }
        return new ResolvedDevice(fallbackId, null);
    }
}
