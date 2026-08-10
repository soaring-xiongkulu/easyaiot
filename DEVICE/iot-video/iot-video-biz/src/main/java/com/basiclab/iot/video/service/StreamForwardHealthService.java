package com.basiclab.iot.video.service;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.dal.StreamForwardTaskRepository;
import com.basiclab.iot.video.domain.StreamForwardTaskRow;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/**
 * Mirrors Python {@code stream_forward_health_service.run_stream_forward_health_cycle}.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class StreamForwardHealthService {

    private final StreamForwardTaskRepository taskRepository;
    private final RemoteScheduleSupport remoteScheduleSupport;
    private final StreamForwardRemoteDeployService remoteDeployService;
    private final IotNodeClient iotNodeClient;
    private final VideoProperties videoProperties;

    public boolean isHealthMonitorEnabled() {
        if (!iotNodeClient.isRemoteDeployEnabled()) {
            return false;
        }
        String env = trimToNull(System.getenv("STREAM_FORWARD_HEALTH_MONITOR_ENABLED"));
        if (env != null) {
            return isTruthy(env);
        }
        return videoProperties.getStreamForwardHealth().isEnabled();
    }

    public Map<String, Integer> runHealthCycle() {
        if (!isHealthMonitorEnabled()) {
            return Map.of("checked", 0, "migrated", 0);
        }

        List<StreamForwardTaskRow> tasks = taskRepository.findEnabledRemoteCapable();
        int checked = 0;
        int migratedTotal = 0;

        for (StreamForwardTaskRow task : tasks) {
            if (!remoteScheduleSupport.shouldUseRemoteDeploy(task)) {
                continue;
            }
            checked++;
            try {
                migratedTotal += remoteDeployService.migrateUnhealthyTask(task);
            } catch (Exception e) {
                log.error("推流转发健康检查失败 task_id={}: {}", task.getId(), e.getMessage(), e);
            }
        }

        if (migratedTotal > 0) {
            log.info("推流转发健康检查完成: checked={} migrated={}", checked, migratedTotal);
        }

        Map<String, Integer> stats = new LinkedHashMap<>();
        stats.put("checked", checked);
        stats.put("migrated", migratedTotal);
        return stats;
    }

    private static boolean isTruthy(String value) {
        String normalized = value.trim().toLowerCase(Locale.ROOT);
        return normalized.equals("1")
                || normalized.equals("true")
                || normalized.equals("yes")
                || normalized.equals("on");
    }

    private static String trimToNull(String value) {
        if (value == null) {
            return null;
        }
        String trimmed = value.trim();
        return trimmed.isEmpty() ? null : trimmed;
    }
}
