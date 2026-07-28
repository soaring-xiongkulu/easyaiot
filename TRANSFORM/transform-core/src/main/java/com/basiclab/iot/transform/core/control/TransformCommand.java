package com.basiclab.iot.transform.core.control;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.HashMap;
import java.util.Map;

/**
 * 下行控制指令（Topic: iot_transform_command）。
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class TransformCommand {
    private String commandId;
    /** RELOAD_CONFIG | SET_ROLE | SET_CHANNELS | PING | SHUTDOWN_HINT */
    private String type;
    /** "*" 表示广播 */
    @Builder.Default
    private String targetInstanceId = "*";
    private String targetNodeId;
    @Builder.Default
    private Map<String, Object> payload = new HashMap<>();
    private long issuedAt;
}
