package com.basiclab.iot.common.constant;

/**
 * redis缓存的key 常量
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public class CacheConstants {
    /**
     * 权限缓存前缀
     */
    public final static String LOGIN_TOKEN_KEY = "login_tokens:";


    /**
     * 设备信息 cache key
     * link-> def_device:deviceIdentification
     */
    public static final String DEF_DEVICE = "def_device:";

    /**
     * 全局产品信息 前缀
     * link-> def_product:productIdentification
     */
    public static final String DEF_PRODUCT = "def_product:";

    /**
     * 全局产品模型 前缀
     * link-> def_product_model:productIdentification
     */
    public static final String DEF_PRODUCT_MODEL = "def_product_model:";

    /**
     * 全局产品模型超级表 前缀
     * link-> def_product_model_super_table:productIdentification:serviceCode:deviceIdentification
     */
    public static final String DEF_PRODUCT_MODEL_SUPER_TABLE = "def_product_model_super_table:";

    /**
     * 智能盒子设备状态 前缀
     */
    public static final String DEF_DEVICE_STATE = "def_device_state:";

    /**
     * 智能盒子设备日志-时间索引-前缀
     */
    public static final String DEF_DEVICE_LOG_COUNTER = "def_device_log_counter:";
    public static final String DEF_DEVICE_LOG_TIME_INDEX = "def_device_log_time_index:";
    public static final String DEF_DEVICE_LOG_DETAIL = "def_device_log_detail:";

    /**
     * 智能盒子设备地址 前缀
     */
    public static final String DEF_DEVICE_ADDRESS = "def_device_address:";

    /**
     * TDengine superTableFields cache key
     * link-> def_tdengine_superTableFields:productIdentification:serviceCode:deviceIdentification
     */
    public static final String DEF_TDENGINE_SUPERTABLEFILELDS = "def_tdengine_superTableFields:";


    /**
     * 设备数据转换脚本 cache key
     * link-> def_device_data_reported_agreement_script:deviceIdentification
     */
    public static final String DEF_DEVICE_DATA_REPORTED_AGREEMENT_SCRIPT = "def_device_data_reported_agreement_script:";

    public static final String CATALOG_DATA_CATCH = "catalog_data_catch";

    /**
     * 语音广播消息管理类
     */
    public static final String AUDIO_BROADCAST_MANAGER = "audio_broadcast_manager";

}
