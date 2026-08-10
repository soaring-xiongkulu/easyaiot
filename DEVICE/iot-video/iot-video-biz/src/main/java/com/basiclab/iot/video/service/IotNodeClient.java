package com.basiclab.iot.video.service;

import com.basiclab.iot.video.config.VideoProperties;
import javax.annotation.PostConstruct;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/**
 * Mirrors retired Python {@code app.utils.node_client} — iot-node scheduler + workload HTTP client.
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class IotNodeClient {

    private final VideoProperties videoProperties;
    private RestTemplate restTemplate;

    @PostConstruct
    void initRestTemplate() {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        int timeoutMs = videoProperties.getNodeRemote().getRequestTimeoutMs();
        factory.setConnectTimeout(timeoutMs);
        factory.setReadTimeout(timeoutMs);
        this.restTemplate = new RestTemplate(factory);
    }

    public boolean isRemoteDeployEnabled() {
        String env = trimToNull(System.getenv("NODE_REMOTE_DEPLOY"));
        if (env != null) {
            return isTruthy(env);
        }
        Boolean configured = videoProperties.getNodeRemote().getRemoteDeployEnabled();
        if (configured != null) {
            return configured;
        }
        String profile = trimToNull(System.getenv("EASYAIOT_DEPLOY_PROFILE"));
        if (profile != null) {
            String p = profile.toLowerCase(Locale.ROOT);
            if (p.equals("mini") || p.equals("1") || p.equals("minimal") || p.equals("4g")) {
                return false;
            }
        }
        return true;
    }

    public String nodeApiBase() {
        String env = trimToNull(System.getenv("JAVA_BACKEND_URL"));
        if (env == null) {
            env = trimToNull(System.getenv("GATEWAY_URL"));
        }
        if (env == null) {
            env = trimToNull(videoProperties.getNodeRemote().getGatewayUrl());
        }
        if (env == null) {
            env = "http://localhost:48080";
        }
        return env.replaceAll("/+$", "") + "/admin-api/node";
    }

    public Map<String, Object> allocateNode(
            String workloadType,
            String workloadId,
            List<String> capabilities,
            boolean preferGpu,
            boolean sticky,
            Long targetNodeId,
            List<Long> excludeNodeIds
    ) {
        if (targetNodeId != null) {
            Map<String, Object> node = getNode(targetNodeId);
            Map<String, Object> out = new LinkedHashMap<>();
            out.put("nodeId", targetNodeId);
            out.put("host", node.get("host"));
            out.put("agentPort", node.get("agentPort"));
            out.put("gpuIds", formatGpuIds(node.get("maxGpuCount")));
            out.put("bindingId", null);
            return out;
        }

        Map<String, Object> requirements = new LinkedHashMap<>();
        requirements.put("capabilities", capabilities != null ? capabilities : List.of("algorithm_realtime"));
        requirements.put("gpuCount", 0);
        requirements.put("preferGpu", preferGpu);
        if (excludeNodeIds != null && !excludeNodeIds.isEmpty()) {
            requirements.put("excludeNodeIds", excludeNodeIds);
        }

        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("workloadType", workloadType);
        payload.put("workloadId", workloadId);
        payload.put("sticky", sticky);
        payload.put("requirements", requirements);

        return postJson("/scheduler/allocate", payload);
    }

    public Map<String, Object> deployWorkload(
            long nodeId,
            String workloadType,
            String workloadId,
            List<String> command,
            String workDir,
            String logDir,
            Map<String, String> env,
            String gpuIds,
            List<Map<String, String>> files
    ) {
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("nodeId", nodeId);
        payload.put("workloadType", workloadType);
        payload.put("workloadId", workloadId);
        payload.put("command", command);
        payload.put("workDir", workDir);
        payload.put("logDir", logDir);
        payload.put("gpuIds", gpuIds);
        payload.put("env", env);
        if (files != null && !files.isEmpty()) {
            payload.put("files", files);
        }
        return postJson("/workload/deploy", payload);
    }

    public void stopWorkload(long nodeId, String workloadType, String workloadId) {
        String url = nodeApiBase() + "/workload/stop"
                + "?nodeId=" + nodeId
                + "&workloadType=" + encode(workloadType)
                + "&workloadId=" + encode(workloadId);
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            ResponseEntity<Map> response = restTemplate.postForEntity(url, new HttpEntity<>(headers), Map.class);
            ensureSuccess(response);
        } catch (RestClientException ex) {
            log.warn("iot-node stop workload failed nodeId={} type={} id={}: {}", nodeId, workloadType, workloadId, ex.getMessage());
        }
    }

    public void releaseWorkload(String workloadType, String workloadId) {
        String url = nodeApiBase() + "/scheduler/release"
                + "?workloadType=" + encode(workloadType)
                + "&workloadId=" + encode(workloadId);
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            ResponseEntity<Map> response = restTemplate.postForEntity(url, new HttpEntity<>(headers), Map.class);
            ensureSuccess(response);
        } catch (RestClientException ex) {
            log.warn("iot-node release workload failed type={} id={}: {}", workloadType, workloadId, ex.getMessage());
        }
    }

    public Map<String, Object> getNode(long nodeId) {
        String url = nodeApiBase() + "/get?id=" + nodeId;
        try {
            ResponseEntity<Map> response = restTemplate.getForEntity(url, Map.class);
            return ensureSuccess(response);
        } catch (RestClientException ex) {
            throw new NodeClientException("查询节点失败 nodeId=" + nodeId + ": " + ex.getMessage(), ex);
        }
    }

    public boolean isNodeOnline(long nodeId) {
        try {
            Map<String, Object> node = getNode(nodeId);
            String status = String.valueOf(node.getOrDefault("status", "")).toLowerCase(Locale.ROOT);
            return "online".equals(status);
        } catch (Exception e) {
            log.warn("查询节点状态失败 nodeId={}: {}", nodeId, e.getMessage());
            return false;
        }
    }

    private Map<String, Object> postJson(String path, Map<String, Object> payload) {
        String url = nodeApiBase() + path;
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<Map<String, Object>> entity = new HttpEntity<>(payload, headers);
            ResponseEntity<Map> response = restTemplate.postForEntity(url, entity, Map.class);
            return ensureSuccess(response);
        } catch (RestClientException ex) {
            throw new NodeClientException("iot-node API 失败 " + path + ": " + ex.getMessage(), ex);
        }
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> ensureSuccess(ResponseEntity<Map> response) {
        if (!response.getStatusCode().is2xxSuccessful()) {
            throw new NodeClientException("iot-node HTTP " + response.getStatusCode().value());
        }
        Map<?, ?> body = response.getBody();
        if (body == null) {
            throw new NodeClientException("iot-node 空响应");
        }
        Object code = body.get("code");
        if (code instanceof Number number && number.intValue() != 0) {
            Object msg = body.get("msg") != null ? body.get("msg") : body.get("message");
            throw new NodeClientException(String.valueOf(msg != null ? msg : body));
        }
        Object data = body.get("data");
        if (data instanceof Map<?, ?> map) {
            Map<String, Object> out = new LinkedHashMap<>();
            map.forEach((k, v) -> out.put(String.valueOf(k), v));
            return out;
        }
        return new LinkedHashMap<>();
    }

    private static String formatGpuIds(Object maxGpuCount) {
        if (maxGpuCount == null) {
            return null;
        }
        int count;
        try {
            count = Integer.parseInt(String.valueOf(maxGpuCount));
        } catch (NumberFormatException e) {
            return null;
        }
        if (count <= 0) {
            return null;
        }
        List<String> ids = new ArrayList<>();
        for (int i = 0; i < count; i++) {
            ids.add(String.valueOf(i));
        }
        return String.join(",", ids);
    }

    private static String encode(String value) {
        return value == null ? "" : value;
    }

    private static boolean isTruthy(String value) {
        String normalized = value.trim().toLowerCase(Locale.ROOT);
        return normalized.equals("1") || normalized.equals("true") || normalized.equals("yes") || normalized.equals("on");
    }

    private static String trimToNull(String value) {
        if (value == null) {
            return null;
        }
        String trimmed = value.trim();
        return trimmed.isEmpty() ? null : trimmed;
    }

    public static class NodeClientException extends RuntimeException {
        public NodeClientException(String message) {
            super(message);
        }

        public NodeClientException(String message, Throwable cause) {
            super(message, cause);
        }
    }
}
