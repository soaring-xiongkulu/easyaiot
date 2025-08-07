package com.basiclab.iot.device.controller.admin.protocol.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import java.time.LocalDateTime;
import com.alibaba.excel.annotation.*;

@Schema(description = "管理后台 - 协议信息 Response VO")
@Data
@ExcelIgnoreUnannotated
public class ProtocolRespVO {

    @Schema(description = "id", requiredMode = Schema.RequiredMode.REQUIRED, example = "22090")
    @ExcelProperty("id")
    private Long id;

    @Schema(description = "应用ID", requiredMode = Schema.RequiredMode.REQUIRED, example = "3540")
    @ExcelProperty("应用ID")
    private String appId;

    @Schema(description = "产品标识", requiredMode = Schema.RequiredMode.REQUIRED, example = "30177")
    @ExcelProperty("产品标识")
    private String pid;

    @Schema(description = "协议名称", example = "芋艿")
    @ExcelProperty("协议名称")
    private String protocolName;

    @Schema(description = "协议标识")
    @ExcelProperty("协议标识")
    private String protocolCode;

    @Schema(description = "协议版本")
    @ExcelProperty("协议版本")
    private String protocolVersion;

    @Schema(description = "协议类型 ：mqtt || coap || modbus || http", example = "1")
    @ExcelProperty("协议类型 ：mqtt || coap || modbus || http")
    private String protocolType;

    @Schema(description = "协议语言")
    @ExcelProperty("协议语言")
    private String protocolVoice;

    @Schema(description = "类名", example = "王五")
    @ExcelProperty("类名")
    private String className;

    @Schema(description = "文件地址")
    @ExcelProperty("文件地址")
    private String filePath;

    @Schema(description = "内容")
    @ExcelProperty("内容")
    private String content;

    @Schema(description = "状态(字典值：0启用  1停用)", requiredMode = Schema.RequiredMode.REQUIRED, example = "2")
    @ExcelProperty("状态(字典值：0启用  1停用)")
    private String status;

    @Schema(description = "创建者")
    @ExcelProperty("创建者")
    private String createBy;

    @Schema(description = "创建时间", requiredMode = Schema.RequiredMode.REQUIRED)
    @ExcelProperty("创建时间")
    private LocalDateTime createTime;

    @Schema(description = "更新者")
    @ExcelProperty("更新者")
    private String updateBy;

    @Schema(description = "备注", example = "你说的对")
    @ExcelProperty("备注")
    private String remark;

}