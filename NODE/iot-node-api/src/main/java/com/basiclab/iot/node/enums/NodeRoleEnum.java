package com.basiclab.iot.node.enums;

import lombok.AllArgsConstructor;
import lombok.Getter;

@Getter
@AllArgsConstructor
public enum NodeRoleEnum {

    COMPUTE("compute", "计算节点"),
    GPU("gpu", "GPU 节点"),
    MEDIA("media", "媒体节点"),
    MQTT("mqtt", "MQTT网关节点"),
    STORAGE("storage", "存储节点"),
    HYBRID("hybrid", "混合节点");

    private final String role;
    private final String name;

}
