package com.basiclab.iot.node.service.impl;

import cn.hutool.http.HttpRequest;
import cn.hutool.http.HttpResponse;
import cn.hutool.json.JSONObject;
import cn.hutool.json.JSONUtil;
import com.basiclab.iot.common.exception.ServiceException;
import com.basiclab.iot.node.dal.dataobject.ComputeNodeDO;
import com.basiclab.iot.node.dal.pgsql.ComputeNodeMapper;
import com.basiclab.iot.node.enums.NodeStatusEnum;
import com.basiclab.iot.node.service.NodeCameraAccessService;
import com.basiclab.iot.node.service.NodeVideoWorkloadSyncService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.util.Collections;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.AGENT_COMMAND_FAILED;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.COMPUTE_NODE_NOT_EXISTS;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.COMPUTE_NODE_OFFLINE;

@Slf4j
@Service
public class NodeCameraAccessServiceImpl implements NodeCameraAccessService {

    private static final Set<String> ALLOWED = Set.of(
            "discover", "scan-segment", "probe-onvif", "probe-stream", "nvr-channels");
    private static final long MODULE_SYNC_INTERVAL_MS = 5 * 60 * 1000L;
    private static final Map<Long, Long> LAST_MODULE_SYNC = new ConcurrentHashMap<>();

    @Resource
    private ComputeNodeMapper computeNodeMapper;
    @Resource
    private NodeVideoWorkloadSyncService nodeVideoWorkloadSyncService;

    @Override
    public Object execute(Long nodeId, String operation, Map<String, Object> payload) {
        String op = operation == null ? "" : operation.trim().toLowerCase();
        if (!ALLOWED.contains(op)) {
            throw exception(AGENT_COMMAND_FAILED, "不支持的摄像头接入操作: " + operation);
        }
        ComputeNodeDO node = computeNodeMapper.selectById(nodeId);
        if (node == null) {
            throw exception(COMPUTE_NODE_NOT_EXISTS);
        }
        if (!NodeStatusEnum.ONLINE.getStatus().equals(node.getStatus())) {
            throw exception(COMPUTE_NODE_OFFLINE);
        }

        if ("scan-segment".equals(op) || "probe-onvif".equals(op) || "nvr-channels".equals(op)) {
            ensureCameraModules(node);
        }
        int port = node.getAgentPort() != null ? node.getAgentPort() : 9100;
        String url = String.format("http://%s:%d/camera/%s", node.getHost(), port, op);
        try {
            HttpResponse response = HttpRequest.post(url)
                    .header("X-Agent-Token", node.getAgentToken())
                    .header("Content-Type", "application/json")
                    .body(JSONUtil.toJsonStr(payload != null ? payload : Collections.emptyMap()))
                    .timeout("scan-segment".equals(op) ? 330_000 : 90_000)
                    .execute();
            if (!response.isOk()) {
                throw exception(AGENT_COMMAND_FAILED,
                        "HTTP " + response.getStatus() + " — " + response.body());
            }
            JSONObject json = JSONUtil.parseObj(response.body());
            if (json.getInt("code", -1) != 0) {
                throw exception(AGENT_COMMAND_FAILED, json.getStr("msg", response.body()));
            }
            return json.get("data");
        } catch (ServiceException e) {
            throw e;
        } catch (Exception e) {
            log.error("摄像头接入 Agent 请求失败 nodeId={} operation={}: {}",
                    nodeId, op, e.getMessage(), e);
            throw exception(AGENT_COMMAND_FAILED, node.getHost() + ":" + port + " — " + e.getMessage());
        }
    }

    /** 摄像头扫描复用 VIDEO 轻量协议实现；限频同步，避免每次探测重复传输。 */
    private void ensureCameraModules(ComputeNodeDO node) {
        long now = System.currentTimeMillis();
        Long lastSync = LAST_MODULE_SYNC.get(node.getId());
        if (lastSync != null && now - lastSync < MODULE_SYNC_INTERVAL_MS) {
            return;
        }
        synchronized (LAST_MODULE_SYNC) {
            lastSync = LAST_MODULE_SYNC.get(node.getId());
            if (lastSync == null || now - lastSync >= MODULE_SYNC_INTERVAL_MS) {
                nodeVideoWorkloadSyncService.syncBeforeDeploy(node, "camera_access");
                LAST_MODULE_SYNC.put(node.getId(), now);
            }
        }
    }
}
