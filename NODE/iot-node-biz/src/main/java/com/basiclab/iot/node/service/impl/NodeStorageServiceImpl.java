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
import com.basiclab.iot.node.service.NfsMultiClusterService;
import com.basiclab.iot.node.util.CredentialEncryptUtil;
import com.basiclab.iot.node.util.NodeFunctions;
import com.basiclab.iot.node.util.SshSessionHelper;
import com.basiclab.iot.node.util.StorageStackDeployUtil;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.multipart.MultipartFile;

import javax.annotation.Resource;
import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.AccessDeniedException;
import java.nio.file.FileVisitResult;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.SimpleFileVisitor;
import java.nio.file.attribute.BasicFileAttributes;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Base64;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;

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
import static com.basiclab.iot.node.enums.ErrorCodeConstants.STORAGE_MEDIA_ROOT_UNUSABLE;
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
    @Resource
    private NfsMultiClusterService nfsMultiClusterService;

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
            String platformRole = resolveNfsClusterRole(platform);
            centerVo = toTopologyNode(platform, edgeByCompute.get(platform.getId()), kindForClusterRole(platform, platformRole));
            resp.setCenter(centerVo);
            nodes.add(centerVo);
            included.add(platform.getId());
        }

        if (all != null) {
            for (ComputeNodeDO n : all) {
                if (n == null || n.getId() == null || included.contains(n.getId())) {
                    continue;
                }
                String clusterRole = resolveNfsClusterRole(n);
                boolean storage = StorageStackDeployUtil.isStorageRole(n.getNodeRole());
                boolean client = StorageStackDeployUtil.isClientMountRole(n.getNodeRole());
                boolean tagged = StringUtils.hasText(clusterRole);
                if (!storage && !client && !tagged) {
                    continue;
                }
                String kind = kindForClusterRole(n, clusterRole);
                NodeCephTopologyRespVO.TopologyNodeVO vo = toTopologyNode(n, edgeByCompute.get(n.getId()), kind);
                nodes.add(vo);
                included.add(n.getId());
            }
        }

        Long primaryId = null;
        for (NodeCephTopologyRespVO.TopologyNodeVO n : nodes) {
            if ("primary".equals(n.getNfsClusterRole())) {
                primaryId = n.getNodeId();
                break;
            }
        }
        for (NodeCephTopologyRespVO.TopologyNodeVO n : nodes) {
            if (n.getNodeId() == null || n.getNodeId().equals(primaryId)) {
                continue;
            }
            if ("client".equals(n.getNfsClusterRole()) && primaryId != null) {
                NodeCephTopologyRespVO.TopologyLinkVO link = new NodeCephTopologyRespVO.TopologyLinkVO();
                link.setSourceNodeId(primaryId);
                link.setTargetNodeId(n.getNodeId());
                link.setRelation("nfs_mount");
                links.add(link);
            } else if ("standby".equals(n.getNfsClusterRole()) && primaryId != null) {
                NodeCephTopologyRespVO.TopologyLinkVO link = new NodeCephTopologyRespVO.TopologyLinkVO();
                link.setSourceNodeId(primaryId);
                link.setTargetNodeId(n.getNodeId());
                link.setRelation("nfs_standby");
                links.add(link);
            }
        }

        resp.setNodes(nodes);
        resp.setLinks(links);

        NodeCephTopologyRespVO.TopologySummaryVO summary = new NodeCephTopologyRespVO.TopologySummaryVO();
        int primaryCnt = 0;
        int standbyCnt = 0;
        int candidateCnt = 0;
        int clientCnt = 0;
        int ready = 0;
        int notReady = 0;
        int offline = 0;
        int unprobed = 0;
        String lastProbeAt = null;
        Boolean primaryReady = null;
        Long primaryNodeId = null;
        String primaryHost = null;
        Long standbyNodeId = null;
        String standbyHost = null;
        for (NodeCephTopologyRespVO.TopologyNodeVO n : nodes) {
            String role = n.getNfsClusterRole();
            if ("primary".equals(role)) {
                primaryCnt++;
                primaryNodeId = n.getNodeId();
                primaryHost = n.getHost();
                // 主节点「Export就绪」看真 Export，不看本机目录可写
                primaryReady = Boolean.TRUE.equals(n.getNfsExportReady());
            } else if ("standby".equals(role)) {
                standbyCnt++;
                if (standbyNodeId == null) {
                    standbyNodeId = n.getNodeId();
                    standbyHost = n.getHost();
                }
            } else if ("candidate".equals(role)) {
                candidateCnt++;
            } else if ("client".equals(role)) {
                // pending 且从未挂载成功：不计入覆盖率分母（避免纳管中的节点把覆盖率永远拖成 0%）
                boolean pendingUnmounted = isPendingUnmountedClient(n);
                if (!pendingUnmounted) {
                    clientCnt++;
                    if (Boolean.TRUE.equals(n.getNfsMountReady())) {
                        ready++;
                    } else {
                        notReady++;
                    }
                }
            }
            if ("offline".equalsIgnoreCase(n.getStatus()) || "pending".equalsIgnoreCase(n.getStatus())) {
                offline++;
            }
            if (!"primary".equals(role) && !StringUtils.hasText(n.getNfsProbeAt())) {
                unprobed++;
            }
            if (StringUtils.hasText(n.getNfsProbeAt())) {
                if (lastProbeAt == null || n.getNfsProbeAt().compareTo(lastProbeAt) > 0) {
                    lastProbeAt = n.getNfsProbeAt();
                }
            }
        }
        summary.setTotalNodes(nodes.size());
        summary.setPrimaryCount(primaryCnt);
        summary.setStandbyCount(standbyCnt);
        summary.setCandidateCount(candidateCnt);
        summary.setPrimaryReady(primaryReady);
        summary.setPrimaryNodeId(primaryNodeId);
        summary.setPrimaryHost(primaryHost);
        summary.setStandbyNodeId(standbyNodeId);
        summary.setStandbyHost(standbyHost);
        summary.setStorageNodes(primaryCnt + standbyCnt);
        summary.setClientNodes(clientCnt);
        summary.setMountReadyCount(ready);
        summary.setMountNotReadyCount(notReady);
        summary.setOfflineCount(offline);
        summary.setUnprobedCount(unprobed);
        summary.setLastProbeAt(lastProbeAt);
        // 无有效客户端时：以主 Export 就绪为准；有客户端时按挂载覆盖率
        if (clientCnt <= 0) {
            summary.setCoveragePercent(Boolean.TRUE.equals(primaryReady) ? 100 : 0);
        } else {
            summary.setCoveragePercent((int) Math.round(ready * 100.0 / clientCnt));
        }
        resp.setSummary(summary);
        return resp;
    }

    /** pending 且未挂载：只展示、不进覆盖率分母 */
    private static boolean isPendingUnmountedClient(NodeCephTopologyRespVO.TopologyNodeVO n) {
        if (n == null || Boolean.TRUE.equals(n.getNfsMountReady())) {
            return false;
        }
        if (Boolean.TRUE.equals(n.getIsPlatform())) {
            return false;
        }
        String status = n.getStatus() != null ? n.getStatus().trim().toLowerCase(Locale.ROOT) : "";
        return "pending".equals(status);
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
        }
        // 控制面本机：解析可写媒体根并直接视为就绪（不依赖 SSH 探测 /mnt）
        String mountSource = firstNonBlank(tags.get("nfs_mount_source"), null);
        if (ComputeNodeServiceImpl.isPlatformNode(node)) {
            String localRoot = findWritableLocalMediaRoot(node, false);
            if (StringUtils.hasText(localRoot)) {
                mountPath = localRoot.replaceAll("/+$", "");
                mountReady = true;
                if (!StringUtils.hasText(mountSource) || mountSource.startsWith("local:")
                        || !isLikelyNfsMountSource(mountSource)) {
                    mountSource = "local:" + mountPath;
                }
            }
        }

        boolean exportReady = false;
        String exportTag = firstNonBlank(tags.get("nfs_export_ready"), null);
        if (StringUtils.hasText(exportTag)) {
            String r = exportTag.trim().toLowerCase(Locale.ROOT);
            exportReady = "true".equals(r) || "1".equals(r) || "yes".equals(r) || "on".equals(r);
        } else if (StringUtils.hasText(mountSource)) {
            // 真 NFS 源形如 host:/path；local: 仅本机目录
            exportReady = isLikelyNfsMountSource(mountSource);
        }

        String clusterRole = resolveNfsClusterRole(node);
        String nfsServer = StorageStackDeployUtil.resolveNfsServerHost(node, tags);
        String nfsExport = tagString(tags, "nfs_export", mountPath);
        String backend = "nfs";
        String taggedBackend = firstNonBlank(tags.get("storage_backend"), null);
        if (StringUtils.hasText(taggedBackend) && !"local_bind".equalsIgnoreCase(taggedBackend.trim())) {
            backend = taggedBackend.trim();
        }

        NodeCephTopologyRespVO.TopologyNodeVO vo = new NodeCephTopologyRespVO.TopologyNodeVO();
        vo.setNodeId(node.getId());
        vo.setName(node.getName());
        vo.setHost(node.getHost());
        vo.setNodeRole(node.getNodeRole());
        vo.setFunctions(NodeFunctions.parse(node));
        vo.setStatus(node.getStatus());
        vo.setAgentPort(node.getAgentPort() != null ? node.getAgentPort() : 9100);
        vo.setKind(kind);
        vo.setNfsClusterRole(clusterRole);
        vo.setIsPlatform(ComputeNodeServiceImpl.isPlatformNode(node));
        vo.setNfsMountReady(mountReady);
        vo.setNfsExportReady(exportReady);
        vo.setNfsMountPath(mountPath);
        vo.setNfsServerHost(nfsServer);
        vo.setNfsExportPath(nfsExport);
        vo.setStorageBackend(backend);
        vo.setNfsProbeAt(firstNonBlank(tags.get("nfs_probe_at"), null));
        vo.setNfsProbeSummary(firstNonBlank(tags.get("nfs_probe_summary"), null));
        vo.setNfsMountSource(mountSource);
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
        boolean sshConfigured = cred != null && StringUtils.hasText(cred.getCredentialEnc());
        vo.setSshCredentialConfigured(sshConfigured || ComputeNodeServiceImpl.isPlatformNode(node));
        return vo;
    }

    private static boolean isLikelyNfsMountSource(String source) {
        if (!StringUtils.hasText(source) || source.startsWith("local:")) {
            return false;
        }
        // 形如 10.x.x.x:/mnt/... 或 host:/export
        return source.contains(":/");
    }

    /** 控制面本机媒体根：目录存在且可写（含 playbacks）即视为就绪 */
    private boolean isLocalMediaRootReady(String mountPath) {
        if (!StringUtils.hasText(mountPath)) {
            return false;
        }
        try {
            Path root = Paths.get(mountPath);
            if (!Files.isDirectory(root) || !Files.isWritable(root)) {
                return false;
            }
            Path playbacks = root.resolve("playbacks");
            return Files.isDirectory(playbacks) || Files.isWritable(root);
        } catch (Exception ignored) {
            return false;
        }
    }

    /**
     * 解析 NFS 集群角色：primary | standby | client | candidate。
     * 优先 tags.nfs_cluster_role；兼容旧 nfs_role；未分配的 storage 为 candidate。
     */
    private String resolveNfsClusterRole(ComputeNodeDO node) {
        Map<String, String> tags = node.getTags() != null ? node.getTags() : Map.of();
        String explicit = firstNonBlank(tags.get("nfs_cluster_role"), null);
        if (StringUtils.hasText(explicit)) {
            String r = explicit.trim().toLowerCase(Locale.ROOT);
            if ("primary".equals(r) || "standby".equals(r) || "client".equals(r) || "candidate".equals(r)) {
                return r;
            }
            if ("server".equals(r)) {
                return "primary";
            }
        }
        String legacy = firstNonBlank(tags.get("nfs_role"), null);
        if (StringUtils.hasText(legacy)) {
            String r = legacy.trim().toLowerCase(Locale.ROOT);
            if ("client".equals(r)) {
                return "client";
            }
            if ("server".equals(r)) {
                String host = node.getHost() != null ? node.getHost().trim() : "";
                String server = StorageStackDeployUtil.resolveNfsServerHost(node, tags);
                if (StringUtils.hasText(host) && host.equals(server)) {
                    return "primary";
                }
                // 旧标签标了 server 但挂载目标指向别处：视为备或候选
                return "standby";
            }
        }
        if (StorageStackDeployUtil.isStorageRole(node.getNodeRole())) {
            return "candidate";
        }
        if (ComputeNodeServiceImpl.isPlatformNode(node)) {
            String host = node.getHost() != null ? node.getHost().trim() : "";
            String server = StorageStackDeployUtil.resolveNfsServerHost(node, tags);
            if (!StringUtils.hasText(tags.get("nfs_server_host")) && !StringUtils.hasText(tags.get("ceph_mon_host"))) {
                // 未分配时：控制面默认视作主（单机 Export）
                return "primary";
            }
            if (StringUtils.hasText(host) && (host.equals(server)
                    || "127.0.0.1".equals(server) || "localhost".equalsIgnoreCase(server))) {
                return "primary";
            }
            return "client";
        }
        if (StorageStackDeployUtil.isClientMountRole(node.getNodeRole())) {
            return "client";
        }
        return "candidate";
    }

    private String kindForClusterRole(ComputeNodeDO node, String clusterRole) {
        if (ComputeNodeServiceImpl.isPlatformNode(node)) {
            return "platform";
        }
        if ("primary".equals(clusterRole)) {
            return "nfs_primary";
        }
        if ("standby".equals(clusterRole)) {
            return "nfs_standby";
        }
        if ("client".equals(clusterRole)) {
            return "nfs_client";
        }
        return "nfs_candidate";
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
                : firstNonBlank(System.getenv("EASYAIOT_EDGE_MEDIA_ROOT"),
                System.getenv("EASYAIOT_MEDIA_ROOT"), mediaHostDataRoot);
        if (!StringUtils.hasText(mountRoot)) {
            mountRoot = "/mnt/easyaiot-media";
        }
        mountRoot = mountRoot.replaceAll("/+$", "");
        String nfsExport = StringUtils.hasText(req.getNfsExport())
                ? req.getNfsExport().trim().replaceAll("/+$", "")
                : mountRoot;
        String mountOpts = StringUtils.hasText(req.getNfsMountOpts())
                ? req.getNfsMountOpts().trim()
                : "vers=3,tcp,nolock,_netdev";

        List<ComputeNodeDO> allNodes = computeNodeMapper.selectList();
        if (allNodes == null) {
            allNodes = new ArrayList<>();
        }

        ComputeNodeDO primaryNode;
        if (req.getServerNodeId() != null) {
            primaryNode = requireNode(req.getServerNodeId());
        } else {
            primaryNode = null;
            for (ComputeNodeDO n : allNodes) {
                if (n != null && StorageStackDeployUtil.isStorageRole(n.getNodeRole())) {
                    primaryNode = n;
                    break;
                }
            }
            if (primaryNode == null) {
                primaryNode = computeNodeMapper.selectPlatformNode();
            }
            if (primaryNode == null && !allNodes.isEmpty()) {
                primaryNode = allNodes.get(0);
            }
            if (primaryNode == null) {
                throw exception(COMPUTE_NODE_NOT_EXISTS);
            }
        }

        String primaryHost = StringUtils.hasText(primaryNode.getHost())
                ? primaryNode.getHost().trim()
                : "127.0.0.1";

        ComputeNodeDO standbyNode = null;
        if (req.getStandbyNodeId() != null) {
            if (req.getStandbyNodeId().equals(primaryNode.getId())) {
                throw exception(STORAGE_NODE_ROLE_INVALID);
            }
            standbyNode = requireNode(req.getStandbyNodeId());
        } else if (req.getServerNodeId() == null) {
            // 默认分配：第二台 storage 作备
            for (ComputeNodeDO n : allNodes) {
                if (n == null || n.getId() == null || n.getId().equals(primaryNode.getId())) {
                    continue;
                }
                if (StorageStackDeployUtil.isStorageRole(n.getNodeRole())) {
                    standbyNode = n;
                    break;
                }
            }
        }

        applyNfsTags(primaryNode, primaryHost, nfsExport, mountRoot, mountOpts, "primary");
        computeNodeMapper.updateById(primaryNode);

        if (standbyNode != null) {
            applyNfsTags(standbyNode, primaryHost, nfsExport, mountRoot, mountOpts, "standby");
            computeNodeMapper.updateById(standbyNode);
        }

        Set<Long> reserved = new HashSet<>();
        reserved.add(primaryNode.getId());
        if (standbyNode != null) {
            reserved.add(standbyNode.getId());
        }

        List<Long> clientIds = req.getClientNodeIds();
        if (clientIds == null || clientIds.isEmpty()) {
            clientIds = new ArrayList<>();
            for (ComputeNodeDO n : allNodes) {
                if (n == null || n.getId() == null || reserved.contains(n.getId())) {
                    continue;
                }
                if (StorageStackDeployUtil.isClientMountRole(n.getNodeRole())
                        || ComputeNodeServiceImpl.isPlatformNode(n)) {
                    clientIds.add(n.getId());
                }
            }
        } else {
            ComputeNodeDO platform = computeNodeMapper.selectPlatformNode();
            if (platform != null && platform.getId() != null
                    && !reserved.contains(platform.getId())
                    && !clientIds.contains(platform.getId())) {
                clientIds = new ArrayList<>(clientIds);
                clientIds.add(platform.getId());
            }
        }

        for (Long clientId : clientIds) {
            if (clientId == null || reserved.contains(clientId)) {
                continue;
            }
            ComputeNodeDO client = requireNode(clientId);
            String clientMount = mountRoot;
            if (ComputeNodeServiceImpl.isPlatformNode(client)) {
                String localRoot = findWritableLocalMediaRoot(client, false);
                if (StringUtils.hasText(localRoot)) {
                    clientMount = localRoot;
                }
            }
            applyNfsTags(client, primaryHost, nfsExport, clientMount, mountOpts, "client");
            if (ComputeNodeServiceImpl.isPlatformNode(client)) {
                Map<String, String> tags = client.getTags() != null ? new HashMap<>(client.getTags()) : new HashMap<>();
                tags.put("nfs_mount_ready", "true");
                tags.put("ceph_mount_ready", "true");
                tags.put("nfs_mount_source", "local:" + clientMount);
                tags.put("nfs_probe_summary", "assign: platform local media ready");
                tags.put("nfs_probe_at", Instant.now().toString());
                client.setTags(tags);
            }
            computeNodeMapper.updateById(client);
        }

        // 其余 storage 候选：显式标 candidate，避免误显示为主服务端
        for (ComputeNodeDO n : allNodes) {
            if (n == null || n.getId() == null || reserved.contains(n.getId())) {
                continue;
            }
            if (clientIds.contains(n.getId())) {
                continue;
            }
            if (!StorageStackDeployUtil.isStorageRole(n.getNodeRole())) {
                continue;
            }
            applyNfsTags(n, primaryHost, nfsExport, mountRoot, mountOpts, "candidate");
            computeNodeMapper.updateById(n);
        }

        try {
            nfsMultiClusterService.upsertLocalCluster(primaryNode, standbyNode, mountRoot, nfsExport, mountOpts);
        } catch (Exception e) {
            log.warn("同步本地 NFS 集群记录失败: {}", e.getMessage());
        }

        return getCephTopology();
    }

    @Override
    public NodeCephTopologyRespVO promoteNfsPrimary(Long nodeId) {
        ComputeNodeDO target = requireNode(nodeId);
        String targetRole = resolveNfsClusterRole(target);
        if (!"standby".equals(targetRole) && !StorageStackDeployUtil.isStorageRole(target.getNodeRole())
                && !ComputeNodeServiceImpl.isPlatformNode(target)) {
            throw exception(STORAGE_NODE_ROLE_INVALID);
        }

        List<ComputeNodeDO> all = computeNodeMapper.selectList();
        if (all == null) {
            all = new ArrayList<>();
        }
        ComputeNodeDO currentPrimary = null;
        for (ComputeNodeDO n : all) {
            if (n != null && "primary".equals(resolveNfsClusterRole(n))) {
                currentPrimary = n;
                break;
            }
        }

        Map<String, String> targetTags = target.getTags() != null ? target.getTags() : Map.of();
        String mountRoot = firstNonBlank(
                targetTags.get("media_mount_path"),
                targetTags.get("ceph_mount_path"),
                mediaHostDataRoot);
        if (!StringUtils.hasText(mountRoot)) {
            mountRoot = "/mnt/easyaiot-media";
        }
        mountRoot = mountRoot.replaceAll("/+$", "");
        String nfsExport = tagString(targetTags, "nfs_export", mountRoot);
        String mountOpts = tagString(targetTags, "nfs_mount_opts", "vers=3,tcp,nolock,_netdev");
        String newPrimaryHost = StringUtils.hasText(target.getHost()) ? target.getHost().trim() : "127.0.0.1";

        applyNfsTags(target, newPrimaryHost, nfsExport, mountRoot, mountOpts, "primary");
        computeNodeMapper.updateById(target);

        if (currentPrimary != null && !currentPrimary.getId().equals(target.getId())) {
            applyNfsTags(currentPrimary, newPrimaryHost, nfsExport, mountRoot, mountOpts, "standby");
            computeNodeMapper.updateById(currentPrimary);
        }

        for (ComputeNodeDO n : all) {
            if (n == null || n.getId() == null) {
                continue;
            }
            if (n.getId().equals(target.getId())) {
                continue;
            }
            if (currentPrimary != null && n.getId().equals(currentPrimary.getId())) {
                continue;
            }
            String role = resolveNfsClusterRole(n);
            if ("client".equals(role) || "standby".equals(role)) {
                applyNfsTags(n, newPrimaryHost, nfsExport, mountRoot, mountOpts, role);
                computeNodeMapper.updateById(n);
            }
        }
        writeOpLog(nodeId, "promote_primary", true,
                "已升主 NFS primary → " + newPrimaryHost + "（客户端需重新挂载）", null);
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
                // 控制面：不依赖 SSH，直接按可写本机媒体根刷新就绪态（避免 /mnt 权限把覆盖率锁死在 0%）
                if (ComputeNodeServiceImpl.isPlatformNode(node)) {
                    try {
                        String localRoot = findWritableLocalMediaRoot(node, false);
                        if (StringUtils.hasText(localRoot)) {
                            markPlatformLocalMediaReady(node, localRoot, "batch-refresh: local media ready");
                            item.setSuccess(true);
                            item.setMessage("控制面本机媒体根已就绪: " + localRoot);
                            ok++;
                        } else {
                            NodeStorageStackCheckRespVO check = checkStorageStackBySsh(nodeId);
                            item.setSuccess(Boolean.TRUE.equals(check.getSuccess())
                                    && Boolean.TRUE.equals(check.getMountReady()));
                            item.setMessage(check.getMessage());
                            item.setSteps(check.getSteps());
                            if (Boolean.TRUE.equals(item.getSuccess())) {
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
                    continue;
                }
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
                    if (StorageStackDeployUtil.isStorageRole(node.getNodeRole())) {
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
            String primaryHost,
            String nfsExport,
            String mountRoot,
            String mountOpts,
            String clusterRole) {
        Map<String, String> tags = node.getTags() != null ? new HashMap<>(node.getTags()) : new HashMap<>();
        tags.put("storage_backend", "nfs");
        tags.put("media_mount_path", mountRoot);
        tags.put("nfs_export", nfsExport);
        tags.put("nfs_mount_opts", mountOpts);
        tags.put("ceph_mount_path", mountRoot);
        String role = StringUtils.hasText(clusterRole) ? clusterRole.trim().toLowerCase(Locale.ROOT) : "client";
        tags.put("nfs_cluster_role", role);
        if ("primary".equals(role)) {
            String selfHost = StringUtils.hasText(node.getHost()) ? node.getHost().trim() : primaryHost;
            tags.put("nfs_server_host", selfHost);
            tags.put("ceph_mon_host", selfHost);
            tags.put("nfs_role", "server");
        } else if ("standby".equals(role)) {
            tags.put("nfs_server_host", primaryHost);
            tags.put("ceph_mon_host", primaryHost);
            tags.put("nfs_role", "server");
        } else if ("candidate".equals(role)) {
            tags.put("nfs_server_host", primaryHost);
            tags.put("ceph_mon_host", primaryHost);
            tags.put("nfs_role", "candidate");
        } else {
            tags.put("nfs_server_host", primaryHost);
            tags.put("ceph_mon_host", primaryHost);
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
        // storage 角色或控制面（单机作 NFS 服务端）
        if (!StorageStackDeployUtil.isStorageRole(node.getNodeRole())
                && !ComputeNodeServiceImpl.isPlatformNode(node)) {
            throw exception(STORAGE_NODE_ROLE_INVALID);
        }
        return deployWithScript(node, "NFS 服务端", StorageStackDeployUtil.buildOsdInstallScript(node),
                "NFS_SERVER_OK", "deploy_server");
    }

    @Override
    public NodeMediaRemoteDeployRespVO deployStorageClientBySsh(Long nodeId) {
        ComputeNodeDO node = requireNode(nodeId);
        // 计算/媒体客户端，或控制面作为 NFS 客户端（集群有独立 storage 时）
        if (!StorageStackDeployUtil.isClientMountRole(node.getNodeRole())
                && !ComputeNodeServiceImpl.isPlatformNode(node)) {
            throw exception(STORAGE_NODE_ROLE_INVALID);
        }
        return deployWithScript(node, "NFS 客户端挂载", StorageStackDeployUtil.buildClientInstallScript(node),
                "CLIENT_MOUNT_OK", "deploy_client");
    }

    @Override
    public NodeMediaRemoteDeployRespVO deployStoragePoolBySsh(Long nodeId) {
        ComputeNodeDO node = requireNode(nodeId);
        if (!StorageStackDeployUtil.isStorageRole(node.getNodeRole())
                && !ComputeNodeServiceImpl.isPlatformNode(node)) {
            throw exception(STORAGE_NODE_ROLE_INVALID);
        }
        return deployWithScript(node, "初始化 NFS Export", StorageStackDeployUtil.buildPoolCreateScript(node),
                "NFS_SERVER_OK", "deploy_export");
    }

    @Override
    public NodeMediaRemoteDeployRespVO stopStorageOsdBySsh(Long nodeId) {
        ComputeNodeDO node = requireNode(nodeId);
        if (!StorageStackDeployUtil.isStorageRole(node.getNodeRole())
                && !ComputeNodeServiceImpl.isPlatformNode(node)) {
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
        if (!StorageStackDeployUtil.isClientMountRole(node.getNodeRole())
                && !ComputeNodeServiceImpl.isPlatformNode(node)) {
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
        if (ComputeNodeServiceImpl.isPlatformNode(node)) {
            return runHealthCheckLocal(node);
        }
        NodeSshCredential credential = loadSshCredential(node.getId());
        int sshPort = ComputeNodeServiceImpl.resolveSshPort(node);
        NodeStorageStackCheckRespVO resp = new NodeStorageStackCheckRespVO();
        List<NodeMediaRemoteDeployRespVO.DeployStep> steps = new ArrayList<>();
        resp.setSteps(steps);

        try (SshSessionHelper ssh = openSshSession(node, credential, sshPort)) {
            steps.add(runStep("SSH 连接", "success", "已连接 " + node.getHost() + ":" + sshPort));
            HealthProbe probe = probeHealth(ssh, node);
            return fillStackCheckFromProbe(resp, steps, node, probe);
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

    /** 控制面本机检测：不经 SSH，直接跑 check_nfs_health.sh */
    private NodeStorageStackCheckRespVO runHealthCheckLocal(ComputeNodeDO node) {
        NodeStorageStackCheckRespVO resp = new NodeStorageStackCheckRespVO();
        List<NodeMediaRemoteDeployRespVO.DeployStep> steps = new ArrayList<>();
        resp.setSteps(steps);
        try {
            steps.add(runStep("本机执行", "success", "控制面节点，跳过 SSH"));
            HealthProbe probe = probeHealthLocal(node);
            return fillStackCheckFromProbe(resp, steps, node, probe);
        } catch (Exception e) {
            log.error("NFS 本机检测失败 nodeId={}", node.getId(), e);
            steps.add(runStep("本机检测", "failed",
                    e.getMessage() != null ? e.getMessage() : e.getClass().getSimpleName()));
            resp.setSuccess(false);
            resp.setDeployed(false);
            resp.setMessage(steps.get(steps.size() - 1).getOutput());
            writeOpLog(node.getId(), resolveOpType("check_stack"), false, resp.getMessage(), steps);
            return resp;
        }
    }

    private NodeStorageStackCheckRespVO fillStackCheckFromProbe(
            NodeStorageStackCheckRespVO resp,
            List<NodeMediaRemoteDeployRespVO.DeployStep> steps,
            ComputeNodeDO node,
            HealthProbe probe) {
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
                || outIndicatesServerRole(probe.rawOutput)
                || "primary".equals(resolveNfsClusterRole(node));
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
    }

    private NodeMediaRemoteDeployRespVO deployWithScript(
            ComputeNodeDO node, String phaseName, String scriptBody, String successToken, String opType) {
        if (ComputeNodeServiceImpl.isPlatformNode(node)) {
            return deployWithLocalScript(node, phaseName, scriptBody, successToken, opType);
        }
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

    /** 控制面本机部署：直接执行 NFS 脚本（必要时 sudo -n） */
    private NodeMediaRemoteDeployRespVO deployWithLocalScript(
            ComputeNodeDO node, String phaseName, String scriptBody, String successToken, String opType) {
        NodeMediaRemoteDeployRespVO resp = new NodeMediaRemoteDeployRespVO();
        List<NodeMediaRemoteDeployRespVO.DeployStep> steps = new ArrayList<>();
        resp.setSteps(steps);
        try {
            String sourceRoot = resolveStorageClusterSource();
            steps.add(runStep("本机执行", "success", "控制面节点，跳过 SSH；脚本源 " + sourceRoot));
            String localBody = scriptBody.replace(StorageStackDeployUtil.remoteClusterRoot(), sourceRoot);
            LocalExecResult result = execLocalScript(localBody, DEPLOY_TIMEOUT_MS, true);
            NodeMediaRemoteDeployRespVO.DeployStep deployStep = new NodeMediaRemoteDeployRespVO.DeployStep();
            deployStep.setName(phaseName);
            deployStep.setOutput(trimOutput(result.output, 8000));
            boolean ok = result.exitCode == 0 && result.output.contains(successToken);
            deployStep.setStatus(ok ? "success" : "failed");
            steps.add(deployStep);
            resp.setSuccess(ok);
            if (ok) {
                resp.setMessage(phaseName + " 完成");
                try {
                    HealthProbe probe = probeHealthLocal(node);
                    persistProbeResult(node, probe, resp.getMessage());
                    if (probe.mountStep != null) {
                        steps.add(probe.mountStep);
                    }
                    if (probe.nfsExportStep != null) {
                        steps.add(probe.nfsExportStep);
                    }
                } catch (Exception probeEx) {
                    log.warn("本机部署后探针失败 nodeId={}: {}", node.getId(), probeEx.getMessage());
                }
            } else {
                String hint = result.output.contains("Permission denied") || result.exitCode == 1
                        ? "（本机安装 NFS 需要 root/sudo；无特权时仅本机目录可用，远端无法 mount）"
                        : "";
                resp.setMessage(phaseName + " 失败" + hint);
            }
            writeOpLog(node.getId(), opType, ok, resp.getMessage(), steps);
            return resp;
        } catch (Exception e) {
            steps.add(runStep(phaseName, "failed",
                    e.getMessage() != null ? e.getMessage() : e.getClass().getSimpleName()));
            resp.setSuccess(false);
            resp.setMessage(phaseName + " 失败: " + steps.get(steps.size() - 1).getOutput());
            writeOpLog(node.getId(), opType, false, resp.getMessage(), steps);
            return resp;
        }
    }

    private HealthProbe probeHealthLocal(ComputeNodeDO node) throws Exception {
        String sourceRoot = resolveStorageClusterSource();
        String body = StorageStackDeployUtil.buildHealthCheckScript(node)
                .replace(StorageStackDeployUtil.remoteClusterRoot(), sourceRoot);
        String out = execLocalScript(body, CHECK_TIMEOUT_MS, false).output;
        return parseHealthOutput(out, node);
    }

    private HealthProbe probeHealth(SshSessionHelper ssh, ComputeNodeDO node) throws Exception {
        String sourceRoot = resolveStorageClusterSource();
        syncStorageCluster(ssh, sourceRoot);
        SshSessionHelper.SshExecResult result = execRemoteScript(
                ssh, StorageStackDeployUtil.buildHealthCheckScript(node), CHECK_TIMEOUT_MS);
        return parseHealthOutput(result.combinedOutput(), node);
    }

    private HealthProbe parseHealthOutput(String out, ComputeNodeDO node) {
        HealthProbe probe = new HealthProbe();
        probe.rawOutput = out;
        boolean clientRole = out.contains("NFS_ROLE_CLIENT")
                || (!StorageStackDeployUtil.isStorageRole(node.getNodeRole())
                && !"primary".equals(resolveNfsClusterRole(node))
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
        probe.mountReady = mountOk && (sourceOk || !sourceMismatch) && rwOk;
        if (mountOk && sourceOk && !rwOk) {
            probe.mountReady = false;
        }
        if (mountOk && out.contains("MOUNT_LOCAL_BIND_OK") && rwOk) {
            probe.mountReady = true;
        }
        // 本机目录可写但未 Export：单机可用，跨节点不可用
        if (!Boolean.TRUE.equals(probe.mountReady) && out.contains("MOUNT_FSTYPE_LOCAL_OK") && rwOk && subOk) {
            probe.mountReady = true;
        }
        probe.poolExists = subOk;
        probe.cephHealthy = Boolean.TRUE.equals(probe.nfsServerReady)
                && (clientRole || out.contains("NFS_EXPORT_OK"));
        probe.osdRunning = out.contains("NFS_PORT_OK") || out.contains("NFS_PORT_SKIP_CLIENT");
        probe.cephfsReady = probe.mountReady;
        return probe;
    }

    private static final class LocalExecResult {
        private final int exitCode;
        private final String output;

        private LocalExecResult(int exitCode, String output) {
            this.exitCode = exitCode;
            this.output = output != null ? output : "";
        }
    }

    private LocalExecResult execLocalScript(String scriptBody, long timeoutMs, boolean allowSudo) throws Exception {
        Path tmp = Files.createTempFile("easyaiot-nfs-", ".sh");
        try {
            Files.writeString(tmp, scriptBody, StandardCharsets.UTF_8);
            tmp.toFile().setExecutable(true);
            List<String> cmd = new ArrayList<>();
            boolean useSudo = allowSudo && !isCurrentUserRoot() && canSudoNonInteractive();
            if (useSudo) {
                cmd.add("sudo");
                cmd.add("-n");
            }
            cmd.add("bash");
            cmd.add(tmp.toAbsolutePath().toString());
            ProcessBuilder pb = new ProcessBuilder(cmd);
            pb.redirectErrorStream(true);
            Process process = pb.start();
            String output;
            try (BufferedReader reader = new BufferedReader(
                    new InputStreamReader(process.getInputStream(), StandardCharsets.UTF_8))) {
                output = reader.lines().collect(Collectors.joining("\n"));
            }
            boolean finished = process.waitFor(Math.max(timeoutMs, 1000L), TimeUnit.MILLISECONDS);
            if (!finished) {
                process.destroyForcibly();
                throw new IllegalStateException("本机脚本执行超时");
            }
            return new LocalExecResult(process.exitValue(), output);
        } finally {
            try {
                Files.deleteIfExists(tmp);
            } catch (Exception ignored) {
                // ignore
            }
        }
    }

    private static boolean isCurrentUserRoot() {
        try {
            Process p = new ProcessBuilder("id", "-u").start();
            String uid;
            try (BufferedReader reader = new BufferedReader(
                    new InputStreamReader(p.getInputStream(), StandardCharsets.UTF_8))) {
                uid = reader.readLine();
            }
            if (p.waitFor(3, TimeUnit.SECONDS) && p.exitValue() == 0 && "0".equals(uid != null ? uid.trim() : "")) {
                return true;
            }
        } catch (Exception ignored) {
            // fall through
        }
        return "root".equals(System.getProperty("user.name"));
    }

    private static boolean canSudoNonInteractive() {
        try {
            Process p = new ProcessBuilder("sudo", "-n", "true").start();
            return p.waitFor(5, TimeUnit.SECONDS) && p.exitValue() == 0;
        } catch (Exception ignored) {
            return false;
        }
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
        boolean exportReady = Boolean.TRUE.equals(probe.nfsExportReady)
                && (probe.rawOutput == null || !probe.rawOutput.contains("NFS_EXPORT_SKIP_CLIENT"));
        // 客户端跳过 Export 检查时不写 true，避免误标「真 Export」
        if (probe.rawOutput != null && probe.rawOutput.contains("NFS_EXPORT_SKIP_CLIENT")) {
            tags.put("nfs_export_ready", "false");
        } else {
            tags.put("nfs_export_ready", exportReady ? "true" : "false");
        }
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
        NodeStorageFileListRespVO resp = new NodeStorageFileListRespVO();
        resp.setMountRoot(mountRoot);
        resp.setAbsolutePath(abs);
        resp.setRelativePath(toRelativePath(mountRoot, abs));
        try {
            List<NodeStorageFileEntryVO> vos = useLocalMediaFiles(node)
                    ? listLocalMediaEntries(mountRoot, abs)
                    : listRemoteMediaEntries(node, mountRoot, abs);
            resp.setEntries(vos);
            return resp;
        } catch (AccessDeniedException e) {
            log.error("列出媒体文件无权限 nodeId={} path={}", nodeId, abs, e);
            throw exception(STORAGE_MEDIA_ROOT_UNUSABLE, abs);
        } catch (RuntimeException e) {
            throw e;
        } catch (Exception e) {
            log.error("列出媒体文件失败 nodeId={} path={}", nodeId, abs, e);
            if (e.getCause() instanceof AccessDeniedException) {
                throw exception(STORAGE_MEDIA_ROOT_UNUSABLE, abs);
            }
            throw exception(STORAGE_FILE_PATH_INVALID);
        }
    }

    @Override
    public NodeStorageFileDownloadResult downloadMediaFile(Long nodeId, String relativePath) {
        ComputeNodeDO node = requireNode(nodeId);
        String mountRoot = resolveNodeMountRoot(node);
        String abs = resolveJailAbsolutePath(mountRoot, relativePath);
        try {
            if (useLocalMediaFiles(node)) {
                Path path = Paths.get(abs);
                if (!Files.isRegularFile(path)) {
                    throw exception(STORAGE_FILE_NOT_FOUND);
                }
                long size = Files.size(path);
                if (size > FILE_DOWNLOAD_MAX_BYTES) {
                    throw exception(STORAGE_FILE_TOO_LARGE);
                }
                NodeStorageFileDownloadResult result = new NodeStorageFileDownloadResult();
                result.setFileName(path.getFileName().toString());
                result.setSize(size);
                result.setContent(Files.readAllBytes(path));
                return result;
            }
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
            }
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
        NodeStorageFileOpsRespVO resp = new NodeStorageFileOpsRespVO();
        try {
            if (useLocalMediaFiles(node)) {
                Path child = Paths.get(childAbs);
                if (Files.exists(child)) {
                    throw exception(STORAGE_FILE_EXISTS);
                }
                Files.createDirectories(child);
            } else {
                NodeSshCredential credential = loadSshCredential(nodeId);
                int sshPort = ComputeNodeServiceImpl.resolveSshPort(node);
                try (SshSessionHelper ssh = openSshSession(node, credential, sshPort)) {
                    SshSessionHelper.SftpEntry existing = ssh.stat(childAbs);
                    if (existing != null) {
                        throw exception(STORAGE_FILE_EXISTS);
                    }
                    ssh.mkdir(childAbs);
                }
            }
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
        NodeStorageFileOpsRespVO resp = new NodeStorageFileOpsRespVO();
        try {
            boolean overwrite;
            byte[] bytes = file.getBytes();
            if (useLocalMediaFiles(node)) {
                Path child = Paths.get(childAbs);
                if (Files.isDirectory(child)) {
                    throw exception(STORAGE_FILE_EXISTS);
                }
                overwrite = Files.exists(child);
                Path parent = child.getParent();
                if (parent != null) {
                    Files.createDirectories(parent);
                }
                Files.write(child, bytes);
            } else {
                NodeSshCredential credential = loadSshCredential(nodeId);
                int sshPort = ComputeNodeServiceImpl.resolveSshPort(node);
                try (SshSessionHelper ssh = openSshSession(node, credential, sshPort)) {
                    SshSessionHelper.SftpEntry existing = ssh.stat(childAbs);
                    if (existing != null && existing.directory) {
                        throw exception(STORAGE_FILE_EXISTS);
                    }
                    overwrite = existing != null;
                    ssh.uploadBytes(childAbs, bytes);
                }
            }
            resp.setSuccess(true);
            resp.setMessage((overwrite ? "已覆盖上传 " : "已上传 ") + fileName + "（" + bytes.length + " 字节）");
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
        NodeStorageFileOpsRespVO resp = new NodeStorageFileOpsRespVO();
        try {
            boolean directory;
            String name;
            if (useLocalMediaFiles(node)) {
                Path path = Paths.get(abs);
                if (!Files.exists(path)) {
                    throw exception(STORAGE_FILE_NOT_FOUND);
                }
                directory = Files.isDirectory(path);
                name = path.getFileName() != null ? path.getFileName().toString() : abs;
                deleteLocalRecursive(path);
            } else {
                NodeSshCredential credential = loadSshCredential(nodeId);
                int sshPort = ComputeNodeServiceImpl.resolveSshPort(node);
                try (SshSessionHelper ssh = openSshSession(node, credential, sshPort)) {
                    SshSessionHelper.SftpEntry stat = ssh.stat(abs);
                    if (stat == null) {
                        throw exception(STORAGE_FILE_NOT_FOUND);
                    }
                    directory = stat.directory;
                    name = stat.name;
                    ssh.deleteRecursive(abs);
                }
            }
            resp.setSuccess(true);
            resp.setMessage((directory ? "已删除目录 " : "已删除文件 ") + name);
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
        NodeStorageFileOpsRespVO resp = new NodeStorageFileOpsRespVO();
        try {
            if (useLocalMediaFiles(node)) {
                Path src = Paths.get(abs);
                Path dst = Paths.get(targetAbs);
                if (!Files.exists(src)) {
                    throw exception(STORAGE_FILE_NOT_FOUND);
                }
                if (Files.exists(dst)) {
                    throw exception(STORAGE_FILE_EXISTS);
                }
                Files.move(src, dst);
            } else {
                NodeSshCredential credential = loadSshCredential(nodeId);
                int sshPort = ComputeNodeServiceImpl.resolveSshPort(node);
                try (SshSessionHelper ssh = openSshSession(node, credential, sshPort)) {
                    SshSessionHelper.SftpEntry src = ssh.stat(abs);
                    if (src == null) {
                        throw exception(STORAGE_FILE_NOT_FOUND);
                    }
                    if (ssh.stat(targetAbs) != null) {
                        throw exception(STORAGE_FILE_EXISTS);
                    }
                    ssh.rename(abs, targetAbs);
                }
            }
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

    /** 控制面节点：iot-node 本机直读写媒体根，不经 SSH */
    private boolean useLocalMediaFiles(ComputeNodeDO node) {
        return ComputeNodeServiceImpl.isPlatformNode(node);
    }

    private List<NodeStorageFileEntryVO> listRemoteMediaEntries(
            ComputeNodeDO node, String mountRoot, String abs) throws Exception {
        NodeSshCredential credential = loadSshCredential(node.getId());
        int sshPort = ComputeNodeServiceImpl.resolveSshPort(node);
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
            return vos;
        }
    }

    private List<NodeStorageFileEntryVO> listLocalMediaEntries(String mountRoot, String abs) throws IOException {
        Path dir = Paths.get(abs);
        if (!Files.exists(dir)) {
            try {
                Files.createDirectories(dir);
                if (abs.replaceAll("/+$", "").equals(mountRoot.replaceAll("/+$", ""))) {
                    ensureLocalMediaLayout(Paths.get(mountRoot));
                }
            } catch (AccessDeniedException e) {
                throw e;
            }
        }
        if (!Files.isDirectory(dir)) {
            throw exception(STORAGE_FILE_PATH_INVALID);
        }
        if (!Files.isReadable(dir)) {
            throw new AccessDeniedException(abs);
        }
        File[] files = dir.toFile().listFiles();
        List<NodeStorageFileEntryVO> vos = new ArrayList<>();
        if (files == null) {
            return vos;
        }
        Arrays.sort(files, Comparator.comparing(File::getName, String.CASE_INSENSITIVE_ORDER));
        for (File f : files) {
            if (f == null) {
                continue;
            }
            NodeStorageFileEntryVO vo = new NodeStorageFileEntryVO();
            vo.setName(f.getName());
            vo.setDirectory(f.isDirectory());
            vo.setSize(f.isFile() ? f.length() : 0L);
            if (f.lastModified() > 0) {
                vo.setMtime(LocalDateTime.ofInstant(Instant.ofEpochMilli(f.lastModified()), ZoneId.systemDefault()));
            }
            vo.setRelativePath(toRelativePath(mountRoot, joinPath(abs, f.getName())));
            vos.add(vo);
        }
        return vos;
    }

    private void deleteLocalRecursive(Path path) throws IOException {
        if (!Files.exists(path)) {
            return;
        }
        Files.walkFileTree(path, new SimpleFileVisitor<>() {
            @Override
            public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) throws IOException {
                Files.deleteIfExists(file);
                return FileVisitResult.CONTINUE;
            }

            @Override
            public FileVisitResult postVisitDirectory(Path dir, IOException exc) throws IOException {
                if (exc != null) {
                    throw exc;
                }
                Files.deleteIfExists(dir);
                return FileVisitResult.CONTINUE;
            }
        });
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
        if (useLocalMediaFiles(node)) {
            return findWritableLocalMediaRoot(node, true);
        }
        Map<String, String> tags = node.getTags() != null ? node.getTags() : Map.of();
        String mount = firstNonBlank(tags.get("media_mount_path"), tags.get("ceph_mount_path"), mediaHostDataRoot);
        if (!StringUtils.hasText(mount)) {
            mount = "/mnt/easyaiot-media";
        }
        return mount.replace('\\', '/').replaceAll("/+$", "");
    }

    /**
     * 控制面本机媒体根：优先可写路径。
     * Docker：优先容器挂载点（EASYAIOT_EDGE_MEDIA_ROOT / 配置）；
     * IDEA：优先 bootstrap/tags/环境变量，/mnt 无权限则回退 $HOME/easyaiot/media。
     *
     * @param required true 时找不到可写根抛业务异常（文件浏览）；false 时返回 null（拓扑展示）
     */
    private String findWritableLocalMediaRoot(ComputeNodeDO node, boolean required) {
        Map<String, String> tags = node.getTags() != null ? node.getTags() : Map.of();
        boolean docker = isRunningInDocker();
        LinkedHashMap<String, Boolean> ordered = new LinkedHashMap<>();
        addPathCandidate(ordered, System.getenv("EASYAIOT_EDGE_MEDIA_ROOT"));
        addPathCandidate(ordered, System.getenv("EASYAIOT_MEDIA_ROOT"));
        String homeFallback = Paths.get(System.getProperty("user.home", "."), "easyaiot", "media")
                .toAbsolutePath().normalize().toString();
        String tmpFallback = Paths.get(System.getProperty("java.io.tmpdir", "/tmp"), "easyaiot-media")
                .toAbsolutePath().normalize().toString();
        String cwdFallback = Paths.get(System.getProperty("user.dir", "."), "easyaiot-media")
                .toAbsolutePath().normalize().toString();
        if (docker) {
            // 容器内优先挂载点
            addPathCandidate(ordered, mediaHostDataRoot);
            addPathCandidate(ordered, tags.get("media_mount_path"));
            addPathCandidate(ordered, tags.get("ceph_mount_path"));
            addPathCandidate(ordered, homeFallback);
            addPathCandidate(ordered, tmpFallback);
        } else {
            // IDEA/宿主机：优先用户可写目录，避免 tags 里陈旧的 /mnt 抢先失败又挡住回退
            addPathCandidate(ordered, homeFallback);
            addPathCandidate(ordered, tmpFallback);
            addPathCandidate(ordered, cwdFallback);
            addPathCandidate(ordered, tags.get("media_mount_path"));
            addPathCandidate(ordered, tags.get("ceph_mount_path"));
            addPathCandidate(ordered, mediaHostDataRoot);
        }

        for (String candidate : ordered.keySet()) {
            if (tryPrepareLocalMediaRoot(candidate)) {
                syncPlatformMediaRootTag(node, candidate);
                return candidate.replace('\\', '/').replaceAll("/+$", "");
            }
        }
        if (required) {
            throw exception(STORAGE_MEDIA_ROOT_UNUSABLE,
                    StringUtils.hasText(mediaHostDataRoot) ? mediaHostDataRoot : "/mnt/easyaiot-media");
        }
        return null;
    }

    private static void addPathCandidate(LinkedHashMap<String, Boolean> ordered, String raw) {
        if (!StringUtils.hasText(raw)) {
            return;
        }
        String norm = raw.trim().replace('\\', '/').replaceAll("/+$", "");
        if (!norm.isEmpty()) {
            ordered.putIfAbsent(norm, Boolean.TRUE);
        }
    }

    private boolean tryPrepareLocalMediaRoot(String root) {
        if (!StringUtils.hasText(root)) {
            return false;
        }
        try {
            Path path = Paths.get(root);
            if (Files.exists(path)) {
                return Files.isDirectory(path) && Files.isReadable(path) && Files.isWritable(path);
            }
            Files.createDirectories(path);
            ensureLocalMediaLayout(path);
            return Files.isWritable(path);
        } catch (Exception ex) {
            log.debug("本机媒体根不可用 {}: {}", root, ex.toString());
            return false;
        }
    }

    private static void ensureLocalMediaLayout(Path root) throws IOException {
        Files.createDirectories(root.resolve("alert_images"));
        Files.createDirectories(root.resolve("playbacks/live"));
        Files.createDirectories(root.resolve("playbacks/ai"));
        Files.createDirectories(root.resolve("playbacks/gb28181"));
        Files.createDirectories(root.resolve("snaps"));
        Files.createDirectories(root.resolve("logs"));
    }

    /** 控制面本机媒体根就绪：写 tags，供覆盖率与文件浏览使用 */
    private void markPlatformLocalMediaReady(ComputeNodeDO node, String root, String summary) {
        if (node == null || node.getId() == null || !StringUtils.hasText(root)) {
            return;
        }
        String norm = root.replace('\\', '/').replaceAll("/+$", "");
        try {
            ComputeNodeDO latest = computeNodeMapper.selectById(node.getId());
            if (latest == null) {
                return;
            }
            Map<String, String> next = latest.getTags() != null ? new HashMap<>(latest.getTags()) : new HashMap<>();
            next.put("media_mount_path", norm);
            next.put("ceph_mount_path", norm);
            next.put("nfs_mount_ready", "true");
            next.put("ceph_mount_ready", "true");
            next.put("nfs_probe_ok", "true");
            next.put("nfs_probe_at", Instant.now().toString());
            next.put("nfs_mount_source", "local:" + norm);
            String shortSummary = summary != null ? summary.trim() : ("local media ready @ " + norm);
            if (shortSummary.length() > 240) {
                shortSummary = shortSummary.substring(0, 240);
            }
            next.put("nfs_probe_summary", shortSummary);
            latest.setTags(next);
            computeNodeMapper.updateById(latest);
            node.setTags(next);
        } catch (Exception ex) {
            log.warn("标记控制面本机媒体就绪失败: {}", ex.getMessage());
        }
    }

    /** 若实际使用的根与 tags 不一致（如从 /mnt 回退到 HOME），写回以免 UI 仍显示无权限路径 */
    private void syncPlatformMediaRootTag(ComputeNodeDO node, String root) {
        if (node == null || node.getId() == null || !StringUtils.hasText(root)) {
            return;
        }
        String norm = root.replace('\\', '/').replaceAll("/+$", "");
        Map<String, String> tags = node.getTags() != null ? node.getTags() : Map.of();
        String tagged = firstNonBlank(tags.get("media_mount_path"), tags.get("ceph_mount_path"), null);
        boolean pathSame = StringUtils.hasText(tagged) && tagged.replaceAll("/+$", "").equals(norm);
        boolean ready = "true".equalsIgnoreCase(String.valueOf(tags.get("nfs_mount_ready")));
        if (pathSame && ready) {
            return;
        }
        markPlatformLocalMediaReady(node, norm, "local-bootstrap/sync: media root ready @ " + norm);
    }

    private static boolean isRunningInDocker() {
        if (Files.exists(Paths.get("/.dockerenv"))) {
            return true;
        }
        try {
            String cgroup = Files.readString(Paths.get("/proc/1/cgroup"));
            String lower = cgroup.toLowerCase(Locale.ROOT);
            return lower.contains("docker") || lower.contains("containerd") || lower.contains("kubepods");
        } catch (Exception ignored) {
            return false;
        }
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
        String[] envKeys = {
                storageClusterSourcePath,
                System.getenv("EASYAIOT_STORAGE_CLUSTER_PATH"),
                System.getenv("EASYAIOT_MEDIA_CLUSTER_PATH"),
        };
        for (String configured : envKeys) {
            if (configured != null && !configured.isBlank()) {
                File dir = new File(configured.trim());
                if (dir.isDirectory() && new File(dir, "check_nfs_health.sh").isFile()) {
                    return dir.getAbsolutePath();
                }
            }
        }
        Path current = Paths.get(System.getProperty("user.dir", ".")).toAbsolutePath().normalize();
        for (int depth = 0; depth < 12 && current != null; depth++) {
            Path candidate = current.resolve(".scripts/media-cluster/nfs");
            if (Files.isRegularFile(candidate.resolve("check_nfs_health.sh"))) {
                return candidate.toAbsolutePath().toString();
            }
            // IDEA 常在 DEVICE/iot-node/iot-node-biz 下启动
            Path fromModule = current.resolve("../../.scripts/media-cluster/nfs").normalize();
            if (Files.isRegularFile(fromModule.resolve("check_nfs_health.sh"))) {
                return fromModule.toAbsolutePath().toString();
            }
            current = current.getParent();
        }
        String[] fallbacks = {
                "/opt/easyaiot/.scripts/media-cluster/nfs",
                System.getProperty("user.dir") + "/.scripts/media-cluster/nfs",
                System.getProperty("user.dir") + "/../.scripts/media-cluster/nfs",
        };
        for (String path : fallbacks) {
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
