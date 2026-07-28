package com.basiclab.iot.transform.runtime.dal.dataobject;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;

/** 推送失败台账。 */
@Data
@EqualsAndHashCode(callSuper = true)
@TableName("transform_push_failure")
public class PushFailureDO extends BaseEntity {
    @TableId
    private String id;
    private String failureSource;
    private String pushRecordId;
    private String failureReason;
    private String envelopeJson;
}
