package com.basiclab.iot.node.util;

import cn.hutool.http.HttpRequest;
import cn.hutool.http.HttpResponse;
import cn.hutool.json.JSONObject;
import cn.hutool.json.JSONUtil;
import com.basiclab.iot.common.exception.ServiceException;
import com.basiclab.iot.node.dal.dataobject.ComputeNodeDO;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.util.HashMap;
import java.util.Map;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.AGENT_COMMAND_FAILED;

@Component
@Slf4j
public class NodeSentinelAgentClient {

    private static final int PROBE_TIMEOUT_MS = 120_000;
    private static final int VALIDATE_TIMEOUT_MS = 120_000;

    public Map<String, Object> probe(ComputeNodeDO node, String level) {
        Map<String, Object> body = new HashMap<>();
        body.put("level", level != null ? level : "L1");
        return postAgent(node, "/sentinel/probe", body, PROBE_TIMEOUT_MS);
    }

    public Map<String, Object> validate(ComputeNodeDO node, String workloadType, Map<String, Object> requirements) {
        Map<String, Object> body = new HashMap<>();
        body.put("workloadType", workloadType);
        body.put("requirements", requirements != null ? requirements : Map.of());
        return postAgent(node, "/sentinel/validate", body, VALIDATE_TIMEOUT_MS);
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> postAgent(ComputeNodeDO node, String path, Map<String, Object> body, int timeoutMs) {
        int port = node.getAgentPort() != null ? node.getAgentPort() : 9100;
        String url = String.format("http://%s:%d%s", node.getHost(), port, path);
        try {
            HttpResponse response = HttpRequest.post(url)
                    .header("X-Agent-Token", node.getAgentToken())
                    .header("Content-Type", "application/json")
                    .body(JSONUtil.toJsonStr(body))
                    .timeout(timeoutMs)
                    .execute();
            if (!response.isOk()) {
                throw exception(AGENT_COMMAND_FAILED,
                        "HTTP " + response.getStatus() + " — " + response.body());
            }
            JSONObject json = JSONUtil.parseObj(response.body());
            if (json.getInt("code", -1) != 0) {
                throw exception(AGENT_COMMAND_FAILED, json.getStr("msg", response.body()));
            }
            Object data = json.get("data");
            if (data instanceof Map<?, ?> map) {
                return (Map<String, Object>) map;
            }
            return Map.of();
        } catch (ServiceException e) {
            throw e;
        } catch (Exception e) {
            log.error("Sentinel Agent 请求异常 nodeId={} url={}: {}", node.getId(), url, e.getMessage());
            String detail = e.getMessage() != null ? e.getMessage() : e.getClass().getSimpleName();
            throw exception(AGENT_COMMAND_FAILED, node.getHost() + ":" + port + " — " + detail);
        }
    }
}
