package com.basiclab.iot.node.service.impl;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.json.JsonUtils;
import com.basiclab.iot.node.dal.dataobject.ComputeNodeDO;
import com.basiclab.iot.node.dal.dataobject.EdgeNodeDO;
import com.basiclab.iot.node.dal.dataobject.NodeSshCredentialDO;
import com.basiclab.iot.node.dal.dataobject.NodeStorageOpLogDO;
import com.basiclab.iot.node.dal.pgsql.ComputeNodeMapper;
import com.basiclab.iot.node.dal.pgsql.EdgeNodeMapper;
import com.basiclab.iot.node.dal.pgsql.NodeSshCredentialMapper;
import com.basiclab.iot.node.dal.pgsql.NodeStorageOpLogMapper;
import com.basiclab.iot.node.domain.vo.NodeCephTopologyRespVO;
import com.basiclab.iot.node.domain.vo.NodeMediaRemoteDeployRespVO;
import com.basiclab.iot.node.domain.vo.NodeNfsBatchRefreshReqVO;
import com.basiclab.iot.node.domain.vo.NodeNfsBatchRefreshRespVO;
import com.basiclab.iot.node.domain.vo.NodeNfsClusterAssignReqVO;
import com.basiclab.iot.node.domain.vo.NodeStorageFileDownloadResult;
import com.basiclab.iot.node.domain.vo.NodeStorageFileEntryVO;
import com.basiclab.iot.node.domain.vo.NodeStorageFileListRespVO;
import com.basiclab.iot.node.domain.vo.NodeStorageFileOpsRespVO;
import com.basiclab.iot.node.domain.vo.NodeStorageMountCheckRespVO;
import com.basiclab.iot.node.domain.vo.NodeStorageOpLogPageReqVO;
import com.basiclab.iot.node.domain.vo.NodeStorageOpLogRespVO;
import com.basiclab.iot.node.domain.vo.NodeStorageStackCheckRespVO;
import com.basiclab.iot.node.domain.vo.NodeWorkloadBundleNodeResultVO;
import com.basiclab.iot.node.service.NodeStorageService;
import com.basiclab.iot.node.util.CredentialEncryptUtil;
import com.basiclab.iot.node.util.SshSessionHelper;
import com.basiclab.iot.node.util.StorageStackDeployUtil;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.multipart.MultipartFile;

import javax.annotation.Resource;
import java.io.File;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneId;
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
import static com.basiclab.iot.node.enums.ErrorCodeConstants.STORAGE_FILE_EXISTS;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.STORAGE_FILE_NAME_INVALID;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.STORAGE_FILE_NOT_FOUND;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.STORAGE_FILE_PATH_INVALID;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.STORAGE_FILE_ROOT_FORBIDDEN;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.STORAGE_FILE_TOO_LARGE;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.STORAGE_NODE_ROLE_INVALID;

@Slf4j
@Service
@Validated
public class NodeStorageServiceImpl implements NodeStorageService {

    private static final int DEPLOY_TIMEOUT_MS = 900000;
    private static final int CHECK_TIMEOUT_MS = 120000;
    private static final int OPS_TIMEOUT_MS = 180000;
    private static final int OP_LOG_STEPS_MAX = 32000;
    private static final int OP_LOG_KEEP_PER_NODE = 100;
    private static final long FILE_DOWNLOAD_MAX_BYTES = 50L * 1024 * 1024;
    private static final String[] SYNC_RELATIVE_FILES = {
            "install_nfs_server.sh",
            "install_nfs_client.sh",
            "mount-all.sh",
            "check_nfs_health.sh",
    };

    /** 批量刷新时覆盖单次检测的 op_type */
    private final ThreadLocal<String> opLogTypeOverride = new ThreadLocal<>();

    @Resource
    private ComputeNodeMapper computeNodeMapper;
    @Resource
    private EdgeNodeMapper edgeNodeMapper;
    @Resource
    private NodeSshCredentialMapper nodeSshCredentialMapper;
    @Resource
    private NodeStorageOpLogMapper nodeStorageOpLogMapper;

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
        int unprobed = 0;
        String lastProbeAt = null;
        for (NodeCephTopologyRespVO.TopologyNodeVO n : nodes) {
            if ("storage_nfs".equals(n.getKind())) {
                storageCnt++;
            } else if ("nfs_client".equals(n.getKind())) {
                clientCnt++;
            }
            if ("offline".equalsIgnoreCase(n.getStatus()) || "pending".equalsIgnoreCase(n.getStatus())) {
                offline++;
            }
            if (!"platform".equals(n.getKind()) && !StringUtils.hasText(n.getNfsProbeAt())) {
                unprobed++;
            }
            if (StringUtils.hasText(n.getNfsProbeAt())) {
                if (lastProbeAt == null || n.getNfsProbeAt().compareTo(lastProbeAt) > 0) {
                    lastProbeAt = n.getNfsProbeAt();
                }
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
        summary.setUnprobedCount(unprobed);
        summary.setLastProbeAt(lastProbeAt);
        int coverageBase = clientCnt > 0 ? clientCnt : Math.max(ready + notReady, 0);
        if (coverageBase <= 0) {
            summary.setCoveragePercent(0);
        } else {
            // 覆盖率按客户端就绪计；若无纯客户端则以非 platform 就绪占比
            int readyClients = 0;
            int clientBase = 0;
            for (NodeCephTopologyRespVO.TopologyNodeVO n : nodes) {
                if ("nfs_client".equals(n.getKind())) {
                    clientBase++;
                    if (Boolean.TRUE.equals(n.getNfsMountReady())) {
                        readyClients++;
                    }
                }
            }
            if (clientBase > 0) {
                summary.setCoveragePercent((int) Math.round(readyClients * 100.0 / clientBase));
            } else {
                summary.setCoveragePercent((int) Math.round(ready * 100.0 / coverageBase));
            }
        }
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
        boolean hasProbe = StringUtils.hasText(firstNonBlank(tags.get("nfs_probe_at"), null));
        String readyTag = firstNonBlank(tags.get("nfs_mount_ready"), tags.get("ceph_mount_ready"), null);
        if (StringUtils.hasText(readyTag)) {
            String r = readyTag.trim().toLowerCase(Locale.ROOT);
            mountReady = "true".equals(r) || "1".equals(r) || "yes".equals(r) || "on".equals(r);
        } else if (edge != null && Boolean.TRUE.equals(edge.getCephMountReady())) {
            mountReady = true;
        } else if ("platform".equals(kind) && !hasProbe) {
            // 平台节点未探测时默认就绪；若已有探针则以探针为准
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
        vo.setNfsProbeAt(firstNonBlank(tags.get("nfs_probe_at"), null));
        vo.setNfsProbeSummary(firstNonBlank(tags.get("nfs_probe_summary"), null));
        vo.setNfsMountSource(firstNonBlank(tags.get("nfs_mount_source"), null));
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

    @Override
    public NodeNfsBatchRefreshRespVO batchRefreshBySsh(NodeNfsBatchRefreshReqVO req) {
        if (req == null) {
            req = new NodeNfsBatchRefreshReqVO();
        }
        boolean auto = Boolean.TRUE.equals(req.getAuto());
        String refreshType = auto ? "auto_refresh" : "refresh";
        List<Long> targetIds = req.getNodeIds();
        if (targetIds == null || targetIds.isEmpty()) {
            targetIds = new ArrayList<>();
            List<ComputeNodeDO> all = computeNodeMapper.selectList();
            if (all != null) {
                for (ComputeNodeDO n : all) {
                    if (n == null || n.getId() == null) {
                        continue;
                    }
                    String role = n.getNodeRole();
                    if (StorageStackDeployUtil.isStorageRole(role) || StorageStackDeployUtil.isClientMountRole(role)
                            || ComputeNodeServiceImpl.isPlatformNode(n)) {
                        targetIds.add(n.getId());
                    }
                }
            }
        }

        NodeNfsBatchRefreshRespVO resp = new NodeNfsBatchRefreshRespVO();
        List<NodeWorkloadBundleNodeResultVO> results = new ArrayList<>();
        int ok = 0;
        int fail = 0;
        int skipped = 0;
        opLogTypeOverride.set(refreshType);
        try {
            for (Long nodeId : targetIds) {
                if (nodeId == null) {
                    continue;
                }
                ComputeNodeDO node = computeNodeMapper.selectById(nodeId);
                NodeWorkloadBundleNodeResultVO item = new NodeWorkloadBundleNodeResultVO();
                item.setNodeId(nodeId);
                if (node == null) {
                    item.setSuccess(false);
                    item.setMessage("节点不存在");
                    fail++;
                    results.add(item);
                    continue;
                }
                item.setNodeName(node.getName());
                item.setHost(node.getHost());
                NodeSshCredentialDO cred = nodeSshCredentialMapper.selectByNodeId(nodeId);
                if (cred == null || !StringUtils.hasText(cred.getCredentialEnc())) {
                    item.setSuccess(true);
                    item.setMessage("跳过：未配置 SSH 凭据");
                    skipped++;
                    results.add(item);
                    writeOpLog(nodeId, refreshType, true, item.getMessage(), null);
                    continue;
                }
                try {
                    if (StorageStackDeployUtil.isStorageRole(node.getNodeRole())
                            || ComputeNodeServiceImpl.isPlatformNode(node)) {
                        NodeStorageStackCheckRespVO check = checkStorageStackBySsh(nodeId);
                        item.setSuccess(Boolean.TRUE.equals(check.getSuccess()));
                        item.setMessage(check.getMessage());
                        item.setSteps(check.getSteps());
                        if (Boolean.TRUE.equals(check.getSuccess())) {
                            ok++;
                        } else {
                            fail++;
                        }
                    } else {
                        NodeStorageMountCheckRespVO check = checkStorageMountBySsh(nodeId);
                        item.setSuccess(Boolean.TRUE.equals(check.getSuccess()));
                        item.setMessage(check.getMessage());
                        item.setSteps(check.getSteps());
                        if (Boolean.TRUE.equals(check.getSuccess())) {
                            ok++;
                        } else {
                            fail++;
                        }
                    }
                } catch (Exception e) {
                    item.setSuccess(false);
                    item.setMessage(e.getMessage() != null ? e.getMessage() : e.getClass().getSimpleName());
                    fail++;
                    writeOpLog(nodeId, refreshType, false, item.getMessage(), null);
                }
                results.add(item);
            }
        } finally {
            opLogTypeOverride.remove();
        }
        resp.setResults(results);
        resp.setSuccess(fail == 0);
        resp.setMessage(String.format("刷新完成：成功 %d，失败 %d，跳过 %d", ok, fail, skipped));
        writeOpLog(null, refreshType, fail == 0, resp.getMessage(), null);
        resp.setTopology(getCephTopology());
        return resp;
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
        if (!StorageStackDeployUtil.isStorageRole(node.getNodeRole())
                && !ComputeNodeServiceImpl.isPlatformNode(node)
                && !StorageStackDeployUtil.isClientMountRole(node.getNodeRole())) {
            throw exception(STORAGE_NODE_ROLE_INVALID);
        }
        return runHealthCheck(node);
    }

    @Override
    public NodeStorageMountCheckRespVO checkStorageMountBySsh(Long nodeId) {
        ComputeNodeDO node = requireNode(nodeId);
        if (!StorageStackDeployUtil.isClientMountRole(node.getNodeRole())
                && !ComputeNodeServiceImpl.isPlatformNode(node)) {
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
            if (probe.sourceStep != null) {
                steps.add(probe.sourceStep);
            }
            steps.add(probe.mountStep);
            if (probe.rwStep != null) {
                steps.add(probe.rwStep);
            }
            resp.setMountReady(probe.mountReady);
            resp.setSuccess(true);
            resp.setMessage(buildMountCheckMessage(probe, node));
            persistProbeResult(node, probe, resp.getMessage());
            writeOpLog(node.getId(), resolveOpType("check_mount"), true, resp.getMessage(), steps);
            return resp;
        } catch (Exception e) {
            NodeStorageMountCheckRespVO failResp = buildMountCheckFailure(resp, steps, node, sshPort, e);
            writeOpLog(node.getId(), resolveOpType("check_mount"), false, failResp.getMessage(), steps);
            return failResp;
        }
    }

    @Override
    public NodeMediaRemoteDeployRespVO deployStorageOsdBySsh(Long nodeId) {
        ComputeNodeDO node = requireNode(nodeId);
        if (!StorageStackDeployUtil.isStorageRole(node.getNodeRole())) {
            throw exception(STORAGE_NODE_ROLE_INVALID);
        }
        return deployWithScript(node, "NFS 服务端", StorageStackDeployUtil.buildOsdInstallScript(node),
                "NFS_SERVER_OK", "deploy_server");
    }

    @Override
    public NodeMediaRemoteDeployRespVO deployStorageClientBySsh(Long nodeId) {
        ComputeNodeDO node = requireNode(nodeId);
        if (!StorageStackDeployUtil.isClientMountRole(node.getNodeRole())) {
            throw exception(STORAGE_NODE_ROLE_INVALID);
        }
        return deployWithScript(node, "NFS 客户端挂载", StorageStackDeployUtil.buildClientInstallScript(node),
                "CLIENT_MOUNT_OK", "deploy_client");
    }

    @Override
    public NodeMediaRemoteDeployRespVO deployStoragePoolBySsh(Long nodeId) {
        ComputeNodeDO node = requireNode(nodeId);
        if (!StorageStackDeployUtil.isStorageRole(node.getNodeRole())) {
            throw exception(STORAGE_NODE_ROLE_INVALID);
        }
        return deployWithScript(node, "初始化 NFS Export", StorageStackDeployUtil.buildPoolCreateScript(node),
                "NFS_SERVER_OK", "deploy_export");
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
            step.setName("卸载 NFS");
            step.setOutput(trimOutput(result.combinedOutput(), 4000));
            boolean ok = result.isSuccess() && result.combinedOutput().contains("UNMOUNT_OK");
            step.setStatus(ok ? "success" : "failed");
            steps.add(step);
            resp.setSuccess(ok);
            resp.setMessage(ok ? "NFS 已卸载" : "卸载 NFS 失败");
            if (ok) {
                HealthProbe cleared = new HealthProbe();
                cleared.mountReady = false;
                cleared.rawOutput = "UNMOUNT_OK";
                persistProbeResult(node, cleared, "NFS 已卸载");
            }
            writeOpLog(node.getId(), "unmount", ok, resp.getMessage(), steps);
            return resp;
        } catch (Exception e) {
            NodeMediaRemoteDeployRespVO fail = buildDeployFailure(resp, steps, node, sshPort, "卸载 NFS", e);
            writeOpLog(node.getId(), "unmount", false, fail.getMessage(), steps);
            return fail;
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
            if (probe.sourceStep != null) {
                steps.add(probe.sourceStep);
            }
            steps.add(probe.poolStep);
            steps.add(probe.mountStep);
            if (probe.rwStep != null) {
                steps.add(probe.rwStep);
            }

            resp.setCephHealthy(probe.cephHealthy);
            resp.setOsdRunning(probe.osdRunning);
            resp.setPoolExists(probe.poolExists);
            resp.setCephfsReady(probe.cephfsReady);
            resp.setMountReady(probe.mountReady);
            boolean isServerRole = StorageStackDeployUtil.isStorageRole(node.getNodeRole())
                    || outIndicatesServerRole(probe.rawOutput);
            boolean deployed;
            if (isServerRole) {
                deployed = Boolean.TRUE.equals(probe.nfsExportReady) && Boolean.TRUE.equals(probe.mountReady);
            } else {
                deployed = Boolean.TRUE.equals(probe.mountReady);
            }
            resp.setDeployed(deployed);
            resp.setSuccess(true);
            resp.setMessage(buildStackCheckMessage(resp, node));
            persistProbeResult(node, probe, resp.getMessage());
            writeOpLog(node.getId(), resolveOpType("check_stack"), true, resp.getMessage(), steps);
            return resp;
        } catch (Exception e) {
            log.error("NFS SSH 检测失败 nodeId={} host={}:{}", node.getId(), node.getHost(), sshPort, e);
            NodeMediaRemoteDeployRespVO.DeployStep fail = new NodeMediaRemoteDeployRespVO.DeployStep();
            fail.setName(steps.isEmpty() ? "SSH 连接" : "检测中断");
            fail.setStatus("failed");
            String detail = e.getMessage() != null ? e.getMessage() : e.getClass().getSimpleName();
            fail.setOutput("连接 " + node.getHost() + ":" + sshPort + " 失败: " + detail);
            steps.add(fail);
            resp.setSuccess(false);
            resp.setDeployed(false);
            resp.setMessage(fail.getOutput());
            writeOpLog(node.getId(), resolveOpType("check_stack"), false, resp.getMessage(), steps);
            return resp;
        }
    }

    private NodeMediaRemoteDeployRespVO deployWithScript(
            ComputeNodeDO node, String phaseName, String scriptBody, String successToken, String opType) {
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
            if (ok) {
                try {
                    HealthProbe probe = probeHealth(ssh, node);
                    persistProbeResult(node, probe, resp.getMessage());
                    steps.add(probe.mountStep);
                } catch (Exception probeEx) {
                    log.warn("部署后探针失败 nodeId={}: {}", node.getId(), probeEx.getMessage());
                }
            }
            writeOpLog(node.getId(), opType, ok, resp.getMessage(), steps);
            return resp;
        } catch (Exception e) {
            NodeMediaRemoteDeployRespVO fail = buildDeployFailure(resp, steps, node, sshPort, phaseName, e);
            writeOpLog(node.getId(), opType, false, fail.getMessage(), steps);
            return fail;
        }
    }

    private HealthProbe probeHealth(SshSessionHelper ssh, ComputeNodeDO node) throws Exception {
        String sourceRoot = resolveStorageClusterSource();
        syncStorageCluster(ssh, sourceRoot);
        SshSessionHelper.SshExecResult result = execRemoteScript(
                ssh, StorageStackDeployUtil.buildHealthCheckScript(node), CHECK_TIMEOUT_MS);
        String out = result.combinedOutput();

        HealthProbe probe = new HealthProbe();
        probe.rawOutput = out;
        boolean clientRole = out.contains("NFS_ROLE_CLIENT")
                || (!StorageStackDeployUtil.isStorageRole(node.getNodeRole())
                && !out.contains("NFS_ROLE_SERVER"));

        if (clientRole && (out.contains("NFS_SERVER_CLI_SKIP_CLIENT") || out.contains("NFS_SERVER_CLI_MISSING"))) {
            probe.nfsServerStep = runStep("NFS 服务端", "success", "客户端节点，跳过服务端 CLI 检查");
        } else {
            probe.nfsServerStep = stepFromToken("NFS 服务端", out, "NFS_SERVER_CLI_OK", "NFS_SERVER_CLI_MISSING",
                    "未安装 nfs-kernel-server");
        }
        if (out.contains("NFS_EXPORT_SKIP_CLIENT")) {
            probe.nfsExportStep = runStep("NFS Export", "success", "客户端节点，跳过 Export 检查");
        } else {
            probe.nfsExportStep = stepFromToken("NFS Export", out, "NFS_EXPORT_OK", "NFS_EXPORT_MISSING", "Export 未配置");
        }
        if (out.contains("NFS_PORT_SKIP_CLIENT")) {
            probe.nfsPortStep = runStep("NFS 2049", "success", "客户端节点，跳过端口检查");
        } else {
            probe.nfsPortStep = stepFromToken("NFS 2049", out, "NFS_PORT_OK", "NFS_PORT_MISSING", "2049 未监听");
        }

        boolean subOk = out.contains("MOUNT_ALERT_IMAGES_OK") && out.contains("MOUNT_PLAYBACKS_OK");
        probe.poolStep = runStep("媒体子目录", subOk ? "success" : "failed",
                subOk ? "alert_images / playbacks / snaps 已就绪" : "子目录未完整创建");

        boolean mountOk = out.contains("MOUNT_ROOT_OK") || out.contains("MOUNT_LOCAL_BIND_OK");
        boolean sourceOk = out.contains("MOUNT_SOURCE_OK")
                || out.contains("MOUNT_LOCAL_BIND_OK")
                || out.contains("MOUNT_FSTYPE_LOCAL_OK");
        boolean sourceMismatch = out.contains("MOUNT_SOURCE_MISMATCH");
        boolean rwOk = out.contains("MOUNT_RW_OK");

        probe.mountSource = extractMountSource(out);
        if (sourceMismatch) {
            probe.sourceStep = runStep("挂载源", "failed",
                    "挂载源与配置不一致" + (probe.mountSource != null ? "：" + probe.mountSource : ""));
        } else if (sourceOk || mountOk) {
            probe.sourceStep = runStep("挂载源", "success",
                    probe.mountSource != null ? "源=" + probe.mountSource : "挂载源匹配或本机回退");
        } else {
            probe.sourceStep = runStep("挂载源", "failed", "未能确认挂载源");
        }

        probe.mountStep = runStep("NFS 挂载", mountOk ? "success" : "failed",
                mountOk ? "挂载点 " + StorageStackDeployUtil.buildDeployEnvMap(node).get("MOUNT_ROOT") + " 已就绪"
                        : "NFS 未挂载");
        probe.rwStep = runStep("读写探针", rwOk ? "success" : (mountOk ? "failed" : "failed"),
                rwOk ? "挂载根可写" : "挂载根不可写或未挂载");

        probe.nfsServerReady = out.contains("NFS_SERVER_CLI_OK") || out.contains("NFS_EXPORT_OK")
                || out.contains("NFS_SERVER_CLI_SKIP_CLIENT");
        probe.nfsExportReady = out.contains("NFS_EXPORT_OK") || out.contains("NFS_EXPORT_SKIP_CLIENT");
        // 客户端：挂载 + 源匹配（或本机回退）+ 读写；缺 RW 仍可视为未完全就绪
        probe.mountReady = mountOk && (sourceOk || !sourceMismatch) && rwOk;
        if (mountOk && sourceOk && !rwOk) {
            probe.mountReady = false;
        }
        if (mountOk && out.contains("MOUNT_LOCAL_BIND_OK") && rwOk) {
            probe.mountReady = true;
        }
        probe.poolExists = subOk;
        probe.cephHealthy = Boolean.TRUE.equals(probe.nfsServerReady)
                && (clientRole || out.contains("NFS_EXPORT_OK"));
        probe.osdRunning = out.contains("NFS_PORT_OK") || out.contains("NFS_PORT_SKIP_CLIENT");
        probe.cephfsReady = probe.mountReady;
        return probe;
    }

    private static boolean outIndicatesServerRole(String out) {
        return out != null && out.contains("NFS_ROLE_SERVER");
    }

    private static String extractMountSource(String out) {
        if (out == null) {
            return null;
        }
        for (String line : out.split("\\R")) {
            String trimmed = line.trim();
            if (trimmed.startsWith("MOUNT_SOURCE=")) {
                String val = trimmed.substring("MOUNT_SOURCE=".length()).trim();
                return StringUtils.hasText(val) ? val : null;
            }
        }
        return null;
    }

    private void persistProbeResult(ComputeNodeDO node, HealthProbe probe, String summary) {
        if (node == null || node.getId() == null || probe == null) {
            return;
        }
        ComputeNodeDO latest = computeNodeMapper.selectById(node.getId());
        if (latest == null) {
            return;
        }
        Map<String, String> tags = latest.getTags() != null ? new HashMap<>(latest.getTags()) : new HashMap<>();
        boolean ready = Boolean.TRUE.equals(probe.mountReady);
        String readyStr = ready ? "true" : "false";
        tags.put("nfs_mount_ready", readyStr);
        tags.put("ceph_mount_ready", readyStr);
        String at = Instant.now().toString();
        tags.put("nfs_probe_at", at);
        tags.put("nfs_probe_ok", readyStr);
        String shortSummary = summary != null ? summary.trim() : "";
        if (shortSummary.length() > 240) {
            shortSummary = shortSummary.substring(0, 240);
        }
        tags.put("nfs_probe_summary", shortSummary);
        if (StringUtils.hasText(probe.mountSource)) {
            tags.put("nfs_mount_source", probe.mountSource.trim());
        }
        latest.setTags(tags);
        computeNodeMapper.updateById(latest);
        node.setTags(tags);

        EdgeNodeDO edge = edgeNodeMapper.selectByComputeNodeId(latest.getId());
        if (edge != null) {
            edge.setCephMountReady(ready);
            edgeNodeMapper.updateById(edge);
        }
    }

    private String resolveOpType(String defaultType) {
        String override = opLogTypeOverride.get();
        return StringUtils.hasText(override) ? override : defaultType;
    }

    private void writeOpLog(
            Long nodeId,
            String opType,
            boolean success,
            String message,
            List<NodeMediaRemoteDeployRespVO.DeployStep> steps) {
        try {
            NodeStorageOpLogDO row = new NodeStorageOpLogDO();
            row.setNodeId(nodeId);
            row.setOpType(opType != null ? opType : "refresh");
            row.setSuccess(success);
            String msg = message != null ? message.trim() : "";
            if (msg.length() > 1000) {
                msg = msg.substring(0, 1000);
            }
            row.setMessage(msg);
            if (steps != null && !steps.isEmpty()) {
                String json = JsonUtils.toJsonString(steps);
                if (json != null && json.length() > OP_LOG_STEPS_MAX) {
                    json = json.substring(0, OP_LOG_STEPS_MAX);
                }
                row.setStepsJson(json);
            }
            nodeStorageOpLogMapper.insert(row);
            if (nodeId != null) {
                trimOpLogs(nodeId);
            }
        } catch (Exception e) {
            log.warn("写入 NFS 操作日志失败 nodeId={} opType={}: {}", nodeId, opType, e.getMessage());
        }
    }

    private void trimOpLogs(Long nodeId) {
        long count = nodeStorageOpLogMapper.countByNodeId(nodeId);
        if (count <= OP_LOG_KEEP_PER_NODE) {
            return;
        }
        List<NodeStorageOpLogDO> keepNewest = nodeStorageOpLogMapper.selectList(
                new com.basiclab.iot.common.core.query.LambdaQueryWrapperX<NodeStorageOpLogDO>()
                        .eq(NodeStorageOpLogDO::getNodeId, nodeId)
                        .orderByDesc(NodeStorageOpLogDO::getCreateTime)
                        .last("LIMIT " + OP_LOG_KEEP_PER_NODE));
        if (keepNewest == null || keepNewest.isEmpty()) {
            return;
        }
        Set<Long> keepIds = new HashSet<>();
        for (NodeStorageOpLogDO row : keepNewest) {
            if (row.getId() != null) {
                keepIds.add(row.getId());
            }
        }
        List<NodeStorageOpLogDO> all = nodeStorageOpLogMapper.selectList(NodeStorageOpLogDO::getNodeId, nodeId);
        if (all == null) {
            return;
        }
        for (NodeStorageOpLogDO row : all) {
            if (row.getId() != null && !keepIds.contains(row.getId())) {
                nodeStorageOpLogMapper.deleteById(row.getId());
            }
        }
    }

    @Override
    public PageResult<NodeStorageOpLogRespVO> getOpLogPage(NodeStorageOpLogPageReqVO req) {
        if (req == null) {
            req = new NodeStorageOpLogPageReqVO();
        }
        PageResult<NodeStorageOpLogDO> page = nodeStorageOpLogMapper.selectPage(req);
        List<NodeStorageOpLogRespVO> list = new ArrayList<>();
        if (page.getList() != null) {
            for (NodeStorageOpLogDO row : page.getList()) {
                list.add(toOpLogResp(row));
            }
        }
        return new PageResult<>(list, page.getTotal());
    }

    private NodeStorageOpLogRespVO toOpLogResp(NodeStorageOpLogDO row) {
        NodeStorageOpLogRespVO vo = new NodeStorageOpLogRespVO();
        vo.setId(row.getId());
        vo.setNodeId(row.getNodeId());
        vo.setOpType(row.getOpType());
        vo.setSuccess(row.getSuccess());
        vo.setMessage(row.getMessage());
        vo.setCreateTime(row.getCreateTime());
        if (StringUtils.hasText(row.getStepsJson())) {
            try {
                List<NodeMediaRemoteDeployRespVO.DeployStep> steps = JsonUtils.parseArray(
                        row.getStepsJson(), NodeMediaRemoteDeployRespVO.DeployStep.class);
                if (steps != null) {
                    vo.setSteps(steps);
                }
            } catch (Exception ignore) {
                // keep empty steps
            }
        }
        return vo;
    }

    @Override
    public NodeStorageFileListRespVO listMediaFiles(Long nodeId, String relativePath) {
        ComputeNodeDO node = requireNode(nodeId);
        String mountRoot = resolveNodeMountRoot(node);
        String abs = resolveJailAbsolutePath(mountRoot, relativePath);
        NodeSshCredential credential = loadSshCredential(nodeId);
        int sshPort = ComputeNodeServiceImpl.resolveSshPort(node);
        NodeStorageFileListRespVO resp = new NodeStorageFileListRespVO();
        resp.setMountRoot(mountRoot);
        resp.setAbsolutePath(abs);
        resp.setRelativePath(toRelativePath(mountRoot, abs));
        try (SshSessionHelper ssh = openSshSession(node, credential, sshPort)) {
            List<SshSessionHelper.SftpEntry> entries = ssh.listDir(abs);
            List<NodeStorageFileEntryVO> vos = new ArrayList<>();
            for (SshSessionHelper.SftpEntry e : entries) {
                NodeStorageFileEntryVO vo = new NodeStorageFileEntryVO();
                vo.setName(e.name);
                vo.setDirectory(e.directory);
                vo.setSize(e.size);
                if (e.mtimeSec > 0) {
                    vo.setMtime(LocalDateTime.ofInstant(Instant.ofEpochSecond(e.mtimeSec), ZoneId.systemDefault()));
                }
                vo.setRelativePath(toRelativePath(mountRoot, joinPath(abs, e.name)));
                vos.add(vo);
            }
            resp.setEntries(vos);
            return resp;
        } catch (Exception e) {
            log.error("列出媒体文件失败 nodeId={} path={}", nodeId, abs, e);
            throw exception(STORAGE_FILE_PATH_INVALID);
        }
    }

    @Override
    public NodeStorageFileDownloadResult downloadMediaFile(Long nodeId, String relativePath) {
        ComputeNodeDO node = requireNode(nodeId);
        String mountRoot = resolveNodeMountRoot(node);
        String abs = resolveJailAbsolutePath(mountRoot, relativePath);
        NodeSshCredential credential = loadSshCredential(nodeId);
        int sshPort = ComputeNodeServiceImpl.resolveSshPort(node);
        try (SshSessionHelper ssh = openSshSession(node, credential, sshPort)) {
            SshSessionHelper.SftpEntry stat = ssh.stat(abs);
            if (stat == null || stat.directory) {
                throw exception(STORAGE_FILE_NOT_FOUND);
            }
            if (stat.size > FILE_DOWNLOAD_MAX_BYTES) {
                throw exception(STORAGE_FILE_TOO_LARGE);
            }
            byte[] bytes = ssh.downloadBytes(abs);
            NodeStorageFileDownloadResult result = new NodeStorageFileDownloadResult();
            result.setFileName(stat.name);
            result.setSize(stat.size);
            result.setContent(bytes);
            return result;
        } catch (RuntimeException e) {
            throw e;
        } catch (Exception e) {
            log.error("下载媒体文件失败 nodeId={} path={}", nodeId, abs, e);
            throw exception(STORAGE_FILE_NOT_FOUND);
        }
    }

    @Override
    public NodeStorageFileOpsRespVO mkdirMediaDir(Long nodeId, String parentRelativePath, String name) {
        String dirName = sanitizeEntryName(name);
        ComputeNodeDO node = requireNode(nodeId);
        String mountRoot = resolveNodeMountRoot(node);
        String parentAbs = resolveJailAbsolutePath(mountRoot, parentRelativePath);
        String childRel = toRelativePath(mountRoot, joinPath(parentAbs, dirName));
        String childAbs = resolveJailAbsolutePath(mountRoot, childRel);
        NodeSshCredential credential = loadSshCredential(nodeId);
        int sshPort = ComputeNodeServiceImpl.resolveSshPort(node);
        NodeStorageFileOpsRespVO resp = new NodeStorageFileOpsRespVO();
        try (SshSessionHelper ssh = openSshSession(node, credential, sshPort)) {
            SshSessionHelper.SftpEntry existing = ssh.stat(childAbs);
            if (existing != null) {
                throw exception(STORAGE_FILE_EXISTS);
            }
            ssh.mkdir(childAbs);
            resp.setSuccess(true);
            resp.setMessage("已创建目录 " + dirName);
            resp.setRelativePath(childRel);
            writeOpLog(nodeId, "mkdir", true, resp.getMessage() + " @ " + childRel, null);
            return resp;
        } catch (RuntimeException e) {
            writeOpLog(nodeId, "mkdir", false, e.getMessage(), null);
            throw e;
        } catch (Exception e) {
            log.error("创建目录失败 nodeId={} path={}", nodeId, childAbs, e);
            writeOpLog(nodeId, "mkdir", false, e.getMessage(), null);
            throw exception(STORAGE_FILE_PATH_INVALID);
        }
    }

    @Override
    public NodeStorageFileOpsRespVO uploadMediaFile(Long nodeId, String parentRelativePath, MultipartFile file) {
        if (file == null || file.isEmpty()) {
            throw exception(STORAGE_FILE_NAME_INVALID);
        }
        String original = file.getOriginalFilename();
        String fileName = sanitizeEntryName(original != null ? original : "upload.bin");
        if (file.getSize() > FILE_DOWNLOAD_MAX_BYTES) {
            throw exception(STORAGE_FILE_TOO_LARGE);
        }
        ComputeNodeDO node = requireNode(nodeId);
        String mountRoot = resolveNodeMountRoot(node);
        String parentAbs = resolveJailAbsolutePath(mountRoot, parentRelativePath);
        String childRel = toRelativePath(mountRoot, joinPath(parentAbs, fileName));
        String childAbs = resolveJailAbsolutePath(mountRoot, childRel);
        NodeSshCredential credential = loadSshCredential(nodeId);
        int sshPort = ComputeNodeServiceImpl.resolveSshPort(node);
        NodeStorageFileOpsRespVO resp = new NodeStorageFileOpsRespVO();
        try (SshSessionHelper ssh = openSshSession(node, credential, sshPort)) {
            SshSessionHelper.SftpEntry existing = ssh.stat(childAbs);
            if (existing != null && existing.directory) {
                throw exception(STORAGE_FILE_EXISTS);
            }
            byte[] bytes = file.getBytes();
            ssh.uploadBytes(childAbs, bytes);
            resp.setSuccess(true);
            resp.setMessage((existing != null ? "已覆盖上传 " : "已上传 ") + fileName + "（" + bytes.length + " 字节）");
            resp.setRelativePath(childRel);
            writeOpLog(nodeId, "upload", true, resp.getMessage() + " @ " + childRel, null);
            return resp;
        } catch (RuntimeException e) {
            writeOpLog(nodeId, "upload", false, e.getMessage(), null);
            throw e;
        } catch (Exception e) {
            log.error("上传文件失败 nodeId={} path={}", nodeId, childAbs, e);
            writeOpLog(nodeId, "upload", false, e.getMessage(), null);
            throw exception(STORAGE_FILE_PATH_INVALID);
        }
    }

    @Override
    public NodeStorageFileOpsRespVO deleteMediaPath(Long nodeId, String relativePath) {
        ComputeNodeDO node = requireNode(nodeId);
        String mountRoot = resolveNodeMountRoot(node);
        String abs = resolveJailAbsolutePath(mountRoot, relativePath);
        if (!StringUtils.hasText(toRelativePath(mountRoot, abs))) {
            throw exception(STORAGE_FILE_ROOT_FORBIDDEN);
        }
        NodeSshCredential credential = loadSshCredential(nodeId);
        int sshPort = ComputeNodeServiceImpl.resolveSshPort(node);
        NodeStorageFileOpsRespVO resp = new NodeStorageFileOpsRespVO();
        try (SshSessionHelper ssh = openSshSession(node, credential, sshPort)) {
            SshSessionHelper.SftpEntry stat = ssh.stat(abs);
            if (stat == null) {
                throw exception(STORAGE_FILE_NOT_FOUND);
            }
            ssh.deleteRecursive(abs);
            resp.setSuccess(true);
            resp.setMessage((stat.directory ? "已删除目录 " : "已删除文件 ") + stat.name);
            resp.setRelativePath(toRelativePath(mountRoot, abs));
            writeOpLog(nodeId, "delete", true, resp.getMessage() + " @ " + resp.getRelativePath(), null);
            return resp;
        } catch (RuntimeException e) {
            writeOpLog(nodeId, "delete", false, e.getMessage(), null);
            throw e;
        } catch (Exception e) {
            log.error("删除失败 nodeId={} path={}", nodeId, abs, e);
            writeOpLog(nodeId, "delete", false, e.getMessage(), null);
            throw exception(STORAGE_FILE_PATH_INVALID);
        }
    }

    @Override
    public NodeStorageFileOpsRespVO renameMediaPath(Long nodeId, String relativePath, String newName) {
        String targetName = sanitizeEntryName(newName);
        ComputeNodeDO node = requireNode(nodeId);
        String mountRoot = resolveNodeMountRoot(node);
        String abs = resolveJailAbsolutePath(mountRoot, relativePath);
        if (!StringUtils.hasText(toRelativePath(mountRoot, abs))) {
            throw exception(STORAGE_FILE_PATH_INVALID);
        }
        int slash = abs.lastIndexOf('/');
        String parentAbs = slash > 0 ? abs.substring(0, slash) : mountRoot;
        String targetAbs = resolveJailAbsolutePath(mountRoot, toRelativePath(mountRoot, joinPath(parentAbs, targetName)));
        NodeSshCredential credential = loadSshCredential(nodeId);
        int sshPort = ComputeNodeServiceImpl.resolveSshPort(node);
        NodeStorageFileOpsRespVO resp = new NodeStorageFileOpsRespVO();
        try (SshSessionHelper ssh = openSshSession(node, credential, sshPort)) {
            SshSessionHelper.SftpEntry src = ssh.stat(abs);
            if (src == null) {
                throw exception(STORAGE_FILE_NOT_FOUND);
            }
            if (ssh.stat(targetAbs) != null) {
                throw exception(STORAGE_FILE_EXISTS);
            }
            ssh.rename(abs, targetAbs);
            resp.setSuccess(true);
            resp.setMessage("已重命名为 " + targetName);
            resp.setRelativePath(toRelativePath(mountRoot, targetAbs));
            writeOpLog(nodeId, "rename", true, resp.getMessage() + " @ " + resp.getRelativePath(), null);
            return resp;
        } catch (RuntimeException e) {
            writeOpLog(nodeId, "rename", false, e.getMessage(), null);
            throw e;
        } catch (Exception e) {
            log.error("重命名失败 nodeId={} path={} -> {}", nodeId, abs, targetAbs, e);
            writeOpLog(nodeId, "rename", false, e.getMessage(), null);
            throw exception(STORAGE_FILE_PATH_INVALID);
        }
    }

    private String sanitizeEntryName(String raw) {
        if (!StringUtils.hasText(raw)) {
            throw exception(STORAGE_FILE_NAME_INVALID);
        }
        String name = raw.trim().replace('\\', '/');
        int slash = name.lastIndexOf('/');
        if (slash >= 0) {
            name = name.substring(slash + 1);
        }
        name = name.trim();
        if (!StringUtils.hasText(name) || ".".equals(name) || "..".equals(name)
                || name.contains("/") || name.contains("..")) {
            throw exception(STORAGE_FILE_NAME_INVALID);
        }
        if (name.length() > 200) {
            throw exception(STORAGE_FILE_NAME_INVALID);
        }
        return name;
    }

    private String resolveJailAbsolutePath(String mountRoot, String relativePath) {
        String root = mountRoot.replace('\\', '/').replaceAll("/+$", "");
        if (!root.startsWith("/")) {
            root = "/" + root;
        }
        String rel = relativePath == null ? "" : relativePath.trim().replace('\\', '/');
        while (rel.startsWith("/")) {
            rel = rel.substring(1);
        }
        if (rel.contains("..")) {
            throw exception(STORAGE_FILE_PATH_INVALID);
        }
        String abs = rel.isEmpty() ? root : root + "/" + rel;
        abs = abs.replaceAll("/{2,}", "/");
        String rootSlash = root.endsWith("/") ? root : root + "/";
        if (!abs.equals(root) && !abs.startsWith(rootSlash)) {
            throw exception(STORAGE_FILE_PATH_INVALID);
        }
        return abs;
    }

    private String resolveNodeMountRoot(ComputeNodeDO node) {
        Map<String, String> tags = node.getTags() != null ? node.getTags() : Map.of();
        String mount = firstNonBlank(tags.get("media_mount_path"), tags.get("ceph_mount_path"), mediaHostDataRoot);
        if (!StringUtils.hasText(mount)) {
            mount = "/mnt/easyaiot-media";
        }
        return mount.replace('\\', '/').replaceAll("/+$", "");
    }

    private static String toRelativePath(String mountRoot, String absolute) {
        String root = mountRoot.replaceAll("/+$", "");
        String abs = absolute.replace('\\', '/');
        if (abs.equals(root)) {
            return "";
        }
        String prefix = root + "/";
        if (abs.startsWith(prefix)) {
            return abs.substring(prefix.length());
        }
        return abs;
    }

    private static String joinPath(String base, String name) {
        if (base.endsWith("/")) {
            return base + name;
        }
        return base + "/" + name;
    }

    private NodeMediaRemoteDeployRespVO.DeployStep stepFromToken(
            String name, String output, String okToken, String failToken, String failHint) {
        if (output.contains(okToken)) {
            return runStep(name, "success", name + " 正常");
        }
        if (output.contains(failToken)) {
            return runStep(name, "failed", failHint);
        }
        if (output.contains(okToken.replace("_OK", "_SKIP_CLIENT"))) {
            return runStep(name, "success", name + " 跳过（客户端）");
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
        private NodeMediaRemoteDeployRespVO.DeployStep sourceStep;
        private NodeMediaRemoteDeployRespVO.DeployStep rwStep;
        private Boolean nfsServerReady;
        private Boolean nfsExportReady;
        private Boolean cephHealthy;
        private Boolean osdRunning;
        private Boolean poolExists;
        private Boolean cephfsReady;
        private Boolean mountReady;
        private String rawOutput;
        private String mountSource;
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
