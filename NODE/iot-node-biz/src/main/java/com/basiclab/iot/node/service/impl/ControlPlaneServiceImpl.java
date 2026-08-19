package com.basiclab.iot.node.service.impl;

import cn.hutool.core.util.IdUtil;
import cn.hutool.core.util.StrUtil;
import cn.hutool.http.HttpRequest;
import cn.hutool.http.HttpResponse;
import cn.hutool.json.JSONObject;
import cn.hutool.json.JSONUtil;
import com.basiclab.iot.common.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.node.dal.dataobject.ComputeNodeDO;
import com.basiclab.iot.node.dal.dataobject.ControlPlanePeerDO;
import com.basiclab.iot.node.dal.pgsql.ComputeNodeMapper;
import com.basiclab.iot.node.dal.pgsql.ControlPlanePeerMapper;
import com.basiclab.iot.node.domain.vo.*;
import com.basiclab.iot.node.enums.NodeStatusEnum;
import com.basiclab.iot.node.service.ComputeNodeService;
import com.basiclab.iot.node.service.ControlPlaneEndpointResolver;
import com.basiclab.iot.node.service.ControlPlaneService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.validation.annotation.Validated;

import javax.annotation.Resource;
import java.net.URI;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.stream.Collectors;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.*;
import static com.basiclab.iot.node.service.impl.ComputeNodeServiceImpl.isPlatformNode;

@Slf4j
@Service
@Validated
public class ControlPlaneServiceImpl implements ControlPlaneService {

    private static final int PEER_HTTP_TIMEOUT_MS = 15000;
    private static final String PEER_TOKEN_HEADER = "X-Peer-Token";
    private static final String LANE_LOCAL_KEY = "local";

    @Resource
    private ComputeNodeMapper computeNodeMapper;
    @Resource
    private ControlPlanePeerMapper controlPlanePeerMapper;
    @Resource
    private ComputeNodeService computeNodeService;
    @Resource
    private ControlPlaneEndpointResolver controlPlaneEndpointResolver;

    @Override
    public PageResult<ClusterLaneRespVO> listLanes(ClusterLanePageReqVO reqVO) {
        computeNodeService.ensurePlatformNode();
        ensureWorkerControlPlaneAssignments();
        long peerTotal = controlPlanePeerMapper.selectCount();
        long total = 1 + peerTotal;
        int pageNo = reqVO.getPageNo();
        int pageSize = reqVO.getPageSize();
        int globalStart = (pageNo - 1) * pageSize;
        if (globalStart >= total) {
            return new PageResult<>(new ArrayList<>(), total);
        }
        int globalEnd = (int) Math.min((long) globalStart + pageSize, total);
        List<ClusterLaneRespVO> lanes = new ArrayList<>();
        if (globalStart == 0) {
            lanes.add(buildLocalLane());
        }
        int firstPeerIdx = globalStart == 0 ? 0 : globalStart - 1;
        int lastPeerIdx = globalEnd - 2;
        if (lastPeerIdx >= firstPeerIdx && lastPeerIdx >= 0) {
            List<ControlPlanePeerDO> peers = fetchPeersOrdered(firstPeerIdx, lastPeerIdx - firstPeerIdx + 1);
            for (ControlPlanePeerDO peer : peers) {
                lanes.add(buildPeerLane(peer));
            }
        }
        return new PageResult<>(lanes, total);
    }

    @Override
    public List<ControlPlanePeerRespVO> listPeers() {
        return controlPlanePeerMapper.selectList().stream()
                .sorted(Comparator.comparing(ControlPlanePeerDO::getId))
                .map(this::toPeerResp)
                .collect(Collectors.toList());
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ControlPlanePeerRespVO createPeer(ControlPlanePeerSaveReqVO reqVO) {
        computeNodeService.ensurePlatformNode();
        String apiBaseUrl = normalizeApiBaseUrl(reqVO.getApiBaseUrl());
        String localApiBaseUrl = normalizeApiBaseUrl(controlPlaneEndpointResolver.resolveControlPlaneUrl(null));
        if (apiBaseUrl.equalsIgnoreCase(localApiBaseUrl)) {
            throw exception(CONTROL_PLANE_PEER_SELF_REGISTER);
        }
        if (controlPlanePeerMapper.selectByApiBaseUrl(apiBaseUrl) != null) {
            throw exception(CONTROL_PLANE_PEER_URL_EXISTS);
        }
        String peerToken = StrUtil.blankToDefault(reqVO.getPeerToken(), IdUtil.fastSimpleUUID());
        ControlPlanePeerDO peer = ControlPlanePeerDO.builder()
                .name(reqVO.getName().trim())
                .apiBaseUrl(apiBaseUrl)
                .peerToken(peerToken)
                .status("unknown")
                .remark(reqVO.getRemark())
                .build();
        controlPlanePeerMapper.insert(peer);
        try {
            registerOutboundPeer(peer, peerToken);
            refreshPeerSnapshot(peer);
            controlPlanePeerMapper.updateById(peer);
        } catch (Exception ex) {
            log.warn("对等中心节点同步失败: {}", ex.getMessage());
            peer.setStatus("offline");
            controlPlanePeerMapper.updateById(peer);
            throw exception(CONTROL_PLANE_PEER_SYNC_FAILED);
        }
        return toPeerResp(peer);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void deletePeer(Long id) {
        ControlPlanePeerDO peer = validatePeerExists(id);
        controlPlanePeerMapper.deleteById(peer.getId());
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void syncPeer(Long id) {
        ControlPlanePeerDO peer = validatePeerExists(id);
        try {
            registerOutboundPeer(peer, peer.getPeerToken());
            refreshPeerSnapshot(peer);
            peer.setLastSyncAt(LocalDateTime.now());
            controlPlanePeerMapper.updateById(peer);
        } catch (Exception ex) {
            peer.setStatus("offline");
            controlPlanePeerMapper.updateById(peer);
            throw exception(CONTROL_PLANE_PEER_SYNC_FAILED);
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void registerPeer(ControlPlanePeerRegisterReqVO reqVO, String inboundToken) {
        if (StrUtil.isBlank(inboundToken) || !inboundToken.equals(reqVO.getPeerToken())) {
            throw exception(CONTROL_PLANE_PEER_TOKEN_INVALID);
        }
        String apiBaseUrl = normalizeApiBaseUrl(reqVO.getApiBaseUrl());
        String localApiBaseUrl = normalizeApiBaseUrl(controlPlaneEndpointResolver.resolveControlPlaneUrl(null));
        if (apiBaseUrl.equalsIgnoreCase(localApiBaseUrl)) {
            return;
        }
        ControlPlanePeerDO existing = controlPlanePeerMapper.selectByApiBaseUrl(apiBaseUrl);
        if (existing != null) {
            existing.setName(reqVO.getName().trim());
            existing.setHost(reqVO.getHost());
            existing.setPeerToken(reqVO.getPeerToken());
            existing.setStatus("online");
            existing.setLastSyncAt(LocalDateTime.now());
            controlPlanePeerMapper.updateById(existing);
            return;
        }
        ControlPlanePeerDO peer = ControlPlanePeerDO.builder()
                .name(reqVO.getName().trim())
                .apiBaseUrl(apiBaseUrl)
                .host(reqVO.getHost())
                .peerToken(reqVO.getPeerToken())
                .status("online")
                .lastSyncAt(LocalDateTime.now())
                .remark("对等中心节点自动注册")
                .build();
        controlPlanePeerMapper.insert(peer);
    }

    @Override
    public ControlPlaneSnapshotRespVO getSnapshot(String inboundToken) {
        if (StrUtil.isBlank(inboundToken)) {
            throw exception(CONTROL_PLANE_PEER_TOKEN_INVALID);
        }
        boolean tokenMatched = controlPlanePeerMapper.selectList().stream()
                .anyMatch(peer -> inboundToken.equals(peer.getPeerToken()));
        if (!tokenMatched) {
            throw exception(CONTROL_PLANE_PEER_TOKEN_INVALID);
        }
        computeNodeService.ensurePlatformNode();
        ensureWorkerControlPlaneAssignments();
        ComputeNodeDO platformNode = computeNodeMapper.selectPlatformNode();
        if (platformNode == null) {
            throw exception(COMPUTE_NODE_NOT_EXISTS);
        }
        ControlPlaneSnapshotRespVO resp = new ControlPlaneSnapshotRespVO();
        resp.setName(platformNode.getName());
        resp.setApiBaseUrl(normalizeApiBaseUrl(controlPlaneEndpointResolver.resolveControlPlaneUrl(null)));
        resp.setHost(platformNode.getHost());
        resp.setPlatformNode(computeNodeService.getNode(platformNode.getId()));
        resp.setWorkerNodes(listLocalWorkerResp(platformNode.getId()));
        return resp;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void batchLaneAction(ClusterLaneBatchReqVO reqVO) {
        if (reqVO.getLaneKey() != null && !LANE_LOCAL_KEY.equals(reqVO.getLaneKey())) {
            throw exception(CONTROL_PLANE_PEER_SYNC_FAILED);
        }
        String action = reqVO.getAction() == null ? "" : reqVO.getAction().trim().toLowerCase(Locale.ROOT);
        boolean maintenanceOn = "maintenance_on".equals(action);
        boolean maintenanceOff = "maintenance_off".equals(action);
        if (!maintenanceOn && !maintenanceOff) {
            return;
        }
        for (Long nodeId : reqVO.getNodeIds()) {
            ComputeNodeDO node = computeNodeMapper.selectById(nodeId);
            if (node == null || isPlatformNode(node)) {
                continue;
            }
            node.setStatus(maintenanceOn ? NodeStatusEnum.MAINTENANCE.getStatus() : NodeStatusEnum.ONLINE.getStatus());
            computeNodeMapper.updateById(node);
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void ensureWorkerControlPlaneAssignments() {
        ComputeNodeDO platformNode = computeNodeMapper.selectPlatformNode();
        if (platformNode == null) {
            return;
        }
        if (platformNode.getControlPlaneId() == null) {
            platformNode.setControlPlaneId(platformNode.getId());
            computeNodeMapper.updateById(platformNode);
        }
        Long platformId = platformNode.getId();
        for (ComputeNodeDO node : computeNodeMapper.selectList()) {
            if (isPlatformNode(node)) {
                if (node.getControlPlaneId() == null) {
                    node.setControlPlaneId(node.getId());
                    computeNodeMapper.updateById(node);
                }
                continue;
            }
            if (node.getControlPlaneId() == null) {
                node.setControlPlaneId(platformId);
                computeNodeMapper.updateById(node);
            }
        }
    }

    private List<ControlPlanePeerDO> fetchPeersOrdered(int offset, int limit) {
        return controlPlanePeerMapper.selectList(new LambdaQueryWrapperX<ControlPlanePeerDO>()
                .orderByAsc(ControlPlanePeerDO::getId)
                .last("LIMIT " + limit + " OFFSET " + offset));
    }

    private ClusterLaneRespVO buildLocalLane() {
        ComputeNodeDO platformNode = computeNodeMapper.selectPlatformNode();
        if (platformNode == null) {
            throw exception(COMPUTE_NODE_NOT_EXISTS);
        }
        ClusterLaneRespVO lane = new ClusterLaneRespVO();
        lane.setLaneKey(LANE_LOCAL_KEY);
        lane.setControlPlaneId(platformNode.getId());
        lane.setIsLocal(true);
        lane.setSyncStatus("synced");
        lane.setCentralNode(computeNodeService.getNode(platformNode.getId()));
        lane.setWorkerNodes(listLocalWorkerResp(platformNode.getId()));
        return lane;
    }

    private List<ComputeNodeRespVO> listLocalWorkerResp(Long platformId) {
        return computeNodeMapper.selectList().stream()
                .filter(node -> !isPlatformNode(node))
                .filter(node -> platformId.equals(node.getControlPlaneId()))
                .sorted(Comparator.comparing(ComputeNodeDO::getUpdateTime, Comparator.nullsLast(Comparator.reverseOrder())))
                .map(node -> computeNodeService.getNode(node.getId()))
                .collect(Collectors.toList());
    }

    private ClusterLaneRespVO buildPeerLane(ControlPlanePeerDO peer) {
        ClusterLaneRespVO lane = new ClusterLaneRespVO();
        lane.setLaneKey("peer-" + peer.getId());
        lane.setIsLocal(false);
        lane.setPeerId(peer.getId());
        lane.setSyncStatus(peer.getStatus());
        try {
            ControlPlaneSnapshotRespVO snapshot = fetchRemoteSnapshot(peer);
            ComputeNodeRespVO central = snapshot.getPlatformNode();
            if (central != null) {
                central.setIsRemote(true);
                central.setPeerId(peer.getId());
                lane.setControlPlaneId(central.getId());
                lane.setCentralNode(central);
            } else {
                lane.setCentralNode(buildPeerPlaceholderCentral(peer));
            }
            List<ComputeNodeRespVO> workers = snapshot.getWorkerNodes() == null
                    ? new ArrayList<>()
                    : snapshot.getWorkerNodes();
            workers.forEach(worker -> {
                worker.setIsRemote(true);
                worker.setPeerId(peer.getId());
            });
            lane.setWorkerNodes(workers);
            if (!"offline".equals(peer.getStatus())) {
                lane.setSyncStatus("online");
            }
        } catch (Exception ex) {
            log.debug("拉取对等中心节点快照失败: peerId={}, {}", peer.getId(), ex.getMessage());
            lane.setCentralNode(buildPeerPlaceholderCentral(peer));
            lane.setWorkerNodes(new ArrayList<>());
            lane.setSyncStatus("offline");
        }
        return lane;
    }

    private ComputeNodeRespVO buildPeerPlaceholderCentral(ControlPlanePeerDO peer) {
        ComputeNodeRespVO central = new ComputeNodeRespVO();
        central.setId(peer.getRemotePlatformNodeId());
        central.setName(peer.getName());
        central.setHost(peer.getHost() != null ? peer.getHost() : extractHost(peer.getApiBaseUrl()));
        central.setStatus(peer.getStatus());
        central.setNodeRole("hybrid");
        central.setIsPlatform(true);
        central.setIsRemote(true);
        central.setPeerId(peer.getId());
        return central;
    }

    private void registerOutboundPeer(ControlPlanePeerDO peer, String peerToken) {
        ComputeNodeDO platformNode = computeNodeMapper.selectPlatformNode();
        ControlPlanePeerRegisterReqVO body = new ControlPlanePeerRegisterReqVO();
        body.setName(platformNode != null ? platformNode.getName() : "控制面节点");
        body.setApiBaseUrl(normalizeApiBaseUrl(controlPlaneEndpointResolver.resolveControlPlaneUrl(null)));
        body.setHost(platformNode != null ? platformNode.getHost() : null);
        body.setPeerToken(peerToken);
        String url = peer.getApiBaseUrl() + "/node/control-plane/peer/register";
        HttpResponse response = HttpRequest.post(url)
                .header(PEER_TOKEN_HEADER, peerToken)
                .body(JSONUtil.toJsonStr(body))
                .timeout(PEER_HTTP_TIMEOUT_MS)
                .execute();
        if (!response.isOk()) {
            throw new IllegalStateException("HTTP " + response.getStatus());
        }
        JSONObject json = JSONUtil.parseObj(response.body());
        if (json.getInt("code", 500) != 0) {
            throw new IllegalStateException(json.getStr("msg", "register failed"));
        }
        peer.setStatus("online");
        peer.setLastSyncAt(LocalDateTime.now());
    }

    private void refreshPeerSnapshot(ControlPlanePeerDO peer) {
        ControlPlaneSnapshotRespVO snapshot = fetchRemoteSnapshot(peer);
        if (snapshot.getPlatformNode() != null && snapshot.getPlatformNode().getId() != null) {
            peer.setRemotePlatformNodeId(snapshot.getPlatformNode().getId());
        }
        if (snapshot.getHost() != null) {
            peer.setHost(snapshot.getHost());
        }
        peer.setStatus("online");
        peer.setLastSyncAt(LocalDateTime.now());
    }

    private ControlPlaneSnapshotRespVO fetchRemoteSnapshot(ControlPlanePeerDO peer) {
        String url = peer.getApiBaseUrl() + "/node/control-plane/snapshot";
        HttpResponse response = HttpRequest.get(url)
                .header(PEER_TOKEN_HEADER, peer.getPeerToken())
                .timeout(PEER_HTTP_TIMEOUT_MS)
                .execute();
        if (!response.isOk()) {
            throw new IllegalStateException("HTTP " + response.getStatus());
        }
        JSONObject json = JSONUtil.parseObj(response.body());
        if (json.getInt("code", 500) != 0) {
            throw new IllegalStateException(json.getStr("msg", "snapshot failed"));
        }
        return JSONUtil.toBean(json.getJSONObject("data"), ControlPlaneSnapshotRespVO.class);
    }

    private ControlPlanePeerDO validatePeerExists(Long id) {
        ControlPlanePeerDO peer = controlPlanePeerMapper.selectById(id);
        if (peer == null) {
            throw exception(CONTROL_PLANE_PEER_NOT_EXISTS);
        }
        return peer;
    }

    private ControlPlanePeerRespVO toPeerResp(ControlPlanePeerDO peer) {
        return BeanUtils.toBean(peer, ControlPlanePeerRespVO.class);
    }

    private String normalizeApiBaseUrl(String raw) {
        if (raw == null) {
            return "";
        }
        String trimmed = raw.trim();
        while (trimmed.endsWith("/")) {
            trimmed = trimmed.substring(0, trimmed.length() - 1);
        }
        return trimmed;
    }

    private String extractHost(String apiBaseUrl) {
        try {
            URI uri = URI.create(apiBaseUrl);
            return uri.getHost();
        } catch (Exception ignored) {
            return apiBaseUrl;
        }
    }

}
