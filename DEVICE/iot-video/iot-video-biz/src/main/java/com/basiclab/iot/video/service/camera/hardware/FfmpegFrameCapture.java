package com.basiclab.iot.video.service.camera.hardware;

import com.basiclab.iot.video.util.FfmpegCompat;
import lombok.extern.slf4j.Slf4j;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.TimeUnit;

@Slf4j
public final class FfmpegFrameCapture {

    private FfmpegFrameCapture() {}

    public static byte[] captureJpeg(String source, int timeoutSeconds) throws CaptureException {
        if (source == null || source.isBlank()) {
            throw new CaptureException("设备源地址为空");
        }
        String trimmed = source.trim();
        List<String> command = new ArrayList<>();
        command.add(FfmpegCompat.resolveFfmpegBinary());
        command.add("-hide_banner");
        command.add("-loglevel");
        command.add("error");
        if (trimmed.toLowerCase(Locale.ROOT).startsWith("rtsp://")) {
            command.addAll(FfmpegCompat.ffmpegRtspTimeoutArgs(5_000_000, 5_000_000));
        } else {
            command.addAll(FfmpegCompat.ffmpegNonRtspTimeoutArgs(5_000_000));
        }
        command.add("-i");
        command.add(trimmed);
        command.add("-vframes");
        command.add("1");
        command.add("-f");
        command.add("image2");
        command.add("-vcodec");
        command.add("mjpeg");
        command.add("-q:v");
        command.add("2");
        command.add("pipe:1");
        try {
            ProcessBuilder builder = new ProcessBuilder(command);
            builder.redirectErrorStream(false);
            Process process = builder.start();
            ByteArrayOutputStream stdout = readStream(process.getInputStream());
            String stderr = new String(process.getErrorStream().readAllBytes(), StandardCharsets.UTF_8);
            boolean finished = process.waitFor(timeoutSeconds, TimeUnit.SECONDS);
            if (!finished) {
                process.destroyForcibly();
                throw new CaptureException("视频流抽帧超时");
            }
            if (process.exitValue() != 0) {
                throw new CaptureException("视频流抽帧失败: " + (stderr.isBlank() ? "ffmpeg exit " + process.exitValue() : stderr));
            }
            if (stdout.size() == 0) {
                throw new CaptureException("视频流抽帧失败: 未获取到图像数据");
            }
            return stdout.toByteArray();
        } catch (CaptureException ex) {
            throw ex;
        } catch (Exception ex) {
            throw new CaptureException("视频流抽帧异常: " + ex.getMessage());
        }
    }

    private static ByteArrayOutputStream readStream(InputStream input) throws Exception {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        byte[] buffer = new byte[8192];
        int read;
        while ((read = input.read(buffer)) >= 0) {
            out.write(buffer, 0, read);
        }
        return out;
    }

    public static class CaptureException extends Exception {
        public CaptureException(String message) {
            super(message);
        }
    }
}
