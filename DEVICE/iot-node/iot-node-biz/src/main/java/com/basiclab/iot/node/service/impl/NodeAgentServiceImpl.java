package com.basiclab.iot.node.service.impl;

import cn.hutool.core.util.StrUtil;
import com.basiclab.iot.node.dal.dataobject.ComputeNodeDO;
import com.basiclab.iot.node.dal.dataobject.NodeMetricSnapshotDO;
import com.basiclab.iot.node.dal.pgsql.ComputeNodeMapper;
import com.basiclab.iot.node.dal.pgsql.NodeMetricSnapshotMapper;
import com.basiclab.iot.node.domain.vo.NodeAgentHeartbeatReqVO;
import com.basiclab.iot.node.domain.vo.NodeAgentRegisterReqVO;
import com.basiclab.iot.node.enums.NodeRoleEnum;
import com.basiclab.iot.node.enums.NodeStatusEnum;
import com.basiclab.iot.node.service.EdgeNodeService;
import com.basiclab.iot.node.service.NodeAgentService;
import com.basiclab.iot.node.service.NodeClusterMetricsBroadcaster;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.validation.annotation.Validated;

import javax.annotation.Resource;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.TimeUnit;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.AGENT_CAPACITY_MISMATCH;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.AGENT_HOST_MISMATCH;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.AGENT_TOKEN_INVALID;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.COMPUTE_NODE_NOT_EXISTS;

@Service
@Validated
@Slf4j
public class NodeAgentServiceImpl implements NodeAgentService {

    private static final String HEARTBEAT_KEY_PREFIX = "node:heartbeat:";
    /** 已绑定的内存容量指纹，用于拦截同 NODE_ID 下两套硬件交叉上报 */
    private static final String CAPACITY_KEY_PREFIX = "node:agent:cap:";
    private static final long HEARTBEAT_TTL_SECONDS = 60;
    /** 容量差异超过该比例视为冲突（宿主机 61G vs 容器 30G ≈ 50%） */
    private static final double CAPACITY_MISMATCH_RATIO = 0.20;
    private static final String TAG_AGENT_HOSTNAME = "agent_hostname";
    private static final String TAG_AGENT_MEM_TOTAL = "agent_mem_total_bytes";

    @Resource
    private ComputeNodeMapper computeNodeMapper;
    @Resource
    private NodeMetricSnapshotMapper nodeMetricSnapshotMapper;
    @Resource
    private StringRedisTemplate stringRedisTemplate;
    @Resource
    private NodeClusterMetricsBroadcaster nodeClusterMetricsBroadcaster;

    @Resource
    private EdgeNodeService edgeNodeService;

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void register(NodeAgentRegisterReqVO reqVO) {
        ComputeNodeDO node = validateAgent(reqVO.getNodeId(), reqVO.getAgentToken());
        node.setStatus(NodeStatusEnum.ONLINE.getStatus());
        node.setLastHeartbeatAt(LocalDateTime.now());
        // 显式 register 仅在原 Agent 心跳过期时允许换绑主机名
        bindOrValidateAgentHostname(node, reqVO.getHostname(), true, null);
        if (reqVO.getCapabilities() != null && !reqVO.getCapabilities().isEmpty()) {
            Map<String, Boolean> caps = node.getCapabilities() != null
                    ? new HashMap<>(node.getCapabilities()) : new HashMap<>();
            caps.putAll(reqVO.getCapabilities());
            if (ComputeNodeServiceImpl.isPlatformNode(node)) {
                caps.put("platform", true);
            }
            node.setCapabilities(caps);
        }
        computeNodeMapper.updateById(node);
        touchHeartbeat(node.getId());
        // 注册只推单节点状态，避免全量 snapshot 清空前端已合并的容量字段
        nodeClusterMetricsBroadcaster.broadcastNodeUpdate(node, null);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void heartbeat(NodeAgentHeartbeatReqVO reqVO) {
        ComputeNodeDO node = validateAgent(reqVO.getNodeId(), reqVO.getAgentToken());
        bindOrValidateAgentHostname(node, reqVO.getHostname(), false, reqVO.getMemTotalBytes());
        // 即使 hostname 相同/缺失，也要按内存总量指纹拦截两套硬件交叉上报
        bindOrValidateAgentCapacity(node, reqVO.getMemTotalBytes(), reqVO.getDiskTotalBytes(), false);
        node.setStatus(NodeStatusEnum.ONLINE.getStatus());
        node.setLastHeartbeatAt(LocalDateTime.now());
        syncGpuCountFromHeartbeat(node, reqVO.getGpuInfo());
        syncCephMountFromHeartbeat(node, reqVO);
        computeNodeMapper.updateById(node);
        // 边缘运行时节点：刷新 edge_node 管理表心跳/Ceph 状态
        if (node.getTags() != null && ("true".equalsIgnoreCase(node.getTags().get("edge_runtime"))
                || "edge".equalsIgnoreCase(node.getTags().get("node_tier")))) {
            try {
                edgeNodeService.syncEdgeNodeRecord(node, null);
            } catch (Exception ignored) {
                // 管理表失败不影响心跳主链路
            }
        }

        NodeMetricSnapshotDO snapshot = NodeMetricSnapshotDO.builder()
                .nodeId(node.getId())
                .cpuPercent(reqVO.getCpuPercent())
                .memPercent(reqVO.getMemPercent())
                .memUsedBytes(reqVO.getMemUsedBytes())
                .memTotalBytes(reqVO.getMemTotalBytes())
                .diskPercent(reqVO.getDiskPercent())
                .diskUsedBytes(reqVO.getDiskUsedBytes())
                .diskTotalBytes(reqVO.getDiskTotalBytes())
                .bandwidthMbps(reqVO.getBandwidthMbps())
                .activeTasks(reqVO.getActiveTasks())
                .gpuInfo(reqVO.getGpuInfo())
                .collectedAt(LocalDateTime.now())
                .build();
        nodeMetricSnapshotMapper.insert(snapshot);
        touchHeartbeat(node.getId());
        nodeClusterMetricsBroadcaster.broadcastNodeUpdate(node, snapshot);
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

    private void touchHeartbeat(Long nodeId) {
        stringRedisTemplate.opsForValue().set(
                HEARTBEAT_KEY_PREFIX + nodeId,
                String.valueOf(System.currentTimeMillis()),
                HEARTBEAT_TTL_SECONDS,
                TimeUnit.SECONDS);
    }

    /**
     * 绑定或校验 Agent 主机名。
     * <p>
     * - heartbeat：容量指纹一致时允许同机改名；
     * - register：仅心跳过期时允许换绑（禁止「控制面直接刷新 hostname」，
     *   否则冲突 Agent 会通过 register 与本机来回抢绑）。
     */
    private void bindOrValidateAgentHostname(ComputeNodeDO node, String hostname,
                                             boolean allowRebindWhenStale, Long memTotalBytes) {
        if (StrUtil.isBlank(hostname)) {
            return;
        }
        String reported = hostname.trim();
        Map<String, String> tags = node.getTags() != null
                ? new HashMap<>(node.getTags()) : new HashMap<>();
        String bound = tags.get(TAG_AGENT_HOSTNAME);
        if (StrUtil.isNotBlank(bound) && !bound.equalsIgnoreCase(reported)) {
            boolean staleTakeover = allowRebindWhenStale && !hasFreshHeartbeat(node.getId());
            // 同机改名：仅 heartbeat 带容量且指纹一致时允许
            boolean sameMachineRename = memTotalBytes != null
                    && memTotalBytes > 0
                    && capacityMatchesBound(node, memTotalBytes);
            if (!staleTakeover && !sameMachineRename) {
                log.warn("拒绝冲突 Agent: nodeId={}, boundHostname={}, reportedHostname={}",
                        node.getId(), bound, reported);
                throw exception(AGENT_HOST_MISMATCH);
            }
            if (sameMachineRename) {
                log.info("同机主机名变更，允许换绑: nodeId={}, {} -> {}", node.getId(), bound, reported);
            } else {
                log.warn("原 Agent 心跳已过期，允许换绑主机名: nodeId={}, {} -> {}", node.getId(), bound, reported);
            }
        }
        tags.put(TAG_AGENT_HOSTNAME, reported);
        node.setTags(tags);
    }

    private boolean capacityMatchesBound(ComputeNodeDO node, long memTotalBytes) {
        Long boundMem = readBoundMemTotal(node, CAPACITY_KEY_PREFIX + node.getId());
        if (boundMem == null || boundMem <= 0) {
            return false;
        }
        return relativeDiff(boundMem, memTotalBytes) <= CAPACITY_MISMATCH_RATIO;
    }

    /**
     * 按内存总量指纹绑定 Agent，解决「同 hostname / 旧 Agent 不报 hostname」时两套硬件指标跳动。
     * <p>
     * 控制面节点特例：若新上报容量显著更大（宿主机 > 容器 cgroup），允许抢绑，稳定到真实宿主机容量。
     */
    private void bindOrValidateAgentCapacity(ComputeNodeDO node, Long memTotalBytes, Long diskTotalBytes,
                                            boolean allowRebindWhenStale) {
        if (memTotalBytes == null || memTotalBytes <= 0) {
            return;
        }
        String redisKey = CAPACITY_KEY_PREFIX + node.getId();
        Long boundMem = readBoundMemTotal(node, redisKey);

        if (boundMem != null && boundMem > 0 && relativeDiff(boundMem, memTotalBytes) > CAPACITY_MISMATCH_RATIO) {
            boolean platformLargerTakeover = ComputeNodeServiceImpl.isPlatformNode(node)
                    && memTotalBytes > boundMem * (1.0 + CAPACITY_MISMATCH_RATIO);
            boolean staleTakeover = allowRebindWhenStale && !hasFreshHeartbeat(node.getId());
            if (platformLargerTakeover) {
                log.warn("平台节点采纳更大容量上报: nodeId={}, boundMem={}, reportedMem={}",
                        node.getId(), boundMem, memTotalBytes);
            } else if (!staleTakeover) {
                log.warn("拒绝冲突容量上报: nodeId={}, boundMem={}, reportedMem={}, diskTotal={}",
                        node.getId(), boundMem, memTotalBytes, diskTotalBytes);
                throw exception(AGENT_CAPACITY_MISMATCH);
            } else {
                log.warn("原 Agent 心跳已过期，允许换绑容量: nodeId={}, {} -> {}",
                        node.getId(), boundMem, memTotalBytes);
            }
        }

        String fingerprint = memTotalBytes + ":" + (diskTotalBytes == null ? 0 : diskTotalBytes);
        stringRedisTemplate.opsForValue().set(redisKey, fingerprint, HEARTBEAT_TTL_SECONDS * 2, TimeUnit.SECONDS);

        Map<String, String> tags = node.getTags() != null
                ? new HashMap<>(node.getTags()) : new HashMap<>();
        tags.put(TAG_AGENT_MEM_TOTAL, String.valueOf(memTotalBytes));
        if (diskTotalBytes != null && diskTotalBytes > 0) {
            tags.put("agent_disk_total_bytes", String.valueOf(diskTotalBytes));
        }
        node.setTags(tags);
    }

    private Long readBoundMemTotal(ComputeNodeDO node, String redisKey) {
        String redisVal = stringRedisTemplate.opsForValue().get(redisKey);
        if (StrUtil.isNotBlank(redisVal)) {
            try {
                return Long.parseLong(redisVal.split(":")[0]);
            } catch (NumberFormatException ignored) {
                // fall through to tags
            }
        }
        if (node.getTags() != null && StrUtil.isNotBlank(node.getTags().get(TAG_AGENT_MEM_TOTAL))) {
            try {
                return Long.parseLong(node.getTags().get(TAG_AGENT_MEM_TOTAL));
            } catch (NumberFormatException ignored) {
                return null;
            }
        }
        return null;
    }

    private static double relativeDiff(long a, long b) {
        long max = Math.max(a, b);
        if (max <= 0) {
            return 0;
        }
        return Math.abs(a - b) * 1.0 / max;
    }

    private boolean hasFreshHeartbeat(Long nodeId) {
        Boolean exists = stringRedisTemplate.hasKey(HEARTBEAT_KEY_PREFIX + nodeId);
        return Boolean.TRUE.equals(exists);
    }

    /** GPU / 混合节点：根据 Agent 上报的 gpu_info 同步 maxGpuCount（含控制面 HYBRID 节点） */
    private void syncGpuCountFromHeartbeat(ComputeNodeDO node, java.util.List<java.util.Map<String, Object>> gpuInfo) {
        String role = node.getNodeRole();
        if (gpuInfo == null || gpuInfo.isEmpty()) {
            return;
        }
        if (!NodeRoleEnum.GPU.getRole().equals(role) && !NodeRoleEnum.HYBRID.getRole().equals(role)) {
            return;
        }
        int detected = gpuInfo.size();
        if (node.getMaxGpuCount() == null || node.getMaxGpuCount() < detected) {
            node.setMaxGpuCount(detected);
        }
    }

    /** 将 Agent 上报的挂载状态写入节点 tags，供调度器与拓扑使用 */
    private void syncCephMountFromHeartbeat(ComputeNodeDO node, NodeAgentHeartbeatReqVO reqVO) {
        if (reqVO.getCephMountReady() == null && StrUtil.isBlank(reqVO.getCephMountRoot())) {
            return;
        }
        Map<String, String> tags = node.getTags() != null
                ? new HashMap<>(node.getTags()) : new HashMap<>();
        if (reqVO.getCephMountReady() != null) {
            String ready = Boolean.TRUE.equals(reqVO.getCephMountReady()) ? "true" : "false";
            tags.put("ceph_mount_ready", ready);
            tags.put("nfs_mount_ready", ready);
        }
        if (StrUtil.isNotBlank(reqVO.getCephMountRoot())) {
            String root = reqVO.getCephMountRoot().trim();
            tags.put("ceph_mount_path", root);
            tags.put("media_mount_path", root);
        }
        if (reqVO.getClusterMode() != null) {
            tags.put("cluster_mode", Boolean.TRUE.equals(reqVO.getClusterMode()) ? "true" : "false");
        }
        node.setTags(tags);
    }

}
