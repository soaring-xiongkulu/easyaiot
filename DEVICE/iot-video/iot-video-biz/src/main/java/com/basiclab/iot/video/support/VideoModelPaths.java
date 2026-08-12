package com.basiclab.iot.video.support;

import com.basiclab.iot.video.config.VideoProperties;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

import java.nio.file.Files;
import java.nio.file.Path;

/**
 * Face/plate model path helpers. Prefer {@code DEVICE/iot-video/models} (Phase1 cutover);
 * fall back to legacy {@code VIDEO/*.onnx} until Phase5 deletes the tree.
 */
@Component
@RequiredArgsConstructor
public class VideoModelPaths {

    private static final long MIN_FACE_REC_BYTES = 10L * 1024 * 1024;
    private static final long MIN_PLATE_DETECT_BYTES = 10L * 1024 * 1024;
    private static final long MIN_PLATE_REC_BYTES = 10L * 1024;

    private final VideoProperties videoProperties;

    public Path repoRoot() {
        String configured = videoProperties.getRuntime().getRepoRoot();
        if (configured != null && !configured.isBlank()) {
            return Path.of(configured.trim());
        }
        String envRoot = firstNonBlank(
                System.getenv("ACME_CANDIDATE_ROOT"),
                System.getenv("ACME_ROOT"),
                System.getenv("RUNTIME_ROOT")
        );
        if (envRoot != null) {
            return Path.of(envRoot.trim());
        }
        Path cwd = Path.of(System.getProperty("user.dir"));
        if (Files.isDirectory(cwd.resolve("DEVICE")) || Files.isDirectory(cwd.resolve("VIDEO"))) {
            return cwd;
        }
        Path parent = cwd.getParent();
        if (parent != null && (Files.isDirectory(parent.resolve("DEVICE")) || Files.isDirectory(parent.resolve("VIDEO")))) {
            return parent;
        }
        return cwd;
    }

    public Path modelsRoot() {
        String configured = videoProperties.getInference() != null
                ? videoProperties.getInference().getModelsDir()
                : null;
        if (configured != null && !configured.isBlank()) {
            return Path.of(configured.trim());
        }
        String env = envOrNull("VIDEO_MODELS_DIR");
        if (env != null) {
            return Path.of(env);
        }
        return repoRoot().resolve("DEVICE/iot-video/models");
    }

    /** @deprecated Prefer {@link #modelsRoot()}; kept for callers during cutover. */
    public Path videoRoot() {
        return repoRoot().resolve("VIDEO");
    }

    public Path faceRecModelPath() {
        String env = envOrNull("FACE_MATCH_MODEL_PATH");
        if (env != null) {
            return Path.of(env);
        }
        Path primary = modelsRoot().resolve("face_rec.onnx");
        if (Files.isRegularFile(primary)) {
            return primary;
        }
        return videoRoot().resolve("face_rec.onnx");
    }

    public Path plateDetectModelPath() {
        String env = envOrNull("PLATE_DETECT_MODEL_PATH");
        if (env != null) {
            return Path.of(env);
        }
        Path primary = modelsRoot().resolve("plate_detect.onnx");
        if (Files.isRegularFile(primary)) {
            return primary;
        }
        return videoRoot().resolve("plate_detect.onnx");
    }

    public Path plateRecModelPath() {
        String env = envOrNull("PLATE_REC_MODEL_PATH");
        if (env != null) {
            return Path.of(env);
        }
        Path primary = modelsRoot().resolve("plate_rec.onnx");
        if (Files.isRegularFile(primary)) {
            return primary;
        }
        return videoRoot().resolve("plate_rec.onnx");
    }

    public String milvusUri() {
        String env = envOrNull("MILVUS_URI");
        return env != null ? env : "http://localhost:19530";
    }

    public String faceMilvusCollection() {
        String env = envOrNull("FACE_MILVUS_COLLECTION");
        return env != null ? env : "face_embeddings";
    }

    public boolean isFaceRecModelReady() {
        return fileSizeAtLeast(faceRecModelPath(), MIN_FACE_REC_BYTES);
    }

    public long faceRecModelSizeBytes() {
        return fileSize(faceRecModelPath());
    }

    /**
     * Mirrors Python {@code plate_model_download._model_ready()}.
     */
    public boolean isPlateModelReady() {
        Path detect = plateDetectModelPath();
        Path rec = plateRecModelPath();
        if (!fileSizeAtLeast(detect, MIN_PLATE_DETECT_BYTES)) {
            return false;
        }
        if (!fileSizeAtLeast(rec, MIN_PLATE_REC_BYTES)) {
            return false;
        }
        return Files.isRegularFile(rec.resolveSibling(rec.getFileName() + ".data"));
    }

    private static boolean fileSizeAtLeast(Path path, long minBytes) {
        long size = fileSize(path);
        return size >= minBytes;
    }

    private static long fileSize(Path path) {
        if (!Files.isRegularFile(path)) {
            return 0L;
        }
        try {
            return Files.size(path);
        } catch (Exception ex) {
            return 0L;
        }
    }

    private static String envOrNull(String key) {
        String value = System.getenv(key);
        if (value == null || value.isBlank()) {
            return null;
        }
        return value.trim();
    }

    private static String firstNonBlank(String... values) {
        for (String value : values) {
            if (value != null && !value.isBlank()) {
                return value.trim();
            }
        }
        return null;
    }
}
