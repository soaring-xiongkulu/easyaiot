package com.basiclab.iot.sink.util;

/**
 * IoT 设备 ServerId 工具类
 * <p>
 * 用于管理设备与网关 serverId 的映射关系
 *
 * @author 翱翔的雄库鲁
 */
public class IotDeviceServerIdUtils {

    /**
     * Redis Key 前缀：设备 ID -> ServerId 映射
     * 格式：iot_device_server_id:{deviceId}
     */
    public static final String REDIS_KEY_PREFIX = "iot_device_server_id:";

    /**
     * 构建设备 ServerId 的 Redis Key
     *
     * @param deviceId 设备 ID
     * @return Redis Key
     */
    public static String buildRedisKey(Long deviceId) {
        return REDIS_KEY_PREFIX + deviceId;
    }

    /**
     * 从 Redis Key 中提取设备 ID
     *
     * @param redisKey Redis Key
     * @return 设备 ID，如果格式不正确返回 null
     */
    public static Long extractDeviceId(String redisKey) {
        if (redisKey == null || !redisKey.startsWith(REDIS_KEY_PREFIX)) {
            return null;
        }
        try {
            String deviceIdStr = redisKey.substring(REDIS_KEY_PREFIX.length());
            return Long.parseLong(deviceIdStr);
        } catch (NumberFormatException e) {
            return null;
        }
    }

}

