package com.basiclab.iot.stream.service.bean;

public interface ErrorCallback<T> {

    void run(int code, String msg, T data);
}
