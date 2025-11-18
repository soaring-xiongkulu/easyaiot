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

