package com.basiclab.iot.node.service.impl;

import com.basiclab.iot.node.dal.dataobject.ComputeNodeDO;
import com.basiclab.iot.node.dal.dataobject.NodeSshCredentialDO;
import com.basiclab.iot.node.dal.pgsql.ComputeNodeMapper;
import com.basiclab.iot.node.dal.pgsql.NodeSshCredentialMapper;
import com.basiclab.iot.node.domain.vo.NodeFfmpegBatchReqVO;
import com.basiclab.iot.node.domain.vo.NodeFfmpegCheckRespVO;
import com.basiclab.iot.node.domain.vo.NodeMediaRemoteDeployRespVO;
import com.basiclab.iot.node.domain.vo.NodeWorkloadBundleBatchRespVO;
import com.basiclab.iot.node.domain.vo.NodeWorkloadBundleNodeResultVO;
import com.basiclab.iot.node.service.NodeFfmpegDeployService;
import com.basiclab.iot.node.util.CredentialEncryptUtil;
import com.basiclab.iot.node.util.FfmpegStaticDeployUtil;
import com.basiclab.iot.node.util.SshSessionHelper;
import com.basiclab.iot.node.util.WorkloadBundleDeployUtil;
import com.basiclab.iot.node.enums.WorkloadBundleTypeEnum;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.io.File;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.TimeUnit;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.COMPUTE_NODE_NOT_EXISTS;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.COMPUTE_NODE_PLATFORM_UPDATE_FORBIDDEN;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.SSH_CREDENTIAL_NOT_EXISTS;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.VIDEO_SOURCE_NOT_FOUND;
import static com.basiclab.iot.node.service.impl.ComputeNodeServiceImpl.resolveSshPort;

@Slf4j
@Service
public class NodeFfmpegDeployServiceImpl implements NodeFfmpegDeployService {

    private static final int DEPLOY_TIMEOUT_MS = 600_000;
    private static final long EXPORT_TIMEOUT_MS = 600_000L;

    @Resource
    private ComputeNodeMapper computeNodeMapper;
    @Resource
    private NodeSshCredentialMapper nodeSshCredentialMapper;

    @Value("${easyaiot.video.source-path:}")
    private String videoSourcePath;

    @Override
    public NodeFfmpegCheckRespVO checkBySsh(Long nodeId) {
        ComputeNodeDO node = validateNode(nodeId);
        NodeFfmpegCheckRespVO resp = new NodeFfmpegCheckRespVO();
        resp.setFfmpegPath(FfmpegStaticDeployUtil.REMOTE_FFMPEG_BIN);
        try (SshSessionHelper ssh = openSsh(node)) {
            resp.getSteps().add(step("SSH 连接", "success", "已连接 " + node.getHost()));
            probeFfmpeg(ssh, resp);
            resp.setSuccess(Boolean.TRUE.equals(resp.getFfmpegReady()));
            resp.setMessage(resp.getSuccess() ? "FFmpeg 已就绪" : "FFmpeg 未安装或不可用");
        } catch (Exception e) {
            resp.setSuccess(false);
            resp.setFfmpegReady(false);
            resp.setMessage(e.getMessage());
            resp.getSteps().add(step("检测中断", "failed", e.getMessage()));
        }
        return resp;
    }

    @Override
    public NodeWorkloadBundleBatchRespVO batchCheckBySsh(NodeFfmpegBatchReqVO reqVO) {
        return batchExecute(reqVO, this::checkNodeInternal);
    }

    @Override
    public NodeWorkloadBundleBatchRespVO batchDeployBySsh(NodeFfmpegBatchReqVO reqVO) {
        return batchExecute(reqVO, this::deployInternal);
    }

    @Override
    public NodeWorkloadBundleBatchRespVO batchRemoveBySsh(NodeFfmpegBatchReqVO reqVO) {
        return batchExecute(reqVO, this::removeInternal);
    }

    @Override
    public boolean deployOnNodeIfMissing(Long nodeId, List<NodeMediaRemoteDeployRespVO.DeployStep> steps) {
        ComputeNodeDO node = validateNode(nodeId);
        try (SshSessionHelper ssh = openSsh(node)) {
            SshSessionHelper.SshExecResult probe = ssh.exec(FfmpegStaticDeployUtil.verifyCommand(), 30_000);
            if (probe.combinedOutput().contains("FFMPEG_OK")) {
                steps.add(step("FFmpeg", "skipped", "已存在 " + FfmpegStaticDeployUtil.REMOTE_FFMPEG_BIN));
                return true;
            }
        } catch (Exception e) {
            steps.add(step("FFmpeg", "failed", e.getMessage()));
            return false;
        }
        NodeWorkloadBundleNodeResultVO result = deployInternal(node);
        steps.addAll(result.getSteps());
        return Boolean.TRUE.equals(result.getSuccess());
    }

    private NodeWorkloadBundleBatchRespVO batchExecute(
            NodeFfmpegBatchReqVO reqVO,
            NodeFfmpegAction action) {
        NodeWorkloadBundleBatchRespVO resp = new NodeWorkloadBundleBatchRespVO();
        resp.setBundleType("ffmpeg");
        boolean allOk = true;
        for (Long nodeId : reqVO.getNodeIds()) {
            ComputeNodeDO node;
            try {
                node = validateNode(nodeId);
            } catch (Exception e) {
                NodeWorkloadBundleNodeResultVO fail = baseResult(null);
                fail.setNodeId(nodeId);
                fail.setSuccess(false);
                fail.setMessage(e.getMessage());
                resp.getResults().add(fail);
                allOk = false;
                continue;
            }
            NodeWorkloadBundleNodeResultVO one = action.apply(node);
            resp.getResults().add(one);
            if (!Boolean.TRUE.equals(one.getSuccess())) {
                allOk = false;
            }
        }
        resp.setSuccess(allOk);
        resp.setMessage(allOk
                ? "全部 " + resp.getResults().size() + " 个节点 FFmpeg 操作成功"
                : "部分节点 FFmpeg 操作失败");
        return resp;
    }

    @FunctionalInterface
    private interface NodeFfmpegAction {
        NodeWorkloadBundleNodeResultVO apply(ComputeNodeDO node);
    }

    private NodeWorkloadBundleNodeResultVO checkNodeInternal(ComputeNodeDO node) {
        NodeFfmpegCheckRespVO check = checkBySsh(node.getId());
        NodeWorkloadBundleNodeResultVO result = baseResult(node);
        result.setSuccess(check.getSuccess());
        result.setMessage(check.getMessage());
        result.setSteps(new ArrayList<>(check.getSteps()));
        return result;
    }

    private NodeWorkloadBundleNodeResultVO deployInternal(ComputeNodeDO node) {
        NodeWorkloadBundleNodeResultVO result = baseResult(node);
        List<NodeMediaRemoteDeployRespVO.DeployStep> steps = result.getSteps();
        try (SshSessionHelper ssh = openSsh(node)) {
            steps.add(step("SSH 连接", "success", "已连接 " + node.getHost()));

            String uname = detectRemoteArch(ssh);
            String archKey = FfmpegStaticDeployUtil.archKeyForUname(uname);
            steps.add(step("探测架构", "success", "uname -m => " + uname + "，使用 " + archKey + " 静态包"));

            String sourceRoot = resolveVideoSourceRoot();
            File tarball = ensureLocalTarball(sourceRoot, archKey, steps);
            if (tarball == null) {
                result.setSuccess(false);
                result.setMessage(lastFailed(steps));
                return result;
            }

            File installScript = new File(sourceRoot, FfmpegStaticDeployUtil.INSTALL_FFMPEG_SCRIPT);
            if (!installScript.isFile()) {
                steps.add(step("同步安装脚本", "failed", "缺少 " + FfmpegStaticDeployUtil.INSTALL_FFMPEG_SCRIPT));
                result.setSuccess(false);
                result.setMessage(lastFailed(steps));
                return result;
            }

            String remoteRoot = FfmpegStaticDeployUtil.REMOTE_FFMPEG_ROOT;
            String remoteCache = remoteRoot + "/" + FfmpegStaticDeployUtil.REMOTE_CACHE_SUBDIR;
            ssh.ensureRemoteDir(remoteCache);
            String remoteTar = remoteCache + "/" + tarball.getName();
            ssh.uploadFile(tarball.getAbsolutePath(), remoteTar);
            ssh.uploadFile(installScript.getAbsolutePath(),
                    remoteCache + "/" + FfmpegStaticDeployUtil.INSTALL_FFMPEG_SCRIPT);
            ssh.exec("chmod +x " + remoteCache + "/" + FfmpegStaticDeployUtil.INSTALL_FFMPEG_SCRIPT, 10_000);
            steps.add(step("同步离线包", "success",
                    "已上传 " + tarball.getName() + "（" + formatBytes(tarball.length()) + "）至 " + remoteCache));

            SshSessionHelper.SshExecResult install = ssh.exec(
                    "sudo bash " + remoteCache + "/" + FfmpegStaticDeployUtil.INSTALL_FFMPEG_SCRIPT
                            + " '" + remoteRoot + "' '" + remoteTar + "'",
                    DEPLOY_TIMEOUT_MS);
            NodeMediaRemoteDeployRespVO.DeployStep installStep = step("安装 FFmpeg", "failed",
                    trim(install.combinedOutput(), 6000));
            if (install.combinedOutput().contains("FFMPEG_OK")) {
                installStep.setStatus("success");
            }
            steps.add(installStep);

            result.setSuccess("success".equals(installStep.getStatus()));
            result.setMessage(result.getSuccess()
                    ? "FFmpeg 已安装: " + FfmpegStaticDeployUtil.REMOTE_FFMPEG_BIN
                    : installStep.getOutput());
        } catch (Exception e) {
            steps.add(step("安装 FFmpeg", "failed", e.getMessage()));
            result.setSuccess(false);
            result.setMessage(e.getMessage());
        }
        return result;
    }

    private NodeWorkloadBundleNodeResultVO removeInternal(ComputeNodeDO node) {
        NodeWorkloadBundleNodeResultVO result = baseResult(node);
        List<NodeMediaRemoteDeployRespVO.DeployStep> steps = result.getSteps();
        try (SshSessionHelper ssh = openSsh(node)) {
            steps.add(step("SSH 连接", "success", "已连接 " + node.getHost()));
            String root = FfmpegStaticDeployUtil.REMOTE_FFMPEG_ROOT;
            SshSessionHelper.SshExecResult exec = ssh.exec(
                    "if [ -d '" + root + "' ]; then sudo rm -rf '" + root + "' && echo REMOVED; "
                            + "else echo NOT_FOUND; fi; "
                            + "sudo rm -f /etc/profile.d/easyaiot-ffmpeg.sh 2>/dev/null || true",
                    60_000);
            String out = exec.combinedOutput();
            if (out.contains("REMOVED")) {
                steps.add(step("删除 FFmpeg", "success", "已删除 " + root));
                result.setMessage("FFmpeg 已卸载");
            } else {
                steps.add(step("删除 FFmpeg", "skipped", "目录不存在: " + root));
                result.setMessage("FFmpeg 本未安装");
            }
            result.setSuccess(true);
        } catch (Exception e) {
            steps.add(step("删除 FFmpeg", "failed", e.getMessage()));
            result.setSuccess(false);
            result.setMessage(e.getMessage());
        }
        return result;
    }

    private void probeFfmpeg(SshSessionHelper ssh, NodeFfmpegCheckRespVO resp) throws Exception {
        SshSessionHelper.SshExecResult result = ssh.exec(FfmpegStaticDeployUtil.verifyCommand(), 30_000);
        String out = result.combinedOutput();
        boolean ok = out.contains("FFMPEG_OK");
        resp.setFfmpegReady(ok);
        NodeMediaRemoteDeployRespVO.DeployStep s = step("FFmpeg", ok ? "success" : "failed",
                ok ? trim(out, 2000) : "未找到 " + FfmpegStaticDeployUtil.REMOTE_FFMPEG_BIN);
        resp.getSteps().add(s);
    }

    private File ensureLocalTarball(
            String sourceRoot,
            String archKey,
            List<NodeMediaRemoteDeployRespVO.DeployStep> steps) {
        File cacheDir = new File(FfmpegStaticDeployUtil.localCacheDir(sourceRoot, archKey));
        String tarName = "arm64".equals(archKey)
                ? FfmpegStaticDeployUtil.TAR_LINUX_ARM64
                : FfmpegStaticDeployUtil.TAR_LINUX64;
        File tar = new File(cacheDir, tarName);
        File marker = new File(cacheDir, ".ready");
        if (tar.isFile() && tar.length() > 1_048_576L && marker.isFile()) {
            steps.add(step("准备 FFmpeg 离线包", "success",
                    "本机已就绪 " + tar.getAbsolutePath() + "（" + formatBytes(tar.length()) + "）"));
            return tar;
        }
        File exportScript = new File(sourceRoot, FfmpegStaticDeployUtil.EXPORT_FFMPEG_SCRIPT);
        if (!exportScript.isFile()) {
            steps.add(step("准备 FFmpeg 离线包", "failed",
                    "缺少 " + FfmpegStaticDeployUtil.EXPORT_FFMPEG_SCRIPT
                            + "；请在控制面 VIDEO 目录执行: FFMPEG_ARCH=" + archKey
                            + " bash export_ffmpeg_static.sh"));
            return null;
        }
        try {
            if (!cacheDir.exists() && !cacheDir.mkdirs()) {
                log.warn("无法创建 FFmpeg 缓存目录 {}", cacheDir.getAbsolutePath());
            }
            ProcessBuilder pb = new ProcessBuilder("bash", exportScript.getAbsolutePath());
            pb.directory(new File(sourceRoot));
            pb.environment().put("FFMPEG_ARCH", FfmpegStaticDeployUtil.exportArchEnv(archKey));
            pb.environment().put("FFMPEG_CACHE_DIR", cacheDir.getAbsolutePath());
            pb.redirectErrorStream(true);
            Process process = pb.start();
            String output;
            try (InputStream in = process.getInputStream()) {
                output = new String(in.readAllBytes(), StandardCharsets.UTF_8);
            }
            boolean finished = process.waitFor(EXPORT_TIMEOUT_MS, TimeUnit.MILLISECONDS);
            if (!finished) {
                process.destroyForcibly();
                throw new IllegalStateException("export_ffmpeg_static.sh 超时");
            }
            if (process.exitValue() != 0) {
                throw new IllegalStateException(output.isBlank()
                        ? "export 退出码 " + process.exitValue()
                        : output.trim());
            }
            if (!tar.isFile() || tar.length() <= 1_048_576L) {
                steps.add(step("准备 FFmpeg 离线包", "failed",
                        "export 后 tarball 仍不可用\n" + trim(output, 3000)));
                return null;
            }
            steps.add(step("准备 FFmpeg 离线包", "success",
                    "本机已下载 " + tarName + "（" + formatBytes(tar.length()) + "）"));
            return tar;
        } catch (Exception e) {
            steps.add(step("准备 FFmpeg 离线包", "failed", "控制面下载失败: " + e.getMessage()));
            return null;
        }
    }

    private String detectRemoteArch(SshSessionHelper ssh) throws Exception {
        SshSessionHelper.SshExecResult r = ssh.exec("uname -m 2>/dev/null || echo x86_64", 10_000);
        return r.combinedOutput().trim();
    }

    private String resolveVideoSourceRoot() {
        if (videoSourcePath != null && !videoSourcePath.isBlank()) {
            File dir = new File(videoSourcePath.trim());
            if (dir.isDirectory()) {
                return dir.getAbsolutePath();
            }
        }
        String userDir = System.getProperty("user.dir");
        String[] candidates = {"/opt/easyaiot/VIDEO", userDir + "/VIDEO", userDir + "/../VIDEO", userDir + "/../../VIDEO"};
        WorkloadBundleTypeEnum bundle = WorkloadBundleTypeEnum.STREAM_FORWARD;
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
                node.getHost(), resolveSshPort(node), credential.getUsername(),
                credential.getAuthType(), password, privateKey);
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

    private NodeWorkloadBundleNodeResultVO baseResult(ComputeNodeDO node) {
        NodeWorkloadBundleNodeResultVO r = new NodeWorkloadBundleNodeResultVO();
        if (node != null) {
            r.setNodeId(node.getId());
            r.setNodeName(node.getName());
            r.setHost(node.getHost());
        }
        r.setSteps(new ArrayList<>());
        return r;
    }

    private static NodeMediaRemoteDeployRespVO.DeployStep step(String name, String status, String output) {
        NodeMediaRemoteDeployRespVO.DeployStep s = new NodeMediaRemoteDeployRespVO.DeployStep();
        s.setName(name);
        s.setStatus(status);
        s.setOutput(output);
        return s;
    }

    private static String trim(String text, int max) {
        if (text == null) return "";
        String t = text.trim();
        return t.length() <= max ? t : t.substring(0, max) + "...";
    }

    private static String lastFailed(List<NodeMediaRemoteDeployRespVO.DeployStep> steps) {
        for (int i = steps.size() - 1; i >= 0; i--) {
            if ("failed".equals(steps.get(i).getStatus())) {
                return steps.get(i).getOutput();
            }
        }
        return "操作失败";
    }

    private static String formatBytes(long bytes) {
        if (bytes < 1024) return bytes + " B";
        if (bytes < 1024L * 1024) return String.format(Locale.ROOT, "%.1f KB", bytes / 1024.0);
        return String.format(Locale.ROOT, "%.1f MB", bytes / (1024.0 * 1024.0));
    }
}
