package com.basiclab.iot.video.service.camera;

import com.basiclab.iot.video.dal.DeviceRepository;
import com.basiclab.iot.video.domain.DeviceRow;
import com.basiclab.iot.video.exception.VideoBusinessException;
import com.basiclab.iot.video.service.camera.hardware.CameraScreenshotService;
import com.basiclab.iot.video.service.camera.hardware.FfmpegFrameCapture;
import com.basiclab.iot.video.service.camera.hardware.HikScanService;
import com.basiclab.iot.video.service.camera.hardware.OnvifSoapClient;
import com.basiclab.iot.video.service.camera.hardware.OnvifWsDiscovery;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicLong;

@Slf4j
@Service
@RequiredArgsConstructor
public class CameraHardwareService {

    private static final int ONVIF_TIMEOUT_SECONDS = 8;
    private static final List<String> DEFAULT_ONVIF_USERNAMES = List.of("admin", "root", "Administrator");

    private final DeviceRepository deviceRepository;
    private final OnvifSoapClient onvifSoapClient = new OnvifSoapClient();
    private final OnvifWsDiscovery onvifWsDiscovery = new OnvifWsDiscovery();
    private final HikScanService hikScanService;
    private final CameraScreenshotService cameraScreenshotService;
    private final ExecutorService captureExecutor = Executors.newCachedThreadPool();
    private final AtomicLong taskIdSeq = new AtomicLong(1);

    private final Map<String, CaptureTaskState> rtspTasks = new ConcurrentHashMap<>();
    private final Map<String, CaptureTaskState> onvifTasks = new ConcurrentHashMap<>();
    private final Map<String, OnvifSoapClient.Session> onvifSessions = new ConcurrentHashMap<>();

    public List<Map<String, Object>> discoverDevices() {
        return onvifWsDiscovery.discover(2000);
    }

    public void refreshDevices() {
        List<Map<String, Object>> discovered = discoverDevices();
        for (Map<String, Object> item : discovered) {
            String mac = item.get("mac") != null ? String.valueOf(item.get("mac")).trim() : "";
            String ip = item.get("ip") != null ? String.valueOf(item.get("ip")).trim() : "";
            if (mac.isEmpty() || ip.isEmpty()) {
                continue;
            }
            deviceRepository.findByMac(mac).ifPresent(device -> {
                if (device.getIp() != null && !ip.equals(device.getIp())) {
                    deviceRepository.updateFields(device.getId(), Map.of("ip", ip));
                    log.info("设备 {} IP 地址已从 {} 更新为 {}", device.getId(), device.getIp(), ip);
                }
            });
        }
    }

    @SuppressWarnings("unchecked")
    public List<Map<String, Object>> scanSegment(Map<String, Object> data) {
        String targets = str(data.get("targets"));
        if (targets.isEmpty()) {
            throw new VideoBusinessException(400, "请填写扫描目标（网段 / IP / 范围）");
        }
        String ports = strOr(data.get("ports"), "80,443,8000,8443");
        int concurrency = intOr(data.get("concurrency"), 200);
        double timeout = doubleOr(data.get("timeout"), 3.0);
        if (timeout < 0.5 || timeout > 30) {
            throw new VideoBusinessException(400, "单点超时需在 0.5–30 秒之间");
        }
        if (concurrency < 1 || concurrency > 2000) {
            throw new VideoBusinessException(400, "并发数需在 1–2000 之间");
        }
        List<Map<String, Object>> credentials = data.get("credentials") instanceof List<?> list
                ? (List<Map<String, Object>>) list
                : null;
        try {
            return hikScanService.scanSegment(
                    targets,
                    ports,
                    strOrNull(data.get("username")),
                    data.get("password") != null ? String.valueOf(data.get("password")) : null,
                    credentials,
                    concurrency,
                    timeout,
                    boolOr(data.get("only_hits"), true),
                    boolOr(data.get("nvr_only"), false),
                    boolOr(data.get("exclude_nvr"), false)
            );
        } catch (IllegalArgumentException ex) {
            throw new VideoBusinessException(400, ex.getMessage());
        } catch (Exception ex) {
            throw new VideoBusinessException(500, "网段扫描失败: " + ex.getMessage());
        }
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> scanNvrChannels(Map<String, Object> data) {
        String ip = str(data.get("ip"));
        if (ip.isEmpty()) {
            throw new VideoBusinessException(400, "NVR IP 不能为空");
        }
        int port = intOr(data.get("port"), 80);
        List<Map<String, Object>> credentials = data.get("credentials") instanceof List<?> list
                ? (List<Map<String, Object>>) list
                : null;
        String username = strOrNull(data.get("username"));
        if ((credentials == null || credentials.isEmpty()) && (username == null || username.isBlank())) {
            throw new VideoBusinessException(400, "请至少填写一组用户名和密码");
        }
        try {
            return hikScanService.enumerateNvrChannels(
                    ip,
                    port,
                    username,
                    data.get("password") != null ? String.valueOf(data.get("password")) : null,
                    credentials,
                    doubleOr(data.get("timeout"), 5.0),
                    strOrNull(data.get("vendor")),
                    boolOr(data.get("probe_cameras"), false),
                    boolOr(data.get("only_mounted"), true)
            );
        } catch (IllegalArgumentException ex) {
            throw new VideoBusinessException(400, ex.getMessage());
        } catch (Exception ex) {
            throw new VideoBusinessException(500, "NVR 通道枚举失败: " + ex.getMessage());
        }
    }

    public Map<String, Object> ptz(String deviceId, Map<String, Object> data) {
        if (data == null || data.isEmpty()) {
            throw new VideoBusinessException(400, "No data provided");
        }
        DeviceCredentials creds = requireOnvifCredentials(deviceId);
        double x = number(data.get("x"));
        double y = number(data.get("y"));
        double z = number(data.get("z"));
        try {
            OnvifSoapClient.Session session = onvifSession(creds);
            onvifSoapClient.continuousMove(session, x, y, z, creds.username(), creds.password(), ONVIF_TIMEOUT_SECONDS);
            return Map.of("success", true, "message", "PTZ command executed");
        } catch (OnvifSoapClient.OnvifException ex) {
            throw new VideoBusinessException(500, "Internal server error");
        }
    }

    public Map<String, Object> startRtspCapture(String deviceId, Map<String, Object> data) {
        DeviceRow device = requireDevice(deviceId);
        if (rtspTasks.containsKey(deviceId) && rtspTasks.get(deviceId).running) {
            throw new VideoBusinessException(400, "该设备的截图任务已在运行");
        }
        String rtspUrl = data != null && data.get("rtsp_url") != null
                ? String.valueOf(data.get("rtsp_url")).trim()
                : device.getSource();
        if (rtspUrl == null || rtspUrl.isBlank()) {
            throw new VideoBusinessException(400, "RTSP地址不能为空");
        }
        int interval = intOr(data != null ? data.get("interval") : null, 5);
        int maxCount = intOr(data != null ? data.get("max_count") : null, 100);
        CaptureTaskState state = new CaptureTaskState(true);
        state.taskId = taskIdSeq.getAndIncrement();
        rtspTasks.put(deviceId, state);
        captureExecutor.submit(() -> runRtspCaptureTask(deviceId, rtspUrl, interval, maxCount, state));
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("task_id", state.taskId);
        return result;
    }

    public void stopRtspCapture(String deviceId) {
        CaptureTaskState state = rtspTasks.get(deviceId);
        if (state == null) {
            throw new VideoBusinessException(400, "未找到运行的RTSP截图任务");
        }
        state.running = false;
    }

    public String rtspStatus(String deviceId) {
        CaptureTaskState state = rtspTasks.get(deviceId);
        return state != null && state.running ? "running" : "stopped";
    }

    public Map<String, Object> startOnvifCapture(String deviceId, Map<String, Object> data) {
        DeviceCredentials creds = requireOnvifCredentials(deviceId);
        if (onvifTasks.containsKey(deviceId) && onvifTasks.get(deviceId).running) {
            throw new VideoBusinessException(400, "该设备的ONVIF截图任务已在运行");
        }
        int interval = intOr(data != null ? data.get("interval") : null, 5);
        int maxCount = intOr(data != null ? data.get("max_count") : null, 100);
        try {
            OnvifSoapClient.Session session = onvifSession(creds);
            String snapshotUri = onvifSoapClient.getSnapshotUri(session, creds.username(), creds.password(), ONVIF_TIMEOUT_SECONDS);
            if (snapshotUri == null || snapshotUri.isBlank()) {
                throw new VideoBusinessException(400, "无法获取ONVIF快照URI");
            }
            snapshotUri = injectHttpAuth(snapshotUri, creds.username(), creds.password());
            CaptureTaskState state = new CaptureTaskState(true);
            state.taskId = taskIdSeq.getAndIncrement();
            onvifTasks.put(deviceId, state);
            String finalSnapshotUri = snapshotUri;
            captureExecutor.submit(() -> runOnvifCaptureTask(deviceId, finalSnapshotUri, creds, interval, maxCount, state));
            Map<String, Object> result = new LinkedHashMap<>();
            result.put("task_id", state.taskId);
            return result;
        } catch (OnvifSoapClient.OnvifException ex) {
            throw new VideoBusinessException(500, "启动ONVIF截图失败: " + ex.getMessage());
        }
    }

    public void stopOnvifCapture(String deviceId) {
        CaptureTaskState state = onvifTasks.get(deviceId);
        if (state == null) {
            throw new VideoBusinessException(400, "未找到运行的ONVIF截图任务");
        }
        state.running = false;
    }

    public String onvifStatus(String deviceId) {
        CaptureTaskState state = onvifTasks.get(deviceId);
        return state != null && state.running ? "running" : "stopped";
    }

    public List<Map<String, Object>> listOnvifPresets(String deviceId) {
        DeviceCredentials creds = requireOnvifCredentials(deviceId);
        try {
            OnvifSoapClient.Session session = onvifSession(creds);
            List<Map<String, String>> presets = onvifSoapClient.listPresets(session, creds.username(), creds.password(), ONVIF_TIMEOUT_SECONDS);
            return presets.stream().map(p -> {
                Map<String, Object> row = new LinkedHashMap<>();
                row.put("token", p.get("token"));
                row.put("name", p.get("name"));
                return row;
            }).toList();
        } catch (OnvifSoapClient.OnvifException ex) {
            throw new VideoBusinessException(500, ex.getMessage());
        }
    }

    public Map<String, Object> setOnvifPreset(String deviceId, String name, String presetToken) {
        DeviceCredentials creds = requireOnvifCredentials(deviceId);
        try {
            OnvifSoapClient.Session session = onvifSession(creds);
            String token = onvifSoapClient.setPreset(session, name, presetToken, creds.username(), creds.password(), ONVIF_TIMEOUT_SECONDS);
            if (token == null || token.isBlank()) {
                throw new VideoBusinessException(500, "保存预置点失败，设备可能不支持该操作");
            }
            Map<String, Object> data = new LinkedHashMap<>();
            data.put("token", token);
            data.put("name", name);
            return data;
        } catch (OnvifSoapClient.OnvifException ex) {
            throw new VideoBusinessException(500, "保存预置点失败: " + ex.getMessage());
        }
    }

    public void callOnvifPreset(String deviceId, String presetToken) {
        DeviceCredentials creds = requireOnvifCredentials(deviceId);
        try {
            OnvifSoapClient.Session session = onvifSession(creds);
            onvifSoapClient.gotoPreset(session, presetToken, creds.username(), creds.password(), ONVIF_TIMEOUT_SECONDS);
        } catch (OnvifSoapClient.OnvifException ex) {
            throw new VideoBusinessException(500, "调用预置点失败: " + ex.getMessage());
        }
    }

    public void deleteOnvifPreset(String deviceId, String presetToken) {
        DeviceCredentials creds = requireOnvifCredentials(deviceId);
        try {
            OnvifSoapClient.Session session = onvifSession(creds);
            onvifSoapClient.removePreset(session, presetToken, creds.username(), creds.password(), ONVIF_TIMEOUT_SECONDS);
        } catch (OnvifSoapClient.OnvifException ex) {
            throw new VideoBusinessException(500, "删除预置点失败: " + ex.getMessage());
        }
    }

    public Map<String, Object> captureSnapshot(String deviceId) {
        DeviceRow device = requireDevice(deviceId);
        if (device.getSource() == null || device.getSource().isBlank()) {
            throw new VideoBusinessException(400, "设备源地址为空");
        }
        try {
            byte[] jpeg = FfmpegFrameCapture.captureJpeg(device.getSource().trim(), 10);
            return cameraScreenshotService.persistJpeg(deviceId, jpeg, 0, 0);
        } catch (FfmpegFrameCapture.CaptureException ex) {
            throw new VideoBusinessException(500, ex.getMessage());
        }
    }

    public Map<String, Object> connectOnvif(String ip, int port, String password, String username) {
        OnvifSoapClient.OnvifException lastError = null;
        String usedUsername = null;
        OnvifSoapClient.Session session = null;
        for (String candidate : onvifUsernameCandidates(username)) {
            try {
                session = onvifSoapClient.connect(ip, port, candidate, password, ONVIF_TIMEOUT_SECONDS);
                usedUsername = candidate;
                break;
            } catch (OnvifSoapClient.OnvifException ex) {
                lastError = ex;
            }
        }
        if (session == null) {
            throw new VideoBusinessException(500, formatOnvifRegisterError(ip, port, lastError));
        }
        try {
            Map<String, Object> info = new LinkedHashMap<>(onvifSoapClient.getDeviceInformation(session, usedUsername, password, ONVIF_TIMEOUT_SECONDS));
            info.put("ip", ip);
            info.put("port", port);
            info.put("username", usedUsername);
            info.put("password", password);
            info.put("mac", onvifSoapClient.getMacAddress(session, usedUsername, password, ONVIF_TIMEOUT_SECONDS));
            String streamUri = onvifSoapClient.getStreamUri(session, usedUsername, password, ONVIF_TIMEOUT_SECONDS);
            info.put("source", embedRtspAuth(streamUri, usedUsername, password));
            info.put("support_move", session.ptzServiceUrl() != null && !session.ptzServiceUrl().isBlank());
            info.put("support_zoom", info.get("support_move"));
            return info;
        } catch (OnvifSoapClient.OnvifException ex) {
            throw new VideoBusinessException(500, formatOnvifRegisterError(ip, port, ex));
        }
    }

    private void runRtspCaptureTask(String deviceId, String rtspUrl, int interval, int maxCount, CaptureTaskState state) {
        int count = 0;
        while (state.running && count < maxCount) {
            long started = System.currentTimeMillis();
            try {
                byte[] jpeg = FfmpegFrameCapture.captureJpeg(rtspUrl, 10);
                cameraScreenshotService.persistJpeg(deviceId, jpeg, 0, 0);
                count++;
            } catch (Exception ex) {
                log.warn("设备 {} RTSP 截图失败: {}", deviceId, ex.getMessage());
                break;
            }
            long elapsed = System.currentTimeMillis() - started;
            long sleepMs = Math.max(0, interval * 1000L - elapsed);
            if (sleepMs > 0) {
                try {
                    Thread.sleep(sleepMs);
                } catch (InterruptedException ex) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }
        }
        state.running = false;
    }

    private void runOnvifCaptureTask(String deviceId, String snapshotUri, DeviceCredentials creds,
                                     int interval, int maxCount, CaptureTaskState state) {
        int count = 0;
        while (state.running && count < maxCount) {
            long started = System.currentTimeMillis();
            try {
                byte[] jpeg = onvifSoapClient.fetchSnapshot(snapshotUri, creds.username(), creds.password(), 10);
                cameraScreenshotService.persistJpeg(deviceId, jpeg, 0, 0);
                count++;
            } catch (Exception ex) {
                log.warn("设备 {} ONVIF 截图失败: {}", deviceId, ex.getMessage());
                break;
            }
            long elapsed = System.currentTimeMillis() - started;
            long sleepMs = Math.max(0, interval * 1000L - elapsed);
            if (sleepMs > 0) {
                try {
                    Thread.sleep(sleepMs);
                } catch (InterruptedException ex) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }
        }
        state.running = false;
    }

    private OnvifSoapClient.Session onvifSession(DeviceCredentials creds) throws OnvifSoapClient.OnvifException {
        return onvifSessions.computeIfAbsent(creds.deviceId(), id -> {
            try {
                return onvifSoapClient.connect(creds.ip(), creds.port(), creds.username(), creds.password(), ONVIF_TIMEOUT_SECONDS);
            } catch (OnvifSoapClient.OnvifException ex) {
                throw new IllegalStateException(ex);
            }
        });
    }

    private DeviceCredentials requireOnvifCredentials(String deviceId) {
        DeviceRow device = requireDevice(deviceId);
        if (isNvrChannelDevice(device)) {
            throw new VideoBusinessException(400, "设备 " + deviceId + " 为 NVR 挂载通道，不需要 ONVIF 连接");
        }
        if (device.getSource() != null && device.getSource().trim().toLowerCase().startsWith("rtmp://")) {
            throw new VideoBusinessException(400, "设备 " + deviceId + " 的源地址是 RTMP，不需要 ONVIF 连接");
        }
        if (device.getIp() == null || device.getIp().isBlank()) {
            throw new VideoBusinessException(500, "设备未配置 ONVIF 连接信息或 ONVIF SDK 不可用");
        }
        int port = device.getPort() != null && device.getPort() > 0 ? device.getPort() : 80;
        String username = device.getUsername() != null ? device.getUsername() : "admin";
        String password = deviceRepository.findPasswordById(deviceId).orElse("");
        if (password.isBlank()) {
            throw new VideoBusinessException(500, "设备未配置 ONVIF 连接信息或 ONVIF SDK 不可用");
        }
        return new DeviceCredentials(deviceId, device.getIp(), port, username, password);
    }

    private DeviceRow requireDevice(String deviceId) {
        return deviceRepository.findById(deviceId)
                .orElseThrow(() -> new VideoBusinessException(400, "设备不存在: ID=" + deviceId));
    }

    private static boolean isNvrChannelDevice(DeviceRow device) {
        if (device.getNvrId() != null && device.getNvrId() > 0) {
            return true;
        }
        return device.getNvrChannel() > 0 && "NVR-Channel".equalsIgnoreCase(String.valueOf(device.getModel()));
    }

    private static List<String> onvifUsernameCandidates(String username) {
        if (username != null && !username.isBlank()) {
            return List.of(username.trim());
        }
        return DEFAULT_ONVIF_USERNAMES;
    }

    private static String formatOnvifRegisterError(String ip, int port, OnvifSoapClient.OnvifException ex) {
        String detail = ex != null ? ex.getMessage() : "unknown error";
        return "无法连接到设备 " + ip + ":" + port + "，请检查 IP、端口、用户名和密码是否正确（" + detail + "）";
    }

    private static String injectHttpAuth(String uri, String username, String password) {
        if (username == null || username.isBlank() || uri == null) {
            return uri;
        }
        String auth = URLEncoder.encode(username, StandardCharsets.UTF_8) + ":" + URLEncoder.encode(password != null ? password : "", StandardCharsets.UTF_8);
        if (uri.startsWith("http://")) {
            return uri.replaceFirst("http://", "http://" + auth + "@");
        }
        if (uri.startsWith("https://")) {
            return uri.replaceFirst("https://", "https://" + auth + "@");
        }
        return uri;
    }

    private static String embedRtspAuth(String streamUri, String username, String password) {
        if (streamUri == null || streamUri.isBlank() || username == null || username.isBlank()) {
            return streamUri;
        }
        if (!streamUri.startsWith("rtsp://")) {
            return streamUri;
        }
        String auth = URLEncoder.encode(username, StandardCharsets.UTF_8) + ":" + URLEncoder.encode(password != null ? password : "", StandardCharsets.UTF_8);
        return streamUri.replaceFirst("rtsp://", "rtsp://" + auth + "@");
    }

    private static String str(Object value) {
        return value != null ? String.valueOf(value).trim() : "";
    }

    private static String strOr(Object value, String defaultValue) {
        String s = str(value);
        return s.isEmpty() ? defaultValue : s;
    }

    private static String strOrNull(Object value) {
        String s = str(value);
        return s.isEmpty() ? null : s;
    }

    private static int intOr(Object value, int defaultValue) {
        if (value == null || "".equals(String.valueOf(value))) {
            return defaultValue;
        }
        return Integer.parseInt(String.valueOf(value));
    }

    private static double doubleOr(Object value, double defaultValue) {
        if (value == null || "".equals(String.valueOf(value))) {
            return defaultValue;
        }
        return Double.parseDouble(String.valueOf(value));
    }

    private static double number(Object value) {
        if (value == null) {
            return 0.0;
        }
        return Double.parseDouble(String.valueOf(value));
    }

    private static boolean boolOr(Object value, boolean defaultValue) {
        if (value == null) {
            return defaultValue;
        }
        if (value instanceof Boolean bool) {
            return bool;
        }
        String text = String.valueOf(value).trim().toLowerCase();
        if ("false".equals(text) || "0".equals(text) || "no".equals(text)) {
            return false;
        }
        if ("true".equals(text) || "1".equals(text) || "yes".equals(text)) {
            return true;
        }
        return defaultValue;
    }

    private record DeviceCredentials(String deviceId, String ip, int port, String username, String password) {}

    private static final class CaptureTaskState {
        private boolean running;
        private long taskId;

        private CaptureTaskState(boolean running) {
            this.running = running;
        }
    }
}
