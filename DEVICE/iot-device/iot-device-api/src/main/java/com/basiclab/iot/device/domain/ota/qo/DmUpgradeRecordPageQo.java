package com.basiclab.iot.device.domain.ota.qo;

import com.basiclab.iot.common.domain.PageQo;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import java.io.Serializable;

/**
 * 升级记录分页查询
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
@ApiModel(value = "DmUpgradeRecordPageQo对象", description = "升级记录分页Qo")
public class DmUpgradeRecordPageQo extends PageQo implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 版本包ID
     */
    @ApiModelProperty(value = "版本包ID")
    private Long pkgId;

    /**
     * 包类型[0:软件包,1:固件包,2:APP包,3:PC包]
     */
    @ApiModelProperty(value = "包类型[0:软件包,1:固件包,2:APP包,3:PC包]")
    private Integer type;

    /**
     * 设备唯一标识
     */
    @ApiModelProperty(value = "设备唯一标识")
    private String deviceIdentification;

    /**
     * 升级阶段[0:检测,1:命中,2:下载完成,3:下载失败,4:MD5校验失败,5:安装结果,6:启动成功]
     */
    @ApiModelProperty(value = "升级阶段")
    private Integer phase;

    /**
     * 是否成功[0:否,1:是]
     */
    @ApiModelProperty(value = "是否成功[0:否,1:是]")
    private Integer success;
}
