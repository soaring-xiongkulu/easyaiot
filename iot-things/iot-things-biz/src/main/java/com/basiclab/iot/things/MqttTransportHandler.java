package com.basiclab.iot.things;

import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.ChannelInboundHandlerAdapter;
import io.netty.handler.codec.mqtt.*;
import io.netty.util.ReferenceCountUtil;
import io.netty.util.concurrent.Future;
import io.netty.util.concurrent.GenericFutureListener;
import lombok.extern.slf4j.Slf4j;

import java.util.List;
import java.util.UUID;

import static io.netty.handler.codec.mqtt.MqttMessageType.*;
import static io.netty.handler.codec.mqtt.MqttQoS.AT_MOST_ONCE;

@Slf4j
public class MqttTransportHandler extends ChannelInboundHandlerAdapter implements GenericFutureListener<Future<? super Void>> {

    private final List<MqttMessageType> eventsFromClient;
    private final UUID sessionId;

    MqttTransportHandler(List<MqttMessageType> eventsFromClient) {
        this.sessionId = UUID.randomUUID();
        this.eventsFromClient = eventsFromClient;
    }

    @Override
    public void channelRead(ChannelHandlerContext ctx, Object msg) {
        log.trace("[{}] Processing msg: {}", sessionId, msg);
        try {
            if (msg instanceof MqttMessage) {
                MqttMessage message = (MqttMessage) msg;
                if (message.decoderResult().isSuccess()) {
                    processMqttMsg(ctx, message);
                } else {
                    log.error("[{}] Message decoding failed: {}", sessionId, message.decoderResult().cause().getMessage());
                    ctx.close();
                }
            } else {
                log.debug("[{}] Received non mqtt message: {}", sessionId, msg.getClass().getSimpleName());
                ctx.close();
            }
        } finally {
            ReferenceCountUtil.safeRelease(msg);
        }
    }

    void processMqttMsg(ChannelHandlerContext ctx, MqttMessage msg) {
        if (msg.fixedHeader() == null) {
            ctx.close();
            return;
        }
        switch (msg.fixedHeader().messageType()) {
            case CONNECT:
                eventsFromClient.add(CONNECT);
                processConnect(ctx, (MqttConnectMessage) msg);
                break;
            case DISCONNECT:
                eventsFromClient.add(DISCONNECT);
                ctx.close();
                break;
            case PUBLISH:
                // QoS 0 and 1 supported only here
                eventsFromClient.add(PUBLISH);
                MqttPublishMessage mqttPubMsg = (MqttPublishMessage) msg;
                ack(ctx, mqttPubMsg.variableHeader().packetId());
                break;
            case SUBSCRIBE:
                eventsFromClient.add(SUBSCRIBE);
                subscribeMsg((MqttConnectMessage) msg);
                break;
            case PINGREQ:
                // We will not handle PINGREQ and will not send any PINGRESP to simulate the MQTT server is down
                eventsFromClient.add(PINGREQ);
                break;
            default:
                break;
        }
    }

    void processConnect(ChannelHandlerContext ctx, MqttConnectMessage msg) {
        String userName = msg.payload().userName();
        String clientId = msg.payload().clientIdentifier();

        log.warn("[{}][{}] Processing connect msg for client: {}!", sessionId, userName, clientId);
        ctx.writeAndFlush(createMqttConnAckMsg(msg));
    }

    void subscribeMsg(MqttConnectMessage msg) {
        MqttConnectPayload payload = msg.payload();
        String _msg = new String(payload.toString());
        log.warn("[{}][{}] subscribeMsg msg : {}!", sessionId, payload.clientIdentifier(),_msg);
    }

    private MqttConnAckMessage createMqttConnAckMsg(MqttConnectMessage msg) {
        MqttFixedHeader mqttFixedHeader =
                new MqttFixedHeader(CONNACK, false, AT_MOST_ONCE, false, 0);
        MqttConnAckVariableHeader mqttConnAckVariableHeader =
                new MqttConnAckVariableHeader(MqttConnectReturnCode.CONNECTION_ACCEPTED, !msg.variableHeader().isCleanSession());
        return new MqttConnAckMessage(mqttFixedHeader, mqttConnAckVariableHeader);
    }

    private void ack(ChannelHandlerContext ctx, int msgId) {
        if (msgId > 0) {
            ctx.writeAndFlush(createMqttPubAckMsg(msgId));
        }
    }

    public static MqttPubAckMessage createMqttPubAckMsg(int requestId) {
        MqttFixedHeader mqttFixedHeader =
                new MqttFixedHeader(PUBACK, false, AT_MOST_ONCE, false, 0);
        MqttMessageIdVariableHeader mqttMsgIdVariableHeader =
                MqttMessageIdVariableHeader.from(requestId);
        return new MqttPubAckMessage(mqttFixedHeader, mqttMsgIdVariableHeader);
    }

    @Override
    public void operationComplete(Future<? super Void> future) {
        log.trace("[{}] Channel closed!", sessionId);
    }
}
