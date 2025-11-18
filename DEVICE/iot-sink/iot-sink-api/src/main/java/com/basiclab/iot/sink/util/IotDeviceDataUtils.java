package com.basiclab.iot.sink.util;

/**
 * IoT 设备数据工具类
 * <p>
 * 用于管理设备数据在 Redis 中的存储格式
 * <p>
 * <b>注意：此类已废弃，请使用 {@link IotSinkRedisKeyConstants} 作为标准的 Redis Key 规范</b>
 * <p>
 * 为了保持向后兼容，此类暂时保留，但建议迁移到新的规范类
 *
 * @author 翱翔的雄库鲁
 * @deprecated 请使用 {@link IotSinkRedisKeyConstants} 替代
 */
@Deprecated
public class IotDeviceDataUtils {

    /**
     * Redis Key 前缀：设备数据
     * 格式：iot_device_data:{deviceId}
     * <p>
     * <b>已废弃，请使用 {@link IotSinkRedisKeyConstants#DEVICE_DATA_KEY_PREFIX}</b>
     */
    @Deprecated
    public static final String REDIS_KEY_PREFIX = "iot_device_data:";

    /**
     * Redis Hash 字段名：连接状态
     * <p>
     * <b>已废弃，请使用 {@link IotSinkRedisKeyConstants#DEVICE_DATA_FIELD_CONNECT_STATUS}</b>
     */
    @Deprecated
    public static final String HASH_FIELD_CONNECT_STATUS = "connect_status";

    /**
     * Redis Hash 字段名：最后在线时间
     * <p>
     * <b>已废弃，请使用 {@link IotSinkRedisKeyConstants#DEVICE_DATA_FIELD_LAST_ONLINE_TIME}</b>
     */
    @Deprecated
    public static final String HASH_FIELD_LAST_ONLINE_TIME = "last_online_time";

    /**
     * Redis Hash 字段名：扩展信息
     * <p>
     * <b>已废弃，请使用 {@link IotSinkRedisKeyConstants#DEVICE_DATA_FIELD_EXTENSION}</b>
     */
    @Deprecated
    public static final String HASH_FIELD_EXTENSION = "extension";

    /**
     * Redis Hash 字段名：设备版本
     * <p>
     * <b>已废弃，请使用 {@link IotSinkRedisKeyConstants#DEVICE_DATA_FIELD_VERSION}</b>
     */
    @Deprecated
    public static final String HASH_FIELD_VERSION = "version";

    /**
     * Redis Hash 字段名：标签信息
     * <p>
     * <b>已废弃，请使用 {@link IotSinkRedisKeyConstants#DEVICE_DATA_FIELD_TAGS}</b>
     */
    @Deprecated
    public static final String HASH_FIELD_TAGS = "tags";

    /**
     * Redis Hash 字段名：影子状态
     * <p>
     * <b>已废弃，请使用 {@link IotSinkRedisKeyConstants#DEVICE_DATA_FIELD_SHADOW}</b>
     */
    @Deprecated
    public static final String HASH_FIELD_SHADOW = "shadow";

    /**
     * Redis Hash 字段名：配置信息
     * <p>
     * <b>已废弃，请使用 {@link IotSinkRedisKeyConstants#DEVICE_DATA_FIELD_CONFIG}</b>
     */
    @Deprecated
    public static final String HASH_FIELD_CONFIG = "config";

    /**
     * Redis Hash 字段名：OTA进度
     * <p>
     * <b>已废弃，请使用 {@link IotSinkRedisKeyConstants#DEVICE_DATA_FIELD_OTA_PROGRESS}</b>
     */
    @Deprecated
    public static final String HASH_FIELD_OTA_PROGRESS = "ota_progress";

    /**
     * 构建设备数据的 Redis Key
     * <p>
     * <b>已废弃，请使用 {@link IotSinkRedisKeyConstants#buildDeviceDataKey(Long)}</b>
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
     * <b>已废弃，请使用 {@link IotSinkRedisKeyConstants#extractDeviceIdFromDataKey(String)}</b>
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

