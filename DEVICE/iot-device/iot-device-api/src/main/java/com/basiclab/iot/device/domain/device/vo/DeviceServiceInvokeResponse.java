package com.basiclab.iot.device.domain.device.vo;

import com.fasterxml.jackson.annotation.JsonFormat;
import io.swagger.annotations.ApiModelProperty;
import lombok.*;

import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * DeviceServiceInvokeResponse
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Data
@NoArgsConstructor
@AllArgsConstructor
@ToString
@Builder
@EqualsAndHashCode
public class DeviceServiceInvokeResponse implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 主键ID
     */
    @ApiModelProperty(value = "主键ID")
    private Long id;

    /**
     * 消息编号（来自IotDeviceMessage.id）
     */
    @ApiModelProperty(value = "消息编号")
    private String messageId;

    /**
     * 设备编号
     */
    @ApiModelProperty(value = "设备编号")
    private Long deviceId;

    /**
     * 设备标识
     */
    @ApiModelProperty(value = "设备标识")
    private String deviceIdentification;

    /**
     * 产品标识
     */
    @ApiModelProperty(value = "产品标识")
    private String productIdentification;

    /**
     * 服务标识（从topic中提取的identifier）
     */
    @ApiModelProperty(value = "服务标识")
    private String serviceIdentifier;

    /**
     * 请求编号（来自IotDeviceMessage.requestId）
     */
    @ApiModelProperty(value = "请求编号")
    private String requestId;

    /**
     * 请求方法（来自IotDeviceMessage.method，通常是thing.service.invoke）
     */
    @ApiModelProperty(value = "请求方法")
    private String method;

    /**
     * 响应数据（来自IotDeviceMessage.data，JSON格式）
     */
    @ApiModelProperty(value = "响应数据")
    private String responseData;

    /**
     * 响应错误码（来自IotDeviceMessage.code）
     */
    @ApiModelProperty(value = "响应错误码")
    private Integer responseCode;

    /**
     * 响应消息（来自IotDeviceMessage.msg）
     */
    @ApiModelProperty(value = "响应消息")
    private String responseMsg;

    /**
     * MQTT Topic
     */
    @ApiModelProperty(value = "MQTT Topic")
    private String topic;

    /**
     * 上报时间（来自IotDeviceMessage.reportTime）
     */
    @ApiModelProperty(value = "上报时间")
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime reportTime;

    /**
     * 租户编号
     */
    @ApiModelProperty(value = "租户编号")
    private Long tenantId;

    /**
     * 创建时间
     */
    @ApiModelProperty(value = "创建时间")
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime createTime;
}

