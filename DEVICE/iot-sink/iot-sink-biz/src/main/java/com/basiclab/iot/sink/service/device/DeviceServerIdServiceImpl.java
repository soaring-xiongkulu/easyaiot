package com.basiclab.iot.sink.service.device;

import com.basiclab.iot.common.service.RedisService;
import com.basiclab.iot.sink.service.DeviceServerIdService;
import com.basiclab.iot.sink.util.IotSinkRedisKeyConstants;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.concurrent.TimeUnit;

/**
 * DeviceServerIdServiceImpl
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Service
@Slf4j
@RequiredArgsConstructor
public class DeviceServerIdServiceImpl implements DeviceServerIdService {

    /**
     * 映射过期时间：7天（设备可能长时间在线）
     */
    private static final long EXPIRE_TIME = IotSinkRedisKeyConstants.DEVICE_SERVER_ID_EXPIRE_DAYS;
    private static final TimeUnit EXPIRE_TIME_UNIT = TimeUnit.DAYS;

    private final RedisService redisService;

    @Override
    public void saveDeviceServerId(Long deviceId, String serverId) {
        if (deviceId == null || serverId == null) {
            log.warn("[saveDeviceServerId][设备 ID 或 serverId 为空，忽略保存，deviceId: {}，serverId: {}]",
                    deviceId, serverId);
            return;
        }

        String redisKey = IotSinkRedisKeyConstants.buildDeviceServerIdKey(deviceId);
        redisService.setCacheObject(redisKey, serverId, EXPIRE_TIME, EXPIRE_TIME_UNIT);
        log.debug("[saveDeviceServerId][保存设备 serverId 映射，设备 ID: {}，serverId: {}]", deviceId, serverId);
    }

    @Override
    public String getDeviceServerId(Long deviceId) {
        if (deviceId == null) {
            return null;
        }

        String redisKey = IotSinkRedisKeyConstants.buildDeviceServerIdKey(deviceId);
        String serverId = redisService.getCacheObject(redisKey);
        if (serverId != null) {
            log.debug("[getDeviceServerId][获取设备 serverId，设备 ID: {}，serverId: {}]", deviceId, serverId);
        } else {
            log.debug("[getDeviceServerId][设备 serverId 不存在，设备 ID: {}]", deviceId);
        }
        return serverId;
    }

    @Override
    public void removeDeviceServerId(Long deviceId) {
        if (deviceId == null) {
            return;
        }

        String redisKey = IotSinkRedisKeyConstants.buildDeviceServerIdKey(deviceId);
        redisService.deleteObject(redisKey);
        log.debug("[removeDeviceServerId][删除设备 serverId 映射，设备 ID: {}]", deviceId);
    }

}

