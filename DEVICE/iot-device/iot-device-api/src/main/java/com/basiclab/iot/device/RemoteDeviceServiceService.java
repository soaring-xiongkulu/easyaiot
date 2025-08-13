package com.basiclab.iot.device;

import com.basiclab.iot.common.constant.ServiceNameConstants;
import com.basiclab.iot.common.domain.AjaxResult;
import com.basiclab.iot.device.domain.device.vo.DeviceServiceRecord;
import com.basiclab.iot.device.factory.RemoteDeviceFallbackFactory;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;

/**
 * @author EasyAIoT
 * @desc    设备服务记录
 * @created 2025-06-17
 */
@FeignClient(contextId = "RemoteDeviceServiceService", value = ServiceNameConstants.IOT_DEVICE, fallbackFactory = RemoteDeviceFallbackFactory.class, path = "/deviceService")
public interface RemoteDeviceServiceService {

    /**
     * 编辑更新对应的信息
     * @param deviceServiceRecord
     * @return
     */
    @PostMapping("/editByDeviceIdentification")
    public AjaxResult editByDeviceIdentification(@RequestBody DeviceServiceRecord deviceServiceRecord);


}
