package com.basiclab.iot.transform.runtime.dal.dataobject;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;

/** 目标系统（MES/ERP/WMS…）。 */
@Data
@EqualsAndHashCode(callSuper = true)
@TableName("transform_target_system")
public class TargetSystemDO extends BaseEntity {
    @TableId
    private String id;
    private String systemName;
    private String connectorType;
    private Boolean enabled;
    private String configJson;
    private String remark;
}
