package com.basiclab.iot.device.domain.ota.oo;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;
import java.io.Serializable;
import java.util.List;

/**
 * 批量加入测试白名单
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
@ApiModel(value = "DmBatchAddVerifyOo对象", description = "批量加入测试白名单Oo")
public class DmBatchAddVerifyOo implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 版本包ID
     */
    @NotNull(message = "版本包ID不能为空")
    @ApiModelProperty(value = "版本包ID")
    private Long pkgId;

    /**
     * 设备唯一标识列表
     */
    @NotEmpty(message = "设备列表不能为空")
    @ApiModelProperty(value = "设备唯一标识列表")
    private List<String> deviceIdentificationList;
}
