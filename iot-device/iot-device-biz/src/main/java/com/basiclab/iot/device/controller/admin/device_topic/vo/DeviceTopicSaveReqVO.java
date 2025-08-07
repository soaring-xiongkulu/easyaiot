package com.basiclab.iot.device.controller.admin.device_topic.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import javax.validation.constraints.*;

@Schema(description = "管理后台 - 设备Topic数据新增/修改 Request VO")
@Data
public class DeviceTopicSaveReqVO {

    @Schema(description = "id", requiredMode = Schema.RequiredMode.REQUIRED, example = "13975")
    private Long id;

    @Schema(description = "设备标识", requiredMode = Schema.RequiredMode.REQUIRED, example = "7136")
    @NotEmpty(message = "设备标识不能为空")
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

    @Schema(description = "更新者")
    private String updateBy;

    @Schema(description = "备注", example = "你猜")
    private String remark;

}