package com.basiclab.iot.sink.biz.dto;

import lombok.Data;

/**
 * IotDeviceGetReqDTO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Data
public class IotDeviceGetReqDTO {

    /**
     * 设备编号
     */
    private Long id;

    /**
     * 产品唯一标识
     */
    private String productIdentification;
    /**
     * 设备唯一标识
     */
    private String deviceIdentification;

}