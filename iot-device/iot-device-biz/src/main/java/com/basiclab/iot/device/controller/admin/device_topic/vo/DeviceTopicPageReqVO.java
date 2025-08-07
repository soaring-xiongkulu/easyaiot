package com.basiclab.iot.device.controller.admin.device_topic.vo;

import lombok.*;
import io.swagger.v3.oas.annotations.media.Schema;
import com.basiclab.iot.common.domain.PageParam;
import org.springframework.format.annotation.DateTimeFormat;
import java.time.LocalDateTime;

import static com.basiclab.iot.common.utils.date.DateUtils.FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND;

@Schema(description = "管理后台 - 设备Topic数据分页 Request VO")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
public class DeviceTopicPageReqVO extends PageParam {

    @Schema(description = "设备标识", example = "7136")
    private String did;

    @Schema(description = "类型(0:基础Topic,1:自定义Topic)", example = "2")
    private String type;

    @Schema(description = "topic")
    private String topic;

    @Schema(description = "发布者")
    private String publisher;

    @Schema(description = "订阅者")
    private String subscriber;

    @Schema(description = "创建者")
    private String createBy;

    @Schema(description = "创建时间")
    @DateTimeFormat(pattern = FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND)
    private LocalDateTime[] createTime;

    @Schema(description = "更新者")
    private String updateBy;

    @Schema(description = "备注", example = "你猜")
    private String remark;

}