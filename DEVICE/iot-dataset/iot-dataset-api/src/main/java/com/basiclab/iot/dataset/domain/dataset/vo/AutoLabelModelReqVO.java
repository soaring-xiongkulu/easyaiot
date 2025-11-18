package com.basiclab.iot.dataset.domain.dataset.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * AutoLabelModelReqVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
public class AutoLabelModelReqVO {
    @Schema(description = "模型服务ID", required = true)
    private Long modelServiceId;
}