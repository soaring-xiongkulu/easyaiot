package com.basiclab.iot.transform.core.envelope;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;
import java.util.HashMap;
import java.util.Map;

/**
 * TRANSFORM 统一事件信封。iot-sink Kafka 消息归一化后进入本结构，再按渠道投递。
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class TransformEnvelope {

    /** 全局唯一，幂等键 */
    private String eventId;

    private String traceId;

    private FlowType flowType;

    private String tenantId;

    private String deviceId;

    /** 原始 Kafka topic（来自 iot-sink） */
    private String sourceTopic;

    /** 原始 method / 业务类型 */
    private String method;

    private Instant eventTime;

    private Instant ingestTime;

    @Builder.Default
    private Map<String, Object> headers = new HashMap<>();

    /** 业务载荷（JSON 可序列化结构） */
    private Object payload;

    /** 分片提示：deviceId / partyId hash */
    private Integer partitionHint;
}
