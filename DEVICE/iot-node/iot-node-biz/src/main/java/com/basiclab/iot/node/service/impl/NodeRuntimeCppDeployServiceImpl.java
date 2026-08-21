package com.basiclab.iot.node.service.impl;

import com.basiclab.iot.node.dal.dataobject.ComputeNodeDO;
import com.basiclab.iot.node.dal.dataobject.NodeSentinelSnapshotDO;
import com.basiclab.iot.node.dal.dataobject.NodeSshCredentialDO;
import com.basiclab.iot.node.dal.pgsql.ComputeNodeMapper;
import com.basiclab.iot.node.dal.pgsql.NodeSentinelSnapshotMapper;
import com.basiclab.iot.node.dal.pgsql.NodeSshCredentialMapper;
import com.basiclab.iot.node.domain.vo.NodeMediaRemoteDeployRespVO;
import com.basiclab.iot.node.domain.vo.NodeRuntimeCppBatchReqVO;
import com.basiclab.iot.node.domain.vo.NodeRuntimeCppCheckRespVO;
import com.basiclab.iot.node.domain.vo.NodeWorkloadBundleBatchRespVO;
import com.basiclab.iot.node.domain.vo.NodeWorkloadBundleNodeResultVO;
import com.basiclab.iot.node.service.NodeRuntimeCppDeployService;
import com.basiclab.iot.node.util.CredentialEncryptUtil;
import com.basiclab.iot.node.util.RuntimeCppDeployUtil;
import com.basiclab.iot.node.util.SshSessionHelper;
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
import java.util.Map;
import java.util.concurrent.TimeUnit;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.COMPUTE_NODE_NOT_EXISTS;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.COMPUTE_NODE_PLATFORM_UPDATE_FORBIDDEN;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.RUNTIME_SOURCE_NOT_FOUND;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.SSH_CREDENTIAL_NOT_EXISTS;
import static com.basiclab.iot.node.service.impl.ComputeNodeServiceImpl.resolveSshPort;

@Slf4j
@Service
public class NodeRuntimeCppDeployServiceImpl implements NodeRuntimeCppDeployService {

    private static final int DEPLOY_TIMEOUT_MS = 600_000;
    /** 控制面首次编译 + 导出可能较久 */
    private static final long EXPORT_TIMEOUT_MS = 1_800_000L;

    @Resource
    private ComputeNodeMapper computeNodeMapper;
    @Resource
    private NodeSshCredentialMapper nodeSshCredentialMapper;
    @Resource
    private NodeSentinelSnapshotMapper nodeSentinelSnapshotMapper;

    @Value("${easyaiot.runtime.source-path:}")
    private String runtimeSourcePath;

    @Value("${easyaiot.video.source-path:}")
    private String videoSourcePath;

    @Override
    public NodeRuntimeCppCheckRespVO checkBySsh(Long nodeId) {
        ComputeNodeDO node = validateNode(nodeId);
        NodeRuntimeCppCheckRespVO resp = new NodeRuntimeCppCheckRespVO();
        resp.setRuntimePath(RuntimeCppDeployUtil.REMOTE_RUNTIME_BIN);
        String controlPlaneVersion = readControlPlaneVersion();
        resp.setControlPlaneVersion(controlPlaneVersion);
        try (SshSessionHelper ssh = openSsh(node)) {
            resp.getSteps().add(step("SSH 连接", "success", "已连接 " + node.getHost()));
            probeRuntime(ssh, resp);
            resp.setSuccess(Boolean.TRUE.equals(resp.getRuntimeReady()));
            if (Boolean.TRUE.equals(resp.getSuccess())) {
                String nodeVer = resp.getVersion();
                if (controlPlaneVersion != null && !controlPlaneVersion.isBlank()
                        && nodeVer != null && !nodeVer.isBlank()) {
                    boolean match = controlPlaneVersion.equals(nodeVer);
                    resp.setVersionMatch(match);
                    if (match) {
                        resp.setMessage("RUNTIME 已就绪 · 版本 " + nodeVer + "（与控制面一致）");
                    } else {
                        resp.setMessage("RUNTIME 已就绪 · 节点 " + nodeVer
                                + " ≠ 控制面 " + controlPlaneVersion + "（建议重新分发升级）");
                    }
                } else if (nodeVer != null && !nodeVer.isBlank()) {
                    resp.setMessage("RUNTIME 已就绪 · 版本 " + nodeVer);
                } else {
                    resp.setMessage("RUNTIME 已就绪（未检测到 VERSION 文件）");
                }
            } else {
                resp.setMessage("RUNTIME 未安装或不可用");
            }
        } catch (Exception e) {
            resp.setSuccess(false);
            resp.setRuntimeReady(false);
            resp.setMessage(e.getMessage());
            resp.getSteps().add(step("检测中断", "failed", e.getMessage()));
        }
        return resp;
    }

    @Override
    public NodeWorkloadBundleBatchRespVO batchCheckBySsh(NodeRuntimeCppBatchReqVO reqVO) {
        return batchExecute(reqVO, this::checkNodeInternal);
    }

    @Override
    public NodeWorkloadBundleBatchRespVO batchDeployBySsh(NodeRuntimeCppBatchReqVO reqVO) {
        return batchExecute(reqVO, this::deployInternal);
    }

    @Override
    public NodeWorkloadBundleBatchRespVO batchRemoveBySsh(NodeRuntimeCppBatchReqVO reqVO) {
        return batchExecute(reqVO, this::removeInternal);
    }

    @Override
    public boolean deployOnNodeIfMissing(Long nodeId, List<NodeMediaRemoteDeployRespVO.DeployStep> steps) {
        ComputeNodeDO node = validateNode(nodeId);
        try (SshSessionHelper ssh = openSsh(node)) {
            SshSessionHelper.SshExecResult probe = ssh.exec(RuntimeCppDeployUtil.verifyCommand(), 30_000);
            if (RuntimeCppDeployUtil.outputMeansReady(probe.combinedOutput())) {
                steps.add(step("RUNTIME", "skipped", "已就绪 " + RuntimeCppDeployUtil.REMOTE_RUNTIME_BIN));
                return true;
            }
        } catch (Exception e) {
            steps.add(step("RUNTIME", "failed", e.getMessage()));
            return false;
        }
        NodeWorkloadBundleNodeResultVO result = deployInternal(node);
        steps.addAll(result.getSteps());
        return Boolean.TRUE.equals(result.getSuccess());
    }

    private NodeWorkloadBundleBatchRespVO batchExecute(
            NodeRuntimeCppBatchReqVO reqVO,
            NodeRuntimeAction action) {
        NodeWorkloadBundleBatchRespVO resp = new NodeWorkloadBundleBatchRespVO();
        resp.setBundleType("runtime_cpp");
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
                ? "全部 " + resp.getResults().size() + " 个节点 RUNTIME 操作成功"
                : "部分节点 RUNTIME 操作失败");
        return resp;
    }

    @FunctionalInterface
    private interface NodeRuntimeAction {
        NodeWorkloadBundleNodeResultVO apply(ComputeNodeDO node);
    }

    private NodeWorkloadBundleNodeResultVO checkNodeInternal(ComputeNodeDO node) {
        NodeRuntimeCppCheckRespVO check = checkBySsh(node.getId());
        NodeWorkloadBundleNodeResultVO result = baseResult(node);
        result.setSuccess(check.getSuccess());
        result.setMessage(check.getMessage());
        result.setVersion(check.getVersion());
        result.setControlPlaneVersion(check.getControlPlaneVersion());
        result.setVersionMatch(check.getVersionMatch());
        result.setSteps(new ArrayList<>(check.getSteps()));
        return result;
    }

    private NodeWorkloadBundleNodeResultVO deployInternal(ComputeNodeDO node) {
        NodeWorkloadBundleNodeResultVO result = baseResult(node);
        List<NodeMediaRemoteDeployRespVO.DeployStep> steps = result.getSteps();

        RuntimeCppDeployUtil.OsArch sentinelOs = resolveOsArchFromSentinel(node.getId());
        if (sentinelOs != null) {
            String sourceRoot = resolveRuntimeSourceRoot();
            File prefetched = RuntimeCppDeployUtil.findLocalTarball(sourceRoot, sentinelOs);
            if (prefetched == null) {
                String localOs = RuntimeCppDeployUtil.detectLocalOsFamily();
                String localArch = RuntimeCppDeployUtil.detectLocalArchKey();
                steps.add(step("分发前预检", "failed",
                        "Sentinel 上报节点 OS=" + sentinelOs.bundleKey()
                                + "，控制面缺少对应 RUNTIME 离线包。\n"
                                + RuntimeCppDeployUtil.missingBundleHint(sentinelOs.osFamily, sentinelOs.archKey)
                                + "\n控制面本机是 " + localOs + "/" + localArch
                                + "，不会在缺包时 SSH 上传。"));
                result.setSuccess(false);
                result.setMessage(lastFailed(steps));
                return result;
            }
            steps.add(step("分发前预检", "success",
                    "Sentinel 画像 os=" + sentinelOs.bundleKey()
                            + "，本地包已就绪 " + prefetched.getName()
                            + "（" + formatBytes(prefetched.length()) + "）"));
        }

        try (SshSessionHelper ssh = openSsh(node)) {
            steps.add(step("SSH 连接", "success", "已连接 " + node.getHost()));

            RuntimeCppDeployUtil.OsArch target = detectRemoteOsArch(ssh);
            steps.add(step("探测系统", "success",
                    "os-release ID=" + target.osId
                            + " VERSION_ID=" + target.versionId
                            + " uname=" + target.uname
                            + " → 包键 " + target.bundleKey()));

            String sourceRoot = resolveRuntimeSourceRoot();
            File tarball = ensureLocalTarball(sourceRoot, target, steps);
            if (tarball == null) {
                result.setSuccess(false);
                result.setMessage(lastFailed(steps));
                return result;
            }

            File installScript = new File(sourceRoot, RuntimeCppDeployUtil.INSTALL_SCRIPT);
            if (!installScript.isFile()) {
                steps.add(step("同步安装脚本", "failed", "缺少 " + RuntimeCppDeployUtil.INSTALL_SCRIPT));
                result.setSuccess(false);
                result.setMessage(lastFailed(steps));
                return result;
            }

            String remoteRoot = RuntimeCppDeployUtil.REMOTE_RUNTIME_ROOT;
            String remoteCache = remoteRoot + "/" + RuntimeCppDeployUtil.REMOTE_CACHE_SUBDIR;
            ssh.ensureRemoteDir(remoteCache);
            String remoteTar = remoteCache + "/" + tarball.getName();
            ssh.uploadFile(tarball.getAbsolutePath(), remoteTar);
            ssh.uploadFile(installScript.getAbsolutePath(),
                    remoteCache + "/" + RuntimeCppDeployUtil.INSTALL_SCRIPT);
            ssh.exec("chmod +x " + remoteCache + "/" + RuntimeCppDeployUtil.INSTALL_SCRIPT, 10_000);
            steps.add(step("同步离线包", "success",
                    "已上传 " + tarball.getName() + "（" + formatBytes(tarball.length()) + "）至 " + remoteCache));

            SshSessionHelper.SshExecResult install = ssh.exec(
                    "sudo bash " + remoteCache + "/" + RuntimeCppDeployUtil.INSTALL_SCRIPT
                            + " '" + remoteRoot + "' '" + remoteTar + "'",
                    DEPLOY_TIMEOUT_MS);
            SshSessionHelper.SshExecResult smoke = ssh.exec(RuntimeCppDeployUtil.verifyCommand(), 30_000);
            boolean installOk = RuntimeCppDeployUtil.outputMeansReady(smoke.combinedOutput());
            String combined = trim(install.combinedOutput() + "\n" + smoke.combinedOutput(), 6000);
            NodeMediaRemoteDeployRespVO.DeployStep installStep = step(
                    "安装 RUNTIME",
                    installOk ? "success" : "failed",
                    installOk ? combined
                            : "安装后无法执行 --version（包与节点 OS/ABI 不匹配或动态库缺失）\n" + combined);
            steps.add(installStep);

            result.setSuccess(installOk);
            result.setMessage(result.getSuccess()
                    ? "RUNTIME 已安装并可执行: " + RuntimeCppDeployUtil.REMOTE_RUNTIME_BIN
                            + "（" + target.bundleKey() + "）"
                    : installStep.getOutput());
        } catch (Exception e) {
            steps.add(step("安装 RUNTIME", "failed", e.getMessage()));
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
            String root = RuntimeCppDeployUtil.REMOTE_RUNTIME_ROOT;
            SshSessionHelper.SshExecResult exec = ssh.exec(
                    "if [ -d '" + root + "' ]; then sudo rm -rf '" + root + "' && echo REMOVED; "
                            + "else echo NOT_FOUND; fi; "
                            + "sudo rm -f /etc/profile.d/easyaiot-runtime.sh 2>/dev/null || true",
                    60_000);
            String out = exec.combinedOutput();
            if (out.contains("REMOVED")) {
                steps.add(step("删除 RUNTIME", "success", "已删除 " + root));
                result.setMessage("RUNTIME 已卸载");
            } else {
                steps.add(step("删除 RUNTIME", "skipped", "目录不存在: " + root));
                result.setMessage("RUNTIME 本未安装");
            }
            result.setSuccess(true);
        } catch (Exception e) {
            steps.add(step("删除 RUNTIME", "failed", e.getMessage()));
            result.setSuccess(false);
            result.setMessage(e.getMessage());
        }
        return result;
    }

    private void probeRuntime(SshSessionHelper ssh, NodeRuntimeCppCheckRespVO resp) throws Exception {
        try {
            RuntimeCppDeployUtil.OsArch osArch = detectRemoteOsArch(ssh);
            resp.setOsFamily(osArch.osFamily);
            resp.setArch(osArch.archKey);
        } catch (Exception e) {
            log.debug("探测节点 OS 失败: {}", e.getMessage());
        }
        SshSessionHelper.SshExecResult result = ssh.exec(RuntimeCppDeployUtil.verifyCommand(), 30_000);
        String out = result.combinedOutput();
        boolean ok = RuntimeCppDeployUtil.outputMeansReady(out);
        resp.setRuntimeReady(ok);
        if (ok) {
            String block = RuntimeCppDeployUtil.extractVersionBlock(out);
            java.util.Map<String, String> meta = RuntimeCppDeployUtil.parseVersionText(block);
            if (!meta.isEmpty()) {
                resp.setVersion(meta.get("version"));
                resp.setGit(meta.get("git"));
                resp.setBuiltAt(meta.get("built_at"));
            }
        }
        String detail;
        if (ok) {
            String ver = resp.getVersion();
            detail = (ver != null && !ver.isBlank())
                    ? ("版本 " + ver + (resp.getBuiltAt() != null ? " · built_at=" + resp.getBuiltAt() : "")
                    + (resp.getOsFamily() != null ? " · os=" + resp.getOsFamily() : ""))
                    : trim(out, 2000);
        } else if (out.contains("RUNTIME_MISSING")) {
            detail = "未找到 " + RuntimeCppDeployUtil.REMOTE_RUNTIME_BIN;
        } else {
            detail = "RUNTIME 无法执行（需要匹配节点 OS 的离线包）\n" + trim(out, 2500);
        }
        NodeMediaRemoteDeployRespVO.DeployStep s = step("RUNTIME", ok ? "success" : "failed", detail);
        resp.getSteps().add(s);
    }

    /** 读取控制面源码树 / 已安装目录 VERSION.version。 */
    private String readControlPlaneVersion() {
        try {
            String sourceRoot = resolveRuntimeSourceRoot();
            String[] relatives = {"build/VERSION", "VERSION"};
            for (String rel : relatives) {
                File f = new File(sourceRoot, rel);
                if (!f.isFile()) {
                    continue;
                }
                String text = new String(java.nio.file.Files.readAllBytes(f.toPath()), StandardCharsets.UTF_8);
                java.util.Map<String, String> meta = RuntimeCppDeployUtil.parseVersionText(text);
                String ver = meta.get("version");
                if (ver != null && !ver.isBlank()) {
                    return ver;
                }
            }
        } catch (Exception e) {
            log.debug("读取控制面 RUNTIME VERSION 失败: {}", e.getMessage());
        }
        try {
            File installed = new File("/opt/easyaiot/RUNTIME/VERSION");
            if (installed.isFile()) {
                String text = new String(java.nio.file.Files.readAllBytes(installed.toPath()), StandardCharsets.UTF_8);
                java.util.Map<String, String> meta = RuntimeCppDeployUtil.parseVersionText(text);
                String ver = meta.get("version");
                if (ver != null && !ver.isBlank()) {
                    return ver;
                }
            }
        } catch (Exception ignored) {
            // ignore
        }
        return null;
    }

    private File ensureLocalTarball(
            String sourceRoot,
            RuntimeCppDeployUtil.OsArch target,
            List<NodeMediaRemoteDeployRespVO.DeployStep> steps) {
        File existing = RuntimeCppDeployUtil.findLocalTarball(sourceRoot, target);
        if (existing != null) {
            steps.add(step("准备 RUNTIME 离线包", "success",
                    "本机已就绪 " + existing.getAbsolutePath()
                            + "（" + formatBytes(existing.length()) + "）"));
            return existing;
        }

        String osFamily = target.osFamily;
        String archKey = target.archKey;
        File cacheDir = new File(RuntimeCppDeployUtil.localCacheDir(sourceRoot, osFamily, archKey));
        String tarName = RuntimeCppDeployUtil.tarballName(osFamily, archKey);
        File tar = new File(cacheDir, tarName);

        String localOs = RuntimeCppDeployUtil.detectLocalOsFamily();
        String localArch = RuntimeCppDeployUtil.detectLocalArchKey();
        boolean sameAbi = osFamily.equals(localOs) && archKey.equals(localArch);

        if (!sameAbi) {
            steps.add(step("准备 RUNTIME 离线包", "failed",
                    RuntimeCppDeployUtil.missingBundleHint(osFamily, archKey)
                            + "\n控制面本机是 " + localOs + "/" + localArch
                            + "，不会把这份二进制发到 " + target.bundleKey() + "。"));
            return null;
        }

        File exportScript = new File(sourceRoot, RuntimeCppDeployUtil.EXPORT_SCRIPT);
        if (!exportScript.isFile()) {
            steps.add(step("准备 RUNTIME 离线包", "failed",
                    "缺少 " + RuntimeCppDeployUtil.EXPORT_SCRIPT
                            + "；请确认控制面存在 RUNTIME 源码目录"));
            return null;
        }
        try {
            if (!cacheDir.exists() && !cacheDir.mkdirs()) {
                log.warn("无法创建 RUNTIME 缓存目录 {}", cacheDir.getAbsolutePath());
            }
            steps.add(step("控制面准备", "running",
                    "目标与本机 ABI 一致（" + target.bundleKey()
                            + "），若尚未编译将自动执行 install_linux.sh 后导出"));
            ProcessBuilder pb = new ProcessBuilder("bash", exportScript.getAbsolutePath());
            pb.directory(new File(sourceRoot));
            pb.environment().put("RUNTIME_ARCH", RuntimeCppDeployUtil.exportArchEnv(archKey));
            pb.environment().put("RUNTIME_CACHE_DIR", cacheDir.getAbsolutePath());
            pb.environment().put("RUNTIME_AUTO_INSTALL", "1");
            pb.redirectErrorStream(true);
            Process process = pb.start();
            String output;
            try (InputStream in = process.getInputStream()) {
                output = new String(in.readAllBytes(), StandardCharsets.UTF_8);
            }
            boolean finished = process.waitFor(EXPORT_TIMEOUT_MS, TimeUnit.MILLISECONDS);
            if (!finished) {
                process.destroyForcibly();
                throw new IllegalStateException("export_runtime_cpp.sh 超时（含自动编译）");
            }
            if (process.exitValue() != 0) {
                throw new IllegalStateException(output.isBlank()
                        ? "export 退出码 " + process.exitValue()
                        : output.trim());
            }
            if (!RuntimeCppDeployUtil.isUsableTarball(tar)) {
                steps.add(step("准备 RUNTIME 离线包", "failed",
                        "export 后 tarball 仍不可用\n" + trim(output, 3000)));
                return null;
            }
            steps.add(step("准备 RUNTIME 离线包", "success",
                    "控制面已就绪 " + tarName + "（" + formatBytes(tar.length()) + "）\n" + trim(output, 1500)));
            return tar;
        } catch (Exception e) {
            steps.add(step("准备 RUNTIME 离线包", "failed", "控制面编译/导出失败: " + e.getMessage()));
            return null;
        }
    }

    private RuntimeCppDeployUtil.OsArch resolveOsArchFromSentinel(Long nodeId) {
        NodeSentinelSnapshotDO snapshot = nodeSentinelSnapshotMapper.selectById(nodeId);
        if (snapshot == null || snapshot.getEnvironmentProfile() == null) {
            return null;
        }
        Object osObj = snapshot.getEnvironmentProfile().get("os");
        if (!(osObj instanceof Map)) {
            return null;
        }
        @SuppressWarnings("unchecked")
        Map<String, Object> os = (Map<String, Object>) osObj;
        String family = stringVal(os.get("family"));
        if (family == null || family.isBlank()) {
            return null;
        }
        String archRaw = stringVal(os.get("arch"));
        String archKey = RuntimeCppDeployUtil.archKeyForUname(
                archRaw != null && !archRaw.isBlank() ? archRaw : "x86_64");
        return new RuntimeCppDeployUtil.OsArch(
                family,
                archKey,
                stringVal(os.get("id")),
                stringVal(os.get("versionId")),
                archRaw);
    }

    private static String stringVal(Object raw) {
        if (raw == null) {
            return null;
        }
        String text = String.valueOf(raw).trim();
        return text.isEmpty() ? null : text;
    }

    private RuntimeCppDeployUtil.OsArch detectRemoteOsArch(SshSessionHelper ssh) throws Exception {
        SshSessionHelper.SshExecResult r = ssh.exec(RuntimeCppDeployUtil.detectOsReleaseCommand(), 10_000);
        return RuntimeCppDeployUtil.parseOsArch(r.combinedOutput());
    }

    private String resolveRuntimeSourceRoot() {
        if (runtimeSourcePath != null && !runtimeSourcePath.isBlank()) {
            File dir = new File(runtimeSourcePath.trim());
            if (dir.isDirectory() && new File(dir, RuntimeCppDeployUtil.EXPORT_SCRIPT).isFile()) {
                return dir.getAbsolutePath();
            }
        }
        // Sibling of VIDEO when only video.source-path is configured
        if (videoSourcePath != null && !videoSourcePath.isBlank()) {
            File video = new File(videoSourcePath.trim());
            File sibling = new File(video.getParentFile(), "RUNTIME");
            if (sibling.isDirectory() && new File(sibling, RuntimeCppDeployUtil.EXPORT_SCRIPT).isFile()) {
                return sibling.getAbsolutePath();
            }
        }
        String userDir = System.getProperty("user.dir");
        String[] candidates = {
                "/opt/easyaiot/RUNTIME",
                userDir + "/RUNTIME",
                userDir + "/../RUNTIME",
                userDir + "/../../RUNTIME"
        };
        for (String path : candidates) {
            File dir = new File(path);
            if (dir.isDirectory() && new File(dir, RuntimeCppDeployUtil.EXPORT_SCRIPT).isFile()) {
                return dir.getAbsolutePath();
            }
        }
        throw exception(RUNTIME_SOURCE_NOT_FOUND);
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
