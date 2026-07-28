package com.basiclab.iot.transform.runtime.dal.dataobject;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;

import java.time.Instant;

/** 推送记录（Transactional Outbox）。 */
@Data
@EqualsAndHashCode(callSuper = true)
@TableName("transform_push_record")
public class PushRecordDO extends BaseEntity {
    @TableId
    private String id;
    private String eventId;
    private String targetSystemId;
    private String pushRuleId;
    private String deliverChannel;
    private String pushStatus;
    private Integer attemptCount;
    private String lastError;
    private String envelopeJson;
    private Instant nextRetryTime;
    private Instant relayedAt;
}
