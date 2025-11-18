package com.basiclab.iot.device.factory;

import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.device.RemoteAppService;
import com.basiclab.iot.device.domain.app.vo.App;
import lombok.extern.slf4j.Slf4j;
import org.springframework.cloud.openfeign.FallbackFactory;
import org.springframework.stereotype.Component;

/**
 * RemoteAppFallbackFactory
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Component
@Slf4j
public class RemoteAppFallbackFactory implements FallbackFactory<RemoteAppService> {

    @Override
    public RemoteAppService create(Throwable throwable) {
        log.error("应用密钥服务调用失败", throwable);
        return new RemoteAppService() {
            @Override
            public R<App> getAppByAppId(String appId) {
                return R.fail("获取应用信息失败：" + throwable.getMessage());
            }

            @Override
            public R<App> verifyApp(String appId, String appKey, String appSecret) {
                return R.fail("验证应用密钥失败：" + throwable.getMessage());
            }
        };
    }
}

