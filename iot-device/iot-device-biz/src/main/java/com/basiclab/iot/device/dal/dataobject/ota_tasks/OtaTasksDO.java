package com.basiclab.iot.device.dal.dataobject.ota_tasks;

import lombok.*;

import java.time.LocalDateTime;

import com.baomidou.mybatisplus.annotation.*;
import com.basiclab.iot.common.mybatis.core.dataobject.BaseDO;

/**
 * OTA升级任务 DO
 *
 * @author BasicLab
 */
@TableName("ota_tasks")
@KeySequence("ota_tasks_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class OtaTasksDO extends BaseDO {

    /**
     * 主键
     */
    @TableId
    private Long id;
    /**
     * 升级包ID，关联ota_upgrades表
     */
    private Long upgradeId;
    /**
     * 任务名称
     */
    private String taskName;
    /**
     * 任务状态(0:待发布、1:进行中、2:已完成、3:已取消)
     */
    private Short taskStatus;
    /**
     * 计划执行时间
     */
    private LocalDateTime scheduledTime;
    /**
     * 任务描述
     */
    private String description;
    /**
     * 描述
     */
    private String remark;
    /**
     * 创建人
     */
    private Long createdBy;
    /**
     * 创建时间
     */
    private LocalDateTime createdTime;
    /**
     * 更新人
     */
    private Long updatedBy;
    /**
     * 更新时间
     */
    private LocalDateTime updatedTime;

}