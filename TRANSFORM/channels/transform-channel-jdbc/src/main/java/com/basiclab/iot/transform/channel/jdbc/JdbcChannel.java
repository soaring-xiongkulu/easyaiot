package com.basiclab.iot.transform.channel.jdbc;

import com.basiclab.iot.transform.core.channel.ChannelType;
import com.basiclab.iot.transform.core.envelope.TransformEnvelope;
import com.basiclab.iot.transform.core.group.GroupNames;
import com.basiclab.iot.transform.core.spi.TransformChannel;
import lombok.extern.slf4j.Slf4j;

/**
 * JDBC 渠道：抽/落业务库（ERP/WMS 等），投递 Group 横向扩展写库吞吐。
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Slf4j
public class JdbcChannel implements TransformChannel {

    private volatile boolean joined;

    @Override
    public ChannelType type() {
        return ChannelType.JDBC;
    }

    @Override
    public String deliverGroup() {
        return GroupNames.JDBC_DELIVER;
    }

    @Override
    public void join() {
        joined = true;
        log.info("[JdbcChannel] joined deliver group={}", deliverGroup());
    }

    @Override
    public void leave() {
        joined = false;
    }

    @Override
    public void deliver(TransformEnvelope envelope) {
        log.debug("[JdbcChannel] persist eventId={}", envelope.getEventId());
    }

    @Override
    public boolean healthy() {
        return joined;
    }
}
