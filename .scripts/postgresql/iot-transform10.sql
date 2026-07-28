--
-- PostgreSQL database dump
--

\restrict l5Ne7pG1XmbDQe87g4SmkIqYe2sm3lIMx47VUo7dDk9uf05XMaES6uui8h2pKBx

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

DROP DATABASE IF EXISTS "iot-transform20";
--
-- Name: iot-transform20; Type: DATABASE; Schema: -; Owner: -
--

CREATE DATABASE "iot-transform20" WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'en_US.utf8';


\unrestrict l5Ne7pG1XmbDQe87g4SmkIqYe2sm3lIMx47VUo7dDk9uf05XMaES6uui8h2pKBx
\encoding SQL_ASCII
\connect -reuse-previous=on "dbname='iot-transform20'"
\restrict l5Ne7pG1XmbDQe87g4SmkIqYe2sm3lIMx47VUo7dDk9uf05XMaES6uui8h2pKBx

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
-- Name: transform_archive_object; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.transform_archive_object (
    id character varying(64) CONSTRAINT tf_backup_object_id_not_null NOT NULL,
    event_id character varying(128) CONSTRAINT tf_backup_object_event_id_not_null NOT NULL,
    storage_path character varying(2048) CONSTRAINT tf_backup_object_path_not_null NOT NULL,
    content_checksum character varying(128),
    creator character varying(64) DEFAULT ''::character varying,
    create_time timestamp with time zone DEFAULT now() CONSTRAINT tf_backup_object_create_time_not_null NOT NULL,
    updater character varying(64) DEFAULT ''::character varying,
    update_time timestamp with time zone DEFAULT now() CONSTRAINT tf_backup_object_update_time_not_null NOT NULL,
    deleted smallint DEFAULT 0 CONSTRAINT tf_backup_object_deleted_not_null NOT NULL
);


--
-- Name: TABLE transform_archive_object; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.transform_archive_object IS '系统对接-归档对象索引（文件在本地/对象存储）';


--
-- Name: COLUMN transform_archive_object.storage_path; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.transform_archive_object.storage_path IS '归档存储路径';


--
-- Name: COLUMN transform_archive_object.content_checksum; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.transform_archive_object.content_checksum IS '内容校验和';


--
-- Name: transform_field_mapping; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.transform_field_mapping (
    id character varying(64) CONSTRAINT tf_mapping_id_not_null NOT NULL,
    mapping_name character varying(128) CONSTRAINT tf_mapping_name_not_null NOT NULL,
    field_bindings_json text DEFAULT '{}'::text CONSTRAINT tf_mapping_fields_json_not_null NOT NULL,
    enabled boolean DEFAULT true CONSTRAINT tf_mapping_enabled_not_null NOT NULL,
    creator character varying(64) DEFAULT ''::character varying,
    create_time timestamp with time zone DEFAULT now() CONSTRAINT tf_mapping_create_time_not_null NOT NULL,
    updater character varying(64) DEFAULT ''::character varying,
    update_time timestamp with time zone DEFAULT now() CONSTRAINT tf_mapping_update_time_not_null NOT NULL,
    deleted smallint DEFAULT 0 CONSTRAINT tf_mapping_deleted_not_null NOT NULL,
    remark character varying(512) DEFAULT ''::character varying
);


--
-- Name: TABLE transform_field_mapping; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.transform_field_mapping IS '系统对接-字段映射（数据转换）';


--
-- Name: COLUMN transform_field_mapping.mapping_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.transform_field_mapping.mapping_name IS '映射方案名称';


--
-- Name: COLUMN transform_field_mapping.field_bindings_json; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.transform_field_mapping.field_bindings_json IS '源字段→目标字段绑定 JSON';


--
-- Name: transform_flow_pipeline; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.transform_flow_pipeline (
    id character varying(64) CONSTRAINT tf_pipeline_id_not_null NOT NULL,
    pipeline_name character varying(128) CONSTRAINT tf_pipeline_name_not_null NOT NULL,
    flow_type character varying(32),
    field_mapping_id character varying(64),
    enabled boolean DEFAULT true CONSTRAINT tf_pipeline_enabled_not_null NOT NULL,
    creator character varying(64) DEFAULT ''::character varying,
    create_time timestamp with time zone DEFAULT now() CONSTRAINT tf_pipeline_create_time_not_null NOT NULL,
    updater character varying(64) DEFAULT ''::character varying,
    update_time timestamp with time zone DEFAULT now() CONSTRAINT tf_pipeline_update_time_not_null NOT NULL,
    deleted smallint DEFAULT 0 CONSTRAINT tf_pipeline_deleted_not_null NOT NULL,
    remark character varying(512) DEFAULT ''::character varying
);


--
-- Name: TABLE transform_flow_pipeline; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.transform_flow_pipeline IS '系统对接-流转管道';


--
-- Name: COLUMN transform_flow_pipeline.pipeline_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.transform_flow_pipeline.pipeline_name IS '管道名称';


--
-- Name: COLUMN transform_flow_pipeline.field_mapping_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.transform_flow_pipeline.field_mapping_id IS '管道级默认字段映射';


--
-- Name: transform_push_failure; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.transform_push_failure (
    id character varying(64) CONSTRAINT tf_dlq_id_not_null NOT NULL,
    failure_source character varying(64) CONSTRAINT tf_dlq_source_not_null NOT NULL,
    push_record_id character varying(64),
    failure_reason text CONSTRAINT tf_dlq_reason_not_null NOT NULL,
    envelope_json text,
    creator character varying(64) DEFAULT ''::character varying,
    create_time timestamp with time zone DEFAULT now() CONSTRAINT tf_dlq_create_time_not_null NOT NULL,
    updater character varying(64) DEFAULT ''::character varying,
    update_time timestamp with time zone DEFAULT now() CONSTRAINT tf_dlq_update_time_not_null NOT NULL,
    deleted smallint DEFAULT 0 CONSTRAINT tf_dlq_deleted_not_null NOT NULL
);


--
-- Name: TABLE transform_push_failure; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.transform_push_failure IS '系统对接-推送失败台账（可再推）';


--
-- Name: COLUMN transform_push_failure.failure_source; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.transform_push_failure.failure_source IS '失败来源：sink/deliver/outbox 等';


--
-- Name: COLUMN transform_push_failure.push_record_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.transform_push_failure.push_record_id IS '关联推送记录 ID';


--
-- Name: COLUMN transform_push_failure.failure_reason; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.transform_push_failure.failure_reason IS '失败原因';


--
-- Name: transform_push_record; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.transform_push_record (
    id character varying(64) CONSTRAINT tf_outbox_id_not_null NOT NULL,
    event_id character varying(128) CONSTRAINT tf_outbox_event_id_not_null NOT NULL,
    target_system_id character varying(64),
    push_rule_id character varying(64) CONSTRAINT tf_outbox_contract_id_not_null NOT NULL,
    deliver_channel character varying(32) CONSTRAINT tf_outbox_channel_not_null NOT NULL,
    push_status character varying(16) CONSTRAINT tf_outbox_status_not_null NOT NULL,
    attempt_count integer DEFAULT 0 CONSTRAINT tf_outbox_attempts_not_null NOT NULL,
    last_error text,
    envelope_json text CONSTRAINT tf_outbox_envelope_json_not_null NOT NULL,
    next_retry_time timestamp with time zone,
    relayed_at timestamp with time zone,
    creator character varying(64) DEFAULT ''::character varying,
    create_time timestamp with time zone DEFAULT now() CONSTRAINT tf_outbox_create_time_not_null NOT NULL,
    updater character varying(64) DEFAULT ''::character varying,
    update_time timestamp with time zone DEFAULT now() CONSTRAINT tf_outbox_update_time_not_null NOT NULL,
    deleted smallint DEFAULT 0 CONSTRAINT tf_outbox_deleted_not_null NOT NULL
);


--
-- Name: TABLE transform_push_record; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.transform_push_record IS '系统对接-推送记录（Outbox 权威任务）';


--
-- Name: COLUMN transform_push_record.event_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.transform_push_record.event_id IS '业务事件 ID（来自 sink 消息）';


--
-- Name: COLUMN transform_push_record.target_system_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.transform_push_record.target_system_id IS '目标系统 ID';


--
-- Name: COLUMN transform_push_record.push_rule_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.transform_push_record.push_rule_id IS '命中的推送规则 ID';


--
-- Name: COLUMN transform_push_record.deliver_channel; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.transform_push_record.deliver_channel IS '实际投递渠道';


--
-- Name: COLUMN transform_push_record.push_status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.transform_push_record.push_status IS 'PENDING|RELAYING|SENT|FAILED|DELIVERED|DEAD';


--
-- Name: COLUMN transform_push_record.attempt_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.transform_push_record.attempt_count IS '已尝试次数';


--
-- Name: COLUMN transform_push_record.last_error; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.transform_push_record.last_error IS '最近一次失败原因';


--
-- Name: COLUMN transform_push_record.envelope_json; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.transform_push_record.envelope_json IS '统一信封 TransformEnvelope JSON';


--
-- Name: COLUMN transform_push_record.next_retry_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.transform_push_record.next_retry_time IS '下次可重试时间';


--
-- Name: COLUMN transform_push_record.relayed_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.transform_push_record.relayed_at IS '成功转发到内部投递 Topic 的时间';


--
-- Name: transform_push_rule; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.transform_push_rule (
    id character varying(64) CONSTRAINT tf_contract_id_not_null NOT NULL,
    target_system_id character varying(64) CONSTRAINT tf_contract_party_id_not_null NOT NULL,
    flow_type character varying(32),
    deliver_channel character varying(32) CONSTRAINT tf_contract_channel_not_null NOT NULL,
    endpoint_url character varying(1024),
    field_mapping_id character varying(64),
    enabled boolean DEFAULT true CONSTRAINT tf_contract_enabled_not_null NOT NULL,
    request_headers_json text DEFAULT '{}'::text CONSTRAINT tf_contract_headers_json_not_null NOT NULL,
    creator character varying(64) DEFAULT ''::character varying,
    create_time timestamp with time zone DEFAULT now() CONSTRAINT tf_contract_create_time_not_null NOT NULL,
    updater character varying(64) DEFAULT ''::character varying,
    update_time timestamp with time zone DEFAULT now() CONSTRAINT tf_contract_update_time_not_null NOT NULL,
    deleted smallint DEFAULT 0 CONSTRAINT tf_contract_deleted_not_null NOT NULL,
    remark character varying(512) DEFAULT ''::character varying
);


--
-- Name: TABLE transform_push_rule; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.transform_push_rule IS '系统对接-推送规则';


--
-- Name: COLUMN transform_push_rule.target_system_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.transform_push_rule.target_system_id IS '关联目标系统 ID';


--
-- Name: COLUMN transform_push_rule.flow_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.transform_push_rule.flow_type IS '匹配流类型：DATA/ALERT/VIDEO_META/SENSOR；空=全匹配';


--
-- Name: COLUMN transform_push_rule.deliver_channel; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.transform_push_rule.deliver_channel IS '投递渠道：party/http/kafka/mqtt/jdbc';


--
-- Name: COLUMN transform_push_rule.endpoint_url; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.transform_push_rule.endpoint_url IS '推送地址（HTTP/Party endpoint）';


--
-- Name: COLUMN transform_push_rule.field_mapping_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.transform_push_rule.field_mapping_id IS '关联字段映射 ID';


--
-- Name: COLUMN transform_push_rule.request_headers_json; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.transform_push_rule.request_headers_json IS '请求头/密钥等扩展 JSON';


--
-- Name: transform_runtime_instance; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.transform_runtime_instance (
    instance_id character varying(64) NOT NULL,
    node_id character varying(64),
    host character varying(256),
    role character varying(32),
    status character varying(16) DEFAULT 'ONLINE'::character varying NOT NULL,
    joined_groups text,
    cpu_load double precision,
    heap_used_mb bigint,
    heap_max_mb bigint,
    max_consumer_lag bigint DEFAULT 0,
    deliver_success_rate double precision,
    metrics_json text DEFAULT '{}'::text NOT NULL,
    adapt_decision character varying(64),
    last_heartbeat_time timestamp with time zone DEFAULT now() NOT NULL,
    creator character varying(64) DEFAULT ''::character varying,
    create_time timestamp with time zone DEFAULT now() NOT NULL,
    updater character varying(64) DEFAULT ''::character varying,
    update_time timestamp with time zone DEFAULT now() NOT NULL,
    deleted smallint DEFAULT 0 NOT NULL
);


--
-- Name: TABLE transform_runtime_instance; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.transform_runtime_instance IS '系统对接-运行实例监测（上行遥测落盘）';


--
-- Name: COLUMN transform_runtime_instance.instance_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.transform_runtime_instance.instance_id IS 'Runtime 实例 ID';


--
-- Name: COLUMN transform_runtime_instance.node_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.transform_runtime_instance.node_id IS 'iot-node 节点 ID（可空）';


--
-- Name: COLUMN transform_runtime_instance.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.transform_runtime_instance.status IS 'ONLINE|DEGRADED|OFFLINE|STOPPING';


--
-- Name: COLUMN transform_runtime_instance.adapt_decision; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.transform_runtime_instance.adapt_decision IS 'KEEP|SCALE_HINT|DEGRADE_PARTY 等';


--
-- Name: transform_target_system; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.transform_target_system (
    id character varying(64) CONSTRAINT tf_party_id_not_null NOT NULL,
    system_name character varying(128) CONSTRAINT tf_party_name_not_null NOT NULL,
    connector_type character varying(64) CONSTRAINT tf_party_type_not_null NOT NULL,
    enabled boolean DEFAULT true CONSTRAINT tf_party_enabled_not_null NOT NULL,
    config_json text DEFAULT '{}'::text CONSTRAINT tf_party_config_json_not_null NOT NULL,
    creator character varying(64) DEFAULT ''::character varying,
    create_time timestamp with time zone DEFAULT now() CONSTRAINT tf_party_create_time_not_null NOT NULL,
    updater character varying(64) DEFAULT ''::character varying,
    update_time timestamp with time zone DEFAULT now() CONSTRAINT tf_party_update_time_not_null NOT NULL,
    deleted smallint DEFAULT 0 CONSTRAINT tf_party_deleted_not_null NOT NULL,
    remark character varying(512) DEFAULT ''::character varying
);


--
-- Name: TABLE transform_target_system; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.transform_target_system IS '系统对接-目标系统（MES/ERP/WMS/Webhook 等）';


--
-- Name: COLUMN transform_target_system.system_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.transform_target_system.system_name IS '目标系统显示名称';


--
-- Name: COLUMN transform_target_system.connector_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.transform_target_system.connector_type IS '连接器类型，如 mes.rest / erp.rest / wms.rest';


--
-- Name: COLUMN transform_target_system.config_json; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.transform_target_system.config_json IS '连接扩展配置 JSON';


--
-- Name: COLUMN transform_target_system.remark; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.transform_target_system.remark IS '备注';


--
-- Data for Name: transform_archive_object; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.transform_archive_object (id, event_id, storage_path, content_checksum, creator, create_time, updater, update_time, deleted) FROM stdin;
\.


--
-- Data for Name: transform_field_mapping; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.transform_field_mapping (id, mapping_name, field_bindings_json, enabled, creator, create_time, updater, update_time, deleted, remark) FROM stdin;
map-identity	identity	{}	t		2026-07-28 14:26:31.666+08		2026-07-28 14:26:31.666+08	0	
\.


--
-- Data for Name: transform_flow_pipeline; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.transform_flow_pipeline (id, pipeline_name, flow_type, field_mapping_id, enabled, creator, create_time, updater, update_time, deleted, remark) FROM stdin;
pipeline-default	default	\N	map-identity	t		2026-07-28 14:26:31.670043+08		2026-07-28 14:26:31.670043+08	0	
\.


--
-- Data for Name: transform_push_failure; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.transform_push_failure (id, failure_source, push_record_id, failure_reason, envelope_json, creator, create_time, updater, update_time, deleted) FROM stdin;
\.


--
-- Data for Name: transform_push_record; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.transform_push_record (id, event_id, target_system_id, push_rule_id, deliver_channel, push_status, attempt_count, last_error, envelope_json, next_retry_time, relayed_at, creator, create_time, updater, update_time, deleted) FROM stdin;
6febb2de-2ca7-43ae-b6db-94fc3e554230	c3bbee8c30a84754b2e1a29a5a3c46f1	demo-erp	contract-erp-data	party	DELIVERED	0	\N	{"eventId":"c3bbee8c30a84754b2e1a29a5a3c46f1","traceId":"c3bbee8c30a84754b2e1a29a5a3c46f1","flowType":"DATA","tenantId":"1","deviceId":"line-A-temp-01","sourceTopic":"iot_device_message","method":"thing.property.post","eventTime":1785219997.614369718,"ingestTime":1785219997.614370700,"headers":{"channel":"party","partyId":"demo-erp","contractId":"contract-erp-data","outboxId":"6febb2de-2ca7-43ae-b6db-94fc3e554230","endpoint":"http://127.0.0.1:18080/erp/telemetry","contract":{"id":"contract-erp-data","partyId":"demo-erp","flowType":"DATA","channel":"party","endpoint":"http://127.0.0.1:18080/erp/telemetry","mappingId":"map-identity","enabled":true,"headers":{},"createdAt":1.785219991667946E9},"partyType":"erp.rest"},"payload":{"id":"c3bbee8c30a84754b2e1a29a5a3c46f1","reportTime":"2026-07-28T06:26:37.457463+00:00","deviceId":"line-A-temp-01","tenantId":1,"serverId":"e2e-script","method":"thing.property.post","params":{"temperature":42.8,"humidity":61,"line":"A"},"topic":"/iot/e2e_product/line-A-temp-01/property/upstream/report","needReply":false},"partitionHint":1382273419}	\N	2026-07-28 14:26:38.360362+08	\N	2026-07-28 14:26:37.641888+08	\N	2026-07-28 14:26:38.391554+08	0
bda181fc-6e03-4585-be87-da1f3972bfe0	c3bbee8c30a84754b2e1a29a5a3c46f1	e2e-http	contract-http-webhook	http	DELIVERED	0	\N	{"eventId":"c3bbee8c30a84754b2e1a29a5a3c46f1","traceId":"c3bbee8c30a84754b2e1a29a5a3c46f1","flowType":"DATA","tenantId":"1","deviceId":"line-A-temp-01","sourceTopic":"iot_device_message","method":"thing.property.post","eventTime":1785219997.614369718,"ingestTime":1785219997.614370700,"headers":{"channel":"http","partyId":"e2e-http","contractId":"contract-http-webhook","outboxId":"bda181fc-6e03-4585-be87-da1f3972bfe0","endpoint":"http://127.0.0.1:18080/webhook/transform","contract":{"id":"contract-http-webhook","partyId":"e2e-http","flowType":null,"channel":"http","endpoint":"http://127.0.0.1:18080/webhook/transform","mappingId":"map-identity","enabled":true,"headers":{"partySecret":"e2e-secret"},"createdAt":1.785219991667946E9},"partySecret":"e2e-secret","partyType":"mes.rest"},"payload":{"id":"c3bbee8c30a84754b2e1a29a5a3c46f1","reportTime":"2026-07-28T06:26:37.457463+00:00","deviceId":"line-A-temp-01","tenantId":1,"serverId":"e2e-script","method":"thing.property.post","params":{"temperature":42.8,"humidity":61,"line":"A"},"topic":"/iot/e2e_product/line-A-temp-01/property/upstream/report","needReply":false},"partitionHint":1382273419}	\N	2026-07-28 14:26:38.36752+08	\N	2026-07-28 14:26:37.645019+08	\N	2026-07-28 14:26:38.391553+08	0
89fe76f1-96d6-4338-b446-2fd7c120d94b	40002b81c71b400d9c636bb07b726431	demo-mes	contract-mes-alert	party	DELIVERED	0	\N	{"eventId":"40002b81c71b400d9c636bb07b726431","traceId":"40002b81c71b400d9c636bb07b726431","flowType":"ALERT","tenantId":null,"deviceId":"cam-gate-01","sourceTopic":"iot-alert-notification","method":null,"eventTime":1785219998.737335651,"ingestTime":1785219998.737335914,"headers":{"channel":"party","partyId":"demo-mes","contractId":"contract-mes-alert","outboxId":"89fe76f1-96d6-4338-b446-2fd7c120d94b","endpoint":"http://127.0.0.1:18080/mes/alerts","contract":{"id":"contract-mes-alert","partyId":"demo-mes","flowType":"ALERT","channel":"party","endpoint":"http://127.0.0.1:18080/mes/alerts","mappingId":"map-identity","enabled":true,"headers":{},"createdAt":1.785219991667946E9},"partyType":"mes.rest"},"payload":{"id":"40002b81c71b400d9c636bb07b726431","alert_id":88011,"task_id":1,"task_name":"e2e-alert-task","device_id":"cam-gate-01","device_name":"E2E Camera","alert":{"level":"HIGH","type":"intrusion","imageUrl":"http://127.0.0.1/minio/e2e-snap.jpg","videoUrl":"rtsp://127.0.0.1/live/e2e"},"timestamp":"2026-07-28T06:26:37.457487+00:00","shouldNotify":true},"partitionHint":2092322373}	\N	2026-07-28 14:26:39.391949+08	\N	2026-07-28 14:26:38.745635+08	\N	2026-07-28 14:26:39.406993+08	0
fc47b0af-a28a-4b5e-8d46-b498c38d0831	e1000ab7eab64bb6ab2992669c7a2d7c	e2e-http	contract-http-webhook	http	DELIVERED	0	\N	{"eventId":"e1000ab7eab64bb6ab2992669c7a2d7c","traceId":"e1000ab7eab64bb6ab2992669c7a2d7c","flowType":"VIDEO_META","tenantId":null,"deviceId":"e2e-cam-vision","sourceTopic":"iot-face-matching","method":null,"eventTime":1785225813.028541810,"ingestTime":1785225813.028541941,"headers":{"channel":"http","partyId":"e2e-http","contractId":"contract-http-webhook","outboxId":"fc47b0af-a28a-4b5e-8d46-b498c38d0831","endpoint":"http://172.17.0.1:18080/webhook/transform","contract":{"id":"contract-http-webhook","partyId":"e2e-http","flowType":null,"channel":"http","endpoint":"http://172.17.0.1:18080/webhook/transform","mappingId":"map-identity","enabled":true,"headers":{"partySecret":"e2e-secret"},"createdAt":1.785219991667946E9},"partySecret":"e2e-secret","partyType":"mes.rest"},"payload":{"id":"e1000ab7eab64bb6ab2992669c7a2d7c","device_id":"e2e-cam-vision","match_score":0.97,"image_url":"http://127.0.0.1/minio/e2e-face.jpg","kind":"face","timestamp":"2026-07-28T08:03:32.919518+00:00"},"partitionHint":462935301}	\N	2026-07-28 16:03:33.45307+08	\N	2026-07-28 16:03:33.031221+08	\N	2026-07-28 16:03:33.465165+08	0
1ad88baf-f166-49a8-86d0-f8d8e3eb781a	e1000ab7eab64bb6ab2992669c7a2d7c	demo-wms	contract-wms-vision	party	DELIVERED	0	\N	{"eventId":"e1000ab7eab64bb6ab2992669c7a2d7c","traceId":"e1000ab7eab64bb6ab2992669c7a2d7c","flowType":"VIDEO_META","tenantId":null,"deviceId":"e2e-cam-vision","sourceTopic":"iot-face-matching","method":null,"eventTime":1785225813.028541810,"ingestTime":1785225813.028541941,"headers":{"channel":"party","partyId":"demo-wms","contractId":"contract-wms-vision","outboxId":"1ad88baf-f166-49a8-86d0-f8d8e3eb781a","endpoint":"http://172.17.0.1:18080/wms/vision","contract":{"id":"contract-wms-vision","partyId":"demo-wms","flowType":"VIDEO_META","channel":"party","endpoint":"http://172.17.0.1:18080/wms/vision","mappingId":"map-identity","enabled":true,"headers":{},"createdAt":1.785219997453394E9},"partyType":"wms.rest"},"payload":{"id":"e1000ab7eab64bb6ab2992669c7a2d7c","device_id":"e2e-cam-vision","match_score":0.97,"image_url":"http://127.0.0.1/minio/e2e-face.jpg","kind":"face","timestamp":"2026-07-28T08:03:32.919518+00:00"},"partitionHint":462935301}	\N	2026-07-28 16:03:33.459478+08	\N	2026-07-28 16:03:33.032106+08	\N	2026-07-28 16:03:33.469576+08	0
29ffac46-7b0f-433a-a096-7a58f21e00fb	40002b81c71b400d9c636bb07b726431	e2e-http	contract-http-webhook	http	DELIVERED	0	\N	{"eventId":"40002b81c71b400d9c636bb07b726431","traceId":"40002b81c71b400d9c636bb07b726431","flowType":"ALERT","tenantId":null,"deviceId":"cam-gate-01","sourceTopic":"iot-alert-notification","method":null,"eventTime":1785219998.737335651,"ingestTime":1785219998.737335914,"headers":{"channel":"http","partyId":"e2e-http","contractId":"contract-http-webhook","outboxId":"29ffac46-7b0f-433a-a096-7a58f21e00fb","endpoint":"http://127.0.0.1:18080/webhook/transform","contract":{"id":"contract-http-webhook","partyId":"e2e-http","flowType":null,"channel":"http","endpoint":"http://127.0.0.1:18080/webhook/transform","mappingId":"map-identity","enabled":true,"headers":{"partySecret":"e2e-secret"},"createdAt":1.785219991667946E9},"partySecret":"e2e-secret","partyType":"mes.rest"},"payload":{"id":"40002b81c71b400d9c636bb07b726431","alert_id":88011,"task_id":1,"task_name":"e2e-alert-task","device_id":"cam-gate-01","device_name":"E2E Camera","alert":{"level":"HIGH","type":"intrusion","imageUrl":"http://127.0.0.1/minio/e2e-snap.jpg","videoUrl":"rtsp://127.0.0.1/live/e2e"},"timestamp":"2026-07-28T06:26:37.457487+00:00","shouldNotify":true},"partitionHint":2092322373}	\N	2026-07-28 14:26:39.404651+08	\N	2026-07-28 14:26:38.74798+08	\N	2026-07-28 14:26:39.411748+08	0
bd0de3ff-c989-4ff9-b556-35c95cc76858	747a677fdae245d59d44ff9394597e5c	e2e-http	contract-http-webhook	http	DELIVERED	0	\N	{"eventId":"747a677fdae245d59d44ff9394597e5c","traceId":"747a677fdae245d59d44ff9394597e5c","flowType":"DATA","tenantId":"1","deviceId":"e2e-device-001","sourceTopic":"iot_device_message","method":"thing.property.post","eventTime":1785225810.751967032,"ingestTime":1785225810.751967427,"headers":{"channel":"http","partyId":"e2e-http","contractId":"contract-http-webhook","outboxId":"bd0de3ff-c989-4ff9-b556-35c95cc76858","endpoint":"http://172.17.0.1:18080/webhook/transform","contract":{"id":"contract-http-webhook","partyId":"e2e-http","flowType":null,"channel":"http","endpoint":"http://172.17.0.1:18080/webhook/transform","mappingId":"map-identity","enabled":true,"headers":{"partySecret":"e2e-secret"},"createdAt":1.785219991667946E9},"partySecret":"e2e-secret","partyType":"mes.rest"},"payload":{"id":"747a677fdae245d59d44ff9394597e5c","reportTime":"2026-07-28T08:03:30.628183+00:00","deviceId":"e2e-device-001","tenantId":1,"serverId":"e2e-script","method":"thing.property.post","params":{"temperature":36.5,"humidity":55},"topic":"/iot/e2e_product/e2e-device-001/property/upstream/report","needReply":false},"partitionHint":366914959}	\N	2026-07-28 16:03:31.410066+08	\N	2026-07-28 16:03:30.762554+08	\N	2026-07-28 16:03:31.418003+08	0
bb67c3ec-b95b-4fc6-b78d-94d7182860cd	cf4806d4d41a4baf8530d87e1345a322	demo-wms	contract-wms-vision	party	DELIVERED	0	\N	{"eventId":"cf4806d4d41a4baf8530d87e1345a322","traceId":"cf4806d4d41a4baf8530d87e1345a322","flowType":"VIDEO_META","tenantId":null,"deviceId":"e2e-cam-vision","sourceTopic":"iot-face-matching","method":null,"eventTime":1785219999.888796660,"ingestTime":1785219999.888797517,"headers":{"channel":"party","partyId":"demo-wms","contractId":"contract-wms-vision","outboxId":"bb67c3ec-b95b-4fc6-b78d-94d7182860cd","endpoint":"http://127.0.0.1:18080/wms/vision","contract":{"id":"contract-wms-vision","partyId":"demo-wms","flowType":"VIDEO_META","channel":"party","endpoint":"http://127.0.0.1:18080/wms/vision","mappingId":"map-identity","enabled":true,"headers":{},"createdAt":1.785219997453394E9},"partyType":"wms.rest"},"payload":{"id":"cf4806d4d41a4baf8530d87e1345a322","device_id":"e2e-cam-vision","match_score":0.97,"image_url":"http://127.0.0.1/minio/e2e-face.jpg","kind":"face","timestamp":"2026-07-28T06:26:37.457495+00:00"},"partitionHint":462935301}	\N	2026-07-28 14:26:40.43706+08	\N	2026-07-28 14:26:39.909183+08	\N	2026-07-28 14:26:40.440248+08	0
6cb7fdec-67e2-4f14-a738-87ee23b98177	be15ae7268d442dbb3bc6ef4ac8603ef	demo-mes	contract-mes-alert	party	DELIVERED	0	\N	{"eventId":"be15ae7268d442dbb3bc6ef4ac8603ef","traceId":"be15ae7268d442dbb3bc6ef4ac8603ef","flowType":"ALERT","tenantId":null,"deviceId":"e2e-cam-001","sourceTopic":"iot-alert-notification","method":null,"eventTime":1785225811.893267537,"ingestTime":1785225811.893268532,"headers":{"channel":"party","partyId":"demo-mes","contractId":"contract-mes-alert","outboxId":"6cb7fdec-67e2-4f14-a738-87ee23b98177","endpoint":"http://172.17.0.1:18080/mes/alerts","contract":{"id":"contract-mes-alert","partyId":"demo-mes","flowType":"ALERT","channel":"party","endpoint":"http://172.17.0.1:18080/mes/alerts","mappingId":"map-identity","enabled":true,"headers":{},"createdAt":1.785219991667946E9},"partyType":"mes.rest"},"payload":{"id":"be15ae7268d442dbb3bc6ef4ac8603ef","alert_id":90001,"task_id":1,"task_name":"e2e-alert-task","device_id":"e2e-cam-001","device_name":"E2E Camera","alert":{"level":"HIGH","type":"intrusion","imageUrl":"http://127.0.0.1/minio/e2e-snap.jpg","videoUrl":"rtsp://127.0.0.1/live/e2e"},"timestamp":"2026-07-28T08:03:31.777040+00:00","shouldNotify":true},"partitionHint":1456176126}	\N	2026-07-28 16:03:32.42934+08	\N	2026-07-28 16:03:31.901236+08	\N	2026-07-28 16:03:32.43998+08	0
d8ba0cc1-d591-42d7-a06f-5aacdadcce74	cf4806d4d41a4baf8530d87e1345a322	e2e-http	contract-http-webhook	http	DELIVERED	0	\N	{"eventId":"cf4806d4d41a4baf8530d87e1345a322","traceId":"cf4806d4d41a4baf8530d87e1345a322","flowType":"VIDEO_META","tenantId":null,"deviceId":"e2e-cam-vision","sourceTopic":"iot-face-matching","method":null,"eventTime":1785219999.888796660,"ingestTime":1785219999.888797517,"headers":{"channel":"http","partyId":"e2e-http","contractId":"contract-http-webhook","outboxId":"d8ba0cc1-d591-42d7-a06f-5aacdadcce74","endpoint":"http://127.0.0.1:18080/webhook/transform","contract":{"id":"contract-http-webhook","partyId":"e2e-http","flowType":null,"channel":"http","endpoint":"http://127.0.0.1:18080/webhook/transform","mappingId":"map-identity","enabled":true,"headers":{"partySecret":"e2e-secret"},"createdAt":1.785219991667946E9},"partySecret":"e2e-secret","partyType":"mes.rest"},"payload":{"id":"cf4806d4d41a4baf8530d87e1345a322","device_id":"e2e-cam-vision","match_score":0.97,"image_url":"http://127.0.0.1/minio/e2e-face.jpg","kind":"face","timestamp":"2026-07-28T06:26:37.457495+00:00"},"partitionHint":462935301}	\N	2026-07-28 14:26:40.431474+08	\N	2026-07-28 14:26:39.906224+08	\N	2026-07-28 14:26:40.435564+08	0
2a9b857e-0128-4a9f-a513-10c5fca9cdf1	3f272cdde10f4d5b936e5f97306aff8a	demo-erp	contract-erp-data	party	DELIVERED	1	org.springframework.kafka.KafkaException: Send failed; nested exception is org.apache.kafka.common.errors.TimeoutException: Topic iot_transform_deliver not present in metadata after 60000 ms.	{"eventId":"3f272cdde10f4d5b936e5f97306aff8a","traceId":"3f272cdde10f4d5b936e5f97306aff8a","flowType":"DATA","tenantId":"1","deviceId":"e2e-device-001","sourceTopic":"iot_device_message","method":"thing.property.post","eventTime":1785225486.183930238,"ingestTime":1785225486.183931226,"headers":{"channel":"party","partyId":"demo-erp","contractId":"contract-erp-data","outboxId":"2a9b857e-0128-4a9f-a513-10c5fca9cdf1","endpoint":"http://127.0.0.1:18080/erp/telemetry","contract":{"id":"contract-erp-data","partyId":"demo-erp","flowType":"DATA","channel":"party","endpoint":"http://127.0.0.1:18080/erp/telemetry","mappingId":"map-identity","enabled":true,"headers":{},"createdAt":1.785219991667946E9},"partyType":"erp.rest"},"payload":{"id":"3f272cdde10f4d5b936e5f97306aff8a","reportTime":"2026-07-28T07:58:06.055956+00:00","deviceId":"e2e-device-001","tenantId":1,"serverId":"e2e-script","method":"thing.property.post","params":{"temperature":36.5,"humidity":55},"topic":"/iot/e2e_product/e2e-device-001/property/upstream/report","needReply":false},"partitionHint":366914959}	2026-07-28 15:59:08.609728+08	2026-07-28 15:59:09.062874+08	\N	2026-07-28 15:58:06.190846+08	\N	2026-07-28 15:59:09.06927+08	0
8d8c3833-009f-4a23-9604-8d90b22152d8	60aeb1eb79f5422ea7430bd16306f1bb	demo-erp	contract-erp-data	party	DELIVERED	0	\N	{"eventId":"60aeb1eb79f5422ea7430bd16306f1bb","traceId":"60aeb1eb79f5422ea7430bd16306f1bb","flowType":"DATA","tenantId":"1","deviceId":"e2e-device-001","sourceTopic":"iot_device_message","method":"thing.property.post","eventTime":1785225092.070027712,"ingestTime":1785225092.070033227,"headers":{"channel":"party","partyId":"demo-erp","contractId":"contract-erp-data","outboxId":"8d8c3833-009f-4a23-9604-8d90b22152d8","endpoint":"http://127.0.0.1:18080/erp/telemetry","contract":{"id":"contract-erp-data","partyId":"demo-erp","flowType":"DATA","channel":"party","endpoint":"http://127.0.0.1:18080/erp/telemetry","mappingId":"map-identity","enabled":true,"headers":{},"createdAt":1.785219991667946E9},"partyType":"erp.rest"},"payload":{"id":"60aeb1eb79f5422ea7430bd16306f1bb","reportTime":"2026-07-28T07:51:31.948303+00:00","deviceId":"e2e-device-001","tenantId":1,"serverId":"e2e-script","method":"thing.property.post","params":{"temperature":36.5,"humidity":55},"topic":"/iot/e2e_product/e2e-device-001/property/upstream/report","needReply":false},"partitionHint":366914959}	\N	2026-07-28 15:51:32.363565+08	\N	2026-07-28 15:51:32.10146+08	\N	2026-07-28 15:51:32.391634+08	0
d7b89ea2-296b-4394-a00d-cc0928898eb5	fef4225be3754773a4d2075ac5d7bb87	demo-erp	contract-erp-data	party	DELIVERED	0	\N	{"eventId":"fef4225be3754773a4d2075ac5d7bb87","traceId":"fef4225be3754773a4d2075ac5d7bb87","flowType":"DATA","tenantId":"1","deviceId":"e2e-device-001","sourceTopic":"iot_device_message","method":"thing.property.post","eventTime":1785225127.424543652,"ingestTime":1785225127.424544756,"headers":{"channel":"party","partyId":"demo-erp","contractId":"contract-erp-data","outboxId":"d7b89ea2-296b-4394-a00d-cc0928898eb5","endpoint":"http://127.0.0.1:18080/erp/telemetry","contract":{"id":"contract-erp-data","partyId":"demo-erp","flowType":"DATA","channel":"party","endpoint":"http://127.0.0.1:18080/erp/telemetry","mappingId":"map-identity","enabled":true,"headers":{},"createdAt":1.785219991667946E9},"partyType":"erp.rest"},"payload":{"id":"fef4225be3754773a4d2075ac5d7bb87","reportTime":"2026-07-28T07:52:07.302754+00:00","deviceId":"e2e-device-001","tenantId":1,"serverId":"e2e-script","method":"thing.property.post","params":{"temperature":36.5,"humidity":55},"topic":"/iot/e2e_product/e2e-device-001/property/upstream/report","needReply":false},"partitionHint":366914959}	\N	2026-07-28 15:52:07.486904+08	\N	2026-07-28 15:52:07.435569+08	\N	2026-07-28 15:52:07.497719+08	0
c9b738a5-171d-48d2-86cd-83d15a0e35dd	fef4225be3754773a4d2075ac5d7bb87	e2e-http	contract-http-webhook	http	DELIVERED	0	\N	{"eventId":"fef4225be3754773a4d2075ac5d7bb87","traceId":"fef4225be3754773a4d2075ac5d7bb87","flowType":"DATA","tenantId":"1","deviceId":"e2e-device-001","sourceTopic":"iot_device_message","method":"thing.property.post","eventTime":1785225127.424543652,"ingestTime":1785225127.424544756,"headers":{"channel":"http","partyId":"e2e-http","contractId":"contract-http-webhook","outboxId":"c9b738a5-171d-48d2-86cd-83d15a0e35dd","endpoint":"http://127.0.0.1:18080/webhook/transform","contract":{"id":"contract-http-webhook","partyId":"e2e-http","flowType":null,"channel":"http","endpoint":"http://127.0.0.1:18080/webhook/transform","mappingId":"map-identity","enabled":true,"headers":{"partySecret":"e2e-secret"},"createdAt":1.785219991667946E9},"partySecret":"e2e-secret","partyType":"mes.rest"},"payload":{"id":"fef4225be3754773a4d2075ac5d7bb87","reportTime":"2026-07-28T07:52:07.302754+00:00","deviceId":"e2e-device-001","tenantId":1,"serverId":"e2e-script","method":"thing.property.post","params":{"temperature":36.5,"humidity":55},"topic":"/iot/e2e_product/e2e-device-001/property/upstream/report","needReply":false},"partitionHint":366914959}	\N	2026-07-28 15:52:07.497981+08	\N	2026-07-28 15:52:07.440465+08	\N	2026-07-28 15:52:07.502781+08	0
6b7d98f0-d292-444d-9b08-86c7cdee8a0f	60aeb1eb79f5422ea7430bd16306f1bb	e2e-http	contract-http-webhook	http	DELIVERED	0	\N	{"eventId":"60aeb1eb79f5422ea7430bd16306f1bb","traceId":"60aeb1eb79f5422ea7430bd16306f1bb","flowType":"DATA","tenantId":"1","deviceId":"e2e-device-001","sourceTopic":"iot_device_message","method":"thing.property.post","eventTime":1785225092.070027712,"ingestTime":1785225092.070033227,"headers":{"channel":"http","partyId":"e2e-http","contractId":"contract-http-webhook","outboxId":"6b7d98f0-d292-444d-9b08-86c7cdee8a0f","endpoint":"http://127.0.0.1:18080/webhook/transform","contract":{"id":"contract-http-webhook","partyId":"e2e-http","flowType":null,"channel":"http","endpoint":"http://127.0.0.1:18080/webhook/transform","mappingId":"map-identity","enabled":true,"headers":{"partySecret":"e2e-secret"},"createdAt":1.785219991667946E9},"partySecret":"e2e-secret","partyType":"mes.rest"},"payload":{"id":"60aeb1eb79f5422ea7430bd16306f1bb","reportTime":"2026-07-28T07:51:31.948303+00:00","deviceId":"e2e-device-001","tenantId":1,"serverId":"e2e-script","method":"thing.property.post","params":{"temperature":36.5,"humidity":55},"topic":"/iot/e2e_product/e2e-device-001/property/upstream/report","needReply":false},"partitionHint":366914959}	\N	2026-07-28 15:51:32.368822+08	\N	2026-07-28 15:51:32.102597+08	\N	2026-07-28 15:51:32.391634+08	0
9a1f7153-0c8e-496d-af93-d395fa746cdc	3f272cdde10f4d5b936e5f97306aff8a	e2e-http	contract-http-webhook	http	DELIVERED	1	org.springframework.kafka.KafkaException: Send failed; nested exception is org.apache.kafka.common.errors.TimeoutException: Topic iot_transform_deliver not present in metadata after 60000 ms.	{"eventId":"3f272cdde10f4d5b936e5f97306aff8a","traceId":"3f272cdde10f4d5b936e5f97306aff8a","flowType":"DATA","tenantId":"1","deviceId":"e2e-device-001","sourceTopic":"iot_device_message","method":"thing.property.post","eventTime":1785225486.183930238,"ingestTime":1785225486.183931226,"headers":{"channel":"http","partyId":"e2e-http","contractId":"contract-http-webhook","outboxId":"9a1f7153-0c8e-496d-af93-d395fa746cdc","endpoint":"http://127.0.0.1:18080/webhook/transform","contract":{"id":"contract-http-webhook","partyId":"e2e-http","flowType":null,"channel":"http","endpoint":"http://127.0.0.1:18080/webhook/transform","mappingId":"map-identity","enabled":true,"headers":{"partySecret":"e2e-secret"},"createdAt":1.785219991667946E9},"partySecret":"e2e-secret","partyType":"mes.rest"},"payload":{"id":"3f272cdde10f4d5b936e5f97306aff8a","reportTime":"2026-07-28T07:58:06.055956+00:00","deviceId":"e2e-device-001","tenantId":1,"serverId":"e2e-script","method":"thing.property.post","params":{"temperature":36.5,"humidity":55},"topic":"/iot/e2e_product/e2e-device-001/property/upstream/report","needReply":false},"partitionHint":366914959}	2026-07-28 16:00:08.615482+08	2026-07-28 16:00:09.142047+08	\N	2026-07-28 15:58:06.196578+08	\N	2026-07-28 16:00:09.155787+08	0
50c44046-1af2-4caf-8ca1-3ec268b3e009	9801507581814dfe8efe1dbcd85dd057	demo-mes	contract-mes-alert	party	DELIVERED	0	\N	{"eventId":"9801507581814dfe8efe1dbcd85dd057","traceId":"9801507581814dfe8efe1dbcd85dd057","flowType":"ALERT","tenantId":null,"deviceId":"e2e-cam-001","sourceTopic":"iot-alert-notification","method":null,"eventTime":1785225093.225536390,"ingestTime":1785225093.225537491,"headers":{"channel":"party","partyId":"demo-mes","contractId":"contract-mes-alert","outboxId":"50c44046-1af2-4caf-8ca1-3ec268b3e009","endpoint":"http://127.0.0.1:18080/mes/alerts","contract":{"id":"contract-mes-alert","partyId":"demo-mes","flowType":"ALERT","channel":"party","endpoint":"http://127.0.0.1:18080/mes/alerts","mappingId":"map-identity","enabled":true,"headers":{},"createdAt":1.785219991667946E9},"partyType":"mes.rest"},"payload":{"id":"9801507581814dfe8efe1dbcd85dd057","alert_id":90001,"task_id":1,"task_name":"e2e-alert-task","device_id":"e2e-cam-001","device_name":"E2E Camera","alert":{"level":"HIGH","type":"intrusion","imageUrl":"http://127.0.0.1/minio/e2e-snap.jpg","videoUrl":"rtsp://127.0.0.1/live/e2e"},"timestamp":"2026-07-28T07:51:33.110542+00:00","shouldNotify":true},"partitionHint":1456176126}	\N	2026-07-28 15:51:33.387775+08	\N	2026-07-28 15:51:33.241877+08	\N	2026-07-28 15:51:33.397426+08	0
aeec8401-f2be-4993-9ccc-1df3a1f837e9	9801507581814dfe8efe1dbcd85dd057	e2e-http	contract-http-webhook	http	DELIVERED	0	\N	{"eventId":"9801507581814dfe8efe1dbcd85dd057","traceId":"9801507581814dfe8efe1dbcd85dd057","flowType":"ALERT","tenantId":null,"deviceId":"e2e-cam-001","sourceTopic":"iot-alert-notification","method":null,"eventTime":1785225093.225536390,"ingestTime":1785225093.225537491,"headers":{"channel":"http","partyId":"e2e-http","contractId":"contract-http-webhook","outboxId":"aeec8401-f2be-4993-9ccc-1df3a1f837e9","endpoint":"http://127.0.0.1:18080/webhook/transform","contract":{"id":"contract-http-webhook","partyId":"e2e-http","flowType":null,"channel":"http","endpoint":"http://127.0.0.1:18080/webhook/transform","mappingId":"map-identity","enabled":true,"headers":{"partySecret":"e2e-secret"},"createdAt":1.785219991667946E9},"partySecret":"e2e-secret","partyType":"mes.rest"},"payload":{"id":"9801507581814dfe8efe1dbcd85dd057","alert_id":90001,"task_id":1,"task_name":"e2e-alert-task","device_id":"e2e-cam-001","device_name":"E2E Camera","alert":{"level":"HIGH","type":"intrusion","imageUrl":"http://127.0.0.1/minio/e2e-snap.jpg","videoUrl":"rtsp://127.0.0.1/live/e2e"},"timestamp":"2026-07-28T07:51:33.110542+00:00","shouldNotify":true},"partitionHint":1456176126}	\N	2026-07-28 15:51:33.398022+08	\N	2026-07-28 15:51:33.245601+08	\N	2026-07-28 15:51:33.407356+08	0
1c4a2cfe-2eb6-4f4b-8d40-93a44755fe53	92642dff9e4f432ca2c8f33fa4349cc7	e2e-http	contract-http-webhook	http	DELIVERED	0	\N	{"eventId":"92642dff9e4f432ca2c8f33fa4349cc7","traceId":"92642dff9e4f432ca2c8f33fa4349cc7","flowType":"VIDEO_META","tenantId":null,"deviceId":"e2e-cam-vision","sourceTopic":"iot-face-matching","method":null,"eventTime":1785225094.377702283,"ingestTime":1785225094.377703711,"headers":{"channel":"http","partyId":"e2e-http","contractId":"contract-http-webhook","outboxId":"1c4a2cfe-2eb6-4f4b-8d40-93a44755fe53","endpoint":"http://127.0.0.1:18080/webhook/transform","contract":{"id":"contract-http-webhook","partyId":"e2e-http","flowType":null,"channel":"http","endpoint":"http://127.0.0.1:18080/webhook/transform","mappingId":"map-identity","enabled":true,"headers":{"partySecret":"e2e-secret"},"createdAt":1.785219991667946E9},"partySecret":"e2e-secret","partyType":"mes.rest"},"payload":{"id":"92642dff9e4f432ca2c8f33fa4349cc7","device_id":"e2e-cam-vision","match_score":0.97,"image_url":"http://127.0.0.1/minio/e2e-face.jpg","kind":"face","timestamp":"2026-07-28T07:51:34.259620+00:00"},"partitionHint":462935301}	\N	2026-07-28 15:51:34.410606+08	\N	2026-07-28 15:51:34.390545+08	\N	2026-07-28 15:51:34.415765+08	0
327797a9-5b78-4d1b-a4b1-05e963fa31ab	92642dff9e4f432ca2c8f33fa4349cc7	demo-wms	contract-wms-vision	party	DELIVERED	0	\N	{"eventId":"92642dff9e4f432ca2c8f33fa4349cc7","traceId":"92642dff9e4f432ca2c8f33fa4349cc7","flowType":"VIDEO_META","tenantId":null,"deviceId":"e2e-cam-vision","sourceTopic":"iot-face-matching","method":null,"eventTime":1785225094.377702283,"ingestTime":1785225094.377703711,"headers":{"channel":"party","partyId":"demo-wms","contractId":"contract-wms-vision","outboxId":"327797a9-5b78-4d1b-a4b1-05e963fa31ab","endpoint":"http://127.0.0.1:18080/wms/vision","contract":{"id":"contract-wms-vision","partyId":"demo-wms","flowType":"VIDEO_META","channel":"party","endpoint":"http://127.0.0.1:18080/wms/vision","mappingId":"map-identity","enabled":true,"headers":{},"createdAt":1.785219997453394E9},"partyType":"wms.rest"},"payload":{"id":"92642dff9e4f432ca2c8f33fa4349cc7","device_id":"e2e-cam-vision","match_score":0.97,"image_url":"http://127.0.0.1/minio/e2e-face.jpg","kind":"face","timestamp":"2026-07-28T07:51:34.259620+00:00"},"partitionHint":462935301}	\N	2026-07-28 15:51:34.415177+08	\N	2026-07-28 15:51:34.392494+08	\N	2026-07-28 15:51:34.417747+08	0
73817a21-0eaa-4bae-b116-861834428996	e3b50d66a82345dcba815eb6911381bd	demo-erp	contract-erp-data	party	DELIVERED	1	org.springframework.kafka.KafkaException: Send failed; nested exception is org.apache.kafka.common.errors.TimeoutException: Topic iot_transform_deliver not present in metadata after 60000 ms.	{"eventId":"e3b50d66a82345dcba815eb6911381bd","traceId":"e3b50d66a82345dcba815eb6911381bd","flowType":"DATA","tenantId":"1","deviceId":"e2e-device-001","sourceTopic":"iot_device_message","method":"thing.property.post","eventTime":1785225676.338336062,"ingestTime":1785225676.338337416,"headers":{"channel":"party","partyId":"demo-erp","contractId":"contract-erp-data","outboxId":"73817a21-0eaa-4bae-b116-861834428996","endpoint":"http://172.17.0.1:18080/erp/telemetry","contract":{"id":"contract-erp-data","partyId":"demo-erp","flowType":"DATA","channel":"party","endpoint":"http://172.17.0.1:18080/erp/telemetry","mappingId":"map-identity","enabled":true,"headers":{},"createdAt":1.785219991667946E9},"partyType":"erp.rest"},"payload":{"id":"e3b50d66a82345dcba815eb6911381bd","reportTime":"2026-07-28T08:01:16.215576+00:00","deviceId":"e2e-device-001","tenantId":1,"serverId":"e2e-script","method":"thing.property.post","params":{"temperature":36.5,"humidity":55},"topic":"/iot/e2e_product/e2e-device-001/property/upstream/report","needReply":false},"partitionHint":366914959}	2026-07-28 16:02:18.655264+08	2026-07-28 16:02:19.309986+08	\N	2026-07-28 16:01:16.353755+08	\N	2026-07-28 16:02:19.321122+08	0
0744c55b-9280-4da8-ae84-b9062838700c	4ff863f142744bf09ac41ca72fc60c41	e2e-http	contract-http-webhook	http	DELIVERED	0	\N	{"eventId":"4ff863f142744bf09ac41ca72fc60c41","traceId":"4ff863f142744bf09ac41ca72fc60c41","flowType":"VIDEO_META","tenantId":null,"deviceId":"e2e-cam-vision","sourceTopic":"iot-face-matching","method":null,"eventTime":1785225129.711675576,"ingestTime":1785225129.711676961,"headers":{"channel":"http","partyId":"e2e-http","contractId":"contract-http-webhook","outboxId":"0744c55b-9280-4da8-ae84-b9062838700c","endpoint":"http://127.0.0.1:18080/webhook/transform","contract":{"id":"contract-http-webhook","partyId":"e2e-http","flowType":null,"channel":"http","endpoint":"http://127.0.0.1:18080/webhook/transform","mappingId":"map-identity","enabled":true,"headers":{"partySecret":"e2e-secret"},"createdAt":1.785219991667946E9},"partySecret":"e2e-secret","partyType":"mes.rest"},"payload":{"id":"4ff863f142744bf09ac41ca72fc60c41","device_id":"e2e-cam-vision","match_score":0.97,"image_url":"http://127.0.0.1/minio/e2e-face.jpg","kind":"face","timestamp":"2026-07-28T07:52:09.595894+00:00"},"partitionHint":462935301}	\N	2026-07-28 15:52:10.536199+08	\N	2026-07-28 15:52:09.71657+08	\N	2026-07-28 15:52:10.538537+08	0
a197ca26-3e29-4705-b883-251ced3818b0	747a677fdae245d59d44ff9394597e5c	demo-erp	contract-erp-data	party	DELIVERED	0	\N	{"eventId":"747a677fdae245d59d44ff9394597e5c","traceId":"747a677fdae245d59d44ff9394597e5c","flowType":"DATA","tenantId":"1","deviceId":"e2e-device-001","sourceTopic":"iot_device_message","method":"thing.property.post","eventTime":1785225810.751967032,"ingestTime":1785225810.751967427,"headers":{"channel":"party","partyId":"demo-erp","contractId":"contract-erp-data","outboxId":"a197ca26-3e29-4705-b883-251ced3818b0","endpoint":"http://172.17.0.1:18080/erp/telemetry","contract":{"id":"contract-erp-data","partyId":"demo-erp","flowType":"DATA","channel":"party","endpoint":"http://172.17.0.1:18080/erp/telemetry","mappingId":"map-identity","enabled":true,"headers":{},"createdAt":1.785219991667946E9},"partyType":"erp.rest"},"payload":{"id":"747a677fdae245d59d44ff9394597e5c","reportTime":"2026-07-28T08:03:30.628183+00:00","deviceId":"e2e-device-001","tenantId":1,"serverId":"e2e-script","method":"thing.property.post","params":{"temperature":36.5,"humidity":55},"topic":"/iot/e2e_product/e2e-device-001/property/upstream/report","needReply":false},"partitionHint":366914959}	\N	2026-07-28 16:03:31.401507+08	\N	2026-07-28 16:03:30.75931+08	\N	2026-07-28 16:03:31.414783+08	0
6704f0b4-d0a0-488c-915a-c2cee794fd98	be15ae7268d442dbb3bc6ef4ac8603ef	e2e-http	contract-http-webhook	http	DELIVERED	0	\N	{"eventId":"be15ae7268d442dbb3bc6ef4ac8603ef","traceId":"be15ae7268d442dbb3bc6ef4ac8603ef","flowType":"ALERT","tenantId":null,"deviceId":"e2e-cam-001","sourceTopic":"iot-alert-notification","method":null,"eventTime":1785225811.893267537,"ingestTime":1785225811.893268532,"headers":{"channel":"http","partyId":"e2e-http","contractId":"contract-http-webhook","outboxId":"6704f0b4-d0a0-488c-915a-c2cee794fd98","endpoint":"http://172.17.0.1:18080/webhook/transform","contract":{"id":"contract-http-webhook","partyId":"e2e-http","flowType":null,"channel":"http","endpoint":"http://172.17.0.1:18080/webhook/transform","mappingId":"map-identity","enabled":true,"headers":{"partySecret":"e2e-secret"},"createdAt":1.785219991667946E9},"partySecret":"e2e-secret","partyType":"mes.rest"},"payload":{"id":"be15ae7268d442dbb3bc6ef4ac8603ef","alert_id":90001,"task_id":1,"task_name":"e2e-alert-task","device_id":"e2e-cam-001","device_name":"E2E Camera","alert":{"level":"HIGH","type":"intrusion","imageUrl":"http://127.0.0.1/minio/e2e-snap.jpg","videoUrl":"rtsp://127.0.0.1/live/e2e"},"timestamp":"2026-07-28T08:03:31.777040+00:00","shouldNotify":true},"partitionHint":1456176126}	\N	2026-07-28 16:03:32.436038+08	\N	2026-07-28 16:03:31.906494+08	\N	2026-07-28 16:03:32.443037+08	0
41da36d3-ad28-413d-952a-97a4f7e32ed7	11022bb6ce554355810a098f3fd30bc5	demo-mes	contract-mes-alert	party	DELIVERED	0	\N	{"eventId":"11022bb6ce554355810a098f3fd30bc5","traceId":"11022bb6ce554355810a098f3fd30bc5","flowType":"ALERT","tenantId":null,"deviceId":"e2e-cam-001","sourceTopic":"iot-alert-notification","method":null,"eventTime":1785225128.570522303,"ingestTime":1785225128.570523340,"headers":{"channel":"party","partyId":"demo-mes","contractId":"contract-mes-alert","outboxId":"41da36d3-ad28-413d-952a-97a4f7e32ed7","endpoint":"http://127.0.0.1:18080/mes/alerts","contract":{"id":"contract-mes-alert","partyId":"demo-mes","flowType":"ALERT","channel":"party","endpoint":"http://127.0.0.1:18080/mes/alerts","mappingId":"map-identity","enabled":true,"headers":{},"createdAt":1.785219991667946E9},"partyType":"mes.rest"},"payload":{"id":"11022bb6ce554355810a098f3fd30bc5","alert_id":90001,"task_id":1,"task_name":"e2e-alert-task","device_id":"e2e-cam-001","device_name":"E2E Camera","alert":{"level":"HIGH","type":"intrusion","imageUrl":"http://127.0.0.1/minio/e2e-snap.jpg","videoUrl":"rtsp://127.0.0.1/live/e2e"},"timestamp":"2026-07-28T07:52:08.457554+00:00","shouldNotify":true},"partitionHint":1456176126}	\N	2026-07-28 15:52:09.518818+08	\N	2026-07-28 15:52:08.578409+08	\N	2026-07-28 15:52:09.528248+08	0
50e10d00-6be9-46cc-a1bc-28a9f5ee00a3	11022bb6ce554355810a098f3fd30bc5	e2e-http	contract-http-webhook	http	DELIVERED	0	\N	{"eventId":"11022bb6ce554355810a098f3fd30bc5","traceId":"11022bb6ce554355810a098f3fd30bc5","flowType":"ALERT","tenantId":null,"deviceId":"e2e-cam-001","sourceTopic":"iot-alert-notification","method":null,"eventTime":1785225128.570522303,"ingestTime":1785225128.570523340,"headers":{"channel":"http","partyId":"e2e-http","contractId":"contract-http-webhook","outboxId":"50e10d00-6be9-46cc-a1bc-28a9f5ee00a3","endpoint":"http://127.0.0.1:18080/webhook/transform","contract":{"id":"contract-http-webhook","partyId":"e2e-http","flowType":null,"channel":"http","endpoint":"http://127.0.0.1:18080/webhook/transform","mappingId":"map-identity","enabled":true,"headers":{"partySecret":"e2e-secret"},"createdAt":1.785219991667946E9},"partySecret":"e2e-secret","partyType":"mes.rest"},"payload":{"id":"11022bb6ce554355810a098f3fd30bc5","alert_id":90001,"task_id":1,"task_name":"e2e-alert-task","device_id":"e2e-cam-001","device_name":"E2E Camera","alert":{"level":"HIGH","type":"intrusion","imageUrl":"http://127.0.0.1/minio/e2e-snap.jpg","videoUrl":"rtsp://127.0.0.1/live/e2e"},"timestamp":"2026-07-28T07:52:08.457554+00:00","shouldNotify":true},"partitionHint":1456176126}	\N	2026-07-28 15:52:09.52564+08	\N	2026-07-28 15:52:08.58173+08	\N	2026-07-28 15:52:09.534377+08	0
e3cab340-ff8e-4b7d-b743-0691e424085a	4ff863f142744bf09ac41ca72fc60c41	demo-wms	contract-wms-vision	party	DELIVERED	0	\N	{"eventId":"4ff863f142744bf09ac41ca72fc60c41","traceId":"4ff863f142744bf09ac41ca72fc60c41","flowType":"VIDEO_META","tenantId":null,"deviceId":"e2e-cam-vision","sourceTopic":"iot-face-matching","method":null,"eventTime":1785225129.711675576,"ingestTime":1785225129.711676961,"headers":{"channel":"party","partyId":"demo-wms","contractId":"contract-wms-vision","outboxId":"e3cab340-ff8e-4b7d-b743-0691e424085a","endpoint":"http://127.0.0.1:18080/wms/vision","contract":{"id":"contract-wms-vision","partyId":"demo-wms","flowType":"VIDEO_META","channel":"party","endpoint":"http://127.0.0.1:18080/wms/vision","mappingId":"map-identity","enabled":true,"headers":{},"createdAt":1.785219997453394E9},"partyType":"wms.rest"},"payload":{"id":"4ff863f142744bf09ac41ca72fc60c41","device_id":"e2e-cam-vision","match_score":0.97,"image_url":"http://127.0.0.1/minio/e2e-face.jpg","kind":"face","timestamp":"2026-07-28T07:52:09.595894+00:00"},"partitionHint":462935301}	\N	2026-07-28 15:52:10.540294+08	\N	2026-07-28 15:52:09.71737+08	\N	2026-07-28 15:52:10.542019+08	0
a5148c0b-1173-40a0-bb7b-65e60be8e7df	e3b50d66a82345dcba815eb6911381bd	e2e-http	contract-http-webhook	http	DELIVERED	2	org.springframework.kafka.KafkaException: Send failed; nested exception is org.apache.kafka.common.errors.TimeoutException: Topic iot_transform_deliver not present in metadata after 60000 ms.	{"eventId":"e3b50d66a82345dcba815eb6911381bd","traceId":"e3b50d66a82345dcba815eb6911381bd","flowType":"DATA","tenantId":"1","deviceId":"e2e-device-001","sourceTopic":"iot_device_message","method":"thing.property.post","eventTime":1785225676.338336062,"ingestTime":1785225676.338337416,"headers":{"channel":"http","partyId":"e2e-http","contractId":"contract-http-webhook","outboxId":"a5148c0b-1173-40a0-bb7b-65e60be8e7df","endpoint":"http://172.17.0.1:18080/webhook/transform","contract":{"id":"contract-http-webhook","partyId":"e2e-http","flowType":null,"channel":"http","endpoint":"http://172.17.0.1:18080/webhook/transform","mappingId":"map-identity","enabled":true,"headers":{"partySecret":"e2e-secret"},"createdAt":1.785219991667946E9},"partySecret":"e2e-secret","partyType":"mes.rest"},"payload":{"id":"e3b50d66a82345dcba815eb6911381bd","reportTime":"2026-07-28T08:01:16.215576+00:00","deviceId":"e2e-device-001","tenantId":1,"serverId":"e2e-script","method":"thing.property.post","params":{"temperature":36.5,"humidity":55},"topic":"/iot/e2e_product/e2e-device-001/property/upstream/report","needReply":false},"partitionHint":366914959}	2026-07-28 16:04:22.729926+08	2026-07-28 16:04:23.529133+08	\N	2026-07-28 16:01:16.357009+08	\N	2026-07-28 16:04:23.540034+08	0
\.


--
-- Data for Name: transform_push_rule; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.transform_push_rule (id, target_system_id, flow_type, deliver_channel, endpoint_url, field_mapping_id, enabled, request_headers_json, creator, create_time, updater, update_time, deleted, remark) FROM stdin;
contract-mes-alert	demo-mes	ALERT	party	http://172.17.0.1:18080/mes/alerts	map-identity	t	{}		2026-07-28 14:26:31.667946+08	\N	2026-07-28 16:03:30.593298+08	0	
contract-erp-data	demo-erp	DATA	party	http://172.17.0.1:18080/erp/telemetry	map-identity	t	{}		2026-07-28 14:26:31.667946+08	\N	2026-07-28 16:03:30.604461+08	0	
contract-http-webhook	e2e-http	\N	http	http://172.17.0.1:18080/webhook/transform	map-identity	t	{"partySecret":"e2e-secret"}		2026-07-28 14:26:31.667946+08	\N	2026-07-28 16:03:30.608292+08	0	
contract-wms-vision	demo-wms	VIDEO_META	party	http://172.17.0.1:18080/wms/vision	map-identity	t	{}	\N	2026-07-28 14:26:37.453394+08	\N	2026-07-28 16:03:30.624723+08	0	
\.


--
-- Data for Name: transform_runtime_instance; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.transform_runtime_instance (instance_id, node_id, host, role, status, joined_groups, cpu_load, heap_used_mb, heap_max_mb, max_consumer_lag, deliver_success_rate, metrics_json, adapt_decision, last_heartbeat_time, creator, create_time, updater, update_time, deleted) FROM stdin;
f0b6c19e1354402bbfad71ebc1b754d9		ubuntu	full	ONLINE	transform.kafka.consume.device,transform.http.deliver,transform.party.deliver	5.49267578125	58	15744	0	1	{"published":0,"dlq":0,"delivered":0,"failed":0,"accepted":0}	KEEP	2026-07-28 15:01:51.635756+08	\N	2026-07-28 15:01:06.585625+08	\N	2026-07-28 15:01:51.637276+08	0
transform-runtime-2-ubuntu-48111		6a5ba42e0bd2	full	ONLINE	transform.kafka.consume.device,transform.http.deliver,transform.party.deliver	3.4609375	131	1024	0	1	{"published":0,"dlq":0,"delivered":0,"failed":0,"accepted":0}	KEEP	2026-07-28 16:11:48.780184+08	\N	2026-07-28 15:09:35.371649+08	\N	2026-07-28 16:11:48.780523+08	0
transform-runtime-1-ubuntu-48110		552ee59c8ecf	full	ONLINE	transform.kafka.consume.device,transform.http.deliver,transform.party.deliver	3.162109375	96	1024	0	1	{"failed":0,"delivered":0,"dlq":0,"published":0,"accepted":0}	KEEP	2026-07-28 16:12:01.722228+08	\N	2026-07-28 15:09:35.199951+08	\N	2026-07-28 16:12:01.722912+08	0
tf-pipe-test-1-ubuntu-48112-1500082	worker-test	27fb8d827715	full	ONLINE	transform.kafka.consume.device,transform.http.deliver,transform.party.deliver	1.7109375	112	1024	0	1	{"dlq":0,"published":0,"accepted":0,"failed":0,"delivered":0}	KEEP	2026-07-28 15:58:01.849675+08	\N	2026-07-28 15:58:01.996225+08	\N	2026-07-28 15:58:01.887048+08	0
8bc0c8c288fa4f1eb1d4858a2ce47a25		ubuntu	full	ONLINE	transform.kafka.consume.device,transform.http.deliver,transform.party.deliver	2.90869140625	105	15744	0	1	{"published":22,"accepted":11,"failed":0,"delivered":22,"dlq":0}	KEEP	2026-07-28 16:12:05.982575+08	\N	2026-07-28 15:02:04.272794+08	\N	2026-07-28 16:12:05.98299+08	0
tf-pipe-test-1-ubuntu-48112-1543331	worker-test	e10b22874e4e	full	ONLINE	transform.kafka.consume.device,transform.http.deliver,transform.party.deliver	2.67529296875	138	1024	0	1	{"delivered":0,"failed":0,"accepted":0,"published":0,"dlq":0}	KEEP	2026-07-28 16:12:11.718703+08	\N	2026-07-28 16:03:26.504689+08	\N	2026-07-28 16:12:11.718969+08	0
tf-pipe-test-1-ubuntu-48112-1524797	worker-test	1e271b35fd6e	full	ONLINE	transform.kafka.consume.device,transform.http.deliver,transform.party.deliver	2.8837890625	139	1024	0	1	{"delivered":0,"dlq":0,"published":0,"accepted":0,"failed":0}	KEEP	2026-07-28 16:02:12.236038+08	\N	2026-07-28 16:01:12.173151+08	\N	2026-07-28 16:02:12.237845+08	0
\.


--
-- Data for Name: transform_target_system; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.transform_target_system (id, system_name, connector_type, enabled, config_json, creator, create_time, updater, update_time, deleted, remark) FROM stdin;
demo-mes	Demo MES	mes.rest	t	{}		2026-07-28 14:26:31.664048+08	\N	2026-07-28 16:03:30.5712+08	0	
demo-erp	Demo ERP	erp.rest	t	{}		2026-07-28 14:26:31.664048+08	\N	2026-07-28 16:03:30.57538+08	0	
demo-wms	Demo WMS	wms.rest	t	{}		2026-07-28 14:26:31.664048+08	\N	2026-07-28 16:03:30.578968+08	0	
e2e-http	E2E HTTP Webhook	mes.rest	t	{}	\N	2026-07-28 14:26:37.416178+08	\N	2026-07-28 16:03:30.582995+08	0	
\.


--
-- Name: transform_archive_object tf_backup_object_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transform_archive_object
    ADD CONSTRAINT tf_backup_object_pkey PRIMARY KEY (id);


--
-- Name: transform_push_rule tf_contract_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transform_push_rule
    ADD CONSTRAINT tf_contract_pkey PRIMARY KEY (id);


--
-- Name: transform_push_failure tf_dlq_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transform_push_failure
    ADD CONSTRAINT tf_dlq_pkey PRIMARY KEY (id);


--
-- Name: transform_field_mapping tf_mapping_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transform_field_mapping
    ADD CONSTRAINT tf_mapping_pkey PRIMARY KEY (id);


--
-- Name: transform_target_system tf_party_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transform_target_system
    ADD CONSTRAINT tf_party_pkey PRIMARY KEY (id);


--
-- Name: transform_flow_pipeline tf_pipeline_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transform_flow_pipeline
    ADD CONSTRAINT tf_pipeline_pkey PRIMARY KEY (id);


--
-- Name: transform_push_record transform_push_record_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transform_push_record
    ADD CONSTRAINT transform_push_record_pkey PRIMARY KEY (id);


--
-- Name: transform_runtime_instance transform_runtime_instance_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transform_runtime_instance
    ADD CONSTRAINT transform_runtime_instance_pkey PRIMARY KEY (instance_id);


--
-- Name: idx_transform_archive_object_event; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transform_archive_object_event ON public.transform_archive_object USING btree (event_id);


--
-- Name: idx_transform_push_failure_create_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transform_push_failure_create_time ON public.transform_push_failure USING btree (create_time);


--
-- Name: idx_transform_push_failure_record; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transform_push_failure_record ON public.transform_push_failure USING btree (push_record_id);


--
-- Name: idx_transform_push_record_create_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transform_push_record_create_time ON public.transform_push_record USING btree (create_time);


--
-- Name: idx_transform_push_record_status_retry; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transform_push_record_status_retry ON public.transform_push_record USING btree (push_status, next_retry_time);


--
-- Name: idx_transform_push_rule_flow; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transform_push_rule_flow ON public.transform_push_rule USING btree (flow_type) WHERE (deleted = 0);


--
-- Name: idx_transform_push_rule_target; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transform_push_rule_target ON public.transform_push_rule USING btree (target_system_id);


--
-- Name: idx_transform_runtime_instance_heartbeat; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transform_runtime_instance_heartbeat ON public.transform_runtime_instance USING btree (last_heartbeat_time);


--
-- Name: idx_transform_runtime_instance_node; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transform_runtime_instance_node ON public.transform_runtime_instance USING btree (node_id);


--
-- Name: uk_transform_push_record_event_rule; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uk_transform_push_record_event_rule ON public.transform_push_record USING btree (event_id, push_rule_id) WHERE (deleted = 0);


--
-- PostgreSQL database dump complete
--

\unrestrict l5Ne7pG1XmbDQe87g4SmkIqYe2sm3lIMx47VUo7dDk9uf05XMaES6uui8h2pKBx

