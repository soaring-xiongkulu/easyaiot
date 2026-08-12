package com.basiclab.iot.node.framework.bootstrap;

import com.basiclab.iot.node.dal.dataobject.ComputeNodeDO;
import com.basiclab.iot.node.dal.pgsql.ComputeNodeMapper;
import com.basiclab.iot.node.domain.vo.NodeNfsClusterAssignReqVO;
import com.basiclab.iot.node.service.NodeStorageService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;

import javax.annotation.Resource;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;

/**
 * IDEA / 宿主机本地启动时：自动准备媒体根、尽量拉起本机 NFS，并为控制面补齐主服务端角色映射。
 * Docker 容器内默认只建目录 + 角色 tags（真 NFS 由宿主机 install / 挂载卷提供）。
 */
@Slf4j
@Order(200)
@Component
public class LocalNfsMediaBootstrap implements ApplicationRunner {

    private static final String DEFAULT_ROOT = "/mnt/easyaiot-media";

    @Value("${easyaiot.storage.local-nfs-bootstrap:true}")
    private boolean enabled;

    @Value("${easyaiot.edge.media-host-data-root:" + DEFAULT_ROOT + "}")
    private String configuredMediaRoot;

    @Resource
    private NodeStorageService nodeStorageService;
    @Resource
    private ComputeNodeMapper computeNodeMapper;

    @Override
    public void run(ApplicationArguments args) {
        if (!enabled) {
            return;
        }
        if ("0".equals(System.getenv("EASYAIOT_LOCAL_NFS_BOOTSTRAP"))) {
            return;
        }
        try {
            Path mediaRoot = resolveWritableMediaRoot();
            ensureMediaLayout(mediaRoot);
            boolean docker = isRunningInDocker();
            if (!docker || "1".equals(System.getenv("EASYAIOT_LOCAL_NFS_BOOTSTRAP"))) {
                tryEnsureNfsStack(mediaRoot);
            } else {
                log.info("[LocalNfsMediaBootstrap] 容器环境：跳过本机 NFS 安装，仅确保目录 {}", mediaRoot);
            }
            ensurePlatformNfsMapping(mediaRoot);
        } catch (Exception ex) {
            log.warn("[LocalNfsMediaBootstrap] 本地 NFS 映射引导失败（不影响启动）: {}", ex.getMessage());
        }
    }

    private Path resolveWritableMediaRoot() {
        String envRoot = firstNonBlank(
                System.getenv("EASYAIOT_EDGE_MEDIA_ROOT"),
                System.getenv("EASYAIOT_MEDIA_ROOT"),
                configuredMediaRoot);
        Path preferred = Paths.get(StringUtils.hasText(envRoot) ? envRoot.trim() : DEFAULT_ROOT);
        if (canUseRoot(preferred)) {
            return preferred.toAbsolutePath().normalize();
        }
        Path home = Paths.get(System.getProperty("user.home", "."), "easyaiot", "media");
        log.warn("[LocalNfsMediaBootstrap] {} 不可写，回退到 {}", preferred, home);
        return home.toAbsolutePath().normalize();
    }

    private boolean canUseRoot(Path root) {
        try {
            Files.createDirectories(root);
            Path probe = root.resolve(".easyaiot_write_probe");
            Files.writeString(probe, "ok", StandardCharsets.UTF_8);
            Files.deleteIfExists(probe);
            return true;
        } catch (Exception ignored) {
            return false;
        }
    }

    private void ensureMediaLayout(Path root) throws Exception {
        Files.createDirectories(root.resolve("alert_images"));
        Files.createDirectories(root.resolve("playbacks/live"));
        Files.createDirectories(root.resolve("playbacks/ai"));
        Files.createDirectories(root.resolve("playbacks/gb28181"));
        Files.createDirectories(root.resolve("snaps"));
        Files.createDirectories(root.resolve("logs"));
        try {
            root.toFile().setWritable(true, false);
        } catch (Exception ignored) {
            // best-effort
        }
        log.info("[LocalNfsMediaBootstrap] 媒体根已就绪: {}", root);
    }

    private void tryEnsureNfsStack(Path mediaRoot) {
        Path script = resolveEnsureScript();
        if (script == null) {
            log.info("[LocalNfsMediaBootstrap] 未找到 ensure_nfs_media_stack.sh，仅使用本地目录 {}", mediaRoot);
            return;
        }
        try {
            ProcessBuilder pb = new ProcessBuilder("bash", script.toAbsolutePath().toString());
            pb.redirectErrorStream(true);
            Map<String, String> env = pb.environment();
            env.put("EASYAIOT_MEDIA_ROOT", mediaRoot.toString());
            env.put("MOUNT_ROOT", mediaRoot.toString());
            env.put("NFS_EXPORT", mediaRoot.toString());
            if (!StringUtils.hasText(env.get("NFS_SERVER"))) {
                env.put("NFS_SERVER", "127.0.0.1");
            }
            Process process = pb.start();
            String output;
            try (BufferedReader reader = new BufferedReader(
                    new InputStreamReader(process.getInputStream(), StandardCharsets.UTF_8))) {
                output = reader.lines().collect(Collectors.joining("\n"));
            }
            boolean finished = process.waitFor(3, TimeUnit.MINUTES);
            if (!finished) {
                process.destroyForcibly();
                log.warn("[LocalNfsMediaBootstrap] ensure_nfs_media_stack 超时");
                return;
            }
            int code = process.exitValue();
            if (code == 0 || (output != null && output.contains("ENSURE_NFS_MEDIA_STACK_OK"))) {
                log.info("[LocalNfsMediaBootstrap] 本机 NFS 栈已确保: {}", mediaRoot);
            } else {
                log.warn("[LocalNfsMediaBootstrap] ensure_nfs_media_stack 退出码={}，已保留本地目录。输出: {}",
                        code, abbreviate(output, 400));
            }
        } catch (Exception ex) {
            log.warn("[LocalNfsMediaBootstrap] 执行 ensure_nfs_media_stack 失败: {}", ex.getMessage());
        }
    }

    private void ensurePlatformNfsMapping(Path mediaRoot) {
        ComputeNodeDO platform = computeNodeMapper.selectPlatformNode();
        if (platform == null) {
            log.debug("[LocalNfsMediaBootstrap] 控制面节点尚未纳管，跳过角色映射");
            return;
        }

        Map<String, String> tags = platform.getTags();
        String role = tags != null ? tags.get("nfs_cluster_role") : null;
        if (!StringUtils.hasText(role)) {
            // 显式传入 clientNodeIds，避免空列表触发「自动拉全量客户端」
            // （否则远程 pending 节点会被标成 client，挂载覆盖率恒为 0%）
            NodeNfsClusterAssignReqVO req = new NodeNfsClusterAssignReqVO();
            req.setServerNodeId(platform.getId());
            req.setMountRoot(mediaRoot.toString());
            req.setNfsExport(mediaRoot.toString());
            req.setClientNodeIds(java.util.List.of(platform.getId()));
            nodeStorageService.assignNfsCluster(req);
            platform = computeNodeMapper.selectById(platform.getId());
            log.info("[LocalNfsMediaBootstrap] 已为控制面自动分配 NFS 主服务端映射: nodeId={} root={}",
                    platform != null ? platform.getId() : null, mediaRoot);
        } else if (!isRunningInDocker()) {
            demoteUnmountedRemoteClients(platform);
            platform = computeNodeMapper.selectById(platform.getId());
        }

        if (platform != null) {
            markLocalMediaReady(platform, mediaRoot);
        }
    }

    /** 本机媒体根可写即挂载就绪；真 Export 另标 nfs_export_ready */
    private void markLocalMediaReady(ComputeNodeDO platform, Path mediaRoot) {
        Map<String, String> tags = platform.getTags() != null
                ? new java.util.HashMap<>(platform.getTags())
                : new java.util.HashMap<>();
        tags.put("storage_backend", "nfs");
        tags.put("media_mount_path", mediaRoot.toString());
        tags.put("ceph_mount_path", mediaRoot.toString());
        tags.put("nfs_export", mediaRoot.toString());
        if (!StringUtils.hasText(tags.get("nfs_cluster_role"))) {
            tags.put("nfs_cluster_role", "primary");
            tags.put("nfs_role", "server");
        }
        if (!StringUtils.hasText(tags.get("nfs_server_host")) && StringUtils.hasText(platform.getHost())) {
            tags.put("nfs_server_host", platform.getHost().trim());
            tags.put("ceph_mon_host", platform.getHost().trim());
        }
        boolean exportOk = isLocalNfsExportReady(mediaRoot);
        tags.put("nfs_mount_ready", "true");
        tags.put("ceph_mount_ready", "true");
        tags.put("nfs_export_ready", exportOk ? "true" : "false");
        tags.put("nfs_probe_ok", "true");
        tags.put("nfs_probe_at", java.time.Instant.now().toString());
        if (exportOk) {
            tags.put("nfs_probe_summary", "local-bootstrap: NFS export ready @ " + mediaRoot);
            tags.put("nfs_mount_source", "127.0.0.1:" + mediaRoot);
        } else {
            tags.put("nfs_probe_summary",
                    "local-bootstrap: media dir ready @ " + mediaRoot
                            + "（无真 Export：同机可用，远端无法 mount.nfs）");
            tags.put("nfs_mount_source", "local:" + mediaRoot);
        }
        platform.setTags(tags);
        computeNodeMapper.updateById(platform);
        log.info("[LocalNfsMediaBootstrap] 控制面本机媒体根已标记就绪: {} export={}", mediaRoot, exportOk);
    }

    /** exportfs 能看到媒体根且 2049 在听，才算真 Export */
    private static boolean isLocalNfsExportReady(Path mediaRoot) {
        try {
            Process p = new ProcessBuilder("bash", "-lc",
                    "exportfs -v 2>/dev/null | grep -F " + shellQuote(mediaRoot.toString())
                            + " >/dev/null && (ss -ltn 2>/dev/null | grep -q ':2049' || netstat -ltn 2>/dev/null | grep -q ':2049')")
                    .redirectErrorStream(true)
                    .start();
            boolean finished = p.waitFor(8, TimeUnit.SECONDS);
            return finished && p.exitValue() == 0;
        } catch (Exception ignored) {
            return false;
        }
    }

    private static String shellQuote(String value) {
        if (value == null) {
            return "''";
        }
        return "'" + value.replace("'", "'\\''") + "'";
    }

    /**
     * IDEA 本地：把从未挂载成功的远程 client 收回为 candidate，避免覆盖率被拖成 0%。
     */
    private void demoteUnmountedRemoteClients(ComputeNodeDO platform) {
        Long platformId = platform.getId();
        java.util.List<ComputeNodeDO> all = computeNodeMapper.selectList();
        if (all == null || all.isEmpty()) {
            return;
        }
        int demoted = 0;
        for (ComputeNodeDO node : all) {
            if (node == null || node.getId() == null || node.getId().equals(platformId)) {
                continue;
            }
            Map<String, String> tags = node.getTags();
            if (tags == null) {
                continue;
            }
            String nodeRole = tags.get("nfs_cluster_role");
            if (!"client".equalsIgnoreCase(nodeRole)) {
                continue;
            }
            boolean ready = "true".equalsIgnoreCase(String.valueOf(tags.get("nfs_mount_ready")))
                    || "true".equalsIgnoreCase(String.valueOf(tags.get("ceph_mount_ready")));
            if (ready) {
                continue;
            }
            String status = node.getStatus() != null ? node.getStatus().trim().toLowerCase(Locale.ROOT) : "";
            // 已在线且探测过：保留 client，提示去部署页挂载
            if ("online".equals(status) && StringUtils.hasText(tags.get("nfs_probe_at"))) {
                continue;
            }
            Map<String, String> next = new java.util.HashMap<>(tags);
            next.put("nfs_cluster_role", "candidate");
            next.put("nfs_role", "candidate");
            next.put("nfs_mount_ready", "false");
            next.put("ceph_mount_ready", "false");
            node.setTags(next);
            computeNodeMapper.updateById(node);
            demoted++;
        }
        if (demoted > 0) {
            log.info("[LocalNfsMediaBootstrap] 已将 {} 个未挂载远程客户端收回为 candidate（本地 IDEA 模式）", demoted);
        }
    }

    private Path resolveEnsureScript() {
        String envScript = System.getenv("EASYAIOT_ENSURE_NFS_SCRIPT");
        if (StringUtils.hasText(envScript)) {
            Path p = Paths.get(envScript.trim());
            if (Files.isRegularFile(p)) {
                return p;
            }
        }
        String envRoot = System.getenv("EASYAIOT_ROOT");
        if (StringUtils.hasText(envRoot)) {
            Path p = Paths.get(envRoot, ".scripts/media-cluster/nfs/ensure_nfs_media_stack.sh");
            if (Files.isRegularFile(p)) {
                return p;
            }
        }
        Path current = Paths.get(System.getProperty("user.dir", ".")).toAbsolutePath().normalize();
        for (int depth = 0; depth < 10 && current != null; depth++) {
            Path candidate = current.resolve(".scripts/media-cluster/nfs/ensure_nfs_media_stack.sh");
            if (Files.isRegularFile(candidate)) {
                return candidate;
            }
            // IDEA 常在 DEVICE/iot-node/iot-node-biz 下启动
            Path fromModule = current.resolve("../../.scripts/media-cluster/nfs/ensure_nfs_media_stack.sh")
                    .normalize();
            if (Files.isRegularFile(fromModule)) {
                return fromModule;
            }
            current = current.getParent();
        }
        return null;
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

    private static String firstNonBlank(String... values) {
        if (values == null) {
            return null;
        }
        for (String v : values) {
            if (StringUtils.hasText(v)) {
                return v.trim();
            }
        }
        return null;
    }

    private static String abbreviate(String text, int max) {
        if (text == null) {
            return "";
        }
        String t = text.trim();
        if (t.length() <= max) {
            return t;
        }
        return t.substring(0, max) + "...";
    }
}
