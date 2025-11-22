--
-- PostgreSQL database dump
--

\restrict xhtzy3pIvDsIXl7oi2odys2htmEbmA6btf4B2nNuuFCH8N7NTU0ERUgTAxkhyE2

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
-- Name: ai_service; Type: TABLE; Schema: public; Owner: postgres
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
    updated_at timestamp without time zone
);


ALTER TABLE public.ai_service OWNER TO postgres;

--
-- Name: ai_service_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.ai_service_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ai_service_id_seq OWNER TO postgres;

--
-- Name: ai_service_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.ai_service_id_seq OWNED BY public.ai_service.id;


--
-- Name: export_record; Type: TABLE; Schema: public; Owner: postgres
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


ALTER TABLE public.export_record OWNER TO postgres;

--
-- Name: export_record_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.export_record_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.export_record_id_seq OWNER TO postgres;

--
-- Name: export_record_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.export_record_id_seq OWNED BY public.export_record.id;


--
-- Name: inference_task; Type: TABLE; Schema: public; Owner: postgres
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


ALTER TABLE public.inference_task OWNER TO postgres;

--
-- Name: inference_task_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.inference_task_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.inference_task_id_seq OWNER TO postgres;

--
-- Name: inference_task_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.inference_task_id_seq OWNED BY public.inference_task.id;


--
-- Name: llm_config; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.llm_config (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    model_type character varying(50),
    icon_url character varying(500),
    vendor character varying(100),
    base_url character varying(500) NOT NULL,
    api_key character varying(200) NOT NULL,
    model character varying(100) NOT NULL,
    api_version character varying(50),
    request_timeout integer,
    max_retries integer,
    context_window integer,
    max_output_tokens integer,
    supported_features json,
    temperature double precision,
    system_prompt text,
    is_customizable boolean,
    rag_enabled boolean,
    prompt_template text,
    domain_adaptation character varying(100),
    input_token_price double precision,
    output_token_price double precision,
    avg_response_time double precision,
    total_tokens_used bigint,
    monthly_budget double precision,
    is_active boolean,
    status character varying(20),
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    last_test_time timestamp without time zone
);


ALTER TABLE public.llm_config OWNER TO postgres;

--
-- Name: llm_config_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.llm_config_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.llm_config_id_seq OWNER TO postgres;

--
-- Name: llm_config_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.llm_config_id_seq OWNED BY public.llm_config.id;


--
-- Name: model; Type: TABLE; Schema: public; Owner: postgres
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
    rknn_model_path character varying(500)
);


ALTER TABLE public.model OWNER TO postgres;

--
-- Name: model_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.model_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.model_id_seq OWNER TO postgres;

--
-- Name: model_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.model_id_seq OWNED BY public.model.id;


--
-- Name: ocr_result; Type: TABLE; Schema: public; Owner: postgres
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


ALTER TABLE public.ocr_result OWNER TO postgres;

--
-- Name: ocr_result_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.ocr_result_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ocr_result_id_seq OWNER TO postgres;

--
-- Name: ocr_result_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.ocr_result_id_seq OWNED BY public.ocr_result.id;


--
-- Name: speech_record; Type: TABLE; Schema: public; Owner: postgres
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


ALTER TABLE public.speech_record OWNER TO postgres;

--
-- Name: speech_record_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.speech_record_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.speech_record_id_seq OWNER TO postgres;

--
-- Name: speech_record_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.speech_record_id_seq OWNED BY public.speech_record.id;


--
-- Name: train_task; Type: TABLE; Schema: public; Owner: postgres
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
    train_results_path character varying(500)
);


ALTER TABLE public.train_task OWNER TO postgres;

--
-- Name: train_task_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.train_task_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.train_task_id_seq OWNER TO postgres;

--
-- Name: train_task_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.train_task_id_seq OWNED BY public.train_task.id;


--
-- Name: ai_service id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ai_service ALTER COLUMN id SET DEFAULT nextval('public.ai_service_id_seq'::regclass);


--
-- Name: export_record id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.export_record ALTER COLUMN id SET DEFAULT nextval('public.export_record_id_seq'::regclass);


--
-- Name: inference_task id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inference_task ALTER COLUMN id SET DEFAULT nextval('public.inference_task_id_seq'::regclass);


--
-- Name: llm_config id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.llm_config ALTER COLUMN id SET DEFAULT nextval('public.llm_config_id_seq'::regclass);


--
-- Name: model id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.model ALTER COLUMN id SET DEFAULT nextval('public.model_id_seq'::regclass);


--
-- Name: ocr_result id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ocr_result ALTER COLUMN id SET DEFAULT nextval('public.ocr_result_id_seq'::regclass);


--
-- Name: speech_record id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.speech_record ALTER COLUMN id SET DEFAULT nextval('public.speech_record_id_seq'::regclass);


--
-- Name: train_task id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.train_task ALTER COLUMN id SET DEFAULT nextval('public.train_task_id_seq'::regclass);


--
-- Data for Name: ai_service; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.ai_service (id, model_id, service_name, server_ip, port, inference_endpoint, status, mac_address, deploy_time, last_heartbeat, process_id, log_path, model_version, format, created_at, updated_at) FROM stdin;
2	3	model_3_onnx_1.0.1	192.168.11.28	10000	http://192.168.11.28:10000/inference	running	30:c1:05:16:5a:68	2025-11-23 05:03:47.157704	2025-11-23 07:02:59.156544	3341939	/projects/easyaiot/AI/logs/2	1.0.1	onnx	2025-11-23 05:03:47.158308	2025-11-23 07:02:59.157105
3	3	model_3_onnx_1.0.1	192.168.11.28	10001	http://192.168.11.28:10001/inference	running	30:c1:05:16:5a:68	2025-11-23 05:03:55.644905	2025-11-23 07:02:59.661862	3342083	/projects/easyaiot/AI/logs/3	1.0.1	onnx	2025-11-23 05:03:55.645332	2025-11-23 07:02:59.662252
1	3	model_3_onnx_1.0.1	192.168.11.28	9999	http://192.168.11.28:9999/inference	running	30:c1:05:16:5a:68	2025-11-23 05:03:15.111839	2025-11-23 07:03:00.193403	3342182	/projects/easyaiot/AI/logs/1	1.0.1	onnx	2025-11-23 05:03:15.113205	2025-11-23 07:03:00.193785
\.


--
-- Data for Name: export_record; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.export_record (id, model_id, model_name, format, minio_path, local_path, created_at, status, message) FROM stdin;
1	3	安全帽模型	onnx	exports/model_3/onnx/model.onnx	/tmp/tmp6ae5jrr1/model.onnx	2025-11-22 18:05:20.113985	COMPLETED	\N
\.


--
-- Data for Name: inference_task; Type: TABLE DATA; Schema: public; Owner: postgres
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
\.


--
-- Data for Name: llm_config; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.llm_config (id, name, description, model_type, icon_url, vendor, base_url, api_key, model, api_version, request_timeout, max_retries, context_window, max_output_tokens, supported_features, temperature, system_prompt, is_customizable, rag_enabled, prompt_template, domain_adaptation, input_token_price, output_token_price, avg_response_time, total_tokens_used, monthly_budget, is_active, status, created_at, updated_at, last_test_time) FROM stdin;
\.


--
-- Data for Name: model; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.model (id, name, description, model_path, image_url, version, created_at, updated_at, onnx_model_path, torchscript_model_path, tensorrt_model_path, openvino_model_path, rknn_model_path) FROM stdin;
1	人模型	用于识别人的AI算法	/api/v1/buckets/models/objects/download?prefix=models/model_1/train_20/best.pt	/api/v1/buckets/models/objects/download?prefix=images/6dc4c28fe6444f98955bdc98bcfe6ed4.jpg	V2025.08.5	2025-08-25 10:37:44.147967	2025-08-30 05:22:51.040101	\N	\N	\N	\N	\N
3	安全帽模型	识别安全帽的模型	/api/v1/buckets/models/objects/download?prefix=yolo/yolov8/onnx/1727f89c9a434c18a2a78d54d0a54023.onnx	/api/v1/buckets/models/objects/download?prefix=images/7e6ef2e33af64a18add7f91a66b6403e.jpg	1.0.1	2025-11-22 08:33:51.975637	2025-11-22 13:35:32.600112	exports/model_3/onnx/model.onnx	\N	\N	exports/model_3/openvino/model_openvino_model/	\N
\.


--
-- Data for Name: ocr_result; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.ocr_result (id, text, confidence, bbox, polygon, page_num, line_num, word_num, image_url, created_at) FROM stdin;
\.


--
-- Data for Name: speech_record; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.speech_record (id, order_id, audio_file_path, filename, file_size, duration, recognized_text, confidence, status, created_at, completed_at, error_message) FROM stdin;
\.


--
-- Data for Name: train_task; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.train_task (id, model_id, progress, dataset_path, hyperparameters, start_time, end_time, status, train_log, checkpoint_dir, metrics_path, minio_model_path, train_results_path) FROM stdin;
6	1	10	/api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip	{"epochs": 100, "model_arch": "model/yolov8n.pt", "img_size": 640, "batch_size": 16, "use_gpu": true}	2025-08-30 04:20:12.508389	\N	preparing	[2025-08-30 12:20:13] 开始准备训练数据，项目ID: 1\n[2025-08-30 12:20:13] 获取项目信息成功，项目名称: 人模型\n[2025-08-30 12:20:14] 数据集验证成功，使用原始路径: /api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip\n[2025-08-30 12:20:14] 项目目录: /projects/easyaiot/AI/data/datasets/1\n[2025-08-30 12:20:14] 数据配置文件路径: /projects/easyaiot/AI/data/datasets/1/data.yaml\n[2025-08-30 12:20:14] 检查数据集配置文件...\n[2025-08-30 12:20:14] 加载预训练YOLOv8模型...\n[2025-08-30 12:20:14] 尝试加载预训练模型: /projects/easyaiot/AI/model/yolov8n.pt\n		\N	\N	\N
3	1	10	/api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip	{"epochs": 100, "model_arch": "model/yolov8n.pt", "img_size": 640, "batch_size": 16, "use_gpu": true}	2025-08-30 04:09:03.61429	\N	preparing	[2025-08-30 12:09:04] 开始准备训练数据，项目ID: 1\n[2025-08-30 12:09:04] 获取项目信息成功，项目名称: 人模型\n[2025-08-30 12:09:04] 数据集验证成功，使用原始路径: /api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip\n[2025-08-30 12:09:05] 项目目录: /projects/easyaiot/AI/data/datasets/1\n[2025-08-30 12:09:05] 数据配置文件路径: /projects/easyaiot/AI/data/datasets/1/data.yaml\n[2025-08-30 12:09:05] 检查数据集配置文件...\n[2025-08-30 12:09:05] 加载预训练YOLOv8模型...\n[2025-08-30 12:09:05] 尝试加载预训练模型: /projects/easyaiot/AI/model/yolov8n.pt\n		\N	\N	\N
2	1	10	/api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip	{"epochs": 100, "model_arch": "model/yolov8n.pt", "img_size": 640, "batch_size": 16, "use_gpu": true}	2025-08-30 04:05:45.965389	\N	preparing	[2025-08-30 12:05:47] 开始准备训练数据，项目ID: 1\n[2025-08-30 12:05:47] 获取项目信息成功，项目名称: 人模型\n[2025-08-30 12:05:47] 数据集验证成功，使用原始路径: /api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip\n[2025-08-30 12:05:47] 项目目录: /projects/easyaiot/AI/data/datasets/1\n[2025-08-30 12:05:47] 数据配置文件路径: /projects/easyaiot/AI/data/datasets/1/data.yaml\n[2025-08-30 12:05:47] 检查数据集配置文件...\n[2025-08-30 12:05:47] 加载预训练YOLOv8模型...\n[2025-08-30 12:05:47] 尝试加载预训练模型: /projects/easyaiot/AI/model/yolov8n.pt\n		\N	\N	\N
4	1	10	/api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip	{"epochs": 100, "model_arch": "model/yolov8n.pt", "img_size": 640, "batch_size": 16, "use_gpu": true}	2025-08-30 04:14:05.135787	\N	preparing	[2025-08-30 12:14:06] 开始准备训练数据，项目ID: 1\n[2025-08-30 12:14:06] 获取项目信息成功，项目名称: 人模型\n[2025-08-30 12:14:06] 数据集验证成功，使用原始路径: /api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip\n[2025-08-30 12:14:06] 项目目录: /projects/easyaiot/AI/data/datasets/1\n[2025-08-30 12:14:06] 数据配置文件路径: /projects/easyaiot/AI/data/datasets/1/data.yaml\n[2025-08-30 12:14:06] 检查数据集配置文件...\n[2025-08-30 12:14:06] 加载预训练YOLOv8模型...\n[2025-08-30 12:14:07] 尝试加载预训练模型: /projects/easyaiot/AI/model/yolov8n.pt\n		\N	\N	\N
1	1	10	/api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip	{"epochs": 100, "model_arch": "model/yolov8n.pt", "img_size": 640, "batch_size": 16, "use_gpu": true}	2025-08-30 04:04:49.247897	\N	preparing	[2025-08-30 12:04:50] 开始准备训练数据，项目ID: 1\n[2025-08-30 12:04:50] 获取项目信息成功，项目名称: 人模型\n[2025-08-30 12:04:50] 数据集验证成功，使用原始路径: /api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip\n[2025-08-30 12:04:50] 项目目录: /projects/easyaiot/AI/data/datasets/1\n[2025-08-30 12:04:50] 数据配置文件路径: /projects/easyaiot/AI/data/datasets/1/data.yaml\n[2025-08-30 12:04:50] 检查数据集配置文件...\n[2025-08-30 12:04:50] 加载预训练YOLOv8模型...\n[2025-08-30 12:04:51] 尝试加载预训练模型: /projects/easyaiot/AI/model/yolov8n.pt\n		\N	\N	\N
5	1	10	/api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip	{"epochs": 100, "model_arch": "model/yolov8n.pt", "img_size": 640, "batch_size": 16, "use_gpu": true}	2025-08-30 04:17:50.939088	\N	preparing	[2025-08-30 12:17:52] 开始准备训练数据，项目ID: 1\n[2025-08-30 12:17:52] 获取项目信息成功，项目名称: 人模型\n[2025-08-30 12:17:52] 数据集验证成功，使用原始路径: /api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip\n[2025-08-30 12:17:52] 项目目录: /projects/easyaiot/AI/data/datasets/1\n[2025-08-30 12:17:52] 数据配置文件路径: /projects/easyaiot/AI/data/datasets/1/data.yaml\n[2025-08-30 12:17:52] 检查数据集配置文件...\n[2025-08-30 12:17:52] 加载预训练YOLOv8模型...\n[2025-08-30 12:17:52] 尝试加载预训练模型: /projects/easyaiot/AI/model/yolov8n.pt\n		\N	\N	\N
7	1	10	/api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip	{"epochs": 100, "model_arch": "model/yolov8n.pt", "img_size": 640, "batch_size": 16, "use_gpu": true}	2025-08-30 04:32:47.695145	\N	preparing	[2025-08-30 12:32:48] 开始准备训练数据，项目ID: 1\n[2025-08-30 12:32:48] 获取项目信息成功，项目名称: 人模型\n[2025-08-30 12:32:48] 数据集验证成功，使用原始路径: /api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip\n[2025-08-30 12:32:49] 项目目录: /projects/easyaiot/AI/data/datasets/1\n[2025-08-30 12:32:49] 数据配置文件路径: /projects/easyaiot/AI/data/datasets/1/data.yaml\n[2025-08-30 12:32:49] 检查数据集配置文件...\n[2025-08-30 12:32:49] 加载预训练YOLOv8模型...\n[2025-08-30 12:32:49] 尝试加载预训练模型: /projects/easyaiot/AI/model/yolov8n.pt\n		\N	\N	\N
8	1	10	/api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip	{"epochs": 100, "model_arch": "model/yolov8n.pt", "img_size": 640, "batch_size": 16, "use_gpu": true}	2025-08-30 04:36:01.576862	\N	error	[2025-08-30 12:36:27] 开始准备训练数据，项目ID: 1\n[2025-08-30 12:37:01] 获取项目信息成功，项目名称: 人模型\n[2025-08-30 12:37:14] 数据集验证成功，使用原始路径: /api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip\n[2025-08-30 12:37:15] 项目目录: /projects/easyaiot/AI/data/datasets/1\n[2025-08-30 12:37:21] 数据配置文件路径: /projects/easyaiot/AI/data/datasets/1/data.yaml\n[2025-08-30 12:37:22] 检查数据集配置文件...\n[2025-08-30 12:37:53] 加载预训练YOLOv8模型...\n[2025-08-30 12:37:56] 尝试加载预训练模型: /projects/easyaiot/AI/model/yolov8n.pt\n[2025-08-30 12:38:08] 预训练模型加载失败: PytorchStreamReader failed reading zip archive: invalid header or archive is corrupted\n		\N	\N	\N
10	1	10	/api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip	{"epochs": 100, "model_arch": "model/yolov8n.pt", "img_size": 640, "batch_size": 16, "use_gpu": true}	2025-08-30 04:43:39.87098	\N	error	[2025-08-30 12:43:40] 开始准备训练数据，项目ID: 1\n[2025-08-30 12:43:41] 获取项目信息成功，项目名称: 人模型\n[2025-08-30 12:43:41] 数据集验证成功，使用原始路径: /api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip\n[2025-08-30 12:43:41] 项目目录: /projects/easyaiot/AI/data/datasets/1\n[2025-08-30 12:43:41] 数据配置文件路径: /projects/easyaiot/AI/data/datasets/1/data.yaml\n[2025-08-30 12:43:41] 检查数据集配置文件...\n[2025-08-30 12:43:41] 加载预训练YOLOv8模型...\n[2025-08-30 12:43:41] 尝试加载预训练模型: /projects/easyaiot/AI/model/yolov8n.pt\n[2025-08-30 12:43:41] 预训练模型加载失败: PytorchStreamReader failed reading zip archive: invalid header or archive is corrupted\n		\N	\N	\N
11	1	10	/api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip	{"epochs": 100, "model_arch": "model/yolov8n.pt", "img_size": 640, "batch_size": 16, "use_gpu": true}	2025-08-30 04:50:11.207953	\N	preparing	[2025-08-30 12:50:12] 开始准备训练数据，项目ID: 1\n[2025-08-30 12:50:12] 获取项目信息成功，项目名称: 人模型\n[2025-08-30 12:50:12] 数据集验证成功，使用原始路径: /api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip\n[2025-08-30 12:50:12] 项目目录: /projects/easyaiot/AI/data/datasets/1\n[2025-08-30 12:50:12] 数据配置文件路径: /projects/easyaiot/AI/data/datasets/1/data.yaml\n[2025-08-30 12:50:12] 检查数据集配置文件...\n[2025-08-30 12:50:13] 加载预训练YOLOv8模型...\n[2025-08-30 12:50:13] 尝试加载预训练模型: /projects/easyaiot/AI/model/yolov8n.pt\n		\N	\N	\N
13	1	10	/api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip	{"epochs": 100, "model_arch": "model/yolov8n.pt", "img_size": 640, "batch_size": 16, "use_gpu": true}	2025-08-30 04:52:34.809657	\N	error	[2025-08-30 12:52:35] 开始准备训练数据，项目ID: 1\n[2025-08-30 12:52:36] 获取项目信息成功，项目名称: 人模型\n[2025-08-30 12:52:36] 数据集验证成功，使用原始路径: /api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip\n[2025-08-30 12:52:36] 项目目录: /projects/easyaiot/AI/data/datasets/1\n[2025-08-30 12:52:36] 数据配置文件路径: /projects/easyaiot/AI/data/datasets/1/data.yaml\n[2025-08-30 12:52:36] 检查数据集配置文件...\n[2025-08-30 12:52:36] 加载预训练YOLOv8模型...\n[2025-08-30 12:52:36] 尝试加载预训练模型: /projects/easyaiot/AI/model/yolov8n.pt\n[2025-08-30 12:52:36] 预训练模型加载失败: PytorchStreamReader failed reading zip archive: invalid header or archive is corrupted\n		\N	\N	\N
12	1	10	/api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip	{"epochs": 100, "model_arch": "model/yolov8n.pt", "img_size": 640, "batch_size": 16, "use_gpu": true}	2025-08-30 04:50:59.492811	\N	preparing	[2025-08-30 12:51:00] 开始准备训练数据，项目ID: 1\n[2025-08-30 12:51:00] 获取项目信息成功，项目名称: 人模型\n[2025-08-30 12:51:00] 数据集验证成功，使用原始路径: /api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip\n[2025-08-30 12:51:00] 项目目录: /projects/easyaiot/AI/data/datasets/1\n[2025-08-30 12:51:01] 数据配置文件路径: /projects/easyaiot/AI/data/datasets/1/data.yaml\n[2025-08-30 12:51:01] 检查数据集配置文件...\n[2025-08-30 12:51:01] 加载预训练YOLOv8模型...\n[2025-08-30 12:51:01] 尝试加载预训练模型: /projects/easyaiot/AI/model/yolov8n.pt\n		\N	\N	\N
9	1	10	/api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip	{"epochs": 100, "model_arch": "model/yolov8n.pt", "img_size": 640, "batch_size": 16, "use_gpu": true}	2025-08-30 04:42:51.803234	\N	error	[2025-08-30 12:42:57] 开始准备训练数据，项目ID: 1\n[2025-08-30 12:42:57] 获取项目信息成功，项目名称: 人模型\n[2025-08-30 12:42:58] 数据集验证成功，使用原始路径: /api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip\n[2025-08-30 12:42:58] 项目目录: /projects/easyaiot/AI/data/datasets/1\n[2025-08-30 12:42:58] 数据配置文件路径: /projects/easyaiot/AI/data/datasets/1/data.yaml\n[2025-08-30 12:42:58] 检查数据集配置文件...\n[2025-08-30 12:42:58] 加载预训练YOLOv8模型...\n[2025-08-30 12:42:58] 尝试加载预训练模型: /projects/easyaiot/AI/model/yolov8n.pt\n[2025-08-30 12:43:01] 预训练模型文件不存在: /projects/easyaiot/AI/model/yolov8n.pt\n		\N	\N	\N
14	1	10	/api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip	{"epochs": 100, "model_arch": "model/yolov8n.pt", "img_size": 640, "batch_size": 16, "use_gpu": true}	2025-08-30 04:57:12.432184	\N	error	[2025-08-30 12:57:13] 开始准备训练数据，项目ID: 1\n[2025-08-30 12:57:13] 获取项目信息成功，项目名称: 人模型\n[2025-08-30 12:57:13] 数据集验证成功，使用原始路径: /api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip\n[2025-08-30 12:57:13] 项目目录: /projects/easyaiot/AI/data/datasets/1\n[2025-08-30 12:57:14] 数据配置文件路径: /projects/easyaiot/AI/data/datasets/1/data.yaml\n[2025-08-30 12:57:14] 检查数据集配置文件...\n[2025-08-30 12:57:14] 加载预训练YOLOv8模型...\n[2025-08-30 12:57:14] 尝试加载预训练模型: /projects/easyaiot/AI/model/yolov8n.pt\n[2025-08-30 12:57:14] 预训练模型加载失败: PytorchStreamReader failed reading zip archive: invalid header or archive is corrupted\n		\N	\N	\N
16	1	15	/api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip	{"epochs": 100, "model_arch": "model/yolov8n.pt", "img_size": 640, "batch_size": 16, "use_gpu": true}	2025-08-30 05:02:37.73719	\N	preparing	[2025-08-30 13:02:38] 开始准备训练数据，项目ID: 1\n[2025-08-30 13:02:38] 获取项目信息成功，项目名称: 人模型\n[2025-08-30 13:02:39] 数据集验证成功，使用原始路径: /api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip\n[2025-08-30 13:02:39] 项目目录: /projects/easyaiot/AI/data/datasets/1\n[2025-08-30 13:02:39] 数据配置文件路径: /projects/easyaiot/AI/data/datasets/1/data.yaml\n[2025-08-30 13:02:39] 检查数据集配置文件...\n[2025-08-30 13:02:39] 加载预训练YOLOv8模型...\n[2025-08-30 13:02:39] 尝试加载预训练模型: /projects/easyaiot/AI/model/yolov8n.pt\n[2025-08-30 13:02:39] 预训练模型加载成功! 模型路径: /projects/easyaiot/AI/model/yolov8n.pt\n[2025-08-30 13:02:39] 开始训练模型，共100个epochs...\n[2025-08-30 13:02:40] 开始训练模型，配置: 数据文件=/projects/easyaiot/AI/data/datasets/1/data.yaml, epochs=100, 图像尺寸=640x640, 批次大小=16\n[2025-08-30 13:02:40] GPU状态检查: {\n  "pytorch_version": "2.0.1+cu117",\n  "cuda_available": true,\n  "cuda_version": "11.7",\n  "device_count": 1,\n  "device_0_name": "NVIDIA RTX A5000",\n  "device_0_capability": [\n    8,\n    6\n  ]\n}\n[2025-08-30 13:02:40] 使用GPU进行训练: NVIDIA RTX A5000\n	/projects/easyaiot/AI/data/datasets/1/train_results/checkpoints	\N	\N	\N
15	1	15	/api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip	{"epochs": 100, "model_arch": "model/yolov8n.pt", "img_size": 640, "batch_size": 16, "use_gpu": true}	2025-08-30 04:59:21.262579	\N	preparing	[2025-08-30 12:59:22] 开始准备训练数据，项目ID: 1\n[2025-08-30 12:59:22] 获取项目信息成功，项目名称: 人模型\n[2025-08-30 12:59:22] 数据集验证成功，使用原始路径: /api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip\n[2025-08-30 12:59:22] 项目目录: /projects/easyaiot/AI/data/datasets/1\n[2025-08-30 12:59:22] 数据配置文件路径: /projects/easyaiot/AI/data/datasets/1/data.yaml\n[2025-08-30 12:59:22] 检查数据集配置文件...\n[2025-08-30 12:59:23] 加载预训练YOLOv8模型...\n[2025-08-30 12:59:23] 尝试加载预训练模型: /projects/easyaiot/AI/model/yolov8n.pt\n[2025-08-30 12:59:23] 预训练模型加载成功! 模型路径: /projects/easyaiot/AI/model/yolov8n.pt\n[2025-08-30 12:59:23] 开始训练模型，共100个epochs...\n[2025-08-30 12:59:23] 开始训练模型，配置: 数据文件=/projects/easyaiot/AI/data/datasets/1/data.yaml, epochs=100, 图像尺寸=640x640, 批次大小=16\n[2025-08-30 12:59:23] GPU状态检查: {\n  "pytorch_version": "2.0.1+cu117",\n  "cuda_available": true,\n  "cuda_version": "11.7",\n  "device_count": 1,\n  "device_0_name": "NVIDIA RTX A5000",\n  "device_0_capability": [\n    8,\n    6\n  ]\n}\n[2025-08-30 12:59:24] 使用GPU进行训练: NVIDIA RTX A5000\n	/projects/easyaiot/AI/data/datasets/1/train_results/checkpoints	\N	\N	\N
18	1	15	/api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip	{"epochs": 100, "model_arch": "model/yolov8n.pt", "img_size": 640, "batch_size": 16, "use_gpu": true}	2025-08-30 05:09:31.896726	\N	preparing	[2025-08-30 13:09:33] 开始准备训练数据，项目ID: 1\n[2025-08-30 13:09:33] 获取项目信息成功，项目名称: 人模型\n[2025-08-30 13:09:33] 数据集验证成功，使用原始路径: /api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip\n[2025-08-30 13:09:33] 项目目录: /projects/easyaiot/AI/data/datasets/1\n[2025-08-30 13:09:33] 数据配置文件路径: /projects/easyaiot/AI/data/datasets/1/data.yaml\n[2025-08-30 13:09:33] 检查数据集配置文件...\n[2025-08-30 13:09:33] 加载预训练YOLOv8模型...\n[2025-08-30 13:09:33] 尝试加载预训练模型: model/yolov8n.pt\n[2025-08-30 13:09:34] 预训练模型加载成功! 模型路径: model/yolov8n.pt\n[2025-08-30 13:09:34] 开始训练模型，共100个epochs...\n[2025-08-30 13:09:34] 开始训练模型，配置: 数据文件=/projects/easyaiot/AI/data/datasets/1/data.yaml, epochs=100, 图像尺寸=640x640, 批次大小=16\n[2025-08-30 13:09:34] GPU状态检查: {\n  "pytorch_version": "2.0.1+cu117",\n  "cuda_available": true,\n  "cuda_version": "11.7",\n  "device_count": 1,\n  "device_0_name": "NVIDIA RTX A5000",\n  "device_0_capability": [\n    8,\n    6\n  ]\n}\n[2025-08-30 13:09:34] 使用GPU进行训练: NVIDIA RTX A5000\n	/projects/easyaiot/AI/data/datasets/1/train_results/checkpoints	\N	\N	\N
17	1	100	/api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip	{"epochs": 100, "model_arch": "model/yolov8n.pt", "img_size": 640, "batch_size": 16, "use_gpu": true}	2025-08-30 05:04:36.030287	2025-08-30 05:07:08.50721	completed	[2025-08-30 13:04:37] 开始准备训练数据，项目ID: 1\n[2025-08-30 13:04:37] 获取项目信息成功，项目名称: 人模型\n[2025-08-30 13:04:37] 数据集验证成功，使用原始路径: /api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip\n[2025-08-30 13:04:37] 项目目录: /projects/easyaiot/AI/data/datasets/1\n[2025-08-30 13:04:37] 数据配置文件路径: /projects/easyaiot/AI/data/datasets/1/data.yaml\n[2025-08-30 13:04:37] 检查数据集配置文件...\n[2025-08-30 13:04:37] 加载预训练YOLOv8模型...\n[2025-08-30 13:04:37] 尝试加载预训练模型: /projects/easyaiot/AI/model/yolov8n.pt\n[2025-08-30 13:04:38] 预训练模型加载成功! 模型路径: /projects/easyaiot/AI/model/yolov8n.pt\n[2025-08-30 13:04:38] 开始训练模型，共100个epochs...\n[2025-08-30 13:04:38] 开始训练模型，配置: 数据文件=/projects/easyaiot/AI/data/datasets/1/data.yaml, epochs=100, 图像尺寸=640x640, 批次大小=16\n[2025-08-30 13:04:38] GPU状态检查: {\n  "pytorch_version": "2.0.1+cu117",\n  "cuda_available": true,\n  "cuda_version": "11.7",\n  "device_count": 1,\n  "device_0_name": "NVIDIA RTX A5000",\n  "device_0_capability": [\n    8,\n    6\n  ]\n}\n[2025-08-30 13:04:38] 使用GPU进行训练: NVIDIA RTX A5000\n[2025-08-30 13:06:59] 训练结果CSV已上传至Minio: /api/v1/buckets/model-train/objects/download?prefix=models/model_1/train_17/results.csv\n[2025-08-30 13:07:00] 训练结果图表已上传至Minio: /api/v1/buckets/model-train/objects/download?prefix=models/model_1/train_17/results.png\n[2025-08-30 13:07:00] 训练完成，正在保存结果...\n[2025-08-30 13:07:01] 模型训练完成!\n[2025-08-30 13:07:01] 训练结果保存路径: /projects/easyaiot/AI/data/datasets/1/train_results\n[2025-08-30 13:07:01] 检查最佳模型文件是否存在: /projects/easyaiot/AI/data/datasets/1/train_results/weights/best.pt\n[2025-08-30 13:07:01] 找到最佳模型文件，开始复制到保存目录: /projects/easyaiot/AI/data/datasets/1/train_results/weights/best.pt\n[2025-08-30 13:07:01] 模型文件已成功复制到保存目录: /projects/easyaiot/AI/static/models/1/train/weights\n[2025-08-30 13:07:01] 开始上传最佳模型到Minio...\n[2025-08-30 13:07:08] 模型已成功上传至Minio: /api/v1/buckets/models/objects/download?prefix=models/model_1/train_17/best.pt\n[2025-08-30 13:07:08] 训练日志已上传至Minio: /api/v1/buckets/log-bucket/objects/download?prefix=logs/model_1/train_17.txt\n[2025-08-30 13:07:08] 模型训练完成并已保存\n	/projects/easyaiot/AI/data/datasets/1/train_results/checkpoints	/api/v1/buckets/model-train/objects/download?prefix=models/model_1/train_17/results.csv	/api/v1/buckets/models/objects/download?prefix=models/model_1/train_17/best.pt	/api/v1/buckets/model-train/objects/download?prefix=models/model_1/train_17/results.png
19	1	10	/api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip	{"epochs": 100, "model_arch": "model/yolov8n.pt", "img_size": 640, "batch_size": 16, "use_gpu": true}	2025-08-30 05:12:51.929875	\N	preparing	[2025-08-30 13:12:53] 开始准备训练数据，项目ID: 1\n[2025-08-30 13:12:53] 获取项目信息成功，项目名称: 人模型\n[2025-08-30 13:12:53] 数据集验证成功，使用原始路径: /api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip\n[2025-08-30 13:12:53] 项目目录: /projects/easyaiot/AI/data/datasets/1\n[2025-08-30 13:12:53] 数据配置文件路径: /projects/easyaiot/AI/data/datasets/1/data.yaml\n[2025-08-30 13:12:53] 检查数据集配置文件...\n[2025-08-30 13:12:53] 加载预训练YOLOv8模型...\n[2025-08-30 13:12:53] 尝试加载预训练模型: model/yolov8n.pt\n		\N	\N	\N
20	1	100	/api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip	{"epochs": 100, "model_arch": "yolov8n.pt", "img_size": 640, "batch_size": 16, "use_gpu": true}	2025-08-30 05:13:49.213499	2025-08-30 05:15:25.148511	completed	[2025-08-30 13:13:50] 开始准备训练数据，项目ID: 1\n[2025-08-30 13:13:50] 获取项目信息成功，项目名称: 人模型\n[2025-08-30 13:13:50] 数据集验证成功，使用原始路径: /api/v1/buckets/datasets/objects/download?prefix=dataset-3.zip\n[2025-08-30 13:13:50] 项目目录: /projects/easyaiot/AI/data/datasets/1\n[2025-08-30 13:13:50] 数据配置文件路径: /projects/easyaiot/AI/data/datasets/1/data.yaml\n[2025-08-30 13:13:50] 检查数据集配置文件...\n[2025-08-30 13:13:51] 加载预训练YOLOv8模型...\n[2025-08-30 13:13:51] 尝试加载预训练模型: yolov8n.pt\n[2025-08-30 13:13:51] 预训练模型加载成功!\n[2025-08-30 13:13:51] 开始训练模型，共100个epochs...\n[2025-08-30 13:13:51] 开始训练模型，配置: 数据文件=/projects/easyaiot/AI/data/datasets/1/data.yaml, epochs=100, 图像尺寸=640x640, 批次大小=16\n[2025-08-30 13:13:51] GPU状态检查: {\n  "pytorch_version": "2.0.1+cu117",\n  "cuda_available": true,\n  "cuda_version": "11.7",\n  "device_count": 1,\n  "device_0_name": "NVIDIA RTX A5000",\n  "device_0_capability": [\n    8,\n    6\n  ]\n}\n[2025-08-30 13:13:52] 使用GPU进行训练: NVIDIA RTX A5000\n[2025-08-30 13:15:16] 训练结果CSV已上传至Minio: /api/v1/buckets/model-train/objects/download?prefix=models/model_1/train_20/results.csv\n[2025-08-30 13:15:17] 训练结果图表已上传至Minio: /api/v1/buckets/model-train/objects/download?prefix=models/model_1/train_20/results.png\n[2025-08-30 13:15:17] 训练完成，正在保存结果...\n[2025-08-30 13:15:18] 模型训练完成!\n[2025-08-30 13:15:18] 训练结果保存路径: /projects/easyaiot/AI/data/datasets/1/train_results\n[2025-08-30 13:15:18] 检查最佳模型文件是否存在: /projects/easyaiot/AI/data/datasets/1/train_results/weights/best.pt\n[2025-08-30 13:15:18] 找到最佳模型文件，开始复制到保存目录: /projects/easyaiot/AI/data/datasets/1/train_results/weights/best.pt\n[2025-08-30 13:15:18] 模型文件已成功复制到保存目录: /projects/easyaiot/AI/static/models/1/train/weights\n[2025-08-30 13:15:18] 开始上传最佳模型到Minio...\n[2025-08-30 13:15:24] 模型已成功上传至Minio: /api/v1/buckets/models/objects/download?prefix=models/model_1/train_20/best.pt\n[2025-08-30 13:15:25] 训练日志已上传至Minio: /api/v1/buckets/log-bucket/objects/download?prefix=logs/model_1/train_20.txt\n[2025-08-30 13:15:25] 模型训练完成并已保存\n	/projects/easyaiot/AI/data/datasets/1/train_results/checkpoints	/api/v1/buckets/model-train/objects/download?prefix=models/model_1/train_20/results.csv	/api/v1/buckets/models/objects/download?prefix=models/model_1/train_20/best.pt	/api/v1/buckets/model-train/objects/download?prefix=models/model_1/train_20/results.png
\.


--
-- Name: ai_service_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.ai_service_id_seq', 3, true);


--
-- Name: export_record_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.export_record_id_seq', 1, true);


--
-- Name: inference_task_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.inference_task_id_seq', 54, true);


--
-- Name: llm_config_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.llm_config_id_seq', 1, false);


--
-- Name: model_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.model_id_seq', 4, true);


--
-- Name: ocr_result_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.ocr_result_id_seq', 1, false);


--
-- Name: speech_record_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.speech_record_id_seq', 1, false);


--
-- Name: train_task_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.train_task_id_seq', 20, true);


--
-- Name: ai_service ai_service_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ai_service
    ADD CONSTRAINT ai_service_pkey PRIMARY KEY (id);


--
-- Name: export_record export_record_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.export_record
    ADD CONSTRAINT export_record_pkey PRIMARY KEY (id);


--
-- Name: inference_task inference_task_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inference_task
    ADD CONSTRAINT inference_task_pkey PRIMARY KEY (id);


--
-- Name: llm_config llm_config_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.llm_config
    ADD CONSTRAINT llm_config_name_key UNIQUE (name);


--
-- Name: llm_config llm_config_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.llm_config
    ADD CONSTRAINT llm_config_pkey PRIMARY KEY (id);


--
-- Name: model model_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.model
    ADD CONSTRAINT model_pkey PRIMARY KEY (id);


--
-- Name: ocr_result ocr_result_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ocr_result
    ADD CONSTRAINT ocr_result_pkey PRIMARY KEY (id);


--
-- Name: speech_record speech_record_order_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.speech_record
    ADD CONSTRAINT speech_record_order_id_key UNIQUE (order_id);


--
-- Name: speech_record speech_record_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.speech_record
    ADD CONSTRAINT speech_record_pkey PRIMARY KEY (id);


--
-- Name: train_task train_task_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.train_task
    ADD CONSTRAINT train_task_pkey PRIMARY KEY (id);


--
-- Name: ai_service ai_service_model_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ai_service
    ADD CONSTRAINT ai_service_model_id_fkey FOREIGN KEY (model_id) REFERENCES public.model(id);


--
-- Name: export_record export_record_model_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.export_record
    ADD CONSTRAINT export_record_model_id_fkey FOREIGN KEY (model_id) REFERENCES public.model(id);


--
-- Name: inference_task inference_task_model_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inference_task
    ADD CONSTRAINT inference_task_model_id_fkey FOREIGN KEY (model_id) REFERENCES public.model(id);


--
-- Name: train_task train_task_model_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.train_task
    ADD CONSTRAINT train_task_model_id_fkey FOREIGN KEY (model_id) REFERENCES public.model(id);


--
-- PostgreSQL database dump complete
--

\unrestrict xhtzy3pIvDsIXl7oi2odys2htmEbmA6btf4B2nNuuFCH8N7NTU0ERUgTAxkhyE2

