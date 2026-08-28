package com.basiclab.iot.flow.dal.dataobject;

import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.basiclab.iot.common.core.db.TenantBaseDO;
import com.basiclab.iot.common.core.type.LongListTypeHandler;
import lombok.Data;
import lombok.EqualsAndHashCode;

import java.util.List;

/**
 * 审批用户组（候选人策略 USER_GROUP）
 */
@TableName(value = "flow_user_group", autoResultMap = true)
@KeySequence("flow_user_group_seq")
@Data
@EqualsAndHashCode(callSuper = true)
public class FlowUserGroupDO extends TenantBaseDO {

    @TableId
    private Long id;
    /** 用户组名称 */
    private String name;
    /** 描述 */
    private String description;
    /** 成员用户 ID 列表 */
    @TableField(typeHandler = LongListTypeHandler.class)
    private List<Long> memberUserIds;
    /** 状态：0 开启 / 1 关闭 */
    private Integer status;

}
