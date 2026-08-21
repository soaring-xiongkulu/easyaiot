package com.basiclab.iot.node.util;

import cn.hutool.core.util.StrUtil;
import com.basiclab.iot.node.dal.dataobject.ComputeNodeDO;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/**
 * NFS 共享媒体栈远程部署（唯一产品存储通路）。
 * 未配置 nfs_server_host 时：勾选 nfs 的节点用本机 host；其它节点不得静默回退为 local_bind。
 */
public final class StorageStackDeployUtil {

    private static final String REMOTE_ROOT = "/opt/easyaiot/storage-cluster";
    private static final String DEFAULT_MOUNT_ROOT = "/mnt/easyaiot-media";
    private static final String DEFAULT_NFS_MOUNT_OPTS = "vers=3,tcp,nolock,_netdev";

    private StorageStackDeployUtil() {
    }

    public static String remoteClusterRoot() {
        return REMOTE_ROOT;
    }

    public static String tagString(Map<String, String> tags, String key, String defaultValue) {
        if (tags == null || !tags.containsKey(key)) {
            return defaultValue;
        }
        String raw = tags.get(key);
        return StrUtil.isBlank(raw) ? defaultValue : raw.trim();
    }

    public static Map<String, String> buildDeployEnvMap(ComputeNodeDO node) {
        Map<String, String> tags = node.getTags();
        Map<String, String> env = new LinkedHashMap<>();
        String mountRoot = tagString(tags, "media_mount_path", DEFAULT_MOUNT_ROOT);
        String nfsExport = tagString(tags, "nfs_export", mountRoot);
        String nfsServer = resolveNfsServerHost(node, tags);

        env.put("STORAGE_CLUSTER_ROOT", REMOTE_ROOT);
        env.put("MOUNT_ROOT", mountRoot);
        env.put("NFS_SERVER", nfsServer);
        env.put("NFS_EXPORT", nfsExport);
        env.put("NFS_MOUNT_OPTS", tagString(tags, "nfs_mount_opts", DEFAULT_NFS_MOUNT_OPTS));
        env.put("NODE_HOST", StrUtil.blankToDefault(node.getHost(), ""));
        env.put("NODE_NAME", StrUtil.blankToDefault(node.getName(), node.getHost()));
        return env;
    }

    /**
     * 解析 NFS 服务端地址（唯一 NFS 通路）。
     * <ul>
     *   <li>优先 tags.nfs_server_host / 兼容 ceph_mon_host</li>
     *   <li>勾选 nfs 的节点未配置时用本机 host（本机即 Export 服务端）</li>
     *   <li>客户端未配置时不得回退为本机 IP（否则会挂到自己）</li>
     * </ul>
     */
    public static String resolveNfsServerHost(ComputeNodeDO node, Map<String, String> tags) {
        String explicit = tagString(tags, "nfs_server_host", null);
        if (StrUtil.isNotBlank(explicit)) {
            return explicit.trim();
        }
        String legacy = tagString(tags, "ceph_mon_host", null);
        if (StrUtil.isNotBlank(legacy)) {
            return legacy.trim();
        }
        String role = node != null ? node.getNodeRole() : null;
        if (isStorageRole(role)) {
            if (node != null && StrUtil.isNotBlank(node.getHost())) {
                return node.getHost().trim();
            }
            return "127.0.0.1";
        }
        // 拓扑主/备服务端：即使未勾选 nfs 功能，也应作为 Export 端
        String clusterRole = tagString(tags, "nfs_cluster_role", null);
        if ("primary".equalsIgnoreCase(clusterRole) || "standby".equalsIgnoreCase(clusterRole)
                || "server".equalsIgnoreCase(tagString(tags, "nfs_role", null))) {
            if (node != null && StrUtil.isNotBlank(node.getHost())) {
                return node.getHost().trim();
            }
            return "127.0.0.1";
        }
        // 客户端：缺省标签时返回空，由安装脚本显式失败，避免误挂本机
        return "";
    }

    public static String buildDeployEnvScript(ComputeNodeDO node) {
        StringBuilder sb = new StringBuilder("#!/usr/bin/env bash\nset -euo pipefail\n");
        for (Map.Entry<String, String> entry : buildDeployEnvMap(node).entrySet()) {
            sb.append("export ").append(entry.getKey()).append("=\"")
                    .append(entry.getValue().replace("\"", "\\\"")).append("\"\n");
        }
        return sb.toString();
    }

    public static String buildClientInstallScript(ComputeNodeDO node) {
        return buildDeployEnvScript(node)
                + "bash \"${STORAGE_CLUSTER_ROOT}/install_nfs_client.sh\"\n";
    }

    /** 原 OSD 部署 → NFS 服务端安装 */
    public static String buildOsdInstallScript(ComputeNodeDO node) {
        return buildDeployEnvScript(node)
                + "bash \"${STORAGE_CLUSTER_ROOT}/install_nfs_server.sh\"\n";
    }

    /** 原 Pool 创建 → 初始化 export 子目录 */
    public static String buildPoolCreateScript(ComputeNodeDO node) {
        return buildDeployEnvScript(node)
                + "bash \"${STORAGE_CLUSTER_ROOT}/install_nfs_server.sh\"\n";
    }

    public static String buildHealthCheckScript(ComputeNodeDO node) {
        return buildDeployEnvScript(node)
                + "bash \"${STORAGE_CLUSTER_ROOT}/check_nfs_health.sh\"\n";
    }

    public static String buildUnmountScript(ComputeNodeDO node) {
        String mount = buildDeployEnvMap(node).get("MOUNT_ROOT");
        return buildDeployEnvScript(node)
                + "if mountpoint -q \"" + mount + "\"; then umount \"" + mount + "\" || true; fi\n"
                + "echo UNMOUNT_OK\n";
    }

    public static boolean isStorageRole(String role) {
        return NodeFunctions.parse(role).contains("nfs");
    }

    public static boolean isClientMountRole(String role) {
        List<String> functions = NodeFunctions.parse(role);
        for (String id : NodeFunctions.NFS_CLIENT) {
            if (functions.contains(id)) {
                return true;
            }
        }
        return false;
    }
}
