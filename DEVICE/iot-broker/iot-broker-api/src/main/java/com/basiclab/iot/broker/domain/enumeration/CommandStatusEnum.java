package com.basiclab.iot.broker.domain.enumeration;

import lombok.Getter;

/**
 * @author EasyAIoT
 * @desc
 * @created 2025-06-17
 */
public enum CommandStatusEnum {

    /**
     *  0.未下发 1.已下发 2.已回复
     */
    NOT_DELIVERED(0),
    ALREADY_DELIVERED(1),
    ALREADY_RESPONSE(2),

    ;
    @Getter
    private Integer code;

    CommandStatusEnum(Integer code) {
        this.code = code;
    }


}
