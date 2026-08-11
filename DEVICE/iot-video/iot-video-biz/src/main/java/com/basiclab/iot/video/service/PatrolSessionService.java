package com.basiclab.iot.video.service;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.dal.AlgorithmTaskRepository;
import com.basiclab.iot.video.dal.DeviceDirectoryRepository;
import com.basiclab.iot.video.dal.DeviceRepository;
import com.basiclab.iot.video.dal.PatrolSessionRepository;
import com.basiclab.iot.video.domain.AlgorithmTaskRow;
import com.basiclab.iot.video.domain.DeviceDirectoryRow;
import com.basiclab.iot.video.domain.PatrolSessionRow;
import com.basiclab.iot.video.exception.VideoBusinessException;
import com.basiclab.iot.video.process.PatrolSupervisor;
import com.basiclab.iot.video.service.camera.Gb28181SyncService;
import com.basiclab.iot.video.support.JsonFields;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.nio.file.Path;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

@Slf4j
@Service
@RequiredArgsConstructor
public class PatrolSessionService {

    private static final int DEFAULT_MAX_DEVICES = 128;
    private static final int DEFAULT_MAX_SESSIONS = 4;
    private static final String DEFAULT_DIRECTORY_NAME = "默认分组";

    private final PatrolSessionRepository sessionRepository;
    private final AlgorithmTaskRepository algorithmTaskRepository;
    private final DeviceDirectoryRepository directoryRepository;
    private final DeviceRepository deviceRepository;
    private final PatrolProgressHub progressHub;
    private final PatrolSupervisor supervisor;
    private final VideoProperties videoProperties;
    private final Gb28181SyncService gb28181SyncService;

    private final Set<Long> startingSessions = ConcurrentHashMap.newKeySet();

    public Map<String, Object> createSession(Map<String, Object> data) {
        List<String> deviceIds = validateDevices(extractStringList(data.get("device_ids")));
        List<Object> modelIds = extractModelIds(data);
        if (modelIds.isEmpty()) {
            throw new VideoBusinessException(400, "模型列表不能为空");
        }

        Long algorithmTaskId = toLongOrNull(data.get("algorithm_task_id"));
        if (algorithmTaskId != null) {
            AlgorithmTaskRow task = algorithmTaskRepository.findById(algorithmTaskId)
                    .orElseThrow(() -> new VideoBusinessException(400, "算法任务不存在: " + algorithmTaskId));
            if (modelIds.isEmpty() && task.getModelIds() != null && !task.getModelIds().isBlank()) {
                modelIds = JsonFields.parseJsonList(task.getModelIds());
            }
        }

        int intervalSec = Math.max(3, toInt(data.get("interval_sec"), 10));
        int poolSize = Math.max(1, Math.min(toInt(data.get("pool_size"), 4), 16));
        String sessionName = str(data.get("session_name"));
        if (sessionName.isEmpty()) {
            sessionName = "巡检-" + LocalDateTime.now().format(DateTimeFormatter.ofPattern("MMddHHmm"));
        }

        Map<String, Object> progress = new LinkedHashMap<>();
        for (String did : deviceIds) {
            progress.put(did, Map.of());
        }

        PatrolSessionRow row = new PatrolSessionRow();
        row.setSessionName(sessionName);
        row.setPatrolMode("pool");
        row.setIntervalSec(intervalSec);
        row.setPoolSize(poolSize);
        row.setDeviceIdsJson(PatrolSessionRow.toJsonList(deviceIds));
        row.setModelIdsJson(PatrolSessionRow.toJsonList(modelIds));
        row.setAlgorithmTaskId(algorithmTaskId);
        row.setAlertEventEnabled(toBool(data.get("alert_event_enabled"), true));
        row.setAlertEventSuppressTime(toInt(data.get("alert_event_suppress_time"), 5));
        row.setFaceDetectionEnabled(toBool(data.get("face_detection_enabled"), true));
        row.setPlateDetectionEnabled(toBool(data.get("plate_detection_enabled"), true));
        row.setStatus("stopped");
        row.setProgressJson(PatrolSessionRow.toJsonObject(progress));

        long id = sessionRepository.insert(row);
        return sessionRepository.findById(id)
                .orElseThrow(() -> new VideoBusinessException(500, "创建巡检会话失败"))
                .toMap();
    }

    public Map<String, Object> getSession(long sessionId) {
        return sessionRepository.findById(sessionId)
                .orElseThrow(() -> new VideoBusinessException(404, "巡检会话不存在"))
                .toMap();
    }

    public Map<String, Object> startSession(long sessionId) {
        PatrolSessionRow session = sessionRepository.findById(sessionId)
                .orElseThrow(() -> new VideoBusinessException(400, "巡检会话不存在"));

        if ("running".equals(session.getStatus()) && supervisor.isAlive(sessionId)) {
            return Map.of("ok", true, "message", "巡检已在运行", "data", session.toMap());
        }

        if (supervisor.countAlive() >= maxSessions()) {
            return Map.of("ok", false, "message", "同时运行的巡检会话不能超过 " + maxSessions() + " 个", "data", session.toMap());
        }

        if (!startingSessions.add(sessionId)) {
            return Map.of("ok", true, "message", "巡检正在启动中", "data", session.toMap());
        }

        try {
            stopSession(sessionId, false);
            Path logDir = Path.of(videoProperties.getRuntime().getLogsDir(), "patrol_" + sessionId);
            try {
                supervisor.start(sessionId, logDir);
                sessionRepository.updateRunning(sessionId, logDir.toString());
                broadcast(sessionId, "status");
                PatrolSessionRow updated = sessionRepository.findById(sessionId).orElse(session);
                return Map.of("ok", true, "message", "巡检已启动", "data", updated.toMap());
            } catch (Exception e) {
                sessionRepository.updateError(sessionId, e.getMessage());
                PatrolSessionRow updated = sessionRepository.findById(sessionId).orElse(session);
                return Map.of("ok", false, "message", e.getMessage(), "data", updated.toMap());
            }
        } finally {
            startingSessions.remove(sessionId);
        }
    }

    public Map<String, Object> stopSession(long sessionId) {
        return stopSession(sessionId, true);
    }

    public Map<String, Object> stopSession(long sessionId, boolean updateStatus) {
        supervisor.stop(sessionId);
        if (updateStatus) {
            sessionRepository.updateStopped(sessionId);
            broadcast(sessionId, "status");
        }
        PatrolSessionRow session = sessionRepository.findById(sessionId).orElse(null);
        return Map.of("ok", true, "message", "巡检已停止", "data", session != null ? session.toMap() : null);
    }

    public Map<String, Object> buildStats(long sessionId) {
        PatrolSessionRow session = sessionRepository.findById(sessionId)
                .orElseThrow(() -> new VideoBusinessException(404, "巡检会话不存在"));
        return buildStatsPayload(session);
    }

    public SseEmitter subscribeEvents(long sessionId) {
        PatrolSessionRow session = sessionRepository.findById(sessionId)
                .orElseThrow(() -> new VideoBusinessException(404, "巡检会话不存在"));
        return progressHub.subscribe(sessionId, buildStatsPayload(session));
    }

    public Map<String, Object> patchSession(long sessionId, Map<String, Object> data) {
        PatrolSessionRow session = sessionRepository.findById(sessionId)
                .orElseThrow(() -> new VideoBusinessException(404, "巡检会话不存在"));

        sessionRepository.updatePatch(sessionId, data);
        broadcast(sessionId, "progress");
        return sessionRepository.findById(sessionId).orElse(session).toMap();
    }

    public boolean receiveHeartbeat(Map<String, Object> data) {
        if (data == null) {
            return false;
        }
        Object rawId = data.get("session_id");
        if (rawId == null) {
            rawId = data.get("patrol_session_id");
        }
        if (rawId == null) {
            return false;
        }
        long sessionId = Long.parseLong(String.valueOf(rawId));
        PatrolSessionRow session = sessionRepository.findById(sessionId).orElse(null);
        if (session == null) {
            return false;
        }

        String serverIp = data.get("server_ip") != null ? String.valueOf(data.get("server_ip")) : null;
        Integer processId = toIntOrNull(data.get("process_id"));
        String progressJson = null;
        if (data.get("progress") != null) {
            progressJson = PatrolSessionRow.toJsonObject(data.get("progress"));
        }
        Integer totalPatrols = toIntOrNull(data.get("total_patrols"));
        Integer totalDetections = toIntOrNull(data.get("total_detections"));
        String status = "stopped".equals(session.getStatus()) ? null : "running";

        sessionRepository.updateHeartbeat(
                sessionId, serverIp, processId, progressJson, totalPatrols, totalDetections, status
        );
        broadcast(sessionId, "progress");
        return true;
    }

    public Map<String, Object> resolveDirectoryDevices(int directoryId, boolean includeChildren) {
        DeviceDirectoryRow directory = directoryRepository.findById(directoryId)
                .orElseThrow(() -> new VideoBusinessException(400, "目录不存在: ID=" + directoryId));

        if (isDefaultDirectory(directory)) {
            try {
                gb28181SyncService.syncFromWvp(false, null, null);
            } catch (Exception exc) {
                log.warn("目录巡检设备列表加载前国标同步失败: {}", exc.getMessage());
            }
        }

        List<Integer> dirIds = collectDirectoryIds(directoryId, includeChildren);
        List<String> deviceIds = deviceRepository.listIdsByDirectoryIds(dirIds);

        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("directory_id", directoryId);
        payload.put("directory_name", directory.getName());
        payload.put("device_ids", deviceIds);
        payload.put("total", deviceIds.size());
        return payload;
    }

    public void broadcast(long sessionId, String eventType) {
        sessionRepository.findById(sessionId).ifPresent(session ->
                progressHub.publish(sessionId, eventType, buildStatsPayload(session))
        );
    }

    private Map<String, Object> buildStatsPayload(PatrolSessionRow session) {
        Map<String, Object> data = new LinkedHashMap<>(session.toMap());
        @SuppressWarnings("unchecked")
        List<Object> deviceIds = (List<Object>) data.getOrDefault("device_ids", List.of());
        @SuppressWarnings("unchecked")
        Map<String, Object> progress = (Map<String, Object>) data.getOrDefault("progress", Map.of());
        int done = 0;
        for (Object did : deviceIds) {
            @SuppressWarnings("unchecked")
            Map<String, Object> entry = (Map<String, Object>) progress.get(String.valueOf(did));
            if (entry != null && entry.get("last_patrol_at") != null) {
                done++;
            }
        }
        int total = deviceIds.size();
        data.put("completed_devices", done);
        data.put("total_devices", total);
        data.put("completion_ratio", total > 0 ? (double) done / total : 0.0);
        return data;
    }

    private List<Integer> collectDirectoryIds(int directoryId, boolean includeChildren) {
        List<Integer> ids = new ArrayList<>();
        ids.add(directoryId);
        if (!includeChildren) {
            return ids;
        }
        collectChildren(directoryId, ids);
        return ids;
    }

    private void collectChildren(int parentId, List<Integer> ids) {
        for (DeviceDirectoryRow child : directoryRepository.findByParentId(parentId)) {
            ids.add(child.getId());
            collectChildren(child.getId(), ids);
        }
    }

    private boolean isDefaultDirectory(DeviceDirectoryRow directory) {
        return directory != null
                && DEFAULT_DIRECTORY_NAME.equals(directory.getName())
                && directory.getParentId() == null;
    }

    private List<String> validateDevices(List<String> deviceIds) {
        if (deviceIds == null || deviceIds.isEmpty()) {
            throw new VideoBusinessException(400, "设备列表不能为空");
        }
        int max = maxDevices();
        if (deviceIds.size() > max) {
            throw new VideoBusinessException(400, "单会话设备数不能超过 " + max);
        }
        Set<String> unique = new LinkedHashSet<>();
        for (String did : deviceIds) {
            String s = did != null ? did.trim() : "";
            if (!s.isEmpty()) {
                unique.add(s);
            }
        }
        if (unique.isEmpty()) {
            throw new VideoBusinessException(400, "设备列表不能为空");
        }
        return new ArrayList<>(unique);
    }

    private List<Object> extractModelIds(Map<String, Object> data) {
        Object raw = data.get("model_ids");
        if (raw instanceof List<?> list) {
            return new ArrayList<>(list);
        }
        return JsonFields.parseJsonList(raw != null ? String.valueOf(raw) : null);
    }

    @SuppressWarnings("unchecked")
    private List<String> extractStringList(Object raw) {
        if (raw instanceof List<?> list) {
            List<String> out = new ArrayList<>();
            for (Object item : list) {
                if (item != null) {
                    out.add(String.valueOf(item));
                }
            }
            return out;
        }
        return JsonFields.parseJsonList(raw != null ? String.valueOf(raw) : null)
                .stream().map(String::valueOf).toList();
    }

    private int maxDevices() {
        String env = System.getenv("PATROL_MAX_DEVICES");
        if (env != null && !env.isBlank()) {
            try {
                return Integer.parseInt(env.trim());
            } catch (NumberFormatException ignored) {
                return DEFAULT_MAX_DEVICES;
            }
        }
        return DEFAULT_MAX_DEVICES;
    }

    private int maxSessions() {
        String env = System.getenv("PATROL_MAX_SESSIONS");
        if (env != null && !env.isBlank()) {
            try {
                return Integer.parseInt(env.trim());
            } catch (NumberFormatException ignored) {
                return DEFAULT_MAX_SESSIONS;
            }
        }
        return DEFAULT_MAX_SESSIONS;
    }

    private static String str(Object value) {
        return value != null ? String.valueOf(value).trim() : "";
    }

    private static int toInt(Object value, int defaultValue) {
        if (value == null || "".equals(String.valueOf(value))) {
            return defaultValue;
        }
        return Integer.parseInt(String.valueOf(value));
    }

    private static Integer toIntOrNull(Object value) {
        if (value == null || "".equals(String.valueOf(value))) {
            return null;
        }
        try {
            return Integer.parseInt(String.valueOf(value));
        } catch (NumberFormatException e) {
            return null;
        }
    }

    private static Long toLongOrNull(Object value) {
        if (value == null || "".equals(String.valueOf(value))) {
            return null;
        }
        return Long.parseLong(String.valueOf(value));
    }

    private static boolean toBool(Object value, boolean defaultValue) {
        if (value == null) {
            return defaultValue;
        }
        if (value instanceof Boolean bool) {
            return bool;
        }
        String s = String.valueOf(value).trim().toLowerCase();
        if ("0".equals(s) || "false".equals(s)) {
            return false;
        }
        if ("1".equals(s) || "true".equals(s)) {
            return true;
        }
        return defaultValue;
    }
}
