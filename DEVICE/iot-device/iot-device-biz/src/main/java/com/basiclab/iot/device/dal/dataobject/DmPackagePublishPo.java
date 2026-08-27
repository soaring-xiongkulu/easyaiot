package com.basiclab.iot.device.dal.dataobject;

import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.basiclab.iot.common.domain.BaseEntity2;
import lombok.*;

import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * 发布记录（全量/灰度）
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
@EqualsAndHashCode(callSuper = false)
@TableName("device_ota_version_publish")
@KeySequence("device_ota_version_publish_id_seq")
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DmPackagePublishPo extends BaseEntity2 implements Serializable {

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
     * 发布策略[0:全量,1:灰度]
     */
    @TableField(value = "publish_strategy")
    private Integer publishStrategy;
    /**
     * 灰度阶梯[1:设备级,2:产品级,3:全量]
     */
    @TableField(value = "gray_ladder")
    private Integer grayLadder;
    /**
     * 状态[1:已发布,0:已撤销]
     */
    @TableField(value = "status")
    private Integer status;
    /**
     * 发布时间
     */
    @TableField(value = "publish_time")
    private LocalDateTime publishTime;
    /**
     * 撤回原因
     */
    @TableField(value = "withdraw_reason")
    private String withdrawReason;
    /**
     * 撤回时间
     */
    @TableField(value = "withdraw_time")
    private LocalDateTime withdrawTime;
}
