package com.basiclab.iot.device.hooks;

import lombok.Getter;
import lombok.Setter;
import lombok.ToString;

import java.io.Serializable;
import java.util.Map;

/**
 * 连接断开	客户端连接层在准备关闭时
 *
 * @author IoT
 * @description
 * @date 2024/6/14
 */
@ToString
@Setter
@Getter
public class DisconnectedHook extends BaseHook implements Serializable {

    /**
     * 错误原因
     */

    private String reason;

    /**
     * 断开连接时间戳
     */
    private Long disconnectedAt;

    public DisconnectedHook(Map<String, Object> map) {
        super(map);
        this.setReason((String) map.get("reason"));
        this.setDisconnectedAt((Long) map.get("disconnected_at"));
    }
}