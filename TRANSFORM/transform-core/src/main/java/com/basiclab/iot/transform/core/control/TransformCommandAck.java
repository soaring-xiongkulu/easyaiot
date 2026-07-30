package com.basiclab.iot.transform.core.control;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 下行指令回执（Topic: iot_transform_command_ack）。
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class TransformCommandAck {
    private String commandId;
    private String instanceId;
    private String nodeId;
    private String host;
    /** 对应 TransformCommand.type */
    private String type;
    /** OK | ACCEPTED | REQUIRES_RESTART | FAILED | IGNORED */
    private String status;
    private String message;
    private long timestampEpochMs;
}
