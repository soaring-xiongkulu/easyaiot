package com.basiclab.iot.device.domain.ota.qo;

import com.basiclab.iot.common.domain.PageQo;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import java.io.Serializable;

/**
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @desc
 * @created 2025-05-28
 */
@Data
@ApiModel(value = "DmPackagePageQo对象", description = "版本包列表实体对象Qo")
public class DmPackagePageQo extends PageQo implements Serializable {

    private static final long serialVersionUID = 7223864037660091822L;
    /**
     * 主键ID
     */
    @ApiModelProperty(value = "主键ID")
    private Long id;
    /**
     * 包类型[0:软件包,1:固件包,2:APP包,3:PC包]
     */
    @ApiModelProperty(value = "包类型[0:软件包,1:固件包,2:APP包,3:PC包]")
    private Integer type;
    /**
     * 包名称
     */
    @ApiModelProperty(value = "包名称")
    private String name;
    /**
     * 包版本号
     */
    @ApiModelProperty(value = "包版本号")
    private String version;
    /**
     * 状态[0:未验证,1:测试中,2:已发布,3:待发布,4:已撤回]
     */
    @ApiModelProperty(value = "状态[0:未验证,1:测试中,2:已发布,3:待发布,4:已撤回]")
    private Integer status;
    /**
     * 适用产品标识
     */
    @ApiModelProperty(value = "适用产品标识")
    private String productIdentification;

}
