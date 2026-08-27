package com.basiclab.iot.device.domain.ota.oo;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import javax.validation.constraints.NotNull;
import java.io.Serializable;

/**
 * 测试结果上报
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
@ApiModel(value = "DmPackageTestResultOo对象", description = "版本包测试结果Oo")
public class DmPackageTestResultOo implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 版本包ID
     */
    @NotNull(message = "版本包ID不能为空")
    @ApiModelProperty(value = "版本包ID")
    private Long id;

    /**
     * 是否通过[true:通过,false:不通过]
     */
    @NotNull(message = "测试结果不能为空")
    @ApiModelProperty(value = "是否通过[true:通过,false:不通过]")
    private Boolean passed;

    /**
     * 测试备注
     */
    @ApiModelProperty(value = "测试备注")
    private String remark;
}
