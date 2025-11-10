package com.basiclab.iot.device.factory;

import com.basiclab.iot.common.domain.AjaxResult;
import com.basiclab.iot.device.RemoteDeviceServiceService;
import com.basiclab.iot.device.domain.device.vo.DeviceServiceRecord;
import lombok.extern.slf4j.Slf4j;
import org.springframework.cloud.openfeign.FallbackFactory;
import org.springframework.stereotype.Component;


/**
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @desc
 * @created 2025-06-17
 */
@Slf4j
@Component
public class RemoteDeviceServiceFallbackFactory implements FallbackFactory<RemoteDeviceServiceService> {

    @Override
    public RemoteDeviceServiceService create(Throwable throwable) {
        log.error("设备管理开放服务调用失败:{}", throwable.getMessage());
        return new RemoteDeviceServiceService() {
            @Override
            public AjaxResult editByDeviceIdentification(DeviceServiceRecord deviceServiceRecord) {
                return AjaxResult.error("编辑DeviceServiceRecord失败: " + deviceServiceRecord);
            }
        };

    }


}
