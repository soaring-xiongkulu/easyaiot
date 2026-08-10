package com.basiclab.iot.video.service;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.dal.AlgorithmTaskRepository;
import com.basiclab.iot.video.domain.AlgorithmTaskRow;
import com.basiclab.iot.video.exception.VideoBusinessException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.charset.Charset;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class AlgorithmTaskLogService {

    private final AlgorithmTaskRepository taskRepository;
    private final VideoProperties videoProperties;

    public Map<String, Object> getExtractorLogs(long taskId, int lines, String date) {
        AlgorithmTaskRow task = requireTask(taskId);
        String taskType = normalizeTaskType(task.getTaskType());
        if (!"realtime".equals(taskType) && !"snap".equals(taskType)) {
            throw new VideoBusinessException(400, "不支持的任务类型: " + taskType);
        }
        return readServiceLogs(task, taskId, lines, date);
    }

    public Map<String, Object> getSorterLogs(long taskId, int lines, String date) {
        AlgorithmTaskRow task = requireTask(taskId);
        String taskType = normalizeTaskType(task.getTaskType());
        if (!"realtime".equals(taskType)) {
            throw new VideoBusinessException(400, "新架构已统一使用实时算法服务，请使用realtime日志接口");
        }
        return readServiceLogs(task, taskId, lines, date);
    }

    public Map<String, Object> getPusherLogs(long taskId, int lines, String date) {
        AlgorithmTaskRow task = requireTask(taskId);
        String taskType = normalizeTaskType(task.getTaskType());
        if (!"realtime".equals(taskType)) {
            throw new VideoBusinessException(400, "新架构已统一使用实时算法服务，请使用realtime日志接口");
        }
        return readServiceLogs(task, taskId, lines, date);
    }

    public Map<String, Object> getRealtimeLogs(long taskId, int lines, String date) {
        AlgorithmTaskRow task = requireTask(taskId);
        String taskType = normalizeTaskType(task.getTaskType());
        if (!"realtime".equals(taskType) && !"snap".equals(taskType) && !"patrol".equals(taskType)) {
            throw new VideoBusinessException(400, "不支持的任务类型: " + taskType);
        }
        Map<String, Object> data = readServiceLogs(task, taskId, lines, date);
        data.put("task_enabled", Boolean.TRUE.equals(task.getIsEnabled()));
        data.put("task_run_status", task.getRunStatus() != null ? task.getRunStatus() : "stopped");
        return data;
    }

    private Map<String, Object> readServiceLogs(AlgorithmTaskRow task, long taskId, int lines, String date) {
        Path logDir = resolveLogDir(task, taskId);
        String logFilename = (date != null && !date.isBlank())
                ? date.trim() + ".log"
                : LocalDate.now().format(DateTimeFormatter.ISO_LOCAL_DATE) + ".log";
        Path logFile = logDir.resolve(logFilename);
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("log_file", logFilename);
        data.put("is_all_file", date == null || date.isBlank());
        if (!Files.isRegularFile(logFile)) {
            data.put("logs", "日志文件不存在: " + logFilename + "\n请等待服务运行后生成日志。");
            data.put("total_lines", 0);
            return data;
        }
        try {
            List<String> allLines = readLines(logFile);
            int from = Math.max(0, allLines.size() - lines);
            List<String> tail = allLines.subList(from, allLines.size());
            data.put("logs", String.join("", tail));
            data.put("total_lines", allLines.size());
            return data;
        } catch (IOException e) {
            throw new VideoBusinessException(500, "读取日志文件失败: " + e.getMessage());
        }
    }

    private List<String> readLines(Path logFile) throws IOException {
        try {
            return Files.readAllLines(logFile);
        } catch (IOException utf8Error) {
            return Files.readAllLines(logFile, Charset.forName("GBK"));
        }
    }

    private Path resolveLogDir(AlgorithmTaskRow task, long taskId) {
        if (task.getServiceLogPath() != null && !task.getServiceLogPath().isBlank()) {
            return Path.of(task.getServiceLogPath());
        }
        return Path.of(videoProperties.getRuntime().getLogsDir(), "task_" + taskId);
    }

    private AlgorithmTaskRow requireTask(long taskId) {
        return taskRepository.findById(taskId)
                .orElseThrow(() -> new VideoBusinessException(400, "算法任务不存在"));
    }

    private String normalizeTaskType(String taskType) {
        String tt = taskType != null ? taskType.trim().toLowerCase() : "realtime";
        if ("snapshot".equals(tt)) {
            return "snap";
        }
        return tt;
    }
}
