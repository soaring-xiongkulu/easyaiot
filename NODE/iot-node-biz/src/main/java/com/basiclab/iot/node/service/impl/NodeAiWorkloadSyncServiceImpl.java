package com.basiclab.iot.node.service.impl;

import com.basiclab.iot.node.dal.dataobject.ComputeNodeDO;
import com.basiclab.iot.node.dal.dataobject.NodeSshCredentialDO;
import com.basiclab.iot.node.dal.pgsql.NodeSshCredentialMapper;
import com.basiclab.iot.node.enums.WorkloadBundleTypeEnum;
import com.basiclab.iot.node.service.NodeAiWorkloadSyncService;
import com.basiclab.iot.node.util.CredentialEncryptUtil;
import com.basiclab.iot.node.util.SshSessionHelper;
import com.basiclab.iot.node.util.WorkloadBundleDeployUtil;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.io.File;
import java.util.List;
import java.util.Locale;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.AI_SOURCE_NOT_FOUND;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.SSH_CREDENTIAL_NOT_EXISTS;

@Slf4j
@Service
public class NodeAiWorkloadSyncServiceImpl implements NodeAiWorkloadSyncService {

    @Resource
    private NodeSshCredentialMapper nodeSshCredentialMapper;

    @Value("${easyaiot.ai.source-path:}")
    private String aiSourcePath;

    @Value("${easyaiot.ai.remote-root:" + WorkloadBundleDeployUtil.REMOTE_AI_ROOT + "}")
    private String aiRemoteRoot;

    @Value("${easyaiot.ai.auto-sync-before-deploy:true}")
    private boolean autoSyncBeforeDeploy;

    @Override
    public void syncBeforeDeploy(ComputeNodeDO node, String workloadType) {
        if (!autoSyncBeforeDeploy || !WorkloadBundleDeployUtil.requiresAiSync(workloadType)) {
            return;
        }
        if (ComputeNodeServiceImpl.isPlatformNode(node)) {
            log.debug("控制面节点跳过 AI SSH 同步 nodeId={} type={}", node.getId(), workloadType);
            return;
        }
        WorkloadBundleTypeEnum bundle = WorkloadBundleTypeEnum.of(
                workloadType == null ? "" : workloadType.trim().toLowerCase(Locale.ROOT));
        if (bundle == null) {
            bundle = WorkloadBundleTypeEnum.AI_SERVICE;
        }
        List<String> relativePaths;
        if (bundle == WorkloadBundleTypeEnum.AUTO_LABEL) {
            relativePaths = WorkloadBundleDeployUtil.syncAutoLabelRelativePaths();
        } else {
            relativePaths = WorkloadBundleDeployUtil.syncScriptRelativePaths(bundle);
        }
        if (relativePaths.isEmpty()) {
            return;
        }

        String sourceRoot = resolveAiSourceRoot();
        NodeSshCredential sshCredential = loadSshCredential(node.getId());
        int sshPort = ComputeNodeServiceImpl.resolveSshPort(node);

        int uploaded = 0;
        try (SshSessionHelper ssh = openSshSession(node, sshCredential, sshPort)) {
            ssh.ensureRemoteDir(aiRemoteRoot);
            for (String relative : relativePaths) {
                File local = new File(sourceRoot, relative);
                String remote = aiRemoteRoot + "/" + relative;
                if (local.isFile()) {
                    ssh.uploadFile(local.getAbsolutePath(), remote);
                    uploaded++;
                } else if (local.isDirectory()) {
                    uploaded += ssh.uploadDirectoryRecursive(
                            local,
                            remote,
                            WorkloadBundleDeployUtil::shouldSkipDirectory,
                            WorkloadBundleDeployUtil::shouldSkipFile);
                } else {
                    throw exception(AI_SOURCE_NOT_FOUND);
                }
            }
        } catch (RuntimeException e) {
            throw e;
        } catch (Exception e) {
            log.error("AI 代码 SSH 同步失败 nodeId={} host={} type={}: {}",
                    node.getId(), node.getHost(), workloadType, e.getMessage(), e);
            throw new IllegalStateException(
                    "AI 代码同步失败: " + node.getHost() + " — " + e.getMessage(), e);
        }

        log.info(
                "AI 工作负载代码已同步 nodeId={} host={} type={} files={} remote={}",
                node.getId(), node.getHost(), workloadType, uploaded, aiRemoteRoot);
    }

    private String resolveAiSourceRoot() {
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
        WorkloadBundleTypeEnum bundle = WorkloadBundleTypeEnum.AI_SERVICE;
        for (String path : candidates) {
            File marker = new File(path, WorkloadBundleDeployUtil.sourceRootMarker(bundle));
            File runDeploy = new File(path, WorkloadBundleDeployUtil.scriptReadyMarker(bundle));
            if (marker.isFile() && runDeploy.isFile()) {
                return new File(path).getAbsolutePath();
            }
        }
        throw exception(AI_SOURCE_NOT_FOUND);
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
}
