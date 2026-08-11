package com.basiclab.iot.sink.service.media;

import com.basiclab.iot.sink.config.NfsMediaProperties;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

@Component
@RequiredArgsConstructor
public class NfsMediaPathResolver {

    private final NfsMediaProperties props;

    public Path resolveMediaPath(String rawPath, String cwd) {
        if (!StringUtils.hasText(rawPath)) {
            return Paths.get("");
        }
        String trimmed = rawPath.trim();
        Path path = Paths.get(trimmed);
        if (!path.isAbsolute() && StringUtils.hasText(cwd)) {
            path = Paths.get(cwd.trim()).resolve(trimmed).normalize();
        } else {
            path = path.normalize();
        }

        if (Files.exists(path)) {
            return ensureUnderMount(path);
        }

        Path mapped = mapContainerToMount(path);
        if (mapped != null && Files.exists(mapped)) {
            return ensureUnderMount(mapped);
        }
        return ensureUnderMount(path);
    }

    private Path mapContainerToMount(Path path) {
        String mountRoot = normalizeRoot(props.getMountRoot());
        String containerRoot = normalizeRoot(props.getContainerDataRoot());
        String p = path.toString().replace('\\', '/');
        if (p.equals(containerRoot) || p.startsWith(containerRoot + "/")) {
            String rel = p.substring(containerRoot.length());
            if (rel.startsWith("/")) {
                rel = rel.substring(1);
            }
            return Paths.get(mountRoot, rel.split("/"));
        }
        if (p.equals("/data") || p.startsWith("/data/")) {
            String rel = p.equals("/data") ? "" : p.substring("/data/".length());
            return rel.isEmpty() ? Paths.get(mountRoot) : Paths.get(mountRoot, rel.split("/"));
        }
        return null;
    }

    private Path ensureUnderMount(Path path) {
        if (!props.isNfsOnly()) {
            return path;
        }
        String mountRoot = normalizeRoot(props.getMountRoot());
        String abs = path.toAbsolutePath().normalize().toString().replace('\\', '/');
        if (abs.equals(mountRoot) || abs.startsWith(mountRoot + "/")) {
            return path.toAbsolutePath().normalize();
        }
        throw new IllegalArgumentException("路径不在 NFS 媒体根下: " + abs + " (root=" + mountRoot + ")");
    }

    private static String normalizeRoot(String root) {
        if (!StringUtils.hasText(root)) {
            return "/mnt/easyaiot-media";
        }
        String r = root.trim().replace('\\', '/');
        while (r.endsWith("/") && r.length() > 1) {
            r = r.substring(0, r.length() - 1);
        }
        return r;
    }
}
