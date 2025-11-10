package com.basiclab.iot.device.factory;

import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.device.RemoteDeviceActionService;
import com.basiclab.iot.device.domain.device.vo.DeviceEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.cloud.openfeign.FallbackFactory;
import org.springframework.stereotype.Component;

/**
 * 设备动作服务降级处理
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Component
public class RemoteDeviceActionFallbackFactory implements FallbackFactory<RemoteDeviceActionService> {
    private static final Logger log = LoggerFactory.getLogger(RemoteDeviceActionFallbackFactory.class);

    @Override
    public RemoteDeviceActionService create(Throwable throwable) {
        log.error("设备消息服务调用失败:{}", throwable.getMessage());
        return new RemoteDeviceActionService() {
            @Override
            public R add(DeviceEvent mqttsDeviceEvent) {
                return R.fail("新增设备动作失败:" + throwable.getMessage());
            }
        };
    }
}
