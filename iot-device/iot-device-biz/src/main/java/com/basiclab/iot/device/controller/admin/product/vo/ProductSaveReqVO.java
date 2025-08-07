package com.basiclab.iot.device.controller.admin.product.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import javax.validation.constraints.*;

@Schema(description = "管理后台 - 产品新增/修改 Request VO")
@Data
public class ProductSaveReqVO {

    @Schema(description = "id", requiredMode = Schema.RequiredMode.REQUIRED, example = "12926")
    private Long id;

    @Schema(description = "模板code")
    private String templateCode;

    @Schema(description = "产品名称", requiredMode = Schema.RequiredMode.REQUIRED, example = "李四")
    @NotEmpty(message = "产品名称不能为空")
    private String name;

    @Schema(description = "产品唯一标识", requiredMode = Schema.RequiredMode.REQUIRED, example = "2009")
    @NotEmpty(message = "产品唯一标识不能为空")
    private String pid;

    @Schema(description = "厂商名称 :支持中文、英文大小写、数字、下划线和中划线", requiredMode = Schema.RequiredMode.REQUIRED, example = "王五")
    @NotEmpty(message = "厂商名称 :支持中文、英文大小写、数字、下划线和中划线不能为空")
    private String manufacturerName;

    @Schema(description = "产品型号，建议包含字母或数字来保证可扩展性。支持英文大小写、数字、下划线和中划线", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotEmpty(message = "产品型号，建议包含字母或数字来保证可扩展性。支持英文大小写、数字、下划线和中划线不能为空")
    private String model;

    @Schema(description = "数据格式，默认为JSON无需修改。", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotEmpty(message = "数据格式，默认为JSON无需修改。不能为空")
    private String dataFormat;

    @Schema(description = "设备接入平台的协议类型，默认为MQTT无需修改。", requiredMode = Schema.RequiredMode.REQUIRED, example = "2")
    @NotEmpty(message = "设备接入平台的协议类型，默认为MQTT无需修改。不能为空")
    private String protocolType;

    @Schema(description = "状态(字典值：0启用  1停用)", requiredMode = Schema.RequiredMode.REQUIRED, example = "2")
    @NotNull(message = "状态(字典值：0启用  1停用)不能为空")
    private Short enabledStatus;

    @Schema(description = "产品描述", example = "你猜")
    private String remark;

    @Schema(description = "创建者")
    private String createBy;

    @Schema(description = "更新者")
    private String updateBy;

    @Schema(description = "认证方式")
    private String authMode;

    @Schema(description = "用户名", example = "王五")
    private String userName;

    @Schema(description = "密码")
    private String password;

    @Schema(description = "连接实例")
    private String connector;

    @Schema(description = "签名密钥")
    private String signKey;

    @Schema(description = "协议加密方式 0：不加密 1：SM4加密 2：AES加密")
    private Integer encryptMethod;

    @Schema(description = "加密密钥")
    private String encryptKey;

    @Schema(description = "加密向量")
    private String encryptVector;

    @Schema(description = "产品类型ID", example = "29799")
    private Long productTypeId;

    @Schema(description = "产品类型名称", example = "张三")
    private String productTypeName;

    @Schema(description = "厂商Code:支持英文大小写，数字，下划线和中划线", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotEmpty(message = "厂商Code:支持英文大小写，数字，下划线和中划线不能为空")
    private String manufacturerCode;

}