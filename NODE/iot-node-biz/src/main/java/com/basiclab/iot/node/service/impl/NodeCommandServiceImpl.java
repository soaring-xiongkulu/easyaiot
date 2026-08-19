package com.basiclab.iot.node.service.impl;

import cn.hutool.http.HttpRequest;
import cn.hutool.http.HttpResponse;
import cn.hutool.json.JSONObject;
import cn.hutool.json.JSONUtil;
import com.basiclab.iot.common.exception.ServiceException;
import com.basiclab.iot.node.dal.dataobject.ComputeNodeDO;
import com.basiclab.iot.node.dal.dataobject.NodeWorkloadBindingDO;
import com.basiclab.iot.node.dal.pgsql.ComputeNodeMapper;
import com.basiclab.iot.node.dal.pgsql.NodeWorkloadBindingMapper;
import com.basiclab.iot.node.domain.vo.NodeWorkloadDeployReqVO;
import com.basiclab.iot.node.domain.vo.NodeWorkloadDeployRespVO;
import com.basiclab.iot.node.enums.NodeStatusEnum;
import com.basiclab.iot.node.service.NodeAiWorkloadSyncService;
import com.basiclab.iot.node.service.NodeCommandService;
import com.basiclab.iot.node.service.NodeSentinelService;
import com.basiclab.iot.node.service.NodeVideoWorkloadSyncService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.validation.annotation.Validated;

import javax.annotation.Resource;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.AGENT_COMMAND_FAILED;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.COMPUTE_NODE_NOT_EXISTS;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.COMPUTE_NODE_OFFLINE;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.WORKLOAD_BINDING_NOT_EXISTS;

@Slf4j
@Service
@Validated
public class NodeCommandServiceImpl implements NodeCommandService {

    private static final int AGENT_TIMEOUT_MS = 60000;

    @Resource
    private ComputeNodeMapper computeNodeMapper;
    @Resource
    private NodeWorkloadBindingMapper nodeWorkloadBindingMapper;
    @Resource
    private NodeVideoWorkloadSyncService nodeVideoWorkloadSyncService;
    @Resource
    private NodeAiWorkloadSyncService nodeAiWorkloadSyncService;
    @Resource
    private NodeSentinelService nodeSentinelService;

    @Override
    @Transactional(rollbackFor = Exception.class)
    public NodeWorkloadDeployRespVO deployWorkload(NodeWorkloadDeployReqVO reqVO) {
        ComputeNodeDO node = validateOnlineNode(reqVO.getNodeId());
        nodeVideoWorkloadSyncService.syncBeforeDeploy(node, reqVO.getWorkloadType());
        nodeAiWorkloadSyncService.syncBeforeDeploy(node, reqVO.getWorkloadType());

        Map<String, Object> requirements = new HashMap<>();
        if (reqVO.getEnv() != null && reqVO.getEnv().get("capabilities") != null) {
            requirements.put("capabilities", reqVO.getEnv().get("capabilities"));
        }
        nodeSentinelService.validateBeforeDeploy(node.getId(), reqVO.getWorkloadType(), requirements);

        String runtime = reqVO.getRuntime() == null || reqVO.getRuntime().isBlank()
                ? "process" : reqVO.getRuntime().trim().toLowerCase();
        if ("process".equals(runtime) && (reqVO.getCommand() == null || reqVO.getCommand().isEmpty())) {
            throw exception(AGENT_COMMAND_FAILED, "runtime=process 时启动命令不能为空");
        }
        Map<String, Object> body = new HashMap<>();
        body.put("workloadType", reqVO.getWorkloadType());
        body.put("workloadId", reqVO.getWorkloadId());
        body.put("command", reqVO.getCommand());
        body.put("runtime", runtime);
        body.put("image", reqVO.getImage());
        body.put("workDir", reqVO.getWorkDir());
        body.put("logDir", reqVO.getLogDir());
        body.put("gpuIds", reqVO.getGpuIds());
        body.put("env", reqVO.getEnv());
        if (reqVO.getFiles() != null && !reqVO.getFiles().isEmpty()) {
            body.put("files", reqVO.getFiles());
        }

        JSONObject result = callAgentWithStaleWorkloadRetry(node, reqVO, body);
        Integer pid = result.getInt("pid");

        NodeWorkloadBindingDO binding = nodeWorkloadBindingMapper.selectByWorkload(
                reqVO.getWorkloadType(), reqVO.getWorkloadId());
        if (binding == null) {
            binding = NodeWorkloadBindingDO.builder()
                    .nodeId(node.getId())
                    .workloadType(reqVO.getWorkloadType())
                    .workloadId(reqVO.getWorkloadId())
                    .status("running")
                    .processPid(pid)
                    .bindAt(LocalDateTime.now())
                    .build();
            nodeWorkloadBindingMapper.insert(binding);
        } else {
            binding.setNodeId(node.getId());
            binding.setStatus("running");
            binding.setProcessPid(pid);
            binding.setBindAt(LocalDateTime.now());
            nodeWorkloadBindingMapper.updateById(binding);
        }

        NodeWorkloadDeployRespVO resp = new NodeWorkloadDeployRespVO();
        resp.setPid(pid);
        resp.setNodeId(node.getId());
        resp.setWorkloadType(reqVO.getWorkloadType());
        resp.setWorkloadId(reqVO.getWorkloadId());
        resp.setBindingId(binding.getId());
        return resp;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void stopWorkload(Long nodeId, String workloadType, String workloadId) {
        ComputeNodeDO node = computeNodeMapper.selectById(nodeId);
        if (node == null) {
            throw exception(COMPUTE_NODE_NOT_EXISTS);
        }
        Map<String, Object> body = new HashMap<>();
        body.put("workloadType", workloadType);
        body.put("workloadId", workloadId);
        // 硬停失败必须抛出，避免前端误以为已 docker rm
        JSONObject data = callAgent(node, "/workload/stop", body);
        // 新 Agent 会回 removed；显式 false 表示本机未找到容器/进程
        if (data != null && data.containsKey("removed") && !data.getBool("removed", false)) {
            throw exception(AGENT_COMMAND_FAILED,
                    "未找到可停止的容器/进程 workloadId=" + workloadId);
        }
        NodeWorkloadBindingDO binding = nodeWorkloadBindingMapper.selectByWorkload(workloadType, workloadId);
        if (binding != null) {
            binding.setStatus("stopped");
            binding.setProcessPid(null);
            nodeWorkloadBindingMapper.updateById(binding);
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void stopWorkloadByBinding(String workloadType, String workloadId) {
        NodeWorkloadBindingDO binding = nodeWorkloadBindingMapper.selectByWorkload(workloadType, workloadId);
        if (binding == null || binding.getNodeId() == null) {
            throw exception(WORKLOAD_BINDING_NOT_EXISTS, workloadType + ":" + workloadId);
        }
        stopWorkload(binding.getNodeId(), workloadType, workloadId);
    }

    private ComputeNodeDO validateOnlineNode(Long nodeId) {
        ComputeNodeDO node = computeNodeMapper.selectById(nodeId);
        if (node == null) {
            throw exception(COMPUTE_NODE_NOT_EXISTS);
        }
        if (!NodeStatusEnum.ONLINE.getStatus().equals(node.getStatus())) {
            throw exception(COMPUTE_NODE_OFFLINE);
        }
        return node;
    }

    private JSONObject callAgentWithStaleWorkloadRetry(
            ComputeNodeDO node, NodeWorkloadDeployReqVO reqVO, Map<String, Object> body) {
        try {
            return callAgent(node, "/workload/deploy", body);
        } catch (ServiceException e) {
            if (!isWorkloadAlreadyRunning(e)) {
                throw e;
            }
            log.info("工作负载已运行，先停止再重试 nodeId={} {}:{}",
                    node.getId(), reqVO.getWorkloadType(), reqVO.getWorkloadId());
            stopWorkloadQuietly(node.getId(), reqVO.getWorkloadType(), reqVO.getWorkloadId());
            return callAgent(node, "/workload/deploy", body);
        }
    }

    private void stopWorkloadQuietly(Long nodeId, String workloadType, String workloadId) {
        try {
            stopWorkload(nodeId, workloadType, workloadId);
        } catch (ServiceException e) {
            log.warn("停止 stale workload 失败 nodeId={} {}:{} — {}",
                    nodeId, workloadType, workloadId, e.getMessage());
        }
    }

    private static boolean isWorkloadAlreadyRunning(ServiceException e) {
        if (e == null || e.getMessage() == null) {
            return false;
        }
        return e.getMessage().contains("工作负载已运行");
    }

    private JSONObject callAgent(ComputeNodeDO node, String path, Map<String, Object> body) {
        int port = node.getAgentPort() != null ? node.getAgentPort() : 9100;
        String url = String.format("http://%s:%d%s", node.getHost(), port, path);
        try {
            HttpResponse response = HttpRequest.post(url)
                    .header("X-Agent-Token", node.getAgentToken())
                    .header("Content-Type", "application/json")
                    .body(JSONUtil.toJsonStr(body))
                    .timeout(AGENT_TIMEOUT_MS)
                    .execute();
            if (!response.isOk()) {
                throw exception(AGENT_COMMAND_FAILED,
                        "HTTP " + response.getStatus() + " — " + response.body());
            }
            JSONObject json = JSONUtil.parseObj(response.body());
            if (json.getInt("code", -1) != 0) {
                throw exception(AGENT_COMMAND_FAILED, json.getStr("msg", response.body()));
            }
            return json.getJSONObject("data") != null ? json.getJSONObject("data") : new JSONObject();
        } catch (ServiceException e) {
            throw e;
        } catch (Exception e) {
            log.error("Agent 请求异常 nodeId={} url={}: {}", node.getId(), url, e.getMessage(), e);
            String detail = e.getMessage() != null ? e.getMessage() : e.getClass().getSimpleName();
            throw exception(AGENT_COMMAND_FAILED, node.getHost() + ":" + port + " — " + detail);
        }
    }

}