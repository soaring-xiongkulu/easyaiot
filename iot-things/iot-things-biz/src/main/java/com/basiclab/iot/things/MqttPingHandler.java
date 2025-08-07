
package com.basiclab.iot.things;

import io.netty.channel.Channel;
import io.netty.channel.ChannelFutureListener;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.ChannelInboundHandlerAdapter;
import io.netty.handler.codec.mqtt.MqttFixedHeader;
import io.netty.handler.codec.mqtt.MqttMessage;
import io.netty.handler.codec.mqtt.MqttMessageType;
import io.netty.handler.codec.mqtt.MqttQoS;
import io.netty.handler.timeout.IdleStateEvent;
import io.netty.util.ReferenceCountUtil;
import io.netty.util.concurrent.ScheduledFuture;
import lombok.extern.slf4j.Slf4j;

import java.util.concurrent.TimeUnit;

@Slf4j
final class MqttPingHandler extends ChannelInboundHandlerAdapter {

    private final int keepaliveSeconds;

    private ScheduledFuture<?> pingRespTimeout;

    MqttPingHandler(int keepaliveSeconds) {
        this.keepaliveSeconds = keepaliveSeconds;
    }

    @Override
    public void channelRead(ChannelHandlerContext ctx, Object msg) throws Exception {
        if (!(msg instanceof MqttMessage)) {
            ctx.fireChannelRead(msg);
            return;
        }
        MqttMessage message = (MqttMessage) msg;
        if (message.fixedHeader().messageType() == MqttMessageType.PINGREQ) {
            this.handlePingReq(ctx.channel());
        } else if (message.fixedHeader().messageType() == MqttMessageType.PINGRESP) {
            this.handlePingResp(ctx.channel());
        } else {
            ctx.fireChannelRead(ReferenceCountUtil.retain(msg));
        }
    }

    @Override
    public void userEventTriggered(ChannelHandlerContext ctx, Object evt) throws Exception {
        super.userEventTriggered(ctx, evt);

        if (evt instanceof IdleStateEvent) {
            IdleStateEvent event = (IdleStateEvent) evt;
            switch (event.state()) {
                case READER_IDLE:
                    log.debug("[{}] No reads were performed for specified period for channel {}", event.state(), ctx.channel().id());
                    this.sendPingReq(ctx.channel());
                    break;
                case WRITER_IDLE:
                    log.debug("[{}] No writes were performed for specified period for channel {}", event.state(), ctx.channel().id());
                    this.sendPingReq(ctx.channel());
                    break;
            }
        }
    }

    private void sendPingReq(Channel channel) {
        log.trace("[{}] Sending ping request", channel.id());
        MqttFixedHeader fixedHeader = new MqttFixedHeader(MqttMessageType.PINGREQ, false, MqttQoS.AT_MOST_ONCE, false, 0);
        channel.writeAndFlush(new MqttMessage(fixedHeader));

        if (this.pingRespTimeout == null) {
            this.pingRespTimeout = channel.eventLoop().schedule(() -> {
                MqttFixedHeader fixedHeader2 = new MqttFixedHeader(MqttMessageType.DISCONNECT, false, MqttQoS.AT_MOST_ONCE, false, 0);
                channel.writeAndFlush(new MqttMessage(fixedHeader2)).addListener(ChannelFutureListener.CLOSE);
                //TODO: what do when the connection is closed ?
            }, this.keepaliveSeconds, TimeUnit.SECONDS);
        }
    }

    private void handlePingReq(Channel channel) {
        log.trace("[{}] Handling ping request", channel.id());
        MqttFixedHeader fixedHeader = new MqttFixedHeader(MqttMessageType.PINGRESP, false, MqttQoS.AT_MOST_ONCE, false, 0);
        channel.writeAndFlush(new MqttMessage(fixedHeader));
    }

    private void handlePingResp(Channel channel) {
        log.trace("[{}] Handling ping response", channel.id());
        if (this.pingRespTimeout != null && !this.pingRespTimeout.isCancelled() && !this.pingRespTimeout.isDone()) {
            this.pingRespTimeout.cancel(true);
            this.pingRespTimeout = null;
        }
    }
}
