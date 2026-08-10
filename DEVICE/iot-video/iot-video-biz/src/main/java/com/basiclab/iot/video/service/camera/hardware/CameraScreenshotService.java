package com.basiclab.iot.video.service.camera.hardware;

import com.basiclab.iot.video.dal.DeviceImageRepository;
import com.basiclab.iot.video.service.minio.VideoMinioService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class CameraScreenshotService {

    private static final String SCREENSHOT_BUCKET = "camera-screenshots";
    private static final DateTimeFormatter TIMESTAMP = DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss");

    private final VideoMinioService videoMinioService;
    private final DeviceImageRepository deviceImageRepository;

    public Map<String, Object> persistJpeg(String deviceId, byte[] jpegBytes, int width, int height) {
        if (jpegBytes == null || jpegBytes.length == 0) {
            throw new IllegalStateException("图片上传失败");
        }
        String imageFormat = "jpg";
        String uniqueFilename = UUID.randomUUID().toString().replace("-", "") + "." + imageFormat;
        String timestamp = LocalDateTime.now().format(TIMESTAMP);
        String downloadUrl;
        if (videoMinioService.isStorageEnabled()) {
            String objectName = deviceId + "/" + uniqueFilename;
            videoMinioService.uploadBytes(SCREENSHOT_BUCKET, objectName, jpegBytes, "image/jpeg", true);
            downloadUrl = videoMinioService.buildDownloadUrl(SCREENSHOT_BUCKET, objectName);
        } else {
            Path deviceDir = resolveLocalScreenshotDir(deviceId);
            try {
                Files.createDirectories(deviceDir);
                Path localPath = deviceDir.resolve(uniqueFilename);
                Files.write(localPath, jpegBytes);
                downloadUrl = "/video/alert/image?path=" + URLEncoder.encode(localPath.toString(), StandardCharsets.UTF_8);
            } catch (Exception ex) {
                throw new IllegalStateException("图片上传失败: " + ex.getMessage());
            }
        }
        int imageId = deviceImageRepository.insert(
                deviceId,
                uniqueFilename,
                deviceId + "_" + timestamp + "." + imageFormat,
                downloadUrl,
                width > 0 ? width : null,
                height > 0 ? height : null
        );
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("image_id", imageId);
        data.put("image_url", downloadUrl);
        if (width > 0) {
            data.put("width", width);
        }
        if (height > 0) {
            data.put("height", height);
        }
        return data;
    }

    private Path resolveLocalScreenshotDir(String deviceId) {
        String root = System.getenv("CAMERA_SCREENSHOT_DIR");
        if (root == null || root.isBlank()) {
            root = Path.of(System.getProperty("user.home"), ".video-java", "camera-screenshots").toString();
        }
        return Path.of(root, deviceId);
    }
}
