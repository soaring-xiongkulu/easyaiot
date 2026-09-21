package com.basiclab.iot.visualize.controller.admin.project.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotBlank;
import javax.validation.constraints.Size;

@Schema(description = "管理后台 - 可视化项目创建/修改 Request VO")
@Data
public class VisualizeProjectSaveReqVO {

    @Schema(description = "编号")
    private Long id;

    @Schema(description = "项目名称", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotBlank(message = "项目名称不能为空")
    @Size(max = 128, message = "项目名称不能超过128个字符")
    private String projectName;

    @Schema(description = "项目类型：dashboard 大屏，scada 组态（FUXA），twin 数字孪生", example = "dashboard")
    @Size(max = 32, message = "项目类型不能超过32个字符")
    private String projectType;

    @Schema(description = "缩略图 URL")
    private String indexImage;

    @Schema(description = "备注")
    @Size(max = 512, message = "备注不能超过512个字符")
    private String remarks;

    @Schema(description = "外部编辑器引用（组态可选：FUXA 画面名或相对路径，如 /editor）")
    @Size(max = 256, message = "编辑器引用不能超过256个字符")
    private String editorRef;

}
