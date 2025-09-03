--
-- PostgreSQL database dump
--

-- Dumped from database version 16.2
-- Dumped by pg_dump version 16.2

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
-- Name: export_record; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.export_record (
    id integer NOT NULL,
    model_id integer NOT NULL,
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
-- Name: export_record id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.export_record ALTER COLUMN id SET DEFAULT nextval('public.export_record_id_seq'::regclass);


--
-- Name: inference_task id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inference_task ALTER COLUMN id SET DEFAULT nextval('public.inference_task_id_seq'::regclass);


--
-- Name: model id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.model ALTER COLUMN id SET DEFAULT nextval('public.model_id_seq'::regclass);


--
-- Name: train_task id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.train_task ALTER COLUMN id SET DEFAULT nextval('public.train_task_id_seq'::regclass);


--
-- Data for Name: export_record; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.export_record (id, model_id, format, minio_path, local_path, created_at, status, message) FROM stdin;
\.


--
-- Data for Name: inference_task; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.inference_task (id, model_id, inference_type, input_source, output_path, processed_frames, start_time, end_time, status, error_message, processing_time, stream_output_url) FROM stdin;
\.


--
-- Data for Name: model; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.model (id, name, description, model_path, image_url, version, created_at, updated_at, onnx_model_path, torchscript_model_path, tensorrt_model_path, openvino_model_path, rknn_model_path) FROM stdin;
1	人模型	用于识别人的AI算法	/api/v1/buckets/models/objects/download?prefix=models/model_1/train_20/best.pt	/api/v1/buckets/models/objects/download?prefix=images/6dc4c28fe6444f98955bdc98bcfe6ed4.jpg	V2025.08.5	2025-08-25 10:37:44.147967	2025-08-30 05:22:51.040101	\N	\N	\N	\N	\N
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
-- Name: export_record_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.export_record_id_seq', 1, false);


--
-- Name: inference_task_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.inference_task_id_seq', 1, false);


--
-- Name: model_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.model_id_seq', 1, true);


--
-- Name: train_task_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.train_task_id_seq', 20, true);


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
-- Name: model model_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.model
    ADD CONSTRAINT model_pkey PRIMARY KEY (id);


--
-- Name: train_task train_task_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.train_task
    ADD CONSTRAINT train_task_pkey PRIMARY KEY (id);


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

