package com.basiclab.iot.device.domain.device.vo;

import lombok.*;
import io.swagger.v3.oas.annotations.media.Schema;
import com.basiclab.iot.common.domain.PageParam;
import org.springframework.format.annotation.DateTimeFormat;
import java.time.LocalDateTime;

import static com.basiclab.iot.common.utils.date.DateUtils.FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND;

@Schema(description = "管理后台 - 设备分组分页 Request VO")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
public class DeviceGroupPageReqVO extends PageParam {

    @Schema(description = "分组ID", example = "李四")
    private String groupName;

    @Schema(description = "创建者")
    private String createBy;

    @Schema(description = "创建时间")
    @DateTimeFormat(pattern = FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND)
    private LocalDateTime[] createTime;

    @Schema(description = "更新者")
    private String updateBy;

}