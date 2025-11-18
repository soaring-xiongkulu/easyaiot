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

