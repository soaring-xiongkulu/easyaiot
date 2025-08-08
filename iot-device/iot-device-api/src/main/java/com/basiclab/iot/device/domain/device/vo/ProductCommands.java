package com.basiclab.iot.device.domain.device.vo;

import com.basiclab.iot.common.domain.BaseEntity;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.*;
import lombok.experimental.Accessors;

import java.io.Serializable;

/**

* @Description:    java类作用描述
* @Author:         EasyAIoT
* @E-mail:         andywebjava@163.com
* @Website:        http://iot.mqttsnet.com
* @CreateDate:     2024/12/25$ 23:52$
* @UpdateUser:     EasyAIoT
* @UpdateDate:     2024/12/25$ 23:52$
* @UpdateRemark:   修改内容
* @Version:        1.0

*/
/**
    * 产品模型设备服务命令表
 * @author EasyAIoT
 */
@ApiModel(value="产品模型设备服务命令表")
@Data
@NoArgsConstructor
@AllArgsConstructor
@ToString(callSuper = true)
@Accessors(chain = true)
@Builder
public class ProductCommands extends BaseEntity implements Serializable {
    /**
    * 命令id
    */
    @ApiModelProperty(value="命令id")
    private Long id;

    /**
    * 服务ID
    */
    @ApiModelProperty(value="服务ID")
    private Long serviceId;

    /**
     * 命令标识
     */
    @ApiModelProperty(value = "命令标识")
    private String commandCode;
    /**
    * 指示命令的名字，如门磁的LOCK命令、摄像头的VIDEO_RECORD命令，命令名与参数共同构成一个完整的命令。
支持英文大小写、数字及下划线，长度[2,50]。

    */
    @ApiModelProperty(value="指示命令的名字，如门磁的LOCK命令、摄像头的VIDEO_RECORD命令，命令名与参数共同构成一个完整的命令。,支持英文大小写、数字及下划线，长度[2,50]。,")
    private String name;

    /**
    * 命令描述。
    */
    @ApiModelProperty(value="命令描述。")
    private String description;


    private static final long serialVersionUID = 1L;
}