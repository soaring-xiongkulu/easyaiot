package com.basiclab.iot.node.service.impl;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.json.JsonUtils;
import com.basiclab.iot.node.dal.dataobject.ComputeNodeDO;
import com.basiclab.iot.node.dal.dataobject.NodeMetricSnapshotDO;
import com.basiclab.iot.node.domain.vo.ComputeNodePageReqVO;
import com.basiclab.iot.node.domain.vo.ComputeNodeRespVO;
import com.basiclab.iot.node.domain.vo.NodeClusterMetricNodeVO;
import com.basiclab.iot.node.domain.vo.NodeClusterMetricPushMessage;
import com.basiclab.iot.node.framework.websocket.NodeClusterWebSocketHandler;
import com.basiclab.iot.node.service.ComputeNodeService;
import com.basiclab.iot.node.service.NodeClusterMetricsBroadcaster;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;

import javax.annotation.Resource;
import java.io.IOException;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
@Slf4j
public class NodeClusterMetricsBroadcasterImpl implements NodeClusterMetricsBroadcaster {

    @Resource
    private NodeClusterWebSocketHandler nodeClusterWebSocketHandler;
    @Resource
    private ComputeNodeService computeNodeService;
    @Resource
    private ObjectMapper objectMapper;

    @Override
    public void sendSnapshot(WebSocketSession session) {
        if (session == null || !session.isOpen()) {
            return;
        }
        try {
            session.sendMessage(new TextMessage(buildSnapshotPayload()));
        } catch (IOException ex) {
            log.warn("发送集群指标快照失败: {}", session.getId(), ex);
        }
    }

    @Override
    public void broadcastSnapshot() {
        nodeClusterWebSocketHandler.broadcast(buildSnapshotPayload());
    }

    @Override
    public void broadcastNodeUpdate(ComputeNodeDO node, NodeMetricSnapshotDO metric) {
        NodeClusterMetricNodeVO payload = toMetricNode(node, metric);
        nodeClusterWebSocketHandler.broadcast(JsonUtils.toJsonString(
                NodeClusterMetricPushMessage.nodeUpdate(payload)));
    }

    private String buildSnapshotPayload() {
        ComputeNodePageReqVO reqVO = new ComputeNodePageReqVO();
        reqVO.setPageNo(1);
        reqVO.setPageSize(200);
        PageResult<ComputeNodeRespVO> page = computeNodeService.getNodePage(reqVO);
        List<NodeClusterMetricNodeVO> nodes = page.getList().stream()
                .map(this::toMetricNode)
                .collect(Collectors.toList());
        return JsonUtils.toJsonString(NodeClusterMetricPushMessage.snapshot(nodes));
    }

    private NodeClusterMetricNodeVO toMetricNode(ComputeNodeRespVO resp) {
        NodeClusterMetricNodeVO node = new NodeClusterMetricNodeVO();
        node.setId(resp.getId());
        node.setName(resp.getName());
        node.setHost(resp.getHost());
        node.setStatus(resp.getStatus());
        node.setNodeRole(resp.getNodeRole());
        node.setCpuPercent(resp.getCpuPercent());
        node.setMemPercent(resp.getMemPercent());
        node.setMemUsedBytes(resp.getMemUsedBytes());
        node.setMemTotalBytes(resp.getMemTotalBytes());
        node.setDiskPercent(resp.getDiskPercent());
        node.setDiskUsedBytes(resp.getDiskUsedBytes());
        node.setDiskTotalBytes(resp.getDiskTotalBytes());
        node.setActiveTasks(resp.getActiveTasks());
        node.setGpuInfo(resp.getGpuInfo());
        node.setLastHeartbeatAt(resp.getLastHeartbeatAt());
        node.setIsPlatform(resp.getIsPlatform());
        return node;
    }

    private NodeClusterMetricNodeVO toMetricNode(ComputeNodeDO node, NodeMetricSnapshotDO metric) {
        NodeClusterMetricNodeVO payload = new NodeClusterMetricNodeVO();
        payload.setId(node.getId());
        payload.setName(node.getName());
        payload.setHost(node.getHost());
        payload.setStatus(node.getStatus());
        payload.setNodeRole(node.getNodeRole());
        payload.setLastHeartbeatAt(node.getLastHeartbeatAt());
        payload.setIsPlatform(ComputeNodeServiceImpl.isPlatformNode(node));
        if (metric != null) {
            payload.setCpuPercent(metric.getCpuPercent());
            payload.setMemPercent(metric.getMemPercent());
            payload.setMemUsedBytes(metric.getMemUsedBytes());
            payload.setMemTotalBytes(metric.getMemTotalBytes());
            payload.setDiskPercent(metric.getDiskPercent());
            payload.setDiskUsedBytes(metric.getDiskUsedBytes());
            payload.setDiskTotalBytes(metric.getDiskTotalBytes());
            payload.setActiveTasks(metric.getActiveTasks());
            payload.setGpuInfo(serializeGpuInfo(metric.getGpuInfo()));
        }
        return payload;
    }

    private String serializeGpuInfo(List<Map<String, Object>> gpuInfo) {
        if (gpuInfo == null || gpuInfo.isEmpty()) {
            return null;
        }
        try {
            return objectMapper.writeValueAsString(gpuInfo);
        } catch (Exception ex) {
            return null;
        }
    }

}
