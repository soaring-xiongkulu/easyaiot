package com.basiclab.iot.transform.runtime.pipeline;

import com.basiclab.iot.transform.capability.consume.ConsumeCapability;
import com.basiclab.iot.transform.core.channel.ChannelType;
import com.basiclab.iot.transform.core.envelope.TransformEnvelope;
import com.basiclab.iot.transform.core.spi.TransformChannel;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.util.List;

/**
 * 默认消费链：归一化后 fan-out 到已启用的投递渠道（HTTP / Party 等）。
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class DefaultFanOutConsumeCapability implements ConsumeCapability {

    private final List<TransformChannel> transformChannels;

    @Override
    public boolean onEnvelope(TransformEnvelope envelope) {
        for (TransformChannel channel : transformChannels) {
            if (channel.type() == ChannelType.KAFKA) {
                continue;
            }
            if (channel.deliverGroup() == null) {
                continue;
            }
            try {
                channel.deliver(envelope);
            } catch (Exception e) {
                log.warn("[DefaultFanOutConsumeCapability] deliver failed channel={} eventId={}",
                        channel.type(), envelope.getEventId(), e);
                return false;
            }
        }
        return true;
    }
}
