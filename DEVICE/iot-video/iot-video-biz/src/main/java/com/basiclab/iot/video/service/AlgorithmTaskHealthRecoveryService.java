package com.basiclab.iot.video.service;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.dal.AlgorithmTaskRepository;
import com.basiclab.iot.video.domain.AlgorithmTaskRow;
import com.basiclab.iot.video.process.AlgorithmRuntimeSupervisor;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;

/**
 * Mirrors Python {@code recover_unhealthy_algorithm_tasks} for enabled local tasks.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class AlgorithmTaskHealthRecoveryService {

    private final AlgorithmTaskRepository taskRepository;
    private final AlgorithmTaskLifecycleService lifecycleService;
    private final AlgorithmRuntimeSupervisor supervisor;
    private final VideoProperties videoProperties;

    public int recoverUnhealthyEnabledLocalTasks() {
        if (videoProperties.isSkipBackgroundTasks() || !videoProperties.getHealthMonitor().isEnabled()) {
            return 0;
        }
        List<AlgorithmTaskRow> tasks = taskRepository.findEnabledLocal();
        int recovered = 0;
        for (AlgorithmTaskRow task : tasks) {
            if (isHealthy(task)) {
                continue;
            }
            try {
                log.info(
                        "算法任务 {} ({}) 服务未运行或心跳超时，尝试恢复",
                        task.getId(),
                        task.getTaskName()
                );
                Map<String, Object> result = lifecycleService.start(task.getId());
                recovered++;
                log.info("算法任务 {} 恢复成功: {}", task.getId(), result.get("message"));
            } catch (Exception e) {
                log.error("算法任务 {} 恢复失败: {}", task.getId(), e.getMessage(), e);
            }
        }
        if (recovered > 0) {
            log.info("算法任务健康恢复完成: recovered={}", recovered);
        }
        return recovered;
    }

    boolean isHealthy(AlgorithmTaskRow task) {
        long taskId = task.getId();
        // Local ProcessBuilder is authoritative: a dead process is unhealthy even if DB
        // still says run_status=running with a fresh heartbeat (crash/restart window).
        if (supervisor.isAlive(taskId)) {
            return true;
        }
        return false;
    }
}
