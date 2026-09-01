package com.basiclab.iot.sink.service.impl;

import com.baomidou.dynamic.datasource.toolkit.DynamicDataSourceContextHolder;
import com.basiclab.iot.common.service.RedisService;
import com.basiclab.iot.common.utils.json.JsonUtils;
import com.basiclab.iot.sink.domain.model.AlertNotificationMessage;
import com.basiclab.iot.sink.domain.model.LlmJudgeRequestMessage;
import com.basiclab.iot.sink.service.LlmJudgeEnricher;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.time.Instant;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 大模型（LLM）后处理规则匹配与投递。
 *
 * 运行于告警主链路：规则缓存命中后仅做内存匹配 + Kafka 异步投递（fire-and-forget），
 * 失败只记日志，绝不影响告警落库与通知。命中二次判断（门控）规则时返回 true，
 * 由调用方延迟通知，待研判结论确认后补发。
 */
@Slf4j
@Service
public class LlmJudgeEnricherImpl implements LlmJudgeEnricher {

    private static final String THROTTLE_KEY_PREFIX = "llm:judge:throttle:";

    @Value("${basiclab.llm-judge.enabled:true}")
    private boolean enabled;

    @Value("${spring.kafka.llm-judge.request-topic:iot-alert-llm-judge}")
    private String requestTopic;

    @Value("${basiclab.llm-judge.rule-cache-ttl-sec:60}")
    private long ruleCacheTtlSec;

    @Autowired(required = false)
    private KafkaTemplate<String, String> iotKafkaTemplate;

    @Autowired(required = false)
    private JdbcTemplate jdbcTemplate;

    @Autowired(required = false)
    private RedisService redisService;

    @Autowired(required = false)
    private ObjectMapper objectMapper;

    private final ConcurrentHashMap<String, CacheEntry> ruleCache = new ConcurrentHashMap<>();

    @Override
    public boolean tryEnqueue(AlertNotificationMessage message, Integer alertId) {
        if (!enabled || message == null || message.getAlert() == null
                || alertId == null || iotKafkaTemplate == null) {
            return false;
        }
        try {
            String deviceId = message.getDeviceId();
            if (!StringUtils.hasText(deviceId)) {
                return false;
            }
            String taskType = message.getAlert().getTaskType();
            if (!StringUtils.hasText(taskType)) {
                taskType = "realtime";
            }
            List<RuleView> rules = loadRules(deviceId, taskType);
            if (rules.isEmpty()) {
                return false;
            }
            RuleView matched = matchRule(rules, message.getAlert());
            if (matched == null) {
                return false;
            }
            if (!selectedBySample(message, matched)) {
                markNotSampled(alertId, matched);
                log.debug("[LlmJudgeEnricher] 比例抽检未命中，跳过研判 alertId={} ruleId={} rate={}%",
                        alertId, matched.ruleId, matched.sampleRatePercent);
                return false;
            }
            String judgeMode = matched.judgeMode;
            String imageUrl = message.getAlert().getImagePath();
            String recordPath = message.getAlert().getRecordPath();
            if (!"video".equalsIgnoreCase(judgeMode)) {
                if (!StringUtils.hasText(imageUrl)) {
                    return false;
                }
            } else if (!StringUtils.hasText(recordPath)) {
                if (!StringUtils.hasText(imageUrl)) {
                    return false;
                }
                judgeMode = "image"; // 录像缺失回退图片研判
            }
            if (matched.minIntervalSec > 0 && !tryThrottle(deviceId, matched.ruleId, matched.minIntervalSec)) {
                markSkipped(alertId, matched, "rate_limited",
                        "已命中比例抽检，但处于最小研判间隔内");
                log.debug("[LlmJudgeEnricher] 规则节流命中，跳过研判 deviceId={} ruleId={}", deviceId, matched.ruleId);
                return false;
            }
            boolean gated = matched.secondaryJudge && hasNotificationConfig(message);
            enqueue(buildRequest(message, alertId, matched, judgeMode, imageUrl, recordPath, gated));
            if (gated) {
                log.info("[LlmJudgeEnricher] 命中门控规则，通知延迟待研判 alertId={} deviceId={} ruleId={}",
                        alertId, deviceId, matched.ruleId);
            } else {
                log.debug("[LlmJudgeEnricher] 已投递 LLM 研判 alertId={} deviceId={} ruleId={} judgeMode={}",
                        alertId, deviceId, matched.ruleId, judgeMode);
            }
            return gated;
        } catch (Exception e) {
            // 主链路零影响：任何异常只记日志，不抛出
            log.warn("[LlmJudgeEnricher] 规则匹配/投递异常（已忽略）: {}", e.getMessage());
            return false;
        }
    }

    private LlmJudgeRequestMessage buildRequest(AlertNotificationMessage message, Integer alertId,
                                                RuleView rule, String judgeMode,
                                                String imageUrl, String recordPath, boolean gated) {
        LlmJudgeRequestMessage request = new LlmJudgeRequestMessage();
        request.setCorrelationId(StringUtils.hasText(message.getCorrelationId())
                ? message.getCorrelationId() : UUID.randomUUID().toString());
        request.setAlertId(alertId);
        request.setTaskId(message.getTaskId());
        request.setTaskName(message.getTaskName());
        request.setDeviceId(message.getDeviceId());
        request.setDeviceName(message.getDeviceName());
        request.setRuleId(rule.ruleId);
        request.setAgentId(rule.agentId);
        request.setModelId(rule.modelId);
        request.setJudgeMode(judgeMode);
        request.setPromptOverride(rule.promptOverride);
        request.setRequireJson(rule.requireJson);
        request.setFailPolicy(rule.failPolicy);
        request.setGated(gated);
        request.setTimestamp(Instant.now().atOffset(ZoneOffset.UTC).format(DateTimeFormatter.ISO_OFFSET_DATE_TIME));

        LlmJudgeRequestMessage.MediaRef media = new LlmJudgeRequestMessage.MediaRef();
        media.setImageUrl(imageUrl);
        media.setRecordPath(recordPath);
        media.setEventTime(message.getAlert().getTime());
        media.setPreSeconds(rule.videoPreSeconds);
        media.setPostSeconds(rule.videoPostSeconds);
        media.setMaxSeconds(rule.videoMaxSeconds);
        request.setMedia(media);

        Map<String, Object> context = new LinkedHashMap<>();
        context.put("object", message.getAlert().getObject());
        context.put("event", message.getAlert().getEvent());
        context.put("detections", extractDetections(message.getAlert().getInformation()));
        request.setContext(context);

        if (gated) {
            Map<String, Object> notifyPayload = new LinkedHashMap<>();
            notifyPayload.put("alertNotificationJson", JsonUtils.toJsonString(message));
            request.setNotifyPayload(notifyPayload);
        }
        return request;
    }

    private void enqueue(LlmJudgeRequestMessage request) {
        try {
            String json = JsonUtils.toJsonString(request);
            iotKafkaTemplate.send(requestTopic, request.getDeviceId(), json);
        } catch (Exception e) {
            log.error("[LlmJudgeEnricher] Kafka 投递失败 topic={} {}: {}",
                    requestTopic, request.brief(), e.getMessage());
        }
    }

    /** Redis 节流：min_interval_sec 内同设备同规则只研判一次 */
    private boolean tryThrottle(String deviceId, Integer ruleId, int minIntervalSec) {
        if (redisService == null) {
            return true;
        }
        try {
            String key = THROTTLE_KEY_PREFIX + deviceId + ":" + ruleId;
            return redisService.setLock(key, UUID.randomUUID().toString(), (long) minIntervalSec);
        } catch (Exception e) {
            log.warn("[LlmJudgeEnricher] 节流 Redis 异常（放行）: {}", e.getMessage());
            return true;
        }
    }

    private List<RuleView> loadRules(String deviceId, String taskType) {
        String cacheKey = deviceId + "|" + taskType;
        long now = System.currentTimeMillis();
        CacheEntry entry = ruleCache.get(cacheKey);
        if (entry != null && now - entry.fetchedAt < ruleCacheTtlSec * 1000) {
            return entry.rules;
        }
        List<RuleView> rules = queryRules(deviceId, taskType);
        ruleCache.put(cacheKey, new CacheEntry(rules, now));
        return rules;
    }

    private List<RuleView> queryRules(String deviceId, String taskType) {
        List<RuleView> rules = new ArrayList<>();
        if (jdbcTemplate == null) {
            return rules;
        }
        try {
            DynamicDataSourceContextHolder.push("video");
            List<Map<String, Object>> rows = jdbcTemplate.queryForList(
                    "SELECT r.id, r.match_objects, r.match_events, r.agent_id, r.model_id, "
                            + "r.judge_mode, r.video_pre_seconds, r.video_post_seconds, r.video_max_seconds, "
                            + "r.secondary_judge, r.fail_policy, r.prompt_override, r.require_json, "
                            + "r.sample_rate_percent, r.min_interval_sec "
                            + "FROM algorithm_task_llm_rule r "
                            + "INNER JOIN algorithm_task at ON at.id = r.task_id "
                            + "INNER JOIN algorithm_task_device atd ON atd.task_id = at.id "
                            + "WHERE atd.device_id = ? AND at.task_type = ? "
                            + "AND at.is_enabled = true AND at.alert_event_enabled = true "
                            + "AND at.llm_post_process_enabled = true AND r.enabled = true "
                            + "ORDER BY r.priority DESC, r.id ASC",
                    deviceId, taskType);
            for (Map<String, Object> row : rows) {
                RuleView rule = toRuleView(row);
                if (rule != null) {
                    rules.add(rule);
                }
            }
        } catch (Exception e) {
            log.warn("[LlmJudgeEnricher] 查询 LLM 规则失败 deviceId={}: {}", deviceId, e.getMessage());
        } finally {
            DynamicDataSourceContextHolder.clear();
        }
        return rules;
    }

    private RuleView toRuleView(Map<String, Object> row) {
        try {
            RuleView rule = new RuleView();
            Object id = row.get("id");
            rule.ruleId = id instanceof Number ? ((Number) id).intValue() : Integer.parseInt(String.valueOf(id));
            rule.matchObjects = parseStringArray(row.get("match_objects"));
            rule.matchEvents = parseStringArray(row.get("match_events"));
            rule.agentId = intOf(row.get("agent_id"));
            rule.modelId = intOf(row.get("model_id"));
            Object mode = row.get("judge_mode");
            rule.judgeMode = mode != null ? String.valueOf(mode) : "image";
            rule.videoPreSeconds = intOf(row.get("video_pre_seconds"), 5);
            rule.videoPostSeconds = intOf(row.get("video_post_seconds"), 10);
            rule.videoMaxSeconds = intOf(row.get("video_max_seconds"), 30);
            rule.secondaryJudge = boolOf(row.get("secondary_judge"), false);
            Object fail = row.get("fail_policy");
            rule.failPolicy = fail != null ? String.valueOf(fail) : "skip";
            Object prompt = row.get("prompt_override");
            rule.promptOverride = prompt != null ? String.valueOf(prompt) : null;
            rule.requireJson = boolOf(row.get("require_json"), true);
            rule.sampleRatePercent = intOf(row.get("sample_rate_percent"), 10);
            rule.minIntervalSec = intOf(row.get("min_interval_sec"), 0);
            return rule;
        } catch (Exception e) {
            log.warn("[LlmJudgeEnricher] 规则解析失败: {}", e.getMessage());
            return null;
        }
    }

    private RuleView matchRule(List<RuleView> rules, AlertNotificationMessage.AlertInfo alert) {
        for (RuleView rule : rules) {
            if (rule.matchObjects != null && !rule.matchObjects.isEmpty()) {
                if (!matchesObjects(rule.matchObjects, alert)) {
                    continue;
                }
            }
            if (rule.matchEvents != null && !rule.matchEvents.isEmpty()) {
                if (alert.getEvent() == null
                        || !rule.matchEvents.contains(alert.getEvent().toLowerCase())) {
                    continue;
                }
            }
            return rule;
        }
        return null;
    }

    /**
     * 稳定比例抽检：同一 correlationId 在重复投递/重放时始终得到相同选择结果，
     * 避免随机数导致重复调用或审计口径漂移。
     */
    private boolean selectedBySample(AlertNotificationMessage message, RuleView rule) {
        int rate = rule.sampleRatePercent == null ? 10 : Math.max(1, Math.min(100, rule.sampleRatePercent));
        if (rate >= 100) {
            return true;
        }
        String identity = StringUtils.hasText(message.getCorrelationId())
                ? message.getCorrelationId()
                : String.valueOf(message.getDeviceId()) + "|" + message.getAlert().getTime();
        int bucket = Math.floorMod((identity + "|" + rule.ruleId).hashCode(), 100);
        return bucket < rate;
    }

    /** 未抽中的告警也明确标记，前端可区分“未抽检”和“研判尚未返回”。 */
    private void markNotSampled(Integer alertId, RuleView rule) {
        markSkipped(alertId, rule, "not_sampled", "未命中本次比例抽检，不调用大模型");
    }

    private void markSkipped(Integer alertId, RuleView rule, String status, String reason) {
        if (jdbcTemplate == null || alertId == null) {
            return;
        }
        try {
            DynamicDataSourceContextHolder.push("video");
            Map<String, Object> detail = new LinkedHashMap<>();
            detail.put("status", status);
            detail.put("rule_id", rule.ruleId);
            detail.put("sample_rate_percent", rule.sampleRatePercent);
            detail.put("reason", reason);
            jdbcTemplate.update(
                    "UPDATE alert SET llm_judge_status = ?, llm_judge_detail = ? WHERE id = ?",
                    status, JsonUtils.toJsonString(detail), alertId);
        } catch (Exception e) {
            log.warn("[LlmJudgeEnricher] 写入未抽检状态失败 alertId={}: {}", alertId, e.getMessage());
        } finally {
            DynamicDataSourceContextHolder.clear();
        }
    }

    private boolean matchesObjects(List<String> matchObjects, AlertNotificationMessage.AlertInfo alert) {
        String objectName = alert.getObject();
        if (objectName != null && matchObjects.contains(objectName.toLowerCase())) {
            return true;
        }
        List<Map<String, Object>> detections = extractDetections(alert.getInformation());
        for (Map<String, Object> det : detections) {
            Object raw = det.get("class_name");
            if (raw == null) {
                raw = det.get("className");
            }
            if (raw != null && matchObjects.contains(String.valueOf(raw).toLowerCase())) {
                return true;
            }
        }
        return false;
    }

    @SuppressWarnings("unchecked")
    private List<Map<String, Object>> extractDetections(Object information) {
        if (information == null) {
            return List.of();
        }
        try {
            Map<String, Object> infoMap;
            if (information instanceof Map) {
                infoMap = (Map<String, Object>) information;
            } else if (information instanceof String) {
                if (objectMapper == null) {
                    return List.of();
                }
                infoMap = objectMapper.readValue((String) information, Map.class);
            } else {
                return List.of();
            }
            Object detectionsObj = infoMap.get("detections");
            if (detectionsObj instanceof List) {
                List<Map<String, Object>> out = new ArrayList<>();
                for (Object item : (List<?>) detectionsObj) {
                    if (item instanceof Map) {
                        out.add((Map<String, Object>) item);
                    }
                }
                return out;
            }
        } catch (Exception ignored) {
            // 解析失败视为无检测明细
        }
        return List.of();
    }

    private List<String> parseStringArray(Object raw) {
        if (raw == null) {
            return null;
        }
        String text = String.valueOf(raw);
        if (!StringUtils.hasText(text)) {
            return null;
        }
        try {
            if (objectMapper == null) {
                return null;
            }
            JsonNode node = objectMapper.readTree(text);
            if (!node.isArray()) {
                return null;
            }
            List<String> out = new ArrayList<>();
            for (JsonNode item : node) {
                if (item.isTextual()) {
                    out.add(item.asText().toLowerCase());
                }
            }
            return out.isEmpty() ? null : out;
        } catch (Exception e) {
            log.warn("[LlmJudgeEnricher] match_objects/events 解析失败: {}", e.getMessage());
            return null;
        }
    }

    /** 与通知发送侧一致的判断：有人或存在免人渠道（HTTP/Webhook/群机器人） */
    private boolean hasNotificationConfig(AlertNotificationMessage message) {
        List<Map<String, Object>> channels = message.getChannels();
        List<Map<String, Object>> notifyUsers = message.getNotifyUsers();
        if (channels == null || channels.isEmpty()) {
            return false;
        }
        if (notifyUsers != null && !notifyUsers.isEmpty()) {
            return true;
        }
        for (Map<String, Object> channel : channels) {
            if (Boolean.TRUE.equals(channel.get("userless"))) {
                return true;
            }
            Object method = channel.get("method");
            if (method == null) {
                continue;
            }
            String m = String.valueOf(method).toLowerCase();
            if ("http".equals(m) || "webhook".equals(m)) {
                return true;
            }
            Object templateId = channel.get("template_id");
            if (templateId != null && ("wxcp".equals(m) || "wechat".equals(m) || "weixin".equals(m)
                    || "ding".equals(m) || "dingtalk".equals(m)
                    || "feishu".equals(m) || "lark".equals(m))) {
                return true;
            }
        }
        return false;
    }

    private static Integer intOf(Object value) {
        return intOf(value, null);
    }

    private static Integer intOf(Object value, Integer fallback) {
        if (value == null) {
            return fallback;
        }
        if (value instanceof Number) {
            return ((Number) value).intValue();
        }
        try {
            return Integer.parseInt(String.valueOf(value));
        } catch (NumberFormatException e) {
            return fallback;
        }
    }

    private static boolean boolOf(Object value, boolean fallback) {
        if (value == null) {
            return fallback;
        }
        if (value instanceof Boolean) {
            return (Boolean) value;
        }
        return Boolean.parseBoolean(String.valueOf(value));
    }

    private static final class RuleView {
        Integer ruleId;
        List<String> matchObjects;
        List<String> matchEvents;
        Integer agentId;
        Integer modelId;
        String judgeMode;
        Integer videoPreSeconds;
        Integer videoPostSeconds;
        Integer videoMaxSeconds;
        boolean secondaryJudge;
        String failPolicy;
        String promptOverride;
        Boolean requireJson;
        Integer sampleRatePercent;
        Integer minIntervalSec;
    }

    private static final class CacheEntry {
        final List<RuleView> rules;
        final long fetchedAt;

        CacheEntry(List<RuleView> rules, long fetchedAt) {
            this.rules = rules;
            this.fetchedAt = fetchedAt;
        }
    }
}
