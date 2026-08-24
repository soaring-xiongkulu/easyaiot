package com.basiclab.iot.sink.util;

import org.junit.jupiter.api.Test;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;

class AlertEventGrouperTest {

    @Test
    void shouldSplitDetectionsByModelAndClass() {
        Map<String, Object> person = detection(1, "person");
        Map<String, Object> detection = detection(32, "detection");

        Map<String, List<Map<String, Object>>> groups = AlertEventGrouper.groupDetections(
                List.of(person, detection));

        assertEquals(List.of("1:person", "32:detection"), List.copyOf(groups.keySet()));
        assertEquals(List.of(1), AlertEventGrouper.collectModelIds(groups.get("1:person")));
        assertEquals(List.of(32), AlertEventGrouper.collectModelIds(groups.get("32:detection")));
    }

    @Test
    void shouldNormalizeEquivalentClassNames() {
        Map<String, List<Map<String, Object>>> groups = AlertEventGrouper.groupDetections(
                List.of(detection(1, "Safety Helmet"), detection(1, "safety-helmet")));

        assertEquals(List.of("1:safety_helmet"), List.copyOf(groups.keySet()));
        assertEquals(2, groups.get("1:safety_helmet").size());
    }

    private Map<String, Object> detection(int modelId, String className) {
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("model_id", modelId);
        result.put("class_name", className);
        return result;
    }
}
