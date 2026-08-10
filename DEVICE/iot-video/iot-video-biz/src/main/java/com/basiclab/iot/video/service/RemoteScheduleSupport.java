package com.basiclab.iot.video.service;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.domain.AlgorithmTaskRow;
import com.basiclab.iot.video.domain.StreamForwardTaskRow;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Locale;
import java.util.Map;

@Component
@RequiredArgsConstructor
public class RemoteScheduleSupport {

    public static final String WORKLOAD_ALGORITHM = "algorithm_task";
    public static final String WORKLOAD_STREAM_FORWARD = "stream_forward";
    public static final String WORKLOAD_POST_PROCESS = "post_process";

    private final IotNodeClient iotNodeClient;
    private final VideoProperties videoProperties;

    public boolean shouldUseRemoteDeploy(String schedulePolicy) {
        if (!iotNodeClient.isRemoteDeployEnabled()) {
            return false;
        }
        String policy = schedulePolicy != null ? schedulePolicy : "local";
        return "auto".equalsIgnoreCase(policy) || "node".equalsIgnoreCase(policy);
    }

    public boolean shouldUseRemoteDeploy(AlgorithmTaskRow task) {
        return shouldUseRemoteDeploy(task.getSchedulePolicy());
    }

    public boolean shouldUseRemoteDeploy(StreamForwardTaskRow task) {
        return shouldUseRemoteDeploy(task.getSchedulePolicy());
    }

    public List<String> algorithmCapabilities(String taskType) {
        String tt = normalizeTaskType(taskType);
        if ("snap".equals(tt)) {
            return List.of("algorithm_snap");
        }
        if ("patrol".equals(tt)) {
            return List.of("algorithm_patrol");
        }
        return List.of("algorithm_realtime");
    }

    public String resolveVideoControlUrl() {
        String base = trimToNull(System.getenv("JAVA_BACKEND_URL"));
        if (base == null) {
            base = trimToNull(System.getenv("GATEWAY_URL"));
        }
        if (base == null) {
            base = trimToNull(videoProperties.getNodeRemote().getGatewayUrl());
        }
        if (base == null) {
            base = "http://localhost:48080";
        }
        return base.replaceAll("/+$", "") + "/admin-api/video";
    }

    public Map<String, String> copyProcessEnv() {
        Map<String, String> env = new java.util.LinkedHashMap<>();
        for (String key : List.of(
                "DATABASE_URL", "GATEWAY_URL", "GB28181_SERVICE_URL", "JWT_TOKEN", "JAVA_BACKEND_URL",
                "GB28181_HTTP_READ_TIMEOUT", "GB28181_PLAY_PROTOCOL", "GB28181_HEVC_RTSP_FIRST",
                "GB28181_OPENCV_RTMP_FALLBACK_RTSP", "POD_IP", "HOST_IP", "AI_SERVICE_URL",
                "USE_GPU", "GPU_IDS", "GPU_POLICY", "INFER_GPU_POLICY", "FFMPEG_GPU_POLICY",
                "CUDA_VISIBLE_DEVICES", "NVIDIA_VISIBLE_DEVICES", "ORT_EXECUTION_PROVIDERS",
                "KAFKA_BOOTSTRAP_SERVERS", "MINIO_ENDPOINT", "MINIO_ACCESS_KEY", "MINIO_SECRET_KEY",
                "MINIO_SECURE", "NACOS_SERVER", "VIDEO_ENV",
                "CLUSTER_MODE", "MEDIA_HOST_DATA_ROOT", "MEDIA_RECORD_DIR", "MEDIA_SNAP_DIR",
                "MEDIA_UPLOAD_MODE", "MEDIA_SNAP_UPLOAD_MODE", "ALERT_IMAGES_DIR",
                "MEDIA_NODE_POOL_ENABLED", "MEDIA_NODE_REGION", "MEDIA_HTTP_PLAY_HOST",
                "IOT_SINK_API_URL", "IOT_SINK_USE_GATEWAY", "IOT_SINK_HOST", "IOT_SINK_PORT",
                "EASYAIOT_DEPLOY_PROFILE", "ALERT_HOOK_URL", "ALERT_KEEP_LATEST",
                "VIDEO_SERVICE_HOST", "VIDEO_SERVICE_URL", "VIDEO_API_USE_GATEWAY",
                "FFMPEG_HWACCEL", "FFMPEG_THREADS", "FFMPEG_PRESET", "FFMPEG_VIDEO_BITRATE", "FFMPEG_GOP_SIZE",
                "AI_RTSP_TRANSPORT", "OPENCV_FFMPEG_RTSP_TRANSPORT", "FFMPEG_RTSP_TRANSPORT",
                "OPENCV_FFMPEG_CAPTURE_OPTIONS", "RTSP_OPEN_TIMEOUT_MSEC", "RTSP_READ_TIMEOUT_MSEC",
                "REALTIME_TARGET_STREAMS", "REALTIME_THREAD_QUEUE_SIZE", "REALTIME_MAX_MUXING_QUEUE_SIZE",
                "REALTIME_RW_TIMEOUT_US", "REALTIME_RTSP_OPEN_TIMEOUT_US", "REALTIME_NVENC_SKIP_TEST",
                "REALTIME_NVENC_PRESET", "REALTIME_STREAM_STAGGER_SEC",
                "STREAM_FORWARD_TARGET_STREAMS", "STREAM_FORWARD_THREAD_QUEUE_SIZE",
                "STREAM_FORWARD_MAX_MUXING_QUEUE_SIZE", "STREAM_FORWARD_NVENC_SKIP_TEST",
                "STREAM_FORWARD_NVENC_PRESET", "STREAM_FORWARD_RELAY_STAGGER_SEC"
        )) {
            String val = System.getenv(key);
            if (val != null && !val.isBlank()) {
                env.put(key, val);
            }
        }
        return env;
    }

    public String remoteVideoRoot() {
        String env = trimToNull(System.getenv("NODE_REMOTE_VIDEO_ROOT"));
        if (env != null) {
            return env;
        }
        return videoProperties.getNodeRemote().getRemoteVideoRoot();
    }

    public String remoteRuntimeBin() {
        String env = trimToNull(System.getenv("REMOTE_RUNTIME_BIN"));
        if (env != null) {
            return env;
        }
        return videoProperties.getNodeRemote().getRemoteRuntimeBin();
    }

    public String remoteRuntimeLdLibraryPath() {
        String env = trimToNull(System.getenv("REMOTE_RUNTIME_LD_LIBRARY_PATH"));
        if (env != null) {
            return env;
        }
        return videoProperties.getNodeRemote().getRemoteRuntimeLdLibraryPath();
    }

    public String remotePython() {
        String env = trimToNull(System.getenv("NODE_REMOTE_PYTHON"));
        if (env != null) {
            return env;
        }
        return videoProperties.getNodeRemote().getRemotePython();
    }

    private static String normalizeTaskType(String taskType) {
        String tt = taskType != null ? taskType.trim().toLowerCase(Locale.ROOT) : "realtime";
        if ("snapshot".equals(tt)) {
            return "snap";
        }
        return tt;
    }

    private static String trimToNull(String value) {
        if (value == null) {
            return null;
        }
        String trimmed = value.trim();
        return trimmed.isEmpty() ? null : trimmed;
    }
}
