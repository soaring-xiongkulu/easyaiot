package com.basiclab.iot.device.controller.admin.device_topic.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import java.time.LocalDateTime;
import com.alibaba.excel.annotation.*;

@Schema(description = "管理后台 - 设备Topic数据 Response VO")
@Data
@ExcelIgnoreUnannotated
public class DeviceTopicRespVO {

    @Schema(description = "id", requiredMode = Schema.RequiredMode.REQUIRED, example = "13975")
    @ExcelProperty("id")
    private Long id;

    @Schema(description = "设备标识", requiredMode = Schema.RequiredMode.REQUIRED, example = "7136")
    @ExcelProperty("设备标识")
    private String did;

    @Schema(description = "类型(0:基础Topic,1:自定义Topic)", example = "2")
    @ExcelProperty("类型(0:基础Topic,1:自定义Topic)")
    private String type;

    @Schema(description = "topic")
    @ExcelProperty("topic")
    private String topic;

    @Schema(description = "发布者")
    @ExcelProperty("发布者")
    private String publisher;

    @Schema(description = "订阅者")
    @ExcelProperty("订阅者")
    private String subscriber;

    @Schema(description = "创建者")
    @ExcelProperty("创建者")
    private String createBy;

    @Schema(description = "创建时间", requiredMode = Schema.RequiredMode.REQUIRED)
    @ExcelProperty("创建时间")
    private LocalDateTime createTime;

    @Schema(description = "更新者")
    @ExcelProperty("更新者")
    private String updateBy;

    @Schema(description = "备注", example = "你猜")
    @ExcelProperty("备注")
    private String remark;

}