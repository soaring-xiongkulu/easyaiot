package com.basiclab.iot.video.service;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.dal.StreamForwardTaskRepository;
import com.basiclab.iot.video.domain.StreamForwardTaskRow;
import com.basiclab.iot.video.process.StreamForwardSupervisor;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;

/**
 * Mirrors Python {@code stream_forward_launcher_service.auto_start_all_tasks} for enabled local tasks.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class StreamForwardAutoStartService {

    private final StreamForwardTaskRepository taskRepository;
    private final StreamForwardService streamForwardService;
    private final StreamForwardSupervisor supervisor;
    private final VideoProperties videoProperties;

    public int startAllEnabledLocalTasks() {
        if (videoProperties.isSkipBackgroundTasks()) {
            return 0;
        }
        List<StreamForwardTaskRow> tasks = taskRepository.findEnabledLocal();
        if (tasks.isEmpty()) {
            log.info("没有需要启动的推流转发任务（is_enabled=true, schedule_policy=local）");
            return 0;
        }
        log.info("发现 {} 个需要启动的推流转发任务，开始启动服务...", tasks.size());
        int successCount = 0;
        for (StreamForwardTaskRow task : tasks) {
            long taskId = task.getId();
            try {
                if (task.getDeviceIds() == null || task.getDeviceIds().isEmpty()) {
                    log.warn("任务 {} ({}) 没有关联的摄像头，跳过", taskId, task.getTaskName());
                    continue;
                }
                if (supervisor.isAlive(taskId)) {
                    log.debug("推流转发任务 {} 已在运行，跳过自动启动", taskId);
                    successCount++;
                    continue;
                }
                Map<String, Object> result = streamForwardService.start(taskId);
                successCount++;
                log.info("推流转发任务 {} ({}) 自动启动成功: {}", taskId, task.getTaskName(), result.get("message"));
            } catch (Exception e) {
                log.error("推流转发任务 {} ({}) 自动启动失败: {}", taskId, task.getTaskName(), e.getMessage(), e);
            }
        }
        log.info("推流转发任务自动启动完成: {}/{}", successCount, tasks.size());
        return successCount;
    }
}
