--
-- PostgreSQL database dump
--

\restrict KJM1yFgt7vdzHI08ckJHfmIgDFgu8pia6MROPKXCRdrLDy6VkU10gdC2Qyv8zzJ

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

DROP DATABASE IF EXISTS "iot-ai20";
--
-- Name: iot-ai20; Type: DATABASE; Schema: -; Owner: -
--

CREATE DATABASE "iot-ai20" WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'en_US.utf8';


\unrestrict KJM1yFgt7vdzHI08ckJHfmIgDFgu8pia6MROPKXCRdrLDy6VkU10gdC2Qyv8zzJ
\encoding SQL_ASCII
\connect -reuse-previous=on "dbname='iot-ai20'"
\restrict KJM1yFgt7vdzHI08ckJHfmIgDFgu8pia6MROPKXCRdrLDy6VkU10gdC2Qyv8zzJ

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
-- Name: ai_service; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ai_service (
    id integer NOT NULL,
    model_id integer,
    service_name character varying(100) NOT NULL,
    server_ip character varying(50),
    port integer,
    inference_endpoint character varying(200),
    status character varying(20),
    mac_address character varying(50),
    deploy_time timestamp without time zone,
    last_heartbeat timestamp without time zone,
    process_id integer,
    log_path character varying(500),
    model_version character varying(20),
    format character varying(50),
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    node_id bigint
);


--
-- Name: ai_service_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.ai_service_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: ai_service_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.ai_service_id_seq OWNED BY public.ai_service.id;


--
-- Name: auto_label_model_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.auto_label_model_history (
    id integer NOT NULL,
    dataset_id bigint NOT NULL,
    model_id integer,
    train_task_id integer,
    source_model_id integer,
    version_no integer NOT NULL,
    annotated_count integer,
    class_names text,
    map50 double precision,
    status character varying(20) NOT NULL,
    trigger_source character varying(30) NOT NULL,
    error_message text,
    created_at timestamp without time zone,
    completed_at timestamp without time zone
);


--
-- Name: COLUMN auto_label_model_history.dataset_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.auto_label_model_history.dataset_id IS '数据集ID';


--
-- Name: COLUMN auto_label_model_history.model_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.auto_label_model_history.model_id IS '发布后模型ID';


--
-- Name: COLUMN auto_label_model_history.train_task_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.auto_label_model_history.train_task_id IS '训练任务ID';


--
-- Name: COLUMN auto_label_model_history.source_model_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.auto_label_model_history.source_model_id IS '微调基座模型ID';


--
-- Name: COLUMN auto_label_model_history.version_no; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.auto_label_model_history.version_no IS '更新序号';


--
-- Name: COLUMN auto_label_model_history.annotated_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.auto_label_model_history.annotated_count IS '参与训练的已标注张数';


--
-- Name: COLUMN auto_label_model_history.class_names; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.auto_label_model_history.class_names IS '类别 JSON';


--
-- Name: COLUMN auto_label_model_history.map50; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.auto_label_model_history.map50 IS '训练 mAP50';


--
-- Name: COLUMN auto_label_model_history.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.auto_label_model_history.status IS 'PENDING/TRAINING/COMPLETED/FAILED';


--
-- Name: COLUMN auto_label_model_history.trigger_source; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.auto_label_model_history.trigger_source IS 'manual/pipeline';


--
-- Name: COLUMN auto_label_model_history.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.auto_label_model_history.created_at IS '创建时间';


--
-- Name: COLUMN auto_label_model_history.completed_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.auto_label_model_history.completed_at IS '完成时间';


--
-- Name: auto_label_model_history_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.auto_label_model_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: auto_label_model_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.auto_label_model_history_id_seq OWNED BY public.auto_label_model_history.id;


--
-- Name: auto_label_result; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.auto_label_result (
    id integer NOT NULL,
    task_id integer NOT NULL,
    dataset_image_id bigint NOT NULL,
    annotations text,
    status character varying(20) NOT NULL,
    error_message text,
    created_at timestamp without time zone
);


--
-- Name: COLUMN auto_label_result.task_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.auto_label_result.task_id IS '任务ID';


--
-- Name: COLUMN auto_label_result.dataset_image_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.auto_label_result.dataset_image_id IS '数据集图片ID';


--
-- Name: COLUMN auto_label_result.annotations; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.auto_label_result.annotations IS '标注结果JSON';


--
-- Name: COLUMN auto_label_result.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.auto_label_result.status IS '状态[SUCCESS:成功,FAILED:失败]';


--
-- Name: COLUMN auto_label_result.error_message; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.auto_label_result.error_message IS '错误信息';


--
-- Name: COLUMN auto_label_result.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.auto_label_result.created_at IS '创建时间';


--
-- Name: auto_label_result_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.auto_label_result_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: auto_label_result_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.auto_label_result_id_seq OWNED BY public.auto_label_result.id;


--
-- Name: auto_label_subtask; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.auto_label_subtask (
    id integer NOT NULL,
    parent_task_id integer NOT NULL,
    dataset_id bigint NOT NULL,
    frame_task_id bigint,
    frame_task_name character varying(200),
    rtmp_url text,
    subtask_type character varying(30),
    status character varying(20) NOT NULL,
    queue_position integer,
    assigned_node_id integer,
    assigned_node_host character varying(100),
    workload_id character varying(64),
    captured_count integer,
    labeled_count integer,
    failed_count integer,
    processed_images integer,
    error_message text,
    config_json text,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    started_at timestamp without time zone,
    completed_at timestamp without time zone
);


--
-- Name: COLUMN auto_label_subtask.parent_task_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.auto_label_subtask.parent_task_id IS '父任务ID';


--
-- Name: COLUMN auto_label_subtask.dataset_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.auto_label_subtask.dataset_id IS '数据集ID';


--
-- Name: COLUMN auto_label_subtask.frame_task_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.auto_label_subtask.frame_task_id IS '帧捕获任务/摄像头ID';


--
-- Name: COLUMN auto_label_subtask.frame_task_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.auto_label_subtask.frame_task_name IS '摄像头任务名称';


--
-- Name: COLUMN auto_label_subtask.rtmp_url; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.auto_label_subtask.rtmp_url IS '视频流地址';


--
-- Name: COLUMN auto_label_subtask.subtask_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.auto_label_subtask.subtask_type IS '子任务类型';


--
-- Name: COLUMN auto_label_subtask.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.auto_label_subtask.status IS 'QUEUED/DISPATCHING/RUNNING/COMPLETED/FAILED';


--
-- Name: COLUMN auto_label_subtask.queue_position; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.auto_label_subtask.queue_position IS '队列位置';


--
-- Name: COLUMN auto_label_subtask.assigned_node_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.auto_label_subtask.assigned_node_id IS '分配的节点ID';


--
-- Name: COLUMN auto_label_subtask.assigned_node_host; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.auto_label_subtask.assigned_node_host IS '节点主机';


--
-- Name: COLUMN auto_label_subtask.workload_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.auto_label_subtask.workload_id IS '节点工作负载绑定ID';


--
-- Name: COLUMN auto_label_subtask.config_json; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.auto_label_subtask.config_json IS '子任务配置 JSON';


--
-- Name: auto_label_subtask_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.auto_label_subtask_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: auto_label_subtask_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.auto_label_subtask_id_seq OWNED BY public.auto_label_subtask.id;


--
-- Name: auto_label_task; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.auto_label_task (
    id integer NOT NULL,
    dataset_id bigint NOT NULL,
    model_service_id integer,
    status character varying(20) NOT NULL,
    total_images integer,
    processed_images integer,
    success_count integer,
    failed_count integer,
    confidence_threshold double precision,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    error_message text,
    model_id integer,
    label_mode character varying(20) DEFAULT 'yolo'::character varying,
    text_prompts text,
    annotation_type character varying(20) DEFAULT 'rectangle'::character varying,
    phase character varying(20),
    bootstrap_limit integer,
    bootstrap_selection character varying(30) DEFAULT 'unlabeled_first'::character varying,
    review_passed boolean DEFAULT false,
    return_masks boolean DEFAULT false,
    pipeline_config text,
    execution_mode character varying(20) DEFAULT 'local'::character varying,
    queue_priority integer DEFAULT 0,
    selected_frame_task_ids text
);


--
-- Name: COLUMN auto_label_task.dataset_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.auto_label_task.dataset_id IS '数据集ID';


--
-- Name: COLUMN auto_label_task.model_service_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.auto_label_task.model_service_id IS 'AI服务ID';


--
-- Name: COLUMN auto_label_task.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.auto_label_task.status IS '状态[PENDING:待处理,PROCESSING:处理中,COMPLETED:已完成,FAILED:失败]';


--
-- Name: COLUMN auto_label_task.total_images; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.auto_label_task.total_images IS '总图片数';


--
-- Name: COLUMN auto_label_task.processed_images; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.auto_label_task.processed_images IS '已处理图片数';


--
-- Name: COLUMN auto_label_task.success_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.auto_label_task.success_count IS '成功标注数';


--
-- Name: COLUMN auto_label_task.failed_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.auto_label_task.failed_count IS '失败数';


--
-- Name: COLUMN auto_label_task.confidence_threshold; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.auto_label_task.confidence_threshold IS '置信度阈值';


--
-- Name: COLUMN auto_label_task.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.auto_label_task.created_at IS '创建时间';


--
-- Name: COLUMN auto_label_task.updated_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.auto_label_task.updated_at IS '更新时间';


--
-- Name: COLUMN auto_label_task.started_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.auto_label_task.started_at IS '开始时间';


--
-- Name: COLUMN auto_label_task.completed_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.auto_label_task.completed_at IS '完成时间';


--
-- Name: COLUMN auto_label_task.error_message; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.auto_label_task.error_message IS '错误信息';


--
-- Name: auto_label_task_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.auto_label_task_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: auto_label_task_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.auto_label_task_id_seq OWNED BY public.auto_label_task.id;


--
-- Name: export_record; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.export_record (
    id integer NOT NULL,
    model_id integer NOT NULL,
    model_name character varying(100),
    format character varying(50) NOT NULL,
    minio_path character varying(500),
    local_path character varying(500),
    created_at timestamp without time zone,
    status character varying(20),
    message text
);


--
-- Name: export_record_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.export_record_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: export_record_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.export_record_id_seq OWNED BY public.export_record.id;


--
-- Name: inference_task; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.inference_task (
    id integer NOT NULL,
    model_id integer,
    inference_type character varying(20) NOT NULL,
    input_source character varying(500),
    output_path character varying(500),
    processed_frames integer,
    start_time timestamp without time zone,
    end_time timestamp without time zone,
    status character varying(20),
    error_message text,
    processing_time double precision,
    stream_output_url character varying(500)
);


--
-- Name: inference_task_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.inference_task_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: inference_task_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.inference_task_id_seq OWNED BY public.inference_task.id;


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
-- Name: llm_deploy_service; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.llm_deploy_service (
    id integer NOT NULL,
    service_name character varying(100) NOT NULL,
    qwen_model_key character varying(50) NOT NULL,
    hf_model_id character varying(200) NOT NULL,
    node_id bigint,
    server_ip character varying(50),
    port integer,
    api_endpoint character varying(300),
    tensor_parallel_size integer,
    max_model_len integer,
    status character varying(20),
    llm_config_id integer,
    process_id integer,
    log_path character varying(500),
    error_message text,
    deploy_time timestamp without time zone,
    last_heartbeat timestamp without time zone,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: llm_deploy_service_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.llm_deploy_service_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: llm_deploy_service_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.llm_deploy_service_id_seq OWNED BY public.llm_deploy_service.id;


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
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    onnx_model_path character varying(500),
    torchscript_model_path character varying(500),
    tensorrt_model_path character varying(500),
    openvino_model_path character varying(500),
    rknn_model_path character varying(500),
    status integer DEFAULT 0,
    class_names text,
    selected_class_names text,
    model_origin character varying(32) DEFAULT 'upload'::character varying,
    origin_ref character varying(128),
    family_key character varying(120),
    is_family_active boolean
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
-- Name: ocr_result; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ocr_result (
    id integer NOT NULL,
    text text NOT NULL,
    confidence double precision,
    bbox json,
    polygon json,
    page_num integer,
    line_num integer,
    word_num integer,
    image_url character varying(500),
    created_at timestamp without time zone
);


--
-- Name: ocr_result_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.ocr_result_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: ocr_result_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.ocr_result_id_seq OWNED BY public.ocr_result.id;


--
-- Name: plate_algorithm_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.plate_algorithm_version (
    id integer NOT NULL,
    version character varying(50) NOT NULL,
    description text,
    base_model character varying(100) NOT NULL,
    model_path character varying(500),
    metrics_path character varying(500),
    train_results_path character varying(500),
    status character varying(20) NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: plate_algorithm_version_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.plate_algorithm_version_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: plate_algorithm_version_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.plate_algorithm_version_id_seq OWNED BY public.plate_algorithm_version.id;


--
-- Name: plate_dataset; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.plate_dataset (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    dataset_source character varying(1000) NOT NULL,
    source_type character varying(20) NOT NULL,
    status character varying(20) NOT NULL,
    merged_from text,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: plate_dataset_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.plate_dataset_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: plate_dataset_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.plate_dataset_id_seq OWNED BY public.plate_dataset.id;


--
-- Name: plate_inference_task; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.plate_inference_task (
    id integer NOT NULL,
    version_id integer,
    status character varying(20) NOT NULL,
    input_source character varying(1000),
    output_image_path character varying(500),
    output_json_path character varying(500),
    detection_count integer NOT NULL,
    result_preview text,
    error_message text,
    processing_time double precision,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: plate_inference_task_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.plate_inference_task_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: plate_inference_task_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.plate_inference_task_id_seq OWNED BY public.plate_inference_task.id;


--
-- Name: plate_train_task; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.plate_train_task (
    id integer NOT NULL,
    version_id integer,
    status character varying(20) NOT NULL,
    progress integer NOT NULL,
    dataset_source character varying(1000) NOT NULL,
    dataset_local_path character varying(1000),
    normalized_data_yaml character varying(1000),
    hyperparameters text,
    train_log text NOT NULL,
    error_message text,
    minio_model_path character varying(500),
    metrics_path character varying(500),
    train_results_path character varying(500),
    start_time timestamp without time zone,
    end_time timestamp without time zone,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: plate_train_task_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.plate_train_task_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: plate_train_task_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.plate_train_task_id_seq OWNED BY public.plate_train_task.id;


--
-- Name: rag_expert; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.rag_expert (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    category character varying(50) NOT NULL,
    system_prompt text NOT NULL,
    welcome_message text,
    is_enabled boolean DEFAULT true NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: rag_expert_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.rag_expert_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: rag_expert_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.rag_expert_id_seq OWNED BY public.rag_expert.id;


--
-- Name: rag_expert_knowledge_set; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.rag_expert_knowledge_set (
    expert_id integer NOT NULL,
    knowledge_set_id integer NOT NULL
);


--
-- Name: rag_knowledge_document; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.rag_knowledge_document (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    content_type character varying(80),
    char_count integer DEFAULT 0,
    status character varying(20) DEFAULT 'parsed'::character varying NOT NULL,
    source_type character varying(20) DEFAULT 'upload'::character varying NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: rag_knowledge_document_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.rag_knowledge_document_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: rag_knowledge_document_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.rag_knowledge_document_id_seq OWNED BY public.rag_knowledge_document.id;


--
-- Name: rag_knowledge_segment; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.rag_knowledge_segment (
    id integer NOT NULL,
    document_id integer NOT NULL,
    segment_index integer NOT NULL,
    title character varying(255),
    content text NOT NULL,
    search_terms text DEFAULT '' NOT NULL,
    tags json,
    is_enabled boolean DEFAULT true NOT NULL,
    milvus_id character varying(64),
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: rag_knowledge_segment_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.rag_knowledge_segment_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: rag_knowledge_segment_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.rag_knowledge_segment_id_seq OWNED BY public.rag_knowledge_segment.id;


--
-- Name: rag_knowledge_set; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.rag_knowledge_set (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    category character varying(50) NOT NULL,
    description text,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: rag_knowledge_set_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.rag_knowledge_set_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: rag_knowledge_set_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.rag_knowledge_set_id_seq OWNED BY public.rag_knowledge_set.id;


--
-- Name: rag_knowledge_set_segment; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.rag_knowledge_set_segment (
    knowledge_set_id integer NOT NULL,
    segment_id integer NOT NULL
);


--
-- Name: sam_inference_result; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sam_inference_result (
    id integer NOT NULL,
    prompt_type character varying(20) NOT NULL,
    prompt_data text,
    image_url character varying(500),
    result_data text,
    model_type character varying(20),
    inference_ms integer,
    created_at timestamp without time zone
);


--
-- Name: COLUMN sam_inference_result.prompt_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sam_inference_result.prompt_type IS '提示类型[point/box/auto/text]';


--
-- Name: COLUMN sam_inference_result.prompt_data; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sam_inference_result.prompt_data IS '提示参数JSON';


--
-- Name: COLUMN sam_inference_result.image_url; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sam_inference_result.image_url IS '图片URL';


--
-- Name: COLUMN sam_inference_result.result_data; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sam_inference_result.result_data IS '推理结果JSON';


--
-- Name: COLUMN sam_inference_result.model_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sam_inference_result.model_type IS '模型类型[vit_b/vit_l/vit_h]';


--
-- Name: COLUMN sam_inference_result.inference_ms; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sam_inference_result.inference_ms IS '推理耗时(毫秒)';


--
-- Name: COLUMN sam_inference_result.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sam_inference_result.created_at IS '创建时间';


--
-- Name: sam_inference_result_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sam_inference_result_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sam_inference_result_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sam_inference_result_id_seq OWNED BY public.sam_inference_result.id;


--
-- Name: speech_record; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.speech_record (
    id integer NOT NULL,
    order_id character varying(100) NOT NULL,
    audio_file_path character varying(500),
    filename character varying(255) NOT NULL,
    file_size integer NOT NULL,
    duration integer NOT NULL,
    recognized_text text,
    confidence double precision,
    status character varying(20),
    created_at timestamp without time zone,
    completed_at timestamp without time zone,
    error_message text
);


--
-- Name: speech_record_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.speech_record_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: speech_record_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.speech_record_id_seq OWNED BY public.speech_record.id;


--
-- Name: train_task; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.train_task (
    id integer NOT NULL,
    model_id integer,
    progress integer,
    dataset_path character varying(200) NOT NULL,
    hyperparameters text,
    start_time timestamp without time zone,
    end_time timestamp without time zone,
    status character varying(20),
    train_log text NOT NULL,
    checkpoint_dir character varying(500) NOT NULL,
    metrics_path text,
    minio_model_path character varying(500),
    train_results_path character varying(500),
    name character varying(100),
    dataset_name character varying(100),
    dataset_version character varying(100),
    schedule_policy character varying(20) DEFAULT 'local'::character varying,
    target_node_id bigint,
    node_id bigint,
    service_server_ip character varying(128),
    service_process_id bigint
);


--
-- Name: train_task_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.train_task_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: train_task_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.train_task_id_seq OWNED BY public.train_task.id;


--
-- Name: ai_service id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_service ALTER COLUMN id SET DEFAULT nextval('public.ai_service_id_seq'::regclass);


--
-- Name: auto_label_model_history id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auto_label_model_history ALTER COLUMN id SET DEFAULT nextval('public.auto_label_model_history_id_seq'::regclass);


--
-- Name: auto_label_result id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auto_label_result ALTER COLUMN id SET DEFAULT nextval('public.auto_label_result_id_seq'::regclass);


--
-- Name: auto_label_subtask id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auto_label_subtask ALTER COLUMN id SET DEFAULT nextval('public.auto_label_subtask_id_seq'::regclass);


--
-- Name: auto_label_task id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auto_label_task ALTER COLUMN id SET DEFAULT nextval('public.auto_label_task_id_seq'::regclass);


--
-- Name: export_record id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.export_record ALTER COLUMN id SET DEFAULT nextval('public.export_record_id_seq'::regclass);


--
-- Name: inference_task id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inference_task ALTER COLUMN id SET DEFAULT nextval('public.inference_task_id_seq'::regclass);


--
-- Name: llm_config id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_config ALTER COLUMN id SET DEFAULT nextval('public.llm_config_id_seq'::regclass);


--
-- Name: llm_deploy_service id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_deploy_service ALTER COLUMN id SET DEFAULT nextval('public.llm_deploy_service_id_seq'::regclass);


--
-- Name: model id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model ALTER COLUMN id SET DEFAULT nextval('public.model_id_seq'::regclass);


--
-- Name: ocr_result id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ocr_result ALTER COLUMN id SET DEFAULT nextval('public.ocr_result_id_seq'::regclass);


--
-- Name: plate_algorithm_version id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plate_algorithm_version ALTER COLUMN id SET DEFAULT nextval('public.plate_algorithm_version_id_seq'::regclass);


--
-- Name: plate_dataset id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plate_dataset ALTER COLUMN id SET DEFAULT nextval('public.plate_dataset_id_seq'::regclass);


--
-- Name: plate_inference_task id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plate_inference_task ALTER COLUMN id SET DEFAULT nextval('public.plate_inference_task_id_seq'::regclass);


--
-- Name: plate_train_task id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plate_train_task ALTER COLUMN id SET DEFAULT nextval('public.plate_train_task_id_seq'::regclass);


--
-- Name: rag_expert id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rag_expert ALTER COLUMN id SET DEFAULT nextval('public.rag_expert_id_seq'::regclass);


--
-- Name: rag_knowledge_document id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rag_knowledge_document ALTER COLUMN id SET DEFAULT nextval('public.rag_knowledge_document_id_seq'::regclass);


--
-- Name: rag_knowledge_segment id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rag_knowledge_segment ALTER COLUMN id SET DEFAULT nextval('public.rag_knowledge_segment_id_seq'::regclass);


--
-- Name: rag_knowledge_set id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rag_knowledge_set ALTER COLUMN id SET DEFAULT nextval('public.rag_knowledge_set_id_seq'::regclass);


--
-- Name: sam_inference_result id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sam_inference_result ALTER COLUMN id SET DEFAULT nextval('public.sam_inference_result_id_seq'::regclass);


--
-- Name: speech_record id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.speech_record ALTER COLUMN id SET DEFAULT nextval('public.speech_record_id_seq'::regclass);


--
-- Name: train_task id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.train_task ALTER COLUMN id SET DEFAULT nextval('public.train_task_id_seq'::regclass);


--
-- Data for Name: ai_service; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.ai_service (id, model_id, service_name, server_ip, port, inference_endpoint, status, mac_address, deploy_time, last_heartbeat, process_id, log_path, model_version, format, created_at, updated_at, node_id) FROM stdin;
1	3	model_3_pytorch_1.0.1	192.168.11.28	9999	http://192.168.11.28:9999/inference	stopped	30:c1:05:16:5a:68	2025-11-23 05:03:15.111839	2025-12-11 14:34:14.839699	1252756	/opt/projects/easyaiot/AI/logs/1	1.0.1	pytorch	2025-11-23 05:03:15.113205	2025-12-11 14:34:14.839944	\N
\.


--
-- Data for Name: auto_label_model_history; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.auto_label_model_history (id, dataset_id, model_id, train_task_id, source_model_id, version_no, annotated_count, class_names, map50, status, trigger_source, error_message, created_at, completed_at) FROM stdin;
\.


--
-- Data for Name: auto_label_result; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.auto_label_result (id, task_id, dataset_image_id, annotations, status, error_message, created_at) FROM stdin;
\.


--
-- Data for Name: auto_label_subtask; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.auto_label_subtask (id, parent_task_id, dataset_id, frame_task_id, frame_task_name, rtmp_url, subtask_type, status, queue_position, assigned_node_id, assigned_node_host, workload_id, captured_count, labeled_count, failed_count, processed_images, error_message, config_json, created_at, updated_at, started_at, completed_at) FROM stdin;
\.


--
-- Data for Name: auto_label_task; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.auto_label_task (id, dataset_id, model_service_id, status, total_images, processed_images, success_count, failed_count, confidence_threshold, created_at, updated_at, started_at, completed_at, error_message, model_id, label_mode, text_prompts, annotation_type, phase, bootstrap_limit, bootstrap_selection, review_passed, return_masks, pipeline_config, execution_mode, queue_priority, selected_frame_task_ids) FROM stdin;
\.


--
-- Data for Name: export_record; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.export_record (id, model_id, model_name, format, minio_path, local_path, created_at, status, message) FROM stdin;
1	3	安全帽模型	onnx	exports/model_3/onnx/model.onnx	/tmp/tmp6ae5jrr1/model.onnx	2025-11-22 18:05:20.113985	COMPLETED	\N
\.


--
-- Data for Name: inference_task; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.inference_task (id, model_id, inference_type, input_source, output_path, processed_frames, start_time, end_time, status, error_message, processing_time, stream_output_url) FROM stdin;
12	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/97f79981259c4172b8a7cb09a0418b5e.png	/api/v1/buckets/inference-results/objects/download?prefix=images/20251122/result_12_ff6332eb.jpg	\N	2025-11-22 13:35:51.046862	2025-11-22 13:35:51.362978	COMPLETED	\N	0.3048872947692871	\N
13	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/9551a746273a479a80c4223d9866ff94.png	/api/v1/buckets/inference-results/objects/download?prefix=images/20251122/result_13_8deb830f.jpg	\N	2025-11-22 13:37:30.909706	2025-11-22 13:37:31.235971	COMPLETED	\N	0.3189702033996582	\N
14	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/09224a512ef9477e9f7e8697e163e2f7.png	\N	\N	2025-11-22 13:38:21.779117	\N	PROCESSING	\N	\N	\N
5	\N	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/d55a99a0e09c4a7a9a3f005a678b8161.jpg	/api/v1/buckets/inference-results/objects/download?prefix=images/20251122/result_5_9d1d9883.jpg	\N	2025-11-22 13:24:18.255712	2025-11-22 13:24:20.018554	COMPLETED	\N	1.567838430404663	\N
6	\N	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/35faf43d5284438d94507f6ae0419ed8.jpg	/api/v1/buckets/inference-results/objects/download?prefix=images/20251122/result_6_1fd63e8c.jpg	\N	2025-11-22 13:31:29.061454	2025-11-22 13:31:30.709686	COMPLETED	\N	1.4649066925048828	\N
24	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/869b97f0d7a14f70ad31d41dd1e32b38.png	\N	\N	2025-11-22 22:50:26.04244	2025-11-23 06:50:26.201653	COMPLETED	\N	\N	\N
7	\N	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/6ec437c90bf449d2bbd342ff5f166172.jpg	/api/v1/buckets/inference-results/objects/download?prefix=images/20251122/result_7_5fb72782.jpg	\N	2025-11-22 13:32:46.677446	2025-11-22 13:32:46.921912	COMPLETED	\N	0.23665499687194824	\N
15	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/c405d0a6d8174a37814dea4006b06768.png	/api/v1/buckets/inference-results/objects/download?prefix=images/20251122/result_15_51492fd9.jpg	\N	2025-11-22 13:47:51.393502	2025-11-22 13:47:51.863136	COMPLETED	\N	0.1776888370513916	\N
8	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/756b47a43b39479baf9ccfa8d2dbc629.jpg	/api/v1/buckets/inference-results/objects/download?prefix=images/20251122/result_8_0bfb59c5.jpg	\N	2025-11-22 13:32:58.8858	2025-11-22 13:32:59.126101	COMPLETED	\N	0.23288822174072266	\N
9	\N	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/d7a582924b4c418d937af12ed1413e33.jpg	/api/v1/buckets/inference-results/objects/download?prefix=images/20251122/result_9_21f3d6c7.jpg	\N	2025-11-22 13:33:05.355347	2025-11-22 13:33:05.559702	COMPLETED	\N	0.19696044921875	\N
10	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/e295a143359e4ace81d7ac7e3ae0844c.png	/api/v1/buckets/inference-results/objects/download?prefix=images/20251122/result_10_acc89f28.jpg	\N	2025-11-22 13:33:51.572976	2025-11-22 13:33:51.976791	COMPLETED	\N	0.39517951011657715	\N
16	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/c405d0a6d8174a37814dea4006b06768.png	/api/v1/buckets/inference-results/objects/download?prefix=images/20251123/result_16_285a495d.jpg	\N	2025-11-22 22:21:57.350817	2025-11-22 22:21:57.943056	COMPLETED	\N	0.19422173500061035	\N
11	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/c9d656634bb04a1e9d4ffb8cbd92e741.png	/api/v1/buckets/inference-results/objects/download?prefix=images/20251122/result_11_d3038b15.jpg	\N	2025-11-22 13:34:44.1771	2025-11-22 13:34:44.493716	COMPLETED	\N	0.30571866035461426	\N
25	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/46d1c88dbe9f429fb4d815ab01b2bb52.png	\N	\N	2025-11-22 22:50:34.033708	2025-11-23 06:50:34.132165	COMPLETED	\N	\N	\N
17	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/c405d0a6d8174a37814dea4006b06768.png	\N	\N	2025-11-22 22:27:05.867743	\N	PROCESSING	\N	\N	\N
18	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/c405d0a6d8174a37814dea4006b06768.png	\N	\N	2025-11-22 22:30:02.783731	2025-11-23 06:30:02.857539	ERROR	\N	\N	\N
19	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/c405d0a6d8174a37814dea4006b06768.png	\N	\N	2025-11-22 22:30:15.077538	2025-11-23 06:30:15.092021	ERROR	\N	\N	\N
20	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/c405d0a6d8174a37814dea4006b06768.png	\N	\N	2025-11-22 22:30:21.81459	2025-11-23 06:30:21.823677	ERROR	\N	\N	\N
21	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/c405d0a6d8174a37814dea4006b06768.png	\N	\N	2025-11-22 22:32:30.27677	2025-11-23 06:32:30.351547	ERROR	\N	\N	\N
22	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/c405d0a6d8174a37814dea4006b06768.png	\N	\N	2025-11-22 22:34:16.776372	2025-11-23 06:34:16.843811	ERROR	\N	\N	\N
23	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/c405d0a6d8174a37814dea4006b06768.png	\N	\N	2025-11-22 22:35:15.264173	2025-11-23 06:35:15.338838	ERROR	\N	\N	\N
26	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/b19cf8a1e1aa4da58dcf66806c176706.png	\N	\N	2025-11-22 22:50:38.406646	2025-11-23 06:50:38.505742	COMPLETED	\N	\N	\N
27	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/d86fbae719d946b4b4c5ac8267b674b1.png	\N	\N	2025-11-22 22:50:47.015527	2025-11-23 06:50:47.115502	COMPLETED	\N	\N	\N
28	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/c405d0a6d8174a37814dea4006b06768.png	/api/v1/buckets/inference-results/objects/download?prefix=images/20251123/result_28_e66cf928.jpg	\N	2025-11-22 22:55:33.443615	2025-11-23 06:55:33.638641	COMPLETED	\N	\N	\N
29	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/c405d0a6d8174a37814dea4006b06768.png	/api/v1/buckets/inference-results/objects/download?prefix=images/20251123/result_29_e2dc8ad0.jpg	\N	2025-11-22 22:55:38.435985	2025-11-23 06:55:38.574764	COMPLETED	\N	\N	\N
30	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/c405d0a6d8174a37814dea4006b06768.png	/api/v1/buckets/inference-results/objects/download?prefix=images/20251123/result_30_5499fb6d.jpg	\N	2025-11-22 22:55:39.603581	2025-11-23 06:55:39.726827	COMPLETED	\N	\N	\N
31	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/c405d0a6d8174a37814dea4006b06768.png	/api/v1/buckets/inference-results/objects/download?prefix=images/20251123/result_31_47464a8d.jpg	\N	2025-11-22 22:55:40.67445	2025-11-23 06:55:40.807798	COMPLETED	\N	\N	\N
32	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/c405d0a6d8174a37814dea4006b06768.png	/api/v1/buckets/inference-results/objects/download?prefix=images/20251123/result_32_473b42d5.jpg	\N	2025-11-22 22:55:41.379191	2025-11-23 06:55:41.502433	COMPLETED	\N	\N	\N
33	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/c405d0a6d8174a37814dea4006b06768.png	/api/v1/buckets/inference-results/objects/download?prefix=images/20251123/result_33_82c08bd0.jpg	\N	2025-11-22 22:55:42.104878	2025-11-23 06:55:42.221021	COMPLETED	\N	\N	\N
34	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/c405d0a6d8174a37814dea4006b06768.png	/api/v1/buckets/inference-results/objects/download?prefix=images/20251123/result_34_4103362f.jpg	\N	2025-11-22 22:55:42.779004	2025-11-23 06:55:42.909297	COMPLETED	\N	\N	\N
35	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/c405d0a6d8174a37814dea4006b06768.png	/api/v1/buckets/inference-results/objects/download?prefix=images/20251123/result_35_cdac3f0e.jpg	\N	2025-11-22 22:55:43.372022	2025-11-23 06:55:43.502743	COMPLETED	\N	\N	\N
36	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/c405d0a6d8174a37814dea4006b06768.png	/api/v1/buckets/inference-results/objects/download?prefix=images/20251123/result_36_af387902.jpg	\N	2025-11-22 22:55:43.958558	2025-11-23 06:55:44.084102	COMPLETED	\N	\N	\N
37	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/c405d0a6d8174a37814dea4006b06768.png	/api/v1/buckets/inference-results/objects/download?prefix=images/20251123/result_37_0ffbc073.jpg	\N	2025-11-22 22:55:44.545542	2025-11-23 06:55:44.677737	COMPLETED	\N	\N	\N
38	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/c405d0a6d8174a37814dea4006b06768.png	/api/v1/buckets/inference-results/objects/download?prefix=images/20251123/result_38_943c59ff.jpg	\N	2025-11-22 22:56:09.509901	2025-11-23 06:56:09.639508	COMPLETED	\N	\N	\N
39	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/c405d0a6d8174a37814dea4006b06768.png	/api/v1/buckets/inference-results/objects/download?prefix=images/20251123/result_39_9b601d9c.jpg	\N	2025-11-22 22:56:15.121054	2025-11-23 06:56:15.25198	COMPLETED	\N	\N	\N
40	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/c405d0a6d8174a37814dea4006b06768.png	/api/v1/buckets/inference-results/objects/download?prefix=images/20251123/result_40_34504642.jpg	\N	2025-11-22 22:56:15.79304	2025-11-23 06:56:15.918662	COMPLETED	\N	\N	\N
41	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/c405d0a6d8174a37814dea4006b06768.png	/api/v1/buckets/inference-results/objects/download?prefix=images/20251123/result_41_3daf3a3f.jpg	\N	2025-11-22 22:56:16.407021	2025-11-23 06:56:16.538936	COMPLETED	\N	\N	\N
42	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/c405d0a6d8174a37814dea4006b06768.png	/api/v1/buckets/inference-results/objects/download?prefix=images/20251123/result_42_a1bca067.jpg	\N	2025-11-22 22:56:17.032805	2025-11-23 06:56:17.175501	COMPLETED	\N	\N	\N
43	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/c405d0a6d8174a37814dea4006b06768.png	/api/v1/buckets/inference-results/objects/download?prefix=images/20251123/result_43_bbb6ddd4.jpg	\N	2025-11-22 23:00:01.759607	2025-11-23 07:00:01.957136	COMPLETED	\N	\N	\N
44	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/c405d0a6d8174a37814dea4006b06768.png	/api/v1/buckets/inference-results/objects/download?prefix=images/20251123/result_44_07320916.jpg	\N	2025-11-22 23:00:02.45676	2025-11-23 07:00:02.594548	COMPLETED	\N	\N	\N
45	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/c405d0a6d8174a37814dea4006b06768.png	/api/v1/buckets/inference-results/objects/download?prefix=images/20251123/result_45_adb71918.jpg	\N	2025-11-22 23:00:03.113754	2025-11-23 07:00:03.247906	COMPLETED	\N	\N	\N
46	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/c405d0a6d8174a37814dea4006b06768.png	/api/v1/buckets/inference-results/objects/download?prefix=images/20251123/result_46_c1932a29.jpg	\N	2025-11-22 23:00:03.608591	2025-11-23 07:00:03.740103	COMPLETED	\N	\N	\N
47	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/c405d0a6d8174a37814dea4006b06768.png	/api/v1/buckets/inference-results/objects/download?prefix=images/20251123/result_47_d6dc5cf1.jpg	\N	2025-11-22 23:00:04.173032	2025-11-23 07:00:04.297782	COMPLETED	\N	\N	\N
48	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/c405d0a6d8174a37814dea4006b06768.png	/api/v1/buckets/inference-results/objects/download?prefix=images/20251123/result_48_da725fd0.jpg	\N	2025-11-22 23:00:04.718485	2025-11-23 07:00:04.853562	COMPLETED	\N	\N	\N
49	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/c405d0a6d8174a37814dea4006b06768.png	/api/v1/buckets/inference-results/objects/download?prefix=images/20251123/result_49_928b5f21.jpg	\N	2025-11-22 23:00:05.252675	2025-11-23 07:00:05.385457	COMPLETED	\N	\N	\N
50	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/c405d0a6d8174a37814dea4006b06768.png	/api/v1/buckets/inference-results/objects/download?prefix=images/20251123/result_50_053bfecb.jpg	\N	2025-11-22 23:00:05.805926	2025-11-23 07:00:05.943561	COMPLETED	\N	\N	\N
51	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/c405d0a6d8174a37814dea4006b06768.png	/api/v1/buckets/inference-results/objects/download?prefix=images/20251123/result_51_632d2674.jpg	\N	2025-11-22 23:00:06.396758	2025-11-23 07:00:06.536643	COMPLETED	\N	\N	\N
52	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/c405d0a6d8174a37814dea4006b06768.png	/api/v1/buckets/inference-results/objects/download?prefix=images/20251123/result_52_a0c4988b.jpg	\N	2025-11-22 23:00:06.930948	2025-11-23 07:00:07.065988	COMPLETED	\N	\N	\N
53	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/c405d0a6d8174a37814dea4006b06768.png	/api/v1/buckets/inference-results/objects/download?prefix=images/20251123/result_53_cba37c65.jpg	\N	2025-11-22 23:00:07.529188	2025-11-23 07:00:07.672544	COMPLETED	\N	\N	\N
54	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/c405d0a6d8174a37814dea4006b06768.png	/api/v1/buckets/inference-results/objects/download?prefix=images/20251123/result_54_b0e652ad.jpg	\N	2025-11-22 23:00:08.050989	2025-11-23 07:00:08.18449	COMPLETED	\N	\N	\N
55	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/5cc2477c48e0445593df8b8598571f20.png	/api/v1/buckets/inference-results/objects/download?prefix=images/20251123/result_55_66578186.jpg	\N	2025-11-22 23:25:45.133941	2025-11-22 23:25:45.540071	COMPLETED	\N	0.2248547077178955	\N
56	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/6cee2c48d42f4c4a865f6cc750700319.png	/api/v1/buckets/inference-results/objects/download?prefix=images/20251123/result_56_4a376234.jpg	\N	2025-11-22 23:25:52.122922	2025-11-22 23:25:52.307409	COMPLETED	\N	0.17902803421020508	\N
57	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/c9c68e2bbe024695bbe222e2adc5c048.jpg	/api/v1/buckets/inference-results/objects/download?prefix=images/20251211/result_57_7bd94791.jpg	\N	2025-12-11 05:59:24.144816	2025-12-11 13:59:26.372638	COMPLETED	\N	\N	\N
58	\N	video	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/89e7e1bb332946ab87e5e0a4dd7a68af.mp4	/api/v1/buckets/inference-results/objects/download?prefix=videos/20251211/processed_58_1765436363.mp4	1800	2025-12-11 06:58:20.239395	2025-12-11 06:59:23.23634	COMPLETED	\N	59.400715827941895	\N
59	\N	video	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/e4ae017b561c4d44b79d78714a11ff3a.mp4	/api/v1/buckets/inference-results/objects/download?prefix=videos/20251211/processed_59_1765436406.mp4	1800	2025-12-11 06:58:56.505407	2025-12-11 07:00:06.843887	COMPLETED	\N	66.74621534347534	\N
60	3	image	/api/v1/buckets/inference-inputs/objects/download?prefix=inputs/002b8a14fec645bc98e6bcf39c9b5457.jpg	/api/v1/buckets/inference-results/objects/download?prefix=images/20260618/result_60_17684d53.jpg	\N	2026-06-18 10:23:10.799052	2026-06-18 10:23:10.995147	COMPLETED	\N	0.1808302402496338	\N
\.


--
-- Data for Name: llm_config; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.llm_config (id, name, service_type, vendor, model_type, model_name, base_url, api_key, api_version, temperature, max_tokens, timeout, is_active, status, last_test_time, last_test_result, description, icon_url, created_at, updated_at) FROM stdin;
2	QwenVL3视觉模型	online	aliyun	vision	qwen-vl-max	https://dashscope.aliyuncs.com/compatible-mode/v1	sk-xxxxxxxxxxxxxxxxxxx	\N	0.7	2000	60	t	active	2025-12-11 08:50:54.524481	{"success": false, "message": "连接测试失败: 404", "error": ""}	\N	/api/v1/buckets/models/objects/download?prefix=llm_images/0931043a235948cd8e4765455b7c5316.png	2025-12-11 07:43:43.887508	2025-12-11 11:26:41.294643
\.


--
-- Data for Name: llm_deploy_service; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.llm_deploy_service (id, service_name, qwen_model_key, hf_model_id, node_id, server_ip, port, api_endpoint, tensor_parallel_size, max_model_len, status, llm_config_id, process_id, log_path, error_message, deploy_time, last_heartbeat, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: model; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.model (id, name, description, model_path, image_url, version, created_at, updated_at, onnx_model_path, torchscript_model_path, tensorrt_model_path, openvino_model_path, rknn_model_path, status, class_names, selected_class_names, model_origin, origin_ref) FROM stdin;
6	睡岗模型	识别在岗位睡觉的模型	/api/v1/buckets/models/objects/download?prefix=yolo/yolov8/21f8ba84e4e64d9a9de924d3eb246033.pt	/api/v1/buckets/models/objects/download?prefix=images/3e03ffae14114b29867b1dad357e9e23.png	1.0.0	2025-11-22 23:27:35.012975	2025-11-22 23:27:35.012977	\N	\N	\N	\N	\N	0	\N	\N	upload	\N
1	人模型	用于识别人的AI算法	/api/v1/buckets/models/objects/download?prefix=yolo/yolov11/362479958ba04288b42ab1796f9afa57.pt	/api/v1/buckets/models/objects/download?prefix=images/69707887371944979f0fa32091e46b11.jpg	1.0.0	2025-08-25 10:37:44.147967	2025-11-22 23:31:45.752278	\N	\N	\N	\N	\N	0	\N	\N	upload	\N
5	反光衣模型	识别反光衣的模型	/api/v1/buckets/models/objects/download?prefix=yolo/yolov8/c7b364e123a84f70a954403399c61dac.pt	/api/v1/buckets/models/objects/download?prefix=images/a36ab47d67044d6eb07d58aa399bd78b.png	1.0.0	2025-11-22 23:26:47.840522	2026-05-18 09:25:45.554297	\N	\N	\N	\N	\N	0	\N	\N	upload	\N
7	火焰模型	识别火焰的模型	/api/v1/buckets/models/objects/download?prefix=yolo/yolov8/df55c892173c4f3e96b3462e833f0e75.pt	/api/v1/buckets/models/objects/download?prefix=images/d81d3fe5476e4701a34b94e07cdc2820.png	1.0.0	2025-11-22 23:29:18.785875	2026-05-18 09:26:28.338878	\N	\N	\N	\N	\N	0	\N	\N	upload	\N
8	吸烟模型	用于识别吸烟的模型	/api/v1/buckets/models/objects/download?prefix=yolo/yolov8/baaab3e73fd74064ae42d57b0e170663.pt	/api/v1/buckets/models/objects/download?prefix=images/96e7070b3102445cb9f948849677d1ea.png	1.0.0	2025-11-22 23:30:37.986784	2026-05-18 09:26:54.353864	\N	\N	\N	\N	\N	0	\N	\N	upload	\N
10	打电话模型	用于识别打电话的模型	/api/v1/buckets/models/objects/download?prefix=yolo/yolov8/onnx/6e25627aa8434831b4ddcee194b8be59.onnx	/api/v1/buckets/models/objects/download?prefix=images/ac4cdfd5ee5a4283a951d19cdf92e9e5.png	v1.0.0	2026-05-18 09:29:56.19438	2026-05-18 09:29:56.194384	\N	\N	\N	\N	\N	0	\N	\N	upload	\N
12	道路积水模型	识别道路积水的模型	/api/v1/buckets/models/objects/download?prefix=yolo/yolov8/onnx/f4e85385c70049efbf6bb748d2e2746f.onnx	/api/v1/buckets/models/objects/download?prefix=images/8153678ba3a346ae887a0a633e376217.png	v1.0.0	2026-05-18 09:35:44.770934	2026-05-18 09:35:44.770939	\N	\N	\N	\N	\N	0	\N	\N	upload	\N
11	口罩模型	用于识别口罩的模型	/api/v1/buckets/models/objects/download?prefix=yolo/yolov8/onnx/1c9a1e98bf114ffa990701292c41dd82.onnx	/api/v1/buckets/models/objects/download?prefix=images/fafd5c18743e41e2903dc9eaaa9d4722.png	v1.0.0	2026-05-18 09:33:22.887931	2026-05-18 09:35:51.370426	\N	\N	\N	\N	\N	0	\N	\N	upload	\N
13	跌倒检测模型	识别跌倒检测的模型	/api/v1/buckets/models/objects/download?prefix=yolo/yolov8/onnx/f7bd3b98d1ea476c98761b57d42f73c4.onnx	/api/v1/buckets/models/objects/download?prefix=images/283c519096264729b82ac8f413ebf8a0.png	v1.0.0	2026-05-19 01:14:05.336851	2026-05-19 01:14:05.336854	\N	\N	\N	\N	\N	0	\N	\N	upload	\N
14	人脸检测模型	识别人脸的模型	/api/v1/buckets/models/objects/download?prefix=yolo/yolov8/onnx/573ce175b4134208aa03d8bacfc76a4d.onnx	/api/v1/buckets/models/objects/download?prefix=images/77a9217ff3a048b1a1b672a105b18caf.png	v1.0.0	2026-05-19 01:16:50.221649	2026-05-19 01:16:50.221654	\N	\N	\N	\N	\N	0	\N	\N	upload	\N
9	车牌模型	用于识别车牌的模型	/api/v1/buckets/models/objects/download?prefix=yolo/yolov8/onnx/974487e51ee649b69bbdf691545976cd.onnx	/api/v1/buckets/models/objects/download?prefix=images/47e184f6949c4001b46e93a36259c750.png	v1.0.0	2026-05-18 08:59:45.326275	2026-05-19 01:48:52.320976	\N	\N	\N	\N	\N	0	\N	\N	upload	\N
3	安全帽模型	识别安全帽的模型	/api/v1/buckets/models/objects/download?prefix=yolo/yolov8/9e75951cea044845be8f8f1f2223c551.pt	/api/v1/buckets/models/objects/download?prefix=images/7e6ef2e33af64a18add7f91a66b6403e.jpg	1.0.1	2025-11-22 08:33:51.975637	2026-06-18 10:22:43.139583	exports/model_3/onnx/model.onnx	\N	\N	exports/model_3/openvino/model_openvino_model/	\N	0	["head", "safehat"]	["head", "safehat"]	upload	\N
\.


--
-- Data for Name: ocr_result; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.ocr_result (id, text, confidence, bbox, polygon, page_num, line_num, word_num, image_url, created_at) FROM stdin;
\.


--
-- Data for Name: plate_algorithm_version; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.plate_algorithm_version (id, version, description, base_model, model_path, metrics_path, train_results_path, status, is_active, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: plate_dataset; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.plate_dataset (id, name, description, dataset_source, source_type, status, merged_from, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: plate_inference_task; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.plate_inference_task (id, version_id, status, input_source, output_image_path, output_json_path, detection_count, result_preview, error_message, processing_time, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: plate_train_task; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.plate_train_task (id, version_id, status, progress, dataset_source, dataset_local_path, normalized_data_yaml, hyperparameters, train_log, error_message, minio_model_path, metrics_path, train_results_path, start_time, end_time, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: sam_inference_result; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.sam_inference_result (id, prompt_type, prompt_data, image_url, result_data, model_type, inference_ms, created_at) FROM stdin;
\.


--
-- Data for Name: speech_record; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.speech_record (id, order_id, audio_file_path, filename, file_size, duration, recognized_text, confidence, status, created_at, completed_at, error_message) FROM stdin;
\.


--
-- Data for Name: train_task; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.train_task (id, model_id, progress, dataset_path, hyperparameters, start_time, end_time, status, train_log, checkpoint_dir, metrics_path, minio_model_path, train_results_path, name, dataset_name, dataset_version, schedule_policy, target_node_id, node_id, service_server_ip, service_process_id) FROM stdin;
8	1	10	/api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip	{"epochs": 100, "model_arch": "model/yolov8n.pt", "img_size": 640, "batch_size": 16, "use_gpu": true}	2025-08-30 04:36:01.576862	\N	error	[2025-08-30 12:36:27] 开始准备训练数据，项目ID: 1\n[2025-08-30 12:37:01] 获取项目信息成功，项目名称: 人模型\n[2025-08-30 12:37:14] 数据集验证成功，使用原始路径: /api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip\n[2025-08-30 12:37:15] 项目目录: /projects/easyaiot/AI/data/datasets/1\n[2025-08-30 12:37:21] 数据配置文件路径: /projects/easyaiot/AI/data/datasets/1/data.yaml\n[2025-08-30 12:37:22] 检查数据集配置文件...\n[2025-08-30 12:37:53] 加载预训练YOLOv8模型...\n[2025-08-30 12:37:56] 尝试加载预训练模型: /projects/easyaiot/AI/model/yolov8n.pt\n[2025-08-30 12:38:08] 预训练模型加载失败: PytorchStreamReader failed reading zip archive: invalid header or archive is corrupted\n		\N	\N	\N	\N	\N	\N	local	\N	\N	\N	\N
10	1	10	/api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip	{"epochs": 100, "model_arch": "model/yolov8n.pt", "img_size": 640, "batch_size": 16, "use_gpu": true}	2025-08-30 04:43:39.87098	\N	error	[2025-08-30 12:43:40] 开始准备训练数据，项目ID: 1\n[2025-08-30 12:43:41] 获取项目信息成功，项目名称: 人模型\n[2025-08-30 12:43:41] 数据集验证成功，使用原始路径: /api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip\n[2025-08-30 12:43:41] 项目目录: /projects/easyaiot/AI/data/datasets/1\n[2025-08-30 12:43:41] 数据配置文件路径: /projects/easyaiot/AI/data/datasets/1/data.yaml\n[2025-08-30 12:43:41] 检查数据集配置文件...\n[2025-08-30 12:43:41] 加载预训练YOLOv8模型...\n[2025-08-30 12:43:41] 尝试加载预训练模型: /projects/easyaiot/AI/model/yolov8n.pt\n[2025-08-30 12:43:41] 预训练模型加载失败: PytorchStreamReader failed reading zip archive: invalid header or archive is corrupted\n		\N	\N	\N	\N	\N	\N	local	\N	\N	\N	\N
9	1	10	/api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip	{"epochs": 100, "model_arch": "model/yolov8n.pt", "img_size": 640, "batch_size": 16, "use_gpu": true}	2025-08-30 04:42:51.803234	\N	error	[2025-08-30 12:42:57] 开始准备训练数据，项目ID: 1\n[2025-08-30 12:42:57] 获取项目信息成功，项目名称: 人模型\n[2025-08-30 12:42:58] 数据集验证成功，使用原始路径: /api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip\n[2025-08-30 12:42:58] 项目目录: /projects/easyaiot/AI/data/datasets/1\n[2025-08-30 12:42:58] 数据配置文件路径: /projects/easyaiot/AI/data/datasets/1/data.yaml\n[2025-08-30 12:42:58] 检查数据集配置文件...\n[2025-08-30 12:42:58] 加载预训练YOLOv8模型...\n[2025-08-30 12:42:58] 尝试加载预训练模型: /projects/easyaiot/AI/model/yolov8n.pt\n[2025-08-30 12:43:01] 预训练模型文件不存在: /projects/easyaiot/AI/model/yolov8n.pt\n		\N	\N	\N	\N	\N	\N	local	\N	\N	\N	\N
13	1	10	/api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip	{"epochs": 100, "model_arch": "model/yolov8n.pt", "img_size": 640, "batch_size": 16, "use_gpu": true}	2025-08-30 04:52:34.809657	\N	error	[2025-08-30 12:52:35] 开始准备训练数据，项目ID: 1\n[2025-08-30 12:52:36] 获取项目信息成功，项目名称: 人模型\n[2025-08-30 12:52:36] 数据集验证成功，使用原始路径: /api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip\n[2025-08-30 12:52:36] 项目目录: /projects/easyaiot/AI/data/datasets/1\n[2025-08-30 12:52:36] 数据配置文件路径: /projects/easyaiot/AI/data/datasets/1/data.yaml\n[2025-08-30 12:52:36] 检查数据集配置文件...\n[2025-08-30 12:52:36] 加载预训练YOLOv8模型...\n[2025-08-30 12:52:36] 尝试加载预训练模型: /projects/easyaiot/AI/model/yolov8n.pt\n[2025-08-30 12:52:36] 预训练模型加载失败: PytorchStreamReader failed reading zip archive: invalid header or archive is corrupted\n		\N	\N	\N	train_13	\N	\N	local	\N	\N	\N	\N
14	1	10	/api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip	{"epochs": 100, "model_arch": "model/yolov8n.pt", "img_size": 640, "batch_size": 16, "use_gpu": true}	2025-08-30 04:57:12.432184	\N	error	[2025-08-30 12:57:13] 开始准备训练数据，项目ID: 1\n[2025-08-30 12:57:13] 获取项目信息成功，项目名称: 人模型\n[2025-08-30 12:57:13] 数据集验证成功，使用原始路径: /api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip\n[2025-08-30 12:57:13] 项目目录: /projects/easyaiot/AI/data/datasets/1\n[2025-08-30 12:57:14] 数据配置文件路径: /projects/easyaiot/AI/data/datasets/1/data.yaml\n[2025-08-30 12:57:14] 检查数据集配置文件...\n[2025-08-30 12:57:14] 加载预训练YOLOv8模型...\n[2025-08-30 12:57:14] 尝试加载预训练模型: /projects/easyaiot/AI/model/yolov8n.pt\n[2025-08-30 12:57:14] 预训练模型加载失败: PytorchStreamReader failed reading zip archive: invalid header or archive is corrupted\n		\N	\N	\N	train_14	\N	\N	local	\N	\N	\N	\N
17	1	100	/api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip	{"epochs": 100, "model_arch": "model/yolov8n.pt", "img_size": 640, "batch_size": 16, "use_gpu": true}	2025-08-30 05:04:36.030287	2025-08-30 05:07:08.50721	completed	[2025-08-30 13:04:37] 开始准备训练数据，项目ID: 1\n[2025-08-30 13:04:37] 获取项目信息成功，项目名称: 人模型\n[2025-08-30 13:04:37] 数据集验证成功，使用原始路径: /api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip\n[2025-08-30 13:04:37] 项目目录: /projects/easyaiot/AI/data/datasets/1\n[2025-08-30 13:04:37] 数据配置文件路径: /projects/easyaiot/AI/data/datasets/1/data.yaml\n[2025-08-30 13:04:37] 检查数据集配置文件...\n[2025-08-30 13:04:37] 加载预训练YOLOv8模型...\n[2025-08-30 13:04:37] 尝试加载预训练模型: /projects/easyaiot/AI/model/yolov8n.pt\n[2025-08-30 13:04:38] 预训练模型加载成功! 模型路径: /projects/easyaiot/AI/model/yolov8n.pt\n[2025-08-30 13:04:38] 开始训练模型，共100个epochs...\n[2025-08-30 13:04:38] 开始训练模型，配置: 数据文件=/projects/easyaiot/AI/data/datasets/1/data.yaml, epochs=100, 图像尺寸=640x640, 批次大小=16\n[2025-08-30 13:04:38] GPU状态检查: {\n  "pytorch_version": "2.0.1+cu117",\n  "cuda_available": true,\n  "cuda_version": "11.7",\n  "device_count": 1,\n  "device_0_name": "NVIDIA RTX A5000",\n  "device_0_capability": [\n    8,\n    6\n  ]\n}\n[2025-08-30 13:04:38] 使用GPU进行训练: NVIDIA RTX A5000\n[2025-08-30 13:06:59] 训练结果CSV已上传至Minio: /api/v1/buckets/model-train/objects/download?prefix=models/model_1/train_17/results.csv\n[2025-08-30 13:07:00] 训练结果图表已上传至Minio: /api/v1/buckets/model-train/objects/download?prefix=models/model_1/train_17/results.png\n[2025-08-30 13:07:00] 训练完成，正在保存结果...\n[2025-08-30 13:07:01] 模型训练完成!\n[2025-08-30 13:07:01] 训练结果保存路径: /projects/easyaiot/AI/data/datasets/1/train_results\n[2025-08-30 13:07:01] 检查最佳模型文件是否存在: /projects/easyaiot/AI/data/datasets/1/train_results/weights/best.pt\n[2025-08-30 13:07:01] 找到最佳模型文件，开始复制到保存目录: /projects/easyaiot/AI/data/datasets/1/train_results/weights/best.pt\n[2025-08-30 13:07:01] 模型文件已成功复制到保存目录: /projects/easyaiot/AI/static/models/1/train/weights\n[2025-08-30 13:07:01] 开始上传最佳模型到Minio...\n[2025-08-30 13:07:08] 模型已成功上传至Minio: /api/v1/buckets/models/objects/download?prefix=models/model_1/train_17/best.pt\n[2025-08-30 13:07:08] 训练日志已上传至Minio: /api/v1/buckets/log-bucket/objects/download?prefix=logs/model_1/train_17.txt\n[2025-08-30 13:07:08] 模型训练完成并已保存\n	/projects/easyaiot/AI/data/datasets/1/train_results/checkpoints	/api/v1/buckets/model-train/objects/download?prefix=models/model_1/train_17/results.csv	/api/v1/buckets/models/objects/download?prefix=models/model_1/train_17/best.pt	/api/v1/buckets/model-train/objects/download?prefix=models/model_1/train_17/results.png	train_17	\N	\N	local	\N	\N	\N	\N
7	1	10	/api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip	{"epochs": 100, "model_arch": "model/yolov8n.pt", "img_size": 640, "batch_size": 16, "use_gpu": true}	2025-08-30 04:32:47.695145	2026-06-11 02:43:37.275729	error	[2025-08-30 12:32:48] 开始准备训练数据，项目ID: 1\n[2025-08-30 12:32:48] 获取项目信息成功，项目名称: 人模型\n[2025-08-30 12:32:48] 数据集验证成功，使用原始路径: /api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip\n[2025-08-30 12:32:49] 项目目录: /projects/easyaiot/AI/data/datasets/1\n[2025-08-30 12:32:49] 数据配置文件路径: /projects/easyaiot/AI/data/datasets/1/data.yaml\n[2025-08-30 12:32:49] 检查数据集配置文件...\n[2025-08-30 12:32:49] 加载预训练YOLOv8模型...\n[2025-08-30 12:32:49] 尝试加载预训练模型: /projects/easyaiot/AI/model/yolov8n.pt\n[2026-06-11 10:43:37] 训练进程因服务重启或异常退出而中断。未找到可用断点，请重新训练。\n		\N	\N	\N	\N	\N	\N	local	\N	\N	\N	\N
20	1	100	/api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip	{"epochs": 100, "model_arch": "yolov8n.pt", "img_size": 640, "batch_size": 16, "use_gpu": true}	2025-08-30 05:13:49.213499	2025-08-30 05:15:25.148511	completed	[2025-08-30 13:13:50] 开始准备训练数据，项目ID: 1\n[2025-08-30 13:13:50] 获取项目信息成功，项目名称: 人模型\n[2025-08-30 13:13:50] 数据集验证成功，使用原始路径: /api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip\n[2025-08-30 13:13:50] 项目目录: /projects/easyaiot/AI/data/datasets/1\n[2025-08-30 13:13:50] 数据配置文件路径: /projects/easyaiot/AI/data/datasets/1/data.yaml\n[2025-08-30 13:13:50] 检查数据集配置文件...\n[2025-08-30 13:13:51] 加载预训练YOLOv8模型...\n[2025-08-30 13:13:51] 尝试加载预训练模型: yolov8n.pt\n[2025-08-30 13:13:51] 预训练模型加载成功!\n[2025-08-30 13:13:51] 开始训练模型，共100个epochs...\n[2025-08-30 13:13:51] 开始训练模型，配置: 数据文件=/projects/easyaiot/AI/data/datasets/1/data.yaml, epochs=100, 图像尺寸=640x640, 批次大小=16\n[2025-08-30 13:13:51] GPU状态检查: {\n  "pytorch_version": "2.0.1+cu117",\n  "cuda_available": true,\n  "cuda_version": "11.7",\n  "device_count": 1,\n  "device_0_name": "NVIDIA RTX A5000",\n  "device_0_capability": [\n    8,\n    6\n  ]\n}\n[2025-08-30 13:13:52] 使用GPU进行训练: NVIDIA RTX A5000\n[2025-08-30 13:15:16] 训练结果CSV已上传至Minio: /api/v1/buckets/model-train/objects/download?prefix=models/model_1/train_20/results.csv\n[2025-08-30 13:15:17] 训练结果图表已上传至Minio: /api/v1/buckets/model-train/objects/download?prefix=models/model_1/train_20/results.png\n[2025-08-30 13:15:17] 训练完成，正在保存结果...\n[2025-08-30 13:15:18] 模型训练完成!\n[2025-08-30 13:15:18] 训练结果保存路径: /projects/easyaiot/AI/data/datasets/1/train_results\n[2025-08-30 13:15:18] 检查最佳模型文件是否存在: /projects/easyaiot/AI/data/datasets/1/train_results/weights/best.pt\n[2025-08-30 13:15:18] 找到最佳模型文件，开始复制到保存目录: /projects/easyaiot/AI/data/datasets/1/train_results/weights/best.pt\n[2025-08-30 13:15:18] 模型文件已成功复制到保存目录: /projects/easyaiot/AI/static/models/1/train/weights\n[2025-08-30 13:15:18] 开始上传最佳模型到Minio...\n[2025-08-30 13:15:24] 模型已成功上传至Minio: /api/v1/buckets/models/objects/download?prefix=models/model_1/train_20/best.pt\n[2025-08-30 13:15:25] 训练日志已上传至Minio: /api/v1/buckets/log-bucket/objects/download?prefix=logs/model_1/train_20.txt\n[2025-08-30 13:15:25] 模型训练完成并已保存\n	/projects/easyaiot/AI/data/datasets/1/train_results/checkpoints	/api/v1/buckets/model-train/objects/download?prefix=models/model_1/train_20/results.csv	/api/v1/buckets/models/objects/download?prefix=models/model_1/train_20/best.pt	/api/v1/buckets/model-train/objects/download?prefix=models/model_1/train_20/results.png	train_20	\N	\N	local	\N	\N	\N	\N
1	1	10	/api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip	{"epochs": 100, "model_arch": "model/yolov8n.pt", "img_size": 640, "batch_size": 16, "use_gpu": true, "completed_epochs": 0}	2025-08-30 04:04:49.247897	2026-06-11 02:43:37.271709	stopped	[2025-08-30 12:04:50] 开始准备训练数据，项目ID: 1\n[2025-08-30 12:04:50] 获取项目信息成功，项目名称: 人模型\n[2025-08-30 12:04:50] 数据集验证成功，使用原始路径: /api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip\n[2025-08-30 12:04:50] 项目目录: /projects/easyaiot/AI/data/datasets/1\n[2025-08-30 12:04:50] 数据配置文件路径: /projects/easyaiot/AI/data/datasets/1/data.yaml\n[2025-08-30 12:04:50] 检查数据集配置文件...\n[2025-08-30 12:04:50] 加载预训练YOLOv8模型...\n[2025-08-30 12:04:51] 尝试加载预训练模型: /projects/easyaiot/AI/model/yolov8n.pt\n[2026-06-11 10:43:37] 训练进程因服务重启或异常退出而中断。可点击「继续训练」从断点恢复。\n	/projects/easyaiot/AI/data/datasets/train_1/train_results/weights/last.pt	\N	\N	\N	\N	\N	\N	local	\N	\N	\N	\N
2	1	10	/api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip	{"epochs": 100, "model_arch": "model/yolov8n.pt", "img_size": 640, "batch_size": 16, "use_gpu": true}	2025-08-30 04:05:45.965389	2026-06-11 02:43:37.270316	error	[2025-08-30 12:05:47] 开始准备训练数据，项目ID: 1\n[2025-08-30 12:05:47] 获取项目信息成功，项目名称: 人模型\n[2025-08-30 12:05:47] 数据集验证成功，使用原始路径: /api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip\n[2025-08-30 12:05:47] 项目目录: /projects/easyaiot/AI/data/datasets/1\n[2025-08-30 12:05:47] 数据配置文件路径: /projects/easyaiot/AI/data/datasets/1/data.yaml\n[2025-08-30 12:05:47] 检查数据集配置文件...\n[2025-08-30 12:05:47] 加载预训练YOLOv8模型...\n[2025-08-30 12:05:47] 尝试加载预训练模型: /projects/easyaiot/AI/model/yolov8n.pt\n[2026-06-11 10:43:37] 训练进程因服务重启或异常退出而中断。未找到可用断点，请重新训练。\n		\N	\N	\N	\N	\N	\N	local	\N	\N	\N	\N
3	1	10	/api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip	{"epochs": 100, "model_arch": "model/yolov8n.pt", "img_size": 640, "batch_size": 16, "use_gpu": true}	2025-08-30 04:09:03.61429	2026-06-11 02:43:37.269069	error	[2025-08-30 12:09:04] 开始准备训练数据，项目ID: 1\n[2025-08-30 12:09:04] 获取项目信息成功，项目名称: 人模型\n[2025-08-30 12:09:04] 数据集验证成功，使用原始路径: /api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip\n[2025-08-30 12:09:05] 项目目录: /projects/easyaiot/AI/data/datasets/1\n[2025-08-30 12:09:05] 数据配置文件路径: /projects/easyaiot/AI/data/datasets/1/data.yaml\n[2025-08-30 12:09:05] 检查数据集配置文件...\n[2025-08-30 12:09:05] 加载预训练YOLOv8模型...\n[2025-08-30 12:09:05] 尝试加载预训练模型: /projects/easyaiot/AI/model/yolov8n.pt\n[2026-06-11 10:43:37] 训练进程因服务重启或异常退出而中断。未找到可用断点，请重新训练。\n		\N	\N	\N	\N	\N	\N	local	\N	\N	\N	\N
4	1	10	/api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip	{"epochs": 100, "model_arch": "model/yolov8n.pt", "img_size": 640, "batch_size": 16, "use_gpu": true}	2025-08-30 04:14:05.135787	2026-06-11 02:43:37.271584	error	[2025-08-30 12:14:06] 开始准备训练数据，项目ID: 1\n[2025-08-30 12:14:06] 获取项目信息成功，项目名称: 人模型\n[2025-08-30 12:14:06] 数据集验证成功，使用原始路径: /api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip\n[2025-08-30 12:14:06] 项目目录: /projects/easyaiot/AI/data/datasets/1\n[2025-08-30 12:14:06] 数据配置文件路径: /projects/easyaiot/AI/data/datasets/1/data.yaml\n[2025-08-30 12:14:06] 检查数据集配置文件...\n[2025-08-30 12:14:06] 加载预训练YOLOv8模型...\n[2025-08-30 12:14:07] 尝试加载预训练模型: /projects/easyaiot/AI/model/yolov8n.pt\n[2026-06-11 10:43:37] 训练进程因服务重启或异常退出而中断。未找到可用断点，请重新训练。\n		\N	\N	\N	\N	\N	\N	local	\N	\N	\N	\N
5	1	10	/api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip	{"epochs": 100, "model_arch": "model/yolov8n.pt", "img_size": 640, "batch_size": 16, "use_gpu": true}	2025-08-30 04:17:50.939088	2026-06-11 02:43:37.274003	error	[2025-08-30 12:17:52] 开始准备训练数据，项目ID: 1\n[2025-08-30 12:17:52] 获取项目信息成功，项目名称: 人模型\n[2025-08-30 12:17:52] 数据集验证成功，使用原始路径: /api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip\n[2025-08-30 12:17:52] 项目目录: /projects/easyaiot/AI/data/datasets/1\n[2025-08-30 12:17:52] 数据配置文件路径: /projects/easyaiot/AI/data/datasets/1/data.yaml\n[2025-08-30 12:17:52] 检查数据集配置文件...\n[2025-08-30 12:17:52] 加载预训练YOLOv8模型...\n[2025-08-30 12:17:52] 尝试加载预训练模型: /projects/easyaiot/AI/model/yolov8n.pt\n[2026-06-11 10:43:37] 训练进程因服务重启或异常退出而中断。未找到可用断点，请重新训练。\n		\N	\N	\N	\N	\N	\N	local	\N	\N	\N	\N
6	1	10	/api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip	{"epochs": 100, "model_arch": "model/yolov8n.pt", "img_size": 640, "batch_size": 16, "use_gpu": true}	2025-08-30 04:20:12.508389	2026-06-11 02:43:37.26724	error	[2025-08-30 12:20:13] 开始准备训练数据，项目ID: 1\n[2025-08-30 12:20:13] 获取项目信息成功，项目名称: 人模型\n[2025-08-30 12:20:14] 数据集验证成功，使用原始路径: /api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip\n[2025-08-30 12:20:14] 项目目录: /projects/easyaiot/AI/data/datasets/1\n[2025-08-30 12:20:14] 数据配置文件路径: /projects/easyaiot/AI/data/datasets/1/data.yaml\n[2025-08-30 12:20:14] 检查数据集配置文件...\n[2025-08-30 12:20:14] 加载预训练YOLOv8模型...\n[2025-08-30 12:20:14] 尝试加载预训练模型: /projects/easyaiot/AI/model/yolov8n.pt\n[2026-06-11 10:43:37] 训练进程因服务重启或异常退出而中断。未找到可用断点，请重新训练。\n		\N	\N	\N	\N	\N	\N	local	\N	\N	\N	\N
11	1	10	/api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip	{"epochs": 100, "model_arch": "model/yolov8n.pt", "img_size": 640, "batch_size": 16, "use_gpu": true}	2025-08-30 04:50:11.207953	2026-06-11 02:43:37.277305	error	[2025-08-30 12:50:12] 开始准备训练数据，项目ID: 1\n[2025-08-30 12:50:12] 获取项目信息成功，项目名称: 人模型\n[2025-08-30 12:50:12] 数据集验证成功，使用原始路径: /api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip\n[2025-08-30 12:50:12] 项目目录: /projects/easyaiot/AI/data/datasets/1\n[2025-08-30 12:50:12] 数据配置文件路径: /projects/easyaiot/AI/data/datasets/1/data.yaml\n[2025-08-30 12:50:12] 检查数据集配置文件...\n[2025-08-30 12:50:13] 加载预训练YOLOv8模型...\n[2025-08-30 12:50:13] 尝试加载预训练模型: /projects/easyaiot/AI/model/yolov8n.pt\n[2026-06-11 10:43:37] 训练进程因服务重启或异常退出而中断。未找到可用断点，请重新训练。\n		\N	\N	\N	\N	\N	\N	local	\N	\N	\N	\N
12	1	10	/api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip	{"epochs": 100, "model_arch": "model/yolov8n.pt", "img_size": 640, "batch_size": 16, "use_gpu": true}	2025-08-30 04:50:59.492811	2026-06-11 02:43:37.278834	error	[2025-08-30 12:51:00] 开始准备训练数据，项目ID: 1\n[2025-08-30 12:51:00] 获取项目信息成功，项目名称: 人模型\n[2025-08-30 12:51:00] 数据集验证成功，使用原始路径: /api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip\n[2025-08-30 12:51:00] 项目目录: /projects/easyaiot/AI/data/datasets/1\n[2025-08-30 12:51:01] 数据配置文件路径: /projects/easyaiot/AI/data/datasets/1/data.yaml\n[2025-08-30 12:51:01] 检查数据集配置文件...\n[2025-08-30 12:51:01] 加载预训练YOLOv8模型...\n[2025-08-30 12:51:01] 尝试加载预训练模型: /projects/easyaiot/AI/model/yolov8n.pt\n[2026-06-11 10:43:37] 训练进程因服务重启或异常退出而中断。未找到可用断点，请重新训练。\n		\N	\N	\N	\N	\N	\N	local	\N	\N	\N	\N
15	1	15	/api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip	{"epochs": 100, "model_arch": "model/yolov8n.pt", "img_size": 640, "batch_size": 16, "use_gpu": true}	2025-08-30 04:59:21.262579	2026-06-11 02:43:37.282167	error	[2025-08-30 12:59:22] 开始准备训练数据，项目ID: 1\n[2025-08-30 12:59:22] 获取项目信息成功，项目名称: 人模型\n[2025-08-30 12:59:22] 数据集验证成功，使用原始路径: /api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip\n[2025-08-30 12:59:22] 项目目录: /projects/easyaiot/AI/data/datasets/1\n[2025-08-30 12:59:22] 数据配置文件路径: /projects/easyaiot/AI/data/datasets/1/data.yaml\n[2025-08-30 12:59:22] 检查数据集配置文件...\n[2025-08-30 12:59:23] 加载预训练YOLOv8模型...\n[2025-08-30 12:59:23] 尝试加载预训练模型: /projects/easyaiot/AI/model/yolov8n.pt\n[2025-08-30 12:59:23] 预训练模型加载成功! 模型路径: /projects/easyaiot/AI/model/yolov8n.pt\n[2025-08-30 12:59:23] 开始训练模型，共100个epochs...\n[2025-08-30 12:59:23] 开始训练模型，配置: 数据文件=/projects/easyaiot/AI/data/datasets/1/data.yaml, epochs=100, 图像尺寸=640x640, 批次大小=16\n[2025-08-30 12:59:23] GPU状态检查: {\n  "pytorch_version": "2.0.1+cu117",\n  "cuda_available": true,\n  "cuda_version": "11.7",\n  "device_count": 1,\n  "device_0_name": "NVIDIA RTX A5000",\n  "device_0_capability": [\n    8,\n    6\n  ]\n}\n[2025-08-30 12:59:24] 使用GPU进行训练: NVIDIA RTX A5000\n[2026-06-11 10:43:37] 训练进程因服务重启或异常退出而中断。未找到可用断点，请重新训练。\n	/projects/easyaiot/AI/data/datasets/1/train_results/checkpoints	\N	\N	\N	train_15	\N	\N	local	\N	\N	\N	\N
16	1	15	/api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip	{"epochs": 100, "model_arch": "model/yolov8n.pt", "img_size": 640, "batch_size": 16, "use_gpu": true}	2025-08-30 05:02:37.73719	2026-06-11 02:43:37.284187	error	[2025-08-30 13:02:38] 开始准备训练数据，项目ID: 1\n[2025-08-30 13:02:38] 获取项目信息成功，项目名称: 人模型\n[2025-08-30 13:02:39] 数据集验证成功，使用原始路径: /api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip\n[2025-08-30 13:02:39] 项目目录: /projects/easyaiot/AI/data/datasets/1\n[2025-08-30 13:02:39] 数据配置文件路径: /projects/easyaiot/AI/data/datasets/1/data.yaml\n[2025-08-30 13:02:39] 检查数据集配置文件...\n[2025-08-30 13:02:39] 加载预训练YOLOv8模型...\n[2025-08-30 13:02:39] 尝试加载预训练模型: /projects/easyaiot/AI/model/yolov8n.pt\n[2025-08-30 13:02:39] 预训练模型加载成功! 模型路径: /projects/easyaiot/AI/model/yolov8n.pt\n[2025-08-30 13:02:39] 开始训练模型，共100个epochs...\n[2025-08-30 13:02:40] 开始训练模型，配置: 数据文件=/projects/easyaiot/AI/data/datasets/1/data.yaml, epochs=100, 图像尺寸=640x640, 批次大小=16\n[2025-08-30 13:02:40] GPU状态检查: {\n  "pytorch_version": "2.0.1+cu117",\n  "cuda_available": true,\n  "cuda_version": "11.7",\n  "device_count": 1,\n  "device_0_name": "NVIDIA RTX A5000",\n  "device_0_capability": [\n    8,\n    6\n  ]\n}\n[2025-08-30 13:02:40] 使用GPU进行训练: NVIDIA RTX A5000\n[2026-06-11 10:43:37] 训练进程因服务重启或异常退出而中断。未找到可用断点，请重新训练。\n	/projects/easyaiot/AI/data/datasets/1/train_results/checkpoints	\N	\N	\N	train_16	\N	\N	local	\N	\N	\N	\N
18	1	15	/api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip	{"epochs": 100, "model_arch": "model/yolov8n.pt", "img_size": 640, "batch_size": 16, "use_gpu": true}	2025-08-30 05:09:31.896726	2026-06-11 02:43:37.286034	error	[2025-08-30 13:09:33] 开始准备训练数据，项目ID: 1\n[2025-08-30 13:09:33] 获取项目信息成功，项目名称: 人模型\n[2025-08-30 13:09:33] 数据集验证成功，使用原始路径: /api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip\n[2025-08-30 13:09:33] 项目目录: /projects/easyaiot/AI/data/datasets/1\n[2025-08-30 13:09:33] 数据配置文件路径: /projects/easyaiot/AI/data/datasets/1/data.yaml\n[2025-08-30 13:09:33] 检查数据集配置文件...\n[2025-08-30 13:09:33] 加载预训练YOLOv8模型...\n[2025-08-30 13:09:33] 尝试加载预训练模型: model/yolov8n.pt\n[2025-08-30 13:09:34] 预训练模型加载成功! 模型路径: model/yolov8n.pt\n[2025-08-30 13:09:34] 开始训练模型，共100个epochs...\n[2025-08-30 13:09:34] 开始训练模型，配置: 数据文件=/projects/easyaiot/AI/data/datasets/1/data.yaml, epochs=100, 图像尺寸=640x640, 批次大小=16\n[2025-08-30 13:09:34] GPU状态检查: {\n  "pytorch_version": "2.0.1+cu117",\n  "cuda_available": true,\n  "cuda_version": "11.7",\n  "device_count": 1,\n  "device_0_name": "NVIDIA RTX A5000",\n  "device_0_capability": [\n    8,\n    6\n  ]\n}\n[2025-08-30 13:09:34] 使用GPU进行训练: NVIDIA RTX A5000\n[2026-06-11 10:43:37] 训练进程因服务重启或异常退出而中断。未找到可用断点，请重新训练。\n	/projects/easyaiot/AI/data/datasets/1/train_results/checkpoints	\N	\N	\N	train_18	\N	\N	local	\N	\N	\N	\N
19	1	10	/api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip	{"epochs": 100, "model_arch": "model/yolov8n.pt", "img_size": 640, "batch_size": 16, "use_gpu": true}	2025-08-30 05:12:51.929875	2026-06-11 02:43:37.280485	error	[2025-08-30 13:12:53] 开始准备训练数据，项目ID: 1\n[2025-08-30 13:12:53] 获取项目信息成功，项目名称: 人模型\n[2025-08-30 13:12:53] 数据集验证成功，使用原始路径: /api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip\n[2025-08-30 13:12:53] 项目目录: /projects/easyaiot/AI/data/datasets/1\n[2025-08-30 13:12:53] 数据配置文件路径: /projects/easyaiot/AI/data/datasets/1/data.yaml\n[2025-08-30 13:12:53] 检查数据集配置文件...\n[2025-08-30 13:12:53] 加载预训练YOLOv8模型...\n[2025-08-30 13:12:53] 尝试加载预训练模型: model/yolov8n.pt\n[2026-06-11 10:43:37] 训练进程因服务重启或异常退出而中断。未找到可用断点，请重新训练。\n		\N	\N	\N	train_19	\N	\N	local	\N	\N	\N	\N
22	\N	0	/projects/easyaiot/AI/data/datasets/uploads/9775283215b74d5db820e918e8fbc39e.zip	{"epochs": 100, "model_arch": "yolov8n.pt", "img_size": 640, "batch_size": 16, "use_gpu": false, "task_base_name": "xxx", "dataset_source": "local"}	2026-06-18 10:58:49.431371	\N	error	集群调度失败: Worker 下发失败: 系统异常\n		\N	\N	\N	xxx_人类头部_22	人类头部	\N	auto	\N	\N	\N	\N
21	\N	15	/projects/easyaiot/AI/data/datasets/uploads/d1fafdad41e140739061a1afda8e6c10.zip	{"epochs": 100, "model_arch": "yolov8n.pt", "img_size": 640, "batch_size": 16, "use_gpu": false, "task_base_name": "xxx", "dataset_source": "local", "completed_epochs": 0}	2026-06-18 11:02:23.037397	\N	stopping	[2026-06-18 19:02:27] 开始准备训练数据，任务: xxx_d1fafdad41e140739061a1afda8e6c10_21\n[2026-06-18 19:02:27] 项目目录: /projects/easyaiot/AI/data/datasets/train_21\n[2026-06-18 19:02:27] 数据配置文件路径: /projects/easyaiot/AI/data/datasets/train_21/data.yaml\n[2026-06-18 19:02:27] 检查数据集配置文件...\n[2026-06-18 19:02:27] 数据集配置文件不存在，正在准备本地数据集...\n[2026-06-18 19:02:27] 正在解压本地数据集: /projects/easyaiot/AI/data/datasets/uploads/d1fafdad41e140739061a1afda8e6c10.zip\n[2026-06-18 19:02:32] 本地数据集解压成功\n[2026-06-18 19:02:32] 已标准化 data.yaml 路径: /projects/easyaiot/AI/data/datasets/train_21/data.yaml\n[2026-06-18 19:02:32] 加载预训练YOLOv8模型...\n[2026-06-18 19:02:32] 尝试加载预训练模型: yolov8n.pt\n[2026-06-18 19:02:32] 预训练模型已解析为本地路径: /projects/easyaiot/AI/yolov8n.pt\n[2026-06-18 19:02:32] 预训练模型加载成功!\n[2026-06-18 19:02:32] 开始训练模型，共100个epochs...\n[2026-06-18 19:02:32] 开始训练模型，配置: 数据文件=/projects/easyaiot/AI/data/datasets/train_21/data.yaml, epochs=100, 图像尺寸=640x640, 批次大小=16\n[2026-06-18 19:02:32] GPU状态检查: {\n  "use_gpu_env": true,\n  "gpu_ids_env": null,\n  "cuda_visible_devices": "0",\n  "nvidia_visible_devices": "all",\n  "pytorch_version": "2.11.0+cu130",\n  "cuda_available": false,\n  "cuda_version": "13.0",\n  "device_count": 0,\n  "visible_gpu_ids": [],\n  "multi_gpu": false,\n  "devices": []\n}\n[2026-06-18 19:02:32] 使用 CPU 进行训练\n[2026-06-18 19:02:32] DataLoader workers=8，AMP=False （workers 可通过 TRAIN_DATALOADER_WORKERS 覆盖）\n		\N	\N	\N	xxx_d1fafdad41e140739061a1afda8e6c10_21	d1fafdad41e140739061a1afda8e6c10	\N	auto	\N	4	172.16.13.220	2458762
\.


--
-- Name: ai_service_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.ai_service_id_seq', 3, true);


--
-- Name: auto_label_model_history_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auto_label_model_history_id_seq', 1, false);


--
-- Name: auto_label_result_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auto_label_result_id_seq', 1, false);


--
-- Name: auto_label_subtask_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auto_label_subtask_id_seq', 1, false);


--
-- Name: auto_label_task_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auto_label_task_id_seq', 1, false);


--
-- Name: export_record_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.export_record_id_seq', 1, true);


--
-- Name: inference_task_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.inference_task_id_seq', 60, true);


--
-- Name: llm_config_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.llm_config_id_seq', 3, true);


--
-- Name: llm_deploy_service_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.llm_deploy_service_id_seq', 1, false);


--
-- Name: model_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.model_id_seq', 14, true);


--
-- Name: ocr_result_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.ocr_result_id_seq', 1, false);


--
-- Name: plate_algorithm_version_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.plate_algorithm_version_id_seq', 1, false);


--
-- Name: plate_dataset_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.plate_dataset_id_seq', 1, false);


--
-- Name: plate_inference_task_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.plate_inference_task_id_seq', 1, false);


--
-- Name: plate_train_task_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.plate_train_task_id_seq', 1, false);


--
-- Name: rag_expert_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.rag_expert_id_seq', 1, false);


--
-- Name: rag_knowledge_document_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.rag_knowledge_document_id_seq', 1, false);


--
-- Name: rag_knowledge_segment_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.rag_knowledge_segment_id_seq', 1, false);


--
-- Name: rag_knowledge_set_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.rag_knowledge_set_id_seq', 1, false);


--
-- Name: sam_inference_result_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.sam_inference_result_id_seq', 1, false);


--
-- Name: speech_record_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.speech_record_id_seq', 1, false);


--
-- Name: train_task_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.train_task_id_seq', 22, true);


--
-- Name: ai_service ai_service_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_service
    ADD CONSTRAINT ai_service_pkey PRIMARY KEY (id);


--
-- Name: auto_label_model_history auto_label_model_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auto_label_model_history
    ADD CONSTRAINT auto_label_model_history_pkey PRIMARY KEY (id);


--
-- Name: auto_label_result auto_label_result_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auto_label_result
    ADD CONSTRAINT auto_label_result_pkey PRIMARY KEY (id);


--
-- Name: auto_label_subtask auto_label_subtask_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auto_label_subtask
    ADD CONSTRAINT auto_label_subtask_pkey PRIMARY KEY (id);


--
-- Name: auto_label_task auto_label_task_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auto_label_task
    ADD CONSTRAINT auto_label_task_pkey PRIMARY KEY (id);


--
-- Name: export_record export_record_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.export_record
    ADD CONSTRAINT export_record_pkey PRIMARY KEY (id);


--
-- Name: inference_task inference_task_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inference_task
    ADD CONSTRAINT inference_task_pkey PRIMARY KEY (id);


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
-- Name: llm_deploy_service llm_deploy_service_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_deploy_service
    ADD CONSTRAINT llm_deploy_service_pkey PRIMARY KEY (id);


--
-- Name: model model_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model
    ADD CONSTRAINT model_pkey PRIMARY KEY (id);


--
-- Name: ocr_result ocr_result_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ocr_result
    ADD CONSTRAINT ocr_result_pkey PRIMARY KEY (id);


--
-- Name: plate_algorithm_version plate_algorithm_version_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plate_algorithm_version
    ADD CONSTRAINT plate_algorithm_version_pkey PRIMARY KEY (id);


--
-- Name: plate_dataset plate_dataset_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plate_dataset
    ADD CONSTRAINT plate_dataset_pkey PRIMARY KEY (id);


--
-- Name: plate_inference_task plate_inference_task_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plate_inference_task
    ADD CONSTRAINT plate_inference_task_pkey PRIMARY KEY (id);


--
-- Name: plate_train_task plate_train_task_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plate_train_task
    ADD CONSTRAINT plate_train_task_pkey PRIMARY KEY (id);


--
-- Name: rag_expert rag_expert_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rag_expert
    ADD CONSTRAINT rag_expert_pkey PRIMARY KEY (id);


--
-- Name: rag_expert_knowledge_set rag_expert_knowledge_set_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rag_expert_knowledge_set
    ADD CONSTRAINT rag_expert_knowledge_set_pkey PRIMARY KEY (expert_id, knowledge_set_id);


--
-- Name: rag_knowledge_document rag_knowledge_document_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rag_knowledge_document
    ADD CONSTRAINT rag_knowledge_document_pkey PRIMARY KEY (id);


--
-- Name: rag_knowledge_segment rag_knowledge_segment_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rag_knowledge_segment
    ADD CONSTRAINT rag_knowledge_segment_pkey PRIMARY KEY (id);


--
-- Name: rag_knowledge_set rag_knowledge_set_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rag_knowledge_set
    ADD CONSTRAINT rag_knowledge_set_pkey PRIMARY KEY (id);


--
-- Name: rag_knowledge_set_segment rag_knowledge_set_segment_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rag_knowledge_set_segment
    ADD CONSTRAINT rag_knowledge_set_segment_pkey PRIMARY KEY (knowledge_set_id, segment_id);


--
-- Name: sam_inference_result sam_inference_result_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sam_inference_result
    ADD CONSTRAINT sam_inference_result_pkey PRIMARY KEY (id);


--
-- Name: speech_record speech_record_order_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.speech_record
    ADD CONSTRAINT speech_record_order_id_key UNIQUE (order_id);


--
-- Name: speech_record speech_record_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.speech_record
    ADD CONSTRAINT speech_record_pkey PRIMARY KEY (id);


--
-- Name: train_task train_task_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.train_task
    ADD CONSTRAINT train_task_pkey PRIMARY KEY (id);


--
-- Name: idx_ai_service_node_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ai_service_node_id ON public.ai_service USING btree (node_id);


--
-- Name: ix_auto_label_model_history_dataset_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_auto_label_model_history_dataset_id ON public.auto_label_model_history USING btree (dataset_id);


--
-- Name: ix_model_family_key; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_model_family_key ON public.model USING btree (family_key);


--
-- Name: ix_plate_algorithm_version_version; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_plate_algorithm_version_version ON public.plate_algorithm_version USING btree (version);


--
-- Name: ix_plate_dataset_name; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_plate_dataset_name ON public.plate_dataset USING btree (name);


--
-- Name: ix_rag_expert_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_rag_expert_category ON public.rag_expert USING btree (category);


--
-- Name: ix_rag_knowledge_segment_document_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_rag_knowledge_segment_document_id ON public.rag_knowledge_segment USING btree (document_id);


--
-- Name: ix_rag_knowledge_segment_milvus_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_rag_knowledge_segment_milvus_id ON public.rag_knowledge_segment USING btree (milvus_id);


--
-- Name: ix_rag_knowledge_set_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_rag_knowledge_set_category ON public.rag_knowledge_set USING btree (category);


--
-- Name: ai_service ai_service_model_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_service
    ADD CONSTRAINT ai_service_model_id_fkey FOREIGN KEY (model_id) REFERENCES public.model(id);


--
-- Name: auto_label_result auto_label_result_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auto_label_result
    ADD CONSTRAINT auto_label_result_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.auto_label_task(id);


--
-- Name: auto_label_subtask auto_label_subtask_parent_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auto_label_subtask
    ADD CONSTRAINT auto_label_subtask_parent_task_id_fkey FOREIGN KEY (parent_task_id) REFERENCES public.auto_label_task(id);


--
-- Name: auto_label_task auto_label_task_model_service_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auto_label_task
    ADD CONSTRAINT auto_label_task_model_service_id_fkey FOREIGN KEY (model_service_id) REFERENCES public.ai_service(id);


--
-- Name: export_record export_record_model_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.export_record
    ADD CONSTRAINT export_record_model_id_fkey FOREIGN KEY (model_id) REFERENCES public.model(id);


--
-- Name: inference_task inference_task_model_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inference_task
    ADD CONSTRAINT inference_task_model_id_fkey FOREIGN KEY (model_id) REFERENCES public.model(id);


--
-- Name: llm_deploy_service llm_deploy_service_llm_config_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_deploy_service
    ADD CONSTRAINT llm_deploy_service_llm_config_id_fkey FOREIGN KEY (llm_config_id) REFERENCES public.llm_config(id);


--
-- Name: plate_inference_task plate_inference_task_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plate_inference_task
    ADD CONSTRAINT plate_inference_task_version_id_fkey FOREIGN KEY (version_id) REFERENCES public.plate_algorithm_version(id);


--
-- Name: plate_train_task plate_train_task_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plate_train_task
    ADD CONSTRAINT plate_train_task_version_id_fkey FOREIGN KEY (version_id) REFERENCES public.plate_algorithm_version(id);


--
-- Name: rag_expert_knowledge_set rag_expert_knowledge_set_expert_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rag_expert_knowledge_set
    ADD CONSTRAINT rag_expert_knowledge_set_expert_id_fkey FOREIGN KEY (expert_id) REFERENCES public.rag_expert(id) ON DELETE CASCADE;


--
-- Name: rag_expert_knowledge_set rag_expert_knowledge_set_knowledge_set_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rag_expert_knowledge_set
    ADD CONSTRAINT rag_expert_knowledge_set_knowledge_set_id_fkey FOREIGN KEY (knowledge_set_id) REFERENCES public.rag_knowledge_set(id) ON DELETE CASCADE;


--
-- Name: rag_knowledge_segment rag_knowledge_segment_document_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rag_knowledge_segment
    ADD CONSTRAINT rag_knowledge_segment_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.rag_knowledge_document(id);


--
-- Name: rag_knowledge_set_segment rag_knowledge_set_segment_knowledge_set_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rag_knowledge_set_segment
    ADD CONSTRAINT rag_knowledge_set_segment_knowledge_set_id_fkey FOREIGN KEY (knowledge_set_id) REFERENCES public.rag_knowledge_set(id) ON DELETE CASCADE;


--
-- Name: rag_knowledge_set_segment rag_knowledge_set_segment_segment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rag_knowledge_set_segment
    ADD CONSTRAINT rag_knowledge_set_segment_segment_id_fkey FOREIGN KEY (segment_id) REFERENCES public.rag_knowledge_segment(id) ON DELETE CASCADE;


--
-- Name: train_task train_task_model_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.train_task
    ADD CONSTRAINT train_task_model_id_fkey FOREIGN KEY (model_id) REFERENCES public.model(id);


--
-- PostgreSQL database dump complete
--

\unrestrict KJM1yFgt7vdzHI08ckJHfmIgDFgu8pia6MROPKXCRdrLDy6VkU10gdC2Qyv8zzJ

