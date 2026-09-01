package com.basiclab.iot.sink.service;

import com.basiclab.iot.sink.domain.model.AlertNotificationMessage;

/**
 * 大模型（LLM）后处理规则匹配与投递（运行于告警主链路，必须保持毫秒级、零阻塞）。
 */
public interface LlmJudgeEnricher {

    /**
     * 规则匹配命中后投递 LLM 研判独立队列（fire-and-forget，失败仅记日志）。
     *
     * @return true 表示命中二次判断门控规则（通知应延迟，等待研判结论）
     */
    boolean tryEnqueue(AlertNotificationMessage message, Integer alertId);
}
