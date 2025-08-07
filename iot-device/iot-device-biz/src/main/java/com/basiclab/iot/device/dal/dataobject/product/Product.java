package com.basiclab.iot.device.dal.dataobject.product;

import lombok.*;
import com.baomidou.mybatisplus.annotation.*;
import com.basiclab.iot.common.mybatis.core.dataobject.BaseDO;

/**
 * 产品 DO
 *
 * @author BasicLab
 */
@TableName("product")
@KeySequence("product_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Product extends BaseDO {

    /**
     * id
     */
    @TableId
    private Long id;
    /**
     * 模板code
     */
    private String templateCode;
    /**
     * 产品名称
     */
    private String name;
    /**
     * 产品唯一标识
     */
    private String pid;
    /**
     * 厂商名称 :支持中文、英文大小写、数字、下划线和中划线
     */
    private String manufacturerName;
    /**
     * 产品型号，建议包含字母或数字来保证可扩展性。支持英文大小写、数字、下划线和中划线
     */
    private String model;
    /**
     * 数据格式，默认为JSON无需修改。
     */
    private String dataFormat;
    /**
     * 设备接入平台的协议类型，默认为MQTT无需修改。
     */
    private String protocolType;
    /**
     * 状态(字典值：0启用  1停用)
     */
    private Short enabledStatus;
    /**
     * 产品描述
     */
    private String remark;
    /**
     * 创建者
     */
    private String createBy;
    /**
     * 更新者
     */
    private String updateBy;
    /**
     * 认证方式
     */
    private String authMode;
    /**
     * 用户名
     */
    private String userName;
    /**
     * 密码
     */
    private String password;
    /**
     * 连接实例
     */
    private String connector;
    /**
     * 签名密钥
     */
    private String signKey;
    /**
     * 协议加密方式 0：不加密 1：SM4加密 2：AES加密
     */
    private Integer encryptMethod;
    /**
     * 加密密钥
     */
    private String encryptKey;
    /**
     * 加密向量
     */
    private String encryptVector;
    /**
     * 产品类型ID
     */
    private Long productTypeId;
    /**
     * 产品类型名称
     */
    private String productTypeName;
    /**
     * 厂商Code:支持英文大小写，数字，下划线和中划线
     */
    private String manufacturerCode;

}