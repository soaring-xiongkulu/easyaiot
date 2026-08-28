package com.basiclab.iot.flow.dal.dataobject;

import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.basiclab.iot.common.core.db.TenantBaseDO;
import lombok.Data;
import lombok.EqualsAndHashCode;

/**
 * 流程分类
 */
@TableName("flow_category")
@KeySequence("flow_category_seq")
@Data
@EqualsAndHashCode(callSuper = true)
public class FlowCategoryDO extends TenantBaseDO {

    @TableId
    private Long id;
    /** 分类名称 */
    private String name;
    /** 分类编码（唯一） */
    private String code;
    /** 状态：0 开启 / 1 关闭 */
    private Integer status;
    /** 排序 */
    private Integer sort;
    /** 描述 */
    private String description;

}
