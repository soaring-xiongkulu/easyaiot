package com.basiclab.iot.model.domain.model.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;
import com.alibaba.excel.annotation.*;

@Schema(description = "管理后台 - 模型类型 Response VO")
@Data
@ExcelIgnoreUnannotated
public class ModelTypeRespVO {

    @Schema(description = "主键ID", example = "17169")
    @ExcelProperty("主键ID")
    private Long id;

    @Schema(description = "名称", example = "张三")
    @ExcelProperty("名称")
    private String name;

    @Schema(description = "模型类型分类[0:模型分类,1:行业分类,2:运行环境]", example = "2")
    @ExcelProperty("模型类型分类[0:模型分类,1:行业分类,2:运行环境]")
    private Short type;

    @Schema(description = "父ID", example = "18260")
    @ExcelProperty("父ID")
    private Long parentId;

}