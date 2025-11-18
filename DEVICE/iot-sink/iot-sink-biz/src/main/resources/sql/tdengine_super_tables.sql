-- ============================================
-- TDEngine 超级表建表SQL语句
-- 数据库名称: iot_device
-- 说明: 为所有上行Topic创建对应的超级表
-- ============================================

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS iot_device;

-- 使用数据库
USE iot_device;

-- ============================================
-- 1. 属性上报超级表 (PROPERTY_UPSTREAM_REPORT)
-- ============================================
CREATE STABLE IF NOT EXISTS st_property_upstream_report (
    ts TIMESTAMP,
    report_time TIMESTAMP,
    device_id BIGINT,
    server_id NCHAR(50),
    request_id NCHAR(100),
    method NCHAR(100),
    params NCHAR(5000),
    data NCHAR(5000),
    code INT,
    msg NCHAR(500),
    `topic` NCHAR(500)
) TAGS (
    device_identification NCHAR(20),
    tenant_id BIGINT,
    product_identification NCHAR(20)
);

-- ============================================
-- 2. 属性期望值设置ACK超级表 (PROPERTY_UPSTREAM_DESIRED_SET_ACK)
-- ============================================
CREATE STABLE IF NOT EXISTS st_property_upstream_desired_set_ack (
    ts TIMESTAMP,
    report_time TIMESTAMP,
    device_id BIGINT,
    server_id NCHAR(50),
    request_id NCHAR(100),
    method NCHAR(100),
    data NCHAR(5000),
    code INT,
    msg NCHAR(500),
    `topic` NCHAR(500)
) TAGS (
    device_identification NCHAR(20),
    tenant_id BIGINT,
    product_identification NCHAR(20)
);

-- ============================================
-- 3. 属性期望值查询响应超级表 (PROPERTY_UPSTREAM_DESIRED_QUERY_RESPONSE)
-- ============================================
CREATE STABLE IF NOT EXISTS st_property_upstream_desired_query_response (
    ts TIMESTAMP,
    report_time TIMESTAMP,
    device_id BIGINT,
    server_id NCHAR(50),
    request_id NCHAR(100),
    method NCHAR(100),
    data NCHAR(5000),
    code INT,
    msg NCHAR(500),
    `topic` NCHAR(500)
) TAGS (
    device_identification NCHAR(20),
    tenant_id BIGINT,
    product_identification NCHAR(20)
);

-- ============================================
-- 4. 事件上报超级表 (EVENT_UPSTREAM_REPORT)
-- ============================================
CREATE STABLE IF NOT EXISTS st_event_upstream_report (
    ts TIMESTAMP,
    report_time TIMESTAMP,
    device_id BIGINT,
    server_id NCHAR(50),
    request_id NCHAR(100),
    method NCHAR(100),
    params NCHAR(5000),
    data NCHAR(5000),
    code INT,
    msg NCHAR(500),
    `topic` NCHAR(500),
    identifier NCHAR(100)
) TAGS (
    device_identification NCHAR(20),
    tenant_id BIGINT,
    product_identification NCHAR(20),
    identifier NCHAR(100)
);

-- ============================================
-- 5. 服务调用响应超级表 (SERVICE_UPSTREAM_INVOKE_RESPONSE)
-- ============================================
CREATE STABLE IF NOT EXISTS st_service_upstream_invoke_response (
    ts TIMESTAMP,
    report_time TIMESTAMP,
    device_id BIGINT,
    server_id NCHAR(50),
    request_id NCHAR(100),
    method NCHAR(100),
    data NCHAR(5000),
    code INT,
    msg NCHAR(500),
    `topic` NCHAR(500),
    identifier NCHAR(100)
) TAGS (
    device_identification NCHAR(20),
    tenant_id BIGINT,
    product_identification NCHAR(20),
    identifier NCHAR(100)
);

-- ============================================
-- 6. 设备标签上报超级表 (DEVICE_TAG_UPSTREAM_REPORT)
-- ============================================
CREATE STABLE IF NOT EXISTS st_device_tag_upstream_report (
    ts TIMESTAMP,
    report_time TIMESTAMP,
    device_id BIGINT,
    server_id NCHAR(50),
    request_id NCHAR(100),
    method NCHAR(100),
    params NCHAR(5000),
    data NCHAR(5000),
    code INT,
    msg NCHAR(500),
    `topic` NCHAR(500)
) TAGS (
    device_identification NCHAR(20),
    tenant_id BIGINT,
    product_identification NCHAR(20)
);

-- ============================================
-- 7. 设备标签删除超级表 (DEVICE_TAG_UPSTREAM_DELETE)
-- ============================================
CREATE STABLE IF NOT EXISTS st_device_tag_upstream_delete (
    ts TIMESTAMP,
    report_time TIMESTAMP,
    device_id BIGINT,
    server_id NCHAR(50),
    request_id NCHAR(100),
    method NCHAR(100),
    params NCHAR(5000),
    data NCHAR(5000),
    code INT,
    msg NCHAR(500),
    `topic` NCHAR(500)
) TAGS (
    device_identification NCHAR(20),
    tenant_id BIGINT,
    product_identification NCHAR(20)
);

-- ============================================
-- 8. 影子上报超级表 (SHADOW_UPSTREAM_REPORT)
-- ============================================
CREATE STABLE IF NOT EXISTS st_shadow_upstream_report (
    ts TIMESTAMP,
    report_time TIMESTAMP,
    device_id BIGINT,
    server_id NCHAR(50),
    request_id NCHAR(100),
    method NCHAR(100),
    params NCHAR(5000),
    data NCHAR(5000),
    code INT,
    msg NCHAR(500),
    `topic` NCHAR(500)
) TAGS (
    device_identification NCHAR(20),
    tenant_id BIGINT,
    product_identification NCHAR(20)
);

-- ============================================
-- 9. 配置查询超级表 (CONFIG_UPSTREAM_QUERY)
-- ============================================
CREATE STABLE IF NOT EXISTS st_config_upstream_query (
    ts TIMESTAMP,
    report_time TIMESTAMP,
    device_id BIGINT,
    server_id NCHAR(50),
    request_id NCHAR(100),
    method NCHAR(100),
    params NCHAR(5000),
    data NCHAR(5000),
    code INT,
    msg NCHAR(500),
    `topic` NCHAR(500)
) TAGS (
    device_identification NCHAR(20),
    tenant_id BIGINT,
    product_identification NCHAR(20)
);

-- ============================================
-- 10. NTP请求超级表 (NTP_UPSTREAM_REQUEST)
-- ============================================
CREATE STABLE IF NOT EXISTS st_ntp_upstream_request (
    ts TIMESTAMP,
    report_time TIMESTAMP,
    device_id BIGINT,
    server_id NCHAR(50),
    request_id NCHAR(100),
    method NCHAR(100),
    params NCHAR(5000),
    data NCHAR(5000),
    code INT,
    msg NCHAR(500),
    `topic` NCHAR(500)
) TAGS (
    device_identification NCHAR(20),
    tenant_id BIGINT,
    product_identification NCHAR(20)
);

-- ============================================
-- 11. OTA版本上报超级表 (OTA_UPSTREAM_VERSION_REPORT)
-- ============================================
CREATE STABLE IF NOT EXISTS st_ota_upstream_version_report (
    ts TIMESTAMP,
    report_time TIMESTAMP,
    device_id BIGINT,
    server_id NCHAR(50),
    request_id NCHAR(100),
    method NCHAR(100),
    params NCHAR(5000),
    data NCHAR(5000),
    code INT,
    msg NCHAR(500),
    `topic` NCHAR(500)
) TAGS (
    device_identification NCHAR(20),
    tenant_id BIGINT,
    product_identification NCHAR(20)
);

-- ============================================
-- 12. OTA进度上报超级表 (OTA_UPSTREAM_PROGRESS_REPORT)
-- ============================================
CREATE STABLE IF NOT EXISTS st_ota_upstream_progress_report (
    ts TIMESTAMP,
    report_time TIMESTAMP,
    device_id BIGINT,
    server_id NCHAR(50),
    request_id NCHAR(100),
    method NCHAR(100),
    params NCHAR(5000),
    data NCHAR(5000),
    code INT,
    msg NCHAR(500),
    `topic` NCHAR(500)
) TAGS (
    device_identification NCHAR(20),
    tenant_id BIGINT,
    product_identification NCHAR(20)
);

-- ============================================
-- 13. OTA固件查询超级表 (OTA_UPSTREAM_FIRMWARE_QUERY)
-- ============================================
CREATE STABLE IF NOT EXISTS st_ota_upstream_firmware_query (
    ts TIMESTAMP,
    report_time TIMESTAMP,
    device_id BIGINT,
    server_id NCHAR(50),
    request_id NCHAR(100),
    method NCHAR(100),
    params NCHAR(5000),
    data NCHAR(5000),
    code INT,
    msg NCHAR(500),
    `topic` NCHAR(500)
) TAGS (
    device_identification NCHAR(20),
    tenant_id BIGINT,
    product_identification NCHAR(20)
);

