package com.basiclab.iot.device.dal.dataobject.ota_records;

import lombok.*;

import java.time.LocalDateTime;

import com.baomidou.mybatisplus.annotation.*;
import com.basiclab.iot.common.mybatis.core.dataobject.BaseDO;

/**
 * OTA升级记录 DO
 *
 * @author BasicLab
 */
@TableName("ota_records")
@KeySequence("ota_records_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class OtaRecordsDO extends BaseDO {

    /**
     * 主键
     */
    @TableId
    private Long id;
    /**
     * 任务ID，关联ota_upgrade_tasks表
     */
    private Long taskId;
    /**
     * 设备标识
     */
    private String did;
    /**
     * 升级状态(0:待升级、1:升级中、2:升级成功、3:升级失败)
     */
    private Short upgradeStatus;
    /**
     * 升级进度（百分比）
     */
    private Short progress;
    /**
     * 错误代码
     */
    private String errorCode;
    /**
     * 错误信息
     */
    private String errorMessage;
    /**
     * 升级开始时间
     */
    private LocalDateTime startTime;
    /**
     * 升级结束时间
     */
    private LocalDateTime endTime;
    /**
     * 升级成功详细信息
     */
    private String successDetails;
    /**
     * 升级失败详细信息
     */
    private String failureDetails;
    /**
     * 升级过程日志
     */
    private String logDetails;
    /**
     * 描述
     */
    private String remark;
    /**
     * 记录创建时间
     */
    private LocalDateTime createdTime;
    /**
     * 创建人
     */
    private Long createdBy;
    /**
     * 更新人
     */
    private Long updatedBy;
    /**
     * 更新时间
     */
    private LocalDateTime updatedTime;

}