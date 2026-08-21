package com.basiclab.iot.node.enums;

import lombok.AllArgsConstructor;
import lombok.Getter;

@Getter
@AllArgsConstructor
public enum NodeStatusEnum {

    PENDING("pending", "待纳管"),
    ONLINE("online", "在线"),
    OFFLINE("offline", "离线"),
    MAINTENANCE("maintenance", "维护中");

    private final String status;
    private final String name;

}
