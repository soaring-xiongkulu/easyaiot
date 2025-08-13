package com.basiclab.iot.device.domain.device.vo;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.*;
import lombok.experimental.Accessors;

import java.io.Serializable;

/**
 * @author EasyAIoT
 * @desc
 * @created 2025-06-07
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@ToString(callSuper = true)
@Accessors(chain = true)
@EqualsAndHashCode
@Builder
@ApiModel(value = "DeviceToGateWayVo", description = "设备向网关发送消息vo")
public class DeviceToGateWayVo implements Serializable {

    private static final long serialVersionUID = 1L;

    @ApiModelProperty(value = "下发设备的信息")
    private CommandIssueRequestParam commandIssueRequestParamVo;


    @ApiModelProperty(value = "扩展信息（网关需要使用消息）")
    private ExtendInfoVo extendInfo;


}
