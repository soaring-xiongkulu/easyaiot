package com.basiclab.iot.node.util;

import cn.hutool.core.util.StrUtil;
import com.basiclab.iot.node.dal.dataobject.ComputeNodeDO;

import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;

/**
 * NFS 共享媒体栈远程部署（唯一存储方式；未指定 NFS 服务端时默认本机 export）。
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
     * 未配置 nfs_server_host 时：storage 角色用本机；其他角色默认 127.0.0.1（本机 export 回退）。
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
        if (isStorageRole(node.getNodeRole()) && StrUtil.isNotBlank(node.getHost())) {
            return node.getHost().trim();
        }
        return "127.0.0.1";
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
        return "storage".equalsIgnoreCase(role);
    }

    public static boolean isClientMountRole(String role) {
        if (role == null) {
            return false;
        }
        String r = role.toLowerCase(Locale.ROOT);
        return "storage".equals(r) || "media".equals(r) || "hybrid".equals(r)
                || "compute".equals(r) || "gpu".equals(r);
    }
}
