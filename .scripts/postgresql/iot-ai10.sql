--
-- PostgreSQL database dump
--

\restrict rRKsOUvShSNQC4IyhkitY44vzbttBmzq1e8g1y2jk6X3BtqMcGIYxUsSNTY814q

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
    sorter_push_url character varying(500),
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
-- Name: frame_extractor; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.frame_extractor (
    id integer NOT NULL,
    camera_name character varying(100) NOT NULL,
    input_source character varying(500) NOT NULL,
    input_type character varying(20) NOT NULL,
    model_id integer NOT NULL,
    service_name character varying(100) NOT NULL,
    sorter_receive_url character varying(500),
    port integer NOT NULL,
    server_ip character varying(50),
    status character varying(20),
    process_id integer,
    frame_skip integer,
    current_frame_index bigint,
    is_enabled boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    last_heartbeat timestamp without time zone
);


ALTER TABLE public.frame_extractor OWNER TO postgres;

--
-- Name: frame_extractor_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.frame_extractor_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.frame_extractor_id_seq OWNER TO postgres;

--
-- Name: frame_extractor_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.frame_extractor_id_seq OWNED BY public.frame_extractor.id;


--
-- Name: frame_sorter; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.frame_sorter (
    id integer NOT NULL,
    service_name character varying(100) NOT NULL,
    receive_url character varying(500) NOT NULL,
    output_url character varying(500),
    port integer NOT NULL,
    server_ip character varying(50),
    status character varying(20),
    process_id integer,
    window_size integer,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    last_heartbeat timestamp without time zone
);


ALTER TABLE public.frame_sorter OWNER TO postgres;

--
-- Name: frame_sorter_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.frame_sorter_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.frame_sorter_id_seq OWNER TO postgres;

--
-- Name: frame_sorter_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.frame_sorter_id_seq OWNED BY public.frame_sorter.id;


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
    openvino_model_path character varying(500)
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
-- Name: frame_extractor id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.frame_extractor ALTER COLUMN id SET DEFAULT nextval('public.frame_extractor_id_seq'::regclass);


--
-- Name: frame_sorter id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.frame_sorter ALTER COLUMN id SET DEFAULT nextval('public.frame_sorter_id_seq'::regclass);


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

COPY public.ai_service (id, model_id, service_name, server_ip, port, inference_endpoint, status, mac_address, deploy_time, last_heartbeat, process_id, log_path, model_version, format, sorter_push_url, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: export_record; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.export_record (id, model_id, model_name, format, minio_path, local_path, created_at, status, message) FROM stdin;
\.


--
-- Data for Name: frame_extractor; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.frame_extractor (id, camera_name, input_source, input_type, model_id, service_name, sorter_receive_url, port, server_ip, status, process_id, frame_skip, current_frame_index, is_enabled, created_at, updated_at, last_heartbeat) FROM stdin;
\.


--
-- Data for Name: frame_sorter; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.frame_sorter (id, service_name, receive_url, output_url, port, server_ip, status, process_id, window_size, created_at, updated_at, last_heartbeat) FROM stdin;
\.


--
-- Data for Name: inference_task; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.inference_task (id, model_id, inference_type, input_source, output_path, processed_frames, start_time, end_time, status, error_message, processing_time, stream_output_url) FROM stdin;
\.


--
-- Data for Name: llm_config; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.llm_config (id, name, description, model_type, icon_url, vendor, base_url, api_key, model, api_version, request_timeout, max_retries, context_window, max_output_tokens, supported_features, temperature, system_prompt, is_customizable, rag_enabled, prompt_template, domain_adaptation, input_token_price, output_token_price, avg_response_time, total_tokens_used, monthly_budget, is_active, status, created_at, updated_at, last_test_time) FROM stdin;
\.


--
-- Data for Name: model; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.model (id, name, description, model_path, image_url, version, created_at, updated_at, onnx_model_path, torchscript_model_path, tensorrt_model_path, openvino_model_path) FROM stdin;
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
\.


--
-- Name: ai_service_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.ai_service_id_seq', 1, false);


--
-- Name: export_record_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.export_record_id_seq', 1, false);


--
-- Name: frame_extractor_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.frame_extractor_id_seq', 1, false);


--
-- Name: frame_sorter_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.frame_sorter_id_seq', 1, false);


--
-- Name: inference_task_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.inference_task_id_seq', 1, false);


--
-- Name: llm_config_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.llm_config_id_seq', 1, false);


--
-- Name: model_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.model_id_seq', 1, false);


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

SELECT pg_catalog.setval('public.train_task_id_seq', 1, false);


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
-- Name: frame_extractor frame_extractor_camera_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.frame_extractor
    ADD CONSTRAINT frame_extractor_camera_name_key UNIQUE (camera_name);


--
-- Name: frame_extractor frame_extractor_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.frame_extractor
    ADD CONSTRAINT frame_extractor_pkey PRIMARY KEY (id);


--
-- Name: frame_sorter frame_sorter_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.frame_sorter
    ADD CONSTRAINT frame_sorter_pkey PRIMARY KEY (id);


--
-- Name: frame_sorter frame_sorter_service_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.frame_sorter
    ADD CONSTRAINT frame_sorter_service_name_key UNIQUE (service_name);


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
-- Name: model model_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.model
    ADD CONSTRAINT model_name_key UNIQUE (name);


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
-- Name: frame_extractor frame_extractor_model_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.frame_extractor
    ADD CONSTRAINT frame_extractor_model_id_fkey FOREIGN KEY (model_id) REFERENCES public.model(id);


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

\unrestrict rRKsOUvShSNQC4IyhkitY44vzbttBmzq1e8g1y2jk6X3BtqMcGIYxUsSNTY814q

