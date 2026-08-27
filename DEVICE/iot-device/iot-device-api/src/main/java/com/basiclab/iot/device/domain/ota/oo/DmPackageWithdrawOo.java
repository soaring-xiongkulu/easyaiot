package com.basiclab.iot.device.domain.ota.oo;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;
import java.io.Serializable;

/**
 * 撤回升级包
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
@ApiModel(value = "DmPackageWithdrawOo对象", description = "版本包撤回Oo")
public class DmPackageWithdrawOo implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 版本包ID
     */
    @NotNull(message = "版本包ID不能为空")
    @ApiModelProperty(value = "版本包ID")
    private Long id;

    /**
     * 撤回原因
     */
    @NotBlank(message = "撤回原因不能为空")
    @ApiModelProperty(value = "撤回原因")
    private String reason;
}
