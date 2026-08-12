package com.basiclab.iot.video.service;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.dal.DeviceRepository;
import com.basiclab.iot.video.domain.DeviceRow;
import com.basiclab.iot.video.domain.PatrolSessionRow;
import com.basiclab.iot.video.exception.VideoBusinessException;
import com.basiclab.iot.video.support.JsonFields;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Builds RUNTIME ini for UI patrol sessions → C++ {@code PatrolScheduler}.
 * Does not rewrite RUNTIME inference; only wires session config.
 */
@Service
@RequiredArgsConstructor
public class PatrolRuntimeIniService {

    private final DeviceRepository deviceRepository;
    private final VideoProperties videoProperties;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public record PatrolIni(String iniPath, String runtimeBin, String content) {}

    public PatrolIni generate(PatrolSessionRow session, Path logDir) throws IOException {
        List<Object> rawIds = JsonFields.parseJsonList(session.getDeviceIdsJson());
        List<String> deviceIds = rawIds.stream().map(String::valueOf).filter(s -> !s.isBlank()).toList();
        if (deviceIds.isEmpty()) {
            throw new VideoBusinessException(400, "巡检会话未绑定设备");
        }
        List<Map<String, String>> devices = new ArrayList<>();
        for (String deviceId : deviceIds) {
            DeviceRow row = deviceRepository.findById(deviceId)
                    .orElseThrow(() -> new VideoBusinessException(400, "设备不存在: " + deviceId));
            String source = firstNonBlank(row.getSource(), row.getRtspDirect());
            if (source == null || source.isBlank()) {
                throw new VideoBusinessException(400, "设备 " + deviceId + " 无可用 RTSP/source");
            }
            Map<String, String> d = new LinkedHashMap<>();
            d.put("device_id", deviceId);
            d.put("device_name", firstNonBlank(row.getName(), deviceId));
            d.put("rtsp_url", normalizeRtspUrl(source));
            devices.add(d);
        }

        Files.createDirectories(logDir);
        Path alertImageDir = logDir.resolve("alerts");
        Files.createDirectories(alertImageDir);
        Path configDir = Path.of(videoProperties.getRuntime().getConfigDir());
        Files.createDirectories(configDir);
        Path iniPath = configDir.resolve("patrol_session_" + session.getId() + ".ini");
        Path logPath = logDir.resolve("runtime.log");

        String modelPath = resolveModelPath();
        String classesPath = resolveClassesPath();
        String hookUrl = videoProperties.getRuntime().getHookBaseUrl() + "/video/alert/hook";
        String heartbeatUrl = videoProperties.getRuntime().getHeartbeatBaseUrl() + "/video/patrol/heartbeat";
        int controlPort = 9000 + (int) (session.getId() % 1000);
        int interval = session.getIntervalSec() != null ? Math.max(3, session.getIntervalSec()) : 10;
        int poolSize = session.getPoolSize() != null ? Math.max(1, Math.min(16, session.getPoolSize())) : 4;
        String mode = session.getPatrolMode() != null && !session.getPatrolMode().isBlank()
                ? session.getPatrolMode() : "pool";
        boolean alertEnabled = !Boolean.FALSE.equals(session.getAlertEventEnabled());
        int cooldown = session.getAlertEventSuppressTime() != null ? session.getAlertEventSuppressTime() : 5;
        String devicesJson = objectMapper.writeValueAsString(devices);

        String primary = devices.get(0).get("rtsp_url");
        String content = """
                # Auto-generated for patrol session → RUNTIME PatrolScheduler
                [video]
                rtsp_url=%s
                rtmp_url=
                width=1920
                height=1080
                fps=25
                devices_json=%s

                [ai]
                enable=true
                model_path=%s
                classes_path=%s
                threads=2
                frame_skip=12
                prefer_gpu=true
                force_cpu=false
                gpu_device_id=0

                [alarm]
                enable=%s
                hook_url=%s
                confidence_threshold=0.5
                cooldown_time=%d
                image_dir=%s

                [task]
                id=%d
                control_port=%d

                [video_task]
                device_id=%s
                device_name=%s
                task_type=patrol
                algorithm_name=patrol
                alert_hook_url=%s
                heartbeat_url=%s
                heartbeat_interval_sec=5
                log_path=%s
                alert_image_dir=%s
                headless=true
                frame_skip=12
                patrol_mode=%s
                patrol_interval_sec=%d
                patrol_pool_size=%d
                devices_json=%s

                [features]
                enable_rtmp=false
                enable_draw=true
                enable_alarm=%s
                """.formatted(
                primary,
                devicesJson,
                modelPath,
                classesPath,
                alertEnabled ? "true" : "false",
                hookUrl,
                cooldown,
                alertImageDir.toString().replace('\\', '/'),
                session.getId(),
                controlPort,
                devices.get(0).get("device_id"),
                devices.get(0).get("device_name"),
                hookUrl,
                heartbeatUrl,
                logPath.toString().replace('\\', '/'),
                alertImageDir.toString().replace('\\', '/'),
                mode,
                interval,
                poolSize,
                devicesJson,
                alertEnabled ? "true" : "false"
        );

        Files.writeString(iniPath, content);
        String runtimeBin = resolveRuntimeBin();
        return new PatrolIni(iniPath.toString(), runtimeBin, content);
    }

    public String resolveRuntimeBin() {
        String env = System.getenv("RUNTIME_BIN");
        if (env != null && !env.isBlank() && Files.isRegularFile(Path.of(env))) {
            return env;
        }
        Path root = repoRoot();
        List<Path> candidates = List.of(
                Path.of("F:/acme/.worktrees/video-java/RUNTIME/build-win/Release/RUNTIME.exe"),
                root.resolve("RUNTIME/build-win/Release/RUNTIME.exe"),
                root.resolve("RUNTIME/build/Release/RUNTIME.exe"),
                root.resolve("RUNTIME/build/RUNTIME")
        );
        for (Path p : candidates) {
            if (Files.isRegularFile(p)) {
                return p.toString();
            }
        }
        throw new VideoBusinessException(400,
                "RUNTIME 二进制不存在。请编译 worktree RUNTIME 或设置 RUNTIME_BIN");
    }

    private String resolveModelPath() {
        Path root = repoRoot();
        List<Path> candidates = List.of(
                root.resolve("RUNTIME/models/yolov11n.onnx"),
                Path.of("F:/acme/RUNTIME/models/yolov11n.onnx"),
                Path.of("F:/acme/.worktrees/video-java/RUNTIME/models/yolov11n.onnx")
        );
        for (Path p : candidates) {
            if (Files.isRegularFile(p)) {
                return p.toString().replace('\\', '/');
            }
        }
        String env = System.getenv("RUNTIME_MODEL_PATH");
        if (env != null && !env.isBlank()) {
            return env.replace('\\', '/');
        }
        return candidates.get(0).toString().replace('\\', '/');
    }

    private String resolveClassesPath() {
        Path root = repoRoot();
        List<Path> candidates = List.of(
                root.resolve("RUNTIME/models/coco.names"),
                Path.of("F:/acme/RUNTIME/models/coco.names"),
                Path.of("F:/acme/.worktrees/video-java/RUNTIME/models/coco.names")
        );
        for (Path p : candidates) {
            if (Files.isRegularFile(p)) {
                return p.toString().replace('\\', '/');
            }
        }
        return candidates.get(0).toString().replace('\\', '/');
    }

    private Path repoRoot() {
        String configured = videoProperties.getRuntime().getRepoRoot();
        if (configured != null && !configured.isBlank()) {
            return Path.of(configured.trim());
        }
        String envRoot = System.getenv("ACME_ROOT");
        if (envRoot != null && !envRoot.isBlank()) {
            return Path.of(envRoot.trim());
        }
        return Path.of("F:/acme/.worktrees/video-java");
    }

    private static String normalizeRtspUrl(String url) {
        if (url == null) {
            return null;
        }
        String trimmed = url.trim();
        if (trimmed.regionMatches(true, 0, "file://", 0, 7)) {
            return trimmed.substring(7);
        }
        return trimmed;
    }

    private static String firstNonBlank(String... values) {
        if (values == null) {
            return null;
        }
        for (String v : values) {
            if (v != null && !v.isBlank()) {
                return v.trim();
            }
        }
        return null;
    }
}
