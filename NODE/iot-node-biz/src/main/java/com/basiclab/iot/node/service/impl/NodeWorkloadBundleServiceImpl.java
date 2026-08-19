package com.basiclab.iot.node.service.impl;

import com.basiclab.iot.node.dal.dataobject.ComputeNodeDO;
import com.basiclab.iot.node.dal.dataobject.NodeSshCredentialDO;
import com.basiclab.iot.node.dal.pgsql.ComputeNodeMapper;
import com.basiclab.iot.node.dal.pgsql.NodeSshCredentialMapper;
import com.basiclab.iot.node.domain.vo.NodeMediaRemoteDeployRespVO;
import com.basiclab.iot.node.domain.vo.NodeWorkloadBundleBatchReqVO;
import com.basiclab.iot.node.domain.vo.NodeWorkloadBundleBatchRespVO;
import com.basiclab.iot.node.domain.vo.NodeWorkloadBundleCheckRespVO;
import com.basiclab.iot.node.domain.vo.NodeWorkloadBundleNodeResultVO;
import com.basiclab.iot.node.domain.vo.NodeWorkloadDeployReqVO;
import com.basiclab.iot.node.enums.WorkloadBundleTypeEnum;
import com.basiclab.iot.node.service.NodeCommandService;
import com.basiclab.iot.node.service.NodeFfmpegDeployService;
import com.basiclab.iot.node.service.NodeRuntimeCppDeployService;
import com.basiclab.iot.node.service.NodeWorkloadBundleService;
import com.basiclab.iot.node.util.CredentialEncryptUtil;
import com.basiclab.iot.node.util.FfmpegStaticDeployUtil;
import com.basiclab.iot.node.util.SshSessionHelper;
import com.basiclab.iot.node.util.WorkloadBundleDeployUtil;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.io.File;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.TimeUnit;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.AI_SOURCE_NOT_FOUND;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.COMPUTE_NODE_NOT_EXISTS;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.COMPUTE_NODE_PLATFORM_UPDATE_FORBIDDEN;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.SSH_CREDENTIAL_NOT_EXISTS;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.VIDEO_SOURCE_NOT_FOUND;
import static com.basiclab.iot.node.service.impl.ComputeNodeServiceImpl.resolveSshPort;

/**
 * 计算节点工作负载 bundle 批量分发（离线运行时 + 脚本）。
 */
@Slf4j
@Service
public class NodeWorkloadBundleServiceImpl implements NodeWorkloadBundleService {

    private static final int DEPLOY_TIMEOUT_MS = 900_000;
    private static final long EXPORT_PIP_WHEELS_TIMEOUT_MS = 900_000L;

    @Resource
    private ComputeNodeMapper computeNodeMapper;
    @Resource
    private NodeSshCredentialMapper nodeSshCredentialMapper;
    @Resource
    private NodeFfmpegDeployService nodeFfmpegDeployService;
    @Resource
    private NodeRuntimeCppDeployService nodeRuntimeCppDeployService;
    @Resource
    private NodeCommandService nodeCommandService;

    @Value("${easyaiot.video.source-path:}")
    private String videoSourcePath;

    @Value("${easyaiot.ai.source-path:}")
    private String aiSourcePath;

    @Value("${easyaiot.transform.image:easyaiot/transform-runtime:1.0.0}")
    private String transformImage;

    @Value("${easyaiot.transform.replicas:1}")
    private int transformReplicas;

    @Value("${easyaiot.transform.kafka-bootstrap:127.0.0.1:9092}")
    private String transformKafkaBootstrap;

    @Value("${easyaiot.transform.postgres-url:jdbc:postgresql://127.0.0.1:5432/iot-transform20}")
    private String transformPostgresUrl;

    @Value("${easyaiot.transform.postgres-username:postgres}")
    private String transformPostgresUsername;

    @Value("${easyaiot.transform.postgres-password:iot45722414822}")
    private String transformPostgresPassword;

    @Value("${easyaiot.transform.heartbeat-timeout-sec:120}")
    private int transformHeartbeatTimeoutSec;

    @Override
    public NodeWorkloadBundleCheckRespVO checkBySsh(Long nodeId, String bundleType) {
        WorkloadBundleTypeEnum bundle = requireBundle(bundleType);
        ComputeNodeDO node = validateNode(nodeId);
        NodeWorkloadBundleCheckRespVO resp = new NodeWorkloadBundleCheckRespVO();
        resp.setBundleType(bundle.getType());
        resp.setPythonLauncher(WorkloadBundleDeployUtil.remotePythonLauncher(bundle));
        resp.setFfmpegPath(FfmpegStaticDeployUtil.REMOTE_FFMPEG_BIN);

        try (SshSessionHelper ssh = openSsh(node)) {
            resp.getSteps().add(step("SSH 连接", "success", "已连接 " + node.getHost()));
            if ("VIDEO".equals(bundle.getModule())) {
                probeFfmpeg(ssh, resp);
            } else {
                resp.setFfmpegReady(null);
            }
            probeEnv(ssh, bundle, resp);
            probeScripts(ssh, bundle, resp);
            boolean videoOk = !"VIDEO".equals(bundle.getModule())
                    || Boolean.TRUE.equals(resp.getFfmpegReady());
            resp.setSuccess(videoOk
                    && Boolean.TRUE.equals(resp.getEnvReady())
                    && Boolean.TRUE.equals(resp.getScriptsReady()));
            resp.setMessage(resp.getSuccess()
                    ? "运行时与脚本均已就绪"
                    : buildCheckMessage(resp));
        } catch (Exception e) {
            log.error("bundle 检测失败 nodeId={} bundle={}: {}", nodeId, bundleType, e.getMessage(), e);
            resp.setSuccess(false);
            resp.setMessage(e.getMessage());
            resp.getSteps().add(step("检测中断", "failed", e.getMessage()));
        }
        return resp;
    }

    @Override
    public NodeWorkloadBundleBatchRespVO batchCheckBySsh(NodeWorkloadBundleBatchReqVO reqVO) {
        return batchExecute(reqVO, this::checkNodeInternal);
    }

    @Override
    public NodeWorkloadBundleBatchRespVO batchDeployEnvBySsh(NodeWorkloadBundleBatchReqVO reqVO) {
        return batchExecute(reqVO, this::deployEnvInternal);
    }

    @Override
    public NodeWorkloadBundleBatchRespVO batchDeployScriptsBySsh(NodeWorkloadBundleBatchReqVO reqVO) {
        return batchExecute(reqVO, this::deployScriptsInternal);
    }

    @Override
    public NodeWorkloadBundleBatchRespVO batchDeployFullBySsh(NodeWorkloadBundleBatchReqVO reqVO) {
        WorkloadBundleTypeEnum bundle = requireBundle(reqVO.getBundleType());
        final int replicas = reqVO.getReplicas() != null && reqVO.getReplicas() > 0
                ? reqVO.getReplicas()
                : Math.max(1, transformReplicas);
        if (WorkloadBundleDeployUtil.isJavaRuntimeBundle(bundle)) {
            List<NodeMediaRemoteDeployRespVO.DeployStep> prep = new ArrayList<>();
            if (!ensureLocalTransformImage(prep)) {
                NodeWorkloadBundleBatchRespVO fail = new NodeWorkloadBundleBatchRespVO();
                fail.setBundleType(bundle.getType());
                fail.setSuccess(false);
                fail.setMessage("控制面镜像打包失败：" + lastFailedOutput(prep));
                NodeWorkloadBundleNodeResultVO one = new NodeWorkloadBundleNodeResultVO();
                one.setSuccess(false);
                one.setMessage(fail.getMessage());
                one.setSteps(prep);
                fail.getResults().add(one);
                return fail;
            }
        }
        return batchExecute(reqVO, (node, b) -> {
            NodeWorkloadBundleNodeResultVO result = baseResult(node);
            if ("VIDEO".equals(bundle.getModule())) {
                if (!nodeFfmpegDeployService.deployOnNodeIfMissing(node.getId(), result.getSteps())) {
                    result.setSuccess(false);
                    result.setMessage(lastFailedOutput(result.getSteps()));
                    return result;
                }
                // 算法类 bundle 额外分发 RUNTIME（高性能 executor=cpp）
                if (bundle == WorkloadBundleTypeEnum.ALGORITHM_REALTIME
                        || bundle == WorkloadBundleTypeEnum.ALGORITHM_SNAP
                        || bundle == WorkloadBundleTypeEnum.ALGORITHM_PATROL) {
                    if (!nodeRuntimeCppDeployService.deployOnNodeIfMissing(node.getId(), result.getSteps())) {
                        result.setSuccess(false);
                        result.setMessage(lastFailedOutput(result.getSteps()));
                        return result;
                    }
                }
            }
            NodeWorkloadBundleNodeResultVO env = deployEnvInternal(node, bundle);
            result.getSteps().addAll(env.getSteps());
            if (!Boolean.TRUE.equals(env.getSuccess())) {
                result.setSuccess(false);
                result.setMessage(env.getMessage());
                return result;
            }
            NodeWorkloadBundleNodeResultVO scripts = deployScriptsInternal(node, bundle);
            result.getSteps().addAll(scripts.getSteps());
            if (!Boolean.TRUE.equals(scripts.getSuccess())) {
                result.setSuccess(false);
                result.setMessage(scripts.getMessage());
                return result;
            }
            if (WorkloadBundleDeployUtil.isJavaRuntimeBundle(bundle)) {
                return deployTransformContainersAndVerify(node, result, replicas);
            }
            result.setSuccess(true);
            result.setMessage(scripts.getMessage());
            return result;
        });
    }

    @Override
    public NodeWorkloadBundleBatchRespVO batchRemoveEnvBySsh(NodeWorkloadBundleBatchReqVO reqVO) {
        return batchExecute(reqVO, this::removeEnvInternal);
    }

    @Override
    public NodeWorkloadBundleBatchRespVO batchRemoveScriptsBySsh(NodeWorkloadBundleBatchReqVO reqVO) {
        return batchExecute(reqVO, this::removeScriptsInternal);
    }

    private interface NodeBundleAction {
        NodeWorkloadBundleNodeResultVO apply(ComputeNodeDO node, WorkloadBundleTypeEnum bundle);
    }

    private NodeWorkloadBundleBatchRespVO batchExecute(NodeWorkloadBundleBatchReqVO reqVO, NodeBundleAction action) {
        WorkloadBundleTypeEnum bundle = requireBundle(reqVO.getBundleType());
        NodeWorkloadBundleBatchRespVO resp = new NodeWorkloadBundleBatchRespVO();
        resp.setBundleType(bundle.getType());
        boolean allOk = true;
        int skipped = 0;
        for (Long nodeId : reqVO.getNodeIds()) {
            ComputeNodeDO raw = computeNodeMapper.selectById(nodeId);
            if (raw == null) {
                NodeWorkloadBundleNodeResultVO fail = new NodeWorkloadBundleNodeResultVO();
                fail.setNodeId(nodeId);
                fail.setSuccess(false);
                fail.setMessage("节点不存在");
                fail.getSteps().add(step("节点校验", "failed", "节点不存在"));
                resp.getResults().add(fail);
                allOk = false;
                continue;
            }
            if (shouldSkipLocalDefaultTransform(bundle, raw)) {
                NodeWorkloadBundleNodeResultVO skip = baseResult(raw);
                skip.setSuccess(true);
                skip.setMessage("跳过本机默认 TRANSFORM（概览保留，本机不参与分发）");
                skip.getSteps().add(step("节点筛选", "skipped",
                        "platform 节点默认已有 TRANSFORM，仅参与集群总览，不做分发/覆盖"));
                resp.getResults().add(skip);
                skipped++;
                continue;
            }
            ComputeNodeDO node;
            try {
                node = validateNode(nodeId);
            } catch (Exception e) {
                NodeWorkloadBundleNodeResultVO fail = new NodeWorkloadBundleNodeResultVO();
                fail.setNodeId(nodeId);
                fail.setSuccess(false);
                fail.setMessage(e.getMessage());
                fail.getSteps().add(step("节点校验", "failed", e.getMessage()));
                resp.getResults().add(fail);
                allOk = false;
                continue;
            }
            NodeWorkloadBundleNodeResultVO one = action.apply(node, bundle);
            resp.getResults().add(one);
            if (!Boolean.TRUE.equals(one.getSuccess())) {
                allOk = false;
            }
        }
        resp.setSuccess(allOk);
        if (allOk) {
            if (skipped > 0) {
                resp.setMessage("操作成功，已自动跳过 " + skipped + " 个本机默认 TRANSFORM 节点");
            } else {
                resp.setMessage("全部 " + resp.getResults().size() + " 个节点操作成功");
            }
        } else {
            resp.setMessage(skipped > 0
                    ? "部分节点操作失败（已自动跳过 " + skipped + " 个本机默认 TRANSFORM 节点）"
                    : "部分节点操作失败，请查看各节点步骤");
        }
        return resp;
    }

    private boolean shouldSkipLocalDefaultTransform(WorkloadBundleTypeEnum bundle, ComputeNodeDO node) {
        return WorkloadBundleDeployUtil.isJavaRuntimeBundle(bundle)
                && ComputeNodeServiceImpl.isPlatformNode(node);
    }

    private NodeWorkloadBundleNodeResultVO checkNodeInternal(ComputeNodeDO node, WorkloadBundleTypeEnum bundle) {
        NodeWorkloadBundleCheckRespVO check = checkBySsh(node.getId(), bundle.getType());
        NodeWorkloadBundleNodeResultVO result = baseResult(node);
        result.setSuccess(check.getSuccess());
        result.setMessage(check.getMessage());
        result.setSteps(new ArrayList<>(check.getSteps()));
        return result;
    }

    private NodeWorkloadBundleNodeResultVO deployEnvInternal(ComputeNodeDO node, WorkloadBundleTypeEnum bundle) {
        NodeWorkloadBundleNodeResultVO result = baseResult(node);
        List<NodeMediaRemoteDeployRespVO.DeployStep> steps = result.getSteps();
        try (SshSessionHelper ssh = openSsh(node)) {
            steps.add(step("SSH 连接", "success", "已连接 " + node.getHost()));

            if (WorkloadBundleDeployUtil.isJavaRuntimeBundle(bundle)) {
                String remoteRoot = WorkloadBundleDeployUtil.moduleRoot(bundle);
                ssh.ensureRemoteDir(remoteRoot + "/scripts");
                ssh.ensureRemoteDir(remoteRoot + "/transform-runtime/target");
                ssh.ensureRemoteDir(remoteRoot + "/dist");
                SshSessionHelper.SshExecResult javaCheck = ssh.exec("java -version 2>&1 | head -1", 30_000);
                steps.add(step("Java 运行时", "success", trim(javaCheck.combinedOutput(), 500)));
                SshSessionHelper.SshExecResult dockerCheck = ssh.exec("docker version --format '{{.Server.Version}}' 2>&1", 30_000);
                boolean dockerOk = dockerCheck.isSuccess()
                        || (dockerCheck.combinedOutput() != null
                        && !dockerCheck.combinedOutput().toLowerCase(Locale.ROOT).contains("command not found"));
                steps.add(step("Docker 运行时", dockerOk ? "success" : "failed",
                        trim(dockerCheck.combinedOutput(), 500)));
                // 若已有镜像 tar，尝试 load（脚本同步后更完整；此处允许先检查能力）
                SshSessionHelper.SshExecResult loadTry = ssh.exec(
                        "if [ -f /opt/easyaiot/TRANSFORM/dist/transform-runtime-1.0.0.tar.gz ]; then "
                                + "gunzip -c /opt/easyaiot/TRANSFORM/dist/transform-runtime-1.0.0.tar.gz | docker load && echo IMAGE_LOADED; "
                                + "elif [ -f /opt/easyaiot/TRANSFORM/dist/transform-runtime-1.0.0.tar ]; then "
                                + "docker load -i /opt/easyaiot/TRANSFORM/dist/transform-runtime-1.0.0.tar && echo IMAGE_LOADED; "
                                + "elif docker image inspect easyaiot/transform-runtime:1.0.0 >/dev/null 2>&1; then echo IMAGE_EXISTS; "
                                + "else echo IMAGE_PENDING; fi",
                        600_000);
                steps.add(step("TRANSFORM 镜像", "success", trim(loadTry.combinedOutput(), 1000)));
                result.setSuccess(dockerOk);
                result.setMessage(dockerOk
                        ? "TRANSFORM 支持镜像容器部署（同节点多副本靠不同 workloadId/端口）"
                        : "节点未安装 Docker，无法镜像部署");
                return result;
            }

            String targetPython = detectRemotePythonVersion(ssh);
            steps.add(step("Python 运行时", "success", "目标机 Python " + targetPython));

            String sourceRoot = resolveModuleSourceRoot(bundle);
            File wheelsDir = ensureLocalWheels(sourceRoot, bundle, targetPython, steps);
            if (wheelsDir == null) {
                result.setSuccess(false);
                result.setMessage(lastFailedOutput(steps));
                return result;
            }

            String remoteBundle = WorkloadBundleDeployUtil.remoteBundleDir(bundle);
            ssh.ensureRemoteDir(remoteBundle);
            syncBundleEnvFiles(ssh, sourceRoot, bundle, wheelsDir, remoteBundle, steps);

            String installScript = WorkloadBundleDeployUtil.INSTALL_BUNDLE_ENV_SCRIPT;
            SshSessionHelper.SshExecResult installResult = ssh.exec(
                    "cd '" + remoteBundle + "' && sudo bash " + installScript + " '" + remoteBundle + "'",
                    DEPLOY_TIMEOUT_MS);
            NodeMediaRemoteDeployRespVO.DeployStep installStep = step("离线安装运行时", "failed",
                    trim(installResult.combinedOutput(), 8000));
            if (installResult.combinedOutput().contains("BUNDLE_ENV_OK")) {
                installStep.setStatus("success");
            }
            steps.add(installStep);
            if (!"success".equals(installStep.getStatus())) {
                result.setSuccess(false);
                result.setMessage(installStep.getOutput());
                return result;
            }

            String launcher = WorkloadBundleDeployUtil.remotePythonLauncher(bundle);
            SshSessionHelper.SshExecResult verify = ssh.exec(
                    WorkloadBundleDeployUtil.verifyImportCommand(bundle, launcher), 120_000);
            NodeMediaRemoteDeployRespVO.DeployStep verifyStep = step("依赖验证", "failed",
                    trim(verify.combinedOutput(), 4000));
            if (verify.combinedOutput().contains("OK")) {
                verifyStep.setStatus("success");
            }
            steps.add(verifyStep);

            result.setSuccess("success".equals(verifyStep.getStatus()));
            result.setMessage(result.getSuccess()
                    ? "离线运行时已安装: " + launcher
                    : verifyStep.getOutput());
        } catch (Exception e) {
            log.error("分发运行时失败 node={} bundle={}: {}", node.getHost(), bundle.getType(), e.getMessage(), e);
            steps.add(step("分发运行时", "failed", e.getMessage()));
            result.setSuccess(false);
            result.setMessage(e.getMessage());
        }
        return result;
    }

    private NodeWorkloadBundleNodeResultVO deployScriptsInternal(ComputeNodeDO node, WorkloadBundleTypeEnum bundle) {
        NodeWorkloadBundleNodeResultVO result = baseResult(node);
        List<NodeMediaRemoteDeployRespVO.DeployStep> steps = result.getSteps();
        try (SshSessionHelper ssh = openSsh(node)) {
            steps.add(step("SSH 连接", "success", "已连接 " + node.getHost()));
            if (WorkloadBundleDeployUtil.isJavaRuntimeBundle(bundle)) {
                if (!ensureLocalTransformImage(steps)) {
                    result.setSuccess(false);
                    result.setMessage(lastFailedOutput(steps));
                    return result;
                }
            }
            String sourceRoot = resolveModuleSourceRoot(bundle);
            String remoteRoot = WorkloadBundleDeployUtil.moduleRoot(bundle);
            ssh.ensureRemoteDir(remoteRoot);
            int uploaded = 0;
            for (String relative : WorkloadBundleDeployUtil.syncScriptRelativePaths(bundle)) {
                File local = new File(sourceRoot, relative);
                String remote = remoteRoot + "/" + relative;
                if (local.isFile()) {
                    ssh.uploadFile(local.getAbsolutePath(), remote);
                    uploaded++;
                } else if (local.isDirectory()) {
                    uploaded += ssh.uploadDirectoryRecursive(
                            local, remote,
                            WorkloadBundleDeployUtil::shouldSkipDirectory,
                            WorkloadBundleDeployUtil::shouldSkipFile);
                } else if (WorkloadBundleDeployUtil.isJavaRuntimeBundle(bundle)
                        && (relative.endsWith(".tar") || relative.endsWith(".tar.gz")
                        || relative.endsWith(".jar"))) {
                    steps.add(step("可选制品", "success", "跳过缺失: " + relative + "（全量分发会先 build-image）"));
                } else {
                    throw exception("AI".equals(bundle.getModule()) ? AI_SOURCE_NOT_FOUND : VIDEO_SOURCE_NOT_FOUND);
                }
            }
            if (WorkloadBundleDeployUtil.isJavaRuntimeBundle(bundle)) {
                ssh.exec("chmod +x '" + remoteRoot + "/scripts/'*.sh 2>/dev/null || true", 10_000);
                // 同步后加载镜像（优先 gzip）
                SshSessionHelper.SshExecResult load = ssh.exec(
                        "if [ -f '" + remoteRoot + "/dist/transform-runtime-1.0.0.tar.gz' ]; then "
                                + "gunzip -c '" + remoteRoot + "/dist/transform-runtime-1.0.0.tar.gz' | docker load && echo IMAGE_LOADED; "
                                + "elif [ -f '" + remoteRoot + "/dist/transform-runtime-1.0.0.tar' ]; then "
                                + "docker load -i '" + remoteRoot + "/dist/transform-runtime-1.0.0.tar' && echo IMAGE_LOADED; "
                                + "elif docker image inspect easyaiot/transform-runtime:1.0.0 >/dev/null 2>&1; then echo IMAGE_EXISTS; "
                                + "else echo IMAGE_MISSING; fi",
                        600_000);
                String loadOut = load.combinedOutput();
                boolean imageOk = loadOut.contains("IMAGE_LOADED") || loadOut.contains("IMAGE_EXISTS");
                steps.add(step("加载镜像", imageOk ? "success" : "failed", trim(loadOut, 1500)));
                SshSessionHelper.SshExecResult verify = ssh.exec(
                        WorkloadBundleDeployUtil.verifyImportCommand(bundle, ""), 30_000);
                boolean ok = verify.combinedOutput().contains("OK") && imageOk;
                steps.add(step("TRANSFORM 校验", ok ? "success" : "failed", trim(verify.combinedOutput(), 1000)));
                if (!ok) {
                    result.setSuccess(false);
                    result.setMessage(verify.combinedOutput() + "\n" + loadOut);
                    return result;
                }
            }
            steps.add(step("同步脚本", "success",
                    "已上传 " + uploaded + " 项至 " + remoteRoot + "（bundle=" + bundle.getType() + "）"));
            result.setSuccess(true);
            result.setMessage("脚本已同步至 " + remoteRoot);
        } catch (Exception e) {
            log.error("同步脚本失败 node={} bundle={}: {}", node.getHost(), bundle.getType(), e.getMessage(), e);
            steps.add(step("同步脚本", "failed", e.getMessage()));
            result.setSuccess(false);
            result.setMessage(e.getMessage());
        }
        return result;
    }

    private NodeWorkloadBundleNodeResultVO removeEnvInternal(ComputeNodeDO node, WorkloadBundleTypeEnum bundle) {
        NodeWorkloadBundleNodeResultVO result = baseResult(node);
        List<NodeMediaRemoteDeployRespVO.DeployStep> steps = result.getSteps();
        try (SshSessionHelper ssh = openSsh(node)) {
            steps.add(step("SSH 连接", "success", "已连接 " + node.getHost()));
            String remoteBundle = WorkloadBundleDeployUtil.remoteBundleDir(bundle);
            SshSessionHelper.SshExecResult exec = ssh.exec(
                    "if [ -d '" + remoteBundle + "' ]; then sudo rm -rf '" + remoteBundle + "' && echo REMOVED; "
                            + "else echo NOT_FOUND; fi",
                    60_000);
            String out = exec.combinedOutput();
            if (out.contains("REMOVED")) {
                steps.add(step("删除运行时", "success", "已删除 " + remoteBundle));
                result.setSuccess(true);
                result.setMessage("运行时已删除");
            } else {
                steps.add(step("删除运行时", "skipped", "目录不存在: " + remoteBundle));
                result.setSuccess(true);
                result.setMessage("运行时目录本不存在");
            }
        } catch (Exception e) {
            steps.add(step("删除运行时", "failed", e.getMessage()));
            result.setSuccess(false);
            result.setMessage(e.getMessage());
        }
        return result;
    }

    private NodeWorkloadBundleNodeResultVO removeScriptsInternal(ComputeNodeDO node, WorkloadBundleTypeEnum bundle) {
        NodeWorkloadBundleNodeResultVO result = baseResult(node);
        List<NodeMediaRemoteDeployRespVO.DeployStep> steps = result.getSteps();
        try (SshSessionHelper ssh = openSsh(node)) {
            steps.add(step("SSH 连接", "success", "已连接 " + node.getHost()));
            String remoteRoot = WorkloadBundleDeployUtil.moduleRoot(bundle);
            int removed = 0;
            for (String relative : WorkloadBundleDeployUtil.syncScriptRelativePaths(bundle)) {
                if ("models.py".equals(relative) || "db_models.py".equals(relative) || "app".equals(relative)) {
                    continue;
                }
                String remote = remoteRoot + "/" + relative;
                SshSessionHelper.SshExecResult exec = ssh.exec(
                        "if [ -e '" + remote + "' ]; then sudo rm -rf '" + remote + "' && echo REMOVED; fi",
                        60_000);
                if (exec.combinedOutput().contains("REMOVED")) {
                    removed++;
                }
            }
            steps.add(step("删除脚本", "success",
                    "已删除 bundle 专属目录 " + removed + " 项（保留共享 app/ 与 models）"));
            result.setSuccess(true);
            result.setMessage("bundle 脚本已清理");
        } catch (Exception e) {
            steps.add(step("删除脚本", "failed", e.getMessage()));
            result.setSuccess(false);
            result.setMessage(e.getMessage());
        }
        return result;
    }

    private void probeEnv(SshSessionHelper ssh, WorkloadBundleTypeEnum bundle, NodeWorkloadBundleCheckRespVO resp)
            throws Exception {
        String launcher = WorkloadBundleDeployUtil.remotePythonLauncher(bundle);
        SshSessionHelper.SshExecResult exists = ssh.exec(
                "if [ -x '" + launcher + "' ]; then echo LAUNCHER_OK; else echo LAUNCHER_MISSING; fi", 30_000);
        if (!exists.combinedOutput().contains("LAUNCHER_OK")) {
            resp.setEnvReady(false);
            resp.getSteps().add(step("运行时", "failed", "未找到 " + launcher));
            return;
        }
        SshSessionHelper.SshExecResult verify = ssh.exec(
                WorkloadBundleDeployUtil.verifyImportCommand(bundle, launcher), 120_000);
        boolean ok = verify.combinedOutput().contains("OK");
        resp.setEnvReady(ok);
        resp.getSteps().add(step("运行时", ok ? "success" : "failed",
                ok ? "依赖 import 正常: " + launcher : trim(verify.combinedOutput(), 2000)));
    }

    private void probeFfmpeg(SshSessionHelper ssh, NodeWorkloadBundleCheckRespVO resp) throws Exception {
        SshSessionHelper.SshExecResult result = ssh.exec(FfmpegStaticDeployUtil.verifyCommand(), 30_000);
        String out = result.combinedOutput();
        boolean ok = out.contains("FFMPEG_OK");
        resp.setFfmpegReady(ok);
        resp.getSteps().add(step("FFmpeg", ok ? "success" : "failed",
                ok ? trim(out, 2000) : "未找到 " + FfmpegStaticDeployUtil.REMOTE_FFMPEG_BIN));
    }

    private void probeScripts(SshSessionHelper ssh, WorkloadBundleTypeEnum bundle, NodeWorkloadBundleCheckRespVO resp)
            throws Exception {
        String remoteRoot = WorkloadBundleDeployUtil.moduleRoot(bundle);
        String marker = WorkloadBundleDeployUtil.scriptReadyMarker(bundle);
        SshSessionHelper.SshExecResult exec = ssh.exec(
                "if [ -f '" + remoteRoot + "/" + marker + "' ]; then echo SCRIPT_OK; "
                        + "else echo SCRIPT_MISSING; fi",
                30_000);
        boolean ok = exec.combinedOutput().contains("SCRIPT_OK");
        resp.setScriptsReady(ok);
        resp.getSteps().add(step("脚本", ok ? "success" : "failed",
                ok ? "已就绪: " + marker : "缺少 " + remoteRoot + "/" + marker));
    }

    private void syncBundleEnvFiles(
            SshSessionHelper ssh,
            String sourceRoot,
            WorkloadBundleTypeEnum bundle,
            File wheelsDir,
            String remoteBundle,
            List<NodeMediaRemoteDeployRespVO.DeployStep> steps) throws Exception {
        File req = new File(sourceRoot, WorkloadBundleDeployUtil.requirementsFileName(bundle));
        File install = new File(sourceRoot, WorkloadBundleDeployUtil.INSTALL_BUNDLE_ENV_SCRIPT);
        File getPip = new File(sourceRoot, WorkloadBundleDeployUtil.GET_PIP_SCRIPT);
        if (!req.isFile() || !install.isFile()) {
            throw exception("AI".equals(bundle.getModule()) ? AI_SOURCE_NOT_FOUND : VIDEO_SOURCE_NOT_FOUND);
        }
        ssh.uploadFile(req.getAbsolutePath(), remoteBundle + "/requirements.txt");
        ssh.uploadFile(install.getAbsolutePath(), remoteBundle + "/" + WorkloadBundleDeployUtil.INSTALL_BUNDLE_ENV_SCRIPT);
        ssh.exec("chmod +x " + remoteBundle + "/" + WorkloadBundleDeployUtil.INSTALL_BUNDLE_ENV_SCRIPT, 10_000);
        if (getPip.isFile()) {
            ssh.uploadFile(getPip.getAbsolutePath(), remoteBundle + "/" + WorkloadBundleDeployUtil.GET_PIP_SCRIPT);
        }
        String remoteWheels = remoteBundle + "/" + WorkloadBundleDeployUtil.PIP_WHEELS_DIR;
        ssh.ensureRemoteDir(remoteWheels);
        File[] wheels = listWheelFiles(wheelsDir);
        long bytes = 0;
        for (File wheel : wheels) {
            ssh.uploadFile(wheel.getAbsolutePath(), remoteWheels + "/" + wheel.getName());
            bytes += wheel.length();
        }
        steps.add(step("同步离线包", "success",
                "已上传 requirements + " + wheels.length + " 个 wheel（" + formatBytes(bytes) + "）"));
    }

    private File ensureLocalWheels(
            String sourceRoot,
            WorkloadBundleTypeEnum bundle,
            String targetPython,
            List<NodeMediaRemoteDeployRespVO.DeployStep> steps) {
        File wheelsDir = new File(WorkloadBundleDeployUtil.localWheelsCacheDir(sourceRoot, bundle));
        if (isWheelsReady(wheelsDir, targetPython)) {
            steps.add(step("准备离线 pip 包", "success",
                    "本机离线包已就绪（" + listWheelFiles(wheelsDir).length + " 个，Python " + targetPython + "）"));
            return wheelsDir;
        }
        File exportScript = new File(sourceRoot, WorkloadBundleDeployUtil.EXPORT_PIP_WHEELS_SCRIPT);
        if (!exportScript.isFile()) {
            steps.add(step("准备离线 pip 包", "failed",
                    "缺少 " + WorkloadBundleDeployUtil.EXPORT_PIP_WHEELS_SCRIPT
                            + "，请在控制面执行: BUNDLE_TYPE=" + bundle.getType()
                            + " bash " + exportScript.getAbsolutePath()));
            return null;
        }
        try {
            if (!wheelsDir.exists() && !wheelsDir.mkdirs()) {
                log.warn("无法创建 wheel 缓存目录: {}", wheelsDir.getAbsolutePath());
            }
            String output = runExportScript(exportScript, bundle, targetPython, wheelsDir);
            if (!isWheelsReady(wheelsDir, targetPython)) {
                steps.add(step("准备离线 pip 包", "failed",
                        "export 后 wheel 包仍不完整\n" + trim(output, 4000)));
                return null;
            }
            steps.add(step("准备离线 pip 包", "success",
                    "本机已下载 " + listWheelFiles(wheelsDir).length + " 个 wheel（Python " + targetPython + "）"));
            return wheelsDir;
        } catch (Exception e) {
            steps.add(step("准备离线 pip 包", "failed", "控制面下载 wheel 失败: " + e.getMessage()));
            return null;
        }
    }

    private String runExportScript(File exportScript, WorkloadBundleTypeEnum bundle, String targetPython, File wheelsDir)
            throws Exception {
        ProcessBuilder pb = new ProcessBuilder("bash", exportScript.getAbsolutePath());
        pb.directory(exportScript.getParentFile());
        pb.environment().put("BUNDLE_TYPE", bundle.getType());
        pb.environment().put("BUNDLE_TARGET_PYTHON", targetPython);
        pb.environment().put("BUNDLE_PIP_WHEELS_DIR", wheelsDir.getAbsolutePath());
        pb.redirectErrorStream(true);
        Process process = pb.start();
        String output;
        try (InputStream in = process.getInputStream()) {
            output = new String(in.readAllBytes(), StandardCharsets.UTF_8);
        }
        boolean finished = process.waitFor(EXPORT_PIP_WHEELS_TIMEOUT_MS, TimeUnit.MILLISECONDS);
        if (!finished) {
            process.destroyForcibly();
            throw new IllegalStateException("export_node_pip_wheels.sh 超时");
        }
        if (process.exitValue() != 0) {
            throw new IllegalStateException(output.isBlank()
                    ? "export 退出码 " + process.exitValue()
                    : output.trim());
        }
        return output;
    }

    private boolean isWheelsReady(File wheelsDir, String targetPython) {
        File[] wheels = listWheelFiles(wheelsDir);
        if (wheels.length < 5) {
            return false;
        }
        File marker = new File(wheelsDir, ".target-python");
        if (!marker.isFile()) {
            return false;
        }
        try {
            return Files.readString(marker.toPath(), StandardCharsets.UTF_8).trim().equals(targetPython);
        } catch (Exception e) {
            return false;
        }
    }

    private File[] listWheelFiles(File dir) {
        if (!dir.isDirectory()) {
            return new File[0];
        }
        File[] files = dir.listFiles(f -> f.isFile() && isWheelArtifact(f.getName()));
        return files != null ? files : new File[0];
    }

    private boolean isWheelArtifact(String name) {
        String lower = name.toLowerCase(Locale.ROOT);
        return lower.endsWith(".whl") || lower.endsWith(".tar.gz") || lower.endsWith(".zip");
    }

    private boolean ensureLocalTransformImage(List<NodeMediaRemoteDeployRespVO.DeployStep> steps) {
        try {
            String sourceRoot = resolveModuleSourceRoot(WorkloadBundleTypeEnum.TRANSFORM_RUNTIME);
            File gz = new File(sourceRoot, "dist/transform-runtime-1.0.0.tar.gz");
            File tar = new File(sourceRoot, "dist/transform-runtime-1.0.0.tar");
            File buildScript = new File(sourceRoot, "scripts/build-image.sh");
            if (gz.isFile() || tar.isFile()) {
                if (!gz.isFile() && tar.isFile()) {
                    Process p = new ProcessBuilder("gzip", "-c", tar.getAbsolutePath())
                            .redirectOutput(gz)
                            .redirectErrorStream(true)
                            .start();
                    boolean finished = p.waitFor(120, TimeUnit.SECONDS);
                    if (!finished || p.exitValue() != 0) {
                        steps.add(step("压缩镜像", "failed", "gzip 失败"));
                        return false;
                    }
                    steps.add(step("压缩镜像", "success", gz.getAbsolutePath()));
                } else {
                    steps.add(step("镜像制品", "success",
                            (gz.isFile() ? gz : tar).getAbsolutePath()));
                }
                return true;
            }
            if (!buildScript.isFile()) {
                steps.add(step("构建镜像", "failed", "缺少 build-image.sh: " + buildScript.getAbsolutePath()));
                return false;
            }
            steps.add(step("构建镜像", "success", "开始执行 build-image.sh（无本地制品）"));
            ProcessBuilder pb = new ProcessBuilder("bash", buildScript.getAbsolutePath());
            pb.directory(new File(sourceRoot));
            pb.redirectErrorStream(true);
            Process p = pb.start();
            String out;
            try (InputStream in = p.getInputStream()) {
                out = new String(in.readAllBytes(), StandardCharsets.UTF_8);
            }
            boolean finished = p.waitFor(30, TimeUnit.MINUTES);
            if (!finished) {
                p.destroyForcibly();
                steps.add(step("构建镜像", "failed", "超时"));
                return false;
            }
            boolean ok = p.exitValue() == 0 && (gz.isFile() || tar.isFile());
            steps.add(step("构建镜像", ok ? "success" : "failed", trim(out, 4000)));
            return ok;
        } catch (Exception e) {
            log.error("ensureLocalTransformImage failed: {}", e.getMessage(), e);
            steps.add(step("构建镜像", "failed", e.getMessage()));
            return false;
        }
    }

    /**
     * Agent 拉起 N 容器，再以 Kafka 约定心跳 topic 验收（端口可变不以 HTTP 为主）。
     */
    private NodeWorkloadBundleNodeResultVO deployTransformContainersAndVerify(
            ComputeNodeDO node, NodeWorkloadBundleNodeResultVO result, int replicas) {
        List<NodeMediaRemoteDeployRespVO.DeployStep> steps = result.getSteps();
        List<String> instanceIds = new ArrayList<>();
        try {
            int startPort = 48096;
            for (int i = 1; i <= replicas; i++) {
                String wid = "tr-n" + node.getId() + "-" + i + "-" + System.currentTimeMillis();
                instanceIds.add(wid);
                int preferPort = startPort + i - 1;
                Map<String, String> env = new HashMap<>();
                env.put("RUNTIME", "docker");
                env.put("IMAGE", transformImage);
                env.put("PORT", String.valueOf(preferPort));
                env.put("START_PORT", String.valueOf(startPort));
                env.put("TRANSFORM_INSTANCE_ID", wid);
                env.put("TRANSFORM_NODE_ID", String.valueOf(node.getId()));
                env.put("TRANSFORM_HOST", node.getHost() == null ? "" : node.getHost());
                env.put("TRANSFORM_ROLE", "full");
                env.put("KAFKA_BOOTSTRAP", transformKafkaBootstrap);
                env.put("POSTGRES_URL", transformPostgresUrl);
                env.put("POSTGRES_USERNAME", transformPostgresUsername);
                env.put("POSTGRES_PASSWORD", transformPostgresPassword);

                NodeWorkloadDeployReqVO deployReq = new NodeWorkloadDeployReqVO();
                deployReq.setNodeId(node.getId());
                deployReq.setWorkloadType("transform_runtime");
                deployReq.setWorkloadId(wid);
                deployReq.setRuntime("docker");
                deployReq.setImage(transformImage);
                deployReq.setEnv(env);
                var resp = nodeCommandService.deployWorkload(deployReq);
                steps.add(step("启动容器 #" + i, "success",
                        "workloadId=" + wid + " bindingId=" + resp.getBindingId()
                                + " preferPort=" + preferPort));
            }
            boolean hbOk = waitTransformHeartbeats(instanceIds, steps);
            result.setSuccess(hbOk);
            result.setMessage(hbOk
                    ? "已部署 " + replicas + " 副本并通过 iot_transform_heartbeat 验收"
                    : "容器已启动，但心跳验收未通过（请查 Kafka/日志；端口可变不以 HTTP 固定端口判断）");
        } catch (Exception e) {
            log.error("TRANSFORM 部署运行失败 node={}: {}", node.getHost(), e.getMessage(), e);
            steps.add(step("启动/验收", "failed", e.getMessage()));
            result.setSuccess(false);
            result.setMessage(e.getMessage());
        }
        return result;
    }

    private boolean waitTransformHeartbeats(List<String> instanceIds,
                                            List<NodeMediaRemoteDeployRespVO.DeployStep> steps) {
        try {
            String sourceRoot = resolveModuleSourceRoot(WorkloadBundleTypeEnum.TRANSFORM_RUNTIME);
            File waitPy = new File(sourceRoot, "scripts/wait-heartbeat.py");
            if (!waitPy.isFile()) {
                steps.add(step("心跳验收", "failed", "缺少 wait-heartbeat.py"));
                return false;
            }
            File venvPy = new File(sourceRoot, "scripts/e2e/.venv/bin/python");
            String python = venvPy.isFile() ? venvPy.getAbsolutePath() : "python3";
            boolean allOk = true;
            for (String iid : instanceIds) {
                ProcessBuilder pb = new ProcessBuilder(
                        python, waitPy.getAbsolutePath(),
                        "--bootstrap", transformKafkaBootstrap,
                        "--instance-id", iid,
                        "--timeout", String.valueOf(Math.max(30, transformHeartbeatTimeoutSec))
                );
                pb.redirectErrorStream(true);
                Process p = pb.start();
                String out;
                try (InputStream in = p.getInputStream()) {
                    out = new String(in.readAllBytes(), StandardCharsets.UTF_8);
                }
                boolean finished = p.waitFor(transformHeartbeatTimeoutSec + 30L, TimeUnit.SECONDS);
                boolean ok = finished && p.exitValue() == 0 && out.contains("READY");
                steps.add(step("心跳 " + iid, ok ? "success" : "failed", trim(out, 2000)));
                if (!ok) {
                    allOk = false;
                }
            }
            return allOk;
        } catch (Exception e) {
            steps.add(step("心跳验收", "failed", e.getMessage()));
            return false;
        }
    }

    private String resolveModuleSourceRoot(WorkloadBundleTypeEnum bundle) {
        if ("TRANSFORM".equals(bundle.getModule())) {
            String userDir = System.getProperty("user.dir");
            String[] candidates = {
                    "/opt/easyaiot/TRANSFORM",
                    userDir + "/TRANSFORM",
                    userDir + "/../TRANSFORM",
                    userDir + "/../../TRANSFORM",
                    "/projects/new/easyaiot/TRANSFORM",
            };
            for (String path : candidates) {
                File marker = new File(path, WorkloadBundleDeployUtil.sourceRootMarker(bundle));
                File runScript = new File(path, WorkloadBundleDeployUtil.scriptReadyMarker(bundle));
                if (marker.isFile() && runScript.isFile()) {
                    return new File(path).getAbsolutePath();
                }
            }
            throw exception(VIDEO_SOURCE_NOT_FOUND);
        }
        if ("AI".equals(bundle.getModule())) {
            if (aiSourcePath != null && !aiSourcePath.isBlank()) {
                File dir = new File(aiSourcePath.trim());
                if (dir.isDirectory()) {
                    return dir.getAbsolutePath();
                }
            }
            String userDir = System.getProperty("user.dir");
            String[] candidates = {
                    "/opt/easyaiot/AI",
                    userDir + "/AI",
                    userDir + "/../AI",
                    userDir + "/../../AI",
            };
            for (String path : candidates) {
                File marker = new File(path, WorkloadBundleDeployUtil.sourceRootMarker(bundle));
                File runDeploy = new File(path, WorkloadBundleDeployUtil.scriptReadyMarker(bundle));
                if (marker.isFile() && runDeploy.isFile()) {
                    return new File(path).getAbsolutePath();
                }
            }
            throw exception(AI_SOURCE_NOT_FOUND);
        }
        if (videoSourcePath != null && !videoSourcePath.isBlank()) {
            File dir = new File(videoSourcePath.trim());
            if (dir.isDirectory()) {
                return dir.getAbsolutePath();
            }
        }
        String userDir = System.getProperty("user.dir");
        String[] candidates = {
                "/opt/easyaiot/VIDEO",
                userDir + "/VIDEO",
                userDir + "/../VIDEO",
                userDir + "/../../VIDEO",
        };
        for (String path : candidates) {
            File marker = new File(path, WorkloadBundleDeployUtil.sourceRootMarker(bundle));
            File runDeploy = new File(path, WorkloadBundleDeployUtil.scriptReadyMarker(bundle));
            if (marker.isFile() && runDeploy.isFile()) {
                return new File(path).getAbsolutePath();
            }
        }
        throw exception(VIDEO_SOURCE_NOT_FOUND);
    }

    private SshSessionHelper openSsh(ComputeNodeDO node) throws Exception {
        NodeSshCredentialDO credential = nodeSshCredentialMapper.selectByNodeId(node.getId());
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
        return SshSessionHelper.connect(
                node.getHost(),
                resolveSshPort(node),
                credential.getUsername(),
                credential.getAuthType(),
                password,
                privateKey);
    }

    private ComputeNodeDO validateNode(Long nodeId) {
        ComputeNodeDO node = computeNodeMapper.selectById(nodeId);
        if (node == null) {
            throw exception(COMPUTE_NODE_NOT_EXISTS);
        }
        if (ComputeNodeServiceImpl.isPlatformNode(node)) {
            throw exception(COMPUTE_NODE_PLATFORM_UPDATE_FORBIDDEN);
        }
        return node;
    }

    private WorkloadBundleTypeEnum requireBundle(String bundleType) {
        WorkloadBundleTypeEnum bundle = WorkloadBundleTypeEnum.of(bundleType);
        if (bundle == null) {
            throw new IllegalArgumentException("未知 bundleType: " + bundleType);
        }
        return bundle;
    }

    private NodeWorkloadBundleNodeResultVO baseResult(ComputeNodeDO node) {
        NodeWorkloadBundleNodeResultVO result = new NodeWorkloadBundleNodeResultVO();
        result.setNodeId(node.getId());
        result.setNodeName(node.getName());
        result.setHost(node.getHost());
        result.setSteps(new ArrayList<>());
        return result;
    }

    private static NodeMediaRemoteDeployRespVO.DeployStep step(String name, String status, String output) {
        NodeMediaRemoteDeployRespVO.DeployStep s = new NodeMediaRemoteDeployRespVO.DeployStep();
        s.setName(name);
        s.setStatus(status);
        s.setOutput(output);
        return s;
    }

    private static String trim(String text, int max) {
        if (text == null) {
            return "";
        }
        String t = text.trim();
        return t.length() <= max ? t : t.substring(0, max) + "...";
    }

    private static String lastFailedOutput(List<NodeMediaRemoteDeployRespVO.DeployStep> steps) {
        for (int i = steps.size() - 1; i >= 0; i--) {
            if ("failed".equals(steps.get(i).getStatus())) {
                return steps.get(i).getOutput();
            }
        }
        return "操作失败";
    }

    private static String buildCheckMessage(NodeWorkloadBundleCheckRespVO resp) {
        List<String> parts = new ArrayList<>();
        if (Boolean.FALSE.equals(resp.getFfmpegReady())) {
            parts.add("FFmpeg 未就绪");
        }
        if (!Boolean.TRUE.equals(resp.getEnvReady())) {
            parts.add("运行时未就绪");
        }
        if (!Boolean.TRUE.equals(resp.getScriptsReady())) {
            parts.add("脚本未就绪");
        }
        return String.join("；", parts);
    }

    private static String formatBytes(long bytes) {
        if (bytes < 1024) {
            return bytes + " B";
        }
        if (bytes < 1024L * 1024) {
            return String.format(Locale.ROOT, "%.1f KB", bytes / 1024.0);
        }
        return String.format(Locale.ROOT, "%.1f MB", bytes / (1024.0 * 1024.0));
    }

    private String detectRemotePythonVersion(SshSessionHelper ssh) throws Exception {
        SshSessionHelper.SshExecResult result = ssh.exec(
                "python3 -c \"import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')\" 2>/dev/null || echo 3.10",
                10_000);
        String version = result.combinedOutput().trim();
        return version.matches("3\\.\\d+") ? version : "3.10";
    }
}
