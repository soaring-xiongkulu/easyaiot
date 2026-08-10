package com.basiclab.iot.video.service.talk;

import lombok.Getter;
import lombok.extern.slf4j.Slf4j;

import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.Map;

@Slf4j
class AudioTalkSession {

    private final String sessionId;
    private final String deviceId;
    private final String cameraIp;
    private final int cameraRtspPort;
    private final String username;
    private final String password;
    private final String audioCodec;
    private final int sampleRate;
    private final float volumeGain;
    private final boolean noiseSuppression;
    private final boolean echoCancellation;

    private OnvifAudioBackchannelClient client;
    private DatagramSocket rtpSocket;
    private int rtpSequence;
    private int rtpTimestamp;
    private final int rtpSsrc = 12345678;

    @Getter
    private volatile boolean active;

    AudioTalkSession(
            String sessionId,
            String deviceId,
            String cameraIp,
            int cameraRtspPort,
            String username,
            String password,
            String audioCodec,
            int sampleRate,
            float volumeGain,
            boolean noiseSuppression,
            boolean echoCancellation) {
        this.sessionId = sessionId;
        this.deviceId = deviceId;
        this.cameraIp = cameraIp;
        this.cameraRtspPort = cameraRtspPort;
        this.username = username;
        this.password = password;
        this.audioCodec = audioCodec;
        this.sampleRate = sampleRate;
        this.volumeGain = volumeGain;
        this.noiseSuppression = noiseSuppression;
        this.echoCancellation = echoCancellation;
    }

    boolean start() {
        client = new OnvifAudioBackchannelClient(
                cameraIp, cameraRtspPort, username, password, audioCodec, sampleRate, 10_000);
        if (!client.connect()) {
            closeClient();
            return false;
        }
        Map<String, Object> sdpInfo = client.describeAudioBackchannel("/audio");
        if (!Boolean.TRUE.equals(sdpInfo.get("audio_backchannel_supported"))) {
            closeClient();
            return false;
        }
        @SuppressWarnings("unchecked")
        Map<String, Object> audioTrack = (Map<String, Object>) sdpInfo.get("selected_backchannel_track");
        if (audioTrack == null || !client.setupAudioBackchannel(audioTrack) || !client.play()) {
            closeClient();
            return false;
        }
        try {
            rtpSocket = new DatagramSocket(5000);
            active = true;
            return true;
        } catch (Exception ex) {
            log.warn("RTP socket init failed for {}: {}", sessionId, ex.getMessage());
            closeClient();
            return false;
        }
    }

    void stop() {
        active = false;
        if (rtpSocket != null) {
            rtpSocket.close();
            rtpSocket = null;
        }
        closeClient();
    }

    boolean sendAudio(byte[] pcmData) {
        if (!active || client == null || client.getAudioRtpPort() == null || rtpSocket == null) {
            return false;
        }
        try {
            byte[] payload = pcmToG711(pcmData);
            byte[] packet = buildRtpPacket(payload);
            DatagramPacket datagram = new DatagramPacket(
                    packet,
                    packet.length,
                    InetAddress.getByName(cameraIp),
                    client.getAudioRtpPort());
            rtpSocket.send(datagram);
            return true;
        } catch (Exception ex) {
            log.warn("send audio failed for {}: {}", sessionId, ex.getMessage());
            return false;
        }
    }

    Map<String, Object> toStartPayload() {
        return Map.of(
                "success", true,
                "session_id", sessionId,
                "device_id", deviceId,
                "camera_ip", cameraIp,
                "audio_codec", audioCodec,
                "sample_rate", sampleRate,
                "volume_gain", volumeGain,
                "noise_suppression", noiseSuppression,
                "echo_cancellation", echoCancellation
        );
    }

    private byte[] pcmToG711(byte[] pcmData) {
        if (volumeGain != 1.0f && pcmData.length >= 2) {
            ByteBuffer scaled = ByteBuffer.allocate(pcmData.length).order(ByteOrder.LITTLE_ENDIAN);
            ByteBuffer in = ByteBuffer.wrap(pcmData).order(ByteOrder.LITTLE_ENDIAN);
            while (in.remaining() >= 2) {
                short sample = in.getShort();
                int amplified = Math.round(sample * volumeGain);
                amplified = Math.max(Short.MIN_VALUE, Math.min(Short.MAX_VALUE, amplified));
                scaled.putShort((short) amplified);
            }
            pcmData = scaled.array();
        }
        return G711Codec.encodePcm16(pcmData, audioCodec);
    }

    private byte[] buildRtpPacket(byte[] payload) {
        int payloadType = "PCMU".equalsIgnoreCase(audioCodec) ? 0 : 8;
        ByteBuffer header = ByteBuffer.allocate(12);
        header.put((byte) 0x80);
        header.put((byte) payloadType);
        header.putShort((short) (rtpSequence++ & 0xFFFF));
        header.putInt(rtpTimestamp);
        rtpTimestamp += payload.length;
        header.putInt(rtpSsrc);
        byte[] packet = new byte[12 + payload.length];
        System.arraycopy(header.array(), 0, packet, 0, 12);
        System.arraycopy(payload, 0, packet, 12, payload.length);
        return packet;
    }

    private void closeClient() {
        if (client != null) {
            client.teardown();
            client = null;
        }
    }
}
