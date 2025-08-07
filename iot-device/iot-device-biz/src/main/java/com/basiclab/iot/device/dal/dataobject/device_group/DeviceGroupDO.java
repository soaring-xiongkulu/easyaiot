package com.basiclab.iot.device.dal.dataobject.device_group;

import lombok.*;
import com.baomidou.mybatisplus.annotation.*;
import com.basiclab.iot.common.mybatis.core.dataobject.BaseDO;

/**
 * 设备分组 DO
 *
 * @author BasicLab
 */
@TableName("device_group")
@KeySequence("device_group_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DeviceGroupDO extends BaseDO {

    /**
     * 设备ID
     */
    @TableId
    private Long id;
    /**
     * 分组ID
     */
    private String groupName;
    /**
     * 创建者
     */
    private String createBy;
    /**
     * 更新者
     */
    private String updateBy;

}