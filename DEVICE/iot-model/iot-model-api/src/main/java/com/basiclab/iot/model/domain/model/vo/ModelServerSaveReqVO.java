package com.basiclab.iot.model.domain.model.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import javax.validation.constraints.*;
import java.time.LocalDateTime;

@Schema(description = "管理后台 - 模型服务新增/修改 Request VO")
@Data
public class ModelServerSaveReqVO {

    @Schema(description = "主键ID", example = "1051")
    private Long id;

    @Schema(description = "模型服务名称", example = "王五")
    @NotEmpty(message = "模型服务名称不能为空")
    private String name;

    @Schema(description = "模型ID", example = "5092")
    @NotNull(message = "模型ID不能为空")
    private Long modelId;

    @Schema(description = "数据集ID", example = "21514")
    private Long datasetId;

    @Schema(description = "发布状态[0:待发布,1:已发布,2:发布失败,3:已下架]", example = "1")
    @NotNull(message = "发布状态[0:待发布,1:已发布,2:发布失败,3:已下架]不能为空")
    private Short publishStatus;

    @Schema(description = "审核人ID", example = "530")
    private Long auditUserId;

    @Schema(description = "版本号")
    private String version;

    @Schema(description = "服务访问地址")
    private String serverAddress;

    @Schema(description = "ONNX模型文件", example = "https://www.iocoder.cn")
    private String onnxFileUrl;

    @Schema(description = "描述", example = "你说的对")
    private String description;

    @Schema(description = "模型大小")
    private Long size;

    @Schema(description = "执行状态[0:未启动,1:部署中,2:部署失败,3:运行中,4:已关闭]", example = "1")
    @NotNull(message = "执行状态[0:未启动,1:部署中,2:部署失败,3:运行中,4:已关闭]不能为空")
    private Short executeStatus;

    @Schema(description = "发布时间")
    private LocalDateTime publishTime;

    @Schema(description = "anchors.txt文件", example = "https://www.iocoder.cn")
    private String anchorsFileUrl;

    @Schema(description = "完整应用文件（或量化后应用文件）", example = "https://www.iocoder.cn")
    private String applyFileUrl;

    @Schema(description = "应用文件大小")
    private Long applyFileSize;

    @Schema(description = "应用文件MD5值")
    private String applyFileMd5;

}