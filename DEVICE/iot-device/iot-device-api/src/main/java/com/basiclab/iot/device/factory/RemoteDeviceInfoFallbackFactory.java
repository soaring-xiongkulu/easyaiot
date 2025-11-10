package com.basiclab.iot.device.factory;

import com.basiclab.iot.common.domain.AjaxResult;
import com.basiclab.iot.device.RemoteDeviceInfoService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.cloud.openfeign.FallbackFactory;
import org.springframework.stereotype.Component;

/**
 * 子设备管理服务降级处理
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Component
public class RemoteDeviceInfoFallbackFactory implements FallbackFactory<RemoteDeviceInfoService> {
    private static final Logger log = LoggerFactory.getLogger(RemoteDeviceInfoFallbackFactory.class);

    @Override
    public RemoteDeviceInfoService create(Throwable throwable) {
        log.error("子设备管理服务调用失败:{}", throwable.getMessage());
        return new RemoteDeviceInfoService() {

            /**
             * 刷新子设备数据模型
             * @param ids
             * @return
             */
            @Override
            public AjaxResult refreshDeviceInfoDataModel(Long[] ids) {
                return AjaxResult.error("刷新子设备数据模型失败:" + throwable.getMessage());
            }

        };
    }
}
