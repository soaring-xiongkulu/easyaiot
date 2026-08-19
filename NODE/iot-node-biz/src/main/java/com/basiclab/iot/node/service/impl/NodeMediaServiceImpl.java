package com.basiclab.iot.node.service.impl;

import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.node.dal.dataobject.ComputeNodeDO;
import com.basiclab.iot.node.dal.dataobject.DeviceMediaBindingDO;
import com.basiclab.iot.node.dal.dataobject.NodeSshCredentialDO;
import com.basiclab.iot.node.dal.pgsql.ComputeNodeMapper;
import com.basiclab.iot.node.dal.pgsql.DeviceMediaBindingMapper;
import com.basiclab.iot.node.dal.pgsql.NodeSshCredentialMapper;
import com.basiclab.iot.node.domain.vo.DeviceMediaBindingRespVO;
import cn.hutool.http.HttpRequest;
import cn.hutool.http.HttpResponse;
import cn.hutool.json.JSONObject;
import cn.hutool.json.JSONUtil;
import com.basiclab.iot.node.domain.vo.NodeMediaAllocateReqVO;
import com.basiclab.iot.node.domain.vo.NodeMediaDeployReqVO;
import com.basiclab.iot.node.domain.vo.NodeMediaRemoteDeployRespVO;
import com.basiclab.iot.node.domain.vo.NodeMediaStackCheckRespVO;
import com.basiclab.iot.node.domain.vo.NodePortCheckRespVO;
import com.basiclab.iot.node.domain.vo.NodeSchedulerAllocateReqVO;
import com.basiclab.iot.node.domain.vo.NodeSchedulerAllocateRespVO;
import com.basiclab.iot.node.enums.NodeRoleEnum;
import com.basiclab.iot.node.enums.NodeStatusEnum;
import com.basiclab.iot.node.service.ControlPlaneEndpointResolver;
import com.basiclab.iot.node.service.NodeMediaService;
import com.basiclab.iot.node.service.NodeSchedulerService;
import com.basiclab.iot.node.util.CredentialEncryptUtil;
import com.basiclab.iot.node.util.MediaStackDeployUtil;
import com.basiclab.iot.node.util.MediaStackDeployUtil.DeployPhase;
import com.basiclab.iot.node.util.MediaUrlBuilder;
import com.basiclab.iot.node.util.RemotePortCheckUtil;
import com.basiclab.iot.node.util.SshSessionHelper;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.validation.annotation.Validated;

import javax.annotation.Resource;
import java.io.File;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Base64;
import java.util.Arrays;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import java.util.regex.Pattern;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.COMPUTE_NODE_NOT_EXISTS;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.COMPUTE_NODE_OFFLINE;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.MEDIA_BINDING_NOT_EXISTS;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.MEDIA_CLUSTER_SOURCE_NOT_FOUND;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.SSH_CREDENTIAL_NOT_EXISTS;

@Slf4j
@Service
@Validated
public class NodeMediaServiceImpl implements NodeMediaService {

    private static final int DOCKER_INSTALL_TIMEOUT_MS = 900000;
    private static final int EXPORT_TIMEOUT_MS = 1800000;
    private static final String SRS_DOCKER_IMAGE = "ossrs/srs:5";
    private static final String ZLM_DOCKER_IMAGE = "zlmediakit/zlmediakit:master";
    private static final String SRS_IMAGE_TAR = "ossrs-srs-5.tar";
    private static final String ZLM_IMAGE_TAR = "zlmediakit-master.tar";
    private static final String[] REQUIRED_IMAGE_TARS = {
            SRS_IMAGE_TAR,
            ZLM_IMAGE_TAR,
    };
    private static final String[] SYNC_RELATIVE_FILES = {
            "install_media_stack.sh",
            "install_docker.sh",
            "docker-compose.media-node.yml",
            "srs/cluster.conf.template",
            "zlm/config.ini.template",
    };
    private static final String DEFAULT_ZLM_SECRET = "EasyAIoT_Media_Secret";
    private static final Pattern MEDIA_API_SUCCESS_CODE = Pattern.compile("\"code\"\\s*:\\s*0\\b");
    private static final String REMOTE_COMPOSE_BIN = "/usr/local/bin/docker-compose";
    private static final String[] LOCAL_COMPOSE_CANDIDATES = {
            "/usr/local/bin/docker-compose",
            "/usr/bin/docker-compose",
            "/usr/libexec/docker/cli-plugins/docker-compose",
            "/usr/lib/docker/cli-plugins/docker-compose",
    };

    private static final String WORKLOAD_SRS_LIVE = "srs_live";
    private static final String WORKLOAD_SRS_AI = "srs_ai";
    private static final String WORKLOAD_ZLM = "zlm";

    @Resource
    private DeviceMediaBindingMapper deviceMediaBindingMapper;
    @Resource
    private ComputeNodeMapper computeNodeMapper;
    @Resource
    private NodeSchedulerService nodeSchedulerService;
    @Resource
    private NodeSshCredentialMapper nodeSshCredentialMapper;
    @Resource
    private ControlPlaneEndpointResolver controlPlaneEndpointResolver;

    @Value("${easyaiot.media.cluster-source-path:}")
    private String mediaClusterSourcePath;
    @Value("${easyaiot.media.docker-compose-path:}")
    private String mediaDockerComposePath;

    @Override
    @Transactional(rollbackFor = Exception.class)
    public DeviceMediaBindingRespVO allocate(NodeMediaAllocateReqVO reqVO) {
        boolean needSrsLive = reqVO.getNeedSrsLive() == null || Boolean.TRUE.equals(reqVO.getNeedSrsLive());
        boolean needSrsAi = reqVO.getNeedSrsAi() == null || Boolean.TRUE.equals(reqVO.getNeedSrsAi());
        boolean needZlm = Boolean.TRUE.equals(reqVO.getNeedZlm());

        DeviceMediaBindingDO existing = deviceMediaBindingMapper.selectByDeviceId(reqVO.getDeviceId());
        if (existing != null && "active".equals(existing.getStatus()) && bindingNodesOnline(existing)) {
            return toResp(existing);
        }

        ComputeNodeDO srsLiveNode = null;
        ComputeNodeDO srsAiNode = null;
        ComputeNodeDO zlmNode = null;
        Long srsLiveNodeId = null;
        Long srsAiNodeId = null;
        Long zlmNodeId = null;

        if (needSrsLive) {
            NodeSchedulerAllocateRespVO live = allocateMediaNode(WORKLOAD_SRS_LIVE, reqVO.getDeviceId(),
                    List.of("srs_live"), reqVO.getRegion());
            srsLiveNodeId = live.getNodeId();
            srsLiveNode = computeNodeMapper.selectById(srsLiveNodeId);
        }
        if (needSrsAi) {
            NodeSchedulerAllocateRespVO ai = allocateMediaNode(WORKLOAD_SRS_AI, reqVO.getDeviceId(),
                    List.of("srs_ai"), reqVO.getRegion());
            srsAiNodeId = ai.getNodeId();
            srsAiNode = computeNodeMapper.selectById(srsAiNodeId);
        }
        if (needZlm) {
            NodeSchedulerAllocateRespVO zlm = allocateMediaNode(WORKLOAD_ZLM, reqVO.getDeviceId(),
                    List.of("zlm"), reqVO.getRegion());
            zlmNodeId = zlm.getNodeId();
            zlmNode = computeNodeMapper.selectById(zlmNodeId);
        }

        MediaUrlBuilder.StreamUrls urls = MediaUrlBuilder.build(
                srsLiveNode, srsAiNode, zlmNode, reqVO.getDeviceId(), reqVO.getHttpPlayHost());

        DeviceMediaBindingDO binding = existing != null ? existing : new DeviceMediaBindingDO();
        binding.setDeviceId(reqVO.getDeviceId());
        binding.setSrsLiveNodeId(srsLiveNodeId);
        binding.setSrsAiNodeId(srsAiNodeId);
        binding.setZlmNodeId(zlmNodeId);
        binding.setRtmpStream(urls.getRtmpStream());
        binding.setHttpStream(urls.getHttpStream());
        binding.setAiRtmpStream(urls.getAiRtmpStream());
        binding.setAiHttpStream(urls.getAiHttpStream());
        binding.setZlmHost(urls.getZlmHost());
        binding.setZlmHttpPort(urls.getZlmHttpPort());
        binding.setZlmRtmpPort(urls.getZlmRtmpPort());
        binding.setRegion(reqVO.getRegion());
        binding.setStatus("active");

        if (binding.getId() == null) {
            deviceMediaBindingMapper.insert(binding);
        } else {
            deviceMediaBindingMapper.updateById(binding);
        }
        return toResp(binding);
    }

    @Override
    public DeviceMediaBindingRespVO getBinding(String deviceId) {
        DeviceMediaBindingDO binding = deviceMediaBindingMapper.selectByDeviceId(deviceId);
        if (binding == null) {
            throw exception(MEDIA_BINDING_NOT_EXISTS);
        }
        return toResp(binding);
    }

    @Override
    public Map<String, Object> deployMediaStack(NodeMediaDeployReqVO reqVO) {
        ComputeNodeDO node = computeNodeMapper.selectById(reqVO.getNodeId());
        if (node == null) {
            throw exception(COMPUTE_NODE_NOT_EXISTS);
        }
        if (!NodeStatusEnum.ONLINE.getStatus().equals(node.getStatus())) {
            throw exception(COMPUTE_NODE_OFFLINE);
        }
        Map<String, String> env = MediaStackDeployUtil.buildDeployEnvMap(
                node,
                controlPlaneEndpointResolver.resolveHookHost(),
                controlPlaneEndpointResolver.resolveHookPort(),
                controlPlaneEndpointResolver.resolveHookPathPrefix());
        if (reqVO.getEnv() != null && !reqVO.getEnv().isEmpty()) {
            env.putAll(reqVO.getEnv());
        }
        Map<String, Object> body = new HashMap<>();
        body.put("stackType", reqVO.getStackType());
        body.put("nodeId", String.valueOf(node.getId()));
        body.put("env", env);
        JSONObject result = callAgent(node, "/media/deploy", body);
        Map<String, Object> resp = new HashMap<>();
        resp.put("nodeId", node.getId());
        resp.put("stackType", reqVO.getStackType());
        resp.put("status", result.getStr("status", "running"));
        return resp;
    }

    @Override
    public NodeMediaRemoteDeployRespVO deployMediaStackBySsh(Long nodeId) {
        ComputeNodeDO node = computeNodeMapper.selectById(nodeId);
        if (node == null) {
            throw exception(COMPUTE_NODE_NOT_EXISTS);
        }
        if (!NodeRoleEnum.MEDIA.getRole().equals(node.getNodeRole())
                && !NodeRoleEnum.HYBRID.getRole().equals(node.getNodeRole())) {
            throw new IllegalStateException("仅 media / hybrid 节点支持媒体栈 SSH 部署");
        }
        NodeSshCredential sshCredential = loadSshCredential(nodeId);

        NodeMediaRemoteDeployRespVO resp = new NodeMediaRemoteDeployRespVO();
        List<NodeMediaRemoteDeployRespVO.DeployStep> steps = new ArrayList<>();
        resp.setSteps(steps);

        int sshPort = ComputeNodeServiceImpl.resolveSshPort(node);
        String sourceRoot = resolveMediaClusterSource();

        try (SshSessionHelper ssh = openSshSession(node, sshCredential, sshPort)) {

            steps.add(runStep("SSH 连接", "success", "已连接 " + node.getHost() + ":" + sshPort));

            NodePortCheckRespVO portCheck = checkMediaPortsOnSession(ssh, node);
            steps.add(portCheck.getSteps().get(0));
            if (!Boolean.TRUE.equals(portCheck.getPortsReady())) {
                resp.setSuccess(false);
                resp.setMessage(portCheck.getMessage());
                return resp;
            }

            ExistingMediaCheck existingCheck = checkExistingMediaServices(ssh, node);
            steps.add(existingCheck.step);
            if (existingCheck.srsRunning && existingCheck.zlmRunning) {
                NodeMediaRemoteDeployRespVO.DeployStep verifyStep = verifyServices(ssh, node);
                steps.add(verifyStep);
                resp.setSuccess("success".equals(verifyStep.getStatus()));
                resp.setMessage("SRS 与 ZLMediaKit 均已运行，无需重复部署");
                return resp;
            }

            RemoteImageProbe remoteImages = probeRemoteDockerImages(ssh);
            boolean needSrsTar = !remoteImages.srsImagePresent;
            boolean needZlmTar = !remoteImages.zlmImagePresent;

            NodeMediaRemoteDeployRespVO.DeployStep localImagesStep =
                    ensureLocalMediaImages(sourceRoot, needSrsTar, needZlmTar);
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

            NodeMediaRemoteDeployRespVO.DeployStep cleanStep = removeRemoteMediaCluster(ssh);
            steps.add(cleanStep);
            if (!"success".equals(cleanStep.getStatus())) {
                resp.setSuccess(false);
                resp.setMessage("清理目标机旧目录失败");
                return resp;
            }

            NodeMediaRemoteDeployRespVO.DeployStep syncStep = syncMediaCluster(ssh, sourceRoot, remoteImages);
            steps.add(syncStep);
            if (!"success".equals(syncStep.getStatus())) {
                resp.setSuccess(false);
                resp.setMessage("media-cluster 同步失败");
                return resp;
            }

            NodeMediaRemoteDeployRespVO.DeployStep composeStep = ensureRemoteDockerCompose(ssh);
            steps.add(composeStep);
            if (!"success".equals(composeStep.getStatus())) {
                resp.setSuccess(false);
                resp.setMessage("Docker Compose 未就绪");
                return resp;
            }

            if (needSrsTar || needZlmTar) {
                NodeMediaRemoteDeployRespVO.DeployStep importStep = runRemoteDeployPhase(
                        ssh, node, DeployPhase.PREPARE_IMAGES, "导入镜像", 600000);
                steps.add(importStep);
                if (!"success".equals(importStep.getStatus())) {
                    resp.setSuccess(false);
                    resp.setMessage("镜像导入失败");
                    return resp;
                }
            } else {
                steps.add(runStep("导入镜像", "skipped", "目标机已有 SRS / ZLM Docker 镜像，跳过 docker load"));
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
            resp.setMessage(ok ? "媒体栈部署完成" : "部署完成但服务验证未通过");
            return resp;
        } catch (Exception e) {
            log.error("媒体栈 SSH 部署失败 nodeId={} host={}:{}", nodeId, node.getHost(), sshPort, e);
            NodeMediaRemoteDeployRespVO.DeployStep fail = new NodeMediaRemoteDeployRespVO.DeployStep();
            fail.setName(steps.isEmpty() ? "SSH 连接" : "部署中断");
            fail.setStatus("failed");
            String detail = e.getMessage() != null ? e.getMessage() : e.getClass().getSimpleName();
            fail.setOutput("连接 " + node.getHost() + ":" + sshPort + " 失败: " + detail
                    + (sshPort == 22 ? "（若 SSH 非默认 22 端口，请在节点配置中填写正确端口并保存）" : ""));
            steps.add(fail);
            resp.setSuccess(false);
            resp.setMessage(fail.getOutput());
            return resp;
        }
    }

    @Override
    public NodeMediaRemoteDeployRespVO stopMediaServiceBySsh(Long nodeId, String service) {
        validateMediaNodeRole(nodeId);
        String normalized = normalizeMediaService(service);
        ComputeNodeDO node = requireComputeNode(nodeId);
        NodeSshCredential credential = loadSshCredential(nodeId);
        int sshPort = ComputeNodeServiceImpl.resolveSshPort(node);
        String nodeName = MediaStackDeployUtil.sanitizeNodeName(node.getName(), node.getHost());
        String label = "srs".equals(normalized) ? "SRS" : "ZLMediaKit";

        NodeMediaRemoteDeployRespVO resp = new NodeMediaRemoteDeployRespVO();
        List<NodeMediaRemoteDeployRespVO.DeployStep> steps = new ArrayList<>();
        resp.setSteps(steps);

        try (SshSessionHelper ssh = openSshSession(node, credential, sshPort)) {
            steps.add(runStep("SSH 连接", "success", "已连接 " + node.getHost() + ":" + sshPort));

            String remoteScript = buildMediaComposeScript(nodeName,
                    "stop_" + normalized,
                    "print_step() { echo \">>> $*\"; }\n"
                            + "print_ok() { echo \"[OK] $*\"; }\n"
                            + "REMOTE_ROOT=\"" + MediaStackDeployUtil.remoteClusterRoot() + "\"\n"
                            + "if [[ -f \"${REMOTE_ROOT}/docker-compose.media-node.yml\" ]]; then\n"
                            + "  cd \"${REMOTE_ROOT}\"\n"
                            + "  if docker compose version >/dev/null 2>&1; then COMPOSE_CMD=\"docker compose\"; "
                            + "elif command -v docker-compose >/dev/null 2>&1; then COMPOSE_CMD=\"docker-compose\"; "
                            + "elif [[ -x /usr/local/bin/docker-compose ]]; then COMPOSE_CMD=\"/usr/local/bin/docker-compose\"; "
                            + "else echo \"[WARN] 未找到 compose，尝试 docker stop\"; COMPOSE_CMD=\"\"; fi\n"
                            + "  if [[ -n \"${COMPOSE_CMD}\" ]]; then\n"
                            + "    print_step \"停止 " + label + " 容器\"\n"
                            + "    ${COMPOSE_CMD} -f docker-compose.media-node.yml stop " + normalized + " 2>&1 || true\n"
                            + "  fi\n"
                            + "fi\n"
                            + "for cname in \"" + nodeName + "-" + normalized + "\" \"${MEDIA_NODE_ID:-}\"; do\n"
                            + "  if docker ps -a --format '{{.Names}}' | grep -qx \"${cname}\"; then\n"
                            + "    print_step \"停止容器 ${cname}\"\n"
                            + "    docker stop \"${cname}\" 2>&1 || true\n"
                            + "    print_ok \"已停止 ${cname}\"\n"
                            + "  fi\n"
                            + "done\n"
                            + "echo STOP_OK");
            SshSessionHelper.SshExecResult result = execRemoteScript(ssh, remoteScript, 120000);
            NodeMediaRemoteDeployRespVO.DeployStep step = new NodeMediaRemoteDeployRespVO.DeployStep();
            step.setName("停止 " + label);
            step.setOutput(trimOutput(result.combinedOutput(), 4000));
            boolean ok = result.isSuccess() && result.combinedOutput().contains("STOP_OK");
            step.setStatus(ok ? "success" : "failed");
            steps.add(step);
            resp.setSuccess(ok);
            resp.setMessage(ok ? label + " 已停止" : label + " 停止失败");
            return resp;
        } catch (Exception e) {
            return buildSshFailure(resp, steps, node, sshPort, "停止 " + label, e);
        }
    }

    @Override
    public NodeMediaRemoteDeployRespVO removeMediaContainerBySsh(Long nodeId) {
        validateMediaNodeRole(nodeId);
        ComputeNodeDO node = requireComputeNode(nodeId);
        NodeSshCredential credential = loadSshCredential(nodeId);
        int sshPort = ComputeNodeServiceImpl.resolveSshPort(node);
        String nodeName = MediaStackDeployUtil.sanitizeNodeName(node.getName(), node.getHost());

        NodeMediaRemoteDeployRespVO resp = new NodeMediaRemoteDeployRespVO();
        List<NodeMediaRemoteDeployRespVO.DeployStep> steps = new ArrayList<>();
        resp.setSteps(steps);

        try (SshSessionHelper ssh = openSshSession(node, credential, sshPort)) {
            steps.add(runStep("SSH 连接", "success", "已连接 " + node.getHost() + ":" + sshPort));

            String remoteScript = buildMediaComposeScript(nodeName,
                    "remove_containers",
                    "print_step() { echo \">>> $*\"; }\n"
                            + "print_ok() { echo \"[OK] $*\"; }\n"
                            + "REMOTE_ROOT=\"" + MediaStackDeployUtil.remoteClusterRoot() + "\"\n"
                            + "if [[ -f \"${REMOTE_ROOT}/docker-compose.media-node.yml\" ]]; then\n"
                            + "  cd \"${REMOTE_ROOT}\"\n"
                            + "  if docker compose version >/dev/null 2>&1; then COMPOSE_CMD=\"docker compose\"; "
                            + "elif command -v docker-compose >/dev/null 2>&1; then COMPOSE_CMD=\"docker-compose\"; "
                            + "elif [[ -x /usr/local/bin/docker-compose ]]; then COMPOSE_CMD=\"/usr/local/bin/docker-compose\"; "
                            + "else COMPOSE_CMD=\"\"; fi\n"
                            + "  if [[ -n \"${COMPOSE_CMD}\" ]]; then\n"
                            + "    print_step \"停止并移除 SRS/ZLM 容器\"\n"
                            + "    ${COMPOSE_CMD} -f docker-compose.media-node.yml stop srs zlm 2>&1 || true\n"
                            + "    ${COMPOSE_CMD} -f docker-compose.media-node.yml rm -f srs zlm 2>&1 || true\n"
                            + "  fi\n"
                            + "fi\n"
                            + "for cname in \"" + nodeName + "-srs\" \"" + nodeName + "-zlm\"; do\n"
                            + "  if docker ps -a --format '{{.Names}}' | grep -qx \"${cname}\"; then\n"
                            + "    print_step \"删除容器 ${cname}\"\n"
                            + "    docker rm -f \"${cname}\" 2>&1 || true\n"
                            + "    print_ok \"已删除 ${cname}\"\n"
                            + "  else\n"
                            + "    echo \"[SKIP] 容器不存在: ${cname}\"\n"
                            + "  fi\n"
                            + "done\n"
                            + "echo REMOVE_CONTAINER_OK");
            SshSessionHelper.SshExecResult result = execRemoteScript(ssh, remoteScript, 180000);
            NodeMediaRemoteDeployRespVO.DeployStep step = new NodeMediaRemoteDeployRespVO.DeployStep();
            step.setName("删除容器");
            step.setOutput(trimOutput(result.combinedOutput(), 6000));
            boolean ok = result.isSuccess() && result.combinedOutput().contains("REMOVE_CONTAINER_OK");
            step.setStatus(ok ? "success" : "failed");
            steps.add(step);
            resp.setSuccess(ok);
            resp.setMessage(ok ? "SRS / ZLM 容器已删除" : "删除容器失败");
            return resp;
        } catch (Exception e) {
            return buildSshFailure(resp, steps, node, sshPort, "删除容器", e);
        }
    }

    @Override
    public NodeMediaRemoteDeployRespVO removeMediaImageBySsh(Long nodeId) {
        validateMediaNodeRole(nodeId);
        ComputeNodeDO node = requireComputeNode(nodeId);
        NodeSshCredential credential = loadSshCredential(nodeId);
        int sshPort = ComputeNodeServiceImpl.resolveSshPort(node);

        NodeMediaRemoteDeployRespVO resp = new NodeMediaRemoteDeployRespVO();
        List<NodeMediaRemoteDeployRespVO.DeployStep> steps = new ArrayList<>();
        resp.setSteps(steps);

        try (SshSessionHelper ssh = openSshSession(node, credential, sshPort)) {
            steps.add(runStep("SSH 连接", "success", "已连接 " + node.getHost() + ":" + sshPort));

            String remoteRoot = MediaStackDeployUtil.remoteClusterRoot();
            String remoteScript = buildMediaComposeScript("media",
                    "remove_images",
                    "print_step() { echo \">>> $*\"; }\n"
                            + "print_ok() { echo \"[OK] $*\"; }\n"
                            + "for img in \"" + SRS_DOCKER_IMAGE + "\" \"" + ZLM_DOCKER_IMAGE + "\"; do\n"
                            + "  if docker image inspect \"${img}\" >/dev/null 2>&1; then\n"
                            + "    print_step \"删除镜像 ${img}\"\n"
                            + "    docker rmi -f \"${img}\" 2>&1 || true\n"
                            + "    print_ok \"已删除 ${img}\"\n"
                            + "  else\n"
                            + "    echo \"[SKIP] 镜像不存在: ${img}\"\n"
                            + "  fi\n"
                            + "done\n"
                            + "for tar in \"" + remoteRoot + "/images/" + SRS_IMAGE_TAR + "\" "
                            + "\"" + remoteRoot + "/images/" + ZLM_IMAGE_TAR + "\"; do\n"
                            + "  if [[ -f \"${tar}\" ]]; then\n"
                            + "    print_step \"删除离线包 ${tar}\"\n"
                            + "    rm -f \"${tar}\" 2>&1 || true\n"
                            + "  fi\n"
                            + "done\n"
                            + "echo REMOVE_IMAGE_OK");
            SshSessionHelper.SshExecResult result = execRemoteScript(ssh, remoteScript, 180000);
            NodeMediaRemoteDeployRespVO.DeployStep step = new NodeMediaRemoteDeployRespVO.DeployStep();
            step.setName("删除镜像");
            step.setOutput(trimOutput(result.combinedOutput(), 6000));
            boolean ok = result.isSuccess() && result.combinedOutput().contains("REMOVE_IMAGE_OK");
            step.setStatus(ok ? "success" : "failed");
            steps.add(step);
            resp.setSuccess(ok);
            resp.setMessage(ok ? "SRS / ZLM Docker 镜像已删除" : "删除镜像失败");
            return resp;
        } catch (Exception e) {
            return buildSshFailure(resp, steps, node, sshPort, "删除镜像", e);
        }
    }

    @Override
    public NodePortCheckRespVO checkMediaPortsBySsh(Long nodeId) {
        ComputeNodeDO node = computeNodeMapper.selectById(nodeId);
        if (node == null) {
            throw exception(COMPUTE_NODE_NOT_EXISTS);
        }
        if (!NodeRoleEnum.MEDIA.getRole().equals(node.getNodeRole())
                && !NodeRoleEnum.HYBRID.getRole().equals(node.getNodeRole())) {
            throw new IllegalStateException("仅 media / hybrid 节点支持媒体栈端口检测");
        }
        NodeSshCredential credential = loadSshCredential(nodeId);
        int sshPort = ComputeNodeServiceImpl.resolveSshPort(node);

        NodePortCheckRespVO resp = new NodePortCheckRespVO();
        List<NodeMediaRemoteDeployRespVO.DeployStep> steps = new ArrayList<>();
        resp.setSteps(steps);

        try (SshSessionHelper ssh = openSshSession(node, credential, sshPort)) {
            steps.add(runStep("SSH 连接", "success", "已连接 " + node.getHost() + ":" + sshPort));
            NodePortCheckRespVO portCheck = checkMediaPortsOnSession(ssh, node);
            steps.addAll(portCheck.getSteps());
            resp.setPorts(portCheck.getPorts());
            resp.setPortsReady(portCheck.getPortsReady());
            resp.setSuccess(true);
            resp.setMessage(portCheck.getMessage());
            return resp;
        } catch (Exception e) {
            log.error("媒体栈端口检测失败 nodeId={} host={}:{}", nodeId, node.getHost(), sshPort, e);
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

    private NodePortCheckRespVO checkMediaPortsOnSession(SshSessionHelper ssh, ComputeNodeDO node) throws Exception {
        LinkedHashMap<String, Integer> portMap = RemotePortCheckUtil.mediaDeployPorts(node.getTags());
        return RemotePortCheckUtil.checkPorts(ssh, portMap);
    }

    @Override
    public NodeMediaStackCheckRespVO checkMediaStackBySsh(Long nodeId) {
        ComputeNodeDO node = computeNodeMapper.selectById(nodeId);
        if (node == null) {
            throw exception(COMPUTE_NODE_NOT_EXISTS);
        }
        if (!NodeRoleEnum.MEDIA.getRole().equals(node.getNodeRole())
                && !NodeRoleEnum.HYBRID.getRole().equals(node.getNodeRole())) {
            throw new IllegalStateException("仅 media / hybrid 节点支持媒体栈 SSH 检测");
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

        NodeMediaStackCheckRespVO resp = new NodeMediaStackCheckRespVO();
        List<NodeMediaRemoteDeployRespVO.DeployStep> steps = new ArrayList<>();
        resp.setSteps(steps);

        int sshPort = ComputeNodeServiceImpl.resolveSshPort(node);
        try (SshSessionHelper ssh = SshSessionHelper.connect(
                node.getHost(),
                sshPort,
                credential.getUsername(),
                credential.getAuthType(),
                password,
                privateKey)) {

            steps.add(runStep("SSH 连接", "success", "已连接 " + node.getHost() + ":" + sshPort));

            NodeMediaRemoteDeployRespVO.DeployStep dockerStep = probeRemoteDockerStatus(ssh);
            steps.add(dockerStep);
            resp.setDockerReady("success".equals(dockerStep.getStatus()));

            NodeMediaRemoteDeployRespVO.DeployStep composeStep = probeRemoteComposeStatus(ssh);
            steps.add(composeStep);
            resp.setComposeReady("success".equals(composeStep.getStatus()));

            NodeMediaRemoteDeployRespVO.DeployStep srsStep = probeSrsStatus(ssh, node);
            steps.add(srsStep);
            resp.setSrsRunning("success".equals(srsStep.getStatus()));

            NodeMediaRemoteDeployRespVO.DeployStep zlmStep = probeZlmStatus(ssh, node);
            steps.add(zlmStep);
            resp.setZlmRunning("success".equals(zlmStep.getStatus()));

            boolean deployed = Boolean.TRUE.equals(resp.getSrsRunning()) && Boolean.TRUE.equals(resp.getZlmRunning());
            resp.setDeployed(deployed);
            resp.setSuccess(true);
            resp.setMessage(buildMediaStackCheckMessage(resp, node));
            return resp;
        } catch (Exception e) {
            log.error("媒体栈 SSH 检测失败 nodeId={} host={}:{}", nodeId, node.getHost(), sshPort, e);
            NodeMediaRemoteDeployRespVO.DeployStep fail = new NodeMediaRemoteDeployRespVO.DeployStep();
            fail.setName(steps.isEmpty() ? "SSH 连接" : "检测中断");
            fail.setStatus("failed");
            String detail = e.getMessage() != null ? e.getMessage() : e.getClass().getSimpleName();
            fail.setOutput("连接 " + node.getHost() + ":" + sshPort + " 失败: " + detail);
            steps.add(fail);
            resp.setSuccess(false);
            resp.setDeployed(false);
            resp.setSrsRunning(false);
            resp.setZlmRunning(false);
            resp.setDockerReady(false);
            resp.setComposeReady(false);
            resp.setMessage(fail.getOutput());
            return resp;
        }
    }

    private String buildMediaStackCheckMessage(NodeMediaStackCheckRespVO resp, ComputeNodeDO node) {
        int srsApi = MediaStackDeployUtil.tagInt(node.getTags(), "srs_api_port", 1985);
        int zlmHttp = MediaStackDeployUtil.tagInt(node.getTags(), "zlm_http_port", 6080);
        if (Boolean.TRUE.equals(resp.getDeployed())) {
            return "流媒体栈已部署：SRS（API " + srsApi + "）与 ZLMediaKit（HTTP " + zlmHttp + "）均在运行";
        }
        if (Boolean.TRUE.equals(resp.getSrsRunning()) || Boolean.TRUE.equals(resp.getZlmRunning())) {
            StringBuilder sb = new StringBuilder("流媒体栈部分部署：");
            if (Boolean.TRUE.equals(resp.getSrsRunning())) {
                sb.append("SRS 已运行");
            }
            if (Boolean.TRUE.equals(resp.getZlmRunning())) {
                if (Boolean.TRUE.equals(resp.getSrsRunning())) {
                    sb.append("，");
                }
                sb.append("ZLMediaKit 已运行");
            }
            sb.append("。自动部署前请先停止已有服务，或手动补齐未运行的组件");
            return sb.toString();
        }
        return "未检测到运行中的 SRS / ZLMediaKit，目标机可进行全新部署";
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

    private NodeMediaRemoteDeployRespVO.DeployStep probeSrsStatus(SshSessionHelper ssh, ComputeNodeDO node)
            throws Exception {
        int srsApi = MediaStackDeployUtil.tagInt(node.getTags(), "srs_api_port", 1985);
        SshSessionHelper.SshExecResult result = ssh.exec(
                "body=$(curl -sf --connect-timeout 5 --max-time 10 http://127.0.0.1:" + srsApi
                        + "/api/v1/versions 2>/dev/null || true); "
                        + "if [ -n \"$body\" ] && echo \"$body\" | grep -qE '\"code\"[[:space:]]*:[[:space:]]*0' "
                        + "&& echo \"$body\" | grep -q '\"version\"'; then "
                        + "echo \"$body\"; echo SRS_RUNNING; "
                        + "else echo SRS_STOPPED; fi",
                15000);
        return buildMediaServiceProbeStep("SRS", result.combinedOutput(), "SRS_RUNNING", srsApi, "API");
    }

    private NodeMediaRemoteDeployRespVO.DeployStep probeZlmStatus(SshSessionHelper ssh, ComputeNodeDO node)
            throws Exception {
        int zlmHttp = MediaStackDeployUtil.tagInt(node.getTags(), "zlm_http_port", 6080);
        String remoteRoot = MediaStackDeployUtil.remoteClusterRoot();
        SshSessionHelper.SshExecResult result = ssh.exec(
                "zlm_secret=$(grep -E '^[[:space:]]*secret=' \"" + remoteRoot + "/zlm/config.ini\" 2>/dev/null "
                        + "| head -1 | sed 's/^[[:space:]]*secret=//'); "
                        + "zlm_secret=${zlm_secret:-" + DEFAULT_ZLM_SECRET + "}; "
                        + "body=$(curl -s --connect-timeout 5 --max-time 10 "
                        + "\"http://127.0.0.1:" + zlmHttp + "/index/api/getServerConfig?secret=${zlm_secret}\" "
                        + "2>/dev/null || true); "
                        + "if [ -n \"$body\" ] && echo \"$body\" | grep -qE '\"code\"[[:space:]]*:[[:space:]]*0'; then "
                        + "echo \"$body\" | head -c 280; echo; echo ZLM_RUNNING; "
                        + "elif [ -n \"$body\" ]; then echo \"$body\" | head -c 280; echo; echo ZLM_STOPPED; "
                        + "else echo ZLM_STOPPED; fi",
                15000);
        return buildMediaServiceProbeStep("ZLMediaKit", result.combinedOutput(), "ZLM_RUNNING", zlmHttp, "HTTP");
    }

    private NodeMediaRemoteDeployRespVO.DeployStep buildMediaServiceProbeStep(
            String serviceName, String output, String runningToken, int port, String portLabel) {
        boolean running = output != null && output.contains(runningToken);
        String detail = extractMediaProbeDetail(output, runningToken);
        if (running && !isValidMediaServiceBody(serviceName, detail)) {
            running = false;
        }
        NodeMediaRemoteDeployRespVO.DeployStep step = new NodeMediaRemoteDeployRespVO.DeployStep();
        step.setName(serviceName);
        if (running) {
            step.setStatus("success");
            step.setOutput(serviceName + " 已在运行（" + portLabel + " " + port + "）"
                    + (detail.isBlank() ? "" : "\n" + trimOutput(detail, 500)));
            return step;
        }
        step.setStatus("failed");
        if (!detail.isBlank()) {
            step.setOutput(serviceName + " 未运行（" + portLabel + " " + port + " 无有效 API 响应）\n"
                    + trimOutput(detail, 500));
        } else {
            step.setOutput(serviceName + " 未运行（" + portLabel + " " + port
                    + " 无响应；端口占用不代表 API 可用，请确认进程为 ZLM 且 config.ini 中 secret/端口正确）");
        }
        return step;
    }

    private static String extractMediaProbeDetail(String output, String runningToken) {
        if (output == null) {
            return "";
        }
        return output
                .replace(runningToken, "")
                .replace("SRS_STOPPED", "")
                .replace("ZLM_STOPPED", "")
                .trim();
    }

    private boolean isValidMediaServiceBody(String serviceName, String body) {
        if (body == null || body.isBlank()) {
            return false;
        }
        if (!body.contains("\"code\"")) {
            return false;
        }
        if ("SRS".equals(serviceName)) {
            return body.contains("\"version\"") && MEDIA_API_SUCCESS_CODE.matcher(body).find();
        }
        if ("ZLMediaKit".equals(serviceName)) {
            return MEDIA_API_SUCCESS_CODE.matcher(body).find();
        }
        return true;
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

    private static final class RemoteImageProbe {
        private boolean srsImagePresent;
        private boolean zlmImagePresent;
    }

    private void validateMediaNodeRole(Long nodeId) {
        ComputeNodeDO node = computeNodeMapper.selectById(nodeId);
        if (node == null) {
            throw exception(COMPUTE_NODE_NOT_EXISTS);
        }
        if (!NodeRoleEnum.MEDIA.getRole().equals(node.getNodeRole())
                && !NodeRoleEnum.HYBRID.getRole().equals(node.getNodeRole())) {
            throw new IllegalStateException("仅 media / hybrid 节点支持媒体栈 SSH 操作");
        }
    }

    private ComputeNodeDO requireComputeNode(Long nodeId) {
        ComputeNodeDO node = computeNodeMapper.selectById(nodeId);
        if (node == null) {
            throw exception(COMPUTE_NODE_NOT_EXISTS);
        }
        return node;
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

    private String normalizeMediaService(String service) {
        if (service == null) {
            throw new IllegalArgumentException("service 不能为空");
        }
        String normalized = service.trim().toLowerCase(Locale.ROOT);
        if ("srs".equals(normalized) || "zlm".equals(normalized)) {
            return normalized;
        }
        throw new IllegalArgumentException("service 仅支持 srs 或 zlm");
    }

    private RemoteImageProbe probeRemoteDockerImages(SshSessionHelper ssh) throws Exception {
        SshSessionHelper.SshExecResult result = ssh.exec(
                "docker image inspect " + SRS_DOCKER_IMAGE + " >/dev/null 2>&1 && echo SRS_IMG_OK || echo SRS_IMG_MISSING; "
                        + "docker image inspect " + ZLM_DOCKER_IMAGE + " >/dev/null 2>&1 && echo ZLM_IMG_OK || echo ZLM_IMG_MISSING",
                30000);
        String out = result.combinedOutput();
        RemoteImageProbe probe = new RemoteImageProbe();
        probe.srsImagePresent = out.contains("SRS_IMG_OK");
        probe.zlmImagePresent = out.contains("ZLM_IMG_OK");
        return probe;
    }

    private boolean remoteTarMatches(SshSessionHelper ssh, String tarName, long localSize) throws Exception {
        String remotePath = MediaStackDeployUtil.remoteClusterRoot() + "/images/" + tarName;
        SshSessionHelper.SshExecResult result = ssh.exec(
                "if [ -f \"" + remotePath + "\" ]; then stat -c%s \"" + remotePath + "\"; else echo MISSING; fi",
                30000);
        String out = result.combinedOutput().trim();
        if (!result.isSuccess() || out.contains("MISSING")) {
            return false;
        }
        String sizeLine = out.split("\n")[0].trim();
        try {
            return Long.parseLong(sizeLine) == localSize;
        } catch (NumberFormatException ignored) {
            return false;
        }
    }

    private boolean shouldSkipImageTarSync(RemoteImageProbe remoteImages, String tarName) {
        if (SRS_IMAGE_TAR.equals(tarName)) {
            return remoteImages.srsImagePresent;
        }
        if (ZLM_IMAGE_TAR.equals(tarName)) {
            return remoteImages.zlmImagePresent;
        }
        return false;
    }

    private SshSessionHelper.SshExecResult execRemoteScript(SshSessionHelper ssh, String scriptBody, int timeoutMs)
            throws Exception {
        String encoded = Base64.getEncoder().encodeToString(scriptBody.getBytes(StandardCharsets.UTF_8));
        String tmpScript = "/tmp/easyaiot-media-op-" + System.currentTimeMillis() + ".sh";
        return ssh.exec(
                "echo " + encoded + " | base64 -d > " + tmpScript
                        + " && chmod +x " + tmpScript
                        + " && bash " + tmpScript
                        + " ; rm -f " + tmpScript,
                timeoutMs);
    }

    private String buildMediaComposeScript(String nodeName, String suffix, String body) {
        return "#!/usr/bin/env bash\n"
                + "set -euo pipefail\n"
                + "export MEDIA_NODE_NAME=\"" + nodeName + "\"\n"
                + body;
    }

    private NodeMediaRemoteDeployRespVO buildSshFailure(
            NodeMediaRemoteDeployRespVO resp,
            List<NodeMediaRemoteDeployRespVO.DeployStep> steps,
            ComputeNodeDO node,
            int sshPort,
            String stepName,
            Exception e) {
        log.error("媒体栈 SSH 操作失败 nodeId={} host={}:{} step={}",
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

    private NodeMediaRemoteDeployRespVO.DeployStep ensureLocalMediaImages(
            String sourceRoot, boolean needSrsTar, boolean needZlmTar) {
        if (!needSrsTar && !needZlmTar) {
            return runStep("准备离线镜像", "skipped", "目标机已有全部 Docker 镜像，跳过本机导出");
        }

        File imagesDir = new File(sourceRoot, "images");
        List<String> requiredTars = new ArrayList<>();
        if (needSrsTar) {
            requiredTars.add(SRS_IMAGE_TAR);
        }
        if (needZlmTar) {
            requiredTars.add(ZLM_IMAGE_TAR);
        }
        List<String> missing = listMissingImageTars(imagesDir, requiredTars);
        if (missing.isEmpty()) {
            return runStep("准备离线镜像", "success",
                    "本机离线镜像包已就绪（仅同步目标机缺失项）\n" + describeImageTars(imagesDir, requiredTars));
        }

        NodeMediaRemoteDeployRespVO.DeployStep step = new NodeMediaRemoteDeployRespVO.DeployStep();
        step.setName("准备离线镜像");

        File exportScript = new File(sourceRoot, "export_media_images.sh");
        if (!exportScript.isFile()) {
            step.setStatus("failed");
            step.setOutput("缺少离线镜像包: " + String.join(", ", missing)
                    + "；且未找到 export_media_images.sh，请在本机拉取并 docker save 导出后重试");
            return step;
        }

        try {
            String exportOutput = runExportMediaImagesScript(exportScript);
            missing = listMissingImageTars(imagesDir, requiredTars);
            if (!missing.isEmpty()) {
                step.setStatus("failed");
                step.setOutput("本机导出未完成，仍缺少: " + String.join(", ", missing) + "\n"
                        + trimOutput(exportOutput, 4000));
                return step;
            }
            step.setStatus("success");
            step.setOutput("本机已导出缺失的离线镜像\n" + describeImageTars(imagesDir, requiredTars)
                    + (exportOutput.isBlank() ? "" : "\n" + trimOutput(exportOutput, 3000)));
            return step;
        } catch (Exception e) {
            log.error("本机导出媒体镜像失败 sourceRoot={}", sourceRoot, e);
            step.setStatus("failed");
            step.setOutput("本机导出镜像失败: " + e.getMessage());
            return step;
        }
    }

    private List<String> listMissingImageTars(File imagesDir, List<String> requiredTars) {
        List<String> missing = new ArrayList<>();
        for (String name : requiredTars) {
            File tar = new File(imagesDir, name);
            if (!tar.isFile() || tar.length() == 0) {
                missing.add(name);
            }
        }
        return missing;
    }

    private String describeImageTars(File imagesDir, List<String> requiredTars) {
        StringBuilder sb = new StringBuilder("离线镜像包就绪，将通过文件同步至目标机（目标机不联网拉取）:\n");
        long total = 0;
        for (String name : requiredTars) {
            File tar = new File(imagesDir, name);
            if (tar.isFile()) {
                sb.append("  ").append(name).append(" (").append(formatBytes(tar.length())).append(")\n");
                total += tar.length();
            }
        }
        sb.append("合计 ").append(formatBytes(total));
        return sb.toString().trim();
    }

    private String runExportMediaImagesScript(File exportScript) throws Exception {
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
                    ? "export_media_images.sh 退出码 " + process.exitValue()
                    : output.trim());
        }
        return output;
    }

    private NodeMediaRemoteDeployRespVO.DeployStep runRemoteDeployPhase(
            SshSessionHelper ssh, ComputeNodeDO node, DeployPhase phase, String stepName, int timeoutMs)
            throws Exception {
        String remoteScript = MediaStackDeployUtil.buildDeployScript(
                node,
                controlPlaneEndpointResolver.resolveHookHost(),
                controlPlaneEndpointResolver.resolveHookPort(),
                controlPlaneEndpointResolver.resolveHookPathPrefix(),
                phase);
        String encoded = Base64.getEncoder().encodeToString(remoteScript.getBytes(StandardCharsets.UTF_8));
        String tmpScript = "/tmp/easyaiot-media-" + phase.name().toLowerCase(Locale.ROOT) + ".sh";
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

    private NodeMediaRemoteDeployRespVO.DeployStep removeRemoteMediaCluster(SshSessionHelper ssh)
            throws Exception {
        String remoteRoot = MediaStackDeployUtil.remoteClusterRoot();
        SshSessionHelper.SshExecResult result = ssh.exec(
                "if [ -d \"" + remoteRoot + "\" ]; then "
                        + "rm -rf \"" + remoteRoot + "/srs\" \"" + remoteRoot + "/zlm\" 2>/dev/null; "
                        + "rm -f \"" + remoteRoot + "/install_media_stack.sh\" "
                        + "\"" + remoteRoot + "/install_docker.sh\" "
                        + "\"" + remoteRoot + "/docker-compose.media-node.yml\" 2>/dev/null; "
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

    private NodeMediaRemoteDeployRespVO.DeployStep syncMediaCluster(
            SshSessionHelper ssh, String sourceRoot, RemoteImageProbe remoteImages) throws Exception {
        String remoteRoot = MediaStackDeployUtil.remoteClusterRoot();
        ssh.ensureRemoteDir(remoteRoot + "/srs");
        ssh.ensureRemoteDir(remoteRoot + "/zlm");

        int scriptCount = 0;
        for (String relative : SYNC_RELATIVE_FILES) {
            File local = new File(sourceRoot, relative);
            if (!local.isFile()) {
                throw exception(MEDIA_CLUSTER_SOURCE_NOT_FOUND);
            }
            ssh.uploadFile(local.getAbsolutePath(), remoteRoot + "/" + relative);
            if (relative.endsWith(".sh")) {
                ssh.exec("chmod +x " + remoteRoot + "/" + relative, 10000);
            }
            scriptCount++;
        }

        File imagesDir = new File(sourceRoot, "images");

        NodeMediaRemoteDeployRespVO.DeployStep step = new NodeMediaRemoteDeployRespVO.DeployStep();
        step.setName("同步 media-cluster");

        ssh.ensureRemoteDir(remoteRoot + "/images");
        int syncedTarCount = 0;
        int skippedTarCount = 0;
        long imageBytes = 0;
        for (String name : REQUIRED_IMAGE_TARS) {
            if (shouldSkipImageTarSync(remoteImages, name)) {
                skippedTarCount++;
                continue;
            }
            File tar = new File(imagesDir, name);
            if (!tar.isFile() || tar.length() == 0) {
                step.setStatus("failed");
                step.setOutput("本机缺少离线镜像包: " + name + "；请在本机执行 export_media_images.sh 后重试");
                return step;
            }
            if (remoteTarMatches(ssh, name, tar.length())) {
                skippedTarCount++;
                continue;
            }
            ssh.uploadFile(tar.getAbsolutePath(), remoteRoot + "/images/" + name);
            imageBytes += tar.length();
            syncedTarCount++;
        }

        step.setStatus("success");
        StringBuilder output = new StringBuilder();
        output.append("已上传 ").append(scriptCount).append(" 个脚本/配置");
        if (syncedTarCount > 0) {
            output.append(" + ").append(syncedTarCount).append(" 个离线镜像包（")
                    .append(formatBytes(imageBytes)).append("）");
        }
        if (skippedTarCount > 0) {
            output.append("；跳过 ").append(skippedTarCount).append(" 个已有镜像/离线包");
        }
        output.append(" 至 ").append(remoteRoot);
        step.setOutput(output.toString());
        return step;
    }

    @Deprecated
    private NodeMediaRemoteDeployRespVO.DeployStep syncMediaClusterScripts(SshSessionHelper ssh, String sourceRoot)
            throws Exception {
        String remoteRoot = MediaStackDeployUtil.remoteClusterRoot();
        ssh.ensureRemoteDir(remoteRoot + "/srs");
        ssh.ensureRemoteDir(remoteRoot + "/zlm");
        int count = 0;
        for (String relative : SYNC_RELATIVE_FILES) {
            File local = new File(sourceRoot, relative);
            if (!local.isFile()) {
                throw exception(MEDIA_CLUSTER_SOURCE_NOT_FOUND);
            }
            ssh.uploadFile(local.getAbsolutePath(), remoteRoot + "/" + relative);
            if (relative.endsWith(".sh")) {
                ssh.exec("chmod +x " + remoteRoot + "/" + relative, 10000);
            }
            count++;
        }
        return runStep("同步脚本配置", "success", "已上传 " + count + " 个脚本/配置文件至 " + remoteRoot);
    }

    private NodeMediaRemoteDeployRespVO.DeployStep syncOfflineImages(SshSessionHelper ssh, String sourceRoot)
            throws Exception {
        String remoteRoot = MediaStackDeployUtil.remoteClusterRoot();
        File imagesDir = new File(sourceRoot, "images");
        List<String> missing = listMissingImageTars(imagesDir, Arrays.asList(REQUIRED_IMAGE_TARS));
        NodeMediaRemoteDeployRespVO.DeployStep step = new NodeMediaRemoteDeployRespVO.DeployStep();
        step.setName("同步离线镜像");
        if (!missing.isEmpty()) {
            step.setStatus("failed");
            step.setOutput("缺少离线镜像包: " + String.join(", ", missing));
            return step;
        }

        ssh.ensureRemoteDir(remoteRoot + "/images");
        long imageBytes = 0;
        for (String name : REQUIRED_IMAGE_TARS) {
            File tar = new File(imagesDir, name);
            ssh.uploadFile(tar.getAbsolutePath(), remoteRoot + "/images/" + name);
            imageBytes += tar.length();
        }
        step.setStatus("success");
        step.setOutput("已上传 " + REQUIRED_IMAGE_TARS.length + " 个离线镜像包（"
                + formatBytes(imageBytes) + "）至 " + remoteRoot + "/images/");
        return step;
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
            step.setOutput("目标机 Docker 已就绪\n" + describeRemoteDockerVersion(ssh));
            return step;
        }

        if (checkOut.contains("DOCKER_START_NEEDED")) {
            SshSessionHelper.SshExecResult start = ssh.exec(
                    "(sudo systemctl start docker 2>/dev/null || systemctl start docker 2>/dev/null || true)"
                            + " && sleep 2 && docker info >/dev/null 2>&1 && echo DOCKER_OK || echo DOCKER_STILL_DOWN",
                    60000);
            if (start.combinedOutput().contains("DOCKER_OK")) {
                step.setStatus("success");
                step.setOutput("目标机 Docker 已启动\n" + describeRemoteDockerVersion(ssh));
                return step;
            }
        }

        File installScript = new File(sourceRoot, "install_docker.sh");
        if (!installScript.isFile()) {
            step.setStatus("failed");
            step.setOutput("目标机未安装 Docker，且控制面缺少 install_docker.sh（"
                    + installScript.getAbsolutePath() + "）");
            return step;
        }

        String remoteScript = "/tmp/easyaiot-install-docker-" + System.currentTimeMillis() + ".sh";
        ssh.uploadFile(installScript.getAbsolutePath(), remoteScript);
        SshSessionHelper.SshExecResult install = ssh.exec(
                "chmod +x \"" + remoteScript + "\" && bash \"" + remoteScript + "\"",
                DOCKER_INSTALL_TIMEOUT_MS);
        ssh.exec("rm -f \"" + remoteScript + "\"", 10000);

        SshSessionHelper.SshExecResult verify = ssh.exec(
                "docker info >/dev/null 2>&1 && echo DOCKER_OK || echo DOCKER_FAIL",
                30000);
        if (!install.isSuccess() || !verify.combinedOutput().contains("DOCKER_OK")) {
            step.setStatus("failed");
            step.setOutput("Docker 自动安装失败\n" + trimOutput(install.combinedOutput(), 6000));
            return step;
        }
        step.setStatus("success");
        step.setOutput("目标机已自动安装 Docker\n"
                + trimOutput(install.combinedOutput(), 3000) + "\n"
                + describeRemoteDockerVersion(ssh));
        return step;
    }

    private String describeRemoteDockerVersion(SshSessionHelper ssh) throws Exception {
        SshSessionHelper.SshExecResult version = ssh.exec(
                "docker --version 2>/dev/null; docker compose version 2>/dev/null | head -1 || true",
                15000);
        return trimOutput(version.combinedOutput(), 500);
    }

    private static final class ExistingMediaCheck {
        private final boolean srsRunning;
        private final boolean zlmRunning;
        private final NodeMediaRemoteDeployRespVO.DeployStep step;

        private ExistingMediaCheck(
                boolean srsRunning, boolean zlmRunning, NodeMediaRemoteDeployRespVO.DeployStep step) {
            this.srsRunning = srsRunning;
            this.zlmRunning = zlmRunning;
            this.step = step;
        }
    }

    private ExistingMediaCheck checkExistingMediaServices(SshSessionHelper ssh, ComputeNodeDO node)
            throws Exception {
        int srsApi = MediaStackDeployUtil.tagInt(node.getTags(), "srs_api_port", 1985);
        int zlmHttp = MediaStackDeployUtil.tagInt(node.getTags(), "zlm_http_port", 6080);
        boolean srsRunning = "success".equals(probeSrsStatus(ssh, node).getStatus());
        boolean zlmRunning = "success".equals(probeZlmStatus(ssh, node).getStatus());
        NodeMediaRemoteDeployRespVO.DeployStep step = new NodeMediaRemoteDeployRespVO.DeployStep();
        step.setName("检测已有服务");
        step.setStatus("success");
        if (srsRunning && zlmRunning) {
            step.setOutput("SRS（API " + srsApi + "）与 ZLMediaKit（HTTP " + zlmHttp + "）均已运行，无需重复部署");
        } else if (srsRunning) {
            step.setOutput("检测到 SRS 已运行（API " + srsApi + "），将保留并补部署 ZLMediaKit");
        } else if (zlmRunning) {
            step.setOutput("检测到 ZLMediaKit 已运行（HTTP " + zlmHttp + "），将保留并补部署 SRS");
        } else {
            step.setOutput("目标机未检测到运行中的 SRS / ZLMediaKit，将部署完整媒体栈");
        }
        return new ExistingMediaCheck(srsRunning, zlmRunning, step);
    }

    private NodeMediaRemoteDeployRespVO.DeployStep ensureRemoteDockerCompose(SshSessionHelper ssh)
            throws Exception {
        NodeMediaRemoteDeployRespVO.DeployStep step = new NodeMediaRemoteDeployRespVO.DeployStep();
        step.setName("Docker Compose");

        SshSessionHelper.SshExecResult check = ssh.exec(
                "if docker compose version >/dev/null 2>&1; then echo COMPOSE_PLUGIN; "
                        + "elif command -v docker-compose >/dev/null 2>&1 && docker-compose version >/dev/null 2>&1; then echo COMPOSE_BIN; "
                        + "elif [[ -x /usr/local/bin/docker-compose ]] && /usr/local/bin/docker-compose version >/dev/null 2>&1; then echo COMPOSE_BIN; "
                        + "else echo COMPOSE_MISSING; fi",
                30000);
        String checkOut = check.combinedOutput();
        if (checkOut.contains("COMPOSE_PLUGIN")) {
            step.setStatus("success");
            step.setOutput("目标机已安装 docker compose 插件\n" + describeRemoteComposeVersion(ssh));
            return step;
        }
        if (checkOut.contains("COMPOSE_BIN")) {
            step.setStatus("success");
            step.setOutput("目标机已安装 docker-compose\n" + describeRemoteComposeVersion(ssh));
            return step;
        }

        File localCompose = resolveLocalDockerComposeBinary();
        if (localCompose == null) {
            step.setStatus("failed");
            step.setOutput("目标机未安装 Docker Compose，且控制面未找到可同步的 docker-compose 二进制。"
                    + "请在本机安装 docker-compose-plugin 或 docker-compose，"
                    + "或通过 easyaiot.media.docker-compose-path 指定路径后重试");
            return step;
        }

        String remoteTmp = "/tmp/easyaiot-docker-compose-" + System.currentTimeMillis();
        ssh.uploadFile(localCompose.getAbsolutePath(), remoteTmp);
        SshSessionHelper.SshExecResult install = ssh.exec(
                "chmod +x \"" + remoteTmp + "\""
                        + " && (sudo cp \"" + remoteTmp + "\" \"" + REMOTE_COMPOSE_BIN + "\""
                        + " || cp \"" + remoteTmp + "\" \"" + REMOTE_COMPOSE_BIN + "\")"
                        + " && rm -f \"" + remoteTmp + "\""
                        + " && \"" + REMOTE_COMPOSE_BIN + "\" version",
                60000);
        if (!install.isSuccess()) {
            step.setStatus("failed");
            step.setOutput("同步 docker-compose 失败\n" + trimOutput(install.combinedOutput(), 4000));
            return step;
        }
        step.setStatus("success");
        step.setOutput("已从控制面同步 docker-compose 至 " + REMOTE_COMPOSE_BIN
                + "（源: " + localCompose.getAbsolutePath() + "）\n"
                + trimOutput(install.combinedOutput(), 1000));
        return step;
    }

    private String describeRemoteComposeVersion(SshSessionHelper ssh) throws Exception {
        SshSessionHelper.SshExecResult version = ssh.exec(
                "docker compose version 2>/dev/null || docker-compose --version 2>/dev/null || true",
                15000);
        return trimOutput(version.combinedOutput(), 500);
    }

    private File resolveLocalDockerComposeBinary() {
        if (mediaDockerComposePath != null && !mediaDockerComposePath.isBlank()) {
            File configured = new File(mediaDockerComposePath);
            if (configured.isFile()) {
                return configured;
            }
        }
        for (String path : LOCAL_COMPOSE_CANDIDATES) {
            File candidate = new File(path);
            if (candidate.isFile()) {
                return candidate;
            }
        }
        try {
            ProcessBuilder pb = new ProcessBuilder("sh", "-c", "command -v docker-compose");
            pb.redirectErrorStream(true);
            Process process = pb.start();
            String output;
            try (InputStream in = process.getInputStream()) {
                output = new String(in.readAllBytes(), StandardCharsets.UTF_8).trim();
            }
            if (process.waitFor(10, TimeUnit.SECONDS) && process.exitValue() == 0 && !output.isBlank()) {
                File resolved = new File(output.split("\\s+")[0]);
                if (resolved.isFile()) {
                    return resolved;
                }
            }
        } catch (Exception e) {
            log.warn("解析本机 docker-compose 路径失败: {}", e.getMessage());
        }
        return null;
    }

    private NodeMediaRemoteDeployRespVO.DeployStep verifyServices(SshSessionHelper ssh, ComputeNodeDO node)
            throws Exception {
        NodeMediaRemoteDeployRespVO.DeployStep srsStep = probeSrsStatus(ssh, node);
        NodeMediaRemoteDeployRespVO.DeployStep zlmStep = probeZlmStatus(ssh, node);
        boolean srsOk = "success".equals(srsStep.getStatus());
        boolean zlmOk = "success".equals(zlmStep.getStatus());
        NodeMediaRemoteDeployRespVO.DeployStep step = new NodeMediaRemoteDeployRespVO.DeployStep();
        step.setName("服务验证");
        step.setOutput(trimOutput(srsStep.getOutput(), 2000) + "\n" + trimOutput(zlmStep.getOutput(), 2000));
        if (srsOk && zlmOk) {
            step.setStatus("success");
        } else if (srsOk || zlmOk) {
            step.setStatus("success");
            step.setOutput(step.getOutput() + "\n（部分服务已在运行）");
        } else {
            step.setStatus("failed");
        }
        return step;
    }

    private String resolveMediaClusterSource() {
        if (mediaClusterSourcePath != null && !mediaClusterSourcePath.isBlank()) {
            File dir = new File(mediaClusterSourcePath);
            if (dir.isDirectory()) {
                return dir.getAbsolutePath();
            }
        }
        String[] candidates = {
                "/opt/easyaiot/.scripts/media-cluster",
                System.getProperty("user.dir") + "/.scripts/media-cluster",
                System.getProperty("user.dir") + "/../.scripts/media-cluster",
        };
        for (String path : candidates) {
            File install = new File(path, "install_media_stack.sh");
            if (install.isFile()) {
                return new File(path).getAbsolutePath();
            }
        }
        throw exception(MEDIA_CLUSTER_SOURCE_NOT_FOUND);
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

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void release(String deviceId) {
        DeviceMediaBindingDO binding = deviceMediaBindingMapper.selectByDeviceId(deviceId);
        if (binding == null) {
            return;
        }
        nodeSchedulerService.release(WORKLOAD_SRS_LIVE, deviceId);
        nodeSchedulerService.release(WORKLOAD_SRS_AI, deviceId);
        nodeSchedulerService.release(WORKLOAD_ZLM, deviceId);
        binding.setStatus("released");
        deviceMediaBindingMapper.updateById(binding);
    }

    private NodeSchedulerAllocateRespVO allocateMediaNode(String workloadType, String deviceId,
                                                          List<String> capabilities, String region) {
        NodeSchedulerAllocateReqVO req = new NodeSchedulerAllocateReqVO();
        req.setWorkloadType(workloadType);
        req.setWorkloadId(deviceId);
        req.setSticky(true);
        NodeSchedulerAllocateReqVO.Requirements requirements = new NodeSchedulerAllocateReqVO.Requirements();
        requirements.setCapabilities(capabilities);
        requirements.setRegion(region);
        req.setRequirements(requirements);
        return nodeSchedulerService.allocate(req);
    }

    private boolean bindingNodesOnline(DeviceMediaBindingDO binding) {
        return Arrays.asList(binding.getSrsLiveNodeId(), binding.getSrsAiNodeId(), binding.getZlmNodeId())
                .stream()
                .filter(id -> id != null)
                .allMatch(this::isNodeOnline);
    }

    private boolean isNodeOnline(Long nodeId) {
        ComputeNodeDO node = computeNodeMapper.selectById(nodeId);
        return node != null && NodeStatusEnum.ONLINE.getStatus().equals(node.getStatus());
    }

    private DeviceMediaBindingRespVO toResp(DeviceMediaBindingDO binding) {
        return BeanUtils.toBean(binding, DeviceMediaBindingRespVO.class);
    }

    private JSONObject callAgent(ComputeNodeDO node, String path, Map<String, Object> body) {
        int port = node.getAgentPort() != null ? node.getAgentPort() : 9100;
        String url = String.format("http://%s:%d%s", node.getHost(), port, path);
        HttpResponse response = HttpRequest.post(url)
                .header("X-Agent-Token", node.getAgentToken())
                .header("Content-Type", "application/json")
                .body(JSONUtil.toJsonStr(body))
                .timeout(120000)
                .execute();
        if (!response.isOk()) {
            throw new IllegalStateException("Agent 请求失败 HTTP " + response.getStatus() + ": " + response.body());
        }
        JSONObject json = JSONUtil.parseObj(response.body());
        if (json.getInt("code", -1) != 0) {
            throw new IllegalStateException("Agent 执行失败: " + json.getStr("msg", response.body()));
        }
        return json.getJSONObject("data") != null ? json.getJSONObject("data") : new JSONObject();
    }

}
