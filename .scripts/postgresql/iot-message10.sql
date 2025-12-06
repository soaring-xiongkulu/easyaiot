--
-- PostgreSQL database dump
--

\restrict jJvekh4qsQwg9NC8chVGiKFhvTdezWLZH80O4GSxCB2uKFFObckSowNHFhFbplA

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


\unrestrict jJvekh4qsQwg9NC8chVGiKFhvTdezWLZH80O4GSxCB2uKFFObckSowNHFhFbplA
\encoding SQL_ASCII
\connect -reuse-previous=on "dbname='iot-message20'"
\restrict jJvekh4qsQwg9NC8chVGiKFhvTdezWLZH80O4GSxCB2uKFFObckSowNHFhFbplA

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
{"mailHost":"smtp.qq.com","mailPort":465,"mailFrom":"853017739@qq.com","mailUser":"853017739@qq.com","mailPassword":"gorttpgwqdiabdfc","starttlsEnable":false,"sslEnable":true}	1689749908832	25ea1da0-ed50-11ed-b15c-5face31d80ce	83440192-e39b-4674-98a7-c4f2e70fea8e	3	1	0
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
233b5141-0d06-4f04-a411-486635218698	5	http	POST	http://www.baidu.com	[{"id":0,"name":"p1","value":"p1"}]	[{"id":0,"name":"h1","value":"h1"}]	[{"id":0,"name":"c1","value":"c1","domain":"c1","path":"c1","time":"1690169035649"}]	消息内容	application/json	2023-07-24 11:24:24.178	\N	\N	\N	1	0
d294013c-551a-4cf2-ac69-9048680b569f	5	http2	GET	1	[]	[]	[]	\N	\N	2023-07-25 11:00:58.377	\N	\N	\N	1	0
5ad3a737-6cd2-49ca-b649-2eec29a940c8	5	http推送测试	POST	http://123.com	[{"id":0,"name":"test","value":"test"}]	[{"id":0,"name":"Content-Type","value":"application/json"},{"id":1,"name":"Keep-Alive","value":"timeout=60"},{"id":2,"name":"Connection","value":"keep-alive"}]	[]	{"test":"test”}	application/json	2023-07-25 11:47:40.465	\N	\N	\N	1	0
c065f756-ccd1-4c9e-b09b-3fa7534f63cc	5	http001	GET	http://www.baidu.com	[{"id":0,"name":"1","value":"1"},{"id":1,"name":"2","value":"2"}]	[{"id":0,"name":"1","value":"1"}]	[]	\N	\N	2023-07-25 15:21:17.794	2023-07-25 15:21:31.18	\N	\N	1	0
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
944e8411-8c13-4e9e-9b14-f8edf0aeeeae	3	邮件1	aa	ss@si.com	{"id":0,"filePath":"http://120.77.217.53:39000/messagenotificationfile/annex/2023/07/24/1ebd6786-2012-42af-9c2d-d753926e5d1a.jpg","fileName":"规划要做的20个服务.jpg"}	aa	2023-07-24 09:30:20.301	2023-07-24 17:14:22.378	andywebjava@163.com	\N	1	0
05753441-d5d9-43c1-a7a0-667108a19df4	3	用户分组测试	用户分组测试	aa@Si.com	{"id":0,"filePath":"","fileName":""}	test	2023-07-27 14:46:14.457	2023-07-27 14:48:33.654	andywebjava@163.com	\N	1	0
1	3	邮件测试发送	邮件测试发送		{"id":"001","fileName":"接口文档.txt","filePath":"http://120.77.217.53:39000/thingsboardfile/mailAnnex/2023/07/21/e2147071-2061-4755-b318-2fa33652bc30.txt"}	邮件测试发送_20230724	2023-07-24 08:30:20.301	2023-07-24 17:24:39.519	andywebjava@163.com	\N	1	0
5ee8cd54-6cd7-4a5e-99b8-ed8f76eccd2f	3	哇哈哈	您好			哇哈哈	2023-07-25 14:23:29.162	2023-07-25 14:28:03.585	andywebjava@163.com	\N	1	0
5195a5ea-5c7a-4b6d-a0d4-313ead959a63	3	email001	email001	email001@si.com		test	2023-07-25 15:05:40.656	2023-07-25 15:08:30.067	andywebjava@163.com	\N	1	0
807db0ec-4d8a-4414-a4d1-ec6abfc59979	3	email002	email002	email002@si.com		1	2023-07-25 15:08:56.214	2023-07-25 17:23:36.962	andywebjava@163.com	\N	1	0
515bdf64-20e9-4035-b6bf-6cc6364a5372	3	邮件测试推送	邮件测试推送	1184152227@qq.com	{"id":0,"filePath":"http://120.77.217.53:39000/messagenotificationfile/annex/2023/07/26/31216695-bd3d-4749-8d31-f0c506e12fca.pdf","fileName":"2021年上半年全员信息安全考试培训材料.pdf"}	这是一封来自统一消息通知平台的测试邮件",\n                    "<h1>恭喜，配置正确，邮件发送成功！</h1><p>来自统一消息通知平台，一款专注于批量推送的小而美的工具。</p>	2023-07-24 17:26:01.549	2023-07-26 10:02:13.329	andywebjava@163.com	\N	1	0
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
327fbcc3-900d-4ed5-8d3e-e0d77b1828b4	1	阿里云短信消息模板	test1	\N	2023-07-20 11:23:57.285	\N	13548739321	\N	1	0
8287105d-8692-44a9-8728-3981401323b9	2	tengxun	aaa1	\N	2023-07-24 10:07:44.482	\N	13548739321	\N	1	0
b6c6ae8c-7577-4a74-af71-6de12323a1cc	1	阿里云短信消息模板2	test1	\N	2023-07-20 11:21:48.505	\N	13548739321	\N	1	0
7f5da3de-acc6-4268-903e-82f44f5acfbe	1	aliyun	aa1	\N	2023-07-24 11:01:00.255	\N	13548739321	\N	1	0
1fd097c4-ff9f-46b9-8d14-96fafbcfa916	2	tentxunyun001	txy1110	\N	2023-07-25 15:10:56.575	2023-07-25 15:11:13.499	13387641922	\N	1	0
1	1	阿里云短信test	sms_001	\N	\N	2023-07-25 15:35:10.764	13548739321	\N	1	0
12113123-a79b-498a-b8e7-79cec71fa34c	2	tengxunyun002	002	\N	2023-07-25 15:13:15.758	2023-07-25 15:36:25.936	13387641922	\N	1	0
92e5a1a6-6d2f-4568-9668-07d05d71bace	1	阿里云告警通知模板	SMS_462165066	\N	2023-07-24 10:55:44.406	2023-07-26 14:09:34.971	13548739321	\N	1	0
0fe8e818-7ab1-460c-a6f9-2362019f0376	1	用户分组测试	001	\N	2023-07-27 14:50:06.721	2023-07-27 15:01:32.966	\N	53761ad7-8a08-4023-8529-96d5171ed542	1	0
\.


--
-- Data for Name: t_msg_wx_cp; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.t_msg_wx_cp (id, msg_type, msg_name, cp_msg_type, agent_id, content, title, img_url, describe, url, btn_txt, create_time, modified_time, preview_user, user_group_id, tenant_id, deleted) FROM stdin;
4be6326c-bb47-44c1-838a-84634e4c47d5	4	企业微信001	图文消息	1	\N	test	test	test1	test	\N	2023-07-25 15:19:27.145	2023-07-25 15:19:33.581	pengjian	\N	1	0
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
9615869e-4da3-43f9-9536-c591023e568b	1	aaa	2023-07-21 11:47:29.174	1	0
6ea907a6-6082-4d99-9539-e888477fd717	6	1	2023-07-21 11:50:56.586	1	0
81bd8aa7-beb1-4b61-926a-862a7166eeca	4	22	2023-07-21 11:51:02.152	1	0
fefa03e1-8599-443e-9c72-d3d8639c16e5	2	1	2023-07-21 11:51:10.29	1	0
b0a89baa-38b3-407a-8f67-39207aa66d56	1	13548739321	2023-07-21 17:22:47.761	1	0
15cb5775-7fea-4735-bd4b-cde521dd89c8	3	1184152227@qq.com	2023-07-24 18:09:44.11	1	0
0b291ae8-4ce8-4a97-aab4-737a312f4efd	3	1769324819@qq.com	2023-07-20 11:02:02.195	1	0
9d5b9618-0ece-4b48-8c94-ad985af512b7	1	13387641922	2023-07-25 10:43:21.895	1	0
9ae077f1-9c44-4af9-85fe-fdc09392f94f	2	13387641922	2023-07-25 10:43:21.94	1	0
c25d6e8b-9a6f-4a4a-9b76-1f043f2afda7	3	1131473524@qq.com	2023-07-25 10:43:21.961	1	0
918171cd-c25f-46a6-8bae-f2f7ffba8c96	6	manager9115	2023-07-25 10:43:21.984	1	0
23a2d3aa-d424-4929-97a2-88312dc0c20b	4	pengjian	2023-07-25 10:43:22.005	1	0
2b09cc4b-9404-4165-833a-fed4d6a415b8	1	13397682981	2023-07-25 15:22:22.823	1	0
a2ce3671-5e50-49a2-9281-710b96749ef0	3	test0@test.com	2023-07-26 14:37:51.746	1	0
b1ff9e5a-7a0c-42d0-a27b-645291eb03e3	3	test1@test.com	2023-07-26 14:37:51.775	1	0
\.


--
-- Data for Name: t_preview_user_group; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.t_preview_user_group (id, msg_type, user_group_name, preview_user_id, create_time, tenant_id, deleted) FROM stdin;
53761ad7-8a08-4023-8529-96d5171ed542	1	测试阿里云用户组1	b0a89baa-38b3-407a-8f67-39207aa66d56	2023-07-27 11:54:35.738	1	0
c52b76fa-1ee7-4c5d-8305-075ea876272b	3	测试邮件用户组1	0b291ae8-4ce8-4a97-aab4-737a312f4efd,0dec81aa-4c8e-4b45-a4bb-59743c500f26	2023-07-27 09:31:54.007	1	0
5337a7f5-e947-4b93-818e-b1629f515103	6	dingding	918171cd-c25f-46a6-8bae-f2f7ffba8c96,6ea907a6-6082-4d99-9539-e888477fd717	2023-07-27 11:54:23.204	1	0
\.


--
-- Data for Name: t_push_history; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.t_push_history (id, msg_id, msg_type, msg_name, result, csv_file, create_time, modified_time, tenant_id, deleted) FROM stdin;
245f6a94-8f65-4c94-b14e-0740ddfc62d3	1	3	邮件测试发送	成功	\N	2023-07-24 14:31:00.626	\N	1	0
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

\unrestrict jJvekh4qsQwg9NC8chVGiKFhvTdezWLZH80O4GSxCB2uKFFObckSowNHFhFbplA

