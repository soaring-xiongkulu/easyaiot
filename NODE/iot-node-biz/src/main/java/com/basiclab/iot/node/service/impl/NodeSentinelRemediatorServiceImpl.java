package com.basiclab.iot.node.service.impl;

import cn.hutool.core.util.StrUtil;
import com.basiclab.iot.node.dal.dataobject.ComputeNodeDO;
import com.basiclab.iot.node.dal.pgsql.ComputeNodeMapper;
import com.basiclab.iot.node.domain.vo.NodeMediaRemoteDeployRespVO;
import com.basiclab.iot.node.domain.vo.NodeSentinelRemediateReqVO;
import com.basiclab.iot.node.domain.vo.NodeWorkloadBundleBatchReqVO;
import com.basiclab.iot.node.domain.vo.NodeWorkloadBundleBatchRespVO;
import com.basiclab.iot.node.domain.vo.NodeWorkloadBundleNodeResultVO;
import com.basiclab.iot.node.enums.WorkloadBundleTypeEnum;
import com.basiclab.iot.node.framework.SentinelCapabilityRegistry;
import com.basiclab.iot.node.service.NodeFfmpegDeployService;
import com.basiclab.iot.node.service.NodeMediaService;
import com.basiclab.iot.node.service.NodeRuntimeCppDeployService;
import com.basiclab.iot.node.service.NodeSentinelRemediatorService;
import com.basiclab.iot.node.service.NodeWorkloadBundleService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.AGENT_COMMAND_FAILED;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.AGENT_TOKEN_INVALID;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.COMPUTE_NODE_NOT_EXISTS;

@Service
@Slf4j
public class NodeSentinelRemediatorServiceImpl implements NodeSentinelRemediatorService {

    private static final String REMEDIATE_LOCK_PREFIX = "node:sentinel:remediate:lock:";

    @Resource
    private ComputeNodeMapper computeNodeMapper;
    @Resource
    private SentinelCapabilityRegistry sentinelCapabilityRegistry;
    @Resource
    private NodeRuntimeCppDeployService nodeRuntimeCppDeployService;
    @Resource
    private NodeWorkloadBundleService nodeWorkloadBundleService;
    @Resource
    private NodeMediaService nodeMediaService;
    @Resource
    private NodeFfmpegDeployService nodeFfmpegDeployService;
    @Resource
    private StringRedisTemplate stringRedisTemplate;

    @Override
    public Map<String, Object> remediate(NodeSentinelRemediateReqVO reqVO) {
        ComputeNodeDO node = computeNodeMapper.selectById(reqVO.getNodeId());
        if (node == null) {
            throw exception(COMPUTE_NODE_NOT_EXISTS);
        }
        if (StrUtil.isNotBlank(reqVO.getAgentToken())
                && !reqVO.getAgentToken().equals(node.getAgentToken())) {
            throw exception(AGENT_TOKEN_INVALID);
        }

        String lockKey = REMEDIATE_LOCK_PREFIX + node.getId();
        Boolean locked = stringRedisTemplate.opsForValue()
                .setIfAbsent(lockKey, reqVO.getComponentId(), 600, TimeUnit.SECONDS);
        if (Boolean.FALSE.equals(locked)) {
            return Map.of(
                    "success", false,
                    "reason", "repair_in_progress",
                    "message", "同节点自愈进行中",
                    "componentId", reqVO.getComponentId());
        }

        try {
            String action = resolveAction(reqVO);
            List<Map<String, Object>> logs = new ArrayList<>();
            boolean success;
            String message;
            try {
                HealOutcome outcome = switch (action) {
                    case "deploy_runtime_cpp" -> deployRuntime(node);
                    case "deploy_bundle" -> deployBundle(node, reqVO);
                    case "deploy_media_stack" -> deployMediaStack(node);
                    case "deploy_ffmpeg" -> deployFfmpeg(node);
                    default -> throw exception(AGENT_COMMAND_FAILED, "未知修复动作: " + action);
                };
                success = outcome.success;
                message = outcome.message;
                logs.addAll(outcome.logs);
            } catch (Exception e) {
                success = false;
                message = e.getMessage();
                logs.add(Map.of("name", "执行异常", "status", "failed", "output", String.valueOf(e.getMessage())));
                log.warn("Sentinel 修复失败 nodeId={} component={}: {}",
                        node.getId(), reqVO.getComponentId(), e.getMessage());
            }
            Map<String, Object> result = new HashMap<>();
            result.put("success", success);
            result.put("nodeId", node.getId());
            result.put("componentId", reqVO.getComponentId());
            result.put("action", action);
            result.put("message", message);
            result.put("logs", logs);
            result.put("attempt", reqVO.getAttempt());
            result.put("maxAttempts", reqVO.getMaxAttempts());
            return result;
        } finally {
            stringRedisTemplate.delete(lockKey);
        }
    }

    @SuppressWarnings("unchecked")
    private String resolveAction(NodeSentinelRemediateReqVO reqVO) {
        if (StrUtil.isNotBlank(reqVO.getAction())) {
            return reqVO.getAction().trim();
        }
        Map<String, Object> remediation = sentinelCapabilityRegistry.getRemediation();
        Object specRaw = remediation.get(reqVO.getComponentId());
        if (specRaw instanceof Map<?, ?> spec) {
            Object action = spec.get("action");
            if (action != null) {
                return String.valueOf(action);
            }
        }
        throw exception(AGENT_COMMAND_FAILED, "组件未配置修复动作: " + reqVO.getComponentId());
    }

    private HealOutcome deployRuntime(ComputeNodeDO node) {
        List<NodeMediaRemoteDeployRespVO.DeployStep> steps = new ArrayList<>();
        boolean success = nodeRuntimeCppDeployService.deployOnNodeIfMissing(node.getId(), steps);
        return new HealOutcome(success, success ? "RUNTIME 已分发或已存在" : "RUNTIME 分发失败", toLogs(steps));
    }

    @SuppressWarnings("unchecked")
    private HealOutcome deployBundle(ComputeNodeDO node, NodeSentinelRemediateReqVO reqVO) {
        String bundleType = "model_train";
        if (reqVO.getParams() != null && reqVO.getParams().get("bundle") != null) {
            bundleType = String.valueOf(reqVO.getParams().get("bundle"));
        } else {
            Map<String, Object> remediation = sentinelCapabilityRegistry.getRemediation();
            Object specRaw = remediation.get(reqVO.getComponentId());
            if (specRaw instanceof Map<?, ?> spec && spec.get("params") instanceof Map<?, ?> params) {
                Object bundle = params.get("bundle");
                if (bundle != null) {
                    bundleType = String.valueOf(bundle);
                }
            }
        }
        WorkloadBundleTypeEnum bundle = WorkloadBundleTypeEnum.of(bundleType);
        if (bundle == null) {
            throw exception(AGENT_COMMAND_FAILED, "未知 bundle: " + bundleType);
        }
        NodeWorkloadBundleBatchReqVO batch = new NodeWorkloadBundleBatchReqVO();
        batch.setNodeIds(List.of(node.getId()));
        batch.setBundleType(bundle.getType());
        NodeWorkloadBundleBatchRespVO resp = nodeWorkloadBundleService.batchDeployFullBySsh(batch);
        if (resp.getResults() == null || resp.getResults().isEmpty()) {
            return new HealOutcome(false, "bundle 分发无结果", List.of());
        }
        NodeWorkloadBundleNodeResultVO one = resp.getResults().get(0);
        boolean success = Boolean.TRUE.equals(one.getSuccess());
        return new HealOutcome(success,
                StrUtil.blankToDefault(one.getMessage(), success ? "bundle 分发成功" : "bundle 分发失败"),
                toLogs(one.getSteps()));
    }

    private HealOutcome deployMediaStack(ComputeNodeDO node) {
        var resp = nodeMediaService.deployMediaStackBySsh(node.getId());
        boolean success = resp != null && Boolean.TRUE.equals(resp.getSuccess());
        String message = resp != null ? resp.getMessage() : "媒体栈分发无结果";
        List<NodeMediaRemoteDeployRespVO.DeployStep> steps = resp != null ? resp.getSteps() : List.of();
        return new HealOutcome(success, StrUtil.blankToDefault(message, success ? "媒体栈已就绪" : "媒体栈分发失败"),
                toLogs(steps));
    }

    private HealOutcome deployFfmpeg(ComputeNodeDO node) {
        List<NodeMediaRemoteDeployRespVO.DeployStep> steps = new ArrayList<>();
        boolean success = nodeFfmpegDeployService.deployOnNodeIfMissing(node.getId(), steps);
        return new HealOutcome(success, success ? "ffmpeg 已分发或已存在" : "ffmpeg 分发失败", toLogs(steps));
    }

    private List<Map<String, Object>> toLogs(List<NodeMediaRemoteDeployRespVO.DeployStep> steps) {
        List<Map<String, Object>> logs = new ArrayList<>();
        if (steps == null) {
            return logs;
        }
        for (NodeMediaRemoteDeployRespVO.DeployStep step : steps) {
            if (step == null) {
                continue;
            }
            Map<String, Object> row = new HashMap<>();
            row.put("name", step.getName());
            row.put("status", step.getStatus());
            row.put("output", step.getOutput());
            logs.add(row);
        }
        return logs;
    }

    private record HealOutcome(boolean success, String message, List<Map<String, Object>> logs) {
    }
}
