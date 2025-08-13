package com.basiclab.iot.model.domain.model.vo;

import lombok.*;
import io.swagger.v3.oas.annotations.media.Schema;
import com.basiclab.iot.common.domain.PageParam;
import org.springframework.format.annotation.DateTimeFormat;
import java.time.LocalDateTime;

import static com.basiclab.iot.common.utils.date.DateUtils.FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND;

@Schema(description = "管理后台 - 模型测试视频分页 Request VO")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
public class ModelServerTestVideoPageReqVO extends PageParam {

    @Schema(description = "测试模型服务ID", example = "16349")
    private Long modelServerTestId;

    @Schema(description = "模型ID", example = "15989")
    private Long modelId;

    @Schema(description = "数据集视频ID", example = "15909")
    private Long datasetVideoId;

    @Schema(description = "标注时间")
    @DateTimeFormat(pattern = FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND)
    private LocalDateTime[] annoTime;

    @Schema(description = "标注后视频路径")
    private String annoVideoPath;

    @Schema(description = "状态[0:运行中,1:成功,2:失败]")
    private Short state;

}