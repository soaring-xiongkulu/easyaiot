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

