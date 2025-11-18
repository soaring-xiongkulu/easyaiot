package com.basiclab.iot.device;

import com.basiclab.iot.common.constant.ServiceNameConstants;
import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.device.factory.RemoteProductPropertiesFallbackFactory;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;

import java.util.List;

/**
 * RemoteProductPropertiesService
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@FeignClient(contextId = "RemoteProductPropertiesService", value = ServiceNameConstants.IOT_DEVICE, fallbackFactory = RemoteProductPropertiesFallbackFactory.class)
public interface RemoteProductPropertiesService {

    @GetMapping("/productProperties/selectAllPropertiesByServiceId/{serviceId}")
    R<?> selectAllByServiceId(@RequestParam("serviceId") Long serviceId);

    @PostMapping("/productProperties/selectPropertiesByPropertiesIdList")
    R<?> selectPropertiesByPropertiesIdList(@RequestBody List<Long> propertiesIdList);
}
