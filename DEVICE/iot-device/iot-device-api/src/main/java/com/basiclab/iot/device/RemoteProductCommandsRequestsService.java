package com.basiclab.iot.device;

import com.basiclab.iot.common.constant.ServiceNameConstants;
import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.device.factory.RemoteProductCommandsRequestsFallbackFactory;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;

/**
 * RemoteProductCommandsRequestsService
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@FeignClient(contextId = "remoteProductCommandsService", value = ServiceNameConstants.IOT_DEVICE, fallbackFactory = RemoteProductCommandsRequestsFallbackFactory.class)
public interface RemoteProductCommandsRequestsService {

    @GetMapping("/productProperties/selectAllCommandsRequestsByCommandId/{commandId}")
    R<?> selectAllRequestsByCommandId(@RequestParam("commandId") Long commandId);

}
