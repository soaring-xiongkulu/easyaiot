package com.basiclab.iot.device.dal.dataobject;

import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.basiclab.iot.common.domain.BaseEntity2;
import lombok.*;

import java.io.Serializable;

/**
 * 测试白名单（设备验证名单）
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
@EqualsAndHashCode(callSuper = false)
@TableName("device_ota_version_verify")
@KeySequence("device_ota_version_verify_id_seq")
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DmPackageVerifyPo extends BaseEntity2 implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 主键ID
     */
    @TableId
    private Long id;
    /**
     * 版本包ID（device_ota_pkg.id）
     */
    @TableField(value = "pkg_id")
    private Long pkgId;
    /**
     * 设备唯一标识
     */
    @TableField(value = "device_identification")
    private String deviceIdentification;
    /**
     * 设备名称（冗余展示）
     */
    @TableField(value = "device_name")
    private String deviceName;
    /**
     * 状态[1:有效,0:已移除]
     */
    @TableField(value = "status")
    private Integer status;
    /**
     * 备注
     */
    @TableField(value = "remark")
    private String remark;
}
