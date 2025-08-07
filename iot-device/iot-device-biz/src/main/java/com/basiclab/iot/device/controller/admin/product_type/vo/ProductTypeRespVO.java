package com.basiclab.iot.device.controller.admin.product_type.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import java.time.LocalDateTime;
import com.alibaba.excel.annotation.*;

@Schema(description = "管理后台 - 产品分类 Response VO")
@Data
@ExcelIgnoreUnannotated
public class ProductTypeRespVO {

    @Schema(description = "id", requiredMode = Schema.RequiredMode.REQUIRED, example = "27207")
    @ExcelProperty("id")
    private Long id;

    @Schema(description = "名称", requiredMode = Schema.RequiredMode.REQUIRED, example = "芋艿")
    @ExcelProperty("名称")
    private String name;

    @Schema(description = "排序序号")
    @ExcelProperty("排序序号")
    private Long sort;

    @Schema(description = "父级ID", example = "31891")
    @ExcelProperty("父级ID")
    private String parentId;

    @Schema(description = "创建者")
    @ExcelProperty("创建者")
    private String createBy;

    @Schema(description = "创建时间")
    @ExcelProperty("创建时间")
    private LocalDateTime createTime;

    @Schema(description = "更新者")
    @ExcelProperty("更新者")
    private String updateBy;

}