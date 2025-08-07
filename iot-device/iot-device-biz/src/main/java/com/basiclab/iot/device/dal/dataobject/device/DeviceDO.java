package com.basiclab.iot.device.dal.dataobject.device;

import lombok.*;

import java.time.LocalDateTime;
import java.math.BigDecimal;

import com.baomidou.mybatisplus.annotation.*;
import com.basiclab.iot.common.mybatis.core.dataobject.BaseDO;

/**
 * 设备 DO
 *
 * @author BasicLab
 */
@TableName("device")
@KeySequence("device_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DeviceDO extends BaseDO {

    /**
     * id
     */
    @TableId
    private Long id;
    /**
     * 设备唯一标识
     */
    private String did;
    /**
     * 设备名称
     */
    private String name;
    /**
     * 设备描述
     */
    private String description;
    /**
     * 设备状态： ENABLE:启用 || DISABLE:禁用
     */
    private String enabledStatus;
    /**
     * 连接状态 :    OFFLINE:离线 || ONLINE:在线
     */
    private String connectStatus;
    /**
     * 产品唯一标识
     */
    private String pid;
    /**
     * 创建者
     */
    private String createBy;
    /**
     * 更新者
     */
    private String updateBy;
    /**
     * 备注
     */
    private String remark;
    /**
     * 设备版本号
     */
    private String deviceVersion;
    /**
     * 设备sn号
     */
    private String deviceSn;
    /**
     * IP地址
     */
    private String ipAddress;
    /**
     * MAC地址
     */
    private String macAddress;
    /**
     * 激活状态 0:未激活 1:已激活
     */
    private Short activeStatus;
    /**
     * 扩展json
     */
    private String extension;
    /**
     * 激活时间
     */
    private LocalDateTime activatedTime;
    /**
     * 最后上线时间
     */
    private LocalDateTime lastOnlineTime;
    /**
     * 子设备关联网关的设备唯一标识
     */
    private String parentDid;
    /**
     * 支持以下两种产品类型	•COMMON：普通产品，需直连设备。	•GATEWAY：网关产品，可挂载子设备。	•SUBSET：子设备。
     */
    private String deviceType;
    /**
     * 纬度
     */
    private BigDecimal latitude;
    /**
     * 经度
     */
    private BigDecimal longitude;
    /**
     * 设备所在位置
     */
    private String locationName;
    /**
     * 省,直辖市编码
     */
    private String provinceCode;
    /**
     * 市编码
     */
    private String cityCode;
    /**
     * 区县
     */
    private String regionCode;
    /**
     * 产品名称
     */
    private String productName;
    /**
     * 是否启用设备影子(0=禁用，1=启用)
     */
    private Short isShadow;
    /**
     * 物模型值
     */
    private Object thingsModelValue;
    /**
     * 产品类型ID
     */
    private Long productTypeId;
    /**
     * 产品类型名称
     */
    private String productTypeName;
    /**
     * 分组ID
     */
    private Long groupId;

}