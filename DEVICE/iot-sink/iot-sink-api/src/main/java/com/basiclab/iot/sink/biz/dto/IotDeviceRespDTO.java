package com.basiclab.iot.sink.biz.dto;

import lombok.Data;

/**
 * IoT 设备信息 Response DTO
 *
 * @author 翱翔的雄库鲁
 */
@Data
public class IotDeviceRespDTO {

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
    /**
     * 租户编号
     */
    private Long tenantId;

}