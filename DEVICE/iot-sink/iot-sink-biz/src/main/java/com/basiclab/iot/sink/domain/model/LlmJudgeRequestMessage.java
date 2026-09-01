package com.basiclab.iot.sink.domain.model;

import com.fasterxml.jackson.annotation.JsonAlias;
import lombok.Data;

import java.util.List;
import java.util.Map;

/**
 * 大模型（LLM）告警研判请求消息（iot-sink 投递独立队列 iot-alert-llm-judge，
 * 由 AlertLlmJudgeConsumer 消费后调用 AI 模块内部研判接口）。
 */
@Data
public class LlmJudgeRequestMessage {

    @JsonAlias("correlation_id")
    private String correlationId;

    @JsonAlias("alert_id")
    private Integer alertId;

    @JsonAlias("task_id")
    private Integer taskId;

    @JsonAlias("task_name")
    private String taskName;

    @JsonAlias("device_id")
    private String deviceId;

    @JsonAlias("device_name")
    private String deviceName;

    @JsonAlias("rule_id")
    private Integer ruleId;

    @JsonAlias("agent_id")
    private Integer agentId;

    @JsonAlias("model_id")
    private Integer modelId;

    /** 判断方式：image=事件时刻图片，video=事件间隔视频 */
    @JsonAlias("judge_mode")
    private String judgeMode;

    private MediaRef media;

    @JsonAlias("prompt_override")
    private String promptOverride;

    @JsonAlias("require_json")
    private Boolean requireJson;

    /** LLM 失败时策略：skip（不改动原结果）/confirm（放行）/reject（抑制） */
    @JsonAlias("fail_policy")
    private String failPolicy;

    /** 是否二次判断门控（true 时通知延迟，待研判结论 confirm 后补发） */
    private Boolean gated;

    /** 门控补发通知所需的原告警消息快照（channels/notify_users 等已补齐） */
    @JsonAlias("notify_payload")
    private Map<String, Object> notifyPayload;

    /** 事件上下文（object/event/detections），供智能体提示词组装 */
    private Map<String, Object> context;

    private String timestamp;

    @Data
    public static class MediaRef {
        @JsonAlias("image_url")
        private String imageUrl;

        @JsonAlias("record_path")
        private String recordPath;

        @JsonAlias("event_time")
        private String eventTime;

        @JsonAlias("pre_seconds")
        private Integer preSeconds;

        @JsonAlias("post_seconds")
        private Integer postSeconds;

        @JsonAlias("max_seconds")
        private Integer maxSeconds;
    }

    /** 供链路日志追溯 */
    public String brief() {
        return "alertId=" + alertId + " deviceId=" + deviceId
                + " ruleId=" + ruleId + " judgeMode=" + judgeMode
                + " correlationId=" + correlationId;
    }
}
