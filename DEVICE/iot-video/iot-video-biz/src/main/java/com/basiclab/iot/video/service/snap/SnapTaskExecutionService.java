package com.basiclab.iot.video.service.snap;

import com.basiclab.iot.video.dal.SnapTaskRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.LocalTime;
import java.time.ZoneId;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Executes scheduled snap tasks — aligned with Python {@code execute_snap_task}.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class SnapTaskExecutionService {

    private static final ZoneId SHANGHAI = ZoneId.of("Asia/Shanghai");

    private final SnapTaskRepository snapTaskRepository;
    private final SnapTaskCaptureService snapTaskCaptureService;
    private final ConcurrentHashMap<Integer, Object> taskLocks = new ConcurrentHashMap<>();

    public void execute(int taskId) {
        Object lock = taskLocks.computeIfAbsent(taskId, id -> new Object());
        synchronized (lock) {
            Map<String, Object> task = snapTaskRepository.findById(taskId).orElse(null);
            if (task == null || !Boolean.TRUE.equals(task.get("is_enabled"))) {
                return;
            }
            if (isNightModeSkip(task)) {
                log.debug("任务 {} 处于夜间模式，当前时间不在 23:00-08:00 范围内，跳过执行", task.get("task_name"));
                return;
            }

            String deviceId = task.get("device_id") != null ? String.valueOf(task.get("device_id")) : "";
            int spaceId = task.get("space_id") instanceof Number n ? n.intValue() : 0;

            boolean success;
            String failureReason = null;
            try {
                success = snapTaskCaptureService.captureImage(task, deviceId, spaceId);
                if (!success) {
                    failureReason = "抓拍失败";
                }
            } catch (Exception e) {
                log.error("执行抓拍任务失败 taskId={}: {}", taskId, e.getMessage(), e);
                success = false;
                failureReason = e.getMessage();
            }

            try {
                snapTaskRepository.recordExecutionResult(taskId, success, failureReason);
            } catch (Exception e) {
                log.error("更新抓拍任务统计失败 taskId={}: {}", taskId, e.getMessage(), e);
            }
        }
    }

    private static boolean isNightModeSkip(Map<String, Object> task) {
        if (!Boolean.TRUE.equals(task.get("algorithm_night_mode"))) {
            return false;
        }
        LocalTime now = LocalTime.now(SHANGHAI);
        int hour = now.getHour();
        return hour < 23 && hour >= 8;
    }
}
