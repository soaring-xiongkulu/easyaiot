package com.basiclab.iot.device;

import com.basiclab.iot.common.constant.ServiceNameConstants;
import com.basiclab.iot.common.domain.AjaxResult;
import com.basiclab.iot.device.factory.RemoteProtocolFallbackFactory;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;

/**
 * @program: EasyAIoT
 * @description: 协议管理服务
 * @packagename: com.basiclab.iot.device.api
 * @author: EasyAIoT
 * @emainl: andywebjava@163.com
 * @date: 2024-07-11 15:15
 **/
@FeignClient(contextId = "remoteProtocolService", value = ServiceNameConstants.IOT_DEVICE, fallbackFactory = RemoteProtocolFallbackFactory.class)
public interface RemoteProtocolService {

    /**
     * 刷新协议脚本缓存
     * @return
     */
    @GetMapping("/protocol/protocolScriptCacheRefresh")
    public AjaxResult protocolScriptCacheRefresh();
}
