package com.basiclab.iot.video.service;

import com.basiclab.iot.video.dal.DeviceRepository;
import com.basiclab.iot.video.domain.DeviceRow;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;

/**
 * Mirrors retired Python {@code app.services.stream_url_sync_service}.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class StreamUrlSyncService {

    private final MediaPoolClient mediaPoolClient;
    private final StreamUrlSupport streamUrlSupport;
    private final IotNodeClient iotNodeClient;
    private final DeviceRepository deviceRepository;

    public int syncDeviceStreamUrls(List<String> deviceIds, String deployHost, Long nodeId) {
        String host = deployHost != null ? deployHost.trim() : "";
        if (host.isEmpty()) {
            return 0;
        }

        Map<String, Object> tags = null;
        if (nodeId != null) {
            try {
                Map<String, Object> node = iotNodeClient.getNode(nodeId);
                Object tagsObj = node.get("tags");
                if (tagsObj instanceof Map<?, ?> rawTags) {
                    @SuppressWarnings("unchecked")
                    Map<String, Object> cast = (Map<String, Object>) rawTags;
                    tags = cast;
                }
            } catch (Exception e) {
                log.warn("同步流地址时查询节点失败 node_id={}: {}", nodeId, e.getMessage());
            }
        }

        int updated = 0;
        for (String deviceId : deviceIds) {
            Optional<DeviceRow> deviceOpt = deviceRepository.findById(deviceId);
            if (deviceOpt.isEmpty()) {
                continue;
            }
            DeviceRow device = deviceOpt.get();
            String[] urls;
            try {
                if (mediaPoolClient.isMediaPoolEnabled()) {
                    Map<String, Object> binding = mediaPoolClient.allocateDeviceMedia(deviceId);
                    urls = mediaPoolClient.streamUrlsFromBinding(binding);
                } else {
                    urls = streamUrlSupport.buildStreamUrlsForHost(host, deviceId, tags, null);
                }
            } catch (Exception e) {
                log.warn(
                        "设备流地址同步失败 device_id={} host={}，回退节点默认地址: {}",
                        deviceId, host, e.getMessage()
                );
                urls = streamUrlSupport.buildStreamUrlsForHost(host, deviceId, tags, null);
            }

            Map<String, Object> fields = new LinkedHashMap<>();
            if (isNonBlank(urls[0]) && !Objects.equals(device.getRtmpStream(), urls[0])) {
                fields.put("rtmp_stream", urls[0]);
            }
            if (isNonBlank(urls[1]) && !Objects.equals(device.getHttpStream(), urls[1])) {
                fields.put("http_stream", urls[1]);
            }
            if (isNonBlank(urls[2]) && !Objects.equals(device.getAiRtmpStream(), urls[2])) {
                fields.put("ai_rtmp_stream", urls[2]);
            }
            if (isNonBlank(urls[3]) && !Objects.equals(device.getAiHttpStream(), urls[3])) {
                fields.put("ai_http_stream", urls[3]);
            }
            if (!fields.isEmpty()) {
                deviceRepository.updateFields(deviceId, fields);
                updated++;
                log.info("已同步设备流地址 device_id={} host={} http={}", deviceId, host, urls[1]);
            }
        }
        return updated;
    }

    private static boolean isNonBlank(String value) {
        return value != null && !value.trim().isEmpty();
    }
}
