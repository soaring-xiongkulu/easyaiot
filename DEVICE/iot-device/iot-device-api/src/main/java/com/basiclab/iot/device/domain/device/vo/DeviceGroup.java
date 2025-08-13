package com.basiclab.iot.device.domain.device.vo;

import lombok.*;
import com.baomidou.mybatisplus.annotation.*;
import com.basiclab.iot.common.core.dataobject.BaseDO;

/**
 * 设备分组 DO
 *
 * @author EasyAIoT
 */
@TableName("device_group")
@KeySequence("device_group_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DeviceGroup extends BaseDO {

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