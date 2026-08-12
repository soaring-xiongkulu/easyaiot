package com.basiclab.iot.video.tools;

import ai.onnxruntime.OrtEnvironment;
import ai.onnxruntime.OrtSession;
import com.basiclab.iot.video.inference.onnx.ImageTensors;
import com.basiclab.iot.video.inference.onnx.PoseOnnxEngine;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;

import java.awt.image.BufferedImage;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Standalone evidence runner for Part2 final W1 pose ORT (no Spring).
 *
 * Usage: java ... Part2FinalEvidenceMain pose &lt;image&gt; &lt;onnx&gt; &lt;out.json&gt;
 */
public final class Part2FinalEvidenceMain {

    private Part2FinalEvidenceMain() {
    }

    public static void main(String[] args) throws Exception {
        if (args.length < 1) {
            System.err.println("usage: pose <image> <onnx> <out.json>");
            System.exit(2);
        }
        String cmd = args[0];
        if ("pose".equals(cmd)) {
            runPose(args);
            return;
        }
        System.err.println("unknown cmd " + cmd);
        System.exit(2);
    }

    private static void runPose(String[] args) throws Exception {
        Path image = Path.of(args[1]);
        Path onnx = Path.of(args[2]);
        Path out = Path.of(args[3]);
        ObjectMapper mapper = new ObjectMapper().enable(SerializationFeature.INDENT_OUTPUT);
        Map<String, Object> evidence = new LinkedHashMap<>();
        evidence.put("task", "W1");
        evidence.put("evidence_type", "pose_ort_extract");
        evidence.put("image", image.toString());
        evidence.put("model", onnx.toString());
        evidence.put("python_cli_enabled", false);

        if (!Files.isRegularFile(image) || !Files.isRegularFile(onnx)) {
            evidence.put("status", "BLOCKED");
            evidence.put("error", "missing image or onnx");
            mapper.writeValue(out.toFile(), evidence);
            System.exit(1);
        }

        // Minimal ModelPathResolver stub via anonymous PoseOnnxEngine wiring
        com.basiclab.iot.video.config.VideoProperties props = new com.basiclab.iot.video.config.VideoProperties();
        props.getInference().setPoseModelPath(onnx.toString());
        props.getInference().setOnnxEnabled(true);
        props.getInference().setPythonCliEnabled(false);
        com.basiclab.iot.video.inference.ModelPathResolver resolver =
                new com.basiclab.iot.video.inference.ModelPathResolver(props);
        PoseOnnxEngine engine = new PoseOnnxEngine(resolver);
        long t0 = System.currentTimeMillis();
        BufferedImage bgr = ImageTensors.decodeFile(image);
        List<Map<String, Object>> persons = engine.extractPersons(bgr, 0.25);
        long elapsed = System.currentTimeMillis() - t0;

        // Also dump output tensor shape for debugging
        try (OrtSession session = OrtEnvironment.getEnvironment().createSession(onnx.toString())) {
            evidence.put("input_names", session.getInputNames());
            evidence.put("output_names", session.getOutputNames());
        }

        evidence.put("elapsed_ms", elapsed);
        evidence.put("person_count", persons.size());
        evidence.put("persons_sample", persons.stream().limit(2).toList());
        evidence.put("engine", "onnx-java");
        boolean ok = !persons.isEmpty()
                && persons.get(0).get("keypoints") instanceof List<?> kps
                && kps.size() == 17;
        evidence.put("status", ok ? "PASS" : "PARTIAL");
        if (!ok) {
            evidence.put("note", persons.isEmpty()
                    ? "no persons detected — check sample image / decode"
                    : "unexpected keypoints shape");
        }
        Files.createDirectories(out.getParent());
        mapper.writeValue(out.toFile(), evidence);
        System.out.println(mapper.writeValueAsString(evidence));
        engine.close();
    }
}
