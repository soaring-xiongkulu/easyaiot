package com.basiclab.iot.node.service.impl;

import cn.hutool.http.HttpRequest;
import cn.hutool.http.HttpResponse;
import cn.hutool.json.JSONObject;
import cn.hutool.json.JSONUtil;
import com.basiclab.iot.node.dal.dataobject.ComputeNodeDO;
import com.basiclab.iot.node.dal.dataobject.NodeSshCredentialDO;
import com.basiclab.iot.node.dal.pgsql.ComputeNodeMapper;
import com.basiclab.iot.node.dal.pgsql.NodeSshCredentialMapper;
import com.basiclab.iot.node.domain.vo.NodeMediaRemoteDeployRespVO;
import com.basiclab.iot.node.domain.vo.NodeMqttDeployReqVO;
import com.basiclab.iot.node.domain.vo.NodeMqttStackCheckRespVO;
import com.basiclab.iot.node.domain.vo.NodePortCheckRespVO;
import com.basiclab.iot.node.enums.NodeStatusEnum;
import com.basiclab.iot.node.service.ControlPlaneEndpointResolver;
import com.basiclab.iot.node.service.NodeMqttService;
import com.basiclab.iot.node.util.CredentialEncryptUtil;
import com.basiclab.iot.node.util.MqttStackDeployUtil;
import com.basiclab.iot.node.util.MqttStackDeployUtil.DeployPhase;
import com.basiclab.iot.node.util.RemotePortCheckUtil;
import com.basiclab.iot.node.util.SshSessionHelper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.validation.annotation.Validated;

import javax.annotation.Resource;
import java.io.File;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Base64;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.TimeUnit;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.COMPUTE_NODE_NOT_EXISTS;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.COMPUTE_NODE_OFFLINE;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.MQTT_CLUSTER_SOURCE_NOT_FOUND;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.MQTT_NODE_ROLE_INVALID;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.SSH_CREDENTIAL_NOT_EXISTS;

@Slf4j
@Service
@Validated
public class NodeMqttServiceImpl implements NodeMqttService {

    private static final int DOCKER_INSTALL_TIMEOUT_MS = 900000;
    private static final int EXPORT_TIMEOUT_MS = 1800000;
    private static final String EMQX_DOCKER_IMAGE = "emqx/emqx:5.8.7";
    private static final String EMQX_IMAGE_TAR = "emqx-emqx-5.8.7.tar";
    private static final String[] REQUIRED_IMAGE_TARS = {EMQX_IMAGE_TAR};
    private static final String[] SYNC_RELATIVE_FILES = {
            "install_mqtt_stack.sh",
            "install_docker.sh",
            "docker-compose.mqtt-node.yml",
    };
    private static final String REMOTE_COMPOSE_BIN = "/usr/local/bin/docker-compose";
    private static final String[] LOCAL_COMPOSE_CANDIDATES = {
            "/usr/local/bin/docker-compose",
            "/usr/bin/docker-compose",
            "/usr/libexec/docker/cli-plugins/docker-compose",
            "/usr/lib/docker/cli-plugins/docker-compose",
    };
    /** iot-sink EMQX HTTP 认证默认端口 */
    private static final int DEFAULT_MQTT_AUTH_PORT = 8090;

    @Resource
    private ComputeNodeMapper computeNodeMapper;
    @Resource
    private NodeSshCredentialMapper nodeSshCredentialMapper;
    @Resource
    private ControlPlaneEndpointResolver controlPlaneEndpointResolver;

    @Value("${easyaiot.mqtt.cluster-source-path:}")
    private String mqttClusterSourcePath;
    @Value("${easyaiot.mqtt.auth-port:" + DEFAULT_MQTT_AUTH_PORT + "}")
    private int mqttAuthPort;

    @Override
    public Map<String, Object> deployMqttStack(NodeMqttDeployReqVO reqVO) {
        ComputeNodeDO node = requireComputeNode(reqVO.getNodeId());
        validateMqttRole(node);
        if (!NodeStatusEnum.ONLINE.getStatus().equals(node.getStatus())) {
            throw exception(COMPUTE_NODE_OFFLINE);
        }
        Map<String, String> env = MqttStackDeployUtil.buildDeployEnvMap(
                node, controlPlaneEndpointResolver.resolveHookHost(), mqttAuthPort);
        if (reqVO.getEnv() != null && !reqVO.getEnv().isEmpty()) {
            env.putAll(reqVO.getEnv());
        }
        Map<String, Object> body = new HashMap<>();
        body.put("stackType", reqVO.getStackType() != null ? reqVO.getStackType() : "emqx");
        body.put("nodeId", String.valueOf(node.getId()));
        body.put("env", env);
        JSONObject result = callAgent(node, "/mqtt/deploy", body);
        Map<String, Object> resp = new HashMap<>();
        resp.put("nodeId", node.getId());
        resp.put("stackType", body.get("stackType"));
        resp.put("status", result.getStr("status", "running"));
        return resp;
    }

    @Override
    public NodeMediaRemoteDeployRespVO deployMqttStackBySsh(Long nodeId) {
        ComputeNodeDO node = requireComputeNode(nodeId);
        validateMqttRole(node);
        NodeSshCredential sshCredential = loadSshCredential(nodeId);

        NodeMediaRemoteDeployRespVO resp = new NodeMediaRemoteDeployRespVO();
        List<NodeMediaRemoteDeployRespVO.DeployStep> steps = new ArrayList<>();
        resp.setSteps(steps);

        int sshPort = ComputeNodeServiceImpl.resolveSshPort(node);
        String sourceRoot = resolveMqttClusterSource();

        try (SshSessionHelper ssh = openSshSession(node, sshCredential, sshPort)) {
            steps.add(runStep("SSH 连接", "success", "已连接 " + node.getHost() + ":" + sshPort));

            NodePortCheckRespVO portCheck = checkMqttPortsOnSession(ssh, node);
            steps.add(portCheck.getSteps().get(0));
            if (!Boolean.TRUE.equals(portCheck.getPortsReady())) {
                resp.setSuccess(false);
                resp.setMessage(portCheck.getMessage());
                return resp;
            }

            ExistingEmqxCheck existing = checkExistingEmqx(ssh, node);
            steps.add(existing.step);
            if (existing.running) {
                NodeMediaRemoteDeployRespVO.DeployStep verifyStep = verifyServices(ssh, node);
                steps.add(verifyStep);
                resp.setSuccess("success".equals(verifyStep.getStatus()));
                resp.setMessage("EMQX 已在运行，无需重复部署");
                return resp;
            }

            boolean needTar = !probeRemoteEmqxImage(ssh);
            NodeMediaRemoteDeployRespVO.DeployStep localImagesStep = ensureLocalMqttImages(sourceRoot, needTar);
            steps.add(localImagesStep);
            if (!"success".equals(localImagesStep.getStatus()) && !"skipped".equals(localImagesStep.getStatus())) {
                resp.setSuccess(false);
                resp.setMessage("本机离线镜像未就绪");
                return resp;
            }

            NodeMediaRemoteDeployRespVO.DeployStep dockerStep = ensureRemoteDocker(ssh, sourceRoot);
            steps.add(dockerStep);
            if (!"success".equals(dockerStep.getStatus())) {
                resp.setSuccess(false);
                resp.setMessage("Docker 未就绪");
                return resp;
            }

            NodeMediaRemoteDeployRespVO.DeployStep cleanStep = removeRemoteMqttCluster(ssh);
            steps.add(cleanStep);
            if (!"success".equals(cleanStep.getStatus())) {
                resp.setSuccess(false);
                resp.setMessage("清理目标机旧目录失败");
                return resp;
            }

            NodeMediaRemoteDeployRespVO.DeployStep syncStep = syncMqttCluster(ssh, sourceRoot, !needTar);
            steps.add(syncStep);
            if (!"success".equals(syncStep.getStatus())) {
                resp.setSuccess(false);
                resp.setMessage("mqtt-cluster 同步失败");
                return resp;
            }

            NodeMediaRemoteDeployRespVO.DeployStep composeStep = ensureRemoteDockerCompose(ssh);
            steps.add(composeStep);
            if (!"success".equals(composeStep.getStatus())) {
                resp.setSuccess(false);
                resp.setMessage("Docker Compose 未就绪");
                return resp;
            }

            if (needTar) {
                NodeMediaRemoteDeployRespVO.DeployStep importStep = runRemoteDeployPhase(
                        ssh, node, DeployPhase.PREPARE_IMAGES, "导入镜像", 600000);
                steps.add(importStep);
                if (!"success".equals(importStep.getStatus())) {
                    resp.setSuccess(false);
                    resp.setMessage("镜像导入失败");
                    return resp;
                }
            } else {
                steps.add(runStep("导入镜像", "skipped", "目标机已有 EMQX Docker 镜像，跳过 docker load"));
            }

            NodeMediaRemoteDeployRespVO.DeployStep startStep = runRemoteDeployPhase(
                    ssh, node, DeployPhase.DEPLOY_SERVICES, "启动服务", 300000);
            steps.add(startStep);
            if (!"success".equals(startStep.getStatus())) {
                resp.setSuccess(false);
                resp.setMessage("服务启动失败");
                return resp;
            }

            NodeMediaRemoteDeployRespVO.DeployStep verifyStep = verifyServices(ssh, node);
            steps.add(verifyStep);
            boolean ok = "success".equals(verifyStep.getStatus()) || "skipped".equals(verifyStep.getStatus());
            resp.setSuccess(ok);
            resp.setMessage(ok ? "MQTT 网关部署完成" : "部署完成但服务验证未通过");
            return resp;
        } catch (Exception e) {
            log.error("MQTT 栈 SSH 部署失败 nodeId={} host={}:{}", nodeId, node.getHost(), sshPort, e);
            NodeMediaRemoteDeployRespVO.DeployStep fail = new NodeMediaRemoteDeployRespVO.DeployStep();
            fail.setName(steps.isEmpty() ? "SSH 连接" : "部署中断");
            fail.setStatus("failed");
            String detail = e.getMessage() != null ? e.getMessage() : e.getClass().getSimpleName();
            fail.setOutput("连接 " + node.getHost() + ":" + sshPort + " 失败: " + detail);
            steps.add(fail);
            resp.setSuccess(false);
            resp.setMessage(fail.getOutput());
            return resp;
        }
    }

    @Override
    public NodeMqttStackCheckRespVO checkMqttStackBySsh(Long nodeId) {
        ComputeNodeDO node = requireComputeNode(nodeId);
        validateMqttRole(node);
        NodeSshCredential credential = loadSshCredential(nodeId);
        int sshPort = ComputeNodeServiceImpl.resolveSshPort(node);

        NodeMqttStackCheckRespVO resp = new NodeMqttStackCheckRespVO();
        List<NodeMediaRemoteDeployRespVO.DeployStep> steps = new ArrayList<>();
        resp.setSteps(steps);

        try (SshSessionHelper ssh = openSshSession(node, credential, sshPort)) {
            steps.add(runStep("SSH 连接", "success", "已连接 " + node.getHost() + ":" + sshPort));

            NodeMediaRemoteDeployRespVO.DeployStep dockerStep = probeRemoteDockerStatus(ssh);
            steps.add(dockerStep);
            resp.setDockerReady("success".equals(dockerStep.getStatus()));

            NodeMediaRemoteDeployRespVO.DeployStep composeStep = probeRemoteComposeStatus(ssh);
            steps.add(composeStep);
            resp.setComposeReady("success".equals(composeStep.getStatus()));

            NodeMediaRemoteDeployRespVO.DeployStep emqxStep = probeEmqxStatus(ssh, node);
            steps.add(emqxStep);
            resp.setEmqxRunning("success".equals(emqxStep.getStatus()));
            resp.setDeployed(resp.getEmqxRunning());
            resp.setSuccess(true);
            resp.setMessage(buildCheckMessage(resp, node));
            return resp;
        } catch (Exception e) {
            log.error("MQTT 栈 SSH 检测失败 nodeId={} host={}:{}", nodeId, node.getHost(), sshPort, e);
            NodeMediaRemoteDeployRespVO.DeployStep fail = new NodeMediaRemoteDeployRespVO.DeployStep();
            fail.setName(steps.isEmpty() ? "SSH 连接" : "检测中断");
            fail.setStatus("failed");
            String detail = e.getMessage() != null ? e.getMessage() : e.getClass().getSimpleName();
            fail.setOutput("连接 " + node.getHost() + ":" + sshPort + " 失败: " + detail);
            steps.add(fail);
            resp.setSuccess(false);
            resp.setDeployed(false);
            resp.setEmqxRunning(false);
            resp.setDockerReady(false);
            resp.setComposeReady(false);
            resp.setMessage(fail.getOutput());
            return resp;
        }
    }

    @Override
    public NodePortCheckRespVO checkMqttPortsBySsh(Long nodeId) {
        ComputeNodeDO node = requireComputeNode(nodeId);
        validateMqttRole(node);
        NodeSshCredential credential = loadSshCredential(nodeId);
        int sshPort = ComputeNodeServiceImpl.resolveSshPort(node);

        NodePortCheckRespVO resp = new NodePortCheckRespVO();
        List<NodeMediaRemoteDeployRespVO.DeployStep> steps = new ArrayList<>();
        resp.setSteps(steps);

        try (SshSessionHelper ssh = openSshSession(node, credential, sshPort)) {
            steps.add(runStep("SSH 连接", "success", "已连接 " + node.getHost() + ":" + sshPort));
            NodePortCheckRespVO portCheck = checkMqttPortsOnSession(ssh, node);
            steps.addAll(portCheck.getSteps());
            resp.setPorts(portCheck.getPorts());
            resp.setPortsReady(portCheck.getPortsReady());
            resp.setSuccess(true);
            resp.setMessage(portCheck.getMessage());
            return resp;
        } catch (Exception e) {
            log.error("MQTT 端口检测失败 nodeId={} host={}:{}", nodeId, node.getHost(), sshPort, e);
            NodeMediaRemoteDeployRespVO.DeployStep fail = new NodeMediaRemoteDeployRespVO.DeployStep();
            fail.setName(steps.isEmpty() ? "SSH 连接" : "检测中断");
            fail.setStatus("failed");
            String detail = e.getMessage() != null ? e.getMessage() : e.getClass().getSimpleName();
            fail.setOutput("连接 " + node.getHost() + ":" + sshPort + " 失败: " + detail);
            steps.add(fail);
            resp.setSuccess(false);
            resp.setPortsReady(false);
            resp.setMessage(fail.getOutput());
            return resp;
        }
    }

    @Override
    public NodeMediaRemoteDeployRespVO stopMqttServiceBySsh(Long nodeId) {
        ComputeNodeDO node = requireComputeNode(nodeId);
        validateMqttRole(node);
        NodeSshCredential credential = loadSshCredential(nodeId);
        int sshPort = ComputeNodeServiceImpl.resolveSshPort(node);
        String nodeName = MqttStackDeployUtil.sanitizeNodeName(node.getName(), node.getHost());

        NodeMediaRemoteDeployRespVO resp = new NodeMediaRemoteDeployRespVO();
        List<NodeMediaRemoteDeployRespVO.DeployStep> steps = new ArrayList<>();
        resp.setSteps(steps);

        try (SshSessionHelper ssh = openSshSession(node, credential, sshPort)) {
            steps.add(runStep("SSH 连接", "success", "已连接 " + node.getHost() + ":" + sshPort));
            String remoteRoot = MqttStackDeployUtil.remoteClusterRoot();
            String remoteScript = "#!/usr/bin/env bash\nset -euo pipefail\n"
                    + "print_step() { echo \">>> $*\"; }\n"
                    + "print_ok() { echo \"[OK] $*\"; }\n"
                    + "REMOTE_ROOT=\"" + remoteRoot + "\"\n"
                    + "if [[ -f \"${REMOTE_ROOT}/docker-compose.mqtt-node.yml\" ]]; then\n"
                    + "  cd \"${REMOTE_ROOT}\"\n"
                    + "  if docker compose version >/dev/null 2>&1; then COMPOSE_CMD=\"docker compose\"; "
                    + "elif command -v docker-compose >/dev/null 2>&1; then COMPOSE_CMD=\"docker-compose\"; "
                    + "elif [[ -x /usr/local/bin/docker-compose ]]; then COMPOSE_CMD=\"/usr/local/bin/docker-compose\"; "
                    + "else COMPOSE_CMD=\"\"; fi\n"
                    + "  if [[ -n \"${COMPOSE_CMD}\" ]]; then\n"
                    + "    print_step \"停止 EMQX 容器\"\n"
                    + "    ${COMPOSE_CMD} -f docker-compose.mqtt-node.yml stop emqx 2>&1 || true\n"
                    + "  fi\n"
                    + "fi\n"
                    + "for cname in \"" + nodeName + "-emqx\" \"emqx-server\"; do\n"
                    + "  if docker ps -a --format '{{.Names}}' | grep -qx \"${cname}\"; then\n"
                    + "    print_step \"停止容器 ${cname}\"\n"
                    + "    docker stop \"${cname}\" 2>&1 || true\n"
                    + "    print_ok \"已停止 ${cname}\"\n"
                    + "  fi\n"
                    + "done\n"
                    + "echo STOP_OK";
            SshSessionHelper.SshExecResult result = execRemoteScript(ssh, remoteScript, 120000);
            NodeMediaRemoteDeployRespVO.DeployStep step = new NodeMediaRemoteDeployRespVO.DeployStep();
            step.setName("停止 EMQX");
            step.setOutput(trimOutput(result.combinedOutput(), 4000));
            boolean ok = result.isSuccess() && result.combinedOutput().contains("STOP_OK");
            step.setStatus(ok ? "success" : "failed");
            steps.add(step);
            resp.setSuccess(ok);
            resp.setMessage(ok ? "EMQX 已停止" : "EMQX 停止失败");
            return resp;
        } catch (Exception e) {
            return buildSshFailure(resp, steps, node, sshPort, "停止 EMQX", e);
        }
    }

    @Override
    public NodeMediaRemoteDeployRespVO removeMqttContainerBySsh(Long nodeId) {
        ComputeNodeDO node = requireComputeNode(nodeId);
        validateMqttRole(node);
        NodeSshCredential credential = loadSshCredential(nodeId);
        int sshPort = ComputeNodeServiceImpl.resolveSshPort(node);
        String nodeName = MqttStackDeployUtil.sanitizeNodeName(node.getName(), node.getHost());

        NodeMediaRemoteDeployRespVO resp = new NodeMediaRemoteDeployRespVO();
        List<NodeMediaRemoteDeployRespVO.DeployStep> steps = new ArrayList<>();
        resp.setSteps(steps);

        try (SshSessionHelper ssh = openSshSession(node, credential, sshPort)) {
            steps.add(runStep("SSH 连接", "success", "已连接 " + node.getHost() + ":" + sshPort));
            String remoteRoot = MqttStackDeployUtil.remoteClusterRoot();
            String remoteScript = "#!/usr/bin/env bash\nset -euo pipefail\n"
                    + "print_step() { echo \">>> $*\"; }\n"
                    + "print_ok() { echo \"[OK] $*\"; }\n"
                    + "REMOTE_ROOT=\"" + remoteRoot + "\"\n"
                    + "if [[ -f \"${REMOTE_ROOT}/docker-compose.mqtt-node.yml\" ]]; then\n"
                    + "  cd \"${REMOTE_ROOT}\"\n"
                    + "  if docker compose version >/dev/null 2>&1; then COMPOSE_CMD=\"docker compose\"; "
                    + "elif command -v docker-compose >/dev/null 2>&1; then COMPOSE_CMD=\"docker-compose\"; "
                    + "elif [[ -x /usr/local/bin/docker-compose ]]; then COMPOSE_CMD=\"/usr/local/bin/docker-compose\"; "
                    + "else COMPOSE_CMD=\"\"; fi\n"
                    + "  if [[ -n \"${COMPOSE_CMD}\" ]]; then\n"
                    + "    print_step \"停止并移除 EMQX 容器\"\n"
                    + "    ${COMPOSE_CMD} -f docker-compose.mqtt-node.yml stop emqx 2>&1 || true\n"
                    + "    ${COMPOSE_CMD} -f docker-compose.mqtt-node.yml rm -f emqx 2>&1 || true\n"
                    + "  fi\n"
                    + "fi\n"
                    + "for cname in \"" + nodeName + "-emqx\"; do\n"
                    + "  if docker ps -a --format '{{.Names}}' | grep -qx \"${cname}\"; then\n"
                    + "    print_step \"删除容器 ${cname}\"\n"
                    + "    docker rm -f \"${cname}\" 2>&1 || true\n"
                    + "    print_ok \"已删除 ${cname}\"\n"
                    + "  else\n"
                    + "    echo \"[SKIP] 容器不存在: ${cname}\"\n"
                    + "  fi\n"
                    + "done\n"
                    + "echo REMOVE_CONTAINER_OK";
            SshSessionHelper.SshExecResult result = execRemoteScript(ssh, remoteScript, 180000);
            NodeMediaRemoteDeployRespVO.DeployStep step = new NodeMediaRemoteDeployRespVO.DeployStep();
            step.setName("删除容器");
            step.setOutput(trimOutput(result.combinedOutput(), 6000));
            boolean ok = result.isSuccess() && result.combinedOutput().contains("REMOVE_CONTAINER_OK");
            step.setStatus(ok ? "success" : "failed");
            steps.add(step);
            resp.setSuccess(ok);
            resp.setMessage(ok ? "EMQX 容器已删除" : "删除容器失败");
            return resp;
        } catch (Exception e) {
            return buildSshFailure(resp, steps, node, sshPort, "删除容器", e);
        }
    }

    @Override
    public NodeMediaRemoteDeployRespVO removeMqttImageBySsh(Long nodeId) {
        ComputeNodeDO node = requireComputeNode(nodeId);
        validateMqttRole(node);
        NodeSshCredential credential = loadSshCredential(nodeId);
        int sshPort = ComputeNodeServiceImpl.resolveSshPort(node);

        NodeMediaRemoteDeployRespVO resp = new NodeMediaRemoteDeployRespVO();
        List<NodeMediaRemoteDeployRespVO.DeployStep> steps = new ArrayList<>();
        resp.setSteps(steps);

        try (SshSessionHelper ssh = openSshSession(node, credential, sshPort)) {
            steps.add(runStep("SSH 连接", "success", "已连接 " + node.getHost() + ":" + sshPort));
            String remoteRoot = MqttStackDeployUtil.remoteClusterRoot();
            String remoteScript = "#!/usr/bin/env bash\nset -euo pipefail\n"
                    + "print_step() { echo \">>> $*\"; }\n"
                    + "print_ok() { echo \"[OK] $*\"; }\n"
                    + "for img in \"" + EMQX_DOCKER_IMAGE + "\"; do\n"
                    + "  if docker image inspect \"${img}\" >/dev/null 2>&1; then\n"
                    + "    print_step \"删除镜像 ${img}\"\n"
                    + "    docker rmi -f \"${img}\" 2>&1 || true\n"
                    + "    print_ok \"已删除 ${img}\"\n"
                    + "  else\n"
                    + "    echo \"[SKIP] 镜像不存在: ${img}\"\n"
                    + "  fi\n"
                    + "done\n"
                    + "for tar in \"" + remoteRoot + "/images/" + EMQX_IMAGE_TAR + "\"; do\n"
                    + "  if [[ -f \"${tar}\" ]]; then\n"
                    + "    print_step \"删除离线包 ${tar}\"\n"
                    + "    rm -f \"${tar}\" 2>&1 || true\n"
                    + "  fi\n"
                    + "done\n"
                    + "echo REMOVE_IMAGE_OK";
            SshSessionHelper.SshExecResult result = execRemoteScript(ssh, remoteScript, 180000);
            NodeMediaRemoteDeployRespVO.DeployStep step = new NodeMediaRemoteDeployRespVO.DeployStep();
            step.setName("删除镜像");
            step.setOutput(trimOutput(result.combinedOutput(), 6000));
            boolean ok = result.isSuccess() && result.combinedOutput().contains("REMOVE_IMAGE_OK");
            step.setStatus(ok ? "success" : "failed");
            steps.add(step);
            resp.setSuccess(ok);
            resp.setMessage(ok ? "EMQX Docker 镜像已删除" : "删除镜像失败");
            return resp;
        } catch (Exception e) {
            return buildSshFailure(resp, steps, node, sshPort, "删除镜像", e);
        }
    }

    private NodePortCheckRespVO checkMqttPortsOnSession(SshSessionHelper ssh, ComputeNodeDO node) throws Exception {
        LinkedHashMap<String, Integer> portMap = RemotePortCheckUtil.mqttDeployPorts(node.getTags());
        return RemotePortCheckUtil.checkPorts(ssh, portMap);
    }

    private String buildCheckMessage(NodeMqttStackCheckRespVO resp, ComputeNodeDO node) {
        int dashboard = MqttStackDeployUtil.tagInt(node.getTags(), "emqx_dashboard_port", 18083);
        int mqttTcp = MqttStackDeployUtil.tagInt(node.getTags(), "mqtt_tcp_port", 1883);
        if (Boolean.TRUE.equals(resp.getDeployed())) {
            return "MQTT 网关已部署：EMQX 运行中（MQTT " + mqttTcp + " / Dashboard " + dashboard + "）";
        }
        return "未检测到运行中的 EMQX，目标机可进行全新部署";
    }

    private NodeMediaRemoteDeployRespVO.DeployStep probeRemoteDockerStatus(SshSessionHelper ssh) throws Exception {
        SshSessionHelper.SshExecResult result = ssh.exec(
                "if docker info >/dev/null 2>&1; then echo DOCKER_OK; docker --version 2>/dev/null; "
                        + "elif command -v docker >/dev/null 2>&1; then echo DOCKER_DOWN; "
                        + "else echo DOCKER_MISSING; fi",
                30000);
        String out = result.combinedOutput();
        NodeMediaRemoteDeployRespVO.DeployStep step = new NodeMediaRemoteDeployRespVO.DeployStep();
        step.setName("Docker");
        step.setOutput(trimOutput(out, 2000));
        if (out.contains("DOCKER_OK")) {
            step.setStatus("success");
            return step;
        }
        if (out.contains("DOCKER_DOWN")) {
            step.setStatus("failed");
            step.setOutput("已安装 Docker 但未运行（可尝试 systemctl start docker）");
            return step;
        }
        step.setStatus("failed");
        step.setOutput("未安装 Docker");
        return step;
    }

    private NodeMediaRemoteDeployRespVO.DeployStep probeRemoteComposeStatus(SshSessionHelper ssh) throws Exception {
        SshSessionHelper.SshExecResult result = ssh.exec(
                "if docker compose version >/dev/null 2>&1; then echo COMPOSE_OK; docker compose version 2>/dev/null | head -1; "
                        + "elif command -v docker-compose >/dev/null 2>&1 && docker-compose version >/dev/null 2>&1; "
                        + "then echo COMPOSE_OK; docker-compose --version 2>/dev/null; "
                        + "elif [[ -x /usr/local/bin/docker-compose ]] && /usr/local/bin/docker-compose version >/dev/null 2>&1; "
                        + "then echo COMPOSE_OK; /usr/local/bin/docker-compose --version 2>/dev/null; "
                        + "else echo COMPOSE_MISSING; fi",
                30000);
        String out = result.combinedOutput();
        NodeMediaRemoteDeployRespVO.DeployStep step = new NodeMediaRemoteDeployRespVO.DeployStep();
        step.setName("Docker Compose");
        if (out.contains("COMPOSE_OK")) {
            step.setStatus("success");
            step.setOutput(trimOutput(out.replace("COMPOSE_OK", "").trim(), 1000));
            return step;
        }
        step.setStatus("failed");
        step.setOutput("未安装 Docker Compose（自动部署时会尝试安装或同步）");
        return step;
    }

    private NodeMediaRemoteDeployRespVO.DeployStep probeEmqxStatus(SshSessionHelper ssh, ComputeNodeDO node)
            throws Exception {
        int dashboard = MqttStackDeployUtil.tagInt(node.getTags(), "emqx_dashboard_port", 18083);
        String nodeName = MqttStackDeployUtil.sanitizeNodeName(node.getName(), node.getHost());
        SshSessionHelper.SshExecResult result = ssh.exec(
                "cname=\"" + nodeName + "-emqx\"; "
                        + "if docker exec \"$cname\" /opt/emqx/bin/emqx ctl status >/dev/null 2>&1; then "
                        + "echo EMQX_RUNNING; "
                        + "elif body=$(curl -sf --connect-timeout 5 --max-time 10 "
                        + "http://127.0.0.1:" + dashboard + "/api/v5/status 2>/dev/null); "
                        + "then echo \"$body\"; "
                        + "if echo \"$body\" | grep -qiE 'running|ok|started'; then echo EMQX_RUNNING; "
                        + "else echo EMQX_STOPPED; fi; "
                        + "else echo EMQX_STOPPED; fi",
                20000);
        String out = result.combinedOutput();
        NodeMediaRemoteDeployRespVO.DeployStep step = new NodeMediaRemoteDeployRespVO.DeployStep();
        step.setName("EMQX");
        if (out.contains("EMQX_RUNNING")) {
            step.setStatus("success");
            step.setOutput("EMQX 已在运行（Dashboard " + dashboard + "）\n" + trimOutput(out.replace("EMQX_RUNNING", "").trim(), 500));
            return step;
        }
        step.setStatus("failed");
        step.setOutput("EMQX 未运行（Dashboard " + dashboard + " 无响应）");
        return step;
    }

    private ExistingEmqxCheck checkExistingEmqx(SshSessionHelper ssh, ComputeNodeDO node) throws Exception {
        NodeMediaRemoteDeployRespVO.DeployStep step = probeEmqxStatus(ssh, node);
        ExistingEmqxCheck check = new ExistingEmqxCheck();
        check.step = step;
        check.running = "success".equals(step.getStatus());
        if (check.running) {
            step.setName("检测已有服务");
            step.setOutput("检测到 EMQX 已在运行");
        } else {
            step.setName("检测已有服务");
            step.setStatus("success");
            step.setOutput("未检测到运行中的 EMQX");
        }
        return check;
    }

    private boolean probeRemoteEmqxImage(SshSessionHelper ssh) throws Exception {
        SshSessionHelper.SshExecResult result = ssh.exec(
                "docker image inspect \"" + EMQX_DOCKER_IMAGE + "\" >/dev/null 2>&1 && echo PRESENT || echo MISSING",
                30000);
        return result.combinedOutput().contains("PRESENT");
    }

    private NodeMediaRemoteDeployRespVO.DeployStep ensureLocalMqttImages(String sourceRoot, boolean needTar) {
        if (!needTar) {
            return runStep("准备离线镜像", "skipped", "目标机已有 EMQX Docker 镜像，跳过本机导出");
        }
        File imagesDir = new File(sourceRoot, "images");
        File tar = new File(imagesDir, EMQX_IMAGE_TAR);
        if (tar.isFile() && tar.length() > 0) {
            return runStep("准备离线镜像", "success",
                    "本机离线镜像包已就绪\n  " + EMQX_IMAGE_TAR + " (" + formatBytes(tar.length()) + ")");
        }
        NodeMediaRemoteDeployRespVO.DeployStep step = new NodeMediaRemoteDeployRespVO.DeployStep();
        step.setName("准备离线镜像");
        File exportScript = new File(sourceRoot, "export_mqtt_images.sh");
        if (!exportScript.isFile()) {
            step.setStatus("failed");
            step.setOutput("缺少离线镜像包: " + EMQX_IMAGE_TAR + "；且未找到 export_mqtt_images.sh");
            return step;
        }
        try {
            String exportOutput = runExportScript(exportScript);
            if (!tar.isFile() || tar.length() == 0) {
                step.setStatus("failed");
                step.setOutput("本机导出未完成，仍缺少: " + EMQX_IMAGE_TAR + "\n" + trimOutput(exportOutput, 4000));
                return step;
            }
            step.setStatus("success");
            step.setOutput("本机已导出 EMQX 离线镜像\n  " + EMQX_IMAGE_TAR + " (" + formatBytes(tar.length()) + ")"
                    + (exportOutput.isBlank() ? "" : "\n" + trimOutput(exportOutput, 3000)));
            return step;
        } catch (Exception e) {
            log.error("本机导出 EMQX 镜像失败 sourceRoot={}", sourceRoot, e);
            step.setStatus("failed");
            step.setOutput("本机导出镜像失败: " + e.getMessage());
            return step;
        }
    }

    private String runExportScript(File exportScript) throws Exception {
        ProcessBuilder pb = new ProcessBuilder("bash", exportScript.getAbsolutePath());
        pb.directory(exportScript.getParentFile());
        pb.redirectErrorStream(true);
        Process process = pb.start();
        String output;
        try (InputStream in = process.getInputStream()) {
            output = new String(in.readAllBytes(), StandardCharsets.UTF_8);
        }
        boolean finished = process.waitFor(EXPORT_TIMEOUT_MS, TimeUnit.MILLISECONDS);
        if (!finished) {
            process.destroyForcibly();
            throw new IllegalStateException("导出超时（超过 " + (EXPORT_TIMEOUT_MS / 60000) + " 分钟）");
        }
        if (process.exitValue() != 0) {
            throw new IllegalStateException(output.isBlank()
                    ? "export_mqtt_images.sh 退出码 " + process.exitValue()
                    : output.trim());
        }
        return output;
    }

    private NodeMediaRemoteDeployRespVO.DeployStep runRemoteDeployPhase(
            SshSessionHelper ssh, ComputeNodeDO node, DeployPhase phase, String stepName, int timeoutMs)
            throws Exception {
        String remoteScript = MqttStackDeployUtil.buildDeployScript(
                node, controlPlaneEndpointResolver.resolveHookHost(), mqttAuthPort, phase);
        String encoded = Base64.getEncoder().encodeToString(remoteScript.getBytes(StandardCharsets.UTF_8));
        String tmpScript = "/tmp/easyaiot-mqtt-" + phase.name().toLowerCase(Locale.ROOT) + ".sh";
        SshSessionHelper.SshExecResult result = ssh.exec(
                "echo " + encoded + " | base64 -d > " + tmpScript
                        + " && chmod +x " + tmpScript
                        + " && bash " + tmpScript,
                timeoutMs);
        NodeMediaRemoteDeployRespVO.DeployStep step = new NodeMediaRemoteDeployRespVO.DeployStep();
        step.setName(stepName);
        step.setOutput(trimOutput(result.combinedOutput(), 8000));
        step.setStatus(result.isSuccess() ? "success" : "failed");
        return step;
    }

    private NodeMediaRemoteDeployRespVO.DeployStep removeRemoteMqttCluster(SshSessionHelper ssh) throws Exception {
        String remoteRoot = MqttStackDeployUtil.remoteClusterRoot();
        SshSessionHelper.SshExecResult result = ssh.exec(
                "if [ -d \"" + remoteRoot + "\" ]; then "
                        + "rm -rf \"" + remoteRoot + "/emqx\" 2>/dev/null; "
                        + "rm -f \"" + remoteRoot + "/install_mqtt_stack.sh\" "
                        + "\"" + remoteRoot + "/install_docker.sh\" "
                        + "\"" + remoteRoot + "/docker-compose.mqtt-node.yml\" 2>/dev/null; "
                        + "mkdir -p \"" + remoteRoot + "/images\"; "
                        + "echo CLEANED; "
                        + "else mkdir -p \"" + remoteRoot + "/images\"; echo NOT_EXISTS; fi",
                120000);
        NodeMediaRemoteDeployRespVO.DeployStep step = new NodeMediaRemoteDeployRespVO.DeployStep();
        step.setName("清理旧目录");
        step.setOutput(trimOutput(result.combinedOutput(), 2000));
        if (!result.isSuccess()) {
            step.setStatus("failed");
            step.setOutput(step.getOutput() + "\n无法清理 " + remoteRoot + "，请检查 SSH 用户权限");
            return step;
        }
        step.setStatus("success");
        if (step.getOutput() != null && step.getOutput().contains("NOT_EXISTS")) {
            step.setOutput("目标机不存在 " + remoteRoot + "，已创建目录");
        } else {
            step.setOutput("已清理脚本与配置（保留已有离线镜像包 images/）");
        }
        return step;
    }

    private NodeMediaRemoteDeployRespVO.DeployStep syncMqttCluster(
            SshSessionHelper ssh, String sourceRoot, boolean skipImageTar) throws Exception {
        String remoteRoot = MqttStackDeployUtil.remoteClusterRoot();
        ssh.ensureRemoteDir(remoteRoot + "/emqx");
        ssh.ensureRemoteDir(remoteRoot + "/images");

        int scriptCount = 0;
        for (String relative : SYNC_RELATIVE_FILES) {
            File local = new File(sourceRoot, relative);
            if (!local.isFile()) {
                throw exception(MQTT_CLUSTER_SOURCE_NOT_FOUND);
            }
            ssh.uploadFile(local.getAbsolutePath(), remoteRoot + "/" + relative);
            if (relative.endsWith(".sh")) {
                ssh.exec("chmod +x " + remoteRoot + "/" + relative, 10000);
            }
            scriptCount++;
        }

        NodeMediaRemoteDeployRespVO.DeployStep step = new NodeMediaRemoteDeployRespVO.DeployStep();
        step.setName("同步 mqtt-cluster");
        int syncedTarCount = 0;
        long imageBytes = 0;
        if (!skipImageTar) {
            File tar = new File(sourceRoot, "images/" + EMQX_IMAGE_TAR);
            if (!tar.isFile() || tar.length() == 0) {
                step.setStatus("failed");
                step.setOutput("本机缺少离线镜像包: " + EMQX_IMAGE_TAR);
                return step;
            }
            if (!remoteTarMatches(ssh, EMQX_IMAGE_TAR, tar.length())) {
                ssh.uploadFile(tar.getAbsolutePath(), remoteRoot + "/images/" + EMQX_IMAGE_TAR);
                imageBytes = tar.length();
                syncedTarCount = 1;
            }
        }
        step.setStatus("success");
        StringBuilder output = new StringBuilder();
        output.append("已上传 ").append(scriptCount).append(" 个脚本/配置");
        if (syncedTarCount > 0) {
            output.append(" + ").append(syncedTarCount).append(" 个离线镜像包（")
                    .append(formatBytes(imageBytes)).append("）");
        } else if (skipImageTar) {
            output.append("；跳过已有镜像/离线包");
        }
        output.append(" 至 ").append(remoteRoot);
        step.setOutput(output.toString());
        return step;
    }

    private boolean remoteTarMatches(SshSessionHelper ssh, String tarName, long localSize) throws Exception {
        String remoteRoot = MqttStackDeployUtil.remoteClusterRoot();
        SshSessionHelper.SshExecResult result = ssh.exec(
                "f=\"" + remoteRoot + "/images/" + tarName + "\"; "
                        + "if [[ -f \"$f\" ]]; then wc -c < \"$f\"; else echo 0; fi",
                15000);
        try {
            long remoteSize = Long.parseLong(result.combinedOutput().trim().split("\\s+")[0]);
            return remoteSize == localSize && remoteSize > 0;
        } catch (NumberFormatException e) {
            return false;
        }
    }

    private NodeMediaRemoteDeployRespVO.DeployStep ensureRemoteDocker(SshSessionHelper ssh, String sourceRoot)
            throws Exception {
        NodeMediaRemoteDeployRespVO.DeployStep step = new NodeMediaRemoteDeployRespVO.DeployStep();
        step.setName("Docker");
        SshSessionHelper.SshExecResult check = ssh.exec(
                "if docker info >/dev/null 2>&1; then echo DOCKER_OK; "
                        + "elif command -v docker >/dev/null 2>&1; then echo DOCKER_START_NEEDED; "
                        + "else echo DOCKER_MISSING; fi",
                30000);
        String checkOut = check.combinedOutput();
        if (checkOut.contains("DOCKER_OK")) {
            step.setStatus("success");
            step.setOutput("目标机 Docker 已就绪");
            return step;
        }
        if (checkOut.contains("DOCKER_START_NEEDED")) {
            SshSessionHelper.SshExecResult start = ssh.exec(
                    "(sudo systemctl start docker 2>/dev/null || systemctl start docker 2>/dev/null || true)"
                            + " && sleep 2 && docker info >/dev/null 2>&1 && echo DOCKER_OK || echo DOCKER_STILL_DOWN",
                    60000);
            if (start.combinedOutput().contains("DOCKER_OK")) {
                step.setStatus("success");
                step.setOutput("目标机 Docker 已启动");
                return step;
            }
        }
        File installScript = new File(sourceRoot, "install_docker.sh");
        if (!installScript.isFile()) {
            step.setStatus("failed");
            step.setOutput("目标机未安装 Docker，且控制面缺少 install_docker.sh");
            return step;
        }
        String remoteRoot = MqttStackDeployUtil.remoteClusterRoot();
        ssh.ensureRemoteDir(remoteRoot);
        ssh.uploadFile(installScript.getAbsolutePath(), remoteRoot + "/install_docker.sh");
        ssh.exec("chmod +x " + remoteRoot + "/install_docker.sh", 10000);
        SshSessionHelper.SshExecResult install = ssh.exec(
                "bash " + remoteRoot + "/install_docker.sh", DOCKER_INSTALL_TIMEOUT_MS);
        if (install.isSuccess()) {
            step.setStatus("success");
            step.setOutput("已在目标机安装 Docker\n" + trimOutput(install.combinedOutput(), 3000));
            return step;
        }
        step.setStatus("failed");
        step.setOutput("自动安装 Docker 失败\n" + trimOutput(install.combinedOutput(), 4000));
        return step;
    }

    private NodeMediaRemoteDeployRespVO.DeployStep ensureRemoteDockerCompose(SshSessionHelper ssh) throws Exception {
        NodeMediaRemoteDeployRespVO.DeployStep existing = probeRemoteComposeStatus(ssh);
        if ("success".equals(existing.getStatus())) {
            existing.setName("Docker Compose");
            return existing;
        }
        for (String localPath : LOCAL_COMPOSE_CANDIDATES) {
            File local = new File(localPath);
            if (!local.isFile()) {
                continue;
            }
            ssh.ensureRemoteDir("/usr/local/bin");
            ssh.uploadFile(local.getAbsolutePath(), REMOTE_COMPOSE_BIN);
            ssh.exec("chmod +x " + REMOTE_COMPOSE_BIN, 10000);
            NodeMediaRemoteDeployRespVO.DeployStep after = probeRemoteComposeStatus(ssh);
            if ("success".equals(after.getStatus())) {
                after.setName("Docker Compose");
                after.setOutput("已同步 docker-compose 至 " + REMOTE_COMPOSE_BIN);
                return after;
            }
        }
        NodeMediaRemoteDeployRespVO.DeployStep step = new NodeMediaRemoteDeployRespVO.DeployStep();
        step.setName("Docker Compose");
        step.setStatus("failed");
        step.setOutput("未找到可用的 Docker Compose");
        return step;
    }

    private NodeMediaRemoteDeployRespVO.DeployStep verifyServices(SshSessionHelper ssh, ComputeNodeDO node)
            throws Exception {
        NodeMediaRemoteDeployRespVO.DeployStep emqx = probeEmqxStatus(ssh, node);
        emqx.setName("服务验证");
        return emqx;
    }

    private String resolveMqttClusterSource() {
        if (mqttClusterSourcePath != null && !mqttClusterSourcePath.isBlank()) {
            File dir = new File(mqttClusterSourcePath);
            if (dir.isDirectory()) {
                return dir.getAbsolutePath();
            }
        }
        String[] candidates = {
                "/opt/easyaiot/.scripts/mqtt-cluster",
                System.getProperty("user.dir") + "/.scripts/mqtt-cluster",
                System.getProperty("user.dir") + "/../.scripts/mqtt-cluster",
        };
        for (String path : candidates) {
            File check = new File(path, "install_mqtt_stack.sh");
            if (check.isFile()) {
                return new File(path).getAbsolutePath();
            }
        }
        throw exception(MQTT_CLUSTER_SOURCE_NOT_FOUND);
    }

    private ComputeNodeDO requireComputeNode(Long nodeId) {
        ComputeNodeDO node = computeNodeMapper.selectById(nodeId);
        if (node == null) {
            throw exception(COMPUTE_NODE_NOT_EXISTS);
        }
        return node;
    }

    private void validateMqttRole(ComputeNodeDO node) {
        if (!MqttStackDeployUtil.isMqttRole(node.getNodeRole())) {
            throw exception(MQTT_NODE_ROLE_INVALID);
        }
    }

    private JSONObject callAgent(ComputeNodeDO node, String path, Map<String, Object> body) {
        String url = "http://" + node.getHost() + ":" + node.getAgentPort() + path;
        HttpResponse response = HttpRequest.post(url)
                .header("X-Agent-Token", node.getAgentToken())
                .body(JSONUtil.toJsonStr(body))
                .timeout(120000)
                .execute();
        JSONObject json = JSONUtil.parseObj(response.body());
        if (json.getInt("code", 1) != 0) {
            throw new IllegalStateException(json.getStr("msg", "Agent 调用失败"));
        }
        return json.getJSONObject("data") != null ? json.getJSONObject("data") : new JSONObject();
    }

    private static final class NodeSshCredential {
        private final NodeSshCredentialDO credential;
        private final String password;
        private final String privateKey;

        private NodeSshCredential(NodeSshCredentialDO credential, String password, String privateKey) {
            this.credential = credential;
            this.password = password;
            this.privateKey = privateKey;
        }
    }

    private static final class ExistingEmqxCheck {
        private NodeMediaRemoteDeployRespVO.DeployStep step;
        private boolean running;
    }

    private NodeSshCredential loadSshCredential(Long nodeId) {
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
        return new NodeSshCredential(credential, password, privateKey);
    }

    private SshSessionHelper openSshSession(ComputeNodeDO node, NodeSshCredential credential, int sshPort)
            throws Exception {
        return SshSessionHelper.connect(
                node.getHost(),
                sshPort,
                credential.credential.getUsername(),
                credential.credential.getAuthType(),
                credential.password,
                credential.privateKey);
    }

    private SshSessionHelper.SshExecResult execRemoteScript(SshSessionHelper ssh, String scriptBody, int timeoutMs)
            throws Exception {
        String encoded = Base64.getEncoder().encodeToString(scriptBody.getBytes(StandardCharsets.UTF_8));
        String tmpScript = "/tmp/easyaiot-mqtt-op-" + System.currentTimeMillis() + ".sh";
        return ssh.exec(
                "echo " + encoded + " | base64 -d > " + tmpScript
                        + " && chmod +x " + tmpScript
                        + " && bash " + tmpScript
                        + " ; rm -f " + tmpScript,
                timeoutMs);
    }

    private NodeMediaRemoteDeployRespVO buildSshFailure(
            NodeMediaRemoteDeployRespVO resp,
            List<NodeMediaRemoteDeployRespVO.DeployStep> steps,
            ComputeNodeDO node,
            int sshPort,
            String stepName,
            Exception e) {
        log.error("MQTT 栈 SSH 操作失败 nodeId={} host={}:{} step={}",
                node.getId(), node.getHost(), sshPort, stepName, e);
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

    private NodeMediaRemoteDeployRespVO.DeployStep runStep(String name, String status, String output) {
        NodeMediaRemoteDeployRespVO.DeployStep step = new NodeMediaRemoteDeployRespVO.DeployStep();
        step.setName(name);
        step.setStatus(status);
        step.setOutput(output);
        return step;
    }

    private String trimOutput(String text, int maxLen) {
        if (text == null) {
            return "";
        }
        String trimmed = text.trim();
        if (trimmed.length() <= maxLen) {
            return trimmed;
        }
        return trimmed.substring(0, maxLen) + "\n... (输出已截断)";
    }

    private static String formatBytes(long bytes) {
        if (bytes < 1024) {
            return bytes + " B";
        }
        if (bytes < 1024 * 1024) {
            return String.format("%.1f KB", bytes / 1024.0);
        }
        if (bytes < 1024L * 1024 * 1024) {
            return String.format("%.1f MB", bytes / 1024.0 / 1024.0);
        }
        return String.format("%.2f GB", bytes / 1024.0 / 1024.0 / 1024.0);
    }

}
