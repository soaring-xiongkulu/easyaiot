package com.basiclab.iot.device.dal.dataobject;

import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.basiclab.iot.common.domain.BaseEntity2;
import lombok.*;

import java.io.Serializable;

/**
 * 设备版本档案（产品+设备版本号 → 升级包绑定）
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
@EqualsAndHashCode(callSuper = false)
@TableName("device_ota_version")
@KeySequence("device_ota_version_id_seq")
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DmDeviceVersionPo extends BaseEntity2 implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 主键ID
     */
    @TableId
    private Long id;
    /**
     * 设备版本号
     */
    @TableField(value = "device_version")
    private String deviceVersion;
    /**
     * 所属产品标识
     */
    @TableField(value = "product_identification")
    private String productIdentification;
    /**
     * 软件包ID（device_ota_pkg.id）
     */
    @TableField(value = "app_pkg_id")
    private Long appPkgId;
    /**
     * 固件包ID（device_ota_pkg.id）
     */
    @TableField(value = "os_pkg_id")
    private Long osPkgId;
    /**
     * 升级方式[0:非强制升级,1:强制升级]
     */
    @TableField(value = "upgrade_mode")
    private Integer upgradeMode;
    /**
     * 升级描述
     */
    @TableField(value = "remark")
    private String remark;
}
