package com.basiclab.iot.device;

import com.basiclab.iot.common.constant.ServiceNameConstants;
import com.basiclab.iot.common.domain.AjaxResult;
import com.basiclab.iot.device.factory.RemoteDeviceInfoFallbackFactory;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;

/**
 * 子设备管理服务
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@FeignClient(contextId = "remoteDeviceInfoService", value = ServiceNameConstants.IOT_DEVICE, fallbackFactory = RemoteDeviceInfoFallbackFactory.class)
public interface RemoteDeviceInfoService {

    /**
     * 刷新子设备数据模型
     *
     * @param ids
     * @return
     */
    @GetMapping("/deviceInfo/refreshDeviceInfoDataModel")
    public AjaxResult refreshDeviceInfoDataModel(@RequestParam(name = "ids", required = false) Long[] ids);




}
