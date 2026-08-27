package com.basiclab.iot.device.domain.ota.oo;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import javax.validation.constraints.NotNull;
import java.io.Serializable;
import java.util.List;

/**
 * 发布升级包
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
@ApiModel(value = "DmPackagePublishOo对象", description = "版本包发布Oo")
public class DmPackagePublishOo implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 版本包ID
     */
    @NotNull(message = "版本包ID不能为空")
    @ApiModelProperty(value = "版本包ID")
    private Long id;

    /**
     * 发布策略[0:全量,1:灰度]
     */
    @NotNull(message = "发布策略不能为空")
    @ApiModelProperty(value = "发布策略[0:全量,1:灰度]")
    private Integer publishStrategy;

    /**
     * 灰度阶梯[1:设备级,2:产品级,3:全量]
     */
    @ApiModelProperty(value = "灰度阶梯[1:设备级,2:产品级,3:全量]")
    private Integer grayLadder;

    /**
     * 灰度范围（发布策略为灰度时必填，范围类型需与灰度阶梯匹配）
     */
    @ApiModelProperty(value = "灰度范围（发布策略为灰度时必填）")
    private List<DmGrayScopeOo> grayScopes;

    /**
     * 是否跳过测试直接发布
     */
    @ApiModelProperty(value = "是否跳过测试直接发布")
    private Boolean skipVerify;
}
