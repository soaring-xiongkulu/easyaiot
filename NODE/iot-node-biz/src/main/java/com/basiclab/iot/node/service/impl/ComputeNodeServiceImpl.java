package com.basiclab.iot.node.service.impl;

import cn.hutool.core.util.IdUtil;
import cn.hutool.core.util.StrUtil;
import com.basiclab.iot.common.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.node.dal.dataobject.ComputeNodeDO;
import com.basiclab.iot.node.dal.dataobject.NodeMetricSnapshotDO;
import com.basiclab.iot.node.dal.dataobject.NodeSshCredentialDO;
import com.basiclab.iot.node.dal.pgsql.ComputeNodeMapper;
import com.basiclab.iot.node.dal.pgsql.NodeMetricSnapshotMapper;
import com.basiclab.iot.node.dal.pgsql.NodeSshCredentialMapper;
import com.basiclab.iot.node.dal.pgsql.NodeWorkloadBindingMapper;
import com.basiclab.iot.node.domain.vo.ComputeNodePageReqVO;
import com.basiclab.iot.node.domain.vo.ComputeNodeRespVO;
import com.basiclab.iot.node.domain.vo.ComputeNodeSaveReqVO;
import com.basiclab.iot.node.domain.vo.NodeAgentCheckRespVO;
import com.basiclab.iot.node.domain.vo.NodeMediaRemoteDeployRespVO;
import com.basiclab.iot.node.domain.vo.NodePortCheckRespVO;
import com.basiclab.iot.node.domain.vo.NodeMetricTrendPointRespVO;
import com.basiclab.iot.node.domain.vo.NodeMetricTrendReqVO;
import com.basiclab.iot.node.domain.vo.NodeMetricTrendRespVO;
import com.basiclab.iot.node.domain.vo.PlatformAgentBootstrapRespVO;
import com.basiclab.iot.node.domain.vo.NodeMetricTrendSeriesRespVO;
import com.basiclab.iot.node.enums.NodeRoleEnum;
import com.basiclab.iot.node.enums.NodeStatusEnum;
import com.basiclab.iot.node.service.ControlPlaneEndpointResolver;
import com.basiclab.iot.node.service.ComputeNodeService;
import com.basiclab.iot.node.util.AgentDeployUtil;
import com.basiclab.iot.node.util.CredentialEncryptUtil;
import com.basiclab.iot.node.util.HostIpUtil;
import com.basiclab.iot.node.util.RemotePortCheckUtil;
import com.basiclab.iot.node.util.SshClientUtil;
import com.basiclab.iot.node.util.SshSessionHelper;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.validation.annotation.Validated;

import javax.annotation.Resource;
import java.io.File;
import java.io.InputStream;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Base64;
import java.util.Comparator;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.*;

@Service
@Validated
@Slf4j
public class ComputeNodeServiceImpl implements ComputeNodeService {

    private static final int DEFAULT_SSH_PORT = 22;
    private static final int DEFAULT_AGENT_PORT = 9100;
    private static final int DEPLOY_TIMEOUT_MS = 300000;
    private static final int EXPORT_PIP_WHEELS_TIMEOUT_MS = 600000;
    private static final String PLATFORM_CAPABILITY_KEY = "platform";
    private static final String PLATFORM_NODE_NAME = "控制面节点";

    @Resource
    private ComputeNodeMapper computeNodeMapper;
    @Resource
    private NodeSshCredentialMapper nodeSshCredentialMapper;
    @Resource
    private NodeMetricSnapshotMapper nodeMetricSnapshotMapper;
    @Resource
    private NodeWorkloadBindingMapper nodeWorkloadBindingMapper;
    @Resource
    private ObjectMapper objectMapper;

    @Value("${easyaiot.agent.source-path:}")
    private String agentSourcePath;
    @Resource
    private ControlPlaneEndpointResolver controlPlaneEndpointResolver;

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ComputeNodeRespVO createNode(ComputeNodeSaveReqVO createReqVO) {
        if (computeNodeMapper.selectByHost(createReqVO.getHost()) != null) {
            throw exception(COMPUTE_NODE_HOST_EXISTS);
        }
        ComputeNodeDO node = BeanUtils.toBean(createReqVO, ComputeNodeDO.class);
        node.setSshPort(defaultPort(createReqVO.getSshPort(), DEFAULT_SSH_PORT));
        node.setAgentPort(defaultPort(createReqVO.getAgentPort(), DEFAULT_AGENT_PORT));
        node.setStatus(NodeStatusEnum.PENDING.getStatus());
        node.setWeight(createReqVO.getWeight() != null ? createReqVO.getWeight() : 100);
        applyRoleGpuDefaults(node, createReqVO.getMaxGpuCount());
        node.setMaxTaskCount(createReqVO.getMaxTaskCount() != null ? createReqVO.getMaxTaskCount() : 50);
        if (node.getCapabilities() == null) {
            node.setCapabilities(defaultCapabilities(createReqVO.getNodeRole()));
        }
        node.setAgentToken(IdUtil.fastSimpleUUID());
        ensurePlatformNode();
        ComputeNodeDO platformNode = computeNodeMapper.selectPlatformNode();
        if (platformNode != null) {
            node.setControlPlaneId(platformNode.getId());
        }
        computeNodeMapper.insert(node);
        saveSshCredential(node.getId(), createReqVO);
        return toRespVO(node, true);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void updateNode(ComputeNodeSaveReqVO updateReqVO) {
        ComputeNodeDO existing = validateExists(updateReqVO.getId());
        if (isPlatformNode(existing)) {
            throw exception(COMPUTE_NODE_PLATFORM_UPDATE_FORBIDDEN);
        }
        ComputeNodeDO other = computeNodeMapper.selectByHost(updateReqVO.getHost());
        if (other != null && !other.getId().equals(updateReqVO.getId())) {
            throw exception(COMPUTE_NODE_HOST_EXISTS);
        }
        ComputeNodeDO updateObj = BeanUtils.toBean(updateReqVO, ComputeNodeDO.class);
        updateObj.setSshPort(defaultPort(updateReqVO.getSshPort(), defaultPort(existing.getSshPort(), DEFAULT_SSH_PORT)));
        updateObj.setAgentPort(defaultPort(updateReqVO.getAgentPort(), defaultPort(existing.getAgentPort(), DEFAULT_AGENT_PORT)));
        updateObj.setAgentToken(existing.getAgentToken());
        updateObj.setStatus(existing.getStatus());
        updateObj.setLastHeartbeatAt(existing.getLastHeartbeatAt());
        applyRoleGpuDefaults(updateObj, updateReqVO.getMaxGpuCount());
        computeNodeMapper.updateById(updateObj);
        saveSshCredential(updateReqVO.getId(), updateReqVO);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void deleteNode(Long id) {
        ComputeNodeDO node = validateExists(id);
        if (isPlatformNode(node)) {
            throw exception(COMPUTE_NODE_PLATFORM_DELETE_FORBIDDEN);
        }
        if (nodeWorkloadBindingMapper.countRunningByNodeId(id) > 0) {
            throw exception(COMPUTE_NODE_HAS_WORKLOAD);
        }
        computeNodeMapper.deleteById(id);
        NodeSshCredentialDO credential = nodeSshCredentialMapper.selectByNodeId(id);
        if (credential != null) {
            nodeSshCredentialMapper.deleteById(credential.getId());
        }
    }

    @Override
    public ComputeNodeRespVO getNode(Long id) {
        ComputeNodeDO node = validateExists(id);
        return toRespVO(node, false);
    }

    @Override
    public PageResult<ComputeNodeRespVO> getNodePage(ComputeNodePageReqVO pageReqVO) {
        ensurePlatformNode();
        PageResult<ComputeNodeDO> pageResult = computeNodeMapper.selectPage(pageReqVO);
        List<ComputeNodeRespVO> list = pageResult.getList().stream()
                .map(node -> toRespVO(node, false))
                .sorted(platformNodeFirstComparator())
                .collect(Collectors.toList());
        return new PageResult<>(list, pageResult.getTotal());
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void ensurePlatformNode() {
        String hostIp = HostIpUtil.detectHostIp();
        ComputeNodeDO platformNode = computeNodeMapper.selectPlatformNode();
        if (platformNode != null) {
            boolean changed = false;
            if (!hostIp.equals(platformNode.getHost())) {
                ComputeNodeDO conflict = computeNodeMapper.selectByHost(hostIp);
                if (conflict == null || conflict.getId().equals(platformNode.getId())) {
                    platformNode.setHost(hostIp);
                    changed = true;
                }
            }
            Map<String, Boolean> caps = platformNode.getCapabilities() != null
                    ? new HashMap<>(platformNode.getCapabilities()) : defaultCapabilities(platformNode.getNodeRole());
            if (!Boolean.TRUE.equals(caps.get(PLATFORM_CAPABILITY_KEY))) {
                caps.put(PLATFORM_CAPABILITY_KEY, true);
                changed = true;
            }
            if (mergeDefaultCapabilities(caps, platformNode.getNodeRole())) {
                changed = true;
            }
            if (changed) {
                platformNode.setCapabilities(caps);
                computeNodeMapper.updateById(platformNode);
            }
            return;
        }

        ComputeNodeDO byHost = computeNodeMapper.selectByHost(hostIp);
        if (byHost != null) {
            Map<String, Boolean> caps = byHost.getCapabilities() != null
                    ? new HashMap<>(byHost.getCapabilities())
                    : defaultCapabilities(byHost.getNodeRole());
            caps.put(PLATFORM_CAPABILITY_KEY, true);
            mergeDefaultCapabilities(caps, byHost.getNodeRole());
            byHost.setCapabilities(caps);
            computeNodeMapper.updateById(byHost);
            return;
        }

        ComputeNodeDO node = new ComputeNodeDO();
        node.setName(PLATFORM_NODE_NAME);
        node.setHost(hostIp);
        node.setNodeRole(NodeRoleEnum.HYBRID.getRole());
        node.setStatus(NodeStatusEnum.ONLINE.getStatus());
        node.setSshPort(DEFAULT_SSH_PORT);
        node.setAgentPort(DEFAULT_AGENT_PORT);
        node.setWeight(100);
        node.setMaxGpuCount(0);
        node.setMaxTaskCount(50);
        Map<String, Boolean> caps = defaultCapabilities(NodeRoleEnum.HYBRID.getRole());
        caps.put(PLATFORM_CAPABILITY_KEY, true);
        node.setCapabilities(caps);
        node.setAgentToken(IdUtil.fastSimpleUUID());
        node.setRemark("平台控制面宿主机，自动纳管");
        computeNodeMapper.insert(node);
        node.setControlPlaneId(node.getId());
        computeNodeMapper.updateById(node);
        log.info("已自动纳管控制面节点: id={}, host={}", node.getId(), node.getHost());
    }

    @Override
    public PlatformAgentBootstrapRespVO getPlatformAgentBootstrap() {
        ensurePlatformNode();
        ComputeNodeDO node = computeNodeMapper.selectPlatformNode();
        if (node == null) {
            throw exception(COMPUTE_NODE_NOT_EXISTS);
        }
        PlatformAgentBootstrapRespVO resp = new PlatformAgentBootstrapRespVO();
        resp.setNodeId(node.getId());
        resp.setAgentToken(node.getAgentToken());
        resp.setAgentPort(defaultPort(node.getAgentPort(), DEFAULT_AGENT_PORT));
        resp.setControlPlaneUrl(resolveControlPlaneUrl(null));
        return resp;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean testSsh(Long id) {
        ComputeNodeDO node = validateExists(id);
        if (isPlatformNode(node)) {
            throw exception(COMPUTE_NODE_PLATFORM_UPDATE_FORBIDDEN);
        }
        NodeSshCredentialDO credential = nodeSshCredentialMapper.selectByNodeId(id);
        if (credential == null) {
            throw exception(SSH_CREDENTIAL_NOT_EXISTS);
        }
        String password = null;
        String privateKey = null;
        if ("password".equals(credential.getAuthType())) {
            password = CredentialEncryptUtil.decrypt(credential.getCredentialEnc());
        } else {
            privateKey = CredentialEncryptUtil.decrypt(credential.getCredentialEnc());
        }
        int sshPort = resolveSshPort(node);
        boolean ok = SshClientUtil.testConnection(node.getHost(), sshPort,
                credential.getUsername(), credential.getAuthType(), password, privateKey);
        credential.setLastTestAt(LocalDateTime.now());
        credential.setLastTestOk(ok);
        nodeSshCredentialMapper.updateById(credential);
        if (!ok) {
            throw exception(SSH_CONNECT_FAILED);
        }
        return true;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public String resetAgentToken(Long id) {
        ComputeNodeDO node = validateExists(id);
        if (isPlatformNode(node)) {
            throw exception(COMPUTE_NODE_PLATFORM_UPDATE_FORBIDDEN);
        }
        String token = IdUtil.fastSimpleUUID();
        node.setAgentToken(token);
        computeNodeMapper.updateById(node);
        return token;
    }

    @Override
    public ComputeNodeRespVO getAgentSetup(Long id) {
        ComputeNodeDO node = validateExists(id);
        if (!NodeStatusEnum.PENDING.getStatus().equals(node.getStatus())) {
            throw exception(COMPUTE_NODE_NOT_PENDING);
        }
        return toRespVO(node, true);
    }

    @Override
    public NodeMediaRemoteDeployRespVO deployAgentBySsh(Long nodeId, String controlPlaneUrlOverride) {
        ComputeNodeDO node = validateExists(nodeId);
        if (isPlatformNode(node)) {
            throw exception(COMPUTE_NODE_PLATFORM_UPDATE_FORBIDDEN);
        }
        NodeSshCredentialDO credential = nodeSshCredentialMapper.selectByNodeId(nodeId);
        if (credential == null) {
            throw exception(SSH_CREDENTIAL_NOT_EXISTS);
        }
        String password = null;
        String privateKey = null;
        if ("password".equals(credential.getAuthType())) {
            password = CredentialEncryptUtil.decrypt(credential.getCredentialEnc());
        } else {
            privateKey = CredentialEncryptUtil.decrypt(credential.getCredentialEnc());
        }

        NodeMediaRemoteDeployRespVO resp = new NodeMediaRemoteDeployRespVO();
        List<NodeMediaRemoteDeployRespVO.DeployStep> steps = new ArrayList<>();
        resp.setSteps(steps);

        int sshPort = resolveSshPort(node);
        try (SshSessionHelper ssh = SshSessionHelper.connect(
                node.getHost(),
                sshPort,
                credential.getUsername(),
                credential.getAuthType(),
                password,
                privateKey)) {

            steps.add(runDeployStep("SSH 连接", "success", "已连接 " + node.getHost() + ":" + sshPort));

            NodePortCheckRespVO portCheck = checkAgentPortOnSession(ssh, node);
            steps.add(portCheck.getSteps().get(0));
            if (!Boolean.TRUE.equals(portCheck.getPortsReady())) {
                resp.setSuccess(false);
                resp.setMessage(portCheck.getMessage());
                return resp;
            }

            String targetPython = detectRemotePythonVersion(ssh);
            String sourceRoot = resolveAgentSource();
            AgentPipBundle pipBundle = resolveAgentPipBundle(targetPython);
            NodeMediaRemoteDeployRespVO.DeployStep wheelsStep = ensureLocalAgentPipWheels(pipBundle, targetPython);
            steps.add(wheelsStep);
            if (!"success".equals(wheelsStep.getStatus())) {
                resp.setSuccess(false);
                resp.setMessage(wheelsStep.getOutput());
                return resp;
            }

            NodeMediaRemoteDeployRespVO.DeployStep pythonStep = ensureRemotePythonRuntime(ssh, targetPython);
            steps.add(pythonStep);
            if (!"success".equals(pythonStep.getStatus())) {
                resp.setSuccess(false);
                resp.setMessage(pythonStep.getOutput());
                return resp;
            }

            NodeMediaRemoteDeployRespVO.DeployStep syncStep = syncAgentFiles(ssh, sourceRoot, pipBundle);
            steps.add(syncStep);
            if (!"success".equals(syncStep.getStatus())) {
                resp.setSuccess(false);
                resp.setMessage(syncStep.getOutput());
                return resp;
            }

            String controlPlaneUrl = resolveControlPlaneUrl(controlPlaneUrlOverride);
            int agentPort = node.getAgentPort() != null && node.getAgentPort() > 0
                    ? node.getAgentPort() : DEFAULT_AGENT_PORT;
            String envContent = AgentDeployUtil.buildEnvContent(
                    node.getId(),
                    node.getAgentToken() != null ? node.getAgentToken() : "",
                    agentPort,
                    controlPlaneUrl);
            String installScript = AgentDeployUtil.buildInstallScript(envContent);
            String encoded = Base64.getEncoder().encodeToString(installScript.getBytes(StandardCharsets.UTF_8));
            SshSessionHelper.SshExecResult installResult = ssh.exec(
                    "echo " + encoded + " | base64 -d > /tmp/easyaiot-agent-install.sh "
                            + "&& chmod +x /tmp/easyaiot-agent-install.sh "
                            + "&& sudo bash /tmp/easyaiot-agent-install.sh",
                    DEPLOY_TIMEOUT_MS);
            NodeMediaRemoteDeployRespVO.DeployStep installStep = new NodeMediaRemoteDeployRespVO.DeployStep();
            installStep.setName("安装启动");
            String installOutput = trimDeployOutput(installResult.combinedOutput(), 8000);
            installStep.setOutput(installOutput);
            if (!isAgentInstallOutputSuccessful(installResult, installOutput)) {
                installStep.setStatus("failed");
                steps.add(installStep);
                resp.setSuccess(false);
                resp.setMessage(resolveAgentInstallFailureMessage(installOutput));
                return resp;
            }
            installStep.setStatus("success");
            steps.add(installStep);

            NodeMediaRemoteDeployRespVO.DeployStep verifyStep = verifyAgentService(ssh, node);
            steps.add(verifyStep);
            boolean ok = "success".equals(verifyStep.getStatus());
            resp.setSuccess(ok);
            resp.setMessage(ok ? "Agent 部署完成，等待心跳上报" : "服务已安装但验证未通过");
            return resp;
        } catch (Exception e) {
            log.error("Agent SSH 部署失败 nodeId={}", nodeId, e);
            NodeMediaRemoteDeployRespVO.DeployStep fail = new NodeMediaRemoteDeployRespVO.DeployStep();
            fail.setName("部署中断");
            fail.setStatus("failed");
            fail.setOutput(e.getMessage());
            steps.add(fail);
            resp.setSuccess(false);
            resp.setMessage(e.getMessage());
            return resp;
        }
    }

    @Override
    public NodePortCheckRespVO checkAgentPortBySsh(Long nodeId) {
        ComputeNodeDO node = validateExists(nodeId);
        NodeSshCredentialDO credential = nodeSshCredentialMapper.selectByNodeId(nodeId);
        if (credential == null) {
            throw exception(SSH_CREDENTIAL_NOT_EXISTS);
        }
        String password = null;
        String privateKey = null;
        if ("password".equals(credential.getAuthType())) {
            password = CredentialEncryptUtil.decrypt(credential.getCredentialEnc());
        } else {
            privateKey = CredentialEncryptUtil.decrypt(credential.getCredentialEnc());
        }

        NodePortCheckRespVO resp = new NodePortCheckRespVO();
        List<NodeMediaRemoteDeployRespVO.DeployStep> steps = new ArrayList<>();
        resp.setSteps(steps);

        int sshPort = resolveSshPort(node);
        try (SshSessionHelper ssh = SshSessionHelper.connect(
                node.getHost(),
                sshPort,
                credential.getUsername(),
                credential.getAuthType(),
                password,
                privateKey)) {

            steps.add(runDeployStep("SSH 连接", "success", "已连接 " + node.getHost() + ":" + sshPort));
            NodePortCheckRespVO portCheck = checkAgentPortOnSession(ssh, node);
            steps.addAll(portCheck.getSteps());
            resp.setPorts(portCheck.getPorts());
            resp.setPortsReady(portCheck.getPortsReady());
            resp.setSuccess(true);
            resp.setMessage(portCheck.getMessage());
            return resp;
        } catch (Exception e) {
            log.error("Agent 端口检测失败 nodeId={} host={}:{}", nodeId, node.getHost(), sshPort, e);
            NodeMediaRemoteDeployRespVO.DeployStep fail = new NodeMediaRemoteDeployRespVO.DeployStep();
            fail.setName(steps.isEmpty() ? "SSH 连接" : "检测中断");
            fail.setStatus("failed");
            fail.setOutput(e.getMessage());
            steps.add(fail);
            resp.setSuccess(false);
            resp.setPortsReady(false);
            resp.setMessage(e.getMessage());
            return resp;
        }
    }

    private NodePortCheckRespVO checkAgentPortOnSession(SshSessionHelper ssh, ComputeNodeDO node) throws Exception {
        int agentPort = node.getAgentPort() != null && node.getAgentPort() > 0 ? node.getAgentPort() : 9100;
        LinkedHashMap<String, Integer> portMap = new LinkedHashMap<>();
        portMap.put("节点代理", agentPort);
        return RemotePortCheckUtil.checkPorts(ssh, portMap);
    }

    @Override
    public NodeAgentCheckRespVO checkAgentBySsh(Long nodeId, String controlPlaneUrlOverride) {
        ComputeNodeDO node = validateExists(nodeId);
        NodeSshCredentialDO credential = nodeSshCredentialMapper.selectByNodeId(nodeId);
        if (credential == null) {
            throw exception(SSH_CREDENTIAL_NOT_EXISTS);
        }
        String password = null;
        String privateKey = null;
        if ("password".equals(credential.getAuthType())) {
            password = CredentialEncryptUtil.decrypt(credential.getCredentialEnc());
        } else {
            privateKey = CredentialEncryptUtil.decrypt(credential.getCredentialEnc());
        }

        NodeAgentCheckRespVO resp = new NodeAgentCheckRespVO();
        List<NodeMediaRemoteDeployRespVO.DeployStep> steps = new ArrayList<>();
        resp.setSteps(steps);

        int sshPort = resolveSshPort(node);
        try (SshSessionHelper ssh = SshSessionHelper.connect(
                node.getHost(),
                sshPort,
                credential.getUsername(),
                credential.getAuthType(),
                password,
                privateKey)) {

            steps.add(runDeployStep("SSH 连接", "success", "已连接 " + node.getHost() + ":" + sshPort));

            NodeMediaRemoteDeployRespVO.DeployStep dirStep = probeAgentInstallDir(ssh);
            steps.add(dirStep);
            resp.setInstallDirReady("success".equals(dirStep.getStatus()));

            NodeMediaRemoteDeployRespVO.DeployStep serviceStep = probeAgentServiceStatus(ssh);
            steps.add(serviceStep);
            resp.setServiceRunning("success".equals(serviceStep.getStatus()));

            NodeMediaRemoteDeployRespVO.DeployStep healthStep = probeAgentHealth(ssh, node);
            steps.add(healthStep);
            resp.setHealthOk("success".equals(healthStep.getStatus()));

            String expectedControlPlaneUrl = resolveControlPlaneUrl(controlPlaneUrlOverride);
            resp.setExpectedControlPlaneUrl(expectedControlPlaneUrl);
            NodeMediaRemoteDeployRespVO.DeployStep envStep = probeAgentEnvConfig(ssh, node, expectedControlPlaneUrl);
            steps.add(envStep);
            applyEnvProbeResult(resp, envStep);

            NodeMediaRemoteDeployRespVO.DeployStep cpStep = probeControlPlaneReachability(
                    ssh, StrUtil.blankToDefault(resp.getControlPlaneUrl(), expectedControlPlaneUrl));
            steps.add(cpStep);
            resp.setControlPlaneReachable("success".equals(cpStep.getStatus()));

            NodeMediaRemoteDeployRespVO.DeployStep logStep = probeAgentRecentLogs(ssh);
            steps.add(logStep);

            boolean deployed = Boolean.TRUE.equals(resp.getServiceRunning())
                    && Boolean.TRUE.equals(resp.getHealthOk());
            resp.setDeployed(deployed);
            resp.setSuccess(true);
            resp.setMessage(buildAgentCheckMessage(resp, node));
            return resp;
        } catch (Exception e) {
            log.error("Agent SSH 检测失败 nodeId={} host={}:{}", nodeId, node.getHost(), sshPort, e);
            NodeMediaRemoteDeployRespVO.DeployStep fail = new NodeMediaRemoteDeployRespVO.DeployStep();
            fail.setName(steps.isEmpty() ? "SSH 连接" : "检测中断");
            fail.setStatus("failed");
            String detail = e.getMessage() != null ? e.getMessage() : e.getClass().getSimpleName();
            fail.setOutput("连接 " + node.getHost() + ":" + sshPort + " 失败: " + detail);
            steps.add(fail);
            resp.setSuccess(false);
            resp.setDeployed(false);
            resp.setInstallDirReady(false);
            resp.setServiceRunning(false);
            resp.setHealthOk(false);
            resp.setMessage(fail.getOutput());
            return resp;
        }
    }

    @Override
    public NodeMediaRemoteDeployRespVO stopAgentBySsh(Long nodeId) {
        return runAgentRemoteOp(nodeId, "停止 Agent", buildAgentStopScript(), "STOP_OK", "节点代理已停止", "停止 Agent 失败");
    }

    @Override
    public NodeMediaRemoteDeployRespVO removeAgentBySsh(Long nodeId) {
        return runAgentRemoteOp(nodeId, "删除 Agent", buildAgentRemoveScript(), "REMOVE_OK",
                "节点代理已删除", "删除 Agent 失败");
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void setMaintenance(Long id, boolean enabled) {
        ComputeNodeDO node = validateExists(id);
        if (isPlatformNode(node)) {
            throw exception(COMPUTE_NODE_PLATFORM_UPDATE_FORBIDDEN);
        }
        node.setStatus(enabled ? NodeStatusEnum.MAINTENANCE.getStatus() : NodeStatusEnum.OFFLINE.getStatus());
        computeNodeMapper.updateById(node);
    }

    @Override
    public NodeMetricTrendRespVO getMetricTrend(NodeMetricTrendReqVO reqVO) {
        int minutes = reqVO.getMinutes() != null ? reqVO.getMinutes() : 30;
        int maxPoints = reqVO.getMaxPoints() != null ? reqVO.getMaxPoints() : 120;
        LocalDateTime since = LocalDateTime.now().minusMinutes(minutes);

        List<ComputeNodeDO> targetNodes = resolveTrendTargetNodes(reqVO.getNodeIds());
        if (targetNodes.isEmpty()) {
            NodeMetricTrendRespVO empty = new NodeMetricTrendRespVO();
            empty.setSeries(List.of());
            return empty;
        }

        Map<Long, ComputeNodeDO> nodeMap = targetNodes.stream()
                .collect(Collectors.toMap(ComputeNodeDO::getId, n -> n, (a, b) -> a, LinkedHashMap::new));
        List<Long> nodeIds = new ArrayList<>(nodeMap.keySet());
        List<NodeMetricSnapshotDO> snapshots = nodeMetricSnapshotMapper.selectByNodeIdsSince(nodeIds, since);

        Map<Long, List<NodeMetricSnapshotDO>> grouped = snapshots.stream()
                .collect(Collectors.groupingBy(NodeMetricSnapshotDO::getNodeId));

        List<NodeMetricTrendSeriesRespVO> seriesList = new ArrayList<>();
        for (Long nodeId : nodeIds) {
            ComputeNodeDO node = nodeMap.get(nodeId);
            List<NodeMetricSnapshotDO> nodeSnapshots = grouped.getOrDefault(nodeId, List.of());
            List<NodeMetricSnapshotDO> limited = nodeSnapshots.size() > maxPoints
                    ? nodeSnapshots.subList(nodeSnapshots.size() - maxPoints, nodeSnapshots.size())
                    : nodeSnapshots;

            NodeMetricTrendSeriesRespVO series = new NodeMetricTrendSeriesRespVO();
            series.setNodeId(nodeId);
            series.setNodeName(node.getName());
            series.setHost(node.getHost());
            series.setStatus(node.getStatus());
            series.setPoints(limited.stream().map(this::toTrendPoint).collect(Collectors.toList()));
            seriesList.add(series);
        }

        NodeMetricTrendRespVO resp = new NodeMetricTrendRespVO();
        resp.setSeries(seriesList);
        return resp;
    }

    private List<ComputeNodeDO> resolveTrendTargetNodes(List<Long> nodeIds) {
        if (nodeIds != null && !nodeIds.isEmpty()) {
            return nodeIds.stream()
                    .map(computeNodeMapper::selectById)
                    .filter(Objects::nonNull)
                    .filter(this::isTrendEligibleNode)
                    .sorted(Comparator.comparing(ComputeNodeDO::getName, Comparator.nullsLast(String::compareTo)))
                    .collect(Collectors.toList());
        }
        return computeNodeMapper.selectList(new LambdaQueryWrapperX<ComputeNodeDO>()
                        .in(ComputeNodeDO::getNodeRole,
                                NodeRoleEnum.COMPUTE.getRole(), NodeRoleEnum.HYBRID.getRole())
                        .orderByAsc(ComputeNodeDO::getName))
                .stream()
                .filter(this::isTrendEligibleNode)
                .collect(Collectors.toList());
    }

    private boolean isTrendEligibleNode(ComputeNodeDO node) {
        String role = node.getNodeRole();
        return NodeRoleEnum.COMPUTE.getRole().equals(role) || NodeRoleEnum.HYBRID.getRole().equals(role);
    }

    private NodeMetricTrendPointRespVO toTrendPoint(NodeMetricSnapshotDO snapshot) {
        NodeMetricTrendPointRespVO point = new NodeMetricTrendPointRespVO();
        point.setCollectedAt(snapshot.getCollectedAt());
        point.setCpuPercent(snapshot.getCpuPercent());
        point.setMemPercent(snapshot.getMemPercent());
        point.setDiskPercent(snapshot.getDiskPercent());
        point.setActiveTasks(snapshot.getActiveTasks());
        point.setMemUsedBytes(snapshot.getMemUsedBytes());
        point.setDiskUsedBytes(snapshot.getDiskUsedBytes());
        point.setGpuMemUsedBytes(calcGpuMemUsedBytes(snapshot.getGpuInfo()));
        point.setGpuMemPercent(calcAvgGpuMemPercent(snapshot.getGpuInfo()));
        point.setGpuUtilPercent(calcAvgGpuUtil(snapshot.getGpuInfo()));
        return point;
    }

    private Long calcGpuMemUsedBytes(List<Map<String, Object>> gpuInfo) {
        if (gpuInfo == null || gpuInfo.isEmpty()) {
            return 0L;
        }
        long sum = 0;
        for (Map<String, Object> gpu : gpuInfo) {
            sum += Math.round(toDouble(gpu.get("mem_used_mb")) * 1024 * 1024);
        }
        return sum;
    }

    private BigDecimal calcAvgGpuMemPercent(List<Map<String, Object>> gpuInfo) {
        if (gpuInfo == null || gpuInfo.isEmpty()) {
            return BigDecimal.ZERO;
        }
        double sum = 0;
        int count = 0;
        for (Map<String, Object> gpu : gpuInfo) {
            double total = toDouble(gpu.get("mem_total_mb"));
            if (total <= 0) {
                continue;
            }
            sum += toDouble(gpu.get("mem_used_mb")) / total * 100;
            count++;
        }
        return count > 0 ? scalePercent(sum / count) : BigDecimal.ZERO;
    }

    private BigDecimal calcAvgGpuUtil(List<Map<String, Object>> gpuInfo) {
        if (gpuInfo == null || gpuInfo.isEmpty()) {
            return BigDecimal.ZERO;
        }
        double sum = 0;
        int count = 0;
        for (Map<String, Object> gpu : gpuInfo) {
            sum += toDouble(gpu.get("util"));
            count++;
        }
        return count > 0 ? scalePercent(sum / count) : BigDecimal.ZERO;
    }

    private double toDouble(Object value) {
        if (value == null) {
            return 0;
        }
        if (value instanceof Number) {
            return ((Number) value).doubleValue();
        }
        try {
            return Double.parseDouble(String.valueOf(value));
        } catch (NumberFormatException ignored) {
            return 0;
        }
    }

    private BigDecimal scalePercent(double value) {
        return BigDecimal.valueOf(value).setScale(1, RoundingMode.HALF_UP);
    }

    private NodeMediaRemoteDeployRespVO runAgentRemoteOp(Long nodeId, String stepName, String remoteScript,
                                                         String okMarker, String successMessage, String failMessage) {
        ComputeNodeDO node = validateExists(nodeId);
        NodeSshCredentialDO credential = nodeSshCredentialMapper.selectByNodeId(nodeId);
        if (credential == null) {
            throw exception(SSH_CREDENTIAL_NOT_EXISTS);
        }
        String password = null;
        String privateKey = null;
        if ("password".equals(credential.getAuthType())) {
            password = CredentialEncryptUtil.decrypt(credential.getCredentialEnc());
        } else {
            privateKey = CredentialEncryptUtil.decrypt(credential.getCredentialEnc());
        }

        NodeMediaRemoteDeployRespVO resp = new NodeMediaRemoteDeployRespVO();
        List<NodeMediaRemoteDeployRespVO.DeployStep> steps = new ArrayList<>();
        resp.setSteps(steps);

        int sshPort = resolveSshPort(node);
        try (SshSessionHelper ssh = SshSessionHelper.connect(
                node.getHost(),
                sshPort,
                credential.getUsername(),
                credential.getAuthType(),
                password,
                privateKey)) {

            steps.add(runDeployStep("SSH 连接", "success", "已连接 " + node.getHost() + ":" + sshPort));

            String encoded = Base64.getEncoder().encodeToString(remoteScript.getBytes(StandardCharsets.UTF_8));
            SshSessionHelper.SshExecResult result = ssh.exec(
                    "echo " + encoded + " | base64 -d | sudo bash -s",
                    120000);
            NodeMediaRemoteDeployRespVO.DeployStep step = new NodeMediaRemoteDeployRespVO.DeployStep();
            step.setName(stepName);
            step.setOutput(trimDeployOutput(result.combinedOutput(), 6000));
            boolean ok = result.isSuccess() && result.combinedOutput().contains(okMarker);
            step.setStatus(ok ? "success" : "failed");
            steps.add(step);
            resp.setSuccess(ok);
            resp.setMessage(ok ? successMessage : failMessage);
            return resp;
        } catch (Exception e) {
            log.error("Agent SSH 运维失败 nodeId={} op={}", nodeId, stepName, e);
            NodeMediaRemoteDeployRespVO.DeployStep fail = new NodeMediaRemoteDeployRespVO.DeployStep();
            fail.setName(steps.isEmpty() ? "SSH 连接" : stepName);
            fail.setStatus("failed");
            String detail = e.getMessage() != null ? e.getMessage() : e.getClass().getSimpleName();
            fail.setOutput("连接 " + node.getHost() + ":" + sshPort + " 失败: " + detail);
            steps.add(fail);
            resp.setSuccess(false);
            resp.setMessage(fail.getOutput());
            return resp;
        }
    }

    private String buildAgentStopScript() {
        return "#!/usr/bin/env bash\n"
                + "set -euo pipefail\n"
                + "if systemctl list-unit-files easyaiot-node-agent.service >/dev/null 2>&1; then\n"
                + "  echo '>>> 停止 easyaiot-node-agent'\n"
                + "  systemctl stop easyaiot-node-agent 2>&1 || true\n"
                + "  echo '[OK] 服务已停止'\n"
                + "else\n"
                + "  echo '[SKIP] 服务未注册'\n"
                + "fi\n"
                + "echo STOP_OK\n";
    }

    private String buildAgentRemoveScript() {
        String dir = AgentDeployUtil.REMOTE_INSTALL_DIR;
        return "#!/usr/bin/env bash\n"
                + "set -euo pipefail\n"
                + "if systemctl list-unit-files easyaiot-node-agent.service >/dev/null 2>&1; then\n"
                + "  echo '>>> 停止并禁用 easyaiot-node-agent'\n"
                + "  systemctl stop easyaiot-node-agent 2>&1 || true\n"
                + "  systemctl disable easyaiot-node-agent 2>&1 || true\n"
                + "fi\n"
                + "if [[ -f /etc/systemd/system/easyaiot-node-agent.service ]]; then\n"
                + "  echo '>>> 删除 systemd 单元文件'\n"
                + "  rm -f /etc/systemd/system/easyaiot-node-agent.service\n"
                + "  systemctl daemon-reload\n"
                + "  echo '[OK] systemd 单元已移除'\n"
                + "else\n"
                + "  echo '[SKIP] systemd 单元不存在'\n"
                + "fi\n"
                + "if [[ -d '" + dir + "' ]]; then\n"
                + "  echo '>>> 删除安装目录 " + dir + "'\n"
                + "  rm -rf '" + dir + "'\n"
                + "  echo '[OK] 安装目录已删除'\n"
                + "else\n"
                + "  echo '[SKIP] 安装目录不存在'\n"
                + "fi\n"
                + "echo REMOVE_OK\n";
    }

    private void saveSshCredential(Long nodeId, ComputeNodeSaveReqVO reqVO) {
        if (StrUtil.isBlank(reqVO.getSshUsername())) {
            return;
        }
        String secret = "password".equals(reqVO.getSshAuthType()) ? reqVO.getSshPassword() : reqVO.getSshPrivateKey();
        if (StrUtil.isBlank(secret)) {
            return;
        }
        NodeSshCredentialDO credential = nodeSshCredentialMapper.selectByNodeId(nodeId);
        if (credential == null) {
            credential = new NodeSshCredentialDO();
            credential.setNodeId(nodeId);
        }
        credential.setUsername(reqVO.getSshUsername());
        credential.setAuthType(StrUtil.blankToDefault(reqVO.getSshAuthType(), "password"));
        credential.setCredentialEnc(CredentialEncryptUtil.encrypt(secret));
        if (credential.getId() == null) {
            nodeSshCredentialMapper.insert(credential);
        } else {
            nodeSshCredentialMapper.updateById(credential);
        }
    }

    private ComputeNodeDO validateExists(Long id) {
        ComputeNodeDO node = computeNodeMapper.selectById(id);
        if (node == null) {
            throw exception(COMPUTE_NODE_NOT_EXISTS);
        }
        return node;
    }

    private ComputeNodeRespVO toRespVO(ComputeNodeDO node, boolean exposeToken) {
        ComputeNodeRespVO resp = BeanUtils.toBean(node, ComputeNodeRespVO.class);
        resp.setIsPlatform(isPlatformNode(node));
        if (exposeToken) {
            resp.setAgentToken(node.getAgentToken());
        }
        NodeSshCredentialDO credential = nodeSshCredentialMapper.selectByNodeId(node.getId());
        if (credential != null) {
            resp.setSshUsername(credential.getUsername());
            resp.setSshAuthType(credential.getAuthType());
            resp.setSshCredentialConfigured(true);
            resp.setSshLastTestAt(credential.getLastTestAt());
            resp.setSshLastTestOk(credential.getLastTestOk());
        } else {
            resp.setSshCredentialConfigured(false);
        }
        NodeMetricSnapshotDO metric = nodeMetricSnapshotMapper.selectLatestByNodeId(node.getId());
        if (metric != null) {
            resp.setCpuPercent(metric.getCpuPercent());
            resp.setMemPercent(metric.getMemPercent());
            resp.setMemUsedBytes(metric.getMemUsedBytes());
            resp.setMemTotalBytes(metric.getMemTotalBytes());
            resp.setDiskPercent(metric.getDiskPercent());
            resp.setDiskUsedBytes(metric.getDiskUsedBytes());
            resp.setDiskTotalBytes(metric.getDiskTotalBytes());
            resp.setActiveTasks(metric.getActiveTasks());
            try {
                resp.setGpuInfo(metric.getGpuInfo() != null ? objectMapper.writeValueAsString(metric.getGpuInfo()) : null);
            } catch (Exception ignored) {
                resp.setGpuInfo(null);
            }
        }
        return resp;
    }

    private int defaultPort(Integer port, int defaultValue) {
        return port != null && port > 0 ? port : defaultValue;
    }

    static int resolveSshPort(ComputeNodeDO node) {
        return node.getSshPort() != null && node.getSshPort() > 0 ? node.getSshPort() : DEFAULT_SSH_PORT;
    }

    static boolean isPlatformNode(ComputeNodeDO node) {
        return node != null
                && node.getCapabilities() != null
                && Boolean.TRUE.equals(node.getCapabilities().get(PLATFORM_CAPABILITY_KEY));
    }

    private Comparator<ComputeNodeRespVO> platformNodeFirstComparator() {
        return Comparator.comparing((ComputeNodeRespVO node) -> !Boolean.TRUE.equals(node.getIsPlatform()));
    }

    /** 将角色默认能力合并进已有 map，返回是否有变更（用于升级历史节点能力字段）。 */
    private boolean mergeDefaultCapabilities(Map<String, Boolean> caps, String nodeRole) {
        Map<String, Boolean> defaults = defaultCapabilities(nodeRole);
        boolean changed = false;
        for (Map.Entry<String, Boolean> entry : defaults.entrySet()) {
            if (Boolean.TRUE.equals(entry.getValue()) && !Boolean.TRUE.equals(caps.get(entry.getKey()))) {
                caps.put(entry.getKey(), true);
                changed = true;
            }
        }
        return changed;
    }

    private Map<String, Boolean> defaultCapabilities(String nodeRole) {
        Map<String, Boolean> caps = new HashMap<>();
        if (NodeRoleEnum.COMPUTE.getRole().equals(nodeRole)
                || NodeRoleEnum.GPU.getRole().equals(nodeRole)
                || NodeRoleEnum.HYBRID.getRole().equals(nodeRole)) {
            caps.put("ai_inference", true);
            caps.put("algorithm_realtime", true);
            caps.put("algorithm_snap", true);
            caps.put("algorithm_patrol", true);
            caps.put("stream_forward", true);
            caps.put("auto_label", true);
            caps.put("model_train", true);
        }
        if (NodeRoleEnum.GPU.getRole().equals(nodeRole)
                || NodeRoleEnum.HYBRID.getRole().equals(nodeRole)) {
            caps.put("llm_inference", true);
        }
        if (NodeRoleEnum.MEDIA.getRole().equals(nodeRole) || NodeRoleEnum.HYBRID.getRole().equals(nodeRole)) {
            caps.put("srs_live", true);
            caps.put("srs_ai", true);
            caps.put("zlm", true);
        }
        if (NodeRoleEnum.STORAGE.getRole().equals(nodeRole)) {
            caps.put("ceph_osd", true);
            caps.put("media_storage", true);
        }
        if (NodeRoleEnum.MQTT.getRole().equals(nodeRole)) {
            caps.put("emqx", true);
            caps.put("mqtt_gateway", true);
        }
        return caps;
    }

    /**
     * 按节点角色规范化 GPU 数量：计算节点无 GPU，GPU 节点至少 1 张。
     */
    private void applyRoleGpuDefaults(ComputeNodeDO node, Integer requestedMaxGpuCount) {
        String role = node.getNodeRole();
        if (NodeRoleEnum.COMPUTE.getRole().equals(role)
                || NodeRoleEnum.STORAGE.getRole().equals(role)
                || NodeRoleEnum.MQTT.getRole().equals(role)) {
            node.setMaxGpuCount(0);
            return;
        }
        if (NodeRoleEnum.GPU.getRole().equals(role)) {
            int count = requestedMaxGpuCount != null && requestedMaxGpuCount > 0 ? requestedMaxGpuCount : 1;
            node.setMaxGpuCount(count);
            return;
        }
        node.setMaxGpuCount(requestedMaxGpuCount != null ? requestedMaxGpuCount : 0);
    }

    private String resolveControlPlaneUrl(String override) {
        return controlPlaneEndpointResolver.resolveControlPlaneUrl(override);
    }

    private String resolveAgentSource() {
        for (String path : listAgentSourceCandidates()) {
            File entry = new File(path, "run_agent.py");
            if (entry.isFile()) {
                return new File(path).getAbsolutePath();
            }
        }
        throw exception(AGENT_SOURCE_NOT_FOUND);
    }

    /**
     * Agent 源码候选目录（优先完整 repo/NODE，最后才是 /opt/easyaiot/node-agent 运行时目录）。
     */
    private List<String> listAgentSourceCandidates() {
        LinkedHashMap<String, Boolean> ordered = new LinkedHashMap<>();
        if (agentSourcePath != null && !agentSourcePath.isBlank()) {
            ordered.put(agentSourcePath.trim(), Boolean.TRUE);
        }
        ordered.put("/opt/easyaiot/NODE", Boolean.TRUE);
        String userDir = System.getProperty("user.dir");
        if (userDir != null && !userDir.isBlank()) {
            ordered.put(userDir + "/NODE", Boolean.TRUE);
            ordered.put(userDir + "/../NODE", Boolean.TRUE);
            ordered.put(userDir + "/../../NODE", Boolean.TRUE);
        }
        ordered.put("/opt/easyaiot/node-agent", Boolean.TRUE);
        return new ArrayList<>(ordered.keySet());
    }

    private File resolveAgentExportScript() {
        for (String path : listAgentSourceCandidates()) {
            File script = new File(path, AgentDeployUtil.EXPORT_PIP_WHEELS_SCRIPT);
            if (script.isFile()) {
                return script;
            }
        }
        return null;
    }

    private AgentPipBundle resolveAgentPipBundle(String targetPython) {
        for (String path : listAgentSourceCandidates()) {
            if (isAgentPipWheelsReady(path, targetPython)) {
                File wheelsDir = new File(path, AgentDeployUtil.PIP_WHEELS_DIR);
                File getPip = new File(path, AgentDeployUtil.GET_PIP_SCRIPT);
                return new AgentPipBundle(path, wheelsDir, getPip);
            }
        }
        File exportScript = resolveAgentExportScript();
        if (exportScript == null) {
            return new AgentPipBundle(null, null, null);
        }
        String bundleRoot = exportScript.getParentFile().getAbsolutePath();
        File getPip = new File(bundleRoot, AgentDeployUtil.GET_PIP_SCRIPT);
        File cacheDir = new File(System.getProperty("java.io.tmpdir"),
                "easyaiot-agent-pip-wheels/" + targetPython.replace('.', '_'));
        if (isAgentPipWheelsReady(bundleRoot, targetPython, cacheDir)) {
            return new AgentPipBundle(bundleRoot, cacheDir, getPip);
        }
        File wheelsDir = resolveWritablePipWheelsDir(exportScript.getParentFile(), targetPython);
        return new AgentPipBundle(bundleRoot, wheelsDir, getPip);
    }

    private File resolveWritablePipWheelsDir(File bundleRoot, String targetPython) {
        File defaultDir = new File(bundleRoot, AgentDeployUtil.PIP_WHEELS_DIR);
        if (isDirectoryWritable(defaultDir)) {
            return defaultDir;
        }
        File cacheDir = new File(System.getProperty("java.io.tmpdir"),
                "easyaiot-agent-pip-wheels/" + targetPython.replace('.', '_'));
        if (!cacheDir.exists() && !cacheDir.mkdirs()) {
            log.warn("无法创建 Agent pip 缓存目录: {}", cacheDir.getAbsolutePath());
        }
        return cacheDir;
    }

    private boolean isDirectoryWritable(File dir) {
        try {
            if (!dir.exists() && !dir.mkdirs()) {
                return false;
            }
            if (!dir.isDirectory()) {
                return false;
            }
            File probe = new File(dir, ".write-probe-" + System.currentTimeMillis());
            if (!probe.createNewFile()) {
                return false;
            }
            return probe.delete();
        } catch (Exception e) {
            return false;
        }
    }

    private static final class AgentPipBundle {
        private final String bundleRoot;
        private File wheelsDir;
        private File getPipScript;

        private AgentPipBundle(String bundleRoot, File wheelsDir, File getPipScript) {
            this.bundleRoot = bundleRoot;
            this.wheelsDir = wheelsDir;
            this.getPipScript = getPipScript;
        }
    }

    private NodeMediaRemoteDeployRespVO.DeployStep syncAgentFiles(
            SshSessionHelper ssh, String sourceRoot, AgentPipBundle pipBundle) throws Exception {
        ssh.ensureRemoteDir(AgentDeployUtil.REMOTE_INSTALL_DIR);
        int count = 0;
        for (String relative : AgentDeployUtil.SYNC_RELATIVE_FILES) {
            File local = new File(sourceRoot, relative);
            if (!local.isFile()) {
                throw exception(AGENT_SOURCE_NOT_FOUND);
            }
            ssh.uploadFile(local.getAbsolutePath(), AgentDeployUtil.REMOTE_INSTALL_DIR + "/" + relative);
            if (relative.endsWith(".sh")) {
                ssh.exec("chmod +x " + AgentDeployUtil.REMOTE_INSTALL_DIR + "/" + relative, 10000);
            }
            count++;
        }

        File getPip = pipBundle.getPipScript;
        if (getPip == null || !getPip.isFile()) {
            NodeMediaRemoteDeployRespVO.DeployStep fail = new NodeMediaRemoteDeployRespVO.DeployStep();
            fail.setName("同步文件");
            fail.setStatus("failed");
            fail.setOutput("本机缺少 " + AgentDeployUtil.GET_PIP_SCRIPT
                    + "，请重新执行 export_pip_wheels.sh 生成完整离线包后重试");
            return fail;
        }
        ssh.uploadFile(getPip.getAbsolutePath(),
                AgentDeployUtil.REMOTE_INSTALL_DIR + "/" + AgentDeployUtil.GET_PIP_SCRIPT);
        count++;

        File wheelsDir = pipBundle.wheelsDir;
        File[] wheels = listPipWheelFiles(wheelsDir);
        if (wheels.length == 0) {
            NodeMediaRemoteDeployRespVO.DeployStep fail = new NodeMediaRemoteDeployRespVO.DeployStep();
            fail.setName("同步文件");
            fail.setStatus("failed");
            fail.setOutput("本机缺少离线 pip 包，请执行 NODE/export_pip_wheels.sh 后重试");
            return fail;
        }

        String remoteWheelsDir = AgentDeployUtil.REMOTE_INSTALL_DIR + "/" + AgentDeployUtil.PIP_WHEELS_DIR;
        ssh.ensureRemoteDir(remoteWheelsDir);
        long wheelBytes = 0;
        for (File wheel : wheels) {
            ssh.uploadFile(wheel.getAbsolutePath(), remoteWheelsDir + "/" + wheel.getName());
            wheelBytes += wheel.length();
        }

        NodeMediaRemoteDeployRespVO.DeployStep step = new NodeMediaRemoteDeployRespVO.DeployStep();
        step.setName("同步文件");
        step.setStatus("success");
        String wheelsNote = pipBundle.bundleRoot != null && wheelsDir != null
                && !wheelsDir.getAbsolutePath().startsWith(new File(pipBundle.bundleRoot).getAbsolutePath())
                ? "\n离线包目录: " + wheelsDir.getAbsolutePath()
                : "";
        step.setOutput("已上传 " + count + " 个文件 + " + wheels.length + " 个离线 pip 包（"
                + formatDeployBytes(wheelBytes) + "）至 " + AgentDeployUtil.REMOTE_INSTALL_DIR + wheelsNote);
        return step;
    }

    private NodeMediaRemoteDeployRespVO.DeployStep ensureLocalAgentPipWheels(
            AgentPipBundle pipBundle, String targetPython) {
        if (pipBundle.wheelsDir != null) {
            File[] existing = listPipWheelFiles(pipBundle.wheelsDir);
            if (existing.length > 0 && pipBundle.bundleRoot != null
                    && isAgentPipWheelsReady(pipBundle.bundleRoot, targetPython, pipBundle.wheelsDir)) {
                long total = 0;
                for (File wheel : existing) {
                    total += wheel.length();
                }
                return runDeployStep("准备离线 pip 包", "success",
                        "本机离线 pip 包已就绪（" + existing.length + " 个，"
                                + formatDeployBytes(total) + "，目标 Python " + targetPython + "）\n目录: "
                                + pipBundle.wheelsDir.getAbsolutePath());
            }
        }

        File exportScript = resolveAgentExportScript();
        if (exportScript == null) {
            return runDeployStep("准备离线 pip 包", "failed",
                    "缺少离线 pip 包且未找到 export_pip_wheels.sh；"
                            + "请配置 EASYAIOT_AGENT_SOURCE_PATH 指向含 NODE 源码的目录，"
                            + "或在平台执行: bash NODE/export_pip_wheels.sh");
        }

        File wheelsDir = pipBundle.wheelsDir != null
                ? pipBundle.wheelsDir
                : resolveWritablePipWheelsDir(exportScript.getParentFile(), targetPython);

        try {
            String exportOutput = runExportPipWheelsScript(exportScript, targetPython, wheelsDir);
            File[] wheels = listPipWheelFiles(wheelsDir);
            if (wheels.length == 0) {
                return runDeployStep("准备离线 pip 包", "failed",
                        "export_pip_wheels.sh 执行后仍未生成 wheel 包\n"
                                + trimDeployOutput(exportOutput, 4000));
            }
            long total = 0;
            for (File wheel : wheels) {
                total += wheel.length();
            }
            String output = "本机已下载离线 pip 包（" + wheels.length + " 个，"
                    + formatDeployBytes(total) + "，目标 Python " + targetPython + "）\n目录: "
                    + wheelsDir.getAbsolutePath();
            if (!exportOutput.isBlank()) {
                output += "\n" + trimDeployOutput(exportOutput, 3000);
            }
            pipBundle.wheelsDir = wheelsDir;
            if (pipBundle.getPipScript == null || !pipBundle.getPipScript.isFile()) {
                pipBundle.getPipScript = new File(exportScript.getParentFile(), AgentDeployUtil.GET_PIP_SCRIPT);
            }
            return runDeployStep("准备离线 pip 包", "success", output);
        } catch (Exception e) {
            log.error("本机导出 Agent pip wheel 失败 wheelsDir={}", wheelsDir.getAbsolutePath(), e);
            return runDeployStep("准备离线 pip 包", "failed",
                    "本机下载 pip 包失败: " + e.getMessage()
                            + "\n请确认平台服务器已安装 pip，或设置 PYTHON 指向带 pip 的解释器");
        }
    }

    private boolean isAgentPipWheelsReady(String bundleRoot, String targetPython) {
        return isAgentPipWheelsReady(bundleRoot, targetPython, new File(bundleRoot, AgentDeployUtil.PIP_WHEELS_DIR));
    }

    private boolean isAgentPipWheelsReady(String bundleRoot, String targetPython, File wheelsDir) {
        File[] wheels = listPipWheelFiles(wheelsDir);
        if (wheels.length == 0) {
            return false;
        }
        File marker = new File(wheelsDir, ".target-python");
        if (!marker.isFile()) {
            return false;
        }
        try {
            String markerVersion = Files.readString(marker.toPath(), StandardCharsets.UTF_8).trim();
            if (!markerVersion.equals(targetPython)) {
                return false;
            }
        } catch (Exception e) {
            return false;
        }
        if (!hasAgentBootstrapWheel(wheelsDir, "pip")
                || !hasAgentBootstrapWheel(wheelsDir, "setuptools")
                || !hasAgentBootstrapWheel(wheelsDir, "wheel")) {
            return false;
        }
        if (!new File(bundleRoot, AgentDeployUtil.GET_PIP_SCRIPT).isFile()) {
            return false;
        }
        if (isPythonVersionBelow(targetPython, "3.10")) {
            return hasAgentBootstrapWheel(wheelsDir, "importlib_metadata")
                    && hasAgentBootstrapWheel(wheelsDir, "zipp");
        }
        return hasAgentBootstrapWheel(wheelsDir, "requests")
                && hasAgentBootstrapWheel(wheelsDir, "psutil")
                && hasAgentBootstrapWheel(wheelsDir, "flask")
                && hasAgentBootstrapWheel(wheelsDir, "minio");
    }

    private boolean hasAgentBootstrapWheel(File wheelsDir, String prefix) {
        String lowerPrefix = prefix.toLowerCase(Locale.ROOT);
        File[] wheels = listPipWheelFiles(wheelsDir);
        for (File wheel : wheels) {
            if (wheel.getName().toLowerCase(Locale.ROOT).startsWith(lowerPrefix)) {
                return true;
            }
        }
        return false;
    }

    private boolean isPythonVersionBelow(String version, String threshold) {
        int[] current = parsePythonVersion(version);
        int[] baseline = parsePythonVersion(threshold);
        if (current == null || baseline == null) {
            return false;
        }
        if (current[0] != baseline[0]) {
            return current[0] < baseline[0];
        }
        return current[1] < baseline[1];
    }

    private int[] parsePythonVersion(String version) {
        if (version == null || !version.matches("3\\.\\d+")) {
            return null;
        }
        String[] parts = version.split("\\.");
        return new int[]{Integer.parseInt(parts[0]), Integer.parseInt(parts[1])};
    }

    private File[] listPipWheelFiles(File wheelsDir) {
        if (!wheelsDir.isDirectory()) {
            return new File[0];
        }
        File[] files = wheelsDir.listFiles(f -> f.isFile() && isPipWheelArtifact(f.getName()));
        return files != null ? files : new File[0];
    }

    private boolean isPipWheelArtifact(String name) {
        String lower = name.toLowerCase(Locale.ROOT);
        return lower.endsWith(".whl") || lower.endsWith(".tar.gz") || lower.endsWith(".zip");
    }

    private String detectRemotePythonVersion(SshSessionHelper ssh) throws Exception {
        SshSessionHelper.SshExecResult result = ssh.exec(
                "python3 -c \"import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')\" 2>/dev/null || echo 3.10",
                10000);
        String version = result.combinedOutput().trim();
        if (!version.matches("3\\.\\d+")) {
            return "3.10";
        }
        return version;
    }

    private NodeMediaRemoteDeployRespVO.DeployStep ensureRemotePythonRuntime(SshSessionHelper ssh, String targetPython)
            throws Exception {
        SshSessionHelper.SshExecResult result = ssh.exec(
                "if command -v python3 >/dev/null 2>&1 "
                        + "&& python3 -c \"import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')\" "
                        + "2>/dev/null | grep -qx '" + targetPython + "'; then "
                        + "echo PYTHON_OK; "
                        + "else echo PYTHON_MISMATCH; fi",
                15000);
        String out = result.combinedOutput();
        if (out.contains("PYTHON_OK")) {
            return runDeployStep("Python 运行时", "success",
                    "目标机 Python " + targetPython + " 可用；"
                            + "将同步离线 wheel + get-pip.py，在 prefix 目录隔离安装（无需联网 apt / python-venv）");
        }
        if (out.contains("PYTHON_MISMATCH")) {
            return runDeployStep("Python 运行时", "failed",
                    "目标机 Python 版本与预期 " + targetPython + " 不一致。\n"
                            + trimDeployOutput(out, 800)
                            + "\n请确认目标机已安装 python" + targetPython);
        }
        return runDeployStep("Python 运行时", "failed",
                "目标机未找到 python3。\n" + trimDeployOutput(out, 800));
    }

    private String runExportPipWheelsScript(File exportScript, String targetPython, File wheelsDir)
            throws Exception {
        ProcessBuilder pb = new ProcessBuilder("bash", exportScript.getAbsolutePath());
        pb.directory(exportScript.getParentFile());
        pb.environment().put("AGENT_TARGET_PYTHON", targetPython);
        if (wheelsDir != null) {
            pb.environment().put("AGENT_PIP_WHEELS_DIR", wheelsDir.getAbsolutePath());
        }
        pb.redirectErrorStream(true);
        Process process = pb.start();
        String output;
        try (InputStream in = process.getInputStream()) {
            output = new String(in.readAllBytes(), StandardCharsets.UTF_8);
        }
        boolean finished = process.waitFor(EXPORT_PIP_WHEELS_TIMEOUT_MS, TimeUnit.MILLISECONDS);
        if (!finished) {
            process.destroyForcibly();
            throw new IllegalStateException("export_pip_wheels.sh 超时（超过 "
                    + (EXPORT_PIP_WHEELS_TIMEOUT_MS / 60000) + " 分钟）");
        }
        if (process.exitValue() != 0) {
            throw new IllegalStateException(output.isBlank()
                    ? "export_pip_wheels.sh 退出码 " + process.exitValue()
                    : output.trim());
        }
        return output;
    }

    private String formatDeployBytes(long bytes) {
        if (bytes < 1024) {
            return bytes + " B";
        }
        if (bytes < 1024L * 1024) {
            return String.format(Locale.ROOT, "%.1f KB", bytes / 1024.0);
        }
        return String.format(Locale.ROOT, "%.1f MB", bytes / (1024.0 * 1024.0));
    }

    private NodeMediaRemoteDeployRespVO.DeployStep probeAgentInstallDir(SshSessionHelper ssh) throws Exception {
        String dir = AgentDeployUtil.REMOTE_INSTALL_DIR;
        SshSessionHelper.SshExecResult result = ssh.exec(
                "if [ -d '" + dir + "' ] && [ -f '" + dir + "/run_agent.py' ]; then echo DIR_OK; "
                        + "ls -la '" + dir + "' 2>/dev/null | head -5; "
                        + "elif [ -d '" + dir + "' ]; then echo DIR_PARTIAL; "
                        + "else echo DIR_MISSING; fi",
                15000);
        String out = result.combinedOutput();
        NodeMediaRemoteDeployRespVO.DeployStep step = new NodeMediaRemoteDeployRespVO.DeployStep();
        step.setName("安装目录");
        step.setOutput(trimDeployOutput(out, 2000));
        if (out.contains("DIR_OK")) {
            step.setStatus("success");
            return step;
        }
        if (out.contains("DIR_PARTIAL")) {
            step.setStatus("failed");
            step.setOutput("目录 " + dir + " 存在但缺少 run_agent.py，可能安装不完整");
            return step;
        }
        step.setStatus("failed");
        step.setOutput("未找到安装目录 " + dir);
        return step;
    }

    private NodeMediaRemoteDeployRespVO.DeployStep probeAgentServiceStatus(SshSessionHelper ssh) throws Exception {
        SshSessionHelper.SshExecResult result = ssh.exec(
                "if systemctl is-active easyaiot-node-agent >/dev/null 2>&1; then echo SERVICE_ACTIVE; "
                        + "systemctl status easyaiot-node-agent --no-pager -l 2>/dev/null | head -3; "
                        + "elif systemctl list-unit-files easyaiot-node-agent.service >/dev/null 2>&1; then echo SERVICE_INACTIVE; "
                        + "else echo SERVICE_MISSING; fi",
                15000);
        String out = result.combinedOutput();
        NodeMediaRemoteDeployRespVO.DeployStep step = new NodeMediaRemoteDeployRespVO.DeployStep();
        step.setName("systemd 服务");
        step.setOutput(trimDeployOutput(out, 2000));
        if (out.contains("SERVICE_ACTIVE")) {
            step.setStatus("success");
            return step;
        }
        if (out.contains("SERVICE_INACTIVE")) {
            step.setStatus("failed");
            step.setOutput("已注册 easyaiot-node-agent 服务但未运行");
            return step;
        }
        step.setStatus("failed");
        step.setOutput("未注册 easyaiot-node-agent 服务");
        return step;
    }

    private NodeMediaRemoteDeployRespVO.DeployStep probeAgentHealth(SshSessionHelper ssh, ComputeNodeDO node)
            throws Exception {
        int agentPort = node.getAgentPort() != null && node.getAgentPort() > 0
                ? node.getAgentPort() : DEFAULT_AGENT_PORT;
        SshSessionHelper.SshExecResult result = ssh.exec(buildAgentHealthProbeScript(agentPort), 30000);
        String out = result.combinedOutput();
        NodeMediaRemoteDeployRespVO.DeployStep step = new NodeMediaRemoteDeployRespVO.DeployStep();
        step.setName("健康检查");
        if (out.contains("HEALTH_OK")) {
            step.setStatus("success");
            step.setOutput("http://127.0.0.1:" + agentPort + "/health 响应正常");
            return step;
        }
        step.setStatus("failed");
        StringBuilder output = new StringBuilder("http://127.0.0.1:" + agentPort + "/health 无响应");
        if (out.contains("PORT_MISMATCH=1")) {
            output.append("\nagent.env 中 AGENT_LISTEN_PORT 与平台节点代理端口不一致，请重新部署以同步配置");
        } else if (out.contains("HEALTH_OK_ON_CONFIGURED_PORT=1")) {
            output.append("\nAgent 在 agent.env 配置的端口有响应，但与平台登记端口不一致，请重新部署");
        } else if (out.contains("CURL_MISSING=1")) {
            output.append("\n目标机未安装 curl/wget，无法执行 HTTP 探测");
        } else {
            output.append("\n服务可能刚启动或进程异常，可查看 Agent 日志后重试");
        }
        String diag = trimDeployOutput(out, 1500);
        if (!diag.isBlank()) {
            output.append('\n').append(diag);
        }
        step.setOutput(output.toString());
        return step;
    }

    private String buildAgentHealthProbeScript(int agentPort) {
        String envFile = AgentDeployUtil.REMOTE_INSTALL_DIR + "/agent.env";
        return "AGENT_PORT=" + agentPort + "\n"
                + "ENV_FILE='" + envFile + "'\n"
                + "probe_health() {\n"
                + "  local port=\"$1\"\n"
                + "  if command -v curl >/dev/null 2>&1; then\n"
                + "    curl -sf \"http://127.0.0.1:${port}/health\" >/dev/null 2>&1\n"
                + "    return $?\n"
                + "  fi\n"
                + "  if command -v wget >/dev/null 2>&1; then\n"
                + "    wget -q -O /dev/null \"http://127.0.0.1:${port}/health\" 2>/dev/null\n"
                + "    return $?\n"
                + "  fi\n"
                + "  python3 -c \"import urllib.request; urllib.request.urlopen('http://127.0.0.1:'+str(${port})+'/health', timeout=3)\" 2>/dev/null\n"
                + "}\n"
                + "for i in 1 2 3 4 5 6; do\n"
                + "  if probe_health \"$AGENT_PORT\"; then echo HEALTH_OK; exit 0; fi\n"
                + "  sleep 2\n"
                + "done\n"
                + "LISTEN_PORT=$(grep '^AGENT_LISTEN_PORT=' \"$ENV_FILE\" 2>/dev/null | head -1 | cut -d= -f2- | tr -d ' ')\n"
                + "echo HEALTH_FAIL\n"
                + "echo AGENT_LISTEN_PORT=${LISTEN_PORT:-unset}\n"
                + "if ! command -v curl >/dev/null 2>&1 && ! command -v wget >/dev/null 2>&1; then\n"
                + "  echo CURL_MISSING=1\n"
                + "fi\n"
                + "if [ -n \"$LISTEN_PORT\" ] && [ \"$LISTEN_PORT\" != \"$AGENT_PORT\" ]; then\n"
                + "  echo PORT_MISMATCH=1\n"
                + "  if probe_health \"$LISTEN_PORT\"; then echo HEALTH_OK_ON_CONFIGURED_PORT=1; fi\n"
                + "fi\n"
                + "ss -tlnp 2>/dev/null | grep -E \":(${AGENT_PORT}|${LISTEN_PORT:-9100}) \" | head -3 || true";
    }

    private String buildAgentCheckMessage(NodeAgentCheckRespVO resp, ComputeNodeDO node) {
        int agentPort = node.getAgentPort() != null && node.getAgentPort() > 0
                ? node.getAgentPort() : DEFAULT_AGENT_PORT;
        if (Boolean.TRUE.equals(resp.getDeployed()) && Boolean.TRUE.equals(resp.getConfigOk())
                && Boolean.TRUE.equals(resp.getControlPlaneReachable())) {
            return "节点代理已部署：服务运行正常，接入配置正确，控制面可达（端口 " + agentPort + "）";
        }
        if (Boolean.TRUE.equals(resp.getDeployed())) {
            StringBuilder sb = new StringBuilder("节点代理已部署且服务正常，但");
            if (Boolean.FALSE.equals(resp.getConfigOk())) {
                sb.append(" agent.env 与平台不一致");
            } else if (Boolean.FALSE.equals(resp.getControlPlaneReachable())) {
                sb.append(" 目标机无法访问控制面地址");
            } else {
                sb.append(" 心跳尚未上报");
            }
            sb.append("，请按下方诊断项排查");
            return sb.toString();
        }
        if (Boolean.TRUE.equals(resp.getServiceRunning()) || Boolean.TRUE.equals(resp.getHealthOk())) {
            StringBuilder sb = new StringBuilder("节点代理部分可用：");
            if (Boolean.TRUE.equals(resp.getServiceRunning())) {
                sb.append("systemd 服务已运行");
            }
            if (Boolean.TRUE.equals(resp.getHealthOk())) {
                if (Boolean.TRUE.equals(resp.getServiceRunning())) {
                    sb.append("，");
                }
                sb.append("健康检查通过");
            } else if (Boolean.TRUE.equals(resp.getServiceRunning())) {
                sb.append("，但健康检查未通过");
            }
            if (Boolean.FALSE.equals(resp.getConfigOk())) {
                sb.append("；接入配置与平台不一致");
            }
            sb.append("。建议重新部署（将自动重启服务）或排查服务状态");
            return sb.toString();
        }
        if (Boolean.TRUE.equals(resp.getInstallDirReady())) {
            return "检测到安装目录 " + AgentDeployUtil.REMOTE_INSTALL_DIR
                    + "，但服务未运行，可尝试重新部署";
        }
        return "未检测到节点代理，可进行全新部署";
    }

    private void applyEnvProbeResult(NodeAgentCheckRespVO resp, NodeMediaRemoteDeployRespVO.DeployStep envStep) {
        String out = envStep.getOutput() != null ? envStep.getOutput() : "";
        resp.setNodeIdMatch(out.contains("NODE_ID_MATCH=1"));
        resp.setTokenMatch(out.contains("TOKEN_MATCH=1"));
        resp.setConfigOk(Boolean.TRUE.equals(resp.getNodeIdMatch())
                && Boolean.TRUE.equals(resp.getTokenMatch())
                && out.contains("LISTEN_PORT_MATCH=1"));
        int cpIdx = out.indexOf("CP_URL=");
        if (cpIdx >= 0) {
            String line = out.substring(cpIdx);
            int end = line.indexOf('\n');
            resp.setControlPlaneUrl(line.substring("CP_URL=".length(), end >= 0 ? end : line.length()).trim());
        }
    }

    private NodeMediaRemoteDeployRespVO.DeployStep probeAgentEnvConfig(
            SshSessionHelper ssh, ComputeNodeDO node, String expectedControlPlaneUrl) throws Exception {
        String envFile = AgentDeployUtil.REMOTE_INSTALL_DIR + "/agent.env";
        String expectedNodeId = String.valueOf(node.getId());
        String expectedToken = node.getAgentToken() != null ? node.getAgentToken() : "";
        int expectedAgentPort = node.getAgentPort() != null && node.getAgentPort() > 0
                ? node.getAgentPort() : DEFAULT_AGENT_PORT;
        String script = "ENV_FILE='" + envFile + "'\n"
                + "EXPECTED_NODE_ID='" + expectedNodeId + "'\n"
                + "EXPECTED_TOKEN='" + expectedToken.replace("'", "'\\''") + "'\n"
                + "EXPECTED_CP='" + expectedControlPlaneUrl.replace("'", "'\\''") + "'\n"
                + "EXPECTED_LISTEN_PORT='" + expectedAgentPort + "'\n"
                + "if [ ! -f \"$ENV_FILE\" ]; then echo ENV_MISSING; exit 0; fi\n"
                + "NODE_ID=$(grep '^NODE_ID=' \"$ENV_FILE\" | head -1 | cut -d= -f2- | tr -d ' \\r\\n')\n"
                + "TOKEN=$(grep '^AGENT_TOKEN=' \"$ENV_FILE\" | head -1 | cut -d= -f2- | tr -d ' \\r\\n')\n"
                + "CP_URL=$(grep '^CONTROL_PLANE_URL=' \"$ENV_FILE\" | head -1 | cut -d= -f2- | tr -d ' \\r\\n')\n"
                + "LISTEN_PORT=$(grep '^AGENT_LISTEN_PORT=' \"$ENV_FILE\" | head -1 | cut -d= -f2- | tr -d ' \\r\\n')\n"
                + "echo NODE_ID=$NODE_ID\n"
                + "echo EXPECTED_NODE_ID=$EXPECTED_NODE_ID\n"
                + "echo CP_URL=$CP_URL\n"
                + "echo EXPECTED_CP=$EXPECTED_CP\n"
                + "echo AGENT_LISTEN_PORT=${LISTEN_PORT:-unset}\n"
                + "echo EXPECTED_LISTEN_PORT=$EXPECTED_LISTEN_PORT\n"
                + "if [ \"$NODE_ID\" = \"$EXPECTED_NODE_ID\" ]; then echo NODE_ID_MATCH=1; else echo NODE_ID_MATCH=0; fi\n"
                + "if [ \"$TOKEN\" = \"$EXPECTED_TOKEN\" ]; then echo TOKEN_MATCH=1; else echo TOKEN_MATCH=0; fi\n"
                + "if [ \"$CP_URL\" = \"$EXPECTED_CP\" ]; then echo CP_MATCH=1; else echo CP_MATCH=0; fi\n"
                + "if [ \"$LISTEN_PORT\" = \"$EXPECTED_LISTEN_PORT\" ]; then echo LISTEN_PORT_MATCH=1; else echo LISTEN_PORT_MATCH=0; fi\n"
                + "if echo \"$CP_URL\" | grep -Eq 'localhost|127\\.0\\.0\\.1'; then echo CP_LOCALHOST=1; fi";
        SshSessionHelper.SshExecResult result = ssh.exec(script, 15000);
        String out = result.combinedOutput();
        NodeMediaRemoteDeployRespVO.DeployStep step = new NodeMediaRemoteDeployRespVO.DeployStep();
        step.setName("接入配置");
        step.setOutput(trimDeployOutput(out, 3000));
        if (out.contains("ENV_MISSING")) {
            step.setStatus("failed");
            step.setOutput("未找到 " + envFile);
            return step;
        }
        boolean idOk = out.contains("NODE_ID_MATCH=1");
        boolean tokenOk = out.contains("TOKEN_MATCH=1");
        boolean cpOk = out.contains("CP_MATCH=1");
        boolean portOk = out.contains("LISTEN_PORT_MATCH=1");
        boolean localhost = out.contains("CP_LOCALHOST=1");
        if (idOk && tokenOk && cpOk && portOk && !localhost) {
            step.setStatus("success");
        } else if (idOk && tokenOk) {
            step.setStatus(localhost || !portOk ? "failed" : "success");
            if (localhost) {
                step.setOutput(step.getOutput() + "\nCONTROL_PLANE_URL 使用了 localhost/127.0.0.1，远程 Agent 无法访问平台");
            } else if (!cpOk) {
                step.setOutput(step.getOutput() + "\nCONTROL_PLANE_URL 与平台期望不一致，请更新 agent.env 并重启服务");
            } else if (!portOk) {
                step.setOutput(step.getOutput() + "\nAGENT_LISTEN_PORT 与平台节点代理端口不一致，请重新部署并重启服务");
            }
        } else {
            step.setStatus("failed");
            if (!idOk) {
                step.setOutput(step.getOutput() + "\nNODE_ID 与平台不一致");
            }
            if (!tokenOk) {
                step.setOutput(step.getOutput() + "\nAGENT_TOKEN 与平台不一致（若重置过令牌需同步 agent.env）");
            }
            if (!portOk) {
                step.setOutput(step.getOutput() + "\nAGENT_LISTEN_PORT 与平台节点代理端口不一致，请重新部署并重启服务");
            }
        }
        return step;
    }

    private NodeMediaRemoteDeployRespVO.DeployStep probeControlPlaneReachability(
            SshSessionHelper ssh, String controlPlaneUrl) throws Exception {
        NodeMediaRemoteDeployRespVO.DeployStep step = new NodeMediaRemoteDeployRespVO.DeployStep();
        step.setName("控制面连通");
        if (controlPlaneUrl == null || controlPlaneUrl.isBlank()) {
            step.setStatus("failed");
            step.setOutput("未读取到 CONTROL_PLANE_URL，无法探测");
            return step;
        }
        String safeUrl = controlPlaneUrl.trim().replaceAll("/+$", "").replace("'", "'\\''");
        String script = "CP='" + safeUrl + "'\n"
                + "CODE=$(curl -s -o /dev/null -w '%{http_code}' --connect-timeout 5 "
                + "-X POST \"$CP/register\" -H 'Content-Type: application/json' "
                + "-d '{\"nodeId\":0,\"agentToken\":\"probe\"}' 2>/dev/null || echo 000)\n"
                + "echo HTTP_CODE=$CODE\n"
                + "echo TARGET=$CP/register";
        SshSessionHelper.SshExecResult result = ssh.exec(script, 20000);
        String out = result.combinedOutput();
        step.setOutput(trimDeployOutput(out, 2000));
        if (out.contains("HTTP_CODE=000")) {
            step.setStatus("failed");
            step.setOutput(step.getOutput() + "\n目标机无法连接控制面，请检查网络、防火墙及 CONTROL_PLANE_URL 是否使用平台可达 IP");
            return step;
        }
        step.setStatus("success");
        return step;
    }

    private NodeMediaRemoteDeployRespVO.DeployStep probeAgentRecentLogs(SshSessionHelper ssh) throws Exception {
        SshSessionHelper.SshExecResult result = ssh.exec(
                "journalctl -u easyaiot-node-agent -n 12 --no-pager 2>/dev/null | tail -8 || "
                        + "echo '无法读取 systemd 日志（服务可能未安装）'",
                15000);
        NodeMediaRemoteDeployRespVO.DeployStep step = new NodeMediaRemoteDeployRespVO.DeployStep();
        step.setName("Agent 日志");
        step.setOutput(trimDeployOutput(result.combinedOutput(), 4000));
        step.setStatus(result.combinedOutput().contains("注册成功") ? "success"
                : result.combinedOutput().contains("注册失败") || result.combinedOutput().contains("请求异常")
                ? "failed" : "success");
        return step;
    }

    private NodeMediaRemoteDeployRespVO.DeployStep verifyAgentService(SshSessionHelper ssh, ComputeNodeDO node)
            throws Exception {
        int agentPort = node.getAgentPort() != null && node.getAgentPort() > 0
                ? node.getAgentPort() : DEFAULT_AGENT_PORT;
        SshSessionHelper.SshExecResult serviceResult = ssh.exec(
                "systemctl is-active easyaiot-node-agent 2>/dev/null || echo INACTIVE",
                15000);
        SshSessionHelper.SshExecResult healthResult = ssh.exec(buildAgentHealthProbeScript(agentPort), 30000);
        String out = serviceResult.combinedOutput() + " " + healthResult.combinedOutput();
        NodeMediaRemoteDeployRespVO.DeployStep step = new NodeMediaRemoteDeployRespVO.DeployStep();
        step.setName("服务验证");
        step.setOutput(out.trim());
        boolean serviceActive = out.contains("active");
        boolean healthOk = out.contains("HEALTH_OK");
        if (serviceActive && healthOk) {
            step.setStatus("success");
        } else {
            step.setStatus("failed");
            if (serviceActive && out.contains("HEALTH_FAIL")) {
                step.setOutput(out.trim() + "\n服务已启动但健康检查未通过，请检查 journalctl -u easyaiot-node-agent");
            }
        }
        return step;
    }

    private boolean isAgentInstallOutputSuccessful(SshSessionHelper.SshExecResult result, String output) {
        if (!result.isSuccess()) {
            return false;
        }
        if (output == null || !output.contains("INSTALL_OK")) {
            return false;
        }
        String lower = output.toLowerCase(Locale.ROOT);
        return !lower.contains("install_fail:")
                && !lower.contains("externally-managed-environment")
                && !lower.contains("ensurepip is not available");
    }

    private String resolveAgentInstallFailureMessage(String output) {
        if (output != null) {
            String lower = output.toLowerCase(Locale.ROOT);
            if (lower.contains("ensurepip is not available") || lower.contains("python3.12-venv")
                    || lower.contains("python3-venv")) {
                return "Agent 安装失败：目标机缺少 python-venv 包，请执行 sudo apt install python3.12-venv 后重试";
            }
            if (lower.contains("externally-managed-environment")) {
                return "Agent 安装失败：系统 Python 受 PEP 668 保护，请确认 install.sh 已更新为 venv 隔离安装";
            }
            if (lower.contains("install_fail:")) {
                int idx = lower.indexOf("install_fail:");
                return "Agent 安装失败：" + output.substring(idx).split("\n")[0].trim();
            }
        }
        return "Agent 安装脚本执行失败";
    }

    private NodeMediaRemoteDeployRespVO.DeployStep runDeployStep(String name, String status, String output) {
        NodeMediaRemoteDeployRespVO.DeployStep step = new NodeMediaRemoteDeployRespVO.DeployStep();
        step.setName(name);
        step.setStatus(status);
        step.setOutput(output);
        return step;
    }

    private String trimDeployOutput(String text, int maxLen) {
        if (text == null) {
            return "";
        }
        String trimmed = text.trim();
        if (trimmed.length() <= maxLen) {
            return trimmed;
        }
        return trimmed.substring(0, maxLen) + "\n... (输出已截断)";
    }

}
