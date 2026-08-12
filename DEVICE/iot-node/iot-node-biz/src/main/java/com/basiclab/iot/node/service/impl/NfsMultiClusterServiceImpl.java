package com.basiclab.iot.node.service.impl;

import com.basiclab.iot.node.dal.dataobject.ComputeNodeDO;
import com.basiclab.iot.node.dal.dataobject.NfsClusterBridgeDO;
import com.basiclab.iot.node.dal.dataobject.NfsClusterDO;
import com.basiclab.iot.node.dal.dataobject.NodeSshCredentialDO;
import com.basiclab.iot.node.dal.pgsql.ComputeNodeMapper;
import com.basiclab.iot.node.dal.pgsql.ControlPlanePeerMapper;
import com.basiclab.iot.node.dal.pgsql.NfsClusterBridgeMapper;
import com.basiclab.iot.node.dal.pgsql.NfsClusterMapper;
import com.basiclab.iot.node.dal.pgsql.NodeSshCredentialMapper;
import com.basiclab.iot.node.dal.dataobject.ControlPlanePeerDO;
import com.basiclab.iot.node.domain.vo.NfsBridgeCreateReqVO;
import com.basiclab.iot.node.domain.vo.NfsClusterActivateReqVO;
import com.basiclab.iot.node.domain.vo.NfsMultiClusterOverviewRespVO;
import com.basiclab.iot.node.service.NfsMultiClusterService;
import com.basiclab.iot.node.util.CredentialEncryptUtil;
import com.basiclab.iot.node.util.SshSessionHelper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;
import org.springframework.validation.annotation.Validated;

import javax.annotation.Resource;
import java.io.File;
import java.nio.file.Files;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.atomic.AtomicBoolean;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.COMPUTE_NODE_NOT_EXISTS;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.NFS_BRIDGE_INVALID;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.NFS_BRIDGE_RUNNING;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.NFS_BRIDGE_SOURCE_NOT_ACTIVE;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.NFS_CLUSTER_NOT_EXISTS;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.NFS_CLUSTER_SWITCH_BLOCKED;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.SSH_CREDENTIAL_NOT_EXISTS;

@Slf4j
@Service
@Validated
public class NfsMultiClusterServiceImpl implements NfsMultiClusterService {

    private static final String LOCAL_LANE = "local";
    private static final String DEFAULT_PATHS = "alert_images,playbacks,snaps";
    private static final long BRIDGE_FILE_MAX_BYTES = 200L * 1024 * 1024;

    private final AtomicBoolean bridgeRunning = new AtomicBoolean(false);

    @Resource
    private NfsClusterMapper nfsClusterMapper;
    @Resource
    private NfsClusterBridgeMapper nfsClusterBridgeMapper;
    @Resource
    private ComputeNodeMapper computeNodeMapper;
    @Resource
    private NodeSshCredentialMapper nodeSshCredentialMapper;
    @Resource
    private ControlPlanePeerMapper controlPlanePeerMapper;

    @Override
    public NfsMultiClusterOverviewRespVO getOverview() {
        ensureLocalClusterSeeded();
        ensurePeerClustersSeeded();
        NfsMultiClusterOverviewRespVO resp = new NfsMultiClusterOverviewRespVO();
        List<NfsClusterDO> clusters = nfsClusterMapper.selectAllActiveRows();
        Map<Long, ComputeNodeDO> nodeCache = new HashMap<>();
        List<NfsMultiClusterOverviewRespVO.NfsClusterRespVO> clusterVos = new ArrayList<>();
        for (NfsClusterDO c : clusters) {
            clusterVos.add(toClusterVo(c, nodeCache));
            if (Boolean.TRUE.equals(c.getIsActive())) {
                resp.setActiveClusterId(c.getId());
                resp.setActiveClusterName(c.getName());
            }
        }
        resp.setClusters(clusterVos);

        List<NfsMultiClusterOverviewRespVO.NfsBridgeRespVO> bridgeVos = new ArrayList<>();
        Map<Long, NfsClusterDO> clusterById = new HashMap<>();
        for (NfsClusterDO c : clusters) {
            clusterById.put(c.getId(), c);
        }
        for (NfsClusterBridgeDO b : nfsClusterBridgeMapper.selectAllOrdered()) {
            bridgeVos.add(toBridgeVo(b, clusterById));
        }
        resp.setBridges(bridgeVos);
        return resp;
    }

    @Override
    public NfsClusterDO upsertLocalCluster(
            ComputeNodeDO primary, ComputeNodeDO standby, String mountRoot, String nfsExport, String mountOpts) {
        NfsClusterDO existing = nfsClusterMapper.selectByLaneKey(LOCAL_LANE);
        ComputeNodeDO platform = computeNodeMapper.selectPlatformNode();
        Long cpId = platform != null ? platform.getId() : (primary != null ? primary.getId() : null);
        String name = platform != null && StringUtils.hasText(platform.getName())
                ? platform.getName() + " NFS"
                : "本机 NFS 集群";
        if (existing == null) {
            existing = new NfsClusterDO();
            existing.setLaneKey(LOCAL_LANE);
            existing.setName(name);
            existing.setControlPlaneId(cpId);
            existing.setStatus("active");
            existing.setIsActive(nfsClusterMapper.selectActive() == null);
            existing.setMountRoot(mountRoot);
            existing.setNfsExport(nfsExport);
            existing.setNfsMountOpts(mountOpts);
            existing.setPrimaryNodeId(primary != null ? primary.getId() : null);
            existing.setStandbyNodeId(standby != null ? standby.getId() : null);
            nfsClusterMapper.insert(existing);
        } else {
            existing.setName(name);
            existing.setControlPlaneId(cpId);
            existing.setMountRoot(mountRoot);
            existing.setNfsExport(nfsExport);
            existing.setNfsMountOpts(mountOpts);
            existing.setPrimaryNodeId(primary != null ? primary.getId() : null);
            existing.setStandbyNodeId(standby != null ? standby.getId() : null);
            existing.setStatus("active");
            if (nfsClusterMapper.selectActive() == null) {
                existing.setIsActive(true);
            }
            nfsClusterMapper.updateById(existing);
        }
        stampClusterIdOnMembers(existing);
        return existing;
    }

    private void stampClusterIdOnMembers(NfsClusterDO cluster) {
        if (cluster == null || cluster.getId() == null) {
            return;
        }
        List<Long> ids = new ArrayList<>();
        if (cluster.getPrimaryNodeId() != null) {
            ids.add(cluster.getPrimaryNodeId());
        }
        if (cluster.getStandbyNodeId() != null) {
            ids.add(cluster.getStandbyNodeId());
        }
        List<ComputeNodeDO> all = computeNodeMapper.selectList();
        if (all != null) {
            for (ComputeNodeDO n : all) {
                if (n == null || n.getId() == null || n.getTags() == null) {
                    continue;
                }
                String role = n.getTags().get("nfs_cluster_role");
                if ("client".equals(role) || "candidate".equals(role)) {
                    ids.add(n.getId());
                }
            }
        }
        for (Long id : ids) {
            ComputeNodeDO node = computeNodeMapper.selectById(id);
            if (node == null) {
                continue;
            }
            Map<String, String> tags = node.getTags() != null ? new HashMap<>(node.getTags()) : new HashMap<>();
            tags.put("nfs_cluster_id", String.valueOf(cluster.getId()));
            node.setTags(tags);
            computeNodeMapper.updateById(node);
        }
    }

    private void ensureLocalClusterSeeded() {
        if (nfsClusterMapper.selectByLaneKey(LOCAL_LANE) != null) {
            return;
        }
        ComputeNodeDO platform = computeNodeMapper.selectPlatformNode();
        ComputeNodeDO primary = null;
        ComputeNodeDO standby = null;
        List<ComputeNodeDO> all = computeNodeMapper.selectList();
        if (all != null) {
            for (ComputeNodeDO n : all) {
                if (n == null || n.getTags() == null) {
                    continue;
                }
                String role = n.getTags().get("nfs_cluster_role");
                if ("primary".equals(role) && primary == null) {
                    primary = n;
                } else if ("standby".equals(role) && standby == null) {
                    standby = n;
                }
            }
        }
        if (primary == null) {
            primary = platform;
        }
        String mount = "/mnt/easyaiot-media";
        if (primary != null && primary.getTags() != null && StringUtils.hasText(primary.getTags().get("media_mount_path"))) {
            mount = primary.getTags().get("media_mount_path");
        }
        upsertLocalCluster(primary, standby, mount, mount, "vers=3,tcp,nolock,_netdev");
    }

    private void ensurePeerClustersSeeded() {
        List<ControlPlanePeerDO> peers = controlPlanePeerMapper.selectList();
        if (peers == null || peers.isEmpty()) {
            return;
        }
        for (ControlPlanePeerDO peer : peers) {
            if (peer == null || peer.getId() == null) {
                continue;
            }
            String laneKey = "peer-" + peer.getId();
            if (nfsClusterMapper.selectByLaneKey(laneKey) != null) {
                continue;
            }
            NfsClusterDO row = new NfsClusterDO();
            row.setLaneKey(laneKey);
            row.setName(StringUtils.hasText(peer.getName()) ? peer.getName() + " NFS" : laneKey + " NFS");
            row.setControlPlaneId(peer.getRemotePlatformNodeId());
            row.setPrimaryNodeId(peer.getRemotePlatformNodeId());
            row.setMountRoot("/mnt/easyaiot-media");
            row.setNfsExport("/mnt/easyaiot-media");
            row.setNfsMountOpts("vers=3,tcp,nolock,_netdev");
            row.setIsActive(false);
            row.setStatus("active");
            row.setRemark(peer.getHost());
            nfsClusterMapper.insert(row);
        }
    }

    @Override
    public NfsMultiClusterOverviewRespVO activateCluster(NfsClusterActivateReqVO req) {
        if (req == null || req.getClusterId() == null) {
            throw exception(NFS_CLUSTER_NOT_EXISTS);
        }
        NfsClusterDO target = nfsClusterMapper.selectById(req.getClusterId());
        if (target == null) {
            throw exception(NFS_CLUSTER_NOT_EXISTS);
        }
        NfsClusterDO current = nfsClusterMapper.selectActive();
        if (current != null && current.getId().equals(target.getId())) {
            return getOverview();
        }
        List<NfsClusterBridgeDO> activeBridges = new ArrayList<>();
        if (current != null) {
            for (NfsClusterBridgeDO b : nfsClusterBridgeMapper.selectBySourceClusterId(current.getId())) {
                if (Boolean.TRUE.equals(b.getEnabled()) && !"stopped".equals(b.getStatus())) {
                    activeBridges.add(b);
                }
            }
        }
        if (!activeBridges.isEmpty() && !Boolean.TRUE.equals(req.getForceStopBridges())) {
            throw exception(NFS_CLUSTER_SWITCH_BLOCKED);
        }
        if (current != null) {
            stopBridgesBySourceCluster(current.getId());
            current.setIsActive(false);
            nfsClusterMapper.updateById(current);
        }
        for (NfsClusterDO c : nfsClusterMapper.selectAllActiveRows()) {
            if (Boolean.TRUE.equals(c.getIsActive()) && !c.getId().equals(target.getId())) {
                c.setIsActive(false);
                nfsClusterMapper.updateById(c);
            }
        }
        target.setIsActive(true);
        nfsClusterMapper.updateById(target);
        return getOverview();
    }

    @Override
    public NfsMultiClusterOverviewRespVO createBridge(NfsBridgeCreateReqVO req) {
        if (req == null || req.getSourceClusterId() == null || req.getTargetClusterId() == null) {
            throw exception(NFS_BRIDGE_INVALID);
        }
        if (req.getSourceClusterId().equals(req.getTargetClusterId())) {
            throw exception(NFS_BRIDGE_INVALID);
        }
        NfsClusterDO source = nfsClusterMapper.selectById(req.getSourceClusterId());
        NfsClusterDO target = nfsClusterMapper.selectById(req.getTargetClusterId());
        if (source == null || target == null) {
            throw exception(NFS_CLUSTER_NOT_EXISTS);
        }
        if (!Boolean.TRUE.equals(source.getIsActive())) {
            throw exception(NFS_BRIDGE_SOURCE_NOT_ACTIVE);
        }
        String targetRel = StringUtils.hasText(req.getTargetRelPath())
                ? req.getTargetRelPath().trim().replaceAll("^/+", "").replaceAll("/+$", "")
                : "_bridge/" + source.getId();
        if (!targetRel.startsWith("_bridge/") && !"_bridge".equals(targetRel)) {
            throw exception(NFS_BRIDGE_INVALID);
        }
        if (targetRel.contains("..")) {
            throw exception(NFS_BRIDGE_INVALID);
        }
        String paths = StringUtils.hasText(req.getSourceRelPaths()) ? req.getSourceRelPaths().trim() : DEFAULT_PATHS;
        NfsClusterBridgeDO bridge = new NfsClusterBridgeDO();
        bridge.setName(StringUtils.hasText(req.getName()) ? req.getName().trim()
                : source.getName() + " → " + target.getName());
        bridge.setSourceClusterId(source.getId());
        bridge.setTargetClusterId(target.getId());
        bridge.setSourceRelPaths(paths);
        bridge.setTargetRelPath(targetRel);
        bridge.setScheduleCron(StringUtils.hasText(req.getScheduleCron()) ? req.getScheduleCron().trim() : null);
        bridge.setEnabled(true);
        bridge.setStatus("idle");
        nfsClusterBridgeMapper.insert(bridge);
        return getOverview();
    }

    @Override
    public NfsMultiClusterOverviewRespVO stopBridge(Long bridgeId) {
        NfsClusterBridgeDO bridge = requireBridge(bridgeId);
        bridge.setEnabled(false);
        bridge.setStatus("stopped");
        bridge.setLastMessage("已停止");
        nfsClusterBridgeMapper.updateById(bridge);
        return getOverview();
    }

    @Override
    public NfsMultiClusterOverviewRespVO enableBridge(Long bridgeId, boolean enabled) {
        NfsClusterBridgeDO bridge = requireBridge(bridgeId);
        bridge.setEnabled(enabled);
        bridge.setStatus(enabled ? "idle" : "stopped");
        nfsClusterBridgeMapper.updateById(bridge);
        return getOverview();
    }

    @Override
    public int stopBridgesBySourceCluster(Long sourceClusterId) {
        if (sourceClusterId == null) {
            return 0;
        }
        int n = 0;
        for (NfsClusterBridgeDO b : nfsClusterBridgeMapper.selectBySourceClusterId(sourceClusterId)) {
            if (Boolean.TRUE.equals(b.getEnabled()) || !"stopped".equals(b.getStatus())) {
                b.setEnabled(false);
                b.setStatus("stopped");
                b.setLastMessage("主集群切换：已自动停止桥接");
                nfsClusterBridgeMapper.updateById(b);
                n++;
            }
        }
        return n;
    }

    @Override
    public NfsMultiClusterOverviewRespVO runBridge(Long bridgeId) {
        NfsClusterBridgeDO bridge = requireBridge(bridgeId);
        if (!Boolean.TRUE.equals(bridge.getEnabled())) {
            throw exception(NFS_BRIDGE_INVALID);
        }
        NfsClusterDO source = nfsClusterMapper.selectById(bridge.getSourceClusterId());
        if (source == null || !Boolean.TRUE.equals(source.getIsActive())) {
            throw exception(NFS_BRIDGE_SOURCE_NOT_ACTIVE);
        }
        if (!bridgeRunning.compareAndSet(false, true)) {
            throw exception(NFS_BRIDGE_RUNNING);
        }
        bridge.setStatus("running");
        nfsClusterBridgeMapper.updateById(bridge);
        try {
            String msg = doSync(bridge, source);
            bridge.setLastRunAt(LocalDateTime.now());
            bridge.setLastSuccess(true);
            bridge.setLastMessage(msg);
            bridge.setStatus("idle");
            nfsClusterBridgeMapper.updateById(bridge);
        } catch (RuntimeException e) {
            bridge.setLastRunAt(LocalDateTime.now());
            bridge.setLastSuccess(false);
            bridge.setLastMessage(e.getMessage());
            bridge.setStatus("error");
            nfsClusterBridgeMapper.updateById(bridge);
            throw e;
        } catch (Exception e) {
            bridge.setLastRunAt(LocalDateTime.now());
            bridge.setLastSuccess(false);
            bridge.setLastMessage(e.getMessage());
            bridge.setStatus("error");
            nfsClusterBridgeMapper.updateById(bridge);
            throw exception(NFS_BRIDGE_INVALID);
        } finally {
            bridgeRunning.set(false);
        }
        return getOverview();
    }

    private String doSync(NfsClusterBridgeDO bridge, NfsClusterDO source) throws Exception {
        NfsClusterDO target = nfsClusterMapper.selectById(bridge.getTargetClusterId());
        if (target == null || target.getPrimaryNodeId() == null) {
            throw exception(NFS_CLUSTER_NOT_EXISTS);
        }
        if (source.getPrimaryNodeId() == null) {
            throw exception(NFS_CLUSTER_NOT_EXISTS);
        }
        ComputeNodeDO srcNode = computeNodeMapper.selectById(source.getPrimaryNodeId());
        ComputeNodeDO dstNode = computeNodeMapper.selectById(target.getPrimaryNodeId());
        if (srcNode == null || dstNode == null) {
            throw exception(COMPUTE_NODE_NOT_EXISTS);
        }
        String srcRoot = StringUtils.hasText(source.getMountRoot()) ? source.getMountRoot() : "/mnt/easyaiot-media";
        String dstRoot = StringUtils.hasText(target.getMountRoot()) ? target.getMountRoot() : "/mnt/easyaiot-media";
        String targetRel = StringUtils.hasText(bridge.getTargetRelPath())
                ? bridge.getTargetRelPath()
                : "_bridge/" + source.getId();
        String[] paths = (StringUtils.hasText(bridge.getSourceRelPaths()) ? bridge.getSourceRelPaths() : DEFAULT_PATHS)
                .split(",");

        int files = 0;
        int skipped = 0;
        boolean srcLocal = ComputeNodeServiceImpl.isPlatformNode(srcNode);
        boolean dstLocal = ComputeNodeServiceImpl.isPlatformNode(dstNode);

        try (SshSessionHelper srcSsh = srcLocal ? null : openSsh(srcNode);
             SshSessionHelper dstSsh = dstLocal ? null : openSsh(dstNode)) {
            for (String raw : paths) {
                String rel = raw == null ? "" : raw.trim().replaceAll("^/+", "").replaceAll("/+$", "");
                if (!StringUtils.hasText(rel) || rel.contains("..")) {
                    continue;
                }
                String srcAbs = join(srcRoot, rel);
                String dstAbs = join(dstRoot, join(targetRel, rel));
                int[] counts = syncTree(srcLocal, srcSsh, srcAbs, dstLocal, dstSsh, dstAbs);
                files += counts[0];
                skipped += counts[1];
            }
        }
        return String.format("同步完成：写入 %d 个文件，跳过过大/异常 %d（目标 %s；首次含历史全量，后续增量）",
                files, skipped, targetRel);
    }

    private int[] syncTree(
            boolean srcLocal, SshSessionHelper srcSsh, String srcAbs,
            boolean dstLocal, SshSessionHelper dstSsh, String dstAbs) throws Exception {
        int files = 0;
        int skipped = 0;
        if (srcLocal) {
            File srcDir = new File(srcAbs);
            if (!srcDir.isDirectory()) {
                return new int[]{0, 0};
            }
            ensureDstDir(dstLocal, dstSsh, dstAbs);
            File[] children = srcDir.listFiles();
            if (children == null) {
                return new int[]{0, 0};
            }
            for (File child : children) {
                String childDst = join(dstAbs, child.getName());
                if (child.isDirectory()) {
                    int[] sub = syncTree(true, null, child.getAbsolutePath(), dstLocal, dstSsh, childDst);
                    files += sub[0];
                    skipped += sub[1];
                } else if (child.isFile()) {
                    if (child.length() > BRIDGE_FILE_MAX_BYTES) {
                        skipped++;
                        continue;
                    }
                    byte[] bytes = Files.readAllBytes(child.toPath());
                    writeDstFile(dstLocal, dstSsh, childDst, bytes);
                    files++;
                }
            }
            return new int[]{files, skipped};
        }

        List<SshSessionHelper.SftpEntry> entries = srcSsh.listDir(srcAbs);
        ensureDstDir(dstLocal, dstSsh, dstAbs);
        for (SshSessionHelper.SftpEntry e : entries) {
            if (".".equals(e.name) || "..".equals(e.name)) {
                continue;
            }
            String childSrc = join(srcAbs, e.name);
            String childDst = join(dstAbs, e.name);
            if (e.directory) {
                int[] sub = syncTree(false, srcSsh, childSrc, dstLocal, dstSsh, childDst);
                files += sub[0];
                skipped += sub[1];
            } else {
                if (e.size > BRIDGE_FILE_MAX_BYTES) {
                    skipped++;
                    continue;
                }
                byte[] bytes = srcSsh.downloadBytes(childSrc);
                writeDstFile(dstLocal, dstSsh, childDst, bytes);
                files++;
            }
        }
        return new int[]{files, skipped};
    }

    private void ensureDstDir(boolean dstLocal, SshSessionHelper dstSsh, String dstAbs) throws Exception {
        if (dstLocal) {
            Files.createDirectories(new File(dstAbs).toPath());
        } else {
            dstSsh.ensureRemoteDir(dstAbs);
        }
    }

    private void writeDstFile(boolean dstLocal, SshSessionHelper dstSsh, String dstAbs, byte[] bytes) throws Exception {
        if (dstLocal) {
            File f = new File(dstAbs);
            File parent = f.getParentFile();
            if (parent != null) {
                Files.createDirectories(parent.toPath());
            }
            Files.write(f.toPath(), bytes);
        } else {
            int slash = dstAbs.lastIndexOf('/');
            if (slash > 0) {
                dstSsh.ensureRemoteDir(dstAbs.substring(0, slash));
            }
            dstSsh.uploadBytes(dstAbs, bytes);
        }
    }

    private SshSessionHelper openSsh(ComputeNodeDO node) throws Exception {
        NodeSshCredentialDO credential = nodeSshCredentialMapper.selectByNodeId(node.getId());
        if (credential == null || !StringUtils.hasText(credential.getCredentialEnc())) {
            throw exception(SSH_CREDENTIAL_NOT_EXISTS);
        }
        String password = null;
        String privateKey = null;
        if ("password".equals(credential.getAuthType())) {
            password = CredentialEncryptUtil.decrypt(credential.getCredentialEnc());
        } else {
            privateKey = CredentialEncryptUtil.decrypt(credential.getCredentialEnc());
        }
        int port = ComputeNodeServiceImpl.resolveSshPort(node);
        return SshSessionHelper.connect(
                node.getHost(), port, credential.getUsername(), credential.getAuthType(), password, privateKey);
    }

    private NfsClusterBridgeDO requireBridge(Long id) {
        if (id == null) {
            throw exception(NFS_BRIDGE_INVALID);
        }
        NfsClusterBridgeDO bridge = nfsClusterBridgeMapper.selectById(id);
        if (bridge == null) {
            throw exception(NFS_BRIDGE_INVALID);
        }
        return bridge;
    }

    private NfsMultiClusterOverviewRespVO.NfsClusterRespVO toClusterVo(
            NfsClusterDO c, Map<Long, ComputeNodeDO> nodeCache) {
        NfsMultiClusterOverviewRespVO.NfsClusterRespVO vo = new NfsMultiClusterOverviewRespVO.NfsClusterRespVO();
        vo.setId(c.getId());
        vo.setName(c.getName());
        vo.setLaneKey(c.getLaneKey());
        vo.setControlPlaneId(c.getControlPlaneId());
        vo.setPrimaryNodeId(c.getPrimaryNodeId());
        vo.setStandbyNodeId(c.getStandbyNodeId());
        vo.setMountRoot(c.getMountRoot());
        vo.setNfsExport(c.getNfsExport());
        vo.setIsActive(c.getIsActive());
        vo.setStatus(c.getStatus());
        ComputeNodeDO primary = resolveNode(c.getPrimaryNodeId(), nodeCache);
        if (primary != null) {
            vo.setPrimaryHost(primary.getHost());
            vo.setPrimaryName(primary.getName());
            vo.setPrimaryReady(readMountReady(primary));
        }
        ComputeNodeDO standby = resolveNode(c.getStandbyNodeId(), nodeCache);
        if (standby != null) {
            vo.setStandbyHost(standby.getHost());
            vo.setStandbyName(standby.getName());
        }
        int clients = 0;
        int ready = 0;
        String clusterIdStr = String.valueOf(c.getId());
        List<ComputeNodeDO> all = computeNodeMapper.selectList();
        if (all != null) {
            for (ComputeNodeDO n : all) {
                if (n == null || n.getTags() == null) {
                    continue;
                }
                if (!clusterIdStr.equals(n.getTags().get("nfs_cluster_id"))) {
                    continue;
                }
                if ("client".equals(n.getTags().get("nfs_cluster_role"))) {
                    clients++;
                    if (readMountReady(n)) {
                        ready++;
                    }
                }
            }
        }
        vo.setClientCount(clients);
        vo.setClientReadyCount(ready);
        return vo;
    }

    private NfsMultiClusterOverviewRespVO.NfsBridgeRespVO toBridgeVo(
            NfsClusterBridgeDO b, Map<Long, NfsClusterDO> clusterById) {
        NfsMultiClusterOverviewRespVO.NfsBridgeRespVO vo = new NfsMultiClusterOverviewRespVO.NfsBridgeRespVO();
        vo.setId(b.getId());
        vo.setName(b.getName());
        vo.setSourceClusterId(b.getSourceClusterId());
        vo.setTargetClusterId(b.getTargetClusterId());
        vo.setSourceRelPaths(b.getSourceRelPaths());
        vo.setTargetRelPath(b.getTargetRelPath());
        vo.setScheduleCron(b.getScheduleCron());
        vo.setEnabled(b.getEnabled());
        vo.setStatus(b.getStatus());
        vo.setLastRunAt(b.getLastRunAt());
        vo.setLastSuccess(b.getLastSuccess());
        vo.setLastMessage(b.getLastMessage());
        vo.setCreateTime(b.getCreateTime());
        NfsClusterDO src = clusterById.get(b.getSourceClusterId());
        NfsClusterDO dst = clusterById.get(b.getTargetClusterId());
        if (src != null) {
            vo.setSourceClusterName(src.getName());
        }
        if (dst != null) {
            vo.setTargetClusterName(dst.getName());
        }
        return vo;
    }

    private ComputeNodeDO resolveNode(Long id, Map<Long, ComputeNodeDO> cache) {
        if (id == null) {
            return null;
        }
        if (cache.containsKey(id)) {
            return cache.get(id);
        }
        ComputeNodeDO n = computeNodeMapper.selectById(id);
        cache.put(id, n);
        return n;
    }

    private boolean readMountReady(ComputeNodeDO node) {
        if (node == null || node.getTags() == null) {
            return false;
        }
        String ready = node.getTags().get("nfs_mount_ready");
        if (!StringUtils.hasText(ready)) {
            ready = node.getTags().get("ceph_mount_ready");
        }
        if (!StringUtils.hasText(ready)) {
            return false;
        }
        String r = ready.trim().toLowerCase(Locale.ROOT);
        return "true".equals(r) || "1".equals(r) || "yes".equals(r);
    }

    private static String join(String a, String b) {
        String left = a == null ? "" : a.replaceAll("/+$", "");
        String right = b == null ? "" : b.replaceAll("^/+", "");
        if (!StringUtils.hasText(left)) {
            return "/" + right;
        }
        if (!StringUtils.hasText(right)) {
            return left;
        }
        return left + "/" + right;
    }
}
