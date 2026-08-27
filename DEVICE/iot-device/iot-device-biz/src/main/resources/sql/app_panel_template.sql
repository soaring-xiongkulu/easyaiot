-- App 控制面板模板表：云端定制每个产品在 APP 内展示的控制页面，绑定产品后下发到 APP 动态渲染
-- 注意：panel_schema 存储模板 JSON（页面 + 组件配置），App 端按该 JSON 动态渲染控制页

CREATE TABLE IF NOT EXISTS public.app_panel_template (
    id BIGSERIAL NOT NULL,
    template_code VARCHAR(64) NOT NULL, -- 模板编码：全局唯一，App 可按编码兜底取默认模板
    template_name VARCHAR(128) NOT NULL, -- 模板名称
    product_identification VARCHAR(100), -- 绑定产品标识（对应 product.product_identification）
    status VARCHAR(16) DEFAULT 'DRAFT' NOT NULL, -- 状态：DRAFT-草稿，PUBLISHED-已发布，DISABLED-停用
    version INT DEFAULT 1, -- 版本号，每次发布自增
    panel_schema TEXT, -- 面板模板 JSON：pages[{name,widgets[{id,type,title,...}]}]
    remark VARCHAR(255) NULL, -- 备注
    created_by VARCHAR(64) NULL,
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP NULL,
    updated_by VARCHAR(64) NULL,
    updated_time TIMESTAMP NULL,
    tenant_id BIGINT DEFAULT 0 NOT NULL,
    deleted INT DEFAULT 0 NOT NULL,
    CONSTRAINT app_panel_template_pkey PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS idx_app_panel_template_code ON public.app_panel_template(template_code);
CREATE INDEX IF NOT EXISTS idx_app_panel_template_product_identification ON public.app_panel_template(product_identification);
CREATE INDEX IF NOT EXISTS idx_app_panel_template_tenant_id ON public.app_panel_template(tenant_id);

COMMENT ON TABLE public.app_panel_template IS 'App控制面板模板表';
COMMENT ON COLUMN public.app_panel_template.id IS '主键';
COMMENT ON COLUMN public.app_panel_template.template_code IS '模板编码：全局唯一';
COMMENT ON COLUMN public.app_panel_template.template_name IS '模板名称';
COMMENT ON COLUMN public.app_panel_template.product_identification IS '绑定产品标识';
COMMENT ON COLUMN public.app_panel_template.status IS '状态：DRAFT-草稿，PUBLISHED-已发布，DISABLED-停用';
COMMENT ON COLUMN public.app_panel_template.version IS '版本号，每次发布自增';
COMMENT ON COLUMN public.app_panel_template.panel_schema IS '面板模板JSON：pages[{name,widgets[...]}]';
COMMENT ON COLUMN public.app_panel_template.remark IS '备注';
COMMENT ON COLUMN public.app_panel_template.tenant_id IS '租户编号';
COMMENT ON COLUMN public.app_panel_template.deleted IS '是否删除：0-未删除，1-已删除';
