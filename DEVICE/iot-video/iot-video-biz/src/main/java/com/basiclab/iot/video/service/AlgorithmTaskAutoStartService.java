package com.basiclab.iot.video.service;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.dal.AlgorithmTaskRepository;
import com.basiclab.iot.video.domain.AlgorithmTaskRow;
import com.basiclab.iot.video.process.AlgorithmRuntimeSupervisor;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Locale;
import java.util.Map;

/**
 * Mirrors Python {@code auto_start_all_tasks} for enabled local algorithm tasks on startup.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class AlgorithmTaskAutoStartService {

    private final AlgorithmTaskRepository taskRepository;
    private final AlgorithmTaskLifecycleService lifecycleService;
    private final AlgorithmRuntimeSupervisor supervisor;
    private final VideoProperties videoProperties;

    public int startAllEnabledLocalTasks() {
        if (videoProperties.isSkipBackgroundTasks()) {
            return 0;
        }
        List<AlgorithmTaskRow> tasks = taskRepository.findEnabledLocal();
        if (tasks.isEmpty()) {
            log.info("没有启用的算法任务，跳过服务启动");
            return 0;
        }
        log.info("发现 {} 个启用的算法任务，开始启动服务...", tasks.size());
        int successCount = 0;
        for (AlgorithmTaskRow task : tasks) {
            long taskId = task.getId();
            try {
                if (supervisor.isAlive(taskId)) {
                    log.debug("任务 {} ({}) 已在运行，跳过自动启动", taskId, task.getTaskName());
                    successCount++;
                    continue;
                }
                if (!canAutoStart(task)) {
                    continue;
                }
                Map<String, Object> result = lifecycleService.start(taskId);
                successCount++;
                log.info("任务 {} ({}) 自动启动成功: {}", taskId, task.getTaskName(), result.get("message"));
            } catch (Exception e) {
                log.error("任务 {} ({}) 自动启动失败: {}", taskId, task.getTaskName(), e.getMessage(), e);
            }
        }
        log.info("算法任务自动启动完成: {}/{}", successCount, tasks.size());
        return successCount;
    }

    private boolean canAutoStart(AlgorithmTaskRow task) {
        String taskType = normalizeTaskType(task.getTaskType());
        if (isBlankModelIds(task.getModelIds())) {
            log.warn("任务 {} ({}) 缺少模型 ID 配置，跳过", task.getId(), task.getTaskName());
            return false;
        }
        if ("snap".equals(taskType) || "patrol".equals(taskType)) {
            if (task.getDeviceIds() == null || task.getDeviceIds().isEmpty()) {
                log.warn("任务 {} ({}) 没有关联的设备，跳过", task.getId(), task.getTaskName());
                return false;
            }
            return true;
        }
        if ("realtime".equals(taskType)) {
            return true;
        }
        log.warn("任务 {} ({}) 未知任务类型 {}，跳过", task.getId(), task.getTaskName(), taskType);
        return false;
    }

    private static String normalizeTaskType(String taskType) {
        String tt = taskType != null ? taskType.trim().toLowerCase(Locale.ROOT) : "realtime";
        if ("snapshot".equals(tt)) {
            return "snap";
        }
        return tt;
    }

    private static boolean isBlankModelIds(String modelIds) {
        if (modelIds == null || modelIds.isBlank()) {
            return true;
        }
        String trimmed = modelIds.trim();
        return "[]".equals(trimmed) || "null".equalsIgnoreCase(trimmed);
    }
}
