package com.basiclab.iot.video.service.postprocess;

import lombok.Data;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Per-camera / per-task YAML calibration for Java post-process rules.
 */
@Data
public class PostProcessRuleConfig {

    private String rule;
    private String cameraId;
    private String taskId;
    private Map<String, Region> regions = new LinkedHashMap<>();
    private Params params = new Params();
    private Alarm alarm = new Alarm();

    @Data
    public static class Region {
        /** box | polyline | polygon */
        private String type = "box";
        private Double x;
        private Double y;
        private Double w;
        private Double h;
        private List<List<Double>> points = new ArrayList<>();
    }

    @Data
    public static class Params {
        private List<String> classes = new ArrayList<>();
        private Double intrusionRatioThreshold = 0.35;
        private Double minConfidence = 0.5;
        private Integer suppressSec = 30;
        private Integer minCount = 1;
        private Integer maxCount;
    }

    @Data
    public static class Alarm {
        private String event = "post_process_rule";
        private String severity = "warning";
    }
}
