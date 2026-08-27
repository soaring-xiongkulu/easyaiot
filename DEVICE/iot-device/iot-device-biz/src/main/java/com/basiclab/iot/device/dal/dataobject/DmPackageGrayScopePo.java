package com.basiclab.iot.device.dal.dataobject;

import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.basiclab.iot.common.domain.BaseEntity2;
import lombok.*;

import java.io.Serializable;

/**
 * 灰度范围
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
@EqualsAndHashCode(callSuper = false)
@TableName("device_ota_version_gray_scope")
@KeySequence("device_ota_version_gray_scope_id_seq")
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DmPackageGrayScopePo extends BaseEntity2 implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 主键ID
     */
    @TableId
    private Long id;
    /**
     * 发布记录ID（device_ota_version_publish.id）
     */
    @TableField(value = "publish_id")
    private Long publishId;
    /**
     * 版本包ID（device_ota_pkg.id）
     */
    @TableField(value = "pkg_id")
    private Long pkgId;
    /**
     * 范围类型[1:设备,2:产品]
     */
    @TableField(value = "scope_type")
    private Integer scopeType;
    /**
     * 范围值（设备唯一标识/产品标识）
     */
    @TableField(value = "scope_value")
    private String scopeValue;
}
