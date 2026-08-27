package com.basiclab.iot.device.domain.ota.oo;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import javax.validation.constraints.NotBlank;
import java.io.Serializable;
import java.util.List;

/**
 * 设备检测升级（统一出入口：一次携带四类包当前版本，返回全部待升级项）
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
@ApiModel(value = "DmOtaCheckOo对象", description = "设备检测升级Oo")
public class DmOtaCheckOo implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 设备唯一标识
     */
    @NotBlank(message = "设备唯一标识不能为空")
    @ApiModelProperty(value = "设备唯一标识")
    private String deviceIdentification;

    /**
     * 产品标识（可选，用于灰度产品级匹配与产品过滤）
     */
    @ApiModelProperty(value = "产品标识（可选）")
    private String productIdentification;

    /**
     * 设备整机版本号（可选，用于设备版本档案匹配）
     */
    @ApiModelProperty(value = "设备整机版本号（可选，用于设备版本档案匹配）")
    private String deviceVersion;

    /**
     * 当前各类型版本[软件包/固件包/APP包/PC包]
     */
    @ApiModelProperty(value = "当前各类型版本")
    private List<DmOtaVersionOo> versions;
}
