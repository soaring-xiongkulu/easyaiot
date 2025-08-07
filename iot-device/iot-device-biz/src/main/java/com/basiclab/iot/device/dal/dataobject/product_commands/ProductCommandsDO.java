package com.basiclab.iot.device.dal.dataobject.product_commands;

import lombok.*;
import com.baomidou.mybatisplus.annotation.*;
import com.basiclab.iot.common.mybatis.core.dataobject.BaseDO;

/**
 * 产品模型设备服务命令 DO
 *
 * @author BasicLab
 */
@TableName("product_commands")
@KeySequence("product_commands_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ProductCommandsDO extends BaseDO {

    /**
     * 命令id
     */
    @TableId
    private Long id;
    /**
     * 服务ID
     */
    private Long serviceId;
    /**
     * 指示命令的名字，如门磁的LOCK命令、摄像头的VIDEO_RECORD命令，命令名与参数共同构成一个完整的命令。	支持英文大小写、数字及下划线，长度[2,50]。	
     */
    private String name;
    /**
     * 命令描述。
     */
    private String description;
    /**
     * 创建者
     */
    private String createBy;
    /**
     * 更新者
     */
    private String updateBy;

}