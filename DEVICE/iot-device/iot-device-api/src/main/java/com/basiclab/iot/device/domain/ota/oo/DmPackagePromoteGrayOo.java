package com.basiclab.iot.device.domain.ota.oo;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import javax.validation.constraints.NotNull;
import java.io.Serializable;
import java.util.List;

/**
 * 灰度升阶（仅相邻升阶：设备级→产品级→全量）
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
@ApiModel(value = "DmPackagePromoteGrayOo对象", description = "灰度升阶Oo")
public class DmPackagePromoteGrayOo implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 版本包ID
     */
    @NotNull(message = "版本包ID不能为空")
    @ApiModelProperty(value = "版本包ID")
    private Long id;

    /**
     * 目标灰度阶梯[1:设备级,2:产品级,3:全量]
     */
    @NotNull(message = "目标灰度阶梯不能为空")
    @ApiModelProperty(value = "目标灰度阶梯[1:设备级,2:产品级,3:全量]")
    private Integer targetLadder;

    /**
     * 新阶梯的灰度范围（升到非全量阶梯时必填；升到全量时清空）
     */
    @ApiModelProperty(value = "新阶梯的灰度范围（升到非全量阶梯时必填）")
    private List<DmGrayScopeOo> grayScopes;
}
