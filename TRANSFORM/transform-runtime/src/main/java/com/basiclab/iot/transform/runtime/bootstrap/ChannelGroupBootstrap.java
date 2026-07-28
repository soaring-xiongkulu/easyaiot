package com.basiclab.iot.transform.runtime.bootstrap;

import com.basiclab.iot.transform.capability.sense.SenseCapability;
import com.basiclab.iot.transform.core.sense.NodeSenseSnapshot;
import com.basiclab.iot.transform.core.spi.TransformChannel;
import com.basiclab.iot.transform.runtime.config.TransformRuntimeProperties;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.context.event.ContextClosedEvent;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.stream.Collectors;

/**
 * 启动时按启用渠道自动 join 约定 Group；关闭时 leave。
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class ChannelGroupBootstrap implements ApplicationRunner {

    private final List<TransformChannel> transformChannels;
    private final SenseCapability senseCapability;
    private final TransformRuntimeProperties properties;

    @Override
    public void run(ApplicationArguments args) {
        for (TransformChannel channel : transformChannels) {
            channel.join();
            log.info("[ChannelGroupBootstrap] channel={} consumeGroup={} deliverGroup={}",
                    channel.type(), channel.consumeGroup(), channel.deliverGroup());
        }
        NodeSenseSnapshot snap = senseCapability.sense();
        snap.setNodeId(properties.getNodeId());
        snap.setJoinedGroups(transformChannels.stream()
                .map(c -> {
                    String cg = c.consumeGroup();
                    String dg = c.deliverGroup();
                    if (cg != null && dg != null) {
                        return cg + "," + dg;
                    }
                    return cg != null ? cg : dg;
                })
                .filter(s -> s != null && !s.isBlank())
                .collect(Collectors.joining(";")));
        log.info("[ChannelGroupBootstrap] instance ready, sense={}", snap);
    }

    @EventListener(ContextClosedEvent.class)
    public void leaveAll() {
        for (TransformChannel channel : transformChannels) {
            try {
                channel.leave();
            } catch (Exception e) {
                log.warn("[ChannelGroupBootstrap] leave failed: {}", channel.type(), e);
            }
        }
    }
}
