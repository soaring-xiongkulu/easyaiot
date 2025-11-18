package com.basiclab.iot.device.dal.dataobject;

import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.basiclab.iot.common.domain.BaseEntity2;
import lombok.*;

import java.io.Serializable;

/**
 * DmDeviceLogPo
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
@EqualsAndHashCode(callSuper = false)
@TableName("device_ota_log")
@KeySequence("device_ota_log_id_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DmDeviceLogPo extends BaseEntity2 implements Serializable {

    private static final long serialVersionUID = 8680432594156579274L;
    /**
     * 主键ID
     */
    @TableId
    private Long id;
    /**
     * 包ID(dm_ota_pkg.id)
     */
    @TableField(value = "pkg_id")
    private Long pkgId;
    /**
     * 大版本ID(dm_ota_version.id)
     */
    @TableField(value = "version_id")
    private Long versionId;
    /**
     * 大版本号
     */
    @TableField(value = "device_version")
    private String deviceVersion;
    /**
     * 包版本号
     */
    @TableField(value = "pkg_version")
    private String pkgVersion;
    /**
     * 包名称
     */
    @TableField(value = "pkg_name")
    private String pkgName;
    /**
     * 设备唯一ID
     */
    @TableField(value = "device_identification")
    private String deviceIdentification;
    /**
     * 验证状态[0:未验证,1:验证中,2:验证成功,3:验证失败]
     */
    @TableField(value = "status")
    private Integer status;
    /**
     * 设备日志
     */
    @TableField(value = "device_log")
    private String deviceLog;
}
