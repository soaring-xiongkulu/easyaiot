package com.basiclab.iot.node.util;

import java.util.Locale;

/**
 * RUNTIME（C++ 高性能算法执行器）离线分发工具常量。
 * 控制面导出 tarball → SSH 同步 → 节点 install_runtime_cpp.sh。
 */
public final class RuntimeCppDeployUtil {

    public static final String REMOTE_RUNTIME_ROOT = "/opt/easyaiot/RUNTIME";
    public static final String REMOTE_RUNTIME_BIN = REMOTE_RUNTIME_ROOT + "/bin/RUNTIME";
    public static final String REMOTE_RUNTIME_LIB = REMOTE_RUNTIME_ROOT + "/lib";
    public static final String REMOTE_RUNTIME_CONFIG = REMOTE_RUNTIME_ROOT + "/config";
    public static final String REMOTE_RUNTIME_VERSION = REMOTE_RUNTIME_ROOT + "/VERSION";
    public static final String REMOTE_CACHE_SUBDIR = "cache";

    public static final String EXPORT_SCRIPT = "export_runtime_cpp.sh";
    public static final String INSTALL_SCRIPT = "install_runtime_cpp.sh";

    private RuntimeCppDeployUtil() {
    }

    public static String localCacheDir(String runtimeSourceRoot, String archKey) {
        return runtimeSourceRoot + "/.bundle-runtime/" + archKey;
    }

    public static String tarballNameForArch(String archKey) {
        return "easyaiot-runtime-" + archKey + ".tar.gz";
    }

    public static String archKeyForUname(String unameMachine) {
        String m = unameMachine == null ? "" : unameMachine.trim().toLowerCase(Locale.ROOT);
        if (m.contains("aarch64") || m.contains("arm64")) {
            return "arm64";
        }
        return "x86_64";
    }

    public static String exportArchEnv(String archKey) {
        return "arm64".equals(archKey) ? "arm64" : "x86_64";
    }

    public static String verifyCommand() {
        return "if [ -x '" + REMOTE_RUNTIME_BIN + "' ]; then "
                + "echo BIN_OK; "
                + "if [ -f '" + REMOTE_RUNTIME_VERSION + "' ]; then "
                + "echo '---VERSION_BEGIN---'; "
                + "cat '" + REMOTE_RUNTIME_VERSION + "'; "
                + "echo '---VERSION_END---'; "
                + "else echo VERSION_MISSING; fi; "
                + "ldd '" + REMOTE_RUNTIME_BIN + "' 2>/dev/null | head -5 || true; "
                + "echo RUNTIME_OK; "
                + "else echo RUNTIME_MISSING; fi";
    }

    public static String remoteLdLibraryPath() {
        return REMOTE_RUNTIME_LIB
                + ":/usr/local/cuda/lib64:/usr/local/cuda/lib"
                + ":/usr/lib/x86_64-linux-gnu:/usr/lib/aarch64-linux-gnu";
    }

    /** 从 VERSION 文本解析 key=value。 */
    public static java.util.Map<String, String> parseVersionText(String text) {
        java.util.Map<String, String> map = new java.util.LinkedHashMap<>();
        if (text == null || text.isBlank()) {
            return map;
        }
        for (String line : text.split("\\R")) {
            String trimmed = line.trim();
            if (trimmed.isEmpty() || trimmed.startsWith("#")) {
                continue;
            }
            int idx = trimmed.indexOf('=');
            if (idx <= 0) {
                continue;
            }
            String key = trimmed.substring(0, idx).trim();
            String value = trimmed.substring(idx + 1).trim();
            if (!key.isEmpty()) {
                map.put(key, value);
            }
        }
        return map;
    }

    public static String extractVersionBlock(String combinedOutput) {
        if (combinedOutput == null) {
            return "";
        }
        int begin = combinedOutput.indexOf("---VERSION_BEGIN---");
        int end = combinedOutput.indexOf("---VERSION_END---");
        if (begin >= 0 && end > begin) {
            return combinedOutput.substring(begin + "---VERSION_BEGIN---".length(), end).trim();
        }
        return "";
    }
}
