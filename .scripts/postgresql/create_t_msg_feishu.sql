-- 创建 t_msg_feishu 表
-- 用于飞书消息模板存储

CREATE TABLE IF NOT EXISTS public.t_msg_feishu (
    id character varying(64) NOT NULL,
    msg_type integer,
    msg_name text,
    radio_type text,
    feishu_msg_type text,
    web_hook text,
    content text,
    create_time timestamp without time zone,
    modified_time timestamp without time zone,
    preview_user character varying(1000),
    title character varying(200),
    "imgUrl" character varying(200),
    "btnTxt" text,
    "btnUrl" character varying(200),
    url character varying(200),
    user_group_id character varying(64),
    tenant_id bigint DEFAULT 0 NOT NULL,
    deleted smallint DEFAULT 0 NOT NULL
);

ALTER TABLE public.t_msg_feishu OWNER TO postgres;

COMMENT ON COLUMN public.t_msg_feishu.tenant_id IS '租户编号';
COMMENT ON COLUMN public.t_msg_feishu.deleted IS '是否删除';

-- 添加主键约束
ALTER TABLE ONLY public.t_msg_feishu
    ADD CONSTRAINT t_msg_feishu_pkey PRIMARY KEY (id);

