package com.basiclab.iot.device.factory;

import com.basiclab.iot.common.domain.AjaxResult;
import com.basiclab.iot.device.RemoteProtocolService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.cloud.openfeign.FallbackFactory;
import org.springframework.stereotype.Component;

/**
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @program: EasyAIoT
 * @description: 协议管理服务降级处理
 * @packagename: com.basiclab.iot.device.api.factory
 * @date: 2025-07-11 15:17
 **/
@Component
public class RemoteProtocolFallbackFactory implements FallbackFactory<RemoteProtocolService> {
    private static final Logger log = LoggerFactory.getLogger(RemoteProtocolFallbackFactory.class);


    @Override
    public RemoteProtocolService create(Throwable throwable) {
        log.error("协议管理服务调用失败:{}", throwable.getMessage());
        return new RemoteProtocolService() {
            @Override
            public AjaxResult protocolScriptCacheRefresh() {
                return AjaxResult.error("协议脚本缓存刷新失败:" + throwable.getMessage());
            }
        };
    }

}
