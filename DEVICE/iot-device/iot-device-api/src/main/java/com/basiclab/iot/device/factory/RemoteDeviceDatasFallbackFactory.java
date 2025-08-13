package com.basiclab.iot.device.factory;

import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.device.RemoteDeviceDatasService;
import com.basiclab.iot.device.domain.device.vo.DeviceServiceRecord;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.cloud.openfeign.FallbackFactory;
import org.springframework.stereotype.Component;

/**
 * 设备消息服务降级处理
 *
 * @author EasyAIoT
 */
@Component
public class RemoteDeviceDatasFallbackFactory implements FallbackFactory<RemoteDeviceDatasService> {
    private static final Logger log = LoggerFactory.getLogger(RemoteDeviceDatasFallbackFactory.class);

    @Override
    public RemoteDeviceDatasService create(Throwable throwable) {
        log.error("设备消息服务调用失败:{}", throwable.getMessage());
        return new RemoteDeviceDatasService() {
            @Override
            public R add(DeviceServiceRecord mqttsDeviceServiceRecord) {
                return R.fail("新增设备消息失败:" + throwable.getMessage());
            }

        };
    }
}
