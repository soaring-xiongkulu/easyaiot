package com.basiclab.iot.transform.core.contract;

/** TRANSFORM 内部 Kafka topic。 */
public final class TransformTopics {
    public static final String DELIVER = "iot_transform_deliver";
    public static final String DLQ = "iot_transform_dlq";
    public static final String ARCHIVE = "iot_transform_archive";

    /** 下行指令：Control / NODE / 管理 API → 各 runtime */
    public static final String COMMAND = "iot_transform_command";

    /** 指令回执：各 runtime → 控制面（按 commandId 汇聚） */
    public static final String COMMAND_ACK = "iot_transform_command_ack";

    /** 上行监测：各 runtime → 中心（并落盘 PG） */
    public static final String TELEMETRY = "iot_transform_telemetry";

    /**
     * 轻量心跳约定：部署验收 / 存活探测专用。
     * 不依赖固定 HTTP 端口；与 TELEMETRY 同源触发，载荷更小。
     */
    public static final String HEARTBEAT = "iot_transform_heartbeat";

    private TransformTopics() {
    }
}
