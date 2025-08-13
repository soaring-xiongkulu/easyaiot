package com.basiclab.iot.model.domain.model.vo;

import lombok.Data;

import javax.validation.constraints.NotBlank;

@Data
public class PodModelSaveReqVO {
    @NotBlank(message = "模型名称不能为空")
    private String modelName;

    private String description;
    private String version = "1.0";

    @NotBlank(message = "PT模型地址不能为空")
    private String ptModelUrl;

    @NotBlank(message = "训练结果地址不能为空")
    private String ptResultUrl;
}
