
package com.basiclab.iot.things;

import io.netty.channel.EventLoop;
import io.netty.handler.codec.mqtt.MqttUnsubscribeMessage;
import io.netty.util.concurrent.Promise;

import java.util.function.Consumer;

final class MqttPendingUnsubscription{

    private final Promise<Void> future;
    private final String topic;

    private final RetransmissionHandler<MqttUnsubscribeMessage> retransmissionHandler;

    MqttPendingUnsubscription(Promise<Void> future, String topic, MqttUnsubscribeMessage unsubscribeMessage, PendingOperation operation) {
        this.future = future;
        this.topic = topic;

        this.retransmissionHandler = new RetransmissionHandler<>(operation);
        this.retransmissionHandler.setOriginalMessage(unsubscribeMessage);
    }

    Promise<Void> getFuture() {
        return future;
    }

    String getTopic() {
        return topic;
    }

    void startRetransmissionTimer(EventLoop eventLoop, Consumer<Object> sendPacket) {
        this.retransmissionHandler.setHandle((fixedHeader, originalMessage) ->
                sendPacket.accept(new MqttUnsubscribeMessage(fixedHeader, originalMessage.variableHeader(), originalMessage.payload())));
        this.retransmissionHandler.start(eventLoop);
    }

    void onUnsubackReceived(){
        this.retransmissionHandler.stop();
    }

    void onChannelClosed(){
        this.retransmissionHandler.stop();
    }
}
