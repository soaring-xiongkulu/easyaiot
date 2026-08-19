--
-- PostgreSQL database dump
--

\restrict rKgUTqhVdPDZrzcgKcGm4jkXOHz5nv2NjEd0s49H9maOB8hmbCzrESvcLMCfLg2

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

DROP DATABASE IF EXISTS "iot-node20";
--
-- Name: iot-node20; Type: DATABASE; Schema: -; Owner: -
--

CREATE DATABASE "iot-node20" WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'en_US.utf8';


\unrestrict rKgUTqhVdPDZrzcgKcGm4jkXOHz5nv2NjEd0s49H9maOB8hmbCzrESvcLMCfLg2
\encoding SQL_ASCII
\connect -reuse-previous=on "dbname='iot-node20'"
\restrict rKgUTqhVdPDZrzcgKcGm4jkXOHz5nv2NjEd0s49H9maOB8hmbCzrESvcLMCfLg2

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
-- Name: compute_node_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.compute_node_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: compute_node; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.compute_node (
    id bigint DEFAULT nextval('public.compute_node_id_seq'::regclass) NOT NULL,
    name character varying(64) NOT NULL,
    host character varying(128) NOT NULL,
    ssh_port integer DEFAULT 22,
    agent_port integer DEFAULT 9100,
    status character varying(16) DEFAULT 'pending'::character varying,
    node_role character varying(256) NOT NULL,
    region character varying(64),
    tags jsonb,
    capabilities jsonb,
    max_gpu_count integer DEFAULT 0,
    max_task_count integer DEFAULT 50,
    weight integer DEFAULT 100,
    agent_token character varying(128),
    remark character varying(256),
    last_heartbeat_at timestamp without time zone,
    creator character varying(64),
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updater character varying(64),
    update_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    deleted smallint DEFAULT 0,
    control_plane_id bigint
);


--
-- Name: COLUMN compute_node.control_plane_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.compute_node.control_plane_id IS '所属中心节点（平台节点）ID';


--
-- Name: control_plane_peer_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.control_plane_peer_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: control_plane_peer; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.control_plane_peer (
    id bigint DEFAULT nextval('public.control_plane_peer_id_seq'::regclass) NOT NULL,
    name character varying(128) NOT NULL,
    api_base_url character varying(512) NOT NULL,
    host character varying(128),
    peer_token character varying(128),
    status character varying(32) DEFAULT 'pending'::character varying,
    remote_platform_node_id bigint,
    last_sync_at timestamp without time zone,
    remark character varying(256),
    creator character varying(64),
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updater character varying(64),
    update_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    deleted smallint DEFAULT 0
);


--
-- Name: device_media_binding_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.device_media_binding_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: device_media_binding; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.device_media_binding (
    id bigint DEFAULT nextval('public.device_media_binding_id_seq'::regclass) NOT NULL,
    device_id character varying(100) NOT NULL,
    srs_live_node_id bigint,
    srs_ai_node_id bigint,
    zlm_node_id bigint,
    rtmp_stream character varying(512),
    http_stream character varying(512),
    ai_rtmp_stream character varying(512),
    ai_http_stream character varying(512),
    zlm_host character varying(128),
    zlm_http_port integer,
    zlm_rtmp_port integer,
    region character varying(64),
    status character varying(16) DEFAULT 'active'::character varying,
    creator character varying(64),
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updater character varying(64),
    update_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    deleted smallint DEFAULT 0
);


--
-- Name: edge_node; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.edge_node (
    id bigint NOT NULL,
    compute_node_id bigint NOT NULL,
    name character varying(128) NOT NULL,
    host character varying(128) NOT NULL,
    status character varying(32) DEFAULT 'offline'::character varying NOT NULL,
    fingerprint character varying(128),
    mqtt_client_id character varying(128),
    mqtt_username character varying(128),
    agent_version character varying(64),
    node_role character varying(32) DEFAULT 'compute'::character varying,
    max_task_count integer DEFAULT 1,
    active_task_count integer DEFAULT 0,
    ceph_mount_ready boolean DEFAULT false,
    last_heartbeat_at timestamp without time zone,
    enabled boolean DEFAULT true NOT NULL,
    remark character varying(512),
    tags jsonb,
    creator character varying(64) DEFAULT ''::character varying,
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updater character varying(64) DEFAULT ''::character varying,
    update_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted smallint DEFAULT 0 NOT NULL
);


--
-- Name: TABLE edge_node; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.edge_node IS '边缘算法运行时节点统一管理表';


--
-- Name: COLUMN edge_node.compute_node_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.edge_node.compute_node_id IS '关联 compute_node.id';


--
-- Name: COLUMN edge_node.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.edge_node.status IS 'online / offline / disabled';


--
-- Name: COLUMN edge_node.ceph_mount_ready; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.edge_node.ceph_mount_ready IS 'CephFS 挂载是否就绪（调度前置条件）';


--
-- Name: COLUMN edge_node.enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.edge_node.enabled IS '是否参与调度';


--
-- Name: COLUMN edge_node.deleted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.edge_node.deleted IS '逻辑删除：0 未删，1 已删';


--
-- Name: edge_node_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.edge_node_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: edge_node_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.edge_node_id_seq OWNED BY public.edge_node.id;


--
-- Name: nfs_cluster_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.nfs_cluster_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: nfs_cluster; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.nfs_cluster (
    id bigint DEFAULT nextval('public.nfs_cluster_id_seq'::regclass) NOT NULL,
    name character varying(128) NOT NULL,
    lane_key character varying(64) NOT NULL,
    control_plane_id bigint,
    primary_node_id bigint,
    standby_node_id bigint,
    mount_root character varying(256) DEFAULT '/mnt/easyaiot-media'::character varying,
    nfs_export character varying(256),
    nfs_mount_opts character varying(128) DEFAULT 'vers=3,tcp,nolock,_netdev'::character varying,
    is_active boolean DEFAULT false NOT NULL,
    status character varying(32) DEFAULT 'active'::character varying,
    remark character varying(256),
    creator character varying(64),
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updater character varying(64),
    update_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    deleted smallint DEFAULT 0 NOT NULL,
    tenant_id bigint DEFAULT 0
);


--
-- Name: nfs_cluster_bridge_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.nfs_cluster_bridge_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: nfs_cluster_bridge; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.nfs_cluster_bridge (
    id bigint DEFAULT nextval('public.nfs_cluster_bridge_id_seq'::regclass) NOT NULL,
    name character varying(128),
    source_cluster_id bigint NOT NULL,
    target_cluster_id bigint NOT NULL,
    source_rel_paths character varying(512) DEFAULT 'alert_images,playbacks,snaps'::character varying,
    target_rel_path character varying(256),
    schedule_cron character varying(64),
    enabled boolean DEFAULT true NOT NULL,
    status character varying(32) DEFAULT 'idle'::character varying,
    last_run_at timestamp without time zone,
    last_success boolean,
    last_message character varying(1024),
    creator character varying(64),
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updater character varying(64),
    update_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    deleted smallint DEFAULT 0 NOT NULL,
    tenant_id bigint DEFAULT 0
);


--
-- Name: node_metric_snapshot_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.node_metric_snapshot_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: node_metric_snapshot; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.node_metric_snapshot (
    id bigint DEFAULT nextval('public.node_metric_snapshot_id_seq'::regclass) NOT NULL,
    node_id bigint NOT NULL,
    cpu_percent numeric(5,2),
    mem_percent numeric(5,2),
    disk_percent numeric(5,2),
    gpu_info jsonb,
    active_tasks integer DEFAULT 0,
    bandwidth_mbps numeric(10,2),
    collected_at timestamp without time zone NOT NULL,
    creator character varying(64),
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updater character varying(64),
    update_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    deleted smallint DEFAULT 0,
    mem_used_bytes bigint,
    mem_total_bytes bigint,
    disk_used_bytes bigint,
    disk_total_bytes bigint
);


--
-- Name: node_ssh_credential_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.node_ssh_credential_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: node_ssh_credential; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.node_ssh_credential (
    id bigint DEFAULT nextval('public.node_ssh_credential_id_seq'::regclass) NOT NULL,
    node_id bigint NOT NULL,
    auth_type character varying(16) DEFAULT 'password'::character varying NOT NULL,
    username character varying(64) NOT NULL,
    credential_enc text NOT NULL,
    public_key_fp character varying(64),
    last_test_at timestamp without time zone,
    last_test_ok boolean,
    creator character varying(64),
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updater character varying(64),
    update_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    deleted smallint DEFAULT 0
);


--
-- Name: node_storage_op_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.node_storage_op_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: node_storage_op_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.node_storage_op_log (
    id bigint DEFAULT nextval('public.node_storage_op_log_id_seq'::regclass) NOT NULL,
    node_id bigint,
    op_type character varying(32) NOT NULL,
    success boolean DEFAULT false,
    message character varying(1024),
    steps_json text,
    creator character varying(64),
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updater character varying(64),
    update_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    deleted smallint DEFAULT 0 NOT NULL
);


--
-- Name: node_workload_binding_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.node_workload_binding_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: node_workload_binding; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.node_workload_binding (
    id bigint DEFAULT nextval('public.node_workload_binding_id_seq'::regclass) NOT NULL,
    node_id bigint NOT NULL,
    workload_type character varying(32) NOT NULL,
    workload_id character varying(64) NOT NULL,
    status character varying(16) DEFAULT 'running'::character varying,
    process_pid integer,
    bind_at timestamp without time zone,
    creator character varying(64),
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updater character varying(64),
    update_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    deleted smallint DEFAULT 0
);


--
-- Name: edge_node id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.edge_node ALTER COLUMN id SET DEFAULT nextval('public.edge_node_id_seq'::regclass);


--
-- Data for Name: compute_node; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.compute_node (id, name, host, ssh_port, agent_port, status, node_role, region, tags, capabilities, max_gpu_count, max_task_count, weight, agent_token, remark, last_heartbeat_at, creator, create_time, updater, update_time, deleted, control_plane_id) FROM stdin;
2	NFS-Storage-01	192.168.1.11	22	9100	pending	nfs	\N	{"nfs_role": "server","nfs_export": "/mnt/easyaiot-media","nfs_probe_at": "2026-08-12T06:27:56.519563392Z","nfs_probe_ok": "true","ceph_mon_host": "192.168.1.11","ceph_osd_path": "/var/lib/ceph/osd","nfs_cluster_id": "1","nfs_mount_opts": "vers=3,tcp,nolock,_netdev","ceph_mount_path": "/mnt/easyaiot-media","nfs_mount_ready": "true","nfs_server_host": "192.168.1.11","storage_backend": "nfs","ceph_mount_ready": "true","media_mount_path": "/mnt/easyaiot-media","nfs_cluster_role": "primary","nfs_export_ready": "true","nfs_probe_summary": "NFS 存储已就绪：Export 正常，客户端已挂载至 /mnt/easyaiot-media"}	{"ceph_osd": true, "media_storage": true}	0	50	100	d92c6783e84b6c7c64ca378656fcb115	\N	\N	\N	2026-08-11 15:13:47.308782	1	2026-08-12 14:27:56.520608	0	1
1	控制面节点	192.168.1.10	22	9100	online	algorithm,forward,live,nfs	\N	{"nfs_role": "client","nfs_export": "/mnt/easyaiot-media","nfs_probe_at": "2026-08-12T06:27:56.561629314Z","nfs_probe_ok": "true","ceph_mon_host": "192.168.1.11","agent_hostname": "demo-node","nfs_cluster_id": "1","nfs_mount_opts": "vers=3,tcp,nolock,_netdev","ceph_mount_path": "/tmp/easyaiot-media","nfs_mount_ready": "true","nfs_server_host": "192.168.1.11","storage_backend": "nfs","ceph_mount_ready": "true","media_mount_path": "/tmp/easyaiot-media","nfs_cluster_role": "client","nfs_mount_source": "local:/tmp/easyaiot-media","nfs_probe_summary": "batch-refresh: local media ready","agent_mem_total_bytes": "66009735168","agent_disk_total_bytes": "1005867986944"}	{"zlm": true, "srs_ai": true, "platform": true, "srs_live": true, "auto_label": true, "model_train": true, "ai_inference": true, "llm_inference": true, "algorithm_snap": true, "stream_forward": true, "algorithm_patrol": true, "algorithm_realtime": true}	0	50	100	cd3d4d946d7446a913f846b92ad94557	平台控制面宿主机，自动纳管	2026-08-12 14:35:42.300706	\N	2026-07-14 16:35:07.615462	1	2026-08-12 14:35:42.301037	0	1
3	NFS-Client-01	192.168.1.12	22	9100	pending	algorithm,forward,live,train,llm,label,infer	\N	{"nfs_role": "client","nfs_export": "/mnt/easyaiot-media","nfs_probe_at": "2026-08-12T06:28:00.006608648Z","nfs_probe_ok": "false","ceph_mon_host": "192.168.1.11","nfs_cluster_id": "1","nfs_mount_opts": "vers=3,tcp,nolock,_netdev","ceph_mount_path": "/mnt/easyaiot-media","nfs_mount_ready": "false","nfs_server_host": "192.168.1.11","storage_backend": "nfs","ceph_mount_ready": "false","media_mount_path": "/mnt/easyaiot-media","nfs_cluster_role": "client","nfs_export_ready": "false","nfs_probe_summary": "NFS 未挂载至 /mnt/easyaiot-media，请执行客户端挂载部署"}	{"zlm": true, "srs_ai": true, "srs_live": true, "auto_label": true, "model_train": true, "ai_inference": true, "llm_inference": true, "algorithm_snap": true, "stream_forward": true, "algorithm_patrol": true, "algorithm_realtime": true}	0	50	100	0ec4652835ee5d457fd3e73d007c280a	\N	\N	\N	2026-08-11 15:13:55.843354	1	2026-08-12 14:28:00.006898	0	1
\.


--
-- Data for Name: control_plane_peer; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.control_plane_peer (id, name, api_base_url, host, peer_token, status, remote_platform_node_id, last_sync_at, remark, creator, create_time, updater, update_time, deleted) FROM stdin;
\.


--
-- Data for Name: device_media_binding; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.device_media_binding (id, device_id, srs_live_node_id, srs_ai_node_id, zlm_node_id, rtmp_stream, http_stream, ai_rtmp_stream, ai_http_stream, zlm_host, zlm_http_port, zlm_rtmp_port, region, status, creator, create_time, updater, update_time, deleted) FROM stdin;
\.


--
-- Data for Name: edge_node; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.edge_node (id, compute_node_id, name, host, status, fingerprint, mqtt_client_id, mqtt_username, agent_version, node_role, max_task_count, active_task_count, ceph_mount_ready, last_heartbeat_at, enabled, remark, tags, creator, create_time, updater, update_time, deleted) FROM stdin;
\.


--
-- Data for Name: nfs_cluster; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.nfs_cluster (id, name, lane_key, control_plane_id, primary_node_id, standby_node_id, mount_root, nfs_export, nfs_mount_opts, is_active, status, remark, creator, create_time, updater, update_time, deleted, tenant_id) FROM stdin;
2	客户三方 NFS（模拟）	customer-sim	1	1	\N	/tmp/easyaiot-customer-media	/tmp/easyaiot-customer-media	vers=3,tcp,nolock,_netdev	f	active	模拟客户/三方	\N	2026-08-12 13:33:13.104525	\N	2026-08-12 13:34:02.424322	0	0
1	控制面节点 NFS	local	1	2	\N	/mnt/easyaiot-media	/mnt/easyaiot-media	vers=3,tcp,nolock,_netdev	t	active	\N	\N	2026-08-12 13:32:38.92004	1	2026-08-12 13:35:31.756787	0	0
\.


--
-- Data for Name: nfs_cluster_bridge; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.nfs_cluster_bridge (id, name, source_cluster_id, target_cluster_id, source_rel_paths, target_rel_path, schedule_cron, enabled, status, last_run_at, last_success, last_message, creator, create_time, updater, update_time, deleted, tenant_id) FROM stdin;
2	客户→原主集群	2	1	alert_images,playbacks	_bridge/2	\N	f	stopped	2026-08-12 13:34:01.972741	t	主集群切换：已自动停止桥接	\N	2026-08-12 13:34:01.323867	\N	2026-08-12 13:34:02.420271	0	0
1	主集群→客户三方	1	2	alert_images,playbacks,snaps	_bridge/1	\N	t	idle	2026-08-12 13:34:03.735648	t	同步完成：写入 11 个文件，跳过过大/异常 0（目标 _bridge/1；首次含历史全量，后续增量）	\N	2026-08-12 13:33:59.464585	\N	2026-08-12 13:34:03.735859	0	0
\.


--
-- Data for Name: node_metric_snapshot; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.node_metric_snapshot (id, node_id, cpu_percent, mem_percent, disk_percent, gpu_info, active_tasks, bandwidth_mbps, collected_at, creator, create_time, updater, update_time, deleted, mem_used_bytes, mem_total_bytes, disk_used_bytes, disk_total_bytes) FROM stdin;
26390	1	81.20	76.60	84.40	[]	0	0.00	2026-08-12 14:30:36.475237	\N	2026-08-12 14:30:36.476124	\N	2026-08-12 14:30:36.476124	0	50552430592	66009735168	805376778240	1005867986944
26391	1	89.70	76.70	84.40	[]	0	0.00	2026-08-12 14:30:47.016692	\N	2026-08-12 14:30:47.0188	\N	2026-08-12 14:30:47.0188	0	50641768448	66009735168	805377273856	1005867986944
26392	1	87.70	76.70	84.40	[]	0	0.00	2026-08-12 14:30:57.561808	\N	2026-08-12 14:30:57.563026	\N	2026-08-12 14:30:57.563026	0	50658525184	66009735168	805377880064	1005867986944
26393	1	84.70	76.90	84.40	[]	0	0.00	2026-08-12 14:31:08.109662	\N	2026-08-12 14:31:08.110956	\N	2026-08-12 14:31:08.110956	0	50758770688	66009735168	805378211840	1005867986944
26394	1	90.90	77.20	84.40	[]	0	0.00	2026-08-12 14:31:18.674453	\N	2026-08-12 14:31:18.67568	\N	2026-08-12 14:31:18.67568	0	50953715712	66009735168	805378240512	1005867986944
26395	1	68.20	77.90	84.40	[]	0	0.00	2026-08-12 14:31:29.239486	\N	2026-08-12 14:31:29.241435	\N	2026-08-12 14:31:29.241435	0	51431317504	66009735168	805384085504	1005867986944
26396	1	86.30	77.60	84.40	[]	0	0.00	2026-08-12 14:31:39.794282	\N	2026-08-12 14:31:39.795765	\N	2026-08-12 14:31:39.795765	0	51202592768	66009735168	805385654272	1005867986944
26397	1	88.40	76.60	84.40	[]	0	0.00	2026-08-12 14:31:50.349732	\N	2026-08-12 14:31:50.351455	\N	2026-08-12 14:31:50.351455	0	50534490112	66009735168	805386874880	1005867986944
26398	1	85.00	76.20	84.40	[]	0	0.00	2026-08-12 14:32:00.888413	\N	2026-08-12 14:32:00.889413	\N	2026-08-12 14:32:00.889413	0	50300325888	66009735168	805387661312	1005867986944
26399	1	53.00	76.30	84.40	[]	0	0.00	2026-08-12 14:32:11.449034	\N	2026-08-12 14:32:11.451515	\N	2026-08-12 14:32:11.451515	0	50350280704	66009735168	805388316672	1005867986944
26400	1	34.60	76.30	84.40	[]	0	0.00	2026-08-12 14:32:21.993551	\N	2026-08-12 14:32:21.995912	\N	2026-08-12 14:32:21.995912	0	50366722048	66009735168	805388591104	1005867986944
26401	1	81.90	76.60	84.40	[]	0	0.00	2026-08-12 14:32:32.534667	\N	2026-08-12 14:32:32.535954	\N	2026-08-12 14:32:32.535954	0	50563702784	66009735168	805392900096	1005867986944
26402	1	72.50	76.60	84.40	[]	0	0.00	2026-08-12 14:32:43.068691	\N	2026-08-12 14:32:43.071636	\N	2026-08-12 14:32:43.071636	0	50558156800	66009735168	805393244160	1005867986944
26403	1	97.90	76.70	84.40	[]	0	0.00	2026-08-12 14:32:53.639814	\N	2026-08-12 14:32:53.64105	\N	2026-08-12 14:32:53.64105	0	50645442560	66009735168	805393383424	1005867986944
26404	1	84.20	76.60	84.40	[]	0	0.00	2026-08-12 14:33:04.180275	\N	2026-08-12 14:33:04.182017	\N	2026-08-12 14:33:04.182017	0	50586669056	66009735168	805398380544	1005867986944
26405	1	49.60	76.70	84.40	[]	0	0.00	2026-08-12 14:33:14.764678	\N	2026-08-12 14:33:14.765657	\N	2026-08-12 14:33:14.765657	0	50600878080	66009735168	805398466560	1005867986944
26406	1	91.10	76.60	84.40	[]	0	0.00	2026-08-12 14:33:25.299864	\N	2026-08-12 14:33:25.301001	\N	2026-08-12 14:33:25.301001	0	50581127168	66009735168	805398589440	1005867986944
26407	1	84.70	76.40	84.40	[]	0	0.00	2026-08-12 14:33:35.83314	\N	2026-08-12 14:33:35.834187	\N	2026-08-12 14:33:35.834187	0	50436014080	66009735168	805398851584	1005867986944
26408	1	50.00	76.70	84.40	[]	0	0.00	2026-08-12 14:33:46.367782	\N	2026-08-12 14:33:46.368603	\N	2026-08-12 14:33:46.368603	0	50600251392	66009735168	805399236608	1005867986944
26409	1	85.80	76.50	84.40	[]	0	0.00	2026-08-12 14:33:56.903646	\N	2026-08-12 14:33:56.904547	\N	2026-08-12 14:33:56.904547	0	50512191488	66009735168	805399412736	1005867986944
26410	1	82.30	76.30	84.40	[]	0	0.00	2026-08-12 14:34:07.431299	\N	2026-08-12 14:34:07.432361	\N	2026-08-12 14:34:07.432361	0	50387886080	66009735168	805399748608	1005867986944
26411	1	83.70	76.60	84.40	[]	0	0.00	2026-08-12 14:34:17.968116	\N	2026-08-12 14:34:17.968995	\N	2026-08-12 14:34:17.968995	0	50560073728	66009735168	805400137728	1005867986944
26412	1	79.20	76.90	84.40	[]	0	0.00	2026-08-12 14:34:28.494882	\N	2026-08-12 14:34:28.495541	\N	2026-08-12 14:34:28.495541	0	50767994880	66009735168	805405184000	1005867986944
26413	1	90.50	77.20	84.40	[]	0	0.00	2026-08-12 14:34:39.025898	\N	2026-08-12 14:34:39.026866	\N	2026-08-12 14:34:39.026866	0	50967916544	66009735168	805405667328	1005867986944
26414	1	52.80	77.50	84.40	[]	0	0.00	2026-08-12 14:34:49.571128	\N	2026-08-12 14:34:49.572879	\N	2026-08-12 14:34:49.572879	0	51165675520	66009735168	805406351360	1005867986944
26415	1	88.00	77.40	84.40	[]	0	0.00	2026-08-12 14:35:00.117621	\N	2026-08-12 14:35:00.119548	\N	2026-08-12 14:35:00.119548	0	51107520512	66009735168	805406490624	1005867986944
26416	1	85.10	77.40	84.40	[]	0	0.00	2026-08-12 14:35:10.653563	\N	2026-08-12 14:35:10.654531	\N	2026-08-12 14:35:10.654531	0	51117608960	66009735168	805406777344	1005867986944
26417	1	57.50	77.00	84.40	[]	0	0.00	2026-08-12 14:35:21.18299	\N	2026-08-12 14:35:21.183741	\N	2026-08-12 14:35:21.183741	0	50810327040	66009735168	805407027200	1005867986944
26418	1	77.70	76.80	84.40	[]	0	0.00	2026-08-12 14:35:31.733051	\N	2026-08-12 14:35:31.733982	\N	2026-08-12 14:35:31.733982	0	50706747392	66009735168	805407084544	1005867986944
26419	1	95.70	77.00	84.40	[]	0	0.00	2026-08-12 14:35:42.302845	\N	2026-08-12 14:35:42.304807	\N	2026-08-12 14:35:42.304807	0	50844766208	66009735168	805408034816	1005867986944
\.


--
-- Data for Name: node_ssh_credential; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.node_ssh_credential (id, node_id, auth_type, username, credential_enc, public_key_fp, last_test_at, last_test_ok, creator, create_time, updater, update_time, deleted) FROM stdin;
1	2	password	demo	ZGVtb19zc2hfcGFzc3dvcmQ=	\N	2026-08-11 15:13:56.070491	t	\N	2026-08-11 15:13:47.739113	\N	2026-08-11 15:13:56.072162	0
2	3	password	demo	ZGVtb19zc2hfcGFzc3dvcmQ=	\N	2026-08-11 15:13:56.351247	t	\N	2026-08-11 15:13:55.848203	\N	2026-08-11 15:13:56.351882	0
\.


--
-- Data for Name: node_storage_op_log; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.node_storage_op_log (id, node_id, op_type, success, message, steps_json, creator, create_time, updater, update_time, deleted) FROM stdin;
86	3	auto_refresh	t	NFS 未挂载至 /mnt/easyaiot-media，请执行客户端挂载部署	[{"name":"SSH 连接","status":"success","output":"已连接 192.168.1.12:22"},{"name":"挂载源","status":"failed","output":"未能确认挂载源"},{"name":"NFS 挂载","status":"failed","output":"NFS 未挂载"},{"name":"读写探针","status":"failed","output":"挂载根不可写或未挂载"}]	\N	2026-08-12 13:14:39.615663	\N	2026-08-12 13:14:39.615663	0
87	\N	auto_refresh	t	刷新完成：成功 3，失败 0，跳过 0	\N	\N	2026-08-12 13:14:39.620783	\N	2026-08-12 13:14:39.620783	0
88	2	auto_refresh	t	NFS 存储已就绪：Export 正常，客户端已挂载至 /mnt/easyaiot-media	[{"name":"SSH 连接","status":"success","output":"已连接 192.168.1.11:22"},{"name":"NFS 服务端","status":"success","output":"NFS 服务端 正常"},{"name":"NFS Export","status":"success","output":"NFS Export 正常"},{"name":"NFS 2049","status":"success","output":"NFS 2049 正常"},{"name":"挂载源","status":"success","output":"挂载源匹配或本机回退"},{"name":"媒体子目录","status":"success","output":"alert_images / playbacks / snaps 已就绪"},{"name":"NFS 挂载","status":"success","output":"挂载点 /mnt/easyaiot-media 已就绪"},{"name":"读写探针","status":"success","output":"挂载根可写"}]	\N	2026-08-12 13:29:41.458679	\N	2026-08-12 13:29:41.458679	0
89	3	auto_refresh	t	NFS 未挂载至 /mnt/easyaiot-media，请执行客户端挂载部署	[{"name":"SSH 连接","status":"success","output":"已连接 192.168.1.12:22"},{"name":"挂载源","status":"failed","output":"未能确认挂载源"},{"name":"NFS 挂载","status":"failed","output":"NFS 未挂载"},{"name":"读写探针","status":"failed","output":"挂载根不可写或未挂载"}]	\N	2026-08-12 13:29:44.649226	\N	2026-08-12 13:29:44.649226	0
90	\N	auto_refresh	t	刷新完成：成功 3，失败 0，跳过 0	\N	\N	2026-08-12 13:29:44.654469	\N	2026-08-12 13:29:44.654469	0
91	2	refresh	t	NFS 存储已就绪：Export 正常，客户端已挂载至 /mnt/easyaiot-media	[{"name":"SSH 连接","status":"success","output":"已连接 192.168.1.11:22"},{"name":"NFS 服务端","status":"success","output":"NFS 服务端 正常"},{"name":"NFS Export","status":"success","output":"NFS Export 正常"},{"name":"NFS 2049","status":"success","output":"NFS 2049 正常"},{"name":"挂载源","status":"success","output":"挂载源匹配或本机回退"},{"name":"媒体子目录","status":"success","output":"alert_images / playbacks / snaps 已就绪"},{"name":"NFS 挂载","status":"success","output":"挂载点 /mnt/easyaiot-media 已就绪"},{"name":"读写探针","status":"success","output":"挂载根可写"}]	1	2026-08-12 13:35:35.484287	1	2026-08-12 13:35:35.484287	0
92	3	refresh	t	NFS 未挂载至 /mnt/easyaiot-media，请执行客户端挂载部署	[{"name":"SSH 连接","status":"success","output":"已连接 192.168.1.12:22"},{"name":"挂载源","status":"failed","output":"未能确认挂载源"},{"name":"NFS 挂载","status":"failed","output":"NFS 未挂载"},{"name":"读写探针","status":"failed","output":"挂载根不可写或未挂载"}]	1	2026-08-12 13:35:38.432358	1	2026-08-12 13:35:38.432358	0
93	\N	refresh	t	刷新完成：成功 3，失败 0，跳过 0	\N	1	2026-08-12 13:35:38.440874	1	2026-08-12 13:35:38.440874	0
94	2	auto_refresh	t	NFS 存储已就绪：Export 正常，客户端已挂载至 /mnt/easyaiot-media	[{"name":"SSH 连接","status":"success","output":"已连接 192.168.1.11:22"},{"name":"NFS 服务端","status":"success","output":"NFS 服务端 正常"},{"name":"NFS Export","status":"success","output":"NFS Export 正常"},{"name":"NFS 2049","status":"success","output":"NFS 2049 正常"},{"name":"挂载源","status":"success","output":"挂载源匹配或本机回退"},{"name":"媒体子目录","status":"success","output":"alert_images / playbacks / snaps 已就绪"},{"name":"NFS 挂载","status":"success","output":"挂载点 /mnt/easyaiot-media 已就绪"},{"name":"读写探针","status":"success","output":"挂载根可写"}]	\N	2026-08-12 13:42:35.665469	\N	2026-08-12 13:42:35.665469	0
95	3	auto_refresh	t	NFS 未挂载至 /mnt/easyaiot-media，请执行客户端挂载部署	[{"name":"SSH 连接","status":"success","output":"已连接 192.168.1.12:22"},{"name":"挂载源","status":"failed","output":"未能确认挂载源"},{"name":"NFS 挂载","status":"failed","output":"NFS 未挂载"},{"name":"读写探针","status":"failed","output":"挂载根不可写或未挂载"}]	\N	2026-08-12 13:42:40.53966	\N	2026-08-12 13:42:40.53966	0
96	\N	auto_refresh	t	刷新完成：成功 3，失败 0，跳过 0	\N	\N	2026-08-12 13:42:40.549306	\N	2026-08-12 13:42:40.549306	0
97	2	auto_refresh	t	NFS 存储已就绪：Export 正常，客户端已挂载至 /mnt/easyaiot-media	[{"name":"SSH 连接","status":"success","output":"已连接 192.168.1.11:22"},{"name":"NFS 服务端","status":"success","output":"NFS 服务端 正常"},{"name":"NFS Export","status":"success","output":"NFS Export 正常"},{"name":"NFS 2049","status":"success","output":"NFS 2049 正常"},{"name":"挂载源","status":"success","output":"挂载源匹配或本机回退"},{"name":"媒体子目录","status":"success","output":"alert_images / playbacks / snaps 已就绪"},{"name":"NFS 挂载","status":"success","output":"挂载点 /mnt/easyaiot-media 已就绪"},{"name":"读写探针","status":"success","output":"挂载根可写"}]	\N	2026-08-12 13:57:42.792244	\N	2026-08-12 13:57:42.792244	0
98	3	auto_refresh	t	NFS 未挂载至 /mnt/easyaiot-media，请执行客户端挂载部署	[{"name":"SSH 连接","status":"success","output":"已连接 192.168.1.12:22"},{"name":"挂载源","status":"failed","output":"未能确认挂载源"},{"name":"NFS 挂载","status":"failed","output":"NFS 未挂载"},{"name":"读写探针","status":"failed","output":"挂载根不可写或未挂载"}]	\N	2026-08-12 13:57:45.781444	\N	2026-08-12 13:57:45.781444	0
99	\N	auto_refresh	t	刷新完成：成功 3，失败 0，跳过 0	\N	\N	2026-08-12 13:57:45.791724	\N	2026-08-12 13:57:45.791724	0
100	2	auto_refresh	t	NFS 存储已就绪：Export 正常，客户端已挂载至 /mnt/easyaiot-media	[{"name":"SSH 连接","status":"success","output":"已连接 192.168.1.11:22"},{"name":"NFS 服务端","status":"success","output":"NFS 服务端 正常"},{"name":"NFS Export","status":"success","output":"NFS Export 正常"},{"name":"NFS 2049","status":"success","output":"NFS 2049 正常"},{"name":"挂载源","status":"success","output":"挂载源匹配或本机回退"},{"name":"媒体子目录","status":"success","output":"alert_images / playbacks / snaps 已就绪"},{"name":"NFS 挂载","status":"success","output":"挂载点 /mnt/easyaiot-media 已就绪"},{"name":"读写探针","status":"success","output":"挂载根可写"}]	\N	2026-08-12 14:12:49.889039	\N	2026-08-12 14:12:49.889039	0
101	3	auto_refresh	t	NFS 未挂载至 /mnt/easyaiot-media，请执行客户端挂载部署	[{"name":"SSH 连接","status":"success","output":"已连接 192.168.1.12:22"},{"name":"挂载源","status":"failed","output":"未能确认挂载源"},{"name":"NFS 挂载","status":"failed","output":"NFS 未挂载"},{"name":"读写探针","status":"failed","output":"挂载根不可写或未挂载"}]	\N	2026-08-12 14:12:52.590227	\N	2026-08-12 14:12:52.590227	0
102	\N	auto_refresh	t	刷新完成：成功 3，失败 0，跳过 0	\N	\N	2026-08-12 14:12:52.595665	\N	2026-08-12 14:12:52.595665	0
103	2	auto_refresh	t	NFS 存储已就绪：Export 正常，客户端已挂载至 /mnt/easyaiot-media	[{"name":"SSH 连接","status":"success","output":"已连接 192.168.1.11:22"},{"name":"NFS 服务端","status":"success","output":"NFS 服务端 正常"},{"name":"NFS Export","status":"success","output":"NFS Export 正常"},{"name":"NFS 2049","status":"success","output":"NFS 2049 正常"},{"name":"挂载源","status":"success","output":"挂载源匹配或本机回退"},{"name":"媒体子目录","status":"success","output":"alert_images / playbacks / snaps 已就绪"},{"name":"NFS 挂载","status":"success","output":"挂载点 /mnt/easyaiot-media 已就绪"},{"name":"读写探针","status":"success","output":"挂载根可写"}]	\N	2026-08-12 14:27:56.540992	\N	2026-08-12 14:27:56.540992	0
104	3	auto_refresh	t	NFS 未挂载至 /mnt/easyaiot-media，请执行客户端挂载部署	[{"name":"SSH 连接","status":"success","output":"已连接 192.168.1.12:22"},{"name":"挂载源","status":"failed","output":"未能确认挂载源"},{"name":"NFS 挂载","status":"failed","output":"NFS 未挂载"},{"name":"读写探针","status":"failed","output":"挂载根不可写或未挂载"}]	\N	2026-08-12 14:28:00.018714	\N	2026-08-12 14:28:00.018714	0
105	\N	auto_refresh	t	刷新完成：成功 3，失败 0，跳过 0	\N	\N	2026-08-12 14:28:00.02594	\N	2026-08-12 14:28:00.02594	0
\.


--
-- Data for Name: node_workload_binding; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.node_workload_binding (id, node_id, workload_type, workload_id, status, process_pid, bind_at, creator, create_time, updater, update_time, deleted) FROM stdin;
\.


--
-- Name: compute_node_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.compute_node_id_seq', 3, true);


--
-- Name: control_plane_peer_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.control_plane_peer_id_seq', 1, false);


--
-- Name: device_media_binding_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.device_media_binding_id_seq', 1, false);


--
-- Name: edge_node_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.edge_node_id_seq', 1, false);


--
-- Name: nfs_cluster_bridge_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.nfs_cluster_bridge_id_seq', 2, true);


--
-- Name: nfs_cluster_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.nfs_cluster_id_seq', 7, true);


--
-- Name: node_metric_snapshot_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.node_metric_snapshot_id_seq', 26419, true);


--
-- Name: node_ssh_credential_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.node_ssh_credential_id_seq', 2, true);


--
-- Name: node_storage_op_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.node_storage_op_log_id_seq', 105, true);


--
-- Name: node_workload_binding_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.node_workload_binding_id_seq', 1, false);


--
-- Name: compute_node compute_node_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.compute_node
    ADD CONSTRAINT compute_node_pkey PRIMARY KEY (id);


--
-- Name: control_plane_peer control_plane_peer_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.control_plane_peer
    ADD CONSTRAINT control_plane_peer_pkey PRIMARY KEY (id);


--
-- Name: device_media_binding device_media_binding_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.device_media_binding
    ADD CONSTRAINT device_media_binding_pkey PRIMARY KEY (id);


--
-- Name: edge_node edge_node_compute_node_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.edge_node
    ADD CONSTRAINT edge_node_compute_node_id_key UNIQUE (compute_node_id);


--
-- Name: edge_node edge_node_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.edge_node
    ADD CONSTRAINT edge_node_pkey PRIMARY KEY (id);


--
-- Name: nfs_cluster_bridge nfs_cluster_bridge_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nfs_cluster_bridge
    ADD CONSTRAINT nfs_cluster_bridge_pkey PRIMARY KEY (id);


--
-- Name: nfs_cluster nfs_cluster_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nfs_cluster
    ADD CONSTRAINT nfs_cluster_pkey PRIMARY KEY (id);


--
-- Name: node_metric_snapshot node_metric_snapshot_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.node_metric_snapshot
    ADD CONSTRAINT node_metric_snapshot_pkey PRIMARY KEY (id);


--
-- Name: node_ssh_credential node_ssh_credential_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.node_ssh_credential
    ADD CONSTRAINT node_ssh_credential_pkey PRIMARY KEY (id);


--
-- Name: node_storage_op_log node_storage_op_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.node_storage_op_log
    ADD CONSTRAINT node_storage_op_log_pkey PRIMARY KEY (id);


--
-- Name: node_workload_binding node_workload_binding_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.node_workload_binding
    ADD CONSTRAINT node_workload_binding_pkey PRIMARY KEY (id);


--
-- Name: idx_edge_node_compute; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_edge_node_compute ON public.edge_node USING btree (compute_node_id);


--
-- Name: idx_edge_node_host; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_edge_node_host ON public.edge_node USING btree (host);


--
-- Name: idx_edge_node_host_alive; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_edge_node_host_alive ON public.edge_node USING btree (host) WHERE (deleted = 0);


--
-- Name: idx_edge_node_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_edge_node_status ON public.edge_node USING btree (status);


--
-- Name: idx_edge_node_status_alive; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_edge_node_status_alive ON public.edge_node USING btree (status) WHERE (deleted = 0);


--
-- Name: idx_nfs_bridge_source; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_nfs_bridge_source ON public.nfs_cluster_bridge USING btree (source_cluster_id) WHERE (deleted = 0);


--
-- Name: idx_nfs_bridge_target; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_nfs_bridge_target ON public.nfs_cluster_bridge USING btree (target_cluster_id) WHERE (deleted = 0);


--
-- Name: idx_nfs_cluster_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_nfs_cluster_active ON public.nfs_cluster USING btree (is_active) WHERE (deleted = 0);


--
-- Name: idx_node_metric_node_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_node_metric_node_time ON public.node_metric_snapshot USING btree (node_id, collected_at DESC);


--
-- Name: idx_node_storage_op_log_node_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_node_storage_op_log_node_time ON public.node_storage_op_log USING btree (node_id, create_time DESC) WHERE (deleted = 0);


--
-- Name: uk_compute_node_host; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uk_compute_node_host ON public.compute_node USING btree (host) WHERE (deleted = 0);


--
-- Name: uk_control_plane_peer_api_base_url; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uk_control_plane_peer_api_base_url ON public.control_plane_peer USING btree (api_base_url) WHERE (deleted = 0);


--
-- Name: uk_device_media_binding_device; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uk_device_media_binding_device ON public.device_media_binding USING btree (device_id) WHERE (deleted = 0);


--
-- Name: uk_edge_node_compute_node; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uk_edge_node_compute_node ON public.edge_node USING btree (compute_node_id) WHERE (deleted = 0);


--
-- Name: uk_nfs_cluster_lane; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uk_nfs_cluster_lane ON public.nfs_cluster USING btree (lane_key) WHERE (deleted = 0);


--
-- Name: uk_node_ssh_credential_node; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uk_node_ssh_credential_node ON public.node_ssh_credential USING btree (node_id) WHERE (deleted = 0);


--
-- Name: uk_node_workload; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uk_node_workload ON public.node_workload_binding USING btree (workload_type, workload_id) WHERE (deleted = 0);


--
-- PostgreSQL database dump complete
--

\unrestrict rKgUTqhVdPDZrzcgKcGm4jkXOHz5nv2NjEd0s49H9maOB8hmbCzrESvcLMCfLg2

