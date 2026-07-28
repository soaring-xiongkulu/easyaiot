package com.basiclab.iot.transform.core.spi;

import com.basiclab.iot.transform.core.channel.ChannelType;
import com.basiclab.iot.transform.core.envelope.TransformEnvelope;

/**
 * 渠道适配器 SPI：每个渠道模块实现消费侧与/或投递侧。
 * <p>
 * 运行时按配置启用渠道 → 自动 join 该渠道约定 Group → 无状态扩缩。
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public interface TransformChannel {

    ChannelType type();

    /** 本渠道约定的消费 Group（可空：纯投递渠道） */
    default String consumeGroup() {
        return null;
    }

    /** 本渠道约定的投递 Group（可空：纯消费渠道） */
    default String deliverGroup() {
        return null;
    }

    /** 启动并加入约定 Group */
    void join();

    /** 优雅退出 Group */
    void leave();

    /** 投递一条已映射事件（投递侧渠道实现） */
    default void deliver(TransformEnvelope envelope) {
        throw new UnsupportedOperationException(type() + " does not support deliver");
    }

    boolean healthy();
}
