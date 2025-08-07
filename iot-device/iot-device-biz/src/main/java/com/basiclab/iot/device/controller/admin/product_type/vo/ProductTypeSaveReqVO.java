package com.basiclab.iot.device.controller.admin.product_type.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import javax.validation.constraints.*;

@Schema(description = "管理后台 - 产品分类新增/修改 Request VO")
@Data
public class ProductTypeSaveReqVO {

    @Schema(description = "id", requiredMode = Schema.RequiredMode.REQUIRED, example = "27207")
    private Long id;

    @Schema(description = "名称", requiredMode = Schema.RequiredMode.REQUIRED, example = "芋艿")
    @NotEmpty(message = "名称不能为空")
    private String name;

    @Schema(description = "排序序号")
    private Long sort;

    @Schema(description = "父级ID", example = "31891")
    private String parentId;

    @Schema(description = "创建者")
    private String createBy;

    @Schema(description = "更新者")
    private String updateBy;

}