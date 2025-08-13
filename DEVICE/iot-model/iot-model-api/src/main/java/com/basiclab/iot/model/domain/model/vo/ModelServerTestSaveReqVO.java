package com.basiclab.iot.model.domain.model.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import javax.validation.constraints.*;
import java.time.LocalDateTime;

@Schema(description = "管理后台 - 模型测试服务新增/修改 Request VO")
@Data
public class ModelServerTestSaveReqVO {

    @Schema(description = "主键ID", example = "10970")
    private Long id;

    @Schema(description = "模型服务ID", example = "23393")
    @NotNull(message = "模型服务ID不能为空")
    private Long modelServeId;

    @Schema(description = "模型ID", example = "23378")
    private Long modelId;

    @Schema(description = "测试模型服务名称", example = "王五")
    @NotEmpty(message = "测试模型服务名称不能为空")
    private String name;

    @Schema(description = "测试模型服务类型[0:图片测试,1:视频测试]", example = "2")
    @NotNull(message = "测试模型服务类型[0:图片测试,1:视频测试]不能为空")
    private Short type;

    @Schema(description = "计划标注数量")
    private Integer plannedQuantity;

    @Schema(description = "已经标注数量")
    private Integer markedQuantity;

    @Schema(description = "无目标数量", example = "3115")
    private Integer notTargetCount;

    @Schema(description = "完成时间")
    private LocalDateTime finishTime;

    @Schema(description = "服务状态[0:进行中,1:成功,2:失败]")
    @NotNull(message = "服务状态[0:进行中,1:成功,2:失败]不能为空")
    private Short state;

    @Schema(description = "描述", example = "随便")
    private String description;

}