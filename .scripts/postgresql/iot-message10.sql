--
-- PostgreSQL database dump
--

\restrict fZCIMJ7YUAJZdjJWBs0ZadWJBe6KODBYATxobaCnaCKZbrSM1W5SnGMQELjs81N

-- Dumped from database version 18.1 (Debian 18.1-1.pgdg13+2)
-- Dumped by pg_dump version 18.1 (Debian 18.1-1.pgdg13+2)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

DROP DATABASE IF EXISTS "iot-message20";
--
-- Name: iot-message20; Type: DATABASE; Schema: -; Owner: -
--

CREATE DATABASE "iot-message20" WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'en_US.utf8';


\unrestrict fZCIMJ7YUAJZdjJWBs0ZadWJBe6KODBYATxobaCnaCKZbrSM1W5SnGMQELjs81N
\encoding SQL_ASCII
\connect -reuse-previous=on "dbname='iot-message20'"
\restrict fZCIMJ7YUAJZdjJWBs0ZadWJBe6KODBYATxobaCnaCKZbrSM1W5SnGMQELjs81N

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: message_config; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.message_config (
    configuration text,
    create_time bigint,
    creator_id character varying(255),
    id character varying(64) NOT NULL,
    msg_type integer,
    tenant_id bigint DEFAULT 0 NOT NULL,
    deleted smallint DEFAULT 0 NOT NULL
);


--
-- Name: TABLE message_config; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.message_config IS '消息配置表';


--
-- Name: COLUMN message_config.configuration; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.message_config.configuration IS '配置信息';


--
-- Name: COLUMN message_config.create_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.message_config.create_time IS '创建时间(只读)';


--
-- Name: COLUMN message_config.creator_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.message_config.creator_id IS '创建者ID(只读)';


--
-- Name: COLUMN message_config.id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.message_config.id IS 'id';


--
-- Name: COLUMN message_config.msg_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.message_config.msg_type IS '通知类型';


--
-- Name: COLUMN message_config.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.message_config.tenant_id IS '租户编号';


--
-- Name: COLUMN message_config.deleted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.message_config.deleted IS '是否删除';


--
-- Name: t_ding_app; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.t_ding_app (
    id character varying(64) NOT NULL,
    app_name text,
    agent_id text,
    app_key text,
    app_secret text,
    create_time timestamp without time zone,
    modified_time timestamp without time zone,
    tenant_id bigint DEFAULT 0 NOT NULL,
    deleted smallint DEFAULT 0 NOT NULL
);


--
-- Name: COLUMN t_ding_app.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.t_ding_app.tenant_id IS '租户编号';


--
-- Name: COLUMN t_ding_app.deleted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.t_ding_app.deleted IS '是否删除';


--
-- Name: t_ding_app_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.t_ding_app_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: t_ding_app_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.t_ding_app_id_seq OWNED BY public.t_ding_app.id;


--
-- Name: t_msg_ding; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.t_msg_ding (
    id character varying(64) NOT NULL,
    msg_type integer,
    msg_name text,
    radio_type text,
    ding_msg_type text,
    agent_id text,
    web_hook text,
    content text,
    create_time timestamp without time zone,
    modified_time timestamp without time zone,
    preview_user character varying(1000),
    title character varying(200),
    btntxt text,
    btnurl character varying(200),
    url character varying(200),
    imgurl character varying(200),
    user_group_id character varying(64),
    tenant_id bigint DEFAULT 0 NOT NULL,
    deleted smallint DEFAULT 0 NOT NULL
);


--
-- Name: COLUMN t_msg_ding.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.t_msg_ding.tenant_id IS '租户编号';


--
-- Name: COLUMN t_msg_ding.deleted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.t_msg_ding.deleted IS '是否删除';


--
-- Name: t_msg_ding_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.t_msg_ding_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: t_msg_ding_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.t_msg_ding_id_seq OWNED BY public.t_msg_ding.id;


--
-- Name: t_msg_feishu; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.t_msg_feishu (
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


--
-- Name: COLUMN t_msg_feishu.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.t_msg_feishu.tenant_id IS '租户编号';


--
-- Name: COLUMN t_msg_feishu.deleted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.t_msg_feishu.deleted IS '是否删除';


--
-- Name: t_msg_http; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.t_msg_http (
    id character varying(64) NOT NULL,
    msg_type integer,
    msg_name text,
    method text,
    url text,
    params text,
    headers text,
    cookies text,
    body text,
    body_type text,
    create_time timestamp without time zone,
    modified_time timestamp without time zone,
    preview_user character varying,
    user_group_id character varying(64),
    tenant_id bigint DEFAULT 0 NOT NULL,
    deleted smallint DEFAULT 0 NOT NULL
);


--
-- Name: COLUMN t_msg_http.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.t_msg_http.tenant_id IS '租户编号';


--
-- Name: COLUMN t_msg_http.deleted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.t_msg_http.deleted IS '是否删除';


--
-- Name: t_msg_http_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.t_msg_http_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: t_msg_http_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.t_msg_http_id_seq OWNED BY public.t_msg_http.id;


--
-- Name: t_msg_kefu; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.t_msg_kefu (
    id integer NOT NULL,
    msg_type integer,
    msg_name text,
    kefu_msg_type text,
    content text,
    img_url text,
    describe text,
    url text,
    create_time timestamp without time zone,
    modified_time timestamp without time zone,
    tenant_id bigint DEFAULT 0 NOT NULL,
    deleted smallint DEFAULT 0 NOT NULL
);


--
-- Name: COLUMN t_msg_kefu.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.t_msg_kefu.tenant_id IS '租户编号';


--
-- Name: COLUMN t_msg_kefu.deleted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.t_msg_kefu.deleted IS '是否删除';


--
-- Name: t_msg_ma_subscribe; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.t_msg_ma_subscribe (
    id integer NOT NULL,
    msg_type integer,
    msg_name text,
    template_id text,
    page text,
    create_time timestamp without time zone,
    modified_time timestamp without time zone,
    tenant_id bigint DEFAULT 0 NOT NULL,
    deleted smallint DEFAULT 0 NOT NULL
);


--
-- Name: COLUMN t_msg_ma_subscribe.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.t_msg_ma_subscribe.tenant_id IS '租户编号';


--
-- Name: COLUMN t_msg_ma_subscribe.deleted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.t_msg_ma_subscribe.deleted IS '是否删除';


--
-- Name: t_msg_ma_subscribe_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.t_msg_ma_subscribe_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: t_msg_ma_subscribe_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.t_msg_ma_subscribe_id_seq OWNED BY public.t_msg_ma_subscribe.id;


--
-- Name: t_msg_ma_template; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.t_msg_ma_template (
    id integer NOT NULL,
    msg_type integer,
    msg_name text,
    template_id text,
    page text,
    emphasis_keyword text,
    create_time timestamp without time zone,
    modified_time timestamp without time zone,
    tenant_id bigint DEFAULT 0 NOT NULL,
    deleted smallint DEFAULT 0 NOT NULL
);


--
-- Name: COLUMN t_msg_ma_template.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.t_msg_ma_template.tenant_id IS '租户编号';


--
-- Name: COLUMN t_msg_ma_template.deleted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.t_msg_ma_template.deleted IS '是否删除';


--
-- Name: t_msg_ma_template_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.t_msg_ma_template_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: t_msg_ma_template_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.t_msg_ma_template_id_seq OWNED BY public.t_msg_ma_template.id;


--
-- Name: t_msg_mail; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.t_msg_mail (
    id character varying(64) NOT NULL,
    msg_type integer,
    msg_name text,
    title text,
    cc text,
    files text,
    content text,
    create_time timestamp without time zone,
    modified_time timestamp without time zone,
    preview_user character varying(1000),
    user_group_id character varying(64),
    tenant_id bigint DEFAULT 0 NOT NULL,
    deleted smallint DEFAULT 0 NOT NULL
);


--
-- Name: COLUMN t_msg_mail.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.t_msg_mail.tenant_id IS '租户编号';


--
-- Name: COLUMN t_msg_mail.deleted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.t_msg_mail.deleted IS '是否删除';


--
-- Name: t_msg_mp_subscribe; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.t_msg_mp_subscribe (
    id integer NOT NULL,
    msg_type integer,
    msg_name text,
    template_id text,
    url text,
    ma_appid text,
    ma_page_path text,
    preview_user text,
    wx_account_id integer,
    create_time timestamp without time zone,
    modified_time timestamp without time zone,
    tenant_id bigint DEFAULT 0 NOT NULL,
    deleted smallint DEFAULT 0 NOT NULL
);


--
-- Name: COLUMN t_msg_mp_subscribe.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.t_msg_mp_subscribe.tenant_id IS '租户编号';


--
-- Name: COLUMN t_msg_mp_subscribe.deleted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.t_msg_mp_subscribe.deleted IS '是否删除';


--
-- Name: t_msg_mp_template; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.t_msg_mp_template (
    id integer NOT NULL,
    msg_type integer,
    msg_name text,
    template_id text,
    url text,
    ma_appid text,
    ma_page_path text,
    create_time timestamp without time zone,
    modified_time timestamp without time zone,
    tenant_id bigint DEFAULT 0 NOT NULL,
    deleted smallint DEFAULT 0 NOT NULL
);


--
-- Name: COLUMN t_msg_mp_template.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.t_msg_mp_template.tenant_id IS '租户编号';


--
-- Name: COLUMN t_msg_mp_template.deleted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.t_msg_mp_template.deleted IS '是否删除';


--
-- Name: t_msg_sms; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.t_msg_sms (
    id character varying(64) NOT NULL,
    msg_type integer,
    msg_name text,
    template_id text,
    content text,
    create_time timestamp without time zone,
    modified_time timestamp without time zone,
    preview_user character varying(1000),
    user_group_id character varying(64),
    tenant_id bigint DEFAULT 0 NOT NULL,
    deleted smallint DEFAULT 0 NOT NULL
);


--
-- Name: COLUMN t_msg_sms.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.t_msg_sms.tenant_id IS '租户编号';


--
-- Name: COLUMN t_msg_sms.deleted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.t_msg_sms.deleted IS '是否删除';


--
-- Name: t_msg_wx_cp; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.t_msg_wx_cp (
    id character varying(64) NOT NULL,
    msg_type integer,
    msg_name text,
    cp_msg_type text,
    agent_id text,
    content text,
    title text,
    img_url text,
    describe text,
    url text,
    btn_txt text,
    create_time timestamp without time zone,
    modified_time timestamp without time zone,
    preview_user character varying(1000),
    user_group_id character varying(64),
    tenant_id bigint DEFAULT 0 NOT NULL,
    deleted smallint DEFAULT 0 NOT NULL
);


--
-- Name: COLUMN t_msg_wx_cp.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.t_msg_wx_cp.tenant_id IS '租户编号';


--
-- Name: COLUMN t_msg_wx_cp.deleted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.t_msg_wx_cp.deleted IS '是否删除';


--
-- Name: t_msg_wx_uniform; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.t_msg_wx_uniform (
    id integer NOT NULL,
    msg_type integer,
    msg_name text,
    mp_template_id text,
    ma_template_id text,
    mp_url text,
    ma_appid text,
    ma_page_path text,
    page text,
    emphasis_keyword text,
    create_time timestamp without time zone,
    modified_time timestamp without time zone,
    tenant_id bigint DEFAULT 0 NOT NULL,
    deleted smallint DEFAULT 0 NOT NULL
);


--
-- Name: COLUMN t_msg_wx_uniform.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.t_msg_wx_uniform.tenant_id IS '租户编号';


--
-- Name: COLUMN t_msg_wx_uniform.deleted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.t_msg_wx_uniform.deleted IS '是否删除';


--
-- Name: t_preview_user; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.t_preview_user (
    id character varying(64) NOT NULL,
    msg_type integer,
    preview_user character varying(200),
    create_time timestamp without time zone,
    tenant_id bigint DEFAULT 0 NOT NULL,
    deleted smallint DEFAULT 0 NOT NULL
);


--
-- Name: COLUMN t_preview_user.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.t_preview_user.tenant_id IS '租户编号';


--
-- Name: COLUMN t_preview_user.deleted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.t_preview_user.deleted IS '是否删除';


--
-- Name: t_preview_user_group; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.t_preview_user_group (
    id character varying(64) NOT NULL,
    msg_type integer,
    user_group_name character varying(200),
    preview_user_id text,
    create_time timestamp without time zone,
    tenant_id bigint DEFAULT 0 NOT NULL,
    deleted smallint DEFAULT 0 NOT NULL
);


--
-- Name: COLUMN t_preview_user_group.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.t_preview_user_group.tenant_id IS '租户编号';


--
-- Name: COLUMN t_preview_user_group.deleted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.t_preview_user_group.deleted IS '是否删除';


--
-- Name: t_push_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.t_push_history (
    id character varying(64) NOT NULL,
    msg_id character varying(64),
    msg_type integer,
    msg_name text,
    result text,
    csv_file text,
    create_time timestamp without time zone,
    modified_time timestamp without time zone,
    tenant_id bigint DEFAULT 0 NOT NULL,
    deleted smallint DEFAULT 0 NOT NULL
);


--
-- Name: COLUMN t_push_history.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.t_push_history.tenant_id IS '租户编号';


--
-- Name: COLUMN t_push_history.deleted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.t_push_history.deleted IS '是否删除';


--
-- Name: t_template_data; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.t_template_data (
    id character varying(64) NOT NULL,
    msg_type integer,
    msg_id character varying(64),
    name text,
    value text,
    color text,
    create_time timestamp without time zone,
    modified_time timestamp without time zone,
    tenant_id bigint DEFAULT 0 NOT NULL,
    deleted smallint DEFAULT 0 NOT NULL
);


--
-- Name: COLUMN t_template_data.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.t_template_data.tenant_id IS '租户编号';


--
-- Name: COLUMN t_template_data.deleted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.t_template_data.deleted IS '是否删除';


--
-- Name: t_wx_account; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.t_wx_account (
    id integer NOT NULL,
    account_type text,
    account_name text,
    app_id text,
    app_secret text,
    token text,
    aes_key text,
    create_time timestamp without time zone,
    modified_time timestamp without time zone,
    tenant_id bigint DEFAULT 0 NOT NULL,
    deleted smallint DEFAULT 0 NOT NULL
);


--
-- Name: COLUMN t_wx_account.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.t_wx_account.tenant_id IS '租户编号';


--
-- Name: COLUMN t_wx_account.deleted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.t_wx_account.deleted IS '是否删除';


--
-- Name: t_wx_cp_app; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.t_wx_cp_app (
    id integer NOT NULL,
    corpid text,
    app_name text,
    agent_id text,
    secret text,
    token text,
    aes_key text,
    create_time timestamp without time zone,
    modified_time timestamp without time zone,
    tenant_id bigint DEFAULT 0 NOT NULL,
    deleted smallint DEFAULT 0 NOT NULL
);


--
-- Name: COLUMN t_wx_cp_app.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.t_wx_cp_app.tenant_id IS '租户编号';


--
-- Name: COLUMN t_wx_cp_app.deleted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.t_wx_cp_app.deleted IS '是否删除';


--
-- Name: t_wx_mp_user; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.t_wx_mp_user (
    open_id text NOT NULL,
    nickname text,
    sex_desc text,
    sex integer,
    language text,
    city text,
    province text,
    country text,
    head_img_url text,
    subscribe_time text,
    union_id text,
    remark text,
    group_id integer,
    subscribe_scene text,
    qr_scene text,
    qr_scene_str text,
    create_time text,
    modified_time text,
    tenant_id bigint DEFAULT 0 NOT NULL,
    deleted smallint DEFAULT 0 NOT NULL
);


--
-- Name: COLUMN t_wx_mp_user.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.t_wx_mp_user.tenant_id IS '租户编号';


--
-- Name: COLUMN t_wx_mp_user.deleted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.t_wx_mp_user.deleted IS '是否删除';


--
-- Name: table_name_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.table_name_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: table_name_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.table_name_id_seq OWNED BY public.t_msg_kefu.id;


--
-- Name: t_msg_kefu id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.t_msg_kefu ALTER COLUMN id SET DEFAULT nextval('public.table_name_id_seq'::regclass);


--
-- Name: t_msg_ma_subscribe id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.t_msg_ma_subscribe ALTER COLUMN id SET DEFAULT nextval('public.t_msg_ma_subscribe_id_seq'::regclass);


--
-- Name: t_msg_ma_template id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.t_msg_ma_template ALTER COLUMN id SET DEFAULT nextval('public.t_msg_ma_template_id_seq'::regclass);


--
-- Data for Name: message_config; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.message_config (configuration, create_time, creator_id, id, msg_type, tenant_id, deleted) FROM stdin;
{"wxCpCorpId":"a","wxCpApp":[{"agentId":"1","appName":"122","id":0,"secret":"1"}]}	1689906299290	25ea1da0-ed50-11ed-b15c-5face31d80ce	cb743247-c75d-4921-9ab5-184067839d54	4	1	0
{"txyunAppId":"1111","txyunAppKey":"1","txyunSign":"1"}	1689905782221	25ea1da0-ed50-11ed-b15c-5face31d80ce	92042652-fec4-4e3d-aeff-0e2378233d87	2	1	0
{"isHttpUseProxy":true,"host":"12.12.13","port":"80","userName":"a","password":"a"}	1689906394550	25ea1da0-ed50-11ed-b15c-5face31d80ce	00a66566-3a4a-4894-a9ab-18f6eb1d1497	5	1	0
{"aliyunAccessKeyId":"LTAI5tAzfKSJigmEYGRNBGU8","aliyunAccessKeySecret":"JbUZ4fHNmYDniY9OFfF8qBUiEbPbCQ","aliyunSign":"短信通知"}	1689905755523	25ea1da0-ed50-11ed-b15c-5face31d80ce	5e52b025-2ebd-4a5c-ae31-3752327cb526	1	1	0
{"feishuWebhook":"https://www.feishu.cn/flow/api/trigger-webhook/71e645fe33a058cb414d1e4e46bfce4d"}	1765352183596	25ea1da0-ed50-11ed-b15c-5face31d80ce	f2174096-0159-4211-939a-d28f43ab000f	7	0	0
{"mailHost":"smtp.qq.com","mailPort":465,"mailFrom":"xxxxx@qq.com","mailUser":"xxxxx@qq.com","mailPassword":"gorttpgwqdiabdfc","starttlsEnable":false,"sslEnable":true}	1689749908832	25ea1da0-ed50-11ed-b15c-5face31d80ce	83440192-e39b-4674-98a7-c4f2e70fea8e	3	1	0
\.


--
-- Data for Name: t_ding_app; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.t_ding_app (id, app_name, agent_id, app_key, app_secret, create_time, modified_time, tenant_id, deleted) FROM stdin;
\.


--
-- Data for Name: t_msg_ding; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.t_msg_ding (id, msg_type, msg_name, radio_type, ding_msg_type, agent_id, web_hook, content, create_time, modified_time, preview_user, title, btntxt, btnurl, url, imgurl, user_group_id, tenant_id, deleted) FROM stdin;
940afe96-7843-4b5d-8eb5-c44fa54ac406	6	dingdign test	工作通知方式	文本消息	1	\N	dfs	2023-07-24 14:51:14.011	\N	1	\N	\N	\N	\N	\N	\N	1	0
8f230ac9-bd4e-4bd6-be84-8aa9cd9da5a6	6	dingding001	群机器人消息	链接消息	\N	http://www.baidu.com	test111	2023-07-25 15:20:15.35	2023-07-25 15:20:27.942	manager9115	test	\N	\N	test	test	\N	1	0
\.


--
-- Data for Name: t_msg_feishu; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.t_msg_feishu (id, msg_type, msg_name, radio_type, feishu_msg_type, web_hook, content, create_time, modified_time, preview_user, title, "imgUrl", "btnTxt", "btnUrl", url, user_group_id, tenant_id, deleted) FROM stdin;
\.


--
-- Data for Name: t_msg_http; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.t_msg_http (id, msg_type, msg_name, method, url, params, headers, cookies, body, body_type, create_time, modified_time, preview_user, user_group_id, tenant_id, deleted) FROM stdin;
\.


--
-- Data for Name: t_msg_kefu; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.t_msg_kefu (id, msg_type, msg_name, kefu_msg_type, content, img_url, describe, url, create_time, modified_time, tenant_id, deleted) FROM stdin;
\.


--
-- Data for Name: t_msg_ma_subscribe; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.t_msg_ma_subscribe (id, msg_type, msg_name, template_id, page, create_time, modified_time, tenant_id, deleted) FROM stdin;
\.


--
-- Data for Name: t_msg_ma_template; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.t_msg_ma_template (id, msg_type, msg_name, template_id, page, emphasis_keyword, create_time, modified_time, tenant_id, deleted) FROM stdin;
\.


--
-- Data for Name: t_msg_mail; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.t_msg_mail (id, msg_type, msg_name, title, cc, files, content, create_time, modified_time, preview_user, user_group_id, tenant_id, deleted) FROM stdin;
907aec07-5b5f-4d88-bef0-9991262099f2	3	告警通知	告警通知-大门设备	\N	\N	【告警通知】\n设备名称: 大门设备\n设备ID: 1764341204704370850\n对象类型: car\n事件类型: 江北初中监控安防任务\n告警时间: 2025-12-10 15:13:00	2025-12-10 15:13:05.796	\N	xxxxx@163.com	\N	0	0
794f743b-1fd1-4ac6-8a41-a18353806474	3	告警通知	告警通知-大门设备	\N	\N	【告警通知】\n设备名称: 大门设备\n设备ID: 1764341204704370850\n对象类型: truck\n事件类型: 江北初中监控安防任务\n告警时间: 2025-12-10 14:46:00	2025-12-10 14:46:05.836	\N	xxxxx@163.com	\N	0	0
5356e214-9673-4d48-b952-2894dc584765	3	告警通知	告警通知-大门设备	\N	\N	【告警通知】\n设备名称: 大门设备\n设备ID: 1764341204704370850\n对象类型: car\n事件类型: 江北初中监控安防任务\n告警时间: 2025-12-10 14:52:00	2025-12-10 14:52:05.574	\N	xxxxx@163.com	\N	0	0
5186b29e-1a14-494e-8dd3-af314f464d26	3	告警通知	告警通知-大门设备	\N	\N	【告警通知】\n设备名称: 大门设备\n设备ID: 1764341204704370850\n对象类型: car\n事件类型: 江北初中监控安防任务\n告警时间: 2025-12-10 14:57:00	2025-12-10 14:57:05.951	\N	xxxxx@163.com	\N	0	0
bf366265-b98c-4bc9-8b12-a8c2426c2110	3	告警通知	告警通知-大门设备	\N	\N	【告警通知】\n设备名称: 大门设备\n设备ID: 1764341204704370850\n对象类型: car\n事件类型: 江北初中监控安防任务\n告警时间: 2025-12-10 15:03:00	2025-12-10 15:03:05.63	\N	xxxxx@163.com	\N	0	0
ade227fe-5ff3-4eda-9647-c133c0636189	3	告警通知	告警通知-大门设备	\N	\N	【告警通知】\n设备名称: 大门设备\n设备ID: 1764341204704370850\n对象类型: car\n事件类型: 江北初中监控安防任务\n告警时间: 2025-12-10 15:19:00	2025-12-10 15:19:05.567	\N	xxxxx@163.com	\N	0	0
e3a0432d-b0b2-438b-9681-9bfcc6a90873	3	告警通知	告警通知-大门设备	\N	\N	【告警通知】\n设备名称: 大门设备\n设备ID: 1764341204704370850\n对象类型: car\n事件类型: 江北初中监控安防任务\n告警时间: 2025-12-10 15:24:00	2025-12-10 15:24:05.7	\N	xxxxx@163.com	\N	0	0
175bc751-760d-40df-956b-ac2b3f374c60	3	告警通知	告警通知-大门设备	\N	\N	【告警通知】\n设备名称: 大门设备\n设备ID: 1764341204704370850\n对象类型: car\n事件类型: 江北初中监控安防任务\n告警时间: 2025-12-10 15:29:00	2025-12-10 15:29:05.71	\N	xxxxx@163.com	\N	0	0
5bdb23a7-4e2d-46de-b746-7745d6fc6eb5	3	告警通知	告警通知-大门设备	\N	\N	【告警通知】\n设备名称: 大门设备\n设备ID: 1764341204704370850\n对象类型: car\n事件类型: 江北初中监控安防任务\n告警时间: 2025-12-10 15:35:00	2025-12-10 15:35:05.676	\N	xxxxx@163.com	\N	0	0
0d5b118a-2d4e-4f76-a212-8d172648aed4	3	告警通知	告警通知-大门设备	\N	\N	【告警通知】\n设备名称: 大门设备\n设备ID: 1764341204704370850\n对象类型: car\n事件类型: 江北初中监控安防任务\n告警时间: 2025-12-10 15:40:00	2025-12-10 15:40:05.795	\N	xxxxx@163.com	\N	0	0
fb6cd163-9339-4df1-8b93-6a0af93197ab	3	告警通知	告警通知-大门设备	\N	\N	【告警通知】\n设备名称: 大门设备\n设备ID: 1764341204704370850\n对象类型: car\n事件类型: 江北初中监控安防任务\n告警时间: 2025-12-10 15:46:00	2025-12-10 15:46:05.811	\N	xxxxx@163.com	\N	0	0
\.


--
-- Data for Name: t_msg_mp_subscribe; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.t_msg_mp_subscribe (id, msg_type, msg_name, template_id, url, ma_appid, ma_page_path, preview_user, wx_account_id, create_time, modified_time, tenant_id, deleted) FROM stdin;
\.


--
-- Data for Name: t_msg_mp_template; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.t_msg_mp_template (id, msg_type, msg_name, template_id, url, ma_appid, ma_page_path, create_time, modified_time, tenant_id, deleted) FROM stdin;
\.


--
-- Data for Name: t_msg_sms; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.t_msg_sms (id, msg_type, msg_name, template_id, content, create_time, modified_time, preview_user, user_group_id, tenant_id, deleted) FROM stdin;
\.


--
-- Data for Name: t_msg_wx_cp; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.t_msg_wx_cp (id, msg_type, msg_name, cp_msg_type, agent_id, content, title, img_url, describe, url, btn_txt, create_time, modified_time, preview_user, user_group_id, tenant_id, deleted) FROM stdin;
\.


--
-- Data for Name: t_msg_wx_uniform; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.t_msg_wx_uniform (id, msg_type, msg_name, mp_template_id, ma_template_id, mp_url, ma_appid, ma_page_path, page, emphasis_keyword, create_time, modified_time, tenant_id, deleted) FROM stdin;
\.


--
-- Data for Name: t_preview_user; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.t_preview_user (id, msg_type, preview_user, create_time, tenant_id, deleted) FROM stdin;
b1ff9e5a-7a0c-42d0-a27b-645291eb03e3	3	xxxxx@163.com	2023-07-26 14:37:51.775	1	0
\.


--
-- Data for Name: t_preview_user_group; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.t_preview_user_group (id, msg_type, user_group_name, preview_user_id, create_time, tenant_id, deleted) FROM stdin;
43785cb5-c36a-429c-824b-fc32ee7a3df5	3	EasyAIoT测试分组	b1ff9e5a-7a0c-42d0-a27b-645291eb03e3	2025-12-10 14:22:45.3	0	0
\.


--
-- Data for Name: t_push_history; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.t_push_history (id, msg_id, msg_type, msg_name, result, csv_file, create_time, modified_time, tenant_id, deleted) FROM stdin;
5b50deca-7078-4622-a070-ff3b3ae4dcc9	5356e214-9673-4d48-b952-2894dc584765	3	告警通知	失败，失败原因：收件人列表为空，无法发送邮件。请检查邮件模板是否配置了用户组，以及用户组中是否包含有效的邮箱地址	\N	2025-12-10 14:52:05.675	\N	0	0
f6a0f0ab-9eab-4bea-84ac-3de4cc343843	5186b29e-1a14-494e-8dd3-af314f464d26	3	告警通知	失败，失败原因：收件人列表为空，无法发送邮件。请检查邮件模板是否配置了用户组，以及用户组中是否包含有效的邮箱地址	\N	2025-12-10 14:57:05.99	\N	0	0
e69ee9d8-20bf-4b96-8cd0-f9df9ab5b8b5	bf366265-b98c-4bc9-8b12-a8c2426c2110	3	告警通知	成功	\N	2025-12-10 15:03:06.538	\N	0	0
6ff49950-a9fa-4771-892b-fa17dd373634	907aec07-5b5f-4d88-bef0-9991262099f2	3	告警通知	成功	\N	2025-12-10 15:13:06.464	\N	0	0
cff756ca-97fe-433e-86c3-85f9ed2d2448	ade227fe-5ff3-4eda-9647-c133c0636189	3	告警通知	成功	\N	2025-12-10 15:19:06.381	\N	0	0
30157675-407b-4d5b-a33c-c454ad212b1c	e3a0432d-b0b2-438b-9681-9bfcc6a90873	3	告警通知	成功	\N	2025-12-10 15:24:06.48	\N	0	0
bf38c472-c3e6-4cdb-807e-c75ca044451b	175bc751-760d-40df-956b-ac2b3f374c60	3	告警通知	成功	\N	2025-12-10 15:29:06.505	\N	0	0
213297e3-64f3-4e39-9ade-058ddd11fa83	5bdb23a7-4e2d-46de-b746-7745d6fc6eb5	3	告警通知	成功	\N	2025-12-10 15:35:06.315	\N	0	0
5dd04995-921e-498f-9fe4-b9b0e10983a9	0d5b118a-2d4e-4f76-a212-8d172648aed4	3	告警通知	成功	\N	2025-12-10 15:40:06.373	\N	0	0
dca51709-6a52-4b90-bca8-24cd1abcedb3	fb6cd163-9339-4df1-8b93-6a0af93197ab	3	告警通知	成功	\N	2025-12-10 15:46:06.441	\N	0	0
\.


--
-- Data for Name: t_template_data; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.t_template_data (id, msg_type, msg_id, name, value, color, create_time, modified_time, tenant_id, deleted) FROM stdin;
a07934ea-b5ec-49e4-9d7e-19392015259b	1	327fbcc3-900d-4ed5-8d3e-e0d77b1828b4	用户名	测试用户	\N	2023-07-20 11:23:57.638	\N	1	0
28e92201-4b61-4208-9331-21e9bec406ae	1	327fbcc3-900d-4ed5-8d3e-e0d77b1828b4	用户性别	男	\N	2023-07-20 11:23:57.665	\N	1	0
\.


--
-- Data for Name: t_wx_account; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.t_wx_account (id, account_type, account_name, app_id, app_secret, token, aes_key, create_time, modified_time, tenant_id, deleted) FROM stdin;
\.


--
-- Data for Name: t_wx_cp_app; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.t_wx_cp_app (id, corpid, app_name, agent_id, secret, token, aes_key, create_time, modified_time, tenant_id, deleted) FROM stdin;
\.


--
-- Data for Name: t_wx_mp_user; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.t_wx_mp_user (open_id, nickname, sex_desc, sex, language, city, province, country, head_img_url, subscribe_time, union_id, remark, group_id, subscribe_scene, qr_scene, qr_scene_str, create_time, modified_time, tenant_id, deleted) FROM stdin;
\.


--
-- Name: t_ding_app_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.t_ding_app_id_seq', 1, false);


--
-- Name: t_msg_ding_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.t_msg_ding_id_seq', 1, false);


--
-- Name: t_msg_http_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.t_msg_http_id_seq', 1, false);


--
-- Name: t_msg_ma_subscribe_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.t_msg_ma_subscribe_id_seq', 1, false);


--
-- Name: t_msg_ma_template_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.t_msg_ma_template_id_seq', 1, false);


--
-- Name: table_name_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.table_name_id_seq', 1, false);


--
-- Name: message_config message_config_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.message_config
    ADD CONSTRAINT message_config_pkey PRIMARY KEY (id);


--
-- Name: t_ding_app t_ding_app_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.t_ding_app
    ADD CONSTRAINT t_ding_app_pkey PRIMARY KEY (id);


--
-- Name: t_msg_ding t_msg_ding_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.t_msg_ding
    ADD CONSTRAINT t_msg_ding_pkey PRIMARY KEY (id);


--
-- Name: t_msg_feishu t_msg_feishu_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.t_msg_feishu
    ADD CONSTRAINT t_msg_feishu_pkey PRIMARY KEY (id);


--
-- Name: t_msg_http t_msg_http_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.t_msg_http
    ADD CONSTRAINT t_msg_http_pkey PRIMARY KEY (id);


--
-- Name: t_msg_ma_subscribe t_msg_ma_subscribe_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.t_msg_ma_subscribe
    ADD CONSTRAINT t_msg_ma_subscribe_pkey PRIMARY KEY (id);


--
-- Name: t_msg_ma_template t_msg_ma_template_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.t_msg_ma_template
    ADD CONSTRAINT t_msg_ma_template_pkey PRIMARY KEY (id);


--
-- Name: t_msg_mail t_msg_mail_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.t_msg_mail
    ADD CONSTRAINT t_msg_mail_pkey PRIMARY KEY (id);


--
-- Name: t_msg_mp_subscribe t_msg_mp_subscribe_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.t_msg_mp_subscribe
    ADD CONSTRAINT t_msg_mp_subscribe_pkey PRIMARY KEY (id);


--
-- Name: t_msg_mp_template t_msg_mp_template_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.t_msg_mp_template
    ADD CONSTRAINT t_msg_mp_template_pkey PRIMARY KEY (id);


--
-- Name: t_msg_sms t_msg_sms_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.t_msg_sms
    ADD CONSTRAINT t_msg_sms_pkey PRIMARY KEY (id);


--
-- Name: t_msg_wx_cp t_msg_wx_cp_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.t_msg_wx_cp
    ADD CONSTRAINT t_msg_wx_cp_pkey PRIMARY KEY (id);


--
-- Name: t_msg_wx_uniform t_msg_wx_uniform_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.t_msg_wx_uniform
    ADD CONSTRAINT t_msg_wx_uniform_pkey PRIMARY KEY (id);


--
-- Name: t_preview_user_group t_preview_user_group_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.t_preview_user_group
    ADD CONSTRAINT t_preview_user_group_pkey PRIMARY KEY (id);


--
-- Name: t_preview_user t_preview_user_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.t_preview_user
    ADD CONSTRAINT t_preview_user_pkey PRIMARY KEY (id);


--
-- Name: t_push_history t_push_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.t_push_history
    ADD CONSTRAINT t_push_history_pkey PRIMARY KEY (id);


--
-- Name: t_template_data t_template_data_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.t_template_data
    ADD CONSTRAINT t_template_data_pkey PRIMARY KEY (id);


--
-- Name: t_wx_account t_wx_account_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.t_wx_account
    ADD CONSTRAINT t_wx_account_pkey PRIMARY KEY (id);


--
-- Name: t_wx_cp_app t_wx_cp_app_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.t_wx_cp_app
    ADD CONSTRAINT t_wx_cp_app_pkey PRIMARY KEY (id);


--
-- Name: t_wx_mp_user t_wx_mp_user_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.t_wx_mp_user
    ADD CONSTRAINT t_wx_mp_user_pkey PRIMARY KEY (open_id);


--
-- Name: t_msg_kefu table_name_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.t_msg_kefu
    ADD CONSTRAINT table_name_pkey PRIMARY KEY (id);


--
-- PostgreSQL database dump complete
--

\unrestrict fZCIMJ7YUAJZdjJWBs0ZadWJBe6KODBYATxobaCnaCKZbrSM1W5SnGMQELjs81N

