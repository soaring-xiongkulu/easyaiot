-- 设备服务调用响应表
-- 用于存储平台调用设备服务后，设备返回的ACK消息

CREATE TABLE IF NOT EXISTS public.device_service_invoke_response (
    id BIGSERIAL NOT NULL,
    message_id VARCHAR(255) NOT NULL, -- 消息编号（来自IotDeviceMessage.id）
    device_id BIGINT NOT NULL, -- 设备编号
    device_identification VARCHAR(255) NULL, -- 设备标识
    product_identification VARCHAR(255) NULL, -- 产品标识
    service_identifier VARCHAR(255) NULL, -- 服务标识（从topic中提取的identifier）
    request_id VARCHAR(255) NULL, -- 请求编号（来自IotDeviceMessage.requestId）
    method VARCHAR(255) NULL, -- 请求方法（来自IotDeviceMessage.method，通常是thing.service.invoke）
    response_data TEXT NULL, -- 响应数据（来自IotDeviceMessage.data，JSON格式）
    response_code INTEGER NULL, -- 响应错误码（来自IotDeviceMessage.code）
    response_msg VARCHAR(500) NULL, -- 响应消息（来自IotDeviceMessage.msg）
    topic VARCHAR(500) NULL, -- MQTT Topic
    report_time TIMESTAMP NULL, -- 上报时间（来自IotDeviceMessage.reportTime）
    tenant_id BIGINT DEFAULT 0 NOT NULL, -- 租户编号
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL, -- 创建时间
    CONSTRAINT device_service_invoke_response_pkey PRIMARY KEY (id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_device_service_invoke_response_message_id ON public.device_service_invoke_response(message_id);
CREATE INDEX IF NOT EXISTS idx_device_service_invoke_response_device_id ON public.device_service_invoke_response(device_id);
CREATE INDEX IF NOT EXISTS idx_device_service_invoke_response_device_identification ON public.device_service_invoke_response(device_identification);
CREATE INDEX IF NOT EXISTS idx_device_service_invoke_response_tenant_id ON public.device_service_invoke_response(tenant_id);
CREATE INDEX IF NOT EXISTS idx_device_service_invoke_response_create_time ON public.device_service_invoke_response(create_time);

-- 表注释
COMMENT ON TABLE public.device_service_invoke_response IS '设备服务调用响应表，用于存储平台调用设备服务后，设备返回的ACK消息';

-- 列注释
COMMENT ON COLUMN public.device_service_invoke_response.id IS '主键ID';
COMMENT ON COLUMN public.device_service_invoke_response.message_id IS '消息编号（来自IotDeviceMessage.id）';
COMMENT ON COLUMN public.device_service_invoke_response.device_id IS '设备编号';
COMMENT ON COLUMN public.device_service_invoke_response.device_identification IS '设备标识';
COMMENT ON COLUMN public.device_service_invoke_response.product_identification IS '产品标识';
COMMENT ON COLUMN public.device_service_invoke_response.service_identifier IS '服务标识（从topic中提取的identifier）';
COMMENT ON COLUMN public.device_service_invoke_response.request_id IS '请求编号（来自IotDeviceMessage.requestId）';
COMMENT ON COLUMN public.device_service_invoke_response.method IS '请求方法（来自IotDeviceMessage.method，通常是thing.service.invoke）';
COMMENT ON COLUMN public.device_service_invoke_response.response_data IS '响应数据（来自IotDeviceMessage.data，JSON格式）';
COMMENT ON COLUMN public.device_service_invoke_response.response_code IS '响应错误码（来自IotDeviceMessage.code）';
COMMENT ON COLUMN public.device_service_invoke_response.response_msg IS '响应消息（来自IotDeviceMessage.msg）';
COMMENT ON COLUMN public.device_service_invoke_response.topic IS 'MQTT Topic';
COMMENT ON COLUMN public.device_service_invoke_response.report_time IS '上报时间（来自IotDeviceMessage.reportTime）';
COMMENT ON COLUMN public.device_service_invoke_response.tenant_id IS '租户编号';
COMMENT ON COLUMN public.device_service_invoke_response.create_time IS '创建时间';

