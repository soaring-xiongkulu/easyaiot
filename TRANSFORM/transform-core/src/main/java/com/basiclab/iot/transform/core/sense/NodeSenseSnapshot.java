package com.basiclab.iot.transform.core.sense;

import lombok.Builder;
import lombok.Data;

/**
 * 节点自感知快照：运行时周期性采集，驱动自适应扩缩与分片认领。
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
@Builder
public class NodeSenseSnapshot {

    private String instanceId;

    private String nodeId;

    private String host;

    /** 本实例已加入的 Group 列表（逗号分隔便于日志） */
    private String joinedGroups;

    private double cpuLoad;

    private long heapUsedMb;

    private long heapMaxMb;

    /** 各消费 Group 最大 lag */
    private long maxConsumerLag;

    /** 投递成功率 0~1 */
    private double deliverSuccessRate;

    private long timestampEpochMs;
}
