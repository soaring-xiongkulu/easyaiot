--
-- PostgreSQL database dump
--

\restrict zr8m9NxfLnjNh5D4bz6iwSUMgNGLRWkY0BSRweRzuOG0lqIAJsS6QjfQvRSjfr1

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
    manufacturer character varying(100),
    model character varying(100),
    firmware_version character varying(100),
    serial_number character varying(300),
    hardware_id character varying(100),
    support_move boolean,
    support_zoom boolean,
    nvr_id integer,
    nvr_channel smallint NOT NULL,
    enable_forward boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.device OWNER TO postgres;

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
-- Name: alert id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alert ALTER COLUMN id SET DEFAULT nextval('public.alert_id_seq'::regclass);


--
-- Name: image id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.image ALTER COLUMN id SET DEFAULT nextval('public.image_id_seq'::regclass);


--
-- Name: nvr id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.nvr ALTER COLUMN id SET DEFAULT nextval('public.nvr_id_seq'::regclass);


--
-- Data for Name: alert; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.alert (id, object, event, region, information, "time", device_id, device_name, image_path, record_path) FROM stdin;
1	person	intrusion	A区	检测到未授权人员进入A区，置信度: 0.95	2025-11-19 23:31:24.506606+08	CAM001	前门摄像头	/data/images/alert_001.jpg	/data/records/alert_001.mp4
2	vehicle	illegal_parking	停车场B区	检测到车辆在禁停区域停留超过5分钟	2025-11-19 23:31:35.563195+08	CAM002	停车场摄像头	/data/images/alert_002.jpg	/data/records/alert_002.mp4
3	fire	fire_detection	仓库C区	检测到疑似火源，温度异常升高	2025-11-19 23:31:35.567243+08	CAM003	仓库监控	/data/images/alert_003.jpg	/data/records/alert_003.mp4
4	person	crowd_gathering	大厅	检测到人员异常聚集，人数超过10人	2025-11-19 23:31:35.57129+08	CAM004	大厅摄像头	/data/images/alert_004.jpg	/data/records/alert_004.mp4
5	bag	abandoned_object	安检区	检测到可疑物品遗留，超过30分钟未移动	2025-11-19 23:31:35.574824+08	CAM005	安检摄像头	/data/images/alert_005.jpg	/data/records/alert_005.mp4
6	person	loitering	D区通道	检测到人员在敏感区域徘徊超过10分钟	2025-11-19 23:31:35.577818+08	CAM006	通道监控	/data/images/alert_006.jpg	/data/records/alert_006.mp4
7	vehicle	overspeed	主干道	检测到车辆超速行驶，速度: 85km/h，限速: 60km/h	2025-11-19 23:31:35.580586+08	CAM007	道路监控	/data/images/alert_007.jpg	/data/records/alert_007.mp4
8	person	abnormal_behavior	E区	检测到异常行为：快速移动并翻越围栏	2025-11-19 23:31:35.583462+08	CAM008	周界监控	/data/images/alert_008.jpg	/data/records/alert_008.mp4
9	smoke	smoke_detection	机房	检测到烟雾，可能发生火灾或设备故障	2025-11-19 23:31:35.58633+08	CAM009	机房监控	/data/images/alert_009.jpg	/data/records/alert_009.mp4
10	person	fall_detection	F区走廊	检测到人员摔倒，可能需要医疗救助	2025-11-19 23:31:35.589036+08	CAM010	走廊监控	/data/images/alert_010.jpg	/data/records/alert_010.mp4
\.


--
-- Data for Name: device; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.device (id, name, source, rtmp_stream, http_stream, stream, ip, port, username, password, mac, manufacturer, model, firmware_version, serial_number, hardware_id, support_move, support_zoom, nvr_id, nvr_channel, enable_forward, created_at, updated_at) FROM stdin;
1756592990129676672	我的设备	rtsp://admin:Zmg1451571@192.168.0.2:554/Streaming/Channels/101?transportmode=unicast&profile=Profile_1	rtmp://localhost:1935/live/1756592990129676672	http://localhost:8080/live/1756592990129676672.flv	0	192.168.0.2	80	admin	Zmg1451571@	50:e5:38:aa:e5:92	HIKVISION	DS-2SC2Q140MY-T/W	V5.8.21	DS-2SC2Q140MY-T/W20250528AACHGA7118735	88	t	t	\N	0	t	2025-08-30 22:29:50.225535	2025-11-24 14:51:36.441867
1763993199200825623	舞蹈室设备	rtmp://localhost:1935/live/video1	rtmp://localhost:1935/live/video1	http://localhost:8080/live/video1.flv	0	localhost	554	admin	Zmg1451571@		EasyAIoT	Camera-EasyAIoT				f	f	\N	0	\N	2025-11-24 14:06:39.203389	2025-11-24 14:51:43.439391
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
-- Name: alert_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.alert_id_seq', 10, true);


--
-- Name: image_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.image_id_seq', 1, false);


--
-- Name: nvr_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.nvr_id_seq', 1, false);


--
-- Name: alert alert_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alert
    ADD CONSTRAINT alert_pkey PRIMARY KEY (id);


--
-- Name: device device_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.device
    ADD CONSTRAINT device_pkey PRIMARY KEY (id);


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
-- Name: device device_nvr_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.device
    ADD CONSTRAINT device_nvr_id_fkey FOREIGN KEY (nvr_id) REFERENCES public.nvr(id) ON DELETE CASCADE;


--
-- Name: image image_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.image
    ADD CONSTRAINT image_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.device(id);


--
-- PostgreSQL database dump complete
--

\unrestrict zr8m9NxfLnjNh5D4bz6iwSUMgNGLRWkY0BSRweRzuOG0lqIAJsS6QjfQvRSjfr1

