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
 * 升级记录（检测/命中/下载/校验/安装/启动 全链路）
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
@EqualsAndHashCode(callSuper = false)
@TableName("device_ota_upgrade_record")
@KeySequence("device_ota_upgrade_record_id_seq")
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DmUpgradeRecordPo extends BaseEntity2 implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 主键ID
     */
    @TableId
    private Long id;
    /**
     * 版本包ID（device_ota_pkg.id，可空）
     */
    @TableField(value = "pkg_id")
    private Long pkgId;
    /**
     * 包类型[0:软件包,1:固件包,2:APP包,3:PC包]
     */
    @TableField(value = "type")
    private Integer type;
    /**
     * 设备唯一标识
     */
    @TableField(value = "device_identification")
    private String deviceIdentification;
    /**
     * 设备名称
     */
    @TableField(value = "device_name")
    private String deviceName;
    /**
     * 产品标识
     */
    @TableField(value = "product_identification")
    private String productIdentification;
    /**
     * 升级前版本
     */
    @TableField(value = "from_version")
    private String fromVersion;
    /**
     * 升级目标版本
     */
    @TableField(value = "to_version")
    private String toVersion;
    /**
     * 通道[1:测试,2:正式]
     */
    @TableField(value = "channel")
    private Integer channel;
    /**
     * 升级阶段[0:检测,1:命中,2:下载完成,3:下载失败,4:MD5校验失败,5:安装结果,6:启动成功]
     */
    @TableField(value = "phase")
    private Integer phase;
    /**
     * 升级进度（0-100）
     */
    @TableField(value = "progress")
    private Integer progress;
    /**
     * 是否成功[0:否,1:是]
     */
    @TableField(value = "success")
    private Integer success;
    /**
     * 错误码
     */
    @TableField(value = "error_code")
    private String errorCode;
    /**
     * 错误信息
     */
    @TableField(value = "error_msg")
    private String errorMsg;
    /**
     * 升级耗时（毫秒）
     */
    @TableField(value = "cost_ms")
    private Long costMs;
    /**
     * 升级发生时间
     */
    @TableField(value = "upgrade_time")
    private LocalDateTime upgradeTime;
}
