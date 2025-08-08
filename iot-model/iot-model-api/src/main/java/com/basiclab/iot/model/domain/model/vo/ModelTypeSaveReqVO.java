package com.basiclab.iot.model.domain.model.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import javax.validation.constraints.*;

@Schema(description = "管理后台 - 模型类型新增/修改 Request VO")
@Data
public class ModelTypeSaveReqVO {

    @Schema(description = "主键ID", example = "17169")
    private Long id;

    @Schema(description = "名称", example = "张三")
    @NotEmpty(message = "名称不能为空")
    private String name;

    @Schema(description = "模型类型分类[0:模型分类,1:行业分类,2:运行环境]", example = "2")
    @NotNull(message = "模型类型分类[0:模型分类,1:行业分类,2:运行环境]不能为空")
    private Short type;

    @Schema(description = "父ID", example = "18260")
    private Long parentId;

}