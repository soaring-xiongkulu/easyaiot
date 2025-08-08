package com.basiclab.iot.common.domain;

import lombok.Data;

@Data
public class PageRequest {
    private Integer current;
    private Integer size;
}
