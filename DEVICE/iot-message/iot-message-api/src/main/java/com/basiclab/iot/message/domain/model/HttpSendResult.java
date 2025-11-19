package com.basiclab.iot.message.domain.model;

import com.basiclab.iot.message.domain.model.SendResult;
import lombok.Getter;
import lombok.Setter;
import lombok.ToString;

/**
 * HttpSendResult
 */
@Getter
@Setter
@ToString
public class HttpSendResult extends SendResult {
    private String headers;

    private String body;

    private String cookies;
}
