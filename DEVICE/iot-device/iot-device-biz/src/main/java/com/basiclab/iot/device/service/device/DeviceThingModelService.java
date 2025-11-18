package com.basiclab.iot.device.service.device;


import com.basiclab.iot.device.domain.device.vo.TDDeviceDataResp;

import java.util.List;

/**
 * DeviceThingModelService
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
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
