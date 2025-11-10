package com.basiclab.iot.device.cache.service;

import cn.hutool.core.bean.BeanUtil;
import com.basiclab.iot.common.constant.CacheConstants;
import com.basiclab.iot.common.service.RedisService;
import com.basiclab.iot.common.utils.bean.BeanPlusUtil;
import com.basiclab.iot.device.cache.CacheSuperAbstract;
import com.basiclab.iot.device.domain.device.vo.Device;
import com.basiclab.iot.device.domain.device.vo.DeviceCacheVO;
import com.basiclab.iot.device.domain.device.vo.ProductCacheVO;
import com.basiclab.iot.device.service.device.DeviceInfoService;
import com.basiclab.iot.device.service.device.DeviceService;
import com.basiclab.iot.device.service.product.ProductService;
import com.github.pagehelper.PageHelper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;
import java.util.stream.IntStream;


/**
 * 设备缓存处理
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class DeviceCacheService extends CacheSuperAbstract {
    private final RedisService redisService;
    private final DeviceService deviceService;
    private final DeviceInfoService deviceInfoService;
    private final ProductService productService;


    /**
     * Refresh the cache with device data for a specific tenant.
     */
    public void refreshDeviceCacheForTenant() {
        int totalDataCount = deviceService.findDeviceTotal().intValue();
        int totalPages = (int) Math.ceil((double) totalDataCount / PAGE_SIZE);
        List<Device> deviceList = IntStream.range(0, totalPages).mapToObj(currentPage -> {
                    PageHelper.startPage(currentPage + 1, PAGE_SIZE);
                    return deviceService.findDevices();
                })
                .flatMap(Collection::stream)
                .collect(Collectors.toList());

        cacheDevicesForTenant(deviceList);
    }

    /**
     * Cache a list of devices for a specific tenant.
     *
     * @param deviceList List of devices to be cached.
     */
    public void cacheDevicesForTenant(List<Device> deviceList) {
        Optional.ofNullable(deviceList)
                .orElse(Collections.emptyList())
                .stream()
                .filter(Objects::nonNull)
                .map(this::transformToDeviceCacheVO)
                .forEach(deviceCacheVO -> {
                    cacheDeviceBasedOnIdentification(deviceCacheVO);
                    cacheDeviceBasedOnClientId(deviceCacheVO);
                });
    }

    /**
     * Transforms a device object into a DeviceCacheVO object with associated product data.
     *
     * @param device Device object to be transformed.
     * @return Transformed DeviceCacheVO object.
     */
    public DeviceCacheVO transformToDeviceCacheVO(Device device) {
        DeviceCacheVO deviceCacheVO = BeanUtil.toBeanIgnoreError(device, DeviceCacheVO.class);

        Optional.ofNullable(deviceCacheVO.getProductIdentification())
                .map(productService::findOneByProductIdentification)
                .ifPresent(product -> {
                    ProductCacheVO productCacheVO = BeanPlusUtil.toBeanIgnoreError(product, ProductCacheVO.class);
                    deviceCacheVO.setProductCacheVO(productCacheVO);
                });

        return deviceCacheVO;
    }

    /**
     * Cache the DeviceCacheVO object based on its identification.
     *
     * @param deviceCacheVO DeviceCacheVO object to be cached.
     */
    private void cacheDeviceBasedOnIdentification(DeviceCacheVO deviceCacheVO) {
        String cacheKey = CacheConstants.DEF_DEVICE + deviceCacheVO.getDeviceIdentification();
        redisService.delete(cacheKey);
        redisService.setCacheObject(cacheKey, deviceCacheVO, THIRTY_MINUTES, TimeUnit.MINUTES);
    }

    /**
     * Cache the DeviceCacheVO object based on its client ID.
     *
     * @param deviceCacheVO DeviceCacheVO object to be cached.
     */
    private void cacheDeviceBasedOnClientId(DeviceCacheVO deviceCacheVO) {
        String cacheKey = CacheConstants.DEF_DEVICE + deviceCacheVO.getClientId();
        redisService.delete(cacheKey);
        redisService.setCacheObject(cacheKey, deviceCacheVO, THIRTY_MINUTES, TimeUnit.MINUTES);
    }
}
