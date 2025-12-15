--
-- PostgreSQL database dump
--

\restrict Fxw8kG3gVEObSjt53dfInfuAPpla7dLlSt2hdg1IzOtgl3fYIegIsi0S4hwmPKX

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

DROP DATABASE IF EXISTS "iot-device20";
--
-- Name: iot-device20; Type: DATABASE; Schema: -; Owner: -
--

CREATE DATABASE "iot-device20" WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'en_US.utf8';


\unrestrict Fxw8kG3gVEObSjt53dfInfuAPpla7dLlSt2hdg1IzOtgl3fYIegIsi0S4hwmPKX
\encoding SQL_ASCII
\connect -reuse-previous=on "dbname='iot-device20'"
\restrict Fxw8kG3gVEObSjt53dfInfuAPpla7dLlSt2hdg1IzOtgl3fYIegIsi0S4hwmPKX

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

--
-- Name: update_updated_time_column(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_updated_time_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_time = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


--
-- Name: algorithm_alarm_data_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.algorithm_alarm_data_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: algorithm_customer_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.algorithm_customer_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: algorithm_model_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.algorithm_model_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: algorithm_nvr_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.algorithm_nvr_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: algorithm_playback_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.algorithm_playback_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: algorithm_push_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.algorithm_push_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: algorithm_task_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.algorithm_task_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: algorithm_video_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.algorithm_video_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: app; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.app (
    id bigint NOT NULL,
    app_id character varying(32) NOT NULL,
    app_key character varying(32) NOT NULL,
    app_secret character varying(64) NOT NULL,
    app_name character varying(128) DEFAULT NULL::character varying,
    app_desc character varying(512) DEFAULT NULL::character varying,
    status character varying(16) DEFAULT 'ENABLE'::character varying NOT NULL,
    permission_type character varying(16) DEFAULT 'READ_WRITE'::character varying NOT NULL,
    expire_time timestamp without time zone,
    tenant_id bigint,
    remark character varying(512) DEFAULT NULL::character varying,
    created_by character varying(64) DEFAULT NULL::character varying,
    created_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_by character varying(64) DEFAULT NULL::character varying,
    updated_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted smallint DEFAULT 0
);


--
-- Name: TABLE app; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.app IS '应用密钥表';


--
-- Name: COLUMN app.id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.app.id IS '主键ID';


--
-- Name: COLUMN app.app_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.app.app_id IS '应用ID（AppID）：应用的唯一标识';


--
-- Name: COLUMN app.app_key; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.app.app_key IS '应用密钥（AppKey）：公匙，相当于账号';


--
-- Name: COLUMN app.app_secret; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.app.app_secret IS '应用密钥（AppSecret）：私匙，相当于密码';


--
-- Name: COLUMN app.app_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.app.app_name IS '应用名称';


--
-- Name: COLUMN app.app_desc; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.app.app_desc IS '应用描述';


--
-- Name: COLUMN app.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.app.status IS '状态：ENABLE-启用，DISABLE-禁用';


--
-- Name: COLUMN app.permission_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.app.permission_type IS '权限类型：READ_ONLY-只读，READ_WRITE-读写';


--
-- Name: COLUMN app.expire_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.app.expire_time IS '过期时间';


--
-- Name: COLUMN app.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.app.tenant_id IS '租户编号';


--
-- Name: COLUMN app.remark; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.app.remark IS '备注';


--
-- Name: COLUMN app.created_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.app.created_by IS '创建人';


--
-- Name: COLUMN app.created_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.app.created_time IS '创建时间';


--
-- Name: COLUMN app.updated_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.app.updated_by IS '更新人';


--
-- Name: COLUMN app.updated_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.app.updated_time IS '更新时间';


--
-- Name: COLUMN app.deleted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.app.deleted IS '是否删除：0-未删除，1-已删除';


--
-- Name: dataset; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dataset (
    id bigint NOT NULL,
    dataset_code character varying(200) NOT NULL,
    name character varying(200) NOT NULL,
    cover_path character varying(200),
    description character varying(200),
    dataset_type smallint NOT NULL,
    audit smallint NOT NULL,
    reason character varying(200),
    create_by character varying(255),
    create_time timestamp(6) without time zone,
    tenant_id bigint DEFAULT 0 NOT NULL,
    update_by character varying(255),
    update_time timestamp(6) without time zone,
    deleted smallint DEFAULT 0 NOT NULL,
    is_allocated smallint DEFAULT 0 NOT NULL,
    model_service_id bigint,
    is_sync_minio smallint DEFAULT 0 NOT NULL,
    zip_url character varying(500)
);


--
-- Name: TABLE dataset; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.dataset IS '数据集表';


--
-- Name: COLUMN dataset.id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset.id IS '主键ID';


--
-- Name: COLUMN dataset.dataset_code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset.dataset_code IS '数据集编码';


--
-- Name: COLUMN dataset.name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset.name IS '数据集名称';


--
-- Name: COLUMN dataset.cover_path; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset.cover_path IS '封面地址';


--
-- Name: COLUMN dataset.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset.description IS '描述';


--
-- Name: COLUMN dataset.dataset_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset.dataset_type IS '数据集类型，0-图片；1-文本';


--
-- Name: COLUMN dataset.audit; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset.audit IS '数据集状态：0-待审核；1-审核通过；2-审核驳回';


--
-- Name: COLUMN dataset.reason; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset.reason IS '审核驳回理由';


--
-- Name: COLUMN dataset.create_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset.create_by IS '创建人';


--
-- Name: COLUMN dataset.create_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset.create_time IS '创建时间';


--
-- Name: COLUMN dataset.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset.tenant_id IS '租户编号';


--
-- Name: COLUMN dataset.update_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset.update_by IS '创建人';


--
-- Name: COLUMN dataset.update_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset.update_time IS '创建时间';


--
-- Name: COLUMN dataset.deleted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset.deleted IS '是否删除';


--
-- Name: COLUMN dataset.is_allocated; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset.is_allocated IS '是否已划分数据集[0:否,1:是]';


--
-- Name: COLUMN dataset.model_service_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset.model_service_id IS '自动化标注预训练模型服务ID';


--
-- Name: COLUMN dataset.is_sync_minio; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset.is_sync_minio IS '是否已生成数据集到Minio[0:否,1:是]';


--
-- Name: COLUMN dataset.zip_url; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset.zip_url IS '数据集压缩包下载地址';


--
-- Name: dataset_frame_task; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dataset_frame_task (
    id bigint NOT NULL,
    dataset_id bigint NOT NULL,
    task_name character varying(255) NOT NULL,
    task_code character varying(20) NOT NULL,
    task_type smallint NOT NULL,
    channel_id character varying(50),
    device_id character varying(50),
    rtmp_url character varying(100),
    create_by character varying(255),
    create_time timestamp(6) without time zone,
    tenant_id bigint DEFAULT 0 NOT NULL,
    update_by character varying(255),
    update_time timestamp(6) without time zone,
    deleted smallint DEFAULT 0 NOT NULL
);


--
-- Name: TABLE dataset_frame_task; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.dataset_frame_task IS '视频流帧捕获任务';


--
-- Name: COLUMN dataset_frame_task.id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_frame_task.id IS '主键id';


--
-- Name: COLUMN dataset_frame_task.dataset_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_frame_task.dataset_id IS '数据集ID';


--
-- Name: COLUMN dataset_frame_task.task_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_frame_task.task_name IS '任务名称';


--
-- Name: COLUMN dataset_frame_task.task_code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_frame_task.task_code IS '任务编码';


--
-- Name: COLUMN dataset_frame_task.task_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_frame_task.task_type IS '任务类型[0:实时帧捕获,1:GB28181帧捕获]';


--
-- Name: COLUMN dataset_frame_task.channel_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_frame_task.channel_id IS '通道ID';


--
-- Name: COLUMN dataset_frame_task.device_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_frame_task.device_id IS '设备ID';


--
-- Name: COLUMN dataset_frame_task.rtmp_url; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_frame_task.rtmp_url IS 'RTMP流地址';


--
-- Name: COLUMN dataset_frame_task.create_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_frame_task.create_by IS '创建人';


--
-- Name: COLUMN dataset_frame_task.create_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_frame_task.create_time IS '创建时间';


--
-- Name: COLUMN dataset_frame_task.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_frame_task.tenant_id IS '租户编号';


--
-- Name: COLUMN dataset_frame_task.update_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_frame_task.update_by IS '创建人';


--
-- Name: COLUMN dataset_frame_task.update_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_frame_task.update_time IS '创建时间';


--
-- Name: COLUMN dataset_frame_task.deleted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_frame_task.deleted IS '是否删除';


--
-- Name: dataset_frame_task_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dataset_frame_task_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dataset_frame_task_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dataset_frame_task_id_seq OWNED BY public.dataset_frame_task.id;


--
-- Name: dataset_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dataset_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dataset_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dataset_id_seq OWNED BY public.dataset.id;


--
-- Name: dataset_image; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dataset_image (
    id bigint NOT NULL,
    dataset_id bigint NOT NULL,
    name character varying(200) NOT NULL,
    path character varying(200) NOT NULL,
    modification_count integer DEFAULT 0,
    last_modified timestamp(6) without time zone,
    width integer,
    heigh integer,
    size bigint,
    annotations text,
    dataset_video_id bigint,
    create_by character varying(255),
    create_time timestamp(6) without time zone,
    tenant_id bigint DEFAULT 0 NOT NULL,
    update_by character varying(255),
    update_time timestamp(6) without time zone,
    deleted smallint DEFAULT 0 NOT NULL,
    completed smallint DEFAULT 0 NOT NULL,
    is_train smallint DEFAULT 0 NOT NULL,
    is_validation smallint DEFAULT 0 NOT NULL,
    is_test smallint DEFAULT 0 NOT NULL
);


--
-- Name: TABLE dataset_image; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.dataset_image IS '图片数据集表';


--
-- Name: COLUMN dataset_image.id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_image.id IS '主键ID';


--
-- Name: COLUMN dataset_image.dataset_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_image.dataset_id IS '数据集ID';


--
-- Name: COLUMN dataset_image.name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_image.name IS '图片名称';


--
-- Name: COLUMN dataset_image.path; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_image.path IS '图片地址';


--
-- Name: COLUMN dataset_image.modification_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_image.modification_count IS '修改次数';


--
-- Name: COLUMN dataset_image.last_modified; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_image.last_modified IS '最后修改时间';


--
-- Name: COLUMN dataset_image.width; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_image.width IS '图片宽度';


--
-- Name: COLUMN dataset_image.heigh; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_image.heigh IS '图片高度';


--
-- Name: COLUMN dataset_image.size; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_image.size IS '图片大小';


--
-- Name: COLUMN dataset_image.annotations; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_image.annotations IS '标注信息，JSON格式';


--
-- Name: COLUMN dataset_image.dataset_video_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_image.dataset_video_id IS '视频ID（来源为视频切片）';


--
-- Name: COLUMN dataset_image.create_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_image.create_by IS '创建人';


--
-- Name: COLUMN dataset_image.create_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_image.create_time IS '创建时间';


--
-- Name: COLUMN dataset_image.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_image.tenant_id IS '租户编号';


--
-- Name: COLUMN dataset_image.update_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_image.update_by IS '创建人';


--
-- Name: COLUMN dataset_image.update_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_image.update_time IS '创建时间';


--
-- Name: COLUMN dataset_image.deleted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_image.deleted IS '是否删除';


--
-- Name: COLUMN dataset_image.completed; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_image.completed IS '是否标注完成[0:否,1:是]';


--
-- Name: COLUMN dataset_image.is_train; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_image.is_train IS '是否训练集[0:否,1:是]';


--
-- Name: COLUMN dataset_image.is_validation; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_image.is_validation IS '是否验证集[0:否,1:是]';


--
-- Name: COLUMN dataset_image.is_test; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_image.is_test IS '是否测试集[0:否,1:是]';


--
-- Name: dataset_image_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dataset_image_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dataset_image_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dataset_image_id_seq OWNED BY public.dataset_image.id;


--
-- Name: dataset_image_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dataset_image_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dataset_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dataset_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dataset_tag; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dataset_tag (
    id bigint NOT NULL,
    name character varying(200) NOT NULL,
    color character varying(20),
    dataset_id bigint NOT NULL,
    warehouse_id bigint,
    description character varying(200),
    create_by character varying(255),
    create_time timestamp(6) without time zone,
    tenant_id bigint DEFAULT 0 NOT NULL,
    update_by character varying(255),
    update_time timestamp(6) without time zone,
    deleted smallint DEFAULT 0 NOT NULL,
    shortcut integer NOT NULL
);


--
-- Name: TABLE dataset_tag; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.dataset_tag IS '数据集标签表';


--
-- Name: COLUMN dataset_tag.id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_tag.id IS '主键ID';


--
-- Name: COLUMN dataset_tag.name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_tag.name IS '标签名称';


--
-- Name: COLUMN dataset_tag.color; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_tag.color IS '标签颜色';


--
-- Name: COLUMN dataset_tag.dataset_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_tag.dataset_id IS '数据集ID';


--
-- Name: COLUMN dataset_tag.warehouse_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_tag.warehouse_id IS '数据仓ID';


--
-- Name: COLUMN dataset_tag.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_tag.description IS '描述';


--
-- Name: COLUMN dataset_tag.create_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_tag.create_by IS '创建人';


--
-- Name: COLUMN dataset_tag.create_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_tag.create_time IS '创建时间';


--
-- Name: COLUMN dataset_tag.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_tag.tenant_id IS '租户编号';


--
-- Name: COLUMN dataset_tag.update_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_tag.update_by IS '创建人';


--
-- Name: COLUMN dataset_tag.update_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_tag.update_time IS '创建时间';


--
-- Name: COLUMN dataset_tag.deleted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_tag.deleted IS '是否删除';


--
-- Name: COLUMN dataset_tag.shortcut; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_tag.shortcut IS '快捷键编号';


--
-- Name: dataset_tag_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dataset_tag_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dataset_tag_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dataset_tag_id_seq OWNED BY public.dataset_tag.id;


--
-- Name: dataset_tag_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dataset_tag_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dataset_task; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dataset_task (
    id bigint NOT NULL,
    name character varying(200) NOT NULL,
    dataset_id bigint NOT NULL,
    data_range smallint NOT NULL,
    planned_quantity integer NOT NULL,
    marked_quantity integer DEFAULT 0,
    new_label smallint NOT NULL,
    finish_status smallint NOT NULL,
    finish_time timestamp(6) without time zone,
    model_id bigint,
    model_serve_id bigint,
    is_stop smallint DEFAULT 0 NOT NULL,
    task_type smallint NOT NULL,
    end_time timestamp(6) without time zone,
    not_target_count integer DEFAULT 0,
    create_by character varying(255),
    create_time timestamp(6) without time zone,
    tenant_id bigint DEFAULT 0 NOT NULL,
    update_by character varying(255),
    update_time timestamp(6) without time zone,
    deleted smallint DEFAULT 0 NOT NULL
);


--
-- Name: TABLE dataset_task; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.dataset_task IS '标注任务表';


--
-- Name: COLUMN dataset_task.id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task.id IS '主键ID';


--
-- Name: COLUMN dataset_task.name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task.name IS '任务名称';


--
-- Name: COLUMN dataset_task.dataset_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task.dataset_id IS '数据集ID';


--
-- Name: COLUMN dataset_task.data_range; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task.data_range IS '数据范围[0:全部,1:无标注,2:有标注]';


--
-- Name: COLUMN dataset_task.planned_quantity; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task.planned_quantity IS '计划标注数量';


--
-- Name: COLUMN dataset_task.marked_quantity; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task.marked_quantity IS '已标注数量';


--
-- Name: COLUMN dataset_task.new_label; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task.new_label IS '新标签入库[0:否,1:是]';


--
-- Name: COLUMN dataset_task.finish_status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task.finish_status IS '完成状态[0:未完成,1:已完成]';


--
-- Name: COLUMN dataset_task.finish_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task.finish_time IS '完成时间';


--
-- Name: COLUMN dataset_task.model_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task.model_id IS '模型ID';


--
-- Name: COLUMN dataset_task.model_serve_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task.model_serve_id IS '模型服务ID';


--
-- Name: COLUMN dataset_task.is_stop; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task.is_stop IS '是否停止[0:否,1:是]';


--
-- Name: COLUMN dataset_task.task_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task.task_type IS '任务类型[0:智能标注,1:人员标注,2:审核]';


--
-- Name: COLUMN dataset_task.end_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task.end_time IS '截止时间(人员或审核)';


--
-- Name: COLUMN dataset_task.not_target_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task.not_target_count IS '无目标数量';


--
-- Name: COLUMN dataset_task.create_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task.create_by IS '创建人';


--
-- Name: COLUMN dataset_task.create_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task.create_time IS '创建时间';


--
-- Name: COLUMN dataset_task.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task.tenant_id IS '租户编号';


--
-- Name: COLUMN dataset_task.update_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task.update_by IS '创建人';


--
-- Name: COLUMN dataset_task.update_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task.update_time IS '创建时间';


--
-- Name: COLUMN dataset_task.deleted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task.deleted IS '是否删除';


--
-- Name: dataset_task_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dataset_task_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dataset_task_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dataset_task_id_seq OWNED BY public.dataset_task.id;


--
-- Name: dataset_task_result; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dataset_task_result (
    id bigint NOT NULL,
    dataset_image_id bigint NOT NULL,
    model_id bigint,
    has_anno smallint NOT NULL,
    annos character varying(200) NOT NULL,
    task_type smallint NOT NULL,
    user_id bigint NOT NULL,
    pass_status smallint NOT NULL,
    task_id bigint NOT NULL,
    reason character varying(200),
    is_update smallint DEFAULT 0 NOT NULL,
    create_by character varying(255),
    create_time timestamp(6) without time zone,
    tenant_id bigint DEFAULT 0 NOT NULL,
    update_by character varying(255),
    update_time timestamp(6) without time zone,
    deleted smallint DEFAULT 0 NOT NULL
);


--
-- Name: TABLE dataset_task_result; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.dataset_task_result IS '标注任务结果表';


--
-- Name: COLUMN dataset_task_result.id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task_result.id IS '主键ID';


--
-- Name: COLUMN dataset_task_result.dataset_image_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task_result.dataset_image_id IS '数据集图片ID';


--
-- Name: COLUMN dataset_task_result.model_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task_result.model_id IS '模型ID';


--
-- Name: COLUMN dataset_task_result.has_anno; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task_result.has_anno IS '是否有标注[0:无,1:有]';


--
-- Name: COLUMN dataset_task_result.annos; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task_result.annos IS '标注信息';


--
-- Name: COLUMN dataset_task_result.task_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task_result.task_type IS '任务类型[0:智能标注,1:人员标注,2:审核]';


--
-- Name: COLUMN dataset_task_result.user_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task_result.user_id IS '标注或审核的用户id';


--
-- Name: COLUMN dataset_task_result.pass_status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task_result.pass_status IS '通过状态[0:待审核,1:通过,2:驳回]';


--
-- Name: COLUMN dataset_task_result.task_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task_result.task_id IS '任务ID';


--
-- Name: COLUMN dataset_task_result.reason; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task_result.reason IS '驳回原因';


--
-- Name: COLUMN dataset_task_result.is_update; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task_result.is_update IS '是否修改过[0:否,1是]';


--
-- Name: COLUMN dataset_task_result.create_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task_result.create_by IS '创建人';


--
-- Name: COLUMN dataset_task_result.create_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task_result.create_time IS '创建时间';


--
-- Name: COLUMN dataset_task_result.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task_result.tenant_id IS '租户编号';


--
-- Name: COLUMN dataset_task_result.update_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task_result.update_by IS '创建人';


--
-- Name: COLUMN dataset_task_result.update_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task_result.update_time IS '创建时间';


--
-- Name: COLUMN dataset_task_result.deleted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task_result.deleted IS '是否删除';


--
-- Name: dataset_task_result_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dataset_task_result_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dataset_task_result_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dataset_task_result_id_seq OWNED BY public.dataset_task_result.id;


--
-- Name: dataset_task_result_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dataset_task_result_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dataset_task_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dataset_task_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dataset_task_user; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dataset_task_user (
    id bigint NOT NULL,
    task_id bigint NOT NULL,
    user_id bigint NOT NULL,
    audit_user_id bigint,
    create_by character varying(255),
    create_time timestamp(6) without time zone,
    tenant_id bigint DEFAULT 0 NOT NULL,
    update_by character varying(255),
    update_time timestamp(6) without time zone,
    deleted smallint DEFAULT 0 NOT NULL
);


--
-- Name: TABLE dataset_task_user; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.dataset_task_user IS '标注任务用户表';


--
-- Name: COLUMN dataset_task_user.id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task_user.id IS '主键ID';


--
-- Name: COLUMN dataset_task_user.task_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task_user.task_id IS '任务ID';


--
-- Name: COLUMN dataset_task_user.user_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task_user.user_id IS '标注用户ID';


--
-- Name: COLUMN dataset_task_user.audit_user_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task_user.audit_user_id IS '审核用户ID';


--
-- Name: COLUMN dataset_task_user.create_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task_user.create_by IS '创建人';


--
-- Name: COLUMN dataset_task_user.create_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task_user.create_time IS '创建时间';


--
-- Name: COLUMN dataset_task_user.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task_user.tenant_id IS '租户编号';


--
-- Name: COLUMN dataset_task_user.update_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task_user.update_by IS '创建人';


--
-- Name: COLUMN dataset_task_user.update_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task_user.update_time IS '创建时间';


--
-- Name: COLUMN dataset_task_user.deleted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_task_user.deleted IS '是否删除';


--
-- Name: dataset_task_user_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dataset_task_user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dataset_task_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dataset_task_user_id_seq OWNED BY public.dataset_task_user.id;


--
-- Name: dataset_task_user_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dataset_task_user_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dataset_video; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dataset_video (
    id bigint NOT NULL,
    dataset_id bigint NOT NULL,
    video_path character varying(200) NOT NULL,
    cover_path character varying(200),
    description character varying(200),
    create_by character varying(255),
    create_time timestamp(6) without time zone,
    tenant_id bigint DEFAULT 0 NOT NULL,
    update_by character varying(255),
    update_time timestamp(6) without time zone,
    deleted smallint DEFAULT 0 NOT NULL,
    name character varying(200) NOT NULL
);


--
-- Name: TABLE dataset_video; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.dataset_video IS '视频数据集表';


--
-- Name: COLUMN dataset_video.id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_video.id IS '主键ID';


--
-- Name: COLUMN dataset_video.dataset_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_video.dataset_id IS '数据集ID';


--
-- Name: COLUMN dataset_video.video_path; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_video.video_path IS '视频地址';


--
-- Name: COLUMN dataset_video.cover_path; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_video.cover_path IS '封面地址';


--
-- Name: COLUMN dataset_video.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_video.description IS '描述';


--
-- Name: COLUMN dataset_video.create_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_video.create_by IS '创建人';


--
-- Name: COLUMN dataset_video.create_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_video.create_time IS '创建时间';


--
-- Name: COLUMN dataset_video.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_video.tenant_id IS '租户编号';


--
-- Name: COLUMN dataset_video.update_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_video.update_by IS '创建人';


--
-- Name: COLUMN dataset_video.update_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_video.update_time IS '创建时间';


--
-- Name: COLUMN dataset_video.deleted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_video.deleted IS '是否删除';


--
-- Name: COLUMN dataset_video.name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dataset_video.name IS '视频名称';


--
-- Name: dataset_video_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dataset_video_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dataset_video_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dataset_video_id_seq OWNED BY public.dataset_video.id;


--
-- Name: dataset_video_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dataset_video_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: datasource_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.datasource_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: device; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.device (
    id bigint NOT NULL,
    client_id character varying(10),
    app_id character varying(10),
    device_identification character varying(20) NOT NULL,
    device_name character varying(50),
    device_description character varying(300),
    device_status character varying(10),
    connect_status character varying(10) DEFAULT 'OFFLINE'::character varying,
    is_will character varying(2),
    product_identification character varying(20) NOT NULL,
    create_by character varying(10),
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    update_by character varying(10),
    update_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    remark character varying(100),
    device_version character varying(100),
    device_sn character varying(20) NOT NULL,
    ip_address character varying(20),
    mac_address character varying(20),
    active_status smallint DEFAULT 0,
    extension text,
    activated_time timestamp without time zone,
    last_online_time timestamp without time zone,
    parent_identification character varying(20),
    device_type character varying,
    tenant_id bigint DEFAULT 0 NOT NULL,
    deleted smallint DEFAULT 0 NOT NULL
);


--
-- Name: TABLE device; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.device IS '边设备档案信息表';


--
-- Name: COLUMN device.id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.id IS 'id';


--
-- Name: COLUMN device.client_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.client_id IS '客户端标识';


--
-- Name: COLUMN device.app_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.app_id IS '应用ID';


--
-- Name: COLUMN device.device_identification; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.device_identification IS '设备标识';


--
-- Name: COLUMN device.device_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.device_name IS '设备名称';


--
-- Name: COLUMN device.device_description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.device_description IS '设备描述';


--
-- Name: COLUMN device.device_status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.device_status IS '设备状态： ENABLE:启用 || DISABLE:禁用';


--
-- Name: COLUMN device.connect_status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.connect_status IS '连接状态 :    OFFLINE:离线 || ONLINE:在线';


--
-- Name: COLUMN device.is_will; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.is_will IS '是否遗言';


--
-- Name: COLUMN device.product_identification; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.product_identification IS '产品标识';


--
-- Name: COLUMN device.create_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.create_by IS '创建者';


--
-- Name: COLUMN device.create_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.create_time IS '创建时间';


--
-- Name: COLUMN device.update_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.update_by IS '更新者';


--
-- Name: COLUMN device.update_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.update_time IS '更新时间';


--
-- Name: COLUMN device.remark; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.remark IS '备注';


--
-- Name: COLUMN device.device_version; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.device_version IS '设备版本';


--
-- Name: COLUMN device.device_sn; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.device_sn IS '设备sn号';


--
-- Name: COLUMN device.ip_address; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.ip_address IS 'ip地址';


--
-- Name: COLUMN device.mac_address; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.mac_address IS 'mac地址';


--
-- Name: COLUMN device.active_status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.active_status IS '激活状态 0:未激活 1:已激活';


--
-- Name: COLUMN device.extension; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.extension IS '扩展json';


--
-- Name: COLUMN device.activated_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.activated_time IS '激活时间';


--
-- Name: COLUMN device.last_online_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.last_online_time IS '最后上线时间';


--
-- Name: COLUMN device.parent_identification; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.parent_identification IS '关联网关设备标识';


--
-- Name: COLUMN device.device_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.device_type IS '支持以下两种产品类型
•COMMON：普通产品，需直连设备。
•GATEWAY：网关产品，可挂载子设备。
•SUBSET：子设备。
•VIDEO_COMMON：视频设备。';


--
-- Name: COLUMN device.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.tenant_id IS '租户编号';


--
-- Name: COLUMN device.deleted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.deleted IS '是否删除';


--
-- Name: device_event; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.device_event (
    id bigint NOT NULL,
    device_identification character varying(255),
    event_type character varying(255),
    message text,
    status character varying(255),
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    event_name character varying(255),
    event_code character varying(255),
    deleted smallint DEFAULT 0 NOT NULL,
    tenant_id bigint DEFAULT 0 NOT NULL
);


--
-- Name: TABLE device_event; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.device_event IS '设备动作数据表';


--
-- Name: COLUMN device_event.id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_event.id IS 'id';


--
-- Name: COLUMN device_event.device_identification; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_event.device_identification IS '设备标识';


--
-- Name: COLUMN device_event.event_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_event.event_type IS '事件类型';


--
-- Name: COLUMN device_event.message; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_event.message IS '内容信息';


--
-- Name: COLUMN device_event.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_event.status IS '状态';


--
-- Name: COLUMN device_event.create_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_event.create_time IS '创建时间';


--
-- Name: COLUMN device_event.event_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_event.event_name IS '事件名称';


--
-- Name: COLUMN device_event.event_code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_event.event_code IS '事件标识符';


--
-- Name: COLUMN device_event.deleted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_event.deleted IS '是否删除';


--
-- Name: COLUMN device_event.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_event.tenant_id IS '租户编号';


--
-- Name: device_event_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.device_event_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: device_event_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.device_event_id_seq OWNED BY public.device_event.id;


--
-- Name: device_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.device_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: device_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.device_id_seq OWNED BY public.device.id;


--
-- Name: device_location; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.device_location (
    id bigint NOT NULL,
    device_identification character varying(100) NOT NULL,
    latitude numeric(10,7),
    longitude numeric(10,7),
    full_name character varying(500),
    province_code character varying(50),
    city_code character varying(50),
    region_code character varying(50),
    create_by character varying(64),
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    update_by character varying(64),
    update_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    remark character varying(500),
    tenant_id bigint DEFAULT 0 NOT NULL,
    deleted smallint DEFAULT 0 NOT NULL
);


--
-- Name: COLUMN device_location.id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_location.id IS '主键';


--
-- Name: COLUMN device_location.device_identification; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_location.device_identification IS '设备标识';


--
-- Name: COLUMN device_location.latitude; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_location.latitude IS '纬度';


--
-- Name: COLUMN device_location.longitude; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_location.longitude IS '经度';


--
-- Name: COLUMN device_location.full_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_location.full_name IS '位置名称';


--
-- Name: COLUMN device_location.province_code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_location.province_code IS '省,直辖市编码';


--
-- Name: COLUMN device_location.city_code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_location.city_code IS '市编码';


--
-- Name: COLUMN device_location.region_code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_location.region_code IS '区县';


--
-- Name: COLUMN device_location.create_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_location.create_by IS '创建者';


--
-- Name: COLUMN device_location.create_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_location.create_time IS '创建时间';


--
-- Name: COLUMN device_location.update_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_location.update_by IS '更新者';


--
-- Name: COLUMN device_location.update_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_location.update_time IS '更新时间';


--
-- Name: COLUMN device_location.remark; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_location.remark IS '备注';


--
-- Name: COLUMN device_location.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_location.tenant_id IS '租户编号';


--
-- Name: COLUMN device_location.deleted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_location.deleted IS '是否删除';


--
-- Name: device_location_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.device_location_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: device_location_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.device_location_id_seq OWNED BY public.device_location.id;


--
-- Name: device_log_file_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.device_log_file_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: device_ota_device_model_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.device_ota_device_model_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


--
-- Name: device_ota_pkg; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.device_ota_pkg (
    id integer NOT NULL,
    type smallint,
    name character varying(64),
    version character varying(64),
    upgrade_mode smallint,
    url character varying(500),
    key_version_flag smallint,
    status smallint,
    upload_time timestamp without time zone,
    publish_time timestamp without time zone,
    created_by character varying(64),
    created_time timestamp without time zone,
    updated_by character varying(64),
    file_md5 character varying(255),
    remark character varying(255),
    updated_time timestamp without time zone,
    tenant_id bigint DEFAULT 0 NOT NULL,
    deleted smallint DEFAULT 0 NOT NULL
);


--
-- Name: COLUMN device_ota_pkg.id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_ota_pkg.id IS '主键ID';


--
-- Name: COLUMN device_ota_pkg.type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_ota_pkg.type IS '包类型[0:软件包,1:固件包,2:电控包]';


--
-- Name: COLUMN device_ota_pkg.name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_ota_pkg.name IS '包名称';


--
-- Name: COLUMN device_ota_pkg.version; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_ota_pkg.version IS '包版本号';


--
-- Name: COLUMN device_ota_pkg.upgrade_mode; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_ota_pkg.upgrade_mode IS '升级方式[0:非强制升级,1:强制升级]';


--
-- Name: COLUMN device_ota_pkg.url; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_ota_pkg.url IS '包路径';


--
-- Name: COLUMN device_ota_pkg.key_version_flag; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_ota_pkg.key_version_flag IS '关键版本标识[0:否,1:是]';


--
-- Name: COLUMN device_ota_pkg.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_ota_pkg.status IS '状态[0:未验证,1:已验证,2:已发布]';


--
-- Name: COLUMN device_ota_pkg.upload_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_ota_pkg.upload_time IS '上传时间';


--
-- Name: COLUMN device_ota_pkg.publish_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_ota_pkg.publish_time IS '发布时间';


--
-- Name: COLUMN device_ota_pkg.created_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_ota_pkg.created_by IS '创建人';


--
-- Name: COLUMN device_ota_pkg.created_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_ota_pkg.created_time IS '创建时间';


--
-- Name: COLUMN device_ota_pkg.updated_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_ota_pkg.updated_by IS '更新人ID';


--
-- Name: COLUMN device_ota_pkg.file_md5; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_ota_pkg.file_md5 IS '文件MD5值';


--
-- Name: COLUMN device_ota_pkg.remark; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_ota_pkg.remark IS '备注';


--
-- Name: COLUMN device_ota_pkg.updated_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_ota_pkg.updated_time IS '更新时间';


--
-- Name: COLUMN device_ota_pkg.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_ota_pkg.tenant_id IS '租户编号';


--
-- Name: COLUMN device_ota_pkg.deleted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_ota_pkg.deleted IS '是否删除';


--
-- Name: device_ota_pkg_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.device_ota_pkg_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: device_ota_pkg_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.device_ota_pkg_id_seq OWNED BY public.device_ota_pkg.id;


--
-- Name: device_ota_version_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.device_ota_version_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


--
-- Name: device_ota_version_publish_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.device_ota_version_publish_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


--
-- Name: device_ota_version_verify_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.device_ota_version_verify_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


--
-- Name: device_service_invoke_response; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.device_service_invoke_response (
    id bigint NOT NULL,
    message_id character varying(255) NOT NULL,
    device_id bigint NOT NULL,
    device_identification character varying(255),
    product_identification character varying(255),
    service_identifier character varying(255),
    request_id character varying(255),
    method character varying(255),
    response_data text,
    response_code integer,
    response_msg character varying(500),
    topic character varying(500),
    report_time timestamp without time zone,
    tenant_id bigint DEFAULT 0 NOT NULL,
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: TABLE device_service_invoke_response; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.device_service_invoke_response IS '设备服务调用响应表，用于存储平台调用设备服务后，设备返回的ACK消息';


--
-- Name: COLUMN device_service_invoke_response.id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_service_invoke_response.id IS '主键ID';


--
-- Name: COLUMN device_service_invoke_response.message_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_service_invoke_response.message_id IS '消息编号（来自IotDeviceMessage.id）';


--
-- Name: COLUMN device_service_invoke_response.device_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_service_invoke_response.device_id IS '设备编号';


--
-- Name: COLUMN device_service_invoke_response.device_identification; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_service_invoke_response.device_identification IS '设备标识';


--
-- Name: COLUMN device_service_invoke_response.product_identification; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_service_invoke_response.product_identification IS '产品标识';


--
-- Name: COLUMN device_service_invoke_response.service_identifier; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_service_invoke_response.service_identifier IS '服务标识（从topic中提取的identifier）';


--
-- Name: COLUMN device_service_invoke_response.request_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_service_invoke_response.request_id IS '请求编号（来自IotDeviceMessage.requestId）';


--
-- Name: COLUMN device_service_invoke_response.method; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_service_invoke_response.method IS '请求方法（来自IotDeviceMessage.method，通常是thing.service.invoke）';


--
-- Name: COLUMN device_service_invoke_response.response_data; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_service_invoke_response.response_data IS '响应数据（来自IotDeviceMessage.data，JSON格式）';


--
-- Name: COLUMN device_service_invoke_response.response_code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_service_invoke_response.response_code IS '响应错误码（来自IotDeviceMessage.code）';


--
-- Name: COLUMN device_service_invoke_response.response_msg; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_service_invoke_response.response_msg IS '响应消息（来自IotDeviceMessage.msg）';


--
-- Name: COLUMN device_service_invoke_response.topic; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_service_invoke_response.topic IS 'MQTT Topic';


--
-- Name: COLUMN device_service_invoke_response.report_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_service_invoke_response.report_time IS '上报时间（来自IotDeviceMessage.reportTime）';


--
-- Name: COLUMN device_service_invoke_response.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_service_invoke_response.tenant_id IS '租户编号';


--
-- Name: COLUMN device_service_invoke_response.create_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_service_invoke_response.create_time IS '创建时间';


--
-- Name: device_service_invoke_response_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.device_service_invoke_response_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: device_service_invoke_response_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.device_service_invoke_response_id_seq OWNED BY public.device_service_invoke_response.id;


--
-- Name: device_topic; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.device_topic (
    id bigint NOT NULL,
    device_identification character varying(100) NOT NULL,
    type character varying(255),
    topic character varying(100),
    publisher character varying(255),
    subscriber character varying(255),
    create_by character varying(64),
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    update_by character varying(64),
    update_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    remark character varying(500),
    tenant_id bigint DEFAULT 0 NOT NULL,
    deleted smallint DEFAULT 0 NOT NULL
);


--
-- Name: TABLE device_topic; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.device_topic IS '设备Topic数据表';


--
-- Name: COLUMN device_topic.id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_topic.id IS 'id';


--
-- Name: COLUMN device_topic.device_identification; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_topic.device_identification IS '设备标识';


--
-- Name: COLUMN device_topic.type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_topic.type IS '类型(0:基础Topic,1:自定义Topic)';


--
-- Name: COLUMN device_topic.topic; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_topic.topic IS 'topic';


--
-- Name: COLUMN device_topic.publisher; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_topic.publisher IS '发布者';


--
-- Name: COLUMN device_topic.subscriber; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_topic.subscriber IS '订阅者';


--
-- Name: COLUMN device_topic.create_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_topic.create_by IS '创建者';


--
-- Name: COLUMN device_topic.create_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_topic.create_time IS '创建时间';


--
-- Name: COLUMN device_topic.update_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_topic.update_by IS '更新者';


--
-- Name: COLUMN device_topic.update_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_topic.update_time IS '更新时间';


--
-- Name: COLUMN device_topic.remark; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_topic.remark IS '备注';


--
-- Name: COLUMN device_topic.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_topic.tenant_id IS '租户编号';


--
-- Name: COLUMN device_topic.deleted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_topic.deleted IS '是否删除';


--
-- Name: device_topic_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.device_topic_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: device_topic_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.device_topic_id_seq OWNED BY public.device_topic.id;


--
-- Name: dm_ota_version_lang_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dm_ota_version_lang_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


--
-- Name: experiment_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.experiment_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: experiment_image_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.experiment_image_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: experiment_resources_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.experiment_resources_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: experiment_run_record_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.experiment_run_record_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: experiment_share_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.experiment_share_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: experiment_share_parameters_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.experiment_share_parameters_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: experiment_tag_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.experiment_tag_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: experiment_user_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.experiment_user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: file_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.file_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: iot_app_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.iot_app_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: iot_app_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.iot_app_id_seq OWNED BY public.app.id;


--
-- Name: model_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.model_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: model_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.model_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: model_server_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.model_server_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: model_server_quantify_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.model_server_quantify_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: model_server_quantify_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.model_server_quantify_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: model_server_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.model_server_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: model_server_test_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.model_server_test_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: model_server_test_image_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.model_server_test_image_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: model_server_test_image_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.model_server_test_image_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: model_server_test_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.model_server_test_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: model_server_test_video_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.model_server_test_video_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: model_server_test_video_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.model_server_test_video_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: model_server_video_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.model_server_video_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: model_server_video_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.model_server_video_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: model_type_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.model_type_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: model_type_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.model_type_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: ota_packages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ota_packages (
    id bigint NOT NULL,
    app_id character varying(64) NOT NULL,
    package_name character varying(100) NOT NULL,
    package_type smallint NOT NULL,
    product_identification character varying(100) NOT NULL,
    version character varying(255) NOT NULL,
    file_location character varying(255) NOT NULL,
    status smallint NOT NULL,
    description character varying(255),
    custom_info text,
    remark character varying(255),
    created_by bigint,
    created_time timestamp(6) without time zone NOT NULL,
    updated_by bigint,
    updated_time timestamp(6) without time zone NOT NULL,
    tenant_id bigint,
    deleted smallint DEFAULT 0 NOT NULL
);


--
-- Name: TABLE ota_packages; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.ota_packages IS 'OTA升级包表';


--
-- Name: COLUMN ota_packages.id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.ota_packages.id IS '主键';


--
-- Name: COLUMN ota_packages.app_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.ota_packages.app_id IS '应用ID';


--
-- Name: COLUMN ota_packages.package_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.ota_packages.package_name IS '包名称';


--
-- Name: COLUMN ota_packages.package_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.ota_packages.package_type IS '升级包类型(0:软件包、1:固件包)';


--
-- Name: COLUMN ota_packages.product_identification; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.ota_packages.product_identification IS '产品标识';


--
-- Name: COLUMN ota_packages.version; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.ota_packages.version IS '升级包版本号';


--
-- Name: COLUMN ota_packages.file_location; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.ota_packages.file_location IS '升级包的位置';


--
-- Name: COLUMN ota_packages.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.ota_packages.status IS '状态';


--
-- Name: COLUMN ota_packages.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.ota_packages.description IS '升级包功能描述';


--
-- Name: COLUMN ota_packages.custom_info; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.ota_packages.custom_info IS '自定义信息';


--
-- Name: COLUMN ota_packages.remark; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.ota_packages.remark IS '描述';


--
-- Name: COLUMN ota_packages.created_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.ota_packages.created_by IS '创建人';


--
-- Name: COLUMN ota_packages.created_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.ota_packages.created_time IS '创建时间';


--
-- Name: COLUMN ota_packages.updated_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.ota_packages.updated_by IS '更新人';


--
-- Name: COLUMN ota_packages.updated_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.ota_packages.updated_time IS '更新时间';


--
-- Name: COLUMN ota_packages.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.ota_packages.tenant_id IS '租户ID';


--
-- Name: COLUMN ota_packages.deleted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.ota_packages.deleted IS '是否删除';


--
-- Name: product; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.product (
    id bigint NOT NULL,
    app_id character varying(64) NOT NULL,
    template_identification character varying(100),
    product_name character varying(255) NOT NULL,
    product_identification character varying(100) NOT NULL,
    product_type character varying(255) NOT NULL,
    manufacturer_id character varying(255) NOT NULL,
    manufacturer_name character varying(255) NOT NULL,
    model character varying(255) NOT NULL,
    data_format character varying(255) NOT NULL,
    device_type character varying(255) NOT NULL,
    protocol_type character varying(255) NOT NULL,
    status character varying(10) NOT NULL,
    remark character varying(255),
    create_by character varying(64),
    create_time timestamp(6) without time zone DEFAULT CURRENT_TIMESTAMP,
    update_by character varying(64),
    update_time timestamp(6) without time zone,
    auth_mode character varying(255),
    user_name character varying(255),
    password character varying(255),
    connector character varying(255),
    sign_key character varying(255),
    encrypt_method integer DEFAULT 0,
    encrypt_key character varying(255),
    encrypt_vector character varying(255),
    tenant_id bigint DEFAULT 0 NOT NULL
);


--
-- Name: TABLE product; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.product IS '产品模型';


--
-- Name: COLUMN product.id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product.id IS 'id';


--
-- Name: COLUMN product.app_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product.app_id IS '应用ID';


--
-- Name: COLUMN product.template_identification; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product.template_identification IS '产品模版标识';


--
-- Name: COLUMN product.product_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product.product_name IS '产品名称:自定义，支持中文、英文大小写、数字、下划线和中划线';


--
-- Name: COLUMN product.product_identification; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product.product_identification IS '产品标识';


--
-- Name: COLUMN product.product_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product.product_type IS '支持以下两种产品类型
•COMMON：普通产品，需直连设备。
•GATEWAY：网关产品，可挂载子设备。
•SUBSET：子设备。
•VIDEO_COMMON：视频设备。';


--
-- Name: COLUMN product.manufacturer_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product.manufacturer_id IS '厂商ID:支持英文大小写，数字，下划线和中划线';


--
-- Name: COLUMN product.manufacturer_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product.manufacturer_name IS '厂商名称 :支持中文、英文大小写、数字、下划线和中划线';


--
-- Name: COLUMN product.model; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product.model IS '产品型号，建议包含字母或数字来保证可扩展性。支持英文大小写、数字、下划线和中划线
';


--
-- Name: COLUMN product.data_format; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product.data_format IS '数据格式，默认为JSON无需修改。';


--
-- Name: COLUMN product.device_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product.device_type IS '设备类型:支持英文大小写、数字、下划线和中划线,
';


--
-- Name: COLUMN product.protocol_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product.protocol_type IS '设备接入平台的协议类型，默认为MQTT无需修改。
 ';


--
-- Name: COLUMN product.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product.status IS '状态(字典值：0启用  1停用)';


--
-- Name: COLUMN product.remark; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product.remark IS '产品描述';


--
-- Name: COLUMN product.create_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product.create_by IS '创建者';


--
-- Name: COLUMN product.create_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product.create_time IS '创建时间';


--
-- Name: COLUMN product.update_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product.update_by IS '更新者';


--
-- Name: COLUMN product.update_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product.update_time IS '更新时间';


--
-- Name: COLUMN product.auth_mode; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product.auth_mode IS '认证方式';


--
-- Name: COLUMN product.user_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product.user_name IS '用户名';


--
-- Name: COLUMN product.password; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product.password IS '密码';


--
-- Name: COLUMN product.connector; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product.connector IS '连接实例';


--
-- Name: COLUMN product.sign_key; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product.sign_key IS '签名密钥';


--
-- Name: COLUMN product.encrypt_method; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product.encrypt_method IS '协议加密方式 0：不加密 1：SM4加密 2：AES加密';


--
-- Name: COLUMN product.encrypt_key; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product.encrypt_key IS '加密密钥';


--
-- Name: COLUMN product.encrypt_vector; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product.encrypt_vector IS '加密向量';


--
-- Name: COLUMN product.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product.tenant_id IS '租户编号';


--
-- Name: product_commands; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.product_commands (
    id bigint NOT NULL,
    service_id bigint NOT NULL,
    name character varying(255) NOT NULL,
    description character varying(255),
    create_by character varying(64),
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    update_by character varying(64),
    update_time timestamp without time zone,
    command_code character varying(255),
    remark character varying(255),
    tenant_id bigint DEFAULT 0 NOT NULL
);


--
-- Name: TABLE product_commands; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.product_commands IS '产品模型设备服务命令表';


--
-- Name: COLUMN product_commands.id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands.id IS '命令id';


--
-- Name: COLUMN product_commands.service_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands.service_id IS '服务ID';


--
-- Name: COLUMN product_commands.name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands.name IS '指示命令的名字，如门磁的LOCK命令、摄像头的VIDEO_RECORD命令，命令名与参数共同构成一个完整的命令。支持英文大小写、数字及下划线，长度[2,50]。';


--
-- Name: COLUMN product_commands.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands.description IS '命令描述';


--
-- Name: COLUMN product_commands.create_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands.create_by IS '创建者';


--
-- Name: COLUMN product_commands.create_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands.create_time IS '创建时间';


--
-- Name: COLUMN product_commands.update_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands.update_by IS '更新者';


--
-- Name: COLUMN product_commands.update_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands.update_time IS '更新时间';


--
-- Name: COLUMN product_commands.command_code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands.command_code IS '命令标识';


--
-- Name: COLUMN product_commands.remark; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands.remark IS '备注';


--
-- Name: COLUMN product_commands.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands.tenant_id IS '租户编号';


--
-- Name: product_commands_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.product_commands_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: product_commands_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_commands_id_seq OWNED BY public.product_commands.id;


--
-- Name: product_commands_requests; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.product_commands_requests (
    id bigint NOT NULL,
    service_id bigint NOT NULL,
    commands_id bigint NOT NULL,
    datatype character varying(255) NOT NULL,
    enumlist character varying(255),
    max character varying(255),
    maxlength character varying(255),
    min character varying(255),
    parameter_description character varying(255),
    parameter_name character varying(255),
    required character varying(255) DEFAULT '0'::character varying,
    step character varying(255),
    unit character varying(255),
    create_by character varying(64),
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    update_by character varying(64),
    update_time timestamp without time zone,
    parameter_code character varying(255),
    tenant_id bigint DEFAULT 0 NOT NULL
);


--
-- Name: TABLE product_commands_requests; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.product_commands_requests IS '产品模型设备下发服务命令属性表';


--
-- Name: COLUMN product_commands_requests.id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands_requests.id IS 'id';


--
-- Name: COLUMN product_commands_requests.service_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands_requests.service_id IS '服务ID';


--
-- Name: COLUMN product_commands_requests.commands_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands_requests.commands_id IS '命令ID';


--
-- Name: COLUMN product_commands_requests.datatype; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands_requests.datatype IS '指示数据类型。取值范围：string、int、decimal';


--
-- Name: COLUMN product_commands_requests.enumlist; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands_requests.enumlist IS '指示枚举值。如开关状态status可有如下取值"enumList" : ["OPEN","CLOSE"]目前本字段是非功能性字段，仅起到描述作用。建议准确定义。';


--
-- Name: COLUMN product_commands_requests.max; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands_requests.max IS '指示最大值。仅当dataType为int、decimal时生效，逻辑小于等于。';


--
-- Name: COLUMN product_commands_requests.maxlength; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands_requests.maxlength IS '指示字符串长度。仅当dataType为string时生效。';


--
-- Name: COLUMN product_commands_requests.min; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands_requests.min IS '指示最小值。仅当dataType为int、decimal时生效，逻辑大于等于。';


--
-- Name: COLUMN product_commands_requests.parameter_description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands_requests.parameter_description IS '命令中参数的描述，不影响实际功能，可配置为空字符串""。';


--
-- Name: COLUMN product_commands_requests.parameter_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands_requests.parameter_name IS '命令中参数的名字。';


--
-- Name: COLUMN product_commands_requests.required; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands_requests.required IS '指示本条属性是否必填，取值为0或1，默认取值1（必填）。目前本字段是非功能性字段，仅起到描述作用。';


--
-- Name: COLUMN product_commands_requests.step; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands_requests.step IS '指示步长。';


--
-- Name: COLUMN product_commands_requests.unit; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands_requests.unit IS '指示单位。取值根据参数确定，如：•温度单位："C"或"K"•百分比单位："%"•压强单位："Pa"或"kPa"';


--
-- Name: COLUMN product_commands_requests.create_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands_requests.create_by IS '创建者';


--
-- Name: COLUMN product_commands_requests.create_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands_requests.create_time IS '创建时间';


--
-- Name: COLUMN product_commands_requests.update_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands_requests.update_by IS '更新者';


--
-- Name: COLUMN product_commands_requests.update_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands_requests.update_time IS '更新时间';


--
-- Name: COLUMN product_commands_requests.parameter_code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands_requests.parameter_code IS '请求参数编码';


--
-- Name: COLUMN product_commands_requests.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands_requests.tenant_id IS '租户编号';


--
-- Name: product_commands_requests_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.product_commands_requests_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: product_commands_requests_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_commands_requests_id_seq OWNED BY public.product_commands_requests.id;


--
-- Name: product_commands_response; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.product_commands_response (
    id bigint NOT NULL,
    commands_id bigint NOT NULL,
    service_id bigint,
    datatype character varying(255) NOT NULL,
    enumlist character varying(255),
    max character varying(255),
    maxlength character varying(255),
    min character varying(255),
    parameter_description character varying(255),
    parameter_name character varying(255),
    required character varying(255) DEFAULT '0'::character varying,
    step character varying(255),
    unit character varying(255),
    create_by character varying(64),
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    update_by character varying(64),
    update_time timestamp without time zone,
    parameter_code character varying(255),
    tenant_id bigint DEFAULT 0 NOT NULL
);


--
-- Name: TABLE product_commands_response; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.product_commands_response IS '产品模型设备响应服务命令属性表';


--
-- Name: COLUMN product_commands_response.id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands_response.id IS 'id';


--
-- Name: COLUMN product_commands_response.commands_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands_response.commands_id IS '命令ID';


--
-- Name: COLUMN product_commands_response.service_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands_response.service_id IS '服务ID';


--
-- Name: COLUMN product_commands_response.datatype; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands_response.datatype IS '指示数据类型。取值范围：string、int、decimal';


--
-- Name: COLUMN product_commands_response.enumlist; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands_response.enumlist IS '指示枚举值。如开关状态status可有如下取值"enumList" : ["OPEN","CLOSE"]目前本字段是非功能性字段，仅起到描述作用。建议准确定义。';


--
-- Name: COLUMN product_commands_response.max; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands_response.max IS '指示最大值。仅当dataType为int、decimal时生效，逻辑小于等于。';


--
-- Name: COLUMN product_commands_response.maxlength; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands_response.maxlength IS '指示字符串长度。仅当dataType为string时生效。';


--
-- Name: COLUMN product_commands_response.min; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands_response.min IS '指示最小值。仅当dataType为int、decimal时生效，逻辑大于等于。';


--
-- Name: COLUMN product_commands_response.parameter_description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands_response.parameter_description IS '命令中参数的描述，不影响实际功能，可配置为空字符串""。';


--
-- Name: COLUMN product_commands_response.parameter_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands_response.parameter_name IS '命令中参数的名字。';


--
-- Name: COLUMN product_commands_response.required; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands_response.required IS '指示本条属性是否必填，取值为0或1，默认取值1（必填）。目前本字段是非功能性字段，仅起到描述作用。';


--
-- Name: COLUMN product_commands_response.step; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands_response.step IS '指示步长。';


--
-- Name: COLUMN product_commands_response.unit; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands_response.unit IS '指示单位。取值根据参数确定，如：•温度单位："C"或"K"•百分比单位："%"•压强单位："Pa"或"kPa"';


--
-- Name: COLUMN product_commands_response.create_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands_response.create_by IS '创建者';


--
-- Name: COLUMN product_commands_response.create_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands_response.create_time IS '创建时间';


--
-- Name: COLUMN product_commands_response.update_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands_response.update_by IS '更新者';


--
-- Name: COLUMN product_commands_response.update_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands_response.update_time IS '更新时间';


--
-- Name: COLUMN product_commands_response.parameter_code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands_response.parameter_code IS '响应参数编码';


--
-- Name: COLUMN product_commands_response.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_commands_response.tenant_id IS '租户编号';


--
-- Name: product_commands_response_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.product_commands_response_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: product_commands_response_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_commands_response_id_seq OWNED BY public.product_commands_response.id;


--
-- Name: product_event; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.product_event (
    id bigint NOT NULL,
    event_name character varying(255) NOT NULL,
    event_code character varying(255) NOT NULL,
    event_type character varying(255) NOT NULL,
    template_identification character varying(255),
    product_identification character varying(255),
    status character varying(10) DEFAULT '0'::character varying,
    description character varying(255),
    create_by character varying(64),
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    update_by character varying(64),
    update_time timestamp without time zone,
    tenant_id bigint DEFAULT 0 NOT NULL
);


--
-- Name: TABLE product_event; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.product_event IS '产品事件表';


--
-- Name: COLUMN product_event.id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_event.id IS '主键';


--
-- Name: COLUMN product_event.event_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_event.event_name IS '事件名称';


--
-- Name: COLUMN product_event.event_code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_event.event_code IS '事件标识';


--
-- Name: COLUMN product_event.event_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_event.event_type IS '事件类型。INFO_EVENT_TYPE：信息。ALERT_EVENT_TYPE：告警。ERROR_EVENT_TYPE：故障';


--
-- Name: COLUMN product_event.template_identification; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_event.template_identification IS '产品模版标识';


--
-- Name: COLUMN product_event.product_identification; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_event.product_identification IS '产品标识';


--
-- Name: COLUMN product_event.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_event.status IS '状态(字典值：0启用  1停用)';


--
-- Name: COLUMN product_event.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_event.description IS '描述';


--
-- Name: COLUMN product_event.create_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_event.create_by IS '创建者';


--
-- Name: COLUMN product_event.create_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_event.create_time IS '创建时间';


--
-- Name: COLUMN product_event.update_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_event.update_by IS '更新者';


--
-- Name: COLUMN product_event.update_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_event.update_time IS '更新时间';


--
-- Name: COLUMN product_event.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_event.tenant_id IS '租户编号';


--
-- Name: product_event_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.product_event_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: product_event_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_event_id_seq OWNED BY public.product_event.id;


--
-- Name: product_event_response; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.product_event_response (
    id bigint NOT NULL,
    event_id bigint NOT NULL,
    service_id bigint,
    datatype character varying(255) NOT NULL,
    enumlist character varying(255),
    max character varying(255),
    maxlength character varying(255),
    min character varying(255),
    parameter_description character varying(255),
    parameter_name character varying(255),
    required character varying(255) NOT NULL,
    step character varying(255),
    unit character varying(255),
    create_by character varying(64),
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    update_by character varying(64),
    update_time timestamp without time zone,
    tenant_id bigint DEFAULT 0 NOT NULL
);


--
-- Name: TABLE product_event_response; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.product_event_response IS '产品模型设备响应服务命令属性表（事件响应）';


--
-- Name: COLUMN product_event_response.id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_event_response.id IS 'id';


--
-- Name: COLUMN product_event_response.event_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_event_response.event_id IS '事件id';


--
-- Name: COLUMN product_event_response.service_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_event_response.service_id IS '服务ID';


--
-- Name: COLUMN product_event_response.datatype; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_event_response.datatype IS '指示数据类型。取值范围：string、int、decimal';


--
-- Name: COLUMN product_event_response.enumlist; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_event_response.enumlist IS '指示枚举值。如开关状态status可有如下取值"enumList" : ["OPEN","CLOSE"]目前本字段是非功能性字段，仅起到描述作用。建议准确定义。';


--
-- Name: COLUMN product_event_response.max; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_event_response.max IS '指示最大值。仅当dataType为int、decimal时生效，逻辑小于等于。';


--
-- Name: COLUMN product_event_response.maxlength; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_event_response.maxlength IS '指示字符串长度。仅当dataType为string时生效。';


--
-- Name: COLUMN product_event_response.min; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_event_response.min IS '指示最小值。仅当dataType为int、decimal时生效，逻辑大于等于。';


--
-- Name: COLUMN product_event_response.parameter_description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_event_response.parameter_description IS '命令中参数的描述，不影响实际功能，可配置为空字符串""。';


--
-- Name: COLUMN product_event_response.parameter_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_event_response.parameter_name IS '命令中参数的名字。';


--
-- Name: COLUMN product_event_response.required; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_event_response.required IS '指示本条属性是否必填，取值为0或1，默认取值1（必填）。目前本字段是非功能性字段，仅起到描述作用。';


--
-- Name: COLUMN product_event_response.step; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_event_response.step IS '指示步长。';


--
-- Name: COLUMN product_event_response.unit; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_event_response.unit IS '指示单位。取值根据参数确定，如：•温度单位："C"或"K"•百分比单位："%"•压强单位："Pa"或"kPa"';


--
-- Name: COLUMN product_event_response.create_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_event_response.create_by IS '创建者';


--
-- Name: COLUMN product_event_response.create_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_event_response.create_time IS '创建时间';


--
-- Name: COLUMN product_event_response.update_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_event_response.update_by IS '更新者';


--
-- Name: COLUMN product_event_response.update_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_event_response.update_time IS '更新时间';


--
-- Name: COLUMN product_event_response.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_event_response.tenant_id IS '租户编号';


--
-- Name: product_event_response_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.product_event_response_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: product_event_response_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_event_response_id_seq OWNED BY public.product_event_response.id;


--
-- Name: product_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.product_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: product_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_id_seq OWNED BY public.product.id;


--
-- Name: product_properties; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.product_properties (
    id bigint NOT NULL,
    property_name character varying(255) NOT NULL,
    property_code character varying(255) NOT NULL,
    datatype character varying(255) NOT NULL,
    description character varying(255),
    enumlist character varying(255),
    max character varying(255),
    maxlength bigint,
    method character varying(255),
    min character varying(255),
    required integer,
    step integer,
    unit character varying(255),
    create_by character varying(64),
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    update_by character varying(64),
    update_time timestamp without time zone,
    template_identification character varying(100),
    product_identification character varying(100),
    tenant_id bigint DEFAULT 0 NOT NULL
);


--
-- Name: TABLE product_properties; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.product_properties IS '产品模型服务属性表';


--
-- Name: COLUMN product_properties.id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_properties.id IS '属性id';


--
-- Name: COLUMN product_properties.property_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_properties.property_name IS '功能名称。';


--
-- Name: COLUMN product_properties.property_code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_properties.property_code IS '标识符';


--
-- Name: COLUMN product_properties.datatype; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_properties.datatype IS '指示数据类型：取值范围：string、int、decimal（float和double都可以使用此类型）、DateTime、jsonObject上报数据时，复杂类型数据格式如下：
•DateTime:yyyyMMdd’T’HHmmss’Z’如:20151212T121212Z•jsonObject：自定义json结构体，平台不理解只透传
';


--
-- Name: COLUMN product_properties.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_properties.description IS '属性描述，不影响实际功能，可配置为空字符串""。';


--
-- Name: COLUMN product_properties.enumlist; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_properties.enumlist IS '指示枚举值:如开关状态status可有如下取值"enumList" : ["OPEN","CLOSE"]目前本字段是非功能性字段，仅起到描述作用。建议准确定义。
';


--
-- Name: COLUMN product_properties.max; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_properties.max IS '指示最大值。支持长度不超过50的数字。仅当dataType为int、decimal时生效，逻辑小于等于。
';


--
-- Name: COLUMN product_properties.maxlength; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_properties.maxlength IS '指示字符串长度。仅当dataType为string、DateTime时生效。';


--
-- Name: COLUMN product_properties.method; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_properties.method IS '指示访问模式。R:可读；W:可写；E属性值更改时上报数据取值范围：R、RW、RE、RWE';


--
-- Name: COLUMN product_properties.min; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_properties.min IS '指示最小值。支持长度不超过50的数字。仅当dataType为int、decimal时生效，逻辑大于等于。
';


--
-- Name: COLUMN product_properties.required; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_properties.required IS '指示本条属性是否必填，取值为0或1，默认取值1（必填）。目前本字段是非功能性字段，仅起到描述作用。(字典值link_product_isRequired：0非必填 1必填)
';


--
-- Name: COLUMN product_properties.step; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_properties.step IS '指示步长。';


--
-- Name: COLUMN product_properties.unit; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_properties.unit IS '指示单位。支持长度不超过50。
取值根据参数确定，如：
•温度单位：“C”或“K”
•百分比单位：“%”
•压强单位：“Pa”或“kPa”
';


--
-- Name: COLUMN product_properties.create_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_properties.create_by IS '创建者';


--
-- Name: COLUMN product_properties.create_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_properties.create_time IS '创建时间';


--
-- Name: COLUMN product_properties.update_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_properties.update_by IS '更新者';


--
-- Name: COLUMN product_properties.update_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_properties.update_time IS '更新时间';


--
-- Name: COLUMN product_properties.template_identification; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_properties.template_identification IS '产品模版标识 new';


--
-- Name: COLUMN product_properties.product_identification; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_properties.product_identification IS '产品标识 new';


--
-- Name: COLUMN product_properties.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_properties.tenant_id IS '租户编号';


--
-- Name: product_properties_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.product_properties_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: product_properties_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_properties_id_seq OWNED BY public.product_properties.id;


--
-- Name: product_script; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.product_script (
    id bigint NOT NULL,
    product_id bigint NOT NULL,
    product_identification character varying(100) NOT NULL,
    script_enabled boolean DEFAULT false NOT NULL,
    script_content text,
    script_version integer DEFAULT 1 NOT NULL,
    create_by character varying(64),
    create_time timestamp(6) without time zone DEFAULT CURRENT_TIMESTAMP,
    update_by character varying(64),
    update_time timestamp(6) without time zone,
    tenant_id bigint DEFAULT 0 NOT NULL
);


--
-- Name: TABLE product_script; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.product_script IS '产品脚本表，用于存储产品的数据转换脚本';


--
-- Name: COLUMN product_script.id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_script.id IS '主键ID';


--
-- Name: COLUMN product_script.product_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_script.product_id IS '产品ID，关联product表';


--
-- Name: COLUMN product_script.product_identification; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_script.product_identification IS '产品标识，冗余字段，便于查询';


--
-- Name: COLUMN product_script.script_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_script.script_enabled IS '是否启用脚本，默认不启用';


--
-- Name: COLUMN product_script.script_content; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_script.script_content IS '脚本内容，包含rawDataToProtocol和protocolToRawData两个函数';


--
-- Name: COLUMN product_script.script_version; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_script.script_version IS '脚本版本号，用于版本控制';


--
-- Name: COLUMN product_script.create_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_script.create_by IS '创建者';


--
-- Name: COLUMN product_script.create_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_script.create_time IS '创建时间';


--
-- Name: COLUMN product_script.update_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_script.update_by IS '更新者';


--
-- Name: COLUMN product_script.update_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_script.update_time IS '更新时间';


--
-- Name: COLUMN product_script.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_script.tenant_id IS '租户编号';


--
-- Name: product_script_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.product_script_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: product_script_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_script_id_seq OWNED BY public.product_script.id;


--
-- Name: product_services; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.product_services (
    id bigint NOT NULL,
    service_code character varying(255) NOT NULL,
    service_name character varying(255) NOT NULL,
    template_identification character varying(100),
    product_identification character varying(100),
    status character varying(10) DEFAULT '0'::character varying,
    description character varying(255),
    create_by character varying(64),
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    update_by character varying(64),
    update_time timestamp without time zone,
    tenant_id bigint DEFAULT 0 NOT NULL
);


--
-- Name: TABLE product_services; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.product_services IS '产品模型服务表';


--
-- Name: COLUMN product_services.id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_services.id IS '服务id';


--
-- Name: COLUMN product_services.service_code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_services.service_code IS '服务编码:支持英文大小写、数字、下划线和中划线';


--
-- Name: COLUMN product_services.service_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_services.service_name IS '服务名称';


--
-- Name: COLUMN product_services.template_identification; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_services.template_identification IS '产品模版标识';


--
-- Name: COLUMN product_services.product_identification; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_services.product_identification IS '产品标识';


--
-- Name: COLUMN product_services.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_services.status IS '状态(字典值：0启用  1停用)';


--
-- Name: COLUMN product_services.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_services.description IS '服务的描述信息:文本描述，不影响实际功能，可配置为空字符串""。';


--
-- Name: COLUMN product_services.create_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_services.create_by IS '创建者';


--
-- Name: COLUMN product_services.create_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_services.create_time IS '创建时间';


--
-- Name: COLUMN product_services.update_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_services.update_by IS '更新者';


--
-- Name: COLUMN product_services.update_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_services.update_time IS '更新时间';


--
-- Name: COLUMN product_services.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_services.tenant_id IS '租户编号';


--
-- Name: product_services_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.product_services_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: product_services_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_services_id_seq OWNED BY public.product_services.id;


--
-- Name: product_template; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.product_template (
    id bigint NOT NULL,
    app_id character varying(64) NOT NULL,
    template_identification character varying(100) NOT NULL,
    template_name character varying(255) NOT NULL,
    status character varying(10) NOT NULL,
    remark character varying(255),
    create_by character varying(64),
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    update_by character varying(64),
    update_time timestamp without time zone,
    tenant_id bigint DEFAULT 0 NOT NULL
);


--
-- Name: COLUMN product_template.id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_template.id IS 'id';


--
-- Name: COLUMN product_template.app_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_template.app_id IS '应用ID';


--
-- Name: COLUMN product_template.template_identification; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_template.template_identification IS '产品模版标识';


--
-- Name: COLUMN product_template.template_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_template.template_name IS '产品模板名称:自定义，支持中文、英文大小写、数字、下划线和中划线';


--
-- Name: COLUMN product_template.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_template.status IS '状态(字典值：启用  停用)';


--
-- Name: COLUMN product_template.remark; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_template.remark IS '产品模型模板描述';


--
-- Name: COLUMN product_template.create_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_template.create_by IS '创建者';


--
-- Name: COLUMN product_template.create_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_template.create_time IS '创建时间';


--
-- Name: COLUMN product_template.update_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_template.update_by IS '更新者';


--
-- Name: COLUMN product_template.update_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_template.update_time IS '更新时间';


--
-- Name: COLUMN product_template.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.product_template.tenant_id IS '租户编号';


--
-- Name: product_template_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.product_template_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: product_template_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_template_id_seq OWNED BY public.product_template.id;


--
-- Name: project_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.project_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sys_job_log__seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sys_job_log__seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: warehouse_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.warehouse_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: warehouse; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.warehouse (
    id bigint DEFAULT nextval('public.warehouse_seq'::regclass) NOT NULL,
    name character varying(200) NOT NULL,
    cover_path character varying(200),
    description character varying(200),
    create_by character varying(255),
    create_time timestamp(6) without time zone,
    tenant_id bigint DEFAULT 0 NOT NULL,
    update_by character varying(255),
    update_time timestamp(6) without time zone,
    deleted smallint DEFAULT 0 NOT NULL
);


--
-- Name: TABLE warehouse; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.warehouse IS '数据仓表';


--
-- Name: COLUMN warehouse.id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.warehouse.id IS '主键ID';


--
-- Name: COLUMN warehouse.name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.warehouse.name IS '仓库名称';


--
-- Name: COLUMN warehouse.cover_path; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.warehouse.cover_path IS '封面地址';


--
-- Name: COLUMN warehouse.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.warehouse.description IS '描述';


--
-- Name: COLUMN warehouse.create_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.warehouse.create_by IS '创建人';


--
-- Name: COLUMN warehouse.create_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.warehouse.create_time IS '创建时间';


--
-- Name: COLUMN warehouse.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.warehouse.tenant_id IS '租户编号';


--
-- Name: COLUMN warehouse.update_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.warehouse.update_by IS '创建人';


--
-- Name: COLUMN warehouse.update_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.warehouse.update_time IS '创建时间';


--
-- Name: COLUMN warehouse.deleted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.warehouse.deleted IS '是否删除';


--
-- Name: warehouse_dataset_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.warehouse_dataset_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: warehouse_dataset; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.warehouse_dataset (
    id bigint DEFAULT nextval('public.warehouse_dataset_seq'::regclass) NOT NULL,
    dataset_id bigint NOT NULL,
    warehouse_id bigint NOT NULL,
    plan_sync_count integer DEFAULT 0 NOT NULL,
    sync_count integer DEFAULT 0 NOT NULL,
    sync_status smallint DEFAULT 0 NOT NULL,
    fail_count integer DEFAULT 0 NOT NULL,
    create_by character varying(255),
    create_time timestamp(6) without time zone,
    tenant_id bigint DEFAULT 0 NOT NULL,
    update_by character varying(255),
    update_time timestamp(6) without time zone,
    deleted smallint DEFAULT 0 NOT NULL
);


--
-- Name: TABLE warehouse_dataset; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.warehouse_dataset IS '数据仓数据集关联表';


--
-- Name: COLUMN warehouse_dataset.id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.warehouse_dataset.id IS '主键ID';


--
-- Name: COLUMN warehouse_dataset.dataset_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.warehouse_dataset.dataset_id IS '数据集ID';


--
-- Name: COLUMN warehouse_dataset.warehouse_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.warehouse_dataset.warehouse_id IS '数据仓ID';


--
-- Name: COLUMN warehouse_dataset.plan_sync_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.warehouse_dataset.plan_sync_count IS '计划同步数量';


--
-- Name: COLUMN warehouse_dataset.sync_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.warehouse_dataset.sync_count IS '已同步数量';


--
-- Name: COLUMN warehouse_dataset.sync_status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.warehouse_dataset.sync_status IS '同步状态[0:未同步,1:同步中,2:同步完成]';


--
-- Name: COLUMN warehouse_dataset.fail_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.warehouse_dataset.fail_count IS '同步失败数量';


--
-- Name: COLUMN warehouse_dataset.create_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.warehouse_dataset.create_by IS '创建人';


--
-- Name: COLUMN warehouse_dataset.create_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.warehouse_dataset.create_time IS '创建时间';


--
-- Name: COLUMN warehouse_dataset.tenant_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.warehouse_dataset.tenant_id IS '租户编号';


--
-- Name: COLUMN warehouse_dataset.update_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.warehouse_dataset.update_by IS '创建人';


--
-- Name: COLUMN warehouse_dataset.update_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.warehouse_dataset.update_time IS '创建时间';


--
-- Name: COLUMN warehouse_dataset.deleted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.warehouse_dataset.deleted IS '是否删除';


--
-- Name: warehouse_dataset_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.warehouse_dataset_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: warehouse_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.warehouse_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: app id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app ALTER COLUMN id SET DEFAULT nextval('public.iot_app_id_seq'::regclass);


--
-- Name: dataset id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dataset ALTER COLUMN id SET DEFAULT nextval('public.dataset_id_seq'::regclass);


--
-- Name: dataset_frame_task id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dataset_frame_task ALTER COLUMN id SET DEFAULT nextval('public.dataset_frame_task_id_seq'::regclass);


--
-- Name: dataset_image id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dataset_image ALTER COLUMN id SET DEFAULT nextval('public.dataset_image_id_seq'::regclass);


--
-- Name: dataset_tag id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dataset_tag ALTER COLUMN id SET DEFAULT nextval('public.dataset_tag_id_seq'::regclass);


--
-- Name: dataset_task id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dataset_task ALTER COLUMN id SET DEFAULT nextval('public.dataset_task_id_seq'::regclass);


--
-- Name: dataset_task_result id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dataset_task_result ALTER COLUMN id SET DEFAULT nextval('public.dataset_task_result_id_seq'::regclass);


--
-- Name: dataset_task_user id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dataset_task_user ALTER COLUMN id SET DEFAULT nextval('public.dataset_task_user_id_seq'::regclass);


--
-- Name: dataset_video id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dataset_video ALTER COLUMN id SET DEFAULT nextval('public.dataset_video_id_seq'::regclass);


--
-- Name: device id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.device ALTER COLUMN id SET DEFAULT nextval('public.device_id_seq'::regclass);


--
-- Name: device_event id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.device_event ALTER COLUMN id SET DEFAULT nextval('public.device_event_id_seq'::regclass);


--
-- Name: device_location id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.device_location ALTER COLUMN id SET DEFAULT nextval('public.device_location_id_seq'::regclass);


--
-- Name: device_ota_pkg id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.device_ota_pkg ALTER COLUMN id SET DEFAULT nextval('public.device_ota_pkg_id_seq'::regclass);


--
-- Name: device_service_invoke_response id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.device_service_invoke_response ALTER COLUMN id SET DEFAULT nextval('public.device_service_invoke_response_id_seq'::regclass);


--
-- Name: device_topic id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.device_topic ALTER COLUMN id SET DEFAULT nextval('public.device_topic_id_seq'::regclass);


--
-- Name: product id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product ALTER COLUMN id SET DEFAULT nextval('public.product_id_seq'::regclass);


--
-- Name: product_commands id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_commands ALTER COLUMN id SET DEFAULT nextval('public.product_commands_id_seq'::regclass);


--
-- Name: product_commands_requests id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_commands_requests ALTER COLUMN id SET DEFAULT nextval('public.product_commands_requests_id_seq'::regclass);


--
-- Name: product_commands_response id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_commands_response ALTER COLUMN id SET DEFAULT nextval('public.product_commands_response_id_seq'::regclass);


--
-- Name: product_event id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_event ALTER COLUMN id SET DEFAULT nextval('public.product_event_id_seq'::regclass);


--
-- Name: product_event_response id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_event_response ALTER COLUMN id SET DEFAULT nextval('public.product_event_response_id_seq'::regclass);


--
-- Name: product_properties id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_properties ALTER COLUMN id SET DEFAULT nextval('public.product_properties_id_seq'::regclass);


--
-- Name: product_script id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_script ALTER COLUMN id SET DEFAULT nextval('public.product_script_id_seq'::regclass);


--
-- Name: product_services id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_services ALTER COLUMN id SET DEFAULT nextval('public.product_services_id_seq'::regclass);


--
-- Name: product_template id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_template ALTER COLUMN id SET DEFAULT nextval('public.product_template_id_seq'::regclass);


--
-- Data for Name: app; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.app (id, app_id, app_key, app_secret, app_name, app_desc, status, permission_type, expire_time, tenant_id, remark, created_by, created_time, updated_by, updated_time, deleted) FROM stdin;
\.


--
-- Data for Name: dataset; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.dataset (id, dataset_code, name, cover_path, description, dataset_type, audit, reason, create_by, create_time, tenant_id, update_by, update_time, deleted, is_allocated, model_service_id, is_sync_minio, zip_url) FROM stdin;
3	2h2UCKt2	人	/api/v1/buckets/snap-space/objects/download?prefix=person.jpg	标注人的数据集	0	0	\N	admin	2025-06-18 20:43:11.303	0	1	2025-08-26 04:00:10.296677	0	0	\N	0	/api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip
\.


--
-- Data for Name: dataset_frame_task; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.dataset_frame_task (id, dataset_id, task_name, task_code, task_type, channel_id, device_id, rtmp_url, create_by, create_time, tenant_id, update_by, update_time, deleted) FROM stdin;
1	3	test	2GCLHKdgQvorGzHx	0			test	\N	2025-07-24 14:53:47.806	0	\N	2025-07-24 14:53:47.806	0
\.


--
-- Data for Name: dataset_image; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.dataset_image (id, dataset_id, name, path, modification_count, last_modified, width, heigh, size, annotations, dataset_video_id, create_by, create_time, tenant_id, update_by, update_time, deleted, completed, is_train, is_validation, is_test) FROM stdin;
79	3	frame_0.0.jpg	/api/v1/buckets/dataset/objects/download?prefix=3/94b8caae-9c90-43a2-a7bf-60cfe4dde487.jpg	4	2025-06-30 09:04:10.103	\N	\N	161485	[{"id":1751273910248,"type":"rectangle","label":0,"color":"#0ba27c","points":[{"x":0.15828220858895706,"y":0.16407634628493525},{"x":0.2907975460122699,"y":0.16407634628493525},{"x":0.2907975460122699,"y":0.5937968643490116},{"x":0.15828220858895706,"y":0.5937968643490116}]}]	\N	admin	2025-06-26 10:58:16.429	0	1	2025-08-26 04:00:01.615653	0	1	1	0	0
73	3	frame_3_1750584430504.jpg	/api/v1/buckets/dataset/objects/download?prefix=3/frame_3_1750584430504.jpg	2	2025-06-30 09:26:37.913	704	576	79931	[{"id":1751275597163,"type":"rectangle","label":0,"color":"#0ba27c","points":[{"x":0.2790050858232676,"y":0.49125874125874125},{"x":0.002940241576605218,"y":0.49125874125874125},{"x":0.002940241576605218,"y":0.9982517482517482},{"x":0.2790050858232676,"y":0.9982517482517482}]}]	\N	\N	2025-06-22 17:27:11.096	0	1	2025-08-26 04:00:01.628639	0	1	0	1	0
82	3	frame_3.0.jpg	/api/v1/buckets/dataset/objects/download?prefix=3/311c197e-2ff9-4787-a588-91d0e54b326f.jpg	28	2025-08-25 19:12:18.1	\N	\N	171381	[{"id":1751335823450,"type":"rectangle","label":0,"color":"#0ba27c","points":[{"x":0.11008522727272728,"y":0.12412587412587413},{"x":0.3077469405594406,"y":0.12412587412587413},{"x":0.3077469405594406,"y":0.7884615384615384},{"x":0.11008522727272728,"y":0.7884615384615384}]},{"id":1751335832319,"type":"rectangle","label":0,"color":"#0ba27c","points":[{"x":0.3495410839160839,"y":0.10314685314685315},{"x":0.5265515734265734,"y":0.10314685314685315},{"x":0.5265515734265734,"y":0.8548951048951049},{"x":0.3495410839160839,"y":0.8548951048951049}]},{"id":1751335833695,"type":"rectangle","label":0,"color":"#0ba27c","points":[{"x":0.5826048951048951,"y":0.09965034965034965},{"x":0.7960008741258742,"y":0.09965034965034965},{"x":0.7960008741258742,"y":0.8513986013986014},{"x":0.5826048951048951,"y":0.8513986013986014}]}]	\N	admin	2025-06-26 10:58:17.29	0	1	2025-08-26 04:00:01.641311	0	1	1	0	0
75	3	frame_3_1750584550519.jpg	/api/v1/buckets/dataset/objects/download?prefix=3/frame_3_1750584550519.jpg	2	2025-06-30 09:26:24.86	704	576	0	[{"id":1751275582941,"type":"rectangle","label":0,"color":"#0ba27c","points":[{"x":0.20462492053401143,"y":0.5594405594405595},{"x":0.0029402415766051904,"y":0.5594405594405595},{"x":0.0029402415766051904,"y":0.9965034965034965},{"x":0.20462492053401143,"y":0.9965034965034965}]}]	\N	\N	2025-06-22 17:29:11.107	0	1	2025-08-26 04:00:01.666973	0	1	1	0	0
81	3	frame_2.0.jpg	/api/v1/buckets/dataset/objects/download?prefix=3/38592722-b0e7-43d5-96eb-986b291fc3e8.jpg	6	2025-06-30 09:04:10.07	\N	\N	165614	[{"id":1751273539979,"type":"rectangle","label":0,"color":"#0ba27c","points":[{"x":0.152676399026764,"y":0.14747228980805624},{"x":0.29744525547445255,"y":0.14747228980805624},{"x":0.29744525547445255,"y":0.6319275479859422},{"x":0.152676399026764,"y":0.6319275479859422}]}]	\N	admin	2025-06-26 10:58:17.04	0	1	2025-08-26 04:00:01.653787	0	1	1	0	0
76	3	frame_3_1750584610482.jpg	/api/v1/buckets/dataset/objects/download?prefix=3/frame_3_1750584610482.jpg	2	2025-06-30 09:23:50.577	704	576	0	[{"id":1751275428676,"type":"rectangle","label":0,"color":"#0ba27c","points":[{"x":0.21320724729815638,"y":0.45454545454545453},{"x":0.010092180546725976,"y":0.45454545454545453},{"x":0.010092180546725976,"y":0.965034965034965},{"x":0.21320724729815638,"y":0.965034965034965}]}]	\N	\N	2025-06-22 17:30:11.056	0	1	2025-08-26 04:00:01.680409	0	1	1	0	0
86	3	frame_7.0.jpg	/api/v1/buckets/dataset/objects/download?prefix=3/9833f5a8-9930-435d-af3e-56033d3ee49e.jpg	4	2025-06-30 08:23:00.908	\N	\N	175541	[{"id":1751271778282,"type":"rectangle","label":0,"color":"#0ba27c","points":[{"x":0.12778627622377622,"y":0.10139860139860139},{"x":0.28611232517482516,"y":0.10139860139860139},{"x":0.28611232517482516,"y":0.7604895104895105},{"x":0.12778627622377622,"y":0.7604895104895105}]},{"id":1751271779394,"type":"rectangle","label":0,"color":"#0ba27c","points":[{"x":0.35986669580419584,"y":0.10139860139860139},{"x":0.4965581293706294,"y":0.10139860139860139},{"x":0.4965581293706294,"y":0.7517482517482518},{"x":0.35986669580419584,"y":0.7517482517482518}]},{"id":1751271780474,"type":"rectangle","label":0,"color":"#0ba27c","points":[{"x":0.5771962412587412,"y":0.09965034965034965},{"x":0.7276551573426573,"y":0.09965034965034965},{"x":0.7276551573426573,"y":0.7272727272727273},{"x":0.5771962412587412,"y":0.7272727272727273}]}]	\N	admin	2025-06-26 10:58:18.219	0	1	2025-08-26 04:00:01.693359	0	1	1	0	0
42	3	frame_3_1750582576856.jpg	/api/v1/buckets/dataset/objects/download?prefix=3/frame_3_1750582576856.jpg	19	2025-06-30 09:23:42.644	704	576	64459	[{"id":1751275414685,"type":"rectangle","label":0,"color":"#0ba27c","points":[{"x":0.015813731722822615,"y":0.05244755244755245},{"x":0.4334869675778767,"y":0.05244755244755245},{"x":0.4334869675778767,"y":0.9545454545454546},{"x":0.015813731722822615,"y":0.9545454545454546}]}]	\N	\N	2025-06-22 16:56:17.378	0	1	2025-08-26 04:00:01.706507	0	1	1	0	0
72	3	frame_3_1750584370516.jpg	/api/v1/buckets/dataset/objects/download?prefix=3/frame_3_1750584370516.jpg	2	2025-06-30 09:26:42.846	704	576	80663	[{"id":1751275602442,"type":"rectangle","label":0,"color":"#0ba27c","points":[{"x":0.2353782581055308,"y":0.47027972027972026},{"x":7.946598855689546E-4,"y":0.47027972027972026},{"x":7.946598855689546E-4,"y":0.9912587412587412},{"x":0.2353782581055308,"y":0.9912587412587412}]}]	\N	\N	2025-06-22 17:26:11.252	0	1	2025-08-26 04:00:01.720022	0	1	1	0	0
84	3	frame_5.0.jpg	/api/v1/buckets/dataset/objects/download?prefix=3/cfe28772-2830-41d3-b94c-60abb84ce9bc.jpg	34	2025-06-30 08:22:39.829	\N	\N	177611	[{"id":1751270428450,"type":"rectangle","label":0,"color":"#0ba27c","points":[{"x":0.11545735900962865,"y":0.054332874828060526},{"x":0.3050206327372765,"y":0.054332874828060526},{"x":0.3050206327372765,"y":0.7792297111416782},{"x":0.11545735900962865,"y":0.7792297111416782}]},{"id":1751271752908,"type":"rectangle","label":0,"color":"#0ba27c","points":[{"x":0.5889969405594405,"y":0.08391608391608392},{"x":0.7551901223776224,"y":0.08391608391608392},{"x":0.7551901223776224,"y":0.7482517482517482},{"x":0.5889969405594405,"y":0.7482517482517482}]},{"id":1751271759051,"type":"rectangle","label":0,"color":"#0ba27c","points":[{"x":0.3578999125874126,"y":0.06118881118881119},{"x":0.5122923951048951,"y":0.06118881118881119},{"x":0.5122923951048951,"y":0.7027972027972028},{"x":0.3578999125874126,"y":0.7027972027972028}]}]	\N	admin	2025-06-26 10:58:17.821	0	1	2025-08-26 04:00:01.733627	0	1	1	0	0
74	3	frame_3_1750584490520.jpg	/api/v1/buckets/dataset/objects/download?prefix=3/frame_3_1750584490520.jpg	2	2025-06-30 09:26:32.265	704	576	79775	[{"id":1751275591660,"type":"rectangle","label":0,"color":"#0ba27c","points":[{"x":0.15742212333121422,"y":0.4562937062937063},{"x":-0.0027813095994914383,"y":0.4562937062937063},{"x":-0.0027813095994914383,"y":0.9755244755244754},{"x":0.15742212333121422,"y":0.9755244755244754}]}]	\N	\N	2025-06-22 17:28:11.105	0	1	2025-08-26 04:00:01.746853	0	1	1	0	0
80	3	frame_1.0.jpg	/api/v1/buckets/dataset/objects/download?prefix=3/08f06324-06b3-4d63-911e-abfdaac139b2.jpg	7	2025-06-30 08:58:05.22	\N	\N	164981	[{"id":1751273879313,"type":"rectangle","label":0,"color":"#0ba27c","points":[{"x":0.38017031630170317,"y":0.0998918626655853},{"x":0.5504866180048662,"y":0.0998918626655853},{"x":0.5504866180048662,"y":0.6557177615571776},{"x":0.38017031630170317,"y":0.6557177615571776}]},{"id":1751273880473,"type":"rectangle","label":0,"color":"#0ba27c","points":[{"x":0.07360097323600973,"y":0.0934036226007029},{"x":0.3546228710462287,"y":0.0934036226007029},{"x":0.3546228710462287,"y":0.6513922681805894},{"x":0.07360097323600973,"y":0.6513922681805894}]},{"id":1751273882273,"type":"rectangle","label":0,"color":"#0ba27c","points":[{"x":0.6210462287104623,"y":0.14314679643146797},{"x":0.8254257907542579,"y":0.14314679643146797},{"x":0.8254257907542579,"y":0.629764801297648},{"x":0.6210462287104623,"y":0.629764801297648}]}]	\N	admin	2025-06-26 10:58:16.76	0	1	2025-08-26 04:00:01.805274	0	1	0	0	1
87	3	frame_8.0.jpg	/api/v1/buckets/dataset/objects/download?prefix=3/545ad59f-f4f7-4780-8da4-dc512d5360fb.jpg	31	2025-06-30 08:22:50.512	\N	\N	178390	[{"id":1751271616691,"type":"rectangle","label":0,"color":"#0ba27c","points":[{"x":0.1356534090909091,"y":0.16433566433566432},{"x":0.3008631993006993,"y":0.16433566433566432},{"x":0.3008631993006993,"y":0.7657342657342658},{"x":0.1356534090909091,"y":0.7657342657342658}]},{"id":1751271768347,"type":"rectangle","label":0,"color":"#0ba27c","points":[{"x":0.5162259615384616,"y":0.7272727272727273},{"x":0.32544798951048953,"y":0.7272727272727273},{"x":0.32544798951048953,"y":0.14685314685314688},{"x":0.5162259615384616,"y":0.14685314685314688}]},{"id":1751271769659,"type":"rectangle","label":0,"color":"#0ba27c","points":[{"x":0.5644121503496503,"y":0.15384615384615385},{"x":0.7197880244755245,"y":0.15384615384615385},{"x":0.7197880244755245,"y":0.7797202797202797},{"x":0.5644121503496503,"y":0.7797202797202797}]}]	\N	admin	2025-06-26 10:58:18.395	0	1	2025-08-26 04:00:01.818642	0	1	0	0	1
1	3	frame_3_1750582093136.jpg	/api/v1/buckets/dataset/objects/download?prefix=3/frame_3_1750582093136.jpg	30	2025-06-30 09:23:27.971	704	576	0	[{"id":1751275394229,"type":"rectangle","label":0,"color":"#0ba27c","points":[{"x":0.11451048951048949,"y":0.36713286713286714},{"x":0.49499364272091545,"y":0.36713286713286714},{"x":0.49499364272091545,"y":0.9632867132867133},{"x":0.11451048951048949,"y":0.9632867132867133}]}]	\N	\N	2025-06-22 16:49:42.418	0	1	2025-08-26 04:00:01.761781	0	1	0	1	0
70	3	frame_3_1750584250492.jpg	/api/v1/buckets/dataset/objects/download?prefix=3/frame_3_1750584250492.jpg	2	2025-06-30 09:26:52.135	704	576	0	[{"id":1751275611643,"type":"rectangle","label":0,"color":"#0ba27c","points":[{"x":0.23890208828310613,"y":0.4270976616231087},{"x":0.005939727397774097,"y":0.4270976616231087},{"x":0.005939727397774097,"y":0.9814305364511692},{"x":0.23890208828310613,"y":0.9814305364511692}]}]	\N	\N	2025-06-22 17:24:11.307	0	1	2025-08-26 04:00:01.775498	0	1	0	0	1
71	3	frame_3_1750584310521.jpg	/api/v1/buckets/dataset/objects/download?prefix=3/frame_3_1750584310521.jpg	2	2025-06-30 09:26:48.329	704	576	80270	[{"id":1751275607923,"type":"rectangle","label":0,"color":"#0ba27c","points":[{"x":0.21189195948480677,"y":0.5371389270976616},{"x":0.00256346129798668,"y":0.5371389270976616},{"x":0.00256346129798668,"y":0.9649243466299863},{"x":0.21189195948480677,"y":0.9649243466299863}]}]	\N	\N	2025-06-22 17:25:13.606	0	1	2025-08-26 04:00:01.791696	0	1	1	0	0
77	3	frame_3_1750584670505.jpg	/api/v1/buckets/dataset/objects/download?prefix=3/frame_3_1750584670505.jpg	3	2025-06-25 07:24:11.075	704	576	0	[{"id":1750836249855,"type":"rectangle","label":0,"color":"#0ba27c","points":[{"x":0.01065340909090909,"y":0.4253472222222222},{"x":0.3231534090909091,"y":0.4253472222222222},{"x":0.3231534090909091,"y":0.9878472222222222},{"x":0.01065340909090909,"y":0.9878472222222222}]}]	\N	\N	2025-06-22 17:31:11.265	0	1	2025-08-26 04:00:01.833449	0	1	1	0	0
78	3	微信图片_20250619154857.jpg	/api/v1/buckets/dataset/objects/download?prefix=3/87f704c0-a07d-47ac-95f0-ae38cae3c199.jpg	5	2025-06-30 09:04:10.105	\N	\N	745340	[{"id":1751274211080,"type":"rectangle","label":0,"color":"#0ba27c","points":[{"x":0.14973679711455734,"y":0.11888111888111888},{"x":0.31873538527718337,"y":0.11888111888111888},{"x":0.31873538527718337,"y":0.7272727272727273},{"x":0.14973679711455734,"y":0.7272727272727273}]},{"id":1751274212320,"type":"rectangle","label":0,"color":"#0ba27c","points":[{"x":0.3677994915179458,"y":0.09965034965034965},{"x":0.5440668361606847,"y":0.09965034965034965},{"x":0.5440668361606847,"y":0.7097902097902098},{"x":0.3677994915179458,"y":0.7097902097902098}]},{"id":1751274213416,"type":"rectangle","label":0,"color":"#0ba27c","points":[{"x":0.6294747248020118,"y":0.11188811188811189},{"x":0.8139194204848779,"y":0.11188811188811189},{"x":0.8139194204848779,"y":0.6975524475524476},{"x":0.6294747248020118,"y":0.6975524475524476}]}]	\N	admin	2025-06-26 10:56:14.293	0	1	2025-08-26 04:00:01.846551	0	1	1	0	0
88	3	frame_3_1750584250492.jpg	/api/v1/buckets/dataset/objects/download?prefix=3/336b6b4e-c51f-4200-a8aa-e505897362a9.jpg	3	2025-06-30 14:49:29.584	\N	\N	79839	[{"id":1751294967051,"type":"rectangle","label":0,"color":"#0ba27c","points":[{"x":0.23180228862047042,"y":0.42657342657342656},{"x":0.0043706293706293475,"y":0.42657342657342656},{"x":0.0043706293706293475,"y":0.9912587412587412},{"x":0.23180228862047042,"y":0.9912587412587412}]}]	\N	admin	2025-06-30 22:49:09.932	0	1	2025-08-26 04:00:01.860027	0	1	0	1	0
85	3	frame_6.0.jpg	/api/v1/buckets/dataset/objects/download?prefix=3/9a8b10c8-53fb-41d3-bc72-ed7f3662d2f0.jpg	12	2025-06-30 08:22:12.036	\N	\N	178379	[{"id":1751270383047,"type":"rectangle","label":0,"color":"#0ba27c","points":[{"x":0.3480659965034965,"y":0.08216783216783216},{"x":0.5437609265734266,"y":0.08216783216783216},{"x":0.5437609265734266,"y":0.7167832167832168},{"x":0.3480659965034965,"y":0.7167832167832168}]}]	\N	admin	2025-06-26 10:58:18.029	0	1	2025-08-26 04:00:01.872839	0	1	0	1	0
83	3	frame_4.0.jpg	/api/v1/buckets/dataset/objects/download?prefix=3/c2fffd14-c4be-469a-8aeb-6dbde23c6bbf.jpg	6	2025-06-30 08:20:31.745	\N	\N	178334	[{"id":1751271628627,"type":"rectangle","label":0,"color":"#0ba27c","points":[{"x":0.15433784965034966,"y":0.0979020979020979},{"x":0.29594624125874125,"y":0.0979020979020979},{"x":0.29594624125874125,"y":0.7395104895104895},{"x":0.15433784965034966,"y":0.7395104895104895}]},{"id":1751271629571,"type":"rectangle","label":0,"color":"#0ba27c","points":[{"x":0.37953452797202797,"y":0.11013986013986014},{"x":0.48180725524475526,"y":0.11013986013986014},{"x":0.48180725524475526,"y":0.7237762237762237},{"x":0.37953452797202797,"y":0.7237762237762237}]},{"id":1751271630682,"type":"rectangle","label":0,"color":"#0ba27c","points":[{"x":0.6076813811188811,"y":0.11188811188811189},{"x":0.7974759615384616,"y":0.11188811188811189},{"x":0.7974759615384616,"y":0.7185314685314685},{"x":0.6076813811188811,"y":0.7185314685314685}]}]	\N	admin	2025-06-26 10:58:17.594	0	1	2025-08-26 04:00:01.886101	0	1	1	0	0
\.


--
-- Data for Name: dataset_tag; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.dataset_tag (id, name, color, dataset_id, warehouse_id, description, create_by, create_time, tenant_id, update_by, update_time, deleted, shortcut) FROM stdin;
1	人	#0ba27c	3	\N	描述人的标签	admin	2025-06-19 07:57:03.489	0	1	2025-08-26 04:00:01.592822	0	0
\.


--
-- Data for Name: dataset_task; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.dataset_task (id, name, dataset_id, data_range, planned_quantity, marked_quantity, new_label, finish_status, finish_time, model_id, model_serve_id, is_stop, task_type, end_time, not_target_count, create_by, create_time, tenant_id, update_by, update_time, deleted) FROM stdin;
\.


--
-- Data for Name: dataset_task_result; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.dataset_task_result (id, dataset_image_id, model_id, has_anno, annos, task_type, user_id, pass_status, task_id, reason, is_update, create_by, create_time, tenant_id, update_by, update_time, deleted) FROM stdin;
\.


--
-- Data for Name: dataset_task_user; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.dataset_task_user (id, task_id, user_id, audit_user_id, create_by, create_time, tenant_id, update_by, update_time, deleted) FROM stdin;
\.


--
-- Data for Name: dataset_video; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.dataset_video (id, dataset_id, video_path, cover_path, description, create_by, create_time, tenant_id, update_by, update_time, deleted, name) FROM stdin;
2	3	/api/v1/buckets/snap-space/objects/download?prefix=test2.mp4	/api/v1/buckets/snap-space/objects/download?prefix=微信图片_20250619154857.jpg	KTV跳舞的小姐姐	admin	2025-06-19 16:14:52.634	0	admin	2025-06-19 16:14:52.634	0	KTV跳舞的小姐姐
\.


--
-- Data for Name: device; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.device (id, client_id, app_id, device_identification, device_name, device_description, device_status, connect_status, is_will, product_identification, create_by, create_time, update_by, update_time, remark, device_version, device_sn, ip_address, mac_address, active_status, extension, activated_time, last_online_time, parent_identification, device_type, tenant_id, deleted) FROM stdin;
57038	\N	默认场景	9720084293632004	储能设备	\N	ENABLE	ONLINE	\N	9820630576939008	admin	2024-10-13 10:56:28	1	2025-08-11 15:27:33.475	\N	\N	9720084293632005	\N	\N	0	\N	\N	\N	\N	GATEWAY	1	0
\.


--
-- Data for Name: device_event; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.device_event (id, device_identification, event_type, message, status, create_time, event_name, event_code, deleted, tenant_id) FROM stdin;
\.


--
-- Data for Name: device_location; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.device_location (id, device_identification, latitude, longitude, full_name, province_code, city_code, region_code, create_by, create_time, update_by, update_time, remark, tenant_id, deleted) FROM stdin;
\.


--
-- Data for Name: device_ota_pkg; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.device_ota_pkg (id, type, name, version, upgrade_mode, url, key_version_flag, status, upload_time, publish_time, created_by, created_time, updated_by, file_md5, remark, updated_time, tenant_id, deleted) FROM stdin;
6	0	软件测试包	1.0.0	0	http://127.0.0.1:19300/statics/2024/07/30/c9f0e8a0-0664-4edc-a6b6-020ea85c3a94.png	0	0	2024-07-30 15:09:13.814	\N	admin	2024-07-30 15:09:13.856	admin	\N	软件测试包	2024-07-30 15:09:13.856	1	0
7	1	固件测试包	1.0.0	0	http://127.0.0.1:19300/statics/2024/07/30/f57bbdb2-5b20-4f55-a97b-1bc6ac11252e.png	1	0	2024-07-30 15:50:37.294	\N	admin	2024-07-30 15:50:37.3	admin	\N	固件升级测试包	2024-07-30 15:50:37.3	1	0
\.


--
-- Data for Name: device_service_invoke_response; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.device_service_invoke_response (id, message_id, device_id, device_identification, product_identification, service_identifier, request_id, method, response_data, response_code, response_msg, topic, report_time, tenant_id, create_time) FROM stdin;
\.


--
-- Data for Name: device_topic; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.device_topic (id, device_identification, type, topic, publisher, subscriber, create_by, create_time, update_by, update_time, remark, tenant_id, deleted) FROM stdin;
\.


--
-- Data for Name: ota_packages; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.ota_packages (id, app_id, package_name, package_type, product_identification, version, file_location, status, description, custom_info, remark, created_by, created_time, updated_by, updated_time, tenant_id, deleted) FROM stdin;
\.


--
-- Data for Name: product; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.product (id, app_id, template_identification, product_name, product_identification, product_type, manufacturer_id, manufacturer_name, model, data_format, device_type, protocol_type, status, remark, create_by, create_time, update_by, update_time, auth_mode, user_name, password, connector, sign_key, encrypt_method, encrypt_key, encrypt_vector, tenant_id) FROM stdin;
22	智能家居	3ff77a5289144dacbb6d32bee107f90f	智能网关	9820630576939008	COMMON	12321	华科南航科技有限公司	32423	JSON	32423	GB28181	0	23432	admin	2024-07-04 17:35:50.852	admin	2024-07-04 17:35:50.852	32423	32432	32423	432432	32423	0	32432	23432	1
\.


--
-- Data for Name: product_commands; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.product_commands (id, service_id, name, description, create_by, create_time, update_by, update_time, command_code, remark, tenant_id) FROM stdin;
\.


--
-- Data for Name: product_commands_requests; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.product_commands_requests (id, service_id, commands_id, datatype, enumlist, max, maxlength, min, parameter_description, parameter_name, required, step, unit, create_by, create_time, update_by, update_time, parameter_code, tenant_id) FROM stdin;
\.


--
-- Data for Name: product_commands_response; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.product_commands_response (id, commands_id, service_id, datatype, enumlist, max, maxlength, min, parameter_description, parameter_name, required, step, unit, create_by, create_time, update_by, update_time, parameter_code, tenant_id) FROM stdin;
\.


--
-- Data for Name: product_event; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.product_event (id, event_name, event_code, event_type, template_identification, product_identification, status, description, create_by, create_time, update_by, update_time, tenant_id) FROM stdin;
\.


--
-- Data for Name: product_event_response; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.product_event_response (id, event_id, service_id, datatype, enumlist, max, maxlength, min, parameter_description, parameter_name, required, step, unit, create_by, create_time, update_by, update_time, tenant_id) FROM stdin;
\.


--
-- Data for Name: product_properties; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.product_properties (id, property_name, property_code, datatype, description, enumlist, max, maxlength, method, min, required, step, unit, create_by, create_time, update_by, update_time, template_identification, product_identification, tenant_id) FROM stdin;
46	接收信号强度	RSSI	TEXT	\N		\N	10240	r	\N	\N	\N	\N	admin	2024-06-18 15:30:04.327	admin	2024-06-18 15:30:04.327	\N	9820630576939008	1
47	z轴倾斜角度	PVAngle_Z	TEXT	\N		\N	10240	r	\N	\N	\N	\N	admin	2024-06-18 15:30:27.916	admin	2024-06-18 15:30:27.916	\N	9820630576939008	1
48	y轴倾斜角度	PVAngle_Y	TEXT	\N		\N	10240	r	\N	\N	\N	\N	admin	2024-06-18 15:30:41.868	admin	2024-06-18 15:30:41.868	\N	9820630576939008	1
49	x轴倾斜角度	PVAngle_X	TEXT	\N		\N	10240	r	\N	\N	\N	\N	admin	2024-06-18 15:30:58.784	admin	2024-06-18 15:30:58.784	\N	9820630576939008	1
50	事件时间	eventTime	TEXT	\N		\N	10240	r	\N	\N	\N	\N	admin	2024-06-18 15:31:57.754	admin	2024-06-18 15:31:57.754	\N	9820630576939008	1
51	电量	Vbatt	TEXT	\N		\N	10240	r	\N	\N	\N	\N	admin	2024-06-18 15:32:13.564	admin	2024-06-18 15:32:13.565	\N	9820630576939008	1
52	服务ID	serviceId	TEXT	\N		\N	10240	r	\N	\N	\N	\N	admin	2024-06-18 15:32:45.728	admin	2024-06-18 15:32:45.728	\N	9820630576939008	1
53	设备ID	deviceId	TEXT	\N		\N	10240	r	\N	\N	\N	\N	admin	2024-06-18 15:32:59.716	admin	2024-06-18 15:32:59.716	\N	9820630576939008	1
\.


--
-- Data for Name: product_script; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.product_script (id, product_id, product_identification, script_enabled, script_content, script_version, create_by, create_time, update_by, update_time, tenant_id) FROM stdin;
\.


--
-- Data for Name: product_services; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.product_services (id, service_code, service_name, template_identification, product_identification, status, description, create_by, create_time, update_by, update_time, tenant_id) FROM stdin;
\.


--
-- Data for Name: product_template; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.product_template (id, app_id, template_identification, template_name, status, remark, create_by, create_time, update_by, update_time, tenant_id) FROM stdin;
\.


--
-- Data for Name: warehouse; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.warehouse (id, name, cover_path, description, create_by, create_time, tenant_id, update_by, update_time, deleted) FROM stdin;
1	数据仓（人、火焰）	/api/v1/buckets/snap-space/objects/download?prefix=545ad59f-f4f7-4780-8da4-dc512d5360fb.jpg	数据仓（人、火焰）的融合数据集。	admin	2025-06-30 23:17:50.864	0	admin	2025-06-30 23:17:50.864	0
2	数据仓（人、火焰）	/api/v1/buckets/snap-space/objects/download?prefix=545ad59f-f4f7-4780-8da4-dc512d5360fb.jpg	数据仓（人、火焰）的融合数据集仓库。	admin	2025-06-30 23:18:29.288	0	admin	2025-06-30 23:18:29.288	0
\.


--
-- Data for Name: warehouse_dataset; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.warehouse_dataset (id, dataset_id, warehouse_id, plan_sync_count, sync_count, sync_status, fail_count, create_by, create_time, tenant_id, update_by, update_time, deleted) FROM stdin;
\.


--
-- Name: algorithm_alarm_data_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.algorithm_alarm_data_id_seq', 1263305, true);


--
-- Name: algorithm_customer_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.algorithm_customer_id_seq', 1, false);


--
-- Name: algorithm_model_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.algorithm_model_id_seq', 1, false);


--
-- Name: algorithm_nvr_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.algorithm_nvr_id_seq', 1, false);


--
-- Name: algorithm_playback_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.algorithm_playback_id_seq', 1, false);


--
-- Name: algorithm_push_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.algorithm_push_log_id_seq', 1, false);


--
-- Name: algorithm_task_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.algorithm_task_id_seq', 1, false);


--
-- Name: algorithm_video_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.algorithm_video_id_seq', 1, false);


--
-- Name: dataset_frame_task_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.dataset_frame_task_id_seq', 1, true);


--
-- Name: dataset_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.dataset_id_seq', 1, false);


--
-- Name: dataset_image_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.dataset_image_id_seq', 2, true);


--
-- Name: dataset_image_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.dataset_image_seq', 1, false);


--
-- Name: dataset_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.dataset_seq', 1, false);


--
-- Name: dataset_tag_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.dataset_tag_id_seq', 1, true);


--
-- Name: dataset_tag_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.dataset_tag_seq', 1, false);


--
-- Name: dataset_task_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.dataset_task_id_seq', 1, false);


--
-- Name: dataset_task_result_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.dataset_task_result_id_seq', 1, false);


--
-- Name: dataset_task_result_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.dataset_task_result_seq', 1, false);


--
-- Name: dataset_task_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.dataset_task_seq', 1, false);


--
-- Name: dataset_task_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.dataset_task_user_id_seq', 1, false);


--
-- Name: dataset_task_user_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.dataset_task_user_seq', 1, false);


--
-- Name: dataset_video_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.dataset_video_id_seq', 1, false);


--
-- Name: dataset_video_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.dataset_video_seq', 1, false);


--
-- Name: datasource_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.datasource_seq', 1, false);


--
-- Name: device_event_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.device_event_id_seq', 1, false);


--
-- Name: device_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.device_id_seq', 57077, true);


--
-- Name: device_location_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.device_location_id_seq', 1, false);


--
-- Name: device_log_file_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.device_log_file_id_seq', 17, true);


--
-- Name: device_ota_device_model_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.device_ota_device_model_id_seq', 1, false);


--
-- Name: device_ota_pkg_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.device_ota_pkg_id_seq', 1, false);


--
-- Name: device_ota_version_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.device_ota_version_id_seq', 6, true);


--
-- Name: device_ota_version_publish_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.device_ota_version_publish_id_seq', 1, false);


--
-- Name: device_ota_version_verify_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.device_ota_version_verify_id_seq', 11, true);


--
-- Name: device_service_invoke_response_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.device_service_invoke_response_id_seq', 1, false);


--
-- Name: device_topic_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.device_topic_id_seq', 1, false);


--
-- Name: dm_ota_version_lang_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.dm_ota_version_lang_id_seq', 1, false);


--
-- Name: experiment_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.experiment_id_seq', 1, false);


--
-- Name: experiment_image_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.experiment_image_id_seq', 1, false);


--
-- Name: experiment_resources_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.experiment_resources_id_seq', 1, false);


--
-- Name: experiment_run_record_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.experiment_run_record_id_seq', 1, false);


--
-- Name: experiment_share_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.experiment_share_id_seq', 1, false);


--
-- Name: experiment_share_parameters_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.experiment_share_parameters_id_seq', 1, false);


--
-- Name: experiment_tag_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.experiment_tag_id_seq', 1, false);


--
-- Name: experiment_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.experiment_user_id_seq', 1, false);


--
-- Name: file_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.file_seq', 1, false);


--
-- Name: iot_app_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.iot_app_id_seq', 1, false);


--
-- Name: model_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.model_id_seq', 1, false);


--
-- Name: model_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.model_seq', 1, false);


--
-- Name: model_server_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.model_server_id_seq', 1, false);


--
-- Name: model_server_quantify_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.model_server_quantify_id_seq', 1, false);


--
-- Name: model_server_quantify_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.model_server_quantify_seq', 1, false);


--
-- Name: model_server_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.model_server_seq', 1, false);


--
-- Name: model_server_test_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.model_server_test_id_seq', 1, false);


--
-- Name: model_server_test_image_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.model_server_test_image_id_seq', 1, false);


--
-- Name: model_server_test_image_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.model_server_test_image_seq', 1, false);


--
-- Name: model_server_test_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.model_server_test_seq', 1, false);


--
-- Name: model_server_test_video_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.model_server_test_video_id_seq', 1, false);


--
-- Name: model_server_test_video_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.model_server_test_video_seq', 1, false);


--
-- Name: model_server_video_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.model_server_video_id_seq', 1, false);


--
-- Name: model_server_video_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.model_server_video_seq', 1, false);


--
-- Name: model_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.model_type_id_seq', 1, false);


--
-- Name: model_type_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.model_type_seq', 1, false);


--
-- Name: product_commands_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.product_commands_id_seq', 1, false);


--
-- Name: product_commands_requests_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.product_commands_requests_id_seq', 1, false);


--
-- Name: product_commands_response_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.product_commands_response_id_seq', 1, false);


--
-- Name: product_event_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.product_event_id_seq', 1, false);


--
-- Name: product_event_response_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.product_event_response_id_seq', 1, false);


--
-- Name: product_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.product_id_seq', 30, true);


--
-- Name: product_properties_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.product_properties_id_seq', 53, true);


--
-- Name: product_script_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.product_script_id_seq', 1, false);


--
-- Name: product_services_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.product_services_id_seq', 1, false);


--
-- Name: product_template_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.product_template_id_seq', 1, false);


--
-- Name: project_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.project_seq', 1, false);


--
-- Name: sys_job_log__seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.sys_job_log__seq', 103012, true);


--
-- Name: warehouse_dataset_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.warehouse_dataset_id_seq', 1, false);


--
-- Name: warehouse_dataset_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.warehouse_dataset_seq', 1, false);


--
-- Name: warehouse_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.warehouse_id_seq', 1, false);


--
-- Name: warehouse_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.warehouse_seq', 1, false);


--
-- Name: product _copy_113; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product
    ADD CONSTRAINT _copy_113 PRIMARY KEY (id);


--
-- Name: product_template _copy_35; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_template
    ADD CONSTRAINT _copy_35 PRIMARY KEY (id);


--
-- Name: product_properties _copy_37; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_properties
    ADD CONSTRAINT _copy_37 PRIMARY KEY (id);


--
-- Name: ota_packages _copy_42; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ota_packages
    ADD CONSTRAINT _copy_42 PRIMARY KEY (id);


--
-- Name: device_topic _copy_47; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.device_topic
    ADD CONSTRAINT _copy_47 PRIMARY KEY (id);


--
-- Name: device_location _copy_48_1; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.device_location
    ADD CONSTRAINT _copy_48_1 PRIMARY KEY (id);


--
-- Name: device _copy_52; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.device
    ADD CONSTRAINT _copy_52 PRIMARY KEY (id);


--
-- Name: dataset_image dataset_image_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dataset_image
    ADD CONSTRAINT dataset_image_pkey PRIMARY KEY (id);


--
-- Name: dataset dataset_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dataset
    ADD CONSTRAINT dataset_pkey PRIMARY KEY (id);


--
-- Name: dataset_tag dataset_tag_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dataset_tag
    ADD CONSTRAINT dataset_tag_pkey PRIMARY KEY (id);


--
-- Name: dataset_task dataset_task_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dataset_task
    ADD CONSTRAINT dataset_task_pkey PRIMARY KEY (id);


--
-- Name: dataset_task_result dataset_task_result_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dataset_task_result
    ADD CONSTRAINT dataset_task_result_pkey PRIMARY KEY (id);


--
-- Name: dataset_task_user dataset_task_user_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dataset_task_user
    ADD CONSTRAINT dataset_task_user_pkey PRIMARY KEY (id);


--
-- Name: dataset_video dataset_video_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dataset_video
    ADD CONSTRAINT dataset_video_pkey PRIMARY KEY (id);


--
-- Name: device_event device_event_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.device_event
    ADD CONSTRAINT device_event_pkey PRIMARY KEY (id);


--
-- Name: device_ota_pkg device_ota_pkg_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.device_ota_pkg
    ADD CONSTRAINT device_ota_pkg_pkey PRIMARY KEY (id);


--
-- Name: device_service_invoke_response device_service_invoke_response_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.device_service_invoke_response
    ADD CONSTRAINT device_service_invoke_response_pkey PRIMARY KEY (id);


--
-- Name: app iot_app_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app
    ADD CONSTRAINT iot_app_pkey PRIMARY KEY (id);


--
-- Name: product_commands product_commands_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_commands
    ADD CONSTRAINT product_commands_pkey PRIMARY KEY (id);


--
-- Name: product_commands_requests product_commands_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_commands_requests
    ADD CONSTRAINT product_commands_requests_pkey PRIMARY KEY (id);


--
-- Name: product_commands_response product_commands_response_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_commands_response
    ADD CONSTRAINT product_commands_response_pkey PRIMARY KEY (id);


--
-- Name: product_event product_event_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_event
    ADD CONSTRAINT product_event_pkey PRIMARY KEY (id);


--
-- Name: product_event_response product_event_response_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_event_response
    ADD CONSTRAINT product_event_response_pkey PRIMARY KEY (id);


--
-- Name: product_services product_services_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_services
    ADD CONSTRAINT product_services_pkey PRIMARY KEY (id);


--
-- Name: app uk_app_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app
    ADD CONSTRAINT uk_app_id UNIQUE (app_id);


--
-- Name: app uk_app_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app
    ADD CONSTRAINT uk_app_key UNIQUE (app_key);


--
-- Name: warehouse_dataset warehouse_dataset_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.warehouse_dataset
    ADD CONSTRAINT warehouse_dataset_pkey PRIMARY KEY (id);


--
-- Name: warehouse warehouse_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.warehouse
    ADD CONSTRAINT warehouse_pkey PRIMARY KEY (id);


--
-- Name: idx_app_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_app_id ON public.ota_packages USING btree (app_id);


--
-- Name: INDEX idx_app_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON INDEX public.idx_app_id IS '应用ID';


--
-- Name: idx_created_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_created_time ON public.app USING btree (created_time);


--
-- Name: idx_device_event_create_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_device_event_create_time ON public.device_event USING btree (create_time);


--
-- Name: idx_device_event_device_identification; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_device_event_device_identification ON public.device_event USING btree (device_identification);


--
-- Name: idx_device_event_event_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_device_event_event_code ON public.device_event USING btree (event_code);


--
-- Name: idx_device_event_tenant_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_device_event_tenant_id ON public.device_event USING btree (tenant_id);


--
-- Name: idx_device_service_invoke_response_create_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_device_service_invoke_response_create_time ON public.device_service_invoke_response USING btree (create_time);


--
-- Name: idx_device_service_invoke_response_device_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_device_service_invoke_response_device_id ON public.device_service_invoke_response USING btree (device_id);


--
-- Name: idx_device_service_invoke_response_device_identification; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_device_service_invoke_response_device_identification ON public.device_service_invoke_response USING btree (device_identification);


--
-- Name: idx_device_service_invoke_response_message_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_device_service_invoke_response_message_id ON public.device_service_invoke_response USING btree (message_id);


--
-- Name: idx_device_service_invoke_response_tenant_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_device_service_invoke_response_tenant_id ON public.device_service_invoke_response USING btree (tenant_id);


--
-- Name: idx_expire_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_expire_time ON public.app USING btree (expire_time);


--
-- Name: idx_product_commands_requests_commands_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_product_commands_requests_commands_id ON public.product_commands_requests USING btree (commands_id);


--
-- Name: idx_product_commands_requests_service_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_product_commands_requests_service_id ON public.product_commands_requests USING btree (service_id);


--
-- Name: idx_product_commands_requests_tenant_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_product_commands_requests_tenant_id ON public.product_commands_requests USING btree (tenant_id);


--
-- Name: idx_product_commands_response_commands_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_product_commands_response_commands_id ON public.product_commands_response USING btree (commands_id);


--
-- Name: idx_product_commands_response_service_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_product_commands_response_service_id ON public.product_commands_response USING btree (service_id);


--
-- Name: idx_product_commands_response_tenant_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_product_commands_response_tenant_id ON public.product_commands_response USING btree (tenant_id);


--
-- Name: idx_product_commands_service_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_product_commands_service_id ON public.product_commands USING btree (service_id);


--
-- Name: idx_product_commands_tenant_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_product_commands_tenant_id ON public.product_commands USING btree (tenant_id);


--
-- Name: idx_product_event_event_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_product_event_event_code ON public.product_event USING btree (event_code);


--
-- Name: idx_product_event_product_identification; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_product_event_product_identification ON public.product_event USING btree (product_identification);


--
-- Name: idx_product_event_response_event_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_product_event_response_event_id ON public.product_event_response USING btree (event_id);


--
-- Name: idx_product_event_response_service_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_product_event_response_service_id ON public.product_event_response USING btree (service_id);


--
-- Name: idx_product_event_response_tenant_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_product_event_response_tenant_id ON public.product_event_response USING btree (tenant_id);


--
-- Name: idx_product_event_tenant_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_product_event_tenant_id ON public.product_event USING btree (tenant_id);


--
-- Name: idx_product_identification; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_product_identification ON public.ota_packages USING btree (product_identification);


--
-- Name: INDEX idx_product_identification; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON INDEX public.idx_product_identification IS '产品标识';


--
-- Name: idx_product_script_product_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_product_script_product_id ON public.product_script USING btree (product_id);


--
-- Name: idx_product_script_product_identification; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_product_script_product_identification ON public.product_script USING btree (product_identification);


--
-- Name: idx_product_script_tenant_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_product_script_tenant_id ON public.product_script USING btree (tenant_id);


--
-- Name: idx_product_services_product_identification; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_product_services_product_identification ON public.product_services USING btree (product_identification);


--
-- Name: idx_product_services_service_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_product_services_service_code ON public.product_services USING btree (service_code);


--
-- Name: idx_product_services_tenant_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_product_services_tenant_id ON public.product_services USING btree (tenant_id);


--
-- Name: idx_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_status ON public.app USING btree (status);


--
-- Name: idx_tenant_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tenant_id ON public.app USING btree (tenant_id);


--
-- Name: idx_version; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_version ON public.ota_packages USING btree (version);


--
-- Name: INDEX idx_version; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON INDEX public.idx_version IS '升级包版本号';


--
-- Name: manufacturer_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX manufacturer_id ON public.product USING btree (manufacturer_id);


--
-- Name: INDEX manufacturer_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON INDEX public.manufacturer_id IS '厂商ID索引';


--
-- Name: app update_iot_app_updated_time; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_iot_app_updated_time BEFORE UPDATE ON public.app FOR EACH ROW EXECUTE FUNCTION public.update_updated_time_column();


--
-- PostgreSQL database dump complete
--

\unrestrict Fxw8kG3gVEObSjt53dfInfuAPpla7dLlSt2hdg1IzOtgl3fYIegIsi0S4hwmPKX

