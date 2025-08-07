
package com.basiclab.iot.things;

import java.util.regex.Pattern;

final class MqttSubscription {

    private final String topic;
    private final Pattern topicRegex;
    private final MqttHandler handler;

    private final boolean once;

    private boolean called;

    MqttSubscription(String topic, MqttHandler handler, boolean once) {
        if (topic == null) {
            throw new NullPointerException("topic");
        }
        if (handler == null) {
            throw new NullPointerException("handler");
        }
        this.topic = topic;
        this.handler = handler;
        this.once = once;
        this.topicRegex = Pattern.compile(topic.replace("+", "[^/]+").replace("#", ".+") + "$");
    }

    String getTopic() {
        return topic;
    }

    public MqttHandler getHandler() {
        return handler;
    }

    boolean isOnce() {
        return once;
    }

    boolean isCalled() {
        return called;
    }

    boolean matches(String topic) {
        return this.topicRegex.matcher(topic).matches();
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;

        MqttSubscription that = (MqttSubscription) o;

        return once == that.once && topic.equals(that.topic) && handler.equals(that.handler);
    }

    @Override
    public int hashCode() {
        int result = topic.hashCode();
        result = 31 * result + handler.hashCode();
        result = 31 * result + (once ? 1 : 0);
        return result;
    }

    void setCalled(boolean called) {
        this.called = called;
    }
}
