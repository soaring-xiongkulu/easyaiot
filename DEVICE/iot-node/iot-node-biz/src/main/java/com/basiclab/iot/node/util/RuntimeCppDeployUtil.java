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
                + "ldd '" + REMOTE_RUNTIME_BIN + "' 2>/dev/null | head -5 || true; "
                + "echo RUNTIME_OK; "
                + "else echo RUNTIME_MISSING; fi";
    }

    public static String remoteLdLibraryPath() {
        return REMOTE_RUNTIME_LIB
                + ":/usr/local/cuda/lib64:/usr/local/cuda/lib"
                + ":/usr/lib/x86_64-linux-gnu:/usr/lib/aarch64-linux-gnu";
    }
}
