package com.basiclab.iot.device.domain.ota.vo;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import java.io.Serializable;

/**
 * 白名单分组（按产品）
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
@ApiModel(value = "DmWhiteGroupVo对象", description = "白名单分组（按产品）")
public class DmWhiteGroupVo implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 产品标识
     */
    @ApiModelProperty(value = "产品标识")
    private String productIdentification;

    /**
     * 产品名称
     */
    @ApiModelProperty(value = "产品名称")
    private String productName;

    /**
     * 产品下设备数
     */
    @ApiModelProperty(value = "产品下设备数")
    private Long deviceCount;
}
