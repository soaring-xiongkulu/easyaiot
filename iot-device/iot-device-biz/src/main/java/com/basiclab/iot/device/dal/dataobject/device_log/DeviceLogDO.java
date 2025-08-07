package com.basiclab.iot.device.dal.dataobject.device_log;

import lombok.*;

import java.time.LocalDateTime;

import com.baomidou.mybatisplus.annotation.*;
import com.basiclab.iot.common.mybatis.core.dataobject.BaseDO;

/**
 * 设备日志 DO
 *
 * @author BasicLab
 */
@TableName("device_log")
@KeySequence("device_log_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DeviceLogDO extends BaseDO {

    /**
     * id
     */
    @TableId
    private Long id;
    /**
     * 设备唯一标识
     */
    private String did;
    /**
     * 文件地址
     */
    private String fileUrl;
    /**
     * 上传时间
     */
    private LocalDateTime uploadTime;
    /**
     * 文件名称
     */
    private String fileName;
    /**
     * 文件大小
     */
    private Long fileSize;
    /**
     * 备注
     */
    private String remark;
    /**
     * 状态[0:成功, 1:未开始, 2:上传中, 3:失败]
     */
    private Short status;
    /**
     * 创建者
     */
    private String createdBy;
    /**
     * 创建时间
     */
    private LocalDateTime createdTime;
    /**
     * 更新者
     */
    private String updatedBy;
    /**
     * 更新时间
     */
    private LocalDateTime updatedTime;

}