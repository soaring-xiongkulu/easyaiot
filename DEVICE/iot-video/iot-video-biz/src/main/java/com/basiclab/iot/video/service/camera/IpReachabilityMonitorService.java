package com.basiclab.iot.video.service.camera;

import com.basiclab.iot.video.dal.DeviceRepository;
import com.basiclab.iot.video.domain.DeviceRow;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import java.net.InetAddress;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Lightweight IP reachability monitor (Python {@code IpReachabilityMonitor} simplified).
 * RTSP sources skip aggressive ICMP to avoid false offline.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class IpReachabilityMonitorService {

    private final DeviceRepository deviceRepository;
    private final Map<String, Boolean> lastOnline = new ConcurrentHashMap<>();

    public int registerDevicesOnStartup() {
        List<DeviceRow> devices = deviceRepository.list(1, 10_000, null);
        int registered = 0;
        for (DeviceRow device : devices) {
            String ip = resolveIp(device);
            if (ip != null) {
                lastOnline.put(device.getId(), null);
                registered++;
            }
        }
        log.info("IP 在线监控已登记设备数: {}", registered);
        return registered;
    }

    @Scheduled(fixedDelayString = "${video.health-monitor.ip-check-interval-ms:60000}")
    public void pollReachability() {
        for (DeviceRow device : deviceRepository.list(1, 500, null)) {
            String ip = resolveIp(device);
            if (ip == null) {
                continue;
            }
            String source = device.getSource() != null ? device.getSource().toLowerCase(Locale.ROOT) : "";
            if (source.startsWith("rtsp://") || source.startsWith("rtmp://")) {
                continue;
            }
            boolean reachable = ping(ip);
            Boolean previous = lastOnline.put(device.getId(), reachable);
            if (previous != null && previous != reachable) {
                log.info("设备在线状态变化 deviceId={} ip={} online={}", device.getId(), ip, reachable);
            }
        }
    }

    private static String resolveIp(DeviceRow device) {
        if (device.getIp() != null && !device.getIp().isBlank()) {
            return device.getIp().strip();
        }
        String source = device.getSource();
        if (source == null || source.isBlank()) {
            return null;
        }
        try {
            String host = java.net.URI.create(source.strip()).getHost();
            return host != null && !host.isBlank() ? host.strip() : null;
        } catch (Exception ex) {
            return null;
        }
    }

    private static boolean ping(String ip) {
        try {
            return InetAddress.getByName(ip).isReachable(1500);
        } catch (Exception ex) {
            return false;
        }
    }
}
