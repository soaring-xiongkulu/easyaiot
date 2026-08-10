package com.basiclab.iot.video.service;

import com.basiclab.iot.video.config.VideoProperties;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import java.time.Instant;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Slf4j
@Component
@RequiredArgsConstructor
public class PostProcessSinkClient {

    private final VideoProperties videoProperties;
    private final RestTemplate restTemplate = new RestTemplate();

    public boolean publishPostProcessRequest(Map<String, Object> ctx, String alertImagePath) {
        Map<String, Object> message = buildPostProcessRequestMessage(ctx, alertImagePath);
        String url = sinkEnqueueUrl();
        if (videoProperties.getPostProcess().isUseStubEnqueue()) {
            log.info(
                    "post-process mini path (stub enqueue): taskId={}, deviceId={}, frameNumber={}",
                    message.get("taskId"),
                    message.get("deviceId"),
                    message.get("frameNumber")
            );
            PostProcessEnqueueAudit.record(normalizeEnqueueUrl(url), true);
            return true;
        }
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<Map<String, Object>> entity = new HttpEntity<>(message, headers);
            ResponseEntity<Map> response = restTemplate.postForEntity(url, entity, Map.class);
            boolean ok = response.getStatusCode().is2xxSuccessful();
            if (ok && response.getBody() != null) {
                Object code = response.getBody().get("code");
                if (code instanceof Number number && number.intValue() != 0) {
                    ok = false;
                }
            }
            PostProcessEnqueueAudit.record(normalizeEnqueueUrl(url), ok);
            return ok;
        } catch (RestClientException ex) {
            log.warn("post-process enqueue HTTP failed url={}: {}", url, ex.getMessage());
            PostProcessEnqueueAudit.record(normalizeEnqueueUrl(url), false);
            return false;
        }
    }

    public void publishPostProcessRequestAsync(Map<String, Object> ctx, String alertImagePath) {
        Thread thread = new Thread(
                () -> publishPostProcessRequest(ctx, alertImagePath),
                "post-process-enqueue"
        );
        thread.setDaemon(true);
        thread.start();
    }

    static String normalizeEnqueueUrl(String url) {
        if (url == null || url.isBlank()) {
            return "post-process/enqueue";
        }
        int idx = url.indexOf("post-process/enqueue");
        if (idx >= 0) {
            return url.substring(idx);
        }
        return "post-process/enqueue";
    }

    private String sinkEnqueueUrl() {
        VideoProperties.PostProcess cfg = videoProperties.getPostProcess();
        String explicit = cfg.getSinkApiUrl() != null ? cfg.getSinkApiUrl().trim() : "";
        if (!explicit.isEmpty()) {
            String base = explicit.replaceAll("/+$", "");
            return base + "/post-process/enqueue";
        }
        String host = cfg.getSinkHost() != null ? cfg.getSinkHost().trim() : "127.0.0.1";
        String port = cfg.getSinkPort() != null ? cfg.getSinkPort().trim() : "48092";
        return "http://" + host + ":" + port + "/post-process/enqueue";
    }

    private Map<String, Object> buildPostProcessRequestMessage(Map<String, Object> ctx, String alertImagePath) {
        Map<String, Object> message = new LinkedHashMap<>();
        Object ts = ctx.get("timestamp");
        String eventTime;
        Object timestampEpoch = null;
        if (ts instanceof Number number) {
            timestampEpoch = number.doubleValue();
            eventTime = Instant.ofEpochMilli((long) (number.doubleValue() * 1000))
                    .atOffset(ZoneOffset.UTC)
                    .format(DateTimeFormatter.ISO_INSTANT);
        } else {
            eventTime = Instant.now().atOffset(ZoneOffset.UTC).format(DateTimeFormatter.ISO_INSTANT);
        }

        message.put("taskId", ctx.get("task_id"));
        message.put("taskName", ctx.get("task_name"));
        message.put("taskCode", ctx.get("task_code"));
        message.put("taskType", ctx.get("task_type"));
        message.put("deviceId", ctx.get("device_id"));
        message.put("deviceName", ctx.get("device_name"));
        message.put("frameNumber", ctx.get("frame_number"));
        message.put("timestamp", eventTime);
        message.put("timestampEpoch", timestampEpoch);
        message.put("detections", ctx.getOrDefault("detections", List.of()));
        message.put("trackedDetections", ctx.getOrDefault("tracked_detections", List.of()));
        message.put("trackingEnabled", Boolean.TRUE.equals(ctx.get("tracking_enabled")));
        message.put("regions", ctx.getOrDefault("regions", List.of()));
        message.put("modelIds", ctx.getOrDefault("model_ids", List.of()));
        message.put("alertClassNames", ctx.getOrDefault("alert_class_names", List.of()));
        message.put("poseAnalysisEnabled", Boolean.TRUE.equals(ctx.get("pose_analysis_enabled")));
        message.put("poseIntentEnabled", Boolean.TRUE.equals(ctx.get("pose_intent_enabled")));

        String imagePath = alertImagePath != null ? alertImagePath : stringOrNull(ctx.get("alert_image_path"));
        message.put("alertImagePath", imagePath);

        String correlationId = stringOrNull(ctx.get("correlation_id"));
        if (correlationId == null) {
            correlationId = UUID.randomUUID().toString();
        }
        message.put("correlationId", correlationId);
        return message;
    }

    private static String stringOrNull(Object value) {
        if (value == null) {
            return null;
        }
        String text = String.valueOf(value).trim();
        return text.isEmpty() ? null : text;
    }
}
