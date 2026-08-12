package com.basiclab.iot.video.service.autoenroll;

import com.basiclab.iot.video.dal.DeviceRepository;
import com.basiclab.iot.video.dal.FaceAutoEnrollRepository;
import com.basiclab.iot.video.dal.FaceLibraryRepository;
import com.basiclab.iot.video.dal.PlateAutoEnrollRepository;
import com.basiclab.iot.video.dal.PlateLibraryRepository;
import com.basiclab.iot.video.domain.DeviceRow;
import com.basiclab.iot.video.exception.VideoBusinessException;
import com.basiclab.iot.video.service.camera.Gb28181SourceResolver;
import com.basiclab.iot.video.service.camera.hardware.FfmpegFrameCapture;
import com.basiclab.iot.video.service.face.FaceLibraryService;
import com.basiclab.iot.video.service.plate.PlateLibraryService;
import com.basiclab.iot.video.service.plate.PlateRecognitionService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.time.OffsetDateTime;
import java.util.Comparator;
import java.util.List;
import java.util.Map;

/**
 * Periodic auto-enroll ticks aligned with Python {@code run_auto_enroll_tick} (face + plate).
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class AutoEnrollTickService {

    private final FaceAutoEnrollRepository faceAutoEnrollRepository;
    private final PlateAutoEnrollRepository plateAutoEnrollRepository;
    private final FaceLibraryRepository faceLibraryRepository;
    private final PlateLibraryRepository plateLibraryRepository;
    private final DeviceRepository deviceRepository;
    private final Gb28181SourceResolver gb28181SourceResolver;
    private final FaceLibraryService faceLibraryService;
    private final PlateRecognitionService plateRecognitionService;
    private final PlateLibraryService plateLibraryService;

    public void runTick() {
        Instant now = Instant.now();
        for (Map<String, Object> task : faceAutoEnrollRepository.findAllRunning()) {
            try {
                tickFaceTask(task, now);
            } catch (Exception ex) {
                log.error("人脸自动录入任务执行异常 library={}: {}", task.get("library_id"), ex.getMessage(), ex);
            }
        }
        for (Map<String, Object> task : plateAutoEnrollRepository.findAllRunning()) {
            try {
                tickPlateTask(task, now);
            } catch (Exception ex) {
                log.error("车牌自动录入任务执行异常 library={}: {}", task.get("library_id"), ex.getMessage(), ex);
            }
        }
    }

    @SuppressWarnings("unchecked")
    private void tickFaceTask(Map<String, Object> task, Instant now) {
        int libraryId = (Integer) task.get("library_id");
        if (isExpired(task, now)) {
            faceAutoEnrollRepository.stopRunning(libraryId);
            log.info("人脸自动录入已过期停止 library={}", libraryId);
            return;
        }
        int intervalSec = Math.max(1, (Integer) task.getOrDefault("capture_interval_sec", 5));
        if (!shouldTick(task, now, intervalSec)) {
            return;
        }
        List<Object> deviceIds = (List<Object>) task.getOrDefault("device_ids", List.of());
        if (deviceIds.isEmpty()) {
            return;
        }
        int idx = ((Number) task.getOrDefault("last_device_index", 0)).intValue() % deviceIds.size();
        String deviceId = String.valueOf(deviceIds.get(idx));
        int nextIndex = (idx + 1) % deviceIds.size();

        log.info("人脸自动录入 tick: library={} device={} index={}", libraryId, deviceId, idx);

        if (faceLibraryRepository.findById(libraryId).filter(lib -> Boolean.TRUE.equals(lib.get("is_enabled"))).isEmpty()) {
            faceAutoEnrollRepository.recordTickOutcome(libraryId, nextIndex, false);
            return;
        }
        DeviceRow device = deviceRepository.findById(deviceId).orElse(null);
        if (device == null || device.getSource() == null || device.getSource().isBlank()) {
            faceAutoEnrollRepository.recordTickOutcome(libraryId, nextIndex, false);
            return;
        }
        byte[] frame;
        try {
            frame = captureFrame(device.getSource().trim());
        } catch (Exception ex) {
            log.warn("人脸自动录入抓帧失败 library={} device={}: {}", libraryId, deviceId, ex.getMessage());
            faceAutoEnrollRepository.recordTickOutcome(libraryId, nextIndex, false);
            return;
        }
        try {
            Map<String, Object> match = faceLibraryService.matchInLibrary(libraryId, frame, null, 1);
            if (Boolean.TRUE.equals(match.get("matched"))) {
                faceAutoEnrollRepository.recordTickOutcome(libraryId, nextIndex, false);
                return;
            }
        } catch (Exception ex) {
            log.debug("人脸自动录入匹配跳过 library={}: {}", libraryId, ex.getMessage());
        }
        String prefix = task.get("person_name_prefix") != null
                ? String.valueOf(task.get("person_name_prefix"))
                : "摄像头自动录入";
        String personName = prefix + "-" + (System.currentTimeMillis() % 100000);
        try {
            faceLibraryService.addEntry(libraryId, personName, frame, null, null, null, true);
            faceAutoEnrollRepository.recordTickOutcome(libraryId, nextIndex, true);
            log.info("人脸自动录入入库成功 library={} device={}", libraryId, deviceId);
        } catch (VideoBusinessException ex) {
            log.info("人脸自动录入跳过 library={}: {}", libraryId, ex.getMessage());
            faceAutoEnrollRepository.recordTickOutcome(libraryId, nextIndex, false);
        } catch (Exception ex) {
            log.warn("人脸自动录入入库失败 library={}: {}", libraryId, ex.getMessage());
            faceAutoEnrollRepository.recordTickOutcome(libraryId, nextIndex, false);
        }
    }

    @SuppressWarnings("unchecked")
    private void tickPlateTask(Map<String, Object> task, Instant now) {
        int libraryId = (Integer) task.get("library_id");
        if (isExpired(task, now)) {
            plateAutoEnrollRepository.stopRunning(libraryId);
            log.info("车牌自动录入已过期停止 library={}", libraryId);
            return;
        }
        int intervalSec = Math.max(1, (Integer) task.getOrDefault("capture_interval_sec", 5));
        if (!shouldTick(task, now, intervalSec)) {
            return;
        }
        List<Object> deviceIds = (List<Object>) task.getOrDefault("device_ids", List.of());
        if (deviceIds.isEmpty()) {
            return;
        }
        int idx = ((Number) task.getOrDefault("last_device_index", 0)).intValue() % deviceIds.size();
        String deviceId = String.valueOf(deviceIds.get(idx));
        int nextIndex = (idx + 1) % deviceIds.size();

        log.info("车牌自动录入 tick: library={} device={} index={}", libraryId, deviceId, idx);

        if (plateLibraryRepository.findById(libraryId).filter(lib -> Boolean.TRUE.equals(lib.get("is_enabled"))).isEmpty()) {
            plateAutoEnrollRepository.recordTickOutcome(libraryId, nextIndex, false);
            return;
        }
        DeviceRow device = deviceRepository.findById(deviceId).orElse(null);
        if (device == null || device.getSource() == null || device.getSource().isBlank()) {
            plateAutoEnrollRepository.recordTickOutcome(libraryId, nextIndex, false);
            return;
        }
        byte[] frame;
        try {
            frame = captureFrame(device.getSource().trim());
        } catch (Exception ex) {
            log.warn("车牌自动录入抓帧失败 library={} device={}: {}", libraryId, deviceId, ex.getMessage());
            plateAutoEnrollRepository.recordTickOutcome(libraryId, nextIndex, false);
            return;
        }
        List<Map<String, Object>> plates;
        try {
            plates = plateRecognitionService.isEngineAvailable()
                    ? plateRecognitionService.recognizePlates(frame)
                    : List.of();
        } catch (Exception ex) {
            log.warn("车牌自动录入识别失败 library={}: {}", libraryId, ex.getMessage());
            plateAutoEnrollRepository.recordTickOutcome(libraryId, nextIndex, false);
            return;
        }
        if (plates.isEmpty()) {
            plateAutoEnrollRepository.recordTickOutcome(libraryId, nextIndex, false);
            return;
        }
        Map<String, Object> best = plates.stream()
                .max(Comparator.comparingDouble(p -> ((Number) p.getOrDefault("detect_conf", 0)).doubleValue()))
                .orElse(plates.get(0));
        String plateNo = best.get("plate_no") != null ? String.valueOf(best.get("plate_no")).trim() : "";
        if (plateNo.isBlank()) {
            plateAutoEnrollRepository.recordTickOutcome(libraryId, nextIndex, false);
            return;
        }
        Map<String, Object> match = plateLibraryService.matchInLibrary(libraryId, plateNo);
        if (Boolean.TRUE.equals(match.get("matched"))) {
            plateAutoEnrollRepository.recordTickOutcome(libraryId, nextIndex, false);
            return;
        }
        try {
            plateLibraryService.addEntry(
                    libraryId,
                    plateNo,
                    best.get("plate_color") != null ? String.valueOf(best.get("plate_color")) : null,
                    null,
                    null,
                    null,
                    frame,
                    true
            );
            plateAutoEnrollRepository.recordTickOutcome(libraryId, nextIndex, true);
            log.info("车牌自动录入入库成功 library={} plateNo={}", libraryId, plateNo);
        } catch (VideoBusinessException ex) {
            log.info("车牌自动录入跳过 library={}: {}", libraryId, ex.getMessage());
            plateAutoEnrollRepository.recordTickOutcome(libraryId, nextIndex, false);
        } catch (Exception ex) {
            log.warn("车牌自动录入入库失败 library={}: {}", libraryId, ex.getMessage());
            plateAutoEnrollRepository.recordTickOutcome(libraryId, nextIndex, false);
        }
    }

    private byte[] captureFrame(String source) throws FfmpegFrameCapture.CaptureException {
        String playable = source;
        if (Gb28181SourceResolver.isGb28181Source(source)) {
            String resolved = gb28181SourceResolver.resolve(source);
            if (resolved == null || resolved.isBlank()) {
                throw new FfmpegFrameCapture.CaptureException("国标点播失败或设备离线");
            }
            playable = resolved.trim();
        }
        try {
            return FfmpegFrameCapture.captureJpeg(playable, 10);
        } catch (FfmpegFrameCapture.CaptureException ex) {
            if (Gb28181SourceResolver.isGb28181Source(source)) {
                String alternate = gb28181SourceResolver.resolveAlternatePullUrl(source, playable);
                if (alternate != null && !alternate.isBlank()) {
                    return FfmpegFrameCapture.captureJpeg(alternate.trim(), 10);
                }
            }
            throw ex;
        }
    }

    private static boolean isExpired(Map<String, Object> task, Instant now) {
        Object expiresAt = task.get("expires_at");
        if (expiresAt == null) {
            return false;
        }
        try {
            Instant expires = expiresAt instanceof Instant instant
                    ? instant
                    : OffsetDateTime.parse(String.valueOf(expiresAt)).toInstant();
            return !now.isBefore(expires);
        } catch (Exception ignored) {
            return false;
        }
    }

    private static boolean shouldTick(Map<String, Object> task, Instant now, int intervalSec) {
        Object lastTick = task.get("last_tick_at");
        if (lastTick == null) {
            return true;
        }
        try {
            Instant last = lastTick instanceof Instant instant
                    ? instant
                    : OffsetDateTime.parse(String.valueOf(lastTick)).toInstant();
            return now.getEpochSecond() - last.getEpochSecond() >= intervalSec;
        } catch (Exception ignored) {
            return true;
        }
    }
}
