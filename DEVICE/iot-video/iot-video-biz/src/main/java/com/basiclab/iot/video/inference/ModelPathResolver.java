package com.basiclab.iot.video.inference;

import com.basiclab.iot.video.config.VideoProperties;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

/**
 * Resolves Part2 ONNX model paths (env / config / DEVICE/iot-video/models / VIDEO fallbacks).
 */
@Component
@RequiredArgsConstructor
public class ModelPathResolver {

    private final VideoProperties videoProperties;

    public Path faceRecModel() {
        return firstExisting(
                env("FACE_MATCH_MODEL_PATH"),
                configured(videoProperties.getInference().getFaceRecModelPath()),
                underModels("face_rec.onnx"),
                underVideo("face_rec.onnx"),
                underVideo("_retired_python_video/face_rec.onnx")
        );
    }

    public Path faceDetModel() {
        return firstExisting(
                env("FACE_CAPTURE_MODEL_PATH"),
                configured(videoProperties.getInference().getFaceDetModelPath()),
                underModels("face_det.onnx"),
                underVideo("face_det.onnx"),
                underVideo("_retired_python_video/face_det.onnx")
        );
    }

    public Path plateDetectModel() {
        return firstExisting(
                env("PLATE_DETECT_MODEL_PATH"),
                configured(videoProperties.getInference().getPlateDetectModelPath()),
                underModels("plate_detect.onnx"),
                underVideo("plate_detect.onnx")
        );
    }

    public Path plateRecModel() {
        return firstExisting(
                env("PLATE_REC_MODEL_PATH"),
                configured(videoProperties.getInference().getPlateRecModelPath()),
                underModels("plate_rec.onnx"),
                underVideo("plate_rec.onnx")
        );
    }

    public Path poseModel() {
        return firstExisting(
                env("POSE_MODEL_PATH"),
                configured(videoProperties.getInference().getPoseModelPath()),
                underModels("yolo26n-pose.onnx"),
                underVideo("yolo26n-pose.onnx"),
                underVideo("models/yolo26n-pose.onnx")
        );
    }

    /**
     * Canonical models root after Phase1 cutover: {@code DEVICE/iot-video/models}.
     */
    public Path modelsRoot() {
        List<Path> candidates = new ArrayList<>();
        String configured = videoProperties.getInference() != null
                ? videoProperties.getInference().getModelsDir()
                : null;
        if (configured != null && !configured.isBlank()) {
            candidates.add(Paths.get(configured.trim()));
        }
        String envDir = System.getenv("VIDEO_MODELS_DIR");
        if (envDir != null && !envDir.isBlank()) {
            candidates.add(Paths.get(envDir.trim()));
        }
        for (Path root : repoRoots()) {
            candidates.add(root.resolve("DEVICE/iot-video/models"));
        }
        Path cwd = Paths.get("").toAbsolutePath();
        candidates.add(cwd.resolve("DEVICE/iot-video/models"));
        for (Path p : candidates) {
            if (p != null && Files.isDirectory(p)) {
                return p.toAbsolutePath().normalize();
            }
        }
        // Prefer creating-friendly default under first repo root even if not yet present
        if (!repoRoots().isEmpty()) {
            return repoRoots().get(0).resolve("DEVICE/iot-video/models").toAbsolutePath().normalize();
        }
        return cwd.resolve("DEVICE/iot-video/models").toAbsolutePath().normalize();
    }

    public Path videoRoot() {
        List<Path> candidates = new ArrayList<>();
        for (Path root : repoRoots()) {
            candidates.add(root.resolve("VIDEO"));
        }
        Path cwd = Paths.get("").toAbsolutePath();
        candidates.add(cwd.resolve("VIDEO"));
        Path parent = cwd.getParent();
        if (parent != null) {
            candidates.add(parent.resolve("VIDEO"));
        }
        for (Path p : candidates) {
            if (p != null && Files.isDirectory(p)) {
                return p.toAbsolutePath().normalize();
            }
        }
        if (!repoRoots().isEmpty()) {
            return repoRoots().get(0).resolve("VIDEO").toAbsolutePath().normalize();
        }
        return cwd.resolve("VIDEO").toAbsolutePath().normalize();
    }

    private List<Path> repoRoots() {
        List<Path> roots = new ArrayList<>();
        String repo = videoProperties.getRuntime() != null ? videoProperties.getRuntime().getRepoRoot() : null;
        if (repo != null && !repo.isBlank()) {
            roots.add(Paths.get(repo.trim()));
        }
        for (String key : List.of("ACME_CANDIDATE_ROOT", "ACME_ROOT", "RUNTIME_ROOT")) {
            String v = System.getenv(key);
            if (v != null && !v.isBlank()) {
                roots.add(Paths.get(v.trim()));
            }
        }
        Path cwd = Paths.get("").toAbsolutePath();
        if (Files.isDirectory(cwd.resolve("DEVICE")) || Files.isDirectory(cwd.resolve("VIDEO"))) {
            roots.add(cwd);
        }
        return roots;
    }

    private Path underModels(String relative) {
        return modelsRoot().resolve(relative);
    }

    private Path underVideo(String relative) {
        return videoRoot().resolve(relative);
    }

    private static Path configured(String raw) {
        if (raw == null || raw.isBlank()) {
            return null;
        }
        return Paths.get(raw);
    }

    private static Path env(String key) {
        String v = System.getenv(key);
        if (v == null || v.isBlank()) {
            return null;
        }
        return Paths.get(v);
    }

    private static Path firstExisting(Path... paths) {
        if (paths == null) {
            return null;
        }
        for (Path path : paths) {
            if (path != null && Files.isRegularFile(path) && Files.isReadable(path)) {
                try {
                    if (Files.size(path) > 1024) {
                        return path.toAbsolutePath().normalize();
                    }
                } catch (Exception ignored) {
                    // try next
                }
            }
        }
        return null;
    }
}
