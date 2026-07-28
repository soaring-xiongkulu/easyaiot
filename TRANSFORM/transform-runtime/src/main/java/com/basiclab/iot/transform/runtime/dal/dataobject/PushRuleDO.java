package com.basiclab.iot.transform.runtime.dal.dataobject;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;

/** 推送规则。 */
@Data
@EqualsAndHashCode(callSuper = true)
@TableName("transform_push_rule")
public class PushRuleDO extends BaseEntity {
    @TableId
    private String id;
    private String targetSystemId;
    private String flowType;
    private String deliverChannel;
    private String endpointUrl;
    private String fieldMappingId;
    private Boolean enabled;
    private String requestHeadersJson;
    private String remark;
}
