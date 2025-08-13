package com.basiclab.iot.device.dal.dataobject;

import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.basiclab.iot.common.domain.BaseEntity2;
import lombok.*;

import java.io.Serializable;

/**
 * @author IoT
 * @desc
 * @created 2024-05-27
 */
@Data
@EqualsAndHashCode(callSuper = false)
@TableName("device_ota_version")
@KeySequence("device_ota_version_id_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DmOtaVersionPo extends BaseEntity2 implements Serializable {

    private static final long serialVersionUID = 2043891425456744097L;
    /**
     * 主键ID
     */
    @TableId
    private Long id;
    /**
     * 大版本号
     */
    @TableField(value = "device_version")
    private String deviceVersion;
    /**
     * 产品标识
     */
    @TableField(value = "product_identification")
    private String productIdentification;
    /**
     * 软件升级包(dm_ota_pkg.id)
     */
    @TableField(value = "app_pkg_id")
    private Long appPkgId;
    /**
     * 固件升级包(dm_ota_pkg.id)
     */
    @TableField(value = "os_pkg_id")
    private Long osPkgId;
    /**
     * 升级方式[0:非强制升级,1:强制升级]
     */
    @TableField(value = "upgrade_mode")
    private Integer upgradeMode;
    /**
     * 状态[0:未验证,1:已验证,2:已发布,3:待发布]
     */
    @TableField(value = "status")
    private Integer status;
    /**
     * 升级描述
     */
    @TableField(value = "remark")
    private String remark;
}
