package com.basiclab.iot.device.domain.ota.oo;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;
import java.io.Serializable;
import java.util.List;

/**
 * 灰度扩容（同阶梯追加范围）
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
@ApiModel(value = "DmPackageExpandGrayOo对象", description = "灰度扩容Oo")
public class DmPackageExpandGrayOo implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 版本包ID
     */
    @NotNull(message = "版本包ID不能为空")
    @ApiModelProperty(value = "版本包ID")
    private Long id;

    /**
     * 追加的灰度范围（范围类型需与当前阶梯匹配）
     */
    @NotEmpty(message = "灰度范围不能为空")
    @ApiModelProperty(value = "追加的灰度范围（范围类型需与当前阶梯匹配）")
    private List<DmGrayScopeOo> grayScopes;
}
