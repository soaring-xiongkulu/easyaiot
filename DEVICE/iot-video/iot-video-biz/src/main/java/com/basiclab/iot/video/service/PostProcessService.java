package com.basiclab.iot.video.service;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.dal.AlgorithmTaskRepository;
import com.basiclab.iot.video.dal.DeviceDetectionRegionRepository;
import com.basiclab.iot.video.domain.AlgorithmTaskRow;
import com.basiclab.iot.video.exception.VideoBusinessException;
import com.basiclab.iot.video.support.JsonFields;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class PostProcessService {

    private final AlgorithmTaskRepository taskRepository;
    private final DeviceDetectionRegionRepository regionRepository;
    private final VideoProperties videoProperties;

    public Map<String, Object> getStatus(long taskId) {
        AlgorithmTaskRow task = taskRepository.findById(taskId)
                .orElseThrow(() -> new VideoBusinessException(404, "任务不存在"));
        String scriptName = defaultScriptName(task.getPostProcessScript());
        Path workspace = taskWorkspaceDir(taskId);
        Path scriptPath = workspace.resolve(scriptName);
        Map<String, Object> status = new LinkedHashMap<>();
        status.put("task_id", taskId);
        status.put("post_process_enabled", Boolean.TRUE.equals(task.getPostProcessEnabled()));
        status.put("post_process_script", scriptName);
        status.put("post_process_replicas", task.getPostProcessReplicas() != null ? task.getPostProcessReplicas() : 1);
        status.put("script_exists", Files.isRegularFile(scriptPath));
        status.put("workspace_path", workspace.toString());
        status.put("workspace_root", videoProperties.getPostProcess().getWorkspaceRoot());
        status.put("enqueue_count", PostProcessEnqueueAudit.enqueueCount());
        status.put("enqueue_url", PostProcessEnqueueAudit.lastEnqueueUrl());
        status.put("enqueue_ok", PostProcessEnqueueAudit.lastEnqueueOk());
        return status;
    }

    public boolean taskNeedsSinkProcessing(AlgorithmTaskRow task) {
        if (task == null) {
            return false;
        }
        return Boolean.TRUE.equals(task.getPostProcessEnabled())
                || Boolean.TRUE.equals(task.getPoseAnalysisEnabled())
                || Boolean.TRUE.equals(task.getPoseIntentEnabled());
    }

    public Map<String, Object> buildTaskContext(
            AlgorithmTaskRow task,
            String deviceId,
            String deviceName,
            int frameNumber,
            double timestamp,
            List<Map<String, Object>> detections,
            List<Map<String, Object>> trackedDetections,
            List<Map<String, Object>> regions,
            String alertImagePath,
            String correlationId
    ) {
        Map<String, Object> ctx = new LinkedHashMap<>();
        ctx.put("task_id", task.getId());
        ctx.put("task_name", task.getTaskName());
        ctx.put("task_code", task.getTaskCode());
        ctx.put("task_type", task.getTaskType() != null ? task.getTaskType() : "realtime");
        ctx.put("device_id", deviceId);
        ctx.put("device_name", deviceName);
        ctx.put("frame_number", frameNumber);
        ctx.put("timestamp", timestamp);
        ctx.put("detections", detections != null ? detections : List.of());
        ctx.put("tracked_detections", trackedDetections != null ? trackedDetections : detections);
        ctx.put("tracking_enabled", Boolean.TRUE.equals(task.getTrackingEnabled()));
        ctx.put("regions", regions != null ? regions : List.of());
        ctx.put("model_ids", parseModelIds(task.getModelIds()));
        ctx.put("alert_class_names", JsonFields.parseJsonList(task.getAlertClassNames()));
        boolean poseEnabled = Boolean.TRUE.equals(task.getPoseAnalysisEnabled())
                || Boolean.TRUE.equals(task.getPoseIntentEnabled());
        ctx.put("pose_analysis_enabled", poseEnabled);
        ctx.put("pose_intent_enabled", Boolean.TRUE.equals(task.getPoseIntentEnabled()));
        if (alertImagePath != null) {
            ctx.put("alert_image_path", alertImagePath);
        }
        if (correlationId != null) {
            ctx.put("correlation_id", correlationId);
        }
        return ctx;
    }

    public List<Map<String, Object>> loadRegionsForDevice(String deviceId) {
        return regionRepository.listByDevice(deviceId);
    }

    public void ensureWorkspace(long taskId, String scriptName) {
        try {
            Path workspace = taskWorkspaceDir(taskId);
            Files.createDirectories(workspace);
            Path scriptPath = workspace.resolve(scriptName);
            if (!Files.isRegularFile(scriptPath)) {
                Files.writeString(scriptPath, POST_PROCESS_TEMPLATE);
            }
        } catch (Exception ignored) {
            // workspace optional for certify enqueue path
        }
    }

    private Path taskWorkspaceDir(long taskId) {
        return Path.of(videoProperties.getPostProcess().getWorkspaceRoot(), "task_" + taskId);
    }

    private static String defaultScriptName(String script) {
        if (script == null || script.isBlank()) {
            return "post_process.py";
        }
        return script.trim();
    }

    private static List<Integer> parseModelIds(String raw) {
        List<Object> parsed = JsonFields.parseJsonList(raw);
        List<Integer> ids = new ArrayList<>();
        for (Object item : parsed) {
            if (item == null) {
                continue;
            }
            try {
                ids.add(Integer.parseInt(String.valueOf(item)));
            } catch (NumberFormatException ignored) {
                // skip invalid
            }
        }
        return ids;
    }

    private static final String POST_PROCESS_TEMPLATE = """
def process(ctx):
    return {"counts": {}}
""";
}
