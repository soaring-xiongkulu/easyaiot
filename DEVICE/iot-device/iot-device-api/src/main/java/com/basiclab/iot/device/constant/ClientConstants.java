package com.basiclab.iot.device.constant;

/**
 *  @author 翱翔的雄库鲁 on 2020/9/4
 */
public class ClientConstants {


    /**
     * 成功接入	客户端认证完成并成功接入系统后
     */
    public static final String CLIENT_CONNECTED = "client_connected";

    /**
     * 连接断开	客户端连接层在准备关闭时
     */
    public static final String CLIENT_DISCONNECTED = "client_disconnected";

    /**
     * 订阅主题
     */
    public static final String CLIENT_SUBSCRIBE = "client_subscribe";

    /**
     * 会话订阅主题
     */
    public static final String SESSION_SUBSCRIBED = "session_subscribed";

    /**
     * 设备端MQTT链接的client_id 头部关键字
     */
    public static final String DEVICE_CLIENT_HEAD = "device_";

    /**
     * IOS移动端MQTT链接的client_id头部关键字
     */
    public static final String APP_IOS_CLIENT_HEAD = "app_ios_";

    /**
     * Android移动端MQTT链接的client_id头部关键字
     */
    public static final String APP_ANDROID_CLIENT_HEAD = "app_android_";

    /**
     * WX移动端MQTT链接的client_id头部关键字
     */
    public static final String APP_WX_CLIENT_HEAD = "app_wx_";

    /**
     * IPAD移动端MQTT链接的client_id头部关键字
     */
    public static final String APP_IPAD_CLIENT_HEAD = "app_ipad_";

    /**
     * 设备用户绑定关系操作锁前缀
     */
    public static final String DEVICE_BIND_LOCK_PREFIX = "device_bind_lock:";

    /**
     * 设备用户绑定关系
     */
    public static final String DEVICE_BIND_USERS = "device_bind_users";

    /**
     * mqtt连接客户端时间戳版本
     */
    public static final String MQTT_CLIENT_VERSION = "mqtt_client_version";

    /**
     * 设备mqtt连接状态操作锁前缀
     */
    public static final String DEVICE_ONLINE_LOCK_PREFIX = "device_online_lock:";

    /**
     * 设备mqtt连接状态
     */
    public static final String MQTT_DEVICE_ONLINE_STATUS = "mqtt_device_online_status";

    /**
     * 用户mqtt连接状态操作锁前缀
     */
    public static final String USER_ONLINE_LOCK_PREFIX = "user_online_lock:";

    /**
     * 用户mqtt连接状态
     */
    public static final String MQTT_USER_ONLINE_STATUS = "mqtt_user_online_status";

}
