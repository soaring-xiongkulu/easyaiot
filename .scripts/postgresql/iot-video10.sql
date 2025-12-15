--
-- PostgreSQL database dump
--

\restrict 514UTGdllHDJRrPq5M7gcBVdjchVy357G3BLPSdpoKXI4sxJcglUiGeeTGaouZi

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


\unrestrict 514UTGdllHDJRrPq5M7gcBVdjchVy357G3BLPSdpoKXI4sxJcglUiGeeTGaouZi
\encoding SQL_ASCII
\connect -reuse-previous=on "dbname='iot-video20'"
\restrict 514UTGdllHDJRrPq5M7gcBVdjchVy357G3BLPSdpoKXI4sxJcglUiGeeTGaouZi

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
    record_path character varying(200),
    task_type character varying(20),
    notify_users text,
    channels text,
    notification_sent boolean NOT NULL,
    notification_sent_time timestamp without time zone
);


--
-- Name: COLUMN alert.task_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.alert.task_type IS '告警事件类型[realtime:实时算法任务,snap:抓拍算法任务]';


--
-- Name: COLUMN alert.notify_users; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.alert.notify_users IS '通知人列表（JSON格式，格式：[{"phone": "xxx", "email": "xxx", "name": "xxx"}, ...]）';


--
-- Name: COLUMN alert.channels; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.alert.channels IS '通知渠道配置（JSON格式，格式：[{"method": "sms", "template_id": "xxx"}, ...]）';


--
-- Name: COLUMN alert.notification_sent; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.alert.notification_sent IS '是否已发送通知';


--
-- Name: COLUMN alert.notification_sent_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.alert.notification_sent_time IS '通知发送时间';


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

COMMENT ON COLUMN public.algorithm_model_service.task_id IS '所属算法任务ID';


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
    llm_enabled boolean NOT NULL,
    llm_model_id integer,
    llm_frame_interval integer NOT NULL,
    regulation_rule_ids text,
    regulation_rules_content text,
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
-- Name: COLUMN algorithm_task.llm_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.llm_enabled IS '是否启用大模型实时分析';


--
-- Name: COLUMN algorithm_task.llm_model_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.llm_model_id IS '关联的大模型ID';


--
-- Name: COLUMN algorithm_task.llm_frame_interval; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.llm_frame_interval IS '大模型分析频率（每N帧分析一次，如25抽1帧）';


--
-- Name: COLUMN algorithm_task.regulation_rule_ids; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.regulation_rule_ids IS '关联的监管规则ID列表（JSON格式，如[1,2,3]）';


--
-- Name: COLUMN algorithm_task.regulation_rules_content; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.regulation_rules_content IS '监管规则内容（从监管规则详情列表获取，用分号拼接，用于大模型分析）';


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

COMMENT ON COLUMN public.detection_region.task_id IS '所属任务ID（关联到algorithm_task或snap_task）';


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
    auto_snap_enabled boolean NOT NULL,
    directory_id integer,
    cover_image_path character varying(500),
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: COLUMN device.auto_snap_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.auto_snap_enabled IS '是否开启自动抓拍[默认不开启]';


--
-- Name: COLUMN device.directory_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.directory_id IS '所属目录ID';


--
-- Name: COLUMN device.cover_image_path; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.cover_image_path IS '摄像头封面展示图路径';


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
    model_ids text,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
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
-- Name: COLUMN device_detection_region.model_ids; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_detection_region.model_ids IS '关联的算法模型ID列表（JSON格式，如[1,2,3]）';


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
-- Name: llm_config; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.llm_config (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    service_type character varying(20) NOT NULL,
    vendor character varying(50) NOT NULL,
    model_type character varying(50) NOT NULL,
    model_name character varying(100) NOT NULL,
    base_url character varying(500) NOT NULL,
    api_key character varying(200),
    api_version character varying(50),
    temperature double precision NOT NULL,
    max_tokens integer NOT NULL,
    timeout integer NOT NULL,
    is_active boolean NOT NULL,
    status character varying(20) NOT NULL,
    last_test_time timestamp without time zone,
    last_test_result text,
    description text,
    icon_url character varying(500),
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: COLUMN llm_config.name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.llm_config.name IS '模型名称';


--
-- Name: COLUMN llm_config.service_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.llm_config.service_type IS '服务类型[online:线上服务,local:本地服务]';


--
-- Name: COLUMN llm_config.vendor; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.llm_config.vendor IS '供应商[aliyun:阿里云,openai:OpenAI,anthropic:Anthropic,local:本地服务]';


--
-- Name: COLUMN llm_config.model_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.llm_config.model_type IS '模型类型[text:文本,vision:视觉,multimodal:多模态]';


--
-- Name: COLUMN llm_config.model_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.llm_config.model_name IS '模型标识（如qwen-vl-max）';


--
-- Name: COLUMN llm_config.base_url; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.llm_config.base_url IS 'API基础URL';


--
-- Name: COLUMN llm_config.api_key; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.llm_config.api_key IS 'API密钥（线上服务必填，本地服务可选）';


--
-- Name: COLUMN llm_config.api_version; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.llm_config.api_version IS 'API版本';


--
-- Name: COLUMN llm_config.temperature; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.llm_config.temperature IS '温度参数';


--
-- Name: COLUMN llm_config.max_tokens; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.llm_config.max_tokens IS '最大输出token数';


--
-- Name: COLUMN llm_config.timeout; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.llm_config.timeout IS '请求超时时间（秒）';


--
-- Name: COLUMN llm_config.is_active; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.llm_config.is_active IS '是否激活';


--
-- Name: COLUMN llm_config.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.llm_config.status IS '状态[active:激活,inactive:未激活,error:错误]';


--
-- Name: COLUMN llm_config.last_test_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.llm_config.last_test_time IS '最后测试时间';


--
-- Name: COLUMN llm_config.last_test_result; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.llm_config.last_test_result IS '最后测试结果';


--
-- Name: COLUMN llm_config.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.llm_config.description IS '模型描述';


--
-- Name: COLUMN llm_config.icon_url; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.llm_config.icon_url IS '图标URL';


--
-- Name: llm_config_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.llm_config_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: llm_config_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.llm_config_id_seq OWNED BY public.llm_config.id;


--
-- Name: llm_inference_record; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.llm_inference_record (
    id integer NOT NULL,
    record_name character varying(255),
    llm_model_id integer,
    input_type character varying(20) NOT NULL,
    input_intent text,
    input_image_path character varying(500),
    input_video_path character varying(500),
    output_text text,
    output_json text,
    output_image_path character varying(500),
    output_video_path character varying(500),
    status character varying(20) NOT NULL,
    error_message text,
    inference_time double precision,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: COLUMN llm_inference_record.record_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.llm_inference_record.record_name IS '记录名称（可选，用于标识推理任务）';


--
-- Name: COLUMN llm_inference_record.llm_model_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.llm_inference_record.llm_model_id IS '使用的大模型ID';


--
-- Name: COLUMN llm_inference_record.input_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.llm_inference_record.input_type IS '输入类型[image:图片,video:视频]';


--
-- Name: COLUMN llm_inference_record.input_intent; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.llm_inference_record.input_intent IS '监管意图（自然语言描述）';


--
-- Name: COLUMN llm_inference_record.input_image_path; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.llm_inference_record.input_image_path IS '输入图片路径（存储在MinIO）';


--
-- Name: COLUMN llm_inference_record.input_video_path; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.llm_inference_record.input_video_path IS '输入视频路径（存储在MinIO）';


--
-- Name: COLUMN llm_inference_record.output_text; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.llm_inference_record.output_text IS '推理结果文本';


--
-- Name: COLUMN llm_inference_record.output_json; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.llm_inference_record.output_json IS '推理结果JSON（规则描述等）';


--
-- Name: COLUMN llm_inference_record.output_image_path; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.llm_inference_record.output_image_path IS '输出图片路径（如果有）';


--
-- Name: COLUMN llm_inference_record.output_video_path; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.llm_inference_record.output_video_path IS '输出视频路径（如果有）';


--
-- Name: COLUMN llm_inference_record.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.llm_inference_record.status IS '状态[completed:已完成,failed:失败,processing:处理中]';


--
-- Name: COLUMN llm_inference_record.error_message; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.llm_inference_record.error_message IS '错误信息（如果失败）';


--
-- Name: COLUMN llm_inference_record.inference_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.llm_inference_record.inference_time IS '推理耗时（秒）';


--
-- Name: llm_inference_record_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.llm_inference_record_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: llm_inference_record_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.llm_inference_record_id_seq OWNED BY public.llm_inference_record.id;


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
    created_at timestamp with time zone,
    updated_at timestamp with time zone
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
-- Name: regulation_rule; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.regulation_rule (
    id integer NOT NULL,
    rule_name character varying(255) NOT NULL,
    rule_code character varying(255) NOT NULL,
    scene_type character varying(100) NOT NULL,
    rule_type character varying(50) NOT NULL,
    rule_description text,
    severity character varying(20) NOT NULL,
    is_enabled boolean NOT NULL,
    sort_order integer NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: COLUMN regulation_rule.rule_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.regulation_rule.rule_name IS '规则名称';


--
-- Name: COLUMN regulation_rule.rule_code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.regulation_rule.rule_code IS '规则编号（唯一标识）';


--
-- Name: COLUMN regulation_rule.scene_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.regulation_rule.scene_type IS '场景类型[detention_center:看守所,prison:监狱,detention_house:拘留所,interrogation_room:审讯室,security_center:安防监控中心等]';


--
-- Name: COLUMN regulation_rule.rule_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.regulation_rule.rule_type IS '规则类型[safety:安全规则,compliance:合规规则,quality:质量规则,behavior:行为规则]';


--
-- Name: COLUMN regulation_rule.rule_description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.regulation_rule.rule_description IS '规则描述';


--
-- Name: COLUMN regulation_rule.severity; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.regulation_rule.severity IS '严重程度[low:低,medium:中,high:高,critical:严重]';


--
-- Name: COLUMN regulation_rule.is_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.regulation_rule.is_enabled IS '是否启用';


--
-- Name: COLUMN regulation_rule.sort_order; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.regulation_rule.sort_order IS '排序顺序';


--
-- Name: regulation_rule_detail; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.regulation_rule_detail (
    id integer NOT NULL,
    regulation_rule_id integer NOT NULL,
    rule_name character varying(255) NOT NULL,
    rule_description text,
    priority integer NOT NULL,
    trigger_conditions text,
    is_enabled boolean NOT NULL,
    sort_order integer NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: COLUMN regulation_rule_detail.regulation_rule_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.regulation_rule_detail.regulation_rule_id IS '所属监管规则ID';


--
-- Name: COLUMN regulation_rule_detail.rule_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.regulation_rule_detail.rule_name IS '规则名称';


--
-- Name: COLUMN regulation_rule_detail.rule_description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.regulation_rule_detail.rule_description IS '规则描述';


--
-- Name: COLUMN regulation_rule_detail.priority; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.regulation_rule_detail.priority IS '优先级（数字越大优先级越高）';


--
-- Name: COLUMN regulation_rule_detail.trigger_conditions; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.regulation_rule_detail.trigger_conditions IS '触发条件（JSON格式，描述何时应用此规则）';


--
-- Name: COLUMN regulation_rule_detail.is_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.regulation_rule_detail.is_enabled IS '是否启用';


--
-- Name: COLUMN regulation_rule_detail.sort_order; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.regulation_rule_detail.sort_order IS '排序顺序';


--
-- Name: regulation_rule_detail_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.regulation_rule_detail_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: regulation_rule_detail_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.regulation_rule_detail_id_seq OWNED BY public.regulation_rule_detail.id;


--
-- Name: regulation_rule_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.regulation_rule_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: regulation_rule_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.regulation_rule_id_seq OWNED BY public.regulation_rule.id;


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
-- Name: stream_forward_task; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.stream_forward_task (
    id integer NOT NULL,
    task_name character varying(255) NOT NULL,
    task_code character varying(255) NOT NULL,
    output_format character varying(50) NOT NULL,
    output_quality character varying(50) NOT NULL,
    output_bitrate character varying(50),
    status smallint NOT NULL,
    is_enabled boolean NOT NULL,
    exception_reason character varying(500),
    service_server_ip character varying(45),
    service_port integer,
    service_process_id integer,
    service_last_heartbeat timestamp without time zone,
    service_log_path character varying(500),
    total_streams integer NOT NULL,
    last_process_time timestamp without time zone,
    last_success_time timestamp without time zone,
    description character varying(500),
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: COLUMN stream_forward_task.task_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.stream_forward_task.task_name IS '任务名称';


--
-- Name: COLUMN stream_forward_task.task_code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.stream_forward_task.task_code IS '任务编号（唯一标识）';


--
-- Name: COLUMN stream_forward_task.output_format; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.stream_forward_task.output_format IS '输出格式[rtmp:RTMP,rtsp:RTSP]';


--
-- Name: COLUMN stream_forward_task.output_quality; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.stream_forward_task.output_quality IS '输出质量[low:低,medium:中,high:高]';


--
-- Name: COLUMN stream_forward_task.output_bitrate; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.stream_forward_task.output_bitrate IS '输出码率（如512k,1M等，为空则使用默认值）';


--
-- Name: COLUMN stream_forward_task.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.stream_forward_task.status IS '状态[0:正常,1:异常]';


--
-- Name: COLUMN stream_forward_task.is_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.stream_forward_task.is_enabled IS '是否启用[0:停用,1:启用]';


--
-- Name: COLUMN stream_forward_task.exception_reason; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.stream_forward_task.exception_reason IS '异常原因';


--
-- Name: COLUMN stream_forward_task.service_server_ip; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.stream_forward_task.service_server_ip IS '服务运行服务器IP';


--
-- Name: COLUMN stream_forward_task.service_port; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.stream_forward_task.service_port IS '服务端口';


--
-- Name: COLUMN stream_forward_task.service_process_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.stream_forward_task.service_process_id IS '服务进程ID';


--
-- Name: COLUMN stream_forward_task.service_last_heartbeat; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.stream_forward_task.service_last_heartbeat IS '服务最后心跳时间';


--
-- Name: COLUMN stream_forward_task.service_log_path; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.stream_forward_task.service_log_path IS '服务日志路径';


--
-- Name: COLUMN stream_forward_task.total_streams; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.stream_forward_task.total_streams IS '总推流数';


--
-- Name: COLUMN stream_forward_task.last_process_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.stream_forward_task.last_process_time IS '最后处理时间';


--
-- Name: COLUMN stream_forward_task.last_success_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.stream_forward_task.last_success_time IS '最后成功时间';


--
-- Name: COLUMN stream_forward_task.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.stream_forward_task.description IS '任务描述';


--
-- Name: stream_forward_task_device; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.stream_forward_task_device (
    stream_forward_task_id integer NOT NULL,
    device_id character varying(100) NOT NULL,
    created_at timestamp without time zone
);


--
-- Name: COLUMN stream_forward_task_device.stream_forward_task_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.stream_forward_task_device.stream_forward_task_id IS '推流转发任务ID';


--
-- Name: COLUMN stream_forward_task_device.device_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.stream_forward_task_device.device_id IS '摄像头ID';


--
-- Name: COLUMN stream_forward_task_device.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.stream_forward_task_device.created_at IS '创建时间';


--
-- Name: stream_forward_task_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.stream_forward_task_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: stream_forward_task_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.stream_forward_task_id_seq OWNED BY public.stream_forward_task.id;


--
-- Name: streaming_session; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.streaming_session (
    id character varying(100) NOT NULL,
    llm_model_id integer,
    llm_model_name character varying(100),
    prompt text,
    video_config text,
    status character varying(20) NOT NULL,
    websocket_status character varying(20) NOT NULL,
    processed_frames integer NOT NULL,
    duration_seconds double precision NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    started_at timestamp without time zone,
    stopped_at timestamp without time zone
);


--
-- Name: COLUMN streaming_session.id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.streaming_session.id IS '会话ID（UUID）';


--
-- Name: COLUMN streaming_session.llm_model_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.streaming_session.llm_model_id IS '使用的大模型ID';


--
-- Name: COLUMN streaming_session.llm_model_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.streaming_session.llm_model_name IS '大模型名称';


--
-- Name: COLUMN streaming_session.prompt; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.streaming_session.prompt IS '提示词';


--
-- Name: COLUMN streaming_session.video_config; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.streaming_session.video_config IS '视频配置（JSON格式）';


--
-- Name: COLUMN streaming_session.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.streaming_session.status IS '状态[active:活跃,stopped:已停止,error:错误]';


--
-- Name: COLUMN streaming_session.websocket_status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.streaming_session.websocket_status IS 'WebSocket连接状态[connected:已连接,disconnected:未连接]';


--
-- Name: COLUMN streaming_session.processed_frames; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.streaming_session.processed_frames IS '已处理帧数';


--
-- Name: COLUMN streaming_session.duration_seconds; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.streaming_session.duration_seconds IS '持续时间（秒）';


--
-- Name: COLUMN streaming_session.started_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.streaming_session.started_at IS '开始时间';


--
-- Name: COLUMN streaming_session.stopped_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.streaming_session.stopped_at IS '停止时间';


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
-- Name: llm_config id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_config ALTER COLUMN id SET DEFAULT nextval('public.llm_config_id_seq'::regclass);


--
-- Name: llm_inference_record id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_inference_record ALTER COLUMN id SET DEFAULT nextval('public.llm_inference_record_id_seq'::regclass);


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
-- Name: regulation_rule id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.regulation_rule ALTER COLUMN id SET DEFAULT nextval('public.regulation_rule_id_seq'::regclass);


--
-- Name: regulation_rule_detail id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.regulation_rule_detail ALTER COLUMN id SET DEFAULT nextval('public.regulation_rule_detail_id_seq'::regclass);


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
-- Name: stream_forward_task id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.stream_forward_task ALTER COLUMN id SET DEFAULT nextval('public.stream_forward_task_id_seq'::regclass);


--
-- Name: tracking_target id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tracking_target ALTER COLUMN id SET DEFAULT nextval('public.tracking_target_id_seq'::regclass);


--
-- Data for Name: alert; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.alert (id, object, event, region, information, "time", device_id, device_name, image_path, record_path, task_type, notify_users, channels, notification_sent, notification_sent_time) FROM stdin;
\.


--
-- Data for Name: algorithm_model_service; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.algorithm_model_service (id, task_id, service_name, service_url, service_type, model_id, threshold, request_method, request_headers, request_body_template, timeout, is_enabled, sort_order, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: algorithm_task; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.algorithm_task (id, task_name, task_code, task_type, model_ids, model_names, extract_interval, rtmp_input_url, rtmp_output_url, tracking_enabled, tracking_similarity_threshold, tracking_max_age, tracking_smooth_alpha, alert_event_enabled, alert_notification_enabled, alert_notification_config, alarm_suppress_time, last_notify_time, space_id, cron_expression, frame_skip, llm_enabled, llm_model_id, llm_frame_interval, regulation_rule_ids, regulation_rules_content, status, is_enabled, run_status, exception_reason, service_server_ip, service_port, service_process_id, service_last_heartbeat, service_log_path, total_frames, total_detections, total_captures, last_process_time, last_success_time, last_capture_time, description, defense_mode, defense_schedule, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: algorithm_task_device; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.algorithm_task_device (task_id, device_id, created_at) FROM stdin;
\.


--
-- Data for Name: detection_region; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.detection_region (id, task_id, region_name, region_type, points, image_id, algorithm_type, algorithm_model_id, algorithm_threshold, algorithm_enabled, color, opacity, is_enabled, sort_order, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: device; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.device (id, name, source, rtmp_stream, http_stream, stream, ip, port, username, password, mac, manufacturer, model, firmware_version, serial_number, hardware_id, support_move, support_zoom, nvr_id, nvr_channel, enable_forward, auto_snap_enabled, directory_id, cover_image_path, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: device_detection_region; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.device_detection_region (id, device_id, region_name, region_type, points, image_id, color, opacity, is_enabled, sort_order, model_ids, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: device_directory; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.device_directory (id, name, parent_id, description, sort_order, created_at, updated_at) FROM stdin;
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
\.


--
-- Data for Name: llm_config; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.llm_config (id, name, service_type, vendor, model_type, model_name, base_url, api_key, api_version, temperature, max_tokens, timeout, is_active, status, last_test_time, last_test_result, description, icon_url, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: llm_inference_record; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.llm_inference_record (id, record_name, llm_model_id, input_type, input_intent, input_image_path, input_video_path, output_text, output_json, output_image_path, output_video_path, status, error_message, inference_time, created_at, updated_at) FROM stdin;
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
\.


--
-- Data for Name: region_model_service; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.region_model_service (id, region_id, service_name, service_url, service_type, model_id, threshold, request_method, request_headers, request_body_template, timeout, is_enabled, sort_order, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: regulation_rule; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.regulation_rule (id, rule_name, rule_code, scene_type, rule_type, rule_description, severity, is_enabled, sort_order, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: regulation_rule_detail; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.regulation_rule_detail (id, regulation_rule_id, rule_name, rule_description, priority, trigger_conditions, is_enabled, sort_order, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: snap_space; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.snap_space (id, space_name, space_code, bucket_name, save_mode, save_time, description, device_id, created_at, updated_at) FROM stdin;
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
-- Data for Name: stream_forward_task; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.stream_forward_task (id, task_name, task_code, output_format, output_quality, output_bitrate, status, is_enabled, exception_reason, service_server_ip, service_port, service_process_id, service_last_heartbeat, service_log_path, total_streams, last_process_time, last_success_time, description, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: stream_forward_task_device; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.stream_forward_task_device (stream_forward_task_id, device_id, created_at) FROM stdin;
\.


--
-- Data for Name: streaming_session; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.streaming_session (id, llm_model_id, llm_model_name, prompt, video_config, status, websocket_status, processed_frames, duration_seconds, created_at, updated_at, started_at, stopped_at) FROM stdin;
\.


--
-- Data for Name: tracking_target; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tracking_target (id, task_id, device_id, device_name, track_id, class_id, class_name, first_seen_time, last_seen_time, leave_time, duration, first_seen_frame, last_seen_frame, total_detections, information, created_at, updated_at) FROM stdin;
\.


--
-- Name: alert_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.alert_id_seq', 1, false);


--
-- Name: algorithm_model_service_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.algorithm_model_service_id_seq', 1, false);


--
-- Name: algorithm_task_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.algorithm_task_id_seq', 1, false);


--
-- Name: detection_region_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.detection_region_id_seq', 1, false);


--
-- Name: device_detection_region_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.device_detection_region_id_seq', 1, false);


--
-- Name: device_directory_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.device_directory_id_seq', 1, false);


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

SELECT pg_catalog.setval('public.image_id_seq', 1, false);


--
-- Name: llm_config_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.llm_config_id_seq', 1, false);


--
-- Name: llm_inference_record_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.llm_inference_record_id_seq', 1, false);


--
-- Name: nvr_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.nvr_id_seq', 1, false);


--
-- Name: playback_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.playback_id_seq', 1, false);


--
-- Name: pusher_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.pusher_id_seq', 1, false);


--
-- Name: record_space_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.record_space_id_seq', 1, false);


--
-- Name: region_model_service_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.region_model_service_id_seq', 1, false);


--
-- Name: regulation_rule_detail_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.regulation_rule_detail_id_seq', 1, false);


--
-- Name: regulation_rule_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.regulation_rule_id_seq', 1, false);


--
-- Name: snap_space_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.snap_space_id_seq', 1, false);


--
-- Name: snap_task_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.snap_task_id_seq', 1, false);


--
-- Name: sorter_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.sorter_id_seq', 1, false);


--
-- Name: stream_forward_task_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.stream_forward_task_id_seq', 1, false);


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
-- Name: llm_config llm_config_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_config
    ADD CONSTRAINT llm_config_name_key UNIQUE (name);


--
-- Name: llm_config llm_config_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_config
    ADD CONSTRAINT llm_config_pkey PRIMARY KEY (id);


--
-- Name: llm_inference_record llm_inference_record_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_inference_record
    ADD CONSTRAINT llm_inference_record_pkey PRIMARY KEY (id);


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
-- Name: regulation_rule_detail regulation_rule_detail_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.regulation_rule_detail
    ADD CONSTRAINT regulation_rule_detail_pkey PRIMARY KEY (id);


--
-- Name: regulation_rule regulation_rule_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.regulation_rule
    ADD CONSTRAINT regulation_rule_pkey PRIMARY KEY (id);


--
-- Name: regulation_rule regulation_rule_rule_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.regulation_rule
    ADD CONSTRAINT regulation_rule_rule_code_key UNIQUE (rule_code);


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
-- Name: stream_forward_task_device stream_forward_task_device_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.stream_forward_task_device
    ADD CONSTRAINT stream_forward_task_device_pkey PRIMARY KEY (stream_forward_task_id, device_id);


--
-- Name: stream_forward_task stream_forward_task_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.stream_forward_task
    ADD CONSTRAINT stream_forward_task_pkey PRIMARY KEY (id);


--
-- Name: stream_forward_task stream_forward_task_task_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.stream_forward_task
    ADD CONSTRAINT stream_forward_task_task_code_key UNIQUE (task_code);


--
-- Name: streaming_session streaming_session_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.streaming_session
    ADD CONSTRAINT streaming_session_pkey PRIMARY KEY (id);


--
-- Name: tracking_target tracking_target_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tracking_target
    ADD CONSTRAINT tracking_target_pkey PRIMARY KEY (id);


--
-- Name: algorithm_model_service algorithm_model_service_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.algorithm_model_service
    ADD CONSTRAINT algorithm_model_service_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.algorithm_task(id) ON DELETE CASCADE;


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
-- Name: algorithm_task algorithm_task_llm_model_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.algorithm_task
    ADD CONSTRAINT algorithm_task_llm_model_id_fkey FOREIGN KEY (llm_model_id) REFERENCES public.llm_config(id) ON DELETE SET NULL;


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
-- Name: llm_inference_record llm_inference_record_llm_model_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_inference_record
    ADD CONSTRAINT llm_inference_record_llm_model_id_fkey FOREIGN KEY (llm_model_id) REFERENCES public.llm_config(id) ON DELETE SET NULL;


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
-- Name: regulation_rule_detail regulation_rule_detail_regulation_rule_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.regulation_rule_detail
    ADD CONSTRAINT regulation_rule_detail_regulation_rule_id_fkey FOREIGN KEY (regulation_rule_id) REFERENCES public.regulation_rule(id) ON DELETE CASCADE;


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
-- Name: stream_forward_task_device stream_forward_task_device_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.stream_forward_task_device
    ADD CONSTRAINT stream_forward_task_device_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.device(id) ON DELETE CASCADE;


--
-- Name: stream_forward_task_device stream_forward_task_device_stream_forward_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.stream_forward_task_device
    ADD CONSTRAINT stream_forward_task_device_stream_forward_task_id_fkey FOREIGN KEY (stream_forward_task_id) REFERENCES public.stream_forward_task(id) ON DELETE CASCADE;


--
-- Name: streaming_session streaming_session_llm_model_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.streaming_session
    ADD CONSTRAINT streaming_session_llm_model_id_fkey FOREIGN KEY (llm_model_id) REFERENCES public.llm_config(id) ON DELETE SET NULL;


--
-- Name: tracking_target tracking_target_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tracking_target
    ADD CONSTRAINT tracking_target_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.algorithm_task(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict 514UTGdllHDJRrPq5M7gcBVdjchVy357G3BLPSdpoKXI4sxJcglUiGeeTGaouZi

