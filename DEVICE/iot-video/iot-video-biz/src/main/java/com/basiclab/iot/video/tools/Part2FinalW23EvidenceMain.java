package com.basiclab.iot.video.tools;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.domain.AlgorithmTaskRow;
import com.basiclab.iot.video.service.postprocess.PostProcessRuleEngine;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Evidence helpers for Part2 final W2/W3 (standalone, no Spring container).
 */
public final class Part2FinalW23EvidenceMain {

    public static void main(String[] args) throws Exception {
        if (args.length < 1) {
            System.err.println("usage: w3-rules | w2-ini-check");
            System.exit(2);
        }
        switch (args[0]) {
            case "w3-rules" -> runW3(args);
            case "w2-ini-check" -> runW2Ini(args);
            default -> {
                System.err.println("unknown " + args[0]);
                System.exit(2);
            }
        }
    }

    private static void runW3(String[] args) throws Exception {
        Path rulesDir = Path.of(args[1]);
        Path out = Path.of(args[2]);
        VideoProperties props = new VideoProperties();
        props.getPostProcess().setJavaRulesEnabled(true);
        props.getPostProcess().setRulesDir(rulesDir.toString());
        PostProcessRuleEngine engine = new PostProcessRuleEngine(props);

        List<Map<String, Object>> detections = new ArrayList<>();
        Map<String, Object> person = new LinkedHashMap<>();
        person.put("class_name", "person");
        person.put("confidence", 0.9);
        person.put("bbox", List.of(120, 120, 180, 200));
        detections.add(person);

        AlgorithmTaskRow task = new AlgorithmTaskRow();
        task.setId(9001L);
        task.setTaskCode("w3_demo");
        task.setPostProcessEnabled(true);

        Map<String, Object> eval = engine.evaluate(task, "cam_demo", detections, List.of());
        Map<String, Object> evidence = new LinkedHashMap<>();
        evidence.put("task", "W3");
        evidence.put("evidence_type", "yaml_java_rules");
        evidence.put("rules_dir", rulesDir.toString());
        evidence.put("java_rules_enabled", true);
        evidence.put("python_worker", false);
        evidence.put("eval", eval);
        boolean ok = Boolean.TRUE.equals(eval.get("triggered"))
                && ((Number) eval.get("rule_count")).intValue() >= 1;
        evidence.put("status", ok ? "PASS" : "PARTIAL");
        Files.createDirectories(out.getParent());
        ObjectMapper mapper = new ObjectMapper().enable(SerializationFeature.INDENT_OUTPUT);
        mapper.writeValue(out.toFile(), evidence);
        System.out.println(mapper.writeValueAsString(evidence));
    }

    private static void runW2Ini(String[] args) throws Exception {
        Path ini = Path.of(args[1]);
        Path runtimeBin = Path.of(args[2]);
        Path out = Path.of(args[3]);
        Map<String, Object> evidence = new LinkedHashMap<>();
        evidence.put("task", "W2");
        evidence.put("evidence_type", "patrol_runtime_ini");
        evidence.put("ini", ini.toString());
        evidence.put("runtime_bin", runtimeBin.toString());
        evidence.put("runtime_exists", Files.isRegularFile(runtimeBin));
        evidence.put("python_run_deploy", false);
        if (!Files.isRegularFile(ini)) {
            evidence.put("status", "BLOCKED");
            evidence.put("error", "ini missing");
        } else {
            String content = Files.readString(ini);
            evidence.put("has_task_type_patrol", content.contains("task_type=patrol"));
            evidence.put("has_devices_json", content.contains("devices_json="));
            evidence.put("has_patrol_mode", content.contains("patrol_mode="));
            evidence.put("engine", "RUNTIME PatrolScheduler");
            boolean ok = Files.isRegularFile(runtimeBin)
                    && content.contains("task_type=patrol")
                    && content.contains("devices_json=");
            evidence.put("status", ok ? "PASS" : "PARTIAL");
            evidence.put("ini_excerpt", content.lines().limit(40).toList());
        }
        Files.createDirectories(out.getParent());
        ObjectMapper mapper = new ObjectMapper().enable(SerializationFeature.INDENT_OUTPUT);
        mapper.writeValue(out.toFile(), evidence);
        System.out.println(mapper.writeValueAsString(evidence));
    }
}
