package com.basiclab.iot.device.service.product_properties;



import com.basiclab.iot.device.controller.admin.device.vo.TDDeviceDataResp;

import java.util.List;

/**
 * @author Basiclab
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
