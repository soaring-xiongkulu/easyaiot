package com.basiclab.iot.transform.capability.consume;

import com.basiclab.iot.transform.core.envelope.TransformEnvelope;

/**
 * 消费能力：从约定 Group 拉取上游事件并交给下游处理链。
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public interface ConsumeCapability {

    /**
     * 处理一条已归一化事件。
     *
     * @return true 表示可提交位点；false 表示需重试/进入死信策略
     */
    boolean onEnvelope(TransformEnvelope envelope);
}
