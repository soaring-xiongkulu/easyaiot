package com.basiclab.iot.device.service.device;


import com.basiclab.iot.device.domain.device.vo.TDDeviceDataResp;

import java.util.List;

/**
 * @author IoT
 */
public interface DeviceThingModelService {
    /**
     * 获取设备属性值
     *
     * @param id   设备主键id
     * @param name 属性名称/属性标识
     * @return List<TDDeviceDataResp>
     */
    List<TDDeviceDataResp> getDeviceThingModels(Long id, String name);
}
