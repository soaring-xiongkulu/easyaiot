package com.basiclab.iot.device.dal.dataobject.ota_packages;

import lombok.*;

import java.time.LocalDateTime;

import com.baomidou.mybatisplus.annotation.*;
import com.basiclab.iot.common.mybatis.core.dataobject.BaseDO;

/**
 * OTA升级包 DO
 *
 * @author BasicLab
 */
@TableName("ota_packages")
@KeySequence("ota_packages_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class OtaPackagesDO extends BaseDO {

    /**
     * 主键
     */
    @TableId
    private Long id;
    /**
     * 应用ID
     */
    private String appId;
    /**
     * 包名称
     */
    private String packageName;
    /**
     * 升级包类型(0:软件包、1:固件包)
     */
    private Short packageType;
    /**
     * 产品标识
     */
    private String productIdentification;
    /**
     * 升级包版本号
     */
    private String version;
    /**
     * 升级包的位置
     */
    private String fileLocation;
    /**
     * 状态
     */
    private Short status;
    /**
     * 升级包功能描述
     */
    private String description;
    /**
     * 自定义信息
     */
    private String customInfo;
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