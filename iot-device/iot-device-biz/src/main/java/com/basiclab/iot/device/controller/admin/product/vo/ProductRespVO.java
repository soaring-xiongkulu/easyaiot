package com.basiclab.iot.device.controller.admin.product.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import java.time.LocalDateTime;
import com.alibaba.excel.annotation.*;

@Schema(description = "管理后台 - 产品 Response VO")
@Data
@ExcelIgnoreUnannotated
public class ProductRespVO {

    @Schema(description = "id", requiredMode = Schema.RequiredMode.REQUIRED, example = "12926")
    @ExcelProperty("id")
    private Long id;

    @Schema(description = "模板code")
    @ExcelProperty("模板code")
    private String templateCode;

    @Schema(description = "产品名称", requiredMode = Schema.RequiredMode.REQUIRED, example = "李四")
    @ExcelProperty("产品名称")
    private String name;

    @Schema(description = "产品唯一标识", requiredMode = Schema.RequiredMode.REQUIRED, example = "2009")
    @ExcelProperty("产品唯一标识")
    private String pid;

    @Schema(description = "厂商名称 :支持中文、英文大小写、数字、下划线和中划线", requiredMode = Schema.RequiredMode.REQUIRED, example = "王五")
    @ExcelProperty("厂商名称 :支持中文、英文大小写、数字、下划线和中划线")
    private String manufacturerName;

    @Schema(description = "产品型号，建议包含字母或数字来保证可扩展性。支持英文大小写、数字、下划线和中划线", requiredMode = Schema.RequiredMode.REQUIRED)
    @ExcelProperty("产品型号，建议包含字母或数字来保证可扩展性。支持英文大小写、数字、下划线和中划线")
    private String model;

    @Schema(description = "数据格式，默认为JSON无需修改。", requiredMode = Schema.RequiredMode.REQUIRED)
    @ExcelProperty("数据格式，默认为JSON无需修改。")
    private String dataFormat;

    @Schema(description = "设备接入平台的协议类型，默认为MQTT无需修改。", requiredMode = Schema.RequiredMode.REQUIRED, example = "2")
    @ExcelProperty("设备接入平台的协议类型，默认为MQTT无需修改。")
    private String protocolType;

    @Schema(description = "状态(字典值：0启用  1停用)", requiredMode = Schema.RequiredMode.REQUIRED, example = "2")
    @ExcelProperty("状态(字典值：0启用  1停用)")
    private Short enabledStatus;

    @Schema(description = "产品描述", example = "你猜")
    @ExcelProperty("产品描述")
    private String remark;

    @Schema(description = "创建者")
    @ExcelProperty("创建者")
    private String createBy;

    @Schema(description = "创建时间")
    @ExcelProperty("创建时间")
    private LocalDateTime createTime;

    @Schema(description = "更新者")
    @ExcelProperty("更新者")
    private String updateBy;

    @Schema(description = "认证方式")
    @ExcelProperty("认证方式")
    private String authMode;

    @Schema(description = "用户名", example = "王五")
    @ExcelProperty("用户名")
    private String userName;

    @Schema(description = "密码")
    @ExcelProperty("密码")
    private String password;

    @Schema(description = "连接实例")
    @ExcelProperty("连接实例")
    private String connector;

    @Schema(description = "签名密钥")
    @ExcelProperty("签名密钥")
    private String signKey;

    @Schema(description = "协议加密方式 0：不加密 1：SM4加密 2：AES加密")
    @ExcelProperty("协议加密方式 0：不加密 1：SM4加密 2：AES加密")
    private Integer encryptMethod;

    @Schema(description = "加密密钥")
    @ExcelProperty("加密密钥")
    private String encryptKey;

    @Schema(description = "加密向量")
    @ExcelProperty("加密向量")
    private String encryptVector;

    @Schema(description = "产品类型ID", example = "29799")
    @ExcelProperty("产品类型ID")
    private Long productTypeId;

    @Schema(description = "产品类型名称", example = "张三")
    @ExcelProperty("产品类型名称")
    private String productTypeName;

    @Schema(description = "厂商Code:支持英文大小写，数字，下划线和中划线", requiredMode = Schema.RequiredMode.REQUIRED)
    @ExcelProperty("厂商Code:支持英文大小写，数字，下划线和中划线")
    private String manufacturerCode;

}