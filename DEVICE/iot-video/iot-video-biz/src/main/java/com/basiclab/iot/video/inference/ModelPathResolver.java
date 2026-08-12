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
 * Resolves Part2 ONNX model paths (env / config / VIDEO root defaults).
 */
@Component
@RequiredArgsConstructor
public class ModelPathResolver {

    private final VideoProperties videoProperties;

    public Path faceRecModel() {
        return firstExisting(
                env("FACE_MATCH_MODEL_PATH"),
                configured(videoProperties.getInference().getFaceRecModelPath()),
                underVideo("face_rec.onnx"),
                underVideo("_retired_python_video/face_rec.onnx")
        );
    }

    public Path faceDetModel() {
        return firstExisting(
                env("FACE_CAPTURE_MODEL_PATH"),
                configured(videoProperties.getInference().getFaceDetModelPath()),
                underVideo("face_det.onnx"),
                underVideo("_retired_python_video/face_det.onnx")
        );
    }

    public Path plateDetectModel() {
        return firstExisting(
                env("PLATE_DETECT_MODEL_PATH"),
                configured(videoProperties.getInference().getPlateDetectModelPath()),
                underVideo("plate_detect.onnx")
        );
    }

    public Path plateRecModel() {
        return firstExisting(
                env("PLATE_REC_MODEL_PATH"),
                configured(videoProperties.getInference().getPlateRecModelPath()),
                underVideo("plate_rec.onnx")
        );
    }

    public Path videoRoot() {
        List<Path> candidates = new ArrayList<>();
        Path cwd = Paths.get("").toAbsolutePath();
        candidates.add(cwd.resolve("VIDEO"));
        candidates.add(Paths.get("F:/acme/.worktrees/video-java/VIDEO"));
        String repo = videoProperties.getRuntime() != null ? videoProperties.getRuntime().getRepoRoot() : null;
        if (repo != null && !repo.isBlank()) {
            candidates.add(Paths.get(repo, "VIDEO"));
            // worktree layout: repoRoot may be main acme while models live under .worktrees/*/VIDEO
            candidates.add(Paths.get(repo, ".worktrees", "video-java", "VIDEO"));
        }
        for (Path p : candidates) {
            if (p != null && Files.isDirectory(p)) {
                return p.toAbsolutePath().normalize();
            }
        }
        return Paths.get("F:/acme/.worktrees/video-java/VIDEO");
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
