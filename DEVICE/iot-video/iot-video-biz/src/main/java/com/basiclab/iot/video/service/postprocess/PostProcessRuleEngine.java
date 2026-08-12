package com.basiclab.iot.video.service.postprocess;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.domain.AlgorithmTaskRow;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.yaml.snakeyaml.Yaml;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/**
 * YAML-driven post-process rules (region count / intrusion). Replaces Python {@code run_worker.py}
 * as the commercial default path — no plugin Python required.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class PostProcessRuleEngine {

    private final VideoProperties videoProperties;

    public boolean javaRulesEnabled() {
        String env = System.getenv("VIDEO_POST_PROCESS_JAVA_RULES");
        if (env != null && !env.isBlank()) {
            String n = env.trim().toLowerCase(Locale.ROOT);
            return n.equals("1") || n.equals("true") || n.equals("yes") || n.equals("on");
        }
        return videoProperties.getPostProcess().isJavaRulesEnabled();
    }

    public Path rulesDir() {
        String configured = videoProperties.getPostProcess().getRulesDir();
        if (configured != null && !configured.isBlank()) {
            return Path.of(configured.trim());
        }
        return Path.of(videoProperties.getPostProcess().getWorkspaceRoot(), "rules");
    }

    public List<PostProcessRuleConfig> loadRulesFor(AlgorithmTaskRow task, String deviceId) {
        List<PostProcessRuleConfig> out = new ArrayList<>();
        Path dir = rulesDir();
        if (!Files.isDirectory(dir)) {
            return out;
        }
        try (var stream = Files.list(dir)) {
            stream.filter(p -> {
                String name = p.getFileName().toString().toLowerCase(Locale.ROOT);
                return name.endsWith(".yaml") || name.endsWith(".yml");
            }).forEach(p -> {
                try {
                    PostProcessRuleConfig cfg = loadYaml(p);
                    if (matches(cfg, task, deviceId)) {
                        out.add(cfg);
                    }
                } catch (Exception ex) {
                    log.warn("skip post-process rule {}: {}", p, ex.getMessage());
                }
            });
        } catch (IOException ex) {
            log.warn("list post-process rules failed: {}", ex.getMessage());
        }
        // Task workspace rule file (post_process.yaml) preferred over scripts.
        if (task != null) {
            Path workspaceRule = Path.of(videoProperties.getPostProcess().getWorkspaceRoot())
                    .resolve("task_" + task.getId())
                    .resolve("post_process.yaml");
            if (Files.isRegularFile(workspaceRule)) {
                try {
                    PostProcessRuleConfig cfg = loadYaml(workspaceRule);
                    if (matches(cfg, task, deviceId)) {
                        out.add(0, cfg);
                    }
                } catch (Exception ex) {
                    log.warn("workspace rule load failed {}: {}", workspaceRule, ex.getMessage());
                }
            }
        }
        return out;
    }

    public Map<String, Object> evaluate(
            AlgorithmTaskRow task,
            String deviceId,
            List<Map<String, Object>> detections,
            List<Map<String, Object>> regions
    ) {
        List<PostProcessRuleConfig> rules = loadRulesFor(task, deviceId);
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("engine", "java-yaml");
        result.put("python_worker", false);
        result.put("rule_count", rules.size());
        List<Map<String, Object>> hits = new ArrayList<>();
        for (PostProcessRuleConfig rule : rules) {
            Map<String, Object> hit = evaluateOne(rule, detections, regions);
            if (hit != null) {
                hits.add(hit);
            }
        }
        result.put("hits", hits);
        result.put("triggered", !hits.isEmpty());
        return result;
    }

    private Map<String, Object> evaluateOne(
            PostProcessRuleConfig rule,
            List<Map<String, Object>> detections,
            List<Map<String, Object>> dbRegions
    ) {
        String type = rule.getRule() != null ? rule.getRule().trim().toLowerCase(Locale.ROOT) : "";
        return switch (type) {
            case "region_count", "area_count" -> evalRegionCount(rule, detections);
            case "region_intrusion", "conveyor_edge_intrusion", "intrusion" -> evalIntrusion(rule, detections);
            default -> {
                log.debug("unknown post-process rule type: {}", type);
                yield null;
            }
        };
    }

    private Map<String, Object> evalRegionCount(PostProcessRuleConfig rule, List<Map<String, Object>> detections) {
        PostProcessRuleConfig.Region region = primaryRegion(rule);
        if (region == null) {
            return null;
        }
        double minConf = rule.getParams().getMinConfidence() != null ? rule.getParams().getMinConfidence() : 0.5;
        List<String> classes = rule.getParams().getClasses();
        int count = 0;
        for (Map<String, Object> det : detections != null ? detections : List.<Map<String, Object>>of()) {
            if (!classAllowed(det, classes)) {
                continue;
            }
            if (confidence(det) < minConf) {
                continue;
            }
            double[] box = bbox(det);
            if (box == null) {
                continue;
            }
            if (boxCenterInRegion(box, region)) {
                count++;
            }
        }
        int minCount = rule.getParams().getMinCount() != null ? rule.getParams().getMinCount() : 1;
        Integer maxCount = rule.getParams().getMaxCount();
        boolean triggered = count >= minCount && (maxCount == null || count <= maxCount);
        if (!triggered) {
            return null;
        }
        Map<String, Object> hit = new LinkedHashMap<>();
        hit.put("rule", rule.getRule());
        hit.put("event", rule.getAlarm() != null ? rule.getAlarm().getEvent() : "region_count");
        hit.put("count", count);
        hit.put("camera_id", rule.getCameraId());
        return hit;
    }

    private Map<String, Object> evalIntrusion(PostProcessRuleConfig rule, List<Map<String, Object>> detections) {
        PostProcessRuleConfig.Region interest = rule.getRegions() != null
                ? rule.getRegions().values().stream().findFirst().orElse(null)
                : null;
        if (interest == null) {
            return null;
        }
        double threshold = rule.getParams().getIntrusionRatioThreshold() != null
                ? rule.getParams().getIntrusionRatioThreshold() : 0.35;
        double minConf = rule.getParams().getMinConfidence() != null ? rule.getParams().getMinConfidence() : 0.5;
        List<String> classes = rule.getParams().getClasses();
        double best = 0;
        Map<String, Object> bestDet = null;
        for (Map<String, Object> det : detections != null ? detections : List.<Map<String, Object>>of()) {
            if (!classAllowed(det, classes)) {
                continue;
            }
            if (confidence(det) < minConf) {
                continue;
            }
            double[] box = bbox(det);
            if (box == null) {
                continue;
            }
            double ratio = overlapRatio(box, interest);
            if (ratio > best) {
                best = ratio;
                bestDet = det;
            }
        }
        if (best < threshold) {
            return null;
        }
        Map<String, Object> hit = new LinkedHashMap<>();
        hit.put("rule", rule.getRule());
        hit.put("event", rule.getAlarm() != null ? rule.getAlarm().getEvent() : "region_intrusion");
        hit.put("intrusion_ratio", best);
        hit.put("threshold", threshold);
        hit.put("camera_id", rule.getCameraId());
        if (bestDet != null) {
            hit.put("detection", bestDet);
        }
        return hit;
    }

    private static PostProcessRuleConfig.Region primaryRegion(PostProcessRuleConfig rule) {
        if (rule.getRegions() == null || rule.getRegions().isEmpty()) {
            return null;
        }
        return rule.getRegions().values().iterator().next();
    }

    private static boolean matches(PostProcessRuleConfig cfg, AlgorithmTaskRow task, String deviceId) {
        if (cfg.getCameraId() != null && !cfg.getCameraId().isBlank()
                && deviceId != null && !cfg.getCameraId().equals(deviceId)) {
            return false;
        }
        if (cfg.getTaskId() != null && !cfg.getTaskId().isBlank() && task != null) {
            return cfg.getTaskId().equals(String.valueOf(task.getId()))
                    || cfg.getTaskId().equals(task.getTaskCode());
        }
        return true;
    }

    @SuppressWarnings("unchecked")
    private PostProcessRuleConfig loadYaml(Path path) throws IOException {
        Yaml yaml = new Yaml();
        Object raw = yaml.load(Files.readString(path));
        if (!(raw instanceof Map<?, ?> map)) {
            throw new IOException("yaml root must be mapping");
        }
        PostProcessRuleConfig cfg = new PostProcessRuleConfig();
        cfg.setRule(str(map.get("rule")));
        cfg.setCameraId(str(map.get("camera_id")));
        cfg.setTaskId(str(map.get("task_id")));
        Object regions = map.get("regions");
        if (regions instanceof Map<?, ?> rm) {
            Map<String, PostProcessRuleConfig.Region> parsed = new LinkedHashMap<>();
            for (Map.Entry<?, ?> e : rm.entrySet()) {
                if (e.getValue() instanceof Map<?, ?> rv) {
                    PostProcessRuleConfig.Region region = new PostProcessRuleConfig.Region();
                    region.setType(str(rv.get("type")) != null ? str(rv.get("type")) : "box");
                    region.setX(toDouble(rv.get("x")));
                    region.setY(toDouble(rv.get("y")));
                    region.setW(toDouble(rv.get("w")));
                    region.setH(toDouble(rv.get("h")));
                    Object pts = rv.get("points");
                    if (pts instanceof List<?> list) {
                        List<List<Double>> points = new ArrayList<>();
                        for (Object row : list) {
                            if (row instanceof List<?> pair && pair.size() >= 2) {
                                points.add(List.of(toDouble(pair.get(0)), toDouble(pair.get(1))));
                            }
                        }
                        region.setPoints(points);
                    }
                    parsed.put(String.valueOf(e.getKey()), region);
                }
            }
            cfg.setRegions(parsed);
        }
        Object params = map.get("params");
        if (params instanceof Map<?, ?> pm) {
            PostProcessRuleConfig.Params p = new PostProcessRuleConfig.Params();
            Object classes = pm.get("classes");
            if (classes instanceof List<?> cl) {
                List<String> names = new ArrayList<>();
                for (Object c : cl) {
                    names.add(String.valueOf(c));
                }
                p.setClasses(names);
            }
            p.setIntrusionRatioThreshold(toDouble(pm.get("intrusion_ratio_threshold")));
            p.setMinConfidence(toDouble(pm.get("min_confidence")));
            p.setSuppressSec(toInt(pm.get("suppress_sec")));
            p.setMinCount(toInt(pm.get("min_count")));
            p.setMaxCount(toInt(pm.get("max_count")));
            cfg.setParams(p);
        }
        Object alarm = map.get("alarm");
        if (alarm instanceof Map<?, ?> am) {
            PostProcessRuleConfig.Alarm a = new PostProcessRuleConfig.Alarm();
            a.setEvent(str(am.get("event")) != null ? str(am.get("event")) : "post_process_rule");
            a.setSeverity(str(am.get("severity")) != null ? str(am.get("severity")) : "warning");
            cfg.setAlarm(a);
        }
        return cfg;
    }

    private static boolean classAllowed(Map<String, Object> det, List<String> classes) {
        if (classes == null || classes.isEmpty()) {
            return true;
        }
        String name = str(det.get("class_name"));
        if (name == null) {
            name = str(det.get("label"));
        }
        if (name == null) {
            name = str(det.get("name"));
        }
        if (name == null) {
            return false;
        }
        for (String c : classes) {
            if (c != null && c.equalsIgnoreCase(name)) {
                return true;
            }
        }
        return false;
    }

    private static double confidence(Map<String, Object> det) {
        Double c = toDouble(det.get("confidence"));
        if (c == null) {
            c = toDouble(det.get("score"));
        }
        if (c == null) {
            c = toDouble(det.get("conf"));
        }
        return c != null ? c : 0;
    }

    @SuppressWarnings("unchecked")
    private static double[] bbox(Map<String, Object> det) {
        Object rect = det.get("bbox");
        if (rect == null) {
            rect = det.get("rect");
        }
        if (rect == null) {
            rect = det.get("box");
        }
        if (rect instanceof List<?> list && list.size() >= 4) {
            return new double[]{
                    toDouble(list.get(0)), toDouble(list.get(1)),
                    toDouble(list.get(2)), toDouble(list.get(3))
            };
        }
        if (rect instanceof Map<?, ?> m) {
            Double x1 = toDouble(m.get("x1"));
            Double y1 = toDouble(m.get("y1"));
            Double x2 = toDouble(m.get("x2"));
            Double y2 = toDouble(m.get("y2"));
            if (x1 != null && y1 != null && x2 != null && y2 != null) {
                return new double[]{x1, y1, x2, y2};
            }
        }
        return null;
    }

    private static boolean boxCenterInRegion(double[] box, PostProcessRuleConfig.Region region) {
        double cx = (box[0] + box[2]) / 2.0;
        double cy = (box[1] + box[3]) / 2.0;
        if ("box".equalsIgnoreCase(region.getType()) || region.getType() == null) {
            if (region.getX() == null || region.getY() == null || region.getW() == null || region.getH() == null) {
                return false;
            }
            return cx >= region.getX() && cx <= region.getX() + region.getW()
                    && cy >= region.getY() && cy <= region.getY() + region.getH();
        }
        // polyline/polygon: treat as axis-aligned bbox of points for MVP
        if (region.getPoints() != null && !region.getPoints().isEmpty()) {
            double minX = Double.MAX_VALUE, minY = Double.MAX_VALUE, maxX = -Double.MAX_VALUE, maxY = -Double.MAX_VALUE;
            for (List<Double> p : region.getPoints()) {
                if (p == null || p.size() < 2) {
                    continue;
                }
                minX = Math.min(minX, p.get(0));
                minY = Math.min(minY, p.get(1));
                maxX = Math.max(maxX, p.get(0));
                maxY = Math.max(maxY, p.get(1));
            }
            return cx >= minX && cx <= maxX && cy >= minY && cy <= maxY;
        }
        return false;
    }

    private static double overlapRatio(double[] box, PostProcessRuleConfig.Region region) {
        double rx1, ry1, rx2, ry2;
        if (region.getX() != null && region.getW() != null) {
            rx1 = region.getX();
            ry1 = region.getY() != null ? region.getY() : 0;
            rx2 = rx1 + region.getW();
            ry2 = ry1 + (region.getH() != null ? region.getH() : 0);
        } else if (region.getPoints() != null && !region.getPoints().isEmpty()) {
            rx1 = Double.MAX_VALUE;
            ry1 = Double.MAX_VALUE;
            rx2 = -Double.MAX_VALUE;
            ry2 = -Double.MAX_VALUE;
            for (List<Double> p : region.getPoints()) {
                if (p == null || p.size() < 2) {
                    continue;
                }
                rx1 = Math.min(rx1, p.get(0));
                ry1 = Math.min(ry1, p.get(1));
                rx2 = Math.max(rx2, p.get(0));
                ry2 = Math.max(ry2, p.get(1));
            }
        } else {
            return 0;
        }
        double ix1 = Math.max(box[0], rx1);
        double iy1 = Math.max(box[1], ry1);
        double ix2 = Math.min(box[2], rx2);
        double iy2 = Math.min(box[3], ry2);
        double iw = Math.max(0, ix2 - ix1);
        double ih = Math.max(0, iy2 - iy1);
        double inter = iw * ih;
        double area = Math.max(1e-6, (box[2] - box[0]) * (box[3] - box[1]));
        return inter / area;
    }

    private static String str(Object v) {
        if (v == null) {
            return null;
        }
        String s = String.valueOf(v).trim();
        return s.isEmpty() ? null : s;
    }

    private static Double toDouble(Object v) {
        if (v == null) {
            return null;
        }
        if (v instanceof Number n) {
            return n.doubleValue();
        }
        try {
            return Double.parseDouble(String.valueOf(v));
        } catch (Exception e) {
            return null;
        }
    }

    private static Integer toInt(Object v) {
        Double d = toDouble(v);
        return d == null ? null : d.intValue();
    }
}
