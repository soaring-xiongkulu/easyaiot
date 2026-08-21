package com.basiclab.iot.node.util;

import java.util.Locale;

/**
 * FFmpeg 静态二进制离线分发（推流/算法节点，默认无外网）。
 */
public final class FfmpegStaticDeployUtil {

    public static final String REMOTE_FFMPEG_ROOT = "/opt/easyaiot/tools/ffmpeg";
    public static final String REMOTE_FFMPEG_BIN = REMOTE_FFMPEG_ROOT + "/bin/ffmpeg";
    public static final String REMOTE_FFPROBE_BIN = REMOTE_FFMPEG_ROOT + "/bin/ffprobe";
    public static final String REMOTE_CACHE_SUBDIR = "cache";

    public static final String EXPORT_FFMPEG_SCRIPT = "export_ffmpeg_static.sh";
    public static final String INSTALL_FFMPEG_SCRIPT = "install_ffmpeg_static.sh";

    public static final String TAR_LINUX64 = "ffmpeg-master-latest-linux64-gpl.tar.xz";
    public static final String TAR_LINUX_ARM64 = "ffmpeg-master-latest-linuxarm64-gpl.tar.xz";

    private FfmpegStaticDeployUtil() {
    }

    public static String localCacheDir(String videoSourceRoot, String archKey) {
        return videoSourceRoot + "/.bundle-ffmpeg/" + archKey;
    }

    public static String tarballNameForArch(String unameMachine) {
        String m = unameMachine == null ? "" : unameMachine.trim().toLowerCase(Locale.ROOT);
        if (m.contains("aarch64") || m.contains("arm64")) {
            return TAR_LINUX_ARM64;
        }
        return TAR_LINUX64;
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
        return "if [ -x '" + REMOTE_FFMPEG_BIN + "' ]; then "
                + "'" + REMOTE_FFMPEG_BIN + "' -version 2>/dev/null | head -1; echo FFMPEG_OK; "
                + "else echo FFMPEG_MISSING; fi";
    }
}
