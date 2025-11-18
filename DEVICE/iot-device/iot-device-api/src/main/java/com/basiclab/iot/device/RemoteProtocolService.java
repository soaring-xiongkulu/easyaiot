package com.basiclab.iot.device;

import com.basiclab.iot.common.constant.ServiceNameConstants;
import com.basiclab.iot.common.domain.AjaxResult;
import com.basiclab.iot.device.factory.RemoteProtocolFallbackFactory;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;

/**
 * RemoteProtocolService
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@FeignClient(contextId = "remoteProtocolService", value = ServiceNameConstants.IOT_DEVICE, fallbackFactory = RemoteProtocolFallbackFactory.class)
public interface RemoteProtocolService {

    /**
     * 刷新协议脚本缓存
     * @return
     */
    @GetMapping("/protocol/protocolScriptCacheRefresh")
    public AjaxResult protocolScriptCacheRefresh();
}
