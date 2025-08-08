

package com.basiclab.iot.device;

import com.basiclab.iot.common.constant.ServiceNameConstants;
import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.device.factory.RemoteCacheOpenAnyFallbackFactory;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;

/**
 * 缓存开放服务
 *
 * @author EasyAIoT
 */
@FeignClient(contextId = "remoteCacheOpenService", value = ServiceNameConstants.IOT_DEVICE, fallbackFactory = RemoteCacheOpenAnyFallbackFactory.class, path = "/cache/open/any")
public interface RemoteCacheOpenAnyService {

    /**
     * Refreshes the cache for all devices within a tenant.
     *
     * @return Response indicating the operation was successful.
     */
    @GetMapping("/refreshAllDeviceCaches")
    R refreshAllDeviceCaches();

    /**
     * Refreshes the cache for sub devices within a tenant.
     *
     * @return Response indicating the operation was successful.
     */
    @GetMapping("/refreshAllDeviceInfoCaches")
    R refreshAllDeviceInfoCaches();

    /**
     * Refreshes the cache for all products within a tenant.
     *
     * @return Response indicating the operation was successful.
     */
    @GetMapping("/refreshAllProductCaches")
    R refreshAllProductCaches();

    /**
     * Refreshes the cache for all product models within a tenant.
     *
     * @return Response indicating the operation was successful.
     */
    @GetMapping("/refreshAllProductModelCaches")
    R refreshAllProductModelCaches();


}
