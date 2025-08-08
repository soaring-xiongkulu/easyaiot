package com.basiclab.iot.model.domain.model.vo;

import lombok.*;
import io.swagger.v3.oas.annotations.media.Schema;
import com.basiclab.iot.common.domain.PageParam;

@Schema(description = "管理后台 - 模型类型分页 Request VO")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
public class ModelTypePageReqVO extends PageParam {

    @Schema(description = "名称", example = "张三")
    private String name;

    @Schema(description = "模型类型分类[0:模型分类,1:行业分类,2:运行环境]", example = "2")
    private Short type;

    @Schema(description = "父ID", example = "18260")
    private Long parentId;

}