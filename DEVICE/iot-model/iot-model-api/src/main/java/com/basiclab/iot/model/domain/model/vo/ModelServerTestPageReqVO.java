package com.basiclab.iot.model.domain.model.vo;

import lombok.*;
import io.swagger.v3.oas.annotations.media.Schema;
import com.basiclab.iot.common.domain.PageParam;
import org.springframework.format.annotation.DateTimeFormat;
import java.time.LocalDateTime;

import static com.basiclab.iot.common.utils.date.DateUtils.FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND;

@Schema(description = "管理后台 - 模型测试服务分页 Request VO")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
public class ModelServerTestPageReqVO extends PageParam {

    @Schema(description = "模型服务ID", example = "23393")
    private Long modelServeId;

    @Schema(description = "模型ID", example = "23378")
    private Long modelId;

    @Schema(description = "测试模型服务名称", example = "王五")
    private String name;

    @Schema(description = "测试模型服务类型[0:图片测试,1:视频测试]", example = "2")
    private Short type;

    @Schema(description = "计划标注数量")
    private Integer plannedQuantity;

    @Schema(description = "已经标注数量")
    private Integer markedQuantity;

    @Schema(description = "无目标数量", example = "3115")
    private Integer notTargetCount;

    @Schema(description = "完成时间")
    @DateTimeFormat(pattern = FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND)
    private LocalDateTime[] finishTime;

    @Schema(description = "服务状态[0:进行中,1:成功,2:失败]")
    private Short state;

    @Schema(description = "描述", example = "随便")
    private String description;

}