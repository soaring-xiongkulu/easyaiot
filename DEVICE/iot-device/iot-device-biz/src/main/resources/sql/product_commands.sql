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

