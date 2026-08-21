package com.basiclab.iot.node.service.impl;

import cn.hutool.core.collection.CollUtil;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.node.dal.dataobject.ComputeNodeDO;
import com.basiclab.iot.node.dal.dataobject.NodeMetricSnapshotDO;
import com.basiclab.iot.node.dal.dataobject.NodeWorkloadBindingDO;
import com.basiclab.iot.node.dal.pgsql.ComputeNodeMapper;
import com.basiclab.iot.node.dal.pgsql.NodeMetricSnapshotMapper;
import com.basiclab.iot.node.dal.pgsql.NodeWorkloadBindingMapper;
import com.basiclab.iot.node.domain.vo.ComputeNodePageReqVO;
import com.basiclab.iot.node.domain.vo.NodeSchedulerAllocateReqVO;
import com.basiclab.iot.node.domain.vo.NodeSchedulerAllocateRespVO;
import com.basiclab.iot.node.util.NodeFunctions;
import com.basiclab.iot.node.enums.NodeStatusEnum;
import com.basiclab.iot.node.service.NodeSchedulerService;
import com.basiclab.iot.node.service.NodeSentinelService;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.validation.annotation.Validated;

import javax.annotation.Resource;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.NODE_POOL_EXHAUSTED;

@Service
@Validated
public class NodeSchedulerServiceImpl implements NodeSchedulerService {

    @Resource
    private ComputeNodeMapper computeNodeMapper;
    @Resource
    private NodeMetricSnapshotMapper nodeMetricSnapshotMapper;
    @Resource
    private NodeWorkloadBindingMapper nodeWorkloadBindingMapper;

    @Resource
    private NodeSentinelService nodeSentinelService;

    @Value("${easyaiot.scheduler.prefer-gpu-default:true}")
    private boolean preferGpuDefault;

    @Value("${easyaiot.sentinel.scheduling-enabled:true}")
    private boolean sentinelSchedulingEnabled;

    @Override
    @Transactional(rollbackFor = Exception.class)
    public NodeSchedulerAllocateRespVO allocate(NodeSchedulerAllocateReqVO reqVO) {
        if (Boolean.TRUE.equals(reqVO.getSticky())) {
            NodeWorkloadBindingDO existing = nodeWorkloadBindingMapper.selectByWorkload(
                    reqVO.getWorkloadType(), reqVO.getWorkloadId());
            if (existing != null && "running".equals(existing.getStatus())) {
                ComputeNodeDO node = computeNodeMapper.selectById(existing.getNodeId());
                if (node != null && NodeStatusEnum.ONLINE.getStatus().equals(node.getStatus())) {
                    if (!requiresNfsMount(reqVO) || isNfsMountReady(node)) {
                        return buildResp(node, existing.getId(), null);
                    }
                }
            }
        }

        ComputeNodePageReqVO pageReqVO = new ComputeNodePageReqVO();
        pageReqVO.setPageNo(1);
        pageReqVO.setPageSize(200);
        pageReqVO.setStatus(NodeStatusEnum.ONLINE.getStatus());
        if (reqVO.getRequirements() != null) {
            pageReqVO.setRegion(reqVO.getRequirements().getRegion());
        }
        PageResult<ComputeNodeDO> page = computeNodeMapper.selectPage(pageReqVO);
        final String workloadType = reqVO.getWorkloadType();
        List<ComputeNodeDO> candidates = page.getList().stream()
                .filter(node -> matchRequirements(node, reqVO))
                .sorted(Comparator.comparingDouble((ComputeNodeDO node) -> scoreNode(node, reqVO)).reversed())
                .toList();

        if (candidates.isEmpty()) {
            throw exception(NODE_POOL_EXHAUSTED);
        }
        ComputeNodeDO selected = candidates.get(0);
        NodeWorkloadBindingDO binding = NodeWorkloadBindingDO.builder()
                .nodeId(selected.getId())
                .workloadType(reqVO.getWorkloadType())
                .workloadId(reqVO.getWorkloadId())
                .status("running")
                .bindAt(LocalDateTime.now())
                .build();
        NodeWorkloadBindingDO existing = nodeWorkloadBindingMapper.selectByWorkload(
                reqVO.getWorkloadType(), reqVO.getWorkloadId());
        if (existing != null) {
            binding.setId(existing.getId());
            nodeWorkloadBindingMapper.updateById(binding);
        } else {
            nodeWorkloadBindingMapper.insert(binding);
        }
        return buildResp(selected, binding.getId(), pickGpuIds(selected));
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void release(String workloadType, String workloadId) {
        NodeWorkloadBindingDO binding = nodeWorkloadBindingMapper.selectByWorkload(workloadType, workloadId);
        if (binding != null) {
            binding.setStatus("stopped");
            nodeWorkloadBindingMapper.updateById(binding);
        }
    }

    private boolean matchRequirements(ComputeNodeDO node, NodeSchedulerAllocateReqVO reqVO) {
        if (!matchNodeFunctions(node, reqVO.getWorkloadType())) {
            return false;
        }
        NodeSchedulerAllocateReqVO.Requirements req = reqVO.getRequirements();
        if (req == null) {
            return true;
        }
        if (CollUtil.isNotEmpty(req.getExcludeNodeIds()) && req.getExcludeNodeIds().contains(node.getId())) {
            return false;
        }
        List<String> requiredCapabilities = resolveRequiredCapabilities(reqVO);
        if (!requiredCapabilities.isEmpty()) {
            Map<String, Boolean> caps = node.getCapabilities();
            for (String capability : requiredCapabilities) {
                if (caps == null || !Boolean.TRUE.equals(caps.get(capability))) {
                    return false;
                }
            }
        }
        if (!isNodeResourceHealthy(node, reqVO.getWorkloadType())) {
            return false;
        }
        if (requiresGpu(req) && !isGpuNode(node)) {
            return false;
        }
        if (requiresNfsMount(reqVO) && !isNfsMountReady(node)) {
            return false;
        }
        if (shouldRequireSchedulable(reqVO) && !matchSentinelSchedulable(node, reqVO)) {
            return false;
        }
        if (!matchResourceLimits(node, reqVO)) {
            return false;
        }
        long running = nodeWorkloadBindingMapper.countRunningByNodeId(node.getId());
        return running < node.getMaxTaskCount();
    }

    private boolean requiresGpu(NodeSchedulerAllocateReqVO.Requirements req) {
        return req != null && req.getGpuCount() != null && req.getGpuCount() > 0;
    }

    private boolean resolvePreferGpu(NodeSchedulerAllocateReqVO reqVO) {
        NodeSchedulerAllocateReqVO.Requirements req = reqVO.getRequirements();
        if (req != null && req.getPreferGpu() != null) {
            return req.getPreferGpu();
        }
        if (requiresGpu(req)) {
            return true;
        }
        return preferGpuDefault;
    }

    /** GPU 节点：配置了 maxGpuCount，或心跳上报了 GPU 硬件 */
    private boolean isGpuNode(ComputeNodeDO node) {
        if (node.getMaxGpuCount() != null && node.getMaxGpuCount() > 0) {
            return true;
        }
        NodeMetricSnapshotDO metric = nodeMetricSnapshotMapper.selectLatestByNodeId(node.getId());
        return metric != null && CollUtil.isNotEmpty(metric.getGpuInfo());
    }

    /** 无 GPU 的计算类节点 */
    private boolean isComputeOnlyNode(ComputeNodeDO node) {
        return NodeFunctions.isComputeWorkloadNode(node) && !isGpuNode(node);
    }

    /**
     * 推流转发：过滤资源明显不足的节点（CPU 为整机平均利用率 0–100%）。
     */
    private boolean isNodeResourceHealthy(ComputeNodeDO node, String workloadType) {
        if (!"stream_forward".equals(workloadType)) {
            return true;
        }
        NodeMetricSnapshotDO metric = nodeMetricSnapshotMapper.selectLatestByNodeId(node.getId());
        if (metric == null) {
            return true;
        }
        double cpu = metric.getCpuPercent() != null ? metric.getCpuPercent().doubleValue() : 0;
        double mem = metric.getMemPercent() != null ? metric.getMemPercent().doubleValue() : 0;
        if (mem >= 95) {
            return false;
        }
        if (cpu >= 85) {
            return false;
        }
        return !(cpu >= 60 && mem >= 85);
    }

    private boolean shouldRequireSchedulable(NodeSchedulerAllocateReqVO reqVO) {
        NodeSchedulerAllocateReqVO.Requirements req = reqVO.getRequirements();
        if (req != null && req.getRequireSchedulable() != null) {
            return req.getRequireSchedulable();
        }
        return sentinelSchedulingEnabled;
    }

    private boolean matchSentinelSchedulable(ComputeNodeDO node, NodeSchedulerAllocateReqVO reqVO) {
        if (ComputeNodeServiceImpl.isPlatformNode(node)) {
            return true;
        }
        List<String> requiredCapabilities = resolveRequiredCapabilities(reqVO);
        if (CollUtil.isEmpty(requiredCapabilities)) {
            return true;
        }
        for (String capability : requiredCapabilities) {
            if (!nodeSentinelService.isCapabilitySchedulable(node.getId(), capability)) {
                return false;
            }
        }
        return true;
    }

    private boolean matchResourceLimits(ComputeNodeDO node, NodeSchedulerAllocateReqVO reqVO) {
        NodeSchedulerAllocateReqVO.Requirements req = reqVO.getRequirements();
        NodeMetricSnapshotDO metric = nodeMetricSnapshotMapper.selectLatestByNodeId(node.getId());
        if (metric == null) {
            return true;
        }
        Integer maxCpu = req != null ? req.getMaxCpuPercent() : null;
        Integer maxMem = req != null ? req.getMaxMemPercent() : null;
        if ("stream_forward".equals(reqVO.getWorkloadType())) {
            if (maxCpu == null) {
                maxCpu = 85;
            }
            if (maxMem == null) {
                maxMem = 95;
            }
        }
        if (maxCpu != null && metric.getCpuPercent() != null
                && metric.getCpuPercent().doubleValue() >= maxCpu) {
            return false;
        }
        if (maxMem != null && metric.getMemPercent() != null
                && metric.getMemPercent().doubleValue() >= maxMem) {
            return false;
        }
        Integer minVram = req != null ? req.getMinFreeVramMb() : null;
        if (minVram == null && requiresGpu(req)) {
            minVram = 2048;
        }
        if (minVram != null && minVram > 0 && CollUtil.isNotEmpty(metric.getGpuInfo())) {
            double maxFreeMb = 0;
            for (Map<String, Object> gpu : metric.getGpuInfo()) {
                if (gpu == null) {
                    continue;
                }
                double total = toDouble(gpu.get("mem_total_mb"));
                double used = toDouble(gpu.get("mem_used_mb"));
                maxFreeMb = Math.max(maxFreeMb, Math.max(0, total - used));
            }
            if (maxFreeMb > 0 && maxFreeMb < minVram) {
                return false;
            }
        }
        return true;
    }

    private double toDouble(Object value) {
        if (value instanceof Number number) {
            return number.doubleValue();
        }
        if (value != null) {
            try {
                return Double.parseDouble(String.valueOf(value));
            } catch (NumberFormatException ignored) {
                return 0;
            }
        }
        return 0;
    }

    private boolean matchNodeFunctions(ComputeNodeDO node, String workloadType) {
        return NodeFunctions.matchesWorkload(node, workloadType);
    }

    private List<String> resolveRequiredCapabilities(NodeSchedulerAllocateReqVO reqVO) {
        List<String> capabilities = new ArrayList<>();
        NodeSchedulerAllocateReqVO.Requirements req = reqVO.getRequirements();
        if (req != null && CollUtil.isNotEmpty(req.getCapabilities())) {
            capabilities.addAll(req.getCapabilities());
        }
        // 推流转发需在节点本机 SRS 收流，必须同时具备 srs_live 能力
        if ("stream_forward".equals(reqVO.getWorkloadType()) && !capabilities.contains("srs_live")) {
            capabilities.add("srs_live");
        }
        return capabilities;
    }

    /** 算法任务等需读取 NFS 共享模型/抓拍路径时要求节点挂载就绪 */
    private boolean requiresNfsMount(NodeSchedulerAllocateReqVO reqVO) {
        NodeSchedulerAllocateReqVO.Requirements req = reqVO.getRequirements();
        if (req != null && (Boolean.TRUE.equals(req.getRequireNfsMount())
                || Boolean.TRUE.equals(req.getRequireCephMount()))) {
            return true;
        }
        String workloadType = reqVO.getWorkloadType();
        if ("model_train".equals(workloadType)) {
            return req != null && (Boolean.TRUE.equals(req.getRequireNfsMount())
                    || Boolean.TRUE.equals(req.getRequireCephMount()));
        }
        if (!"algorithm_task".equals(workloadType)) {
            return false;
        }
        if (req == null || CollUtil.isEmpty(req.getCapabilities())) {
            return false;
        }
        for (String capability : req.getCapabilities()) {
            if (capability != null && capability.startsWith("algorithm_")) {
                return true;
            }
        }
        return false;
    }

    private boolean isNfsMountReady(ComputeNodeDO node) {
        if (ComputeNodeServiceImpl.isPlatformNode(node)) {
            return true;
        }
        Map<String, String> tags = node.getTags();
        if (tags == null) {
            return false;
        }
        String ready = tags.containsKey("nfs_mount_ready")
                ? tags.get("nfs_mount_ready")
                : tags.get("ceph_mount_ready");
        if (ready == null) {
            return false;
        }
        return "true".equalsIgnoreCase(ready) || "1".equals(ready) || "yes".equalsIgnoreCase(ready);
    }

    private double scoreNode(ComputeNodeDO node, NodeSchedulerAllocateReqVO reqVO) {
        String workloadType = reqVO.getWorkloadType();
        double weight = node.getWeight() != null ? node.getWeight() : 100;
        NodeMetricSnapshotDO metric = nodeMetricSnapshotMapper.selectLatestByNodeId(node.getId());
        double cpu = metric != null && metric.getCpuPercent() != null
                ? metric.getCpuPercent().doubleValue() / 100.0 : 0.3;
        double mem = metric != null && metric.getMemPercent() != null
                ? metric.getMemPercent().doubleValue() / 100.0 : 0.3;
        long running = nodeWorkloadBindingMapper.countRunningByNodeId(node.getId());
        double taskLoad = node.getMaxTaskCount() > 0 ? (double) running / node.getMaxTaskCount() : 0;

        double score;
        if ("stream_forward".equals(workloadType)) {
            // 空闲槽位优先，兼顾内存/CPU，避免所有分片堆到单一低负载节点
            double capacity = Math.max(1, node.getMaxTaskCount());
            double freeRatio = Math.max(0, (capacity - running) / capacity);
            double cpuNorm = Math.min(cpu, 2.0);
            double resourceHealth = 0.55 * freeRatio + 0.25 * (1 - mem) + 0.20 * Math.max(0, 1 - cpuNorm);
            score = weight * resourceHealth;
        } else {
            score = weight * (1 - cpu) * (1 - taskLoad);
        }
        // 控制面节点仅作兜底：推流转发大幅降权，其它计算负载适度降权
        if (ComputeNodeServiceImpl.isPlatformNode(node)) {
            if ("stream_forward".equals(workloadType)) {
                score *= 0.02;
            } else {
                score *= 0.1;
            }
        }
        boolean preferGpu = resolvePreferGpu(reqVO);
        if (preferGpu && isGpuNode(node)) {
            score *= 2.0;
        } else if (!preferGpu && isComputeOnlyNode(node)) {
            score *= 1.5;
        }
        return score;
    }

    private String pickGpuIds(ComputeNodeDO node) {
        if (node.getMaxGpuCount() == null || node.getMaxGpuCount() <= 0) {
            return null;
        }
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < node.getMaxGpuCount(); i++) {
            if (i > 0) {
                sb.append(',');
            }
            sb.append(i);
        }
        return sb.toString();
    }

    private NodeSchedulerAllocateRespVO buildResp(ComputeNodeDO node, Long bindingId, String gpuIds) {
        NodeSchedulerAllocateRespVO resp = new NodeSchedulerAllocateRespVO();
        resp.setNodeId(node.getId());
        resp.setHost(node.getHost());
        resp.setAgentPort(node.getAgentPort());
        resp.setGpuIds(gpuIds);
        resp.setBindingId(bindingId);
        return resp;
    }

}
