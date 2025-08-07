package com.basiclab.iot.device.controller.admin.protocol.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import javax.validation.constraints.*;

@Schema(description = "管理后台 - 协议信息新增/修改 Request VO")
@Data
public class ProtocolSaveReqVO {

    @Schema(description = "id", requiredMode = Schema.RequiredMode.REQUIRED, example = "22090")
    private Long id;

    @Schema(description = "应用ID", requiredMode = Schema.RequiredMode.REQUIRED, example = "3540")
    @NotEmpty(message = "应用ID不能为空")
    private String appId;

    @Schema(description = "产品标识", requiredMode = Schema.RequiredMode.REQUIRED, example = "30177")
    @NotEmpty(message = "产品标识不能为空")
    private String pid;

    @Schema(description = "协议名称", example = "芋艿")
    private String protocolName;

    @Schema(description = "协议标识")
    private String protocolCode;

    @Schema(description = "协议版本")
    private String protocolVersion;

    @Schema(description = "协议类型 ：mqtt || coap || modbus || http", example = "1")
    private String protocolType;

    @Schema(description = "协议语言")
    private String protocolVoice;

    @Schema(description = "类名", example = "王五")
    private String className;

    @Schema(description = "文件地址")
    private String filePath;

    @Schema(description = "内容")
    private String content;

    @Schema(description = "状态(字典值：0启用  1停用)", requiredMode = Schema.RequiredMode.REQUIRED, example = "2")
    @NotEmpty(message = "状态(字典值：0启用  1停用)不能为空")
    private String status;

    @Schema(description = "创建者")
    private String createBy;

    @Schema(description = "更新者")
    private String updateBy;

    @Schema(description = "备注", example = "你说的对")
    private String remark;

}