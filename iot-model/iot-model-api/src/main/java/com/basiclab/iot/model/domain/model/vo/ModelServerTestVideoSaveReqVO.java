package com.basiclab.iot.model.domain.model.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import javax.validation.constraints.*;
import java.time.LocalDateTime;

@Schema(description = "管理后台 - 模型测试视频新增/修改 Request VO")
@Data
public class ModelServerTestVideoSaveReqVO {

    @Schema(description = "主键ID", example = "7926")
    private Long id;

    @Schema(description = "测试模型服务ID", example = "16349")
    @NotNull(message = "测试模型服务ID不能为空")
    private Long modelServerTestId;

    @Schema(description = "模型ID", example = "15989")
    private Long modelId;

    @Schema(description = "数据集视频ID", example = "15909")
    @NotNull(message = "数据集视频ID不能为空")
    private Long datasetVideoId;

    @Schema(description = "标注时间")
    private LocalDateTime annoTime;

    @Schema(description = "标注后视频路径")
    @NotEmpty(message = "标注后视频路径不能为空")
    private String annoVideoPath;

    @Schema(description = "状态[0:运行中,1:成功,2:失败]")
    @NotNull(message = "状态[0:运行中,1:成功,2:失败]不能为空")
    private Short state;

}