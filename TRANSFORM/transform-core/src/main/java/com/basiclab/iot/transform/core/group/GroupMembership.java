package com.basiclab.iot.transform.core.group;

import lombok.Builder;
import lombok.Data;

import java.time.Instant;
import java.util.Set;

/**
 * Group 成员视图：实例加入/离开后的自感知记录（权威状态在 Kafka consumer group / 协调层）。
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
@Builder
public class GroupMembership {

    private String groupId;

    private String instanceId;

    private Set<String> assignedPartitions;

    private Instant joinedAt;

    private boolean active;
}
