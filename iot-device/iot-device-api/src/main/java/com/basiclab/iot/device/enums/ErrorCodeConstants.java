package com.basiclab.iot.device.enums;

import com.basiclab.iot.common.exception.ErrorCode;

/**
 * Device 字典类型的枚举类
 * device 系统，使用 1-003-000-000 段
 *
 * @author EasyAIoT
 */
public interface ErrorCodeConstants {

    // ========== 设备模块 1-003-000-000 ==========
    ErrorCode DEVICE_NOT_EXISTS = new ErrorCode(1_003_000_000, "设备不存在");

    // ========== 设备分组模块 1-003-001-000 ==========
    ErrorCode DEVICE_GROUP_NOT_EXISTS = new ErrorCode(1_003_001_000, "设备分组不存在");

    // ========== 设备日志模块 1-003-002-000 ==========
    ErrorCode DEVICE_LOG_NOT_EXISTS = new ErrorCode(1_003_002_000, "设备日志不存在");

    // ========== 设备Topic模块 1-003-002-000 ==========
    ErrorCode DEVICE_TOPIC_NOT_EXISTS = new ErrorCode(1_003_003_000, "设备Topic不存在");

    // ========== OTA记录模块 1-003-002-000 ==========
    ErrorCode OTA_RECORDS_NOT_EXISTS = new ErrorCode(1_003_004_000, "OTA记录不存在");

    // ========== OTA任务模块 1-003-002-000 ==========
    ErrorCode OTA_TASKS_NOT_EXISTS = new ErrorCode(1_003_005_000, "OTA任务不存在");

    // ========== 产品模块 1-003-002-000 ==========
    ErrorCode PRODUCT_NOT_EXISTS = new ErrorCode(1_003_006_000, "产品不存在");

    // ========== 产品命令模块 1-003-002-000 ==========
    ErrorCode PRODUCT_COMMANDS_NOT_EXISTS = new ErrorCode(1_003_007_000, "产品命令不存在");

    // ========== 产品命令请求模块 1_003_008_000 ==========
    ErrorCode PRODUCT_COMMANDS_REQUESTS_NOT_EXISTS = new ErrorCode(1_003_008_000, "产品命令请求不存在");

    // ========== 产品命令响应模块 1-003-002-000 ==========
    ErrorCode PRODUCT_COMMANDS_RESPONSE_NOT_EXISTS = new ErrorCode(1_003_009_000, "产品命令响应不存在");

    // ========== 产品模板模块 1-003-002-000 ==========
    ErrorCode PRODUCT_TEMPLATE_NOT_EXISTS = new ErrorCode(1_003_010_000, "产品模板不存在");

    // ========== 产品类型模块 1-003-002-000 ==========
    ErrorCode PRODUCT_TYPE_NOT_EXISTS = new ErrorCode(1_003_011_000, "产品类型不存在");

    // ========== 协议模块 1-003-002-000 ==========
    ErrorCode PROTOCOL_NOT_EXISTS = new ErrorCode(1_003_012_000, "协议不存在");

    // ========== 规则模块 1-003-002-000 ==========
    ErrorCode RULE_NOT_EXISTS = new ErrorCode(1_003_013_000, "规则不存在");

    // ========== 告警规则模块 1-003-002-000 ==========
    ErrorCode RULE_ALARM_NOT_EXISTS = new ErrorCode(1_003_014_000, "告警规则不存在");

    // ========== 告警规则列表模块 1-003-002-000 ==========
    ErrorCode RULE_ALARM_LIST_NOT_EXISTS = new ErrorCode(1_003_015_000, "告警规则列表不存在");

    // ========== 规则表达式模块 1-003-002-000 ==========
    ErrorCode RULE_CONDITIONS_NOT_EXISTS = new ErrorCode(1_003_016_000, "规则表达式不存在");

    // ========== OTA升级包模块 1-003-002-000 ==========
    ErrorCode OTA_PACKAGES_NOT_EXISTS = new ErrorCode(1_003_017_000, "OTA升级包不存在");

    // ========== 物模型事件模块 1-003-002-000 ==========
    ErrorCode PRODUCT_EVENT_NOT_EXISTS = new ErrorCode(1_003_018_000, "物模型事件不存在");

    // ========== 物模型事件模块 1-003-002-000 ==========
    ErrorCode PRODUCT_EVENT_RESPONSE_NOT_EXISTS = new ErrorCode(1_003_019_000, "物模型事件响应不存在");

    // ========== 物模型事件模块 1-003-002-000 ==========
    ErrorCode PRODUCT_PROPERTIES_NOT_EXISTS = new ErrorCode(1_003_020_000, "物模型属性不存在");

    // ========== 物模型事件模块 1-003-002-000 ==========
    ErrorCode PRODUCT_SERVICES_NOT_EXISTS = new ErrorCode(1_003_021_000, "物模型服务不存在");

    // ========== 计算任务模块 1-003-022-000 ==========
    ErrorCode ALGORITHM_ALARM_DATA_NOT_EXISTS = new ErrorCode(1_003_022_001, "告警数据不存在");
    ErrorCode ALGORITHM_CUSTOMER_NOT_EXISTS = new ErrorCode(1_003_022_002, "客户不存在");
    ErrorCode ALGORITHM_MODEL_NOT_EXISTS = new ErrorCode(1_003_022_003, "模型不存在");
    ErrorCode ALGORITHM_TASK_NOT_EXISTS = new ErrorCode(1_003_022_004, "任务不存在");
    ErrorCode ALGORITHM_PUSH_LOG_NOT_EXISTS = new ErrorCode(1_003_022_005, "推送日志不存在");
    ErrorCode ALGORITHM_VIDEO_NOT_EXISTS = new ErrorCode(1_003_022_006, "设备不存在");
    ErrorCode ALGORITHM_PLAYBACK_NOT_EXISTS = new ErrorCode(1_003_022_007, "回放录像不存在");
    ErrorCode ALGORITHM_NVR_NOT_EXISTS = new ErrorCode(1_003_022_008, "NVR不存在");

}
