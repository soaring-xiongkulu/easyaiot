package com.basiclab.iot.stream.bean;

import lombok.Data;

@Data
public class PlayException extends RuntimeException{
    private int code;
    private String msg;

    public PlayException(int code, String msg) {
        this.code = code;
        this.msg = msg;
    }
}
