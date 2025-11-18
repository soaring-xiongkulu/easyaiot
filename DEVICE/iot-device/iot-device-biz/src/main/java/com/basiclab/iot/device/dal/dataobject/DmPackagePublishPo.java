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
 * DmPackagePublishPo
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
@EqualsAndHashCode(callSuper = false)
@TableName("device_ota_version_publish")
@KeySequence("device_ota_version_publish_id_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DmPackagePublishPo extends BaseEntity2 implements Serializable {

    private static final long serialVersionUID = -5700239481080847068L;
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
     * 发布模式[0:立即发布,1:定时发布]
     */
    @TableField(value = "publish_mode")
    private Integer publishMode;
    /**
     * 定时时间
     */
    @TableField(value = "schedule_time")
    private LocalDateTime scheduleTime;
    /**
     * 发布时间
     */
    @TableField(value = "publish_time")
    private LocalDateTime publishTime;
    /**
     * 是否灰度发布 0：否，1：是
     */
    @TableField(value = "is_gray")
    private Integer isGray;
    /**
     * 状态[0:已撤消,1:已发布,2:待发布]
     */
    @TableField(value = "status")
    private Integer status;
}
