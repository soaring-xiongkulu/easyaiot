package com.basiclab.iot.sink.util;

/**
 * IoT Sink Redis Key 规范常量类
 * <p>
 * 统一管理 iot-sink 模块中所有 Redis Key 的格式规范，供其他模块使用
 * <p>
 * Key 命名规范：
 * <ul>
 *     <li>使用小写字母和下划线</li>
 *     <li>格式：{模块前缀}:{业务类型}:{标识符}</li>
 *     <li>模块前缀统一使用：iot_sink</li>
 * </ul>
 *
 * @author 翱翔的雄库鲁
 */
public class IotSinkRedisKeyConstants {

    /**
     * 模块前缀
     */
    private static final String MODULE_PREFIX = "iot_sink";

    // ========== 设备相关 Key ==========

    /**
     * 设备数据 Key 前缀
     * <p>
     * 格式：iot_device_data:{deviceId}
     * <p>
     * 注意：为了保持向后兼容，当前使用旧格式。未来版本将迁移到新格式：iot_sink:device:data:{deviceId}
     * <p>
     * 存储类型：Hash
     * <p>
     * Hash 字段：
     * <ul>
     *     <li>connect_status: 连接状态（ONLINE/OFFLINE）</li>
     *     <li>last_online_time: 最后在线时间（yyyy-MM-dd HH:mm:ss）</li>
     *     <li>extension: 扩展信息（JSON字符串，包含 properties、desired、events 等）</li>
     *     <li>version: 设备版本</li>
     *     <li>tags: 标签信息（JSON字符串）</li>
     *     <li>shadow: 影子状态（JSON字符串）</li>
     *     <li>config: 配置信息（JSON字符串）</li>
     *     <li>ota_progress: OTA进度（JSON字符串）</li>
     * </ul>
     * <p>
     * 过期时间：30天
     */
    public static final String DEVICE_DATA_KEY_PREFIX = "iot_device_data:";

    /**
     * 设备 ServerId 映射 Key 前缀
     * <p>
     * 格式：iot_device_server_id:{deviceId}
     * <p>
     * 注意：为了保持向后兼容，当前使用旧格式。未来版本将迁移到新格式：iot_sink:device:server_id:{deviceId}
     * <p>
     * 存储类型：String
     * <p>
     * 值：serverId（网关标识）
     * <p>
     * 过期时间：7天
     */
    public static final String DEVICE_SERVER_ID_KEY_PREFIX = "iot_device_server_id:";

    // ========== Key 构建方法 ==========

    /**
     * 构建设备数据的 Redis Key
     *
     * @param deviceId 设备 ID
     * @return Redis Key，格式：iot_sink:device:data:{deviceId}
     */
    public static String buildDeviceDataKey(Long deviceId) {
        if (deviceId == null) {
            throw new IllegalArgumentException("设备 ID 不能为空");
        }
        return DEVICE_DATA_KEY_PREFIX + deviceId;
    }

    /**
     * 构建设备 ServerId 映射的 Redis Key
     *
     * @param deviceId 设备 ID
     * @return Redis Key，格式：iot_sink:device:server_id:{deviceId}
     */
    public static String buildDeviceServerIdKey(Long deviceId) {
        if (deviceId == null) {
            throw new IllegalArgumentException("设备 ID 不能为空");
        }
        return DEVICE_SERVER_ID_KEY_PREFIX + deviceId;
    }

    // ========== Key 解析方法 ==========

    /**
     * 从设备数据 Key 中提取设备 ID
     *
     * @param redisKey Redis Key
     * @return 设备 ID，如果格式不正确返回 null
     */
    public static Long extractDeviceIdFromDataKey(String redisKey) {
        if (redisKey == null || !redisKey.startsWith(DEVICE_DATA_KEY_PREFIX)) {
            return null;
        }
        try {
            String deviceIdStr = redisKey.substring(DEVICE_DATA_KEY_PREFIX.length());
            return Long.parseLong(deviceIdStr);
        } catch (NumberFormatException e) {
            return null;
        }
    }

    /**
     * 从设备 ServerId Key 中提取设备 ID
     *
     * @param redisKey Redis Key
     * @return 设备 ID，如果格式不正确返回 null
     */
    public static Long extractDeviceIdFromServerIdKey(String redisKey) {
        if (redisKey == null || !redisKey.startsWith(DEVICE_SERVER_ID_KEY_PREFIX)) {
            return null;
        }
        try {
            String deviceIdStr = redisKey.substring(DEVICE_SERVER_ID_KEY_PREFIX.length());
            return Long.parseLong(deviceIdStr);
        } catch (NumberFormatException e) {
            return null;
        }
    }

    // ========== Hash 字段常量 ==========

    /**
     * 设备数据 Hash 字段：连接状态
     */
    public static final String DEVICE_DATA_FIELD_CONNECT_STATUS = "connect_status";

    /**
     * 设备数据 Hash 字段：最后在线时间
     */
    public static final String DEVICE_DATA_FIELD_LAST_ONLINE_TIME = "last_online_time";

    /**
     * 设备数据 Hash 字段：扩展信息
     */
    public static final String DEVICE_DATA_FIELD_EXTENSION = "extension";

    /**
     * 设备数据 Hash 字段：设备版本
     */
    public static final String DEVICE_DATA_FIELD_VERSION = "version";

    /**
     * 设备数据 Hash 字段：标签信息
     */
    public static final String DEVICE_DATA_FIELD_TAGS = "tags";

    /**
     * 设备数据 Hash 字段：影子状态
     */
    public static final String DEVICE_DATA_FIELD_SHADOW = "shadow";

    /**
     * 设备数据 Hash 字段：配置信息
     */
    public static final String DEVICE_DATA_FIELD_CONFIG = "config";

    /**
     * 设备数据 Hash 字段：OTA进度
     */
    public static final String DEVICE_DATA_FIELD_OTA_PROGRESS = "ota_progress";

    // ========== 过期时间常量 ==========

    /**
     * 设备数据过期时间（天）
     */
    public static final long DEVICE_DATA_EXPIRE_DAYS = 30;

    /**
     * 设备 ServerId 映射过期时间（天）
     */
    public static final long DEVICE_SERVER_ID_EXPIRE_DAYS = 7;

    // ========== 私有构造函数，防止实例化 ==========

    private IotSinkRedisKeyConstants() {
        throw new UnsupportedOperationException("工具类不允许实例化");
    }
}

