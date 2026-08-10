package com.basiclab.iot.video.service;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.dal.DeviceRepository;
import com.basiclab.iot.video.domain.DeviceRow;
import com.basiclab.iot.video.exception.VideoBusinessException;
import com.basiclab.iot.video.process.ViewForwardSupervisor;
import com.basiclab.iot.video.util.FfmpegCompat;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.net.URI;
import java.net.URISyntaxException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class ViewForwardService {

    private final DeviceRepository deviceRepository;
    private final ViewForwardSupervisor supervisor;
    private final VideoProperties videoProperties;

    public Map<String, Object> startStream(String deviceId) {
        DeviceRow device = deviceRepository.findById(deviceId)
                .orElseThrow(() -> new VideoBusinessException(400, "设备不存在: ID=" + deviceId));

        String source = device.getSource() != null ? device.getSource().trim() : "";
        if (source.toLowerCase(Locale.ROOT).startsWith("rtmp://")) {
            throw new VideoBusinessException(400, "摄像头源地址是 RTMP，不支持推送功能");
        }
        if (!isDeviceAvailableForStream(device)) {
            throw new VideoBusinessException(400, "设备处于离线状态，无法启动推送");
        }

        if (supervisor.isAlive(deviceId)) {
            Map<String, Object> data = new LinkedHashMap<>();
            data.put("rtmp_url", device.getRtmpStream());
            data.put("status", "running");
            return Map.of(
                    "message", "流媒体转发已在运行",
                    "data", data
            );
        }

        deviceRepository.updateEnableForward(deviceId, true);
        Path logDir = Path.of(videoProperties.getRuntime().getLogsDir(), "view-forward", deviceId);
        try {
            supervisor.start(deviceId, () -> buildFfmpegCommand(device), logDir);
        } catch (IOException e) {
            deviceRepository.updateEnableForward(deviceId, false);
            throw new VideoBusinessException(500, "启动失败: " + e.getMessage());
        }

        Map<String, Object> data = new HashMap<>();
        data.put("rtmp_url", device.getRtmpStream());
        return Map.of(
                "message", "流媒体转发已启动",
                "data", data
        );
    }

    public Map<String, Object> stopStream(String deviceId) {
        supervisor.stop(deviceId);
        deviceRepository.updateEnableForward(deviceId, false);
        return Map.of("message", "转码已停止", "data", Map.of());
    }

    public Map<String, Object> streamStatus(String deviceId) {
        DeviceRow device = deviceRepository.findById(deviceId)
                .orElseThrow(() -> new VideoBusinessException(400, "设备 " + deviceId + " 不存在"));

        String status = supervisor.isAlive(deviceId) ? "running" : "stopped";
        Integer pid = supervisor.isAlive(deviceId) ? supervisor.currentPid(deviceId) : null;
        String rtmpUrl = device.getRtmpStream();

        Map<String, Object> data = new LinkedHashMap<>();
        data.put("status", status);
        data.put("rtmp_url", rtmpUrl);
        data.put("enable_forward", device.getEnableForward());
        data.put("pid", pid);
        data.put("start_time", null);
        return data;
    }

    public boolean isDeviceAvailableForStream(DeviceRow device) {
        if (device == null) {
            return false;
        }
        String sourceLower = device.getSource() != null ? device.getSource().trim().toLowerCase(Locale.ROOT) : "";
        if (sourceLower.startsWith("rtmp://")) {
            return false;
        }
        if (isCustomCamera(device)) {
            return true;
        }
        if (Boolean.TRUE.equals(device.getChannelOnline())) {
            return true;
        }
        String conn = device.getConnectionStatus() != null
                ? device.getConnectionStatus().trim().toLowerCase(Locale.ROOT) : "";
        if ("online".equals(conn)) {
            return true;
        }
        if (Boolean.TRUE.equals(device.getEnableForward())
                && (isNonBlank(device.getHttpStream()) || isNonBlank(device.getRtmpStream()))) {
            return true;
        }
        String streamSource = isNonBlank(device.getSource()) ? device.getSource().trim()
                : (device.getRtspDirect() != null ? device.getRtspDirect().trim() : "");
        String lower = streamSource.toLowerCase(Locale.ROOT);
        return lower.startsWith("rtsp://") || lower.startsWith("http://") || lower.startsWith("https://")
                || lower.startsWith("gb28181://") || lower.startsWith("file://");
    }

    private boolean isCustomCamera(DeviceRow device) {
        if (device.getNvrId() != null || device.getNvrChannel() > 0) {
            return true;
        }
        String source = device.getSource() != null ? device.getSource().trim() : "";
        if (usesDirectStream(source)) {
            return true;
        }
        if (source.isEmpty()) {
            return false;
        }
        return device.getIp() == null || device.getIp().isBlank();
    }

    private boolean usesDirectStream(String source) {
        String lower = source.toLowerCase(Locale.ROOT);
        return lower.startsWith("rtsp://") || lower.startsWith("rtmp://") || lower.startsWith("gb28181://");
    }

    public List<String> buildForwardCommand(DeviceRow device) {
        return buildFfmpegCommand(device);
    }

    private List<String> buildFfmpegCommand(DeviceRow device) {
        int sourceFps = FfmpegCompat.envInt("VIEW_SOURCE_FPS", FfmpegCompat.envInt("SOURCE_FPS", 25));
        int gopSize = FfmpegCompat.envInt(
                "VIEW_FFMPEG_GOP_SIZE",
                FfmpegCompat.envInt("FFMPEG_GOP_SIZE", Math.max(1, sourceFps * 2))
        );
        String preset = FfmpegCompat.envStr("VIEW_FFMPEG_PRESET", FfmpegCompat.envStr("FFMPEG_PRESET", "veryfast"));
        String bitrate = FfmpegCompat.envStr(
                "VIEW_FFMPEG_VIDEO_BITRATE",
                FfmpegCompat.envStr("FFMPEG_VIDEO_BITRATE", "3500k")
        );
        String crf = FfmpegCompat.envStr("VIEW_FFMPEG_CRF", FfmpegCompat.envStr("FFMPEG_CRF", ""));
        String bufsizeEnv = FfmpegCompat.envStr(
                "VIEW_FFMPEG_VIDEO_BUFSIZE",
                FfmpegCompat.envStr("FFMPEG_VIDEO_BUFSIZE", "")
        );
        String bufsize = bufsizeEnv.isBlank() ? defaultBufsize(bitrate) : bufsizeEnv;

        int rtspOpenTimeoutUs = FfmpegCompat.envInt("FFMPEG_RTSP_OPEN_TIMEOUT_US", 10_000_000);
        int rtspIoTimeoutUs = FfmpegCompat.envInt("FFMPEG_RTSP_IO_TIMEOUT_US", 5_000_000);

        RtspSource parsed = stripRtspTransportQuery(device.getSource() != null ? device.getSource() : "");
        String inputUrl = parsed.url;
        String rtspTransport = parsed.transport != null
                ? parsed.transport
                : FfmpegCompat.envStr(
                        "FFMPEG_RTSP_TRANSPORT",
                        FfmpegCompat.envStr("VIEW_FFMPEG_RTSP_TRANSPORT", "udp")
                ).toLowerCase(Locale.ROOT);
        if (!"tcp".equals(rtspTransport) && !"udp".equals(rtspTransport)) {
            rtspTransport = "udp";
        }

        boolean isRtspInput = inputUrl.trim().toLowerCase(Locale.ROOT).startsWith("rtsp://");
        String videoCodec = FfmpegCompat.resolveViewH264Codec();

        List<String> cmd = new ArrayList<>();
        cmd.add(FfmpegCompat.resolveFfmpegBinary());
        cmd.add("-hide_banner");
        cmd.add("-loglevel");
        cmd.add("warning");

        if (isRtspInput) {
            cmd.add("-rtsp_transport");
            cmd.add(rtspTransport);
            if ("tcp".equals(rtspTransport)) {
                cmd.add("-rtsp_flags");
                cmd.add("prefer_tcp");
            }
            cmd.addAll(FfmpegCompat.ffmpegRtspTimeoutArgs(rtspOpenTimeoutUs, rtspIoTimeoutUs));
        }

        cmd.add("-fflags");
        cmd.add("nobuffer+discardcorrupt+genpts");
        cmd.add("-err_detect");
        cmd.add("ignore_err");
        cmd.add("-flags");
        cmd.add("low_delay");
        if (isFileInput(inputUrl)) {
            cmd.add("-stream_loop");
            cmd.add("-1");
        }
        cmd.add("-i");
        cmd.add(normalizeInputUrl(inputUrl));
        cmd.add("-an");

        if ("copy".equals(videoCodec)) {
            cmd.add("-c:v");
            cmd.add("copy");
        } else if ("h264_nvenc".equals(videoCodec)) {
            String nvencPreset = mapNvencPreset(preset);
            cmd.add("-c:v");
            cmd.add("h264_nvenc");
            cmd.add("-preset");
            cmd.add(nvencPreset);
            cmd.add("-tune");
            cmd.add("ll");
            cmd.add("-rc");
            cmd.add("cbr");
            cmd.add("-b:v");
            cmd.add(bitrate);
            cmd.add("-maxrate");
            cmd.add(bitrate);
            cmd.add("-bufsize");
            cmd.add(bufsize);
            cmd.add("-pix_fmt");
            cmd.add("yuv420p");
            cmd.add("-g");
            cmd.add(String.valueOf(Math.max(1, gopSize)));
            cmd.add("-bf");
            cmd.add("0");
        } else {
            cmd.add("-c:v");
            cmd.add(videoCodec);
            cmd.add("-preset");
            cmd.add(preset);
            cmd.add("-tune");
            cmd.add("zerolatency");
            if (!crf.isBlank()) {
                cmd.add("-crf");
                cmd.add(crf);
            } else {
                cmd.add("-b:v");
                cmd.add(bitrate);
                cmd.add("-maxrate");
                cmd.add(bitrate);
                cmd.add("-bufsize");
                cmd.add(bufsize);
            }
            cmd.add("-pix_fmt");
            cmd.add("yuv420p");
            cmd.add("-profile:v");
            cmd.add("main");
            cmd.add("-g");
            cmd.add(String.valueOf(Math.max(1, gopSize)));
            cmd.add("-keyint_min");
            cmd.add(String.valueOf(Math.max(1, sourceFps)));
            cmd.add("-sc_threshold");
            cmd.add("0");
            cmd.add("-bf");
            cmd.add("0");
        }

        cmd.add("-f");
        cmd.add("flv");
        cmd.add("-flvflags");
        cmd.add("no_duration_filesize");
        cmd.add(device.getRtmpStream());
        return cmd;
    }

    private static String mapNvencPreset(String preset) {
        Map<String, String> mapping = Map.of(
                "ultrafast", "p1",
                "superfast", "p2",
                "veryfast", "p4",
                "faster", "p4",
                "fast", "p5",
                "medium", "p5",
                "slow", "p6",
                "slower", "p7",
                "veryslow", "p7"
        );
        return mapping.getOrDefault(preset.toLowerCase(Locale.ROOT), "p4");
    }

    private static String defaultBufsize(String bitrate) {
        Integer k = parseBitrateToK(bitrate);
        return (Math.max(1, (k != null ? k : 3500) * 2)) + "k";
    }

    private static Integer parseBitrateToK(String value) {
        try {
            String v = value.trim().toLowerCase(Locale.ROOT);
            if (v.isEmpty()) {
                return null;
            }
            if (v.endsWith("k")) {
                return (int) Double.parseDouble(v.substring(0, v.length() - 1));
            }
            if (v.endsWith("m")) {
                return (int) (Double.parseDouble(v.substring(0, v.length() - 1)) * 1000);
            }
            if (v.chars().allMatch(Character::isDigit)) {
                return Math.max(1, Integer.parseInt(v) / 1000);
            }
        } catch (Exception ignored) {
            return null;
        }
        return null;
    }

    private static RtspSource stripRtspTransportQuery(String sourceUrl) {
        try {
            URI uri = new URI(sourceUrl);
            if (!"rtsp".equalsIgnoreCase(uri.getScheme()) || uri.getQuery() == null || uri.getQuery().isBlank()) {
                return new RtspSource(sourceUrl, null);
            }
            String[] pairs = uri.getQuery().split("&");
            String transport = null;
            List<String> kept = new ArrayList<>();
            for (String pair : pairs) {
                String[] kv = pair.split("=", 2);
                String key = kv[0];
                if ("easyaiot_rtsp_transport".equals(key) || "rtsp_transport".equals(key)
                        || "iot_rtsp_transport".equals(key)) {
                    if (kv.length > 1) {
                        transport = kv[1].trim().toLowerCase(Locale.ROOT);
                    }
                } else {
                    kept.add(pair);
                }
            }
            if (transport == null) {
                return new RtspSource(sourceUrl, null);
            }
            String newQuery = String.join("&", kept);
            URI stripped = new URI(
                    uri.getScheme(),
                    uri.getAuthority(),
                    uri.getPath(),
                    newQuery.isEmpty() ? null : newQuery,
                    uri.getFragment()
            );
            return new RtspSource(stripped.toString(), transport);
        } catch (URISyntaxException e) {
            return new RtspSource(sourceUrl, null);
        }
    }

    private static boolean isNonBlank(String value) {
        return value != null && !value.isBlank();
    }

    private static boolean isFileInput(String inputUrl) {
        String lower = normalizeInputUrl(inputUrl).toLowerCase(Locale.ROOT);
        if (lower.startsWith("file://")) {
            return true;
        }
        if (lower.startsWith("rtsp://") || lower.startsWith("http://") || lower.startsWith("https://")
                || lower.startsWith("gb28181://") || lower.startsWith("rtmp://")) {
            return false;
        }
        return lower.contains(".mp4") || lower.contains(".mkv") || lower.contains(".mov");
    }

    /** FFmpeg on Windows does not open {@code file://} URIs; strip to filesystem path. */
    private static String normalizeInputUrl(String inputUrl) {
        if (inputUrl == null) {
            return "";
        }
        String trimmed = inputUrl.trim();
        if (trimmed.toLowerCase(Locale.ROOT).startsWith("file://")) {
            String path = trimmed.substring("file://".length());
            if (path.startsWith("/") && path.length() > 2 && path.charAt(2) == ':') {
                return path.substring(1);
            }
            return path;
        }
        return trimmed;
    }

    private record RtspSource(String url, String transport) {}
}
