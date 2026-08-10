package com.basiclab.iot.video.exception;

import lombok.Getter;

@Getter
public class VideoBusinessException extends RuntimeException {

    private final int code;

    public VideoBusinessException(int code, String message) {
        super(message);
        this.code = code;
    }
}
