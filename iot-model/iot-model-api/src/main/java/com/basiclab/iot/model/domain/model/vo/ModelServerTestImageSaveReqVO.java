package com.basiclab.iot.model.domain.model.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import javax.validation.constraints.*;
import java.time.LocalDateTime;

@Schema(description = "管理后台 - 模型测试图片新增/修改 Request VO")
@Data
public class ModelServerTestImageSaveReqVO {

    @Schema(description = "主键ID", example = "5620")
    private Long id;

    @Schema(description = "测试模型服务ID", example = "30001")
    @NotNull(message = "测试模型服务ID不能为空")
    private Long modelServerTestId;

    @Schema(description = "模型ID", example = "19598")
    private Long modelId;

    @Schema(description = "数据集图片ID", example = "6520")
    @NotNull(message = "数据集图片ID不能为空")
    private Long datasetImageId;

    @Schema(description = "标注时间")
    private LocalDateTime annoTime;

    @Schema(description = "标注后图片路径")
    @NotEmpty(message = "标注后图片路径不能为空")
    private String annoImagePath;

    @Schema(description = "选取次数", example = "9495")
    private Integer modificationCount;

}