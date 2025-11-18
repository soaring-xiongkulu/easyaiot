package com.basiclab.iot.sink.service.device;

import cn.hutool.core.bean.BeanUtil;
import cn.hutool.core.lang.Assert;
import com.basiclab.iot.common.core.KeyValue;
import com.basiclab.iot.sink.biz.dto.IotDeviceRespDTO;
import com.basiclab.iot.sink.dal.dataobject.DeviceDO;
import com.basiclab.iot.sink.dal.mapper.DeviceMapper;
import com.google.common.cache.CacheLoader;
import com.google.common.cache.LoadingCache;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.time.Duration;

import static com.basiclab.iot.common.utils.cache.CacheUtils.buildAsyncReloadingCache;

/**
 * DeviceServiceImpl
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Service
@Slf4j
public class DeviceServiceImpl implements DeviceService {

    private static final Duration CACHE_EXPIRE = Duration.ofMinutes(1);

    /**
     * 通过 id 查询设备的缓存
     */
    private final LoadingCache<Long, IotDeviceRespDTO> deviceCaches = buildAsyncReloadingCache(
            CACHE_EXPIRE,
            new CacheLoader<Long, IotDeviceRespDTO>() {
                @Override
                public IotDeviceRespDTO load(Long id) {
                    DeviceDO deviceDO = deviceMapper.selectById(id);
                    Assert.notNull(deviceDO, "设备({}) 不能为空", id);
                    IotDeviceRespDTO device = convertToDTO(deviceDO);
                    // 相互缓存
                    deviceCaches2.put(new KeyValue<>(device.getProductIdentification(), device.getDeviceIdentification()), device);
                    return device;
                }
            });

    /**
     * 通过 productIdentification + deviceIdentification 查询设备的缓存
     */
    private final LoadingCache<KeyValue<String, String>, IotDeviceRespDTO> deviceCaches2 = buildAsyncReloadingCache(
            CACHE_EXPIRE,
            new CacheLoader<KeyValue<String, String>, IotDeviceRespDTO>() {
                @Override
                public IotDeviceRespDTO load(KeyValue<String, String> kv) {
                    DeviceDO deviceDO = deviceMapper.selectByProductIdentificationAndDeviceIdentification(kv.getKey(), kv.getValue());
                    Assert.notNull(deviceDO, "设备({}/{}) 不能为空", kv.getKey(), kv.getValue());
                    IotDeviceRespDTO device = convertToDTO(deviceDO);
                    // 相互缓存
                    deviceCaches.put(device.getId(), device);
                    return device;
                }
            });

    @Resource
    private DeviceMapper deviceMapper;

    @Override
    public IotDeviceRespDTO getDevice(String productIdentification, String deviceIdentification) {
        return deviceCaches2.getUnchecked(new KeyValue<>(productIdentification, deviceIdentification));
    }

    @Override
    public IotDeviceRespDTO getDevice(Long id) {
        return deviceCaches.getUnchecked(id);
    }

    @Override
    public DeviceDO getDeviceForAuth(String clientId, String userName, String password, String deviceStatus, String protocolType) {
        return deviceMapper.selectByClientIdAndUserNameAndPasswordAndDeviceStatusAndProtocolType(
                clientId, userName, password, deviceStatus, protocolType);
    }

    /**
     * 将 DeviceDO 转换为 IotDeviceRespDTO
     */
    private IotDeviceRespDTO convertToDTO(DeviceDO deviceDO) {
        IotDeviceRespDTO dto = new IotDeviceRespDTO();
        dto.setId(deviceDO.getId());
        dto.setProductIdentification(deviceDO.getProductIdentification());
        dto.setDeviceIdentification(deviceDO.getDeviceIdentification());
        dto.setTenantId(deviceDO.getTenantId());
        return dto;
    }
}

