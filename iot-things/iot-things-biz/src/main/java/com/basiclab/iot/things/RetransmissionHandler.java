
package com.basiclab.iot.things;

import io.netty.channel.EventLoop;
import io.netty.handler.codec.mqtt.MqttFixedHeader;
import io.netty.handler.codec.mqtt.MqttMessage;
import io.netty.handler.codec.mqtt.MqttMessageType;
import io.netty.handler.codec.mqtt.MqttQoS;
import io.netty.util.concurrent.ScheduledFuture;
import lombok.RequiredArgsConstructor;

import java.util.concurrent.TimeUnit;
import java.util.function.BiConsumer;

@RequiredArgsConstructor
final class RetransmissionHandler<T extends MqttMessage> {

    private volatile boolean stopped;
    private final PendingOperation pendingOperation;
    private ScheduledFuture<?> timer;
    private int timeout = 10;
    private BiConsumer<MqttFixedHeader, T> handler;
    private T originalMessage;

    void start(EventLoop eventLoop) {
        if (eventLoop == null) {
            throw new NullPointerException("eventLoop");
        }
        if (this.handler == null) {
            throw new NullPointerException("handler");
        }
        this.timeout = 10;
        this.startTimer(eventLoop);
    }

    private void startTimer(EventLoop eventLoop) {
        if (stopped || pendingOperation.isCanceled()) {
            return;
        }
        this.timer = eventLoop.schedule(() -> {
            if (stopped || pendingOperation.isCanceled()) {
                return;
            }
            this.timeout += 5;
            boolean isDup = this.originalMessage.fixedHeader().isDup();
            if (this.originalMessage.fixedHeader().messageType() == MqttMessageType.PUBLISH && this.originalMessage.fixedHeader().qosLevel() != MqttQoS.AT_MOST_ONCE) {
                isDup = true;
            }
            MqttFixedHeader fixedHeader = new MqttFixedHeader(this.originalMessage.fixedHeader().messageType(), isDup, this.originalMessage.fixedHeader().qosLevel(), this.originalMessage.fixedHeader().isRetain(), this.originalMessage.fixedHeader().remainingLength());
            handler.accept(fixedHeader, originalMessage);
            startTimer(eventLoop);
        }, timeout, TimeUnit.SECONDS);
    }

    void stop() {
        stopped = true;
        if (this.timer != null) {
            this.timer.cancel(true);
        }
    }

    void setHandle(BiConsumer<MqttFixedHeader, T> runnable) {
        this.handler = runnable;
    }

    void setOriginalMessage(T originalMessage) {
        this.originalMessage = originalMessage;
    }
}
