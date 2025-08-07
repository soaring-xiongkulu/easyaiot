package com.basiclab.iot.stream.service.bean;

public interface InviteTimeOutCallback {

    void run(int code, String msg); // code: 0 sip超时, 1 收流超时
}
