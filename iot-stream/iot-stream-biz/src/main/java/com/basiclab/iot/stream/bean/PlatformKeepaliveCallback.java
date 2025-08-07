package com.basiclab.iot.stream.bean;

public interface PlatformKeepaliveCallback {
    public void run(String platformServerGbId, int failCount);
}
