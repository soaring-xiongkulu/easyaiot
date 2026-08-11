package com.basiclab.iot.video.service.snap;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.dal.SnapTaskRepository;
import com.basiclab.iot.video.support.SnapCronSupport;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.concurrent.ThreadPoolTaskScheduler;
import org.springframework.scheduling.support.CronTrigger;
import org.springframework.stereotype.Service;

import javax.annotation.PreDestroy;
import java.time.ZoneId;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ScheduledFuture;

/**
 * Per-task cron scheduler — aligned with Python {@code snap_task_service} APScheduler jobs
 * and {@code init_all_tasks}.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class SnapTaskSchedulerService {

    private static final ZoneId SHANGHAI = ZoneId.of("Asia/Shanghai");

    private final SnapTaskRepository snapTaskRepository;
    private final SnapTaskExecutionService executionService;
    private final VideoProperties videoProperties;

    private final ConcurrentHashMap<Integer, ScheduledFuture<?>> runningTasks = new ConcurrentHashMap<>();
    private final ThreadPoolTaskScheduler taskScheduler = createScheduler();

    private static ThreadPoolTaskScheduler createScheduler() {
        ThreadPoolTaskScheduler scheduler = new ThreadPoolTaskScheduler();
        scheduler.setPoolSize(4);
        scheduler.setThreadNamePrefix("snap-task-");
        scheduler.setRemoveOnCancelPolicy(true);
        scheduler.initialize();
        return scheduler;
    }

    /**
     * Load all enabled tasks into the scheduler (Python {@code init_all_tasks}).
     */
    public int initAllTasks() {
        if (!isSchedulerEnabled()) {
            log.debug("抓拍任务调度器已禁用，跳过 init_all_tasks");
            return 0;
        }
        List<Map<String, Object>> tasks = snapTaskRepository.listEnabled();
        int scheduled = 0;
        for (Map<String, Object> task : tasks) {
            int taskId = ((Number) task.get("id")).intValue();
            if (addTaskToScheduler(taskId)) {
                scheduled++;
            }
        }
        List<Integer> scheduledIds = new ArrayList<>(runningTasks.keySet());
        scheduledIds.sort(Integer::compareTo);
        log.info("抓拍任务调度器初始化完成: enabled={}, scheduled={}, scheduled_task_ids={}",
                tasks.size(), scheduled, scheduledIds);
        return scheduled;
    }

    /** Scheduled task ids for diagnostics / code-parity evidence (Python {@code _running_tasks}). */
    public List<Integer> getScheduledTaskIds() {
        List<Integer> ids = new ArrayList<>(runningTasks.keySet());
        ids.sort(Integer::compareTo);
        return ids;
    }

    public boolean addTaskToScheduler(int taskId) {
        if (!isSchedulerEnabled()) {
            return false;
        }
        Map<String, Object> task = snapTaskRepository.findById(taskId).orElse(null);
        if (task == null || !Boolean.TRUE.equals(task.get("is_enabled"))) {
            return false;
        }
        removeTaskFromScheduler(taskId);

        String cronExpression = task.get("cron_expression") != null
                ? String.valueOf(task.get("cron_expression")).trim()
                : "0 */5 * * * *";
        try {
            String springCron = SnapCronSupport.normalizeForSpring(cronExpression);
            CronTrigger trigger = new CronTrigger(springCron, SHANGHAI);
            ScheduledFuture<?> future = taskScheduler.schedule(
                    () -> executionService.execute(taskId),
                    trigger
            );
            runningTasks.put(taskId, future);
            log.info("任务已添加到调度器: {} (ID={})", task.get("task_name"), taskId);
            return true;
        } catch (Exception e) {
            log.error("添加任务到调度器失败 taskId={}: {}", taskId, e.getMessage(), e);
            return false;
        }
    }

    public void removeTaskFromScheduler(int taskId) {
        ScheduledFuture<?> future = runningTasks.remove(taskId);
        if (future != null) {
            future.cancel(false);
            log.info("任务已从调度器移除: ID={}", taskId);
        }
    }

    public void rescheduleTask(int taskId) {
        removeTaskFromScheduler(taskId);
        addTaskToScheduler(taskId);
    }

    public boolean isSchedulerEnabled() {
        return !videoProperties.isSkipBackgroundTasks()
                && videoProperties.getSnapTaskScheduler().isEnabled();
    }

    @PreDestroy
    public void shutdown() {
        runningTasks.keySet().forEach(this::removeTaskFromScheduler);
        taskScheduler.shutdown();
        log.info("抓拍任务调度器已关闭");
    }
}
