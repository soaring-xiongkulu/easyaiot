package com.basiclab.iot.video.service.ops;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Locale;
import java.util.concurrent.TimeUnit;

/**
 * SRS container data-mount sanity check on startup (Python {@code maybe_fix_srs_on_startup}).
 */
@Slf4j
@Service
public class SrsStartupGuardService {

    public boolean checkOnStartup() {
        if (isDisabled()) {
            log.info("SRS 启动自检跳过: SRS_AUTO_FIX_ON_START=off");
            return false;
        }
        if (runningInsideContainer()) {
            log.info("SRS 启动自检跳过: 容器内运行");
            return false;
        }
        String expected = resolveExpectedDataDir();
        String actual = resolveContainerDataMount("srs-server");
        if (actual == null) {
            log.info("SRS 启动自检: 容器未运行或无法解析挂载 (expected={})", expected);
            return false;
        }
        boolean mismatch = !Path.of(expected).normalize().equals(Path.of(actual).normalize());
        if (mismatch) {
            log.warn("SRS 数据目录挂载不一致 expected={} actual={} (未自动执行 fix_srs.sh)", expected, actual);
            return false;
        }
        log.info("SRS 启动自检通过: data_mount={}", actual);
        return true;
    }

    private static boolean isDisabled() {
        String raw = System.getenv("SRS_AUTO_FIX_ON_START");
        if (raw == null) {
            return false;
        }
        return raw.strip().toLowerCase(Locale.ROOT).matches("0|false|no|off");
    }

    private static boolean runningInsideContainer() {
        return Files.exists(Path.of("/.dockerenv"));
    }

    private static String resolveExpectedDataDir() {
        String explicit = System.getenv("EASYAIOT_HOST_DATA_DIR");
        if (explicit != null && !explicit.isBlank()) {
            return Path.of(explicit.strip()).normalize().toString();
        }
        String home = System.getProperty("user.home", "");
        return Path.of(home, "easyaiot", "data").normalize().toString();
    }

    private static String resolveContainerDataMount(String containerName) {
        try {
            Process process = new ProcessBuilder(
                    "docker", "inspect", containerName,
                    "--format", "{{range .Mounts}}{{if eq .Destination \"/data\"}}{{.Source}}{{end}}{{end}}"
            ).redirectErrorStream(true).start();
            boolean finished = process.waitFor(15, TimeUnit.SECONDS);
            if (!finished || process.exitValue() != 0) {
                return null;
            }
            String source = new String(process.getInputStream().readAllBytes()).strip();
            return source.isEmpty() ? null : new File(source).getPath();
        } catch (Exception ex) {
            return null;
        }
    }
}
