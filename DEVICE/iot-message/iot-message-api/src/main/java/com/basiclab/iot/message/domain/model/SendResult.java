package com.basiclab.iot.message.domain.model;

import lombok.Builder;
import lombok.Getter;
import lombok.Setter;
import lombok.ToString;
import lombok.experimental.Tolerate;

/**
 * 发送结果
 */
@Getter
@Setter
@ToString
@Builder
public class SendResult {

    @Tolerate
    public SendResult() {
    }

    private boolean success;

    private String info;

    private String msgName;
}
