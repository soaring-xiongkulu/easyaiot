package com.basiclab.iot.device;

import com.basiclab.iot.common.constant.ServiceNameConstants;
import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.device.domain.device.vo.DeviceEvent;
import com.basiclab.iot.device.factory.RemoteDeviceActionFallbackFactory;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;

/**
 * 设备动作服务
 *
 * @author EasyAIoT
 */
@FeignClient(contextId = "remoteDeviceActionService", value = ServiceNameConstants.IOT_DEVICE, fallbackFactory = RemoteDeviceActionFallbackFactory.class)
public interface RemoteDeviceActionService {

    /**
     * 新增设备动作
     *
     * @param mqttsDeviceEvent
     * @return
     */
    @PostMapping("/action")
    public R add(@RequestBody DeviceEvent mqttsDeviceEvent);
}
