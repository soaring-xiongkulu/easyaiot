package com.basiclab.iot.sink.service;

import com.basiclab.iot.sink.domain.model.LlmJudgeRequestMessage;

/**
 * 大模型（LLM）研判执行与回写（运行于独立队列消费者线程）。
 */
public interface LlmJudgeService {

    /**
     * 调用 AI 模块内部研判接口，落库研判结果并回写告警；
     * 门控模式下按结论补发/抑制通知。失败抛出异常触发队列重试。
     */
    void executeAndWriteBack(LlmJudgeRequestMessage request);
}
