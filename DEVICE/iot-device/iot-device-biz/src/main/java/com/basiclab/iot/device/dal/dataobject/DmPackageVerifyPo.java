package com.basiclab.iot.device.dal.dataobject;

import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.basiclab.iot.common.domain.BaseEntity2;
import lombok.*;

import java.io.Serializable;

/**
 * DmPackageVerifyPo
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
@EqualsAndHashCode(callSuper = false)
@TableName("device_ota_version_verify")
@KeySequence("device_ota_version_verify_id_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DmPackageVerifyPo extends BaseEntity2 implements Serializable {

    private static final long serialVersionUID = 5676634787839834596L;
    /**
     * 主键ID
     */
    @TableId
    private Long id;
    /**
     * 大版本ID(dm_ota_version.id)
     */
    @TableField(value = "version_id")
    private Long versionId;
    /**
     * 包ID(dm_ota_pkg.id)
     */
    @TableField(value = "pkg_id")
    private Long pkgId;
    /**
     * IoT平台唯一码
     */
    @TableField(value = "device_identification")
    private String deviceIdentification;
    /**
     * 设备sn
     */
    @TableField(value = "device_sn")
    private String deviceSn;
    /**
     * 设备版本
     */
    @TableField(value = "device_version")
    private String deviceVersion;
    /**
     * 设备ID(dm_device.id)
     */
    @TableField(value = "device_id")
    private Long deviceId;
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
