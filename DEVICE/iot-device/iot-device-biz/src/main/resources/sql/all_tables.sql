-- ============================================
-- 合并所有表结构SQL文件
-- 执行前会先删除已存在的表
-- ============================================

-- ============================================
-- 第一部分：删除表（按依赖关系，先删除依赖表）
-- ============================================

DROP TABLE IF EXISTS public.product_commands_requests CASCADE;
DROP TABLE IF EXISTS public.product_commands_response CASCADE;
DROP TABLE IF EXISTS public.product_event_response CASCADE;
DROP TABLE IF EXISTS public.product_commands CASCADE;
DROP TABLE IF EXISTS public.product_services CASCADE;
DROP TABLE IF EXISTS public.product_event CASCADE;
DROP TABLE IF EXISTS public.device_event CASCADE;
DROP TABLE IF EXISTS public.device_service_invoke_response CASCADE;

-- ============================================
-- 第二部分：创建表（按依赖关系，先创建基础表）
-- ============================================

-- 产品模型服务表
CREATE TABLE IF NOT EXISTS public.product_services (
    id BIGSERIAL NOT NULL,
    service_code VARCHAR(255) NOT NULL, -- 服务编码:支持英文大小写、数字、下划线和中划线
    service_name VARCHAR(255) NOT NULL, -- 服务名称
    template_identification VARCHAR(100) NULL, -- 产品模版标识
    product_identification VARCHAR(100) NULL, -- 产品标识
    status VARCHAR(10) DEFAULT '0' NULL, -- 状态(字典值：0启用  1停用)
    description VARCHAR(255) NULL, -- 服务的描述信息:文本描述，不影响实际功能，可配置为空字符串""。
    create_by VARCHAR(64) NULL, -- 创建者
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP NULL, -- 创建时间
    update_by VARCHAR(64) NULL, -- 更新者
    update_time TIMESTAMP NULL, -- 更新时间
    tenant_id BIGINT DEFAULT 0 NOT NULL, -- 租户编号
    CONSTRAINT product_services_pkey PRIMARY KEY (id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_product_services_service_code ON public.product_services(service_code);
CREATE INDEX IF NOT EXISTS idx_product_services_product_identification ON public.product_services(product_identification);
CREATE INDEX IF NOT EXISTS idx_product_services_tenant_id ON public.product_services(tenant_id);

-- 表注释
COMMENT ON TABLE public.product_services IS '产品模型服务表';

-- 列注释
COMMENT ON COLUMN public.product_services.id IS '服务id';
COMMENT ON COLUMN public.product_services.service_code IS '服务编码:支持英文大小写、数字、下划线和中划线';
COMMENT ON COLUMN public.product_services.service_name IS '服务名称';
COMMENT ON COLUMN public.product_services.template_identification IS '产品模版标识';
COMMENT ON COLUMN public.product_services.product_identification IS '产品标识';
COMMENT ON COLUMN public.product_services.status IS '状态(字典值：0启用  1停用)';
COMMENT ON COLUMN public.product_services.description IS '服务的描述信息:文本描述，不影响实际功能，可配置为空字符串""。';
COMMENT ON COLUMN public.product_services.create_by IS '创建者';
COMMENT ON COLUMN public.product_services.create_time IS '创建时间';
COMMENT ON COLUMN public.product_services.update_by IS '更新者';
COMMENT ON COLUMN public.product_services.update_time IS '更新时间';
COMMENT ON COLUMN public.product_services.tenant_id IS '租户编号';

-- 产品事件表
CREATE TABLE IF NOT EXISTS public.product_event (
    id BIGSERIAL NOT NULL,
    event_name VARCHAR(255) NOT NULL, -- 事件名称
    event_code VARCHAR(255) NOT NULL, -- 事件标识
    event_type VARCHAR(255) NOT NULL, -- 事件类型。INFO_EVENT_TYPE：信息。ALERT_EVENT_TYPE：告警。ERROR_EVENT_TYPE：故障
    template_identification VARCHAR(255) NULL, -- 产品模版标识
    product_identification VARCHAR(255) NULL, -- 产品标识
    status VARCHAR(10) DEFAULT '0' NULL, -- 状态(字典值：0启用  1停用)
    description VARCHAR(255) NULL, -- 描述
    create_by VARCHAR(64) NULL, -- 创建者
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP NULL, -- 创建时间
    update_by VARCHAR(64) NULL, -- 更新者
    update_time TIMESTAMP NULL, -- 更新时间
    tenant_id BIGINT DEFAULT 0 NOT NULL, -- 租户编号
    CONSTRAINT product_event_pkey PRIMARY KEY (id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_product_event_event_code ON public.product_event(event_code);
CREATE INDEX IF NOT EXISTS idx_product_event_product_identification ON public.product_event(product_identification);
CREATE INDEX IF NOT EXISTS idx_product_event_tenant_id ON public.product_event(tenant_id);

-- 表注释
COMMENT ON TABLE public.product_event IS '产品事件表';

-- 列注释
COMMENT ON COLUMN public.product_event.id IS '主键';
COMMENT ON COLUMN public.product_event.event_name IS '事件名称';
COMMENT ON COLUMN public.product_event.event_code IS '事件标识';
COMMENT ON COLUMN public.product_event.event_type IS '事件类型。INFO_EVENT_TYPE：信息。ALERT_EVENT_TYPE：告警。ERROR_EVENT_TYPE：故障';
COMMENT ON COLUMN public.product_event.template_identification IS '产品模版标识';
COMMENT ON COLUMN public.product_event.product_identification IS '产品标识';
COMMENT ON COLUMN public.product_event.status IS '状态(字典值：0启用  1停用)';
COMMENT ON COLUMN public.product_event.description IS '描述';
COMMENT ON COLUMN public.product_event.create_by IS '创建者';
COMMENT ON COLUMN public.product_event.create_time IS '创建时间';
COMMENT ON COLUMN public.product_event.update_by IS '更新者';
COMMENT ON COLUMN public.product_event.update_time IS '更新时间';
COMMENT ON COLUMN public.product_event.tenant_id IS '租户编号';

-- 产品模型设备服务命令表
CREATE TABLE IF NOT EXISTS public.product_commands (
    id BIGSERIAL NOT NULL,
    service_id BIGINT NOT NULL, -- 服务ID
    "name" VARCHAR(255) NOT NULL, -- 指示命令的名字，如门磁的LOCK命令、摄像头的VIDEO_RECORD命令，命令名与参数共同构成一个完整的命令。支持英文大小写、数字及下划线，长度[2,50]。
    description VARCHAR(255) NULL, -- 命令描述
    create_by VARCHAR(64) NULL, -- 创建者
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP NULL, -- 创建时间
    update_by VARCHAR(64) NULL, -- 更新者
    update_time TIMESTAMP NULL, -- 更新时间
    command_code VARCHAR(255) NULL, -- 命令标识
    remark VARCHAR(255) NULL, -- 备注
    tenant_id BIGINT DEFAULT 0 NOT NULL, -- 租户编号
    CONSTRAINT product_commands_pkey PRIMARY KEY (id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_product_commands_service_id ON public.product_commands(service_id);
CREATE INDEX IF NOT EXISTS idx_product_commands_tenant_id ON public.product_commands(tenant_id);

-- 表注释
COMMENT ON TABLE public.product_commands IS '产品模型设备服务命令表';

-- 列注释
COMMENT ON COLUMN public.product_commands.id IS '命令id';
COMMENT ON COLUMN public.product_commands.service_id IS '服务ID';
COMMENT ON COLUMN public.product_commands."name" IS '指示命令的名字，如门磁的LOCK命令、摄像头的VIDEO_RECORD命令，命令名与参数共同构成一个完整的命令。支持英文大小写、数字及下划线，长度[2,50]。';
COMMENT ON COLUMN public.product_commands.description IS '命令描述';
COMMENT ON COLUMN public.product_commands.create_by IS '创建者';
COMMENT ON COLUMN public.product_commands.create_time IS '创建时间';
COMMENT ON COLUMN public.product_commands.update_by IS '更新者';
COMMENT ON COLUMN public.product_commands.update_time IS '更新时间';
COMMENT ON COLUMN public.product_commands.command_code IS '命令标识';
COMMENT ON COLUMN public.product_commands.remark IS '备注';
COMMENT ON COLUMN public.product_commands.tenant_id IS '租户编号';

-- 产品模型设备下发服务命令属性表
CREATE TABLE IF NOT EXISTS public.product_commands_requests (
    id BIGSERIAL NOT NULL,
    service_id BIGINT NOT NULL, -- 服务ID
    commands_id BIGINT NOT NULL, -- 命令ID
    "datatype" VARCHAR(255) NOT NULL, -- 指示数据类型。取值范围：string、int、decimal
    enumlist VARCHAR(255) NULL, -- 指示枚举值。如开关状态status可有如下取值"enumList" : ["OPEN","CLOSE"]目前本字段是非功能性字段，仅起到描述作用。建议准确定义。
    max VARCHAR(255) NULL, -- 指示最大值。仅当dataType为int、decimal时生效，逻辑小于等于。
    maxlength VARCHAR(255) NULL, -- 指示字符串长度。仅当dataType为string时生效。
    min VARCHAR(255) NULL, -- 指示最小值。仅当dataType为int、decimal时生效，逻辑大于等于。
    parameter_description VARCHAR(255) NULL, -- 命令中参数的描述，不影响实际功能，可配置为空字符串""。
    parameter_name VARCHAR(255) NULL, -- 命令中参数的名字。
    required VARCHAR(255) DEFAULT '0' NULL, -- 指示本条属性是否必填，取值为0或1，默认取值1（必填）。目前本字段是非功能性字段，仅起到描述作用。
    step VARCHAR(255) NULL, -- 指示步长。
    unit VARCHAR(255) NULL, -- 指示单位。取值根据参数确定，如：•温度单位："C"或"K"•百分比单位："%"•压强单位："Pa"或"kPa"
    create_by VARCHAR(64) NULL, -- 创建者
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP NULL, -- 创建时间
    update_by VARCHAR(64) NULL, -- 更新者
    update_time TIMESTAMP NULL, -- 更新时间
    parameter_code VARCHAR(255) NULL, -- 请求参数编码
    tenant_id BIGINT DEFAULT 0 NOT NULL, -- 租户编号
    CONSTRAINT product_commands_requests_pkey PRIMARY KEY (id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_product_commands_requests_commands_id ON public.product_commands_requests(commands_id);
CREATE INDEX IF NOT EXISTS idx_product_commands_requests_service_id ON public.product_commands_requests(service_id);
CREATE INDEX IF NOT EXISTS idx_product_commands_requests_tenant_id ON public.product_commands_requests(tenant_id);

-- 表注释
COMMENT ON TABLE public.product_commands_requests IS '产品模型设备下发服务命令属性表';

-- 列注释
COMMENT ON COLUMN public.product_commands_requests.id IS 'id';
COMMENT ON COLUMN public.product_commands_requests.service_id IS '服务ID';
COMMENT ON COLUMN public.product_commands_requests.commands_id IS '命令ID';
COMMENT ON COLUMN public.product_commands_requests."datatype" IS '指示数据类型。取值范围：string、int、decimal';
COMMENT ON COLUMN public.product_commands_requests.enumlist IS '指示枚举值。如开关状态status可有如下取值"enumList" : ["OPEN","CLOSE"]目前本字段是非功能性字段，仅起到描述作用。建议准确定义。';
COMMENT ON COLUMN public.product_commands_requests.max IS '指示最大值。仅当dataType为int、decimal时生效，逻辑小于等于。';
COMMENT ON COLUMN public.product_commands_requests.maxlength IS '指示字符串长度。仅当dataType为string时生效。';
COMMENT ON COLUMN public.product_commands_requests.min IS '指示最小值。仅当dataType为int、decimal时生效，逻辑大于等于。';
COMMENT ON COLUMN public.product_commands_requests.parameter_description IS '命令中参数的描述，不影响实际功能，可配置为空字符串""。';
COMMENT ON COLUMN public.product_commands_requests.parameter_name IS '命令中参数的名字。';
COMMENT ON COLUMN public.product_commands_requests.required IS '指示本条属性是否必填，取值为0或1，默认取值1（必填）。目前本字段是非功能性字段，仅起到描述作用。';
COMMENT ON COLUMN public.product_commands_requests.step IS '指示步长。';
COMMENT ON COLUMN public.product_commands_requests.unit IS '指示单位。取值根据参数确定，如：•温度单位："C"或"K"•百分比单位："%"•压强单位："Pa"或"kPa"';
COMMENT ON COLUMN public.product_commands_requests.create_by IS '创建者';
COMMENT ON COLUMN public.product_commands_requests.create_time IS '创建时间';
COMMENT ON COLUMN public.product_commands_requests.update_by IS '更新者';
COMMENT ON COLUMN public.product_commands_requests.update_time IS '更新时间';
COMMENT ON COLUMN public.product_commands_requests.parameter_code IS '请求参数编码';
COMMENT ON COLUMN public.product_commands_requests.tenant_id IS '租户编号';

-- 产品模型设备响应服务命令属性表
CREATE TABLE IF NOT EXISTS public.product_commands_response (
    id BIGSERIAL NOT NULL,
    commands_id BIGINT NOT NULL, -- 命令ID
    service_id BIGINT NULL, -- 服务ID
    "datatype" VARCHAR(255) NOT NULL, -- 指示数据类型。取值范围：string、int、decimal
    enumlist VARCHAR(255) NULL, -- 指示枚举值。如开关状态status可有如下取值"enumList" : ["OPEN","CLOSE"]目前本字段是非功能性字段，仅起到描述作用。建议准确定义。
    max VARCHAR(255) NULL, -- 指示最大值。仅当dataType为int、decimal时生效，逻辑小于等于。
    maxlength VARCHAR(255) NULL, -- 指示字符串长度。仅当dataType为string时生效。
    min VARCHAR(255) NULL, -- 指示最小值。仅当dataType为int、decimal时生效，逻辑大于等于。
    parameter_description VARCHAR(255) NULL, -- 命令中参数的描述，不影响实际功能，可配置为空字符串""。
    parameter_name VARCHAR(255) NULL, -- 命令中参数的名字。
    required VARCHAR(255) DEFAULT '0' NULL, -- 指示本条属性是否必填，取值为0或1，默认取值1（必填）。目前本字段是非功能性字段，仅起到描述作用。
    step VARCHAR(255) NULL, -- 指示步长。
    unit VARCHAR(255) NULL, -- 指示单位。取值根据参数确定，如：•温度单位："C"或"K"•百分比单位："%"•压强单位："Pa"或"kPa"
    create_by VARCHAR(64) NULL, -- 创建者
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP NULL, -- 创建时间
    update_by VARCHAR(64) NULL, -- 更新者
    update_time TIMESTAMP NULL, -- 更新时间
    parameter_code VARCHAR(255) NULL, -- 响应参数编码
    tenant_id BIGINT DEFAULT 0 NOT NULL, -- 租户编号
    CONSTRAINT product_commands_response_pkey PRIMARY KEY (id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_product_commands_response_commands_id ON public.product_commands_response(commands_id);
CREATE INDEX IF NOT EXISTS idx_product_commands_response_service_id ON public.product_commands_response(service_id);
CREATE INDEX IF NOT EXISTS idx_product_commands_response_tenant_id ON public.product_commands_response(tenant_id);

-- 表注释
COMMENT ON TABLE public.product_commands_response IS '产品模型设备响应服务命令属性表';

-- 列注释
COMMENT ON COLUMN public.product_commands_response.id IS 'id';
COMMENT ON COLUMN public.product_commands_response.commands_id IS '命令ID';
COMMENT ON COLUMN public.product_commands_response.service_id IS '服务ID';
COMMENT ON COLUMN public.product_commands_response."datatype" IS '指示数据类型。取值范围：string、int、decimal';
COMMENT ON COLUMN public.product_commands_response.enumlist IS '指示枚举值。如开关状态status可有如下取值"enumList" : ["OPEN","CLOSE"]目前本字段是非功能性字段，仅起到描述作用。建议准确定义。';
COMMENT ON COLUMN public.product_commands_response.max IS '指示最大值。仅当dataType为int、decimal时生效，逻辑小于等于。';
COMMENT ON COLUMN public.product_commands_response.maxlength IS '指示字符串长度。仅当dataType为string时生效。';
COMMENT ON COLUMN public.product_commands_response.min IS '指示最小值。仅当dataType为int、decimal时生效，逻辑大于等于。';
COMMENT ON COLUMN public.product_commands_response.parameter_description IS '命令中参数的描述，不影响实际功能，可配置为空字符串""。';
COMMENT ON COLUMN public.product_commands_response.parameter_name IS '命令中参数的名字。';
COMMENT ON COLUMN public.product_commands_response.required IS '指示本条属性是否必填，取值为0或1，默认取值1（必填）。目前本字段是非功能性字段，仅起到描述作用。';
COMMENT ON COLUMN public.product_commands_response.step IS '指示步长。';
COMMENT ON COLUMN public.product_commands_response.unit IS '指示单位。取值根据参数确定，如：•温度单位："C"或"K"•百分比单位："%"•压强单位："Pa"或"kPa"';
COMMENT ON COLUMN public.product_commands_response.create_by IS '创建者';
COMMENT ON COLUMN public.product_commands_response.create_time IS '创建时间';
COMMENT ON COLUMN public.product_commands_response.update_by IS '更新者';
COMMENT ON COLUMN public.product_commands_response.update_time IS '更新时间';
COMMENT ON COLUMN public.product_commands_response.parameter_code IS '响应参数编码';
COMMENT ON COLUMN public.product_commands_response.tenant_id IS '租户编号';

-- 产品模型设备响应服务命令属性表（事件响应）
CREATE TABLE IF NOT EXISTS public.product_event_response (
    id BIGSERIAL NOT NULL,
    event_id BIGINT NOT NULL, -- 事件id
    service_id BIGINT NULL, -- 服务ID
    "datatype" VARCHAR(255) NOT NULL, -- 指示数据类型。取值范围：string、int、decimal
    enumlist VARCHAR(255) NULL, -- 指示枚举值。如开关状态status可有如下取值"enumList" : ["OPEN","CLOSE"]目前本字段是非功能性字段，仅起到描述作用。建议准确定义。
    max VARCHAR(255) NULL, -- 指示最大值。仅当dataType为int、decimal时生效，逻辑小于等于。
    maxlength VARCHAR(255) NULL, -- 指示字符串长度。仅当dataType为string时生效。
    min VARCHAR(255) NULL, -- 指示最小值。仅当dataType为int、decimal时生效，逻辑大于等于。
    parameter_description VARCHAR(255) NULL, -- 命令中参数的描述，不影响实际功能，可配置为空字符串""。
    parameter_name VARCHAR(255) NULL, -- 命令中参数的名字。
    required VARCHAR(255) NOT NULL, -- 指示本条属性是否必填，取值为0或1，默认取值1（必填）。目前本字段是非功能性字段，仅起到描述作用。
    step VARCHAR(255) NULL, -- 指示步长。
    unit VARCHAR(255) NULL, -- 指示单位。取值根据参数确定，如：•温度单位："C"或"K"•百分比单位："%"•压强单位："Pa"或"kPa"
    create_by VARCHAR(64) NULL, -- 创建者
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP NULL, -- 创建时间
    update_by VARCHAR(64) NULL, -- 更新者
    update_time TIMESTAMP NULL, -- 更新时间
    tenant_id BIGINT DEFAULT 0 NOT NULL, -- 租户编号
    CONSTRAINT product_event_response_pkey PRIMARY KEY (id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_product_event_response_event_id ON public.product_event_response(event_id);
CREATE INDEX IF NOT EXISTS idx_product_event_response_service_id ON public.product_event_response(service_id);
CREATE INDEX IF NOT EXISTS idx_product_event_response_tenant_id ON public.product_event_response(tenant_id);

-- 表注释
COMMENT ON TABLE public.product_event_response IS '产品模型设备响应服务命令属性表（事件响应）';

-- 列注释
COMMENT ON COLUMN public.product_event_response.id IS 'id';
COMMENT ON COLUMN public.product_event_response.event_id IS '事件id';
COMMENT ON COLUMN public.product_event_response.service_id IS '服务ID';
COMMENT ON COLUMN public.product_event_response."datatype" IS '指示数据类型。取值范围：string、int、decimal';
COMMENT ON COLUMN public.product_event_response.enumlist IS '指示枚举值。如开关状态status可有如下取值"enumList" : ["OPEN","CLOSE"]目前本字段是非功能性字段，仅起到描述作用。建议准确定义。';
COMMENT ON COLUMN public.product_event_response.max IS '指示最大值。仅当dataType为int、decimal时生效，逻辑小于等于。';
COMMENT ON COLUMN public.product_event_response.maxlength IS '指示字符串长度。仅当dataType为string时生效。';
COMMENT ON COLUMN public.product_event_response.min IS '指示最小值。仅当dataType为int、decimal时生效，逻辑大于等于。';
COMMENT ON COLUMN public.product_event_response.parameter_description IS '命令中参数的描述，不影响实际功能，可配置为空字符串""。';
COMMENT ON COLUMN public.product_event_response.parameter_name IS '命令中参数的名字。';
COMMENT ON COLUMN public.product_event_response.required IS '指示本条属性是否必填，取值为0或1，默认取值1（必填）。目前本字段是非功能性字段，仅起到描述作用。';
COMMENT ON COLUMN public.product_event_response.step IS '指示步长。';
COMMENT ON COLUMN public.product_event_response.unit IS '指示单位。取值根据参数确定，如：•温度单位："C"或"K"•百分比单位："%"•压强单位："Pa"或"kPa"';
COMMENT ON COLUMN public.product_event_response.create_by IS '创建者';
COMMENT ON COLUMN public.product_event_response.create_time IS '创建时间';
COMMENT ON COLUMN public.product_event_response.update_by IS '更新者';
COMMENT ON COLUMN public.product_event_response.update_time IS '更新时间';
COMMENT ON COLUMN public.product_event_response.tenant_id IS '租户编号';

-- 设备动作数据表
CREATE TABLE IF NOT EXISTS public.device_event (
    id BIGSERIAL NOT NULL,
    device_identification VARCHAR(255) NULL, -- 设备标识
    event_type VARCHAR(255) NULL, -- 事件类型
    message TEXT NULL, -- 内容信息
    status VARCHAR(255) NULL, -- 状态
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP NULL, -- 创建时间
    event_name VARCHAR(255) NULL, -- 事件名称
    event_code VARCHAR(255) NULL, -- 事件标识符
    deleted SMALLINT DEFAULT 0 NOT NULL, -- 是否删除
    tenant_id BIGINT DEFAULT 0 NOT NULL, -- 租户编号
    CONSTRAINT device_event_pkey PRIMARY KEY (id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_device_event_device_identification ON public.device_event(device_identification);
CREATE INDEX IF NOT EXISTS idx_device_event_event_code ON public.device_event(event_code);
CREATE INDEX IF NOT EXISTS idx_device_event_tenant_id ON public.device_event(tenant_id);
CREATE INDEX IF NOT EXISTS idx_device_event_create_time ON public.device_event(create_time);

-- 表注释
COMMENT ON TABLE public.device_event IS '设备动作数据表';

-- 列注释
COMMENT ON COLUMN public.device_event.id IS 'id';
COMMENT ON COLUMN public.device_event.device_identification IS '设备标识';
COMMENT ON COLUMN public.device_event.event_type IS '事件类型';
COMMENT ON COLUMN public.device_event.message IS '内容信息';
COMMENT ON COLUMN public.device_event.status IS '状态';
COMMENT ON COLUMN public.device_event.create_time IS '创建时间';
COMMENT ON COLUMN public.device_event.event_name IS '事件名称';
COMMENT ON COLUMN public.device_event.event_code IS '事件标识符';
COMMENT ON COLUMN public.device_event.deleted IS '是否删除';
COMMENT ON COLUMN public.device_event.tenant_id IS '租户编号';

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
CREATE INDEX IF NOT EXISTS idx_device_service_invoke_response_service_identifier ON public.device_service_invoke_response(service_identifier);
CREATE INDEX IF NOT EXISTS idx_device_service_invoke_response_request_id ON public.device_service_invoke_response(request_id);
-- 联合索引：用于查询特定设备的服务调用响应
CREATE INDEX IF NOT EXISTS idx_device_service_invoke_response_device_service ON public.device_service_invoke_response(device_id, service_identifier, create_time);
-- 联合索引：用于查询特定租户的服务调用响应
CREATE INDEX IF NOT EXISTS idx_device_service_invoke_response_tenant_time ON public.device_service_invoke_response(tenant_id, create_time);

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

