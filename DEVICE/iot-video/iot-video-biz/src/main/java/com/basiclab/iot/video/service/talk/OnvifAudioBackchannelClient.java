package com.basiclab.iot.video.service.talk;

import lombok.Getter;
import lombok.extern.slf4j.Slf4j;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Slf4j
public class OnvifAudioBackchannelClient implements AutoCloseable {

    private static final Pattern CONTENT_LENGTH = Pattern.compile("(?i)Content-Length:\\s*(\\d+)");

    private final String cameraIp;
    private final int cameraPort;
    private final String username;
    private final String password;
    private final String audioCodec;
    private final int sampleRate;
    private final int socketTimeoutMs;

    private Socket socket;
    private int cseq = 1;

    @Getter
    private String sessionId;

    @Getter
    private Integer audioRtpPort;

    public OnvifAudioBackchannelClient(
            String cameraIp,
            int cameraPort,
            String username,
            String password,
            String audioCodec,
            int sampleRate,
            int socketTimeoutMs) {
        this.cameraIp = cameraIp;
        this.cameraPort = cameraPort;
        this.username = username != null ? username : "admin";
        this.password = password != null ? password : "";
        this.audioCodec = audioCodec != null ? audioCodec : "PCMA";
        this.sampleRate = sampleRate;
        this.socketTimeoutMs = socketTimeoutMs;
    }

    public boolean connect() {
        try {
            socket = new Socket();
            socket.connect(new InetSocketAddress(cameraIp, cameraPort), socketTimeoutMs);
            socket.setSoTimeout(socketTimeoutMs);
            return true;
        } catch (IOException ex) {
            log.warn("RTSP connect failed {}:{} - {}", cameraIp, cameraPort, ex.getMessage());
            return false;
        }
    }

    public Map<String, Object> describeAudioBackchannel(String audioPath) {
        Map<String, Object> sdpInfo = new LinkedHashMap<>();
        sdpInfo.put("audio_backchannel_supported", false);
        sdpInfo.put("audio_tracks", List.of());
        sdpInfo.put("video_tracks", List.of());
        if (socket == null) {
            return sdpInfo;
        }
        String rtspUri = buildRtspUri(audioPath);
        String response = sendRtsp("DESCRIBE", rtspUri, Map.of(
                "Require", "www.onvif.org/ver20/backchannel",
                "Accept", "application/sdp"
        ), true);
        if (response.contains("401")) {
            String authInfo = extractHeader(response, "WWW-Authenticate");
            if (!authInfo.isBlank()) {
                String authHeader = buildDigestAuth("DESCRIBE", rtspUri, authInfo);
                response = sendRtsp("DESCRIBE", rtspUri, Map.of(
                        "Require", "www.onvif.org/ver20/backchannel",
                        "Accept", "application/sdp",
                        "Authorization", authHeader
                ), false);
            }
        }
        return parseSdp(response);
    }

    /**
     * SETUP with actual local RTP/RTCP ports. Callers must bind a UDP socket first and pass its local port
     * (CP-11 T5 — no hardcoded 5000; multi-session safe).
     */
    public boolean setupAudioBackchannel(Map<String, Object> audioTrack, int clientRtpPort) {
        if (socket == null || audioTrack == null) {
            return false;
        }
        if (clientRtpPort <= 0 || clientRtpPort > 65534) {
            return false;
        }
        int clientRtcpPort = clientRtpPort + 1;
        String transport = "RTP/AVP;unicast;client_port=" + clientRtpPort + "-" + clientRtcpPort + ";mode=record";
        String trackId = String.valueOf(audioTrack.getOrDefault("track_id", "1"));
        String controlUrl = String.valueOf(audioTrack.getOrDefault("track_id", ""));
        String rtspUri = buildSetupUri(trackId, controlUrl);
        String response = sendRtsp("SETUP", rtspUri, Map.of(
                "Require", "www.onvif.org/ver20/backchannel",
                "Transport", transport
        ), true);
        if (response.contains("401")) {
            String authInfo = extractHeader(response, "WWW-Authenticate");
            if (!authInfo.isBlank()) {
                String authHeader = buildDigestAuth("SETUP", rtspUri, authInfo);
                response = sendRtsp("SETUP", rtspUri, Map.of(
                        "Require", "www.onvif.org/ver20/backchannel",
                        "Authorization", authHeader,
                        "Transport", transport
                ), false);
            }
        }
        if (!response.contains("200 OK")) {
            return false;
        }
        for (String line : response.split("\r\n")) {
            if (line.regionMatches(true, 0, "Session:", 0, 8)) {
                sessionId = line.substring(8).trim().split(";")[0].trim();
            }
            Matcher matcher = Pattern.compile("server_port=(\\d+)-(\\d+)").matcher(line);
            if (matcher.find()) {
                audioRtpPort = Integer.parseInt(matcher.group(1));
            }
        }
        return sessionId != null;
    }

    public boolean play() {
        if (socket == null || sessionId == null) {
            return false;
        }
        String rtspUri = buildRtspUri("/audio");
        String response = sendRtsp("PLAY", rtspUri, Map.of(
                "Session", sessionId,
                "Range", "npt=0.000-"
        ), true);
        if (response.contains("401")) {
            String authInfo = extractHeader(response, "WWW-Authenticate");
            if (!authInfo.isBlank()) {
                String authHeader = buildDigestAuth("PLAY", rtspUri, authInfo);
                response = sendRtsp("PLAY", rtspUri, Map.of(
                        "Session", sessionId,
                        "Authorization", authHeader,
                        "Range", "npt=0.000-"
                ), false);
            }
        }
        return response.contains("200 OK");
    }

    public void teardown() {
        if (socket == null || sessionId == null) {
            closeSocket();
            return;
        }
        try {
            sendRtsp("TEARDOWN", buildRtspUri("/audio"), Map.of("Session", sessionId), false);
        } catch (Exception ex) {
            log.debug("TEARDOWN failed: {}", ex.getMessage());
        } finally {
            sessionId = null;
            closeSocket();
        }
    }

    @Override
    public void close() {
        teardown();
    }

    private String sendRtsp(String method, String uri, Map<String, String> headers, boolean allowAuthRetry) {
        try {
            StringBuilder request = new StringBuilder();
            request.append(method).append(' ').append(uri).append(" RTSP/1.0\r\n");
            request.append("CSeq: ").append(cseq++).append("\r\n");
            for (Map.Entry<String, String> entry : headers.entrySet()) {
                request.append(entry.getKey()).append(": ").append(entry.getValue()).append("\r\n");
            }
            request.append("User-Agent: ONVIF Audio Backchannel Client\r\n\r\n");
            OutputStream out = socket.getOutputStream();
            out.write(request.toString().getBytes(StandardCharsets.UTF_8));
            out.flush();
            return readRtspResponse();
        } catch (IOException ex) {
            log.warn("RTSP {} failed: {}", method, ex.getMessage());
            return "";
        }
    }

    private String readRtspResponse() throws IOException {
        InputStream in = socket.getInputStream();
        byte[] buffer = new byte[8192];
        int total = 0;
        while (total < buffer.length) {
            int read = in.read(buffer, total, buffer.length - total);
            if (read < 0) {
                break;
            }
            total += read;
            String partial = new String(buffer, 0, total, StandardCharsets.UTF_8);
            int headerEnd = partial.indexOf("\r\n\r\n");
            if (headerEnd >= 0) {
                int contentLength = 0;
                Matcher matcher = CONTENT_LENGTH.matcher(partial.substring(0, headerEnd));
                if (matcher.find()) {
                    contentLength = Integer.parseInt(matcher.group(1));
                }
                int bodyStart = headerEnd + 4;
                while (total - bodyStart < contentLength && total < buffer.length) {
                    int more = in.read(buffer, total, buffer.length - total);
                    if (more < 0) {
                        break;
                    }
                    total += more;
                }
                break;
            }
        }
        return new String(buffer, 0, total, StandardCharsets.UTF_8);
    }

    private Map<String, Object> parseSdp(String response) {
        Map<String, Object> sdpInfo = new LinkedHashMap<>();
        sdpInfo.put("audio_backchannel_supported", false);
        List<Map<String, Object>> audioTracks = new ArrayList<>();
        List<Map<String, Object>> videoTracks = new ArrayList<>();
        if (!response.contains("200 OK")) {
            sdpInfo.put("audio_tracks", audioTracks);
            sdpInfo.put("video_tracks", videoTracks);
            return sdpInfo;
        }
        int sdpStart = response.indexOf("v=0");
        if (sdpStart < 0) {
            sdpInfo.put("audio_tracks", audioTracks);
            sdpInfo.put("video_tracks", videoTracks);
            return sdpInfo;
        }
        Map<String, Object> current = null;
        for (String rawLine : response.substring(sdpStart).split("\r\n")) {
            String line = rawLine.trim();
            if (line.startsWith("m=audio")) {
                if (current != null) {
                    appendTrack(audioTracks, videoTracks, current);
                }
                String[] parts = line.split("\\s+");
                current = new LinkedHashMap<>();
                current.put("type", "audio");
                current.put("port", parts.length > 1 ? Integer.parseInt(parts[1]) : 0);
                current.put("payload_type", parts.length > 3 ? Integer.parseInt(parts[3]) : 0);
                current.put("track_id", "");
                current.put("mode", "");
                current.put("codec", "");
            } else if (line.startsWith("m=video")) {
                if (current != null) {
                    appendTrack(audioTracks, videoTracks, current);
                }
                String[] parts = line.split("\\s+");
                current = new LinkedHashMap<>();
                current.put("type", "video");
                current.put("port", parts.length > 1 ? Integer.parseInt(parts[1]) : 0);
                current.put("track_id", "");
            } else if (line.startsWith("a=") && current != null) {
                if ("a=sendonly".equals(line)) {
                    current.put("mode", "sendonly");
                    sdpInfo.put("audio_backchannel_supported", true);
                } else if ("a=recvonly".equals(line)) {
                    current.put("mode", "recvonly");
                } else if (line.startsWith("a=rtpmap:")) {
                    String[] parts = line.split("[:\\s/]+");
                    if (parts.length >= 3) {
                        current.put("codec", parts[2]);
                    }
                } else if (line.startsWith("a=control:")) {
                    current.put("track_id", extractTrackId(line.substring("a=control:".length()).trim()));
                }
            }
        }
        if (current != null) {
            appendTrack(audioTracks, videoTracks, current);
        }
        sdpInfo.put("audio_tracks", audioTracks);
        sdpInfo.put("video_tracks", videoTracks);
        sdpInfo.put("selected_backchannel_track", selectBestBackchannelTrack(sdpInfo));
        return sdpInfo;
    }

    private void appendTrack(
            List<Map<String, Object>> audioTracks,
            List<Map<String, Object>> videoTracks,
            Map<String, Object> track) {
        if ("audio".equals(track.get("type"))) {
            audioTracks.add(track);
        } else if ("video".equals(track.get("type"))) {
            videoTracks.add(track);
        }
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> selectBestBackchannelTrack(Map<String, Object> sdpInfo) {
        List<Map<String, Object>> audioTracks = (List<Map<String, Object>>) sdpInfo.get("audio_tracks");
        if (audioTracks == null || audioTracks.isEmpty()) {
            return null;
        }
        for (Map<String, Object> track : audioTracks) {
            if ("sendonly".equals(track.get("mode"))) {
                return track;
            }
        }
        for (Map<String, Object> track : audioTracks) {
            String trackId = String.valueOf(track.getOrDefault("track_id", "")).toLowerCase(Locale.ROOT);
            if (trackId.contains("backchannel")) {
                track.put("mode", "sendonly");
                sdpInfo.put("audio_backchannel_supported", true);
                return track;
            }
        }
        for (Map<String, Object> track : audioTracks) {
            String trackId = String.valueOf(track.getOrDefault("track_id", "")).toLowerCase(Locale.ROOT);
            String mode = String.valueOf(track.getOrDefault("mode", ""));
            if (trackId.contains("audio") && !"recvonly".equals(mode)) {
                track.put("mode", "sendonly");
                sdpInfo.put("audio_backchannel_supported", true);
                return track;
            }
        }
        Map<String, Object> fallback = audioTracks.get(0);
        fallback.put("mode", "sendonly");
        sdpInfo.put("audio_backchannel_supported", true);
        return fallback;
    }

    private String extractTrackId(String controlLine) {
        if (controlLine.contains("trackID=")) {
            String trackId = controlLine.substring(controlLine.indexOf("trackID=") + 8);
            int amp = trackId.indexOf('&');
            return amp >= 0 ? trackId.substring(0, amp) : trackId;
        }
        if (controlLine.contains("/")) {
            String trackId = controlLine.substring(controlLine.lastIndexOf('/') + 1);
            int q = trackId.indexOf('?');
            return q >= 0 ? trackId.substring(0, q) : trackId;
        }
        return controlLine;
    }

    private String buildRtspUri(String path) {
        return "rtsp://"
                + encode(username) + ":" + encode(password) + "@"
                + cameraIp + ":" + cameraPort
                + (path.startsWith("/") ? path : "/" + path);
    }

    private String buildSetupUri(String trackId, String controlUrl) {
        if (controlUrl.startsWith("rtsp://")) {
            return controlUrl;
        }
        if (controlUrl.contains("/audio/") || trackId.startsWith("/audio/")) {
            return buildRtspUri(controlUrl.startsWith("/") ? controlUrl : "/" + controlUrl);
        }
        if (trackId.chars().allMatch(Character::isDigit)) {
            return buildRtspUri("/audio/trackID=" + trackId);
        }
        if (trackId.toLowerCase(Locale.ROOT).contains("backchannel")
                || trackId.toLowerCase(Locale.ROOT).contains("audio")) {
            return buildRtspUri("/" + trackId);
        }
        return buildRtspUri("/audio/trackID=" + trackId);
    }

    private String encode(String value) {
        return URLEncoder.encode(value, StandardCharsets.UTF_8);
    }

    private String extractHeader(String response, String headerName) {
        for (String line : response.split("\r\n")) {
            if (line.regionMatches(true, 0, headerName + ":", 0, headerName.length() + 1)) {
                return line.substring(headerName.length() + 1).trim();
            }
        }
        return "";
    }

    private String buildDigestAuth(String method, String uri, String authInfo) {
        Map<String, String> parts = new HashMap<>();
        String cleaned = authInfo.replaceFirst("(?i)^Digest\\s+", "").trim();
        for (String part : cleaned.split(",")) {
            int eq = part.indexOf('=');
            if (eq > 0) {
                String key = part.substring(0, eq).trim();
                String value = part.substring(eq + 1).trim().replace("\"", "");
                parts.put(key, value);
            }
        }
        String realm = parts.getOrDefault("realm", "");
        String nonce = parts.getOrDefault("nonce", "");
        String ha1 = md5(username + ":" + realm + ":" + password);
        String ha2 = md5(method + ":" + uri);
        String responseHash = md5(ha1 + ":" + nonce + ":" + ha2);
        return "Digest username=\"" + username + "\", realm=\"" + realm + "\", nonce=\"" + nonce
                + "\", uri=\"" + uri + "\", response=\"" + responseHash + "\"";
    }

    private String md5(String input) {
        try {
            MessageDigest digest = MessageDigest.getInstance("MD5");
            byte[] hash = digest.digest(input.getBytes(StandardCharsets.UTF_8));
            StringBuilder sb = new StringBuilder();
            for (byte b : hash) {
                sb.append(String.format("%02x", b));
            }
            return sb.toString();
        } catch (NoSuchAlgorithmException ex) {
            throw new IllegalStateException(ex);
        }
    }

    private void closeSocket() {
        if (socket != null) {
            try {
                socket.close();
            } catch (IOException ignored) {
                // ignore
            }
            socket = null;
        }
    }
}
