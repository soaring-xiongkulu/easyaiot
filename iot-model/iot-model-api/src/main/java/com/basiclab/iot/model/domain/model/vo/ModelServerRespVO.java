package com.basiclab.iot.model.domain.model.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import java.time.LocalDateTime;
import com.alibaba.excel.annotation.*;

@Schema(description = "管理后台 - 模型服务 Response VO")
@Data
@ExcelIgnoreUnannotated
public class ModelServerRespVO {

    @Schema(description = "主键ID", example = "1051")
    @ExcelProperty("主键ID")
    private Long id;

    @Schema(description = "模型服务名称", example = "王五")
    @ExcelProperty("模型服务名称")
    private String name;

    @Schema(description = "模型ID", example = "5092")
    @ExcelProperty("模型ID")
    private Long modelId;

    @Schema(description = "数据集ID", example = "21514")
    @ExcelProperty("数据集ID")
    private Long datasetId;

    @Schema(description = "发布状态[0:待发布,1:已发布,2:发布失败,3:已下架]", example = "1")
    @ExcelProperty("发布状态[0:待发布,1:已发布,2:发布失败,3:已下架]")
    private Short publishStatus;

    @Schema(description = "审核人ID", example = "530")
    @ExcelProperty("审核人ID")
    private Long auditUserId;

    @Schema(description = "版本号")
    @ExcelProperty("版本号")
    private String version;

    @Schema(description = "服务访问地址")
    @ExcelProperty("服务访问地址")
    private String serverAddress;

    @Schema(description = "ONNX模型文件", example = "https://www.iocoder.cn")
    @ExcelProperty("ONNX模型文件")
    private String onnxFileUrl;

    @Schema(description = "描述", example = "你说的对")
    @ExcelProperty("描述")
    private String description;

    @Schema(description = "模型大小")
    @ExcelProperty("模型大小")
    private Long size;

    @Schema(description = "执行状态[0:未启动,1:部署中,2:部署失败,3:运行中,4:已关闭]", example = "1")
    @ExcelProperty("执行状态[0:未启动,1:部署中,2:部署失败,3:运行中,4:已关闭]")
    private Short executeStatus;

    @Schema(description = "发布时间")
    @ExcelProperty("发布时间")
    private LocalDateTime publishTime;

    @Schema(description = "anchors.txt文件", example = "https://www.iocoder.cn")
    @ExcelProperty("anchors.txt文件")
    private String anchorsFileUrl;

    @Schema(description = "完整应用文件（或量化后应用文件）", example = "https://www.iocoder.cn")
    @ExcelProperty("完整应用文件（或量化后应用文件）")
    private String applyFileUrl;

    @Schema(description = "应用文件大小")
    @ExcelProperty("应用文件大小")
    private Long applyFileSize;

    @Schema(description = "应用文件MD5值")
    @ExcelProperty("应用文件MD5值")
    private String applyFileMd5;

}