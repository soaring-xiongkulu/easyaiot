package com.basiclab.iot.node.service.impl;

import cn.hutool.core.util.IdUtil;
import cn.hutool.core.util.StrUtil;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.node.dal.dataobject.ComputeNodeDO;
import com.basiclab.iot.node.dal.dataobject.EdgeNodeDO;
import com.basiclab.iot.node.dal.dataobject.NodeMetricSnapshotDO;
import com.basiclab.iot.node.dal.pgsql.ComputeNodeMapper;
import com.basiclab.iot.node.dal.pgsql.EdgeNodeMapper;
import com.basiclab.iot.node.dal.pgsql.NodeMetricSnapshotMapper;
import com.basiclab.iot.node.domain.vo.EdgeEnrollReqVO;
import com.basiclab.iot.node.domain.vo.EdgeEnrollRespVO;
import com.basiclab.iot.node.domain.vo.EdgeNodePageReqVO;
import com.basiclab.iot.node.domain.vo.EdgeNodeRespVO;
import com.basiclab.iot.node.domain.vo.EdgeNodeUpdateReqVO;
import com.basiclab.iot.node.domain.vo.EdgeRuntimeConfigReqVO;
import com.basiclab.iot.node.domain.vo.EdgeRuntimeConfigRespVO;
import com.basiclab.iot.node.enums.NodeRoleEnum;
import com.basiclab.iot.node.enums.NodeStatusEnum;
import com.basiclab.iot.node.service.ControlPlaneEndpointResolver;
import com.basiclab.iot.node.service.EdgeNodeService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.validation.annotation.Validated;

import javax.annotation.Resource;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.AGENT_TOKEN_INVALID;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.COMPUTE_NODE_NOT_EXISTS;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.EDGE_ENROLL_HOST_EMPTY;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.EDGE_JOIN_TOKEN_INVALID;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.EDGE_NODE_NOT_EXISTS;

@Service
@Validated
public class EdgeNodeServiceImpl implements EdgeNodeService {

    private static final int DEFAULT_AGENT_PORT = 9100;
    private static final String DEFAULT_MEDIA_ROOT = "/mnt/easyaiot-media";

    @Resource
    private ComputeNodeMapper computeNodeMapper;

    @Resource
    private EdgeNodeMapper edgeNodeMapper;

    @Resource
    private NodeMetricSnapshotMapper nodeMetricSnapshotMapper;

    @Autowired(required = false)
    private ControlPlaneEndpointResolver controlPlaneEndpointResolver;

    /** 生产环境建议配置；与 EDGE_JOIN_TOKEN 一致 */
    @Value("${easyaiot.edge.join-token:}")
    private String joinToken;

    /** 私网实验室可 true：无需 join-token，仅配 NODE 地址即可纳管 */
    @Value("${easyaiot.edge.allow-open-enroll:true}")
    private boolean allowOpenEnroll;

    @Value("${easyaiot.edge.mqtt-algo-tenant:default}")
    private String mqttAlgoTenant;

    @Value("${easyaiot.edge.media-host-data-root:" + DEFAULT_MEDIA_ROOT + "}")
    private String mediaHostDataRoot;

    @Value("${easyaiot.edge.control-plane-public-url:}")
    private String controlPlanePublicUrl;

    @Value("${server.port:48086}")
    private int serverPort;

    @Override
    @Transactional(rollbackFor = Exception.class)
    public EdgeEnrollRespVO enroll(EdgeEnrollReqVO reqVO) {
        validateJoinToken(reqVO.getJoinToken());
        String host = StrUtil.blankToDefault(reqVO.getHost(), "").trim();
        if (StrUtil.isBlank(host)) {
            throw exception(EDGE_ENROLL_HOST_EMPTY);
        }

        ComputeNodeDO node = computeNodeMapper.selectByHost(host);
        if (node == null) {
            node = createEdgeNode(reqVO, host);
        } else {
            // 已存在：校验或刷新能力，不轮换 token（避免多实例互踢）；指纹可写入 tags
            Map<String, String> tags = node.getTags() != null ? new HashMap<>(node.getTags()) : new HashMap<>();
            if (StrUtil.isNotBlank(reqVO.getFingerprint())) {
                tags.put("edge_fingerprint", reqVO.getFingerprint());
            }
            tags.put("edge_runtime", "true");
            node.setTags(tags);
            if (reqVO.getCapabilities() != null && !reqVO.getCapabilities().isEmpty()) {
                Map<String, Boolean> caps = node.getCapabilities() != null
                        ? new HashMap<>(node.getCapabilities()) : new HashMap<>();
                caps.putAll(reqVO.getCapabilities());
                node.setCapabilities(caps);
            }
            if (reqVO.getMaxTaskCount() != null && reqVO.getMaxTaskCount() > 0) {
                node.setMaxTaskCount(reqVO.getMaxTaskCount());
            }
            node.setStatus(NodeStatusEnum.ONLINE.getStatus());
            node.setLastHeartbeatAt(LocalDateTime.now());
            computeNodeMapper.updateById(node);
        }

        syncEdgeNodeRecord(node, reqVO);
        EdgeNodeDO edgeRecord = edgeNodeMapper.selectByComputeNodeId(node.getId());

        EdgeEnrollRespVO resp = new EdgeEnrollRespVO();
        resp.setNodeId(node.getId());
        resp.setEdgeNodeId(edgeRecord != null ? edgeRecord.getId() : null);
        resp.setAgentToken(node.getAgentToken());
        resp.setRuntimeConfig(buildRuntimeConfig(node));
        return resp;
    }

    @Override
    public PageResult<EdgeNodeRespVO> getEdgeNodePage(EdgeNodePageReqVO reqVO) {
        PageResult<EdgeNodeDO> page = edgeNodeMapper.selectPage(reqVO);
        List<EdgeNodeRespVO> list = page.getList().stream().map(this::toEdgeResp).collect(Collectors.toList());
        return new PageResult<>(list, page.getTotal());
    }

    @Override
    public EdgeNodeRespVO getEdgeNode(Long id) {
        EdgeNodeDO node = edgeNodeMapper.selectById(id);
        if (node == null) {
            throw exception(EDGE_NODE_NOT_EXISTS);
        }
        return toEdgeResp(node);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void updateEdgeNode(EdgeNodeUpdateReqVO reqVO) {
        EdgeNodeDO node = edgeNodeMapper.selectById(reqVO.getId());
        if (node == null) {
            throw exception(EDGE_NODE_NOT_EXISTS);
        }
        if (StrUtil.isNotBlank(reqVO.getName())) {
            node.setName(reqVO.getName().trim());
        }
        if (reqVO.getRemark() != null) {
            node.setRemark(reqVO.getRemark());
        }
        if (reqVO.getMaxTaskCount() != null && reqVO.getMaxTaskCount() > 0) {
            node.setMaxTaskCount(reqVO.getMaxTaskCount());
            ComputeNodeDO compute = computeNodeMapper.selectById(node.getComputeNodeId());
            if (compute != null) {
                compute.setMaxTaskCount(reqVO.getMaxTaskCount());
                computeNodeMapper.updateById(compute);
            }
        }
        if (reqVO.getEnabled() != null) {
            node.setEnabled(reqVO.getEnabled());
            if (!Boolean.TRUE.equals(reqVO.getEnabled())) {
                node.setStatus("disabled");
            }
        }
        edgeNodeMapper.updateById(node);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void deleteEdgeNode(Long id) {
        EdgeNodeDO node = edgeNodeMapper.selectById(id);
        if (node == null) {
            throw exception(EDGE_NODE_NOT_EXISTS);
        }
        edgeNodeMapper.deleteById(id);
        // 软删管理记录即可；compute_node 保留以免误伤通用 Agent，可由运维另行清理
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void syncEdgeNodeRecord(ComputeNodeDO computeNode, EdgeEnrollReqVO enrollHint) {
        if (computeNode == null || computeNode.getId() == null) {
            return;
        }
        EdgeNodeDO existing = edgeNodeMapper.selectByComputeNodeId(computeNode.getId());
        boolean cephReady = false;
        Map<String, String> tags = computeNode.getTags();
        if (tags != null) {
            String ready = tags.get("ceph_mount_ready");
            cephReady = "true".equalsIgnoreCase(ready) || "1".equals(ready);
        }
        String fingerprint = enrollHint != null ? enrollHint.getFingerprint() : null;
        if (StrUtil.isBlank(fingerprint) && tags != null) {
            fingerprint = tags.get("edge_fingerprint");
        }
        String agentVersion = enrollHint != null ? enrollHint.getAgentVersion() : null;
        if (StrUtil.isBlank(agentVersion) && tags != null) {
            agentVersion = tags.get("edge_version");
        }

        if (existing == null) {
            EdgeNodeDO created = EdgeNodeDO.builder()
                    .computeNodeId(computeNode.getId())
                    .name(StrUtil.blankToDefault(computeNode.getName(), "edge-" + computeNode.getHost()))
                    .host(computeNode.getHost())
                    .status(NodeStatusEnum.ONLINE.getStatus())
                    .fingerprint(fingerprint)
                    .mqttClientId("algo-edge-" + computeNode.getId())
                    .mqttUsername("algo-edge-" + computeNode.getId())
                    .agentVersion(agentVersion)
                    .nodeRole(computeNode.getNodeRole())
                    .maxTaskCount(computeNode.getMaxTaskCount() != null ? computeNode.getMaxTaskCount() : 1)
                    .activeTaskCount(0)
                    .cephMountReady(cephReady)
                    .lastHeartbeatAt(computeNode.getLastHeartbeatAt() != null
                            ? computeNode.getLastHeartbeatAt() : LocalDateTime.now())
                    .enabled(true)
                    .remark(computeNode.getRemark())
                    .tags(tags)
                    .build();
            edgeNodeMapper.insert(created);
            return;
        }
        existing.setName(StrUtil.blankToDefault(computeNode.getName(), existing.getName()));
        existing.setHost(computeNode.getHost());
        existing.setStatus(Boolean.FALSE.equals(existing.getEnabled())
                ? "disabled" : NodeStatusEnum.ONLINE.getStatus());
        if (StrUtil.isNotBlank(fingerprint)) {
            existing.setFingerprint(fingerprint);
        }
        existing.setMqttClientId("algo-edge-" + computeNode.getId());
        existing.setMqttUsername("algo-edge-" + computeNode.getId());
        if (StrUtil.isNotBlank(agentVersion)) {
            existing.setAgentVersion(agentVersion);
        }
        existing.setNodeRole(computeNode.getNodeRole());
        if (computeNode.getMaxTaskCount() != null) {
            existing.setMaxTaskCount(computeNode.getMaxTaskCount());
        }
        existing.setCephMountReady(cephReady);
        existing.setLastHeartbeatAt(LocalDateTime.now());
        existing.setTags(tags);
        edgeNodeMapper.updateById(existing);
    }

    private EdgeNodeRespVO toEdgeResp(EdgeNodeDO node) {
        EdgeNodeRespVO vo = new EdgeNodeRespVO();
        vo.setId(node.getId());
        vo.setComputeNodeId(node.getComputeNodeId());
        vo.setName(node.getName());
        vo.setHost(node.getHost());
        vo.setStatus(node.getStatus());
        vo.setFingerprint(node.getFingerprint());
        vo.setMqttClientId(node.getMqttClientId());
        vo.setMqttUsername(node.getMqttUsername());
        vo.setAgentVersion(node.getAgentVersion());
        vo.setNodeRole(node.getNodeRole());
        vo.setMaxTaskCount(node.getMaxTaskCount());
        vo.setActiveTaskCount(node.getActiveTaskCount());
        vo.setCephMountReady(node.getCephMountReady());
        vo.setLastHeartbeatAt(node.getLastHeartbeatAt());
        vo.setEnabled(node.getEnabled());
        vo.setRemark(node.getRemark());
        vo.setTags(node.getTags());
        vo.setCreateTime(node.getCreateTime());
        vo.setUpdateTime(node.getUpdateTime());
        if (node.getComputeNodeId() != null) {
            ComputeNodeDO compute = computeNodeMapper.selectById(node.getComputeNodeId());
            if (compute != null) {
                vo.setAgentPort(compute.getAgentPort());
            }
            NodeMetricSnapshotDO metric = nodeMetricSnapshotMapper.selectLatestByNodeId(node.getComputeNodeId());
            if (metric != null) {
                if (metric.getCpuPercent() != null) {
                    vo.setCpuPercent(metric.getCpuPercent().doubleValue());
                }
                if (metric.getMemPercent() != null) {
                    vo.setMemPercent(metric.getMemPercent().doubleValue());
                }
            }
        }
        return vo;
    }

    @Override
    public EdgeRuntimeConfigRespVO runtimeConfig(EdgeRuntimeConfigReqVO reqVO) {
        ComputeNodeDO node = validateAgent(reqVO.getNodeId(), reqVO.getAgentToken());
        return buildRuntimeConfig(node);
    }

    private void validateJoinToken(String requestToken) {
        if (StrUtil.isNotBlank(joinToken)) {
            if (!joinToken.equals(StrUtil.blankToDefault(requestToken, ""))) {
                throw exception(EDGE_JOIN_TOKEN_INVALID);
            }
            return;
        }
        if (!allowOpenEnroll) {
            throw exception(EDGE_JOIN_TOKEN_INVALID);
        }
    }

    private ComputeNodeDO createEdgeNode(EdgeEnrollReqVO reqVO, String host) {
        String role = StrUtil.blankToDefault(reqVO.getNodeRole(), NodeRoleEnum.COMPUTE.getRole());
        ComputeNodeDO node = ComputeNodeDO.builder()
                .name(StrUtil.blankToDefault(reqVO.getHostname(), "edge-" + host))
                .host(host)
                .sshPort(22)
                .agentPort(DEFAULT_AGENT_PORT)
                .status(NodeStatusEnum.ONLINE.getStatus())
                .nodeRole(role)
                .maxGpuCount(0)
                .maxTaskCount(reqVO.getMaxTaskCount() != null && reqVO.getMaxTaskCount() > 0
                        ? reqVO.getMaxTaskCount() : 1)
                .weight(80)
                .agentToken(IdUtil.fastSimpleUUID())
                .remark("EDGE auto-enroll")
                .lastHeartbeatAt(LocalDateTime.now())
                .build();

        Map<String, Boolean> caps = new HashMap<>();
        if (reqVO.getCapabilities() != null) {
            caps.putAll(reqVO.getCapabilities());
        }
        caps.putIfAbsent("algorithm_realtime", true);
        caps.putIfAbsent("algorithm_snap", true);
        caps.putIfAbsent("algorithm_patrol", true);
        caps.put("edge_runtime", true);
        node.setCapabilities(caps);

        Map<String, String> tags = new HashMap<>();
        tags.put("edge_runtime", "true");
        tags.put("node_tier", "edge");
        if (StrUtil.isNotBlank(reqVO.getFingerprint())) {
            tags.put("edge_fingerprint", reqVO.getFingerprint());
        }
        if (StrUtil.isNotBlank(reqVO.getOsInfo())) {
            tags.put("os_info", reqVO.getOsInfo());
        }
        if (StrUtil.isNotBlank(reqVO.getAgentVersion())) {
            tags.put("edge_version", reqVO.getAgentVersion());
        }
        node.setTags(tags);

        ComputeNodeDO platformNode = computeNodeMapper.selectPlatformNode();
        if (platformNode != null) {
            node.setControlPlaneId(platformNode.getId());
        }
        computeNodeMapper.insert(node);
        return node;
    }

    private EdgeRuntimeConfigRespVO buildRuntimeConfig(ComputeNodeDO node) {
        EdgeRuntimeConfigRespVO cfg = new EdgeRuntimeConfigRespVO();
        cfg.setNodeId(node.getId());
        EdgeNodeDO edge = edgeNodeMapper.selectByComputeNodeId(node.getId());
        if (edge != null) {
            cfg.setEdgeNodeId(edge.getId());
            cfg.setEdgeNodeName(edge.getName());
            cfg.setEdgeNodeHost(edge.getHost());
        }
        cfg.setAgentPort(node.getAgentPort() != null ? node.getAgentPort() : DEFAULT_AGENT_PORT);
        cfg.setMqttBrokerUrls(resolveMqttBrokerUrls());
        cfg.setMqttAlgoTenant(mqttAlgoTenant);
        cfg.setMqttUsername("algo-edge-" + node.getId());
        // 与节点凭证绑定，便于后续接到 EMQX HTTP Auth
        cfg.setMqttPassword(node.getAgentToken());
        cfg.setMqttClientId("algo-edge-" + node.getId());
        String root = StrUtil.blankToDefault(mediaHostDataRoot, DEFAULT_MEDIA_ROOT).replaceAll("/+$", "");
        cfg.setMediaHostDataRoot(root);
        cfg.setAlertImagesDir(root + "/alert_images");
        cfg.setMediaSnapDir(root + "/snaps");
        cfg.setControlPlaneUrl(resolveControlPlaneAgentUrl());
        cfg.setAlgoTopics(defaultAlgoTopics());
        return cfg;
    }

    private List<String> resolveMqttBrokerUrls() {
        List<ComputeNodeDO> mqttNodes = computeNodeMapper.selectList().stream()
                .filter(n -> NodeRoleEnum.MQTT.getRole().equals(n.getNodeRole()))
                .filter(n -> NodeStatusEnum.ONLINE.getStatus().equals(n.getStatus())
                        || NodeStatusEnum.PENDING.getStatus().equals(n.getStatus()))
                .collect(Collectors.toList());
        List<String> urls = new ArrayList<>();
        for (ComputeNodeDO n : mqttNodes) {
            int port = 1883;
            Map<String, String> tags = n.getTags();
            if (tags != null && StrUtil.isNotBlank(tags.get("mqtt_tcp_port"))) {
                try {
                    port = Integer.parseInt(tags.get("mqtt_tcp_port").trim());
                } catch (NumberFormatException ignored) {
                    // keep 1883
                }
            }
            if (StrUtil.isNotBlank(n.getHost())) {
                urls.add(n.getHost() + ":" + port);
            }
        }
        // 无 mqtt 角色节点时，回退本机常见地址，避免 EDGE 完全无法启动（运维仍应部署 EMQX）
        if (urls.isEmpty()) {
            urls.add("127.0.0.1:1883");
        }
        return urls;
    }

    private String resolveControlPlaneAgentUrl() {
        if (StrUtil.isNotBlank(controlPlanePublicUrl)) {
            String base = controlPlanePublicUrl.trim().replaceAll("/+$", "");
            if (base.endsWith("/admin-api/node/agent")) {
                return base;
            }
            if (base.endsWith("/admin-api")) {
                return base + "/node/agent";
            }
            return base + "/admin-api/node/agent";
        }
        if (controlPlaneEndpointResolver != null) {
            try {
                String resolved = controlPlaneEndpointResolver.resolveControlPlaneUrl(null);
                if (StrUtil.isNotBlank(resolved)) {
                    return resolved.trim().replaceAll("/+$", "");
                }
            } catch (Exception ignored) {
                // fallback below
            }
        }
        return "http://127.0.0.1:" + serverPort + "/admin-api/node/agent";
    }

    private Map<String, String> defaultAlgoTopics() {
        Map<String, String> map = new LinkedHashMap<>();
        map.put("cmd", "mqtt/iot-algo-task-cmd");
        map.put("ack", "mqtt/iot-algo-task-ack");
        map.put("heartbeat", "mqtt/iot-algo-task-heartbeat");
        map.put("status", "mqtt/iot-algo-task-status");
        map.put("alert", "mqtt/iot-alert-notification");
        map.put("snapshotAlert", "mqtt/iot-snapshot-alert");
        map.put("postprocess", "mqtt/iot-post-process-request");
        return map;
    }

    private ComputeNodeDO validateAgent(Long nodeId, String agentToken) {
        ComputeNodeDO node = computeNodeMapper.selectById(nodeId);
        if (node == null) {
            throw exception(COMPUTE_NODE_NOT_EXISTS);
        }
        if (StrUtil.isBlank(agentToken) || !agentToken.equals(node.getAgentToken())) {
            throw exception(AGENT_TOKEN_INVALID);
        }
        return node;
    }

}
