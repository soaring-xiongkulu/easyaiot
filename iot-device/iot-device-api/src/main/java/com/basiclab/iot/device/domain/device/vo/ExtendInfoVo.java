package com.basiclab.iot.device.domain.device.vo;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.*;
import lombok.experimental.Accessors;

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
@ApiModel(value = "ExtendInfoVo", description = "扩展信息vo")
public class ExtendInfoVo {

    @ApiModelProperty(value = "事件类型(PUBLISH:事件发布)")
    private String event;

    @ApiModelProperty(value = "协议类型(MQTT : MQTT协议; MODBUS : MODBUS协议)")
    private String protocol;

    @ApiModelProperty(value = "发送主题")
    private String topic;

    @ApiModelProperty(value = "mqtt的qos")
    private String qos;

    @ApiModelProperty(value = "消息发送时间")
    private String time;

    @ApiModelProperty(value = "指令名称")
    private String commandName;

}
