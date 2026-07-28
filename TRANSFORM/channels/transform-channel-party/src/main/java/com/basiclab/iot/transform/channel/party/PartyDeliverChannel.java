package com.basiclab.iot.transform.channel.party;

import com.basiclab.iot.transform.core.channel.ChannelType;
import com.basiclab.iot.transform.core.envelope.TransformEnvelope;
import com.basiclab.iot.transform.core.group.GroupNames;
import com.basiclab.iot.transform.core.spi.TransformChannel;
import com.basiclab.iot.transform.core.spi.PartyConnector;
import lombok.extern.slf4j.Slf4j;

import java.util.List;
import java.util.Map;
/**
 * N 方业务系统聚合渠道：MES / ERP / CRM / WMS / OA / … 连接器入口。
 * <p>
 * 所有 Party 投递共享 {@link GroupNames#PARTY_DELIVER}，实例增减自动扩展投递并行度；
 * 单 Party 失败隔离，不影响同 Group 其他目标。
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Slf4j
public class PartyDeliverChannel implements TransformChannel {

    private volatile boolean joined;
    private final List<PartyConnector> connectors;

    public PartyDeliverChannel(List<PartyConnector> connectors) {
        this.connectors = connectors;
    }

    @Override
    public ChannelType type() {
        return ChannelType.PARTY;
    }

    @Override
    public String deliverGroup() {
        return GroupNames.PARTY_DELIVER;
    }

    @Override
    public void join() {
        joined = true;
        log.info("[PartyDeliverChannel] joined deliver group={}", deliverGroup());
    }

    @Override
    public void leave() {
        joined = false;
    }

    @Override
    public void deliver(TransformEnvelope envelope) {
        String type = String.valueOf(envelope.getHeaders().get("partyType"));
        PartyConnector connector = connectors.stream().filter(c -> c.type().equals(type)).findFirst()
                .orElseThrow(() -> new IllegalArgumentException("unsupported party connector: " + type));
        Object contract = envelope.getHeaders().get("contract");
        if (!(contract instanceof Map)) {
            throw new IllegalArgumentException("party contract is required");
        }
        try {
            connector.deliver((Map<String, Object>) contract, envelope);
        } catch (Exception e) {
            throw new IllegalStateException("party delivery failed", e);
        }
    }

    @Override
    public boolean healthy() {
        return joined;
    }
}
