package com.basiclab.iot.sink.util;

/**
 * IoT 设备 ServerId 工具类
 * <p>
 * 用于管理设备与网关 serverId 的映射关系
 * <p>
 * <b>注意：此类已废弃，请使用 {@link IotSinkRedisKeyConstants} 作为标准的 Redis Key 规范</b>
 * <p>
 * 为了保持向后兼容，此类暂时保留，但建议迁移到新的规范类
 *
 * @author 翱翔的雄库鲁
 * @deprecated 请使用 {@link IotSinkRedisKeyConstants} 替代
 */
@Deprecated
public class IotDeviceServerIdUtils {

    /**
     * Redis Key 前缀：设备 ID -> ServerId 映射
     * 格式：iot_device_server_id:{deviceId}
     * <p>
     * <b>已废弃，请使用 {@link IotSinkRedisKeyConstants#DEVICE_SERVER_ID_KEY_PREFIX}</b>
     */
    @Deprecated
    public static final String REDIS_KEY_PREFIX = "iot_device_server_id:";

    /**
     * 构建设备 ServerId 的 Redis Key
     * <p>
     * <b>已废弃，请使用 {@link IotSinkRedisKeyConstants#buildDeviceServerIdKey(Long)}</b>
     *
     * @param deviceId 设备 ID
     * @return Redis Key
     */
    @Deprecated
    public static String buildRedisKey(Long deviceId) {
        return REDIS_KEY_PREFIX + deviceId;
    }

    /**
     * 从 Redis Key 中提取设备 ID
     * <p>
     * <b>已废弃，请使用 {@link IotSinkRedisKeyConstants#extractDeviceIdFromServerIdKey(String)}</b>
     *
     * @param redisKey Redis Key
     * @return 设备 ID，如果格式不正确返回 null
     */
    @Deprecated
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

