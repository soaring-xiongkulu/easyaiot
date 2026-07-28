package com.basiclab.iot.transform.runtime.dal.dataobject;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;

/** 字段映射（数据转换）。 */
@Data
@EqualsAndHashCode(callSuper = true)
@TableName("transform_field_mapping")
public class FieldMappingDO extends BaseEntity {
    @TableId
    private String id;
    private String mappingName;
    private String fieldBindingsJson;
    private Boolean enabled;
    private String remark;
}
