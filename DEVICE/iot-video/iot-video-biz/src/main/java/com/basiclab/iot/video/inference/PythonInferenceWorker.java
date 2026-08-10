package com.basiclab.iot.video.inference;

import com.basiclab.iot.video.config.VideoProperties;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Base64;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;

/**
 * Subprocess bridge to VIDEO/scripts/inference_workers Python CLIs.
 * Returns real inference when models/runtime are available; honest failure otherwise.
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class PythonInferenceWorker {

    private final VideoProperties videoProperties;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public boolean isFaceEngineAvailable() {
        return isWorkerHealthy("face_inference_cli.py");
    }

    public boolean isPlateEngineAvailable() {
        return isWorkerHealthy("plate_inference_cli.py");
    }

    public boolean isPoseEngineAvailable() {
        return isWorkerHealthy("pose_inference_cli.py");
    }

    public boolean isWorkerHealthy(String scriptName) {
        if (!videoProperties.getInference().isEnabled()) {
            return false;
        }
        Path script = resolveScript(scriptName);
        if (script == null) {
            return false;
        }
        WorkerResult result = run(script, "health", List.of(), null, null);
        return result.ok() && Boolean.TRUE.equals(result.data().get("available"));
    }

    public WorkerResult faceMatchInLibrary(String imagePath, int libraryId, double threshold) {
        Path script = requireScript("face_inference_cli.py");
        List<String> extra = List.of(
                "--library-id", String.valueOf(libraryId),
                "--threshold", String.valueOf(threshold)
        );
        return run(script, "match", extra, imagePath, null);
    }

    public WorkerResult faceRecognize(byte[] imageBytes, Integer libraryId, Double threshold, int topK) {
        Path script = requireScript("face_inference_cli.py");
        List<String> extra = new ArrayList<>();
        extra.add("--top-k");
        extra.add(String.valueOf(topK));
        if (libraryId != null) {
            extra.add("--library-id");
            extra.add(String.valueOf(libraryId));
        }
        if (threshold != null) {
            extra.add("--threshold");
            extra.add(String.valueOf(threshold));
        }
        return run(script, "recognize", extra, null, imageBytes);
    }

    public WorkerResult faceExtractCrop(byte[] imageBytes) {
        Path script = requireScript("face_inference_cli.py");
        return run(script, "extract_crop", List.of(), null, imageBytes);
    }

    public WorkerResult faceAddToLibrary(
            int libraryId,
            int faceEntryId,
            String personName,
            String personCode,
            List<Double> embedding
    ) {
        Path script = requireScript("face_inference_cli.py");
        List<String> extra = new ArrayList<>();
        extra.add("--library-id");
        extra.add(String.valueOf(libraryId));
        extra.add("--face-entry-id");
        extra.add(String.valueOf(faceEntryId));
        extra.add("--person-name");
        extra.add(personName != null ? personName : "");
        if (personCode != null && !personCode.isBlank()) {
            extra.add("--person-code");
            extra.add(personCode);
        }
        if (embedding != null && !embedding.isEmpty()) {
            try {
                extra.add("--embedding-json");
                extra.add(objectMapper.writeValueAsString(embedding));
            } catch (Exception ex) {
                return WorkerResult.fail("embedding serialize failed: " + ex.getMessage());
            }
        }
        return run(script, "add_to_library", extra, null, null);
    }

    public WorkerResult faceDeleteByMilvusId(String milvusId) {
        Path script = requireScript("face_inference_cli.py");
        List<String> extra = List.of("--milvus-id", milvusId != null ? milvusId : "");
        return run(script, "delete_by_milvus_id", extra, null, null);
    }

    /** Mirrors Python {@code face_vector_store.ping()}. */
    public WorkerResult faceVectorStorePing() {
        Path script = resolveScript("face_inference_cli.py");
        if (script == null) {
            return WorkerResult.fail("inference worker script not found: face_inference_cli.py");
        }
        return run(script, "ping", List.of(), null, null);
    }

    public WorkerResult plateRecognize(byte[] imageBytes) {
        Path script = requireScript("plate_inference_cli.py");
        return run(script, "recognize", List.of(), null, imageBytes);
    }

    public WorkerResult plateRecognizePath(String imagePath) {
        Path script = requireScript("plate_inference_cli.py");
        return run(script, "recognize", List.of(), imagePath, null);
    }

    public WorkerResult poseExtract(byte[] imageBytes, double conf) {
        Path script = requireScript("pose_inference_cli.py");
        return run(script, "extract", List.of("--conf", String.valueOf(conf)), null, imageBytes);
    }

    private Path requireScript(String scriptName) {
        Path script = resolveScript(scriptName);
        if (script == null) {
            throw new IllegalStateException("inference worker script not found: " + scriptName);
        }
        return script;
    }

    private Path resolveScript(String scriptName) {
        Path workersDir = resolveWorkersDir();
        if (workersDir == null) {
            return null;
        }
        Path script = workersDir.resolve(scriptName);
        return Files.isRegularFile(script) ? script : null;
    }

    private Path resolveWorkersDir() {
        String configured = videoProperties.getInference().getWorkersDir();
        if (configured != null && !configured.isBlank()) {
            Path dir = Path.of(configured.trim());
            if (Files.isDirectory(dir)) {
                return dir;
            }
        }
        String repoRoot = resolveRepoRoot();
        if (repoRoot == null) {
            return null;
        }
        Path dir = Path.of(repoRoot, "VIDEO", "scripts", "inference_workers");
        return Files.isDirectory(dir) ? dir : null;
    }

    private String resolveRepoRoot() {
        String env = firstNonBlank(System.getenv("ACME_ROOT"), System.getenv("RUNTIME_ROOT"));
        if (env != null) {
            return env;
        }
        String configured = videoProperties.getRuntime().getRepoRoot();
        if (configured != null && !configured.isBlank()) {
            return configured.trim();
        }
        return null;
    }

    private WorkerResult run(
            Path script,
            String command,
            List<String> extraArgs,
            String imagePath,
            byte[] imageBytes
    ) {
        if (!videoProperties.getInference().isEnabled()) {
            return WorkerResult.fail("python inference disabled (video.inference.enabled=false)");
        }
        String python = resolvePythonExecutable();
        List<String> cmd = new ArrayList<>();
        cmd.add(python);
        cmd.add(script.toString());
        cmd.add(command);
        if (extraArgs != null) {
            cmd.addAll(extraArgs);
        }
        if (imagePath != null && !imagePath.isBlank()) {
            cmd.add("--image-path");
            cmd.add(imagePath);
        }
        int timeoutSec = Math.max(5, videoProperties.getInference().getTimeoutSeconds());
        Path tempImagePath = null;
        Path outputFile = null;
        try {
            if (imageBytes != null && imageBytes.length > 0 && (imagePath == null || imagePath.isBlank())) {
                tempImagePath = writeTempInferenceImage(imageBytes);
                cmd.add("--image-path");
                cmd.add(tempImagePath.toString());
            }
            outputFile = java.nio.file.Files.createTempFile("video-worker-out-", ".jsonl");
            ProcessBuilder builder = new ProcessBuilder(cmd)
                    .redirectErrorStream(true)
                    .redirectOutput(outputFile.toFile());
            Map<String, String> env = builder.environment();
            String repoRoot = resolveRepoRoot();
            if (repoRoot != null) {
                env.put("ACME_ROOT", repoRoot);
            }
            String pythonExe = resolvePythonExecutable();
            env.put("VIDEO_PYTHON", pythonExe);
            Process process = builder.start();
            boolean finished = process.waitFor(timeoutSec, TimeUnit.SECONDS);
            if (!finished) {
                process.destroyForcibly();
                return WorkerResult.fail("python worker timeout after " + timeoutSec + "s");
            }
            String output = readWorkerJsonLine(outputFile);
            if (output == null || output.isBlank()) {
                return WorkerResult.fail("python worker empty output (exit=" + process.exitValue() + ")");
            }
            Map<String, Object> data = objectMapper.readValue(output, new TypeReference<>() {});
            if (process.exitValue() != 0 && !Boolean.TRUE.equals(data.get("ok"))
                    && !Boolean.TRUE.equals(data.get("available"))) {
                String err = stringOrNull(data.get("error"));
                return WorkerResult.fail(err != null ? err : "python worker exit " + process.exitValue());
            }
            return WorkerResult.ok(data);
        } catch (Exception ex) {
            log.warn("python inference worker failed: script={}, command={}, error={}", script, command, ex.getMessage());
            return WorkerResult.fail(ex.getMessage());
        } finally {
            if (tempImagePath != null) {
                try {
                    java.nio.file.Files.deleteIfExists(tempImagePath);
                } catch (Exception ignored) {
                    // best-effort temp cleanup
                }
            }
            if (outputFile != null) {
                try {
                    java.nio.file.Files.deleteIfExists(outputFile);
                } catch (Exception ignored) {
                    // best-effort temp cleanup
                }
            }
        }
    }

    private Path writeTempInferenceImage(byte[] imageBytes) throws java.io.IOException {
        Path tmp = java.nio.file.Files.createTempFile("video-infer-", ".jpg");
        java.nio.file.Files.write(tmp, imageBytes);
        return tmp;
    }

    private String readWorkerJsonLine(Path outputFile) throws java.io.IOException {
        if (outputFile == null || !java.nio.file.Files.isRegularFile(outputFile)) {
            return null;
        }
        String jsonLine = null;
        for (String line : java.nio.file.Files.readAllLines(outputFile, StandardCharsets.UTF_8)) {
            String trimmed = line.trim();
            if (trimmed.startsWith("{") && trimmed.endsWith("}")) {
                jsonLine = trimmed;
            }
        }
        return jsonLine;
    }

    private String resolvePythonExecutable() {
        String configured = videoProperties.getInference().getPythonExecutable();
        if (configured != null && !configured.isBlank()) {
            return configured.trim();
        }
        String env = firstNonBlank(System.getenv("VIDEO_PYTHON"), System.getenv("PYTHON"));
        if (env != null) {
            return env;
        }
        return "python";
    }

    private static String firstNonBlank(String... values) {
        for (String value : values) {
            if (value != null && !value.isBlank()) {
                return value.trim();
            }
        }
        return null;
    }

    private static String stringOrNull(Object value) {
        if (value == null) {
            return null;
        }
        String text = String.valueOf(value).trim();
        return text.isEmpty() ? null : text;
    }

    public record WorkerResult(boolean ok, Map<String, Object> data, String error) {
        static WorkerResult ok(Map<String, Object> data) {
            return new WorkerResult(true, data, null);
        }

        static WorkerResult fail(String error) {
            return new WorkerResult(false, new LinkedHashMap<>(), error);
        }
    }
}
