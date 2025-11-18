package com.basiclab.iot.device;

import com.basiclab.iot.common.constant.ServiceNameConstants;
import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.device.domain.app.vo.App;
import com.basiclab.iot.device.factory.RemoteAppFallbackFactory;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;

/**
 * RemoteAppService
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@FeignClient(contextId = "remoteAppService", value = ServiceNameConstants.IOT_DEVICE, fallbackFactory = RemoteAppFallbackFactory.class)
public interface RemoteAppService {

    /**
     * 根据AppId获取应用信息
     *
     * @param appId 应用ID
     * @return 应用信息
     */
    @GetMapping("/app/get-by-app-id")
    R<App> getAppByAppId(@RequestParam("appId") String appId);

    /**
     * 验证AppId、AppKey、AppSecret
     *
     * @param appId     应用ID
     * @param appKey    应用密钥
     * @param appSecret 应用密钥
     * @return 应用信息
     */
    @PostMapping("/app/verify")
    R<App> verifyApp(@RequestParam("appId") String appId,
                     @RequestParam("appKey") String appKey,
                     @RequestParam("appSecret") String appSecret);
}

