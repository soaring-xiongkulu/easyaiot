package com.basiclab.iot.device.dal.dataobject;

import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.basiclab.iot.common.domain.BaseEntity2;
import lombok.*;

import java.io.Serializable;

/**
 * @author IoT
 * @desc
 * @created 2024-05-27
 */
@Data
@EqualsAndHashCode(callSuper = false)
@TableName("device_ota_device_model")
@KeySequence("device_ota_device_model_id_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DmOtaDeviceModelPo extends BaseEntity2 implements Serializable {
    private static final long serialVersionUID = 7182705898327944830L;
    /**
     * 主键ID
     */
    @TableId
    private Long id;
    /**
     * 产品模型编码
     */
    @TableField(value = "product_model")
    private String productModel;
    /**
     * 设备模型编码
     */
    @TableField(value = "device_model")
    private String deviceModel;
    /**
     * 设备大版本号
     */
    @TableField(value = "device_version")
    private String deviceVersion;

}