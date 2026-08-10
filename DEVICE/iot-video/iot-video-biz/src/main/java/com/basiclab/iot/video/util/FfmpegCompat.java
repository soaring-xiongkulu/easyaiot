package com.basiclab.iot.video.util;

import java.io.File;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.concurrent.TimeUnit;

/**
 * FFmpeg binary resolution and encoder / RTSP timeout compatibility — aligned with
 * {@code VIDEO/app/utils/ffmpeg_compat.py}.
 */
public final class FfmpegCompat {

    private static volatile String resolvedBinary;
    private static volatile String configuredBinary;
    private static volatile Set<String> encoderNames;
    private static volatile String rtspOpenTimeoutFlag;
    private static volatile Boolean supportsRwTimeout;
    private static volatile String rtspDemuxerHelp;

    private FfmpegCompat() {}

    public static void setConfiguredBinary(String path) {
        configuredBinary = path;
        resolvedBinary = null;
    }

    public static String resolveFfmpegBinary() {
        if (resolvedBinary != null) {
            return resolvedBinary;
        }
        String explicit = (System.getenv("FFMPEG_PATH") != null ? System.getenv("FFMPEG_PATH") : "").trim()
                .replace("\"", "");
        if (explicit.isBlank() && configuredBinary != null && !configuredBinary.isBlank()) {
            explicit = configuredBinary.trim();
        }
        if (isRunnableBinary(explicit)) {
            resolvedBinary = explicit;
            return resolvedBinary;
        }
        resolvedBinary = "ffmpeg";
        return resolvedBinary;
    }

    private static boolean isRunnableBinary(String path) {
        if (path == null || path.isBlank()) {
            return false;
        }
        File file = new File(path);
        if (!file.isFile()) {
            return false;
        }
        String lower = path.toLowerCase(Locale.ROOT);
        if (lower.endsWith(".exe") || lower.endsWith(".cmd") || lower.endsWith(".bat")) {
            return true;
        }
        return file.canExecute();
    }

    public static Set<String> ffmpegEncoderNames() {
        if (encoderNames != null) {
            return encoderNames;
        }
        Set<String> names = new HashSet<>();
        try {
            Process process = new ProcessBuilder(
                    resolveFfmpegBinary(), "-hide_banner", "-encoders"
            ).redirectErrorStream(true).start();
            boolean finished = process.waitFor(8, TimeUnit.SECONDS);
            if (!finished) {
                process.destroyForcibly();
            }
            String text = new String(process.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
            for (String line : text.split("\n")) {
                String trimmed = line.strip();
                String[] parts = trimmed.split("\\s+");
                if (parts.length >= 2 && parts[0].startsWith("V")) {
                    names.add(parts[1]);
                }
            }
        } catch (Exception ignored) {
            names = new HashSet<>();
        }
        encoderNames = names;
        return encoderNames;
    }

    public static String resolveViewH264Codec() {
        String forced = firstNonBlank(
                System.getenv("VIEW_FFMPEG_CODEC"),
                System.getenv("FFMPEG_VIDEO_CODEC")
        ).toLowerCase(Locale.ROOT);
        if (forced.equals("libx264") || forced.equals("h264_nvenc") || forced.equals("copy")
                || forced.equals("h264_qsv") || forced.equals("h264_amf")) {
            return forced;
        }
        Set<String> encoders = ffmpegEncoderNames();
        if (encoders.contains("libx264")) {
            return "libx264";
        }
        if (encoders.contains("h264_nvenc")) {
            return "h264_nvenc";
        }
        if (encoders.contains("h264_qsv")) {
            return "h264_qsv";
        }
        if (encoders.contains("h264_amf")) {
            return "h264_amf";
        }
        return "copy";
    }

    public static List<String> ffmpegRtspTimeoutArgs(int openUs, int ioUs) {
        String openFlag = ffmpegRtspOpenTimeoutFlag();
        if (ffmpegSupportsRwTimeout()) {
            return List.of(openFlag, String.valueOf(openUs), "-rw_timeout", String.valueOf(ioUs));
        }
        return List.of(openFlag, String.valueOf(Math.max(openUs, ioUs)));
    }

    /** Non-RTSP input timeout args — mirrors {@code camera.py} FFmpegDaemon lines 303–306. */
    public static List<String> ffmpegNonRtspTimeoutArgs(int ioUs) {
        if (ffmpegSupportsRwTimeout()) {
            return List.of("-rw_timeout", String.valueOf(ioUs));
        }
        if ("-timeout".equals(ffmpegRtspOpenTimeoutFlag())) {
            return List.of("-timeout", String.valueOf(ioUs));
        }
        return Collections.emptyList();
    }

    public static String ffmpegRtspOpenTimeoutFlag() {
        if (rtspOpenTimeoutFlag != null) {
            return rtspOpenTimeoutFlag;
        }
        if (rtspDemuxerHasOption("stimeout")) {
            rtspOpenTimeoutFlag = "-stimeout";
        } else {
            rtspOpenTimeoutFlag = "-timeout";
        }
        return rtspOpenTimeoutFlag;
    }

    public static boolean ffmpegSupportsRwTimeout() {
        if (supportsRwTimeout != null) {
            return supportsRwTimeout;
        }
        if (rtspDemuxerHasOption("rw_timeout")) {
            supportsRwTimeout = true;
            return true;
        }
        try {
            Process process = new ProcessBuilder(
                    resolveFfmpegBinary(),
                    "-hide_banner",
                    "-rw_timeout", "1",
                    "-f", "lavfi",
                    "-i", "nullsrc=s=1x1:d=0.01",
                    "-frames:v", "1",
                    "-f", "null",
                    "-"
            ).redirectErrorStream(true).start();
            boolean finished = process.waitFor(8, TimeUnit.SECONDS);
            if (!finished) {
                process.destroyForcibly();
            }
            String err = new String(process.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
            supportsRwTimeout = !ffmpegOptionMissing(err, "rw_timeout");
        } catch (Exception e) {
            supportsRwTimeout = false;
        }
        return supportsRwTimeout;
    }

    private static boolean rtspDemuxerHasOption(String option) {
        String name = option.startsWith("-") ? option.substring(1) : option;
        return rtspDemuxerHelpText().contains("-" + name);
    }

    private static String rtspDemuxerHelpText() {
        if (rtspDemuxerHelp != null) {
            return rtspDemuxerHelp;
        }
        try {
            Process process = new ProcessBuilder(
                    resolveFfmpegBinary(), "-hide_banner", "-h", "demuxer=rtsp"
            ).redirectErrorStream(true).start();
            boolean finished = process.waitFor(5, TimeUnit.SECONDS);
            if (!finished) {
                process.destroyForcibly();
            }
            rtspDemuxerHelp = new String(process.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
        } catch (Exception e) {
            rtspDemuxerHelp = "";
        }
        return rtspDemuxerHelp;
    }

    private static boolean ffmpegOptionMissing(String stderr, String option) {
        if (stderr == null) {
            return false;
        }
        if (stderr.contains("Unrecognized option") || stderr.contains("Option not found")) {
            return true;
        }
        if (option != null && !option.isBlank()) {
            return stderr.contains("Option " + option + " not found");
        }
        return false;
    }

    private static String firstNonBlank(String... values) {
        for (String value : values) {
            if (value != null && !value.isBlank()) {
                return value.trim();
            }
        }
        return "";
    }

    public static int envInt(String name, int defaultValue) {
        String raw = System.getenv(name);
        if (raw == null || raw.isBlank()) {
            return defaultValue;
        }
        try {
            return Integer.parseInt(raw.trim());
        } catch (NumberFormatException e) {
            return defaultValue;
        }
    }

    public static String envStr(String name, String defaultValue) {
        String raw = System.getenv(name);
        if (raw == null || raw.isBlank()) {
            return defaultValue;
        }
        return raw.trim();
    }
}
