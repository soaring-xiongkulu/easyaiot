package com.basiclab.iot.device.factory;

import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.device.RemoteProductPropertiesService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.cloud.openfeign.FallbackFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.bind.annotation.RequestParam;

import java.util.List;

/**
 * RemoteProductPropertiesFallbackFactory
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Component
public class RemoteProductPropertiesFallbackFactory implements FallbackFactory<RemoteProductPropertiesService> {

    private static final Logger log = LoggerFactory.getLogger(RemoteProductPropertiesFallbackFactory.class);

    @Override
    public RemoteProductPropertiesService create(Throwable throwable) {
        log.error("产品服务属性管理服务调用失败:{}", throwable.getMessage());
        return new RemoteProductPropertiesService() {
            @Override
            public R<?> selectAllByServiceId(@RequestParam("serviceId") Long serviceId) {
                return R.fail("产品服务属性", throwable.getMessage());
            }
            @Override
            public R<?> selectPropertiesByPropertiesIdList(List<Long> propertiesIdList){
                return R.fail("根据属性id列表获取属性失败", throwable.getMessage());
            }

        };
    }

}
