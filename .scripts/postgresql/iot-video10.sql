--
-- PostgreSQL database dump
--

\restrict E3WsAYvddKwRlIv0hj4lfff9sF4j3KqAd4QGlnoy84lOPhGD9xt7B5sbjSb2frl

-- Dumped from database version 18.4 (Debian 18.4-1.pgdg13+1)
-- Dumped by pg_dump version 18.4 (Debian 18.4-1.pgdg13+1)

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


\unrestrict E3WsAYvddKwRlIv0hj4lfff9sF4j3KqAd4QGlnoy84lOPhGD9xt7B5sbjSb2frl
\encoding SQL_ASCII
\connect -reuse-previous=on "dbname='iot-video20'"
\restrict E3WsAYvddKwRlIv0hj4lfff9sF4j3KqAd4QGlnoy84lOPhGD9xt7B5sbjSb2frl

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
    device_id character varying(100) NOT NULL,
    device_name character varying(100) NOT NULL,
    image_path character varying(500),
    image_url character varying(500),
    record_path character varying(500),
    task_type character varying(20),
    task_id integer,
    task_name character varying(255),
    notify_users text,
    channels text,
    notification_sent boolean NOT NULL,
    notification_sent_time timestamp without time zone,
    business_tags text,
    correlation_id character varying(36),
    edge_node_id bigint,
    edge_node_name character varying(128),
    edge_node_host character varying(128),
    node_id bigint,
    image_asset_id character varying(36),
    record_asset_id character varying(36)
);


--
-- Name: COLUMN alert.image_path; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.alert.image_path IS '本地图片路径（算法落盘）';


--
-- Name: COLUMN alert.image_url; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.alert.image_url IS 'MinIO 下载路径（/api/v1/buckets/.../objects/download?prefix=...）';


--
-- Name: COLUMN alert.record_path; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.alert.record_path IS '告警录像 MinIO 下载路径（/api/v1/buckets/.../objects/download?prefix=...），非宿主机 /data/playbacks 路径';


--
-- Name: COLUMN alert.task_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.alert.task_type IS '告警事件类型[realtime:实时算法任务,snap:抓拍算法任务]';


--
-- Name: COLUMN alert.task_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.alert.task_id IS '关联的任务ID';


--
-- Name: COLUMN alert.task_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.alert.task_name IS '关联的任务名称';


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
-- Name: COLUMN alert.business_tags; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.alert.business_tags IS '业务标签（JSON数组，库匹配告警携带匹配库标签）';


--
-- Name: COLUMN alert.correlation_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.alert.correlation_id IS '关联事件ID（同一帧算法告警/人脸/车牌）';


--
-- Name: COLUMN alert.edge_node_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.alert.edge_node_id IS '边缘节点 edge_node.id';


--
-- Name: COLUMN alert.edge_node_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.alert.edge_node_name IS '边缘节点名称（冗余）';


--
-- Name: COLUMN alert.edge_node_host; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.alert.edge_node_host IS '边缘节点主机（冗余）';


--
-- Name: COLUMN alert.node_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.alert.node_id IS '运行 compute_node.id（可选）';


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
-- Name: algorithm_post_process_result; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.algorithm_post_process_result (
    id integer NOT NULL,
    task_id integer NOT NULL,
    task_name character varying(255),
    task_code character varying(255),
    task_type character varying(20),
    device_id character varying(100) NOT NULL,
    device_name character varying(100),
    frame_number integer,
    event_time timestamp with time zone,
    counts text,
    events text,
    alerts text,
    payload text,
    correlation_id character varying(36),
    created_at timestamp without time zone
);


--
-- Name: COLUMN algorithm_post_process_result.task_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_post_process_result.task_id IS '算法任务ID';


--
-- Name: COLUMN algorithm_post_process_result.task_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_post_process_result.task_name IS '任务名称';


--
-- Name: COLUMN algorithm_post_process_result.task_code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_post_process_result.task_code IS '任务编号';


--
-- Name: COLUMN algorithm_post_process_result.task_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_post_process_result.task_type IS '任务类型[realtime,snap,patrol]';


--
-- Name: COLUMN algorithm_post_process_result.device_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_post_process_result.device_id IS '设备ID';


--
-- Name: COLUMN algorithm_post_process_result.device_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_post_process_result.device_name IS '设备名称';


--
-- Name: COLUMN algorithm_post_process_result.frame_number; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_post_process_result.frame_number IS '帧序号';


--
-- Name: COLUMN algorithm_post_process_result.event_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_post_process_result.event_time IS '帧事件时间';


--
-- Name: COLUMN algorithm_post_process_result.counts; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_post_process_result.counts IS '计数结果 JSON';


--
-- Name: COLUMN algorithm_post_process_result.events; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_post_process_result.events IS '业务事件 JSON';


--
-- Name: COLUMN algorithm_post_process_result.alerts; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_post_process_result.alerts IS '自定义告警 JSON';


--
-- Name: COLUMN algorithm_post_process_result.payload; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_post_process_result.payload IS '完整后处理结果 JSON';


--
-- Name: COLUMN algorithm_post_process_result.correlation_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_post_process_result.correlation_id IS '关联ID（去重/追溯）';


--
-- Name: algorithm_post_process_result_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.algorithm_post_process_result_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: algorithm_post_process_result_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.algorithm_post_process_result_id_seq OWNED BY public.algorithm_post_process_result.id;


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
    detect_conf double precision NOT NULL,
    extract_interval integer,
    rtmp_input_url character varying(500),
    rtmp_output_url character varying(500),
    tracking_enabled boolean NOT NULL,
    tracking_similarity_threshold double precision NOT NULL,
    tracking_max_age integer NOT NULL,
    tracking_smooth_alpha double precision NOT NULL,
    alert_event_enabled boolean NOT NULL,
    alert_event_suppress_time integer NOT NULL,
    alert_class_names text,
    face_detection_enabled boolean NOT NULL,
    plate_detection_enabled boolean NOT NULL,
    face_matching_enabled boolean NOT NULL,
    face_library_ids text,
    face_matching_threshold double precision,
    plate_matching_enabled boolean NOT NULL,
    plate_library_ids text,
    matching_business_tags text,
    alert_notification_enabled boolean NOT NULL,
    alert_notification_config text,
    alarm_suppress_time integer NOT NULL,
    last_notify_time timestamp without time zone,
    space_id integer,
    cron_expression character varying(255),
    frame_skip integer NOT NULL,
    patrol_mode character varying(20),
    patrol_interval_sec integer,
    patrol_pool_size integer,
    focus_device_id character varying(100),
    status smallint NOT NULL,
    is_enabled boolean NOT NULL,
    run_status character varying(20) NOT NULL,
    exception_reason character varying(500),
    schedule_policy character varying(20) NOT NULL,
    prefer_gpu boolean NOT NULL,
    target_node_id bigint,
    node_id bigint,
    service_server_ip character varying(512),
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
    sam_supplement_enabled boolean NOT NULL,
    sam_supplement_config text,
    motion_gate_enabled boolean NOT NULL,
    motion_gate_config text,
    pose_analysis_enabled boolean NOT NULL,
    pose_analysis_config text,
    pose_intent_enabled boolean NOT NULL,
    pose_library_ids text,
    pose_intent_threshold double precision,
    pose_intent_config text,
    post_process_enabled boolean NOT NULL,
    post_process_script character varying(255),
    post_process_replicas integer NOT NULL,
    defense_mode character varying(20) NOT NULL,
    defense_schedule text,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    face_library_id integer,
    plate_library_id integer,
    executor character varying(20) DEFAULT 'cpp'::character varying,
    runtime_bin_path character varying(500),
    runtime_control_port integer,
    device_deployments text,
    post_pipeline text
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

COMMENT ON COLUMN public.algorithm_task.task_type IS '任务类型[realtime,snap,patrol]';


--
-- Name: COLUMN algorithm_task.model_ids; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.model_ids IS '关联的模型ID列表（JSON格式，如[1,2,3]）';


--
-- Name: COLUMN algorithm_task.model_names; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.model_names IS '关联的模型名称列表（逗号分隔，冗余字段，用于快速显示）';


--
-- Name: COLUMN algorithm_task.detect_conf; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.detect_conf IS 'YOLO检测置信度阈值（0~1，默认0.5）';


--
-- Name: COLUMN algorithm_task.extract_interval; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.extract_interval IS 'AI检测间隔（每N帧推理一次；12≈25fps下每秒2次；NULL时沿用EXTRACT_INTERVAL，默认12）';


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
-- Name: COLUMN algorithm_task.alert_event_suppress_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.alert_event_suppress_time IS '告警事件抑制时间（秒），同一设备两次上报告警事件的最小间隔，减轻Kafka积压，默认5秒';


--
-- Name: COLUMN algorithm_task.alert_class_names; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.alert_class_names IS '告警触发类别标签（JSON数组，为空则任意检测均可触发告警）';


--
-- Name: COLUMN algorithm_task.face_detection_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.face_detection_enabled IS '是否启用人脸检测';


--
-- Name: COLUMN algorithm_task.plate_detection_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.plate_detection_enabled IS '是否启用车牌检测';


--
-- Name: COLUMN algorithm_task.face_matching_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.face_matching_enabled IS '是否启用人脸匹配（默认关闭）';


--
-- Name: COLUMN algorithm_task.face_library_ids; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.face_library_ids IS '关联人脸库ID列表（JSON数组，多库匹配）';


--
-- Name: COLUMN algorithm_task.face_matching_threshold; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.face_matching_threshold IS '人脸匹配相似度阈值（为空则使用人脸库默认值）';


--
-- Name: COLUMN algorithm_task.plate_matching_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.plate_matching_enabled IS '是否启用车牌匹配（默认关闭）';


--
-- Name: COLUMN algorithm_task.plate_library_ids; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.plate_library_ids IS '关联车牌库ID列表（JSON数组，多库匹配）';


--
-- Name: COLUMN algorithm_task.matching_business_tags; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.matching_business_tags IS '匹配业务标签（JSON数组，透传子任务/告警）';


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
-- Name: COLUMN algorithm_task.patrol_mode; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.patrol_mode IS '巡检模式[rotate,pool,hybrid]';


--
-- Name: COLUMN algorithm_task.patrol_interval_sec; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.patrol_interval_sec IS '巡检间隔（秒）';


--
-- Name: COLUMN algorithm_task.patrol_pool_size; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.patrol_pool_size IS '连接池大小';


--
-- Name: COLUMN algorithm_task.focus_device_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.focus_device_id IS '焦点设备ID（hybrid）';


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
-- Name: COLUMN algorithm_task.schedule_policy; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.schedule_policy IS '调度策略[local:本机,auto:自动节点,node:指定节点]';


--
-- Name: COLUMN algorithm_task.prefer_gpu; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.prefer_gpu IS '自动调度时是否优先 GPU 节点';


--
-- Name: COLUMN algorithm_task.target_node_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.target_node_id IS '指定部署节点ID';


--
-- Name: COLUMN algorithm_task.node_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.node_id IS '实际运行节点ID';


--
-- Name: COLUMN algorithm_task.service_server_ip; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.service_server_ip IS '服务运行服务器IP（多节点时为逗号分隔）';


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
-- Name: COLUMN algorithm_task.sam_supplement_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.sam_supplement_enabled IS '是否启用 SAM 补充识别';


--
-- Name: COLUMN algorithm_task.sam_supplement_config; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.sam_supplement_config IS 'SAM 补充配置 JSON';


--
-- Name: COLUMN algorithm_task.motion_gate_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.motion_gate_enabled IS '是否启用运动检测门控（仅实时算法任务）';


--
-- Name: COLUMN algorithm_task.motion_gate_config; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.motion_gate_config IS '运动门控配置 JSON';


--
-- Name: COLUMN algorithm_task.pose_analysis_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.pose_analysis_enabled IS '是否启用人体姿态分析';


--
-- Name: COLUMN algorithm_task.pose_analysis_config; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.pose_analysis_config IS '人体姿态分析配置 JSON';


--
-- Name: COLUMN algorithm_task.pose_intent_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.pose_intent_enabled IS '是否启用姿态意图分析告警';


--
-- Name: COLUMN algorithm_task.pose_library_ids; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.pose_library_ids IS '关联场景姿态库ID列表（JSON数组）';


--
-- Name: COLUMN algorithm_task.pose_intent_threshold; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.pose_intent_threshold IS '姿态意图匹配阈值（为空则使用库默认值）';


--
-- Name: COLUMN algorithm_task.pose_intent_config; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.pose_intent_config IS '姿态意图分析配置 JSON';


--
-- Name: COLUMN algorithm_task.post_process_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.post_process_enabled IS '是否启用 AI 后处理脚本';


--
-- Name: COLUMN algorithm_task.post_process_script; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.post_process_script IS '后处理脚本文件名，默认 post_process.py';


--
-- Name: COLUMN algorithm_task.post_process_replicas; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.post_process_replicas IS '后处理 Worker 副本数（集群水平扩展）';


--
-- Name: COLUMN algorithm_task.defense_mode; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.defense_mode IS '布防模式[full:全防模式,half:半防模式,day:白天模式,night:夜间模式]';


--
-- Name: COLUMN algorithm_task.defense_schedule; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.defense_schedule IS '布防时段配置（JSON格式，7天×24小时的二维数组）';


--
-- Name: COLUMN algorithm_task.post_pipeline; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task.post_pipeline IS 'POST 定制后处理 pipeline JSON';


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
-- Name: algorithm_task_notification_state; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.algorithm_task_notification_state (
    task_id integer NOT NULL,
    device_id character varying(100) NOT NULL,
    channel_key character varying(255) NOT NULL,
    last_notify_time timestamp without time zone,
    last_event_id character varying(36),
    updated_at timestamp without time zone
);


--
-- Name: COLUMN algorithm_task_notification_state.task_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task_notification_state.task_id IS '算法任务ID';


--
-- Name: COLUMN algorithm_task_notification_state.device_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task_notification_state.device_id IS '设备ID';


--
-- Name: COLUMN algorithm_task_notification_state.channel_key; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task_notification_state.channel_key IS '通知渠道稳定键';


--
-- Name: COLUMN algorithm_task_notification_state.last_notify_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task_notification_state.last_notify_time IS '最后通知时间';


--
-- Name: COLUMN algorithm_task_notification_state.last_event_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task_notification_state.last_event_id IS '最后通知事件ID';


--
-- Name: algorithm_task_stream_runtime; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.algorithm_task_stream_runtime (
    task_id integer NOT NULL,
    device_id character varying(100) NOT NULL,
    node_id bigint,
    stream_key character varying(255) NOT NULL,
    source_mode character varying(20) NOT NULL,
    status character varying(20) NOT NULL,
    last_frame_time timestamp with time zone,
    last_detection_time timestamp with time zone,
    last_alert_time timestamp with time zone,
    error_message character varying(500),
    updated_at timestamp without time zone
);


--
-- Name: COLUMN algorithm_task_stream_runtime.task_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task_stream_runtime.task_id IS '算法任务ID';


--
-- Name: COLUMN algorithm_task_stream_runtime.device_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task_stream_runtime.device_id IS '设备ID';


--
-- Name: COLUMN algorithm_task_stream_runtime.node_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task_stream_runtime.node_id IS '运行节点ID';


--
-- Name: COLUMN algorithm_task_stream_runtime.stream_key; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task_stream_runtime.stream_key IS '任务级 SRS stream key';


--
-- Name: COLUMN algorithm_task_stream_runtime.source_mode; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task_stream_runtime.source_mode IS '实际源流模式';


--
-- Name: COLUMN algorithm_task_stream_runtime.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task_stream_runtime.status IS '任务设备运行状态';


--
-- Name: COLUMN algorithm_task_stream_runtime.last_frame_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task_stream_runtime.last_frame_time IS '最后读取帧时间';


--
-- Name: COLUMN algorithm_task_stream_runtime.last_detection_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task_stream_runtime.last_detection_time IS '最后推理时间';


--
-- Name: COLUMN algorithm_task_stream_runtime.last_alert_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task_stream_runtime.last_alert_time IS '最后告警时间';


--
-- Name: COLUMN algorithm_task_stream_runtime.error_message; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.algorithm_task_stream_runtime.error_message IS '最近错误信息';


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
    ai_rtmp_stream text,
    ai_http_stream text,
    stream smallint,
    ip character varying(45),
    port smallint,
    username character varying(100),
    password character varying(100),
    skylink_token text,
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
    rtsp_direct text,
    channel_online boolean,
    connection_status character varying(100),
    enable_forward boolean,
    auto_snap_enabled boolean NOT NULL,
    directory_id integer,
    cover_image_path character varying(500),
    longitude double precision,
    latitude double precision,
    altitude double precision,
    address character varying(500),
    location_source character varying(20),
    location_updated_at timestamp without time zone,
    heading double precision,
    ptz_type smallint,
    direction_type smallint,
    position_type smallint,
    room_type smallint,
    use_type smallint,
    supply_light_type smallint,
    resolution character varying(100),
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: COLUMN device.ai_rtmp_stream; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.ai_rtmp_stream IS 'AI推流地址（用于算法任务）';


--
-- Name: COLUMN device.ai_http_stream; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.ai_http_stream IS 'AI HTTP地址（用于算法任务）';


--
-- Name: COLUMN device.skylink_token; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.skylink_token IS '大疆司空 X-User-Token（机场/无人机共用）';


--
-- Name: COLUMN device.nvr_channel; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.nvr_channel IS 'NVR 通道号，0 表示非 NVR 挂载';


--
-- Name: COLUMN device.rtsp_direct; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.rtsp_direct IS '摄像头直连 RTSP（经 NVR 枚举时 rtsp_direct）';


--
-- Name: COLUMN device.channel_online; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.channel_online IS 'NVR 通道在线状态';


--
-- Name: COLUMN device.connection_status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.connection_status IS 'NVR 通道连接状态/探测备注';


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
-- Name: COLUMN device.longitude; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.longitude IS 'WGS84 经度，用于地图展示';


--
-- Name: COLUMN device.latitude; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.latitude IS 'WGS84 纬度，用于地图展示';


--
-- Name: COLUMN device.altitude; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.altitude IS '海拔高度(米)，可选';


--
-- Name: COLUMN device.address; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.address IS '安装地址或位置描述';


--
-- Name: COLUMN device.location_source; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.location_source IS '位置来源: manual/gb28181/import';


--
-- Name: COLUMN device.location_updated_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.location_updated_at IS '位置信息最后更新时间';


--
-- Name: COLUMN device.heading; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.heading IS '安装朝向(度)，0=正北，顺时针';


--
-- Name: COLUMN device.ptz_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.ptz_type IS '摄像机结构: 1球机 2半球 3固定枪机 4遥控枪机 5遥控半球 6/7多目';


--
-- Name: COLUMN device.direction_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.direction_type IS '监视方位(光轴): 1东2西3南4北5东南6东北7西南8西北';


--
-- Name: COLUMN device.position_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.position_type IS '位置类型: 1检查站2党政3车站码头4中心广场5体育场馆6商业中心7宗教8校园周边9治安复杂10交通干线';


--
-- Name: COLUMN device.room_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.room_type IS '安装位置: 1室外 2室内';


--
-- Name: COLUMN device.use_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.use_type IS '用途: 1治安 2交通 3重点';


--
-- Name: COLUMN device.supply_light_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.supply_light_type IS '补光: 1无 2红外 3白光 4激光 9其他';


--
-- Name: COLUMN device.resolution; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device.resolution IS '支持的分辨率(可多值)';


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
    updated_at timestamp without time zone,
    task_id integer
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
-- Name: COLUMN device_detection_region.task_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_detection_region.task_id IS '算法任务ID';


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
    snap_save_time integer NOT NULL,
    record_save_time integer NOT NULL,
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
-- Name: COLUMN device_directory.snap_save_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_directory.snap_save_time IS '抓拍保存时长[0:永久,>=1:小时]，目录内非自定义设备继承此值';


--
-- Name: COLUMN device_directory.record_save_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_directory.record_save_time IS '录像保存时长[0:永久,>=1:小时]，目录内非自定义设备继承此值';


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
-- Name: device_track_point; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.device_track_point (
    id bigint NOT NULL,
    device_id character varying(100) NOT NULL,
    session_id bigint,
    recorded_at timestamp without time zone NOT NULL,
    longitude double precision NOT NULL,
    latitude double precision NOT NULL,
    altitude double precision,
    speed double precision,
    direction double precision,
    accuracy_m double precision,
    source character varying(20) NOT NULL,
    report_source character varying(50),
    external_key character varying(200),
    created_at timestamp without time zone
);


--
-- Name: COLUMN device_track_point.device_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_track_point.device_id IS '摄像头 device.id';


--
-- Name: COLUMN device_track_point.session_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_track_point.session_id IS '所属轨迹段，可为空（散点）';


--
-- Name: COLUMN device_track_point.recorded_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_track_point.recorded_at IS 'GPS/位置上报时间';


--
-- Name: COLUMN device_track_point.longitude; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_track_point.longitude IS 'WGS84 经度';


--
-- Name: COLUMN device_track_point.latitude; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_track_point.latitude IS 'WGS84 纬度';


--
-- Name: COLUMN device_track_point.altitude; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_track_point.altitude IS '海拔(米)';


--
-- Name: COLUMN device_track_point.speed; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_track_point.speed IS '速度(km/h)';


--
-- Name: COLUMN device_track_point.direction; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_track_point.direction IS '方向角(0-360度，正北为0)';


--
-- Name: COLUMN device_track_point.accuracy_m; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_track_point.accuracy_m IS '定位精度(米)';


--
-- Name: COLUMN device_track_point.source; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_track_point.source IS '来源: gb28181/gps/import/alert/manual';


--
-- Name: COLUMN device_track_point.report_source; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_track_point.report_source IS '上报类型，如 Mobile Position / GPS Alarm';


--
-- Name: COLUMN device_track_point.external_key; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_track_point.external_key IS '外部同步幂等键，防重复写入';


--
-- Name: device_track_point_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.device_track_point_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: device_track_point_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.device_track_point_id_seq OWNED BY public.device_track_point.id;


--
-- Name: device_track_session; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.device_track_session (
    id bigint NOT NULL,
    device_id character varying(100) NOT NULL,
    title character varying(200),
    started_at timestamp without time zone NOT NULL,
    ended_at timestamp without time zone,
    point_count integer NOT NULL,
    distance_m double precision,
    source character varying(20) NOT NULL,
    external_key character varying(200),
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: COLUMN device_track_session.device_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_track_session.device_id IS '摄像头 device.id';


--
-- Name: COLUMN device_track_session.title; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_track_session.title IS '轨迹段名称，如 2024-06-03 巡逻';


--
-- Name: COLUMN device_track_session.started_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_track_session.started_at IS '轨迹段起始时间（首点 recorded_at）';


--
-- Name: COLUMN device_track_session.ended_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_track_session.ended_at IS '轨迹段结束时间（末点 recorded_at）';


--
-- Name: COLUMN device_track_session.point_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_track_session.point_count IS '轨迹点数量（冗余，便于列表展示）';


--
-- Name: COLUMN device_track_session.distance_m; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_track_session.distance_m IS '轨迹总里程(米)，可选缓存';


--
-- Name: COLUMN device_track_session.source; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_track_session.source IS '来源: gb28181/gps/import/system';


--
-- Name: COLUMN device_track_session.external_key; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.device_track_session.external_key IS '外部同步幂等键，如 gb28181:{sip}:{channel}:{date}';


--
-- Name: device_track_session_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.device_track_session_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: device_track_session_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.device_track_session_id_seq OWNED BY public.device_track_session.id;


--
-- Name: face_auto_enroll_task; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.face_auto_enroll_task (
    id integer NOT NULL,
    library_id integer NOT NULL,
    device_ids text NOT NULL,
    duration_minutes integer NOT NULL,
    capture_interval_sec integer NOT NULL,
    person_name_prefix character varying(50) NOT NULL,
    is_running boolean NOT NULL,
    started_at timestamp without time zone,
    expires_at timestamp without time zone,
    enrolled_count integer NOT NULL,
    skipped_count integer NOT NULL,
    last_device_index integer NOT NULL,
    last_tick_at timestamp without time zone,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: COLUMN face_auto_enroll_task.library_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_auto_enroll_task.library_id IS '所属人脸库ID';


--
-- Name: COLUMN face_auto_enroll_task.device_ids; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_auto_enroll_task.device_ids IS '绑定的摄像头ID列表（JSON数组）';


--
-- Name: COLUMN face_auto_enroll_task.duration_minutes; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_auto_enroll_task.duration_minutes IS '录入模式开启时长（分钟）';


--
-- Name: COLUMN face_auto_enroll_task.capture_interval_sec; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_auto_enroll_task.capture_interval_sec IS '抓帧间隔（秒）';


--
-- Name: COLUMN face_auto_enroll_task.person_name_prefix; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_auto_enroll_task.person_name_prefix IS '自动命名前缀';


--
-- Name: COLUMN face_auto_enroll_task.is_running; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_auto_enroll_task.is_running IS '是否正在运行';


--
-- Name: COLUMN face_auto_enroll_task.started_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_auto_enroll_task.started_at IS '本次启动时间';


--
-- Name: COLUMN face_auto_enroll_task.expires_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_auto_enroll_task.expires_at IS '本次到期时间';


--
-- Name: COLUMN face_auto_enroll_task.enrolled_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_auto_enroll_task.enrolled_count IS '本次已录入数量';


--
-- Name: COLUMN face_auto_enroll_task.skipped_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_auto_enroll_task.skipped_count IS '本次跳过数量（已存在或重复）';


--
-- Name: COLUMN face_auto_enroll_task.last_device_index; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_auto_enroll_task.last_device_index IS '轮询摄像头索引';


--
-- Name: COLUMN face_auto_enroll_task.last_tick_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_auto_enroll_task.last_tick_at IS '上次抓帧时间';


--
-- Name: face_auto_enroll_task_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.face_auto_enroll_task_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: face_auto_enroll_task_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.face_auto_enroll_task_id_seq OWNED BY public.face_auto_enroll_task.id;


--
-- Name: face_entry; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.face_entry (
    id integer NOT NULL,
    library_id integer NOT NULL,
    person_id integer,
    person_name character varying(255) NOT NULL,
    person_code character varying(100),
    image_path character varying(500),
    image_url character varying(500),
    milvus_id character varying(64),
    remark character varying(500),
    is_enabled boolean NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: COLUMN face_entry.library_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_entry.library_id IS '所属人脸库ID';


--
-- Name: COLUMN face_entry.person_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_entry.person_id IS '所属归一化人员ID';


--
-- Name: COLUMN face_entry.person_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_entry.person_name IS '人员姓名';


--
-- Name: COLUMN face_entry.person_code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_entry.person_code IS '人员编号/工号';


--
-- Name: COLUMN face_entry.image_path; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_entry.image_path IS '人脸图片本地路径';


--
-- Name: COLUMN face_entry.image_url; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_entry.image_url IS '人脸图片URL（MinIO）';


--
-- Name: COLUMN face_entry.milvus_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_entry.milvus_id IS 'Milvus向量ID';


--
-- Name: COLUMN face_entry.remark; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_entry.remark IS '备注';


--
-- Name: COLUMN face_entry.is_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_entry.is_enabled IS '是否启用';


--
-- Name: face_entry_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.face_entry_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: face_entry_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.face_entry_id_seq OWNED BY public.face_entry.id;


--
-- Name: face_library; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.face_library (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    code character varying(100) NOT NULL,
    business_tags text,
    description character varying(500),
    similarity_threshold double precision NOT NULL,
    is_enabled boolean NOT NULL,
    face_count integer NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: COLUMN face_library.name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_library.name IS '人脸库名称';


--
-- Name: COLUMN face_library.code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_library.code IS '人脸库编码（唯一）';


--
-- Name: COLUMN face_library.business_tags; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_library.business_tags IS '业务标签（JSON数组，如["员工","访客"]）';


--
-- Name: COLUMN face_library.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_library.description IS '描述';


--
-- Name: COLUMN face_library.similarity_threshold; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_library.similarity_threshold IS '默认匹配相似度阈值';


--
-- Name: COLUMN face_library.is_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_library.is_enabled IS '是否启用';


--
-- Name: COLUMN face_library.face_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_library.face_count IS '人脸数量（冗余统计）';


--
-- Name: face_library_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.face_library_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: face_library_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.face_library_id_seq OWNED BY public.face_library.id;


--
-- Name: face_match_record; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.face_match_record (
    id integer NOT NULL,
    task_id integer,
    task_name character varying(255),
    device_id character varying(100) NOT NULL,
    device_name character varying(255),
    library_id integer,
    library_name character varying(255),
    face_image_path character varying(500),
    matched boolean NOT NULL,
    matched_person_name character varying(255),
    matched_person_code character varying(100),
    matched_face_entry_id integer,
    similarity double precision,
    threshold double precision,
    candidates text,
    alert_id integer,
    correlation_id character varying(36),
    task_type character varying(20),
    status character varying(20) NOT NULL,
    error_message character varying(500),
    created_at timestamp without time zone
);


--
-- Name: COLUMN face_match_record.task_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_match_record.task_id IS '算法任务ID';


--
-- Name: COLUMN face_match_record.task_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_match_record.task_name IS '算法任务名称';


--
-- Name: COLUMN face_match_record.device_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_match_record.device_id IS '设备ID';


--
-- Name: COLUMN face_match_record.device_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_match_record.device_name IS '设备名称';


--
-- Name: COLUMN face_match_record.library_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_match_record.library_id IS '人脸库ID';


--
-- Name: COLUMN face_match_record.library_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_match_record.library_name IS '人脸库名称';


--
-- Name: COLUMN face_match_record.face_image_path; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_match_record.face_image_path IS '待匹配人脸图片路径';


--
-- Name: COLUMN face_match_record.matched; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_match_record.matched IS '是否匹配成功';


--
-- Name: COLUMN face_match_record.matched_person_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_match_record.matched_person_name IS '匹配到的人员姓名';


--
-- Name: COLUMN face_match_record.matched_person_code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_match_record.matched_person_code IS '匹配到的人员编号';


--
-- Name: COLUMN face_match_record.matched_face_entry_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_match_record.matched_face_entry_id IS '匹配到的人脸条目ID';


--
-- Name: COLUMN face_match_record.similarity; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_match_record.similarity IS '最高相似度';


--
-- Name: COLUMN face_match_record.threshold; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_match_record.threshold IS '使用的阈值';


--
-- Name: COLUMN face_match_record.candidates; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_match_record.candidates IS '候选结果（JSON）';


--
-- Name: COLUMN face_match_record.alert_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_match_record.alert_id IS '库匹配命中后新建的告警ID';


--
-- Name: COLUMN face_match_record.correlation_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_match_record.correlation_id IS '关联事件ID（与算法告警同一帧）';


--
-- Name: COLUMN face_match_record.task_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_match_record.task_type IS '任务类型';


--
-- Name: COLUMN face_match_record.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_match_record.status IS '处理状态[pending,success,failed]';


--
-- Name: COLUMN face_match_record.error_message; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_match_record.error_message IS '错误信息';


--
-- Name: face_match_record_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.face_match_record_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: face_match_record_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.face_match_record_id_seq OWNED BY public.face_match_record.id;


--
-- Name: face_person; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.face_person (
    id integer NOT NULL,
    library_id integer NOT NULL,
    person_name character varying(255) NOT NULL,
    person_code character varying(100),
    cover_entry_id integer,
    is_enabled boolean NOT NULL,
    face_count integer NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: COLUMN face_person.library_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_person.library_id IS '所属人脸库ID';


--
-- Name: COLUMN face_person.person_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_person.person_name IS '人员姓名';


--
-- Name: COLUMN face_person.person_code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_person.person_code IS '人员编号/工号';


--
-- Name: COLUMN face_person.cover_entry_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_person.cover_entry_id IS '封面人脸条目ID';


--
-- Name: COLUMN face_person.is_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_person.is_enabled IS '是否启用';


--
-- Name: COLUMN face_person.face_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.face_person.face_count IS '关联人脸照片数';


--
-- Name: face_person_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.face_person_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: face_person_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.face_person_id_seq OWNED BY public.face_person.id;


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
-- Name: model; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.model (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    model_path character varying(500),
    image_url character varying(500),
    version character varying(20),
    status integer NOT NULL,
    class_names text,
    selected_class_names text,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    onnx_model_path character varying(500),
    torchscript_model_path character varying(500),
    tensorrt_model_path character varying(500),
    openvino_model_path character varying(500),
    model_origin character varying(32),
    origin_ref character varying(128)
);


--
-- Name: model_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.model_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: model_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.model_id_seq OWNED BY public.model.id;


--
-- Name: nvr; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.nvr (
    id integer NOT NULL,
    ip character varying(45) NOT NULL,
    port smallint NOT NULL,
    username character varying(100),
    password character varying(100),
    name character varying(100),
    model character varying(100),
    vendor character varying(32),
    serial_number character varying(300),
    firmware_version character varying(100),
    device_type character varying(100),
    mac character varying(17),
    scheme character varying(8),
    rtsp_url text,
    source character varying(32),
    rtsp_template text,
    rtsp_port smallint,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: COLUMN nvr.vendor; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.nvr.vendor IS 'hikvision/dahua 等';


--
-- Name: COLUMN nvr.scheme; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.nvr.scheme IS 'http/https';


--
-- Name: COLUMN nvr.rtsp_url; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.nvr.rtsp_url IS 'NVR 预览/取流 RTSP（对齐 hiktools）';


--
-- Name: COLUMN nvr.source; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.nvr.source IS '探测来源 isapi/dahua_cgi 等';


--
-- Name: COLUMN nvr.rtsp_template; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.nvr.rtsp_template IS '自定义 RTSP 路径模板';


--
-- Name: COLUMN nvr.rtsp_port; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.nvr.rtsp_port IS 'RTSP 端口，默认 554';


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
-- Name: patrol_session; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.patrol_session (
    id integer NOT NULL,
    session_name character varying(255) NOT NULL,
    patrol_mode character varying(20) NOT NULL,
    interval_sec integer NOT NULL,
    pool_size integer NOT NULL,
    device_ids text NOT NULL,
    model_ids text NOT NULL,
    focus_device_id character varying(100),
    algorithm_task_id integer,
    alert_event_enabled boolean NOT NULL,
    alert_event_suppress_time integer NOT NULL,
    face_detection_enabled boolean NOT NULL,
    plate_detection_enabled boolean NOT NULL,
    status character varying(20) NOT NULL,
    exception_reason character varying(500),
    service_server_ip character varying(512),
    service_process_id integer,
    service_last_heartbeat timestamp without time zone,
    service_log_path character varying(500),
    progress_json text,
    total_patrols integer NOT NULL,
    total_detections integer NOT NULL,
    last_patrol_time timestamp without time zone,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: COLUMN patrol_session.session_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.patrol_session.session_name IS '会话名称';


--
-- Name: COLUMN patrol_session.patrol_mode; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.patrol_session.patrol_mode IS '巡检模式[rotate:轮询,pool:连接池,hybrid:混合]';


--
-- Name: COLUMN patrol_session.interval_sec; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.patrol_session.interval_sec IS '每路巡检间隔（秒）';


--
-- Name: COLUMN patrol_session.pool_size; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.patrol_session.pool_size IS '连接池并发拉流数（pool/hybrid）';


--
-- Name: COLUMN patrol_session.device_ids; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.patrol_session.device_ids IS '设备ID列表（JSON数组）';


--
-- Name: COLUMN patrol_session.model_ids; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.patrol_session.model_ids IS '模型ID列表（JSON数组）';


--
-- Name: COLUMN patrol_session.focus_device_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.patrol_session.focus_device_id IS '焦点设备ID（hybrid）';


--
-- Name: COLUMN patrol_session.algorithm_task_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.patrol_session.algorithm_task_id IS '关联算法任务模板ID';


--
-- Name: COLUMN patrol_session.alert_event_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.patrol_session.alert_event_enabled IS '是否启用告警';


--
-- Name: COLUMN patrol_session.alert_event_suppress_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.patrol_session.alert_event_suppress_time IS '告警抑制间隔（秒）';


--
-- Name: COLUMN patrol_session.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.patrol_session.status IS '状态[running,stopped,error]';


--
-- Name: COLUMN patrol_session.progress_json; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.patrol_session.progress_json IS '每设备巡检进度（JSON）';


--
-- Name: COLUMN patrol_session.total_patrols; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.patrol_session.total_patrols IS '累计巡检次数';


--
-- Name: COLUMN patrol_session.total_detections; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.patrol_session.total_detections IS '累计检测次数';


--
-- Name: patrol_session_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patrol_session_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: patrol_session_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.patrol_session_id_seq OWNED BY public.patrol_session.id;


--
-- Name: plate_auto_enroll_task; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.plate_auto_enroll_task (
    id integer NOT NULL,
    library_id integer NOT NULL,
    device_ids text NOT NULL,
    duration_minutes integer NOT NULL,
    capture_interval_sec integer NOT NULL,
    is_running boolean NOT NULL,
    started_at timestamp without time zone,
    expires_at timestamp without time zone,
    enrolled_count integer NOT NULL,
    skipped_count integer NOT NULL,
    last_device_index integer NOT NULL,
    last_tick_at timestamp without time zone,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: COLUMN plate_auto_enroll_task.library_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.plate_auto_enroll_task.library_id IS '所属车牌库ID';


--
-- Name: COLUMN plate_auto_enroll_task.device_ids; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.plate_auto_enroll_task.device_ids IS '绑定的摄像头ID列表（JSON数组）';


--
-- Name: COLUMN plate_auto_enroll_task.duration_minutes; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.plate_auto_enroll_task.duration_minutes IS '录入模式开启时长（分钟）';


--
-- Name: COLUMN plate_auto_enroll_task.capture_interval_sec; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.plate_auto_enroll_task.capture_interval_sec IS '抓帧间隔（秒）';


--
-- Name: COLUMN plate_auto_enroll_task.is_running; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.plate_auto_enroll_task.is_running IS '是否正在运行';


--
-- Name: COLUMN plate_auto_enroll_task.started_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.plate_auto_enroll_task.started_at IS '本次启动时间';


--
-- Name: COLUMN plate_auto_enroll_task.expires_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.plate_auto_enroll_task.expires_at IS '本次到期时间';


--
-- Name: COLUMN plate_auto_enroll_task.enrolled_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.plate_auto_enroll_task.enrolled_count IS '本次已录入数量';


--
-- Name: COLUMN plate_auto_enroll_task.skipped_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.plate_auto_enroll_task.skipped_count IS '本次跳过数量（已存在或重复）';


--
-- Name: COLUMN plate_auto_enroll_task.last_device_index; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.plate_auto_enroll_task.last_device_index IS '轮询摄像头索引';


--
-- Name: COLUMN plate_auto_enroll_task.last_tick_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.plate_auto_enroll_task.last_tick_at IS '上次抓帧时间';


--
-- Name: plate_auto_enroll_task_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.plate_auto_enroll_task_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: plate_auto_enroll_task_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.plate_auto_enroll_task_id_seq OWNED BY public.plate_auto_enroll_task.id;


--
-- Name: plate_entry; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.plate_entry (
    id integer NOT NULL,
    library_id integer NOT NULL,
    plate_no character varying(20) NOT NULL,
    plate_color character varying(20),
    owner_name character varying(255),
    owner_phone character varying(50),
    image_path character varying(500),
    image_url character varying(500),
    remark character varying(500),
    is_enabled boolean NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: COLUMN plate_entry.library_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.plate_entry.library_id IS '所属车牌库ID';


--
-- Name: COLUMN plate_entry.plate_no; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.plate_entry.plate_no IS '车牌号码';


--
-- Name: COLUMN plate_entry.plate_color; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.plate_entry.plate_color IS '车牌颜色';


--
-- Name: COLUMN plate_entry.owner_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.plate_entry.owner_name IS '车主姓名';


--
-- Name: COLUMN plate_entry.owner_phone; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.plate_entry.owner_phone IS '车主电话';


--
-- Name: COLUMN plate_entry.image_path; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.plate_entry.image_path IS '车牌图片本地路径';


--
-- Name: COLUMN plate_entry.image_url; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.plate_entry.image_url IS '车牌图片URL（MinIO）';


--
-- Name: COLUMN plate_entry.remark; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.plate_entry.remark IS '备注';


--
-- Name: COLUMN plate_entry.is_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.plate_entry.is_enabled IS '是否启用';


--
-- Name: plate_entry_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.plate_entry_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: plate_entry_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.plate_entry_id_seq OWNED BY public.plate_entry.id;


--
-- Name: plate_library; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.plate_library (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    code character varying(100) NOT NULL,
    business_tags text,
    description character varying(500),
    is_enabled boolean NOT NULL,
    plate_count integer NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: COLUMN plate_library.name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.plate_library.name IS '车牌库名称';


--
-- Name: COLUMN plate_library.code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.plate_library.code IS '车牌库编码（唯一）';


--
-- Name: COLUMN plate_library.business_tags; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.plate_library.business_tags IS '业务标签（JSON数组）';


--
-- Name: COLUMN plate_library.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.plate_library.description IS '描述';


--
-- Name: COLUMN plate_library.is_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.plate_library.is_enabled IS '是否启用';


--
-- Name: COLUMN plate_library.plate_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.plate_library.plate_count IS '车牌数量（冗余统计）';


--
-- Name: plate_library_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.plate_library_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: plate_library_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.plate_library_id_seq OWNED BY public.plate_library.id;


--
-- Name: plate_match_record; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.plate_match_record (
    id integer NOT NULL,
    task_id integer,
    task_name character varying(255),
    device_id character varying(100) NOT NULL,
    device_name character varying(255),
    library_id integer,
    library_name character varying(255),
    plate_no character varying(20),
    plate_color character varying(20),
    plate_image_path character varying(500),
    matched boolean NOT NULL,
    matched_plate_entry_id integer,
    matched_owner_name character varying(255),
    detect_conf double precision,
    alert_id integer,
    correlation_id character varying(36),
    task_type character varying(20),
    status character varying(20) NOT NULL,
    error_message character varying(500),
    created_at timestamp without time zone
);


--
-- Name: COLUMN plate_match_record.task_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.plate_match_record.task_id IS '算法任务ID';


--
-- Name: COLUMN plate_match_record.task_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.plate_match_record.task_name IS '算法任务名称';


--
-- Name: COLUMN plate_match_record.device_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.plate_match_record.device_id IS '设备ID';


--
-- Name: COLUMN plate_match_record.device_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.plate_match_record.device_name IS '设备名称';


--
-- Name: COLUMN plate_match_record.library_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.plate_match_record.library_id IS '车牌库ID';


--
-- Name: COLUMN plate_match_record.library_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.plate_match_record.library_name IS '车牌库名称';


--
-- Name: COLUMN plate_match_record.plate_no; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.plate_match_record.plate_no IS '识别出的车牌号';


--
-- Name: COLUMN plate_match_record.plate_color; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.plate_match_record.plate_color IS '识别出的车牌颜色';


--
-- Name: COLUMN plate_match_record.plate_image_path; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.plate_match_record.plate_image_path IS '车牌裁剪图路径';


--
-- Name: COLUMN plate_match_record.matched; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.plate_match_record.matched IS '是否在库中匹配成功';


--
-- Name: COLUMN plate_match_record.matched_plate_entry_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.plate_match_record.matched_plate_entry_id IS '匹配到的车牌条目ID';


--
-- Name: COLUMN plate_match_record.matched_owner_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.plate_match_record.matched_owner_name IS '匹配到的车主姓名';


--
-- Name: COLUMN plate_match_record.detect_conf; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.plate_match_record.detect_conf IS '识别置信度';


--
-- Name: COLUMN plate_match_record.alert_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.plate_match_record.alert_id IS '库匹配命中后新建的告警ID';


--
-- Name: COLUMN plate_match_record.correlation_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.plate_match_record.correlation_id IS '关联事件ID（与算法告警同一帧）';


--
-- Name: COLUMN plate_match_record.task_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.plate_match_record.task_type IS '任务类型';


--
-- Name: COLUMN plate_match_record.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.plate_match_record.status IS '处理状态[pending,success,failed]';


--
-- Name: COLUMN plate_match_record.error_message; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.plate_match_record.error_message IS '错误信息';


--
-- Name: plate_match_record_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.plate_match_record_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: plate_match_record_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.plate_match_record_id_seq OWNED BY public.plate_match_record.id;


--
-- Name: playback; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.playback (
    id integer NOT NULL,
    file_path character varying(500) NOT NULL,
    event_time timestamp with time zone NOT NULL,
    device_id character varying(100) NOT NULL,
    device_name character varying(100) NOT NULL,
    duration smallint NOT NULL,
    thumbnail_path character varying(500),
    file_size bigint,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    task_id integer
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
-- Name: pose_intent_match_record; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.pose_intent_match_record (
    id integer NOT NULL,
    task_id integer,
    task_name character varying(255),
    device_id character varying(100) NOT NULL,
    device_name character varying(255),
    library_id integer,
    library_name character varying(255),
    entry_id integer,
    entry_name character varying(255),
    similarity double precision,
    intent_event character varying(100),
    matched boolean NOT NULL,
    pose_snapshot text,
    alert_id integer,
    correlation_id character varying(36),
    task_type character varying(20),
    created_at timestamp without time zone
);


--
-- Name: COLUMN pose_intent_match_record.task_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pose_intent_match_record.task_id IS '算法任务ID';


--
-- Name: COLUMN pose_intent_match_record.pose_snapshot; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pose_intent_match_record.pose_snapshot IS '命中时关键点 JSON';


--
-- Name: pose_intent_match_record_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.pose_intent_match_record_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: pose_intent_match_record_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.pose_intent_match_record_id_seq OWNED BY public.pose_intent_match_record.id;


--
-- Name: post_plugin; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.post_plugin (
    id character varying(128) NOT NULL,
    name character varying(256) NOT NULL,
    latest_version character varying(32),
    runtime character varying(16) NOT NULL,
    enabled boolean NOT NULL,
    manifest_json text NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: COLUMN post_plugin.id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.post_plugin.id IS '插件 id，如 acme.echo';


--
-- Name: COLUMN post_plugin.name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.post_plugin.name IS '显示名';


--
-- Name: COLUMN post_plugin.latest_version; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.post_plugin.latest_version IS '当前版本';


--
-- Name: COLUMN post_plugin.runtime; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.post_plugin.runtime IS 'builtin|http|grpc|script';


--
-- Name: COLUMN post_plugin.manifest_json; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.post_plugin.manifest_json IS 'plugin.json 全文';


--
-- Name: post_plugin_service; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.post_plugin_service (
    plugin_id character varying(128) NOT NULL,
    version character varying(32) NOT NULL,
    replicas integer NOT NULL,
    status character varying(32) NOT NULL,
    endpoint text,
    deploy_mode character varying(16),
    binding_json text,
    updated_at timestamp without time zone
);


--
-- Name: COLUMN post_plugin_service.endpoint; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.post_plugin_service.endpoint IS 'http://host:port';


--
-- Name: COLUMN post_plugin_service.deploy_mode; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.post_plugin_service.deploy_mode IS 'endpoint|docker';


--
-- Name: COLUMN post_plugin_service.binding_json; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.post_plugin_service.binding_json IS '节点绑定 JSON';


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
-- Name: record_file; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.record_file (
    id integer NOT NULL,
    space_id integer NOT NULL,
    device_id character varying(100) NOT NULL,
    object_name character varying(500) NOT NULL,
    bucket_name character varying(255) NOT NULL,
    filename character varying(255) NOT NULL,
    file_size bigint,
    content_type character varying(100),
    etag character varying(128),
    url character varying(500) NOT NULL,
    thumbnail_url character varying(500),
    duration integer,
    event_time timestamp without time zone NOT NULL,
    source character varying(50) NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    task_id integer,
    asset_id character varying(36)
);


--
-- Name: COLUMN record_file.device_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.record_file.device_id IS '设备ID';


--
-- Name: COLUMN record_file.object_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.record_file.object_name IS 'MinIO 对象路径';


--
-- Name: COLUMN record_file.bucket_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.record_file.bucket_name IS 'MinIO bucket';


--
-- Name: COLUMN record_file.filename; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.record_file.filename IS '文件名';


--
-- Name: COLUMN record_file.file_size; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.record_file.file_size IS '文件大小（字节）';


--
-- Name: COLUMN record_file.content_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.record_file.content_type IS 'MIME 类型';


--
-- Name: COLUMN record_file.etag; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.record_file.etag IS 'MinIO ETag';


--
-- Name: COLUMN record_file.url; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.record_file.url IS 'MinIO 下载地址';


--
-- Name: COLUMN record_file.thumbnail_url; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.record_file.thumbnail_url IS '封面下载地址';


--
-- Name: COLUMN record_file.duration; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.record_file.duration IS '时长（秒）';


--
-- Name: COLUMN record_file.event_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.record_file.event_time IS '录像时间（排序字段）';


--
-- Name: COLUMN record_file.source; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.record_file.source IS '来源[dvr|manual]';


--
-- Name: record_file_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.record_file_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: record_file_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.record_file_id_seq OWNED BY public.record_file.id;


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
    save_time_custom boolean NOT NULL,
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

COMMENT ON COLUMN public.record_space.save_time IS '文件保存时长[0:永久保存,>=1(单位:小时)]';


--
-- Name: COLUMN record_space.save_time_custom; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.record_space.save_time_custom IS '是否自定义保存时间（False 时跟随目录默认值）';


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
-- Name: scenario_pose_entry; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.scenario_pose_entry (
    id integer NOT NULL,
    library_id integer NOT NULL,
    name character varying(255) NOT NULL,
    source_type character varying(20) NOT NULL,
    image_path character varying(500),
    image_url character varying(500),
    keypoints text,
    feature_vector text,
    keypoint_visibility_min double precision NOT NULL,
    extra_rules text,
    remark character varying(500),
    is_enabled boolean NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: COLUMN scenario_pose_entry.library_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.scenario_pose_entry.library_id IS '所属场景姿态库ID';


--
-- Name: COLUMN scenario_pose_entry.name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.scenario_pose_entry.name IS '条目名称';


--
-- Name: COLUMN scenario_pose_entry.source_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.scenario_pose_entry.source_type IS '来源 image/rule/manual';


--
-- Name: COLUMN scenario_pose_entry.image_path; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.scenario_pose_entry.image_path IS '参考图本地路径';


--
-- Name: COLUMN scenario_pose_entry.image_url; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.scenario_pose_entry.image_url IS '参考图 URL';


--
-- Name: COLUMN scenario_pose_entry.keypoints; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.scenario_pose_entry.keypoints IS 'COCO-17 关键点 JSON';


--
-- Name: COLUMN scenario_pose_entry.feature_vector; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.scenario_pose_entry.feature_vector IS '归一化特征向量 JSON';


--
-- Name: COLUMN scenario_pose_entry.extra_rules; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.scenario_pose_entry.extra_rules IS '附加规则 JSON';


--
-- Name: COLUMN scenario_pose_entry.remark; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.scenario_pose_entry.remark IS '备注';


--
-- Name: COLUMN scenario_pose_entry.is_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.scenario_pose_entry.is_enabled IS '是否启用';


--
-- Name: scenario_pose_entry_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.scenario_pose_entry_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: scenario_pose_entry_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.scenario_pose_entry_id_seq OWNED BY public.scenario_pose_entry.id;


--
-- Name: scenario_pose_library; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.scenario_pose_library (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    code character varying(100) NOT NULL,
    scene_category character varying(50),
    business_tags text,
    description character varying(500),
    similarity_threshold double precision NOT NULL,
    match_mode character varying(30) NOT NULL,
    intent_event character varying(100),
    intent_object character varying(100),
    alert_level character varying(20) NOT NULL,
    is_enabled boolean NOT NULL,
    entry_count integer NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: COLUMN scenario_pose_library.name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.scenario_pose_library.name IS '场景姿态库名称';


--
-- Name: COLUMN scenario_pose_library.code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.scenario_pose_library.code IS '库编码（唯一）';


--
-- Name: COLUMN scenario_pose_library.scene_category; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.scenario_pose_library.scene_category IS '场景类别 fall/climb/squat/hands_up/custom';


--
-- Name: COLUMN scenario_pose_library.business_tags; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.scenario_pose_library.business_tags IS '业务标签 JSON 数组';


--
-- Name: COLUMN scenario_pose_library.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.scenario_pose_library.description IS '描述';


--
-- Name: COLUMN scenario_pose_library.similarity_threshold; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.scenario_pose_library.similarity_threshold IS '默认匹配阈值';


--
-- Name: COLUMN scenario_pose_library.match_mode; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.scenario_pose_library.match_mode IS '匹配模式 angle/ratio/combined';


--
-- Name: COLUMN scenario_pose_library.intent_event; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.scenario_pose_library.intent_event IS '命中告警 event';


--
-- Name: COLUMN scenario_pose_library.intent_object; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.scenario_pose_library.intent_object IS '命中告警 object';


--
-- Name: COLUMN scenario_pose_library.alert_level; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.scenario_pose_library.alert_level IS '告警级别';


--
-- Name: COLUMN scenario_pose_library.is_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.scenario_pose_library.is_enabled IS '是否启用';


--
-- Name: COLUMN scenario_pose_library.entry_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.scenario_pose_library.entry_count IS '条目数量';


--
-- Name: scenario_pose_library_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.scenario_pose_library_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: scenario_pose_library_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.scenario_pose_library_id_seq OWNED BY public.scenario_pose_library.id;


--
-- Name: snap_image; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.snap_image (
    id integer NOT NULL,
    space_id integer NOT NULL,
    device_id character varying(100) NOT NULL,
    object_name character varying(500) NOT NULL,
    bucket_name character varying(255) NOT NULL,
    filename character varying(255) NOT NULL,
    file_size bigint,
    content_type character varying(100),
    etag character varying(128),
    url character varying(500) NOT NULL,
    captured_at timestamp without time zone NOT NULL,
    task_id integer,
    source character varying(50) NOT NULL,
    created_at timestamp without time zone
);


--
-- Name: COLUMN snap_image.device_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_image.device_id IS '设备ID';


--
-- Name: COLUMN snap_image.object_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_image.object_name IS 'MinIO 对象路径';


--
-- Name: COLUMN snap_image.bucket_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_image.bucket_name IS 'MinIO bucket';


--
-- Name: COLUMN snap_image.filename; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_image.filename IS '文件名';


--
-- Name: COLUMN snap_image.file_size; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_image.file_size IS '文件大小（字节）';


--
-- Name: COLUMN snap_image.content_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_image.content_type IS 'MIME 类型';


--
-- Name: COLUMN snap_image.etag; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_image.etag IS 'MinIO ETag';


--
-- Name: COLUMN snap_image.url; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_image.url IS 'MinIO 下载地址';


--
-- Name: COLUMN snap_image.captured_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_image.captured_at IS '抓拍时间（排序字段）';


--
-- Name: COLUMN snap_image.task_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_image.task_id IS '关联抓拍任务ID';


--
-- Name: COLUMN snap_image.source; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_image.source IS '来源[snap|frame|algorithm]';


--
-- Name: snap_image_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.snap_image_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: snap_image_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.snap_image_id_seq OWNED BY public.snap_image.id;


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
    save_time_custom boolean NOT NULL,
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

COMMENT ON COLUMN public.snap_space.save_time IS '文件保存时长[0:永久保存,>=1(单位:小时)]';


--
-- Name: COLUMN snap_space.save_time_custom; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.snap_space.save_time_custom IS '是否自定义保存时间（False 时跟随目录默认值）';


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
-- Name: space_group_save_policy; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.space_group_save_policy (
    id integer NOT NULL,
    group_type character varying(20) NOT NULL,
    group_key character varying(100) NOT NULL,
    snap_save_time integer NOT NULL,
    record_save_time integer NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: COLUMN space_group_save_policy.group_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.space_group_save_policy.group_type IS '分组类型: nvr / gb28181';


--
-- Name: COLUMN space_group_save_policy.group_key; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.space_group_save_policy.group_key IS 'NVR ID 或国标 SIP 设备 ID';


--
-- Name: COLUMN space_group_save_policy.snap_save_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.space_group_save_policy.snap_save_time IS '抓拍保存时长[0:永久,>=1:小时]';


--
-- Name: COLUMN space_group_save_policy.record_save_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.space_group_save_policy.record_save_time IS '录像保存时长[0:永久,>=1:小时]';


--
-- Name: space_group_save_policy_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.space_group_save_policy_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: space_group_save_policy_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.space_group_save_policy_id_seq OWNED BY public.space_group_save_policy.id;


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
    service_server_ip character varying(512),
    service_port integer,
    service_process_id integer,
    service_last_heartbeat timestamp without time zone,
    service_log_path character varying(500),
    schedule_policy character varying(20) NOT NULL,
    prefer_gpu boolean NOT NULL,
    target_node_id bigint,
    node_id bigint,
    device_deployments text,
    total_streams integer NOT NULL,
    last_process_time timestamp without time zone,
    last_success_time timestamp without time zone,
    description character varying(500),
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    executor character varying(20) DEFAULT 'cpp'::character varying,
    runtime_bin_path character varying(500)
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

COMMENT ON COLUMN public.stream_forward_task.service_server_ip IS '服务运行服务器IP（多节点时为逗号分隔）';


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
-- Name: COLUMN stream_forward_task.schedule_policy; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.stream_forward_task.schedule_policy IS '调度策略[local:本机,auto:自动节点,node:指定节点]';


--
-- Name: COLUMN stream_forward_task.prefer_gpu; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.stream_forward_task.prefer_gpu IS '自动调度时是否优先 GPU 节点';


--
-- Name: COLUMN stream_forward_task.target_node_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.stream_forward_task.target_node_id IS '指定部署节点ID';


--
-- Name: COLUMN stream_forward_task.node_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.stream_forward_task.node_id IS '实际运行节点ID（单节点部署）';


--
-- Name: COLUMN stream_forward_task.device_deployments; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.stream_forward_task.device_deployments IS '设备级远程部署明细 JSON：[{device_ids,node_id,host,workload_id,pid}]';


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
-- Name: algorithm_post_process_result id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.algorithm_post_process_result ALTER COLUMN id SET DEFAULT nextval('public.algorithm_post_process_result_id_seq'::regclass);


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
-- Name: device_track_point id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.device_track_point ALTER COLUMN id SET DEFAULT nextval('public.device_track_point_id_seq'::regclass);


--
-- Name: device_track_session id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.device_track_session ALTER COLUMN id SET DEFAULT nextval('public.device_track_session_id_seq'::regclass);


--
-- Name: face_auto_enroll_task id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.face_auto_enroll_task ALTER COLUMN id SET DEFAULT nextval('public.face_auto_enroll_task_id_seq'::regclass);


--
-- Name: face_entry id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.face_entry ALTER COLUMN id SET DEFAULT nextval('public.face_entry_id_seq'::regclass);


--
-- Name: face_library id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.face_library ALTER COLUMN id SET DEFAULT nextval('public.face_library_id_seq'::regclass);


--
-- Name: face_match_record id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.face_match_record ALTER COLUMN id SET DEFAULT nextval('public.face_match_record_id_seq'::regclass);


--
-- Name: face_person id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.face_person ALTER COLUMN id SET DEFAULT nextval('public.face_person_id_seq'::regclass);


--
-- Name: frame_extractor id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.frame_extractor ALTER COLUMN id SET DEFAULT nextval('public.frame_extractor_id_seq'::regclass);


--
-- Name: image id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.image ALTER COLUMN id SET DEFAULT nextval('public.image_id_seq'::regclass);


--
-- Name: model id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model ALTER COLUMN id SET DEFAULT nextval('public.model_id_seq'::regclass);


--
-- Name: nvr id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nvr ALTER COLUMN id SET DEFAULT nextval('public.nvr_id_seq'::regclass);


--
-- Name: patrol_session id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.patrol_session ALTER COLUMN id SET DEFAULT nextval('public.patrol_session_id_seq'::regclass);


--
-- Name: plate_auto_enroll_task id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plate_auto_enroll_task ALTER COLUMN id SET DEFAULT nextval('public.plate_auto_enroll_task_id_seq'::regclass);


--
-- Name: plate_entry id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plate_entry ALTER COLUMN id SET DEFAULT nextval('public.plate_entry_id_seq'::regclass);


--
-- Name: plate_library id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plate_library ALTER COLUMN id SET DEFAULT nextval('public.plate_library_id_seq'::regclass);


--
-- Name: plate_match_record id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plate_match_record ALTER COLUMN id SET DEFAULT nextval('public.plate_match_record_id_seq'::regclass);


--
-- Name: playback id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.playback ALTER COLUMN id SET DEFAULT nextval('public.playback_id_seq'::regclass);


--
-- Name: pose_intent_match_record id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pose_intent_match_record ALTER COLUMN id SET DEFAULT nextval('public.pose_intent_match_record_id_seq'::regclass);


--
-- Name: pusher id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pusher ALTER COLUMN id SET DEFAULT nextval('public.pusher_id_seq'::regclass);


--
-- Name: record_file id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.record_file ALTER COLUMN id SET DEFAULT nextval('public.record_file_id_seq'::regclass);


--
-- Name: record_space id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.record_space ALTER COLUMN id SET DEFAULT nextval('public.record_space_id_seq'::regclass);


--
-- Name: region_model_service id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.region_model_service ALTER COLUMN id SET DEFAULT nextval('public.region_model_service_id_seq'::regclass);


--
-- Name: scenario_pose_entry id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scenario_pose_entry ALTER COLUMN id SET DEFAULT nextval('public.scenario_pose_entry_id_seq'::regclass);


--
-- Name: scenario_pose_library id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scenario_pose_library ALTER COLUMN id SET DEFAULT nextval('public.scenario_pose_library_id_seq'::regclass);


--
-- Name: snap_image id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.snap_image ALTER COLUMN id SET DEFAULT nextval('public.snap_image_id_seq'::regclass);


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
-- Name: space_group_save_policy id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.space_group_save_policy ALTER COLUMN id SET DEFAULT nextval('public.space_group_save_policy_id_seq'::regclass);


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

COPY public.alert (id, object, event, region, information, "time", device_id, device_name, image_path, image_url, record_path, task_type, task_id, task_name, notify_users, channels, notification_sent, notification_sent_time, business_tags, correlation_id, edge_node_id, edge_node_name, edge_node_host, node_id) FROM stdin;
\.


--
-- Data for Name: algorithm_model_service; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.algorithm_model_service (id, task_id, service_name, service_url, service_type, model_id, threshold, request_method, request_headers, request_body_template, timeout, is_enabled, sort_order, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: algorithm_post_process_result; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.algorithm_post_process_result (id, task_id, task_name, task_code, task_type, device_id, device_name, frame_number, event_time, counts, events, alerts, payload, correlation_id, created_at) FROM stdin;
\.


--
-- Data for Name: algorithm_task; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.algorithm_task (id, task_name, task_code, task_type, model_ids, model_names, detect_conf, extract_interval, rtmp_input_url, rtmp_output_url, tracking_enabled, tracking_similarity_threshold, tracking_max_age, tracking_smooth_alpha, alert_event_enabled, alert_event_suppress_time, alert_class_names, face_detection_enabled, plate_detection_enabled, face_matching_enabled, face_library_ids, face_matching_threshold, plate_matching_enabled, plate_library_ids, matching_business_tags, alert_notification_enabled, alert_notification_config, alarm_suppress_time, last_notify_time, space_id, cron_expression, frame_skip, patrol_mode, patrol_interval_sec, patrol_pool_size, focus_device_id, status, is_enabled, run_status, exception_reason, schedule_policy, prefer_gpu, target_node_id, node_id, service_server_ip, service_port, service_process_id, service_last_heartbeat, service_log_path, total_frames, total_detections, total_captures, last_process_time, last_success_time, last_capture_time, description, sam_supplement_enabled, sam_supplement_config, motion_gate_enabled, motion_gate_config, pose_analysis_enabled, pose_analysis_config, pose_intent_enabled, pose_library_ids, pose_intent_threshold, pose_intent_config, post_process_enabled, post_process_script, post_process_replicas, defense_mode, defense_schedule, created_at, updated_at, face_library_id, plate_library_id, executor, runtime_bin_path, runtime_control_port, device_deployments, post_pipeline) FROM stdin;
\.


--
-- Data for Name: algorithm_task_device; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.algorithm_task_device (task_id, device_id, created_at) FROM stdin;
\.


--
-- Data for Name: algorithm_task_notification_state; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.algorithm_task_notification_state (task_id, device_id, channel_key, last_notify_time, last_event_id, updated_at) FROM stdin;
\.


--
-- Data for Name: algorithm_task_stream_runtime; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.algorithm_task_stream_runtime (task_id, device_id, node_id, stream_key, source_mode, status, last_frame_time, last_detection_time, last_alert_time, error_message, updated_at) FROM stdin;
\.


--
-- Data for Name: detection_region; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.detection_region (id, task_id, region_name, region_type, points, image_id, algorithm_type, algorithm_model_id, algorithm_threshold, algorithm_enabled, color, opacity, is_enabled, sort_order, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: device; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.device (id, name, source, rtmp_stream, http_stream, ai_rtmp_stream, ai_http_stream, stream, ip, port, username, password, skylink_token, mac, manufacturer, model, firmware_version, serial_number, hardware_id, support_move, support_zoom, nvr_id, nvr_channel, rtsp_direct, channel_online, connection_status, enable_forward, auto_snap_enabled, directory_id, cover_image_path, longitude, latitude, altitude, address, location_source, location_updated_at, heading, ptz_type, direction_type, position_type, room_type, use_type, supply_light_type, resolution, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: device_detection_region; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.device_detection_region (id, device_id, region_name, region_type, points, image_id, color, opacity, is_enabled, sort_order, model_ids, created_at, updated_at, task_id) FROM stdin;
\.


--
-- Data for Name: device_directory; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.device_directory (id, name, parent_id, description, sort_order, snap_save_time, record_save_time, created_at, updated_at) FROM stdin;
2	默认分组	\N	未手动分组的摄像头（含直连与国标）	-1000	1	1	2026-08-25 09:49:30.210958	2026-08-25 09:49:30.210961
\.


--
-- Data for Name: device_storage_config; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.device_storage_config (id, device_id, snap_storage_bucket, snap_storage_max_size, snap_storage_cleanup_enabled, snap_storage_cleanup_threshold, snap_storage_cleanup_ratio, video_storage_bucket, video_storage_max_size, video_storage_cleanup_enabled, video_storage_cleanup_threshold, video_storage_cleanup_ratio, last_snap_cleanup_time, last_video_cleanup_time, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: device_track_point; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.device_track_point (id, device_id, session_id, recorded_at, longitude, latitude, altitude, speed, direction, accuracy_m, source, report_source, external_key, created_at) FROM stdin;
\.


--
-- Data for Name: device_track_session; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.device_track_session (id, device_id, title, started_at, ended_at, point_count, distance_m, source, external_key, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: face_auto_enroll_task; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.face_auto_enroll_task (id, library_id, device_ids, duration_minutes, capture_interval_sec, person_name_prefix, is_running, started_at, expires_at, enrolled_count, skipped_count, last_device_index, last_tick_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: face_entry; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.face_entry (id, library_id, person_id, person_name, person_code, image_path, image_url, milvus_id, remark, is_enabled, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: face_library; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.face_library (id, name, code, business_tags, description, similarity_threshold, is_enabled, face_count, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: face_match_record; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.face_match_record (id, task_id, task_name, device_id, device_name, library_id, library_name, face_image_path, matched, matched_person_name, matched_person_code, matched_face_entry_id, similarity, threshold, candidates, alert_id, correlation_id, task_type, status, error_message, created_at) FROM stdin;
\.


--
-- Data for Name: face_person; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.face_person (id, library_id, person_name, person_code, cover_entry_id, is_enabled, face_count, created_at, updated_at) FROM stdin;
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
-- Data for Name: model; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.model (id, name, description, model_path, image_url, version, status, class_names, selected_class_names, created_at, updated_at, onnx_model_path, torchscript_model_path, tensorrt_model_path, openvino_model_path, model_origin, origin_ref) FROM stdin;
\.


--
-- Data for Name: nvr; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.nvr (id, ip, port, username, password, name, model, vendor, serial_number, firmware_version, device_type, mac, scheme, rtsp_url, source, rtsp_template, rtsp_port, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: patrol_session; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.patrol_session (id, session_name, patrol_mode, interval_sec, pool_size, device_ids, model_ids, focus_device_id, algorithm_task_id, alert_event_enabled, alert_event_suppress_time, face_detection_enabled, plate_detection_enabled, status, exception_reason, service_server_ip, service_process_id, service_last_heartbeat, service_log_path, progress_json, total_patrols, total_detections, last_patrol_time, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: plate_auto_enroll_task; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.plate_auto_enroll_task (id, library_id, device_ids, duration_minutes, capture_interval_sec, is_running, started_at, expires_at, enrolled_count, skipped_count, last_device_index, last_tick_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: plate_entry; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.plate_entry (id, library_id, plate_no, plate_color, owner_name, owner_phone, image_path, image_url, remark, is_enabled, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: plate_library; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.plate_library (id, name, code, business_tags, description, is_enabled, plate_count, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: plate_match_record; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.plate_match_record (id, task_id, task_name, device_id, device_name, library_id, library_name, plate_no, plate_color, plate_image_path, matched, matched_plate_entry_id, matched_owner_name, detect_conf, alert_id, correlation_id, task_type, status, error_message, created_at) FROM stdin;
\.


--
-- Data for Name: playback; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.playback (id, file_path, event_time, device_id, device_name, duration, thumbnail_path, file_size, created_at, updated_at, task_id) FROM stdin;
\.


--
-- Data for Name: pose_intent_match_record; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.pose_intent_match_record (id, task_id, task_name, device_id, device_name, library_id, library_name, entry_id, entry_name, similarity, intent_event, matched, pose_snapshot, alert_id, correlation_id, task_type, created_at) FROM stdin;
\.


--
-- Data for Name: post_plugin; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.post_plugin (id, name, latest_version, runtime, enabled, manifest_json, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: post_plugin_service; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.post_plugin_service (plugin_id, version, replicas, status, endpoint, deploy_mode, binding_json, updated_at) FROM stdin;
\.


--
-- Data for Name: pusher; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.pusher (id, pusher_name, pusher_code, video_stream_enabled, video_stream_url, device_rtmp_mapping, video_stream_format, video_stream_quality, event_alert_enabled, event_alert_url, event_alert_method, event_alert_format, event_alert_headers, event_alert_template, description, is_enabled, status, server_ip, port, process_id, last_heartbeat, log_path, task_id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: record_file; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.record_file (id, space_id, device_id, object_name, bucket_name, filename, file_size, content_type, etag, url, thumbnail_url, duration, event_time, source, created_at, updated_at, task_id) FROM stdin;
\.


--
-- Data for Name: record_space; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.record_space (id, space_name, space_code, bucket_name, save_mode, save_time, save_time_custom, description, device_id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: region_model_service; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.region_model_service (id, region_id, service_name, service_url, service_type, model_id, threshold, request_method, request_headers, request_body_template, timeout, is_enabled, sort_order, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: scenario_pose_entry; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.scenario_pose_entry (id, library_id, name, source_type, image_path, image_url, keypoints, feature_vector, keypoint_visibility_min, extra_rules, remark, is_enabled, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: scenario_pose_library; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.scenario_pose_library (id, name, code, scene_category, business_tags, description, similarity_threshold, match_mode, intent_event, intent_object, alert_level, is_enabled, entry_count, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: snap_image; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.snap_image (id, space_id, device_id, object_name, bucket_name, filename, file_size, content_type, etag, url, captured_at, task_id, source, created_at) FROM stdin;
\.


--
-- Data for Name: snap_space; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.snap_space (id, space_name, space_code, bucket_name, save_mode, save_time, save_time_custom, description, device_id, created_at, updated_at) FROM stdin;
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
-- Data for Name: space_group_save_policy; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.space_group_save_policy (id, group_type, group_key, snap_save_time, record_save_time, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: stream_forward_task; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.stream_forward_task (id, task_name, task_code, output_format, output_quality, output_bitrate, status, is_enabled, exception_reason, service_server_ip, service_port, service_process_id, service_last_heartbeat, service_log_path, schedule_policy, prefer_gpu, target_node_id, node_id, device_deployments, total_streams, last_process_time, last_success_time, description, created_at, updated_at, executor, runtime_bin_path) FROM stdin;
\.


--
-- Data for Name: stream_forward_task_device; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.stream_forward_task_device (stream_forward_task_id, device_id, created_at) FROM stdin;
\.


--
-- Data for Name: tracking_target; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tracking_target (id, task_id, device_id, device_name, track_id, class_id, class_name, first_seen_time, last_seen_time, leave_time, duration, first_seen_frame, last_seen_frame, total_detections, information, created_at, updated_at) FROM stdin;
\.


--
-- Name: alert_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.alert_id_seq', 8421, true);


--
-- Name: algorithm_model_service_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.algorithm_model_service_id_seq', 1, false);


--
-- Name: algorithm_post_process_result_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.algorithm_post_process_result_id_seq', 1, false);


--
-- Name: algorithm_task_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.algorithm_task_id_seq', 3, true);


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

SELECT pg_catalog.setval('public.device_directory_id_seq', 2, true);


--
-- Name: device_storage_config_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.device_storage_config_id_seq', 1, false);


--
-- Name: device_track_point_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.device_track_point_id_seq', 60, true);


--
-- Name: device_track_session_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.device_track_session_id_seq', 1, true);


--
-- Name: face_auto_enroll_task_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.face_auto_enroll_task_id_seq', 1, false);


--
-- Name: face_entry_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.face_entry_id_seq', 5, true);


--
-- Name: face_library_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.face_library_id_seq', 1, true);


--
-- Name: face_match_record_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.face_match_record_id_seq', 3014, true);


--
-- Name: face_person_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.face_person_id_seq', 1, true);


--
-- Name: frame_extractor_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.frame_extractor_id_seq', 1, false);


--
-- Name: image_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.image_id_seq', 1, false);


--
-- Name: model_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.model_id_seq', 1, false);


--
-- Name: nvr_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.nvr_id_seq', 1, false);


--
-- Name: patrol_session_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.patrol_session_id_seq', 1, false);


--
-- Name: plate_auto_enroll_task_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.plate_auto_enroll_task_id_seq', 1, false);


--
-- Name: plate_entry_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.plate_entry_id_seq', 5, true);


--
-- Name: plate_library_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.plate_library_id_seq', 1, true);


--
-- Name: plate_match_record_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.plate_match_record_id_seq', 2405, true);


--
-- Name: playback_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.playback_id_seq', 574, true);


--
-- Name: pose_intent_match_record_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.pose_intent_match_record_id_seq', 1, false);


--
-- Name: pusher_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.pusher_id_seq', 1, false);


--
-- Name: record_file_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.record_file_id_seq', 575, true);


--
-- Name: record_space_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.record_space_id_seq', 31, true);


--
-- Name: region_model_service_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.region_model_service_id_seq', 1, false);


--
-- Name: scenario_pose_entry_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.scenario_pose_entry_id_seq', 1, false);


--
-- Name: scenario_pose_library_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.scenario_pose_library_id_seq', 1, false);


--
-- Name: snap_image_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.snap_image_id_seq', 6878, true);


--
-- Name: snap_space_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.snap_space_id_seq', 31, true);


--
-- Name: snap_task_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.snap_task_id_seq', 1, false);


--
-- Name: sorter_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.sorter_id_seq', 1, false);


--
-- Name: space_group_save_policy_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.space_group_save_policy_id_seq', 1, false);


--
-- Name: stream_forward_task_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.stream_forward_task_id_seq', 5, true);


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
-- Name: algorithm_post_process_result algorithm_post_process_result_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.algorithm_post_process_result
    ADD CONSTRAINT algorithm_post_process_result_pkey PRIMARY KEY (id);


--
-- Name: algorithm_task_device algorithm_task_device_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.algorithm_task_device
    ADD CONSTRAINT algorithm_task_device_pkey PRIMARY KEY (task_id, device_id);


--
-- Name: algorithm_task_notification_state algorithm_task_notification_state_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.algorithm_task_notification_state
    ADD CONSTRAINT algorithm_task_notification_state_pkey PRIMARY KEY (task_id, device_id, channel_key);


--
-- Name: algorithm_task algorithm_task_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.algorithm_task
    ADD CONSTRAINT algorithm_task_pkey PRIMARY KEY (id);


--
-- Name: algorithm_task_stream_runtime algorithm_task_stream_runtime_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.algorithm_task_stream_runtime
    ADD CONSTRAINT algorithm_task_stream_runtime_pkey PRIMARY KEY (task_id, device_id);


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
-- Name: device_track_point device_track_point_external_key_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.device_track_point
    ADD CONSTRAINT device_track_point_external_key_key UNIQUE (external_key);


--
-- Name: device_track_point device_track_point_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.device_track_point
    ADD CONSTRAINT device_track_point_pkey PRIMARY KEY (id);


--
-- Name: device_track_session device_track_session_external_key_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.device_track_session
    ADD CONSTRAINT device_track_session_external_key_key UNIQUE (external_key);


--
-- Name: device_track_session device_track_session_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.device_track_session
    ADD CONSTRAINT device_track_session_pkey PRIMARY KEY (id);


--
-- Name: face_auto_enroll_task face_auto_enroll_task_library_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.face_auto_enroll_task
    ADD CONSTRAINT face_auto_enroll_task_library_id_key UNIQUE (library_id);


--
-- Name: face_auto_enroll_task face_auto_enroll_task_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.face_auto_enroll_task
    ADD CONSTRAINT face_auto_enroll_task_pkey PRIMARY KEY (id);


--
-- Name: face_entry face_entry_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.face_entry
    ADD CONSTRAINT face_entry_pkey PRIMARY KEY (id);


--
-- Name: face_library face_library_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.face_library
    ADD CONSTRAINT face_library_code_key UNIQUE (code);


--
-- Name: face_library face_library_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.face_library
    ADD CONSTRAINT face_library_pkey PRIMARY KEY (id);


--
-- Name: face_match_record face_match_record_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.face_match_record
    ADD CONSTRAINT face_match_record_pkey PRIMARY KEY (id);


--
-- Name: face_person face_person_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.face_person
    ADD CONSTRAINT face_person_pkey PRIMARY KEY (id);


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
-- Name: model model_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model
    ADD CONSTRAINT model_name_key UNIQUE (name);


--
-- Name: model model_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model
    ADD CONSTRAINT model_pkey PRIMARY KEY (id);


--
-- Name: nvr nvr_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nvr
    ADD CONSTRAINT nvr_pkey PRIMARY KEY (id);


--
-- Name: patrol_session patrol_session_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.patrol_session
    ADD CONSTRAINT patrol_session_pkey PRIMARY KEY (id);


--
-- Name: plate_auto_enroll_task plate_auto_enroll_task_library_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plate_auto_enroll_task
    ADD CONSTRAINT plate_auto_enroll_task_library_id_key UNIQUE (library_id);


--
-- Name: plate_auto_enroll_task plate_auto_enroll_task_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plate_auto_enroll_task
    ADD CONSTRAINT plate_auto_enroll_task_pkey PRIMARY KEY (id);


--
-- Name: plate_entry plate_entry_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plate_entry
    ADD CONSTRAINT plate_entry_pkey PRIMARY KEY (id);


--
-- Name: plate_library plate_library_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plate_library
    ADD CONSTRAINT plate_library_code_key UNIQUE (code);


--
-- Name: plate_library plate_library_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plate_library
    ADD CONSTRAINT plate_library_pkey PRIMARY KEY (id);


--
-- Name: plate_match_record plate_match_record_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plate_match_record
    ADD CONSTRAINT plate_match_record_pkey PRIMARY KEY (id);


--
-- Name: playback playback_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.playback
    ADD CONSTRAINT playback_pkey PRIMARY KEY (id);


--
-- Name: pose_intent_match_record pose_intent_match_record_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pose_intent_match_record
    ADD CONSTRAINT pose_intent_match_record_pkey PRIMARY KEY (id);


--
-- Name: post_plugin post_plugin_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.post_plugin
    ADD CONSTRAINT post_plugin_pkey PRIMARY KEY (id);


--
-- Name: post_plugin_service post_plugin_service_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.post_plugin_service
    ADD CONSTRAINT post_plugin_service_pkey PRIMARY KEY (plugin_id, version);


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
-- Name: record_file record_file_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.record_file
    ADD CONSTRAINT record_file_pkey PRIMARY KEY (id);


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
-- Name: scenario_pose_entry scenario_pose_entry_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scenario_pose_entry
    ADD CONSTRAINT scenario_pose_entry_pkey PRIMARY KEY (id);


--
-- Name: scenario_pose_library scenario_pose_library_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scenario_pose_library
    ADD CONSTRAINT scenario_pose_library_code_key UNIQUE (code);


--
-- Name: scenario_pose_library scenario_pose_library_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scenario_pose_library
    ADD CONSTRAINT scenario_pose_library_pkey PRIMARY KEY (id);


--
-- Name: snap_image snap_image_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.snap_image
    ADD CONSTRAINT snap_image_pkey PRIMARY KEY (id);


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
-- Name: space_group_save_policy space_group_save_policy_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.space_group_save_policy
    ADD CONSTRAINT space_group_save_policy_pkey PRIMARY KEY (id);


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
-- Name: tracking_target tracking_target_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tracking_target
    ADD CONSTRAINT tracking_target_pkey PRIMARY KEY (id);


--
-- Name: record_file uq_record_file_bucket_object; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.record_file
    ADD CONSTRAINT uq_record_file_bucket_object UNIQUE (bucket_name, object_name);


--
-- Name: snap_image uq_snap_image_bucket_object; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.snap_image
    ADD CONSTRAINT uq_snap_image_bucket_object UNIQUE (bucket_name, object_name);


--
-- Name: space_group_save_policy uq_space_group_save_policy; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.space_group_save_policy
    ADD CONSTRAINT uq_space_group_save_policy UNIQUE (group_type, group_key);


--
-- Name: idx_alert_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_alert_time ON public.alert USING btree ("time" DESC);


--
-- Name: idx_device_detection_region_task_device; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_device_detection_region_task_device ON public.device_detection_region USING btree (task_id, device_id);


--
-- Name: idx_face_match_record_correlation_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_face_match_record_correlation_id ON public.face_match_record USING btree (correlation_id);


--
-- Name: idx_plate_match_record_correlation_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_plate_match_record_correlation_id ON public.plate_match_record USING btree (correlation_id);


--
-- Name: idx_playback_task_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_playback_task_id ON public.playback USING btree (task_id);


--
-- Name: idx_record_file_task_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_record_file_task_id ON public.record_file USING btree (task_id);


--
-- Name: ix_alert_correlation_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_alert_correlation_id ON public.alert USING btree (correlation_id);


--
-- Name: ix_alert_edge_node_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_alert_edge_node_id ON public.alert USING btree (edge_node_id);


--
-- Name: ix_alert_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_alert_time ON public.alert USING btree ("time");


--
-- Name: ix_algorithm_post_process_result_correlation_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_algorithm_post_process_result_correlation_id ON public.algorithm_post_process_result USING btree (correlation_id);


--
-- Name: ix_algorithm_post_process_result_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_algorithm_post_process_result_created_at ON public.algorithm_post_process_result USING btree (created_at);


--
-- Name: ix_algorithm_post_process_result_device_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_algorithm_post_process_result_device_id ON public.algorithm_post_process_result USING btree (device_id);


--
-- Name: ix_algorithm_post_process_result_event_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_algorithm_post_process_result_event_time ON public.algorithm_post_process_result USING btree (event_time);


--
-- Name: ix_algorithm_post_process_result_task_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_algorithm_post_process_result_task_id ON public.algorithm_post_process_result USING btree (task_id);


--
-- Name: ix_device_track_point_device_recorded; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_device_track_point_device_recorded ON public.device_track_point USING btree (device_id, recorded_at);


--
-- Name: ix_device_track_point_session_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_device_track_point_session_id ON public.device_track_point USING btree (session_id);


--
-- Name: ix_device_track_point_session_recorded; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_device_track_point_session_recorded ON public.device_track_point USING btree (session_id, recorded_at);


--
-- Name: ix_device_track_session_device_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_device_track_session_device_id ON public.device_track_session USING btree (device_id);


--
-- Name: ix_face_match_record_correlation_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_face_match_record_correlation_id ON public.face_match_record USING btree (correlation_id);


--
-- Name: ix_nvr_ip; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_nvr_ip ON public.nvr USING btree (ip);


--
-- Name: ix_plate_match_record_correlation_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_plate_match_record_correlation_id ON public.plate_match_record USING btree (correlation_id);


--
-- Name: ix_pose_intent_match_record_correlation_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_pose_intent_match_record_correlation_id ON public.pose_intent_match_record USING btree (correlation_id);


--
-- Name: ix_pose_intent_match_record_device_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_pose_intent_match_record_device_id ON public.pose_intent_match_record USING btree (device_id);


--
-- Name: ix_record_file_device_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_record_file_device_id ON public.record_file USING btree (device_id);


--
-- Name: ix_record_file_event_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_record_file_event_time ON public.record_file USING btree (event_time);


--
-- Name: ix_record_file_space_event_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_record_file_space_event_time ON public.record_file USING btree (space_id, event_time);


--
-- Name: ix_record_file_space_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_record_file_space_id ON public.record_file USING btree (space_id);


--
-- Name: ix_snap_image_captured_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_snap_image_captured_at ON public.snap_image USING btree (captured_at);


--
-- Name: ix_snap_image_device_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_snap_image_device_id ON public.snap_image USING btree (device_id);


--
-- Name: ix_snap_image_space_captured_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_snap_image_space_captured_at ON public.snap_image USING btree (space_id, captured_at);


--
-- Name: ix_snap_image_space_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_snap_image_space_id ON public.snap_image USING btree (space_id);


--
-- Name: uq_alert_correlation_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_alert_correlation_id ON public.alert USING btree (correlation_id) WHERE (correlation_id IS NOT NULL);


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
-- Name: algorithm_task algorithm_task_face_library_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.algorithm_task
    ADD CONSTRAINT algorithm_task_face_library_id_fkey FOREIGN KEY (face_library_id) REFERENCES public.face_library(id) ON DELETE SET NULL;


--
-- Name: algorithm_task algorithm_task_plate_library_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.algorithm_task
    ADD CONSTRAINT algorithm_task_plate_library_id_fkey FOREIGN KEY (plate_library_id) REFERENCES public.plate_library(id) ON DELETE SET NULL;


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
-- Name: device_detection_region device_detection_region_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.device_detection_region
    ADD CONSTRAINT device_detection_region_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.algorithm_task(id) ON DELETE CASCADE;


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
    ADD CONSTRAINT device_nvr_id_fkey FOREIGN KEY (nvr_id) REFERENCES public.nvr(id) ON DELETE SET NULL;


--
-- Name: device_storage_config device_storage_config_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.device_storage_config
    ADD CONSTRAINT device_storage_config_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.device(id) ON DELETE CASCADE;


--
-- Name: device_track_point device_track_point_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.device_track_point
    ADD CONSTRAINT device_track_point_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.device(id) ON DELETE CASCADE;


--
-- Name: device_track_point device_track_point_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.device_track_point
    ADD CONSTRAINT device_track_point_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.device_track_session(id) ON DELETE SET NULL;


--
-- Name: device_track_session device_track_session_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.device_track_session
    ADD CONSTRAINT device_track_session_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.device(id) ON DELETE CASCADE;


--
-- Name: face_auto_enroll_task face_auto_enroll_task_library_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.face_auto_enroll_task
    ADD CONSTRAINT face_auto_enroll_task_library_id_fkey FOREIGN KEY (library_id) REFERENCES public.face_library(id) ON DELETE CASCADE;


--
-- Name: face_entry face_entry_library_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.face_entry
    ADD CONSTRAINT face_entry_library_id_fkey FOREIGN KEY (library_id) REFERENCES public.face_library(id) ON DELETE CASCADE;


--
-- Name: face_entry face_entry_person_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.face_entry
    ADD CONSTRAINT face_entry_person_id_fkey FOREIGN KEY (person_id) REFERENCES public.face_person(id) ON DELETE CASCADE;


--
-- Name: face_person face_person_library_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.face_person
    ADD CONSTRAINT face_person_library_id_fkey FOREIGN KEY (library_id) REFERENCES public.face_library(id) ON DELETE CASCADE;


--
-- Name: image image_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.image
    ADD CONSTRAINT image_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.device(id);


--
-- Name: plate_auto_enroll_task plate_auto_enroll_task_library_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plate_auto_enroll_task
    ADD CONSTRAINT plate_auto_enroll_task_library_id_fkey FOREIGN KEY (library_id) REFERENCES public.plate_library(id) ON DELETE CASCADE;


--
-- Name: plate_entry plate_entry_library_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plate_entry
    ADD CONSTRAINT plate_entry_library_id_fkey FOREIGN KEY (library_id) REFERENCES public.plate_library(id) ON DELETE CASCADE;


--
-- Name: record_file record_file_space_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.record_file
    ADD CONSTRAINT record_file_space_id_fkey FOREIGN KEY (space_id) REFERENCES public.record_space(id) ON DELETE CASCADE;


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
-- Name: scenario_pose_entry scenario_pose_entry_library_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scenario_pose_entry
    ADD CONSTRAINT scenario_pose_entry_library_id_fkey FOREIGN KEY (library_id) REFERENCES public.scenario_pose_library(id) ON DELETE CASCADE;


--
-- Name: snap_image snap_image_space_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.snap_image
    ADD CONSTRAINT snap_image_space_id_fkey FOREIGN KEY (space_id) REFERENCES public.snap_space(id) ON DELETE CASCADE;


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
-- Name: tracking_target tracking_target_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tracking_target
    ADD CONSTRAINT tracking_target_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.algorithm_task(id) ON DELETE CASCADE;


--
-- 边缘/中心分层录像的设备策略与统一媒体资产索引
--

CREATE TABLE public.device_recording_policy (
    id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    device_id character varying(100) NOT NULL,
    recording_mode character varying(20) DEFAULT 'continuous'::character varying NOT NULL,
    retention_hours integer DEFAULT 168 NOT NULL,
    event_pre_seconds integer DEFAULT 10 NOT NULL,
    event_post_seconds integer DEFAULT 20 NOT NULL,
    event_image_sync boolean DEFAULT true NOT NULL,
    event_clip_sync boolean DEFAULT true NOT NULL,
    live_transport_mode character varying(20) DEFAULT 'always_push'::character varying NOT NULL,
    playback_route_mode character varying(20) DEFAULT 'auto'::character varying NOT NULL,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    CONSTRAINT uq_device_recording_policy_device_id UNIQUE (device_id)
);

CREATE INDEX ix_device_recording_policy_device_id
    ON public.device_recording_policy USING btree (device_id);

CREATE TABLE public.media_asset (
    id character varying(36) NOT NULL PRIMARY KEY,
    asset_type character varying(32) NOT NULL,
    device_id character varying(100) NOT NULL,
    alert_id bigint,
    task_id bigint,
    source_node_id bigint,
    storage_node_id bigint,
    storage_generation bigint DEFAULT 1 NOT NULL,
    storage_scope character varying(16) NOT NULL,
    storage_backend character varying(16) NOT NULL,
    bucket_name character varying(255),
    object_key character varying(500) NOT NULL,
    status character varying(16) DEFAULT 'pending'::character varying NOT NULL,
    start_time timestamp with time zone,
    end_time timestamp with time zone,
    duration_ms bigint,
    file_size bigint,
    content_type character varying(100) DEFAULT 'application/octet-stream'::character varying NOT NULL,
    etag character varying(128),
    checksum character varying(128),
    retry_count integer DEFAULT 0 NOT NULL,
    last_error text,
    expires_at timestamp with time zone,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    CONSTRAINT uq_media_asset_bucket_object UNIQUE (bucket_name, object_key)
);

CREATE INDEX ix_media_asset_device_id ON public.media_asset USING btree (device_id);
CREATE INDEX ix_media_asset_asset_type ON public.media_asset USING btree (asset_type);
CREATE INDEX ix_media_asset_alert_id ON public.media_asset USING btree (alert_id);
CREATE INDEX ix_media_asset_task_id ON public.media_asset USING btree (task_id);
CREATE INDEX ix_media_asset_source_node_id ON public.media_asset USING btree (source_node_id);
CREATE INDEX ix_media_asset_storage_node_id ON public.media_asset USING btree (storage_node_id);
CREATE INDEX ix_media_asset_status ON public.media_asset USING btree (status);
CREATE INDEX ix_media_asset_start_time ON public.media_asset USING btree (start_time);
CREATE INDEX ix_media_asset_expires_at ON public.media_asset USING btree (expires_at);
CREATE INDEX ix_media_asset_device_time ON public.media_asset USING btree (device_id, start_time, end_time);
CREATE INDEX ix_media_asset_alert_type ON public.media_asset USING btree (alert_id, asset_type);
CREATE INDEX ix_media_asset_source_status ON public.media_asset USING btree (source_node_id, status);
CREATE INDEX ix_media_asset_storage_time ON public.media_asset USING btree (storage_node_id, start_time);
CREATE INDEX ix_media_asset_expiry_status ON public.media_asset USING btree (expires_at, status);

CREATE INDEX ix_alert_image_asset_id ON public.alert USING btree (image_asset_id);
CREATE INDEX ix_alert_record_asset_id ON public.alert USING btree (record_asset_id);
CREATE UNIQUE INDEX ux_record_file_asset_id ON public.record_file USING btree (asset_id)
    WHERE (asset_id IS NOT NULL);


--
-- PostgreSQL database dump complete
--

\unrestrict E3WsAYvddKwRlIv0hj4lfff9sF4j3KqAd4QGlnoy84lOPhGD9xt7B5sbjSb2frl
