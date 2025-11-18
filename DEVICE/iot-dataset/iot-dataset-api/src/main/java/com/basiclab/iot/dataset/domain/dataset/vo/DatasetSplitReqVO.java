package com.basiclab.iot.dataset.domain.dataset.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.DecimalMax;
import javax.validation.constraints.DecimalMin;
import java.math.BigDecimal;

/**
 * DatasetSplitReqVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
public class DatasetSplitReqVO {
    @Schema(description = "训练集比例", required = true)
    @DecimalMin("0.1")
    @DecimalMax("0.9")
    private BigDecimal trainRatio;

    @Schema(description = "验证集比例", required = true)
    @DecimalMin("0.1")
    @DecimalMax("0.9")
    private BigDecimal valRatio;

    @Schema(description = "测试集比例", required = true)
    @DecimalMin("0.1")
    @DecimalMax("0.9")
    private BigDecimal testRatio;
}
