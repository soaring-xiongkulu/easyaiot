package com.basiclab.iot.node.util;

import cn.hutool.core.util.StrUtil;
import com.basiclab.iot.node.dal.dataobject.ComputeNodeDO;

import java.net.URI;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;

public final class MediaStackDeployUtil {

    private static final String REMOTE_ROOT = "/opt/easyaiot/media-cluster";

    private MediaStackDeployUtil() {
    }

    public static String remoteClusterRoot() {
        return REMOTE_ROOT;
    }

    public static String sanitizeNodeName(String name, String host) {
        String raw = StrUtil.blankToDefault(name, StrUtil.blankToDefault(host, "media-node")).trim().toLowerCase(Locale.ROOT);
        String slug = raw.replaceAll("[^a-z0-9-]+", "-").replaceAll("^-+|-+$", "");
        return StrUtil.isBlank(slug) ? "media-node" : slug;
    }

    public static int tagInt(Map<String, String> tags, String key, int defaultValue) {
        if (tags == null || !tags.containsKey(key)) {
            return defaultValue;
        }
        try {
            return Integer.parseInt(tags.get(key));
        } catch (NumberFormatException ignored) {
            return defaultValue;
        }
    }

    public enum DeployPhase {
        FULL,
        PREPARE_IMAGES,
        DEPLOY_SERVICES
    }

    public static String buildDeployScript(ComputeNodeDO node, String hookHost, int hookPort) {
        return buildDeployScript(node, hookHost, hookPort, DeployPhase.FULL);
    }

    public static String buildDeployScript(ComputeNodeDO node, String hookHost, int hookPort, DeployPhase phase) {
        return buildDeployScript(node, hookHost, hookPort, "/admin-api", phase);
    }

    public static String buildDeployScript(
            ComputeNodeDO node, String hookHost, int hookPort, String hookPathPrefix, DeployPhase phase) {
        StringBuilder sb = new StringBuilder(buildDeployEnvScript(node, hookHost, hookPort, hookPathPrefix));
        if (phase == DeployPhase.PREPARE_IMAGES) {
            sb.append("export MEDIA_PREPARE_IMAGES_ONLY=1\n");
        } else if (phase == DeployPhase.DEPLOY_SERVICES) {
            sb.append("export MEDIA_DEPLOY_SERVICES_ONLY=1\n");
        }
        sb.append("bash \"${MEDIA_CLUSTER_ROOT}/install_media_stack.sh\"\n");
        return sb.toString();
    }

    /** Agent /media/deploy 使用的环境变量（与 SSH 部署脚本一致，含节点 tags 中的端口）。 */
    public static Map<String, String> buildDeployEnvMap(
            ComputeNodeDO node, String hookHost, int hookPort, String hookPathPrefix) {
        Map<String, String> tags = node.getTags();
        String nodeName = sanitizeNodeName(node.getName(), node.getHost());
        String host = node.getHost();
        int srsRtmp = tagInt(tags, "srs_rtmp_port", 1935);
        int srsHttp = tagInt(tags, "srs_http_port", 8080);
        int srsApi = tagInt(tags, "srs_api_port", 1985);
        int srsRtc = tagInt(tags, "srs_rtc_port", 8000);
        int zlmHttp = tagInt(tags, "zlm_http_port", 6080);
        int zlmRtmp = tagInt(tags, "zlm_rtmp_port", 10935);
        int zlmRtsp = tagInt(tags, "zlm_rtsp_port", 8554);
        int zlmRtc = tagInt(tags, "zlm_rtc_port", 8800);
        int zlmRtpMin = tagInt(tags, "zlm_rtp_port_min", 30000);
        int zlmRtpMax = tagInt(tags, "zlm_rtp_port_max", 30500);
        String pathPrefix = StrUtil.blankToDefault(hookPathPrefix, "/admin-api");

        Map<String, String> env = new LinkedHashMap<>();
        env.put("MEDIA_CLUSTER_ROOT", REMOTE_ROOT);
        env.put("MEDIA_NODE_NAME", nodeName);
        env.put("MEDIA_NODE_HOST", host);
        env.put("MEDIA_HOOK_HOST", hookHost);
        env.put("MEDIA_HOOK_PORT", String.valueOf(hookPort));
        env.put("MEDIA_HOOK_PATH_PREFIX", pathPrefix);
        env.put("MEDIA_CONTROL_HOOK_HOST", hookHost);
        env.put("MEDIA_CONTROL_HOOK_PORT", String.valueOf(hookPort));
        env.put("MEDIA_CONTROL_HOOK_PATH_PREFIX", pathPrefix);
        env.put("MEDIA_ASSET_REPORT_URL", "http://" + hookHost + ":" + hookPort
                + pathPrefix + "/video/internal/media/assets/report-batch");
        String recordingMode = StrUtil.blankToDefault(node.getRecordingStorageMode(), "central_shared");
        env.put("RECORDING_STORAGE_MODE", recordingMode);
        env.put("RECORDING_STORAGE_GENERATION", String.valueOf(
                node.getRecordingStorageGeneration() != null ? node.getRecordingStorageGeneration() : 1L));
        env.put("COMPUTE_NODE_ID", String.valueOf(node.getId()));
        env.put("MEDIA_DVR_HOOK_HOST", hookHost);
        env.put("MEDIA_DVR_HOOK_PORT", String.valueOf(hookPort));
        env.put("MEDIA_DVR_HOOK_PATH_PREFIX", pathPrefix);
        env.put("MEDIA_DVR_HOOK_PATH", "/sink/media/hook/srs/on_dvr");
        env.put("MEDIA_RECORDING_ROOT", "/mnt/easyaiot-media");
        env.put("REQUIRE_SHARED_STORAGE_MOUNT", isPlatformNode(node) ? "0" : "1");
        if ("edge_local".equals(recordingMode)) {
            env.put("MEDIA_RECORDING_ROOT", tags != null
                    ? StrUtil.blankToDefault(tags.get("edge_recording_root"), "/data/local-storage")
                    : "/data/local-storage");
            env.put("SKIP_CEPH_CHECK", "1");
            env.put("MEDIA_DVR_HOOK_PATH", "/video/media/hook/srs/on_dvr");
            applyEdgeMediaEndpoint(env, node.getMediaPublicUrl(), host);
        }
        String internalToken = System.getenv("MEDIA_INTERNAL_TOKEN");
        if ("edge_local".equals(recordingMode) && StrUtil.isBlank(internalToken)) {
            throw new IllegalStateException("边缘本地存储要求 iot-node 配置 MEDIA_INTERNAL_TOKEN");
        }
        if (StrUtil.isNotBlank(internalToken)) {
            env.put("MEDIA_INTERNAL_TOKEN", internalToken);
        }
        env.put("SRS_CANDIDATE_IP", host);
        env.put("SRS_RTMP_PORT", String.valueOf(srsRtmp));
        env.put("SRS_HTTP_PORT", String.valueOf(srsHttp));
        env.put("SRS_API_PORT", String.valueOf(srsApi));
        env.put("SRS_RTC_PORT", String.valueOf(srsRtc));
        env.put("SRS_FORWARD_ENABLED", "off");
        env.put("SRS_FORWARD_DESTINATION", "127.0.0.1:19350");
        if ("edge_local".equals(recordingMode)) {
            env.put("SRS_FORWARD_ENABLED", "on");
            env.put("SRS_FORWARD_DESTINATION", hookHost + ":" + System.getenv().getOrDefault(
                    "CONTROL_PLANE_SRS_RTMP_PORT", "1935"));
        }
        env.put("ZLM_HTTP_PORT", String.valueOf(zlmHttp));
        env.put("ZLM_RTMP_PORT", String.valueOf(zlmRtmp));
        env.put("ZLM_RTSP_PORT", String.valueOf(zlmRtsp));
        env.put("ZLM_RTC_PORT", String.valueOf(zlmRtc));
        env.put("ZLM_RTC_EXTERN_IP", host);
        env.put("ZLM_RTP_PORT_MIN", String.valueOf(zlmRtpMin));
        env.put("ZLM_RTP_PORT_MAX", String.valueOf(zlmRtpMax));
        env.put("ZLM_SECRET", "EasyAIoT_Media_Secret");
        return env;
    }

    private static boolean isPlatformNode(ComputeNodeDO node) {
        Map<String, Boolean> capabilities = node.getCapabilities();
        if (capabilities == null) {
            return false;
        }
        return Boolean.TRUE.equals(capabilities.get("platform"));
    }

    private static void applyEdgeMediaEndpoint(Map<String, String> env, String publicUrl, String fallbackHost) {
        try {
            URI uri = URI.create(StrUtil.blankToDefault(publicUrl, "http://" + fallbackHost + ":6000"));
            env.put("MEDIA_DVR_HOOK_HOST", StrUtil.blankToDefault(uri.getHost(), fallbackHost));
            int port = uri.getPort() > 0 ? uri.getPort() : ("https".equalsIgnoreCase(uri.getScheme()) ? 443 : 80);
            env.put("MEDIA_DVR_HOOK_PORT", String.valueOf(port));
            String prefix = StrUtil.blankToDefault(uri.getPath(), "").replaceAll("/+$", "");
            env.put("MEDIA_DVR_HOOK_PATH_PREFIX", prefix);
        } catch (Exception ignored) {
            env.put("MEDIA_DVR_HOOK_HOST", fallbackHost);
            env.put("MEDIA_DVR_HOOK_PORT", "6000");
            env.put("MEDIA_DVR_HOOK_PATH_PREFIX", "");
        }
    }

    private static String buildDeployEnvScript(
            ComputeNodeDO node, String hookHost, int hookPort, String hookPathPrefix) {
        Map<String, String> env = buildDeployEnvMap(node, hookHost, hookPort, hookPathPrefix);
        StringBuilder sb = new StringBuilder("#!/usr/bin/env bash\nset -euo pipefail\n");
        for (Map.Entry<String, String> entry : env.entrySet()) {
            sb.append("export ").append(entry.getKey()).append("=\"")
                    .append(entry.getValue().replace("\"", "\\\"")).append("\"\n");
        }
        return sb.toString();
    }

}
