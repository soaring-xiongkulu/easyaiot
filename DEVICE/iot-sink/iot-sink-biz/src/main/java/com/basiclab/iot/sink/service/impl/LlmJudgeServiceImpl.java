package com.basiclab.iot.sink.service.impl;

import com.baomidou.dynamic.datasource.toolkit.DynamicDataSourceContextHolder;
import com.basiclab.iot.common.utils.json.JsonUtils;
import com.basiclab.iot.sink.domain.model.AlertNotificationMessage;
import com.basiclab.iot.sink.domain.model.LlmJudgeRequestMessage;
import com.basiclab.iot.sink.service.LlmJudgeService;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;
import org.springframework.web.client.RestTemplate;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * 大模型（LLM）研判执行与回写（独立队列消费者调用，慢链路，不影响告警主线程）。
 *
 * 流程：先落 pending 行（correlation_id 幂等）→ 调 AI 模块内部研判接口 →
 * 更新研判结果行 + 回写 alert.llm_judge_status/llm_judge_detail + information.llm →
 * 门控模式下按结论补发（confirm/skip）或抑制（reject）通知。
 */
@Slf4j
@Service
public class LlmJudgeServiceImpl implements LlmJudgeService {

    @Value("${basiclab.llm-judge.ai-internal-base-url:http://localhost:8000}")
    private String aiInternalBaseUrl;

    @Value("${basiclab.llm-judge.ai-internal-token:}")
    private String aiInternalToken;

    @Value("${basiclab.llm-judge.judge-timeout-ms:120000}")
    private int judgeTimeoutMs;

    @Value("${spring.kafka.alert-notification.send-topic:iot-alert-notification-send}")
    private String notificationSendTopic;

    @Autowired(required = false)
    private KafkaTemplate<String, String> iotKafkaTemplate;

    @Autowired(required = false)
    private JdbcTemplate jdbcTemplate;

    @Autowired(required = false)
    private ObjectMapper objectMapper;

    private volatile RestTemplate restTemplate;

    @Override
    public void executeAndWriteBack(LlmJudgeRequestMessage request) {
        if (request == null || request.getAlertId() == null) {
            return;
        }
        String correlationId = request.getCorrelationId();
        if (!StringUtils.hasText(correlationId)) {
            correlationId = String.valueOf(request.getAlertId()) + "-" + System.currentTimeMillis();
            request.setCorrelationId(correlationId);
        }
        // 幂等：先落 pending 行（重复消息直接跳过，避免重复调用大模型产生费用）
        if (!insertPendingResult(request, correlationId)) {
            log.info("[LlmJudge] 研判记录已存在，跳过重复执行 {}", request.brief());
            return;
        }
        Map<String, Object> judgement = null;
        String errorMsg = null;
        try {
            judgement = invokeAiJudge(request);
        } catch (Exception e) {
            errorMsg = e.getMessage();
            log.error("[LlmJudge] 调用 AI 研判失败 {}: {}", request.brief(), e.getMessage());
        }
        if (judgement == null) {
            updateResultError(correlationId, errorMsg != null ? errorMsg : "AI 研判未返回结果");
            handleGatedFailure(request, errorMsg);
            return;
        }
        updateResultSuccess(correlationId, request, judgement);
        writeBackAlert(request, judgement);
        handleGatedSuccess(request, judgement);
    }

    private Map<String, Object> invokeAiJudge(LlmJudgeRequestMessage request) {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("agent_id", request.getAgentId());
        body.put("model_id", request.getModelId());
        body.put("media_type", request.getJudgeMode());
        body.put("prompt_override", request.getPromptOverride());
        body.put("require_json", request.getRequireJson() != null && request.getRequireJson());

        Map<String, Object> media = new LinkedHashMap<>();
        LlmJudgeRequestMessage.MediaRef ref = request.getMedia();
        if (ref != null) {
            media.put("image_url", ref.getImageUrl());
            media.put("record_path", ref.getRecordPath());
            media.put("event_time", ref.getEventTime());
            media.put("pre_seconds", ref.getPreSeconds());
            media.put("post_seconds", ref.getPostSeconds());
            media.put("max_seconds", ref.getMaxSeconds());
        }
        body.put("media", media);
        body.put("context", request.getContext() != null ? request.getContext() : Map.of());

        RestTemplate client = restTemplate();
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        if (StringUtils.hasText(aiInternalToken)) {
            headers.set("X-Internal-Token", aiInternalToken);
        }
        String url = normalizeBaseUrl(aiInternalBaseUrl) + "/model/llm/internal/judge";
        HttpEntity<String> entity = new HttpEntity<>(JsonUtils.toJsonString(body), headers);
        try {
            ResponseEntity<String> response = client.postForEntity(url, entity, String.class);
            if (!response.getStatusCode().is2xxSuccessful() || !StringUtils.hasText(response.getBody())) {
                throw new IllegalStateException("AI 研判接口返回异常 status=" + response.getStatusCodeValue());
            }
            Map<String, Object> root = JsonUtils.parseObject(response.getBody(), new TypeReference<Map<String, Object>>() {});
            if (root == null) {
                throw new IllegalStateException("AI 研判接口返回为空");
            }
            Object code = root.get("code");
            if (!(code instanceof Number) || ((Number) code).intValue() != 0) {
                throw new IllegalStateException("AI 研判失败: " + root.get("msg"));
            }
            Object data = root.get("data");
            if (!(data instanceof Map)) {
                throw new IllegalStateException("AI 研判结果缺少 data");
            }
            @SuppressWarnings("unchecked")
            Map<String, Object> result = (Map<String, Object>) data;
            log.info("[LlmJudge] 研判完成 {} confirm={} confidence={} duration={}ms",
                    request.brief(), result.get("confirm"), result.get("confidence"), result.get("duration_ms"));
            return result;
        } catch (Exception e) {
            throw new IllegalStateException("调用 AI 研判接口失败: " + e.getMessage(), e);
        }
    }

    private RestTemplate restTemplate() {
        if (restTemplate == null) {
            synchronized (this) {
                if (restTemplate == null) {
                    SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
                    factory.setConnectTimeout(10_000);
                    factory.setReadTimeout(judgeTimeoutMs);
                    restTemplate = new RestTemplate(factory);
                }
            }
        }
        return restTemplate;
    }

    /** 落 pending 研判记录；已存在返回 false（幂等去重） */
    private boolean insertPendingResult(LlmJudgeRequestMessage request, String correlationId) {
        if (jdbcTemplate == null) {
            log.warn("[LlmJudge] JdbcTemplate 不可用，跳过落库");
            return true;
        }
        try {
            DynamicDataSourceContextHolder.push("video");
            Integer count = jdbcTemplate.queryForObject(
                    "SELECT COUNT(1) FROM algorithm_llm_judge_result WHERE correlation_id = ?",
                    Integer.class, correlationId);
            if (count != null && count > 0) {
                return false;
            }
            jdbcTemplate.update(
                    "INSERT INTO algorithm_llm_judge_result "
                            + "(correlation_id, alert_id, task_id, device_id, rule_id, agent_id, model_id, "
                            + "judge_mode, status, created_at) "
                            + "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', NOW())",
                    correlationId,
                    request.getAlertId(),
                    request.getTaskId(),
                    request.getDeviceId(),
                    request.getRuleId(),
                    request.getAgentId(),
                    request.getModelId(),
                    request.getJudgeMode());
            return true;
        } catch (Exception e) {
            log.error("[LlmJudge] 研判记录落库失败 {}: {}", request.brief(), e.getMessage(), e);
            throw new IllegalStateException("研判记录落库失败", e);
        } finally {
            DynamicDataSourceContextHolder.clear();
        }
    }

    private void updateResultSuccess(String correlationId, LlmJudgeRequestMessage request, Map<String, Object> judgement) {
        if (jdbcTemplate == null) {
            return;
        }
        try {
            DynamicDataSourceContextHolder.push("video");
            jdbcTemplate.update(
                    "UPDATE algorithm_llm_judge_result SET status = 'success', confirm = ?, confidence = ?, "
                            + "reason = ?, raw_response = ?, media_url = ?, duration_ms = ?, "
                            + "prompt = ?, structured = ?, updated_at = NOW() "
                            + "WHERE correlation_id = ?",
                    boolOrNull(judgement.get("confirm")),
                    floatOrNull(judgement.get("confidence")),
                    strOrNull(judgement.get("reason")),
                    strOrNull(judgement.get("raw_response")),
                    mediaUrlOf(request),
                    intOrNull(judgement.get("duration_ms")),
                    promptOf(request),
                    toJson(judgement.get("structured")),
                    correlationId);
        } catch (Exception e) {
            log.warn("[LlmJudge] 研判结果更新失败 correlationId={}: {}", correlationId, e.getMessage());
        } finally {
            DynamicDataSourceContextHolder.clear();
        }
    }

    private void updateResultError(String correlationId, String errorMsg) {
        if (jdbcTemplate == null) {
            return;
        }
        try {
            DynamicDataSourceContextHolder.push("video");
            jdbcTemplate.update(
                    "UPDATE algorithm_llm_judge_result SET status = 'error', error_msg = ?, updated_at = NOW() "
                            + "WHERE correlation_id = ?",
                    errorMsg, correlationId);
        } catch (Exception e) {
            log.warn("[LlmJudge] 研判失败状态更新失败 correlationId={}: {}", correlationId, e.getMessage());
        } finally {
            DynamicDataSourceContextHolder.clear();
        }
    }

    private void writeBackAlert(LlmJudgeRequestMessage request, Map<String, Object> judgement) {
        if (jdbcTemplate == null || request.getAlertId() == null) {
            return;
        }
        Boolean confirm = boolOrNull(judgement.get("confirm"));
        String status = Boolean.TRUE.equals(confirm) ? "confirmed"
                : Boolean.FALSE.equals(confirm) ? "rejected" : "error";
        Map<String, Object> detail = new LinkedHashMap<>();
        detail.put("confirm", confirm);
        detail.put("confidence", judgement.get("confidence"));
        detail.put("reason", judgement.get("reason"));
        detail.put("attributes", judgement.get("structured"));
        detail.put("duration_ms", judgement.get("duration_ms"));
        detail.put("model_id", request.getModelId());
        detail.put("agent_id", request.getAgentId());
        detail.put("judge_mode", request.getJudgeMode());
        detail.put("rule_id", request.getRuleId());
        detail.put("correlation_id", request.getCorrelationId());
        detail.put("judged_at", System.currentTimeMillis());
        String detailJson = JsonUtils.toJsonString(detail);
        try {
            DynamicDataSourceContextHolder.push("video");
            jdbcTemplate.update(
                    "UPDATE alert SET llm_judge_status = ?, llm_judge_detail = ? WHERE id = ?",
                    status, detailJson, request.getAlertId());
            mergeInformationLlm(request.getAlertId(), status, detailJson);
            log.info("[LlmJudge] 告警回写完成 alertId={} status={} confirm={}", request.getAlertId(), status, confirm);
        } catch (Exception e) {
            log.warn("[LlmJudge] 告警回写失败 alertId={}: {}", request.getAlertId(), e.getMessage());
        } finally {
            DynamicDataSourceContextHolder.clear();
        }
    }

    /** information JSON 合并 llm 研判节点（双写：列用于筛选，JSON 用于展示/API 兼容） */
    private void mergeInformationLlm(Integer alertId, String status, String detailJson) {
        try {
            List<Map<String, Object>> rows = jdbcTemplate.queryForList(
                    "SELECT information FROM alert WHERE id = ?", alertId);
            if (rows.isEmpty()) {
                return;
            }
            Object raw = rows.get(0).get("information");
            Map<String, Object> infoMap = new LinkedHashMap<>();
            if (raw != null && StringUtils.hasText(String.valueOf(raw))) {
                if (objectMapper != null) {
                    try {
                        Map<String, Object> parsed = objectMapper.readValue(
                                String.valueOf(raw), new TypeReference<Map<String, Object>>() {});
                        if (parsed != null) {
                            infoMap = parsed;
                        }
                    } catch (Exception ignored) {
                        // 原 information 非 JSON，覆盖式合并
                    }
                }
            }
            Map<String, Object> llmNode;
            Object llmRaw = infoMap.get("llm");
            if (llmRaw instanceof Map) {
                @SuppressWarnings("unchecked")
                Map<String, Object> cast = (Map<String, Object>) llmRaw;
                llmNode = cast;
            } else {
                llmNode = new LinkedHashMap<>();
            }
            llmNode.put("status", status);
            llmNode.put("detail", JsonUtils.parseObject(detailJson, Map.class));
            infoMap.put("llm", llmNode);
            jdbcTemplate.update("UPDATE alert SET information = ? WHERE id = ?",
                    JsonUtils.toJsonString(infoMap), alertId);
        } catch (Exception e) {
            log.warn("[LlmJudge] information 合并失败 alertId={}: {}", alertId, e.getMessage());
        }
    }

    private void handleGatedSuccess(LlmJudgeRequestMessage request, Map<String, Object> judgement) {
        if (!Boolean.TRUE.equals(request.getGated())) {
            return;
        }
        Boolean confirm = boolOrNull(judgement.get("confirm"));
        if (Boolean.FALSE.equals(confirm)) {
            log.info("[LlmJudge] 门控抑制通知（研判不成立） alertId={}", request.getAlertId());
            return;
        }
        resendNotification(request);
    }

    private void handleGatedFailure(LlmJudgeRequestMessage request, String errorMsg) {
        if (!Boolean.TRUE.equals(request.getGated())) {
            return;
        }
        String policy = StringUtils.hasText(request.getFailPolicy()) ? request.getFailPolicy() : "skip";
        if ("reject".equalsIgnoreCase(policy)) {
            log.warn("[LlmJudge] 门控抑制通知（研判失败且 fail_policy=reject） alertId={} err={}",
                    request.getAlertId(), errorMsg);
            return;
        }
        // skip/confirm：研判失败视为放行，补发通知，避免大模型故障导致漏报
        log.warn("[LlmJudge] 门控放行通知（研判失败 fail_policy={}） alertId={}", policy, request.getAlertId());
        resendNotification(request);
    }

    /** 门控补发通知：还原原告警消息（含 channels/notify_users），合并 llm 研判信息后投递通知主题 */
    private void resendNotification(LlmJudgeRequestMessage request) {
        if (iotKafkaTemplate == null || request.getNotifyPayload() == null) {
            log.warn("[LlmJudge] 通知补发失败：KafkaTemplate 或 notify_payload 缺失 alertId={}", request.getAlertId());
            return;
        }
        try {
            Object jsonObj = request.getNotifyPayload().get("alertNotificationJson");
            if (!(jsonObj instanceof String) || !StringUtils.hasText((String) jsonObj)) {
                log.warn("[LlmJudge] 通知补发失败：alertNotificationJson 缺失 alertId={}", request.getAlertId());
                return;
            }
            AlertNotificationMessage message = JsonUtils.parseObject((String) jsonObj, AlertNotificationMessage.class);
            if (message == null) {
                return;
            }
            message.setAlertId(request.getAlertId());
            message.setShouldNotify(true);
            String json = JsonUtils.toJsonString(message);
            iotKafkaTemplate.send(notificationSendTopic, message.getDeviceId(), json);
            log.info("[LlmJudge] 门控补发通知 alertId={} deviceId={}", request.getAlertId(), message.getDeviceId());
        } catch (Exception e) {
            log.error("[LlmJudge] 门控补发通知异常 alertId={}: {}", request.getAlertId(), e.getMessage(), e);
        }
    }

    private static String mediaUrlOf(LlmJudgeRequestMessage request) {
        if (request.getMedia() == null) {
            return null;
        }
        if (StringUtils.hasText(request.getMedia().getImageUrl())) {
            return request.getMedia().getImageUrl();
        }
        return request.getMedia().getRecordPath();
    }

    private static String promptOf(LlmJudgeRequestMessage request) {
        return request.getPromptOverride();
    }

    private String toJson(Object value) {
        if (value == null) {
            return null;
        }
        if (value instanceof String) {
            return (String) value;
        }
        return JsonUtils.toJsonString(value);
    }

    private static Boolean boolOrNull(Object value) {
        if (value == null) {
            return null;
        }
        if (value instanceof Boolean) {
            return (Boolean) value;
        }
        String text = String.valueOf(value).trim().toLowerCase();
        if ("true".equals(text) || "1".equals(text) || "yes".equals(text)) {
            return true;
        }
        if ("false".equals(text) || "0".equals(text) || "no".equals(text)) {
            return false;
        }
        return null;
    }

    private static Float floatOrNull(Object value) {
        if (value == null) {
            return null;
        }
        if (value instanceof Number) {
            return ((Number) value).floatValue();
        }
        try {
            return Float.parseFloat(String.valueOf(value));
        } catch (NumberFormatException e) {
            return null;
        }
    }

    private static Integer intOrNull(Object value) {
        if (value == null) {
            return null;
        }
        if (value instanceof Number) {
            return ((Number) value).intValue();
        }
        try {
            return Integer.parseInt(String.valueOf(value));
        } catch (NumberFormatException e) {
            return null;
        }
    }

    private static String strOrNull(Object value) {
        if (value == null) {
            return null;
        }
        if (value instanceof String) {
            return StringUtils.hasText((String) value) ? (String) value : null;
        }
        return String.valueOf(value);
    }

    private static String normalizeBaseUrl(String baseUrl) {
        if (!StringUtils.hasText(baseUrl)) {
            return "http://localhost:8000";
        }
        return baseUrl.endsWith("/") ? baseUrl.substring(0, baseUrl.length() - 1) : baseUrl;
    }
}
