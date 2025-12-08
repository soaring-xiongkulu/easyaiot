--
-- PostgreSQL database dump
--

\restrict r9sy6otTd8HloIJRblk3DYPxonvDA9tbNNE9kCTxk6hSstzNahgEQiflUMSrqp2

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

DROP DATABASE IF EXISTS "iot-video20";
--
-- Name: iot-video20; Type: DATABASE; Schema: -; Owner: -
--

CREATE DATABASE "iot-video20" WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'en_US.utf8';


\unrestrict r9sy6otTd8HloIJRblk3DYPxonvDA9tbNNE9kCTxk6hSstzNahgEQiflUMSrqp2
\encoding SQL_ASCII
\connect -reuse-previous=on "dbname='iot-video20'"
\restrict r9sy6otTd8HloIJRblk3DYPxonvDA9tbNNE9kCTxk6hSstzNahgEQiflUMSrqp2

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
-- Name: alert; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: alert_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.alert_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: alert_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.alert_id_seq OWNED BY public.alert.id;


--
-- Name: algorithm_model_service; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: COLUMN algorithm_model_service.task_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_model_service.task_id IS '所属任务ID';


--
-- Name: COLUMN algorithm_model_service.service_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_model_service.service_name IS '服务名称';


--
-- Name: COLUMN algorithm_model_service.service_url; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_model_service.service_url IS 'AI模型服务请求接口URL';


--
-- Name: COLUMN algorithm_model_service.service_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_model_service.service_type IS '服务类型[FIRE:火焰烟雾检测,CROWD:人群聚集计数,SMOKE:吸烟检测等]';


--
-- Name: COLUMN algorithm_model_service.model_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_model_service.model_id IS '关联的模型ID';


--
-- Name: COLUMN algorithm_model_service.threshold; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_model_service.threshold IS '检测阈值';


--
-- Name: COLUMN algorithm_model_service.request_method; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_model_service.request_method IS '请求方法[GET,POST]';


--
-- Name: COLUMN algorithm_model_service.request_headers; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_model_service.request_headers IS '请求头（JSON格式）';


--
-- Name: COLUMN algorithm_model_service.request_body_template; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_model_service.request_body_template IS '请求体模板（JSON格式，支持变量替换）';


--
-- Name: COLUMN algorithm_model_service.timeout; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_model_service.timeout IS '请求超时时间（秒）';


--
-- Name: COLUMN algorithm_model_service.is_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_model_service.is_enabled IS '是否启用';


--
-- Name: COLUMN algorithm_model_service.sort_order; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_model_service.sort_order IS '排序顺序';


--
-- Name: algorithm_model_service_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.algorithm_model_service_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: algorithm_model_service_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.algorithm_model_service_id_seq OWNED BY public.algorithm_model_service.id;


--
-- Name: algorithm_task; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.algorithm_task (
    id integer NOT NULL,
    task_name character varying(255) NOT NULL,
    task_code character varying(255) NOT NULL,
    task_type character varying(20) NOT NULL,
    model_ids text,
    model_names text,
    extract_interval integer NOT NULL,
    rtmp_input_url character varying(500),
    rtmp_output_url character varying(500),
    tracking_enabled boolean NOT NULL,
    tracking_similarity_threshold double precision NOT NULL,
    tracking_max_age integer NOT NULL,
    tracking_smooth_alpha double precision NOT NULL,
    alert_event_enabled boolean NOT NULL,
    alert_notification_enabled boolean NOT NULL,
    alert_notification_config text,
    alarm_suppress_time integer NOT NULL,
    last_notify_time timestamp without time zone,
    space_id integer,
    cron_expression character varying(255),
    frame_skip integer NOT NULL,
    status smallint NOT NULL,
    is_enabled boolean NOT NULL,
    run_status character varying(20) NOT NULL,
    exception_reason character varying(500),
    service_server_ip character varying(45),
    service_port integer,
    service_process_id integer,
    service_last_heartbeat timestamp without time zone,
    service_log_path character varying(500),
    total_frames integer NOT NULL,
    total_detections integer NOT NULL,
    total_captures integer NOT NULL,
    last_process_time timestamp without time zone,
    last_success_time timestamp without time zone,
    last_capture_time timestamp without time zone,
    description character varying(500),
    defense_mode character varying(20) NOT NULL,
    defense_schedule text,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: COLUMN algorithm_task.task_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.task_name IS '任务名称';


--
-- Name: COLUMN algorithm_task.task_code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.task_code IS '任务编号（唯一标识）';


--
-- Name: COLUMN algorithm_task.task_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.task_type IS '任务类型[realtime:实时算法任务,snap:抓拍算法任务]';


--
-- Name: COLUMN algorithm_task.model_ids; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.model_ids IS '关联的模型ID列表（JSON格式，如[1,2,3]）';


--
-- Name: COLUMN algorithm_task.model_names; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.model_names IS '关联的模型名称列表（逗号分隔，冗余字段，用于快速显示）';


--
-- Name: COLUMN algorithm_task.extract_interval; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.extract_interval IS '抽帧间隔（每N帧抽一次，仅实时算法任务）';


--
-- Name: COLUMN algorithm_task.rtmp_input_url; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.rtmp_input_url IS 'RTMP输入流地址（仅实时算法任务）';


--
-- Name: COLUMN algorithm_task.rtmp_output_url; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.rtmp_output_url IS 'RTMP输出流地址（仅实时算法任务）';


--
-- Name: COLUMN algorithm_task.tracking_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.tracking_enabled IS '是否启用目标追踪';


--
-- Name: COLUMN algorithm_task.tracking_similarity_threshold; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.tracking_similarity_threshold IS '追踪相似度阈值';


--
-- Name: COLUMN algorithm_task.tracking_max_age; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.tracking_max_age IS '追踪目标最大存活帧数';


--
-- Name: COLUMN algorithm_task.tracking_smooth_alpha; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.tracking_smooth_alpha IS '追踪平滑系数';


--
-- Name: COLUMN algorithm_task.alert_event_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.alert_event_enabled IS '是否启用告警事件';


--
-- Name: COLUMN algorithm_task.alert_notification_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.alert_notification_enabled IS '是否启用告警通知';


--
-- Name: COLUMN algorithm_task.alert_notification_config; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.alert_notification_config IS '告警通知配置（JSON格式，包含通知渠道和模板配置，格式：{"channels": [{"method": "sms", "template_id": "xxx", "template_name": "xxx"}, ...]}）';


--
-- Name: COLUMN algorithm_task.alarm_suppress_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.alarm_suppress_time IS '告警通知抑制时间（秒），防止频繁通知，默认5分钟';


--
-- Name: COLUMN algorithm_task.last_notify_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.last_notify_time IS '最后通知时间';


--
-- Name: COLUMN algorithm_task.space_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.space_id IS '所属抓拍空间ID（仅抓拍算法任务）';


--
-- Name: COLUMN algorithm_task.cron_expression; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.cron_expression IS 'Cron表达式（仅抓拍算法任务）';


--
-- Name: COLUMN algorithm_task.frame_skip; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.frame_skip IS '抽帧间隔（每N帧抓一次，仅抓拍算法任务）';


--
-- Name: COLUMN algorithm_task.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.status IS '状态[0:正常,1:异常]';


--
-- Name: COLUMN algorithm_task.is_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.is_enabled IS '是否启用[0:停用,1:启用]';


--
-- Name: COLUMN algorithm_task.run_status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.run_status IS '运行状态[running:运行中,stopped:已停止,restarting:重启中]';


--
-- Name: COLUMN algorithm_task.exception_reason; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.exception_reason IS '异常原因';


--
-- Name: COLUMN algorithm_task.service_server_ip; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.service_server_ip IS '服务运行服务器IP';


--
-- Name: COLUMN algorithm_task.service_port; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.service_port IS '服务端口';


--
-- Name: COLUMN algorithm_task.service_process_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.service_process_id IS '服务进程ID';


--
-- Name: COLUMN algorithm_task.service_last_heartbeat; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.service_last_heartbeat IS '服务最后心跳时间';


--
-- Name: COLUMN algorithm_task.service_log_path; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.service_log_path IS '服务日志路径';


--
-- Name: COLUMN algorithm_task.total_frames; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.total_frames IS '总处理帧数';


--
-- Name: COLUMN algorithm_task.total_detections; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.total_detections IS '总检测次数';


--
-- Name: COLUMN algorithm_task.total_captures; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.total_captures IS '总抓拍次数（仅抓拍算法任务）';


--
-- Name: COLUMN algorithm_task.last_process_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.last_process_time IS '最后处理时间';


--
-- Name: COLUMN algorithm_task.last_success_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.last_success_time IS '最后成功时间';


--
-- Name: COLUMN algorithm_task.last_capture_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.last_capture_time IS '最后抓拍时间（仅抓拍算法任务）';


--
-- Name: COLUMN algorithm_task.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.description IS '任务描述';


--
-- Name: COLUMN algorithm_task.defense_mode; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.defense_mode IS '布防模式[full:全防模式,half:半防模式,day:白天模式,night:夜间模式]';


--
-- Name: COLUMN algorithm_task.defense_schedule; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.defense_schedule IS '布防时段配置（JSON格式，7天×24小时的二维数组）';


--
-- Name: algorithm_task_device; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.algorithm_task_device (
    task_id integer NOT NULL,
    device_id character varying(100) NOT NULL,
    created_at timestamp without time zone
);


--
-- Name: COLUMN algorithm_task_device.task_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task_device.task_id IS '算法任务ID';


--
-- Name: COLUMN algorithm_task_device.device_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task_device.device_id IS '摄像头ID';


--
-- Name: COLUMN algorithm_task_device.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task_device.created_at IS '创建时间';


--
-- Name: algorithm_task_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.algorithm_task_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: algorithm_task_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.algorithm_task_id_seq OWNED BY public.algorithm_task.id;


--
-- Name: detection_region; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: COLUMN detection_region.task_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.detection_region.task_id IS '所属任务ID';


--
-- Name: COLUMN detection_region.region_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.detection_region.region_name IS '区域名称';


--
-- Name: COLUMN detection_region.region_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.detection_region.region_type IS '区域类型[polygon:多边形,rectangle:矩形]';


--
-- Name: COLUMN detection_region.points; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.detection_region.points IS '区域坐标点(JSON格式，归一化坐标0-1)';


--
-- Name: COLUMN detection_region.image_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.detection_region.image_id IS '参考图片ID（用于绘制区域的基准图片）';


--
-- Name: COLUMN detection_region.algorithm_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.detection_region.algorithm_type IS '绑定的算法类型[FIRE:火焰烟雾检测,CROWD:人群聚集计数,SMOKE:吸烟检测等]';


--
-- Name: COLUMN detection_region.algorithm_model_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.detection_region.algorithm_model_id IS '绑定的算法模型ID';


--
-- Name: COLUMN detection_region.algorithm_threshold; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.detection_region.algorithm_threshold IS '算法阈值';


--
-- Name: COLUMN detection_region.algorithm_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.detection_region.algorithm_enabled IS '是否启用该区域的算法';


--
-- Name: COLUMN detection_region.color; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.detection_region.color IS '区域显示颜色';


--
-- Name: COLUMN detection_region.opacity; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.detection_region.opacity IS '区域透明度(0-1)';


--
-- Name: COLUMN detection_region.is_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.detection_region.is_enabled IS '是否启用该区域';


--
-- Name: COLUMN detection_region.sort_order; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.detection_region.sort_order IS '排序顺序';


--
-- Name: detection_region_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.detection_region_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: detection_region_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.detection_region_id_seq OWNED BY public.detection_region.id;


--
-- Name: device; Type: TABLE; Schema: public; Owner: -
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
    auto_snap_enabled boolean DEFAULT false NOT NULL,
    cover_image_path character varying(500)
);


--
-- Name: COLUMN device.directory_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.directory_id IS '所属目录ID';


--
-- Name: COLUMN device.auto_snap_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.auto_snap_enabled IS '是否开启自动抓拍[默认不开启]';


--
-- Name: device_detection_region; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.device_detection_region (
    id integer NOT NULL,
    device_id character varying(100) NOT NULL,
    region_name character varying(255) NOT NULL,
    region_type character varying(50) NOT NULL,
    points text NOT NULL,
    image_id integer,
    color character varying(20) NOT NULL,
    opacity double precision NOT NULL,
    is_enabled boolean NOT NULL,
    sort_order integer NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    model_ids text
);


--
-- Name: COLUMN device_detection_region.device_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_detection_region.device_id IS '设备ID';


--
-- Name: COLUMN device_detection_region.region_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_detection_region.region_name IS '区域名称';


--
-- Name: COLUMN device_detection_region.region_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_detection_region.region_type IS '区域类型[polygon:多边形,line:线条]';


--
-- Name: COLUMN device_detection_region.points; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_detection_region.points IS '区域坐标点(JSON格式，归一化坐标0-1)';


--
-- Name: COLUMN device_detection_region.image_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_detection_region.image_id IS '参考图片ID（用于绘制区域的基准图片）';


--
-- Name: COLUMN device_detection_region.color; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_detection_region.color IS '区域显示颜色';


--
-- Name: COLUMN device_detection_region.opacity; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_detection_region.opacity IS '区域透明度(0-1)';


--
-- Name: COLUMN device_detection_region.is_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_detection_region.is_enabled IS '是否启用该区域';


--
-- Name: COLUMN device_detection_region.sort_order; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_detection_region.sort_order IS '排序顺序';


--
-- Name: device_detection_region_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.device_detection_region_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: device_detection_region_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.device_detection_region_id_seq OWNED BY public.device_detection_region.id;


--
-- Name: device_directory; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: COLUMN device_directory.name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_directory.name IS '目录名称';


--
-- Name: COLUMN device_directory.parent_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_directory.parent_id IS '父目录ID，NULL表示根目录';


--
-- Name: COLUMN device_directory.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_directory.description IS '目录描述';


--
-- Name: COLUMN device_directory.sort_order; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_directory.sort_order IS '排序顺序';


--
-- Name: device_directory_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.device_directory_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: device_directory_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.device_directory_id_seq OWNED BY public.device_directory.id;


--
-- Name: device_storage_config; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: COLUMN device_storage_config.device_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_storage_config.device_id IS '设备ID';


--
-- Name: COLUMN device_storage_config.snap_storage_bucket; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_storage_config.snap_storage_bucket IS '抓拍图片存储bucket名称';


--
-- Name: COLUMN device_storage_config.snap_storage_max_size; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_storage_config.snap_storage_max_size IS '抓拍图片存储最大空间（字节），0表示不限制';


--
-- Name: COLUMN device_storage_config.snap_storage_cleanup_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_storage_config.snap_storage_cleanup_enabled IS '是否启用抓拍图片自动清理';


--
-- Name: COLUMN device_storage_config.snap_storage_cleanup_threshold; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_storage_config.snap_storage_cleanup_threshold IS '抓拍图片清理阈值（使用率超过此值触发清理）';


--
-- Name: COLUMN device_storage_config.snap_storage_cleanup_ratio; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_storage_config.snap_storage_cleanup_ratio IS '抓拍图片清理比例（清理最老的30%）';


--
-- Name: COLUMN device_storage_config.video_storage_bucket; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_storage_config.video_storage_bucket IS '录像存储bucket名称';


--
-- Name: COLUMN device_storage_config.video_storage_max_size; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_storage_config.video_storage_max_size IS '录像存储最大空间（字节），0表示不限制';


--
-- Name: COLUMN device_storage_config.video_storage_cleanup_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_storage_config.video_storage_cleanup_enabled IS '是否启用录像自动清理';


--
-- Name: COLUMN device_storage_config.video_storage_cleanup_threshold; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_storage_config.video_storage_cleanup_threshold IS '录像清理阈值（使用率超过此值触发清理）';


--
-- Name: COLUMN device_storage_config.video_storage_cleanup_ratio; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_storage_config.video_storage_cleanup_ratio IS '录像清理比例（清理最老的30%）';


--
-- Name: COLUMN device_storage_config.last_snap_cleanup_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_storage_config.last_snap_cleanup_time IS '最后抓拍图片清理时间';


--
-- Name: COLUMN device_storage_config.last_video_cleanup_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_storage_config.last_video_cleanup_time IS '最后录像清理时间';


--
-- Name: device_storage_config_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.device_storage_config_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: device_storage_config_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.device_storage_config_id_seq OWNED BY public.device_storage_config.id;


--
-- Name: frame_extractor; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.frame_extractor (
    id integer NOT NULL,
    extractor_name character varying(255) NOT NULL,
    extractor_code character varying(255) NOT NULL,
    extractor_type character varying(50) NOT NULL,
    "interval" integer NOT NULL,
    description character varying(500),
    is_enabled boolean NOT NULL,
    status character varying(20) NOT NULL,
    server_ip character varying(50),
    port integer,
    process_id integer,
    last_heartbeat timestamp without time zone,
    log_path character varying(500),
    task_id integer,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: COLUMN frame_extractor.extractor_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.frame_extractor.extractor_name IS '抽帧器名称';


--
-- Name: COLUMN frame_extractor.extractor_code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.frame_extractor.extractor_code IS '抽帧器编号（唯一标识）';


--
-- Name: COLUMN frame_extractor.extractor_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.frame_extractor.extractor_type IS '抽帧类型[interval:按间隔,time:按时间]';


--
-- Name: COLUMN frame_extractor."interval"; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.frame_extractor."interval" IS '抽帧间隔（每N帧抽一次，或每N秒抽一次）';


--
-- Name: COLUMN frame_extractor.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.frame_extractor.description IS '描述';


--
-- Name: COLUMN frame_extractor.is_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.frame_extractor.is_enabled IS '是否启用';


--
-- Name: COLUMN frame_extractor.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.frame_extractor.status IS '运行状态[running:运行中,stopped:已停止,error:错误]';


--
-- Name: COLUMN frame_extractor.server_ip; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.frame_extractor.server_ip IS '部署的服务器IP';


--
-- Name: COLUMN frame_extractor.port; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.frame_extractor.port IS '服务端口';


--
-- Name: COLUMN frame_extractor.process_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.frame_extractor.process_id IS '进程ID';


--
-- Name: COLUMN frame_extractor.last_heartbeat; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.frame_extractor.last_heartbeat IS '最后上报时间';


--
-- Name: COLUMN frame_extractor.log_path; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.frame_extractor.log_path IS '日志文件路径';


--
-- Name: COLUMN frame_extractor.task_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.frame_extractor.task_id IS '关联的算法任务ID';


--
-- Name: frame_extractor_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.frame_extractor_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: frame_extractor_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.frame_extractor_id_seq OWNED BY public.frame_extractor.id;


--
-- Name: image; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: image_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.image_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: image_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.image_id_seq OWNED BY public.image.id;


--
-- Name: nvr; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.nvr (
    id integer NOT NULL,
    ip character varying(45) NOT NULL,
    username character varying(100),
    password character varying(100),
    name character varying(100),
    model character varying(100)
);


--
-- Name: nvr_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.nvr_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: nvr_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.nvr_id_seq OWNED BY public.nvr.id;


--
-- Name: playback; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: playback_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.playback_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: playback_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.playback_id_seq OWNED BY public.playback.id;


--
-- Name: pusher; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.pusher (
    id integer NOT NULL,
    pusher_name character varying(255) NOT NULL,
    pusher_code character varying(255) NOT NULL,
    video_stream_enabled boolean NOT NULL,
    video_stream_url character varying(500),
    device_rtmp_mapping text,
    video_stream_format character varying(50) NOT NULL,
    video_stream_quality character varying(50) NOT NULL,
    event_alert_enabled boolean NOT NULL,
    event_alert_url character varying(500),
    event_alert_method character varying(20) NOT NULL,
    event_alert_format character varying(50) NOT NULL,
    event_alert_headers text,
    event_alert_template text,
    description character varying(500),
    is_enabled boolean NOT NULL,
    status character varying(20) NOT NULL,
    server_ip character varying(50),
    port integer,
    process_id integer,
    last_heartbeat timestamp without time zone,
    log_path character varying(500),
    task_id integer,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: COLUMN pusher.pusher_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pusher.pusher_name IS '推送器名称';


--
-- Name: COLUMN pusher.pusher_code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pusher.pusher_code IS '推送器编号（唯一标识）';


--
-- Name: COLUMN pusher.video_stream_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pusher.video_stream_enabled IS '是否启用推送视频流';


--
-- Name: COLUMN pusher.video_stream_url; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pusher.video_stream_url IS '视频流推送地址（RTMP/RTSP等，单摄像头时使用）';


--
-- Name: COLUMN pusher.device_rtmp_mapping; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pusher.device_rtmp_mapping IS '多摄像头RTMP推送映射（JSON格式，device_id -> rtmp_url）';


--
-- Name: COLUMN pusher.video_stream_format; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pusher.video_stream_format IS '视频流格式[rtmp:RTMP,rtsp:RTSP,webrtc:WebRTC]';


--
-- Name: COLUMN pusher.video_stream_quality; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pusher.video_stream_quality IS '视频流质量[low:低,medium:中,high:高]';


--
-- Name: COLUMN pusher.event_alert_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pusher.event_alert_enabled IS '是否启用推送事件告警';


--
-- Name: COLUMN pusher.event_alert_url; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pusher.event_alert_url IS '事件告警推送地址（HTTP/WebSocket/Kafka等）';


--
-- Name: COLUMN pusher.event_alert_method; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pusher.event_alert_method IS '事件告警推送方式[http:HTTP,websocket:WebSocket,kafka:Kafka]';


--
-- Name: COLUMN pusher.event_alert_format; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pusher.event_alert_format IS '事件告警数据格式[json:JSON,xml:XML]';


--
-- Name: COLUMN pusher.event_alert_headers; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pusher.event_alert_headers IS '事件告警请求头（JSON格式）';


--
-- Name: COLUMN pusher.event_alert_template; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pusher.event_alert_template IS '事件告警数据模板（JSON格式，支持变量替换）';


--
-- Name: COLUMN pusher.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pusher.description IS '描述';


--
-- Name: COLUMN pusher.is_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pusher.is_enabled IS '是否启用';


--
-- Name: COLUMN pusher.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pusher.status IS '运行状态[running:运行中,stopped:已停止,error:错误]';


--
-- Name: COLUMN pusher.server_ip; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pusher.server_ip IS '部署的服务器IP';


--
-- Name: COLUMN pusher.port; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pusher.port IS '服务端口';


--
-- Name: COLUMN pusher.process_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pusher.process_id IS '进程ID';


--
-- Name: COLUMN pusher.last_heartbeat; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pusher.last_heartbeat IS '最后上报时间';


--
-- Name: COLUMN pusher.log_path; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pusher.log_path IS '日志文件路径';


--
-- Name: COLUMN pusher.task_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pusher.task_id IS '关联的算法任务ID';


--
-- Name: pusher_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.pusher_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: pusher_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.pusher_id_seq OWNED BY public.pusher.id;


--
-- Name: record_space; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: COLUMN record_space.space_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.record_space.space_name IS '空间名称';


--
-- Name: COLUMN record_space.space_code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.record_space.space_code IS '空间编号（唯一标识）';


--
-- Name: COLUMN record_space.bucket_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.record_space.bucket_name IS 'MinIO bucket名称';


--
-- Name: COLUMN record_space.save_mode; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.record_space.save_mode IS '文件保存模式[0:标准存储,1:归档存储]';


--
-- Name: COLUMN record_space.save_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.record_space.save_time IS '文件保存时间[0:永久保存,>=7(单位:天)]';


--
-- Name: COLUMN record_space.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.record_space.description IS '空间描述';


--
-- Name: COLUMN record_space.device_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.record_space.device_id IS '关联的设备ID（一对一关系）';


--
-- Name: record_space_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.record_space_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: record_space_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.record_space_id_seq OWNED BY public.record_space.id;


--
-- Name: region_model_service; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: COLUMN region_model_service.region_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.region_model_service.region_id IS '所属检测区域ID';


--
-- Name: COLUMN region_model_service.service_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.region_model_service.service_name IS '服务名称';


--
-- Name: COLUMN region_model_service.service_url; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.region_model_service.service_url IS 'AI模型服务请求接口URL';


--
-- Name: COLUMN region_model_service.service_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.region_model_service.service_type IS '服务类型[FIRE:火焰烟雾检测,CROWD:人群聚集计数,SMOKE:吸烟检测等]';


--
-- Name: COLUMN region_model_service.model_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.region_model_service.model_id IS '关联的模型ID';


--
-- Name: COLUMN region_model_service.threshold; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.region_model_service.threshold IS '检测阈值';


--
-- Name: COLUMN region_model_service.request_method; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.region_model_service.request_method IS '请求方法[GET,POST]';


--
-- Name: COLUMN region_model_service.request_headers; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.region_model_service.request_headers IS '请求头（JSON格式）';


--
-- Name: COLUMN region_model_service.request_body_template; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.region_model_service.request_body_template IS '请求体模板（JSON格式，支持变量替换）';


--
-- Name: COLUMN region_model_service.timeout; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.region_model_service.timeout IS '请求超时时间（秒）';


--
-- Name: COLUMN region_model_service.is_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.region_model_service.is_enabled IS '是否启用';


--
-- Name: COLUMN region_model_service.sort_order; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.region_model_service.sort_order IS '排序顺序';


--
-- Name: region_model_service_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.region_model_service_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: region_model_service_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.region_model_service_id_seq OWNED BY public.region_model_service.id;


--
-- Name: snap_space; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: COLUMN snap_space.space_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_space.space_name IS '空间名称';


--
-- Name: COLUMN snap_space.space_code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_space.space_code IS '空间编号（唯一标识）';


--
-- Name: COLUMN snap_space.bucket_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_space.bucket_name IS 'MinIO bucket名称';


--
-- Name: COLUMN snap_space.save_mode; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_space.save_mode IS '文件保存模式[0:标准存储,1:归档存储]';


--
-- Name: COLUMN snap_space.save_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_space.save_time IS '文件保存时间[0:永久保存,>=7(单位:天)]';


--
-- Name: COLUMN snap_space.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_space.description IS '空间描述';


--
-- Name: COLUMN snap_space.device_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_space.device_id IS '关联的设备ID（一对一关系）';


--
-- Name: snap_space_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.snap_space_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: snap_space_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.snap_space_id_seq OWNED BY public.snap_space.id;


--
-- Name: snap_task; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.snap_task (
    id integer NOT NULL,
    task_name character varying(255) NOT NULL,
    task_code character varying(255) NOT NULL,
    space_id integer NOT NULL,
    device_id character varying(100) NOT NULL,
    pusher_id integer,
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


--
-- Name: COLUMN snap_task.task_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_task.task_name IS '任务名称';


--
-- Name: COLUMN snap_task.task_code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_task.task_code IS '任务编号（唯一标识）';


--
-- Name: COLUMN snap_task.space_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_task.space_id IS '所属抓拍空间ID';


--
-- Name: COLUMN snap_task.device_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_task.device_id IS '设备ID';


--
-- Name: COLUMN snap_task.pusher_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_task.pusher_id IS '关联的推送器ID';


--
-- Name: COLUMN snap_task.capture_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_task.capture_type IS '抓拍类型[0:抽帧,1:抓拍]';


--
-- Name: COLUMN snap_task.cron_expression; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_task.cron_expression IS 'Cron表达式';


--
-- Name: COLUMN snap_task.frame_skip; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_task.frame_skip IS '抽帧间隔（每N帧抓一次）';


--
-- Name: COLUMN snap_task.algorithm_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_task.algorithm_enabled IS '是否启用算法推理';


--
-- Name: COLUMN snap_task.algorithm_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_task.algorithm_type IS '算法类型[FIRE:火焰烟雾检测,CROWD:人群聚集计数,SMOKE:吸烟检测等]';


--
-- Name: COLUMN snap_task.algorithm_model_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_task.algorithm_model_id IS '算法模型ID（关联AI模块的Model表）';


--
-- Name: COLUMN snap_task.algorithm_threshold; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_task.algorithm_threshold IS '算法阈值';


--
-- Name: COLUMN snap_task.algorithm_night_mode; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_task.algorithm_night_mode IS '是否仅夜间(23点~8点)启用算法';


--
-- Name: COLUMN snap_task.alarm_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_task.alarm_enabled IS '是否启用告警';


--
-- Name: COLUMN snap_task.alarm_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_task.alarm_type IS '告警类型[0:短信告警,1:邮箱告警,2:短信+邮箱]';


--
-- Name: COLUMN snap_task.phone_number; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_task.phone_number IS '告警手机号[多个用英文逗号分割]';


--
-- Name: COLUMN snap_task.email; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_task.email IS '告警邮箱[多个用英文逗号分割]';


--
-- Name: COLUMN snap_task.notify_users; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_task.notify_users IS '通知人列表（JSON格式，包含用户ID、姓名、手机号、邮箱等）';


--
-- Name: COLUMN snap_task.notify_methods; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_task.notify_methods IS '通知方式[sms:短信,email:邮箱,app:应用内通知，多个用逗号分割]';


--
-- Name: COLUMN snap_task.alarm_suppress_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_task.alarm_suppress_time IS '告警通知抑制时间（秒），防止频繁通知，默认5分钟';


--
-- Name: COLUMN snap_task.last_notify_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_task.last_notify_time IS '最后通知时间';


--
-- Name: COLUMN snap_task.auto_filename; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_task.auto_filename IS '是否自动命名[0:否,1:是]';


--
-- Name: COLUMN snap_task.custom_filename_prefix; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_task.custom_filename_prefix IS '自定义文件前缀';


--
-- Name: COLUMN snap_task.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_task.status IS '状态[0:正常,1:异常]';


--
-- Name: COLUMN snap_task.is_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_task.is_enabled IS '是否启用[0:停用,1:启用]';


--
-- Name: COLUMN snap_task.exception_reason; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_task.exception_reason IS '异常原因';


--
-- Name: COLUMN snap_task.run_status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_task.run_status IS '运行状态[running:运行中,stopped:已停止,restarting:重启中]';


--
-- Name: COLUMN snap_task.total_captures; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_task.total_captures IS '总抓拍次数';


--
-- Name: COLUMN snap_task.last_capture_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_task.last_capture_time IS '最后抓拍时间';


--
-- Name: COLUMN snap_task.last_success_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_task.last_success_time IS '最后成功时间';


--
-- Name: snap_task_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.snap_task_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: snap_task_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.snap_task_id_seq OWNED BY public.snap_task.id;


--
-- Name: sorter; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sorter (
    id integer NOT NULL,
    sorter_name character varying(255) NOT NULL,
    sorter_code character varying(255) NOT NULL,
    sorter_type character varying(50) NOT NULL,
    sort_order character varying(10) NOT NULL,
    description character varying(500),
    is_enabled boolean NOT NULL,
    status character varying(20) NOT NULL,
    server_ip character varying(50),
    port integer,
    process_id integer,
    last_heartbeat timestamp without time zone,
    log_path character varying(500),
    task_id integer,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: COLUMN sorter.sorter_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sorter.sorter_name IS '排序器名称';


--
-- Name: COLUMN sorter.sorter_code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sorter.sorter_code IS '排序器编号（唯一标识）';


--
-- Name: COLUMN sorter.sorter_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sorter.sorter_type IS '排序类型[confidence:置信度,time:时间,score:分数]';


--
-- Name: COLUMN sorter.sort_order; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sorter.sort_order IS '排序顺序[asc:升序,desc:降序]';


--
-- Name: COLUMN sorter.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sorter.description IS '描述';


--
-- Name: COLUMN sorter.is_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sorter.is_enabled IS '是否启用';


--
-- Name: COLUMN sorter.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sorter.status IS '运行状态[running:运行中,stopped:已停止,error:错误]';


--
-- Name: COLUMN sorter.server_ip; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sorter.server_ip IS '部署的服务器IP';


--
-- Name: COLUMN sorter.port; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sorter.port IS '服务端口';


--
-- Name: COLUMN sorter.process_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sorter.process_id IS '进程ID';


--
-- Name: COLUMN sorter.last_heartbeat; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sorter.last_heartbeat IS '最后上报时间';


--
-- Name: COLUMN sorter.log_path; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sorter.log_path IS '日志文件路径';


--
-- Name: COLUMN sorter.task_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sorter.task_id IS '关联的算法任务ID';


--
-- Name: sorter_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sorter_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sorter_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sorter_id_seq OWNED BY public.sorter.id;


--
-- Name: tracking_target; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tracking_target (
    id integer NOT NULL,
    task_id integer NOT NULL,
    device_id character varying(100) NOT NULL,
    device_name character varying(255),
    track_id integer NOT NULL,
    class_id integer,
    class_name character varying(100),
    first_seen_time timestamp without time zone NOT NULL,
    last_seen_time timestamp without time zone,
    leave_time timestamp without time zone,
    duration double precision,
    first_seen_frame integer,
    last_seen_frame integer,
    total_detections integer NOT NULL,
    information text,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: COLUMN tracking_target.task_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.tracking_target.task_id IS '所属算法任务ID';


--
-- Name: COLUMN tracking_target.device_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.tracking_target.device_id IS '设备ID';


--
-- Name: COLUMN tracking_target.device_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.tracking_target.device_name IS '设备名称';


--
-- Name: COLUMN tracking_target.track_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.tracking_target.track_id IS '追踪ID（同一任务内唯一）';


--
-- Name: COLUMN tracking_target.class_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.tracking_target.class_id IS '类别ID';


--
-- Name: COLUMN tracking_target.class_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.tracking_target.class_name IS '类别名称';


--
-- Name: COLUMN tracking_target.first_seen_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.tracking_target.first_seen_time IS '首次出现时间';


--
-- Name: COLUMN tracking_target.last_seen_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.tracking_target.last_seen_time IS '最后出现时间';


--
-- Name: COLUMN tracking_target.leave_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.tracking_target.leave_time IS '离开时间';


--
-- Name: COLUMN tracking_target.duration; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.tracking_target.duration IS '停留时长（秒）';


--
-- Name: COLUMN tracking_target.first_seen_frame; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.tracking_target.first_seen_frame IS '首次出现帧号';


--
-- Name: COLUMN tracking_target.last_seen_frame; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.tracking_target.last_seen_frame IS '最后出现帧号';


--
-- Name: COLUMN tracking_target.total_detections; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.tracking_target.total_detections IS '总检测次数';


--
-- Name: COLUMN tracking_target.information; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.tracking_target.information IS '详细信息（JSON格式）';


--
-- Name: tracking_target_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tracking_target_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tracking_target_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.tracking_target_id_seq OWNED BY public.tracking_target.id;


--
-- Name: alert id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alert ALTER COLUMN id SET DEFAULT nextval('public.alert_id_seq'::regclass);


--
-- Name: algorithm_model_service id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.algorithm_model_service ALTER COLUMN id SET DEFAULT nextval('public.algorithm_model_service_id_seq'::regclass);


--
-- Name: algorithm_task id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.algorithm_task ALTER COLUMN id SET DEFAULT nextval('public.algorithm_task_id_seq'::regclass);


--
-- Name: detection_region id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.detection_region ALTER COLUMN id SET DEFAULT nextval('public.detection_region_id_seq'::regclass);


--
-- Name: device_detection_region id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.device_detection_region ALTER COLUMN id SET DEFAULT nextval('public.device_detection_region_id_seq'::regclass);


--
-- Name: device_directory id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.device_directory ALTER COLUMN id SET DEFAULT nextval('public.device_directory_id_seq'::regclass);


--
-- Name: device_storage_config id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.device_storage_config ALTER COLUMN id SET DEFAULT nextval('public.device_storage_config_id_seq'::regclass);


--
-- Name: frame_extractor id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.frame_extractor ALTER COLUMN id SET DEFAULT nextval('public.frame_extractor_id_seq'::regclass);


--
-- Name: image id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.image ALTER COLUMN id SET DEFAULT nextval('public.image_id_seq'::regclass);


--
-- Name: nvr id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nvr ALTER COLUMN id SET DEFAULT nextval('public.nvr_id_seq'::regclass);


--
-- Name: playback id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.playback ALTER COLUMN id SET DEFAULT nextval('public.playback_id_seq'::regclass);


--
-- Name: pusher id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pusher ALTER COLUMN id SET DEFAULT nextval('public.pusher_id_seq'::regclass);


--
-- Name: record_space id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.record_space ALTER COLUMN id SET DEFAULT nextval('public.record_space_id_seq'::regclass);


--
-- Name: region_model_service id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.region_model_service ALTER COLUMN id SET DEFAULT nextval('public.region_model_service_id_seq'::regclass);


--
-- Name: snap_space id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.snap_space ALTER COLUMN id SET DEFAULT nextval('public.snap_space_id_seq'::regclass);


--
-- Name: snap_task id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.snap_task ALTER COLUMN id SET DEFAULT nextval('public.snap_task_id_seq'::regclass);


--
-- Name: sorter id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sorter ALTER COLUMN id SET DEFAULT nextval('public.sorter_id_seq'::regclass);


--
-- Name: tracking_target id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tracking_target ALTER COLUMN id SET DEFAULT nextval('public.tracking_target_id_seq'::regclass);


--
-- Data for Name: alert; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.alert (id, object, event, region, information, "time", device_id, device_name, image_path, record_path) FROM stdin;
1	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.837182343006134, "bbox": [450, 160, 509, 210], "frame_number": 7710, "first_seen_time": "2025-12-07T13:28:51.473577", "duration": 0.0}	2025-12-07 13:28:51+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_1_1764341204704370850_20251207133231.jpg	\N
2	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7922524809837341, "bbox": [229, 155, 287, 214], "frame_number": 7710, "first_seen_time": "2025-12-07T13:28:51.473577", "duration": 0.0}	2025-12-07 13:28:51+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_2_1764341204704370850_20251207133231.jpg	\N
3	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5151602029800415, "bbox": [105, 51, 151, 77], "frame_number": 7710, "first_seen_time": "2025-12-07T13:28:51.473577", "duration": 0.0}	2025-12-07 13:28:51+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_3_1764341204704370850_20251207133231.jpg	\N
4	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.777413547039032, "bbox": [464, 251, 603, 354], "frame_number": 7785, "first_seen_time": "2025-12-07T13:28:56.819034", "duration": 0.0}	2025-12-07 13:28:56+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_4_1764341204704370850_20251207133232.jpg	\N
5	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7013187408447266, "bbox": [306, 171, 360, 232], "frame_number": 7785, "first_seen_time": "2025-12-07T13:28:56.819034", "duration": 0.0}	2025-12-07 13:28:56+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_5_1764341204704370850_20251207133232.jpg	\N
6	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5083580017089844, "bbox": [323, 53, 349, 76], "frame_number": 7785, "first_seen_time": "2025-12-07T13:28:56.819034", "duration": 0.0}	2025-12-07 13:28:56+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_6_1764341204704370850_20251207133232.jpg	\N
7	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.42127254605293274, "bbox": [389, 59, 417, 81], "frame_number": 7785, "first_seen_time": "2025-12-07T13:28:56.819034", "duration": 0.0}	2025-12-07 13:28:56+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_7_1764341204704370850_20251207133233.jpg	\N
8	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.2954353094100952, "bbox": [288, 40, 307, 58], "frame_number": 7785, "first_seen_time": "2025-12-07T13:28:56.819034", "duration": 0.0}	2025-12-07 13:28:56+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_8_1764341204704370850_20251207133233.jpg	\N
9	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.8269328474998474, "bbox": [419, 191, 505, 280], "frame_number": 7860, "first_seen_time": "2025-12-07T13:29:02.096414", "duration": 0.0}	2025-12-07 13:29:02+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_9_1764341204704370850_20251207133233.jpg	\N
10	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5376191139221191, "bbox": [136, 17, 158, 31], "frame_number": 7860, "first_seen_time": "2025-12-07T13:29:02.096414", "duration": 0.0}	2025-12-07 13:29:02+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_10_1764341204704370850_20251207133233.jpg	\N
11	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5282626748085022, "bbox": [74, 17, 111, 39], "frame_number": 7860, "first_seen_time": "2025-12-07T13:29:02.096414", "duration": 0.0}	2025-12-07 13:29:02+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_11_1764341204704370850_20251207133234.jpg	\N
12	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7331858277320862, "bbox": [456, 114, 505, 150], "frame_number": 7930, "first_seen_time": "2025-12-07T13:29:07.124682", "duration": 0.0}	2025-12-07 13:29:07+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_12_1764341204704370850_20251207133234.jpg	\N
13	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7015420198440552, "bbox": [53, 23, 97, 60], "frame_number": 7930, "first_seen_time": "2025-12-07T13:29:07.124682", "duration": 0.0}	2025-12-07 13:29:07+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_13_1764341204704370850_20251207133234.jpg	\N
14	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6887617707252502, "bbox": [372, 60, 399, 85], "frame_number": 7930, "first_seen_time": "2025-12-07T13:29:07.124682", "duration": 0.0}	2025-12-07 13:29:07+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_14_1764341204704370850_20251207133234.jpg	\N
15	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5050116777420044, "bbox": [133, 6, 177, 27], "frame_number": 7930, "first_seen_time": "2025-12-07T13:29:07.124682", "duration": 0.0}	2025-12-07 13:29:07+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_15_1764341204704370850_20251207133235.jpg	\N
16	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3447834253311157, "bbox": [354, 13, 372, 30], "frame_number": 7930, "first_seen_time": "2025-12-07T13:29:07.124682", "duration": 0.0}	2025-12-07 13:29:07+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_16_1764341204704370850_20251207133235.jpg	\N
17	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.28253963589668274, "bbox": [391, 29, 410, 45], "frame_number": 7930, "first_seen_time": "2025-12-07T13:29:07.124682", "duration": 0.0}	2025-12-07 13:29:07+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_17_1764341204704370850_20251207133235.jpg	\N
18	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7751627564430237, "bbox": [384, 99, 428, 137], "frame_number": 8000, "first_seen_time": "2025-12-07T13:29:12.190666", "duration": 0.0}	2025-12-07 13:29:12+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_18_1764341204704370850_20251207133235.jpg	\N
19	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.45381850004196167, "bbox": [0, 42, 26, 70], "frame_number": 8000, "first_seen_time": "2025-12-07T13:29:12.190666", "duration": 0.0}	2025-12-07 13:29:12+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_19_1764341204704370850_20251207133236.jpg	\N
20	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.44683945178985596, "bbox": [44, 44, 75, 65], "frame_number": 8000, "first_seen_time": "2025-12-07T13:29:12.190666", "duration": 0.0}	2025-12-07 13:29:12+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_20_1764341204704370850_20251207133236.jpg	\N
21	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3854762315750122, "bbox": [328, 41, 351, 57], "frame_number": 8000, "first_seen_time": "2025-12-07T13:29:12.190666", "duration": 0.0}	2025-12-07 13:29:12+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_21_1764341204704370850_20251207133236.jpg	\N
22	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.32208600640296936, "bbox": [302, 15, 318, 29], "frame_number": 8000, "first_seen_time": "2025-12-07T13:29:12.190666", "duration": 0.0}	2025-12-07 13:29:12+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_22_1764341204704370850_20251207133237.jpg	\N
23	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7633663415908813, "bbox": [430, 209, 524, 297], "frame_number": 8075, "first_seen_time": "2025-12-07T13:29:17.407850", "duration": 0.0}	2025-12-07 13:29:17+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_23_1764341204704370850_20251207133237.jpg	\N
24	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3270970284938812, "bbox": [362, 35, 384, 52], "frame_number": 8075, "first_seen_time": "2025-12-07T13:29:17.407850", "duration": 0.0}	2025-12-07 13:29:17+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_24_1764341204704370850_20251207133237.jpg	\N
25	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.30224743485450745, "bbox": [0, 43, 27, 67], "frame_number": 8075, "first_seen_time": "2025-12-07T13:29:17.407850", "duration": 0.0}	2025-12-07 13:29:17+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_25_1764341204704370850_20251207133237.jpg	\N
26	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.2724442183971405, "bbox": [100, 28, 126, 43], "frame_number": 8075, "first_seen_time": "2025-12-07T13:29:17.407850", "duration": 0.0}	2025-12-07 13:29:17+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_26_1764341204704370850_20251207133238.jpg	\N
27	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.8059914112091064, "bbox": [414, 146, 468, 199], "frame_number": 8150, "first_seen_time": "2025-12-07T13:29:22.638858", "duration": 0.0}	2025-12-07 13:29:22+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_27_1764341204704370850_20251207133238.jpg	\N
28	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7261171340942383, "bbox": [372, 47, 398, 73], "frame_number": 8225, "first_seen_time": "2025-12-07T13:29:27.900953", "duration": 0.0}	2025-12-07 13:29:27+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_28_1764341204704370850_20251207133238.jpg	\N
29	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6163268685340881, "bbox": [250, 101, 291, 140], "frame_number": 8225, "first_seen_time": "2025-12-07T13:29:27.900953", "duration": 0.0}	2025-12-07 13:29:27+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_29_1764341204704370850_20251207133238.jpg	\N
30	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4815664291381836, "bbox": [80, 41, 129, 82], "frame_number": 8225, "first_seen_time": "2025-12-07T13:29:27.900953", "duration": 0.0}	2025-12-07 13:29:27+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_30_1764341204704370850_20251207133239.jpg	\N
31	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.454437255859375, "bbox": [199, 6, 222, 24], "frame_number": 8225, "first_seen_time": "2025-12-07T13:29:27.900953", "duration": 0.0}	2025-12-07 13:29:27+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_31_1764341204704370850_20251207133239.jpg	\N
32	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3444811999797821, "bbox": [143, 7, 162, 19], "frame_number": 8225, "first_seen_time": "2025-12-07T13:29:27.900953", "duration": 0.0}	2025-12-07 13:29:27+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_32_1764341204704370850_20251207133239.jpg	\N
33	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.2670177221298218, "bbox": [366, 10, 384, 27], "frame_number": 8225, "first_seen_time": "2025-12-07T13:29:27.900953", "duration": 0.0}	2025-12-07 13:29:27+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_33_1764341204704370850_20251207133239.jpg	\N
34	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6987364292144775, "bbox": [98, 37, 132, 56], "frame_number": 8300, "first_seen_time": "2025-12-07T13:29:33.099609", "duration": 0.0}	2025-12-07 13:29:33+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_34_1764341204704370850_20251207133240.jpg	\N
35	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6896671652793884, "bbox": [222, 70, 257, 98], "frame_number": 8300, "first_seen_time": "2025-12-07T13:29:33.099609", "duration": 0.0}	2025-12-07 13:29:33+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_35_1764341204704370850_20251207133240.jpg	\N
36	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4431343674659729, "bbox": [377, 83, 409, 113], "frame_number": 8300, "first_seen_time": "2025-12-07T13:29:33.099609", "duration": 0.0}	2025-12-07 13:29:33+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_36_1764341204704370850_20251207133240.jpg	\N
37	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.34908321499824524, "bbox": [110, 17, 135, 30], "frame_number": 8300, "first_seen_time": "2025-12-07T13:29:33.099609", "duration": 0.0}	2025-12-07 13:29:33+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_37_1764341204704370850_20251207133240.jpg	\N
38	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7648135423660278, "bbox": [101, 165, 188, 235], "frame_number": 8375, "first_seen_time": "2025-12-07T13:29:38.391771", "duration": 0.0}	2025-12-07 13:29:38+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_38_1764341204704370850_20251207133241.jpg	\N
39	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7597672343254089, "bbox": [286, 152, 340, 212], "frame_number": 8375, "first_seen_time": "2025-12-07T13:29:38.391771", "duration": 0.0}	2025-12-07 13:29:38+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_39_1764341204704370850_20251207133241.jpg	\N
40	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.67081218957901, "bbox": [105, 15, 133, 33], "frame_number": 8375, "first_seen_time": "2025-12-07T13:29:38.391771", "duration": 0.0}	2025-12-07 13:29:38+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_40_1764341204704370850_20251207133241.jpg	\N
41	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6584497690200806, "bbox": [275, 52, 301, 76], "frame_number": 8375, "first_seen_time": "2025-12-07T13:29:38.391771", "duration": 0.0}	2025-12-07 13:29:38+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_41_1764341204704370850_20251207133241.jpg	\N
42	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6380091309547424, "bbox": [252, 97, 294, 131], "frame_number": 8375, "first_seen_time": "2025-12-07T13:29:38.391771", "duration": 0.0}	2025-12-07 13:29:38+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_42_1764341204704370850_20251207133242.jpg	\N
43	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.40039950609207153, "bbox": [0, 73, 30, 101], "frame_number": 8375, "first_seen_time": "2025-12-07T13:29:38.391771", "duration": 0.0}	2025-12-07 13:29:38+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_43_1764341204704370850_20251207133242.jpg	\N
44	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.39417120814323425, "bbox": [65, 33, 103, 55], "frame_number": 8375, "first_seen_time": "2025-12-07T13:29:38.391771", "duration": 0.0}	2025-12-07 13:29:38+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_44_1764341204704370850_20251207133242.jpg	\N
45	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.282621830701828, "bbox": [130, 8, 155, 22], "frame_number": 8375, "first_seen_time": "2025-12-07T13:29:38.391771", "duration": 0.0}	2025-12-07 13:29:38+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_45_1764341204704370850_20251207133242.jpg	\N
46	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.2767898738384247, "bbox": [297, 27, 317, 41], "frame_number": 8375, "first_seen_time": "2025-12-07T13:29:38.391771", "duration": 0.0}	2025-12-07 13:29:38+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_46_1764341204704370850_20251207133243.jpg	\N
47	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.27086034417152405, "bbox": [325, 21, 347, 48], "frame_number": 8375, "first_seen_time": "2025-12-07T13:29:38.391771", "duration": 0.0}	2025-12-07 13:29:38+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_47_1764341204704370850_20251207133243.jpg	\N
48	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.8360335230827332, "bbox": [456, 248, 562, 352], "frame_number": 8455, "first_seen_time": "2025-12-07T13:29:44.094497", "duration": 0.0}	2025-12-07 13:29:44+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_48_1764341204704370850_20251207133243.jpg	\N
49	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.669833779335022, "bbox": [221, 163, 276, 216], "frame_number": 8455, "first_seen_time": "2025-12-07T13:29:44.094497", "duration": 0.0}	2025-12-07 13:29:44+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_49_1764341204704370850_20251207133243.jpg	\N
50	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6273726224899292, "bbox": [384, 100, 428, 134], "frame_number": 8455, "first_seen_time": "2025-12-07T13:29:44.094497", "duration": 0.0}	2025-12-07 13:29:44+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_50_1764341204704370850_20251207133244.jpg	\N
51	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6246422529220581, "bbox": [325, 90, 358, 121], "frame_number": 8455, "first_seen_time": "2025-12-07T13:29:44.094497", "duration": 0.0}	2025-12-07 13:29:44+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_51_1764341204704370850_20251207133244.jpg	\N
52	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6160898804664612, "bbox": [158, 28, 184, 47], "frame_number": 8455, "first_seen_time": "2025-12-07T13:29:44.094497", "duration": 0.0}	2025-12-07 13:29:44+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_52_1764341204704370850_20251207133244.jpg	\N
53	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5153685212135315, "bbox": [40, 76, 90, 111], "frame_number": 8455, "first_seen_time": "2025-12-07T13:29:44.094497", "duration": 0.0}	2025-12-07 13:29:44+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_53_1764341204704370850_20251207133244.jpg	\N
54	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4412367641925812, "bbox": [288, 52, 309, 69], "frame_number": 8455, "first_seen_time": "2025-12-07T13:29:44.094497", "duration": 0.0}	2025-12-07 13:29:44+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_54_1764341204704370850_20251207133245.jpg	\N
55	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.41698354482650757, "bbox": [128, 14, 151, 33], "frame_number": 8455, "first_seen_time": "2025-12-07T13:29:44.094497", "duration": 0.0}	2025-12-07 13:29:44+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_55_1764341204704370850_20251207133245.jpg	\N
56	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.26372814178466797, "bbox": [39, 55, 79, 83], "frame_number": 8455, "first_seen_time": "2025-12-07T13:29:44.094497", "duration": 0.0}	2025-12-07 13:29:44+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_56_1764341204704370850_20251207133245.jpg	\N
57	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6465013027191162, "bbox": [97, 35, 131, 58], "frame_number": 8530, "first_seen_time": "2025-12-07T13:29:49.406018", "duration": 0.0}	2025-12-07 13:29:49+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_57_1764341204704370850_20251207133245.jpg	\N
58	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6355658769607544, "bbox": [394, 101, 434, 137], "frame_number": 8530, "first_seen_time": "2025-12-07T13:29:49.406018", "duration": 0.0}	2025-12-07 13:29:49+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_58_1764341204704370850_20251207133246.jpg	\N
59	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5857651233673096, "bbox": [320, 126, 365, 171], "frame_number": 8530, "first_seen_time": "2025-12-07T13:29:49.406018", "duration": 0.0}	2025-12-07 13:29:49+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_59_1764341204704370850_20251207133246.jpg	\N
60	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.536616861820221, "bbox": [0, 42, 27, 65], "frame_number": 8530, "first_seen_time": "2025-12-07T13:29:49.406018", "duration": 0.0}	2025-12-07 13:29:49+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_60_1764341204704370850_20251207133246.jpg	\N
61	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.29931876063346863, "bbox": [108, 13, 135, 30], "frame_number": 8530, "first_seen_time": "2025-12-07T13:29:49.406018", "duration": 0.0}	2025-12-07 13:29:49+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_61_1764341204704370850_20251207133246.jpg	\N
62	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.651646614074707, "bbox": [372, 42, 394, 63], "frame_number": 8600, "first_seen_time": "2025-12-07T13:29:54.398443", "duration": 0.0}	2025-12-07 13:29:54+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_62_1764341204704370850_20251207133247.jpg	\N
63	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6415706276893616, "bbox": [160, 120, 222, 171], "frame_number": 8600, "first_seen_time": "2025-12-07T13:29:54.398443", "duration": 0.0}	2025-12-07 13:29:54+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_63_1764341204704370850_20251207133247.jpg	\N
64	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5464015007019043, "bbox": [258, 30, 282, 51], "frame_number": 8600, "first_seen_time": "2025-12-07T13:29:54.398443", "duration": 0.0}	2025-12-07 13:29:54+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_64_1764341204704370850_20251207133247.jpg	\N
65	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5290099382400513, "bbox": [300, 22, 318, 35], "frame_number": 8600, "first_seen_time": "2025-12-07T13:29:54.398443", "duration": 0.0}	2025-12-07 13:29:54+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_65_1764341204704370850_20251207133247.jpg	\N
66	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4731430113315582, "bbox": [403, 93, 441, 127], "frame_number": 8600, "first_seen_time": "2025-12-07T13:29:54.398443", "duration": 0.0}	2025-12-07 13:29:54+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_66_1764341204704370850_20251207133248.jpg	\N
67	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.45958447456359863, "bbox": [184, 19, 207, 36], "frame_number": 8600, "first_seen_time": "2025-12-07T13:29:54.398443", "duration": 0.0}	2025-12-07 13:29:54+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_67_1764341204704370850_20251207133248.jpg	\N
68	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.443628191947937, "bbox": [314, 169, 374, 234], "frame_number": 8600, "first_seen_time": "2025-12-07T13:29:54.398443", "duration": 0.0}	2025-12-07 13:29:54+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_68_1764341204704370850_20251207133248.jpg	\N
69	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4596070349216461, "bbox": [363, 31, 381, 47], "frame_number": 8675, "first_seen_time": "2025-12-07T13:29:59.720092", "duration": 0.0}	2025-12-07 13:29:59+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_69_1764341204704370850_20251207133248.jpg	\N
70	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6628457307815552, "bbox": [410, 104, 449, 145], "frame_number": 8750, "first_seen_time": "2025-12-07T13:30:05.056894", "duration": 0.0}	2025-12-07 13:30:05+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_70_1764341204704370850_20251207133249.jpg	\N
71	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6505993604660034, "bbox": [317, 107, 357, 150], "frame_number": 8750, "first_seen_time": "2025-12-07T13:30:05.056894", "duration": 0.0}	2025-12-07 13:30:05+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_71_1764341204704370850_20251207133249.jpg	\N
72	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3742513656616211, "bbox": [267, 76, 296, 106], "frame_number": 8750, "first_seen_time": "2025-12-07T13:30:05.056894", "duration": 0.0}	2025-12-07 13:30:05+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_72_1764341204704370850_20251207133249.jpg	\N
73	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5552597641944885, "bbox": [97, 48, 136, 78], "frame_number": 8820, "first_seen_time": "2025-12-07T13:30:10.089235", "duration": 0.0}	2025-12-07 13:30:10+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_73_1764341204704370850_20251207133249.jpg	\N
74	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4303619861602783, "bbox": [369, 40, 395, 64], "frame_number": 8820, "first_seen_time": "2025-12-07T13:30:10.089235", "duration": 0.0}	2025-12-07 13:30:10+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_74_1764341204704370850_20251207133250.jpg	\N
75	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4110962450504303, "bbox": [135, 4, 160, 22], "frame_number": 8820, "first_seen_time": "2025-12-07T13:30:10.089235", "duration": 0.0}	2025-12-07 13:30:10+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_75_1764341204704370850_20251207133250.jpg	\N
76	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.34019482135772705, "bbox": [323, 21, 345, 39], "frame_number": 8820, "first_seen_time": "2025-12-07T13:30:10.089235", "duration": 0.0}	2025-12-07 13:30:10+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_76_1764341204704370850_20251207133250.jpg	\N
77	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.813818633556366, "bbox": [359, 30, 383, 50], "frame_number": 8895, "first_seen_time": "2025-12-07T13:30:15.369675", "duration": 0.0}	2025-12-07 13:30:15+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_77_1764341204704370850_20251207133251.jpg	\N
78	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7439049482345581, "bbox": [50, 29, 80, 50], "frame_number": 8895, "first_seen_time": "2025-12-07T13:30:15.369675", "duration": 0.0}	2025-12-07 13:30:15+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_78_1764341204704370850_20251207133251.jpg	\N
79	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.669030487537384, "bbox": [323, 45, 344, 62], "frame_number": 8895, "first_seen_time": "2025-12-07T13:30:15.369675", "duration": 0.0}	2025-12-07 13:30:15+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_79_1764341204704370850_20251207133251.jpg	\N
80	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6317571401596069, "bbox": [394, 118, 439, 161], "frame_number": 8895, "first_seen_time": "2025-12-07T13:30:15.369675", "duration": 0.0}	2025-12-07 13:30:15+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_80_1764341204704370850_20251207133251.jpg	\N
81	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5707947015762329, "bbox": [39, 74, 89, 105], "frame_number": 8895, "first_seen_time": "2025-12-07T13:30:15.369675", "duration": 0.0}	2025-12-07 13:30:15+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_81_1764341204704370850_20251207133252.jpg	\N
82	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5701909065246582, "bbox": [117, 9, 155, 34], "frame_number": 8895, "first_seen_time": "2025-12-07T13:30:15.369675", "duration": 0.0}	2025-12-07 13:30:15+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_82_1764341204704370850_20251207133252.jpg	\N
83	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5260851979255676, "bbox": [408, 49, 434, 72], "frame_number": 8895, "first_seen_time": "2025-12-07T13:30:15.369675", "duration": 0.0}	2025-12-07 13:30:15+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_83_1764341204704370850_20251207133252.jpg	\N
84	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.42186981439590454, "bbox": [572, 246, 639, 334], "frame_number": 8895, "first_seen_time": "2025-12-07T13:30:15.369675", "duration": 0.0}	2025-12-07 13:30:15+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_84_1764341204704370850_20251207133252.jpg	\N
85	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4375660717487335, "bbox": [88, 33, 117, 50], "frame_number": 8975, "first_seen_time": "2025-12-07T13:30:21.155285", "duration": 0.0}	2025-12-07 13:30:21+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_85_1764341204704370850_20251207133253.jpg	\N
86	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3409107029438019, "bbox": [30, 39, 66, 56], "frame_number": 8975, "first_seen_time": "2025-12-07T13:30:21.155285", "duration": 0.0}	2025-12-07 13:30:21+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_86_1764341204704370850_20251207133253.jpg	\N
87	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5835882425308228, "bbox": [450, 258, 572, 353], "frame_number": 9055, "first_seen_time": "2025-12-07T13:30:26.873323", "duration": 0.0}	2025-12-07 13:30:26+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_87_1764341204704370850_20251207133253.jpg	\N
88	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3395187556743622, "bbox": [326, 28, 349, 48], "frame_number": 9055, "first_seen_time": "2025-12-07T13:30:26.873323", "duration": 0.0}	2025-12-07 13:30:26+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_88_1764341204704370850_20251207133253.jpg	\N
89	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.28564321994781494, "bbox": [0, 102, 15, 139], "frame_number": 9055, "first_seen_time": "2025-12-07T13:30:26.873323", "duration": 0.0}	2025-12-07 13:30:26+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_89_1764341204704370850_20251207133254.jpg	\N
90	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.8568890690803528, "bbox": [444, 228, 537, 318], "frame_number": 9125, "first_seen_time": "2025-12-07T13:30:31.870803", "duration": 0.0}	2025-12-07 13:30:31+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_90_1764341204704370850_20251207133254.jpg	\N
91	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.31298908591270447, "bbox": [0, 72, 33, 108], "frame_number": 9125, "first_seen_time": "2025-12-07T13:30:31.870803", "duration": 0.0}	2025-12-07 13:30:31+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_91_1764341204704370850_20251207133254.jpg	\N
92	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7765348553657532, "bbox": [379, 64, 410, 94], "frame_number": 9200, "first_seen_time": "2025-12-07T13:30:37.216445", "duration": 0.0}	2025-12-07 13:30:37+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_92_1764341204704370850_20251207133254.jpg	\N
93	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6575173139572144, "bbox": [214, 157, 276, 215], "frame_number": 9200, "first_seen_time": "2025-12-07T13:30:37.216445", "duration": 0.0}	2025-12-07 13:30:37+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_93_1764341204704370850_20251207133255.jpg	\N
94	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5292938351631165, "bbox": [126, 30, 161, 63], "frame_number": 9200, "first_seen_time": "2025-12-07T13:30:37.216445", "duration": 0.0}	2025-12-07 13:30:37+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_94_1764341204704370850_20251207133255.jpg	\N
95	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.49607613682746887, "bbox": [368, 16, 385, 31], "frame_number": 9200, "first_seen_time": "2025-12-07T13:30:37.216445", "duration": 0.0}	2025-12-07 13:30:37+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_95_1764341204704370850_20251207133255.jpg	\N
96	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.2897726595401764, "bbox": [213, 2, 233, 17], "frame_number": 9200, "first_seen_time": "2025-12-07T13:30:37.216445", "duration": 0.0}	2025-12-07 13:30:37+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_96_1764341204704370850_20251207133255.jpg	\N
97	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7052082419395447, "bbox": [389, 114, 432, 156], "frame_number": 9275, "first_seen_time": "2025-12-07T13:30:42.540771", "duration": 0.0}	2025-12-07 13:30:42+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_97_1764341204704370850_20251207133256.jpg	\N
98	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6246564984321594, "bbox": [192, 99, 235, 137], "frame_number": 9275, "first_seen_time": "2025-12-07T13:30:42.540771", "duration": 0.0}	2025-12-07 13:30:42+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_98_1764341204704370850_20251207133256.jpg	\N
99	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5613352656364441, "bbox": [135, 23, 160, 42], "frame_number": 9275, "first_seen_time": "2025-12-07T13:30:42.540771", "duration": 0.0}	2025-12-07 13:30:42+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_99_1764341204704370850_20251207133256.jpg	\N
100	truck	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.2864144444465637, "bbox": [192, 99, 235, 137], "frame_number": 9275, "first_seen_time": "2025-12-07T13:30:42.540771", "duration": 0.0}	2025-12-07 13:30:42+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_100_1764341204704370850_20251207133256.jpg	\N
101	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7415173053741455, "bbox": [251, 85, 290, 120], "frame_number": 9345, "first_seen_time": "2025-12-07T13:30:47.612371", "duration": 0.0}	2025-12-07 13:30:47+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_101_1764341204704370850_20251207133257.jpg	\N
102	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6623492240905762, "bbox": [91, 42, 122, 61], "frame_number": 9345, "first_seen_time": "2025-12-07T13:30:47.612371", "duration": 0.0}	2025-12-07 13:30:47+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_102_1764341204704370850_20251207133257.jpg	\N
103	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.490004301071167, "bbox": [204, 177, 274, 245], "frame_number": 9345, "first_seen_time": "2025-12-07T13:30:47.612371", "duration": 0.0}	2025-12-07 13:30:47+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_103_1764341204704370850_20251207133257.jpg	\N
104	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.46570685505867004, "bbox": [142, 4, 168, 21], "frame_number": 9345, "first_seen_time": "2025-12-07T13:30:47.612371", "duration": 0.0}	2025-12-07 13:30:47+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_104_1764341204704370850_20251207133258.jpg	\N
105	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.41368913650512695, "bbox": [289, 41, 311, 56], "frame_number": 9345, "first_seen_time": "2025-12-07T13:30:47.612371", "duration": 0.0}	2025-12-07 13:30:47+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_105_1764341204704370850_20251207133258.jpg	\N
106	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.39848393201828003, "bbox": [367, 44, 387, 61], "frame_number": 9345, "first_seen_time": "2025-12-07T13:30:47.612371", "duration": 0.0}	2025-12-07 13:30:47+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_106_1764341204704370850_20251207133258.jpg	\N
107	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.26218947768211365, "bbox": [122, 23, 142, 36], "frame_number": 9345, "first_seen_time": "2025-12-07T13:30:47.612371", "duration": 0.0}	2025-12-07 13:30:47+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_107_1764341204704370850_20251207133258.jpg	\N
108	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6456024050712585, "bbox": [307, 292, 402, 355], "frame_number": 9415, "first_seen_time": "2025-12-07T13:30:52.610759", "duration": 0.0}	2025-12-07 13:30:52+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_108_1764341204704370850_20251207133259.jpg	\N
109	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.643828809261322, "bbox": [454, 298, 556, 353], "frame_number": 9415, "first_seen_time": "2025-12-07T13:30:52.610759", "duration": 0.0}	2025-12-07 13:30:52+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_109_1764341204704370850_20251207133259.jpg	\N
110	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.49160486459732056, "bbox": [165, 30, 186, 46], "frame_number": 9415, "first_seen_time": "2025-12-07T13:30:52.610759", "duration": 0.0}	2025-12-07 13:30:52+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_110_1764341204704370850_20251207133259.jpg	\N
111	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.445623517036438, "bbox": [381, 59, 409, 87], "frame_number": 9415, "first_seen_time": "2025-12-07T13:30:52.610759", "duration": 0.0}	2025-12-07 13:30:52+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_111_1764341204704370850_20251207133259.jpg	\N
112	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4133417010307312, "bbox": [243, 136, 287, 180], "frame_number": 9415, "first_seen_time": "2025-12-07T13:30:52.610759", "duration": 0.0}	2025-12-07 13:30:52+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_112_1764341204704370850_20251207133300.jpg	\N
113	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4108670651912689, "bbox": [325, 17, 344, 30], "frame_number": 9415, "first_seen_time": "2025-12-07T13:30:52.610759", "duration": 0.0}	2025-12-07 13:30:52+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_113_1764341204704370850_20251207133300.jpg	\N
114	truck	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.37566253542900085, "bbox": [242, 136, 288, 179], "frame_number": 9415, "first_seen_time": "2025-12-07T13:30:52.610759", "duration": 0.0}	2025-12-07 13:30:52+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_114_1764341204704370850_20251207133300.jpg	\N
115	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.34245944023132324, "bbox": [115, 14, 136, 30], "frame_number": 9415, "first_seen_time": "2025-12-07T13:30:52.610759", "duration": 0.0}	2025-12-07 13:30:52+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_115_1764341204704370850_20251207133300.jpg	\N
116	truck	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.29679396748542786, "bbox": [380, 59, 408, 87], "frame_number": 9415, "first_seen_time": "2025-12-07T13:30:52.610759", "duration": 0.0}	2025-12-07 13:30:52+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_116_1764341204704370850_20251207133301.jpg	\N
117	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.2689181864261627, "bbox": [302, 6, 318, 28], "frame_number": 9415, "first_seen_time": "2025-12-07T13:30:52.610759", "duration": 0.0}	2025-12-07 13:30:52+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_117_1764341204704370850_20251207133301.jpg	\N
118	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7527029514312744, "bbox": [78, 62, 120, 89], "frame_number": 9485, "first_seen_time": "2025-12-07T13:30:57.623550", "duration": 0.0}	2025-12-07 13:30:57+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_118_1764341204704370850_20251207133301.jpg	\N
119	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5991351008415222, "bbox": [380, 48, 404, 68], "frame_number": 9485, "first_seen_time": "2025-12-07T13:30:57.623550", "duration": 0.0}	2025-12-07 13:30:57+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_119_1764341204704370850_20251207133301.jpg	\N
120	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5706430673599243, "bbox": [278, 58, 305, 77], "frame_number": 9485, "first_seen_time": "2025-12-07T13:30:57.623550", "duration": 0.0}	2025-12-07 13:30:57+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_120_1764341204704370850_20251207133302.jpg	\N
121	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3172953724861145, "bbox": [296, 24, 315, 37], "frame_number": 9485, "first_seen_time": "2025-12-07T13:30:57.623550", "duration": 0.0}	2025-12-07 13:30:57+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_121_1764341204704370850_20251207133302.jpg	\N
122	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.29770714044570923, "bbox": [211, 0, 236, 17], "frame_number": 9485, "first_seen_time": "2025-12-07T13:30:57.623550", "duration": 0.0}	2025-12-07 13:30:57+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_122_1764341204704370850_20251207133302.jpg	\N
123	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7133567929267883, "bbox": [402, 124, 452, 171], "frame_number": 9555, "first_seen_time": "2025-12-07T13:31:02.719405", "duration": 0.0}	2025-12-07 13:31:02+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_123_1764341204704370850_20251207133302.jpg	\N
124	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5464404821395874, "bbox": [165, 110, 226, 160], "frame_number": 9555, "first_seen_time": "2025-12-07T13:31:02.719405", "duration": 0.0}	2025-12-07 13:31:02+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_124_1764341204704370850_20251207133303.jpg	\N
125	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5419426560401917, "bbox": [279, 60, 307, 84], "frame_number": 9555, "first_seen_time": "2025-12-07T13:31:02.719405", "duration": 0.0}	2025-12-07 13:31:02+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_125_1764341204704370850_20251207133303.jpg	\N
126	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.45210492610931396, "bbox": [324, 97, 360, 130], "frame_number": 9555, "first_seen_time": "2025-12-07T13:31:02.719405", "duration": 0.0}	2025-12-07 13:31:02+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_126_1764341204704370850_20251207133303.jpg	\N
127	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.299858033657074, "bbox": [325, 35, 345, 49], "frame_number": 9555, "first_seen_time": "2025-12-07T13:31:02.719405", "duration": 0.0}	2025-12-07 13:31:02+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_127_1764341204704370850_20251207133303.jpg	\N
128	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6469599008560181, "bbox": [210, 166, 272, 226], "frame_number": 9625, "first_seen_time": "2025-12-07T13:31:07.734148", "duration": 0.0}	2025-12-07 13:31:07+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_128_1764341204704370850_20251207133304.jpg	\N
129	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4853988289833069, "bbox": [389, 102, 429, 135], "frame_number": 9625, "first_seen_time": "2025-12-07T13:31:07.734148", "duration": 0.0}	2025-12-07 13:31:07+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_129_1764341204704370850_20251207133304.jpg	\N
130	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4660252332687378, "bbox": [323, 91, 352, 120], "frame_number": 9625, "first_seen_time": "2025-12-07T13:31:07.734148", "duration": 0.0}	2025-12-07 13:31:07+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_130_1764341204704370850_20251207133304.jpg	\N
131	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.36992502212524414, "bbox": [325, 40, 347, 59], "frame_number": 9625, "first_seen_time": "2025-12-07T13:31:07.734148", "duration": 0.0}	2025-12-07 13:31:07+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_131_1764341204704370850_20251207133305.jpg	\N
132	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.700363278388977, "bbox": [413, 156, 471, 208], "frame_number": 9700, "first_seen_time": "2025-12-07T13:31:13.031267", "duration": 0.0}	2025-12-07 13:31:13+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_132_1764341204704370850_20251207133305.jpg	\N
133	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6307914853096008, "bbox": [133, 325, 226, 358], "frame_number": 9700, "first_seen_time": "2025-12-07T13:31:13.031267", "duration": 0.0}	2025-12-07 13:31:13+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_133_1764341204704370850_20251207133305.jpg	\N
134	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5963290929794312, "bbox": [27, 73, 90, 115], "frame_number": 9700, "first_seen_time": "2025-12-07T13:31:13.031267", "duration": 0.0}	2025-12-07 13:31:13+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_134_1764341204704370850_20251207133305.jpg	\N
135	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.46822381019592285, "bbox": [260, 31, 283, 51], "frame_number": 9700, "first_seen_time": "2025-12-07T13:31:13.031267", "duration": 0.0}	2025-12-07 13:31:13+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_135_1764341204704370850_20251207133306.jpg	\N
136	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.463990718126297, "bbox": [318, 136, 362, 181], "frame_number": 9700, "first_seen_time": "2025-12-07T13:31:13.031267", "duration": 0.0}	2025-12-07 13:31:13+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_136_1764341204704370850_20251207133306.jpg	\N
137	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4581459164619446, "bbox": [325, 55, 351, 77], "frame_number": 9700, "first_seen_time": "2025-12-07T13:31:13.031267", "duration": 0.0}	2025-12-07 13:31:13+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_137_1764341204704370850_20251207133306.jpg	\N
138	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.32828453183174133, "bbox": [380, 34, 398, 50], "frame_number": 9700, "first_seen_time": "2025-12-07T13:31:13.031267", "duration": 0.0}	2025-12-07 13:31:13+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_138_1764341204704370850_20251207133306.jpg	\N
139	truck	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.2865597605705261, "bbox": [319, 136, 362, 180], "frame_number": 9700, "first_seen_time": "2025-12-07T13:31:13.031267", "duration": 0.0}	2025-12-07 13:31:13+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_139_1764341204704370850_20251207133307.jpg	\N
140	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.682920515537262, "bbox": [54, 72, 102, 102], "frame_number": 9770, "first_seen_time": "2025-12-07T13:31:18.051740", "duration": 0.0}	2025-12-07 13:31:18+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_140_1764341204704370850_20251207133307.jpg	\N
141	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6515487432479858, "bbox": [429, 118, 473, 157], "frame_number": 9770, "first_seen_time": "2025-12-07T13:31:18.051740", "duration": 0.0}	2025-12-07 13:31:18+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_141_1764341204704370850_20251207133307.jpg	\N
142	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6432363986968994, "bbox": [255, 109, 297, 152], "frame_number": 9770, "first_seen_time": "2025-12-07T13:31:18.051740", "duration": 0.0}	2025-12-07 13:31:18+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_142_1764341204704370850_20251207133307.jpg	\N
143	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5255340337753296, "bbox": [85, 26, 118, 49], "frame_number": 9770, "first_seen_time": "2025-12-07T13:31:18.051740", "duration": 0.0}	2025-12-07 13:31:18+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_143_1764341204704370850_20251207133308.jpg	\N
144	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.8021332025527954, "bbox": [309, 154, 357, 208], "frame_number": 9840, "first_seen_time": "2025-12-07T13:31:23.061799", "duration": 0.0}	2025-12-07 13:31:23+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_144_1764341204704370850_20251207133308.jpg	\N
145	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7308577299118042, "bbox": [452, 225, 589, 353], "frame_number": 9840, "first_seen_time": "2025-12-07T13:31:23.061799", "duration": 0.0}	2025-12-07 13:31:23+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_145_1764341204704370850_20251207133308.jpg	\N
146	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5553010106086731, "bbox": [323, 49, 347, 71], "frame_number": 9840, "first_seen_time": "2025-12-07T13:31:23.061799", "duration": 0.0}	2025-12-07 13:31:23+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_146_1764341204704370850_20251207133308.jpg	\N
147	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3331672251224518, "bbox": [389, 56, 414, 78], "frame_number": 9840, "first_seen_time": "2025-12-07T13:31:23.061799", "duration": 0.0}	2025-12-07 13:31:23+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_147_1764341204704370850_20251207133309.jpg	\N
148	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3093125820159912, "bbox": [288, 38, 308, 55], "frame_number": 9840, "first_seen_time": "2025-12-07T13:31:23.061799", "duration": 0.0}	2025-12-07 13:31:23+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_148_1764341204704370850_20251207133309.jpg	\N
149	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.8060349225997925, "bbox": [432, 231, 541, 342], "frame_number": 9910, "first_seen_time": "2025-12-07T13:31:28.091125", "duration": 0.0}	2025-12-07 13:31:28+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_149_1764341204704370850_20251207133309.jpg	\N
150	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5804421901702881, "bbox": [84, 13, 121, 37], "frame_number": 9910, "first_seen_time": "2025-12-07T13:31:28.091125", "duration": 0.0}	2025-12-07 13:31:28+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_150_1764341204704370850_20251207133309.jpg	\N
151	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3648681044578552, "bbox": [143, 15, 166, 30], "frame_number": 9910, "first_seen_time": "2025-12-07T13:31:28.091125", "duration": 0.0}	2025-12-07 13:31:28+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_151_1764341204704370850_20251207133310.jpg	\N
152	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6980199217796326, "bbox": [370, 56, 398, 79], "frame_number": 9985, "first_seen_time": "2025-12-07T13:31:33.402940", "duration": 0.0}	2025-12-07 13:31:33+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_152_1764341204704370850_20251207133310.jpg	\N
153	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6770188212394714, "bbox": [449, 105, 496, 140], "frame_number": 9985, "first_seen_time": "2025-12-07T13:31:33.402940", "duration": 0.0}	2025-12-07 13:31:33+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_153_1764341204704370850_20251207133310.jpg	\N
154	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5827641487121582, "bbox": [145, 306, 237, 356], "frame_number": 9985, "first_seen_time": "2025-12-07T13:31:33.402940", "duration": 0.0}	2025-12-07 13:31:33+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_154_1764341204704370850_20251207133310.jpg	\N
155	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4754662811756134, "bbox": [42, 25, 89, 64], "frame_number": 9985, "first_seen_time": "2025-12-07T13:31:33.402940", "duration": 0.0}	2025-12-07 13:31:33+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_155_1764341204704370850_20251207133311.jpg	\N
156	truck	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3396998941898346, "bbox": [42, 25, 89, 64], "frame_number": 9985, "first_seen_time": "2025-12-07T13:31:33.402940", "duration": 0.0}	2025-12-07 13:31:33+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_156_1764341204704370850_20251207133311.jpg	\N
157	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.29559075832366943, "bbox": [354, 14, 372, 29], "frame_number": 9985, "first_seen_time": "2025-12-07T13:31:33.402940", "duration": 0.0}	2025-12-07 13:31:33+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_157_1764341204704370850_20251207133311.jpg	\N
158	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.28083011507987976, "bbox": [130, 10, 166, 27], "frame_number": 9985, "first_seen_time": "2025-12-07T13:31:33.402940", "duration": 0.0}	2025-12-07 13:31:33+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_158_1764341204704370850_20251207133312.jpg	\N
159	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.27335843443870544, "bbox": [325, 22, 341, 32], "frame_number": 9985, "first_seen_time": "2025-12-07T13:31:33.402940", "duration": 0.0}	2025-12-07 13:31:33+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_159_1764341204704370850_20251207133312.jpg	\N
160	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6442355513572693, "bbox": [379, 80, 412, 110], "frame_number": 10060, "first_seen_time": "2025-12-07T13:31:38.780248", "duration": 0.0}	2025-12-07 13:31:38+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_160_1764341204704370850_20251207133312.jpg	\N
161	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5073203444480896, "bbox": [0, 54, 44, 82], "frame_number": 10060, "first_seen_time": "2025-12-07T13:31:38.780248", "duration": 0.0}	2025-12-07 13:31:38+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_161_1764341204704370850_20251207133312.jpg	\N
162	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7112227082252502, "bbox": [408, 152, 470, 209], "frame_number": 10135, "first_seen_time": "2025-12-07T13:31:44.100520", "duration": 0.0}	2025-12-07 13:31:44+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_162_1764341204704370850_20251207133313.jpg	\N
163	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.761164128780365, "bbox": [410, 132, 460, 182], "frame_number": 10205, "first_seen_time": "2025-12-07T13:31:49.133020", "duration": 0.0}	2025-12-07 13:31:49+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_163_1764341204704370850_20251207133313.jpg	\N
164	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5866259932518005, "bbox": [121, 320, 224, 356], "frame_number": 10205, "first_seen_time": "2025-12-07T13:31:49.133020", "duration": 0.0}	2025-12-07 13:31:49+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_164_1764341204704370850_20251207133313.jpg	\N
165	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6724448204040527, "bbox": [367, 38, 391, 59], "frame_number": 10285, "first_seen_time": "2025-12-07T13:31:54.788089", "duration": 0.0}	2025-12-07 13:31:54+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_165_1764341204704370850_20251207133313.jpg	\N
166	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6437954306602478, "bbox": [266, 77, 298, 105], "frame_number": 10285, "first_seen_time": "2025-12-07T13:31:54.788089", "duration": 0.0}	2025-12-07 13:31:54+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_166_1764341204704370850_20251207133314.jpg	\N
167	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.48581215739250183, "bbox": [128, 10, 151, 25], "frame_number": 10285, "first_seen_time": "2025-12-07T13:31:54.788089", "duration": 0.0}	2025-12-07 13:31:54+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_167_1764341204704370850_20251207133314.jpg	\N
168	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.44776517152786255, "bbox": [191, 10, 211, 30], "frame_number": 10285, "first_seen_time": "2025-12-07T13:31:54.788089", "duration": 0.0}	2025-12-07 13:31:54+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_168_1764341204704370850_20251207133314.jpg	\N
169	truck	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.38860437273979187, "bbox": [24, 51, 96, 110], "frame_number": 10285, "first_seen_time": "2025-12-07T13:31:54.788089", "duration": 0.0}	2025-12-07 13:31:54+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_169_1764341204704370850_20251207133314.jpg	\N
170	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.33497923612594604, "bbox": [25, 51, 96, 110], "frame_number": 10285, "first_seen_time": "2025-12-07T13:31:54.788089", "duration": 0.0}	2025-12-07 13:31:54+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_170_1764341204704370850_20251207133315.jpg	\N
171	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.2516006529331207, "bbox": [365, 5, 380, 20], "frame_number": 10285, "first_seen_time": "2025-12-07T13:31:54.788089", "duration": 0.0}	2025-12-07 13:31:54+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_171_1764341204704370850_20251207133315.jpg	\N
172	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7920233607292175, "bbox": [158, 262, 259, 356], "frame_number": 10365, "first_seen_time": "2025-12-07T13:32:00.535383", "duration": 0.0}	2025-12-07 13:32:00+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_172_1764341204704370850_20251207133315.jpg	\N
173	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6728658676147461, "bbox": [310, 176, 369, 248], "frame_number": 10365, "first_seen_time": "2025-12-07T13:32:00.535383", "duration": 0.0}	2025-12-07 13:32:00+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_173_1764341204704370850_20251207133315.jpg	\N
174	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6641916632652283, "bbox": [22, 61, 70, 88], "frame_number": 10365, "first_seen_time": "2025-12-07T13:32:00.535383", "duration": 0.0}	2025-12-07 13:32:00+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_174_1764341204704370850_20251207133316.jpg	\N
175	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6132383346557617, "bbox": [249, 45, 276, 66], "frame_number": 10365, "first_seen_time": "2025-12-07T13:32:00.535383", "duration": 0.0}	2025-12-07 13:32:00+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_175_1764341204704370850_20251207133316.jpg	\N
176	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5839831829071045, "bbox": [458, 280, 566, 353], "frame_number": 10365, "first_seen_time": "2025-12-07T13:32:00.535383", "duration": 0.0}	2025-12-07 13:32:00+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_176_1764341204704370850_20251207133316.jpg	\N
177	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.46177977323532104, "bbox": [367, 57, 397, 79], "frame_number": 10365, "first_seen_time": "2025-12-07T13:32:00.535383", "duration": 0.0}	2025-12-07 13:32:00+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_177_1764341204704370850_20251207133316.jpg	\N
178	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.314811110496521, "bbox": [70, 31, 101, 43], "frame_number": 10365, "first_seen_time": "2025-12-07T13:32:00.535383", "duration": 0.0}	2025-12-07 13:32:00+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_178_1764341204704370850_20251207133317.jpg	\N
179	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.747072160243988, "bbox": [308, 88, 342, 121], "frame_number": 10440, "first_seen_time": "2025-12-07T13:32:05.845910", "duration": 0.0}	2025-12-07 13:32:05+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_179_1764341204704370850_20251207133317.jpg	\N
180	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6994515657424927, "bbox": [56, 25, 90, 48], "frame_number": 10440, "first_seen_time": "2025-12-07T13:32:05.845910", "duration": 0.0}	2025-12-07 13:32:05+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_180_1764341204704370850_20251207133317.jpg	\N
181	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6550673842430115, "bbox": [105, 15, 128, 31], "frame_number": 10440, "first_seen_time": "2025-12-07T13:32:05.845910", "duration": 0.0}	2025-12-07 13:32:05+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_181_1764341204704370850_20251207133317.jpg	\N
182	truck	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5178782343864441, "bbox": [194, 91, 239, 129], "frame_number": 10440, "first_seen_time": "2025-12-07T13:32:05.845910", "duration": 0.0}	2025-12-07 13:32:05+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_182_1764341204704370850_20251207133318.jpg	\N
183	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4909563660621643, "bbox": [286, 35, 307, 53], "frame_number": 10440, "first_seen_time": "2025-12-07T13:32:05.845910", "duration": 0.0}	2025-12-07 13:32:05+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_183_1764341204704370850_20251207133318.jpg	\N
184	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4322308301925659, "bbox": [275, 64, 301, 86], "frame_number": 10440, "first_seen_time": "2025-12-07T13:32:05.845910", "duration": 0.0}	2025-12-07 13:32:05+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_184_1764341204704370850_20251207133318.jpg	\N
185	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.34559914469718933, "bbox": [194, 91, 238, 129], "frame_number": 10440, "first_seen_time": "2025-12-07T13:32:05.845910", "duration": 0.0}	2025-12-07 13:32:05+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_185_1764341204704370850_20251207133319.jpg	\N
186	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.31534212827682495, "bbox": [0, 55, 29, 81], "frame_number": 10440, "first_seen_time": "2025-12-07T13:32:05.845910", "duration": 0.0}	2025-12-07 13:32:05+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_186_1764341204704370850_20251207133319.jpg	\N
187	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6522824764251709, "bbox": [445, 222, 540, 318], "frame_number": 10510, "first_seen_time": "2025-12-07T13:32:10.947959", "duration": 0.0}	2025-12-07 13:32:10+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_187_1764341204704370850_20251207133319.jpg	\N
188	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5947662591934204, "bbox": [327, 85, 358, 114], "frame_number": 10510, "first_seen_time": "2025-12-07T13:32:10.947959", "duration": 0.0}	2025-12-07 13:32:10+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_188_1764341204704370850_20251207133319.jpg	\N
189	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5363123416900635, "bbox": [123, 16, 147, 36], "frame_number": 10510, "first_seen_time": "2025-12-07T13:32:10.947959", "duration": 0.0}	2025-12-07 13:32:10+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_189_1764341204704370850_20251207133320.jpg	\N
190	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5193572640419006, "bbox": [381, 94, 418, 124], "frame_number": 10510, "first_seen_time": "2025-12-07T13:32:10.947959", "duration": 0.0}	2025-12-07 13:32:10+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_190_1764341204704370850_20251207133320.jpg	\N
191	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.47636330127716064, "bbox": [231, 147, 281, 193], "frame_number": 10510, "first_seen_time": "2025-12-07T13:32:10.947959", "duration": 0.0}	2025-12-07 13:32:10+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_191_1764341204704370850_20251207133320.jpg	\N
192	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4559142589569092, "bbox": [47, 41, 88, 61], "frame_number": 10510, "first_seen_time": "2025-12-07T13:32:10.947959", "duration": 0.0}	2025-12-07 13:32:10+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_192_1764341204704370850_20251207133320.jpg	\N
193	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4449000358581543, "bbox": [152, 31, 179, 51], "frame_number": 10510, "first_seen_time": "2025-12-07T13:32:10.947959", "duration": 0.0}	2025-12-07 13:32:10+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_193_1764341204704370850_20251207133321.jpg	\N
194	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.2805953919887543, "bbox": [1, 39, 28, 64], "frame_number": 10510, "first_seen_time": "2025-12-07T13:32:10.947959", "duration": 0.0}	2025-12-07 13:32:10+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_194_1764341204704370850_20251207133321.jpg	\N
195	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.25223612785339355, "bbox": [289, 48, 310, 65], "frame_number": 10510, "first_seen_time": "2025-12-07T13:32:10.947959", "duration": 0.0}	2025-12-07 13:32:10+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_195_1764341204704370850_20251207133321.jpg	\N
196	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7086948156356812, "bbox": [87, 37, 121, 62], "frame_number": 10585, "first_seen_time": "2025-12-07T13:32:16.230206", "duration": 0.0}	2025-12-07 13:32:16+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_196_1764341204704370850_20251207133321.jpg	\N
197	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6955413222312927, "bbox": [0, 42, 28, 69], "frame_number": 10585, "first_seen_time": "2025-12-07T13:32:16.230206", "duration": 0.0}	2025-12-07 13:32:16+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_197_1764341204704370850_20251207133322.jpg	\N
198	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6580797433853149, "bbox": [321, 118, 361, 159], "frame_number": 10585, "first_seen_time": "2025-12-07T13:32:16.230206", "duration": 0.0}	2025-12-07 13:32:16+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_198_1764341204704370850_20251207133322.jpg	\N
199	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5623562932014465, "bbox": [392, 96, 429, 129], "frame_number": 10585, "first_seen_time": "2025-12-07T13:32:16.230206", "duration": 0.0}	2025-12-07 13:32:16+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_199_1764341204704370850_20251207133322.jpg	\N
200	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5471957921981812, "bbox": [103, 15, 130, 31], "frame_number": 10585, "first_seen_time": "2025-12-07T13:32:16.230206", "duration": 0.0}	2025-12-07 13:32:16+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_200_1764341204704370850_20251207133322.jpg	\N
201	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6083860397338867, "bbox": [165, 25, 193, 45], "frame_number": 10660, "first_seen_time": "2025-12-07T13:32:21.578566", "duration": 0.0}	2025-12-07 13:32:21+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_201_1764341204704370850_20251207133323.jpg	\N
202	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5982936024665833, "bbox": [320, 123, 364, 171], "frame_number": 10660, "first_seen_time": "2025-12-07T13:32:21.578566", "duration": 0.0}	2025-12-07 13:32:21+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_202_1764341204704370850_20251207133323.jpg	\N
203	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5495862364768982, "bbox": [202, 85, 246, 122], "frame_number": 10660, "first_seen_time": "2025-12-07T13:32:21.578566", "duration": 0.0}	2025-12-07 13:32:21+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_203_1764341204704370850_20251207133323.jpg	\N
204	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5159375071525574, "bbox": [397, 73, 424, 100], "frame_number": 10660, "first_seen_time": "2025-12-07T13:32:21.578566", "duration": 0.0}	2025-12-07 13:32:21+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_204_1764341204704370850_20251207133323.jpg	\N
205	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4842112958431244, "bbox": [301, 15, 320, 29], "frame_number": 10660, "first_seen_time": "2025-12-07T13:32:21.578566", "duration": 0.0}	2025-12-07 13:32:21+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_205_1764341204704370850_20251207133324.jpg	\N
206	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3452450931072235, "bbox": [367, 36, 389, 52], "frame_number": 10660, "first_seen_time": "2025-12-07T13:32:21.578566", "duration": 0.0}	2025-12-07 13:32:21+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_206_1764341204704370850_20251207133324.jpg	\N
207	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.2589437663555145, "bbox": [328, 33, 346, 49], "frame_number": 10660, "first_seen_time": "2025-12-07T13:32:21.578566", "duration": 0.0}	2025-12-07 13:32:21+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_207_1764341204704370850_20251207133324.jpg	\N
208	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6352872252464294, "bbox": [30, 35, 66, 55], "frame_number": 10735, "first_seen_time": "2025-12-07T13:32:29.373881", "duration": 0.0}	2025-12-07 13:32:29+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_208_1764341204704370850_20251207133324.jpg	\N
209	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6218544840812683, "bbox": [406, 135, 458, 180], "frame_number": 10735, "first_seen_time": "2025-12-07T13:32:29.373881", "duration": 0.0}	2025-12-07 13:32:29+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_209_1764341204704370850_20251207133325.jpg	\N
210	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6087434887886047, "bbox": [123, 15, 153, 45], "frame_number": 10735, "first_seen_time": "2025-12-07T13:32:29.373881", "duration": 0.0}	2025-12-07 13:32:29+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_210_1764341204704370850_20251207133325.jpg	\N
211	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4441702365875244, "bbox": [318, 171, 375, 240], "frame_number": 10735, "first_seen_time": "2025-12-07T13:32:29.373881", "duration": 0.0}	2025-12-07 13:32:29+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_211_1764341204704370850_20251207133325.jpg	\N
212	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.30266693234443665, "bbox": [121, 11, 152, 27], "frame_number": 10735, "first_seen_time": "2025-12-07T13:32:29.373881", "duration": 0.0}	2025-12-07 13:32:29+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_212_1764341204704370850_20251207133326.jpg	\N
213	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.80111163854599, "bbox": [143, 134, 212, 192], "frame_number": 10810, "first_seen_time": "2025-12-07T13:32:34.641766", "duration": 0.0}	2025-12-07 13:32:34+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_213_1764341204704370850_20251207133326.jpg	\N
214	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7663886547088623, "bbox": [373, 46, 396, 67], "frame_number": 10810, "first_seen_time": "2025-12-07T13:32:34.641766", "duration": 0.0}	2025-12-07 13:32:34+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_214_1764341204704370850_20251207133326.jpg	\N
215	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6617887616157532, "bbox": [314, 189, 379, 264], "frame_number": 10810, "first_seen_time": "2025-12-07T13:32:34.641766", "duration": 0.0}	2025-12-07 13:32:34+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_215_1764341204704370850_20251207133326.jpg	\N
216	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6215589642524719, "bbox": [406, 99, 446, 136], "frame_number": 10810, "first_seen_time": "2025-12-07T13:32:34.641766", "duration": 0.0}	2025-12-07 13:32:34+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_216_1764341204704370850_20251207133327.jpg	\N
217	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4794688820838928, "bbox": [254, 32, 280, 55], "frame_number": 10810, "first_seen_time": "2025-12-07T13:32:34.641766", "duration": 0.0}	2025-12-07 13:32:34+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_217_1764341204704370850_20251207133327.jpg	\N
218	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.42515555024147034, "bbox": [299, 24, 320, 38], "frame_number": 10810, "first_seen_time": "2025-12-07T13:32:34.641766", "duration": 0.0}	2025-12-07 13:32:34+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_218_1764341204704370850_20251207133327.jpg	\N
219	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3772728443145752, "bbox": [326, 43, 347, 59], "frame_number": 10810, "first_seen_time": "2025-12-07T13:32:34.641766", "duration": 0.0}	2025-12-07 13:32:34+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_219_1764341204704370850_20251207133327.jpg	\N
220	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3207044005393982, "bbox": [190, 16, 210, 33], "frame_number": 10810, "first_seen_time": "2025-12-07T13:32:34.641766", "duration": 0.0}	2025-12-07 13:32:34+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_220_1764341204704370850_20251207133328.jpg	\N
221	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.2839614748954773, "bbox": [172, 25, 194, 43], "frame_number": 10890, "first_seen_time": "2025-12-07T13:32:40.210901", "duration": 0.0}	2025-12-07 13:32:40+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_221_1764341204704370850_20251207133328.jpg	\N
222	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5916973948478699, "bbox": [403, 95, 442, 130], "frame_number": 10965, "first_seen_time": "2025-12-07T13:32:45.377616", "duration": 0.0}	2025-12-07 13:32:45+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_222_1764341204704370850_20251207133328.jpg	\N
223	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5567654371261597, "bbox": [317, 97, 356, 132], "frame_number": 10965, "first_seen_time": "2025-12-07T13:32:45.377616", "duration": 0.0}	2025-12-07 13:32:45+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_223_1764341204704370850_20251207133328.jpg	\N
224	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5058301091194153, "bbox": [269, 67, 299, 96], "frame_number": 10965, "first_seen_time": "2025-12-07T13:32:45.377616", "duration": 0.0}	2025-12-07 13:32:45+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_224_1764341204704370850_20251207133329.jpg	\N
225	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6904767751693726, "bbox": [39, 68, 94, 106], "frame_number": 11040, "first_seen_time": "2025-12-07T13:32:50.707988", "duration": 0.0}	2025-12-07 13:32:50+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_225_1764341204704370850_20251207133329.jpg	\N
226	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6172111630439758, "bbox": [119, 8, 149, 27], "frame_number": 11040, "first_seen_time": "2025-12-07T13:32:50.707988", "duration": 0.0}	2025-12-07 13:32:50+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_226_1764341204704370850_20251207133329.jpg	\N
227	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3876309096813202, "bbox": [170, 8, 187, 19], "frame_number": 11040, "first_seen_time": "2025-12-07T13:32:50.707988", "duration": 0.0}	2025-12-07 13:32:50+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_227_1764341204704370850_20251207133329.jpg	\N
228	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.8273446559906006, "bbox": [505, 171, 586, 226], "frame_number": 11115, "first_seen_time": "2025-12-07T13:32:56.003589", "duration": 0.0}	2025-12-07 13:32:56+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_228_1764341204704370850_20251207133330.jpg	\N
229	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7528603672981262, "bbox": [383, 87, 425, 120], "frame_number": 11115, "first_seen_time": "2025-12-07T13:32:56.003589", "duration": 0.0}	2025-12-07 13:32:56+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_229_1764341204704370850_20251207133330.jpg	\N
230	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6653740406036377, "bbox": [98, 14, 135, 43], "frame_number": 11115, "first_seen_time": "2025-12-07T13:32:56.003589", "duration": 0.0}	2025-12-07 13:32:56+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_230_1764341204704370850_20251207133330.jpg	\N
231	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5083420276641846, "bbox": [398, 40, 422, 59], "frame_number": 11115, "first_seen_time": "2025-12-07T13:32:56.003589", "duration": 0.0}	2025-12-07 13:32:56+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_231_1764341204704370850_20251207133330.jpg	\N
232	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.49954670667648315, "bbox": [357, 23, 377, 41], "frame_number": 11115, "first_seen_time": "2025-12-07T13:32:56.003589", "duration": 0.0}	2025-12-07 13:32:56+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_232_1764341204704370850_20251207133331.jpg	\N
233	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4969954788684845, "bbox": [322, 35, 343, 50], "frame_number": 11115, "first_seen_time": "2025-12-07T13:32:56.003589", "duration": 0.0}	2025-12-07 13:32:56+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_233_1764341204704370850_20251207133331.jpg	\N
234	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.40509462356567383, "bbox": [6, 44, 42, 62], "frame_number": 11115, "first_seen_time": "2025-12-07T13:32:56.003589", "duration": 0.0}	2025-12-07 13:32:56+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_234_1764341204704370850_20251207133331.jpg	\N
235	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3745674788951874, "bbox": [154, 4, 173, 19], "frame_number": 11115, "first_seen_time": "2025-12-07T13:32:56.003589", "duration": 0.0}	2025-12-07 13:32:56+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_235_1764341204704370850_20251207133331.jpg	\N
236	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.2827494442462921, "bbox": [29, 41, 47, 61], "frame_number": 11115, "first_seen_time": "2025-12-07T13:32:56.003589", "duration": 0.0}	2025-12-07 13:32:56+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_236_1764341204704370850_20251207133332.jpg	\N
237	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5927704572677612, "bbox": [393, 124, 444, 173], "frame_number": 11190, "first_seen_time": "2025-12-07T13:33:01.237924", "duration": 0.0}	2025-12-07 13:33:01+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_237_1764341204704370850_20251207133332.jpg	\N
238	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4224456548690796, "bbox": [327, 51, 353, 70], "frame_number": 11190, "first_seen_time": "2025-12-07T13:33:01.237924", "duration": 0.0}	2025-12-07 13:33:01+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_238_1764341204704370850_20251207133332.jpg	\N
239	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3670000433921814, "bbox": [74, 37, 101, 54], "frame_number": 11190, "first_seen_time": "2025-12-07T13:33:01.237924", "duration": 0.0}	2025-12-07 13:33:01+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_239_1764341204704370850_20251207133332.jpg	\N
240	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.2848558723926544, "bbox": [300, 20, 317, 34], "frame_number": 11190, "first_seen_time": "2025-12-07T13:33:01.237924", "duration": 0.0}	2025-12-07 13:33:01+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_240_1764341204704370850_20251207133333.jpg	\N
241	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6592299342155457, "bbox": [0, 91, 37, 138], "frame_number": 11265, "first_seen_time": "2025-12-07T13:33:06.544285", "duration": 0.0}	2025-12-07 13:33:06+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_241_1764341204704370850_20251207133333.jpg	\N
242	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.650912344455719, "bbox": [464, 291, 577, 353], "frame_number": 11265, "first_seen_time": "2025-12-07T13:33:06.544285", "duration": 0.0}	2025-12-07 13:33:06+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_242_1764341204704370850_20251207133333.jpg	\N
243	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.42770683765411377, "bbox": [29, 37, 60, 58], "frame_number": 11265, "first_seen_time": "2025-12-07T13:33:06.544285", "duration": 0.0}	2025-12-07 13:33:06+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_243_1764341204704370850_20251207133334.jpg	\N
244	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3488357961177826, "bbox": [119, 22, 145, 37], "frame_number": 11265, "first_seen_time": "2025-12-07T13:33:06.544285", "duration": 0.0}	2025-12-07 13:33:06+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_244_1764341204704370850_20251207133334.jpg	\N
245	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3031005859375, "bbox": [326, 31, 350, 51], "frame_number": 11265, "first_seen_time": "2025-12-07T13:33:06.544285", "duration": 0.0}	2025-12-07 13:33:06+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_245_1764341204704370850_20251207133334.jpg	\N
246	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.8148902058601379, "bbox": [432, 192, 508, 266], "frame_number": 11340, "first_seen_time": "2025-12-07T13:33:11.811388", "duration": 0.0}	2025-12-07 13:33:11+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_246_1764341204704370850_20251207133334.jpg	\N
247	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6764830946922302, "bbox": [376, 59, 406, 86], "frame_number": 11415, "first_seen_time": "2025-12-07T13:33:17.143073", "duration": 0.0}	2025-12-07 13:33:17+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_247_1764341204704370850_20251207133335.jpg	\N
248	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6679120063781738, "bbox": [229, 136, 283, 183], "frame_number": 11415, "first_seen_time": "2025-12-07T13:33:17.143073", "duration": 0.0}	2025-12-07 13:33:17+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_248_1764341204704370850_20251207133335.jpg	\N
249	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5333334803581238, "bbox": [112, 37, 150, 67], "frame_number": 11415, "first_seen_time": "2025-12-07T13:33:17.143073", "duration": 0.0}	2025-12-07 13:33:17+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_249_1764341204704370850_20251207133335.jpg	\N
250	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.502550482749939, "bbox": [207, 3, 230, 19], "frame_number": 11415, "first_seen_time": "2025-12-07T13:33:17.143073", "duration": 0.0}	2025-12-07 13:33:17+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_250_1764341204704370850_20251207133335.jpg	\N
251	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.38977211713790894, "bbox": [366, 14, 385, 29], "frame_number": 11415, "first_seen_time": "2025-12-07T13:33:17.143073", "duration": 0.0}	2025-12-07 13:33:17+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_251_1764341204704370850_20251207133336.jpg	\N
252	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.36605462431907654, "bbox": [153, 3, 173, 17], "frame_number": 11415, "first_seen_time": "2025-12-07T13:33:17.143073", "duration": 0.0}	2025-12-07 13:33:17+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_252_1764341204704370850_20251207133336.jpg	\N
253	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7166202664375305, "bbox": [384, 100, 426, 140], "frame_number": 11490, "first_seen_time": "2025-12-07T13:33:22.412469", "duration": 0.0}	2025-12-07 13:33:22+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_253_1764341204704370850_20251207133336.jpg	\N
254	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6581885814666748, "bbox": [124, 29, 152, 46], "frame_number": 11490, "first_seen_time": "2025-12-07T13:33:22.412469", "duration": 0.0}	2025-12-07 13:33:22+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_254_1764341204704370850_20251207133336.jpg	\N
255	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6421343684196472, "bbox": [203, 88, 244, 122], "frame_number": 11490, "first_seen_time": "2025-12-07T13:33:22.412469", "duration": 0.0}	2025-12-07 13:33:22+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_255_1764341204704370850_20251207133337.jpg	\N
256	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7961600422859192, "bbox": [0, 241, 132, 357], "frame_number": 11565, "first_seen_time": "2025-12-07T13:33:27.626343", "duration": 0.0}	2025-12-07 13:33:27+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_256_1764341204704370850_20251207133337.jpg	\N
257	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7237379550933838, "bbox": [269, 63, 297, 91], "frame_number": 11565, "first_seen_time": "2025-12-07T13:33:27.626343", "duration": 0.0}	2025-12-07 13:33:27+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_257_1764341204704370850_20251207133337.jpg	\N
258	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7067155241966248, "bbox": [240, 127, 286, 168], "frame_number": 11565, "first_seen_time": "2025-12-07T13:33:27.626343", "duration": 0.0}	2025-12-07 13:33:27+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_258_1764341204704370850_20251207133337.jpg	\N
259	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6937137842178345, "bbox": [42, 56, 85, 80], "frame_number": 11565, "first_seen_time": "2025-12-07T13:33:27.626343", "duration": 0.0}	2025-12-07 13:33:27+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_259_1764341204704370850_20251207133338.jpg	\N
260	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.651939332485199, "bbox": [264, 213, 336, 306], "frame_number": 11565, "first_seen_time": "2025-12-07T13:33:27.626343", "duration": 0.0}	2025-12-07 13:33:27+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_260_1764341204704370850_20251207133338.jpg	\N
261	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5212928056716919, "bbox": [294, 33, 314, 47], "frame_number": 11565, "first_seen_time": "2025-12-07T13:33:27.626343", "duration": 0.0}	2025-12-07 13:33:27+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_261_1764341204704370850_20251207133338.jpg	\N
262	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.48723334074020386, "bbox": [122, 10, 147, 27], "frame_number": 11565, "first_seen_time": "2025-12-07T13:33:27.626343", "duration": 0.0}	2025-12-07 13:33:27+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_262_1764341204704370850_20251207133338.jpg	\N
263	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4215651750564575, "bbox": [361, 34, 384, 51], "frame_number": 11565, "first_seen_time": "2025-12-07T13:33:27.626343", "duration": 0.0}	2025-12-07 13:33:27+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_263_1764341204704370850_20251207133339.jpg	\N
264	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.34072133898735046, "bbox": [94, 30, 116, 46], "frame_number": 11565, "first_seen_time": "2025-12-07T13:33:27.626343", "duration": 0.0}	2025-12-07 13:33:27+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_264_1764341204704370850_20251207133339.jpg	\N
265	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.26647165417671204, "bbox": [326, 26, 349, 57], "frame_number": 11565, "first_seen_time": "2025-12-07T13:33:27.626343", "duration": 0.0}	2025-12-07 13:33:27+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_265_1764341204704370850_20251207133339.jpg	\N
266	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7367557883262634, "bbox": [415, 194, 490, 263], "frame_number": 11635, "first_seen_time": "2025-12-07T13:33:32.649770", "duration": 0.0}	2025-12-07 13:33:32+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_266_1764341204704370850_20251207133339.jpg	\N
267	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6361023187637329, "bbox": [317, 182, 375, 250], "frame_number": 11635, "first_seen_time": "2025-12-07T13:33:32.649770", "duration": 0.0}	2025-12-07 13:33:32+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_267_1764341204704370850_20251207133340.jpg	\N
268	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5837632417678833, "bbox": [163, 4, 184, 21], "frame_number": 11635, "first_seen_time": "2025-12-07T13:33:32.649770", "duration": 0.0}	2025-12-07 13:33:32+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_268_1764341204704370850_20251207133340.jpg	\N
269	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5673404335975647, "bbox": [91, 20, 117, 37], "frame_number": 11635, "first_seen_time": "2025-12-07T13:33:32.649770", "duration": 0.0}	2025-12-07 13:33:32+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_269_1764341204704370850_20251207133340.jpg	\N
270	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.49577122926712036, "bbox": [263, 94, 297, 123], "frame_number": 11635, "first_seen_time": "2025-12-07T13:33:32.649770", "duration": 0.0}	2025-12-07 13:33:32+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_270_1764341204704370850_20251207133340.jpg	\N
271	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.40682452917099, "bbox": [195, 11, 216, 28], "frame_number": 11635, "first_seen_time": "2025-12-07T13:33:32.649770", "duration": 0.0}	2025-12-07 13:33:32+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_271_1764341204704370850_20251207133341.jpg	\N
272	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.39191898703575134, "bbox": [376, 45, 400, 71], "frame_number": 11635, "first_seen_time": "2025-12-07T13:33:32.649770", "duration": 0.0}	2025-12-07 13:33:32+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_272_1764341204704370850_20251207133341.jpg	\N
273	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.2747403681278229, "bbox": [119, 22, 147, 48], "frame_number": 11635, "first_seen_time": "2025-12-07T13:33:32.649770", "duration": 0.0}	2025-12-07 13:33:32+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_273_1764341204704370850_20251207133341.jpg	\N
274	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7460594177246094, "bbox": [460, 263, 578, 353], "frame_number": 11705, "first_seen_time": "2025-12-07T13:33:37.728977", "duration": 0.0}	2025-12-07 13:33:37+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_274_1764341204704370850_20251207133341.jpg	\N
275	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.44724777340888977, "bbox": [80, 23, 107, 39], "frame_number": 11705, "first_seen_time": "2025-12-07T13:33:37.728977", "duration": 0.0}	2025-12-07 13:33:37+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_275_1764341204704370850_20251207133342.jpg	\N
276	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.44211748242378235, "bbox": [145, 5, 165, 19], "frame_number": 11705, "first_seen_time": "2025-12-07T13:33:37.728977", "duration": 0.0}	2025-12-07 13:33:37+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_276_1764341204704370850_20251207133342.jpg	\N
277	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.39983421564102173, "bbox": [0, 50, 32, 76], "frame_number": 11705, "first_seen_time": "2025-12-07T13:33:37.728977", "duration": 0.0}	2025-12-07 13:33:37+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_277_1764341204704370850_20251207133342.jpg	\N
278	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.38586491346359253, "bbox": [286, 39, 306, 55], "frame_number": 11705, "first_seen_time": "2025-12-07T13:33:37.728977", "duration": 0.0}	2025-12-07 13:33:37+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_278_1764341204704370850_20251207133343.jpg	\N
279	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.35860902070999146, "bbox": [166, 12, 185, 29], "frame_number": 11705, "first_seen_time": "2025-12-07T13:33:37.728977", "duration": 0.0}	2025-12-07 13:33:37+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_279_1764341204704370850_20251207133343.jpg	\N
280	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.28858494758605957, "bbox": [147, 5, 182, 29], "frame_number": 11705, "first_seen_time": "2025-12-07T13:33:37.728977", "duration": 0.0}	2025-12-07 13:33:37+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_280_1764341204704370850_20251207133343.jpg	\N
281	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6883925795555115, "bbox": [32, 56, 77, 88], "frame_number": 11780, "first_seen_time": "2025-12-07T13:33:42.995518", "duration": 0.0}	2025-12-07 13:33:42+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_281_1764341204704370850_20251207133343.jpg	\N
282	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6796519756317139, "bbox": [290, 38, 314, 55], "frame_number": 11780, "first_seen_time": "2025-12-07T13:33:42.995518", "duration": 0.0}	2025-12-07 13:33:42+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_282_1764341204704370850_20251207133344.jpg	\N
283	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6746045351028442, "bbox": [444, 191, 518, 257], "frame_number": 11780, "first_seen_time": "2025-12-07T13:33:42.995518", "duration": 0.0}	2025-12-07 13:33:42+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_283_1764341204704370850_20251207133344.jpg	\N
284	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5675861835479736, "bbox": [384, 74, 416, 104], "frame_number": 11780, "first_seen_time": "2025-12-07T13:33:42.995518", "duration": 0.0}	2025-12-07 13:33:42+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_284_1764341204704370850_20251207133344.jpg	\N
285	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5046277642250061, "bbox": [226, 61, 261, 90], "frame_number": 11780, "first_seen_time": "2025-12-07T13:33:42.995518", "duration": 0.0}	2025-12-07 13:33:42+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_285_1764341204704370850_20251207133344.jpg	\N
286	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.370930552482605, "bbox": [325, 62, 351, 86], "frame_number": 11780, "first_seen_time": "2025-12-07T13:33:42.995518", "duration": 0.0}	2025-12-07 13:33:42+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_286_1764341204704370850_20251207133345.jpg	\N
287	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.32805630564689636, "bbox": [276, 60, 304, 82], "frame_number": 11860, "first_seen_time": "2025-12-07T13:33:48.672457", "duration": 0.0}	2025-12-07 13:33:48+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_287_1764341204704370850_20251207133348.jpg	\N
288	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7169098854064941, "bbox": [430, 163, 493, 223], "frame_number": 11935, "first_seen_time": "2025-12-07T13:33:53.894489", "duration": 0.0}	2025-12-07 13:33:53+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_288_1764341204704370850_20251207133354.jpg	\N
289	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5574485063552856, "bbox": [309, 186, 371, 264], "frame_number": 11935, "first_seen_time": "2025-12-07T13:33:53.894489", "duration": 0.0}	2025-12-07 13:33:53+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_289_1764341204704370850_20251207133354.jpg	\N
290	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.519658625125885, "bbox": [288, 56, 313, 77], "frame_number": 11935, "first_seen_time": "2025-12-07T13:33:53.894489", "duration": 0.0}	2025-12-07 13:33:53+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_290_1764341204704370850_20251207133354.jpg	\N
291	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4741198420524597, "bbox": [239, 120, 283, 166], "frame_number": 11935, "first_seen_time": "2025-12-07T13:33:53.894489", "duration": 0.0}	2025-12-07 13:33:53+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_291_1764341204704370850_20251207133354.jpg	\N
292	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4198702275753021, "bbox": [300, 26, 318, 42], "frame_number": 11935, "first_seen_time": "2025-12-07T13:33:53.894489", "duration": 0.0}	2025-12-07 13:33:53+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_292_1764341204704370850_20251207133355.jpg	\N
293	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3718794584274292, "bbox": [382, 35, 403, 53], "frame_number": 11935, "first_seen_time": "2025-12-07T13:33:53.894489", "duration": 0.0}	2025-12-07 13:33:53+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_293_1764341204704370850_20251207133355.jpg	\N
294	truck	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.31412845849990845, "bbox": [308, 187, 370, 264], "frame_number": 11935, "first_seen_time": "2025-12-07T13:33:53.894489", "duration": 0.0}	2025-12-07 13:33:53+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_294_1764341204704370850_20251207133355.jpg	\N
295	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.2574574053287506, "bbox": [12, 63, 61, 93], "frame_number": 11935, "first_seen_time": "2025-12-07T13:33:53.894489", "duration": 0.0}	2025-12-07 13:33:53+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_295_1764341204704370850_20251207133356.jpg	\N
296	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.47317931056022644, "bbox": [323, 30, 342, 45], "frame_number": 12010, "first_seen_time": "2025-12-07T13:33:59.272344", "duration": 0.0}	2025-12-07 13:33:59+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_296_1764341204704370850_20251207133359.jpg	\N
297	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7549169063568115, "bbox": [407, 152, 465, 210], "frame_number": 12085, "first_seen_time": "2025-12-07T13:34:04.514997", "duration": 0.0}	2025-12-07 13:34:04+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_297_1764341204704370850_20251207133404.jpg	\N
298	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7130125164985657, "bbox": [360, 36, 385, 57], "frame_number": 12085, "first_seen_time": "2025-12-07T13:34:04.514997", "duration": 0.0}	2025-12-07 13:34:04+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_298_1764341204704370850_20251207133405.jpg	\N
299	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6914222240447998, "bbox": [87, 57, 126, 82], "frame_number": 12085, "first_seen_time": "2025-12-07T13:34:04.514997", "duration": 0.0}	2025-12-07 13:34:04+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_299_1764341204704370850_20251207133405.jpg	\N
300	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6122226715087891, "bbox": [415, 56, 444, 84], "frame_number": 12085, "first_seen_time": "2025-12-07T13:34:04.514997", "duration": 0.0}	2025-12-07 13:34:04+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_300_1764341204704370850_20251207133405.jpg	\N
301	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5934372544288635, "bbox": [320, 56, 346, 76], "frame_number": 12085, "first_seen_time": "2025-12-07T13:34:04.514997", "duration": 0.0}	2025-12-07 13:34:04+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_301_1764341204704370850_20251207133405.jpg	\N
302	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5681024193763733, "bbox": [74, 23, 99, 41], "frame_number": 12085, "first_seen_time": "2025-12-07T13:34:04.514997", "duration": 0.0}	2025-12-07 13:34:04+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_302_1764341204704370850_20251207133406.jpg	\N
303	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4212711751461029, "bbox": [141, 7, 170, 29], "frame_number": 12085, "first_seen_time": "2025-12-07T13:34:04.514997", "duration": 0.0}	2025-12-07 13:34:04+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_303_1764341204704370850_20251207133406.jpg	\N
304	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.31064534187316895, "bbox": [6, 89, 65, 127], "frame_number": 12085, "first_seen_time": "2025-12-07T13:34:04.514997", "duration": 0.0}	2025-12-07 13:34:04+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_304_1764341204704370850_20251207133406.jpg	\N
305	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7665725350379944, "bbox": [434, 237, 538, 344], "frame_number": 12160, "first_seen_time": "2025-12-07T13:34:09.861232", "duration": 0.0}	2025-12-07 13:34:09+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_305_1764341204704370850_20251207133410.jpg	\N
306	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6065273284912109, "bbox": [328, 81, 359, 110], "frame_number": 12160, "first_seen_time": "2025-12-07T13:34:09.861232", "duration": 0.0}	2025-12-07 13:34:09+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_306_1764341204704370850_20251207133410.jpg	\N
307	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4667096734046936, "bbox": [292, 34, 313, 52], "frame_number": 12160, "first_seen_time": "2025-12-07T13:34:09.861232", "duration": 0.0}	2025-12-07 13:34:09+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_307_1764341204704370850_20251207133410.jpg	\N
308	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6271591782569885, "bbox": [27, 45, 67, 71], "frame_number": 12235, "first_seen_time": "2025-12-07T13:34:15.136741", "duration": 0.0}	2025-12-07 13:34:15+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_308_1764341204704370850_20251207133415.jpg	\N
309	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6227349042892456, "bbox": [326, 50, 356, 78], "frame_number": 12235, "first_seen_time": "2025-12-07T13:34:15.136741", "duration": 0.0}	2025-12-07 13:34:15+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_309_1764341204704370850_20251207133415.jpg	\N
310	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6084117293357849, "bbox": [376, 63, 403, 91], "frame_number": 12235, "first_seen_time": "2025-12-07T13:34:15.136741", "duration": 0.0}	2025-12-07 13:34:15+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_310_1764341204704370850_20251207133415.jpg	\N
311	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.603485643863678, "bbox": [96, 49, 132, 75], "frame_number": 12235, "first_seen_time": "2025-12-07T13:34:15.136741", "duration": 0.0}	2025-12-07 13:34:15+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_311_1764341204704370850_20251207133416.jpg	\N
312	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3151783347129822, "bbox": [80, 23, 108, 40], "frame_number": 12235, "first_seen_time": "2025-12-07T13:34:15.136741", "duration": 0.0}	2025-12-07 13:34:15+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_312_1764341204704370850_20251207133416.jpg	\N
313	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7686685919761658, "bbox": [363, 34, 382, 49], "frame_number": 12310, "first_seen_time": "2025-12-07T13:34:20.485256", "duration": 0.0}	2025-12-07 13:34:20+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_313_1764341204704370850_20251207133420.jpg	\N
314	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6223829388618469, "bbox": [61, 46, 101, 73], "frame_number": 12310, "first_seen_time": "2025-12-07T13:34:20.485256", "duration": 0.0}	2025-12-07 13:34:20+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_314_1764341204704370850_20251207133421.jpg	\N
315	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6053532958030701, "bbox": [0, 42, 27, 64], "frame_number": 12310, "first_seen_time": "2025-12-07T13:34:20.485256", "duration": 0.0}	2025-12-07 13:34:20+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_315_1764341204704370850_20251207133421.jpg	\N
316	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7135316133499146, "bbox": [163, 20, 191, 43], "frame_number": 12385, "first_seen_time": "2025-12-07T13:34:25.743116", "duration": 0.0}	2025-12-07 13:34:25+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_316_1764341204704370850_20251207133426.jpg	\N
317	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7080448269844055, "bbox": [390, 94, 434, 135], "frame_number": 12385, "first_seen_time": "2025-12-07T13:34:25.743116", "duration": 0.0}	2025-12-07 13:34:25+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_317_1764341204704370850_20251207133426.jpg	\N
318	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6207813024520874, "bbox": [37, 29, 76, 54], "frame_number": 12385, "first_seen_time": "2025-12-07T13:34:25.743116", "duration": 0.0}	2025-12-07 13:34:25+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_318_1764341204704370850_20251207133426.jpg	\N
319	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5798407196998596, "bbox": [127, 300, 230, 357], "frame_number": 12385, "first_seen_time": "2025-12-07T13:34:25.743116", "duration": 0.0}	2025-12-07 13:34:25+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_319_1764341204704370850_20251207133426.jpg	\N
320	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4664500653743744, "bbox": [372, 23, 390, 41], "frame_number": 12385, "first_seen_time": "2025-12-07T13:34:25.743116", "duration": 0.0}	2025-12-07 13:34:25+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_320_1764341204704370850_20251207133427.jpg	\N
321	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.41401490569114685, "bbox": [294, 27, 311, 43], "frame_number": 12385, "first_seen_time": "2025-12-07T13:34:25.743116", "duration": 0.0}	2025-12-07 13:34:25+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_321_1764341204704370850_20251207133427.jpg	\N
322	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.8195188641548157, "bbox": [413, 190, 487, 260], "frame_number": 12460, "first_seen_time": "2025-12-07T13:34:30.996428", "duration": 0.0}	2025-12-07 13:34:30+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_322_1764341204704370850_20251207133431.jpg	\N
323	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6876662373542786, "bbox": [104, 174, 185, 240], "frame_number": 12460, "first_seen_time": "2025-12-07T13:34:30.996428", "duration": 0.0}	2025-12-07 13:34:30+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_323_1764341204704370850_20251207133431.jpg	\N
324	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.44599008560180664, "bbox": [166, 16, 187, 30], "frame_number": 12460, "first_seen_time": "2025-12-07T13:34:30.996428", "duration": 0.0}	2025-12-07 13:34:30+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_324_1764341204704370850_20251207133431.jpg	\N
325	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.42784154415130615, "bbox": [0, 57, 50, 96], "frame_number": 12460, "first_seen_time": "2025-12-07T13:34:30.996428", "duration": 0.0}	2025-12-07 13:34:30+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_325_1764341204704370850_20251207133432.jpg	\N
326	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7512729167938232, "bbox": [251, 88, 290, 123], "frame_number": 12540, "first_seen_time": "2025-12-07T13:34:36.706753", "duration": 0.0}	2025-12-07 13:34:36+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_326_1764341204704370850_20251207133436.jpg	\N
327	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5913768410682678, "bbox": [94, 40, 125, 59], "frame_number": 12540, "first_seen_time": "2025-12-07T13:34:36.706753", "duration": 0.0}	2025-12-07 13:34:36+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_327_1764341204704370850_20251207133437.jpg	\N
328	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5028074979782104, "bbox": [196, 186, 271, 262], "frame_number": 12540, "first_seen_time": "2025-12-07T13:34:36.706753", "duration": 0.0}	2025-12-07 13:34:36+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_328_1764341204704370850_20251207133437.jpg	\N
329	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.43423619866371155, "bbox": [144, 2, 179, 20], "frame_number": 12540, "first_seen_time": "2025-12-07T13:34:36.706753", "duration": 0.0}	2025-12-07 13:34:36+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_329_1764341204704370850_20251207133437.jpg	\N
330	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.42608001828193665, "bbox": [289, 42, 311, 57], "frame_number": 12540, "first_seen_time": "2025-12-07T13:34:36.706753", "duration": 0.0}	2025-12-07 13:34:36+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_330_1764341204704370850_20251207133438.jpg	\N
331	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.42320334911346436, "bbox": [0, 40, 25, 68], "frame_number": 12540, "first_seen_time": "2025-12-07T13:34:36.706753", "duration": 0.0}	2025-12-07 13:34:36+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_331_1764341204704370850_20251207133438.jpg	\N
332	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3592647612094879, "bbox": [324, 45, 352, 75], "frame_number": 12540, "first_seen_time": "2025-12-07T13:34:36.706753", "duration": 0.0}	2025-12-07 13:34:36+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_332_1764341204704370850_20251207133438.jpg	\N
333	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3455055356025696, "bbox": [367, 45, 388, 62], "frame_number": 12540, "first_seen_time": "2025-12-07T13:34:36.706753", "duration": 0.0}	2025-12-07 13:34:36+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_333_1764341204704370850_20251207133438.jpg	\N
334	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.2538313865661621, "bbox": [124, 21, 148, 35], "frame_number": 12540, "first_seen_time": "2025-12-07T13:34:36.706753", "duration": 0.0}	2025-12-07 13:34:36+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_334_1764341204704370850_20251207133439.jpg	\N
335	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7346024513244629, "bbox": [430, 238, 528, 330], "frame_number": 12615, "first_seen_time": "2025-12-07T13:34:42.038007", "duration": 0.0}	2025-12-07 13:34:42+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_335_1764341204704370850_20251207133442.jpg	\N
336	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5944203734397888, "bbox": [313, 226, 386, 322], "frame_number": 12615, "first_seen_time": "2025-12-07T13:34:42.038007", "duration": 0.0}	2025-12-07 13:34:42+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_336_1764341204704370850_20251207133442.jpg	\N
337	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.48592618107795715, "bbox": [133, 21, 157, 42], "frame_number": 12615, "first_seen_time": "2025-12-07T13:34:42.038007", "duration": 0.0}	2025-12-07 13:34:42+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_337_1764341204704370850_20251207133442.jpg	\N
338	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4291937053203583, "bbox": [255, 111, 292, 147], "frame_number": 12615, "first_seen_time": "2025-12-07T13:34:42.038007", "duration": 0.0}	2025-12-07 13:34:42+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_338_1764341204704370850_20251207133443.jpg	\N
339	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3983638882637024, "bbox": [104, 17, 129, 33], "frame_number": 12615, "first_seen_time": "2025-12-07T13:34:42.038007", "duration": 0.0}	2025-12-07 13:34:42+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_339_1764341204704370850_20251207133443.jpg	\N
340	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3704589605331421, "bbox": [152, 36, 176, 52], "frame_number": 12615, "first_seen_time": "2025-12-07T13:34:42.038007", "duration": 0.0}	2025-12-07 13:34:42+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_340_1764341204704370850_20251207133443.jpg	\N
341	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3371066153049469, "bbox": [378, 51, 406, 79], "frame_number": 12615, "first_seen_time": "2025-12-07T13:34:42.038007", "duration": 0.0}	2025-12-07 13:34:42+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_341_1764341204704370850_20251207133443.jpg	\N
342	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3288508951663971, "bbox": [170, 2, 191, 18], "frame_number": 12615, "first_seen_time": "2025-12-07T13:34:42.038007", "duration": 0.0}	2025-12-07 13:34:42+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_342_1764341204704370850_20251207133444.jpg	\N
343	truck	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.29209673404693604, "bbox": [378, 51, 405, 79], "frame_number": 12615, "first_seen_time": "2025-12-07T13:34:42.038007", "duration": 0.0}	2025-12-07 13:34:42+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_343_1764341204704370850_20251207133444.jpg	\N
344	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7898821830749512, "bbox": [455, 249, 563, 352], "frame_number": 12690, "first_seen_time": "2025-12-07T13:34:47.347681", "duration": 0.0}	2025-12-07 13:34:47+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_344_1764341204704370850_20251207133447.jpg	\N
345	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4425266981124878, "bbox": [77, 26, 103, 40], "frame_number": 12690, "first_seen_time": "2025-12-07T13:34:47.347681", "duration": 0.0}	2025-12-07 13:34:47+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_345_1764341204704370850_20251207133447.jpg	\N
346	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.41566768288612366, "bbox": [144, 7, 164, 21], "frame_number": 12690, "first_seen_time": "2025-12-07T13:34:47.347681", "duration": 0.0}	2025-12-07 13:34:47+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_346_1764341204704370850_20251207133448.jpg	\N
347	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.40510475635528564, "bbox": [0, 53, 33, 80], "frame_number": 12690, "first_seen_time": "2025-12-07T13:34:47.347681", "duration": 0.0}	2025-12-07 13:34:47+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_347_1764341204704370850_20251207133448.jpg	\N
348	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3686692416667938, "bbox": [287, 38, 306, 53], "frame_number": 12690, "first_seen_time": "2025-12-07T13:34:47.347681", "duration": 0.0}	2025-12-07 13:34:47+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_348_1764341204704370850_20251207133448.jpg	\N
349	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3634048104286194, "bbox": [374, 13, 392, 36], "frame_number": 12690, "first_seen_time": "2025-12-07T13:34:47.347681", "duration": 0.0}	2025-12-07 13:34:47+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_349_1764341204704370850_20251207133448.jpg	\N
350	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3503403067588806, "bbox": [392, 33, 416, 52], "frame_number": 12690, "first_seen_time": "2025-12-07T13:34:47.347681", "duration": 0.0}	2025-12-07 13:34:47+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_350_1764341204704370850_20251207133449.jpg	\N
351	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3405909538269043, "bbox": [165, 12, 185, 30], "frame_number": 12690, "first_seen_time": "2025-12-07T13:34:47.347681", "duration": 0.0}	2025-12-07 13:34:47+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_351_1764341204704370850_20251207133449.jpg	\N
352	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.286350816488266, "bbox": [146, 7, 185, 30], "frame_number": 12690, "first_seen_time": "2025-12-07T13:34:47.347681", "duration": 0.0}	2025-12-07 13:34:47+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_352_1764341204704370850_20251207133449.jpg	\N
353	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6691413521766663, "bbox": [289, 44, 313, 63], "frame_number": 12760, "first_seen_time": "2025-12-07T13:34:52.352110", "duration": 0.0}	2025-12-07 13:34:52+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_353_1764341204704370850_20251207133452.jpg	\N
354	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6200099587440491, "bbox": [388, 87, 426, 119], "frame_number": 12760, "first_seen_time": "2025-12-07T13:34:52.352110", "duration": 0.0}	2025-12-07 13:34:52+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_354_1764341204704370850_20251207133452.jpg	\N
355	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6066932678222656, "bbox": [465, 241, 565, 334], "frame_number": 12760, "first_seen_time": "2025-12-07T13:34:52.352110", "duration": 0.0}	2025-12-07 13:34:52+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_355_1764341204704370850_20251207133453.jpg	\N
356	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6059199571609497, "bbox": [325, 73, 352, 97], "frame_number": 12760, "first_seen_time": "2025-12-07T13:34:52.352110", "duration": 0.0}	2025-12-07 13:34:52+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_356_1764341204704370850_20251207133453.jpg	\N
357	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4931528568267822, "bbox": [211, 72, 254, 105], "frame_number": 12760, "first_seen_time": "2025-12-07T13:34:52.352110", "duration": 0.0}	2025-12-07 13:34:52+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_357_1764341204704370850_20251207133453.jpg	\N
358	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.48284393548965454, "bbox": [58, 48, 99, 77], "frame_number": 12760, "first_seen_time": "2025-12-07T13:34:52.352110", "duration": 0.0}	2025-12-07 13:34:52+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_358_1764341204704370850_20251207133453.jpg	\N
359	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5993901491165161, "bbox": [250, 104, 288, 142], "frame_number": 12830, "first_seen_time": "2025-12-07T13:34:57.364025", "duration": 0.0}	2025-12-07 13:34:57+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_359_1764341204704370850_20251207133457.jpg	\N
360	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5794556736946106, "bbox": [378, 69, 407, 99], "frame_number": 12830, "first_seen_time": "2025-12-07T13:34:57.364025", "duration": 0.0}	2025-12-07 13:34:57+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_360_1764341204704370850_20251207133457.jpg	\N
361	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.32796984910964966, "bbox": [324, 69, 349, 88], "frame_number": 12830, "first_seen_time": "2025-12-07T13:34:57.364025", "duration": 0.0}	2025-12-07 13:34:57+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_361_1764341204704370850_20251207133458.jpg	\N
362	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.8443622589111328, "bbox": [141, 251, 247, 356], "frame_number": 12905, "first_seen_time": "2025-12-07T13:35:02.674312", "duration": 0.0}	2025-12-07 13:35:02+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_362_1764341204704370850_20251207133502.jpg	\N
363	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7174971699714661, "bbox": [290, 42, 314, 65], "frame_number": 12905, "first_seen_time": "2025-12-07T13:35:02.674312", "duration": 0.0}	2025-12-07 13:35:02+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_363_1764341204704370850_20251207133503.jpg	\N
364	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6131490468978882, "bbox": [269, 91, 304, 125], "frame_number": 12905, "first_seen_time": "2025-12-07T13:35:02.674312", "duration": 0.0}	2025-12-07 13:35:02+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_364_1764341204704370850_20251207133503.jpg	\N
365	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5685731172561646, "bbox": [93, 40, 124, 59], "frame_number": 12905, "first_seen_time": "2025-12-07T13:35:02.674312", "duration": 0.0}	2025-12-07 13:35:02+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_365_1764341204704370850_20251207133503.jpg	\N
366	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4470106065273285, "bbox": [394, 52, 418, 74], "frame_number": 12905, "first_seen_time": "2025-12-07T13:35:02.674312", "duration": 0.0}	2025-12-07 13:35:02+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_366_1764341204704370850_20251207133504.jpg	\N
367	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6817600727081299, "bbox": [319, 57, 343, 79], "frame_number": 12975, "first_seen_time": "2025-12-07T13:35:07.728622", "duration": 0.0}	2025-12-07 13:35:07+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_367_1764341204704370850_20251207133508.jpg	\N
368	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.59294193983078, "bbox": [376, 27, 396, 44], "frame_number": 12975, "first_seen_time": "2025-12-07T13:35:07.728622", "duration": 0.0}	2025-12-07 13:35:07+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_368_1764341204704370850_20251207133508.jpg	\N
369	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3824734389781952, "bbox": [325, 20, 345, 36], "frame_number": 12975, "first_seen_time": "2025-12-07T13:35:07.728622", "duration": 0.0}	2025-12-07 13:35:07+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_369_1764341204704370850_20251207133508.jpg	\N
370	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.37746497988700867, "bbox": [390, 86, 435, 127], "frame_number": 12975, "first_seen_time": "2025-12-07T13:35:07.728622", "duration": 0.0}	2025-12-07 13:35:07+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_370_1764341204704370850_20251207133508.jpg	\N
371	truck	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.2746017575263977, "bbox": [390, 86, 435, 127], "frame_number": 12975, "first_seen_time": "2025-12-07T13:35:07.728622", "duration": 0.0}	2025-12-07 13:35:07+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_371_1764341204704370850_20251207133509.jpg	\N
372	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7449938654899597, "bbox": [38, 43, 76, 66], "frame_number": 13050, "first_seen_time": "2025-12-07T13:35:13.040005", "duration": 0.0}	2025-12-07 13:35:13+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_372_1764341204704370850_20251207133513.jpg	\N
373	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7295873165130615, "bbox": [454, 104, 506, 147], "frame_number": 13050, "first_seen_time": "2025-12-07T13:35:13.040005", "duration": 0.0}	2025-12-07 13:35:13+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_373_1764341204704370850_20251207133513.jpg	\N
374	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6850693225860596, "bbox": [89, 38, 124, 62], "frame_number": 13050, "first_seen_time": "2025-12-07T13:35:13.040005", "duration": 0.0}	2025-12-07 13:35:13+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_374_1764341204704370850_20251207133513.jpg	\N
375	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6845977306365967, "bbox": [372, 65, 404, 98], "frame_number": 13050, "first_seen_time": "2025-12-07T13:35:13.040005", "duration": 0.0}	2025-12-07 13:35:13+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_375_1764341204704370850_20251207133514.jpg	\N
376	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5703201293945312, "bbox": [317, 122, 356, 159], "frame_number": 13050, "first_seen_time": "2025-12-07T13:35:13.040005", "duration": 0.0}	2025-12-07 13:35:13+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_376_1764341204704370850_20251207133514.jpg	\N
377	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.42510589957237244, "bbox": [125, 9, 144, 24], "frame_number": 13050, "first_seen_time": "2025-12-07T13:35:13.040005", "duration": 0.0}	2025-12-07 13:35:13+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_377_1764341204704370850_20251207133514.jpg	\N
378	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.42351359128952026, "bbox": [145, 41, 172, 58], "frame_number": 13050, "first_seen_time": "2025-12-07T13:35:13.040005", "duration": 0.0}	2025-12-07 13:35:13+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_378_1764341204704370850_20251207133514.jpg	\N
379	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3266686797142029, "bbox": [0, 38, 22, 68], "frame_number": 13050, "first_seen_time": "2025-12-07T13:35:13.040005", "duration": 0.0}	2025-12-07 13:35:13+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_379_1764341204704370850_20251207133515.jpg	\N
380	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3252384662628174, "bbox": [169, 22, 192, 40], "frame_number": 13050, "first_seen_time": "2025-12-07T13:35:13.040005", "duration": 0.0}	2025-12-07 13:35:13+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_380_1764341204704370850_20251207133515.jpg	\N
381	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5812532305717468, "bbox": [323, 144, 372, 195], "frame_number": 13130, "first_seen_time": "2025-12-07T13:35:18.668832", "duration": 0.0}	2025-12-07 13:35:18+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_381_1764341204704370850_20251207133519.jpg	\N
382	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5689855813980103, "bbox": [280, 57, 305, 80], "frame_number": 13130, "first_seen_time": "2025-12-07T13:35:18.668832", "duration": 0.0}	2025-12-07 13:35:18+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_382_1764341204704370850_20251207133519.jpg	\N
383	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3442157506942749, "bbox": [395, 42, 416, 56], "frame_number": 13130, "first_seen_time": "2025-12-07T13:35:18.668832", "duration": 0.0}	2025-12-07 13:35:18+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_383_1764341204704370850_20251207133519.jpg	\N
384	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3102748990058899, "bbox": [4, 41, 57, 78], "frame_number": 13130, "first_seen_time": "2025-12-07T13:35:18.668832", "duration": 0.0}	2025-12-07 13:35:18+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_384_1764341204704370850_20251207133519.jpg	\N
385	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.2513262927532196, "bbox": [114, 17, 138, 31], "frame_number": 13130, "first_seen_time": "2025-12-07T13:35:18.668832", "duration": 0.0}	2025-12-07 13:35:18+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_385_1764341204704370850_20251207133520.jpg	\N
386	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5056594014167786, "bbox": [388, 104, 433, 143], "frame_number": 13205, "first_seen_time": "2025-12-07T13:35:23.995369", "duration": 0.0}	2025-12-07 13:35:23+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_386_1764341204704370850_20251207133524.jpg	\N
387	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.500352680683136, "bbox": [323, 87, 361, 126], "frame_number": 13205, "first_seen_time": "2025-12-07T13:35:23.995369", "duration": 0.0}	2025-12-07 13:35:23+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_387_1764341204704370850_20251207133524.jpg	\N
388	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3495349884033203, "bbox": [106, 15, 139, 42], "frame_number": 13205, "first_seen_time": "2025-12-07T13:35:23.995369", "duration": 0.0}	2025-12-07 13:35:23+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_388_1764341204704370850_20251207133524.jpg	\N
389	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6036497354507446, "bbox": [66, 29, 96, 43], "frame_number": 13280, "first_seen_time": "2025-12-07T13:35:29.308429", "duration": 0.0}	2025-12-07 13:35:29+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_389_1764341204704370850_20251207133529.jpg	\N
390	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5434743165969849, "bbox": [370, 51, 394, 70], "frame_number": 13280, "first_seen_time": "2025-12-07T13:35:29.308429", "duration": 0.0}	2025-12-07 13:35:29+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_390_1764341204704370850_20251207133529.jpg	\N
391	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5192630887031555, "bbox": [124, 28, 151, 47], "frame_number": 13280, "first_seen_time": "2025-12-07T13:35:29.308429", "duration": 0.0}	2025-12-07 13:35:29+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_391_1764341204704370850_20251207133530.jpg	\N
392	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.8213170766830444, "bbox": [409, 138, 469, 195], "frame_number": 13360, "first_seen_time": "2025-12-07T13:35:34.988488", "duration": 0.0}	2025-12-07 13:35:34+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_392_1764341204704370850_20251207133535.jpg	\N
393	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7460299730300903, "bbox": [375, 32, 393, 48], "frame_number": 13360, "first_seen_time": "2025-12-07T13:35:34.988488", "duration": 0.0}	2025-12-07 13:35:34+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_393_1764341204704370850_20251207133535.jpg	\N
394	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6237409114837646, "bbox": [182, 12, 207, 32], "frame_number": 13360, "first_seen_time": "2025-12-07T13:35:34.988488", "duration": 0.0}	2025-12-07 13:35:34+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_394_1764341204704370850_20251207133535.jpg	\N
395	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4131541848182678, "bbox": [288, 40, 308, 55], "frame_number": 13360, "first_seen_time": "2025-12-07T13:35:34.988488", "duration": 0.0}	2025-12-07 13:35:34+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_395_1764341204704370850_20251207133536.jpg	\N
396	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.250993549823761, "bbox": [82, 21, 111, 40], "frame_number": 13360, "first_seen_time": "2025-12-07T13:35:34.988488", "duration": 0.0}	2025-12-07 13:35:34+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_396_1764341204704370850_20251207133536.jpg	\N
397	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7076305150985718, "bbox": [21, 75, 78, 117], "frame_number": 13435, "first_seen_time": "2025-12-07T13:35:40.356198", "duration": 0.0}	2025-12-07 13:35:40+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_397_1764341204704370850_20251207133540.jpg	\N
398	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6778124570846558, "bbox": [0, 320, 80, 358], "frame_number": 13435, "first_seen_time": "2025-12-07T13:35:40.356198", "duration": 0.0}	2025-12-07 13:35:40+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_398_1764341204704370850_20251207133540.jpg	\N
399	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.48864659667015076, "bbox": [61, 43, 102, 70], "frame_number": 13435, "first_seen_time": "2025-12-07T13:35:40.356198", "duration": 0.0}	2025-12-07 13:35:40+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_399_1764341204704370850_20251207133541.jpg	\N
400	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.32680001854896545, "bbox": [464, 326, 552, 354], "frame_number": 13435, "first_seen_time": "2025-12-07T13:35:40.356198", "duration": 0.0}	2025-12-07 13:35:40+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_400_1764341204704370850_20251207133541.jpg	\N
401	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.29926368594169617, "bbox": [169, 2, 203, 18], "frame_number": 13435, "first_seen_time": "2025-12-07T13:35:40.356198", "duration": 0.0}	2025-12-07 13:35:40+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_401_1764341204704370850_20251207133541.jpg	\N
402	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7925458550453186, "bbox": [225, 130, 276, 177], "frame_number": 13515, "first_seen_time": "2025-12-07T13:35:46.080849", "duration": 0.0}	2025-12-07 13:35:46+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_402_1764341204704370850_20251207133546.jpg	\N
403	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7220389246940613, "bbox": [31, 29, 72, 54], "frame_number": 13515, "first_seen_time": "2025-12-07T13:35:46.080849", "duration": 0.0}	2025-12-07 13:35:46+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_403_1764341204704370850_20251207133546.jpg	\N
404	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6847366690635681, "bbox": [372, 58, 399, 79], "frame_number": 13515, "first_seen_time": "2025-12-07T13:35:46.080849", "duration": 0.0}	2025-12-07 13:35:46+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_404_1764341204704370850_20251207133546.jpg	\N
405	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5909393429756165, "bbox": [282, 56, 307, 75], "frame_number": 13515, "first_seen_time": "2025-12-07T13:35:46.080849", "duration": 0.0}	2025-12-07 13:35:46+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_405_1764341204704370850_20251207133547.jpg	\N
406	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.352204829454422, "bbox": [130, 30, 155, 44], "frame_number": 13515, "first_seen_time": "2025-12-07T13:35:46.080849", "duration": 0.0}	2025-12-07 13:35:46+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_406_1764341204704370850_20251207133547.jpg	\N
407	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.33332332968711853, "bbox": [324, 64, 356, 100], "frame_number": 13515, "first_seen_time": "2025-12-07T13:35:46.080849", "duration": 0.0}	2025-12-07 13:35:46+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_407_1764341204704370850_20251207133547.jpg	\N
408	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.29538020491600037, "bbox": [153, 0, 186, 21], "frame_number": 13515, "first_seen_time": "2025-12-07T13:35:46.080849", "duration": 0.0}	2025-12-07 13:35:46+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_408_1764341204704370850_20251207133547.jpg	\N
409	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6620054841041565, "bbox": [219, 177, 276, 236], "frame_number": 13590, "first_seen_time": "2025-12-07T13:35:51.433665", "duration": 0.0}	2025-12-07 13:35:51+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_409_1764341204704370850_20251207133551.jpg	\N
410	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.512765645980835, "bbox": [385, 69, 416, 101], "frame_number": 13590, "first_seen_time": "2025-12-07T13:35:51.433665", "duration": 0.0}	2025-12-07 13:35:51+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_410_1764341204704370850_20251207133551.jpg	\N
411	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.36786404252052307, "bbox": [157, 15, 177, 32], "frame_number": 13590, "first_seen_time": "2025-12-07T13:35:51.433665", "duration": 0.0}	2025-12-07 13:35:51+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_411_1764341204704370850_20251207133552.jpg	\N
412	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3155318796634674, "bbox": [325, 19, 344, 34], "frame_number": 13590, "first_seen_time": "2025-12-07T13:35:51.433665", "duration": 0.0}	2025-12-07 13:35:51+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_412_1764341204704370850_20251207133552.jpg	\N
413	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.28754428029060364, "bbox": [128, 11, 150, 25], "frame_number": 13590, "first_seen_time": "2025-12-07T13:35:51.433665", "duration": 0.0}	2025-12-07 13:35:51+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_413_1764341204704370850_20251207133552.jpg	\N
414	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.26907414197921753, "bbox": [300, 14, 317, 30], "frame_number": 13590, "first_seen_time": "2025-12-07T13:35:51.433665", "duration": 0.0}	2025-12-07 13:35:51+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_414_1764341204704370850_20251207133553.jpg	\N
415	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.8105151653289795, "bbox": [383, 55, 409, 76], "frame_number": 13660, "first_seen_time": "2025-12-07T13:35:56.554622", "duration": 0.0}	2025-12-07 13:35:56+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_415_1764341204704370850_20251207133556.jpg	\N
416	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7321799993515015, "bbox": [108, 50, 146, 73], "frame_number": 13660, "first_seen_time": "2025-12-07T13:35:56.554622", "duration": 0.0}	2025-12-07 13:35:56+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_416_1764341204704370850_20251207133557.jpg	\N
417	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6063464879989624, "bbox": [274, 68, 302, 91], "frame_number": 13660, "first_seen_time": "2025-12-07T13:35:56.554622", "duration": 0.0}	2025-12-07 13:35:56+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_417_1764341204704370850_20251207133557.jpg	\N
418	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.749048113822937, "bbox": [323, 118, 361, 155], "frame_number": 13730, "first_seen_time": "2025-12-07T13:36:01.603435", "duration": 0.0}	2025-12-07 13:36:01+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_418_1764341204704370850_20251207133601.jpg	\N
419	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7126685976982117, "bbox": [415, 156, 479, 216], "frame_number": 13730, "first_seen_time": "2025-12-07T13:36:01.603435", "duration": 0.0}	2025-12-07 13:36:01+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_419_1764341204704370850_20251207133602.jpg	\N
420	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6840705871582031, "bbox": [118, 146, 201, 208], "frame_number": 13730, "first_seen_time": "2025-12-07T13:36:01.603435", "duration": 0.0}	2025-12-07 13:36:01+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_420_1764341204704370850_20251207133602.jpg	\N
421	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6298043727874756, "bbox": [274, 72, 304, 100], "frame_number": 13730, "first_seen_time": "2025-12-07T13:36:01.603435", "duration": 0.0}	2025-12-07 13:36:01+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_421_1764341204704370850_20251207133602.jpg	\N
422	truck	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.42188358306884766, "bbox": [118, 146, 201, 208], "frame_number": 13730, "first_seen_time": "2025-12-07T13:36:01.603435", "duration": 0.0}	2025-12-07 13:36:01+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_422_1764341204704370850_20251207133602.jpg	\N
423	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.409405380487442, "bbox": [323, 39, 344, 54], "frame_number": 13730, "first_seen_time": "2025-12-07T13:36:01.603435", "duration": 0.0}	2025-12-07 13:36:01+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_423_1764341204704370850_20251207133603.jpg	\N
424	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.38298124074935913, "bbox": [368, 35, 389, 50], "frame_number": 13730, "first_seen_time": "2025-12-07T13:36:01.603435", "duration": 0.0}	2025-12-07 13:36:01+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_424_1764341204704370850_20251207133603.jpg	\N
425	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3532869517803192, "bbox": [0, 44, 25, 66], "frame_number": 13730, "first_seen_time": "2025-12-07T13:36:01.603435", "duration": 0.0}	2025-12-07 13:36:01+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_425_1764341204704370850_20251207133603.jpg	\N
426	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6251581907272339, "bbox": [169, 224, 255, 317], "frame_number": 13800, "first_seen_time": "2025-12-07T13:36:06.625566", "duration": 0.0}	2025-12-07 13:36:06+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_426_1764341204704370850_20251207133606.jpg	\N
427	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5335190892219543, "bbox": [400, 125, 448, 167], "frame_number": 13800, "first_seen_time": "2025-12-07T13:36:06.625566", "duration": 0.0}	2025-12-07 13:36:06+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_427_1764341204704370850_20251207133607.jpg	\N
428	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.458612322807312, "bbox": [377, 29, 394, 45], "frame_number": 13800, "first_seen_time": "2025-12-07T13:36:06.625566", "duration": 0.0}	2025-12-07 13:36:06+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_428_1764341204704370850_20251207133607.jpg	\N
429	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.41286149621009827, "bbox": [266, 26, 286, 44], "frame_number": 13800, "first_seen_time": "2025-12-07T13:36:06.625566", "duration": 0.0}	2025-12-07 13:36:06+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_429_1764341204704370850_20251207133607.jpg	\N
430	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3928918242454529, "bbox": [322, 112, 356, 146], "frame_number": 13800, "first_seen_time": "2025-12-07T13:36:06.625566", "duration": 0.0}	2025-12-07 13:36:06+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_430_1764341204704370850_20251207133607.jpg	\N
431	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6754254698753357, "bbox": [418, 98, 456, 130], "frame_number": 13870, "first_seen_time": "2025-12-07T13:36:11.685995", "duration": 0.0}	2025-12-07 13:36:11+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_431_1764341204704370850_20251207133611.jpg	\N
432	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5724645256996155, "bbox": [182, 243, 270, 340], "frame_number": 13870, "first_seen_time": "2025-12-07T13:36:11.685995", "duration": 0.0}	2025-12-07 13:36:11+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_432_1764341204704370850_20251207133612.jpg	\N
433	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5407182574272156, "bbox": [268, 88, 302, 122], "frame_number": 13870, "first_seen_time": "2025-12-07T13:36:11.685995", "duration": 0.0}	2025-12-07 13:36:11+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_433_1764341204704370850_20251207133612.jpg	\N
434	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.432720810174942, "bbox": [62, 31, 100, 56], "frame_number": 13870, "first_seen_time": "2025-12-07T13:36:11.685995", "duration": 0.0}	2025-12-07 13:36:11+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_434_1764341204704370850_20251207133612.jpg	\N
435	truck	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.41454097628593445, "bbox": [181, 244, 269, 341], "frame_number": 13870, "first_seen_time": "2025-12-07T13:36:11.685995", "duration": 0.0}	2025-12-07 13:36:11+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_435_1764341204704370850_20251207133613.jpg	\N
436	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3413534462451935, "bbox": [154, 20, 176, 35], "frame_number": 13870, "first_seen_time": "2025-12-07T13:36:11.685995", "duration": 0.0}	2025-12-07 13:36:11+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_436_1764341204704370850_20251207133613.jpg	\N
437	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.301311731338501, "bbox": [2, 91, 63, 127], "frame_number": 13870, "first_seen_time": "2025-12-07T13:36:11.685995", "duration": 0.0}	2025-12-07 13:36:11+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_437_1764341204704370850_20251207133613.jpg	\N
438	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6801263689994812, "bbox": [413, 143, 489, 212], "frame_number": 13945, "first_seen_time": "2025-12-07T13:36:17.073088", "duration": 0.0}	2025-12-07 13:36:17+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_438_1764341204704370850_20251207133617.jpg	\N
439	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6510463953018188, "bbox": [316, 98, 349, 133], "frame_number": 13945, "first_seen_time": "2025-12-07T13:36:17.073088", "duration": 0.0}	2025-12-07 13:36:17+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_439_1764341204704370850_20251207133617.jpg	\N
440	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5183225274085999, "bbox": [324, 36, 346, 53], "frame_number": 13945, "first_seen_time": "2025-12-07T13:36:17.073088", "duration": 0.0}	2025-12-07 13:36:17+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_440_1764341204704370850_20251207133617.jpg	\N
441	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.8308205604553223, "bbox": [520, 185, 624, 256], "frame_number": 14020, "first_seen_time": "2025-12-07T13:36:22.378426", "duration": 0.0}	2025-12-07 13:36:22+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_441_1764341204704370850_20251207133622.jpg	\N
442	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.8060599565505981, "bbox": [304, 271, 380, 354], "frame_number": 14020, "first_seen_time": "2025-12-07T13:36:22.378426", "duration": 0.0}	2025-12-07 13:36:22+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_442_1764341204704370850_20251207133622.jpg	\N
443	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7846626043319702, "bbox": [101, 27, 127, 43], "frame_number": 14020, "first_seen_time": "2025-12-07T13:36:22.378426", "duration": 0.0}	2025-12-07 13:36:22+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_443_1764341204704370850_20251207133623.jpg	\N
444	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6593890190124512, "bbox": [387, 110, 436, 158], "frame_number": 14020, "first_seen_time": "2025-12-07T13:36:22.378426", "duration": 0.0}	2025-12-07 13:36:22+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_444_1764341204704370850_20251207133623.jpg	\N
445	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5048131942749023, "bbox": [29, 28, 76, 52], "frame_number": 14020, "first_seen_time": "2025-12-07T13:36:22.378426", "duration": 0.0}	2025-12-07 13:36:22+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_445_1764341204704370850_20251207133623.jpg	\N
446	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.47887879610061646, "bbox": [142, 23, 168, 40], "frame_number": 14020, "first_seen_time": "2025-12-07T13:36:22.378426", "duration": 0.0}	2025-12-07 13:36:22+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_446_1764341204704370850_20251207133623.jpg	\N
447	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.2840239107608795, "bbox": [194, 12, 217, 32], "frame_number": 14020, "first_seen_time": "2025-12-07T13:36:22.378426", "duration": 0.0}	2025-12-07 13:36:22+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_447_1764341204704370850_20251207133624.jpg	\N
448	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6845881938934326, "bbox": [245, 125, 287, 166], "frame_number": 14095, "first_seen_time": "2025-12-07T13:36:27.644545", "duration": 0.0}	2025-12-07 13:36:27+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_448_1764341204704370850_20251207133627.jpg	\N
449	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6388729810714722, "bbox": [417, 65, 447, 90], "frame_number": 14095, "first_seen_time": "2025-12-07T13:36:27.644545", "duration": 0.0}	2025-12-07 13:36:27+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_449_1764341204704370850_20251207133628.jpg	\N
450	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5942413210868835, "bbox": [362, 34, 383, 52], "frame_number": 14095, "first_seen_time": "2025-12-07T13:36:27.644545", "duration": 0.0}	2025-12-07 13:36:27+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_450_1764341204704370850_20251207133628.jpg	\N
451	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5036582946777344, "bbox": [0, 48, 24, 70], "frame_number": 14095, "first_seen_time": "2025-12-07T13:36:27.644545", "duration": 0.0}	2025-12-07 13:36:27+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_451_1764341204704370850_20251207133628.jpg	\N
452	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4803043007850647, "bbox": [96, 22, 135, 41], "frame_number": 14095, "first_seen_time": "2025-12-07T13:36:27.644545", "duration": 0.0}	2025-12-07 13:36:27+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_452_1764341204704370850_20251207133628.jpg	\N
453	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3023628294467926, "bbox": [351, 5, 367, 18], "frame_number": 14095, "first_seen_time": "2025-12-07T13:36:27.644545", "duration": 0.0}	2025-12-07 13:36:27+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_453_1764341204704370850_20251207133629.jpg	\N
454	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.25108063220977783, "bbox": [152, 9, 169, 19], "frame_number": 14095, "first_seen_time": "2025-12-07T13:36:27.644545", "duration": 0.0}	2025-12-07 13:36:27+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_454_1764341204704370850_20251207133629.jpg	\N
455	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.43215540051460266, "bbox": [370, 57, 399, 83], "frame_number": 14165, "first_seen_time": "2025-12-07T13:36:32.701346", "duration": 0.0}	2025-12-07 13:36:32+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_455_1764341204704370850_20251207133633.jpg	\N
456	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6497886776924133, "bbox": [389, 103, 433, 141], "frame_number": 14240, "first_seen_time": "2025-12-07T13:36:38.047269", "duration": 0.0}	2025-12-07 13:36:38+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_456_1764341204704370850_20251207133638.jpg	\N
457	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6731166839599609, "bbox": [237, 128, 282, 168], "frame_number": 14315, "first_seen_time": "2025-12-07T13:36:43.369306", "duration": 0.0}	2025-12-07 13:36:43+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_457_1764341204704370850_20251207133643.jpg	\N
458	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6398418545722961, "bbox": [389, 79, 421, 106], "frame_number": 14315, "first_seen_time": "2025-12-07T13:36:43.369306", "duration": 0.0}	2025-12-07 13:36:43+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_458_1764341204704370850_20251207133643.jpg	\N
459	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7288462519645691, "bbox": [363, 29, 382, 46], "frame_number": 14390, "first_seen_time": "2025-12-07T13:36:48.683536", "duration": 0.0}	2025-12-07 13:36:48+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_459_1764341204704370850_20251207133648.jpg	\N
460	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7178851962089539, "bbox": [168, 17, 194, 43], "frame_number": 14390, "first_seen_time": "2025-12-07T13:36:48.683536", "duration": 0.0}	2025-12-07 13:36:48+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_460_1764341204704370850_20251207133649.jpg	\N
461	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7117516398429871, "bbox": [278, 54, 304, 77], "frame_number": 14390, "first_seen_time": "2025-12-07T13:36:48.683536", "duration": 0.0}	2025-12-07 13:36:48+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_461_1764341204704370850_20251207133649.jpg	\N
462	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6226010918617249, "bbox": [101, 15, 126, 33], "frame_number": 14390, "first_seen_time": "2025-12-07T13:36:48.683536", "duration": 0.0}	2025-12-07 13:36:48+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_462_1764341204704370850_20251207133649.jpg	\N
463	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5204119682312012, "bbox": [0, 76, 34, 108], "frame_number": 14390, "first_seen_time": "2025-12-07T13:36:48.683536", "duration": 0.0}	2025-12-07 13:36:48+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_463_1764341204704370850_20251207133650.jpg	\N
464	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7805080413818359, "bbox": [201, 200, 273, 272], "frame_number": 14465, "first_seen_time": "2025-12-07T13:36:53.977815", "duration": 0.0}	2025-12-07 13:36:53+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_464_1764341204704370850_20251207133654.jpg	\N
465	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6194677352905273, "bbox": [430, 212, 514, 293], "frame_number": 14465, "first_seen_time": "2025-12-07T13:36:53.977815", "duration": 0.0}	2025-12-07 13:36:53+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_465_1764341204704370850_20251207133654.jpg	\N
466	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5156451463699341, "bbox": [364, 47, 389, 68], "frame_number": 14465, "first_seen_time": "2025-12-07T13:36:53.977815", "duration": 0.0}	2025-12-07 13:36:53+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_466_1764341204704370850_20251207133654.jpg	\N
467	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.49280908703804016, "bbox": [257, 39, 280, 56], "frame_number": 14465, "first_seen_time": "2025-12-07T13:36:53.977815", "duration": 0.0}	2025-12-07 13:36:53+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_467_1764341204704370850_20251207133655.jpg	\N
468	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4922929108142853, "bbox": [0, 75, 32, 106], "frame_number": 14465, "first_seen_time": "2025-12-07T13:36:53.977815", "duration": 0.0}	2025-12-07 13:36:53+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_468_1764341204704370850_20251207133655.jpg	\N
469	truck	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.42656728625297546, "bbox": [315, 140, 363, 191], "frame_number": 14465, "first_seen_time": "2025-12-07T13:36:53.977815", "duration": 0.0}	2025-12-07 13:36:53+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_469_1764341204704370850_20251207133655.jpg	\N
470	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.805993378162384, "bbox": [314, 72, 343, 100], "frame_number": 14540, "first_seen_time": "2025-12-07T13:36:59.331580", "duration": 0.0}	2025-12-07 13:36:59+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_470_1764341204704370850_20251207133659.jpg	\N
471	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7073209285736084, "bbox": [29, 29, 70, 56], "frame_number": 14540, "first_seen_time": "2025-12-07T13:36:59.331580", "duration": 0.0}	2025-12-07 13:36:59+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_471_1764341204704370850_20251207133659.jpg	\N
472	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.608024537563324, "bbox": [89, 18, 116, 36], "frame_number": 14540, "first_seen_time": "2025-12-07T13:36:59.331580", "duration": 0.0}	2025-12-07 13:36:59+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_472_1764341204704370850_20251207133700.jpg	\N
473	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5637068152427673, "bbox": [276, 57, 304, 76], "frame_number": 14540, "first_seen_time": "2025-12-07T13:36:59.331580", "duration": 0.0}	2025-12-07 13:36:59+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_473_1764341204704370850_20251207133700.jpg	\N
474	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5230236649513245, "bbox": [213, 72, 251, 105], "frame_number": 14540, "first_seen_time": "2025-12-07T13:36:59.331580", "duration": 0.0}	2025-12-07 13:36:59+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_474_1764341204704370850_20251207133700.jpg	\N
475	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.44242075085639954, "bbox": [289, 31, 308, 49], "frame_number": 14540, "first_seen_time": "2025-12-07T13:36:59.331580", "duration": 0.0}	2025-12-07 13:36:59+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_475_1764341204704370850_20251207133700.jpg	\N
476	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.751343846321106, "bbox": [111, 47, 149, 70], "frame_number": 14615, "first_seen_time": "2025-12-07T13:37:04.563536", "duration": 0.0}	2025-12-07 13:37:04+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_476_1764341204704370850_20251207133704.jpg	\N
477	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7193603515625, "bbox": [371, 65, 400, 92], "frame_number": 14615, "first_seen_time": "2025-12-07T13:37:04.563536", "duration": 0.0}	2025-12-07 13:37:04+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_477_1764341204704370850_20251207133705.jpg	\N
478	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7109185457229614, "bbox": [414, 145, 468, 194], "frame_number": 14615, "first_seen_time": "2025-12-07T13:37:04.563536", "duration": 0.0}	2025-12-07 13:37:04+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_478_1764341204704370850_20251207133705.jpg	\N
479	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6295298933982849, "bbox": [325, 59, 356, 82], "frame_number": 14615, "first_seen_time": "2025-12-07T13:37:04.563536", "duration": 0.0}	2025-12-07 13:37:04+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_479_1764341204704370850_20251207133705.jpg	\N
480	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6097187995910645, "bbox": [137, 307, 235, 357], "frame_number": 14615, "first_seen_time": "2025-12-07T13:37:04.563536", "duration": 0.0}	2025-12-07 13:37:04+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_480_1764341204704370850_20251207133705.jpg	\N
481	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4671960175037384, "bbox": [264, 90, 296, 119], "frame_number": 14615, "first_seen_time": "2025-12-07T13:37:04.563536", "duration": 0.0}	2025-12-07 13:37:04+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_481_1764341204704370850_20251207133706.jpg	\N
482	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.41310790181159973, "bbox": [87, 31, 117, 48], "frame_number": 14615, "first_seen_time": "2025-12-07T13:37:04.563536", "duration": 0.0}	2025-12-07 13:37:04+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_482_1764341204704370850_20251207133706.jpg	\N
483	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3353443443775177, "bbox": [198, 13, 216, 28], "frame_number": 14615, "first_seen_time": "2025-12-07T13:37:04.563536", "duration": 0.0}	2025-12-07 13:37:04+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_483_1764341204704370850_20251207133706.jpg	\N
484	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.315143883228302, "bbox": [0, 57, 30, 84], "frame_number": 14615, "first_seen_time": "2025-12-07T13:37:04.563536", "duration": 0.0}	2025-12-07 13:37:04+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_484_1764341204704370850_20251207133706.jpg	\N
485	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6817885637283325, "bbox": [174, 226, 266, 330], "frame_number": 14690, "first_seen_time": "2025-12-07T13:37:09.881973", "duration": 0.0}	2025-12-07 13:37:09+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_485_1764341204704370850_20251207133710.jpg	\N
486	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6653861403465271, "bbox": [22, 57, 69, 89], "frame_number": 14690, "first_seen_time": "2025-12-07T13:37:09.881973", "duration": 0.0}	2025-12-07 13:37:09+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_486_1764341204704370850_20251207133710.jpg	\N
487	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6468631625175476, "bbox": [381, 70, 410, 94], "frame_number": 14690, "first_seen_time": "2025-12-07T13:37:09.881973", "duration": 0.0}	2025-12-07 13:37:09+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_487_1764341204704370850_20251207133710.jpg	\N
488	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6142890453338623, "bbox": [74, 21, 106, 41], "frame_number": 14690, "first_seen_time": "2025-12-07T13:37:09.881973", "duration": 0.0}	2025-12-07 13:37:09+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_488_1764341204704370850_20251207133710.jpg	\N
489	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4772554934024811, "bbox": [322, 81, 354, 110], "frame_number": 14690, "first_seen_time": "2025-12-07T13:37:09.881973", "duration": 0.0}	2025-12-07 13:37:09+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_489_1764341204704370850_20251207133711.jpg	\N
490	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6917245984077454, "bbox": [387, 53, 411, 74], "frame_number": 14765, "first_seen_time": "2025-12-07T13:37:15.189232", "duration": 0.0}	2025-12-07 13:37:15+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_490_1764341204704370850_20251207133715.jpg	\N
491	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6766656637191772, "bbox": [235, 56, 265, 83], "frame_number": 14765, "first_seen_time": "2025-12-07T13:37:15.189232", "duration": 0.0}	2025-12-07 13:37:15+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_491_1764341204704370850_20251207133715.jpg	\N
492	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5334279537200928, "bbox": [323, 84, 363, 117], "frame_number": 14765, "first_seen_time": "2025-12-07T13:37:15.189232", "duration": 0.0}	2025-12-07 13:37:15+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_492_1764341204704370850_20251207133715.jpg	\N
493	truck	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.35530316829681396, "bbox": [127, 40, 161, 66], "frame_number": 14765, "first_seen_time": "2025-12-07T13:37:15.189232", "duration": 0.0}	2025-12-07 13:37:15+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_493_1764341204704370850_20251207133716.jpg	\N
494	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.34188857674598694, "bbox": [276, 16, 292, 29], "frame_number": 14765, "first_seen_time": "2025-12-07T13:37:15.189232", "duration": 0.0}	2025-12-07 13:37:15+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_494_1764341204704370850_20251207133716.jpg	\N
495	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.25099700689315796, "bbox": [304, 298, 391, 355], "frame_number": 14765, "first_seen_time": "2025-12-07T13:37:15.189232", "duration": 0.0}	2025-12-07 13:37:15+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_495_1764341204704370850_20251207133716.jpg	\N
496	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.8466491103172302, "bbox": [484, 229, 572, 304], "frame_number": 14835, "first_seen_time": "2025-12-07T13:37:20.203097", "duration": 0.0}	2025-12-07 13:37:20+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_496_1764341204704370850_20251207133720.jpg	\N
497	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7235561609268188, "bbox": [174, 237, 266, 339], "frame_number": 14835, "first_seen_time": "2025-12-07T13:37:20.203097", "duration": 0.0}	2025-12-07 13:37:20+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_497_1764341204704370850_20251207133720.jpg	\N
498	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.47917377948760986, "bbox": [274, 60, 302, 84], "frame_number": 14905, "first_seen_time": "2025-12-07T13:37:25.231480", "duration": 0.0}	2025-12-07 13:37:25+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_498_1764341204704370850_20251207133725.jpg	\N
499	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4680641293525696, "bbox": [400, 85, 434, 115], "frame_number": 14905, "first_seen_time": "2025-12-07T13:37:25.231480", "duration": 0.0}	2025-12-07 13:37:25+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_499_1764341204704370850_20251207133725.jpg	\N
500	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4299603998661041, "bbox": [320, 81, 352, 113], "frame_number": 14905, "first_seen_time": "2025-12-07T13:37:25.231480", "duration": 0.0}	2025-12-07 13:37:25+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_500_1764341204704370850_20251207133726.jpg	\N
501	truck	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.404392808675766, "bbox": [400, 85, 433, 115], "frame_number": 14905, "first_seen_time": "2025-12-07T13:37:25.231480", "duration": 0.0}	2025-12-07 13:37:25+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_501_1764341204704370850_20251207133726.jpg	\N
502	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.26109862327575684, "bbox": [299, 12, 321, 44], "frame_number": 14905, "first_seen_time": "2025-12-07T13:37:25.231480", "duration": 0.0}	2025-12-07 13:37:25+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_502_1764341204704370850_20251207133726.jpg	\N
503	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5620324611663818, "bbox": [109, 9, 141, 30], "frame_number": 14980, "first_seen_time": "2025-12-07T13:37:30.538434", "duration": 0.0}	2025-12-07 13:37:30+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_503_1764341204704370850_20251207133730.jpg	\N
504	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.41504377126693726, "bbox": [0, 78, 64, 127], "frame_number": 14980, "first_seen_time": "2025-12-07T13:37:30.538434", "duration": 0.0}	2025-12-07 13:37:30+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_504_1764341204704370850_20251207133731.jpg	\N
505	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.2780618369579315, "bbox": [323, 7, 345, 28], "frame_number": 14980, "first_seen_time": "2025-12-07T13:37:30.538434", "duration": 0.0}	2025-12-07 13:37:30+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_505_1764341204704370850_20251207133731.jpg	\N
506	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.8458994626998901, "bbox": [511, 179, 598, 237], "frame_number": 15050, "first_seen_time": "2025-12-07T13:37:35.595655", "duration": 0.0}	2025-12-07 13:37:35+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_506_1764341204704370850_20251207133735.jpg	\N
507	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7483331561088562, "bbox": [383, 89, 422, 124], "frame_number": 15050, "first_seen_time": "2025-12-07T13:37:35.595655", "duration": 0.0}	2025-12-07 13:37:35+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_507_1764341204704370850_20251207133736.jpg	\N
508	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6344331502914429, "bbox": [100, 14, 138, 42], "frame_number": 15050, "first_seen_time": "2025-12-07T13:37:35.595655", "duration": 0.0}	2025-12-07 13:37:35+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_508_1764341204704370850_20251207133736.jpg	\N
509	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5137664675712585, "bbox": [321, 36, 344, 51], "frame_number": 15050, "first_seen_time": "2025-12-07T13:37:35.595655", "duration": 0.0}	2025-12-07 13:37:35+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_509_1764341204704370850_20251207133736.jpg	\N
510	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5094261765480042, "bbox": [400, 40, 424, 61], "frame_number": 15050, "first_seen_time": "2025-12-07T13:37:35.595655", "duration": 0.0}	2025-12-07 13:37:35+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_510_1764341204704370850_20251207133736.jpg	\N
511	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5015323162078857, "bbox": [357, 22, 379, 41], "frame_number": 15050, "first_seen_time": "2025-12-07T13:37:35.595655", "duration": 0.0}	2025-12-07 13:37:35+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_511_1764341204704370850_20251207133737.jpg	\N
512	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.48123636841773987, "bbox": [156, 2, 191, 18], "frame_number": 15050, "first_seen_time": "2025-12-07T13:37:35.595655", "duration": 0.0}	2025-12-07 13:37:35+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_512_1764341204704370850_20251207133737.jpg	\N
513	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3022080361843109, "bbox": [22, 37, 52, 60], "frame_number": 15050, "first_seen_time": "2025-12-07T13:37:35.595655", "duration": 0.0}	2025-12-07 13:37:35+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_513_1764341204704370850_20251207133737.jpg	\N
514	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.26532068848609924, "bbox": [0, 105, 24, 139], "frame_number": 15050, "first_seen_time": "2025-12-07T13:37:35.595655", "duration": 0.0}	2025-12-07 13:37:35+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_514_1764341204704370850_20251207133737.jpg	\N
515	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.8008672595024109, "bbox": [406, 159, 469, 223], "frame_number": 15120, "first_seen_time": "2025-12-07T13:37:40.606842", "duration": 0.0}	2025-12-07 13:37:40+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_515_1764341204704370850_20251207133740.jpg	\N
516	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3186424970626831, "bbox": [327, 62, 359, 84], "frame_number": 15120, "first_seen_time": "2025-12-07T13:37:40.606842", "duration": 0.0}	2025-12-07 13:37:40+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_516_1764341204704370850_20251207133741.jpg	\N
517	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.27142995595932007, "bbox": [100, 29, 126, 45], "frame_number": 15120, "first_seen_time": "2025-12-07T13:37:40.606842", "duration": 0.0}	2025-12-07 13:37:40+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_517_1764341204704370850_20251207133741.jpg	\N
518	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6533930897712708, "bbox": [37, 69, 89, 103], "frame_number": 15195, "first_seen_time": "2025-12-07T13:37:45.834384", "duration": 0.0}	2025-12-07 13:37:45+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_518_1764341204704370850_20251207133746.jpg	\N
519	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6338156461715698, "bbox": [369, 52, 395, 72], "frame_number": 15195, "first_seen_time": "2025-12-07T13:37:45.834384", "duration": 0.0}	2025-12-07 13:37:45+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_519_1764341204704370850_20251207133746.jpg	\N
520	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6019636392593384, "bbox": [50, 30, 83, 49], "frame_number": 15195, "first_seen_time": "2025-12-07T13:37:45.834384", "duration": 0.0}	2025-12-07 13:37:45+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_520_1764341204704370850_20251207133746.jpg	\N
521	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4421810507774353, "bbox": [325, 38, 350, 59], "frame_number": 15195, "first_seen_time": "2025-12-07T13:37:45.834384", "duration": 0.0}	2025-12-07 13:37:45+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_521_1764341204704370850_20251207133746.jpg	\N
522	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7479467391967773, "bbox": [41, 50, 85, 81], "frame_number": 15265, "first_seen_time": "2025-12-07T13:37:50.857589", "duration": 0.0}	2025-12-07 13:37:50+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_522_1764341204704370850_20251207133751.jpg	\N
523	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.45611298084259033, "bbox": [362, 32, 381, 46], "frame_number": 15265, "first_seen_time": "2025-12-07T13:37:50.857589", "duration": 0.0}	2025-12-07 13:37:50+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_523_1764341204704370850_20251207133751.jpg	\N
524	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.8580804467201233, "bbox": [142, 244, 248, 354], "frame_number": 15340, "first_seen_time": "2025-12-07T13:37:56.216144", "duration": 0.0}	2025-12-07 13:37:56+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_524_1764341204704370850_20251207133756.jpg	\N
525	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6867262721061707, "bbox": [387, 85, 427, 121], "frame_number": 15340, "first_seen_time": "2025-12-07T13:37:56.216144", "duration": 0.0}	2025-12-07 13:37:56+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_525_1764341204704370850_20251207133756.jpg	\N
526	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6420819163322449, "bbox": [155, 22, 183, 47], "frame_number": 15340, "first_seen_time": "2025-12-07T13:37:56.216144", "duration": 0.0}	2025-12-07 13:37:56+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_526_1764341204704370850_20251207133756.jpg	\N
527	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5640964508056641, "bbox": [30, 35, 61, 60], "frame_number": 15340, "first_seen_time": "2025-12-07T13:37:56.216144", "duration": 0.0}	2025-12-07 13:37:56+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_527_1764341204704370850_20251207133757.jpg	\N
528	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.44044601917266846, "bbox": [370, 21, 387, 35], "frame_number": 15340, "first_seen_time": "2025-12-07T13:37:56.216144", "duration": 0.0}	2025-12-07 13:37:56+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_528_1764341204704370850_20251207133757.jpg	\N
529	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7698030471801758, "bbox": [136, 147, 203, 202], "frame_number": 15415, "first_seen_time": "2025-12-07T13:38:01.502395", "duration": 0.0}	2025-12-07 13:38:01+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_529_1764341204704370850_20251207133801.jpg	\N
530	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7422324419021606, "bbox": [404, 165, 467, 224], "frame_number": 15415, "first_seen_time": "2025-12-07T13:38:01.502395", "duration": 0.0}	2025-12-07 13:38:01+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_530_1764341204704370850_20251207133802.jpg	\N
531	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5060923099517822, "bbox": [158, 21, 181, 32], "frame_number": 15415, "first_seen_time": "2025-12-07T13:38:01.502395", "duration": 0.0}	2025-12-07 13:38:01+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_531_1764341204704370850_20251207133802.jpg	\N
532	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.34323325753211975, "bbox": [0, 72, 27, 108], "frame_number": 15415, "first_seen_time": "2025-12-07T13:38:01.502395", "duration": 0.0}	2025-12-07 13:38:01+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_532_1764341204704370850_20251207133802.jpg	\N
533	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6847574710845947, "bbox": [233, 118, 279, 162], "frame_number": 15485, "first_seen_time": "2025-12-07T13:38:06.508224", "duration": 0.0}	2025-12-07 13:38:06+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_533_1764341204704370850_20251207133806.jpg	\N
534	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.632986843585968, "bbox": [370, 55, 398, 75], "frame_number": 15485, "first_seen_time": "2025-12-07T13:38:06.508224", "duration": 0.0}	2025-12-07 13:38:06+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_534_1764341204704370850_20251207133807.jpg	\N
535	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5768290758132935, "bbox": [146, 284, 245, 356], "frame_number": 15485, "first_seen_time": "2025-12-07T13:38:06.508224", "duration": 0.0}	2025-12-07 13:38:06+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_535_1764341204704370850_20251207133807.jpg	\N
536	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5113110542297363, "bbox": [124, 30, 150, 48], "frame_number": 15485, "first_seen_time": "2025-12-07T13:38:06.508224", "duration": 0.0}	2025-12-07 13:38:06+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_536_1764341204704370850_20251207133807.jpg	\N
537	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5053322315216064, "bbox": [286, 52, 309, 71], "frame_number": 15485, "first_seen_time": "2025-12-07T13:38:06.508224", "duration": 0.0}	2025-12-07 13:38:06+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_537_1764341204704370850_20251207133807.jpg	\N
538	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.47006916999816895, "bbox": [27, 31, 62, 57], "frame_number": 15485, "first_seen_time": "2025-12-07T13:38:06.508224", "duration": 0.0}	2025-12-07 13:38:06+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_538_1764341204704370850_20251207133808.jpg	\N
539	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.263405442237854, "bbox": [323, 60, 355, 94], "frame_number": 15485, "first_seen_time": "2025-12-07T13:38:06.508224", "duration": 0.0}	2025-12-07 13:38:06+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_539_1764341204704370850_20251207133808.jpg	\N
540	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7071955800056458, "bbox": [230, 158, 281, 210], "frame_number": 15560, "first_seen_time": "2025-12-07T13:38:11.782412", "duration": 0.0}	2025-12-07 13:38:11+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_540_1764341204704370850_20251207133812.jpg	\N
541	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4677621126174927, "bbox": [382, 64, 414, 96], "frame_number": 15560, "first_seen_time": "2025-12-07T13:38:11.782412", "duration": 0.0}	2025-12-07 13:38:11+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_541_1764341204704370850_20251207133812.jpg	\N
542	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3874557316303253, "bbox": [153, 15, 173, 35], "frame_number": 15560, "first_seen_time": "2025-12-07T13:38:11.782412", "duration": 0.0}	2025-12-07 13:38:11+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_542_1764341204704370850_20251207133812.jpg	\N
543	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.38730356097221375, "bbox": [123, 12, 147, 28], "frame_number": 15560, "first_seen_time": "2025-12-07T13:38:11.782412", "duration": 0.0}	2025-12-07 13:38:11+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_543_1764341204704370850_20251207133812.jpg	\N
544	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3376615345478058, "bbox": [171, 27, 194, 41], "frame_number": 15560, "first_seen_time": "2025-12-07T13:38:11.782412", "duration": 0.0}	2025-12-07 13:38:11+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_544_1764341204704370850_20251207133813.jpg	\N
545	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.2523464858531952, "bbox": [301, 6, 319, 29], "frame_number": 15560, "first_seen_time": "2025-12-07T13:38:11.782412", "duration": 0.0}	2025-12-07 13:38:11+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_545_1764341204704370850_20251207133813.jpg	\N
546	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6054941415786743, "bbox": [39, 40, 77, 64], "frame_number": 15635, "first_seen_time": "2025-12-07T13:38:17.153663", "duration": 0.0}	2025-12-07 13:38:17+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_546_1764341204704370850_20251207133817.jpg	\N
547	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4462311267852783, "bbox": [178, 9, 198, 24], "frame_number": 15635, "first_seen_time": "2025-12-07T13:38:17.153663", "duration": 0.0}	2025-12-07 13:38:17+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_547_1764341204704370850_20251207133817.jpg	\N
548	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.40748053789138794, "bbox": [96, 20, 123, 36], "frame_number": 15635, "first_seen_time": "2025-12-07T13:38:17.153663", "duration": 0.0}	2025-12-07 13:38:17+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_548_1764341204704370850_20251207133817.jpg	\N
549	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.38508841395378113, "bbox": [398, 43, 421, 59], "frame_number": 15635, "first_seen_time": "2025-12-07T13:38:17.153663", "duration": 0.0}	2025-12-07 13:38:17+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_549_1764341204704370850_20251207133818.jpg	\N
550	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3805972635746002, "bbox": [279, 46, 304, 68], "frame_number": 15635, "first_seen_time": "2025-12-07T13:38:17.153663", "duration": 0.0}	2025-12-07 13:38:17+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_550_1764341204704370850_20251207133818.jpg	\N
551	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3568303883075714, "bbox": [156, 3, 172, 16], "frame_number": 15635, "first_seen_time": "2025-12-07T13:38:17.153663", "duration": 0.0}	2025-12-07 13:38:17+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_551_1764341204704370850_20251207133818.jpg	\N
552	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.779992938041687, "bbox": [478, 273, 596, 353], "frame_number": 15710, "first_seen_time": "2025-12-07T13:38:22.403493", "duration": 0.0}	2025-12-07 13:38:22+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_552_1764341204704370850_20251207133822.jpg	\N
553	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.703775942325592, "bbox": [288, 47, 313, 66], "frame_number": 15710, "first_seen_time": "2025-12-07T13:38:22.403493", "duration": 0.0}	2025-12-07 13:38:22+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_553_1764341204704370850_20251207133823.jpg	\N
554	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6838749647140503, "bbox": [391, 94, 429, 129], "frame_number": 15710, "first_seen_time": "2025-12-07T13:38:22.403493", "duration": 0.0}	2025-12-07 13:38:22+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_554_1764341204704370850_20251207133823.jpg	\N
555	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5820649266242981, "bbox": [72, 44, 109, 70], "frame_number": 15710, "first_seen_time": "2025-12-07T13:38:22.403493", "duration": 0.0}	2025-12-07 13:38:22+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_555_1764341204704370850_20251207133823.jpg	\N
556	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5816323757171631, "bbox": [325, 78, 354, 104], "frame_number": 15710, "first_seen_time": "2025-12-07T13:38:22.403493", "duration": 0.0}	2025-12-07 13:38:22+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_556_1764341204704370850_20251207133823.jpg	\N
557	truck	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4758954346179962, "bbox": [204, 78, 248, 114], "frame_number": 15710, "first_seen_time": "2025-12-07T13:38:22.403493", "duration": 0.0}	2025-12-07 13:38:22+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_557_1764341204704370850_20251207133824.jpg	\N
558	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.35925203561782837, "bbox": [205, 77, 248, 114], "frame_number": 15710, "first_seen_time": "2025-12-07T13:38:22.403493", "duration": 0.0}	2025-12-07 13:38:22+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_558_1764341204704370850_20251207133824.jpg	\N
559	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3584290146827698, "bbox": [365, 26, 383, 39], "frame_number": 15710, "first_seen_time": "2025-12-07T13:38:22.403493", "duration": 0.0}	2025-12-07 13:38:22+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_559_1764341204704370850_20251207133824.jpg	\N
560	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3257044851779938, "bbox": [325, 27, 343, 41], "frame_number": 15710, "first_seen_time": "2025-12-07T13:38:22.403493", "duration": 0.0}	2025-12-07 13:38:22+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_560_1764341204704370850_20251207133824.jpg	\N
561	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6846523284912109, "bbox": [372, 56, 398, 77], "frame_number": 15790, "first_seen_time": "2025-12-07T13:38:28.092541", "duration": 0.0}	2025-12-07 13:38:28+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_561_1764341204704370850_20251207133828.jpg	\N
562	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.46843037009239197, "bbox": [269, 75, 297, 101], "frame_number": 15790, "first_seen_time": "2025-12-07T13:38:28.092541", "duration": 0.0}	2025-12-07 13:38:28+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_562_1764341204704370850_20251207133828.jpg	\N
563	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.2731562554836273, "bbox": [325, 53, 346, 68], "frame_number": 15790, "first_seen_time": "2025-12-07T13:38:28.092541", "duration": 0.0}	2025-12-07 13:38:28+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_563_1764341204704370850_20251207133828.jpg	\N
564	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7330346703529358, "bbox": [482, 287, 598, 353], "frame_number": 15860, "first_seen_time": "2025-12-07T13:38:33.123311", "duration": 0.0}	2025-12-07 13:38:33+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_564_1764341204704370850_20251207133833.jpg	\N
565	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.668247640132904, "bbox": [177, 207, 260, 297], "frame_number": 15860, "first_seen_time": "2025-12-07T13:38:33.123311", "duration": 0.0}	2025-12-07 13:38:33+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_565_1764341204704370850_20251207133833.jpg	\N
566	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6328766345977783, "bbox": [291, 38, 314, 58], "frame_number": 15860, "first_seen_time": "2025-12-07T13:38:33.123311", "duration": 0.0}	2025-12-07 13:38:33+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_566_1764341204704370850_20251207133833.jpg	\N
567	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5573391318321228, "bbox": [274, 81, 307, 110], "frame_number": 15860, "first_seen_time": "2025-12-07T13:38:33.123311", "duration": 0.0}	2025-12-07 13:38:33+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_567_1764341204704370850_20251207133834.jpg	\N
568	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3583686649799347, "bbox": [80, 44, 113, 65], "frame_number": 15860, "first_seen_time": "2025-12-07T13:38:33.123311", "duration": 0.0}	2025-12-07 13:38:33+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_568_1764341204704370850_20251207133834.jpg	\N
569	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6984907388687134, "bbox": [382, 66, 417, 100], "frame_number": 15935, "first_seen_time": "2025-12-07T13:38:38.425071", "duration": 0.0}	2025-12-07 13:38:38+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_569_1764341204704370850_20251207133838.jpg	\N
570	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5773882865905762, "bbox": [322, 43, 342, 61], "frame_number": 15935, "first_seen_time": "2025-12-07T13:38:38.425071", "duration": 0.0}	2025-12-07 13:38:38+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_570_1764341204704370850_20251207133838.jpg	\N
571	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3504648804664612, "bbox": [166, 23, 191, 44], "frame_number": 15935, "first_seen_time": "2025-12-07T13:38:38.425071", "duration": 0.0}	2025-12-07 13:38:38+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_571_1764341204704370850_20251207133839.jpg	\N
572	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.27963510155677795, "bbox": [325, 15, 344, 28], "frame_number": 15935, "first_seen_time": "2025-12-07T13:38:38.425071", "duration": 0.0}	2025-12-07 13:38:38+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_572_1764341204704370850_20251207133839.jpg	\N
573	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.753007709980011, "bbox": [433, 81, 474, 114], "frame_number": 16010, "first_seen_time": "2025-12-07T13:38:43.752433", "duration": 0.0}	2025-12-07 13:38:43+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_573_1764341204704370850_20251207133844.jpg	\N
574	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6596154570579529, "bbox": [367, 51, 398, 77], "frame_number": 16010, "first_seen_time": "2025-12-07T13:38:43.752433", "duration": 0.0}	2025-12-07 13:38:43+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_574_1764341204704370850_20251207133844.jpg	\N
575	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5023384094238281, "bbox": [320, 84, 350, 114], "frame_number": 16010, "first_seen_time": "2025-12-07T13:38:43.752433", "duration": 0.0}	2025-12-07 13:38:43+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_575_1764341204704370850_20251207133844.jpg	\N
576	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4991588592529297, "bbox": [107, 14, 130, 30], "frame_number": 16010, "first_seen_time": "2025-12-07T13:38:43.752433", "duration": 0.0}	2025-12-07 13:38:43+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_576_1764341204704370850_20251207133844.jpg	\N
577	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4852277636528015, "bbox": [456, 280, 575, 354], "frame_number": 16010, "first_seen_time": "2025-12-07T13:38:43.752433", "duration": 0.0}	2025-12-07 13:38:43+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_577_1764341204704370850_20251207133845.jpg	\N
578	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4419427812099457, "bbox": [0, 58, 29, 84], "frame_number": 16010, "first_seen_time": "2025-12-07T13:38:43.752433", "duration": 0.0}	2025-12-07 13:38:43+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_578_1764341204704370850_20251207133845.jpg	\N
579	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4159083962440491, "bbox": [105, 59, 136, 77], "frame_number": 16010, "first_seen_time": "2025-12-07T13:38:43.752433", "duration": 0.0}	2025-12-07 13:38:43+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_579_1764341204704370850_20251207133845.jpg	\N
580	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.35915327072143555, "bbox": [40, 49, 86, 82], "frame_number": 16010, "first_seen_time": "2025-12-07T13:38:43.752433", "duration": 0.0}	2025-12-07 13:38:43+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_580_1764341204704370850_20251207133845.jpg	\N
581	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3428550958633423, "bbox": [168, 0, 189, 19], "frame_number": 16010, "first_seen_time": "2025-12-07T13:38:43.752433", "duration": 0.0}	2025-12-07 13:38:43+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_581_1764341204704370850_20251207133846.jpg	\N
582	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.33889544010162354, "bbox": [142, 36, 171, 53], "frame_number": 16010, "first_seen_time": "2025-12-07T13:38:43.752433", "duration": 0.0}	2025-12-07 13:38:43+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_582_1764341204704370850_20251207133846.jpg	\N
583	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6566884517669678, "bbox": [324, 125, 368, 169], "frame_number": 16085, "first_seen_time": "2025-12-07T13:38:49.055618", "duration": 0.0}	2025-12-07 13:38:49+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_583_1764341204704370850_20251207133849.jpg	\N
584	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5821230411529541, "bbox": [0, 42, 43, 84], "frame_number": 16085, "first_seen_time": "2025-12-07T13:38:49.055618", "duration": 0.0}	2025-12-07 13:38:49+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_584_1764341204704370850_20251207133849.jpg	\N
585	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5797235369682312, "bbox": [286, 52, 307, 71], "frame_number": 16085, "first_seen_time": "2025-12-07T13:38:49.055618", "duration": 0.0}	2025-12-07 13:38:49+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_585_1764341204704370850_20251207133849.jpg	\N
586	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.258163183927536, "bbox": [391, 37, 413, 53], "frame_number": 16085, "first_seen_time": "2025-12-07T13:38:49.055618", "duration": 0.0}	2025-12-07 13:38:49+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_586_1764341204704370850_20251207133850.jpg	\N
587	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5737122297286987, "bbox": [145, 29, 172, 52], "frame_number": 16160, "first_seen_time": "2025-12-07T13:38:54.308624", "duration": 0.0}	2025-12-07 13:38:54+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_587_1764341204704370850_20251207133854.jpg	\N
588	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5461495518684387, "bbox": [387, 94, 426, 129], "frame_number": 16160, "first_seen_time": "2025-12-07T13:38:54.308624", "duration": 0.0}	2025-12-07 13:38:54+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_588_1764341204704370850_20251207133854.jpg	\N
589	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5049135684967041, "bbox": [93, 32, 122, 47], "frame_number": 16160, "first_seen_time": "2025-12-07T13:38:54.308624", "duration": 0.0}	2025-12-07 13:38:54+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_589_1764341204704370850_20251207133855.jpg	\N
590	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4930739402770996, "bbox": [357, 26, 379, 43], "frame_number": 16160, "first_seen_time": "2025-12-07T13:38:54.308624", "duration": 0.0}	2025-12-07 13:38:54+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_590_1764341204704370850_20251207133855.jpg	\N
591	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.33535078167915344, "bbox": [321, 75, 358, 113], "frame_number": 16160, "first_seen_time": "2025-12-07T13:38:54.308624", "duration": 0.0}	2025-12-07 13:38:54+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_591_1764341204704370850_20251207133855.jpg	\N
592	truck	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3144421875476837, "bbox": [321, 76, 358, 113], "frame_number": 16160, "first_seen_time": "2025-12-07T13:38:54.308624", "duration": 0.0}	2025-12-07 13:38:54+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_592_1764341204704370850_20251207133855.jpg	\N
593	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3079072833061218, "bbox": [112, 15, 136, 29], "frame_number": 16160, "first_seen_time": "2025-12-07T13:38:54.308624", "duration": 0.0}	2025-12-07 13:38:54+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_593_1764341204704370850_20251207133856.jpg	\N
594	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6024297475814819, "bbox": [115, 30, 143, 50], "frame_number": 16235, "first_seen_time": "2025-12-07T13:38:59.551911", "duration": 0.0}	2025-12-07 13:38:59+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_594_1764341204704370850_20251207133859.jpg	\N
595	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.522853672504425, "bbox": [367, 45, 391, 64], "frame_number": 16235, "first_seen_time": "2025-12-07T13:38:59.551911", "duration": 0.0}	2025-12-07 13:38:59+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_595_1764341204704370850_20251207133900.jpg	\N
596	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5183380246162415, "bbox": [53, 29, 83, 46], "frame_number": 16235, "first_seen_time": "2025-12-07T13:38:59.551911", "duration": 0.0}	2025-12-07 13:38:59+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_596_1764341204704370850_20251207133900.jpg	\N
597	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7670751214027405, "bbox": [412, 149, 480, 214], "frame_number": 16310, "first_seen_time": "2025-12-07T13:39:04.801071", "duration": 0.0}	2025-12-07 13:39:04+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_597_1764341204704370850_20251207133905.jpg	\N
598	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6803207397460938, "bbox": [375, 34, 394, 50], "frame_number": 16310, "first_seen_time": "2025-12-07T13:39:04.801071", "duration": 0.0}	2025-12-07 13:39:04+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_598_1764341204704370850_20251207133905.jpg	\N
599	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.503186047077179, "bbox": [287, 42, 307, 59], "frame_number": 16310, "first_seen_time": "2025-12-07T13:39:04.801071", "duration": 0.0}	2025-12-07 13:39:04+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_599_1764341204704370850_20251207133905.jpg	\N
600	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4459373652935028, "bbox": [186, 12, 211, 30], "frame_number": 16310, "first_seen_time": "2025-12-07T13:39:04.801071", "duration": 0.0}	2025-12-07 13:39:04+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_600_1764341204704370850_20251207133905.jpg	\N
601	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7731273770332336, "bbox": [40, 69, 91, 108], "frame_number": 16385, "first_seen_time": "2025-12-07T13:39:10.040902", "duration": 0.0}	2025-12-07 13:39:10+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_601_1764341204704370850_20251207133910.jpg	\N
602	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5683797597885132, "bbox": [0, 44, 18, 68], "frame_number": 16385, "first_seen_time": "2025-12-07T13:39:10.040902", "duration": 0.0}	2025-12-07 13:39:10+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_602_1764341204704370850_20251207133910.jpg	\N
603	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4486178457736969, "bbox": [71, 39, 111, 66], "frame_number": 16385, "first_seen_time": "2025-12-07T13:39:10.040902", "duration": 0.0}	2025-12-07 13:39:10+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_603_1764341204704370850_20251207133910.jpg	\N
604	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.25267308950424194, "bbox": [190, 8, 207, 19], "frame_number": 16385, "first_seen_time": "2025-12-07T13:39:10.040902", "duration": 0.0}	2025-12-07 13:39:10+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_604_1764341204704370850_20251207133911.jpg	\N
605	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.808991551399231, "bbox": [188, 180, 259, 251], "frame_number": 16460, "first_seen_time": "2025-12-07T13:39:15.349689", "duration": 0.0}	2025-12-07 13:39:15+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_605_1764341204704370850_20251207133915.jpg	\N
606	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.625340461730957, "bbox": [377, 65, 406, 97], "frame_number": 16460, "first_seen_time": "2025-12-07T13:39:15.349689", "duration": 0.0}	2025-12-07 13:39:15+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_606_1764341204704370850_20251207133915.jpg	\N
607	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6161125302314758, "bbox": [276, 67, 305, 92], "frame_number": 16460, "first_seen_time": "2025-12-07T13:39:15.349689", "duration": 0.0}	2025-12-07 13:39:15+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_607_1764341204704370850_20251207133916.jpg	\N
608	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6009103655815125, "bbox": [322, 86, 362, 129], "frame_number": 16460, "first_seen_time": "2025-12-07T13:39:15.349689", "duration": 0.0}	2025-12-07 13:39:15+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_608_1764341204704370850_20251207133916.jpg	\N
609	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5687953233718872, "bbox": [65, 22, 98, 44], "frame_number": 16460, "first_seen_time": "2025-12-07T13:39:15.349689", "duration": 0.0}	2025-12-07 13:39:15+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_609_1764341204704370850_20251207133916.jpg	\N
610	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3737778067588806, "bbox": [321, 52, 348, 71], "frame_number": 16460, "first_seen_time": "2025-12-07T13:39:15.349689", "duration": 0.0}	2025-12-07 13:39:15+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_610_1764341204704370850_20251207133916.jpg	\N
611	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3193245530128479, "bbox": [154, 21, 176, 36], "frame_number": 16460, "first_seen_time": "2025-12-07T13:39:15.349689", "duration": 0.0}	2025-12-07 13:39:15+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_611_1764341204704370850_20251207133917.jpg	\N
612	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7753346562385559, "bbox": [155, 282, 249, 357], "frame_number": 16535, "first_seen_time": "2025-12-07T13:39:20.587439", "duration": 0.0}	2025-12-07 13:39:20+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_612_1764341204704370850_20251207133920.jpg	\N
613	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4681275486946106, "bbox": [324, 27, 343, 42], "frame_number": 16535, "first_seen_time": "2025-12-07T13:39:20.587439", "duration": 0.0}	2025-12-07 13:39:20+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_613_1764341204704370850_20251207133921.jpg	\N
614	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.42744332551956177, "bbox": [391, 88, 429, 126], "frame_number": 16535, "first_seen_time": "2025-12-07T13:39:20.587439", "duration": 0.0}	2025-12-07 13:39:20+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_614_1764341204704370850_20251207133921.jpg	\N
615	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.31971150636672974, "bbox": [298, 18, 315, 36], "frame_number": 16535, "first_seen_time": "2025-12-07T13:39:20.587439", "duration": 0.0}	2025-12-07 13:39:20+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_615_1764341204704370850_20251207133921.jpg	\N
616	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7555640935897827, "bbox": [385, 59, 410, 81], "frame_number": 16610, "first_seen_time": "2025-12-07T13:39:25.831629", "duration": 0.0}	2025-12-07 13:39:25+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_616_1764341204704370850_20251207133926.jpg	\N
617	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.642647385597229, "bbox": [118, 49, 152, 69], "frame_number": 16610, "first_seen_time": "2025-12-07T13:39:25.831629", "duration": 0.0}	2025-12-07 13:39:25+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_617_1764341204704370850_20251207133926.jpg	\N
618	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5592110753059387, "bbox": [271, 72, 301, 98], "frame_number": 16610, "first_seen_time": "2025-12-07T13:39:25.831629", "duration": 0.0}	2025-12-07 13:39:25+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_618_1764341204704370850_20251207133926.jpg	\N
619	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.32104647159576416, "bbox": [293, 33, 312, 47], "frame_number": 16610, "first_seen_time": "2025-12-07T13:39:25.831629", "duration": 0.0}	2025-12-07 13:39:25+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_619_1764341204704370850_20251207133926.jpg	\N
620	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7479737401008606, "bbox": [407, 136, 462, 187], "frame_number": 16685, "first_seen_time": "2025-12-07T13:39:31.091889", "duration": 0.0}	2025-12-07 13:39:31+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_620_1764341204704370850_20251207133931.jpg	\N
621	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7365229725837708, "bbox": [277, 65, 306, 91], "frame_number": 16685, "first_seen_time": "2025-12-07T13:39:31.091889", "duration": 0.0}	2025-12-07 13:39:31+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_621_1764341204704370850_20251207133931.jpg	\N
622	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6950486898422241, "bbox": [324, 105, 358, 140], "frame_number": 16685, "first_seen_time": "2025-12-07T13:39:31.091889", "duration": 0.0}	2025-12-07 13:39:31+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_622_1764341204704370850_20251207133931.jpg	\N
623	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6643550395965576, "bbox": [149, 123, 217, 177], "frame_number": 16685, "first_seen_time": "2025-12-07T13:39:31.091889", "duration": 0.0}	2025-12-07 13:39:31+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_623_1764341204704370850_20251207133932.jpg	\N
624	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.29517608880996704, "bbox": [324, 36, 345, 52], "frame_number": 16685, "first_seen_time": "2025-12-07T13:39:31.091889", "duration": 0.0}	2025-12-07 13:39:31+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_624_1764341204704370850_20251207133932.jpg	\N
625	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.261179119348526, "bbox": [117, 31, 147, 51], "frame_number": 16685, "first_seen_time": "2025-12-07T13:39:31.091889", "duration": 0.0}	2025-12-07 13:39:31+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_625_1764341204704370850_20251207133932.jpg	\N
626	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7083748579025269, "bbox": [229, 143, 279, 190], "frame_number": 16760, "first_seen_time": "2025-12-07T13:39:36.403813", "duration": 0.0}	2025-12-07 13:39:36+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_626_1764341204704370850_20251207133936.jpg	\N
627	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5810142755508423, "bbox": [386, 91, 424, 121], "frame_number": 16760, "first_seen_time": "2025-12-07T13:39:36.403813", "duration": 0.0}	2025-12-07 13:39:36+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_627_1764341204704370850_20251207133936.jpg	\N
628	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5670445561408997, "bbox": [323, 81, 353, 107], "frame_number": 16760, "first_seen_time": "2025-12-07T13:39:36.403813", "duration": 0.0}	2025-12-07 13:39:36+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_628_1764341204704370850_20251207133937.jpg	\N
629	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7390888333320618, "bbox": [286, 53, 313, 78], "frame_number": 16835, "first_seen_time": "2025-12-07T13:39:41.660703", "duration": 0.0}	2025-12-07 13:39:41+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_629_1764341204704370850_20251207133941.jpg	\N
630	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6693606376647949, "bbox": [254, 118, 296, 160], "frame_number": 16835, "first_seen_time": "2025-12-07T13:39:41.660703", "duration": 0.0}	2025-12-07 13:39:41+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_630_1764341204704370850_20251207133942.jpg	\N
631	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.562918484210968, "bbox": [399, 63, 427, 88], "frame_number": 16835, "first_seen_time": "2025-12-07T13:39:41.660703", "duration": 0.0}	2025-12-07 13:39:41+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_631_1764341204704370850_20251207133942.jpg	\N
632	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3046784996986389, "bbox": [0, 53, 28, 84], "frame_number": 16835, "first_seen_time": "2025-12-07T13:39:41.660703", "duration": 0.0}	2025-12-07 13:39:41+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_632_1764341204704370850_20251207133942.jpg	\N
633	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.2723316550254822, "bbox": [118, 31, 144, 50], "frame_number": 16835, "first_seen_time": "2025-12-07T13:39:41.660703", "duration": 0.0}	2025-12-07 13:39:41+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_633_1764341204704370850_20251207133942.jpg	\N
634	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6312204599380493, "bbox": [376, 28, 396, 45], "frame_number": 16910, "first_seen_time": "2025-12-07T13:39:46.905643", "duration": 0.0}	2025-12-07 13:39:46+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_634_1764341204704370850_20251207133947.jpg	\N
635	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5756151080131531, "bbox": [318, 60, 344, 82], "frame_number": 16910, "first_seen_time": "2025-12-07T13:39:46.905643", "duration": 0.0}	2025-12-07 13:39:46+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_635_1764341204704370850_20251207133947.jpg	\N
636	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5680029392242432, "bbox": [391, 88, 436, 131], "frame_number": 16910, "first_seen_time": "2025-12-07T13:39:46.905643", "duration": 0.0}	2025-12-07 13:39:46+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_636_1764341204704370850_20251207133947.jpg	\N
637	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7055051922798157, "bbox": [457, 109, 513, 151], "frame_number": 16985, "first_seen_time": "2025-12-07T13:39:52.189934", "duration": 0.0}	2025-12-07 13:39:52+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_637_1764341204704370850_20251207133952.jpg	\N
638	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6744903922080994, "bbox": [43, 43, 80, 64], "frame_number": 16985, "first_seen_time": "2025-12-07T13:39:52.189934", "duration": 0.0}	2025-12-07 13:39:52+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_638_1764341204704370850_20251207133952.jpg	\N
639	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.61838299036026, "bbox": [374, 68, 405, 100], "frame_number": 16985, "first_seen_time": "2025-12-07T13:39:52.189934", "duration": 0.0}	2025-12-07 13:39:52+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_639_1764341204704370850_20251207133952.jpg	\N
640	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.554639458656311, "bbox": [92, 34, 128, 60], "frame_number": 16985, "first_seen_time": "2025-12-07T13:39:52.189934", "duration": 0.0}	2025-12-07 13:39:52+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_640_1764341204704370850_20251207133953.jpg	\N
641	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5335743427276611, "bbox": [316, 128, 358, 169], "frame_number": 16985, "first_seen_time": "2025-12-07T13:39:52.189934", "duration": 0.0}	2025-12-07 13:39:52+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_641_1764341204704370850_20251207133953.jpg	\N
642	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5099079012870789, "bbox": [150, 38, 174, 54], "frame_number": 16985, "first_seen_time": "2025-12-07T13:39:52.189934", "duration": 0.0}	2025-12-07 13:39:52+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_642_1764341204704370850_20251207133953.jpg	\N
643	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.48790594935417175, "bbox": [128, 9, 147, 23], "frame_number": 16985, "first_seen_time": "2025-12-07T13:39:52.189934", "duration": 0.0}	2025-12-07 13:39:52+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_643_1764341204704370850_20251207133954.jpg	\N
644	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3301283121109009, "bbox": [0, 40, 26, 68], "frame_number": 16985, "first_seen_time": "2025-12-07T13:39:52.189934", "duration": 0.0}	2025-12-07 13:39:52+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_644_1764341204704370850_20251207133954.jpg	\N
645	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6033152341842651, "bbox": [323, 151, 374, 205], "frame_number": 17065, "first_seen_time": "2025-12-07T13:39:57.848430", "duration": 0.0}	2025-12-07 13:39:57+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_645_1764341204704370850_20251207133958.jpg	\N
646	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5923474431037903, "bbox": [278, 59, 304, 82], "frame_number": 17065, "first_seen_time": "2025-12-07T13:39:57.848430", "duration": 0.0}	2025-12-07 13:39:57+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_646_1764341204704370850_20251207133958.jpg	\N
647	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4877713620662689, "bbox": [24, 38, 61, 74], "frame_number": 17065, "first_seen_time": "2025-12-07T13:39:57.848430", "duration": 0.0}	2025-12-07 13:39:57+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_647_1764341204704370850_20251207133958.jpg	\N
648	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.36137691140174866, "bbox": [397, 42, 416, 56], "frame_number": 17065, "first_seen_time": "2025-12-07T13:39:57.848430", "duration": 0.0}	2025-12-07 13:39:57+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_648_1764341204704370850_20251207133959.jpg	\N
649	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7531018257141113, "bbox": [361, 33, 383, 53], "frame_number": 17135, "first_seen_time": "2025-12-07T13:40:02.858373", "duration": 0.0}	2025-12-07 13:40:02+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_649_1764341204704370850_20251207134003.jpg	\N
650	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6476051211357117, "bbox": [400, 134, 454, 182], "frame_number": 17135, "first_seen_time": "2025-12-07T13:40:02.858373", "duration": 0.0}	2025-12-07 13:40:02+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_650_1764341204704370850_20251207134003.jpg	\N
651	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5815461277961731, "bbox": [129, 13, 154, 34], "frame_number": 17135, "first_seen_time": "2025-12-07T13:40:02.858373", "duration": 0.0}	2025-12-07 13:40:02+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_651_1764341204704370850_20251207134003.jpg	\N
652	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5104610919952393, "bbox": [173, 21, 196, 37], "frame_number": 17135, "first_seen_time": "2025-12-07T13:40:02.858373", "duration": 0.0}	2025-12-07 13:40:02+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_652_1764341204704370850_20251207134004.jpg	\N
653	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.40249183773994446, "bbox": [319, 111, 367, 164], "frame_number": 17135, "first_seen_time": "2025-12-07T13:40:02.858373", "duration": 0.0}	2025-12-07 13:40:02+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_653_1764341204704370850_20251207134004.jpg	\N
654	truck	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.2759625017642975, "bbox": [319, 101, 368, 163], "frame_number": 17135, "first_seen_time": "2025-12-07T13:40:02.858373", "duration": 0.0}	2025-12-07 13:40:02+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_654_1764341204704370850_20251207134004.jpg	\N
655	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5603576898574829, "bbox": [376, 65, 406, 93], "frame_number": 17205, "first_seen_time": "2025-12-07T13:40:07.858726", "duration": 0.0}	2025-12-07 13:40:07+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_655_1764341204704370850_20251207134008.jpg	\N
656	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.525901198387146, "bbox": [155, 16, 179, 33], "frame_number": 17205, "first_seen_time": "2025-12-07T13:40:07.858726", "duration": 0.0}	2025-12-07 13:40:07+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_656_1764341204704370850_20251207134008.jpg	\N
657	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.2591364085674286, "bbox": [105, 18, 129, 31], "frame_number": 17205, "first_seen_time": "2025-12-07T13:40:07.858726", "duration": 0.0}	2025-12-07 13:40:07+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_657_1764341204704370850_20251207134008.jpg	\N
658	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.859043538570404, "bbox": [451, 244, 575, 352], "frame_number": 17285, "first_seen_time": "2025-12-07T13:40:13.494772", "duration": 0.0}	2025-12-07 13:40:13+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_658_1764341204704370850_20251207134013.jpg	\N
659	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5493625402450562, "bbox": [378, 43, 400, 65], "frame_number": 17285, "first_seen_time": "2025-12-07T13:40:13.494772", "duration": 0.0}	2025-12-07 13:40:13+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_659_1764341204704370850_20251207134014.jpg	\N
660	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.47135454416275024, "bbox": [275, 59, 304, 80], "frame_number": 17285, "first_seen_time": "2025-12-07T13:40:13.494772", "duration": 0.0}	2025-12-07 13:40:13+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_660_1764341204704370850_20251207134014.jpg	\N
661	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.40441277623176575, "bbox": [201, 5, 225, 22], "frame_number": 17285, "first_seen_time": "2025-12-07T13:40:13.494772", "duration": 0.0}	2025-12-07 13:40:13+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_661_1764341204704370850_20251207134014.jpg	\N
662	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.25849950313568115, "bbox": [120, 12, 144, 30], "frame_number": 17285, "first_seen_time": "2025-12-07T13:40:13.494772", "duration": 0.0}	2025-12-07 13:40:13+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_662_1764341204704370850_20251207134014.jpg	\N
663	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7848584651947021, "bbox": [30, 30, 66, 55], "frame_number": 17360, "first_seen_time": "2025-12-07T13:40:18.750574", "duration": 0.0}	2025-12-07 13:40:18+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_663_1764341204704370850_20251207134019.jpg	\N
664	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6545947194099426, "bbox": [293, 28, 313, 46], "frame_number": 17360, "first_seen_time": "2025-12-07T13:40:18.750574", "duration": 0.0}	2025-12-07 13:40:18+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_664_1764341204704370850_20251207134019.jpg	\N
665	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5086437463760376, "bbox": [101, 48, 137, 77], "frame_number": 17360, "first_seen_time": "2025-12-07T13:40:18.750574", "duration": 0.0}	2025-12-07 13:40:18+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_665_1764341204704370850_20251207134019.jpg	\N
666	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.32004308700561523, "bbox": [202, 2, 218, 15], "frame_number": 17360, "first_seen_time": "2025-12-07T13:40:18.750574", "duration": 0.0}	2025-12-07 13:40:18+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_666_1764341204704370850_20251207134019.jpg	\N
667	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5921568274497986, "bbox": [108, 319, 212, 358], "frame_number": 17435, "first_seen_time": "2025-12-07T13:40:24.065985", "duration": 0.0}	2025-12-07 13:40:24+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_667_1764341204704370850_20251207134024.jpg	\N
668	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5550353527069092, "bbox": [98, 16, 125, 34], "frame_number": 17435, "first_seen_time": "2025-12-07T13:40:24.065985", "duration": 0.0}	2025-12-07 13:40:24+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_668_1764341204704370850_20251207134024.jpg	\N
669	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4339006245136261, "bbox": [322, 69, 350, 93], "frame_number": 17435, "first_seen_time": "2025-12-07T13:40:24.065985", "duration": 0.0}	2025-12-07 13:40:24+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_669_1764341204704370850_20251207134024.jpg	\N
670	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3939153850078583, "bbox": [317, 123, 371, 190], "frame_number": 17435, "first_seen_time": "2025-12-07T13:40:24.065985", "duration": 0.0}	2025-12-07 13:40:24+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_670_1764341204704370850_20251207134025.jpg	\N
671	truck	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.35554659366607666, "bbox": [317, 124, 371, 190], "frame_number": 17435, "first_seen_time": "2025-12-07T13:40:24.065985", "duration": 0.0}	2025-12-07 13:40:24+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_671_1764341204704370850_20251207134025.jpg	\N
672	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3124680817127228, "bbox": [357, 28, 376, 44], "frame_number": 17435, "first_seen_time": "2025-12-07T13:40:24.065985", "duration": 0.0}	2025-12-07 13:40:24+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_672_1764341204704370850_20251207134025.jpg	\N
673	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.661697268486023, "bbox": [403, 124, 457, 177], "frame_number": 17510, "first_seen_time": "2025-12-07T13:40:29.336662", "duration": 0.0}	2025-12-07 13:40:29+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_673_1764341204704370850_20251207134029.jpg	\N
674	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.568571150302887, "bbox": [321, 37, 342, 55], "frame_number": 17510, "first_seen_time": "2025-12-07T13:40:29.336662", "duration": 0.0}	2025-12-07 13:40:29+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_674_1764341204704370850_20251207134029.jpg	\N
675	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.47276607155799866, "bbox": [292, 18, 316, 46], "frame_number": 17510, "first_seen_time": "2025-12-07T13:40:29.336662", "duration": 0.0}	2025-12-07 13:40:29+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_675_1764341204704370850_20251207134030.jpg	\N
676	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.26137804985046387, "bbox": [253, 37, 276, 58], "frame_number": 17510, "first_seen_time": "2025-12-07T13:40:29.336662", "duration": 0.0}	2025-12-07 13:40:29+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_676_1764341204704370850_20251207134030.jpg	\N
677	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.622018039226532, "bbox": [392, 78, 421, 104], "frame_number": 17585, "first_seen_time": "2025-12-07T13:40:34.594489", "duration": 0.0}	2025-12-07 13:40:34+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_677_1764341204704370850_20251207134034.jpg	\N
678	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5814381241798401, "bbox": [154, 32, 180, 50], "frame_number": 17585, "first_seen_time": "2025-12-07T13:40:34.594489", "duration": 0.0}	2025-12-07 13:40:34+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_678_1764341204704370850_20251207134035.jpg	\N
679	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5697904825210571, "bbox": [251, 103, 289, 142], "frame_number": 17585, "first_seen_time": "2025-12-07T13:40:34.594489", "duration": 0.0}	2025-12-07 13:40:34+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_679_1764341204704370850_20251207134035.jpg	\N
680	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5275686979293823, "bbox": [361, 40, 383, 56], "frame_number": 17585, "first_seen_time": "2025-12-07T13:40:34.594489", "duration": 0.0}	2025-12-07 13:40:34+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_680_1764341204704370850_20251207134035.jpg	\N
681	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3285987675189972, "bbox": [288, 46, 308, 60], "frame_number": 17585, "first_seen_time": "2025-12-07T13:40:34.594489", "duration": 0.0}	2025-12-07 13:40:34+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_681_1764341204704370850_20251207134035.jpg	\N
682	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.28930434584617615, "bbox": [328, 33, 350, 50], "frame_number": 17585, "first_seen_time": "2025-12-07T13:40:34.594489", "duration": 0.0}	2025-12-07 13:40:34+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_682_1764341204704370850_20251207134036.jpg	\N
683	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.729152500629425, "bbox": [263, 92, 299, 128], "frame_number": 17660, "first_seen_time": "2025-12-07T13:40:39.833821", "duration": 0.0}	2025-12-07 13:40:39+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_683_1764341204704370850_20251207134040.jpg	\N
684	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6660876274108887, "bbox": [437, 213, 531, 304], "frame_number": 17660, "first_seen_time": "2025-12-07T13:40:39.833821", "duration": 0.0}	2025-12-07 13:40:39+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_684_1764341204704370850_20251207134040.jpg	\N
685	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6096623539924622, "bbox": [322, 149, 368, 200], "frame_number": 17660, "first_seen_time": "2025-12-07T13:40:39.833821", "duration": 0.0}	2025-12-07 13:40:39+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_685_1764341204704370850_20251207134040.jpg	\N
686	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5551711916923523, "bbox": [3, 36, 49, 61], "frame_number": 17660, "first_seen_time": "2025-12-07T13:40:39.833821", "duration": 0.0}	2025-12-07 13:40:39+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_686_1764341204704370850_20251207134040.jpg	\N
687	truck	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5380929112434387, "bbox": [13, 215, 152, 324], "frame_number": 17660, "first_seen_time": "2025-12-07T13:40:39.833821", "duration": 0.0}	2025-12-07 13:40:39+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_687_1764341204704370850_20251207134041.jpg	\N
688	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5138606429100037, "bbox": [371, 43, 393, 58], "frame_number": 17660, "first_seen_time": "2025-12-07T13:40:39.833821", "duration": 0.0}	2025-12-07 13:40:39+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_688_1764341204704370850_20251207134041.jpg	\N
689	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3032429814338684, "bbox": [149, 21, 173, 39], "frame_number": 17660, "first_seen_time": "2025-12-07T13:40:39.833821", "duration": 0.0}	2025-12-07 13:40:39+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_689_1764341204704370850_20251207134041.jpg	\N
690	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.30274641513824463, "bbox": [13, 216, 152, 323], "frame_number": 17660, "first_seen_time": "2025-12-07T13:40:39.833821", "duration": 0.0}	2025-12-07 13:40:39+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_690_1764341204704370850_20251207134041.jpg	\N
691	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6513339281082153, "bbox": [156, 237, 251, 342], "frame_number": 17735, "first_seen_time": "2025-12-07T13:40:44.998661", "duration": 0.0}	2025-12-07 13:40:44+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_691_1764341204704370850_20251207134045.jpg	\N
692	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5912347435951233, "bbox": [266, 28, 286, 44], "frame_number": 17735, "first_seen_time": "2025-12-07T13:40:44.998661", "duration": 0.0}	2025-12-07 13:40:44+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_692_1764341204704370850_20251207134045.jpg	\N
693	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5841118097305298, "bbox": [400, 130, 450, 173], "frame_number": 17735, "first_seen_time": "2025-12-07T13:40:44.998661", "duration": 0.0}	2025-12-07 13:40:44+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_693_1764341204704370850_20251207134045.jpg	\N
694	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5408653616905212, "bbox": [321, 116, 359, 152], "frame_number": 17735, "first_seen_time": "2025-12-07T13:40:44.998661", "duration": 0.0}	2025-12-07 13:40:44+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_694_1764341204704370850_20251207134046.jpg	\N
695	truck	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.34649690985679626, "bbox": [0, 83, 58, 132], "frame_number": 17735, "first_seen_time": "2025-12-07T13:40:44.998661", "duration": 0.0}	2025-12-07 13:40:44+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_695_1764341204704370850_20251207134046.jpg	\N
696	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6796411275863647, "bbox": [411, 86, 444, 115], "frame_number": 17810, "first_seen_time": "2025-12-07T13:40:50.332671", "duration": 0.0}	2025-12-07 13:40:50+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_696_1764341204704370850_20251207134050.jpg	\N
697	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6084488034248352, "bbox": [275, 75, 306, 106], "frame_number": 17810, "first_seen_time": "2025-12-07T13:40:50.332671", "duration": 0.0}	2025-12-07 13:40:50+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_697_1764341204704370850_20251207134050.jpg	\N
698	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4806850552558899, "bbox": [215, 190, 283, 255], "frame_number": 17810, "first_seen_time": "2025-12-07T13:40:50.332671", "duration": 0.0}	2025-12-07 13:40:50+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_698_1764341204704370850_20251207134051.jpg	\N
699	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3323614299297333, "bbox": [40, 39, 80, 63], "frame_number": 17810, "first_seen_time": "2025-12-07T13:40:50.332671", "duration": 0.0}	2025-12-07 13:40:50+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_699_1764341204704370850_20251207134051.jpg	\N
700	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6424537301063538, "bbox": [317, 83, 348, 113], "frame_number": 17885, "first_seen_time": "2025-12-07T13:40:55.586219", "duration": 0.0}	2025-12-07 13:40:55+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_700_1764341204704370850_20251207134055.jpg	\N
701	truck	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5192986726760864, "bbox": [406, 121, 468, 180], "frame_number": 17885, "first_seen_time": "2025-12-07T13:40:55.586219", "duration": 0.0}	2025-12-07 13:40:55+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_701_1764341204704370850_20251207134056.jpg	\N
702	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.4537680745124817, "bbox": [407, 121, 468, 180], "frame_number": 17885, "first_seen_time": "2025-12-07T13:40:55.586219", "duration": 0.0}	2025-12-07 13:40:55+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_702_1764341204704370850_20251207134056.jpg	\N
703	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.37173178791999817, "bbox": [325, 30, 345, 48], "frame_number": 17885, "first_seen_time": "2025-12-07T13:40:55.586219", "duration": 0.0}	2025-12-07 13:40:55+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_703_1764341204704370850_20251207134056.jpg	\N
704	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.2815478444099426, "bbox": [381, 37, 402, 55], "frame_number": 17885, "first_seen_time": "2025-12-07T13:40:55.586219", "duration": 0.0}	2025-12-07 13:40:55+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_704_1764341204704370850_20251207134056.jpg	\N
705	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.8524446487426758, "bbox": [496, 154, 578, 216], "frame_number": 17960, "first_seen_time": "2025-12-07T13:41:00.852021", "duration": 0.0}	2025-12-07 13:41:00+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_705_1764341204704370850_20251207134101.jpg	\N
706	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.8024410009384155, "bbox": [309, 207, 370, 280], "frame_number": 17960, "first_seen_time": "2025-12-07T13:41:00.852021", "duration": 0.0}	2025-12-07 13:41:00+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_706_1764341204704370850_20251207134101.jpg	\N
707	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7280855178833008, "bbox": [85, 31, 115, 50], "frame_number": 17960, "first_seen_time": "2025-12-07T13:41:00.852021", "duration": 0.0}	2025-12-07 13:41:00+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_707_1764341204704370850_20251207134101.jpg	\N
708	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7129236459732056, "bbox": [383, 96, 427, 136], "frame_number": 17960, "first_seen_time": "2025-12-07T13:41:00.852021", "duration": 0.0}	2025-12-07 13:41:00+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_708_1764341204704370850_20251207134101.jpg	\N
709	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5328658819198608, "bbox": [130, 24, 158, 44], "frame_number": 17960, "first_seen_time": "2025-12-07T13:41:00.852021", "duration": 0.0}	2025-12-07 13:41:00+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_709_1764341204704370850_20251207134102.jpg	\N
710	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.40023648738861084, "bbox": [24, 27, 64, 57], "frame_number": 17960, "first_seen_time": "2025-12-07T13:41:00.852021", "duration": 0.0}	2025-12-07 13:41:00+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_710_1764341204704370850_20251207134102.jpg	\N
711	truck	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.25514060258865356, "bbox": [24, 28, 64, 56], "frame_number": 17960, "first_seen_time": "2025-12-07T13:41:00.852021", "duration": 0.0}	2025-12-07 13:41:00+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_711_1764341204704370850_20251207134102.jpg	\N
712	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7222728133201599, "bbox": [179, 109, 227, 150], "frame_number": 18010, "first_seen_time": "2025-12-07T13:41:06.983076", "duration": 0.0}	2025-12-07 13:41:06+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_712_1764341204704370850_20251207134107.jpg	\N
713	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6190833449363708, "bbox": [140, 22, 166, 39], "frame_number": 18010, "first_seen_time": "2025-12-07T13:41:06.983076", "duration": 0.0}	2025-12-07 13:41:06+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_713_1764341204704370850_20251207134107.jpg	\N
714	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5953840613365173, "bbox": [391, 124, 440, 170], "frame_number": 18010, "first_seen_time": "2025-12-07T13:41:06.983076", "duration": 0.0}	2025-12-07 13:41:06+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_714_1764341204704370850_20251207134107.jpg	\N
715	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.675085186958313, "bbox": [222, 155, 279, 210], "frame_number": 18085, "first_seen_time": "2025-12-07T13:41:12.117057", "duration": 0.0}	2025-12-07 13:41:12+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_715_1764341204704370850_20251207134112.jpg	\N
716	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6594240069389343, "bbox": [74, 47, 109, 68], "frame_number": 18085, "first_seen_time": "2025-12-07T13:41:12.117057", "duration": 0.0}	2025-12-07 13:41:12+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_716_1764341204704370850_20251207134112.jpg	\N
717	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6321215629577637, "bbox": [260, 77, 293, 107], "frame_number": 18085, "first_seen_time": "2025-12-07T13:41:12.117057", "duration": 0.0}	2025-12-07 13:41:12+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_717_1764341204704370850_20251207134112.jpg	\N
718	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5811365842819214, "bbox": [136, 8, 157, 23], "frame_number": 18085, "first_seen_time": "2025-12-07T13:41:12.117057", "duration": 0.0}	2025-12-07 13:41:12+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_718_1764341204704370850_20251207134113.jpg	\N
719	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5531389117240906, "bbox": [238, 298, 332, 356], "frame_number": 18085, "first_seen_time": "2025-12-07T13:41:12.117057", "duration": 0.0}	2025-12-07 13:41:12+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_719_1764341204704370850_20251207134113.jpg	\N
720	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3942766487598419, "bbox": [290, 38, 313, 53], "frame_number": 18085, "first_seen_time": "2025-12-07T13:41:12.117057", "duration": 0.0}	2025-12-07 13:41:12+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_720_1764341204704370850_20251207134113.jpg	\N
721	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3472261130809784, "bbox": [112, 23, 137, 39], "frame_number": 18085, "first_seen_time": "2025-12-07T13:41:12.117057", "duration": 0.0}	2025-12-07 13:41:12+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_721_1764341204704370850_20251207134113.jpg	\N
722	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3367501497268677, "bbox": [365, 38, 385, 55], "frame_number": 18085, "first_seen_time": "2025-12-07T13:41:12.117057", "duration": 0.0}	2025-12-07 13:41:12+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_722_1764341204704370850_20251207134114.jpg	\N
723	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3076349198818207, "bbox": [325, 41, 350, 66], "frame_number": 18085, "first_seen_time": "2025-12-07T13:41:12.117057", "duration": 0.0}	2025-12-07 13:41:12+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_723_1764341204704370850_20251207134114.jpg	\N
724	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7367557883262634, "bbox": [415, 194, 490, 263], "frame_number": 18160, "first_seen_time": "2025-12-07T13:41:17.385577", "duration": 0.0}	2025-12-07 13:41:17+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_724_1764341204704370850_20251207134117.jpg	\N
725	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6361023187637329, "bbox": [317, 182, 375, 250], "frame_number": 18160, "first_seen_time": "2025-12-07T13:41:17.385577", "duration": 0.0}	2025-12-07 13:41:17+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_725_1764341204704370850_20251207134117.jpg	\N
726	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5837632417678833, "bbox": [163, 4, 184, 21], "frame_number": 18160, "first_seen_time": "2025-12-07T13:41:17.385577", "duration": 0.0}	2025-12-07 13:41:17+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_726_1764341204704370850_20251207134118.jpg	\N
727	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5673404335975647, "bbox": [91, 20, 117, 37], "frame_number": 18160, "first_seen_time": "2025-12-07T13:41:17.385577", "duration": 0.0}	2025-12-07 13:41:17+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_727_1764341204704370850_20251207134118.jpg	\N
728	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.49577122926712036, "bbox": [263, 94, 297, 123], "frame_number": 18160, "first_seen_time": "2025-12-07T13:41:17.385577", "duration": 0.0}	2025-12-07 13:41:17+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_728_1764341204704370850_20251207134118.jpg	\N
729	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.40682452917099, "bbox": [195, 11, 216, 28], "frame_number": 18160, "first_seen_time": "2025-12-07T13:41:17.385577", "duration": 0.0}	2025-12-07 13:41:17+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_729_1764341204704370850_20251207134118.jpg	\N
730	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.39191898703575134, "bbox": [376, 45, 400, 71], "frame_number": 18160, "first_seen_time": "2025-12-07T13:41:17.385577", "duration": 0.0}	2025-12-07 13:41:17+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_730_1764341204704370850_20251207134119.jpg	\N
731	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.2747403681278229, "bbox": [119, 22, 147, 48], "frame_number": 18160, "first_seen_time": "2025-12-07T13:41:17.385577", "duration": 0.0}	2025-12-07 13:41:17+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_731_1764341204704370850_20251207134119.jpg	\N
732	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7825395464897156, "bbox": [63, 27, 95, 47], "frame_number": 18235, "first_seen_time": "2025-12-07T13:41:22.576383", "duration": 0.0}	2025-12-07 13:41:22+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_732_1764341204704370850_20251207134122.jpg	\N
733	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6373655796051025, "bbox": [289, 32, 308, 46], "frame_number": 18235, "first_seen_time": "2025-12-07T13:41:22.576383", "duration": 0.0}	2025-12-07 13:41:22+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_733_1764341204704370850_20251207134123.jpg	\N
734	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5925570130348206, "bbox": [137, 5, 160, 21], "frame_number": 18235, "first_seen_time": "2025-12-07T13:41:22.576383", "duration": 0.0}	2025-12-07 13:41:22+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_734_1764341204704370850_20251207134123.jpg	\N
735	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5892359614372253, "bbox": [434, 193, 516, 278], "frame_number": 18235, "first_seen_time": "2025-12-07T13:41:22.576383", "duration": 0.0}	2025-12-07 13:41:22+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_735_1764341204704370850_20251207134123.jpg	\N
736	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.555523157119751, "bbox": [312, 280, 403, 356], "frame_number": 18235, "first_seen_time": "2025-12-07T13:41:22.576383", "duration": 0.0}	2025-12-07 13:41:22+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_736_1764341204704370850_20251207134123.jpg	\N
737	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5307886600494385, "bbox": [153, 18, 177, 35], "frame_number": 18235, "first_seen_time": "2025-12-07T13:41:22.576383", "duration": 0.0}	2025-12-07 13:41:22+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_737_1764341204704370850_20251207134124.jpg	\N
738	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.39557313919067383, "bbox": [373, 13, 390, 32], "frame_number": 18235, "first_seen_time": "2025-12-07T13:41:22.576383", "duration": 0.0}	2025-12-07 13:41:22+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_738_1764341204704370850_20251207134124.jpg	\N
739	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.38867032527923584, "bbox": [390, 32, 409, 46], "frame_number": 18235, "first_seen_time": "2025-12-07T13:41:22.576383", "duration": 0.0}	2025-12-07 13:41:22+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_739_1764341204704370850_20251207134124.jpg	\N
740	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3459227383136749, "bbox": [143, 11, 176, 33], "frame_number": 18235, "first_seen_time": "2025-12-07T13:41:22.576383", "duration": 0.0}	2025-12-07 13:41:22+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_740_1764341204704370850_20251207134124.jpg	\N
741	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7553043365478516, "bbox": [426, 148, 483, 200], "frame_number": 18310, "first_seen_time": "2025-12-07T13:41:27.833561", "duration": 0.0}	2025-12-07 13:41:27+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_741_1764341204704370850_20251207134128.jpg	\N
742	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.705310583114624, "bbox": [379, 64, 409, 88], "frame_number": 18310, "first_seen_time": "2025-12-07T13:41:27.833561", "duration": 0.0}	2025-12-07 13:41:27+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_742_1764341204704370850_20251207134128.jpg	\N
743	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6679052710533142, "bbox": [292, 31, 316, 49], "frame_number": 18310, "first_seen_time": "2025-12-07T13:41:27.833561", "duration": 0.0}	2025-12-07 13:41:27+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_743_1764341204704370850_20251207134128.jpg	\N
744	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5996431112289429, "bbox": [0, 242, 138, 357], "frame_number": 18310, "first_seen_time": "2025-12-07T13:41:27.833561", "duration": 0.0}	2025-12-07 13:41:27+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_744_1764341204704370850_20251207134128.jpg	\N
745	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5826601386070251, "bbox": [326, 56, 350, 75], "frame_number": 18310, "first_seen_time": "2025-12-07T13:41:27.833561", "duration": 0.0}	2025-12-07 13:41:27+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_745_1764341204704370850_20251207134129.jpg	\N
746	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5618466138839722, "bbox": [305, 325, 403, 356], "frame_number": 18310, "first_seen_time": "2025-12-07T13:41:27.833561", "duration": 0.0}	2025-12-07 13:41:27+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_746_1764341204704370850_20251207134129.jpg	\N
747	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3978460431098938, "bbox": [0, 71, 34, 107], "frame_number": 18310, "first_seen_time": "2025-12-07T13:41:27.833561", "duration": 0.0}	2025-12-07 13:41:27+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_747_1764341204704370850_20251207134129.jpg	\N
748	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.35532206296920776, "bbox": [239, 51, 271, 75], "frame_number": 18310, "first_seen_time": "2025-12-07T13:41:27.833561", "duration": 0.0}	2025-12-07 13:41:27+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_748_1764341204704370850_20251207134129.jpg	\N
749	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.32805630564689636, "bbox": [276, 60, 304, 82], "frame_number": 18385, "first_seen_time": "2025-12-07T13:41:33.137879", "duration": 0.0}	2025-12-07 13:41:33+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_749_1764341204704370850_20251207134133.jpg	\N
750	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.7304434180259705, "bbox": [313, 145, 364, 200], "frame_number": 18465, "first_seen_time": "2025-12-07T13:41:38.812348", "duration": 0.0}	2025-12-07 13:41:38+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_750_1764341204704370850_20251207134139.jpg	\N
751	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.6882311105728149, "bbox": [418, 133, 469, 180], "frame_number": 18465, "first_seen_time": "2025-12-07T13:41:38.812348", "duration": 0.0}	2025-12-07 13:41:38+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_751_1764341204704370850_20251207134139.jpg	\N
752	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5888416171073914, "bbox": [251, 96, 291, 133], "frame_number": 18465, "first_seen_time": "2025-12-07T13:41:38.812348", "duration": 0.0}	2025-12-07 13:41:38+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_752_1764341204704370850_20251207134139.jpg	\N
753	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.5146405696868896, "bbox": [0, 77, 25, 107], "frame_number": 18465, "first_seen_time": "2025-12-07T13:41:38.812348", "duration": 0.0}	2025-12-07 13:41:38+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_753_1764341204704370850_20251207134139.jpg	\N
754	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.3361157774925232, "bbox": [382, 31, 399, 46], "frame_number": 18465, "first_seen_time": "2025-12-07T13:41:38.812348", "duration": 0.0}	2025-12-07 13:41:38+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_754_1764341204704370850_20251207134140.jpg	\N
755	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.30566903948783875, "bbox": [290, 46, 314, 65], "frame_number": 18465, "first_seen_time": "2025-12-07T13:41:38.812348", "duration": 0.0}	2025-12-07 13:41:38+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_755_1764341204704370850_20251207134140.jpg	\N
756	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.25628313422203064, "bbox": [301, 22, 321, 38], "frame_number": 18465, "first_seen_time": "2025-12-07T13:41:38.812348", "duration": 0.0}	2025-12-07 13:41:38+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_756_1764341204704370850_20251207134140.jpg	\N
757	car	江北初中监控安防任务	\N	{"track_id": 0, "confidence": 0.47317931056022644, "bbox": [323, 30, 342, 45], "frame_number": 18535, "first_seen_time": "2025-12-07T13:41:43.818990", "duration": 0.0}	2025-12-07 13:41:43+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_757_1764341204704370850_20251207134144.jpg	\N
758	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.8622957468032837, "bbox": [375, 65, 403, 92], "frame_number": 85, "first_seen_time": "2025-12-07T15:46:10.920964", "duration": 0.0}	2025-12-07 15:46:10+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_758_1764341204704370850_20251207154611.jpg	\N
759	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.7849672436714172, "bbox": [466, 126, 522, 165], "frame_number": 85, "first_seen_time": "2025-12-07T15:46:10.920964", "duration": 0.0}	2025-12-07 15:46:10+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_759_1764341204704370850_20251207154611.jpg	\N
760	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.7027755975723267, "bbox": [69, 21, 108, 54], "frame_number": 85, "first_seen_time": "2025-12-07T15:46:10.920964", "duration": 0.0}	2025-12-07 15:46:10+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_760_1764341204704370850_20251207154611.jpg	\N
761	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.5463178157806396, "bbox": [139, 1, 184, 23], "frame_number": 85, "first_seen_time": "2025-12-07T15:46:10.920964", "duration": 0.0}	2025-12-07 15:46:10+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_761_1764341204704370850_20251207154612.jpg	\N
762	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.5109105706214905, "bbox": [393, 30, 414, 49], "frame_number": 85, "first_seen_time": "2025-12-07T15:46:10.920964", "duration": 0.0}	2025-12-07 15:46:10+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_762_1764341204704370850_20251207154612.jpg	\N
763	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.3089386522769928, "bbox": [323, 25, 343, 39], "frame_number": 85, "first_seen_time": "2025-12-07T15:46:10.920964", "duration": 0.0}	2025-12-07 15:46:10+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_763_1764341204704370850_20251207154612.jpg	\N
764	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.28049445152282715, "bbox": [356, 17, 373, 33], "frame_number": 85, "first_seen_time": "2025-12-07T15:46:10.920964", "duration": 0.0}	2025-12-07 15:46:10+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_764_1764341204704370850_20251207154612.jpg	\N
765	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6410108208656311, "bbox": [61, 40, 94, 59], "frame_number": 155, "first_seen_time": "2025-12-07T15:46:15.908923", "duration": 0.0}	2025-12-07 15:46:15+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_765_1764341204704370850_20251207154616.jpg	\N
766	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.5231753587722778, "bbox": [390, 108, 434, 154], "frame_number": 155, "first_seen_time": "2025-12-07T15:46:15.908923", "duration": 0.0}	2025-12-07 15:46:15+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_766_1764341204704370850_20251207154616.jpg	\N
767	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.3539614677429199, "bbox": [301, 18, 317, 30], "frame_number": 155, "first_seen_time": "2025-12-07T15:46:15.908923", "duration": 0.0}	2025-12-07 15:46:15+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_767_1764341204704370850_20251207154616.jpg	\N
768	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.28036338090896606, "bbox": [328, 45, 351, 64], "frame_number": 155, "first_seen_time": "2025-12-07T15:46:15.908923", "duration": 0.0}	2025-12-07 15:46:15+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_768_1764341204704370850_20251207154616.jpg	\N
769	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.7641527652740479, "bbox": [0, 78, 59, 123], "frame_number": 225, "first_seen_time": "2025-12-07T15:46:20.898336", "duration": 0.0}	2025-12-07 15:46:20+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_769_1764341204704370850_20251207154621.jpg	\N
770	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6824570894241333, "bbox": [32, 35, 69, 54], "frame_number": 225, "first_seen_time": "2025-12-07T15:46:20.898336", "duration": 0.0}	2025-12-07 15:46:20+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_770_1764341204704370850_20251207154621.jpg	\N
771	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.4000597596168518, "bbox": [367, 44, 390, 64], "frame_number": 225, "first_seen_time": "2025-12-07T15:46:20.898336", "duration": 0.0}	2025-12-07 15:46:20+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_771_1764341204704370850_20251207154621.jpg	\N
772	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.3564164638519287, "bbox": [125, 20, 148, 34], "frame_number": 225, "first_seen_time": "2025-12-07T15:46:20.898336", "duration": 0.0}	2025-12-07 15:46:20+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_772_1764341204704370850_20251207154622.jpg	\N
773	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.3152351677417755, "bbox": [326, 32, 350, 54], "frame_number": 225, "first_seen_time": "2025-12-07T15:46:20.898336", "duration": 0.0}	2025-12-07 15:46:20+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_773_1764341204704370850_20251207154622.jpg	\N
774	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.7252546548843384, "bbox": [468, 293, 582, 355], "frame_number": 295, "first_seen_time": "2025-12-07T15:46:26.018329", "duration": 0.0}	2025-12-07 15:46:26+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_774_1764341204704370850_20251207154626.jpg	\N
775	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6855238676071167, "bbox": [11, 60, 63, 93], "frame_number": 295, "first_seen_time": "2025-12-07T15:46:26.018329", "duration": 0.0}	2025-12-07 15:46:26+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_775_1764341204704370850_20251207154626.jpg	\N
776	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.7889636754989624, "bbox": [186, 188, 265, 273], "frame_number": 370, "first_seen_time": "2025-12-07T15:46:31.362282", "duration": 0.0}	2025-12-07 15:46:31+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_776_1764341204704370850_20251207154631.jpg	\N
777	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6395281553268433, "bbox": [383, 72, 417, 105], "frame_number": 370, "first_seen_time": "2025-12-07T15:46:31.362282", "duration": 0.0}	2025-12-07 15:46:31+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_777_1764341204704370850_20251207154631.jpg	\N
778	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6134907603263855, "bbox": [142, 26, 172, 53], "frame_number": 370, "first_seen_time": "2025-12-07T15:46:31.362282", "duration": 0.0}	2025-12-07 15:46:31+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_778_1764341204704370850_20251207154632.jpg	\N
779	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.3467087149620056, "bbox": [370, 19, 386, 32], "frame_number": 370, "first_seen_time": "2025-12-07T15:46:31.362282", "duration": 0.0}	2025-12-07 15:46:31+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_779_1764341204704370850_20251207154632.jpg	\N
780	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.7030173540115356, "bbox": [132, 27, 158, 44], "frame_number": 450, "first_seen_time": "2025-12-07T15:46:37.189083", "duration": 0.0}	2025-12-07 15:46:37+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_780_1764341204704370850_20251207154637.jpg	\N
781	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6256862878799438, "bbox": [196, 95, 238, 131], "frame_number": 450, "first_seen_time": "2025-12-07T15:46:37.189083", "duration": 0.0}	2025-12-07 15:46:37+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_781_1764341204704370850_20251207154637.jpg	\N
782	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.48499083518981934, "bbox": [387, 108, 430, 151], "frame_number": 450, "first_seen_time": "2025-12-07T15:46:37.189083", "duration": 0.0}	2025-12-07 15:46:37+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_782_1764341204704370850_20251207154638.jpg	\N
783	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.748695969581604, "bbox": [253, 82, 292, 115], "frame_number": 520, "first_seen_time": "2025-12-07T15:46:42.222012", "duration": 0.0}	2025-12-07 15:46:42+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_783_1764341204704370850_20251207154642.jpg	\N
784	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6125363707542419, "bbox": [86, 44, 119, 64], "frame_number": 520, "first_seen_time": "2025-12-07T15:46:42.222012", "duration": 0.0}	2025-12-07 15:46:42+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_784_1764341204704370850_20251207154642.jpg	\N
785	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.5363326668739319, "bbox": [210, 170, 276, 232], "frame_number": 520, "first_seen_time": "2025-12-07T15:46:42.222012", "duration": 0.0}	2025-12-07 15:46:42+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_785_1764341204704370850_20251207154643.jpg	\N
786	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.5312808752059937, "bbox": [289, 39, 312, 56], "frame_number": 520, "first_seen_time": "2025-12-07T15:46:42.222012", "duration": 0.0}	2025-12-07 15:46:42+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_786_1764341204704370850_20251207154643.jpg	\N
787	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.38467228412628174, "bbox": [141, 5, 171, 22], "frame_number": 520, "first_seen_time": "2025-12-07T15:46:42.222012", "duration": 0.0}	2025-12-07 15:46:42+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_787_1764341204704370850_20251207154643.jpg	\N
788	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.3651107847690582, "bbox": [366, 41, 387, 58], "frame_number": 520, "first_seen_time": "2025-12-07T15:46:42.222012", "duration": 0.0}	2025-12-07 15:46:42+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_788_1764341204704370850_20251207154643.jpg	\N
789	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.35578635334968567, "bbox": [120, 23, 142, 37], "frame_number": 520, "first_seen_time": "2025-12-07T15:46:42.222012", "duration": 0.0}	2025-12-07 15:46:42+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_789_1764341204704370850_20251207154644.jpg	\N
790	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.25745564699172974, "bbox": [325, 27, 344, 42], "frame_number": 520, "first_seen_time": "2025-12-07T15:46:42.222012", "duration": 0.0}	2025-12-07 15:46:42+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_790_1764341204704370850_20251207154644.jpg	\N
791	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.698971688747406, "bbox": [447, 280, 555, 352], "frame_number": 590, "first_seen_time": "2025-12-07T15:46:47.284279", "duration": 0.0}	2025-12-07 15:46:47+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_791_1764341204704370850_20251207154647.jpg	\N
792	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.554068386554718, "bbox": [308, 273, 396, 355], "frame_number": 590, "first_seen_time": "2025-12-07T15:46:47.284279", "duration": 0.0}	2025-12-07 15:46:47+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_792_1764341204704370850_20251207154647.jpg	\N
793	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.4844076931476593, "bbox": [380, 56, 408, 85], "frame_number": 590, "first_seen_time": "2025-12-07T15:46:47.284279", "duration": 0.0}	2025-12-07 15:46:47+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_793_1764341204704370850_20251207154648.jpg	\N
794	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.4811346232891083, "bbox": [112, 14, 136, 31], "frame_number": 590, "first_seen_time": "2025-12-07T15:46:47.284279", "duration": 0.0}	2025-12-07 15:46:47+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_794_1764341204704370850_20251207154648.jpg	\N
795	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.4211667478084564, "bbox": [245, 130, 287, 170], "frame_number": 590, "first_seen_time": "2025-12-07T15:46:47.284279", "duration": 0.0}	2025-12-07 15:46:47+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_795_1764341204704370850_20251207154648.jpg	\N
796	truck	江北初中监控安防任务		{"track_id": 0, "confidence": 0.390317440032959, "bbox": [245, 130, 288, 170], "frame_number": 590, "first_seen_time": "2025-12-07T15:46:47.284279", "duration": 0.0}	2025-12-07 15:46:47+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_796_1764341204704370850_20251207154648.jpg	\N
797	truck	江北初中监控安防任务		{"track_id": 0, "confidence": 0.28059855103492737, "bbox": [379, 56, 407, 85], "frame_number": 590, "first_seen_time": "2025-12-07T15:46:47.284279", "duration": 0.0}	2025-12-07 15:46:47+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_797_1764341204704370850_20251207154649.jpg	\N
798	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.26507166028022766, "bbox": [142, 18, 164, 38], "frame_number": 590, "first_seen_time": "2025-12-07T15:46:47.284279", "duration": 0.0}	2025-12-07 15:46:47+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_798_1764341204704370850_20251207154649.jpg	\N
799	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.2641775608062744, "bbox": [163, 30, 185, 48], "frame_number": 590, "first_seen_time": "2025-12-07T15:46:47.284279", "duration": 0.0}	2025-12-07 15:46:47+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_799_1764341204704370850_20251207154649.jpg	\N
800	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.8072736859321594, "bbox": [69, 64, 113, 92], "frame_number": 660, "first_seen_time": "2025-12-07T15:46:52.351116", "duration": 0.0}	2025-12-07 15:46:52+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_800_1764341204704370850_20251207154652.jpg	\N
801	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.660849928855896, "bbox": [280, 56, 305, 73], "frame_number": 660, "first_seen_time": "2025-12-07T15:46:52.351116", "duration": 0.0}	2025-12-07 15:46:52+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_801_1764341204704370850_20251207154652.jpg	\N
802	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.4868179261684418, "bbox": [380, 46, 402, 67], "frame_number": 660, "first_seen_time": "2025-12-07T15:46:52.351116", "duration": 0.0}	2025-12-07 15:46:52+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_802_1764341204704370850_20251207154653.jpg	\N
803	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.3523682951927185, "bbox": [296, 24, 316, 36], "frame_number": 660, "first_seen_time": "2025-12-07T15:46:52.351116", "duration": 0.0}	2025-12-07 15:46:52+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_803_1764341204704370850_20251207154653.jpg	\N
804	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.32920682430267334, "bbox": [210, 0, 236, 18], "frame_number": 660, "first_seen_time": "2025-12-07T15:46:52.351116", "duration": 0.0}	2025-12-07 15:46:52+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_804_1764341204704370850_20251207154653.jpg	\N
805	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6967318654060364, "bbox": [401, 119, 449, 163], "frame_number": 730, "first_seen_time": "2025-12-07T15:46:57.432545", "duration": 0.0}	2025-12-07 15:46:57+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_805_1764341204704370850_20251207154657.jpg	\N
806	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6374342441558838, "bbox": [172, 105, 229, 152], "frame_number": 730, "first_seen_time": "2025-12-07T15:46:57.432545", "duration": 0.0}	2025-12-07 15:46:57+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_806_1764341204704370850_20251207154658.jpg	\N
807	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6173793077468872, "bbox": [325, 95, 357, 126], "frame_number": 730, "first_seen_time": "2025-12-07T15:46:57.432545", "duration": 0.0}	2025-12-07 15:46:57+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_807_1764341204704370850_20251207154658.jpg	\N
808	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.5874004364013672, "bbox": [280, 58, 308, 81], "frame_number": 730, "first_seen_time": "2025-12-07T15:46:57.432545", "duration": 0.0}	2025-12-07 15:46:57+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_808_1764341204704370850_20251207154658.jpg	\N
809	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.33094894886016846, "bbox": [104, 33, 136, 56], "frame_number": 730, "first_seen_time": "2025-12-07T15:46:57.432545", "duration": 0.0}	2025-12-07 15:46:57+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_809_1764341204704370850_20251207154658.jpg	\N
810	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.25557181239128113, "bbox": [325, 34, 344, 48], "frame_number": 730, "first_seen_time": "2025-12-07T15:46:57.432545", "duration": 0.0}	2025-12-07 15:46:57+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_810_1764341204704370850_20251207154659.jpg	\N
811	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.5209065079689026, "bbox": [240, 122, 284, 161], "frame_number": 805, "first_seen_time": "2025-12-07T15:47:02.813311", "duration": 0.0}	2025-12-07 15:47:02+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_811_1764341204704370850_20251207154703.jpg	\N
812	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.42240917682647705, "bbox": [323, 74, 350, 97], "frame_number": 805, "first_seen_time": "2025-12-07T15:47:02.813311", "duration": 0.0}	2025-12-07 15:47:02+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_812_1764341204704370850_20251207154703.jpg	\N
813	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.408801406621933, "bbox": [383, 80, 415, 109], "frame_number": 805, "first_seen_time": "2025-12-07T15:47:02.813311", "duration": 0.0}	2025-12-07 15:47:02+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_813_1764341204704370850_20251207154703.jpg	\N
814	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.670626163482666, "bbox": [289, 47, 312, 71], "frame_number": 880, "first_seen_time": "2025-12-07T15:47:08.124262", "duration": 0.0}	2025-12-07 15:47:08+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_814_1764341204704370850_20251207154708.jpg	\N
815	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6111680269241333, "bbox": [263, 103, 301, 142], "frame_number": 880, "first_seen_time": "2025-12-07T15:47:08.124262", "duration": 0.0}	2025-12-07 15:47:08+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_815_1764341204704370850_20251207154708.jpg	\N
816	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.5653157234191895, "bbox": [122, 310, 228, 357], "frame_number": 880, "first_seen_time": "2025-12-07T15:47:08.124262", "duration": 0.0}	2025-12-07 15:47:08+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_816_1764341204704370850_20251207154708.jpg	\N
817	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.5249947309494019, "bbox": [396, 58, 422, 80], "frame_number": 880, "first_seen_time": "2025-12-07T15:47:08.124262", "duration": 0.0}	2025-12-07 15:47:08+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_817_1764341204704370850_20251207154709.jpg	\N
818	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.3085440695285797, "bbox": [106, 34, 135, 55], "frame_number": 880, "first_seen_time": "2025-12-07T15:47:08.124262", "duration": 0.0}	2025-12-07 15:47:08+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_818_1764341204704370850_20251207154709.jpg	\N
819	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.674319326877594, "bbox": [318, 53, 345, 74], "frame_number": 955, "first_seen_time": "2025-12-07T15:47:13.399641", "duration": 0.0}	2025-12-07 15:47:13+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_819_1764341204704370850_20251207154713.jpg	\N
820	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.46691322326660156, "bbox": [388, 81, 428, 119], "frame_number": 955, "first_seen_time": "2025-12-07T15:47:13.399641", "duration": 0.0}	2025-12-07 15:47:13+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_820_1764341204704370850_20251207154713.jpg	\N
821	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.2702358067035675, "bbox": [376, 25, 393, 43], "frame_number": 955, "first_seen_time": "2025-12-07T15:47:13.399641", "duration": 0.0}	2025-12-07 15:47:13+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_821_1764341204704370850_20251207154714.jpg	\N
822	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.2549879550933838, "bbox": [326, 19, 343, 34], "frame_number": 955, "first_seen_time": "2025-12-07T15:47:13.399641", "duration": 0.0}	2025-12-07 15:47:13+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_822_1764341204704370850_20251207154714.jpg	\N
823	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.696694552898407, "bbox": [448, 99, 496, 136], "frame_number": 1030, "first_seen_time": "2025-12-07T15:47:18.723787", "duration": 0.0}	2025-12-07 15:47:18+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_823_1764341204704370850_20251207154719.jpg	\N
824	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6778613328933716, "bbox": [370, 63, 402, 93], "frame_number": 1030, "first_seen_time": "2025-12-07T15:47:18.723787", "duration": 0.0}	2025-12-07 15:47:18+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_824_1764341204704370850_20251207154719.jpg	\N
825	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6694120168685913, "bbox": [29, 49, 64, 69], "frame_number": 1030, "first_seen_time": "2025-12-07T15:47:18.723787", "duration": 0.0}	2025-12-07 15:47:18+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_825_1764341204704370850_20251207154719.jpg	\N
826	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.5812354683876038, "bbox": [318, 112, 354, 147], "frame_number": 1030, "first_seen_time": "2025-12-07T15:47:18.723787", "duration": 0.0}	2025-12-07 15:47:18+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_826_1764341204704370850_20251207154719.jpg	\N
827	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.49486714601516724, "bbox": [78, 40, 116, 65], "frame_number": 1030, "first_seen_time": "2025-12-07T15:47:18.723787", "duration": 0.0}	2025-12-07 15:47:18+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_827_1764341204704370850_20251207154720.jpg	\N
828	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.4071241021156311, "bbox": [163, 27, 187, 44], "frame_number": 1030, "first_seen_time": "2025-12-07T15:47:18.723787", "duration": 0.0}	2025-12-07 15:47:18+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_828_1764341204704370850_20251207154720.jpg	\N
829	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.3652105927467346, "bbox": [121, 12, 141, 25], "frame_number": 1030, "first_seen_time": "2025-12-07T15:47:18.723787", "duration": 0.0}	2025-12-07 15:47:18+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_829_1764341204704370850_20251207154720.jpg	\N
830	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.29564329981803894, "bbox": [164, 0, 198, 17], "frame_number": 1030, "first_seen_time": "2025-12-07T15:47:18.723787", "duration": 0.0}	2025-12-07 15:47:18+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_830_1764341204704370850_20251207154720.jpg	\N
831	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.250265508890152, "bbox": [137, 42, 165, 64], "frame_number": 1030, "first_seen_time": "2025-12-07T15:47:18.723787", "duration": 0.0}	2025-12-07 15:47:18+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_831_1764341204704370850_20251207154721.jpg	\N
832	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6462892293930054, "bbox": [277, 64, 304, 87], "frame_number": 1105, "first_seen_time": "2025-12-07T15:47:23.979892", "duration": 0.0}	2025-12-07 15:47:23+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_832_1764341204704370850_20251207154724.jpg	\N
833	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.643244743347168, "bbox": [31, 38, 73, 69], "frame_number": 1105, "first_seen_time": "2025-12-07T15:47:23.979892", "duration": 0.0}	2025-12-07 15:47:23+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_833_1764341204704370850_20251207154724.jpg	\N
834	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6253413558006287, "bbox": [398, 43, 419, 59], "frame_number": 1105, "first_seen_time": "2025-12-07T15:47:23.979892", "duration": 0.0}	2025-12-07 15:47:23+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_834_1764341204704370850_20251207154724.jpg	\N
835	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.4797884523868561, "bbox": [323, 166, 377, 227], "frame_number": 1105, "first_seen_time": "2025-12-07T15:47:23.979892", "duration": 0.0}	2025-12-07 15:47:23+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_835_1764341204704370850_20251207154725.jpg	\N
836	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.727623462677002, "bbox": [165, 26, 189, 42], "frame_number": 1180, "first_seen_time": "2025-12-07T15:47:29.397412", "duration": 0.0}	2025-12-07 15:47:29+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_836_1764341204704370850_20251207154729.jpg	\N
837	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.5812383890151978, "bbox": [360, 30, 382, 50], "frame_number": 1180, "first_seen_time": "2025-12-07T15:47:29.397412", "duration": 0.0}	2025-12-07 15:47:29+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_837_1764341204704370850_20251207154730.jpg	\N
838	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.5496503114700317, "bbox": [119, 18, 146, 38], "frame_number": 1180, "first_seen_time": "2025-12-07T15:47:29.397412", "duration": 0.0}	2025-12-07 15:47:29+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_838_1764341204704370850_20251207154730.jpg	\N
839	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.5056120157241821, "bbox": [395, 117, 442, 160], "frame_number": 1180, "first_seen_time": "2025-12-07T15:47:29.397412", "duration": 0.0}	2025-12-07 15:47:29+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_839_1764341204704370850_20251207154730.jpg	\N
840	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.43208232522010803, "bbox": [320, 97, 365, 143], "frame_number": 1180, "first_seen_time": "2025-12-07T15:47:29.397412", "duration": 0.0}	2025-12-07 15:47:29+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_840_1764341204704370850_20251207154730.jpg	\N
841	truck	江北初中监控安防任务		{"track_id": 0, "confidence": 0.38157904148101807, "bbox": [320, 97, 365, 143], "frame_number": 1180, "first_seen_time": "2025-12-07T15:47:29.397412", "duration": 0.0}	2025-12-07 15:47:29+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_841_1764341204704370850_20251207154731.jpg	\N
842	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.5174703001976013, "bbox": [374, 65, 403, 86], "frame_number": 1250, "first_seen_time": "2025-12-07T15:47:34.462456", "duration": 0.0}	2025-12-07 15:47:34+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_842_1764341204704370850_20251207154734.jpg	\N
843	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6807945966720581, "bbox": [465, 274, 591, 355], "frame_number": 1325, "first_seen_time": "2025-12-07T15:47:39.781443", "duration": 0.0}	2025-12-07 15:47:39+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_843_1764341204704370850_20251207154740.jpg	\N
844	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.5797601938247681, "bbox": [202, 3, 228, 22], "frame_number": 1325, "first_seen_time": "2025-12-07T15:47:39.781443", "duration": 0.0}	2025-12-07 15:47:39+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_844_1764341204704370850_20251207154740.jpg	\N
845	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.49588871002197266, "bbox": [274, 63, 301, 86], "frame_number": 1325, "first_seen_time": "2025-12-07T15:47:39.781443", "duration": 0.0}	2025-12-07 15:47:39+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_845_1764341204704370850_20251207154740.jpg	\N
846	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.35287755727767944, "bbox": [379, 45, 402, 69], "frame_number": 1325, "first_seen_time": "2025-12-07T15:47:39.781443", "duration": 0.0}	2025-12-07 15:47:39+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_846_1764341204704370850_20251207154740.jpg	\N
847	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.8459974527359009, "bbox": [37, 29, 75, 52], "frame_number": 1400, "first_seen_time": "2025-12-07T15:47:45.061880", "duration": 0.0}	2025-12-07 15:47:45+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_847_1764341204704370850_20251207154745.jpg	\N
848	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.7040075063705444, "bbox": [291, 31, 313, 48], "frame_number": 1400, "first_seen_time": "2025-12-07T15:47:45.061880", "duration": 0.0}	2025-12-07 15:47:45+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_848_1764341204704370850_20251207154745.jpg	\N
849	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6057798266410828, "bbox": [112, 48, 150, 72], "frame_number": 1400, "first_seen_time": "2025-12-07T15:47:45.061880", "duration": 0.0}	2025-12-07 15:47:45+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_849_1764341204704370850_20251207154745.jpg	\N
850	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.3874777555465698, "bbox": [119, 26, 150, 48], "frame_number": 1400, "first_seen_time": "2025-12-07T15:47:45.061880", "duration": 0.0}	2025-12-07 15:47:45+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_850_1764341204704370850_20251207154746.jpg	\N
851	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.7179175019264221, "bbox": [398, 129, 446, 171], "frame_number": 1470, "first_seen_time": "2025-12-07T15:47:50.096455", "duration": 0.0}	2025-12-07 15:47:50+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_851_1764341204704370850_20251207154750.jpg	\N
852	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6830527782440186, "bbox": [249, 122, 291, 160], "frame_number": 1470, "first_seen_time": "2025-12-07T15:47:50.096455", "duration": 0.0}	2025-12-07 15:47:50+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_852_1764341204704370850_20251207154750.jpg	\N
853	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.5846344828605652, "bbox": [360, 34, 382, 52], "frame_number": 1470, "first_seen_time": "2025-12-07T15:47:50.096455", "duration": 0.0}	2025-12-07 15:47:50+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_853_1764341204704370850_20251207154750.jpg	\N
854	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.46301931142807007, "bbox": [320, 89, 353, 120], "frame_number": 1470, "first_seen_time": "2025-12-07T15:47:50.096455", "duration": 0.0}	2025-12-07 15:47:50+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_854_1764341204704370850_20251207154751.jpg	\N
855	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.4339849650859833, "bbox": [119, 12, 143, 29], "frame_number": 1470, "first_seen_time": "2025-12-07T15:47:50.096455", "duration": 0.0}	2025-12-07 15:47:50+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_855_1764341204704370850_20251207154751.jpg	\N
856	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.35059231519699097, "bbox": [311, 177, 387, 275], "frame_number": 1470, "first_seen_time": "2025-12-07T15:47:50.096455", "duration": 0.0}	2025-12-07 15:47:50+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_856_1764341204704370850_20251207154751.jpg	\N
857	truck	江北初中监控安防任务		{"track_id": 0, "confidence": 0.3353498578071594, "bbox": [312, 177, 387, 276], "frame_number": 1470, "first_seen_time": "2025-12-07T15:47:50.096455", "duration": 0.0}	2025-12-07 15:47:50+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_857_1764341204704370850_20251207154751.jpg	\N
858	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.29919034242630005, "bbox": [268, 25, 289, 42], "frame_number": 1470, "first_seen_time": "2025-12-07T15:47:50.096455", "duration": 0.0}	2025-12-07 15:47:50+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_858_1764341204704370850_20251207154752.jpg	\N
859	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.25852248072624207, "bbox": [311, 176, 387, 218], "frame_number": 1470, "first_seen_time": "2025-12-07T15:47:50.096455", "duration": 0.0}	2025-12-07 15:47:50+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_859_1764341204704370850_20251207154752.jpg	\N
860	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.7213017344474792, "bbox": [316, 57, 342, 80], "frame_number": 1540, "first_seen_time": "2025-12-07T15:47:55.158730", "duration": 0.0}	2025-12-07 15:47:55+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_860_1764341204704370850_20251207154755.jpg	\N
861	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.5004894733428955, "bbox": [285, 41, 309, 64], "frame_number": 1540, "first_seen_time": "2025-12-07T15:47:55.158730", "duration": 0.0}	2025-12-07 15:47:55+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_861_1764341204704370850_20251207154755.jpg	\N
862	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.47732776403427124, "bbox": [67, 23, 97, 42], "frame_number": 1540, "first_seen_time": "2025-12-07T15:47:55.158730", "duration": 0.0}	2025-12-07 15:47:55+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_862_1764341204704370850_20251207154755.jpg	\N
863	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.4706091582775116, "bbox": [231, 58, 261, 85], "frame_number": 1540, "first_seen_time": "2025-12-07T15:47:55.158730", "duration": 0.0}	2025-12-07 15:47:55+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_863_1764341204704370850_20251207154756.jpg	\N
864	truck	江北初中监控安防任务		{"track_id": 0, "confidence": 0.43960464000701904, "bbox": [442, 230, 543, 328], "frame_number": 1540, "first_seen_time": "2025-12-07T15:47:55.158730", "duration": 0.0}	2025-12-07 15:47:55+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_864_1764341204704370850_20251207154756.jpg	\N
865	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.4117428660392761, "bbox": [442, 230, 543, 328], "frame_number": 1540, "first_seen_time": "2025-12-07T15:47:55.158730", "duration": 0.0}	2025-12-07 15:47:55+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_865_1764341204704370850_20251207154756.jpg	\N
866	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.32706648111343384, "bbox": [0, 40, 37, 66], "frame_number": 1540, "first_seen_time": "2025-12-07T15:47:55.158730", "duration": 0.0}	2025-12-07 15:47:55+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_866_1764341204704370850_20251207154757.jpg	\N
867	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.7823435664176941, "bbox": [143, 282, 242, 357], "frame_number": 1610, "first_seen_time": "2025-12-07T15:48:00.256045", "duration": 0.0}	2025-12-07 15:48:00+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_867_1764341204704370850_20251207154800.jpg	\N
868	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6295397877693176, "bbox": [411, 139, 464, 186], "frame_number": 1610, "first_seen_time": "2025-12-07T15:48:00.256045", "duration": 0.0}	2025-12-07 15:48:00+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_868_1764341204704370850_20251207154800.jpg	\N
869	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6271167993545532, "bbox": [370, 64, 400, 89], "frame_number": 1610, "first_seen_time": "2025-12-07T15:48:00.256045", "duration": 0.0}	2025-12-07 15:48:00+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_869_1764341204704370850_20251207154801.jpg	\N
870	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6248914003372192, "bbox": [105, 48, 147, 72], "frame_number": 1610, "first_seen_time": "2025-12-07T15:48:00.256045", "duration": 0.0}	2025-12-07 15:48:00+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_870_1764341204704370850_20251207154801.jpg	\N
871	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6015338897705078, "bbox": [326, 57, 356, 80], "frame_number": 1610, "first_seen_time": "2025-12-07T15:48:00.256045", "duration": 0.0}	2025-12-07 15:48:00+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_871_1764341204704370850_20251207154801.jpg	\N
872	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.4636973738670349, "bbox": [198, 14, 215, 28], "frame_number": 1610, "first_seen_time": "2025-12-07T15:48:00.256045", "duration": 0.0}	2025-12-07 15:48:00+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_872_1764341204704370850_20251207154801.jpg	\N
873	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.4508077800273895, "bbox": [83, 32, 117, 50], "frame_number": 1610, "first_seen_time": "2025-12-07T15:48:00.256045", "duration": 0.0}	2025-12-07 15:48:00+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_873_1764341204704370850_20251207154802.jpg	\N
874	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.42475512623786926, "bbox": [266, 86, 297, 115], "frame_number": 1610, "first_seen_time": "2025-12-07T15:48:00.256045", "duration": 0.0}	2025-12-07 15:48:00+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_874_1764341204704370850_20251207154802.jpg	\N
875	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.27751874923706055, "bbox": [296, 32, 313, 46], "frame_number": 1610, "first_seen_time": "2025-12-07T15:48:00.256045", "duration": 0.0}	2025-12-07 15:48:00+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_875_1764341204704370850_20251207154802.jpg	\N
876	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6809799671173096, "bbox": [85, 19, 115, 37], "frame_number": 1680, "first_seen_time": "2025-12-07T15:48:05.318554", "duration": 0.0}	2025-12-07 15:48:05+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_876_1764341204704370850_20251207154805.jpg	\N
877	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.654317319393158, "bbox": [385, 78, 418, 105], "frame_number": 1680, "first_seen_time": "2025-12-07T15:48:05.318554", "duration": 0.0}	2025-12-07 15:48:05+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_877_1764341204704370850_20251207154805.jpg	\N
878	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6335751414299011, "bbox": [53, 48, 93, 77], "frame_number": 1680, "first_seen_time": "2025-12-07T15:48:05.318554", "duration": 0.0}	2025-12-07 15:48:05+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_878_1764341204704370850_20251207154806.jpg	\N
879	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6308600902557373, "bbox": [321, 94, 357, 127], "frame_number": 1680, "first_seen_time": "2025-12-07T15:48:05.318554", "duration": 0.0}	2025-12-07 15:48:05+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_879_1764341204704370850_20251207154806.jpg	\N
880	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.38585329055786133, "bbox": [148, 297, 247, 357], "frame_number": 1680, "first_seen_time": "2025-12-07T15:48:05.318554", "duration": 0.0}	2025-12-07 15:48:05+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_880_1764341204704370850_20251207154806.jpg	\N
881	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.754187285900116, "bbox": [321, 119, 363, 164], "frame_number": 1750, "first_seen_time": "2025-12-07T15:48:10.324084", "duration": 0.0}	2025-12-07 15:48:10+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_881_1764341204704370850_20251207154810.jpg	\N
882	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.5794740319252014, "bbox": [161, 26, 190, 47], "frame_number": 1750, "first_seen_time": "2025-12-07T15:48:10.324084", "duration": 0.0}	2025-12-07 15:48:10+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_882_1764341204704370850_20251207154810.jpg	\N
883	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.49869948625564575, "bbox": [302, 14, 321, 28], "frame_number": 1750, "first_seen_time": "2025-12-07T15:48:10.324084", "duration": 0.0}	2025-12-07 15:48:10+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_883_1764341204704370850_20251207154811.jpg	\N
884	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.48527011275291443, "bbox": [206, 81, 247, 117], "frame_number": 1750, "first_seen_time": "2025-12-07T15:48:10.324084", "duration": 0.0}	2025-12-07 15:48:10+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_884_1764341204704370850_20251207154811.jpg	\N
885	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.42805245518684387, "bbox": [367, 34, 389, 51], "frame_number": 1750, "first_seen_time": "2025-12-07T15:48:10.324084", "duration": 0.0}	2025-12-07 15:48:10+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_885_1764341204704370850_20251207154811.jpg	\N
886	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.42221716046333313, "bbox": [394, 69, 423, 96], "frame_number": 1750, "first_seen_time": "2025-12-07T15:48:10.324084", "duration": 0.0}	2025-12-07 15:48:10+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_886_1764341204704370850_20251207154811.jpg	\N
887	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.3080669939517975, "bbox": [268, 22, 288, 39], "frame_number": 1750, "first_seen_time": "2025-12-07T15:48:10.324084", "duration": 0.0}	2025-12-07 15:48:10+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_887_1764341204704370850_20251207154812.jpg	\N
888	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.8272005915641785, "bbox": [478, 217, 560, 287], "frame_number": 1830, "first_seen_time": "2025-12-07T15:48:16.087244", "duration": 0.0}	2025-12-07 15:48:16+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_888_1764341204704370850_20251207154816.jpg	\N
889	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6483002305030823, "bbox": [185, 222, 271, 313], "frame_number": 1830, "first_seen_time": "2025-12-07T15:48:16.087244", "duration": 0.0}	2025-12-07 15:48:16+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_889_1764341204704370850_20251207154816.jpg	\N
890	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6195691823959351, "bbox": [320, 78, 353, 111], "frame_number": 1900, "first_seen_time": "2025-12-07T15:48:21.141146", "duration": 0.0}	2025-12-07 15:48:21+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_890_1764341204704370850_20251207154821.jpg	\N
891	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.5556108951568604, "bbox": [275, 57, 303, 81], "frame_number": 1900, "first_seen_time": "2025-12-07T15:48:21.141146", "duration": 0.0}	2025-12-07 15:48:21+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_891_1764341204704370850_20251207154821.jpg	\N
892	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.5516181588172913, "bbox": [398, 79, 431, 112], "frame_number": 1900, "first_seen_time": "2025-12-07T15:48:21.141146", "duration": 0.0}	2025-12-07 15:48:21+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_892_1764341204704370850_20251207154821.jpg	\N
893	truck	江北初中监控安防任务		{"track_id": 0, "confidence": 0.4489796757698059, "bbox": [399, 79, 431, 113], "frame_number": 1900, "first_seen_time": "2025-12-07T15:48:21.141146", "duration": 0.0}	2025-12-07 15:48:21+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_893_1764341204704370850_20251207154822.jpg	\N
894	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6220070719718933, "bbox": [93, 13, 129, 34], "frame_number": 1980, "first_seen_time": "2025-12-07T15:48:26.891644", "duration": 0.0}	2025-12-07 15:48:26+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_894_1764341204704370850_20251207154827.jpg	\N
895	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.36140042543411255, "bbox": [451, 281, 576, 354], "frame_number": 1980, "first_seen_time": "2025-12-07T15:48:26.891644", "duration": 0.0}	2025-12-07 15:48:26+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_895_1764341204704370850_20251207154827.jpg	\N
896	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.2633577287197113, "bbox": [150, 13, 171, 27], "frame_number": 1980, "first_seen_time": "2025-12-07T15:48:26.891644", "duration": 0.0}	2025-12-07 15:48:26+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_896_1764341204704370850_20251207154827.jpg	\N
897	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.8143507242202759, "bbox": [479, 141, 541, 182], "frame_number": 2050, "first_seen_time": "2025-12-07T15:48:31.871716", "duration": 0.0}	2025-12-07 15:48:31+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_897_1764341204704370850_20251207154832.jpg	\N
898	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.7800961136817932, "bbox": [377, 71, 407, 102], "frame_number": 2050, "first_seen_time": "2025-12-07T15:48:31.871716", "duration": 0.0}	2025-12-07 15:48:31+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_898_1764341204704370850_20251207154832.jpg	\N
899	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.5555049180984497, "bbox": [0, 42, 26, 70], "frame_number": 2050, "first_seen_time": "2025-12-07T15:48:31.871716", "duration": 0.0}	2025-12-07 15:48:31+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_899_1764341204704370850_20251207154832.jpg	\N
900	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.5259590148925781, "bbox": [325, 29, 342, 43], "frame_number": 2050, "first_seen_time": "2025-12-07T15:48:31.871716", "duration": 0.0}	2025-12-07 15:48:31+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_900_1764341204704370850_20251207154832.jpg	\N
901	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.5130478739738464, "bbox": [396, 34, 417, 53], "frame_number": 2050, "first_seen_time": "2025-12-07T15:48:31.871716", "duration": 0.0}	2025-12-07 15:48:31+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_901_1764341204704370850_20251207154833.jpg	\N
902	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.4773547351360321, "bbox": [81, 19, 118, 50], "frame_number": 2050, "first_seen_time": "2025-12-07T15:48:31.871716", "duration": 0.0}	2025-12-07 15:48:31+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_902_1764341204704370850_20251207154833.jpg	\N
903	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.3243834674358368, "bbox": [145, 1, 193, 22], "frame_number": 2050, "first_seen_time": "2025-12-07T15:48:31.871716", "duration": 0.0}	2025-12-07 15:48:31+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_903_1764341204704370850_20251207154833.jpg	\N
904	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.7415616512298584, "bbox": [386, 101, 429, 143], "frame_number": 2125, "first_seen_time": "2025-12-07T15:48:37.254210", "duration": 0.0}	2025-12-07 15:48:37+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_904_1764341204704370850_20251207154837.jpg	\N
905	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.599120557308197, "bbox": [49, 43, 84, 63], "frame_number": 2125, "first_seen_time": "2025-12-07T15:48:37.254210", "duration": 0.0}	2025-12-07 15:48:37+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_905_1764341204704370850_20251207154837.jpg	\N
906	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.401391863822937, "bbox": [0, 40, 28, 70], "frame_number": 2125, "first_seen_time": "2025-12-07T15:48:37.254210", "duration": 0.0}	2025-12-07 15:48:37+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_906_1764341204704370850_20251207154838.jpg	\N
907	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.3951244652271271, "bbox": [327, 44, 349, 60], "frame_number": 2125, "first_seen_time": "2025-12-07T15:48:37.254210", "duration": 0.0}	2025-12-07 15:48:37+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_907_1764341204704370850_20251207154838.jpg	\N
908	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.30344197154045105, "bbox": [300, 17, 318, 30], "frame_number": 2125, "first_seen_time": "2025-12-07T15:48:37.254210", "duration": 0.0}	2025-12-07 15:48:37+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_908_1764341204704370850_20251207154838.jpg	\N
909	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.7875844836235046, "bbox": [416, 174, 490, 242], "frame_number": 2205, "first_seen_time": "2025-12-07T15:48:42.938862", "duration": 0.0}	2025-12-07 15:48:42+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_909_1764341204704370850_20251207154843.jpg	\N
910	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.4595282971858978, "bbox": [361, 31, 381, 47], "frame_number": 2205, "first_seen_time": "2025-12-07T15:48:42.938862", "duration": 0.0}	2025-12-07 15:48:42+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_910_1764341204704370850_20251207154843.jpg	\N
911	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.7618204951286316, "bbox": [132, 272, 238, 356], "frame_number": 2280, "first_seen_time": "2025-12-07T15:48:48.275174", "duration": 0.0}	2025-12-07 15:48:48+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_911_1764341204704370850_20251207154848.jpg	\N
912	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6664785146713257, "bbox": [406, 123, 453, 169], "frame_number": 2280, "first_seen_time": "2025-12-07T15:48:48.275174", "duration": 0.0}	2025-12-07 15:48:48+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_912_1764341204704370850_20251207154848.jpg	\N
913	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.740359365940094, "bbox": [370, 42, 394, 64], "frame_number": 2355, "first_seen_time": "2025-12-07T15:48:53.465207", "duration": 0.0}	2025-12-07 15:48:53+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_913_1764341204704370850_20251207154853.jpg	\N
914	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.5464010834693909, "bbox": [193, 8, 219, 28], "frame_number": 2355, "first_seen_time": "2025-12-07T15:48:53.465207", "duration": 0.0}	2025-12-07 15:48:53+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_914_1764341204704370850_20251207154854.jpg	\N
915	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.5406530499458313, "bbox": [257, 89, 295, 118], "frame_number": 2355, "first_seen_time": "2025-12-07T15:48:53.465207", "duration": 0.0}	2025-12-07 15:48:53+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_915_1764341204704370850_20251207154854.jpg	\N
916	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.4531952738761902, "bbox": [134, 9, 157, 23], "frame_number": 2355, "first_seen_time": "2025-12-07T15:48:53.465207", "duration": 0.0}	2025-12-07 15:48:53+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_916_1764341204704370850_20251207154854.jpg	\N
917	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.4410144090652466, "bbox": [51, 57, 109, 97], "frame_number": 2355, "first_seen_time": "2025-12-07T15:48:53.465207", "duration": 0.0}	2025-12-07 15:48:53+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_917_1764341204704370850_20251207154854.jpg	\N
918	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.41349485516548157, "bbox": [365, 6, 381, 23], "frame_number": 2355, "first_seen_time": "2025-12-07T15:48:53.465207", "duration": 0.0}	2025-12-07 15:48:53+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_918_1764341204704370850_20251207154855.jpg	\N
919	truck	江北初中监控安防任务		{"track_id": 0, "confidence": 0.2992974519729614, "bbox": [51, 47, 110, 96], "frame_number": 2355, "first_seen_time": "2025-12-07T15:48:53.465207", "duration": 0.0}	2025-12-07 15:48:53+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_919_1764341204704370850_20251207154855.jpg	\N
920	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.7371967434883118, "bbox": [233, 61, 263, 85], "frame_number": 2430, "first_seen_time": "2025-12-07T15:48:58.767285", "duration": 0.0}	2025-12-07 15:48:58+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_920_1764341204704370850_20251207154859.jpg	\N
921	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6668364405632019, "bbox": [78, 44, 113, 64], "frame_number": 2430, "first_seen_time": "2025-12-07T15:48:58.767285", "duration": 0.0}	2025-12-07 15:48:58+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_921_1764341204704370850_20251207154859.jpg	\N
922	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.5731520056724548, "bbox": [374, 69, 404, 100], "frame_number": 2430, "first_seen_time": "2025-12-07T15:48:58.767285", "duration": 0.0}	2025-12-07 15:48:58+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_922_1764341204704370850_20251207154859.jpg	\N
923	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.43105244636535645, "bbox": [300, 283, 391, 354], "frame_number": 2430, "first_seen_time": "2025-12-07T15:48:58.767285", "duration": 0.0}	2025-12-07 15:48:58+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_923_1764341204704370850_20251207154859.jpg	\N
924	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.7055811285972595, "bbox": [296, 127, 340, 171], "frame_number": 2505, "first_seen_time": "2025-12-07T15:49:04.136367", "duration": 0.0}	2025-12-07 15:49:04+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_924_1764341204704370850_20251207154904.jpg	\N
925	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6884863376617432, "bbox": [142, 131, 209, 188], "frame_number": 2505, "first_seen_time": "2025-12-07T15:49:04.136367", "duration": 0.0}	2025-12-07 15:49:04+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_925_1764341204704370850_20251207154904.jpg	\N
926	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6393083930015564, "bbox": [91, 19, 119, 38], "frame_number": 2505, "first_seen_time": "2025-12-07T15:49:04.136367", "duration": 0.0}	2025-12-07 15:49:04+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_926_1764341204704370850_20251207154904.jpg	\N
927	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.607947587966919, "bbox": [265, 85, 296, 113], "frame_number": 2505, "first_seen_time": "2025-12-07T15:49:04.136367", "duration": 0.0}	2025-12-07 15:49:04+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_927_1764341204704370850_20251207154905.jpg	\N
928	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6070762276649475, "bbox": [279, 44, 304, 68], "frame_number": 2505, "first_seen_time": "2025-12-07T15:49:04.136367", "duration": 0.0}	2025-12-07 15:49:04+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_928_1764341204704370850_20251207154905.jpg	\N
929	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.3821501135826111, "bbox": [127, 11, 146, 25], "frame_number": 2505, "first_seen_time": "2025-12-07T15:49:04.136367", "duration": 0.0}	2025-12-07 15:49:04+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_929_1764341204704370850_20251207154905.jpg	\N
930	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.36421680450439453, "bbox": [43, 42, 83, 63], "frame_number": 2505, "first_seen_time": "2025-12-07T15:49:04.136367", "duration": 0.0}	2025-12-07 15:49:04+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_930_1764341204704370850_20251207154905.jpg	\N
931	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.8507575988769531, "bbox": [461, 263, 578, 355], "frame_number": 2580, "first_seen_time": "2025-12-07T15:49:09.458564", "duration": 0.0}	2025-12-07 15:49:09+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_931_1764341204704370850_20251207154909.jpg	\N
932	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.7387872338294983, "bbox": [325, 95, 358, 127], "frame_number": 2580, "first_seen_time": "2025-12-07T15:49:09.458564", "duration": 0.0}	2025-12-07 15:49:09+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_932_1764341204704370850_20251207154910.jpg	\N
933	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.7287979125976562, "bbox": [214, 172, 274, 231], "frame_number": 2580, "first_seen_time": "2025-12-07T15:49:09.458564", "duration": 0.0}	2025-12-07 15:49:09+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_933_1764341204704370850_20251207154910.jpg	\N
934	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6479660272598267, "bbox": [161, 27, 185, 45], "frame_number": 2580, "first_seen_time": "2025-12-07T15:49:09.458564", "duration": 0.0}	2025-12-07 15:49:09+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_934_1764341204704370850_20251207154910.jpg	\N
935	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6139938831329346, "bbox": [44, 72, 97, 105], "frame_number": 2580, "first_seen_time": "2025-12-07T15:49:09.458564", "duration": 0.0}	2025-12-07 15:49:09+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_935_1764341204704370850_20251207154910.jpg	\N
936	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.5922297239303589, "bbox": [384, 103, 427, 138], "frame_number": 2580, "first_seen_time": "2025-12-07T15:49:09.458564", "duration": 0.0}	2025-12-07 15:49:09+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_936_1764341204704370850_20251207154910.jpg	\N
937	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.4486129879951477, "bbox": [130, 14, 154, 32], "frame_number": 2580, "first_seen_time": "2025-12-07T15:49:09.458564", "duration": 0.0}	2025-12-07 15:49:09+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_937_1764341204704370850_20251207154911.jpg	\N
938	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.4131696820259094, "bbox": [288, 54, 308, 71], "frame_number": 2580, "first_seen_time": "2025-12-07T15:49:09.458564", "duration": 0.0}	2025-12-07 15:49:09+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_938_1764341204704370850_20251207154911.jpg	\N
939	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6198899745941162, "bbox": [100, 35, 134, 56], "frame_number": 2655, "first_seen_time": "2025-12-07T15:49:14.735894", "duration": 0.0}	2025-12-07 15:49:14+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_939_1764341204704370850_20251207154915.jpg	\N
940	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.5881683230400085, "bbox": [397, 104, 436, 142], "frame_number": 2655, "first_seen_time": "2025-12-07T15:49:14.735894", "duration": 0.0}	2025-12-07 15:49:14+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_940_1764341204704370850_20251207154915.jpg	\N
941	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.5293403267860413, "bbox": [0, 41, 27, 63], "frame_number": 2655, "first_seen_time": "2025-12-07T15:49:14.735894", "duration": 0.0}	2025-12-07 15:49:14+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_941_1764341204704370850_20251207154915.jpg	\N
942	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.4666186571121216, "bbox": [319, 132, 366, 180], "frame_number": 2655, "first_seen_time": "2025-12-07T15:49:14.735894", "duration": 0.0}	2025-12-07 15:49:14+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_942_1764341204704370850_20251207154915.jpg	\N
943	truck	江北初中监控安防任务		{"track_id": 0, "confidence": 0.4228592813014984, "bbox": [319, 132, 366, 180], "frame_number": 2655, "first_seen_time": "2025-12-07T15:49:14.735894", "duration": 0.0}	2025-12-07 15:49:14+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_943_1764341204704370850_20251207154916.jpg	\N
944	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.3701046407222748, "bbox": [109, 13, 135, 29], "frame_number": 2655, "first_seen_time": "2025-12-07T15:49:14.735894", "duration": 0.0}	2025-12-07 15:49:14+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_944_1764341204704370850_20251207154916.jpg	\N
945	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.7910473942756653, "bbox": [152, 128, 217, 182], "frame_number": 2725, "first_seen_time": "2025-12-07T15:49:19.782621", "duration": 0.0}	2025-12-07 15:49:19+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_945_1764341204704370850_20251207154920.jpg	\N
946	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.7192676067352295, "bbox": [372, 46, 396, 65], "frame_number": 2725, "first_seen_time": "2025-12-07T15:49:19.782621", "duration": 0.0}	2025-12-07 15:49:19+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_946_1764341204704370850_20251207154920.jpg	\N
947	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.7051023840904236, "bbox": [314, 178, 377, 247], "frame_number": 2725, "first_seen_time": "2025-12-07T15:49:19.782621", "duration": 0.0}	2025-12-07 15:49:19+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_947_1764341204704370850_20251207154920.jpg	\N
948	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.513555645942688, "bbox": [404, 96, 443, 131], "frame_number": 2725, "first_seen_time": "2025-12-07T15:49:19.782621", "duration": 0.0}	2025-12-07 15:49:19+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_948_1764341204704370850_20251207154920.jpg	\N
949	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.49006620049476624, "bbox": [186, 18, 210, 35], "frame_number": 2725, "first_seen_time": "2025-12-07T15:49:19.782621", "duration": 0.0}	2025-12-07 15:49:19+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_949_1764341204704370850_20251207154921.jpg	\N
950	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.4404408931732178, "bbox": [298, 24, 320, 37], "frame_number": 2725, "first_seen_time": "2025-12-07T15:49:19.782621", "duration": 0.0}	2025-12-07 15:49:19+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_950_1764341204704370850_20251207154921.jpg	\N
951	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.3811950087547302, "bbox": [327, 42, 346, 57], "frame_number": 2725, "first_seen_time": "2025-12-07T15:49:19.782621", "duration": 0.0}	2025-12-07 15:49:19+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_951_1764341204704370850_20251207154921.jpg	\N
952	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.3360156714916229, "bbox": [257, 32, 280, 52], "frame_number": 2725, "first_seen_time": "2025-12-07T15:49:19.782621", "duration": 0.0}	2025-12-07 15:49:19+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_952_1764341204704370850_20251207154921.jpg	\N
953	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.4052863121032715, "bbox": [363, 33, 383, 49], "frame_number": 2800, "first_seen_time": "2025-12-07T15:49:25.184998", "duration": 0.0}	2025-12-07 15:49:25+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_953_1764341204704370850_20251207154925.jpg	\N
954	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.7597478032112122, "bbox": [312, 145, 364, 199], "frame_number": 2870, "first_seen_time": "2025-12-07T15:49:30.199888", "duration": 0.0}	2025-12-07 15:49:30+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_954_1764341204704370850_20251207154930.jpg	\N
955	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6931774616241455, "bbox": [418, 132, 469, 179], "frame_number": 2870, "first_seen_time": "2025-12-07T15:49:30.199888", "duration": 0.0}	2025-12-07 15:49:30+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_955_1764341204704370850_20251207154930.jpg	\N
956	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6506332755088806, "bbox": [0, 77, 25, 108], "frame_number": 2870, "first_seen_time": "2025-12-07T15:49:30.199888", "duration": 0.0}	2025-12-07 15:49:30+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_956_1764341204704370850_20251207154931.jpg	\N
957	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.5985859632492065, "bbox": [251, 96, 291, 133], "frame_number": 2870, "first_seen_time": "2025-12-07T15:49:30.199888", "duration": 0.0}	2025-12-07 15:49:30+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_957_1764341204704370850_20251207154931.jpg	\N
958	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.42548418045043945, "bbox": [381, 31, 398, 46], "frame_number": 2870, "first_seen_time": "2025-12-07T15:49:30.199888", "duration": 0.0}	2025-12-07 15:49:30+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_958_1764341204704370850_20251207154931.jpg	\N
959	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.3933163285255432, "bbox": [300, 22, 320, 38], "frame_number": 2870, "first_seen_time": "2025-12-07T15:49:30.199888", "duration": 0.0}	2025-12-07 15:49:30+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_959_1764341204704370850_20251207154931.jpg	\N
960	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.25399520993232727, "bbox": [290, 46, 314, 66], "frame_number": 2870, "first_seen_time": "2025-12-07T15:49:30.199888", "duration": 0.0}	2025-12-07 15:49:30+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_960_1764341204704370850_20251207154932.jpg	\N
961	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.47762531042099, "bbox": [323, 29, 342, 45], "frame_number": 2940, "first_seen_time": "2025-12-07T15:49:35.307273", "duration": 0.0}	2025-12-07 15:49:35+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_961_1764341204704370850_20251207154935.jpg	\N
962	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.26026809215545654, "bbox": [373, 47, 401, 75], "frame_number": 2940, "first_seen_time": "2025-12-07T15:49:35.307273", "duration": 0.0}	2025-12-07 15:49:35+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_962_1764341204704370850_20251207154935.jpg	\N
963	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.2527255415916443, "bbox": [326, 6, 342, 21], "frame_number": 2940, "first_seen_time": "2025-12-07T15:49:35.307273", "duration": 0.0}	2025-12-07 15:49:35+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_963_1764341204704370850_20251207154936.jpg	\N
964	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.7321297526359558, "bbox": [422, 68, 456, 97], "frame_number": 3010, "first_seen_time": "2025-12-07T15:49:40.317217", "duration": 0.0}	2025-12-07 15:49:40+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_964_1764341204704370850_20251207154940.jpg	\N
965	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.7212727069854736, "bbox": [363, 42, 388, 64], "frame_number": 3010, "first_seen_time": "2025-12-07T15:49:40.317217", "duration": 0.0}	2025-12-07 15:49:40+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_965_1764341204704370850_20251207154940.jpg	\N
966	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.7101930379867554, "bbox": [423, 195, 503, 270], "frame_number": 3010, "first_seen_time": "2025-12-07T15:49:40.317217", "duration": 0.0}	2025-12-07 15:49:40+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_966_1764341204704370850_20251207154941.jpg	\N
967	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6540900468826294, "bbox": [115, 47, 151, 68], "frame_number": 3010, "first_seen_time": "2025-12-07T15:49:40.317217", "duration": 0.0}	2025-12-07 15:49:40+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_967_1764341204704370850_20251207154941.jpg	\N
968	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6530655026435852, "bbox": [320, 68, 349, 90], "frame_number": 3010, "first_seen_time": "2025-12-07T15:49:40.317217", "duration": 0.0}	2025-12-07 15:49:40+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_968_1764341204704370850_20251207154941.jpg	\N
969	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.5634588003158569, "bbox": [61, 75, 102, 100], "frame_number": 3010, "first_seen_time": "2025-12-07T15:49:40.317217", "duration": 0.0}	2025-12-07 15:49:40+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_969_1764341204704370850_20251207154941.jpg	\N
970	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.4386727809906006, "bbox": [145, 5, 178, 25], "frame_number": 3010, "first_seen_time": "2025-12-07T15:49:40.317217", "duration": 0.0}	2025-12-07 15:49:40+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_970_1764341204704370850_20251207154942.jpg	\N
971	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.40692809224128723, "bbox": [89, 18, 113, 36], "frame_number": 3010, "first_seen_time": "2025-12-07T15:49:40.317217", "duration": 0.0}	2025-12-07 15:49:40+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_971_1764341204704370850_20251207154942.jpg	\N
972	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.40092897415161133, "bbox": [0, 68, 33, 103], "frame_number": 3010, "first_seen_time": "2025-12-07T15:49:40.317217", "duration": 0.0}	2025-12-07 15:49:40+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_972_1764341204704370850_20251207154942.jpg	\N
973	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.2684009373188019, "bbox": [81, 72, 106, 97], "frame_number": 3010, "first_seen_time": "2025-12-07T15:49:40.317217", "duration": 0.0}	2025-12-07 15:49:40+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_973_1764341204704370850_20251207154942.jpg	\N
974	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6201131939888, "bbox": [326, 97, 365, 131], "frame_number": 3085, "first_seen_time": "2025-12-07T15:49:45.610630", "duration": 0.0}	2025-12-07 15:49:45+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_974_1764341204704370850_20251207154945.jpg	\N
975	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.5561163425445557, "bbox": [290, 42, 310, 58], "frame_number": 3085, "first_seen_time": "2025-12-07T15:49:45.610630", "duration": 0.0}	2025-12-07 15:49:45+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_975_1764341204704370850_20251207154946.jpg	\N
976	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.5279054641723633, "bbox": [466, 317, 566, 355], "frame_number": 3085, "first_seen_time": "2025-12-07T15:49:45.610630", "duration": 0.0}	2025-12-07 15:49:45+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_976_1764341204704370850_20251207154946.jpg	\N
977	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.3650283217430115, "bbox": [139, 19, 160, 31], "frame_number": 3085, "first_seen_time": "2025-12-07T15:49:45.610630", "duration": 0.0}	2025-12-07 15:49:45+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_977_1764341204704370850_20251207154946.jpg	\N
978	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.31545284390449524, "bbox": [387, 31, 406, 45], "frame_number": 3085, "first_seen_time": "2025-12-07T15:49:45.610630", "duration": 0.0}	2025-12-07 15:49:45+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_978_1764341204704370850_20251207154946.jpg	\N
979	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6785909533500671, "bbox": [375, 65, 403, 91], "frame_number": 3165, "first_seen_time": "2025-12-07T15:49:51.263415", "duration": 0.0}	2025-12-07 15:49:51+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_979_1764341204704370850_20251207154951.jpg	\N
980	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6441707611083984, "bbox": [326, 50, 355, 78], "frame_number": 3165, "first_seen_time": "2025-12-07T15:49:51.263415", "duration": 0.0}	2025-12-07 15:49:51+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_980_1764341204704370850_20251207154951.jpg	\N
981	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6058930158615112, "bbox": [96, 49, 132, 75], "frame_number": 3165, "first_seen_time": "2025-12-07T15:49:51.263415", "duration": 0.0}	2025-12-07 15:49:51+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_981_1764341204704370850_20251207154952.jpg	\N
982	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.5514758229255676, "bbox": [28, 45, 67, 70], "frame_number": 3165, "first_seen_time": "2025-12-07T15:49:51.263415", "duration": 0.0}	2025-12-07 15:49:51+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_982_1764341204704370850_20251207154952.jpg	\N
983	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.32609519362449646, "bbox": [81, 23, 108, 40], "frame_number": 3165, "first_seen_time": "2025-12-07T15:49:51.263415", "duration": 0.0}	2025-12-07 15:49:51+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_983_1764341204704370850_20251207154952.jpg	\N
984	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6770338416099548, "bbox": [88, 37, 121, 61], "frame_number": 3235, "first_seen_time": "2025-12-07T15:49:56.323239", "duration": 0.0}	2025-12-07 15:49:56+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_984_1764341204704370850_20251207154956.jpg	\N
985	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.5989792346954346, "bbox": [29, 40, 57, 56], "frame_number": 3235, "first_seen_time": "2025-12-07T15:49:56.323239", "duration": 0.0}	2025-12-07 15:49:56+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_985_1764341204704370850_20251207154956.jpg	\N
986	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.36817309260368347, "bbox": [364, 38, 385, 55], "frame_number": 3235, "first_seen_time": "2025-12-07T15:49:56.323239", "duration": 0.0}	2025-12-07 15:49:56+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_986_1764341204704370850_20251207154957.jpg	\N
987	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.717816948890686, "bbox": [399, 113, 452, 166], "frame_number": 3310, "first_seen_time": "2025-12-07T15:50:01.687716", "duration": 0.0}	2025-12-07 15:50:01+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_987_1764341204704370850_20251207155002.jpg	\N
988	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6862155199050903, "bbox": [374, 28, 392, 44], "frame_number": 3310, "first_seen_time": "2025-12-07T15:50:01.687716", "duration": 0.0}	2025-12-07 15:50:01+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_988_1764341204704370850_20251207155002.jpg	\N
989	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.665246844291687, "bbox": [173, 16, 201, 37], "frame_number": 3310, "first_seen_time": "2025-12-07T15:50:01.687716", "duration": 0.0}	2025-12-07 15:50:01+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_989_1764341204704370850_20251207155002.jpg	\N
990	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6188428401947021, "bbox": [291, 35, 312, 49], "frame_number": 3310, "first_seen_time": "2025-12-07T15:50:01.687716", "duration": 0.0}	2025-12-07 15:50:01+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_990_1764341204704370850_20251207155002.jpg	\N
991	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.5945048332214355, "bbox": [64, 24, 97, 46], "frame_number": 3310, "first_seen_time": "2025-12-07T15:50:01.687716", "duration": 0.0}	2025-12-07 15:50:01+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_991_1764341204704370850_20251207155003.jpg	\N
992	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.7827336192131042, "bbox": [34, 73, 84, 112], "frame_number": 3380, "first_seen_time": "2025-12-07T15:50:06.746321", "duration": 0.0}	2025-12-07 15:50:06+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_992_1764341204704370850_20251207155007.jpg	\N
993	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.7007811069488525, "bbox": [67, 42, 107, 68], "frame_number": 3380, "first_seen_time": "2025-12-07T15:50:06.746321", "duration": 0.0}	2025-12-07 15:50:06+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_993_1764341204704370850_20251207155007.jpg	\N
994	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.5420135259628296, "bbox": [0, 45, 13, 68], "frame_number": 3380, "first_seen_time": "2025-12-07T15:50:06.746321", "duration": 0.0}	2025-12-07 15:50:06+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_994_1764341204704370850_20251207155007.jpg	\N
995	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.2918451428413391, "bbox": [171, 2, 201, 17], "frame_number": 3380, "first_seen_time": "2025-12-07T15:50:06.746321", "duration": 0.0}	2025-12-07 15:50:06+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_995_1764341204704370850_20251207155007.jpg	\N
996	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.27409300208091736, "bbox": [190, 8, 204, 21], "frame_number": 3380, "first_seen_time": "2025-12-07T15:50:06.746321", "duration": 0.0}	2025-12-07 15:50:06+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_996_1764341204704370850_20251207155008.jpg	\N
997	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.7812023758888245, "bbox": [35, 28, 77, 53], "frame_number": 3460, "first_seen_time": "2025-12-07T15:50:12.416589", "duration": 0.0}	2025-12-07 15:50:12+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_997_1764341204704370850_20251207155012.jpg	\N
998	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6747403144836426, "bbox": [372, 60, 400, 82], "frame_number": 3460, "first_seen_time": "2025-12-07T15:50:12.416589", "duration": 0.0}	2025-12-07 15:50:12+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_998_1764341204704370850_20251207155012.jpg	\N
999	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6660200953483582, "bbox": [221, 136, 274, 185], "frame_number": 3460, "first_seen_time": "2025-12-07T15:50:12.416589", "duration": 0.0}	2025-12-07 15:50:12+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_999_1764341204704370850_20251207155013.jpg	\N
1000	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6568649411201477, "bbox": [279, 57, 306, 78], "frame_number": 3460, "first_seen_time": "2025-12-07T15:50:12.416589", "duration": 0.0}	2025-12-07 15:50:12+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_1000_1764341204704370850_20251207155013.jpg	\N
1001	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.3626547157764435, "bbox": [154, 0, 188, 24], "frame_number": 3460, "first_seen_time": "2025-12-07T15:50:12.416589", "duration": 0.0}	2025-12-07 15:50:12+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_1001_1764341204704370850_20251207155013.jpg	\N
1002	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.3585255742073059, "bbox": [135, 27, 159, 43], "frame_number": 3460, "first_seen_time": "2025-12-07T15:50:12.416589", "duration": 0.0}	2025-12-07 15:50:12+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_1002_1764341204704370850_20251207155014.jpg	\N
1003	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.319924920797348, "bbox": [323, 65, 356, 103], "frame_number": 3460, "first_seen_time": "2025-12-07T15:50:12.416589", "duration": 0.0}	2025-12-07 15:50:12+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_1003_1764341204704370850_20251207155014.jpg	\N
1004	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.8024737238883972, "bbox": [163, 262, 255, 356], "frame_number": 3530, "first_seen_time": "2025-12-07T15:50:17.484486", "duration": 0.0}	2025-12-07 15:50:17+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_1004_1764341204704370850_20251207155017.jpg	\N
1005	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.5940621495246887, "bbox": [324, 25, 344, 42], "frame_number": 3530, "first_seen_time": "2025-12-07T15:50:17.484486", "duration": 0.0}	2025-12-07 15:50:17+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_1005_1764341204704370850_20251207155018.jpg	\N
1006	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.5482920408248901, "bbox": [389, 85, 427, 122], "frame_number": 3530, "first_seen_time": "2025-12-07T15:50:17.484486", "duration": 0.0}	2025-12-07 15:50:17+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_1006_1764341204704370850_20251207155018.jpg	\N
1007	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.41597074270248413, "bbox": [298, 14, 316, 34], "frame_number": 3530, "first_seen_time": "2025-12-07T15:50:17.484486", "duration": 0.0}	2025-12-07 15:50:17+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_1007_1764341204704370850_20251207155018.jpg	\N
1008	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.2660355269908905, "bbox": [192, 17, 210, 32], "frame_number": 3530, "first_seen_time": "2025-12-07T15:50:17.484486", "duration": 0.0}	2025-12-07 15:50:17+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_1008_1764341204704370850_20251207155018.jpg	\N
1009	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.7164270877838135, "bbox": [387, 65, 415, 90], "frame_number": 3600, "first_seen_time": "2025-12-07T15:50:22.509916", "duration": 0.0}	2025-12-07 15:50:22+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_1009_1764341204704370850_20251207155022.jpg	\N
1010	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.588352382183075, "bbox": [289, 37, 312, 52], "frame_number": 3600, "first_seen_time": "2025-12-07T15:50:22.509916", "duration": 0.0}	2025-12-07 15:50:22+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_1010_1764341204704370850_20251207155023.jpg	\N
1011	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.5499647855758667, "bbox": [265, 86, 295, 114], "frame_number": 3600, "first_seen_time": "2025-12-07T15:50:22.509916", "duration": 0.0}	2025-12-07 15:50:22+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_1011_1764341204704370850_20251207155023.jpg	\N
1012	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.5350363254547119, "bbox": [136, 39, 165, 62], "frame_number": 3600, "first_seen_time": "2025-12-07T15:50:22.509916", "duration": 0.0}	2025-12-07 15:50:22+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_1012_1764341204704370850_20251207155023.jpg	\N
1013	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.3418441712856293, "bbox": [361, 33, 382, 51], "frame_number": 3600, "first_seen_time": "2025-12-07T15:50:22.509916", "duration": 0.0}	2025-12-07 15:50:22+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_1013_1764341204704370850_20251207155023.jpg	\N
1014	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.2626517713069916, "bbox": [0, 41, 27, 67], "frame_number": 3600, "first_seen_time": "2025-12-07T15:50:22.509916", "duration": 0.0}	2025-12-07 15:50:22+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_1014_1764341204704370850_20251207155024.jpg	\N
1015	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.25252091884613037, "bbox": [329, 27, 348, 42], "frame_number": 3600, "first_seen_time": "2025-12-07T15:50:22.509916", "duration": 0.0}	2025-12-07 15:50:22+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_1015_1764341204704370850_20251207155024.jpg	\N
1016	truck	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6604681611061096, "bbox": [13, 217, 151, 325], "frame_number": 3670, "first_seen_time": "2025-12-07T15:50:27.496051", "duration": 0.0}	2025-12-07 15:50:27+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_1016_1764341204704370850_20251207155027.jpg	\N
1017	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6413347125053406, "bbox": [263, 93, 298, 127], "frame_number": 3670, "first_seen_time": "2025-12-07T15:50:27.496051", "duration": 0.0}	2025-12-07 15:50:27+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_1017_1764341204704370850_20251207155028.jpg	\N
1018	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.601871907711029, "bbox": [438, 214, 531, 305], "frame_number": 3670, "first_seen_time": "2025-12-07T15:50:27.496051", "duration": 0.0}	2025-12-07 15:50:27+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_1018_1764341204704370850_20251207155028.jpg	\N
1019	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.5790255069732666, "bbox": [322, 150, 367, 199], "frame_number": 3670, "first_seen_time": "2025-12-07T15:50:27.496051", "duration": 0.0}	2025-12-07 15:50:27+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_1019_1764341204704370850_20251207155028.jpg	\N
1020	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.5038791298866272, "bbox": [371, 42, 393, 58], "frame_number": 3670, "first_seen_time": "2025-12-07T15:50:27.496051", "duration": 0.0}	2025-12-07 15:50:27+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_1020_1764341204704370850_20251207155028.jpg	\N
1021	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.4934521019458771, "bbox": [3, 37, 50, 61], "frame_number": 3670, "first_seen_time": "2025-12-07T15:50:27.496051", "duration": 0.0}	2025-12-07 15:50:27+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_1021_1764341204704370850_20251207155029.jpg	\N
1022	truck	江北初中监控安防任务		{"track_id": 0, "confidence": 0.30166664719581604, "bbox": [322, 150, 368, 197], "frame_number": 3670, "first_seen_time": "2025-12-07T15:50:27.496051", "duration": 0.0}	2025-12-07 15:50:27+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_1022_1764341204704370850_20251207155029.jpg	\N
1023	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.7569589018821716, "bbox": [414, 164, 476, 220], "frame_number": 3740, "first_seen_time": "2025-12-07T15:50:32.529417", "duration": 0.0}	2025-12-07 15:50:32+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_1023_1764341204704370850_20251207155032.jpg	\N
1024	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.6226863861083984, "bbox": [38, 71, 98, 107], "frame_number": 3740, "first_seen_time": "2025-12-07T15:50:32.529417", "duration": 0.0}	2025-12-07 15:50:32+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_1024_1764341204704370850_20251207155033.jpg	\N
1025	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.5854184031486511, "bbox": [317, 143, 364, 191], "frame_number": 3740, "first_seen_time": "2025-12-07T15:50:32.529417", "duration": 0.0}	2025-12-07 15:50:32+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_1025_1764341204704370850_20251207155033.jpg	\N
1026	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.4749499559402466, "bbox": [324, 56, 352, 79], "frame_number": 3740, "first_seen_time": "2025-12-07T15:50:32.529417", "duration": 0.0}	2025-12-07 15:50:32+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_1026_1764341204704370850_20251207155033.jpg	\N
1027	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.4356272518634796, "bbox": [258, 34, 283, 52], "frame_number": 3740, "first_seen_time": "2025-12-07T15:50:32.529417", "duration": 0.0}	2025-12-07 15:50:32+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_1027_1764341204704370850_20251207155033.jpg	\N
1028	car	江北初中监控安防任务		{"track_id": 0, "confidence": 0.2950681746006012, "bbox": [380, 35, 398, 51], "frame_number": 3740, "first_seen_time": "2025-12-07T15:50:32.529417", "duration": 0.0}	2025-12-07 15:50:32+08	1764341204704370850	大门设备	/api/v1/buckets/alert-images/objects/download?prefix=2025%2F12%2F07%2Falert_1028_1764341204704370850_20251207155034.jpg	\N
\.


--
-- Data for Name: algorithm_model_service; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.algorithm_model_service (id, task_id, service_name, service_url, service_type, model_id, threshold, request_method, request_headers, request_body_template, timeout, is_enabled, sort_order, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: algorithm_task; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.algorithm_task (id, task_name, task_code, task_type, model_ids, model_names, extract_interval, rtmp_input_url, rtmp_output_url, tracking_enabled, tracking_similarity_threshold, tracking_max_age, tracking_smooth_alpha, alert_event_enabled, alert_notification_enabled, alert_notification_config, alarm_suppress_time, last_notify_time, space_id, cron_expression, frame_skip, status, is_enabled, run_status, exception_reason, service_server_ip, service_port, service_process_id, service_last_heartbeat, service_log_path, total_frames, total_detections, total_captures, last_process_time, last_success_time, last_capture_time, description, defense_mode, defense_schedule, created_at, updated_at) FROM stdin;
1	江北初中监控安防任务	REALTIME_TASK_F4600A64	realtime	[-1]	yolo11n.pt (默认模型)	25	\N	\N	f	0.2	25	0.25	t	t	{"channels": [{"method": "email", "template_id": "515bdf64-20e9-4035-b6bf-6cc6364a5372", "template_name": "EasyAIoT\\u90ae\\u4ef6\\u6d4b\\u8bd5\\u6a21\\u677f"}]}	300	2025-12-07 08:01:13.596094	\N	\N	1	0	f	stopped	\N	192.168.11.28	\N	1817849	2025-12-07 08:02:05.222645	/opt/projects/easyaiot/VIDEO/logs/task_1	0	0	0	\N	\N	\N	\N	half	[[1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0],[1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0],[1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0],[1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0],[1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0],[1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]]	2025-12-07 03:33:14.529024	2025-12-07 08:02:13.451112
\.


--
-- Data for Name: algorithm_task_device; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.algorithm_task_device (task_id, device_id, created_at) FROM stdin;
1	1764341204704370850	2025-12-07 03:33:14.53405
\.


--
-- Data for Name: detection_region; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.detection_region (id, task_id, region_name, region_type, points, image_id, algorithm_type, algorithm_model_id, algorithm_threshold, algorithm_enabled, color, opacity, is_enabled, sort_order, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: device; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.device (id, name, source, rtmp_stream, http_stream, stream, ip, port, username, password, mac, manufacturer, model, firmware_version, serial_number, hardware_id, support_move, support_zoom, nvr_id, nvr_channel, enable_forward, directory_id, created_at, updated_at, auto_snap_enabled, cover_image_path) FROM stdin;
1764341221624781420	教室102	rtmp://localhost:1935/live/1764341221624781420	rtmp://localhost:1935/live/1764341221624781420	http://localhost:8080/live/1764341221624781420.flv	0	localhost	554	554	Zmg1451571@		EasyAIoT	Camera-EasyAIoT				f	f	\N	0	\N	6	2025-11-28 14:47:01.626613	2025-11-28 15:47:51.041247	f	\N
1764340342947424339	食堂设备	rtmp://localhost:1935/live/1764340342947424339	rtmp://localhost:1935/live/1764340342947424339	http://localhost:8080/live/1764340342947424339.flv	0	localhost	554	554	Zmg1451571@		EasyAIoT	Camera-EasyAIoT				f	f	\N	0	\N	\N	2025-11-28 14:32:22.95178	2025-11-28 15:52:34.233585	f	\N
1764341213886942524	教室101	rtmp://localhost:1935/live/1764341213886942524	rtmp://localhost:1935/live/1764341213886942524	http://localhost:8080/live/1764341213886942524.flv	0	localhost	554				EasyAIoT	Camera-EasyAIoT				f	f	\N	0	\N	6	2025-11-28 14:46:53.888645	2025-11-28 15:05:46.011409	f	\N
1764341204704370850	大门设备	rtmp://localhost:1935/live/1764341204704370850	rtmp://localhost:1935/live/1764341204704370859	http://localhost:8080/live/1764341204704370859.flv	0	localhost	554	554	Zmg1451571@		EasyAIoT	Camera-EasyAIoT				f	f	\N	0	\N	\N	2025-11-28 14:46:44.705985	2025-12-07 07:07:02.77405	t	/api/v1/buckets/camera-screenshots/objects/download?prefix=1764341204704370850/b652a7fac4044ddf873578e3f9b934ee.jpg
\.


--
-- Data for Name: device_detection_region; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.device_detection_region (id, device_id, region_name, region_type, points, image_id, color, opacity, is_enabled, sort_order, created_at, updated_at, model_ids) FROM stdin;
4	1764341204704370850	区域 1	polygon	[{"x": 0.39042331861413043, "y": 0.11080648291925466}, {"x": 0.39042331861413043, "y": 0.11080648291925466}, {"x": 0.6411026664402174, "y": 0.14962635869565216}, {"x": 0.7109784428377329, "y": 0.6030425077639752}, {"x": 0.39479055463897517, "y": 0.7055269798136646}, {"x": 0.287356548427795, "y": 0.4539741847826087}]	\N	#8a8a8a	0.3	t	0	2025-12-07 06:51:53.683404	2025-12-07 06:51:53.683407	[-1]
\.


--
-- Data for Name: device_directory; Type: TABLE DATA; Schema: public; Owner: -
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
-- Data for Name: device_storage_config; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.device_storage_config (id, device_id, snap_storage_bucket, snap_storage_max_size, snap_storage_cleanup_enabled, snap_storage_cleanup_threshold, snap_storage_cleanup_ratio, video_storage_bucket, video_storage_max_size, video_storage_cleanup_enabled, video_storage_cleanup_threshold, video_storage_cleanup_ratio, last_snap_cleanup_time, last_video_cleanup_time, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: frame_extractor; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.frame_extractor (id, extractor_name, extractor_code, extractor_type, "interval", description, is_enabled, status, server_ip, port, process_id, last_heartbeat, log_path, task_id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: image; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.image (id, filename, original_filename, path, width, height, created_at, device_id) FROM stdin;
1	c3e81426b84b4674b281793cd7db9358.jpg	1764341204704370850_20251207_134216.jpg	/api/v1/buckets/camera-screenshots/objects/download?prefix=1764341204704370850/c3e81426b84b4674b281793cd7db9358.jpg	1280	720	2025-12-07 05:42:16.020083	1764341204704370850
2	9198ba2292dd498abcd622c27688da26.jpg	1764341204704370850_20251207_134217.jpg	/api/v1/buckets/camera-screenshots/objects/download?prefix=1764341204704370850/9198ba2292dd498abcd622c27688da26.jpg	1280	720	2025-12-07 05:42:17.042096	1764341204704370850
3	df016d9148a44322af2f8499ffbe88ed.jpg	1764341204704370850_20251207_145211.jpg	/api/v1/buckets/camera-screenshots/objects/download?prefix=1764341204704370850/df016d9148a44322af2f8499ffbe88ed.jpg	1280	720	2025-12-07 06:52:11.908142	1764341204704370850
4	39064d14a66541148498098ae6f51748.jpg	1764341204704370850_20251207_145216.jpg	/api/v1/buckets/camera-screenshots/objects/download?prefix=1764341204704370850/39064d14a66541148498098ae6f51748.jpg	1280	720	2025-12-07 06:52:16.587961	1764341204704370850
5	5a29766a86e7451fa4438ae4a7ab12be.jpg	1764341204704370850_20251207_145217.jpg	/api/v1/buckets/camera-screenshots/objects/download?prefix=1764341204704370850/5a29766a86e7451fa4438ae4a7ab12be.jpg	1280	720	2025-12-07 06:52:17.617701	1764341204704370850
6	0d3107bc368641bfa2e3a44b690359d2.jpg	1764341204704370850_20251207_145220.jpg	/api/v1/buckets/camera-screenshots/objects/download?prefix=1764341204704370850/0d3107bc368641bfa2e3a44b690359d2.jpg	1280	720	2025-12-07 06:52:20.771246	1764341204704370850
7	082514b869e244059ff9531e67bf04aa.jpg	1764341204704370850_20251207_145221.jpg	/api/v1/buckets/camera-screenshots/objects/download?prefix=1764341204704370850/082514b869e244059ff9531e67bf04aa.jpg	1280	720	2025-12-07 06:52:21.848471	1764341204704370850
8	4cb0c5dd4e764c4a9a4aad62181031d2.jpg	1764341204704370850_20251207_145235.jpg	/api/v1/buckets/camera-screenshots/objects/download?prefix=1764341204704370850/4cb0c5dd4e764c4a9a4aad62181031d2.jpg	1280	720	2025-12-07 06:52:35.928617	1764341204704370850
9	c865b4e8fe024643b843ad7d35b14b25.jpg	1764341204704370850_20251207_150408.jpg	/api/v1/buckets/camera-screenshots/objects/download?prefix=1764341204704370850/c865b4e8fe024643b843ad7d35b14b25.jpg	1280	720	2025-12-07 07:04:08.332075	1764341204704370850
10	0b20b0c3fbef47fcb4101dab28eadd93.jpg	1764341204704370850_20251207_150409.jpg	/api/v1/buckets/camera-screenshots/objects/download?prefix=1764341204704370850/0b20b0c3fbef47fcb4101dab28eadd93.jpg	1280	720	2025-12-07 07:04:09.397453	1764341204704370850
11	eaecda9100f6476b87acb633b4c3dd8e.jpg	1764341204704370850_20251207_150430.jpg	/api/v1/buckets/camera-screenshots/objects/download?prefix=1764341204704370850/eaecda9100f6476b87acb633b4c3dd8e.jpg	1280	720	2025-12-07 07:04:30.484752	1764341204704370850
12	9d811f7902044cb8a98edcebbb9293cd.jpg	1764341204704370850_20251207_150431.jpg	/api/v1/buckets/camera-screenshots/objects/download?prefix=1764341204704370850/9d811f7902044cb8a98edcebbb9293cd.jpg	1280	720	2025-12-07 07:04:31.5209	1764341204704370850
13	c92608ff8114422a889a26e03d450548.jpg	1764341204704370850_20251207_150701.jpg	/api/v1/buckets/camera-screenshots/objects/download?prefix=1764341204704370850/c92608ff8114422a889a26e03d450548.jpg	1280	720	2025-12-07 07:07:01.711438	1764341204704370850
14	b652a7fac4044ddf873578e3f9b934ee.jpg	1764341204704370850_20251207_150702.jpg	/api/v1/buckets/camera-screenshots/objects/download?prefix=1764341204704370850/b652a7fac4044ddf873578e3f9b934ee.jpg	1280	720	2025-12-07 07:07:02.769994	1764341204704370850
\.


--
-- Data for Name: nvr; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.nvr (id, ip, username, password, name, model) FROM stdin;
\.


--
-- Data for Name: playback; Type: TABLE DATA; Schema: public; Owner: -
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
24	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765078093343.flv	2025-12-07 11:28:44.149306+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765078093343.jpg	2055006	2025-12-07 11:28:45.266079	2025-12-07 11:28:45.266079
25	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765078124159.flv	2025-12-07 11:29:14.180243+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765078124159.jpg	1975764	2025-12-07 11:29:15.28234	2025-12-07 11:29:15.28234
26	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765078154181.flv	2025-12-07 11:29:44.213188+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765078154181.jpg	1960651	2025-12-07 11:29:45.38809	2025-12-07 11:29:45.38809
27	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765078184213.flv	2025-12-07 11:30:14.24114+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765078184213.jpg	1986525	2025-12-07 11:30:15.362914	2025-12-07 11:30:15.362914
28	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765078214242.flv	2025-12-07 11:30:44.272099+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765078214242.jpg	2009140	2025-12-07 11:30:45.394395	2025-12-07 11:30:45.394395
29	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765078244272.flv	2025-12-07 11:31:14.302065+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765078244272.jpg	1995882	2025-12-07 11:31:15.417003	2025-12-07 11:31:15.417003
30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765078274302.flv	2025-12-07 11:31:44.332037+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765078274302.jpg	1987006	2025-12-07 11:31:45.426023	2025-12-07 11:31:45.426023
31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765078304333.flv	2025-12-07 11:32:14.364015+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765078304333.jpg	1951533	2025-12-07 11:32:15.462568	2025-12-07 11:32:15.462568
32	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765078334365.flv	2025-12-07 11:32:44.392999+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765078334365.jpg	1957631	2025-12-07 11:32:45.505987	2025-12-07 11:32:45.505987
33	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765078364400.flv	2025-12-07 11:33:14.423988+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765078364400.jpg	1967394	2025-12-07 11:33:15.535101	2025-12-07 11:33:15.535101
34	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765078394425.flv	2025-12-07 11:33:32.145803+08	1764341204704370850	大门设备	17	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765078394425.jpg	1069420	2025-12-07 11:33:33.237383	2025-12-07 11:33:33.237383
36	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765078427064.flv	2025-12-07 11:33:47.161801+08	1764341204704370850	大门设备	1	\N	348	2025-12-07 11:33:48.193451	2025-12-07 11:33:48.193451
38	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765078430178.flv	2025-12-07 11:33:51.404518+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765078430178.jpg	53232	2025-12-07 11:33:52.437243	2025-12-07 11:33:52.437243
40	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765078434444.flv	2025-12-07 11:33:54.899285+08	1764341204704370850	大门设备	1	\N	348	2025-12-07 11:33:55.969065	2025-12-07 11:33:55.969065
42	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765078441745.flv	2025-12-07 11:34:02.225796+08	1764341204704370850	大门设备	1	\N	348	2025-12-07 11:34:03.280323	2025-12-07 11:34:03.280323
44	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765078448945.flv	2025-12-07 11:34:09.51631+08	1764341204704370850	大门设备	1	\N	348	2025-12-07 11:34:10.593152	2025-12-07 11:34:10.593152
48	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765078512327.flv	2025-12-07 11:35:13.917031+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765078512327.jpg	97193	2025-12-07 11:35:15.657033	2025-12-07 11:35:15.657033
51	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765078520452.flv	2025-12-07 11:35:45.452942+08	1764341204704370850	大门设备	1	\N	348	2025-12-07 11:35:46.518572	2025-12-07 11:35:46.518572
35	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765078415196.flv	2025-12-07 11:33:44.045009+08	1764341204704370850	大门设备	7	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765078415196.jpg	539768	2025-12-07 11:33:45.134203	2025-12-07 11:33:45.134203
39	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765078431771.flv	2025-12-07 11:33:51.81649+08	1764341204704370850	大门设备	1	\N	13	2025-12-07 11:33:53.469887	2025-12-07 11:33:53.469887
37	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765078427495.flv	2025-12-07 11:33:48.36772+08	1764341204704370850	大门设备	1	\N	348	2025-12-07 11:33:49.395794	2025-12-07 11:33:49.395794
46	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765078506992.flv	2025-12-07 11:35:09.278684+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765078506992.jpg	106347	2025-12-07 11:35:10.331749	2025-12-07 11:35:10.331749
47	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765078512329.flv	2025-12-07 11:35:13.414064+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765078512329.jpg	35237	2025-12-07 11:35:14.530926	2025-12-07 11:35:14.530926
49	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765078516445.flv	2025-12-07 11:35:17.300807+08	1764341204704370850	大门设备	1	\N	21040	2025-12-07 11:35:18.326425	2025-12-07 11:35:18.326425
50	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765078516936.flv	2025-12-07 11:35:41.937175+08	1764341204704370850	大门设备	1	\N	26826	2025-12-07 11:35:43.032316	2025-12-07 11:35:43.032316
41	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765078437917.flv	2025-12-07 11:33:58.71803+08	1764341204704370850	大门设备	1	\N	348	2025-12-07 11:33:59.773904	2025-12-07 11:33:59.773904
43	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765078445252.flv	2025-12-07 11:34:05.91655+08	1764341204704370850	大门设备	1	\N	348	2025-12-07 11:34:06.947704	2025-12-07 11:34:06.947704
45	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765078452538.flv	2025-12-07 11:34:37.538446+08	1764341204704370850	大门设备	1	\N	348	2025-12-07 11:34:38.600868	2025-12-07 11:34:38.600868
52	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765079587822.flv	2025-12-07 11:53:38.654325+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765079587822.jpg	2055006	2025-12-07 11:53:39.760237	2025-12-07 11:53:39.760237
53	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765079858898.flv	2025-12-07 11:58:08.925626+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765079858898.jpg	1967394	2025-12-07 11:58:10.458514	2025-12-07 11:58:10.458514
54	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765079888927.flv	2025-12-07 11:58:38.957534+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765079888927.jpg	1943036	2025-12-07 11:58:40.05728	2025-12-07 11:58:40.05728
55	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765079918958.flv	2025-12-07 11:59:08.506439+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765079918958.jpg	1947145	2025-12-07 11:59:09.629064	2025-12-07 11:59:09.629064
56	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765079948508.flv	2025-12-07 11:59:39.01529+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765079948508.jpg	1919304	2025-12-07 11:59:40.099851	2025-12-07 11:59:40.099851
57	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765079979017.flv	2025-12-07 12:00:09.04714+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765079979017.jpg	1906469	2025-12-07 12:00:10.136746	2025-12-07 12:00:10.136746
58	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080009047.flv	2025-12-07 12:00:39.078974+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080009047.jpg	1954310	2025-12-07 12:00:40.196446	2025-12-07 12:00:40.196446
59	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080039079.flv	2025-12-07 12:01:09.106792+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080039079.jpg	1955910	2025-12-07 12:01:10.2024	2025-12-07 12:01:10.2024
60	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080069107.flv	2025-12-07 12:01:39.136595+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080069107.jpg	1994228	2025-12-07 12:01:40.218559	2025-12-07 12:01:40.218559
61	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080099137.flv	2025-12-07 12:02:09.166383+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080099137.jpg	1979066	2025-12-07 12:02:10.258216	2025-12-07 12:02:10.258216
62	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080129168.flv	2025-12-07 12:02:39.198158+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080129168.jpg	1953658	2025-12-07 12:02:40.35947	2025-12-07 12:02:40.35947
63	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080309351.flv	2025-12-07 12:05:39.378569+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080309351.jpg	1911175	2025-12-07 12:05:40.485098	2025-12-07 12:05:40.485098
64	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080399439.flv	2025-12-07 12:07:02.019974+08	1764341204704370850	大门设备	22	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080399439.jpg	1556328	2025-12-07 12:07:03.117308	2025-12-07 12:07:03.117308
65	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080425059.flv	2025-12-07 12:07:06.120794+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080425059.jpg	102658	2025-12-07 12:07:07.194928	2025-12-07 12:07:07.194928
66	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080461131.flv	2025-12-07 12:07:43.483148+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080461131.jpg	109654	2025-12-07 12:07:44.622681	2025-12-07 12:07:44.622681
67	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080466524.flv	2025-12-07 12:07:48.924907+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080466524.jpg	156650	2025-12-07 12:07:50.027729	2025-12-07 12:07:50.027729
68	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080509981.flv	2025-12-07 12:08:32.298981+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080509981.jpg	107901	2025-12-07 12:08:33.377696	2025-12-07 12:08:33.377696
69	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080515345.flv	2025-12-07 12:08:37.684741+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080515345.jpg	160316	2025-12-07 12:08:38.7508	2025-12-07 12:08:38.7508
70	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080644120.flv	2025-12-07 12:10:46.407948+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080644120.jpg	106347	2025-12-07 12:10:47.54217	2025-12-07 12:10:47.54217
71	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080649428.flv	2025-12-07 12:10:51.869699+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080649428.jpg	154570	2025-12-07 12:10:52.946157	2025-12-07 12:10:52.946157
72	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080696828.flv	2025-12-07 12:12:07.650244+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080696828.jpg	2055006	2025-12-07 12:12:08.753647	2025-12-07 12:12:08.753647
73	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080727651.flv	2025-12-07 12:12:37.680866+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080727651.jpg	1975764	2025-12-07 12:12:38.8119	2025-12-07 12:12:38.8119
74	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080757681.flv	2025-12-07 12:13:07.711485+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080757681.jpg	1960651	2025-12-07 12:13:08.889669	2025-12-07 12:13:08.889669
75	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080787712.flv	2025-12-07 12:13:15.004149+08	1764341204704370850	大门设备	7	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080787712.jpg	597100	2025-12-07 12:13:16.12904	2025-12-07 12:13:16.12904
76	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080796713.flv	2025-12-07 12:13:47.548648+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080796713.jpg	2055006	2025-12-07 12:13:48.652882	2025-12-07 12:13:48.652882
77	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080827549.flv	2025-12-07 12:14:17.580258+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080827549.jpg	1975764	2025-12-07 12:14:18.718952	2025-12-07 12:14:18.718952
78	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080857581.flv	2025-12-07 12:14:34.769462+08	1764341204704370850	大门设备	17	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080857581.jpg	1209318	2025-12-07 12:14:35.905609	2025-12-07 12:14:35.905609
79	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080876889.flv	2025-12-07 12:14:47.366877+08	1764341204704370850	大门设备	9	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080876889.jpg	658866	2025-12-07 12:14:48.477758	2025-12-07 12:14:48.477758
80	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080908947.flv	2025-12-07 12:15:28.522964+08	1764341204704370850	大门设备	18	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080908947.jpg	1246927	2025-12-07 12:15:29.693421	2025-12-07 12:15:29.693421
81	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080931568.flv	2025-12-07 12:15:33.708723+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765080931568.jpg	145391	2025-12-07 12:15:34.803926	2025-12-07 12:15:34.803926
82	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765081119534.flv	2025-12-07 12:18:53.770217+08	1764341204704370850	大门设备	13	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765081119534.jpg	926133	2025-12-07 12:18:54.932544	2025-12-07 12:18:54.932544
83	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765081136791.flv	2025-12-07 12:18:59.320851+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765081136791.jpg	163966	2025-12-07 12:19:00.370332	2025-12-07 12:19:00.370332
84	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765081147411.flv	2025-12-07 12:19:10.750045+08	1764341204704370850	大门设备	2	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765081147411.jpg	181152	2025-12-07 12:19:11.888802	2025-12-07 12:19:11.888802
85	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765081153781.flv	2025-12-07 12:19:15.37893+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765081153781.jpg	128628	2025-12-07 12:19:16.472535	2025-12-07 12:19:16.472535
86	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765081360121.flv	2025-12-07 12:22:42.455158+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765081360121.jpg	109654	2025-12-07 12:22:43.535139	2025-12-07 12:22:43.535139
87	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765081365487.flv	2025-12-07 12:22:47.985228+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765081365487.jpg	168236	2025-12-07 12:22:49.044721	2025-12-07 12:22:49.044721
88	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765081919830.flv	2025-12-07 12:32:19.985504+08	1764341204704370850	大门设备	19	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765081919830.jpg	1284010	2025-12-07 12:32:21.132227	2025-12-07 12:32:21.132227
89	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765081963629.flv	2025-12-07 12:33:07.935869+08	1764341204704370850	大门设备	23	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765081963629.jpg	1561168	2025-12-07 12:33:09.101119	2025-12-07 12:33:09.101119
90	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765082100744.flv	2025-12-07 12:35:24.231025+08	1764341204704370850	大门设备	22	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765082100744.jpg	1492382	2025-12-07 12:35:25.369721	2025-12-07 12:35:25.369721
91	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765082127262.flv	2025-12-07 12:35:28.341033+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765082127262.jpg	96128	2025-12-07 12:35:29.412361	2025-12-07 12:35:29.412361
92	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765082322487.flv	2025-12-07 12:38:48.775972+08	1764341204704370850	大门设备	5	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765082322487.jpg	355177	2025-12-07 12:38:49.908774	2025-12-07 12:38:49.908774
93	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765082331796.flv	2025-12-07 12:38:54.029572+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765082331796.jpg	163271	2025-12-07 12:38:55.095353	2025-12-07 12:38:55.095353
94	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765082903220.flv	2025-12-07 12:48:25.503499+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765082903220.jpg	106347	2025-12-07 12:48:26.647341	2025-12-07 12:48:26.647341
95	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765082908544.flv	2025-12-07 12:48:31.081573+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765082908544.jpg	160316	2025-12-07 12:48:32.151443	2025-12-07 12:48:32.151443
96	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765082912880.flv	2025-12-07 12:48:43.348164+08	1764341204704370850	大门设备	9	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765082912880.jpg	658866	2025-12-07 12:48:44.475954	2025-12-07 12:48:44.475954
97	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765082926380.flv	2025-12-07 12:48:47.8171+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765082926380.jpg	101047	2025-12-07 12:48:48.895118	2025-12-07 12:48:48.895118
98	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765082962913.flv	2025-12-07 12:49:25.195941+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765082962913.jpg	106347	2025-12-07 12:49:26.263483	2025-12-07 12:49:26.263483
99	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765082968225.flv	2025-12-07 12:49:30.673894+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765082968225.jpg	160316	2025-12-07 12:49:31.742111	2025-12-07 12:49:31.742111
100	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765082990038.flv	2025-12-07 12:49:52.329063+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765082990038.jpg	106347	2025-12-07 12:49:53.410682	2025-12-07 12:49:53.410682
101	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765082995358.flv	2025-12-07 12:49:57.897832+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765082995358.jpg	160316	2025-12-07 12:49:59.014698	2025-12-07 12:49:59.014698
102	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765083179299.flv	2025-12-07 12:53:17.537014+08	1764341204704370850	大门设备	17	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765083179299.jpg	1176008	2025-12-07 12:53:18.660293	2025-12-07 12:53:18.660293
103	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765083200576.flv	2025-12-07 12:53:21.732+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765083200576.jpg	97812	2025-12-07 12:53:22.790489	2025-12-07 12:53:22.790489
104	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765083970456.flv	2025-12-07 13:06:41.270302+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765083970456.jpg	2055006	2025-12-07 13:06:42.460257	2025-12-07 13:06:42.460257
105	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084001271.flv	2025-12-07 13:07:11.300681+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084001271.jpg	1975764	2025-12-07 13:07:12.389442	2025-12-07 13:07:12.389442
106	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084049702.flv	2025-12-07 13:07:31.153115+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084049702.jpg	112511	2025-12-07 13:07:32.251069	2025-12-07 13:07:32.251069
107	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084031301.flv	2025-12-07 13:07:41.331063+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084031301.jpg	1960651	2025-12-07 13:07:42.467478	2025-12-07 13:07:42.467478
108	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084064021.flv	2025-12-07 13:07:45.502996+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084064021.jpg	99009	2025-12-07 13:07:46.559883	2025-12-07 13:07:46.559883
109	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084077958.flv	2025-12-07 13:07:58.877119+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084077958.jpg	97555	2025-12-07 13:07:59.949666	2025-12-07 13:07:59.949666
110	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084061331.flv	2025-12-07 13:08:11.360447+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084061331.jpg	1986525	2025-12-07 13:08:12.470052	2025-12-07 13:08:12.470052
111	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084091361.flv	2025-12-07 13:08:41.390834+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084091361.jpg	2009140	2025-12-07 13:08:42.468908	2025-12-07 13:08:42.468908
112	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084121391.flv	2025-12-07 13:09:11.421222+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084121391.jpg	1995882	2025-12-07 13:09:12.509589	2025-12-07 13:09:12.509589
113	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084151422.flv	2025-12-07 13:09:41.453611+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084151422.jpg	1987006	2025-12-07 13:09:42.595938	2025-12-07 13:09:42.595938
114	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084181454.flv	2025-12-07 13:10:11.484003+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084181454.jpg	1951533	2025-12-07 13:10:12.642203	2025-12-07 13:10:12.642203
115	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084211485.flv	2025-12-07 13:10:41.512396+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084211485.jpg	1957631	2025-12-07 13:10:42.623326	2025-12-07 13:10:42.623326
116	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084241906.flv	2025-12-07 13:10:43.553765+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084241906.jpg	138695	2025-12-07 13:10:44.644994	2025-12-07 13:10:44.644994
117	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084257225.flv	2025-12-07 13:10:58.245563+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084257225.jpg	90585	2025-12-07 13:10:59.301585	2025-12-07 13:10:59.301585
118	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084241514.flv	2025-12-07 13:11:11.543791+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084241514.jpg	1967394	2025-12-07 13:11:12.643914	2025-12-07 13:11:12.643914
119	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084271010.flv	2025-12-07 13:11:13.04671+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084271010.jpg	157575	2025-12-07 13:11:14.137316	2025-12-07 13:11:14.137316
120	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084286180.flv	2025-12-07 13:11:27.870918+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084286180.jpg	124692	2025-12-07 13:11:28.977228	2025-12-07 13:11:28.977228
121	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084271545.flv	2025-12-07 13:11:41.575186+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084271545.jpg	1943036	2025-12-07 13:11:42.668596	2025-12-07 13:11:42.668596
122	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084301353.flv	2025-12-07 13:11:43.38209+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084301353.jpg	140030	2025-12-07 13:11:44.451792	2025-12-07 13:11:44.451792
123	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084316109.flv	2025-12-07 13:11:58.077099+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084316109.jpg	119910	2025-12-07 13:11:59.181702	2025-12-07 13:11:59.181702
124	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084301576.flv	2025-12-07 13:12:11.138609+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084301576.jpg	1947145	2025-12-07 13:12:12.282859	2025-12-07 13:12:12.282859
125	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084331197.flv	2025-12-07 13:12:13.302043+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084331197.jpg	144258	2025-12-07 13:12:14.402965	2025-12-07 13:12:14.402965
126	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084346424.flv	2025-12-07 13:12:28.595678+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084346424.jpg	161314	2025-12-07 13:12:29.648807	2025-12-07 13:12:29.648807
127	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084331140.flv	2025-12-07 13:12:41.634982+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084331140.jpg	1919304	2025-12-07 13:12:42.73098	2025-12-07 13:12:42.73098
133	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084419195.flv	2025-12-07 13:13:40.132623+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084419195.jpg	88367	2025-12-07 13:13:41.200202	2025-12-07 13:13:41.200202
137	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084421696.flv	2025-12-07 13:14:11.722185+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084421696.jpg	1955910	2025-12-07 13:14:12.809883	2025-12-07 13:14:12.809883
128	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084361426.flv	2025-12-07 13:12:43.711154+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084361426.jpg	161094	2025-12-07 13:12:44.823278	2025-12-07 13:12:44.823278
131	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084390245.flv	2025-12-07 13:13:13.045408+08	1764341204704370850	大门设备	2	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084390245.jpg	197495	2025-12-07 13:13:14.124163	2025-12-07 13:13:14.124163
132	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084405382.flv	2025-12-07 13:13:26.810867+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084405382.jpg	124603	2025-12-07 13:13:27.909123	2025-12-07 13:13:27.909123
129	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084376061.flv	2025-12-07 13:12:57.408811+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084376061.jpg	114315	2025-12-07 13:12:58.463737	2025-12-07 13:12:58.463737
134	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084391664.flv	2025-12-07 13:13:41.695783+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084391664.jpg	1954310	2025-12-07 13:13:42.839782	2025-12-07 13:13:42.839782
135	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084433412.flv	2025-12-07 13:13:55.56412+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084433412.jpg	159249	2025-12-07 13:13:56.641348	2025-12-07 13:13:56.641348
130	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084361635.flv	2025-12-07 13:13:11.663382+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084361635.jpg	1906469	2025-12-07 13:13:12.760647	2025-12-07 13:13:12.760647
136	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084448417.flv	2025-12-07 13:14:09.955279+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084448417.jpg	122562	2025-12-07 13:14:11.030321	2025-12-07 13:14:11.030321
138	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084463304.flv	2025-12-07 13:14:25.016067+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084463304.jpg	138238	2025-12-07 13:14:26.071225	2025-12-07 13:14:26.071225
139	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084478333.flv	2025-12-07 13:14:41.105623+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084478333.jpg	181600	2025-12-07 13:14:42.166263	2025-12-07 13:14:42.166263
140	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084451724.flv	2025-12-07 13:14:41.753588+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084451724.jpg	1994228	2025-12-07 13:14:43.251914	2025-12-07 13:14:43.251914
141	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084494403.flv	2025-12-07 13:14:57.33176+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084494403.jpg	164863	2025-12-07 13:14:58.394897	2025-12-07 13:14:58.394897
142	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084510253.flv	2025-12-07 13:15:11.416011+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084510253.jpg	119814	2025-12-07 13:15:12.489379	2025-12-07 13:15:12.489379
143	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084481754.flv	2025-12-07 13:15:11.784992+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084481754.jpg	1979066	2025-12-07 13:15:13.584607	2025-12-07 13:15:13.584607
144	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084524314.flv	2025-12-07 13:15:25.461904+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084524314.jpg	116531	2025-12-07 13:15:26.515533	2025-12-07 13:15:26.515533
145	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084538216.flv	2025-12-07 13:15:39.817143+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084538216.jpg	121679	2025-12-07 13:15:40.908078	2025-12-07 13:15:40.908078
146	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084511785.flv	2025-12-07 13:15:41.816396+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084511785.jpg	1953658	2025-12-07 13:15:42.919421	2025-12-07 13:15:42.919421
147	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084553518.flv	2025-12-07 13:15:54.603717+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084553518.jpg	90868	2025-12-07 13:15:55.672151	2025-12-07 13:15:55.672151
148	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084541817.flv	2025-12-07 13:16:11.843802+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084541817.jpg	1954083	2025-12-07 13:16:13.034046	2025-12-07 13:16:13.034046
149	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084574307.flv	2025-12-07 13:16:15.46061+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084574307.jpg	96333	2025-12-07 13:16:16.526659	2025-12-07 13:16:16.526659
150	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084588327.flv	2025-12-07 13:16:29.536863+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084588327.jpg	95183	2025-12-07 13:16:30.584883	2025-12-07 13:16:30.584883
151	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084571844.flv	2025-12-07 13:16:41.875208+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084571844.jpg	1926420	2025-12-07 13:16:43.061997	2025-12-07 13:16:43.061997
152	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084602393.flv	2025-12-07 13:16:43.470124+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084602393.jpg	104176	2025-12-07 13:16:44.542305	2025-12-07 13:16:44.542305
153	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084616462.flv	2025-12-07 13:16:57.508999+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084616462.jpg	86988	2025-12-07 13:16:58.596531	2025-12-07 13:16:58.596531
154	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084630325.flv	2025-12-07 13:17:11.81962+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084630325.jpg	130929	2025-12-07 13:17:12.893472	2025-12-07 13:17:12.893472
155	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084601876.flv	2025-12-07 13:17:11.907615+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084601876.jpg	1957326	2025-12-07 13:17:14.023717	2025-12-07 13:17:14.023717
156	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084644629.flv	2025-12-07 13:17:26.064865+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084644629.jpg	114873	2025-12-07 13:17:27.162442	2025-12-07 13:17:27.162442
157	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084659629.flv	2025-12-07 13:17:41.248099+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084659629.jpg	114225	2025-12-07 13:17:42.317676	2025-12-07 13:17:42.317676
158	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084631908.flv	2025-12-07 13:17:41.935023+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084631908.jpg	1928282	2025-12-07 13:17:43.423554	2025-12-07 13:17:43.423554
159	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084674620.flv	2025-12-07 13:17:56.128129+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084674620.jpg	121444	2025-12-07 13:17:57.197043	2025-12-07 13:17:57.197043
160	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084689401.flv	2025-12-07 13:18:11.118771+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084689401.jpg	133716	2025-12-07 13:18:12.200071	2025-12-07 13:18:12.200071
167	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084721996.flv	2025-12-07 13:19:12.02625+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084721996.jpg	1909646	2025-12-07 13:19:13.148068	2025-12-07 13:19:13.148068
168	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084762585.flv	2025-12-07 13:19:23.73763+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084762585.jpg	114048	2025-12-07 13:19:24.787951	2025-12-07 13:19:24.787951
170	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084776538.flv	2025-12-07 13:20:11.872082+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084776538.jpg	2224622	2025-12-07 13:20:12.970316	2025-12-07 13:20:12.970316
174	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084842116.flv	2025-12-07 13:21:12.145894+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084842116.jpg	1959948	2025-12-07 13:21:13.303229	2025-12-07 13:21:13.303229
175	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084846141.flv	2025-12-07 13:21:20.573448+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084846141.jpg	1937126	2025-12-07 13:21:21.663512	2025-12-07 13:21:21.663512
178	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084902177.flv	2025-12-07 13:22:12.208718+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084902177.jpg	1955250	2025-12-07 13:22:13.288851	2025-12-07 13:22:13.288851
181	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084949937.flv	2025-12-07 13:23:04.608949+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084949937.jpg	2071038	2025-12-07 13:23:05.764819	2025-12-07 13:23:05.764819
183	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084984610.flv	2025-12-07 13:23:39.351114+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084984610.jpg	1926073	2025-12-07 13:23:40.471047	2025-12-07 13:23:40.471047
185	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085022297.flv	2025-12-07 13:24:12.326436+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085022297.jpg	1903095	2025-12-07 13:24:13.412913	2025-12-07 13:24:13.412913
189	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085082360.flv	2025-12-07 13:25:12.390483+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085082360.jpg	1915255	2025-12-07 13:25:13.503708	2025-12-07 13:25:13.503708
190	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085088390.flv	2025-12-07 13:25:23.541933+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085088390.jpg	2060256	2025-12-07 13:25:24.64282	2025-12-07 13:25:24.64282
195	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085172449.flv	2025-12-07 13:26:42.479019+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085172449.jpg	1972009	2025-12-07 13:26:43.580627	2025-12-07 13:26:43.580627
196	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085194040.flv	2025-12-07 13:27:08.204738+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085194040.jpg	1917909	2025-12-07 13:27:09.296744	2025-12-07 13:27:09.296744
199	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085232509.flv	2025-12-07 13:27:42.539023+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085232509.jpg	1916328	2025-12-07 13:27:44.602912	2025-12-07 13:27:44.602912
161	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084661935.flv	2025-12-07 13:18:11.964432+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084661935.jpg	1939970	2025-12-07 13:18:13.334783	2025-12-07 13:18:13.334783
163	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084718551.flv	2025-12-07 13:18:39.827955+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084718551.jpg	101501	2025-12-07 13:18:40.907943	2025-12-07 13:18:40.907943
165	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084733561.flv	2025-12-07 13:18:54.832161+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084733561.jpg	125087	2025-12-07 13:18:55.896725	2025-12-07 13:18:55.896725
176	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084872146.flv	2025-12-07 13:21:42.176306+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084872146.jpg	1926795	2025-12-07 13:21:43.286887	2025-12-07 13:21:43.286887
179	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084915393.flv	2025-12-07 13:22:29.936781+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084915393.jpg	1950269	2025-12-07 13:22:31.098553	2025-12-07 13:22:31.098553
184	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084992268.flv	2025-12-07 13:23:42.296958+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084992268.jpg	1909155	2025-12-07 13:23:43.420012	2025-12-07 13:23:43.420012
186	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085019352.flv	2025-12-07 13:24:13.86636+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085019352.jpg	2102868	2025-12-07 13:24:14.973077	2025-12-07 13:24:14.973077
192	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085123542.flv	2025-12-07 13:25:59.955132+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085123542.jpg	2059554	2025-12-07 13:26:01.055717	2025-12-07 13:26:01.055717
194	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085159955.flv	2025-12-07 13:26:34.038439+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085159955.jpg	2190075	2025-12-07 13:26:35.145533	2025-12-07 13:26:35.145533
198	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085228205.flv	2025-12-07 13:27:42.428029+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085228205.jpg	2161916	2025-12-07 13:27:43.509566	2025-12-07 13:27:43.509566
201	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085262428.flv	2025-12-07 13:28:16.379328+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085262428.jpg	1895174	2025-12-07 13:28:17.463146	2025-12-07 13:28:17.463146
162	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084704413.flv	2025-12-07 13:18:25.597709+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084704413.jpg	100275	2025-12-07 13:18:26.683891	2025-12-07 13:18:26.683891
164	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084691965.flv	2025-12-07 13:18:41.995841+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084691965.jpg	1911175	2025-12-07 13:18:43.091104	2025-12-07 13:18:43.091104
166	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084748500.flv	2025-12-07 13:19:09.628377+08	1764341204704370850	大门设备	1	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084748500.jpg	88875	2025-12-07 13:19:10.711359	2025-12-07 13:19:10.711359
169	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084752027.flv	2025-12-07 13:19:42.05566+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084752027.jpg	1946109	2025-12-07 13:19:43.20714	2025-12-07 13:19:43.20714
171	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084782056.flv	2025-12-07 13:20:12.086071+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084782056.jpg	1962746	2025-12-07 13:20:14.100982	2025-12-07 13:20:14.100982
172	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084812086.flv	2025-12-07 13:20:42.115482+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084812086.jpg	2000356	2025-12-07 13:20:43.212775	2025-12-07 13:20:43.212775
173	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084811873.flv	2025-12-07 13:20:46.140269+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084811873.jpg	2037694	2025-12-07 13:20:47.213995	2025-12-07 13:20:47.213995
177	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084880574.flv	2025-12-07 13:21:55.392607+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084880574.jpg	2114762	2025-12-07 13:21:56.509715	2025-12-07 13:21:56.509715
180	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084932209.flv	2025-12-07 13:22:42.240131+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084932209.jpg	1918558	2025-12-07 13:22:43.345675	2025-12-07 13:22:43.345675
182	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084962240.flv	2025-12-07 13:23:12.266545+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765084962240.jpg	1979385	2025-12-07 13:23:13.34868	2025-12-07 13:23:13.34868
187	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085052328.flv	2025-12-07 13:24:42.358962+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085052328.jpg	1924659	2025-12-07 13:24:43.498632	2025-12-07 13:24:43.498632
188	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085053867.flv	2025-12-07 13:24:48.389666+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085053867.jpg	1943012	2025-12-07 13:24:49.45827	2025-12-07 13:24:49.45827
191	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085112391.flv	2025-12-07 13:25:42.419+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085112391.jpg	1948147	2025-12-07 13:25:43.527597	2025-12-07 13:25:43.527597
193	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085142420.flv	2025-12-07 13:26:12.448512+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085142420.jpg	1988380	2025-12-07 13:26:13.53825	2025-12-07 13:26:13.53825
197	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085202479.flv	2025-12-07 13:27:12.508523+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085202479.jpg	1956768	2025-12-07 13:27:13.617889	2025-12-07 13:27:13.617889
200	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085262540.flv	2025-12-07 13:28:12.568519+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085262540.jpg	1968276	2025-12-07 13:28:13.681607	2025-12-07 13:28:13.681607
202	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085292569.flv	2025-12-07 13:28:42.599012+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085292569.jpg	1932044	2025-12-07 13:28:43.710223	2025-12-07 13:28:43.710223
203	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085296381.flv	2025-12-07 13:28:50.342623+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085296381.jpg	2170570	2025-12-07 13:28:51.408508	2025-12-07 13:28:51.408508
204	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085322599.flv	2025-12-07 13:29:12.629502+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085322599.jpg	1939572	2025-12-07 13:29:13.729858	2025-12-07 13:29:13.729858
205	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085330343.flv	2025-12-07 13:29:24.37091+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085330343.jpg	1879079	2025-12-07 13:29:25.429269	2025-12-07 13:29:25.429269
206	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085352630.flv	2025-12-07 13:29:42.659989+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085352630.jpg	1919267	2025-12-07 13:29:43.776759	2025-12-07 13:29:43.776759
207	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085364371.flv	2025-12-07 13:29:58.266201+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085364371.jpg	2163559	2025-12-07 13:29:59.378431	2025-12-07 13:29:59.378431
208	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085382660.flv	2025-12-07 13:30:12.688473+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085382660.jpg	1902657	2025-12-07 13:30:13.77812	2025-12-07 13:30:13.77812
209	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085398267.flv	2025-12-07 13:30:32.544469+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085398267.jpg	1883561	2025-12-07 13:30:33.637902	2025-12-07 13:30:33.637902
210	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085412690.flv	2025-12-07 13:30:42.721954+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085412690.jpg	1918185	2025-12-07 13:30:43.823083	2025-12-07 13:30:43.823083
211	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085432546.flv	2025-12-07 13:31:06.929727+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085432546.jpg	2121679	2025-12-07 13:31:08.038232	2025-12-07 13:31:08.038232
212	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085442722.flv	2025-12-07 13:31:12.749432+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085442722.jpg	1928080	2025-12-07 13:31:13.866325	2025-12-07 13:31:13.866325
215	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085502781.flv	2025-12-07 13:32:12.810383+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085502781.jpg	1983474	2025-12-07 13:32:13.922932	2025-12-07 13:32:13.922932
219	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085562841.flv	2025-12-07 13:33:12.870325+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085562841.jpg	1944834	2025-12-07 13:33:13.951563	2025-12-07 13:33:13.951563
223	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085622902.flv	2025-12-07 13:34:12.930259+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085622902.jpg	1935002	2025-12-07 13:34:14.014718	2025-12-07 13:34:14.014718
224	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085639575.flv	2025-12-07 13:34:33.45621+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085639575.jpg	1870245	2025-12-07 13:34:34.578603	2025-12-07 13:34:34.578603
225	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085652932.flv	2025-12-07 13:34:42.961724+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085652932.jpg	1956124	2025-12-07 13:34:44.032746	2025-12-07 13:34:44.032746
228	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085707668.flv	2025-12-07 13:35:41.741714+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085707668.jpg	1867647	2025-12-07 13:35:42.803383	2025-12-07 13:35:42.803383
232	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085773054.flv	2025-12-07 13:36:43.082567+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085773054.jpg	1892752	2025-12-07 13:36:44.17064	2025-12-07 13:36:44.17064
233	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085776263.flv	2025-12-07 13:36:50.396192+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085776263.jpg	1888706	2025-12-07 13:36:51.456023	2025-12-07 13:36:51.456023
236	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085833113.flv	2025-12-07 13:37:43.141481+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085833113.jpg	1945079	2025-12-07 13:37:44.261507	2025-12-07 13:37:44.261507
238	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085863143.flv	2025-12-07 13:38:13.172937+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085863143.jpg	1982829	2025-12-07 13:38:14.290025	2025-12-07 13:38:14.290025
241	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085912683.flv	2025-12-07 13:39:06.489192+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085912683.jpg	1884903	2025-12-07 13:39:07.61709	2025-12-07 13:39:07.61709
242	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085923203.flv	2025-12-07 13:39:13.234844+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085923203.jpg	1936380	2025-12-07 13:39:14.372926	2025-12-07 13:39:14.372926
243	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085946490.flv	2025-12-07 13:39:40.174456+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085946490.jpg	2162711	2025-12-07 13:39:41.241573	2025-12-07 13:39:41.241573
245	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085983264.flv	2025-12-07 13:40:13.293748+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085983264.jpg	1917004	2025-12-07 13:40:14.397016	2025-12-07 13:40:14.397016
249	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086043326.flv	2025-12-07 13:41:13.354649+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086043326.jpg	1907439	2025-12-07 13:41:14.439672	2025-12-07 13:41:14.439672
251	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086073355.flv	2025-12-07 13:41:43.384098+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086073355.jpg	1916913	2025-12-07 13:41:44.464179	2025-12-07 13:41:44.464179
252	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086083932.flv	2025-12-07 13:41:45.850687+08	1764341204704370850	大门设备	20	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086083932.jpg	1288222	2025-12-07 13:41:46.961934	2025-12-07 13:41:46.961934
255	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086163446.flv	2025-12-07 13:43:13.474442+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086163446.jpg	1956927	2025-12-07 13:43:14.578004	2025-12-07 13:43:14.578004
256	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086193475.flv	2025-12-07 13:43:43.505888+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086193475.jpg	1955815	2025-12-07 13:43:44.640437	2025-12-07 13:43:44.640437
257	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086223506.flv	2025-12-07 13:44:13.536334+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086223506.jpg	1970010	2025-12-07 13:44:14.732971	2025-12-07 13:44:14.732971
260	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086313596.flv	2025-12-07 13:45:43.62567+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086313596.jpg	1962486	2025-12-07 13:45:44.782549	2025-12-07 13:45:44.782549
213	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085466930.flv	2025-12-07 13:31:41.142992+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085466930.jpg	1994130	2025-12-07 13:31:42.263883	2025-12-07 13:31:42.263883
216	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085501143.flv	2025-12-07 13:32:15.498246+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085501143.jpg	1980597	2025-12-07 13:32:16.594661	2025-12-07 13:32:16.594661
218	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085535499.flv	2025-12-07 13:32:51.711403+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085535499.jpg	2118910	2025-12-07 13:32:52.803163	2025-12-07 13:32:52.803163
221	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085592871.flv	2025-12-07 13:33:42.900793+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085592871.jpg	1931832	2025-12-07 13:33:43.9858	2025-12-07 13:33:43.9858
227	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085682962.flv	2025-12-07 13:35:12.991187+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085682962.jpg	1907016	2025-12-07 13:35:14.063101	2025-12-07 13:35:14.063101
235	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085810397.flv	2025-12-07 13:37:24.462442+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085810397.jpg	2173635	2025-12-07 13:37:25.567266	2025-12-07 13:37:25.567266
254	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086133417.flv	2025-12-07 13:42:43.445994+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086133417.jpg	1911040	2025-12-07 13:42:44.561562	2025-12-07 13:42:44.561562
258	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086253538.flv	2025-12-07 13:44:43.56578+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086253538.jpg	1960833	2025-12-07 13:44:44.680112	2025-12-07 13:44:44.680112
270	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086613899.flv	2025-12-07 13:50:43.930096+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086613899.jpg	1954628	2025-12-07 13:50:45.057243	2025-12-07 13:50:45.057243
273	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086703992.flv	2025-12-07 13:52:14.020418+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086703992.jpg	1948010	2025-12-07 13:52:15.128062	2025-12-07 13:52:15.128062
214	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085472751.flv	2025-12-07 13:31:42.779909+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085472751.jpg	1952550	2025-12-07 13:31:43.881198	2025-12-07 13:31:43.881198
217	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085532811.flv	2025-12-07 13:32:42.840855+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085532811.jpg	1965809	2025-12-07 13:32:43.907657	2025-12-07 13:32:43.907657
220	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085571713.flv	2025-12-07 13:33:25.492681+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085571713.jpg	1871176	2025-12-07 13:33:26.586103	2025-12-07 13:33:26.586103
222	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085605493.flv	2025-12-07 13:33:59.574941+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085605493.jpg	2097992	2025-12-07 13:34:00.658094	2025-12-07 13:34:00.658094
226	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085673457.flv	2025-12-07 13:35:07.666459+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085673457.jpg	2149861	2025-12-07 13:35:08.729035	2025-12-07 13:35:08.729035
229	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085712992.flv	2025-12-07 13:35:42.956652+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085712992.jpg	1932937	2025-12-07 13:35:44.0849	2025-12-07 13:35:44.0849
230	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085742957.flv	2025-12-07 13:36:13.053108+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085742957.jpg	1911217	2025-12-07 13:36:14.14817	2025-12-07 13:36:14.14817
231	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085741743.flv	2025-12-07 13:36:16.261944+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085741743.jpg	2128516	2025-12-07 13:36:17.380007	2025-12-07 13:36:17.380007
234	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085803083.flv	2025-12-07 13:37:13.112025+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085803083.jpg	1955848	2025-12-07 13:37:14.204764	2025-12-07 13:37:14.204764
237	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085844463.flv	2025-12-07 13:37:58.661683+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085844463.jpg	1858342	2025-12-07 13:37:59.760248	2025-12-07 13:37:59.760248
239	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085878663.flv	2025-12-07 13:38:32.682933+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085878663.jpg	2184376	2025-12-07 13:38:33.763903	2025-12-07 13:38:33.763903
240	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085893174.flv	2025-12-07 13:38:43.202391+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085893174.jpg	1958105	2025-12-07 13:38:44.310191	2025-12-07 13:38:44.310191
244	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085953236.flv	2025-12-07 13:39:43.263297+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085953236.jpg	1954370	2025-12-07 13:39:44.336657	2025-12-07 13:39:44.336657
246	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085980175.flv	2025-12-07 13:40:14.131705+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765085980175.jpg	1887605	2025-12-07 13:40:15.515523	2025-12-07 13:40:15.515523
247	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086013294.flv	2025-12-07 13:40:43.325199+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086013294.jpg	1949008	2025-12-07 13:40:44.464847	2025-12-07 13:40:44.464847
248	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086014132.flv	2025-12-07 13:40:47.75997+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086014132.jpg	2207602	2025-12-07 13:40:48.864017	2025-12-07 13:40:48.864017
250	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086047760.flv	2025-12-07 13:41:23.932103+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086047760.jpg	2086851	2025-12-07 13:41:24.997763	2025-12-07 13:41:24.997763
253	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086103384.flv	2025-12-07 13:42:13.415546+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086103384.jpg	1909956	2025-12-07 13:42:14.5525	2025-12-07 13:42:14.5525
259	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086283566.flv	2025-12-07 13:45:13.595225+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086283566.jpg	1915841	2025-12-07 13:45:14.697503	2025-12-07 13:45:14.697503
261	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086343626.flv	2025-12-07 13:46:13.658114+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086343626.jpg	1913717	2025-12-07 13:46:14.790166	2025-12-07 13:46:14.790166
262	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086373659.flv	2025-12-07 13:46:43.685558+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086373659.jpg	1944800	2025-12-07 13:46:44.794353	2025-12-07 13:46:44.794353
263	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086403687.flv	2025-12-07 13:47:13.717001+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086403687.jpg	1914044	2025-12-07 13:47:14.802375	2025-12-07 13:47:14.802375
264	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086433717.flv	2025-12-07 13:47:43.746444+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086433717.jpg	1903346	2025-12-07 13:47:44.914991	2025-12-07 13:47:44.914991
267	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086523808.flv	2025-12-07 13:49:13.836771+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086523808.jpg	1946040	2025-12-07 13:49:14.921282	2025-12-07 13:49:14.921282
265	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086463747.flv	2025-12-07 13:48:13.778887+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086463747.jpg	1924166	2025-12-07 13:48:14.89362	2025-12-07 13:48:14.89362
268	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086553837.flv	2025-12-07 13:49:43.869213+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086553837.jpg	1975955	2025-12-07 13:49:44.959588	2025-12-07 13:49:44.959588
271	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086643931.flv	2025-12-07 13:51:13.957537+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086643931.jpg	1920439	2025-12-07 13:51:15.072584	2025-12-07 13:51:15.072584
266	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086493779.flv	2025-12-07 13:48:43.806329+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086493779.jpg	1919833	2025-12-07 13:48:44.910876	2025-12-07 13:48:44.910876
269	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086583870.flv	2025-12-07 13:50:13.898654+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086583870.jpg	1965214	2025-12-07 13:50:15.027694	2025-12-07 13:50:15.027694
272	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086673958.flv	2025-12-07 13:51:43.990977+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086673958.jpg	1932417	2025-12-07 13:51:45.121154	2025-12-07 13:51:45.121154
274	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086734021.flv	2025-12-07 13:52:44.049858+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086734021.jpg	1925663	2025-12-07 13:52:45.195895	2025-12-07 13:52:45.195895
275	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086764051.flv	2025-12-07 13:53:13.599324+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086764051.jpg	1925250	2025-12-07 13:53:14.699993	2025-12-07 13:53:14.699993
276	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086793600.flv	2025-12-07 13:53:44.108739+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086793600.jpg	1900989	2025-12-07 13:53:45.186164	2025-12-07 13:53:45.186164
277	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086824109.flv	2025-12-07 13:54:14.141178+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086824109.jpg	1893169	2025-12-07 13:54:15.245267	2025-12-07 13:54:15.245267
278	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086854141.flv	2025-12-07 13:54:44.169618+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086854141.jpg	1943451	2025-12-07 13:54:45.274048	2025-12-07 13:54:45.274048
279	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086884170.flv	2025-12-07 13:55:14.202058+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086884170.jpg	1942734	2025-12-07 13:55:15.339793	2025-12-07 13:55:15.339793
280	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086914203.flv	2025-12-07 13:55:44.229497+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086914203.jpg	1977959	2025-12-07 13:55:45.356924	2025-12-07 13:55:45.356924
281	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086944230.flv	2025-12-07 13:56:14.260936+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086944230.jpg	1962766	2025-12-07 13:56:15.413935	2025-12-07 13:56:15.413935
282	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086974261.flv	2025-12-07 13:56:44.290375+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765086974261.jpg	1939655	2025-12-07 13:56:45.378103	2025-12-07 13:56:45.378103
283	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087004291.flv	2025-12-07 13:57:14.320815+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087004291.jpg	1941805	2025-12-07 13:57:15.466235	2025-12-07 13:57:15.466235
284	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087034321.flv	2025-12-07 13:57:44.350253+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087034321.jpg	1917790	2025-12-07 13:57:45.462003	2025-12-07 13:57:45.462003
285	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087064351.flv	2025-12-07 13:58:14.382415+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087064351.jpg	1943765	2025-12-07 13:58:15.512634	2025-12-07 13:58:15.512634
286	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087094383.flv	2025-12-07 13:58:44.412084+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087094383.jpg	1912729	2025-12-07 13:58:45.519561	2025-12-07 13:58:45.519561
287	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087124412.flv	2025-12-07 13:59:14.440792+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087124412.jpg	1928862	2025-12-07 13:59:15.556122	2025-12-07 13:59:15.556122
288	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087154441.flv	2025-12-07 13:59:44.470536+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087154441.jpg	1904377	2025-12-07 13:59:45.573995	2025-12-07 13:59:45.573995
289	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087184472.flv	2025-12-07 14:00:14.502314+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087184472.jpg	1903674	2025-12-07 14:00:15.613925	2025-12-07 14:00:15.613925
290	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087214503.flv	2025-12-07 14:00:44.533125+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087214503.jpg	1939694	2025-12-07 14:00:45.645669	2025-12-07 14:00:45.645669
291	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087244533.flv	2025-12-07 14:01:14.563967+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087244533.jpg	1951056	2025-12-07 14:01:15.681974	2025-12-07 14:01:15.681974
292	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087274565.flv	2025-12-07 14:01:44.591838+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087274565.jpg	1989768	2025-12-07 14:01:45.676415	2025-12-07 14:01:45.676415
293	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087304593.flv	2025-12-07 14:02:14.622736+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087304593.jpg	1949537	2025-12-07 14:02:15.726152	2025-12-07 14:02:15.726152
294	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087334623.flv	2025-12-07 14:02:44.653659+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087334623.jpg	1919978	2025-12-07 14:02:45.811772	2025-12-07 14:02:45.811772
295	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087364655.flv	2025-12-07 14:03:14.684607+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087364655.jpg	1949618	2025-12-07 14:03:15.817268	2025-12-07 14:03:15.817268
302	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087574866.flv	2025-12-07 14:06:44.893812+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087574866.jpg	1942068	2025-12-07 14:06:45.990629	2025-12-07 14:06:45.990629
296	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087394685.flv	2025-12-07 14:03:44.713577+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087394685.jpg	1907139	2025-12-07 14:03:45.829907	2025-12-07 14:03:45.829907
297	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087424715.flv	2025-12-07 14:04:14.745569+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087424715.jpg	1970170	2025-12-07 14:04:15.87598	2025-12-07 14:04:15.87598
298	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087454747.flv	2025-12-07 14:04:44.775582+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087454747.jpg	1899415	2025-12-07 14:04:45.913779	2025-12-07 14:04:45.913779
301	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087544834.flv	2025-12-07 14:06:14.864729+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087544834.jpg	1909008	2025-12-07 14:06:16.039548	2025-12-07 14:06:16.039548
299	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087484776.flv	2025-12-07 14:05:14.804613+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087484776.jpg	1898175	2025-12-07 14:05:15.942811	2025-12-07 14:05:15.942811
300	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087514806.flv	2025-12-07 14:05:44.833663+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087514806.jpg	1920630	2025-12-07 14:05:45.958122	2025-12-07 14:05:45.958122
303	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087604894.flv	2025-12-07 14:07:14.923909+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087604894.jpg	1981174	2025-12-07 14:07:16.029458	2025-12-07 14:07:16.029458
304	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087634925.flv	2025-12-07 14:07:44.957021+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087634925.jpg	1963526	2025-12-07 14:07:46.121351	2025-12-07 14:07:46.121351
305	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087664957.flv	2025-12-07 14:08:14.987147+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087664957.jpg	1951937	2025-12-07 14:08:16.119846	2025-12-07 14:08:16.119846
306	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087694987.flv	2025-12-07 14:08:45.016285+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087694987.jpg	1911418	2025-12-07 14:08:46.159776	2025-12-07 14:08:46.159776
307	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087725017.flv	2025-12-07 14:09:15.047435+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087725017.jpg	1960051	2025-12-07 14:09:16.176963	2025-12-07 14:09:16.176963
308	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087755048.flv	2025-12-07 14:09:20.619093+08	1764341204704370850	大门设备	5	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087755048.jpg	361036	2025-12-07 14:09:21.706506	2025-12-07 14:09:21.706506
309	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087764637.flv	2025-12-07 14:09:55.464963+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087764637.jpg	2055006	2025-12-07 14:09:56.621274	2025-12-07 14:09:56.621274
310	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087795466.flv	2025-12-07 14:10:25.495138+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087795466.jpg	1975764	2025-12-07 14:10:26.664297	2025-12-07 14:10:26.664297
311	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087825495.flv	2025-12-07 14:10:55.524324+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087825495.jpg	1960651	2025-12-07 14:10:56.661527	2025-12-07 14:10:56.661527
312	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087855525.flv	2025-12-07 14:11:25.554518+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087855525.jpg	1986525	2025-12-07 14:11:26.720358	2025-12-07 14:11:26.720358
313	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087885555.flv	2025-12-07 14:11:55.583722+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087885555.jpg	2009140	2025-12-07 14:11:56.682929	2025-12-07 14:11:56.682929
314	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087915584.flv	2025-12-07 14:12:25.613934+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087915584.jpg	1995882	2025-12-07 14:12:26.702737	2025-12-07 14:12:26.702737
315	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087945614.flv	2025-12-07 14:12:55.644153+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087945614.jpg	1987006	2025-12-07 14:12:56.728434	2025-12-07 14:12:56.728434
316	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087975645.flv	2025-12-07 14:13:25.67438+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765087975645.jpg	1951533	2025-12-07 14:13:26.777858	2025-12-07 14:13:26.777858
317	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088005675.flv	2025-12-07 14:13:55.704613+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088005675.jpg	1957631	2025-12-07 14:13:56.833539	2025-12-07 14:13:56.833539
318	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088035706.flv	2025-12-07 14:14:25.733853+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088035706.jpg	1967394	2025-12-07 14:14:26.831446	2025-12-07 14:14:26.831446
319	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088065735.flv	2025-12-07 14:14:55.7671+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088065735.jpg	1943036	2025-12-07 14:14:56.926127	2025-12-07 14:14:56.926127
320	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088095767.flv	2025-12-07 14:15:25.321379+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088095767.jpg	1947145	2025-12-07 14:15:26.439764	2025-12-07 14:15:26.439764
321	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088125323.flv	2025-12-07 14:15:55.824609+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088125323.jpg	1919304	2025-12-07 14:15:56.930447	2025-12-07 14:15:56.930447
322	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088155825.flv	2025-12-07 14:16:03.108188+08	1764341204704370850	大门设备	7	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088155825.jpg	541354	2025-12-07 14:16:04.184723	2025-12-07 14:16:04.184723
323	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088166188.flv	2025-12-07 14:16:37.011228+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088166188.jpg	2055006	2025-12-07 14:16:38.122257	2025-12-07 14:16:38.122257
324	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088197012.flv	2025-12-07 14:17:07.040497+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088197012.jpg	1975764	2025-12-07 14:17:08.154764	2025-12-07 14:17:08.154764
325	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088227041.flv	2025-12-07 14:17:37.070771+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088227041.jpg	1960651	2025-12-07 14:17:38.240998	2025-12-07 14:17:38.240998
326	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088257071.flv	2025-12-07 14:18:07.102076+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088257071.jpg	1986525	2025-12-07 14:18:08.184628	2025-12-07 14:18:08.184628
327	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088287102.flv	2025-12-07 14:18:37.133331+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088287102.jpg	2009140	2025-12-07 14:18:38.294211	2025-12-07 14:18:38.294211
332	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088437255.flv	2025-12-07 14:21:07.283793+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088437255.jpg	1967394	2025-12-07 14:21:08.398777	2025-12-07 14:21:08.398777
333	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088467284.flv	2025-12-07 14:21:37.313095+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088467284.jpg	1943036	2025-12-07 14:21:38.40842	2025-12-07 14:21:38.40842
338	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088617435.flv	2025-12-07 14:24:07.46464+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088617435.jpg	1955910	2025-12-07 14:24:08.580476	2025-12-07 14:24:08.580476
339	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088647466.flv	2025-12-07 14:24:37.495955+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088647466.jpg	1994228	2025-12-07 14:24:38.612323	2025-12-07 14:24:38.612323
346	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088857678.flv	2025-12-07 14:28:07.707209+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088857678.jpg	1939970	2025-12-07 14:28:08.807966	2025-12-07 14:28:08.807966
347	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088887707.flv	2025-12-07 14:28:37.734537+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088887707.jpg	1911175	2025-12-07 14:28:38.864906	2025-12-07 14:28:38.864906
328	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088317135.flv	2025-12-07 14:19:07.163617+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088317135.jpg	1995882	2025-12-07 14:19:08.296785	2025-12-07 14:19:08.296785
329	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088347164.flv	2025-12-07 14:19:37.193906+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088347164.jpg	1987006	2025-12-07 14:19:38.296729	2025-12-07 14:19:38.296729
340	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088677496.flv	2025-12-07 14:25:07.523273+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088677496.jpg	1979066	2025-12-07 14:25:08.674631	2025-12-07 14:25:08.674631
341	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088707524.flv	2025-12-07 14:25:37.556591+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088707524.jpg	1953658	2025-12-07 14:25:38.720552	2025-12-07 14:25:38.720552
343	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088767588.flv	2025-12-07 14:26:37.616234+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088767588.jpg	1926420	2025-12-07 14:26:38.755954	2025-12-07 14:26:38.755954
348	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088917735.flv	2025-12-07 14:29:07.765866+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088917735.jpg	1909646	2025-12-07 14:29:08.849459	2025-12-07 14:29:08.849459
349	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088947766.flv	2025-12-07 14:29:37.796195+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088947766.jpg	1946109	2025-12-07 14:29:38.908009	2025-12-07 14:29:38.908009
330	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088377194.flv	2025-12-07 14:20:07.224199+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088377194.jpg	1951533	2025-12-07 14:20:08.350022	2025-12-07 14:20:08.350022
331	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088407224.flv	2025-12-07 14:20:37.254495+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088407224.jpg	1957631	2025-12-07 14:20:38.397464	2025-12-07 14:20:38.397464
336	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088557375.flv	2025-12-07 14:23:07.404015+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088557375.jpg	1906469	2025-12-07 14:23:08.527853	2025-12-07 14:23:08.527853
337	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088587404.flv	2025-12-07 14:23:37.434326+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088587404.jpg	1954310	2025-12-07 14:23:38.586575	2025-12-07 14:23:38.586575
342	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088737557.flv	2025-12-07 14:26:07.586912+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088737557.jpg	1954083	2025-12-07 14:26:08.740369	2025-12-07 14:26:08.740369
344	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088797617.flv	2025-12-07 14:27:07.647558+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088797617.jpg	1957326	2025-12-07 14:27:08.791925	2025-12-07 14:27:08.791925
345	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088827648.flv	2025-12-07 14:27:37.676883+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088827648.jpg	1928282	2025-12-07 14:27:38.795527	2025-12-07 14:27:38.795527
350	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088977798.flv	2025-12-07 14:30:07.825526+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088977798.jpg	1962746	2025-12-07 14:30:08.937256	2025-12-07 14:30:08.937256
351	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089007826.flv	2025-12-07 14:30:37.858858+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089007826.jpg	2000356	2025-12-07 14:30:39.000886	2025-12-07 14:30:39.000886
334	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088497313.flv	2025-12-07 14:22:06.881425+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088497313.jpg	1947145	2025-12-07 14:22:08.022349	2025-12-07 14:22:08.022349
335	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088526882.flv	2025-12-07 14:22:37.374706+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765088526882.jpg	1919304	2025-12-07 14:22:38.526349	2025-12-07 14:22:38.526349
352	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089037860.flv	2025-12-07 14:31:07.886191+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089037860.jpg	1959948	2025-12-07 14:31:09.02919	2025-12-07 14:31:09.02919
353	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089067888.flv	2025-12-07 14:31:37.918524+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089067888.jpg	1926795	2025-12-07 14:31:39.029031	2025-12-07 14:31:39.029031
354	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089097919.flv	2025-12-07 14:32:07.948859+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089097919.jpg	1955250	2025-12-07 14:32:09.099498	2025-12-07 14:32:09.099498
355	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089127950.flv	2025-12-07 14:32:37.977903+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089127950.jpg	1918558	2025-12-07 14:32:39.083371	2025-12-07 14:32:39.083371
356	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089157978.flv	2025-12-07 14:33:08.00792+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089157978.jpg	1979385	2025-12-07 14:33:09.139451	2025-12-07 14:33:09.139451
357	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089188008.flv	2025-12-07 14:33:38.036953+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089188008.jpg	1909155	2025-12-07 14:33:39.130936	2025-12-07 14:33:39.130936
358	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089218038.flv	2025-12-07 14:34:08.069001+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089218038.jpg	1903095	2025-12-07 14:34:09.206619	2025-12-07 14:34:09.206619
359	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089248069.flv	2025-12-07 14:34:38.098065+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089248069.jpg	1924659	2025-12-07 14:34:39.198294	2025-12-07 14:34:39.198294
360	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089278099.flv	2025-12-07 14:35:08.130142+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089278099.jpg	1915255	2025-12-07 14:35:09.261377	2025-12-07 14:35:09.261377
361	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089308130.flv	2025-12-07 14:35:38.160233+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089308130.jpg	1948147	2025-12-07 14:35:39.329679	2025-12-07 14:35:39.329679
362	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089338161.flv	2025-12-07 14:36:08.189336+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089338161.jpg	1988380	2025-12-07 14:36:09.367978	2025-12-07 14:36:09.367978
363	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089368190.flv	2025-12-07 14:36:38.218451+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089368190.jpg	1972009	2025-12-07 14:36:39.337855	2025-12-07 14:36:39.337855
364	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089398220.flv	2025-12-07 14:37:08.250576+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089398220.jpg	1956768	2025-12-07 14:37:09.388446	2025-12-07 14:37:09.388446
365	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089428251.flv	2025-12-07 14:37:38.279712+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089428251.jpg	1916328	2025-12-07 14:37:39.434968	2025-12-07 14:37:39.434968
366	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089458281.flv	2025-12-07 14:38:08.309859+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089458281.jpg	1968276	2025-12-07 14:38:09.425027	2025-12-07 14:38:09.425027
367	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089488310.flv	2025-12-07 14:38:38.341014+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089488310.jpg	1932044	2025-12-07 14:38:39.460282	2025-12-07 14:38:39.460282
368	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089518341.flv	2025-12-07 14:39:08.371178+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089518341.jpg	1939572	2025-12-07 14:39:09.512287	2025-12-07 14:39:09.512287
369	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089548371.flv	2025-12-07 14:39:38.40035+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089548371.jpg	1919267	2025-12-07 14:39:39.547011	2025-12-07 14:39:39.547011
370	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089578401.flv	2025-12-07 14:40:08.43053+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089578401.jpg	1902657	2025-12-07 14:40:09.547436	2025-12-07 14:40:09.547436
371	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089608431.flv	2025-12-07 14:40:38.460717+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089608431.jpg	1918185	2025-12-07 14:40:39.61366	2025-12-07 14:40:39.61366
372	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089638461.flv	2025-12-07 14:41:08.491912+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089638461.jpg	1928080	2025-12-07 14:41:09.646363	2025-12-07 14:41:09.646363
373	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089668493.flv	2025-12-07 14:41:38.522112+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089668493.jpg	1952550	2025-12-07 14:41:39.6652	2025-12-07 14:41:39.6652
374	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089698522.flv	2025-12-07 14:42:08.550319+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089698522.jpg	1983474	2025-12-07 14:42:09.647473	2025-12-07 14:42:09.647473
375	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089728558.flv	2025-12-07 14:42:38.582532+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089728558.jpg	1965809	2025-12-07 14:42:39.730258	2025-12-07 14:42:39.730258
388	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090118944.flv	2025-12-07 14:49:08.972696+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090118944.jpg	1936380	2025-12-07 14:49:10.063141	2025-12-07 14:49:10.063141
392	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090239065.flv	2025-12-07 14:51:09.093776+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090239065.jpg	1907439	2025-12-07 14:51:10.176809	2025-12-07 14:51:10.176809
398	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090419246.flv	2025-12-07 14:54:09.276453+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090419246.jpg	1970010	2025-12-07 14:54:10.412233	2025-12-07 14:54:10.412233
399	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090449278.flv	2025-12-07 14:54:39.306738+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090449278.jpg	1960833	2025-12-07 14:54:40.464379	2025-12-07 14:54:40.464379
408	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090719550.flv	2025-12-07 14:59:09.576355+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090719550.jpg	1946040	2025-12-07 14:59:10.69216	2025-12-07 14:59:10.69216
409	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090749577.flv	2025-12-07 14:59:39.61065+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090749577.jpg	1975955	2025-12-07 14:59:40.733136	2025-12-07 14:59:40.733136
414	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090899730.flv	2025-12-07 15:02:09.760138+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090899730.jpg	1948010	2025-12-07 15:02:10.887968	2025-12-07 15:02:10.887968
415	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090929760.flv	2025-12-07 15:02:39.788437+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090929760.jpg	1925663	2025-12-07 15:02:40.918503	2025-12-07 15:02:40.918503
418	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091019849.flv	2025-12-07 15:04:09.880338+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091019849.jpg	1893169	2025-12-07 15:04:11.006738	2025-12-07 15:04:11.006738
419	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091049882.flv	2025-12-07 15:04:39.908639+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091049882.jpg	1943451	2025-12-07 15:04:41.006416	2025-12-07 15:04:41.006416
424	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091200032.flv	2025-12-07 15:07:10.060574+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091200032.jpg	1941805	2025-12-07 15:07:11.133525	2025-12-07 15:07:11.133525
425	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091230061.flv	2025-12-07 15:07:40.091115+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091230061.jpg	1917790	2025-12-07 15:07:41.219786	2025-12-07 15:07:41.219786
430	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091380213.flv	2025-12-07 15:10:10.242655+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091380213.jpg	1903674	2025-12-07 15:10:11.382842	2025-12-07 15:10:11.382842
431	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091410244.flv	2025-12-07 15:10:40.275135+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091410244.jpg	1939694	2025-12-07 15:10:41.410496	2025-12-07 15:10:41.410496
376	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089758584.flv	2025-12-07 14:43:08.61175+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089758584.jpg	1944834	2025-12-07 14:43:09.748789	2025-12-07 14:43:09.748789
377	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089788612.flv	2025-12-07 14:43:38.640973+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089788612.jpg	1931832	2025-12-07 14:43:39.740461	2025-12-07 14:43:39.740461
380	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089878704.flv	2025-12-07 14:45:08.733671+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089878704.jpg	1907016	2025-12-07 14:45:09.864732	2025-12-07 14:45:09.864732
381	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089908735.flv	2025-12-07 14:45:38.675917+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089908735.jpg	1932937	2025-12-07 14:45:39.762794	2025-12-07 14:45:39.762794
386	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090058884.flv	2025-12-07 14:48:08.914171+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090058884.jpg	1982829	2025-12-07 14:48:10.024286	2025-12-07 14:48:10.024286
387	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090088914.flv	2025-12-07 14:48:38.943432+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090088914.jpg	1958105	2025-12-07 14:48:40.043848	2025-12-07 14:48:40.043848
390	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090179005.flv	2025-12-07 14:50:09.036231+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090179005.jpg	1917004	2025-12-07 14:50:10.191212	2025-12-07 14:50:10.191212
391	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090209038.flv	2025-12-07 14:50:39.063502+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090209038.jpg	1949008	2025-12-07 14:50:40.176297	2025-12-07 14:50:40.176297
394	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090299126.flv	2025-12-07 14:52:09.154328+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090299126.jpg	1909956	2025-12-07 14:52:10.256966	2025-12-07 14:52:10.256966
395	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090329155.flv	2025-12-07 14:52:39.184607+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090329155.jpg	1911040	2025-12-07 14:52:40.328337	2025-12-07 14:52:40.328337
396	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090359185.flv	2025-12-07 14:53:09.217887+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090359185.jpg	1956927	2025-12-07 14:53:10.376677	2025-12-07 14:53:10.376677
397	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090389218.flv	2025-12-07 14:53:39.245169+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090389218.jpg	1955815	2025-12-07 14:53:40.328498	2025-12-07 14:53:40.328498
402	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090539366.flv	2025-12-07 14:56:09.3966+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090539366.jpg	1913717	2025-12-07 14:56:10.557519	2025-12-07 14:56:10.557519
403	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090569398.flv	2025-12-07 14:56:39.42789+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090569398.jpg	1944800	2025-12-07 14:56:40.577233	2025-12-07 14:56:40.577233
412	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090839670.flv	2025-12-07 15:01:09.699541+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090839670.jpg	1920439	2025-12-07 15:01:10.840363	2025-12-07 15:01:10.840363
413	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090869700.flv	2025-12-07 15:01:39.729839+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090869700.jpg	1932417	2025-12-07 15:01:40.856223	2025-12-07 15:01:40.856223
422	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091139971.flv	2025-12-07 15:06:10.000545+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091139971.jpg	1962766	2025-12-07 15:06:11.094839	2025-12-07 15:06:11.094839
423	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091170001.flv	2025-12-07 15:06:40.032022+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091170001.jpg	1939655	2025-12-07 15:06:41.151118	2025-12-07 15:06:41.151118
428	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091320152.flv	2025-12-07 15:09:10.182669+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091320152.jpg	1928862	2025-12-07 15:09:11.301994	2025-12-07 15:09:11.301994
429	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091350184.flv	2025-12-07 15:09:40.213166+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091350184.jpg	1904377	2025-12-07 15:09:41.373293	2025-12-07 15:09:41.373293
378	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089818641.flv	2025-12-07 14:44:08.672201+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089818641.jpg	1935002	2025-12-07 14:44:09.796601	2025-12-07 14:44:09.796601
379	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089848673.flv	2025-12-07 14:44:38.703434+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089848673.jpg	1956124	2025-12-07 14:44:39.832015	2025-12-07 14:44:39.832015
384	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089998823.flv	2025-12-07 14:47:08.854658+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089998823.jpg	1955848	2025-12-07 14:47:09.982529	2025-12-07 14:47:09.982529
385	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090028855.flv	2025-12-07 14:47:38.883913+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090028855.jpg	1945079	2025-12-07 14:47:40.028649	2025-12-07 14:47:40.028649
389	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090148974.flv	2025-12-07 14:49:39.004962+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090148974.jpg	1954370	2025-12-07 14:49:40.089916	2025-12-07 14:49:40.089916
400	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090479308.flv	2025-12-07 14:55:09.338024+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090479308.jpg	1915841	2025-12-07 14:55:10.484405	2025-12-07 14:55:10.484405
401	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090509338.flv	2025-12-07 14:55:39.365312+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090509338.jpg	1962486	2025-12-07 14:55:40.449997	2025-12-07 14:55:40.449997
406	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090659488.flv	2025-12-07 14:58:09.518766+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090659488.jpg	1924166	2025-12-07 14:58:10.665573	2025-12-07 14:58:10.665573
407	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090689520.flv	2025-12-07 14:58:39.54906+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090689520.jpg	1919833	2025-12-07 14:58:40.709124	2025-12-07 14:58:40.709124
416	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090959789.flv	2025-12-07 15:03:09.350763+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090959789.jpg	1925250	2025-12-07 15:03:10.494556	2025-12-07 15:03:10.494556
417	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090989352.flv	2025-12-07 15:03:39.849037+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090989352.jpg	1900989	2025-12-07 15:03:40.965499	2025-12-07 15:03:40.965499
420	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091079910.flv	2025-12-07 15:05:09.940941+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091079910.jpg	1942734	2025-12-07 15:05:11.047084	2025-12-07 15:05:11.047084
421	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091109942.flv	2025-12-07 15:05:39.970243+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091109942.jpg	1977959	2025-12-07 15:05:41.078864	2025-12-07 15:05:41.078864
382	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089938676.flv	2025-12-07 14:46:08.793157+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089938676.jpg	1911217	2025-12-07 14:46:09.869575	2025-12-07 14:46:09.869575
383	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089968793.flv	2025-12-07 14:46:38.822406+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765089968793.jpg	1892752	2025-12-07 14:46:39.928376	2025-12-07 14:46:39.928376
393	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090269094.flv	2025-12-07 14:51:39.125051+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090269094.jpg	1916913	2025-12-07 14:51:40.238039	2025-12-07 14:51:40.238039
404	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090599428.flv	2025-12-07 14:57:09.460181+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090599428.jpg	1914044	2025-12-07 14:57:10.589039	2025-12-07 14:57:10.589039
405	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090629461.flv	2025-12-07 14:57:39.487473+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090629461.jpg	1903346	2025-12-07 14:57:40.606731	2025-12-07 14:57:40.606731
410	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090779611.flv	2025-12-07 15:00:09.637946+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090779611.jpg	1965214	2025-12-07 15:00:10.782276	2025-12-07 15:00:10.782276
411	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090809638.flv	2025-12-07 15:00:39.669243+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765090809638.jpg	1954628	2025-12-07 15:00:40.789934	2025-12-07 15:00:40.789934
426	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091260091.flv	2025-12-07 15:08:10.121643+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091260091.jpg	1943765	2025-12-07 15:08:11.276299	2025-12-07 15:08:11.276299
427	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091290123.flv	2025-12-07 15:08:40.151161+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091290123.jpg	1912729	2025-12-07 15:08:41.270807	2025-12-07 15:08:41.270807
432	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091440275.flv	2025-12-07 15:11:10.301607+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091440275.jpg	1951056	2025-12-07 15:11:11.412076	2025-12-07 15:11:11.412076
433	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091470302.flv	2025-12-07 15:11:40.335071+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091470302.jpg	1989768	2025-12-07 15:11:41.467837	2025-12-07 15:11:41.467837
434	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091500335.flv	2025-12-07 15:12:10.364528+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091500335.jpg	1949537	2025-12-07 15:12:11.480731	2025-12-07 15:12:11.480731
435	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091530365.flv	2025-12-07 15:12:40.393978+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091530365.jpg	1919978	2025-12-07 15:12:41.520903	2025-12-07 15:12:41.520903
436	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091560402.flv	2025-12-07 15:13:10.424422+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091560402.jpg	1949618	2025-12-07 15:13:11.579144	2025-12-07 15:13:11.579144
437	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091590425.flv	2025-12-07 15:13:40.45486+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091590425.jpg	1907139	2025-12-07 15:13:41.610087	2025-12-07 15:13:41.610087
438	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091620456.flv	2025-12-07 15:14:10.485292+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091620456.jpg	1970170	2025-12-07 15:14:11.609737	2025-12-07 15:14:11.609737
439	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091650487.flv	2025-12-07 15:14:40.513718+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091650487.jpg	1899415	2025-12-07 15:14:41.611597	2025-12-07 15:14:41.611597
440	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091680514.flv	2025-12-07 15:15:10.54614+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091680514.jpg	1898175	2025-12-07 15:15:11.713079	2025-12-07 15:15:11.713079
441	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091710546.flv	2025-12-07 15:15:40.575556+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091710546.jpg	1920630	2025-12-07 15:15:41.761015	2025-12-07 15:15:41.761015
442	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091740576.flv	2025-12-07 15:16:10.606968+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091740576.jpg	1909008	2025-12-07 15:16:11.756546	2025-12-07 15:16:11.756546
443	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091770607.flv	2025-12-07 15:16:40.634376+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091770607.jpg	1942068	2025-12-07 15:16:41.780993	2025-12-07 15:16:41.780993
444	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091800635.flv	2025-12-07 15:17:10.66778+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091800635.jpg	1981174	2025-12-07 15:17:11.810244	2025-12-07 15:17:11.810244
445	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091830668.flv	2025-12-07 15:17:40.69518+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091830668.jpg	1963526	2025-12-07 15:17:41.82205	2025-12-07 15:17:41.82205
446	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091860695.flv	2025-12-07 15:18:10.726576+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091860695.jpg	1951937	2025-12-07 15:18:11.903129	2025-12-07 15:18:11.903129
447	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091890727.flv	2025-12-07 15:18:40.75597+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091890727.jpg	1911418	2025-12-07 15:18:41.851044	2025-12-07 15:18:41.851044
452	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092040879.flv	2025-12-07 15:21:10.907891+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092040879.jpg	1897945	2025-12-07 15:21:12.000841	2025-12-07 15:21:12.000841
453	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092070909.flv	2025-12-07 15:21:40.938267+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092070909.jpg	1913231	2025-12-07 15:21:42.083983	2025-12-07 15:21:42.083983
463	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092371208.flv	2025-12-07 15:26:41.150932+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092371208.jpg	1928990	2025-12-07 15:26:42.252848	2025-12-07 15:26:42.252848
464	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092401151.flv	2025-12-07 15:27:11.268286+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092401151.jpg	1907549	2025-12-07 15:27:12.378173	2025-12-07 15:27:12.378173
465	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092431269.flv	2025-12-07 15:27:41.298642+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092431269.jpg	1889573	2025-12-07 15:27:42.409348	2025-12-07 15:27:42.409348
466	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092461300.flv	2025-12-07 15:28:11.328998+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092461300.jpg	1951202	2025-12-07 15:28:12.441466	2025-12-07 15:28:12.441466
467	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092491330.flv	2025-12-07 15:28:41.358352+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092491330.jpg	1940489	2025-12-07 15:28:42.45088	2025-12-07 15:28:42.45088
476	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092761603.flv	2025-12-07 15:33:11.632504+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092761603.jpg	1907451	2025-12-07 15:33:12.776594	2025-12-07 15:33:12.776594
477	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092791633.flv	2025-12-07 15:33:41.660851+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092791633.jpg	1906112	2025-12-07 15:33:42.768862	2025-12-07 15:33:42.768862
482	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092941782.flv	2025-12-07 15:36:11.811578+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092941782.jpg	1913133	2025-12-07 15:36:12.934578	2025-12-07 15:36:12.934578
488	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093121965.flv	2025-12-07 15:39:11.992636+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093121965.jpg	1920064	2025-12-07 15:39:13.116266	2025-12-07 15:39:13.116266
489	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093151994.flv	2025-12-07 15:39:42.024978+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093151994.jpg	1917230	2025-12-07 15:39:43.212601	2025-12-07 15:39:43.212601
494	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093302147.flv	2025-12-07 15:42:12.174238+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093302147.jpg	1915389	2025-12-07 15:42:13.295417	2025-12-07 15:42:13.295417
495	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093332175.flv	2025-12-07 15:42:42.206896+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093332175.jpg	1930872	2025-12-07 15:42:43.406277	2025-12-07 15:42:43.406277
448	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091920757.flv	2025-12-07 15:19:10.785359+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091920757.jpg	1960051	2025-12-07 15:19:11.90667	2025-12-07 15:19:11.90667
449	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091950786.flv	2025-12-07 15:19:40.816746+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091950786.jpg	1925290	2025-12-07 15:19:41.94301	2025-12-07 15:19:41.94301
454	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092100939.flv	2025-12-07 15:22:10.967641+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092100939.jpg	1922133	2025-12-07 15:22:12.087827	2025-12-07 15:22:12.087827
455	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092130969.flv	2025-12-07 15:22:40.999013+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092130969.jpg	1950463	2025-12-07 15:22:42.169644	2025-12-07 15:22:42.169644
460	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092281118.flv	2025-12-07 15:25:11.147846+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092281118.jpg	1929153	2025-12-07 15:25:12.277198	2025-12-07 15:25:12.277198
461	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092311148.flv	2025-12-07 15:25:41.177208+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092311148.jpg	1948783	2025-12-07 15:25:42.30383	2025-12-07 15:25:42.30383
468	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092521359.flv	2025-12-07 15:29:11.389706+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092521359.jpg	1979652	2025-12-07 15:29:12.477084	2025-12-07 15:29:12.477084
469	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092551390.flv	2025-12-07 15:29:41.422058+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092551390.jpg	1954678	2025-12-07 15:29:42.536533	2025-12-07 15:29:42.536533
474	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092701542.flv	2025-12-07 15:32:11.571809+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092701542.jpg	1904613	2025-12-07 15:32:12.718274	2025-12-07 15:32:12.718274
475	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092731572.flv	2025-12-07 15:32:41.603157+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092731572.jpg	1914001	2025-12-07 15:32:42.755026	2025-12-07 15:32:42.755026
480	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092881722.flv	2025-12-07 15:35:11.751888+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092881722.jpg	1967474	2025-12-07 15:35:12.831266	2025-12-07 15:35:12.831266
481	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092911752.flv	2025-12-07 15:35:41.780233+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092911752.jpg	1957034	2025-12-07 15:35:42.893794	2025-12-07 15:35:42.893794
485	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093031873.flv	2025-12-07 15:37:41.902608+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093031873.jpg	1942313	2025-12-07 15:37:43.045391	2025-12-07 15:37:43.045391
490	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093182025.flv	2025-12-07 15:40:12.05532+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093182025.jpg	1943829	2025-12-07 15:40:13.193224	2025-12-07 15:40:13.193224
491	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093212056.flv	2025-12-07 15:40:42.083775+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093212056.jpg	1972938	2025-12-07 15:40:43.224969	2025-12-07 15:40:43.224969
497	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093392237.flv	2025-12-07 15:43:42.266441+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093392237.jpg	1921382	2025-12-07 15:43:43.358468	2025-12-07 15:43:43.358468
450	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091980818.flv	2025-12-07 15:20:10.84713+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765091980818.jpg	1930200	2025-12-07 15:20:11.972869	2025-12-07 15:20:11.972869
451	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092010848.flv	2025-12-07 15:20:40.878512+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092010848.jpg	1916088	2025-12-07 15:20:42.005043	2025-12-07 15:20:42.005043
457	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092191027.flv	2025-12-07 15:23:41.057752+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092191027.jpg	1961854	2025-12-07 15:23:42.205088	2025-12-07 15:23:42.205088
462	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092341178.flv	2025-12-07 15:26:11.207569+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092341178.jpg	1904879	2025-12-07 15:26:12.299966	2025-12-07 15:26:12.299966
470	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092581423.flv	2025-12-07 15:30:11.45041+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092581423.jpg	1932826	2025-12-07 15:30:12.612289	2025-12-07 15:30:12.612289
471	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092611451.flv	2025-12-07 15:30:41.481761+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092611451.jpg	1952288	2025-12-07 15:30:42.637165	2025-12-07 15:30:42.637165
478	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092821661.flv	2025-12-07 15:34:11.690197+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092821661.jpg	1952469	2025-12-07 15:34:12.818058	2025-12-07 15:34:12.818058
479	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092851692.flv	2025-12-07 15:34:41.720543+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092851692.jpg	1954746	2025-12-07 15:34:42.824437	2025-12-07 15:34:42.824437
483	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092971813.flv	2025-12-07 15:36:41.844921+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092971813.jpg	1956367	2025-12-07 15:36:43.003829	2025-12-07 15:36:43.003829
492	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093242085.flv	2025-12-07 15:41:12.116172+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093242085.jpg	1961175	2025-12-07 15:41:13.296844	2025-12-07 15:41:13.296844
493	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093272116.flv	2025-12-07 15:41:42.145661+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093272116.jpg	1951791	2025-12-07 15:41:43.319663	2025-12-07 15:41:43.319663
456	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092161000.flv	2025-12-07 15:23:11.026384+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092161000.jpg	1975295	2025-12-07 15:23:12.135882	2025-12-07 15:23:12.135882
458	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092221058.flv	2025-12-07 15:24:11.089118+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092221058.jpg	1940584	2025-12-07 15:24:12.226982	2025-12-07 15:24:12.226982
459	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092251089.flv	2025-12-07 15:24:41.116483+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092251089.jpg	1927207	2025-12-07 15:24:42.263204	2025-12-07 15:24:42.263204
472	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092641482.flv	2025-12-07 15:31:11.512111+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092641482.jpg	1908515	2025-12-07 15:31:12.663757	2025-12-07 15:31:12.663757
473	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092671512.flv	2025-12-07 15:31:41.54146+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765092671512.jpg	1946706	2025-12-07 15:31:42.664009	2025-12-07 15:31:42.664009
484	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093001845.flv	2025-12-07 15:37:11.872265+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093001845.jpg	1912289	2025-12-07 15:37:13.028795	2025-12-07 15:37:13.028795
486	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093061903.flv	2025-12-07 15:38:11.934951+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093061903.jpg	1908985	2025-12-07 15:38:13.075376	2025-12-07 15:38:13.075376
487	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093091935.flv	2025-12-07 15:38:41.963294+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093091935.jpg	1901150	2025-12-07 15:38:43.066563	2025-12-07 15:38:43.066563
496	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093362207.flv	2025-12-07 15:43:12.236632+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093362207.jpg	1945424	2025-12-07 15:43:13.394604	2025-12-07 15:43:13.394604
498	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093422267.flv	2025-12-07 15:44:11.813369+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093422267.jpg	1922511	2025-12-07 15:44:12.952042	2025-12-07 15:44:12.952042
499	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093451815.flv	2025-12-07 15:44:42.326262+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093451815.jpg	1897961	2025-12-07 15:44:43.497473	2025-12-07 15:44:43.497473
500	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093482328.flv	2025-12-07 15:45:12.356266+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093482328.jpg	1890917	2025-12-07 15:45:13.506359	2025-12-07 15:45:13.506359
501	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093512358.flv	2025-12-07 15:45:42.385328+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093512358.jpg	1942453	2025-12-07 15:45:43.46417	2025-12-07 15:45:43.46417
502	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093542386.flv	2025-12-07 15:46:12.415444+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093542386.jpg	1940770	2025-12-07 15:46:13.518439	2025-12-07 15:46:13.518439
503	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093565079.flv	2025-12-07 15:46:40.396804+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093565079.jpg	2034903	2025-12-07 15:46:41.501762	2025-12-07 15:46:41.501762
504	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093572416.flv	2025-12-07 15:46:42.445612+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093572416.jpg	1976175	2025-12-07 15:46:43.513122	2025-12-07 15:46:43.513122
505	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093602446.flv	2025-12-07 15:47:12.476828+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093602446.jpg	1960166	2025-12-07 15:47:13.571185	2025-12-07 15:47:13.571185
506	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093600397.flv	2025-12-07 15:47:14.800614+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093600397.jpg	2154301	2025-12-07 15:47:15.903777	2025-12-07 15:47:15.903777
507	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093632477.flv	2025-12-07 15:47:42.509089+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093632477.jpg	1935789	2025-12-07 15:47:43.60138	2025-12-07 15:47:43.60138
508	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093634802.flv	2025-12-07 15:47:48.941509+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093634802.jpg	1886023	2025-12-07 15:47:50.094438	2025-12-07 15:47:50.094438
509	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093662509.flv	2025-12-07 15:48:12.539394+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093662509.jpg	1939964	2025-12-07 15:48:13.653102	2025-12-07 15:48:13.653102
510	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093668943.flv	2025-12-07 15:48:23.604411+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093668943.jpg	2201834	2025-12-07 15:48:24.685357	2025-12-07 15:48:24.685357
511	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093692540.flv	2025-12-07 15:48:42.56774+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093692540.jpg	1915897	2025-12-07 15:48:43.641458	2025-12-07 15:48:43.641458
512	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093703605.flv	2025-12-07 15:48:57.628423+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093703605.jpg	1883290	2025-12-07 15:48:58.723771	2025-12-07 15:48:58.723771
513	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093722569.flv	2025-12-07 15:49:12.598123+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093722569.jpg	1941384	2025-12-07 15:49:13.679584	2025-12-07 15:49:13.679584
515	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093752598.flv	2025-12-07 15:49:42.626543+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093752598.jpg	1910117	2025-12-07 15:49:43.704423	2025-12-07 15:49:43.704423
516	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093771972.flv	2025-12-07 15:50:06.304533+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093771972.jpg	1849590	2025-12-07 15:50:07.395967	2025-12-07 15:50:07.395967
517	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093782628.flv	2025-12-07 15:50:12.657997+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093782628.jpg	1927764	2025-12-07 15:50:13.747571	2025-12-07 15:50:13.747571
519	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093812658.flv	2025-12-07 15:50:42.686483+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093812658.jpg	1902483	2025-12-07 15:50:43.766172	2025-12-07 15:50:43.766172
528	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093962809.flv	2025-12-07 15:53:12.840333+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093962809.jpg	1947305	2025-12-07 15:53:13.963073	2025-12-07 15:53:13.963073
529	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093978495.flv	2025-12-07 15:53:35.014591+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093978495.jpg	2074538	2025-12-07 15:53:36.110605	2025-12-07 15:53:36.110605
531	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094015015.flv	2025-12-07 15:54:09.537902+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094015015.jpg	1997708	2025-12-07 15:54:10.618745	2025-12-07 15:54:10.618745
514	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093737630.flv	2025-12-07 15:49:31.971455+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093737630.jpg	2219448	2025-12-07 15:49:33.035704	2025-12-07 15:49:33.035704
518	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093806305.flv	2025-12-07 15:50:40.91363+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093806305.jpg	2162261	2025-12-07 15:50:41.97882	2025-12-07 15:50:41.97882
521	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093840914.flv	2025-12-07 15:51:14.977813+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093840914.jpg	1866789	2025-12-07 15:51:16.051814	2025-12-07 15:51:16.051814
523	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093874978.flv	2025-12-07 15:51:49.457999+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093874978.jpg	2195930	2025-12-07 15:51:50.572915	2025-12-07 15:51:50.572915
525	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093909458.flv	2025-12-07 15:52:23.869225+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093909458.jpg	1898336	2025-12-07 15:52:25.015527	2025-12-07 15:52:25.015527
527	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093943871.flv	2025-12-07 15:52:58.493467+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093943871.jpg	2119021	2025-12-07 15:52:59.613207	2025-12-07 15:52:59.613207
530	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093992841.flv	2025-12-07 15:53:42.870977+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093992841.jpg	1917736	2025-12-07 15:53:43.965719	2025-12-07 15:53:43.965719
532	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094022872.flv	2025-12-07 15:54:12.898642+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094022872.jpg	1947402	2025-12-07 15:54:14.010256	2025-12-07 15:54:14.010256
520	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093842688.flv	2025-12-07 15:51:12.717999+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093842688.jpg	1901752	2025-12-07 15:51:13.797874	2025-12-07 15:51:13.797874
522	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093872718.flv	2025-12-07 15:51:42.749544+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093872718.jpg	1936297	2025-12-07 15:51:43.924805	2025-12-07 15:51:43.924805
524	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093902751.flv	2025-12-07 15:52:12.779115+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093902751.jpg	1949779	2025-12-07 15:52:13.924217	2025-12-07 15:52:13.924217
526	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093932780.flv	2025-12-07 15:52:42.808712+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765093932780.jpg	1987523	2025-12-07 15:52:43.919452	2025-12-07 15:52:43.919452
533	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094052899.flv	2025-12-07 15:54:42.928327+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094052899.jpg	1904936	2025-12-07 15:54:44.032065	2025-12-07 15:54:44.032065
534	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094049539.flv	2025-12-07 15:54:43.850256+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094049539.jpg	2075759	2025-12-07 15:54:45.132749	2025-12-07 15:54:45.132749
535	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094082930.flv	2025-12-07 15:55:12.95903+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094082930.jpg	1967678	2025-12-07 15:55:14.030263	2025-12-07 15:55:14.030263
536	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094083851.flv	2025-12-07 15:55:18.22263+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094083851.jpg	1973644	2025-12-07 15:55:19.304901	2025-12-07 15:55:19.304901
537	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094112960.flv	2025-12-07 15:55:42.989752+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094112960.jpg	1898632	2025-12-07 15:55:44.095838	2025-12-07 15:55:44.095838
538	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094118223.flv	2025-12-07 15:55:52.759014+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094118223.jpg	2080993	2025-12-07 15:55:53.847142	2025-12-07 15:55:53.847142
539	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094142990.flv	2025-12-07 15:56:13.01949+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094142990.jpg	1895921	2025-12-07 15:56:14.10723	2025-12-07 15:56:14.10723
540	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094152759.flv	2025-12-07 15:56:26.867453+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094152759.jpg	1996494	2025-12-07 15:56:27.948703	2025-12-07 15:56:27.948703
541	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094173020.flv	2025-12-07 15:56:43.049245+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094173020.jpg	1919033	2025-12-07 15:56:44.147759	2025-12-07 15:56:44.147759
542	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094186868.flv	2025-12-07 15:57:01.276889+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094186868.jpg	2061978	2025-12-07 15:57:02.38315	2025-12-07 15:57:02.38315
543	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094203050.flv	2025-12-07 15:57:13.082014+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094203050.jpg	1905624	2025-12-07 15:57:14.235231	2025-12-07 15:57:14.235231
544	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094221277.flv	2025-12-07 15:57:35.787337+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094221277.jpg	1927470	2025-12-07 15:57:36.939288	2025-12-07 15:57:36.939288
545	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094233083.flv	2025-12-07 15:57:43.112797+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094233083.jpg	1940155	2025-12-07 15:57:44.279887	2025-12-07 15:57:44.279887
546	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094255789.flv	2025-12-07 15:58:10.725771+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094255789.jpg	2122123	2025-12-07 15:58:11.834869	2025-12-07 15:58:11.834869
547	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094263113.flv	2025-12-07 15:58:13.140594+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094263113.jpg	1980251	2025-12-07 15:58:14.219487	2025-12-07 15:58:14.219487
548	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094293141.flv	2025-12-07 15:58:43.172403+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094293141.jpg	1961253	2025-12-07 15:58:44.334026	2025-12-07 15:58:44.334026
549	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094290727.flv	2025-12-07 15:58:45.292249+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094290727.jpg	1885238	2025-12-07 15:58:46.375877	2025-12-07 15:58:46.375877
550	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094323173.flv	2025-12-07 15:59:13.202224+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094323173.jpg	1950152	2025-12-07 15:59:14.346676	2025-12-07 15:59:14.346676
551	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094325293.flv	2025-12-07 15:59:19.929738+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094325293.jpg	2150239	2025-12-07 15:59:21.001785	2025-12-07 15:59:21.001785
552	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094353203.flv	2025-12-07 15:59:43.232057+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094353203.jpg	1909000	2025-12-07 15:59:44.312887	2025-12-07 15:59:44.312887
553	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094359930.flv	2025-12-07 15:59:56.401109+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094359930.jpg	1871852	2025-12-07 15:59:57.504095	2025-12-07 15:59:57.504095
555	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094396401.flv	2025-12-07 16:00:31.13462+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094396401.jpg	2152180	2025-12-07 16:00:32.24467	2025-12-07 16:00:32.24467
560	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094473322.flv	2025-12-07 16:01:43.351485+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094473322.jpg	1913429	2025-12-07 16:01:44.432784	2025-12-07 16:01:44.432784
561	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094503352.flv	2025-12-07 16:02:13.381365+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094503352.jpg	1897076	2025-12-07 16:02:14.462162	2025-12-07 16:02:14.462162
563	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094533382.flv	2025-12-07 16:02:43.414252+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094533382.jpg	1910237	2025-12-07 16:02:44.587321	2025-12-07 16:02:44.587321
564	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094563415.flv	2025-12-07 16:03:13.445146+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094563415.jpg	1920424	2025-12-07 16:03:14.587186	2025-12-07 16:03:14.587186
569	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094713565.flv	2025-12-07 16:05:43.594715+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094713565.jpg	1925766	2025-12-07 16:05:44.727826	2025-12-07 16:05:44.727826
574	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094863635.flv	2025-12-07 16:08:13.746415+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094863635.jpg	1905327	2025-12-07 16:08:14.877722	2025-12-07 16:08:14.877722
579	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095013868.flv	2025-12-07 16:10:43.897213+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095013868.jpg	1952577	2025-12-07 16:10:45.057052	2025-12-07 16:10:45.057052
580	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095043898.flv	2025-12-07 16:11:13.926182+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095043898.jpg	1931526	2025-12-07 16:11:15.041341	2025-12-07 16:11:15.041341
585	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095194049.flv	2025-12-07 16:13:44.080065+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095194049.jpg	1912052	2025-12-07 16:13:45.242285	2025-12-07 16:13:45.242285
590	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095344201.flv	2025-12-07 16:16:14.227999+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095344201.jpg	1965983	2025-12-07 16:16:15.338946	2025-12-07 16:16:15.338946
595	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095494349.flv	2025-12-07 16:18:44.380971+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095494349.jpg	1939969	2025-12-07 16:18:45.526027	2025-12-07 16:18:45.526027
596	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095524382.flv	2025-12-07 16:19:14.411969+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095524382.jpg	1908371	2025-12-07 16:19:15.568096	2025-12-07 16:19:15.568096
601	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095674532.flv	2025-12-07 16:21:44.559974+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095674532.jpg	1971461	2025-12-07 16:21:45.684357	2025-12-07 16:21:45.684357
606	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095824684.flv	2025-12-07 16:24:14.711+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095824684.jpg	1944089	2025-12-07 16:24:15.858097	2025-12-07 16:24:15.858097
611	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095974834.flv	2025-12-07 16:26:44.86204+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095974834.jpg	1941360	2025-12-07 16:26:46.008885	2025-12-07 16:26:46.008885
612	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096004862.flv	2025-12-07 16:27:14.895049+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096004862.jpg	1938803	2025-12-07 16:27:15.991498	2025-12-07 16:27:15.991498
617	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096155017.flv	2025-12-07 16:29:45.045103+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096155017.jpg	1913728	2025-12-07 16:29:46.176216	2025-12-07 16:29:46.176216
623	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096335195.flv	2025-12-07 16:32:45.227135+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096335195.jpg	1934675	2025-12-07 16:32:46.392713	2025-12-07 16:32:46.392713
624	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096365227.flv	2025-12-07 16:33:15.255918+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096365227.jpg	1949840	2025-12-07 16:33:16.358137	2025-12-07 16:33:16.358137
629	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096515377.flv	2025-12-07 16:35:45.40772+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096515377.jpg	1904496	2025-12-07 16:35:46.513522	2025-12-07 16:35:46.513522
635	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096695559.flv	2025-12-07 16:38:45.58827+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096695559.jpg	1940076	2025-12-07 16:38:46.763196	2025-12-07 16:38:46.763196
636	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096725589.flv	2025-12-07 16:39:15.616785+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096725589.jpg	1978144	2025-12-07 16:39:16.716037	2025-12-07 16:39:16.716037
554	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094383232.flv	2025-12-07 16:00:13.2619+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094383232.jpg	1958634	2025-12-07 16:00:14.377506	2025-12-07 16:00:14.377506
566	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094623476.flv	2025-12-07 16:04:13.504955+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094623476.jpg	1973087	2025-12-07 16:04:14.639346	2025-12-07 16:04:14.639346
571	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094773626.flv	2025-12-07 16:06:43.653582+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094773626.jpg	1947035	2025-12-07 16:06:44.771071	2025-12-07 16:06:44.771071
572	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094803654.flv	2025-12-07 16:07:13.685522+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094803654.jpg	1903000	2025-12-07 16:07:14.850489	2025-12-07 16:07:14.850489
577	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094953808.flv	2025-12-07 16:09:43.834284+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094953808.jpg	1938437	2025-12-07 16:09:44.919419	2025-12-07 16:09:44.919419
582	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095103956.flv	2025-12-07 16:12:13.989128+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095103956.jpg	1907980	2025-12-07 16:12:15.13391	2025-12-07 16:12:15.13391
587	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095254107.flv	2025-12-07 16:14:44.139033+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095254107.jpg	1904053	2025-12-07 16:14:45.26909	2025-12-07 16:14:45.26909
588	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095284139.flv	2025-12-07 16:15:14.16802+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095284139.jpg	1951091	2025-12-07 16:15:15.299112	2025-12-07 16:15:15.299112
593	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095434289.flv	2025-12-07 16:17:44.320978+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095434289.jpg	1956082	2025-12-07 16:17:45.489909	2025-12-07 16:17:45.489909
598	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095584442.flv	2025-12-07 16:20:14.468969+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095584442.jpg	1918005	2025-12-07 16:20:15.589546	2025-12-07 16:20:15.589546
603	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095734593.flv	2025-12-07 16:22:44.622982+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095734593.jpg	1948892	2025-12-07 16:22:45.790147	2025-12-07 16:22:45.790147
604	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095764623.flv	2025-12-07 16:23:14.652987+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095764623.jpg	1915431	2025-12-07 16:23:15.786475	2025-12-07 16:23:15.786475
609	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095914291.flv	2025-12-07 16:25:44.804022+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095914291.jpg	1897961	2025-12-07 16:25:45.96363	2025-12-07 16:25:45.96363
615	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096094955.flv	2025-12-07 16:28:44.98508+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096094955.jpg	1935094	2025-12-07 16:28:46.088263	2025-12-07 16:28:46.088263
616	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096124986.flv	2025-12-07 16:29:15.016091+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096124986.jpg	1938956	2025-12-07 16:29:16.164455	2025-12-07 16:29:16.164455
621	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096275136.flv	2025-12-07 16:31:45.163369+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096275136.jpg	1901510	2025-12-07 16:31:46.285042	2025-12-07 16:31:46.285042
627	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096455318.flv	2025-12-07 16:34:45.346781+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096455318.jpg	1917025	2025-12-07 16:34:46.47654	2025-12-07 16:34:46.47654
628	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096485347.flv	2025-12-07 16:35:15.376446+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096485347.jpg	1945703	2025-12-07 16:35:16.489684	2025-12-07 16:35:16.489684
633	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096635499.flv	2025-12-07 16:37:45.528703+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096635499.jpg	1917717	2025-12-07 16:37:46.69013	2025-12-07 16:37:46.69013
556	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094413263.flv	2025-12-07 16:00:43.292752+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094413263.jpg	1923180	2025-12-07 16:00:44.424474	2025-12-07 16:00:44.424474
557	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094431135.flv	2025-12-07 16:01:05.677158+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094431135.jpg	1962964	2025-12-07 16:01:06.796805	2025-12-07 16:01:06.796805
558	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094443294.flv	2025-12-07 16:01:13.321615+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094443294.jpg	1929286	2025-12-07 16:01:14.428992	2025-12-07 16:01:14.428992
559	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094465678.flv	2025-12-07 16:01:40.238706+08	1764341204704370850	大门设备	31	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094465678.jpg	2098290	2025-12-07 16:01:41.335501	2025-12-07 16:01:41.335501
562	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094500239.flv	2025-12-07 16:02:13.460953+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094500239.jpg	1938804	2025-12-07 16:02:15.57598	2025-12-07 16:02:15.57598
565	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094593445.flv	2025-12-07 16:03:43.475047+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094593445.jpg	1949492	2025-12-07 16:03:44.631831	2025-12-07 16:03:44.631831
567	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094653505.flv	2025-12-07 16:04:43.53287+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094653505.jpg	1960097	2025-12-07 16:04:44.606434	2025-12-07 16:04:44.606434
568	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094683534.flv	2025-12-07 16:05:13.56479+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094683534.jpg	1938702	2025-12-07 16:05:14.728378	2025-12-07 16:05:14.728378
570	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094743596.flv	2025-12-07 16:06:13.625646+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094743596.jpg	1926833	2025-12-07 16:06:14.741582	2025-12-07 16:06:14.741582
573	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094833686.flv	2025-12-07 16:07:43.633472+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094833686.jpg	1927893	2025-12-07 16:07:44.791064	2025-12-07 16:07:44.791064
575	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094893748.flv	2025-12-07 16:08:43.776368+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094893748.jpg	1887724	2025-12-07 16:08:44.934065	2025-12-07 16:08:44.934065
576	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094923778.flv	2025-12-07 16:09:13.806324+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094923778.jpg	1950277	2025-12-07 16:09:14.977021	2025-12-07 16:09:14.977021
578	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094983835.flv	2025-12-07 16:10:13.867247+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765094983835.jpg	1978028	2025-12-07 16:10:14.966791	2025-12-07 16:10:14.966791
581	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095073926.flv	2025-12-07 16:11:43.956154+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095073926.jpg	1948086	2025-12-07 16:11:45.074441	2025-12-07 16:11:45.074441
583	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095133989.flv	2025-12-07 16:12:44.018105+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095133989.jpg	1944714	2025-12-07 16:12:45.181554	2025-12-07 16:12:45.181554
584	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095164019.flv	2025-12-07 16:13:14.049084+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095164019.jpg	1902949	2025-12-07 16:13:15.183839	2025-12-07 16:13:15.183839
586	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095224080.flv	2025-12-07 16:14:14.107048+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095224080.jpg	1905969	2025-12-07 16:14:15.256172	2025-12-07 16:14:15.256172
589	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095314168.flv	2025-12-07 16:15:44.201009+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095314168.jpg	1953038	2025-12-07 16:15:45.335517	2025-12-07 16:15:45.335517
591	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095374228.flv	2025-12-07 16:16:44.257991+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095374228.jpg	1956225	2025-12-07 16:16:45.360448	2025-12-07 16:16:45.360448
592	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095404258.flv	2025-12-07 16:17:14.288984+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095404258.jpg	1909710	2025-12-07 16:17:15.415008	2025-12-07 16:17:15.415008
594	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095464321.flv	2025-12-07 16:18:14.348974+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095464321.jpg	1910611	2025-12-07 16:18:15.461507	2025-12-07 16:18:15.461507
597	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095554412.flv	2025-12-07 16:19:44.440968+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095554412.jpg	1900039	2025-12-07 16:19:45.576178	2025-12-07 16:19:45.576178
599	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095614469.flv	2025-12-07 16:20:44.50197+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095614469.jpg	1916166	2025-12-07 16:20:45.636654	2025-12-07 16:20:45.636654
600	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095644502.flv	2025-12-07 16:21:14.530972+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095644502.jpg	1942251	2025-12-07 16:21:15.678961	2025-12-07 16:21:15.678961
602	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095704560.flv	2025-12-07 16:22:14.592978+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095704560.jpg	1960552	2025-12-07 16:22:15.736358	2025-12-07 16:22:15.736358
607	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095854711.flv	2025-12-07 16:24:44.743007+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095854711.jpg	1920713	2025-12-07 16:24:45.869575	2025-12-07 16:24:45.869575
608	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095884743.flv	2025-12-07 16:25:14.291046+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095884743.jpg	1920126	2025-12-07 16:25:15.451226	2025-12-07 16:25:15.451226
613	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096034895.flv	2025-12-07 16:27:44.923059+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096034895.jpg	1976181	2025-12-07 16:27:46.07898	2025-12-07 16:27:46.07898
619	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096215076.flv	2025-12-07 16:30:45.104126+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096215076.jpg	1908141	2025-12-07 16:30:46.218015	2025-12-07 16:30:46.218015
620	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096245104.flv	2025-12-07 16:31:15.136138+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096245104.jpg	1927261	2025-12-07 16:31:16.265627	2025-12-07 16:31:16.265627
625	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096395257.flv	2025-12-07 16:33:45.285075+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096395257.jpg	1985391	2025-12-07 16:33:46.404139	2025-12-07 16:33:46.404139
631	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096575436.flv	2025-12-07 16:36:45.465264+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096575436.jpg	1898112	2025-12-07 16:36:46.55571	2025-12-07 16:36:46.55571
632	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096605466.flv	2025-12-07 16:37:15.498606+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096605466.jpg	1895202	2025-12-07 16:37:16.603493	2025-12-07 16:37:16.603493
605	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095794654.flv	2025-12-07 16:23:44.683993+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095794654.jpg	1929497	2025-12-07 16:23:45.825842	2025-12-07 16:23:45.825842
610	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095944804.flv	2025-12-07 16:26:14.834031+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765095944804.jpg	1889810	2025-12-07 16:26:15.940152	2025-12-07 16:26:15.940152
614	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096064924.flv	2025-12-07 16:28:14.95507+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096064924.jpg	1957641	2025-12-07 16:28:16.075496	2025-12-07 16:28:16.075496
618	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096185045.flv	2025-12-07 16:30:15.075114+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096185045.jpg	1940972	2025-12-07 16:30:16.241546	2025-12-07 16:30:16.241546
622	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096305164.flv	2025-12-07 16:32:15.194648+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096305164.jpg	1900782	2025-12-07 16:32:16.294831	2025-12-07 16:32:16.294831
626	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096425285.flv	2025-12-07 16:34:15.317675+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096425285.jpg	1946507	2025-12-07 16:34:16.428725	2025-12-07 16:34:16.428725
630	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096545409.flv	2025-12-07 16:36:15.435647+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096545409.jpg	1965631	2025-12-07 16:36:16.530454	2025-12-07 16:36:16.530454
634	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096665529.flv	2025-12-07 16:38:15.558583+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096665529.jpg	1904417	2025-12-07 16:38:16.669628	2025-12-07 16:38:16.669628
637	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096755618.flv	2025-12-07 16:39:45.647147+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096755618.jpg	1960675	2025-12-07 16:39:46.76517	2025-12-07 16:39:46.76517
638	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096785648.flv	2025-12-07 16:40:15.676374+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096785648.jpg	1949343	2025-12-07 16:40:16.76169	2025-12-07 16:40:16.76169
639	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096815678.flv	2025-12-07 16:40:45.706479+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096815678.jpg	1907635	2025-12-07 16:40:46.809583	2025-12-07 16:40:46.809583
640	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096845707.flv	2025-12-07 16:41:15.740478+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096845707.jpg	1957884	2025-12-07 16:41:16.836322	2025-12-07 16:41:16.836322
641	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096875741.flv	2025-12-07 16:41:45.76738+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096875741.jpg	1920973	2025-12-07 16:41:46.919987	2025-12-07 16:41:46.919987
642	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096905769.flv	2025-12-07 16:42:15.799198+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096905769.jpg	1927463	2025-12-07 16:42:16.925707	2025-12-07 16:42:16.925707
643	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096935800.flv	2025-12-07 16:42:45.83094+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096935800.jpg	1912880	2025-12-07 16:42:46.99857	2025-12-07 16:42:46.99857
644	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096965831.flv	2025-12-07 16:43:15.860615+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096965831.jpg	1896211	2025-12-07 16:43:16.997026	2025-12-07 16:43:16.997026
645	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096995862.flv	2025-12-07 16:43:45.889231+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765096995862.jpg	1909138	2025-12-07 16:43:47.041901	2025-12-07 16:43:47.041901
646	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765097025891.flv	2025-12-07 16:44:15.918793+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765097025891.jpg	1920345	2025-12-07 16:44:17.062798	2025-12-07 16:44:17.062798
647	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765097055919.flv	2025-12-07 16:44:45.949308+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765097055919.jpg	1946163	2025-12-07 16:44:47.072368	2025-12-07 16:44:47.072368
648	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765097085950.flv	2025-12-07 16:45:15.978781+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765097085950.jpg	1972706	2025-12-07 16:45:17.074957	2025-12-07 16:45:17.074957
649	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765097115979.flv	2025-12-07 16:45:46.008218+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765097115979.jpg	1960022	2025-12-07 16:45:47.106292	2025-12-07 16:45:47.106292
650	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765097146009.flv	2025-12-07 16:46:16.04162+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765097146009.jpg	1937366	2025-12-07 16:46:17.130267	2025-12-07 16:46:17.130267
651	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765097176043.flv	2025-12-07 16:46:46.069993+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765097176043.jpg	1925040	2025-12-07 16:46:47.145327	2025-12-07 16:46:47.145327
652	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765097206070.flv	2025-12-07 16:47:16.099341+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765097206070.jpg	1924697	2025-12-07 16:47:17.217956	2025-12-07 16:47:17.217956
653	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765097236100.flv	2025-12-07 16:47:46.131665+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765097236100.jpg	1945430	2025-12-07 16:47:47.298772	2025-12-07 16:47:47.298772
654	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765097266132.flv	2025-12-07 16:48:16.163968+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765097266132.jpg	1902933	2025-12-07 16:48:17.302051	2025-12-07 16:48:17.302051
655	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765097296164.flv	2025-12-07 16:48:46.109242+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765097296164.jpg	1927274	2025-12-07 16:48:47.265489	2025-12-07 16:48:47.265489
656	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765097326111.flv	2025-12-07 16:49:16.22268+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765097326111.jpg	1904578	2025-12-07 16:49:17.35255	2025-12-07 16:49:17.35255
661	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765097476344.flv	2025-12-07 16:51:46.374097+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765097476344.jpg	1952119	2025-12-07 16:51:47.484516	2025-12-07 16:51:47.484516
662	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765097506374.flv	2025-12-07 16:52:16.402988+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765097506374.jpg	1930446	2025-12-07 16:52:17.503607	2025-12-07 16:52:17.503607
663	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765097536403.flv	2025-12-07 16:52:46.432939+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765097536403.jpg	1947766	2025-12-07 16:52:47.530068	2025-12-07 16:52:47.530068
664	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765097566433.flv	2025-12-07 16:53:16.462946+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765097566433.jpg	1906186	2025-12-07 16:53:17.582567	2025-12-07 16:53:17.582567
657	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765097356224.flv	2025-12-07 16:49:46.252212+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765097356224.jpg	1887691	2025-12-07 16:49:47.349046	2025-12-07 16:49:47.349046
658	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765097386253.flv	2025-12-07 16:50:16.283823+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765097386253.jpg	1946778	2025-12-07 16:50:17.381196	2025-12-07 16:50:17.381196
659	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765097416285.flv	2025-12-07 16:50:46.310511+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765097416285.jpg	1938035	2025-12-07 16:50:47.41723	2025-12-07 16:50:47.41723
660	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765097446312.flv	2025-12-07 16:51:16.34327+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765097446312.jpg	1977953	2025-12-07 16:51:17.487321	2025-12-07 16:51:17.487321
665	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765097596463.flv	2025-12-07 16:53:46.495007+08	1764341204704370850	大门设备	30	/api/v1/buckets/record-space/objects/download?prefix=1764341204704370850%2F2025%2F12%2F07%2F1765097596463.jpg	1944624	2025-12-07 16:53:47.589858	2025-12-07 16:53:47.589858
\.


--
-- Data for Name: pusher; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.pusher (id, pusher_name, pusher_code, video_stream_enabled, video_stream_url, device_rtmp_mapping, video_stream_format, video_stream_quality, event_alert_enabled, event_alert_url, event_alert_method, event_alert_format, event_alert_headers, event_alert_template, description, is_enabled, status, server_ip, port, process_id, last_heartbeat, log_path, task_id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: record_space; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.record_space (id, space_name, space_code, bucket_name, save_mode, save_time, description, device_id, created_at, updated_at) FROM stdin;
1	教室102	RECORD_E34D7323	record-space	0	0	设备 1764341221624781420 的自动创建监控录像空间	1764341221624781420	2025-11-28 15:32:55.421852	2025-11-28 15:32:55.421855
2	教室101	RECORD_A718FED6	record-space	0	0	设备 1764341213886942524 的自动创建监控录像空间	1764341213886942524	2025-11-28 15:32:55.434034	2025-11-28 15:32:55.434035
4	食堂设备	RECORD_D442AA20	record-space	0	0	设备 1764340342947424339 的自动创建监控录像空间	1764340342947424339	2025-11-28 15:32:55.45335	2025-11-28 15:52:34.23884
3	大门设备	RECORD_9977C98A	record-space	0	0	设备 1764341204704370850 的自动创建监控录像空间	1764341204704370850	2025-11-28 15:32:55.443836	2025-11-28 15:52:41.821362
\.


--
-- Data for Name: region_model_service; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.region_model_service (id, region_id, service_name, service_url, service_type, model_id, threshold, request_method, request_headers, request_body_template, timeout, is_enabled, sort_order, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: snap_space; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.snap_space (id, space_name, space_code, bucket_name, save_mode, save_time, description, device_id, created_at, updated_at) FROM stdin;
3	教室101	SPACE_780FFEA5	snap-space	0	0	设备 1764341213886942524 的自动创建抓拍空间	1764341213886942524	2025-11-28 14:46:53.899214	2025-11-28 14:46:53.899215
4	教室102	SPACE_058CA8B6	snap-space	0	0	设备 1764341221624781420 的自动创建抓拍空间	1764341221624781420	2025-11-28 14:47:01.644924	2025-11-28 14:47:01.644926
1	食堂设备	SPACE_E593A3AE	snap-space	0	0	设备 1764340342947424339 的自动创建抓拍空间	1764340342947424339	2025-11-28 14:32:22.972691	2025-11-28 15:52:34.234758
2	大门设备	SPACE_E8384A8F	snap-space	0	0	设备 1764341204704370850 的自动创建抓拍空间	1764341204704370850	2025-11-28 14:46:44.72674	2025-11-28 15:52:41.809909
\.


--
-- Data for Name: snap_task; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.snap_task (id, task_name, task_code, space_id, device_id, pusher_id, capture_type, cron_expression, frame_skip, algorithm_enabled, algorithm_type, algorithm_model_id, algorithm_threshold, algorithm_night_mode, alarm_enabled, alarm_type, phone_number, email, notify_users, notify_methods, alarm_suppress_time, last_notify_time, auto_filename, custom_filename_prefix, status, is_enabled, exception_reason, run_status, total_captures, last_capture_time, last_success_time, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: sorter; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.sorter (id, sorter_name, sorter_code, sorter_type, sort_order, description, is_enabled, status, server_ip, port, process_id, last_heartbeat, log_path, task_id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: tracking_target; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tracking_target (id, task_id, device_id, device_name, track_id, class_id, class_name, first_seen_time, last_seen_time, leave_time, duration, first_seen_frame, last_seen_frame, total_detections, information, created_at, updated_at) FROM stdin;
\.


--
-- Name: alert_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.alert_id_seq', 1028, true);


--
-- Name: algorithm_model_service_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.algorithm_model_service_id_seq', 1, false);


--
-- Name: algorithm_task_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.algorithm_task_id_seq', 1, true);


--
-- Name: detection_region_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.detection_region_id_seq', 1, false);


--
-- Name: device_detection_region_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.device_detection_region_id_seq', 4, true);


--
-- Name: device_directory_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.device_directory_id_seq', 7, true);


--
-- Name: device_storage_config_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.device_storage_config_id_seq', 1, false);


--
-- Name: frame_extractor_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.frame_extractor_id_seq', 1, false);


--
-- Name: image_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.image_id_seq', 14, true);


--
-- Name: nvr_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.nvr_id_seq', 1, false);


--
-- Name: playback_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.playback_id_seq', 665, true);


--
-- Name: pusher_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.pusher_id_seq', 1, false);


--
-- Name: record_space_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.record_space_id_seq', 4, true);


--
-- Name: region_model_service_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.region_model_service_id_seq', 1, false);


--
-- Name: snap_space_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.snap_space_id_seq', 4, true);


--
-- Name: snap_task_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.snap_task_id_seq', 1, false);


--
-- Name: sorter_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.sorter_id_seq', 1, false);


--
-- Name: tracking_target_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tracking_target_id_seq', 1, false);


--
-- Name: alert alert_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alert
    ADD CONSTRAINT alert_pkey PRIMARY KEY (id);


--
-- Name: algorithm_model_service algorithm_model_service_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.algorithm_model_service
    ADD CONSTRAINT algorithm_model_service_pkey PRIMARY KEY (id);


--
-- Name: algorithm_task_device algorithm_task_device_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.algorithm_task_device
    ADD CONSTRAINT algorithm_task_device_pkey PRIMARY KEY (task_id, device_id);


--
-- Name: algorithm_task algorithm_task_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.algorithm_task
    ADD CONSTRAINT algorithm_task_pkey PRIMARY KEY (id);


--
-- Name: algorithm_task algorithm_task_task_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.algorithm_task
    ADD CONSTRAINT algorithm_task_task_code_key UNIQUE (task_code);


--
-- Name: detection_region detection_region_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.detection_region
    ADD CONSTRAINT detection_region_pkey PRIMARY KEY (id);


--
-- Name: device_detection_region device_detection_region_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.device_detection_region
    ADD CONSTRAINT device_detection_region_pkey PRIMARY KEY (id);


--
-- Name: device_directory device_directory_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.device_directory
    ADD CONSTRAINT device_directory_pkey PRIMARY KEY (id);


--
-- Name: device device_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.device
    ADD CONSTRAINT device_pkey PRIMARY KEY (id);


--
-- Name: device_storage_config device_storage_config_device_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.device_storage_config
    ADD CONSTRAINT device_storage_config_device_id_key UNIQUE (device_id);


--
-- Name: device_storage_config device_storage_config_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.device_storage_config
    ADD CONSTRAINT device_storage_config_pkey PRIMARY KEY (id);


--
-- Name: frame_extractor frame_extractor_extractor_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.frame_extractor
    ADD CONSTRAINT frame_extractor_extractor_code_key UNIQUE (extractor_code);


--
-- Name: frame_extractor frame_extractor_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.frame_extractor
    ADD CONSTRAINT frame_extractor_pkey PRIMARY KEY (id);


--
-- Name: image image_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.image
    ADD CONSTRAINT image_pkey PRIMARY KEY (id);


--
-- Name: nvr nvr_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nvr
    ADD CONSTRAINT nvr_pkey PRIMARY KEY (id);


--
-- Name: playback playback_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.playback
    ADD CONSTRAINT playback_pkey PRIMARY KEY (id);


--
-- Name: pusher pusher_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pusher
    ADD CONSTRAINT pusher_pkey PRIMARY KEY (id);


--
-- Name: pusher pusher_pusher_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pusher
    ADD CONSTRAINT pusher_pusher_code_key UNIQUE (pusher_code);


--
-- Name: record_space record_space_device_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.record_space
    ADD CONSTRAINT record_space_device_id_key UNIQUE (device_id);


--
-- Name: record_space record_space_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.record_space
    ADD CONSTRAINT record_space_pkey PRIMARY KEY (id);


--
-- Name: record_space record_space_space_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.record_space
    ADD CONSTRAINT record_space_space_code_key UNIQUE (space_code);


--
-- Name: region_model_service region_model_service_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.region_model_service
    ADD CONSTRAINT region_model_service_pkey PRIMARY KEY (id);


--
-- Name: snap_space snap_space_device_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.snap_space
    ADD CONSTRAINT snap_space_device_id_key UNIQUE (device_id);


--
-- Name: snap_space snap_space_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.snap_space
    ADD CONSTRAINT snap_space_pkey PRIMARY KEY (id);


--
-- Name: snap_space snap_space_space_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.snap_space
    ADD CONSTRAINT snap_space_space_code_key UNIQUE (space_code);


--
-- Name: snap_task snap_task_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.snap_task
    ADD CONSTRAINT snap_task_pkey PRIMARY KEY (id);


--
-- Name: snap_task snap_task_task_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.snap_task
    ADD CONSTRAINT snap_task_task_code_key UNIQUE (task_code);


--
-- Name: sorter sorter_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sorter
    ADD CONSTRAINT sorter_pkey PRIMARY KEY (id);


--
-- Name: sorter sorter_sorter_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sorter
    ADD CONSTRAINT sorter_sorter_code_key UNIQUE (sorter_code);


--
-- Name: tracking_target tracking_target_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tracking_target
    ADD CONSTRAINT tracking_target_pkey PRIMARY KEY (id);


--
-- Name: algorithm_task_device algorithm_task_device_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.algorithm_task_device
    ADD CONSTRAINT algorithm_task_device_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.device(id) ON DELETE CASCADE;


--
-- Name: algorithm_task_device algorithm_task_device_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.algorithm_task_device
    ADD CONSTRAINT algorithm_task_device_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.algorithm_task(id) ON DELETE CASCADE;


--
-- Name: algorithm_task algorithm_task_space_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.algorithm_task
    ADD CONSTRAINT algorithm_task_space_id_fkey FOREIGN KEY (space_id) REFERENCES public.snap_space(id) ON DELETE CASCADE;


--
-- Name: detection_region detection_region_image_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.detection_region
    ADD CONSTRAINT detection_region_image_id_fkey FOREIGN KEY (image_id) REFERENCES public.image(id) ON DELETE SET NULL;


--
-- Name: device_detection_region device_detection_region_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.device_detection_region
    ADD CONSTRAINT device_detection_region_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.device(id) ON DELETE CASCADE;


--
-- Name: device_detection_region device_detection_region_image_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.device_detection_region
    ADD CONSTRAINT device_detection_region_image_id_fkey FOREIGN KEY (image_id) REFERENCES public.image(id) ON DELETE SET NULL;


--
-- Name: device device_directory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.device
    ADD CONSTRAINT device_directory_id_fkey FOREIGN KEY (directory_id) REFERENCES public.device_directory(id) ON DELETE SET NULL;


--
-- Name: device_directory device_directory_parent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.device_directory
    ADD CONSTRAINT device_directory_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.device_directory(id) ON DELETE CASCADE;


--
-- Name: device device_nvr_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.device
    ADD CONSTRAINT device_nvr_id_fkey FOREIGN KEY (nvr_id) REFERENCES public.nvr(id) ON DELETE CASCADE;


--
-- Name: device_storage_config device_storage_config_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.device_storage_config
    ADD CONSTRAINT device_storage_config_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.device(id) ON DELETE CASCADE;


--
-- Name: image image_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.image
    ADD CONSTRAINT image_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.device(id);


--
-- Name: record_space record_space_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.record_space
    ADD CONSTRAINT record_space_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.device(id) ON DELETE SET NULL;


--
-- Name: region_model_service region_model_service_region_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.region_model_service
    ADD CONSTRAINT region_model_service_region_id_fkey FOREIGN KEY (region_id) REFERENCES public.detection_region(id) ON DELETE CASCADE;


--
-- Name: snap_space snap_space_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.snap_space
    ADD CONSTRAINT snap_space_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.device(id) ON DELETE SET NULL;


--
-- Name: snap_task snap_task_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.snap_task
    ADD CONSTRAINT snap_task_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.device(id) ON DELETE CASCADE;


--
-- Name: snap_task snap_task_pusher_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.snap_task
    ADD CONSTRAINT snap_task_pusher_id_fkey FOREIGN KEY (pusher_id) REFERENCES public.pusher(id) ON DELETE SET NULL;


--
-- Name: snap_task snap_task_space_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.snap_task
    ADD CONSTRAINT snap_task_space_id_fkey FOREIGN KEY (space_id) REFERENCES public.snap_space(id) ON DELETE CASCADE;


--
-- Name: tracking_target tracking_target_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tracking_target
    ADD CONSTRAINT tracking_target_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.algorithm_task(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict r9sy6otTd8HloIJRblk3DYPxonvDA9tbNNE9kCTxk6hSstzNahgEQiflUMSrqp2

