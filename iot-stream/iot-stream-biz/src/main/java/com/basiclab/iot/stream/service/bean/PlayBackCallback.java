package com.basiclab.iot.stream.service.bean;

public interface PlayBackCallback<T> {

    void call(PlayBackResult<T> msg);

}
