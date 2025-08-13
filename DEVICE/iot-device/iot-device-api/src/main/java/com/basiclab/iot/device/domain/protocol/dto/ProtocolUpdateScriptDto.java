package com.basiclab.iot.device.domain.protocol.dto;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.*;
import lombok.experimental.Accessors;

/**
 * @author EasyAIoT
 * @desc
 * @created 2025-06-21
 */
@ApiModel(value="协议更新脚本传输对象")
@Data
@NoArgsConstructor
@AllArgsConstructor
@ToString(callSuper = true)
@Accessors(chain = true)
@Builder
public class ProtocolUpdateScriptDto {

    @ApiModelProperty("设备id")
    private String deviceIdentification;

    @ApiModelProperty("通知类型   ADD:新增到内存   DELETE:从内存中删除")
    private String notifyType;


}
