--
-- PostgreSQL database dump
--

\restrict k88Kj3l92Z5fxPjrzFejWOwz4JNiTHf0VeLTgzfncbJ4fF4Wu4geZdRPnODzQ6x

-- Dumped from database version 16.10 (Debian 16.10-1.pgdg13+1)
-- Dumped by pg_dump version 16.10 (Ubuntu 16.10-0ubuntu0.24.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
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
-- Name: alert; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alert (
    id integer NOT NULL,
    object character varying(30) NOT NULL,
    event character varying(30) NOT NULL,
    region character varying(30),
    information text,
    "time" timestamp with time zone DEFAULT now() NOT NULL,
    device_id character varying(30) NOT NULL,
    device_name character varying(30) NOT NULL,
    image_path character varying(200),
    record_path character varying(200)
);


ALTER TABLE public.alert OWNER TO postgres;

--
-- Name: alert_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.alert_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.alert_id_seq OWNER TO postgres;

--
-- Name: alert_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.alert_id_seq OWNED BY public.alert.id;


--
-- Name: algorithm_model_service; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.algorithm_model_service (
    id integer NOT NULL,
    task_id integer NOT NULL,
    service_name character varying(255) NOT NULL,
    service_url character varying(500) NOT NULL,
    service_type character varying(100),
    model_id integer,
    threshold double precision,
    request_method character varying(10) NOT NULL,
    request_headers text,
    request_body_template text,
    timeout integer NOT NULL,
    is_enabled boolean NOT NULL,
    sort_order integer NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.algorithm_model_service OWNER TO postgres;

--
-- Name: COLUMN algorithm_model_service.task_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.algorithm_model_service.task_id IS '所属任务ID';


--
-- Name: COLUMN algorithm_model_service.service_name; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.algorithm_model_service.service_name IS '服务名称';


--
-- Name: COLUMN algorithm_model_service.service_url; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.algorithm_model_service.service_url IS 'AI模型服务请求接口URL';


--
-- Name: COLUMN algorithm_model_service.service_type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.algorithm_model_service.service_type IS '服务类型[FIRE:火焰烟雾检测,CROWD:人群聚集计数,SMOKE:吸烟检测等]';


--
-- Name: COLUMN algorithm_model_service.model_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.algorithm_model_service.model_id IS '关联的模型ID';


--
-- Name: COLUMN algorithm_model_service.threshold; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.algorithm_model_service.threshold IS '检测阈值';


--
-- Name: COLUMN algorithm_model_service.request_method; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.algorithm_model_service.request_method IS '请求方法[GET,POST]';


--
-- Name: COLUMN algorithm_model_service.request_headers; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.algorithm_model_service.request_headers IS '请求头（JSON格式）';


--
-- Name: COLUMN algorithm_model_service.request_body_template; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.algorithm_model_service.request_body_template IS '请求体模板（JSON格式，支持变量替换）';


--
-- Name: COLUMN algorithm_model_service.timeout; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.algorithm_model_service.timeout IS '请求超时时间（秒）';


--
-- Name: COLUMN algorithm_model_service.is_enabled; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.algorithm_model_service.is_enabled IS '是否启用';


--
-- Name: COLUMN algorithm_model_service.sort_order; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.algorithm_model_service.sort_order IS '排序顺序';


--
-- Name: algorithm_model_service_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.algorithm_model_service_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.algorithm_model_service_id_seq OWNER TO postgres;

--
-- Name: algorithm_model_service_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.algorithm_model_service_id_seq OWNED BY public.algorithm_model_service.id;


--
-- Name: detection_region; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.detection_region (
    id integer NOT NULL,
    task_id integer NOT NULL,
    region_name character varying(255) NOT NULL,
    region_type character varying(50) NOT NULL,
    points text NOT NULL,
    image_id integer,
    algorithm_type character varying(255),
    algorithm_model_id integer,
    algorithm_threshold double precision,
    algorithm_enabled boolean NOT NULL,
    color character varying(20) NOT NULL,
    opacity double precision NOT NULL,
    is_enabled boolean NOT NULL,
    sort_order integer NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.detection_region OWNER TO postgres;

--
-- Name: COLUMN detection_region.task_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.detection_region.task_id IS '所属任务ID';


--
-- Name: COLUMN detection_region.region_name; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.detection_region.region_name IS '区域名称';


--
-- Name: COLUMN detection_region.region_type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.detection_region.region_type IS '区域类型[polygon:多边形,rectangle:矩形]';


--
-- Name: COLUMN detection_region.points; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.detection_region.points IS '区域坐标点(JSON格式，归一化坐标0-1)';


--
-- Name: COLUMN detection_region.image_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.detection_region.image_id IS '参考图片ID（用于绘制区域的基准图片）';


--
-- Name: COLUMN detection_region.algorithm_type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.detection_region.algorithm_type IS '绑定的算法类型[FIRE:火焰烟雾检测,CROWD:人群聚集计数,SMOKE:吸烟检测等]';


--
-- Name: COLUMN detection_region.algorithm_model_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.detection_region.algorithm_model_id IS '绑定的算法模型ID';


--
-- Name: COLUMN detection_region.algorithm_threshold; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.detection_region.algorithm_threshold IS '算法阈值';


--
-- Name: COLUMN detection_region.algorithm_enabled; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.detection_region.algorithm_enabled IS '是否启用该区域的算法';


--
-- Name: COLUMN detection_region.color; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.detection_region.color IS '区域显示颜色';


--
-- Name: COLUMN detection_region.opacity; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.detection_region.opacity IS '区域透明度(0-1)';


--
-- Name: COLUMN detection_region.is_enabled; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.detection_region.is_enabled IS '是否启用该区域';


--
-- Name: COLUMN detection_region.sort_order; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.detection_region.sort_order IS '排序顺序';


--
-- Name: detection_region_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.detection_region_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.detection_region_id_seq OWNER TO postgres;

--
-- Name: detection_region_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.detection_region_id_seq OWNED BY public.detection_region.id;


--
-- Name: device; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.device (
    id character varying(100) NOT NULL,
    name character varying(100),
    source text NOT NULL,
    rtmp_stream text NOT NULL,
    http_stream text NOT NULL,
    stream smallint,
    ip character varying(45),
    port smallint,
    username character varying(100),
    password character varying(100),
    mac character varying(17),
    manufacturer character varying(100) NOT NULL,
    model character varying(100) NOT NULL,
    firmware_version character varying(100),
    serial_number character varying(300),
    hardware_id character varying(100),
    support_move boolean,
    support_zoom boolean,
    nvr_id integer,
    nvr_channel smallint NOT NULL,
    enable_forward boolean,
    directory_id integer,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    auto_snap_enabled boolean DEFAULT false NOT NULL
);


ALTER TABLE public.device OWNER TO postgres;

--
-- Name: COLUMN device.directory_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.device.directory_id IS '所属目录ID';


--
-- Name: COLUMN device.auto_snap_enabled; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.device.auto_snap_enabled IS '是否开启自动抓拍[默认不开启]';


--
-- Name: device_directory; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.device_directory (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    parent_id integer,
    description character varying(500),
    sort_order integer NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.device_directory OWNER TO postgres;

--
-- Name: COLUMN device_directory.name; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.device_directory.name IS '目录名称';


--
-- Name: COLUMN device_directory.parent_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.device_directory.parent_id IS '父目录ID，NULL表示根目录';


--
-- Name: COLUMN device_directory.description; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.device_directory.description IS '目录描述';


--
-- Name: COLUMN device_directory.sort_order; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.device_directory.sort_order IS '排序顺序';


--
-- Name: device_directory_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.device_directory_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.device_directory_id_seq OWNER TO postgres;

--
-- Name: device_directory_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.device_directory_id_seq OWNED BY public.device_directory.id;


--
-- Name: device_storage_config; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.device_storage_config (
    id integer NOT NULL,
    device_id character varying(100) NOT NULL,
    snap_storage_bucket character varying(255),
    snap_storage_max_size bigint,
    snap_storage_cleanup_enabled boolean NOT NULL,
    snap_storage_cleanup_threshold double precision NOT NULL,
    snap_storage_cleanup_ratio double precision NOT NULL,
    video_storage_bucket character varying(255),
    video_storage_max_size bigint,
    video_storage_cleanup_enabled boolean NOT NULL,
    video_storage_cleanup_threshold double precision NOT NULL,
    video_storage_cleanup_ratio double precision NOT NULL,
    last_snap_cleanup_time timestamp without time zone,
    last_video_cleanup_time timestamp without time zone,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.device_storage_config OWNER TO postgres;

--
-- Name: COLUMN device_storage_config.device_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.device_storage_config.device_id IS '设备ID';


--
-- Name: COLUMN device_storage_config.snap_storage_bucket; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.device_storage_config.snap_storage_bucket IS '抓拍图片存储bucket名称';


--
-- Name: COLUMN device_storage_config.snap_storage_max_size; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.device_storage_config.snap_storage_max_size IS '抓拍图片存储最大空间（字节），0表示不限制';


--
-- Name: COLUMN device_storage_config.snap_storage_cleanup_enabled; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.device_storage_config.snap_storage_cleanup_enabled IS '是否启用抓拍图片自动清理';


--
-- Name: COLUMN device_storage_config.snap_storage_cleanup_threshold; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.device_storage_config.snap_storage_cleanup_threshold IS '抓拍图片清理阈值（使用率超过此值触发清理）';


--
-- Name: COLUMN device_storage_config.snap_storage_cleanup_ratio; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.device_storage_config.snap_storage_cleanup_ratio IS '抓拍图片清理比例（清理最老的30%）';


--
-- Name: COLUMN device_storage_config.video_storage_bucket; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.device_storage_config.video_storage_bucket IS '录像存储bucket名称';


--
-- Name: COLUMN device_storage_config.video_storage_max_size; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.device_storage_config.video_storage_max_size IS '录像存储最大空间（字节），0表示不限制';


--
-- Name: COLUMN device_storage_config.video_storage_cleanup_enabled; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.device_storage_config.video_storage_cleanup_enabled IS '是否启用录像自动清理';


--
-- Name: COLUMN device_storage_config.video_storage_cleanup_threshold; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.device_storage_config.video_storage_cleanup_threshold IS '录像清理阈值（使用率超过此值触发清理）';


--
-- Name: COLUMN device_storage_config.video_storage_cleanup_ratio; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.device_storage_config.video_storage_cleanup_ratio IS '录像清理比例（清理最老的30%）';


--
-- Name: COLUMN device_storage_config.last_snap_cleanup_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.device_storage_config.last_snap_cleanup_time IS '最后抓拍图片清理时间';


--
-- Name: COLUMN device_storage_config.last_video_cleanup_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.device_storage_config.last_video_cleanup_time IS '最后录像清理时间';


--
-- Name: device_storage_config_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.device_storage_config_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.device_storage_config_id_seq OWNER TO postgres;

--
-- Name: device_storage_config_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.device_storage_config_id_seq OWNED BY public.device_storage_config.id;


--
-- Name: image; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.image (
    id integer NOT NULL,
    filename character varying(255) NOT NULL,
    original_filename character varying(255) NOT NULL,
    path character varying(500) NOT NULL,
    width integer NOT NULL,
    height integer NOT NULL,
    created_at timestamp without time zone,
    device_id character varying(100)
);


ALTER TABLE public.image OWNER TO postgres;

--
-- Name: image_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.image_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.image_id_seq OWNER TO postgres;

--
-- Name: image_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.image_id_seq OWNED BY public.image.id;


--
-- Name: nvr; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.nvr (
    id integer NOT NULL,
    ip character varying(45) NOT NULL,
    username character varying(100),
    password character varying(100),
    name character varying(100),
    model character varying(100)
);


ALTER TABLE public.nvr OWNER TO postgres;

--
-- Name: nvr_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.nvr_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.nvr_id_seq OWNER TO postgres;

--
-- Name: nvr_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.nvr_id_seq OWNED BY public.nvr.id;


--
-- Name: playback; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.playback (
    id integer NOT NULL,
    file_path character varying(200) NOT NULL,
    event_time timestamp with time zone NOT NULL,
    device_id character varying(30) NOT NULL,
    device_name character varying(30) NOT NULL,
    duration smallint NOT NULL,
    thumbnail_path character varying(200),
    file_size bigint,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.playback OWNER TO postgres;

--
-- Name: playback_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.playback_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.playback_id_seq OWNER TO postgres;

--
-- Name: playback_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.playback_id_seq OWNED BY public.playback.id;


--
-- Name: record_space; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.record_space (
    id integer NOT NULL,
    space_name character varying(255) NOT NULL,
    space_code character varying(255) NOT NULL,
    bucket_name character varying(255) NOT NULL,
    save_mode smallint NOT NULL,
    save_time integer NOT NULL,
    description character varying(500),
    device_id character varying(100),
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.record_space OWNER TO postgres;

--
-- Name: COLUMN record_space.space_name; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.record_space.space_name IS '空间名称';


--
-- Name: COLUMN record_space.space_code; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.record_space.space_code IS '空间编号（唯一标识）';


--
-- Name: COLUMN record_space.bucket_name; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.record_space.bucket_name IS 'MinIO bucket名称';


--
-- Name: COLUMN record_space.save_mode; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.record_space.save_mode IS '文件保存模式[0:标准存储,1:归档存储]';


--
-- Name: COLUMN record_space.save_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.record_space.save_time IS '文件保存时间[0:永久保存,>=7(单位:天)]';


--
-- Name: COLUMN record_space.description; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.record_space.description IS '空间描述';


--
-- Name: COLUMN record_space.device_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.record_space.device_id IS '关联的设备ID（一对一关系）';


--
-- Name: record_space_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.record_space_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.record_space_id_seq OWNER TO postgres;

--
-- Name: record_space_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.record_space_id_seq OWNED BY public.record_space.id;


--
-- Name: region_model_service; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.region_model_service (
    id integer NOT NULL,
    region_id integer NOT NULL,
    service_name character varying(255) NOT NULL,
    service_url character varying(500) NOT NULL,
    service_type character varying(100),
    model_id integer,
    threshold double precision,
    request_method character varying(10) NOT NULL,
    request_headers text,
    request_body_template text,
    timeout integer NOT NULL,
    is_enabled boolean NOT NULL,
    sort_order integer NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.region_model_service OWNER TO postgres;

--
-- Name: COLUMN region_model_service.region_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.region_model_service.region_id IS '所属检测区域ID';


--
-- Name: COLUMN region_model_service.service_name; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.region_model_service.service_name IS '服务名称';


--
-- Name: COLUMN region_model_service.service_url; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.region_model_service.service_url IS 'AI模型服务请求接口URL';


--
-- Name: COLUMN region_model_service.service_type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.region_model_service.service_type IS '服务类型[FIRE:火焰烟雾检测,CROWD:人群聚集计数,SMOKE:吸烟检测等]';


--
-- Name: COLUMN region_model_service.model_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.region_model_service.model_id IS '关联的模型ID';


--
-- Name: COLUMN region_model_service.threshold; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.region_model_service.threshold IS '检测阈值';


--
-- Name: COLUMN region_model_service.request_method; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.region_model_service.request_method IS '请求方法[GET,POST]';


--
-- Name: COLUMN region_model_service.request_headers; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.region_model_service.request_headers IS '请求头（JSON格式）';


--
-- Name: COLUMN region_model_service.request_body_template; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.region_model_service.request_body_template IS '请求体模板（JSON格式，支持变量替换）';


--
-- Name: COLUMN region_model_service.timeout; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.region_model_service.timeout IS '请求超时时间（秒）';


--
-- Name: COLUMN region_model_service.is_enabled; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.region_model_service.is_enabled IS '是否启用';


--
-- Name: COLUMN region_model_service.sort_order; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.region_model_service.sort_order IS '排序顺序';


--
-- Name: region_model_service_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.region_model_service_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.region_model_service_id_seq OWNER TO postgres;

--
-- Name: region_model_service_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.region_model_service_id_seq OWNED BY public.region_model_service.id;


--
-- Name: snap_space; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.snap_space (
    id integer NOT NULL,
    space_name character varying(255) NOT NULL,
    space_code character varying(255) NOT NULL,
    bucket_name character varying(255) NOT NULL,
    save_mode smallint NOT NULL,
    save_time integer NOT NULL,
    description character varying(500),
    device_id character varying(100),
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.snap_space OWNER TO postgres;

--
-- Name: COLUMN snap_space.space_name; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.snap_space.space_name IS '空间名称';


--
-- Name: COLUMN snap_space.space_code; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.snap_space.space_code IS '空间编号（唯一标识）';


--
-- Name: COLUMN snap_space.bucket_name; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.snap_space.bucket_name IS 'MinIO bucket名称';


--
-- Name: COLUMN snap_space.save_mode; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.snap_space.save_mode IS '文件保存模式[0:标准存储,1:归档存储]';


--
-- Name: COLUMN snap_space.save_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.snap_space.save_time IS '文件保存时间[0:永久保存,>=7(单位:天)]';


--
-- Name: COLUMN snap_space.description; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.snap_space.description IS '空间描述';


--
-- Name: COLUMN snap_space.device_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.snap_space.device_id IS '关联的设备ID（一对一关系）';


--
-- Name: snap_space_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.snap_space_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.snap_space_id_seq OWNER TO postgres;

--
-- Name: snap_space_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.snap_space_id_seq OWNED BY public.snap_space.id;


--
-- Name: snap_task; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.snap_task (
    id integer NOT NULL,
    task_name character varying(255) NOT NULL,
    task_code character varying(255) NOT NULL,
    space_id integer NOT NULL,
    device_id character varying(100) NOT NULL,
    capture_type smallint NOT NULL,
    cron_expression character varying(255) NOT NULL,
    frame_skip integer NOT NULL,
    algorithm_enabled boolean NOT NULL,
    algorithm_type character varying(255),
    algorithm_model_id integer,
    algorithm_threshold double precision,
    algorithm_night_mode boolean NOT NULL,
    alarm_enabled boolean NOT NULL,
    alarm_type smallint NOT NULL,
    phone_number character varying(500),
    email character varying(500),
    notify_users text,
    notify_methods character varying(100),
    alarm_suppress_time integer NOT NULL,
    last_notify_time timestamp without time zone,
    auto_filename boolean NOT NULL,
    custom_filename_prefix character varying(255),
    status smallint NOT NULL,
    is_enabled boolean NOT NULL,
    exception_reason character varying(500),
    run_status character varying(20) NOT NULL,
    total_captures integer NOT NULL,
    last_capture_time timestamp without time zone,
    last_success_time timestamp without time zone,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.snap_task OWNER TO postgres;

--
-- Name: COLUMN snap_task.task_name; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.snap_task.task_name IS '任务名称';


--
-- Name: COLUMN snap_task.task_code; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.snap_task.task_code IS '任务编号（唯一标识）';


--
-- Name: COLUMN snap_task.space_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.snap_task.space_id IS '所属抓拍空间ID';


--
-- Name: COLUMN snap_task.device_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.snap_task.device_id IS '设备ID';


--
-- Name: COLUMN snap_task.capture_type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.snap_task.capture_type IS '抓拍类型[0:抽帧,1:抓拍]';


--
-- Name: COLUMN snap_task.cron_expression; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.snap_task.cron_expression IS 'Cron表达式';


--
-- Name: COLUMN snap_task.frame_skip; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.snap_task.frame_skip IS '抽帧间隔（每N帧抓一次）';


--
-- Name: COLUMN snap_task.algorithm_enabled; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.snap_task.algorithm_enabled IS '是否启用算法推理';


--
-- Name: COLUMN snap_task.algorithm_type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.snap_task.algorithm_type IS '算法类型[FIRE:火焰烟雾检测,CROWD:人群聚集计数,SMOKE:吸烟检测等]';


--
-- Name: COLUMN snap_task.algorithm_model_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.snap_task.algorithm_model_id IS '算法模型ID（关联AI模块的Model表）';


--
-- Name: COLUMN snap_task.algorithm_threshold; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.snap_task.algorithm_threshold IS '算法阈值';


--
-- Name: COLUMN snap_task.algorithm_night_mode; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.snap_task.algorithm_night_mode IS '是否仅夜间(23点~8点)启用算法';


--
-- Name: COLUMN snap_task.alarm_enabled; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.snap_task.alarm_enabled IS '是否启用告警';


--
-- Name: COLUMN snap_task.alarm_type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.snap_task.alarm_type IS '告警类型[0:短信告警,1:邮箱告警,2:短信+邮箱]';


--
-- Name: COLUMN snap_task.phone_number; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.snap_task.phone_number IS '告警手机号[多个用英文逗号分割]';


--
-- Name: COLUMN snap_task.email; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.snap_task.email IS '告警邮箱[多个用英文逗号分割]';


--
-- Name: COLUMN snap_task.notify_users; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.snap_task.notify_users IS '通知人列表（JSON格式，包含用户ID、姓名、手机号、邮箱等）';


--
-- Name: COLUMN snap_task.notify_methods; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.snap_task.notify_methods IS '通知方式[sms:短信,email:邮箱,app:应用内通知，多个用逗号分割]';


--
-- Name: COLUMN snap_task.alarm_suppress_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.snap_task.alarm_suppress_time IS '告警通知抑制时间（秒），防止频繁通知，默认5分钟';


--
-- Name: COLUMN snap_task.last_notify_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.snap_task.last_notify_time IS '最后通知时间';


--
-- Name: COLUMN snap_task.auto_filename; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.snap_task.auto_filename IS '是否自动命名[0:否,1:是]';


--
-- Name: COLUMN snap_task.custom_filename_prefix; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.snap_task.custom_filename_prefix IS '自定义文件前缀';


--
-- Name: COLUMN snap_task.status; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.snap_task.status IS '状态[0:正常,1:异常]';


--
-- Name: COLUMN snap_task.is_enabled; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.snap_task.is_enabled IS '是否启用[0:停用,1:启用]';


--
-- Name: COLUMN snap_task.exception_reason; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.snap_task.exception_reason IS '异常原因';


--
-- Name: COLUMN snap_task.run_status; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.snap_task.run_status IS '运行状态[running:运行中,stopped:已停止,restarting:重启中]';


--
-- Name: COLUMN snap_task.total_captures; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.snap_task.total_captures IS '总抓拍次数';


--
-- Name: COLUMN snap_task.last_capture_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.snap_task.last_capture_time IS '最后抓拍时间';


--
-- Name: COLUMN snap_task.last_success_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.snap_task.last_success_time IS '最后成功时间';


--
-- Name: snap_task_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.snap_task_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.snap_task_id_seq OWNER TO postgres;

--
-- Name: snap_task_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.snap_task_id_seq OWNED BY public.snap_task.id;


--
-- Name: alert id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alert ALTER COLUMN id SET DEFAULT nextval('public.alert_id_seq'::regclass);


--
-- Name: algorithm_model_service id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.algorithm_model_service ALTER COLUMN id SET DEFAULT nextval('public.algorithm_model_service_id_seq'::regclass);


--
-- Name: detection_region id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.detection_region ALTER COLUMN id SET DEFAULT nextval('public.detection_region_id_seq'::regclass);


--
-- Name: device_directory id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.device_directory ALTER COLUMN id SET DEFAULT nextval('public.device_directory_id_seq'::regclass);


--
-- Name: device_storage_config id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.device_storage_config ALTER COLUMN id SET DEFAULT nextval('public.device_storage_config_id_seq'::regclass);


--
-- Name: image id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.image ALTER COLUMN id SET DEFAULT nextval('public.image_id_seq'::regclass);


--
-- Name: nvr id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.nvr ALTER COLUMN id SET DEFAULT nextval('public.nvr_id_seq'::regclass);


--
-- Name: playback id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.playback ALTER COLUMN id SET DEFAULT nextval('public.playback_id_seq'::regclass);


--
-- Name: record_space id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.record_space ALTER COLUMN id SET DEFAULT nextval('public.record_space_id_seq'::regclass);


--
-- Name: region_model_service id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.region_model_service ALTER COLUMN id SET DEFAULT nextval('public.region_model_service_id_seq'::regclass);


--
-- Name: snap_space id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.snap_space ALTER COLUMN id SET DEFAULT nextval('public.snap_space_id_seq'::regclass);


--
-- Name: snap_task id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.snap_task ALTER COLUMN id SET DEFAULT nextval('public.snap_task_id_seq'::regclass);


--
-- Data for Name: alert; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.alert (id, object, event, region, information, "time", device_id, device_name, image_path, record_path) FROM stdin;
\.


--
-- Data for Name: algorithm_model_service; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.algorithm_model_service (id, task_id, service_name, service_url, service_type, model_id, threshold, request_method, request_headers, request_body_template, timeout, is_enabled, sort_order, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: detection_region; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.detection_region (id, task_id, region_name, region_type, points, image_id, algorithm_type, algorithm_model_id, algorithm_threshold, algorithm_enabled, color, opacity, is_enabled, sort_order, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: device; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.device (id, name, source, rtmp_stream, http_stream, stream, ip, port, username, password, mac, manufacturer, model, firmware_version, serial_number, hardware_id, support_move, support_zoom, nvr_id, nvr_channel, enable_forward, directory_id, created_at, updated_at, auto_snap_enabled) FROM stdin;
1764341221624781420	教室102	rtmp://localhost:1935/live/1764341221624781420	rtmp://localhost:1935/live/1764341221624781420	http://localhost:8080/live/1764341221624781420.flv	0	localhost	554	554	Zmg1451571@		EasyAIoT	Camera-EasyAIoT				f	f	\N	0	\N	6	2025-11-28 14:47:01.626613	2025-11-28 15:47:51.041247	f
1764340342947424339	食堂设备	rtmp://localhost:1935/live/1764340342947424339	rtmp://localhost:1935/live/1764340342947424339	http://localhost:8080/live/1764340342947424339.flv	0	localhost	554	554	Zmg1451571@		EasyAIoT	Camera-EasyAIoT				f	f	\N	0	\N	\N	2025-11-28 14:32:22.95178	2025-11-28 15:52:34.233585	f
1764341204704370850	大门设备	rtmp://localhost:1935/live/1764341204704370850	rtmp://localhost:1935/live/1764341204704370850	http://localhost:8080/live/1764341204704370850.flv	0	localhost	554	554	Zmg1451571@		EasyAIoT	Camera-EasyAIoT				f	f	\N	0	\N	\N	2025-11-28 14:46:44.705985	2025-11-28 16:05:00.610583	t
1764341213886942524	教室101	rtmp://localhost:1935/live/1764341213886942524	rtmp://localhost:1935/live/1764341213886942524	http://localhost:8080/live/1764341213886942524.flv	0	localhost	554				EasyAIoT	Camera-EasyAIoT				f	f	\N	0	\N	6	2025-11-28 14:46:53.888645	2025-11-28 15:05:46.011409	f
\.


--
-- Data for Name: device_directory; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.device_directory (id, name, parent_id, description, sort_order, created_at, updated_at) FROM stdin;
1	新希望小学	\N	新希望小学	0	2025-11-28 14:53:47.349435	2025-11-28 15:03:47.175503
2	马玲高中	\N	马玲高中	0	2025-11-28 14:54:03.590275	2025-11-28 15:03:54.771093
4	大门设备	1	大门设备	0	2025-11-28 15:04:46.930872	2025-11-28 15:04:46.930874
5	教室设备	1	教室设备	0	2025-11-28 15:05:00.535135	2025-11-28 15:05:00.535137
6	教学楼一层	5	教学楼一层	0	2025-11-28 15:05:28.23955	2025-11-28 15:05:28.239552
7	教学楼二层	5	教学楼二层	0	2025-11-28 15:05:38.256038	2025-11-28 15:05:38.25604
\.


--
-- Data for Name: device_storage_config; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.device_storage_config (id, device_id, snap_storage_bucket, snap_storage_max_size, snap_storage_cleanup_enabled, snap_storage_cleanup_threshold, snap_storage_cleanup_ratio, video_storage_bucket, video_storage_max_size, video_storage_cleanup_enabled, video_storage_cleanup_threshold, video_storage_cleanup_ratio, last_snap_cleanup_time, last_video_cleanup_time, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: image; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.image (id, filename, original_filename, path, width, height, created_at, device_id) FROM stdin;
\.


--
-- Data for Name: nvr; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.nvr (id, ip, username, password, name, model) FROM stdin;
\.


--
-- Data for Name: playback; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.playback (id, file_path, event_time, device_id, device_name, duration, thumbnail_path, file_size, created_at, updated_at) FROM stdin;
1	1764341204704370850/2025/11/28/1764354964856.flv	2025-11-28 00:00:00+08	1764341204704370850	大门设备	33	1764341204704370850/2025/11/28/1764354964856.jpg	8377195	2025-11-28 18:36:38.652911	2025-11-28 18:36:38.652913
2	1764341204704370850/2025/11/28/1764354998110.flv	2025-11-28 00:00:00+08	1764341204704370850	大门设备	33	1764341204704370850/2025/11/28/1764354998110.jpg	8958314	2025-11-28 18:37:11.819525	2025-11-28 18:37:11.819527
3	1764341204704370850/2025/11/28/1764355031309.flv	2025-11-28 00:00:00+08	1764341204704370850	大门设备	33	1764341204704370850/2025/11/28/1764355031309.jpg	8908048	2025-11-28 18:37:44.94748	2025-11-28 18:37:44.947482
4	1764341204704370850/2025/11/28/1764355064513.flv	2025-11-28 00:00:00+08	1764341204704370850	大门设备	33	1764341204704370850/2025/11/28/1764355064513.jpg	8885338	2025-11-28 18:38:18.07276	2025-11-28 18:38:18.072762
5	1764341204704370850/2025/11/28/1764355097716.flv	2025-11-28 00:00:00+08	1764341204704370850	大门设备	33	1764341204704370850/2025/11/28/1764355097716.jpg	8881110	2025-11-28 18:38:51.296947	2025-11-28 18:38:51.296949
6	1764341204704370850/2025/11/28/1764355164128.flv	2025-11-28 00:00:00+08	1764341204704370850	大门设备	33	1764341204704370850/2025/11/28/1764355164128.jpg	8870346	2025-11-28 18:39:57.762358	2025-11-28 18:39:57.76236
7	1764341204704370850/2025/11/28/1764355197336.flv	2025-11-28 00:00:00+08	1764341204704370850	大门设备	33	1764341204704370850/2025/11/28/1764355197336.jpg	8869808	2025-11-28 18:40:30.927653	2025-11-28 18:40:30.927655
8	1764341204704370850/2025/11/28/1764355230533.flv	2025-11-28 00:00:00+08	1764341204704370850	大门设备	33	1764341204704370850/2025/11/28/1764355230533.jpg	8864133	2025-11-28 18:41:04.098392	2025-11-28 18:41:04.098395
9	1764341204704370850/2025/11/28/1764355263742.flv	2025-11-28 00:00:00+08	1764341204704370850	大门设备	33	1764341204704370850/2025/11/28/1764355263742.jpg	8867718	2025-11-28 18:41:37.355336	2025-11-28 18:41:37.355338
10	1764341204704370850/2025/11/28/1764355296947.flv	2025-11-28 00:00:00+08	1764341204704370850	大门设备	33	1764341204704370850/2025/11/28/1764355296947.jpg	8865312	2025-11-28 18:42:10.578685	2025-11-28 18:42:10.578688
11	1764341204704370850/2025/11/28/1764355330148.flv	2025-11-28 00:00:00+08	1764341204704370850	大门设备	33	1764341204704370850/2025/11/28/1764355330148.jpg	8862995	2025-11-28 18:42:43.837968	2025-11-28 18:42:43.83797
12	1764341204704370850/2025/11/28/1764355363357.flv	2025-11-28 00:00:00+08	1764341204704370850	大门设备	33	1764341204704370850/2025/11/28/1764355363357.jpg	8864370	2025-11-28 18:43:17.011457	2025-11-28 18:43:17.011459
13	1764341204704370850/2025/11/28/1764355396561.flv	2025-11-28 00:00:00+08	1764341204704370850	大门设备	33	1764341204704370850/2025/11/28/1764355396561.jpg	8861529	2025-11-28 18:43:50.248462	2025-11-28 18:43:50.248465
14	1764341204704370850/2025/11/28/1764355496176.flv	2025-11-28 00:00:00+08	1764341204704370850	大门设备	33	1764341204704370850/2025/11/28/1764355496176.jpg	8863777	2025-11-28 18:45:29.792746	2025-11-28 18:45:29.792749
15	1764341204704370850/2025/11/28/1764355529379.flv	2025-11-28 00:00:00+08	1764341204704370850	大门设备	33	1764341204704370850/2025/11/28/1764355529379.jpg	8860658	2025-11-28 18:46:02.980162	2025-11-28 18:46:02.980165
16	1764341204704370850/2025/11/28/1764355562578.flv	2025-11-28 00:00:00+08	1764341204704370850	大门设备	33	1764341204704370850/2025/11/28/1764355562578.jpg	8862856	2025-11-28 18:46:36.294583	2025-11-28 18:46:36.294585
17	1764341204704370850/2025/11/28/1764355595794.flv	2025-11-28 00:00:00+08	1764341204704370850	大门设备	33	1764341204704370850/2025/11/28/1764355595794.jpg	8861000	2025-11-28 18:47:09.345284	2025-11-28 18:47:09.345286
18	1764341204704370850/2025/11/28/1764355628987.flv	2025-11-28 00:00:00+08	1764341204704370850	大门设备	33	1764341204704370850/2025/11/28/1764355628987.jpg	8858479	2025-11-28 18:47:42.646621	2025-11-28 18:47:42.646623
19	1764341204704370850/2025/11/28/1764355662198.flv	2025-11-28 00:00:00+08	1764341204704370850	大门设备	33	1764341204704370850/2025/11/28/1764355662198.jpg	8858104	2025-11-28 18:48:15.877241	2025-11-28 18:48:15.877244
20	1764341204704370850/2025/11/28/1764355695400.flv	2025-11-28 00:00:00+08	1764341204704370850	大门设备	33	1764341204704370850/2025/11/28/1764355695400.jpg	8860286	2025-11-28 18:48:48.98946	2025-11-28 18:48:48.989462
21	1764341204704370850/2025/11/28/1764355728610.flv	2025-11-28 00:00:00+08	1764341204704370850	大门设备	33	1764341204704370850/2025/11/28/1764355728610.jpg	8859710	2025-11-28 18:49:22.166563	2025-11-28 18:49:22.166565
22	1764341204704370850/2025/11/28/1764355761809.flv	2025-11-28 00:00:00+08	1764341204704370850	大门设备	33	1764341204704370850/2025/11/28/1764355761809.jpg	8856730	2025-11-28 18:49:55.444512	2025-11-28 18:49:55.444514
23	1764341204704370850/2025/11/28/1764355795016.flv	2025-11-28 00:00:00+08	1764341204704370850	大门设备	14	1764341204704370850/2025/11/28/1764355795016.jpg	4147652	2025-11-28 18:50:09.877229	2025-11-28 18:50:09.877231
\.


--
-- Data for Name: record_space; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.record_space (id, space_name, space_code, bucket_name, save_mode, save_time, description, device_id, created_at, updated_at) FROM stdin;
1	教室102	RECORD_E34D7323	record-space	0	0	设备 1764341221624781420 的自动创建监控录像空间	1764341221624781420	2025-11-28 15:32:55.421852	2025-11-28 15:32:55.421855
2	教室101	RECORD_A718FED6	record-space	0	0	设备 1764341213886942524 的自动创建监控录像空间	1764341213886942524	2025-11-28 15:32:55.434034	2025-11-28 15:32:55.434035
4	食堂设备	RECORD_D442AA20	record-space	0	0	设备 1764340342947424339 的自动创建监控录像空间	1764340342947424339	2025-11-28 15:32:55.45335	2025-11-28 15:52:34.23884
3	大门设备	RECORD_9977C98A	record-space	0	0	设备 1764341204704370850 的自动创建监控录像空间	1764341204704370850	2025-11-28 15:32:55.443836	2025-11-28 15:52:41.821362
\.


--
-- Data for Name: region_model_service; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.region_model_service (id, region_id, service_name, service_url, service_type, model_id, threshold, request_method, request_headers, request_body_template, timeout, is_enabled, sort_order, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: snap_space; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.snap_space (id, space_name, space_code, bucket_name, save_mode, save_time, description, device_id, created_at, updated_at) FROM stdin;
3	教室101	SPACE_780FFEA5	snap-space	0	0	设备 1764341213886942524 的自动创建抓拍空间	1764341213886942524	2025-11-28 14:46:53.899214	2025-11-28 14:46:53.899215
4	教室102	SPACE_058CA8B6	snap-space	0	0	设备 1764341221624781420 的自动创建抓拍空间	1764341221624781420	2025-11-28 14:47:01.644924	2025-11-28 14:47:01.644926
1	食堂设备	SPACE_E593A3AE	snap-space	0	0	设备 1764340342947424339 的自动创建抓拍空间	1764340342947424339	2025-11-28 14:32:22.972691	2025-11-28 15:52:34.234758
2	大门设备	SPACE_E8384A8F	snap-space	0	0	设备 1764341204704370850 的自动创建抓拍空间	1764341204704370850	2025-11-28 14:46:44.72674	2025-11-28 15:52:41.809909
\.


--
-- Data for Name: snap_task; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.snap_task (id, task_name, task_code, space_id, device_id, capture_type, cron_expression, frame_skip, algorithm_enabled, algorithm_type, algorithm_model_id, algorithm_threshold, algorithm_night_mode, alarm_enabled, alarm_type, phone_number, email, notify_users, notify_methods, alarm_suppress_time, last_notify_time, auto_filename, custom_filename_prefix, status, is_enabled, exception_reason, run_status, total_captures, last_capture_time, last_success_time, created_at, updated_at) FROM stdin;
\.


--
-- Name: alert_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.alert_id_seq', 1, false);


--
-- Name: algorithm_model_service_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.algorithm_model_service_id_seq', 1, false);


--
-- Name: detection_region_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.detection_region_id_seq', 1, false);


--
-- Name: device_directory_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.device_directory_id_seq', 7, true);


--
-- Name: device_storage_config_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.device_storage_config_id_seq', 1, false);


--
-- Name: image_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.image_id_seq', 1, false);


--
-- Name: nvr_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.nvr_id_seq', 1, false);


--
-- Name: playback_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.playback_id_seq', 23, true);


--
-- Name: record_space_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.record_space_id_seq', 4, true);


--
-- Name: region_model_service_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.region_model_service_id_seq', 1, false);


--
-- Name: snap_space_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.snap_space_id_seq', 4, true);


--
-- Name: snap_task_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.snap_task_id_seq', 1, false);


--
-- Name: alert alert_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alert
    ADD CONSTRAINT alert_pkey PRIMARY KEY (id);


--
-- Name: algorithm_model_service algorithm_model_service_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.algorithm_model_service
    ADD CONSTRAINT algorithm_model_service_pkey PRIMARY KEY (id);


--
-- Name: detection_region detection_region_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.detection_region
    ADD CONSTRAINT detection_region_pkey PRIMARY KEY (id);


--
-- Name: device_directory device_directory_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.device_directory
    ADD CONSTRAINT device_directory_pkey PRIMARY KEY (id);


--
-- Name: device device_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.device
    ADD CONSTRAINT device_pkey PRIMARY KEY (id);


--
-- Name: device_storage_config device_storage_config_device_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.device_storage_config
    ADD CONSTRAINT device_storage_config_device_id_key UNIQUE (device_id);


--
-- Name: device_storage_config device_storage_config_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.device_storage_config
    ADD CONSTRAINT device_storage_config_pkey PRIMARY KEY (id);


--
-- Name: image image_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.image
    ADD CONSTRAINT image_pkey PRIMARY KEY (id);


--
-- Name: nvr nvr_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.nvr
    ADD CONSTRAINT nvr_pkey PRIMARY KEY (id);


--
-- Name: playback playback_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.playback
    ADD CONSTRAINT playback_pkey PRIMARY KEY (id);


--
-- Name: record_space record_space_device_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.record_space
    ADD CONSTRAINT record_space_device_id_key UNIQUE (device_id);


--
-- Name: record_space record_space_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.record_space
    ADD CONSTRAINT record_space_pkey PRIMARY KEY (id);


--
-- Name: record_space record_space_space_code_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.record_space
    ADD CONSTRAINT record_space_space_code_key UNIQUE (space_code);


--
-- Name: region_model_service region_model_service_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.region_model_service
    ADD CONSTRAINT region_model_service_pkey PRIMARY KEY (id);


--
-- Name: snap_space snap_space_device_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.snap_space
    ADD CONSTRAINT snap_space_device_id_key UNIQUE (device_id);


--
-- Name: snap_space snap_space_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.snap_space
    ADD CONSTRAINT snap_space_pkey PRIMARY KEY (id);


--
-- Name: snap_space snap_space_space_code_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.snap_space
    ADD CONSTRAINT snap_space_space_code_key UNIQUE (space_code);


--
-- Name: snap_task snap_task_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.snap_task
    ADD CONSTRAINT snap_task_pkey PRIMARY KEY (id);


--
-- Name: snap_task snap_task_task_code_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.snap_task
    ADD CONSTRAINT snap_task_task_code_key UNIQUE (task_code);


--
-- Name: algorithm_model_service algorithm_model_service_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.algorithm_model_service
    ADD CONSTRAINT algorithm_model_service_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.snap_task(id) ON DELETE CASCADE;


--
-- Name: detection_region detection_region_image_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.detection_region
    ADD CONSTRAINT detection_region_image_id_fkey FOREIGN KEY (image_id) REFERENCES public.image(id) ON DELETE SET NULL;


--
-- Name: detection_region detection_region_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.detection_region
    ADD CONSTRAINT detection_region_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.snap_task(id) ON DELETE CASCADE;


--
-- Name: device device_directory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.device
    ADD CONSTRAINT device_directory_id_fkey FOREIGN KEY (directory_id) REFERENCES public.device_directory(id) ON DELETE SET NULL;


--
-- Name: device_directory device_directory_parent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.device_directory
    ADD CONSTRAINT device_directory_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.device_directory(id) ON DELETE CASCADE;


--
-- Name: device device_nvr_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.device
    ADD CONSTRAINT device_nvr_id_fkey FOREIGN KEY (nvr_id) REFERENCES public.nvr(id) ON DELETE CASCADE;


--
-- Name: device_storage_config device_storage_config_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.device_storage_config
    ADD CONSTRAINT device_storage_config_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.device(id) ON DELETE CASCADE;


--
-- Name: image image_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.image
    ADD CONSTRAINT image_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.device(id);


--
-- Name: record_space record_space_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.record_space
    ADD CONSTRAINT record_space_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.device(id) ON DELETE SET NULL;


--
-- Name: region_model_service region_model_service_region_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.region_model_service
    ADD CONSTRAINT region_model_service_region_id_fkey FOREIGN KEY (region_id) REFERENCES public.detection_region(id) ON DELETE CASCADE;


--
-- Name: snap_space snap_space_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.snap_space
    ADD CONSTRAINT snap_space_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.device(id) ON DELETE SET NULL;


--
-- Name: snap_task snap_task_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.snap_task
    ADD CONSTRAINT snap_task_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.device(id) ON DELETE CASCADE;


--
-- Name: snap_task snap_task_space_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.snap_task
    ADD CONSTRAINT snap_task_space_id_fkey FOREIGN KEY (space_id) REFERENCES public.snap_space(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict k88Kj3l92Z5fxPjrzFejWOwz4JNiTHf0VeLTgzfncbJ4fF4Wu4geZdRPnODzQ6x

