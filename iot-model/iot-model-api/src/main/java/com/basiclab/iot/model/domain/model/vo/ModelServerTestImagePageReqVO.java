package com.basiclab.iot.model.domain.model.vo;

import lombok.*;
import io.swagger.v3.oas.annotations.media.Schema;
import com.basiclab.iot.common.domain.PageParam;
import org.springframework.format.annotation.DateTimeFormat;
import java.time.LocalDateTime;

import static com.basiclab.iot.common.utils.date.DateUtils.FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND;

@Schema(description = "管理后台 - 模型测试图片分页 Request VO")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
public class ModelServerTestImagePageReqVO extends PageParam {

    @Schema(description = "测试模型服务ID", example = "30001")
    private Long modelServerTestId;

    @Schema(description = "模型ID", example = "19598")
    private Long modelId;

    @Schema(description = "数据集图片ID", example = "6520")
    private Long datasetImageId;

    @Schema(description = "标注时间")
    @DateTimeFormat(pattern = FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND)
    private LocalDateTime[] annoTime;

    @Schema(description = "标注后图片路径")
    private String annoImagePath;

    @Schema(description = "选取次数", example = "9495")
    private Integer modificationCount;

}