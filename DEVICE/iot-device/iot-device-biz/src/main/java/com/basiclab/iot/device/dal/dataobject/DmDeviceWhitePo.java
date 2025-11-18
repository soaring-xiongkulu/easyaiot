package com.basiclab.iot.device.dal.dataobject;

import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.basiclab.iot.common.domain.BaseEntity2;
import lombok.*;

import java.io.Serializable;

/**
 * DmDeviceWhitePo
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
@EqualsAndHashCode(callSuper = false)
@TableName("device_ota_white")
@KeySequence("device_ota_white_id_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DmDeviceWhitePo extends BaseEntity2 implements Serializable {

    private static final long serialVersionUID = -7916517661889666118L;
    /**
     * 主键ID
     */
    @TableId
    private Long id;
    /**
     * 包ID(dm_ota_pkg.id)
     */
    private Long pkgId;
    /**
     * 产品唯一ID
     */
    private String productIdentification;
    /**
     * 组ID(device_ota_white_group.id)
     */
    private Long groupId;
    /**
     * 设备唯一ID
     */
    private String deviceIdentification;
    /**
     * 设备sn
     */
    private String deviceSn;
    /**
     * 设备ID(device.id)
     */
    private Long deviceId;
}
