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

