package com.basiclab.iot.transform.runtime.dal.dataobject;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;

/** 流转管道。 */
@Data
@EqualsAndHashCode(callSuper = true)
@TableName("transform_flow_pipeline")
public class FlowPipelineDO extends BaseEntity {
    @TableId
    private String id;
    private String pipelineName;
    private String flowType;
    private String fieldMappingId;
    private Boolean enabled;
    private String remark;
}
