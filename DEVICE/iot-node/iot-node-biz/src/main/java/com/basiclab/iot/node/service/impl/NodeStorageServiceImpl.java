package com.basiclab.iot.node.service.impl;

import com.basiclab.iot.node.dal.dataobject.ComputeNodeDO;
import com.basiclab.iot.node.dal.dataobject.EdgeNodeDO;
import com.basiclab.iot.node.dal.dataobject.NodeSshCredentialDO;
import com.basiclab.iot.node.dal.pgsql.ComputeNodeMapper;
import com.basiclab.iot.node.dal.pgsql.EdgeNodeMapper;
import com.basiclab.iot.node.dal.pgsql.NodeSshCredentialMapper;
import com.basiclab.iot.node.domain.vo.NodeCephTopologyRespVO;
import com.basiclab.iot.node.domain.vo.NodeNfsClusterAssignReqVO;
import com.basiclab.iot.node.domain.vo.NodeMediaRemoteDeployRespVO;
import com.basiclab.iot.node.domain.vo.NodeStorageMountCheckRespVO;
import com.basiclab.iot.node.domain.vo.NodeStorageStackCheckRespVO;
import com.basiclab.iot.node.service.NodeStorageService;
import com.basiclab.iot.node.util.CredentialEncryptUtil;
import com.basiclab.iot.node.util.SshSessionHelper;
import com.basiclab.iot.node.util.StorageStackDeployUtil;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.validation.annotation.Validated;
import org.springframework.util.StringUtils;

import javax.annotation.Resource;
import java.io.File;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Base64;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.COMPUTE_NODE_NOT_EXISTS;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.SSH_CREDENTIAL_NOT_EXISTS;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.STORAGE_CLUSTER_SOURCE_NOT_FOUND;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.STORAGE_NODE_ROLE_INVALID;

@Slf4j
@Service
@Validated
public class NodeStorageServiceImpl implements NodeStorageService {

    private static final int DEPLOY_TIMEOUT_MS = 900000;
    private static final int CHECK_TIMEOUT_MS = 120000;
    private static final int OPS_TIMEOUT_MS = 180000;
    private static final String[] SYNC_RELATIVE_FILES = {
            "install_nfs_server.sh",
            "install_nfs_client.sh",
            "mount-all.sh",
            "check_nfs_health.sh",
    };

    @Resource
    private ComputeNodeMapper computeNodeMapper;
    @Resource
    private EdgeNodeMapper edgeNodeMapper;
    @Resource
    private NodeSshCredentialMapper nodeSshCredentialMapper;

    @Value("${easyaiot.storage.cluster-source-path:}")
    private String storageClusterSourcePath;

    @Value("${easyaiot.edge.media-host-data-root:/mnt/easyaiot-media}")
    private String mediaHostDataRoot;

    @Override
    public NodeCephTopologyRespVO getCephTopology() {
        List<ComputeNodeDO> all = computeNodeMapper.selectList();
        ComputeNodeDO platform = computeNodeMapper.selectPlatformNode();
        if (platform == null && all != null && !all.isEmpty()) {
            platform = all.stream()
                    .filter(n -> ComputeNodeServiceImpl.isPlatformNode(n))
                    .findFirst()
                    .orElse(all.get(0));
        }

        Map<Long, EdgeNodeDO> edgeByCompute = new HashMap<>();
        if (all != null) {
            for (ComputeNodeDO n : all) {
                if (n == null || n.getId() == null) {
                    continue;
                }
                EdgeNodeDO edge = edgeNodeMapper.selectByComputeNodeId(n.getId());
                if (edge != null) {
                    edgeByCompute.put(n.getId(), edge);
                }
            }
        }

        NodeCephTopologyRespVO resp = new NodeCephTopologyRespVO();
        List<NodeCephTopologyRespVO.TopologyNodeVO> nodes = new ArrayList<>();
        List<NodeCephTopologyRespVO.TopologyLinkVO> links = new ArrayList<>();
        Set<Long> included = new HashSet<>();

        NodeCephTopologyRespVO.TopologyNodeVO centerVo = null;
        if (platform != null) {
            centerVo = toTopologyNode(platform, edgeByCompute.get(platform.getId()), "platform");
            resp.setCenter(centerVo);
            nodes.add(centerVo);
            included.add(platform.getId());
        }

        if (all != null) {
            for (ComputeNodeDO n : all) {
                if (n == null || n.getId() == null || included.contains(n.getId())) {
                    continue;
                }
                String role = n.getNodeRole();
                boolean storage = StorageStackDeployUtil.isStorageRole(role);
                boolean client = StorageStackDeployUtil.isClientMountRole(role);
                if (!storage && !client) {
                    continue;
                }
                String kind = storage ? "storage_nfs" : "nfs_client";
                NodeCephTopologyRespVO.TopologyNodeVO vo = toTopologyNode(n, edgeByCompute.get(n.getId()), kind);
                nodes.add(vo);
                included.add(n.getId());

                if (centerVo != null && centerVo.getNodeId() != null) {
                    NodeCephTopologyRespVO.TopologyLinkVO link = new NodeCephTopologyRespVO.TopologyLinkVO();
                    link.setSourceNodeId(centerVo.getNodeId());
                    link.setTargetNodeId(n.getId());
                    link.setRelation(storage ? "nfs_export" : "client_mount");
                    links.add(link);
                }
            }
        }

        // 客户端挂载指向 NFS 服务端
        Map<String, Long> hostToId = new HashMap<>();
        for (NodeCephTopologyRespVO.TopologyNodeVO n : nodes) {
            if (n.getHost() != null) {
                hostToId.put(n.getHost().trim(), n.getNodeId());
            }
        }
        for (NodeCephTopologyRespVO.TopologyNodeVO n : nodes) {
            if (!"nfs_client".equals(n.getKind()) || !StringUtils.hasText(n.getNfsServerHost())) {
                continue;
            }
            Long serverId = hostToId.get(n.getNfsServerHost().trim());
            if (serverId == null || serverId.equals(n.getNodeId())) {
                continue;
            }
            NodeCephTopologyRespVO.TopologyLinkVO link = new NodeCephTopologyRespVO.TopologyLinkVO();
            link.setSourceNodeId(serverId);
            link.setTargetNodeId(n.getNodeId());
            link.setRelation("nfs_mount");
            links.add(link);
        }

        resp.setNodes(nodes);
        resp.setLinks(links);

        NodeCephTopologyRespVO.TopologySummaryVO summary = new NodeCephTopologyRespVO.TopologySummaryVO();
        int storageCnt = 0;
        int clientCnt = 0;
        int ready = 0;
        int notReady = 0;
        int offline = 0;
        for (NodeCephTopologyRespVO.TopologyNodeVO n : nodes) {
            if ("storage_nfs".equals(n.getKind())) {
                storageCnt++;
            } else if ("nfs_client".equals(n.getKind())) {
                clientCnt++;
            }
            if ("offline".equalsIgnoreCase(n.getStatus()) || "pending".equalsIgnoreCase(n.getStatus())) {
                offline++;
            }
            if (Boolean.TRUE.equals(n.getNfsMountReady())) {
                ready++;
            } else if (!"platform".equals(n.getKind())) {
                notReady++;
            }
        }
        summary.setTotalNodes(nodes.size());
        summary.setStorageNodes(storageCnt);
        summary.setClientNodes(clientCnt);
        summary.setMountReadyCount(ready);
        summary.setMountNotReadyCount(notReady);
        summary.setOfflineCount(offline);
        resp.setSummary(summary);
        return resp;
    }

    private NodeCephTopologyRespVO.TopologyNodeVO toTopologyNode(
            ComputeNodeDO node, EdgeNodeDO edge, String kind) {
        Map<String, String> tags = node.getTags() != null ? node.getTags() : Map.of();
        String mountPath = firstNonBlank(
                tags.get("ceph_mount_path"),
                tags.get("media_mount_path"),
                mediaHostDataRoot);
        if (!StringUtils.hasText(mountPath)) {
            mountPath = "/mnt/easyaiot-media";
        }
        mountPath = mountPath.replaceAll("/+$", "");

        boolean mountReady = false;
        String readyTag = firstNonBlank(tags.get("nfs_mount_ready"), tags.get("ceph_mount_ready"), null);
        if (StringUtils.hasText(readyTag)) {
            String r = readyTag.trim().toLowerCase(Locale.ROOT);
            mountReady = "true".equals(r) || "1".equals(r) || "yes".equals(r) || "on".equals(r);
        } else if (edge != null && Boolean.TRUE.equals(edge.getCephMountReady())) {
            mountReady = true;
        } else if ("platform".equals(kind)) {
            mountReady = true;
        }

        String nfsServer = StorageStackDeployUtil.resolveNfsServerHost(node, tags);
        String nfsExport = tagString(tags, "nfs_export", mountPath);
        String backend = tagString(tags, "storage_backend", "nfs");
        if ("127.0.0.1".equals(nfsServer) || "localhost".equalsIgnoreCase(nfsServer)) {
            backend = "local_bind";
        }

        NodeCephTopologyRespVO.TopologyNodeVO vo = new NodeCephTopologyRespVO.TopologyNodeVO();
        vo.setNodeId(node.getId());
        vo.setName(node.getName());
        vo.setHost(node.getHost());
        vo.setNodeRole(node.getNodeRole());
        vo.setStatus(node.getStatus());
        vo.setAgentPort(node.getAgentPort() != null ? node.getAgentPort() : 9100);
        vo.setKind(kind);
        vo.setIsPlatform(ComputeNodeServiceImpl.isPlatformNode(node));
        vo.setNfsMountReady(mountReady);
        vo.setNfsMountPath(mountPath);
        vo.setNfsServerHost(nfsServer);
        vo.setNfsExportPath(nfsExport);
        vo.setStorageBackend(backend);
        vo.setCephMountReady(mountReady);
        vo.setCephMountPath(mountPath);
        vo.setCephMonHost(nfsServer);
        vo.setCephPool(firstNonBlank(tags.get("ceph_pool"), "easyaiot-playbacks"));
        vo.setCephfsName(firstNonBlank(tags.get("cephfs_name"), "easyaiot"));
        vo.setAlertImagesDir(mountPath + "/alert_images");
        vo.setPlaybacksDir(mountPath + "/playbacks");
        vo.setSnapsDir(mountPath + "/snaps");
        vo.setLastHeartbeatAt(node.getLastHeartbeatAt());
        NodeSshCredentialDO cred = nodeSshCredentialMapper.selectByNodeId(node.getId());
        vo.setSshCredentialConfigured(cred != null && StringUtils.hasText(cred.getCredentialEnc()));
        return vo;
    }

    private static String tagString(Map<String, String> tags, String key, String defaultValue) {
        if (tags == null || !tags.containsKey(key)) {
            return defaultValue;
        }
        String raw = tags.get(key);
        return StringUtils.hasText(raw) ? raw.trim() : defaultValue;
    }

    @Override
    public NodeCephTopologyRespVO assignNfsCluster(NodeNfsClusterAssignReqVO req) {
        if (req == null) {
            req = new NodeNfsClusterAssignReqVO();
        }
        String mountRoot = StringUtils.hasText(req.getMountRoot())
                ? req.getMountRoot().trim().replaceAll("/+$", "")
                : mediaHostDataRoot.replaceAll("/+$", "");
        String nfsExport = StringUtils.hasText(req.getNfsExport())
                ? req.getNfsExport().trim().replaceAll("/+$", "")
                : mountRoot;
        String mountOpts = StringUtils.hasText(req.getNfsMountOpts())
                ? req.getNfsMountOpts().trim()
                : "vers=3,tcp,nolock,_netdev";

        ComputeNodeDO serverNode;
        if (req.getServerNodeId() != null) {
            serverNode = requireNode(req.getServerNodeId());
        } else {
            serverNode = computeNodeMapper.selectPlatformNode();
            if (serverNode == null) {
                List<ComputeNodeDO> all = computeNodeMapper.selectList();
                serverNode = all != null && !all.isEmpty() ? all.get(0) : null;
            }
            if (serverNode == null) {
                throw exception(COMPUTE_NODE_NOT_EXISTS);
            }
        }

        String serverHost = StringUtils.hasText(serverNode.getHost())
                ? serverNode.getHost().trim()
                : "127.0.0.1";

        applyNfsTags(serverNode, serverHost, nfsExport, mountRoot, mountOpts, true);
        computeNodeMapper.updateById(serverNode);

        List<Long> clientIds = req.getClientNodeIds();
        if (clientIds == null || clientIds.isEmpty()) {
            clientIds = new ArrayList<>();
            List<ComputeNodeDO> all = computeNodeMapper.selectList();
            if (all != null) {
                for (ComputeNodeDO n : all) {
                    if (n == null || n.getId() == null || n.getId().equals(serverNode.getId())) {
                        continue;
                    }
                    if (StorageStackDeployUtil.isClientMountRole(n.getNodeRole())) {
                        clientIds.add(n.getId());
                    }
                }
            }
        }

        for (Long clientId : clientIds) {
            if (clientId == null || clientId.equals(serverNode.getId())) {
                continue;
            }
            ComputeNodeDO client = requireNode(clientId);
            applyNfsTags(client, serverHost, nfsExport, mountRoot, mountOpts, false);
            computeNodeMapper.updateById(client);
        }

        return getCephTopology();
    }

    private void applyNfsTags(
            ComputeNodeDO node,
            String serverHost,
            String nfsExport,
            String mountRoot,
            String mountOpts,
            boolean isServer) {
        Map<String, String> tags = node.getTags() != null ? new HashMap<>(node.getTags()) : new HashMap<>();
        tags.put("storage_backend", "nfs");
        tags.put("media_mount_path", mountRoot);
        tags.put("nfs_export", nfsExport);
        tags.put("nfs_server_host", serverHost);
        tags.put("nfs_mount_opts", mountOpts);
        tags.put("ceph_mon_host", serverHost);
        tags.put("ceph_mount_path", mountRoot);
        if (isServer) {
            tags.put("nfs_role", "server");
        } else {
            tags.put("nfs_role", "client");
        }
        node.setTags(tags);
    }

    private static String firstNonBlank(String a, String b) {
        if (StringUtils.hasText(a)) {
            return a.trim();
        }
        if (StringUtils.hasText(b)) {
            return b.trim();
        }
        return null;
    }

    private static String firstNonBlank(String a, String b, String c) {
        String v = firstNonBlank(a, b);
        if (StringUtils.hasText(v)) {
            return v;
        }
        return StringUtils.hasText(c) ? c.trim() : null;
    }

    @Override
    public NodeStorageStackCheckRespVO checkStorageStackBySsh(Long nodeId) {
        ComputeNodeDO node = requireNode(nodeId);
        if (!StorageStackDeployUtil.isStorageRole(node.getNodeRole())) {
            throw exception(STORAGE_NODE_ROLE_INVALID);
        }
        return runHealthCheck(node);
    }

    @Override
    public NodeStorageMountCheckRespVO checkStorageMountBySsh(Long nodeId) {
        ComputeNodeDO node = requireNode(nodeId);
        if (!StorageStackDeployUtil.isClientMountRole(node.getNodeRole())) {
            throw exception(STORAGE_NODE_ROLE_INVALID);
        }
        NodeSshCredential credential = loadSshCredential(nodeId);
        int sshPort = ComputeNodeServiceImpl.resolveSshPort(node);

        NodeStorageMountCheckRespVO resp = new NodeStorageMountCheckRespVO();
        List<NodeMediaRemoteDeployRespVO.DeployStep> steps = new ArrayList<>();
        resp.setSteps(steps);

        try (SshSessionHelper ssh = openSshSession(node, credential, sshPort)) {
            steps.add(runStep("SSH 连接", "success", "已连接 " + node.getHost() + ":" + sshPort));
            HealthProbe probe = probeHealth(ssh, node);
            steps.add(probe.mountStep);
            resp.setMountReady(probe.mountReady);
            resp.setSuccess(true);
            resp.setMessage(buildMountCheckMessage(probe, node));
            return resp;
        } catch (Exception e) {
            return buildMountCheckFailure(resp, steps, node, sshPort, e);
        }
    }

    @Override
    public NodeMediaRemoteDeployRespVO deployStorageOsdBySsh(Long nodeId) {
        ComputeNodeDO node = requireNode(nodeId);
        if (!StorageStackDeployUtil.isStorageRole(node.getNodeRole())) {
            throw exception(STORAGE_NODE_ROLE_INVALID);
        }
        return deployWithScript(node, "NFS 服务端", StorageStackDeployUtil.buildOsdInstallScript(node), "NFS_SERVER_OK");
    }

    @Override
    public NodeMediaRemoteDeployRespVO deployStorageClientBySsh(Long nodeId) {
        ComputeNodeDO node = requireNode(nodeId);
        if (!StorageStackDeployUtil.isClientMountRole(node.getNodeRole())) {
            throw exception(STORAGE_NODE_ROLE_INVALID);
        }
        return deployWithScript(node, "NFS 客户端挂载", StorageStackDeployUtil.buildClientInstallScript(node), "CLIENT_MOUNT_OK");
    }

    @Override
    public NodeMediaRemoteDeployRespVO deployStoragePoolBySsh(Long nodeId) {
        ComputeNodeDO node = requireNode(nodeId);
        if (!StorageStackDeployUtil.isStorageRole(node.getNodeRole())) {
            throw exception(STORAGE_NODE_ROLE_INVALID);
        }
        return deployWithScript(node, "初始化 NFS Export", StorageStackDeployUtil.buildPoolCreateScript(node), "NFS_SERVER_OK");
    }

    @Override
    public NodeMediaRemoteDeployRespVO stopStorageOsdBySsh(Long nodeId) {
        ComputeNodeDO node = requireNode(nodeId);
        if (!StorageStackDeployUtil.isStorageRole(node.getNodeRole())) {
            throw exception(STORAGE_NODE_ROLE_INVALID);
        }
        NodeSshCredential credential = loadSshCredential(nodeId);
        int sshPort = ComputeNodeServiceImpl.resolveSshPort(node);
        NodeMediaRemoteDeployRespVO resp = new NodeMediaRemoteDeployRespVO();
        List<NodeMediaRemoteDeployRespVO.DeployStep> steps = new ArrayList<>();
        resp.setSteps(steps);
        try (SshSessionHelper ssh = openSshSession(node, credential, sshPort)) {
            steps.add(runStep("SSH 连接", "success", "已连接 " + node.getHost() + ":" + sshPort));
            String script = "#!/usr/bin/env bash\nset -euo pipefail\n"
                    + "systemctl stop nfs-server 2>/dev/null || systemctl stop nfs-kernel-server 2>/dev/null || true\n"
                    + "echo STOP_NFS_OK\n";
            SshSessionHelper.SshExecResult result = execRemoteScript(ssh, script, OPS_TIMEOUT_MS);
            NodeMediaRemoteDeployRespVO.DeployStep step = new NodeMediaRemoteDeployRespVO.DeployStep();
            step.setName("停止 NFS 服务");
            step.setOutput(trimOutput(result.combinedOutput(), 4000));
            boolean ok = result.isSuccess() && result.combinedOutput().contains("STOP_NFS_OK");
            step.setStatus(ok ? "success" : "failed");
            steps.add(step);
            resp.setSuccess(ok);
            resp.setMessage(ok ? "NFS 服务已停止" : "停止 NFS 失败");
            return resp;
        } catch (Exception e) {
            return buildDeployFailure(resp, steps, node, sshPort, "停止 NFS", e);
        }
    }

    @Override
    public NodeMediaRemoteDeployRespVO unmountStorageBySsh(Long nodeId) {
        ComputeNodeDO node = requireNode(nodeId);
        if (!StorageStackDeployUtil.isClientMountRole(node.getNodeRole())) {
            throw exception(STORAGE_NODE_ROLE_INVALID);
        }
        String mountRoot = StorageStackDeployUtil.buildDeployEnvMap(node).get("MOUNT_ROOT");
        NodeSshCredential credential = loadSshCredential(nodeId);
        int sshPort = ComputeNodeServiceImpl.resolveSshPort(node);
        NodeMediaRemoteDeployRespVO resp = new NodeMediaRemoteDeployRespVO();
        List<NodeMediaRemoteDeployRespVO.DeployStep> steps = new ArrayList<>();
        resp.setSteps(steps);
        try (SshSessionHelper ssh = openSshSession(node, credential, sshPort)) {
            steps.add(runStep("SSH 连接", "success", "已连接 " + node.getHost() + ":" + sshPort));
            String script = "#!/usr/bin/env bash\nset -euo pipefail\n"
                    + "MOUNT_ROOT=\"" + mountRoot.replace("\"", "") + "\"\n"
                    + "if mountpoint -q \"${MOUNT_ROOT}\" 2>/dev/null; then umount \"${MOUNT_ROOT}\" || true; fi\n"
                    + "echo UNMOUNT_OK\n";
            SshSessionHelper.SshExecResult result = execRemoteScript(ssh, script, OPS_TIMEOUT_MS);
            NodeMediaRemoteDeployRespVO.DeployStep step = new NodeMediaRemoteDeployRespVO.DeployStep();
            step.setName("卸载 CephFS");
            step.setOutput(trimOutput(result.combinedOutput(), 4000));
            boolean ok = result.isSuccess() && result.combinedOutput().contains("UNMOUNT_OK");
            step.setStatus(ok ? "success" : "failed");
            steps.add(step);
            resp.setSuccess(ok);
            resp.setMessage(ok ? "CephFS 已卸载" : "卸载 CephFS 失败");
            return resp;
        } catch (Exception e) {
            return buildDeployFailure(resp, steps, node, sshPort, "卸载 CephFS", e);
        }
    }

    private NodeStorageStackCheckRespVO runHealthCheck(ComputeNodeDO node) {
        NodeSshCredential credential = loadSshCredential(node.getId());
        int sshPort = ComputeNodeServiceImpl.resolveSshPort(node);
        NodeStorageStackCheckRespVO resp = new NodeStorageStackCheckRespVO();
        List<NodeMediaRemoteDeployRespVO.DeployStep> steps = new ArrayList<>();
        resp.setSteps(steps);

        try (SshSessionHelper ssh = openSshSession(node, credential, sshPort)) {
            steps.add(runStep("SSH 连接", "success", "已连接 " + node.getHost() + ":" + sshPort));
            HealthProbe probe = probeHealth(ssh, node);
            steps.add(probe.nfsServerStep);
            steps.add(probe.nfsExportStep);
            steps.add(probe.nfsPortStep);
            steps.add(probe.poolStep);
            steps.add(probe.mountStep);

            resp.setCephHealthy(probe.cephHealthy);
            resp.setOsdRunning(probe.osdRunning);
            resp.setPoolExists(probe.poolExists);
            resp.setCephfsReady(probe.cephfsReady);
            resp.setMountReady(probe.mountReady);
            boolean deployed = Boolean.TRUE.equals(probe.nfsExportReady)
                    && Boolean.TRUE.equals(probe.mountReady);
            resp.setDeployed(deployed);
            resp.setSuccess(true);
            resp.setMessage(buildStackCheckMessage(resp, node));
            return resp;
        } catch (Exception e) {
            log.error("Ceph SSH 检测失败 nodeId={} host={}:{}", node.getId(), node.getHost(), sshPort, e);
            NodeMediaRemoteDeployRespVO.DeployStep fail = new NodeMediaRemoteDeployRespVO.DeployStep();
            fail.setName(steps.isEmpty() ? "SSH 连接" : "检测中断");
            fail.setStatus("failed");
            String detail = e.getMessage() != null ? e.getMessage() : e.getClass().getSimpleName();
            fail.setOutput("连接 " + node.getHost() + ":" + sshPort + " 失败: " + detail);
            steps.add(fail);
            resp.setSuccess(false);
            resp.setDeployed(false);
            resp.setMessage(fail.getOutput());
            return resp;
        }
    }

    private NodeMediaRemoteDeployRespVO deployWithScript(
            ComputeNodeDO node, String phaseName, String scriptBody, String successToken) {
        NodeSshCredential credential = loadSshCredential(node.getId());
        int sshPort = ComputeNodeServiceImpl.resolveSshPort(node);
        String sourceRoot = resolveStorageClusterSource();

        NodeMediaRemoteDeployRespVO resp = new NodeMediaRemoteDeployRespVO();
        List<NodeMediaRemoteDeployRespVO.DeployStep> steps = new ArrayList<>();
        resp.setSteps(steps);

        try (SshSessionHelper ssh = openSshSession(node, credential, sshPort)) {
            steps.add(runStep("SSH 连接", "success", "已连接 " + node.getHost() + ":" + sshPort));
            steps.add(syncStorageCluster(ssh, sourceRoot));
            SshSessionHelper.SshExecResult result = execRemoteScript(ssh, scriptBody, DEPLOY_TIMEOUT_MS);
            NodeMediaRemoteDeployRespVO.DeployStep deployStep = new NodeMediaRemoteDeployRespVO.DeployStep();
            deployStep.setName(phaseName);
            deployStep.setOutput(trimOutput(result.combinedOutput(), 8000));
            boolean ok = result.isSuccess() && result.combinedOutput().contains(successToken);
            deployStep.setStatus(ok ? "success" : "failed");
            steps.add(deployStep);
            resp.setSuccess(ok);
            resp.setMessage(ok ? phaseName + " 完成" : phaseName + " 失败");
            return resp;
        } catch (Exception e) {
            return buildDeployFailure(resp, steps, node, sshPort, phaseName, e);
        }
    }

    private HealthProbe probeHealth(SshSessionHelper ssh, ComputeNodeDO node) throws Exception {
        String sourceRoot = resolveStorageClusterSource();
        syncStorageCluster(ssh, sourceRoot);
        SshSessionHelper.SshExecResult result = execRemoteScript(
                ssh, StorageStackDeployUtil.buildHealthCheckScript(node), CHECK_TIMEOUT_MS);
        String out = result.combinedOutput();

        HealthProbe probe = new HealthProbe();
        probe.nfsServerStep = stepFromToken("NFS 服务端", out, "NFS_SERVER_CLI_OK", "NFS_SERVER_CLI_MISSING", "未安装 nfs-kernel-server");
        probe.nfsExportStep = stepFromToken("NFS Export", out, "NFS_EXPORT_OK", "NFS_EXPORT_MISSING", "Export 未配置");
        probe.nfsPortStep = stepFromToken("NFS 2049", out, "NFS_PORT_OK", "NFS_PORT_MISSING", "2049 未监听");
        boolean subOk = out.contains("MOUNT_ALERT_IMAGES_OK") && out.contains("MOUNT_PLAYBACKS_OK");
        probe.poolStep = runStep("媒体子目录", subOk ? "success" : "failed",
                subOk ? "alert_images / playbacks / snaps 已就绪" : "子目录未完整创建");
        boolean mountOk = out.contains("MOUNT_ROOT_OK");
        probe.mountStep = runStep("NFS 挂载", mountOk ? "success" : "failed",
                mountOk ? "挂载点 " + StorageStackDeployUtil.buildDeployEnvMap(node).get("MOUNT_ROOT") + " 已就绪"
                        : "NFS 未挂载");

        probe.nfsServerReady = out.contains("NFS_SERVER_CLI_OK") || out.contains("NFS_EXPORT_OK");
        probe.nfsExportReady = out.contains("NFS_EXPORT_OK");
        probe.mountReady = mountOk;
        probe.poolExists = subOk;
        probe.cephHealthy = probe.nfsServerReady;
        probe.osdRunning = out.contains("NFS_PORT_OK");
        probe.cephfsReady = mountOk;
        return probe;
    }

    private NodeMediaRemoteDeployRespVO.DeployStep stepFromToken(
            String name, String output, String okToken, String failToken, String failHint) {
        if (output.contains(okToken)) {
            return runStep(name, "success", name + " 正常");
        }
        if (output.contains(failToken)) {
            return runStep(name, "failed", failHint);
        }
        return runStep(name, "failed", name + " 状态未知");
    }

    private NodeMediaRemoteDeployRespVO.DeployStep syncStorageCluster(SshSessionHelper ssh, String sourceRoot)
            throws Exception {
        String remoteRoot = StorageStackDeployUtil.remoteClusterRoot();
        ssh.ensureRemoteDir(remoteRoot);
        int count = 0;
        for (String relative : SYNC_RELATIVE_FILES) {
            File local = new File(sourceRoot, relative);
            if (!local.isFile()) {
                throw exception(STORAGE_CLUSTER_SOURCE_NOT_FOUND);
            }
            ssh.uploadFile(local.getAbsolutePath(), remoteRoot + "/" + relative);
            ssh.exec("chmod +x " + remoteRoot + "/" + relative, 10000);
            count++;
        }
        return runStep("同步 storage-cluster", "success",
                "已上传 " + count + " 个 NFS 脚本至 " + remoteRoot);
    }

    private String resolveStorageClusterSource() {
        if (storageClusterSourcePath != null && !storageClusterSourcePath.isBlank()) {
            File dir = new File(storageClusterSourcePath);
            if (dir.isDirectory()) {
                return dir.getAbsolutePath();
            }
        }
        String[] candidates = {
                "/opt/easyaiot/.scripts/media-cluster/nfs",
                System.getProperty("user.dir") + "/.scripts/media-cluster/nfs",
                System.getProperty("user.dir") + "/../.scripts/media-cluster/nfs",
        };
        for (String path : candidates) {
            File check = new File(path, "check_nfs_health.sh");
            if (check.isFile()) {
                return new File(path).getAbsolutePath();
            }
        }
        throw exception(STORAGE_CLUSTER_SOURCE_NOT_FOUND);
    }

    private String buildStackCheckMessage(NodeStorageStackCheckRespVO resp, ComputeNodeDO node) {
        String mount = StorageStackDeployUtil.buildDeployEnvMap(node).get("MOUNT_ROOT");
        if (Boolean.TRUE.equals(resp.getDeployed())) {
            return "NFS 存储已就绪：Export 正常，客户端已挂载至 " + mount;
        }
        if (Boolean.TRUE.equals(resp.getCephHealthy())) {
            return "NFS 服务端正常，但客户端未挂载。请执行 NFS 客户端挂载";
        }
        if (Boolean.TRUE.equals(resp.getMountReady())) {
            return "NFS 已挂载，但服务端状态需检查";
        }
        return "NFS 存储未就绪，请完成服务端 Export 与客户端挂载";
    }

    private String buildMountCheckMessage(HealthProbe probe, ComputeNodeDO node) {
        String mount = StorageStackDeployUtil.buildDeployEnvMap(node).get("MOUNT_ROOT");
        if (Boolean.TRUE.equals(probe.mountReady)) {
            return "NFS 已挂载至 " + mount;
        }
        return "NFS 未挂载至 " + mount + "，请执行客户端挂载部署";
    }

    private ComputeNodeDO requireNode(Long nodeId) {
        ComputeNodeDO node = computeNodeMapper.selectById(nodeId);
        if (node == null) {
            throw exception(COMPUTE_NODE_NOT_EXISTS);
        }
        return node;
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

    private static final class HealthProbe {
        private NodeMediaRemoteDeployRespVO.DeployStep nfsServerStep;
        private NodeMediaRemoteDeployRespVO.DeployStep nfsExportStep;
        private NodeMediaRemoteDeployRespVO.DeployStep nfsPortStep;
        private NodeMediaRemoteDeployRespVO.DeployStep poolStep;
        private NodeMediaRemoteDeployRespVO.DeployStep mountStep;
        private Boolean nfsServerReady;
        private Boolean nfsExportReady;
        private Boolean cephHealthy;
        private Boolean osdRunning;
        private Boolean poolExists;
        private Boolean cephfsReady;
        private Boolean mountReady;
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
        String tmpScript = "/tmp/easyaiot-storage-op-" + System.currentTimeMillis() + ".sh";
        return ssh.exec(
                "echo " + encoded + " | base64 -d > " + tmpScript
                        + " && chmod +x " + tmpScript
                        + " && bash " + tmpScript
                        + " ; rm -f " + tmpScript,
                timeoutMs);
    }

    private NodeMediaRemoteDeployRespVO buildDeployFailure(
            NodeMediaRemoteDeployRespVO resp,
            List<NodeMediaRemoteDeployRespVO.DeployStep> steps,
            ComputeNodeDO node,
            int sshPort,
            String stepName,
            Exception e) {
        log.error("Ceph SSH 操作失败 nodeId={} host={}:{} step={}",
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

    private NodeStorageMountCheckRespVO buildMountCheckFailure(
            NodeStorageMountCheckRespVO resp,
            List<NodeMediaRemoteDeployRespVO.DeployStep> steps,
            ComputeNodeDO node,
            int sshPort,
            Exception e) {
        NodeMediaRemoteDeployRespVO.DeployStep fail = new NodeMediaRemoteDeployRespVO.DeployStep();
        fail.setName(steps.isEmpty() ? "SSH 连接" : "检测中断");
        fail.setStatus("failed");
        String detail = e.getMessage() != null ? e.getMessage() : e.getClass().getSimpleName();
        fail.setOutput("连接 " + node.getHost() + ":" + sshPort + " 失败: " + detail);
        steps.add(fail);
        resp.setSuccess(false);
        resp.setMountReady(false);
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

}
