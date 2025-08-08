package com.basiclab.iot.model.domain.model.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import javax.validation.constraints.*;

@Schema(description = "管理后台 - 模型新增/修改 Request VO")
@Data
public class ModelSaveReqVO {

    @Schema(description = "主键ID", example = "12494")
    private Long id;

    @Schema(description = "模型名称", example = "李四")
    @NotEmpty(message = "模型名称不能为空")
    private String name;

    @Schema(description = "描述", example = "你说的对")
    private String description;

    @Schema(description = "封面地址")
    private String coverPath;

    @Schema(description = "模型版本")
    private String version;

    @Schema(description = "模型类型ID", example = "17701")
    @NotNull(message = "模型类型ID不能为空")
    private Long modelTypeId;

    @Schema(description = "发布状态[0:待审核,1:未发布,2:已发布]", example = "2")
    @NotNull(message = "发布状态[0:待审核,1:未发布,2:已发布]不能为空")
    private Short publishStatus;

    @Schema(description = "边缘平台")
    private String edgePlatform;

    @Schema(description = "芯片型号")
    private String chipModel;

    @Schema(description = "运行时环境")
    private String runEnvironment;

    @Schema(description = "开发语言")
    private String devLanguage;

    @Schema(description = "git地址", example = "https://www.iocoder.cn")
    private String gitUrl;

    @Schema(description = "pt模型地址", example = "https://www.iocoder.cn")
    private String ptModelUrl;

    @Schema(description = "pt模型训练结果地址", example = "https://www.iocoder.cn")
    private String ptResultUrl;

    @Schema(description = "onnx模型地址", example = "https://www.iocoder.cn")
    private String onnxModelUrl;

    @Schema(description = "onnx模型训练结果地址", example = "https://www.iocoder.cn")
    private String onnxResultUrl;

    @Schema(description = "rknn模型地址", example = "https://www.iocoder.cn")
    private String rknnModelUrl;

    @Schema(description = "rknn模型训练结果地址", example = "https://www.iocoder.cn")
    private String rknnResultUrl;

}