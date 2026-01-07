--
-- PostgreSQL database dump
--

\restrict eFhTWSxuHf2af2JEdSHaLgUZhNpAddNlm7bKAUcel6gbo3lbiNzqBIyS5aTigmF

-- Dumped from database version 18.1 (Debian 18.1-1.pgdg13+2)
-- Dumped by pg_dump version 18.1 (Ubuntu 18.1-1.pgdg24.04+2)

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
-- Name: wvp_cloud_record; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.wvp_cloud_record (
    id integer NOT NULL,
    app character varying(255),
    stream character varying(255),
    call_id character varying(255),
    start_time bigint,
    end_time bigint,
    media_server_id character varying(50),
    server_id character varying(50),
    file_name character varying(255),
    folder character varying(500),
    file_path character varying(500),
    collect boolean DEFAULT false,
    file_size bigint,
    time_len double precision
);


ALTER TABLE public.wvp_cloud_record OWNER TO postgres;

--
-- Name: TABLE wvp_cloud_record; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.wvp_cloud_record IS '云端录像记录';


--
-- Name: COLUMN wvp_cloud_record.id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_cloud_record.id IS '主键ID';


--
-- Name: COLUMN wvp_cloud_record.app; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_cloud_record.app IS '应用名';


--
-- Name: COLUMN wvp_cloud_record.stream; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_cloud_record.stream IS '流ID';


--
-- Name: COLUMN wvp_cloud_record.call_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_cloud_record.call_id IS '会话ID';


--
-- Name: COLUMN wvp_cloud_record.start_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_cloud_record.start_time IS '录像开始时间';


--
-- Name: COLUMN wvp_cloud_record.end_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_cloud_record.end_time IS '录像结束时间';


--
-- Name: COLUMN wvp_cloud_record.media_server_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_cloud_record.media_server_id IS '媒体服务器ID';


--
-- Name: COLUMN wvp_cloud_record.server_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_cloud_record.server_id IS '信令服务器ID';


--
-- Name: COLUMN wvp_cloud_record.file_name; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_cloud_record.file_name IS '文件名';


--
-- Name: COLUMN wvp_cloud_record.folder; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_cloud_record.folder IS '目录';


--
-- Name: COLUMN wvp_cloud_record.file_path; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_cloud_record.file_path IS '完整路径';


--
-- Name: COLUMN wvp_cloud_record.collect; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_cloud_record.collect IS '是否收藏';


--
-- Name: COLUMN wvp_cloud_record.file_size; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_cloud_record.file_size IS '文件大小';


--
-- Name: COLUMN wvp_cloud_record.time_len; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_cloud_record.time_len IS '时长';


--
-- Name: wvp_cloud_record_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.wvp_cloud_record_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.wvp_cloud_record_id_seq OWNER TO postgres;

--
-- Name: wvp_cloud_record_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.wvp_cloud_record_id_seq OWNED BY public.wvp_cloud_record.id;


--
-- Name: wvp_common_group; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.wvp_common_group (
    id integer NOT NULL,
    device_id character varying(50) NOT NULL,
    name character varying(255) NOT NULL,
    parent_id integer,
    parent_device_id character varying(50) DEFAULT NULL::character varying,
    business_group character varying(50) NOT NULL,
    create_time character varying(50) NOT NULL,
    update_time character varying(50) NOT NULL,
    civil_code character varying(50) DEFAULT NULL::character varying,
    alias character varying(255) DEFAULT NULL::character varying
);


ALTER TABLE public.wvp_common_group OWNER TO postgres;

--
-- Name: TABLE wvp_common_group; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.wvp_common_group IS '通用分组表，存储行业或组织结构';


--
-- Name: COLUMN wvp_common_group.id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_common_group.id IS '主键ID';


--
-- Name: COLUMN wvp_common_group.device_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_common_group.device_id IS '分组对应的平台或设备ID';


--
-- Name: COLUMN wvp_common_group.name; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_common_group.name IS '分组名称';


--
-- Name: COLUMN wvp_common_group.parent_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_common_group.parent_id IS '父级分组ID';


--
-- Name: COLUMN wvp_common_group.parent_device_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_common_group.parent_device_id IS '父级分组对应的设备ID';


--
-- Name: COLUMN wvp_common_group.business_group; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_common_group.business_group IS '业务分组编码';


--
-- Name: COLUMN wvp_common_group.create_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_common_group.create_time IS '创建时间';


--
-- Name: COLUMN wvp_common_group.update_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_common_group.update_time IS '更新时间';


--
-- Name: COLUMN wvp_common_group.civil_code; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_common_group.civil_code IS '行政区划代码';


--
-- Name: COLUMN wvp_common_group.alias; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_common_group.alias IS '别名';


--
-- Name: wvp_common_group_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.wvp_common_group_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.wvp_common_group_id_seq OWNER TO postgres;

--
-- Name: wvp_common_group_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.wvp_common_group_id_seq OWNED BY public.wvp_common_group.id;


--
-- Name: wvp_common_region; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.wvp_common_region (
    id integer NOT NULL,
    device_id character varying(50) NOT NULL,
    name character varying(255) NOT NULL,
    parent_id integer,
    parent_device_id character varying(50) DEFAULT NULL::character varying,
    create_time character varying(50) NOT NULL,
    update_time character varying(50) NOT NULL
);


ALTER TABLE public.wvp_common_region OWNER TO postgres;

--
-- Name: TABLE wvp_common_region; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.wvp_common_region IS '通用行政区域表';


--
-- Name: COLUMN wvp_common_region.id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_common_region.id IS '主键ID';


--
-- Name: COLUMN wvp_common_region.device_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_common_region.device_id IS '区域对应的平台或设备ID';


--
-- Name: COLUMN wvp_common_region.name; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_common_region.name IS '区域名称';


--
-- Name: COLUMN wvp_common_region.parent_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_common_region.parent_id IS '父级区域ID';


--
-- Name: COLUMN wvp_common_region.parent_device_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_common_region.parent_device_id IS '父级区域的设备ID';


--
-- Name: COLUMN wvp_common_region.create_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_common_region.create_time IS '创建时间';


--
-- Name: COLUMN wvp_common_region.update_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_common_region.update_time IS '更新时间';


--
-- Name: wvp_common_region_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.wvp_common_region_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.wvp_common_region_id_seq OWNER TO postgres;

--
-- Name: wvp_common_region_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.wvp_common_region_id_seq OWNED BY public.wvp_common_region.id;


--
-- Name: wvp_device; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.wvp_device (
    id integer NOT NULL,
    device_id character varying(50) NOT NULL,
    name character varying(255),
    manufacturer character varying(255),
    model character varying(255),
    firmware character varying(255),
    transport character varying(50),
    stream_mode character varying(50),
    on_line boolean DEFAULT false,
    register_time character varying(50),
    keepalive_time character varying(50),
    ip character varying(50),
    create_time character varying(50),
    update_time character varying(50),
    port integer,
    expires integer,
    subscribe_cycle_for_catalog integer DEFAULT 0,
    subscribe_cycle_for_mobile_position integer DEFAULT 0,
    mobile_position_submission_interval integer DEFAULT 5,
    subscribe_cycle_for_alarm integer DEFAULT 0,
    host_address character varying(50),
    charset character varying(50),
    ssrc_check boolean DEFAULT false,
    geo_coord_sys character varying(50),
    media_server_id character varying(50) DEFAULT 'auto'::character varying,
    custom_name character varying(255),
    sdp_ip character varying(50),
    local_ip character varying(50),
    password character varying(255),
    as_message_channel boolean DEFAULT false,
    heart_beat_interval integer,
    heart_beat_count integer,
    position_capability integer,
    broadcast_push_after_ack boolean DEFAULT false,
    server_id character varying(50)
);


ALTER TABLE public.wvp_device OWNER TO postgres;

--
-- Name: TABLE wvp_device; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.wvp_device IS '存储国标设备的基础信息及在线状态';


--
-- Name: COLUMN wvp_device.id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device.id IS '主键ID';


--
-- Name: COLUMN wvp_device.device_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device.device_id IS '国标设备编号';


--
-- Name: COLUMN wvp_device.name; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device.name IS '设备名称';


--
-- Name: COLUMN wvp_device.manufacturer; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device.manufacturer IS '设备厂商';


--
-- Name: COLUMN wvp_device.model; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device.model IS '设备型号';


--
-- Name: COLUMN wvp_device.firmware; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device.firmware IS '固件版本号';


--
-- Name: COLUMN wvp_device.transport; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device.transport IS '信令传输协议（TCP/UDP）';


--
-- Name: COLUMN wvp_device.stream_mode; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device.stream_mode IS '拉流方式（主动/被动）';


--
-- Name: COLUMN wvp_device.on_line; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device.on_line IS '在线状态';


--
-- Name: COLUMN wvp_device.register_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device.register_time IS '注册时间';


--
-- Name: COLUMN wvp_device.keepalive_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device.keepalive_time IS '最近心跳时间';


--
-- Name: COLUMN wvp_device.ip; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device.ip IS '设备IP地址';


--
-- Name: COLUMN wvp_device.create_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device.create_time IS '创建时间';


--
-- Name: COLUMN wvp_device.update_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device.update_time IS '更新时间';


--
-- Name: COLUMN wvp_device.port; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device.port IS '信令端口';


--
-- Name: COLUMN wvp_device.expires; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device.expires IS '注册有效期';


--
-- Name: COLUMN wvp_device.subscribe_cycle_for_catalog; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device.subscribe_cycle_for_catalog IS '目录订阅周期';


--
-- Name: COLUMN wvp_device.subscribe_cycle_for_mobile_position; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device.subscribe_cycle_for_mobile_position IS '移动位置订阅周期';


--
-- Name: COLUMN wvp_device.mobile_position_submission_interval; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device.mobile_position_submission_interval IS '移动位置上报间隔';


--
-- Name: COLUMN wvp_device.subscribe_cycle_for_alarm; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device.subscribe_cycle_for_alarm IS '报警订阅周期';


--
-- Name: COLUMN wvp_device.host_address; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device.host_address IS '设备域名/主机地址';


--
-- Name: COLUMN wvp_device.charset; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device.charset IS '信令字符集';


--
-- Name: COLUMN wvp_device.ssrc_check; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device.ssrc_check IS '是否校验SSRC';


--
-- Name: COLUMN wvp_device.geo_coord_sys; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device.geo_coord_sys IS '坐标系类型';


--
-- Name: COLUMN wvp_device.media_server_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device.media_server_id IS '绑定的流媒体服务ID';


--
-- Name: COLUMN wvp_device.custom_name; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device.custom_name IS '自定义显示名称';


--
-- Name: COLUMN wvp_device.sdp_ip; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device.sdp_ip IS 'SDP中携带的IP';


--
-- Name: COLUMN wvp_device.local_ip; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device.local_ip IS '本地局域网IP';


--
-- Name: COLUMN wvp_device.password; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device.password IS '设备鉴权密码';


--
-- Name: COLUMN wvp_device.as_message_channel; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device.as_message_channel IS '是否作为消息通道';


--
-- Name: COLUMN wvp_device.heart_beat_interval; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device.heart_beat_interval IS '心跳间隔';


--
-- Name: COLUMN wvp_device.heart_beat_count; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device.heart_beat_count IS '心跳失败次数';


--
-- Name: COLUMN wvp_device.position_capability; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device.position_capability IS '定位能力标识';


--
-- Name: COLUMN wvp_device.broadcast_push_after_ack; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device.broadcast_push_after_ack IS 'ACK后是否自动推流';


--
-- Name: COLUMN wvp_device.server_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device.server_id IS '所属信令服务器ID';


--
-- Name: wvp_device_alarm; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.wvp_device_alarm (
    id integer NOT NULL,
    device_id character varying(50) NOT NULL,
    channel_id character varying(50) NOT NULL,
    alarm_priority character varying(50),
    alarm_method character varying(50),
    alarm_time character varying(50),
    alarm_description character varying(255),
    longitude double precision,
    latitude double precision,
    alarm_type character varying(50),
    create_time character varying(50) NOT NULL
);


ALTER TABLE public.wvp_device_alarm OWNER TO postgres;

--
-- Name: TABLE wvp_device_alarm; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.wvp_device_alarm IS '记录各设备上报的报警信息';


--
-- Name: COLUMN wvp_device_alarm.id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_alarm.id IS '主键ID';


--
-- Name: COLUMN wvp_device_alarm.device_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_alarm.device_id IS '国标设备ID';


--
-- Name: COLUMN wvp_device_alarm.channel_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_alarm.channel_id IS '报警关联的通道ID';


--
-- Name: COLUMN wvp_device_alarm.alarm_priority; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_alarm.alarm_priority IS '报警级别';


--
-- Name: COLUMN wvp_device_alarm.alarm_method; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_alarm.alarm_method IS '报警方式（视频/语音等）';


--
-- Name: COLUMN wvp_device_alarm.alarm_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_alarm.alarm_time IS '报警发生时间';


--
-- Name: COLUMN wvp_device_alarm.alarm_description; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_alarm.alarm_description IS '报警描述';


--
-- Name: COLUMN wvp_device_alarm.longitude; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_alarm.longitude IS '报警经度';


--
-- Name: COLUMN wvp_device_alarm.latitude; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_alarm.latitude IS '报警纬度';


--
-- Name: COLUMN wvp_device_alarm.alarm_type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_alarm.alarm_type IS '报警类型';


--
-- Name: COLUMN wvp_device_alarm.create_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_alarm.create_time IS '数据入库时间';


--
-- Name: wvp_device_alarm_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.wvp_device_alarm_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.wvp_device_alarm_id_seq OWNER TO postgres;

--
-- Name: wvp_device_alarm_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.wvp_device_alarm_id_seq OWNED BY public.wvp_device_alarm.id;


--
-- Name: wvp_device_channel; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.wvp_device_channel (
    id integer NOT NULL,
    device_id character varying(50),
    name character varying(255),
    manufacturer character varying(50),
    model character varying(50),
    owner character varying(50),
    civil_code character varying(50),
    block character varying(50),
    address character varying(50),
    parental integer,
    parent_id character varying(50),
    safety_way integer,
    register_way integer,
    cert_num character varying(50),
    certifiable integer,
    err_code integer,
    end_time character varying(50),
    secrecy integer,
    ip_address character varying(50),
    port integer,
    password character varying(255),
    status character varying(50),
    longitude double precision,
    latitude double precision,
    ptz_type integer,
    position_type integer,
    room_type integer,
    use_type integer,
    supply_light_type integer,
    direction_type integer,
    resolution character varying(255),
    business_group_id character varying(255),
    download_speed character varying(255),
    svc_space_support_mod integer,
    svc_time_support_mode integer,
    create_time character varying(50) NOT NULL,
    update_time character varying(50) NOT NULL,
    sub_count integer,
    stream_id character varying(255),
    has_audio boolean DEFAULT false,
    gps_time character varying(50),
    stream_identification character varying(50),
    channel_type integer DEFAULT 0 NOT NULL,
    map_level integer DEFAULT 0,
    gb_device_id character varying(50),
    gb_name character varying(255),
    gb_manufacturer character varying(255),
    gb_model character varying(255),
    gb_owner character varying(255),
    gb_civil_code character varying(255),
    gb_block character varying(255),
    gb_address character varying(255),
    gb_parental integer,
    gb_parent_id character varying(255),
    gb_safety_way integer,
    gb_register_way integer,
    gb_cert_num character varying(50),
    gb_certifiable integer,
    gb_err_code integer,
    gb_end_time character varying(50),
    gb_secrecy integer,
    gb_ip_address character varying(50),
    gb_port integer,
    gb_password character varying(50),
    gb_status character varying(50),
    gb_longitude double precision,
    gb_latitude double precision,
    gb_business_group_id character varying(50),
    gb_ptz_type integer,
    gb_position_type integer,
    gb_room_type integer,
    gb_use_type integer,
    gb_supply_light_type integer,
    gb_direction_type integer,
    gb_resolution character varying(255),
    gb_download_speed character varying(255),
    gb_svc_space_support_mod integer,
    gb_svc_time_support_mode integer,
    record_plan_id integer,
    data_type integer NOT NULL,
    data_device_id integer NOT NULL,
    gps_speed double precision,
    gps_altitude double precision,
    gps_direction double precision,
    enable_broadcast integer DEFAULT 0
);


ALTER TABLE public.wvp_device_channel OWNER TO postgres;

--
-- Name: TABLE wvp_device_channel; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.wvp_device_channel IS '保存设备下的通道信息以及扩展属性';


--
-- Name: COLUMN wvp_device_channel.id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.id IS '主键ID';


--
-- Name: COLUMN wvp_device_channel.device_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.device_id IS '所属设备ID';


--
-- Name: COLUMN wvp_device_channel.name; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.name IS '通道名称';


--
-- Name: COLUMN wvp_device_channel.manufacturer; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.manufacturer IS '厂商';


--
-- Name: COLUMN wvp_device_channel.model; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.model IS '型号';


--
-- Name: COLUMN wvp_device_channel.owner; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.owner IS '归属单位';


--
-- Name: COLUMN wvp_device_channel.civil_code; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.civil_code IS '行政区划代码';


--
-- Name: COLUMN wvp_device_channel.block; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.block IS '区域/小区编号';


--
-- Name: COLUMN wvp_device_channel.address; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.address IS '安装地址';


--
-- Name: COLUMN wvp_device_channel.parental; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.parental IS '是否有子节点';


--
-- Name: COLUMN wvp_device_channel.parent_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.parent_id IS '父级通道ID';


--
-- Name: COLUMN wvp_device_channel.safety_way; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.safety_way IS '安全防范等级';


--
-- Name: COLUMN wvp_device_channel.register_way; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.register_way IS '注册方式';


--
-- Name: COLUMN wvp_device_channel.cert_num; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.cert_num IS '证书编号';


--
-- Name: COLUMN wvp_device_channel.certifiable; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.certifiable IS '是否可认证';


--
-- Name: COLUMN wvp_device_channel.err_code; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.err_code IS '故障状态码';


--
-- Name: COLUMN wvp_device_channel.end_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.end_time IS '服务截止时间';


--
-- Name: COLUMN wvp_device_channel.secrecy; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.secrecy IS '保密级别';


--
-- Name: COLUMN wvp_device_channel.ip_address; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.ip_address IS '设备IP地址';


--
-- Name: COLUMN wvp_device_channel.port; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.port IS '设备端口';


--
-- Name: COLUMN wvp_device_channel.password; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.password IS '访问密码';


--
-- Name: COLUMN wvp_device_channel.status; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.status IS '在线状态';


--
-- Name: COLUMN wvp_device_channel.longitude; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.longitude IS '经度';


--
-- Name: COLUMN wvp_device_channel.latitude; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.latitude IS '纬度';


--
-- Name: COLUMN wvp_device_channel.ptz_type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.ptz_type IS '云台类型';


--
-- Name: COLUMN wvp_device_channel.position_type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.position_type IS '点位类型';


--
-- Name: COLUMN wvp_device_channel.room_type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.room_type IS '房间类型';


--
-- Name: COLUMN wvp_device_channel.use_type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.use_type IS '使用性质';


--
-- Name: COLUMN wvp_device_channel.supply_light_type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.supply_light_type IS '补光方式';


--
-- Name: COLUMN wvp_device_channel.direction_type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.direction_type IS '朝向';


--
-- Name: COLUMN wvp_device_channel.resolution; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.resolution IS '分辨率';


--
-- Name: COLUMN wvp_device_channel.business_group_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.business_group_id IS '业务分组ID';


--
-- Name: COLUMN wvp_device_channel.download_speed; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.download_speed IS '下载/码流速率';


--
-- Name: COLUMN wvp_device_channel.svc_space_support_mod; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.svc_space_support_mod IS '空域SVC能力';


--
-- Name: COLUMN wvp_device_channel.svc_time_support_mode; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.svc_time_support_mode IS '时域SVC能力';


--
-- Name: COLUMN wvp_device_channel.create_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.create_time IS '创建时间';


--
-- Name: COLUMN wvp_device_channel.update_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.update_time IS '更新时间';


--
-- Name: COLUMN wvp_device_channel.sub_count; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.sub_count IS '子节点数量';


--
-- Name: COLUMN wvp_device_channel.stream_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.stream_id IS '绑定的流ID';


--
-- Name: COLUMN wvp_device_channel.has_audio; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.has_audio IS '是否有音频';


--
-- Name: COLUMN wvp_device_channel.gps_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.gps_time IS 'GPS定位时间';


--
-- Name: COLUMN wvp_device_channel.stream_identification; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.stream_identification IS '流标识';


--
-- Name: COLUMN wvp_device_channel.channel_type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.channel_type IS '通道类型';


--
-- Name: COLUMN wvp_device_channel.map_level; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.map_level IS '地图层级';


--
-- Name: COLUMN wvp_device_channel.gb_device_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.gb_device_id IS 'GB内的设备ID';


--
-- Name: COLUMN wvp_device_channel.gb_name; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.gb_name IS 'GB上报的名称';


--
-- Name: COLUMN wvp_device_channel.gb_manufacturer; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.gb_manufacturer IS 'GB厂商';


--
-- Name: COLUMN wvp_device_channel.gb_model; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.gb_model IS 'GB型号';


--
-- Name: COLUMN wvp_device_channel.gb_owner; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.gb_owner IS 'GB归属';


--
-- Name: COLUMN wvp_device_channel.gb_civil_code; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.gb_civil_code IS 'GB行政区划';


--
-- Name: COLUMN wvp_device_channel.gb_block; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.gb_block IS 'GB区域';


--
-- Name: COLUMN wvp_device_channel.gb_address; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.gb_address IS 'GB地址';


--
-- Name: COLUMN wvp_device_channel.gb_parental; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.gb_parental IS 'GB子节点标识';


--
-- Name: COLUMN wvp_device_channel.gb_parent_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.gb_parent_id IS 'GB父通道';


--
-- Name: COLUMN wvp_device_channel.gb_safety_way; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.gb_safety_way IS 'GB安全防范';


--
-- Name: COLUMN wvp_device_channel.gb_register_way; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.gb_register_way IS 'GB注册方式';


--
-- Name: COLUMN wvp_device_channel.gb_cert_num; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.gb_cert_num IS 'GB证书编号';


--
-- Name: COLUMN wvp_device_channel.gb_certifiable; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.gb_certifiable IS 'GB认证标志';


--
-- Name: COLUMN wvp_device_channel.gb_err_code; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.gb_err_code IS 'GB错误码';


--
-- Name: COLUMN wvp_device_channel.gb_end_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.gb_end_time IS 'GB截止时间';


--
-- Name: COLUMN wvp_device_channel.gb_secrecy; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.gb_secrecy IS 'GB保密级别';


--
-- Name: COLUMN wvp_device_channel.gb_ip_address; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.gb_ip_address IS 'GB IP';


--
-- Name: COLUMN wvp_device_channel.gb_port; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.gb_port IS 'GB端口';


--
-- Name: COLUMN wvp_device_channel.gb_password; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.gb_password IS 'GB接入密码';


--
-- Name: COLUMN wvp_device_channel.gb_status; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.gb_status IS 'GB状态';


--
-- Name: COLUMN wvp_device_channel.gb_longitude; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.gb_longitude IS 'GB经度';


--
-- Name: COLUMN wvp_device_channel.gb_latitude; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.gb_latitude IS 'GB纬度';


--
-- Name: COLUMN wvp_device_channel.gb_business_group_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.gb_business_group_id IS 'GB业务分组';


--
-- Name: COLUMN wvp_device_channel.gb_ptz_type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.gb_ptz_type IS 'GB云台类型';


--
-- Name: COLUMN wvp_device_channel.gb_position_type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.gb_position_type IS 'GB点位类型';


--
-- Name: COLUMN wvp_device_channel.gb_room_type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.gb_room_type IS 'GB房间类型';


--
-- Name: COLUMN wvp_device_channel.gb_use_type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.gb_use_type IS 'GB用途';


--
-- Name: COLUMN wvp_device_channel.gb_supply_light_type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.gb_supply_light_type IS 'GB补光';


--
-- Name: COLUMN wvp_device_channel.gb_direction_type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.gb_direction_type IS 'GB朝向';


--
-- Name: COLUMN wvp_device_channel.gb_resolution; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.gb_resolution IS 'GB分辨率';


--
-- Name: COLUMN wvp_device_channel.gb_download_speed; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.gb_download_speed IS 'GB码流速率';


--
-- Name: COLUMN wvp_device_channel.gb_svc_space_support_mod; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.gb_svc_space_support_mod IS 'GB空域SVC';


--
-- Name: COLUMN wvp_device_channel.gb_svc_time_support_mode; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.gb_svc_time_support_mode IS 'GB时域SVC';


--
-- Name: COLUMN wvp_device_channel.record_plan_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.record_plan_id IS '绑定的录像计划ID';


--
-- Name: COLUMN wvp_device_channel.data_type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.data_type IS '数据类型标识';


--
-- Name: COLUMN wvp_device_channel.data_device_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.data_device_id IS '数据来源设备主键';


--
-- Name: COLUMN wvp_device_channel.gps_speed; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.gps_speed IS 'GPS速度';


--
-- Name: COLUMN wvp_device_channel.gps_altitude; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.gps_altitude IS 'GPS海拔';


--
-- Name: COLUMN wvp_device_channel.gps_direction; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.gps_direction IS 'GPS方向';


--
-- Name: COLUMN wvp_device_channel.enable_broadcast; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_channel.enable_broadcast IS '是否支持广播';


--
-- Name: wvp_device_channel_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.wvp_device_channel_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.wvp_device_channel_id_seq OWNER TO postgres;

--
-- Name: wvp_device_channel_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.wvp_device_channel_id_seq OWNED BY public.wvp_device_channel.id;


--
-- Name: wvp_device_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.wvp_device_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.wvp_device_id_seq OWNER TO postgres;

--
-- Name: wvp_device_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.wvp_device_id_seq OWNED BY public.wvp_device.id;


--
-- Name: wvp_device_mobile_position; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.wvp_device_mobile_position (
    id integer NOT NULL,
    device_id character varying(50) NOT NULL,
    channel_id character varying(50) NOT NULL,
    device_name character varying(255),
    "time" character varying(50),
    longitude double precision,
    latitude double precision,
    altitude double precision,
    speed double precision,
    direction double precision,
    report_source character varying(50),
    create_time character varying(50)
);


ALTER TABLE public.wvp_device_mobile_position OWNER TO postgres;

--
-- Name: TABLE wvp_device_mobile_position; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.wvp_device_mobile_position IS '存储移动位置订阅上报的数据';


--
-- Name: COLUMN wvp_device_mobile_position.id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_mobile_position.id IS '主键ID';


--
-- Name: COLUMN wvp_device_mobile_position.device_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_mobile_position.device_id IS '设备ID';


--
-- Name: COLUMN wvp_device_mobile_position.channel_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_mobile_position.channel_id IS '通道ID';


--
-- Name: COLUMN wvp_device_mobile_position.device_name; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_mobile_position.device_name IS '设备名称';


--
-- Name: COLUMN wvp_device_mobile_position."time"; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_mobile_position."time" IS '上报时间';


--
-- Name: COLUMN wvp_device_mobile_position.longitude; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_mobile_position.longitude IS '经度';


--
-- Name: COLUMN wvp_device_mobile_position.latitude; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_mobile_position.latitude IS '纬度';


--
-- Name: COLUMN wvp_device_mobile_position.altitude; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_mobile_position.altitude IS '海拔';


--
-- Name: COLUMN wvp_device_mobile_position.speed; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_mobile_position.speed IS '速度';


--
-- Name: COLUMN wvp_device_mobile_position.direction; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_mobile_position.direction IS '方向角';


--
-- Name: COLUMN wvp_device_mobile_position.report_source; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_mobile_position.report_source IS '上报来源';


--
-- Name: COLUMN wvp_device_mobile_position.create_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_device_mobile_position.create_time IS '入库时间';


--
-- Name: wvp_device_mobile_position_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.wvp_device_mobile_position_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.wvp_device_mobile_position_id_seq OWNER TO postgres;

--
-- Name: wvp_device_mobile_position_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.wvp_device_mobile_position_id_seq OWNED BY public.wvp_device_mobile_position.id;


--
-- Name: wvp_jt_channel; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.wvp_jt_channel (
    id integer NOT NULL,
    terminal_db_id integer,
    channel_id integer,
    has_audio boolean DEFAULT false,
    name character varying(255),
    update_time character varying(50) NOT NULL,
    create_time character varying(50) NOT NULL
);


ALTER TABLE public.wvp_jt_channel OWNER TO postgres;

--
-- Name: TABLE wvp_jt_channel; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.wvp_jt_channel IS '交通部 JT/T 1076 通道信息';


--
-- Name: COLUMN wvp_jt_channel.id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_jt_channel.id IS '主键ID';


--
-- Name: COLUMN wvp_jt_channel.terminal_db_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_jt_channel.terminal_db_id IS '所属终端记录ID';


--
-- Name: COLUMN wvp_jt_channel.channel_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_jt_channel.channel_id IS '通道号';


--
-- Name: COLUMN wvp_jt_channel.has_audio; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_jt_channel.has_audio IS '是否有音频';


--
-- Name: COLUMN wvp_jt_channel.name; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_jt_channel.name IS '通道名称';


--
-- Name: COLUMN wvp_jt_channel.update_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_jt_channel.update_time IS '更新时间';


--
-- Name: COLUMN wvp_jt_channel.create_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_jt_channel.create_time IS '创建时间';


--
-- Name: wvp_jt_channel_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.wvp_jt_channel_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.wvp_jt_channel_id_seq OWNER TO postgres;

--
-- Name: wvp_jt_channel_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.wvp_jt_channel_id_seq OWNED BY public.wvp_jt_channel.id;


--
-- Name: wvp_jt_terminal; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.wvp_jt_terminal (
    id integer NOT NULL,
    phone_number character varying(50),
    terminal_id character varying(50),
    province_id character varying(50),
    province_text character varying(100),
    city_id character varying(50),
    city_text character varying(100),
    maker_id character varying(50),
    model character varying(50),
    plate_color character varying(50),
    plate_no character varying(50),
    longitude double precision,
    latitude double precision,
    status boolean DEFAULT false,
    register_time character varying(50) DEFAULT NULL::character varying,
    update_time character varying(50) NOT NULL,
    create_time character varying(50) NOT NULL,
    geo_coord_sys character varying(50),
    media_server_id character varying(50) DEFAULT 'auto'::character varying,
    sdp_ip character varying(50)
);


ALTER TABLE public.wvp_jt_terminal OWNER TO postgres;

--
-- Name: TABLE wvp_jt_terminal; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.wvp_jt_terminal IS '交通部 JT/T 1076 终端信息';


--
-- Name: COLUMN wvp_jt_terminal.id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_jt_terminal.id IS '主键ID';


--
-- Name: COLUMN wvp_jt_terminal.phone_number; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_jt_terminal.phone_number IS '终端SIM卡号';


--
-- Name: COLUMN wvp_jt_terminal.terminal_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_jt_terminal.terminal_id IS '终端设备ID';


--
-- Name: COLUMN wvp_jt_terminal.province_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_jt_terminal.province_id IS '所在省份ID';


--
-- Name: COLUMN wvp_jt_terminal.province_text; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_jt_terminal.province_text IS '所在省份名称';


--
-- Name: COLUMN wvp_jt_terminal.city_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_jt_terminal.city_id IS '所在城市ID';


--
-- Name: COLUMN wvp_jt_terminal.city_text; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_jt_terminal.city_text IS '所在城市名称';


--
-- Name: COLUMN wvp_jt_terminal.maker_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_jt_terminal.maker_id IS '厂商ID';


--
-- Name: COLUMN wvp_jt_terminal.model; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_jt_terminal.model IS '终端型号';


--
-- Name: COLUMN wvp_jt_terminal.plate_color; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_jt_terminal.plate_color IS '车牌颜色';


--
-- Name: COLUMN wvp_jt_terminal.plate_no; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_jt_terminal.plate_no IS '车牌号码';


--
-- Name: COLUMN wvp_jt_terminal.longitude; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_jt_terminal.longitude IS '经度';


--
-- Name: COLUMN wvp_jt_terminal.latitude; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_jt_terminal.latitude IS '纬度';


--
-- Name: COLUMN wvp_jt_terminal.status; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_jt_terminal.status IS '在线状态';


--
-- Name: COLUMN wvp_jt_terminal.register_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_jt_terminal.register_time IS '注册时间';


--
-- Name: COLUMN wvp_jt_terminal.update_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_jt_terminal.update_time IS '更新时间';


--
-- Name: COLUMN wvp_jt_terminal.create_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_jt_terminal.create_time IS '创建时间';


--
-- Name: COLUMN wvp_jt_terminal.geo_coord_sys; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_jt_terminal.geo_coord_sys IS '坐标系';


--
-- Name: COLUMN wvp_jt_terminal.media_server_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_jt_terminal.media_server_id IS '媒体服务器ID';


--
-- Name: COLUMN wvp_jt_terminal.sdp_ip; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_jt_terminal.sdp_ip IS 'SDP IP';


--
-- Name: wvp_jt_terminal_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.wvp_jt_terminal_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.wvp_jt_terminal_id_seq OWNER TO postgres;

--
-- Name: wvp_jt_terminal_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.wvp_jt_terminal_id_seq OWNED BY public.wvp_jt_terminal.id;


--
-- Name: wvp_media_server; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.wvp_media_server (
    id character varying(255) NOT NULL,
    ip character varying(50),
    hook_ip character varying(50),
    sdp_ip character varying(50),
    stream_ip character varying(50),
    http_port integer,
    http_ssl_port integer,
    rtmp_port integer,
    rtmp_ssl_port integer,
    rtp_proxy_port integer,
    rtsp_port integer,
    rtsp_ssl_port integer,
    flv_port integer,
    flv_ssl_port integer,
    mp4_port integer,
    mp4_ssl_port integer,
    ws_flv_port integer,
    ws_flv_ssl_port integer,
    jtt_proxy_port integer,
    auto_config boolean DEFAULT false,
    secret character varying(50),
    type character varying(50) DEFAULT 'zlm'::character varying,
    rtp_enable boolean DEFAULT false,
    rtp_port_range character varying(50),
    send_rtp_port_range character varying(50),
    record_assist_port integer,
    default_server boolean DEFAULT false,
    create_time character varying(50),
    update_time character varying(50),
    hook_alive_interval integer,
    record_path character varying(255),
    record_day integer DEFAULT 7,
    transcode_suffix character varying(255),
    server_id character varying(50)
);


ALTER TABLE public.wvp_media_server OWNER TO postgres;

--
-- Name: TABLE wvp_media_server; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.wvp_media_server IS '媒体服务器（如 ZLM）节点信息';


--
-- Name: COLUMN wvp_media_server.id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_media_server.id IS '媒体服务器ID';


--
-- Name: COLUMN wvp_media_server.ip; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_media_server.ip IS '服务器IP';


--
-- Name: COLUMN wvp_media_server.hook_ip; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_media_server.hook_ip IS 'hook回调IP';


--
-- Name: COLUMN wvp_media_server.sdp_ip; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_media_server.sdp_ip IS 'SDP中使用的IP';


--
-- Name: COLUMN wvp_media_server.stream_ip; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_media_server.stream_ip IS '推流使用的IP';


--
-- Name: COLUMN wvp_media_server.http_port; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_media_server.http_port IS 'HTTP端口';


--
-- Name: COLUMN wvp_media_server.http_ssl_port; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_media_server.http_ssl_port IS 'HTTPS端口';


--
-- Name: COLUMN wvp_media_server.rtmp_port; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_media_server.rtmp_port IS 'RTMP端口';


--
-- Name: COLUMN wvp_media_server.rtmp_ssl_port; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_media_server.rtmp_ssl_port IS 'RTMPS端口';


--
-- Name: COLUMN wvp_media_server.rtp_proxy_port; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_media_server.rtp_proxy_port IS 'RTP代理端口';


--
-- Name: COLUMN wvp_media_server.rtsp_port; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_media_server.rtsp_port IS 'RTSP端口';


--
-- Name: COLUMN wvp_media_server.rtsp_ssl_port; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_media_server.rtsp_ssl_port IS 'RTSPS端口';


--
-- Name: COLUMN wvp_media_server.flv_port; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_media_server.flv_port IS 'FLV端口';


--
-- Name: COLUMN wvp_media_server.flv_ssl_port; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_media_server.flv_ssl_port IS 'FLV HTTPS端口';


--
-- Name: COLUMN wvp_media_server.mp4_port; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_media_server.mp4_port IS 'MP4点播端口';


--
-- Name: COLUMN wvp_media_server.mp4_ssl_port; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_media_server.mp4_ssl_port IS 'MP4 HTTPS端口';


--
-- Name: COLUMN wvp_media_server.ws_flv_port; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_media_server.ws_flv_port IS 'WS-FLV端口';


--
-- Name: COLUMN wvp_media_server.ws_flv_ssl_port; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_media_server.ws_flv_ssl_port IS 'WS-FLV HTTPS端口';


--
-- Name: COLUMN wvp_media_server.jtt_proxy_port; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_media_server.jtt_proxy_port IS 'JT/T代理端口';


--
-- Name: COLUMN wvp_media_server.auto_config; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_media_server.auto_config IS '是否自动配置';


--
-- Name: COLUMN wvp_media_server.secret; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_media_server.secret IS 'ZLM校验密钥';


--
-- Name: COLUMN wvp_media_server.type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_media_server.type IS '节点类型';


--
-- Name: COLUMN wvp_media_server.rtp_enable; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_media_server.rtp_enable IS '是否开启RTP';


--
-- Name: COLUMN wvp_media_server.rtp_port_range; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_media_server.rtp_port_range IS 'RTP端口范围';


--
-- Name: COLUMN wvp_media_server.send_rtp_port_range; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_media_server.send_rtp_port_range IS '发送RTP端口范围';


--
-- Name: COLUMN wvp_media_server.record_assist_port; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_media_server.record_assist_port IS '录像辅助端口';


--
-- Name: COLUMN wvp_media_server.default_server; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_media_server.default_server IS '是否默认节点';


--
-- Name: COLUMN wvp_media_server.create_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_media_server.create_time IS '创建时间';


--
-- Name: COLUMN wvp_media_server.update_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_media_server.update_time IS '更新时间';


--
-- Name: COLUMN wvp_media_server.hook_alive_interval; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_media_server.hook_alive_interval IS 'hook心跳间隔';


--
-- Name: COLUMN wvp_media_server.record_path; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_media_server.record_path IS '录像目录';


--
-- Name: COLUMN wvp_media_server.record_day; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_media_server.record_day IS '录像保留天数';


--
-- Name: COLUMN wvp_media_server.transcode_suffix; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_media_server.transcode_suffix IS '转码指令后缀';


--
-- Name: COLUMN wvp_media_server.server_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_media_server.server_id IS '对应信令服务器ID';


--
-- Name: wvp_platform; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.wvp_platform (
    id integer NOT NULL,
    enable boolean DEFAULT false,
    name character varying(255),
    server_gb_id character varying(50),
    server_gb_domain character varying(50),
    server_ip character varying(50),
    server_port integer,
    device_gb_id character varying(50),
    device_ip character varying(50),
    device_port character varying(50),
    username character varying(255),
    password character varying(50),
    expires character varying(50),
    keep_timeout character varying(50),
    transport character varying(50),
    civil_code character varying(50),
    manufacturer character varying(255),
    model character varying(255),
    address character varying(255),
    character_set character varying(50),
    ptz boolean DEFAULT false,
    rtcp boolean DEFAULT false,
    status boolean DEFAULT false,
    catalog_group integer,
    register_way integer,
    secrecy integer,
    create_time character varying(50),
    update_time character varying(50),
    as_message_channel boolean DEFAULT false,
    catalog_with_platform integer DEFAULT 1,
    catalog_with_group integer DEFAULT 1,
    catalog_with_region integer DEFAULT 1,
    auto_push_channel boolean DEFAULT true,
    send_stream_ip character varying(50),
    server_id character varying(50)
);


ALTER TABLE public.wvp_platform OWNER TO postgres;

--
-- Name: TABLE wvp_platform; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.wvp_platform IS '上级国标平台注册信息';


--
-- Name: COLUMN wvp_platform.id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform.id IS '主键ID';


--
-- Name: COLUMN wvp_platform.enable; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform.enable IS '是否启用该平台注册';


--
-- Name: COLUMN wvp_platform.name; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform.name IS '平台名称';


--
-- Name: COLUMN wvp_platform.server_gb_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform.server_gb_id IS '上级平台国标编码';


--
-- Name: COLUMN wvp_platform.server_gb_domain; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform.server_gb_domain IS '上级平台域编码';


--
-- Name: COLUMN wvp_platform.server_ip; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform.server_ip IS '上级平台IP';


--
-- Name: COLUMN wvp_platform.server_port; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform.server_port IS '上级平台注册端口';


--
-- Name: COLUMN wvp_platform.device_gb_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform.device_gb_id IS '本平台向上注册的国标编码';


--
-- Name: COLUMN wvp_platform.device_ip; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform.device_ip IS '本平台信令IP';


--
-- Name: COLUMN wvp_platform.device_port; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform.device_port IS '本平台信令端口';


--
-- Name: COLUMN wvp_platform.username; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform.username IS '注册用户名';


--
-- Name: COLUMN wvp_platform.password; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform.password IS '注册密码';


--
-- Name: COLUMN wvp_platform.expires; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform.expires IS '注册有效期';


--
-- Name: COLUMN wvp_platform.keep_timeout; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform.keep_timeout IS '心跳超时时间';


--
-- Name: COLUMN wvp_platform.transport; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform.transport IS '传输协议（UDP/TCP）';


--
-- Name: COLUMN wvp_platform.civil_code; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform.civil_code IS '行政区划代码';


--
-- Name: COLUMN wvp_platform.manufacturer; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform.manufacturer IS '厂商';


--
-- Name: COLUMN wvp_platform.model; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform.model IS '型号';


--
-- Name: COLUMN wvp_platform.address; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform.address IS '地址';


--
-- Name: COLUMN wvp_platform.character_set; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform.character_set IS '字符集';


--
-- Name: COLUMN wvp_platform.ptz; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform.ptz IS '是否支持PTZ';


--
-- Name: COLUMN wvp_platform.rtcp; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform.rtcp IS '是否开启RTCP';


--
-- Name: COLUMN wvp_platform.status; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform.status IS '注册状态';


--
-- Name: COLUMN wvp_platform.catalog_group; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform.catalog_group IS '目录分组方式';


--
-- Name: COLUMN wvp_platform.register_way; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform.register_way IS '注册方式';


--
-- Name: COLUMN wvp_platform.secrecy; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform.secrecy IS '保密级别';


--
-- Name: COLUMN wvp_platform.create_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform.create_time IS '创建时间';


--
-- Name: COLUMN wvp_platform.update_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform.update_time IS '更新时间';


--
-- Name: COLUMN wvp_platform.as_message_channel; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform.as_message_channel IS '是否作为消息通道';


--
-- Name: COLUMN wvp_platform.catalog_with_platform; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform.catalog_with_platform IS '是否推送平台目录';


--
-- Name: COLUMN wvp_platform.catalog_with_group; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform.catalog_with_group IS '是否推送分组目录';


--
-- Name: COLUMN wvp_platform.catalog_with_region; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform.catalog_with_region IS '是否推送区域目录';


--
-- Name: COLUMN wvp_platform.auto_push_channel; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform.auto_push_channel IS '是否自动推送通道';


--
-- Name: COLUMN wvp_platform.send_stream_ip; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform.send_stream_ip IS '推流时使用的IP';


--
-- Name: COLUMN wvp_platform.server_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform.server_id IS '对应信令服务器ID';


--
-- Name: wvp_platform_channel; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.wvp_platform_channel (
    id integer NOT NULL,
    platform_id integer,
    device_channel_id integer,
    custom_device_id character varying(50),
    custom_name character varying(255),
    custom_manufacturer character varying(50),
    custom_model character varying(50),
    custom_owner character varying(50),
    custom_civil_code character varying(50),
    custom_block character varying(50),
    custom_address character varying(50),
    custom_parental integer,
    custom_parent_id character varying(50),
    custom_safety_way integer,
    custom_register_way integer,
    custom_cert_num character varying(50),
    custom_certifiable integer,
    custom_err_code integer,
    custom_end_time character varying(50),
    custom_secrecy integer,
    custom_ip_address character varying(50),
    custom_port integer,
    custom_password character varying(255),
    custom_status character varying(50),
    custom_longitude double precision,
    custom_latitude double precision,
    custom_ptz_type integer,
    custom_position_type integer,
    custom_room_type integer,
    custom_use_type integer,
    custom_supply_light_type integer,
    custom_direction_type integer,
    custom_resolution character varying(255),
    custom_business_group_id character varying(255),
    custom_download_speed character varying(255),
    custom_svc_space_support_mod integer,
    custom_svc_time_support_mode integer
);


ALTER TABLE public.wvp_platform_channel OWNER TO postgres;

--
-- Name: TABLE wvp_platform_channel; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.wvp_platform_channel IS '国标平台下发的通道映射关系';


--
-- Name: COLUMN wvp_platform_channel.id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform_channel.id IS '主键ID';


--
-- Name: COLUMN wvp_platform_channel.platform_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform_channel.platform_id IS '平台ID';


--
-- Name: COLUMN wvp_platform_channel.device_channel_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform_channel.device_channel_id IS '本地通道表主键';


--
-- Name: COLUMN wvp_platform_channel.custom_device_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform_channel.custom_device_id IS '自定义国标编码';


--
-- Name: COLUMN wvp_platform_channel.custom_name; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform_channel.custom_name IS '自定义名称';


--
-- Name: COLUMN wvp_platform_channel.custom_manufacturer; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform_channel.custom_manufacturer IS '自定义厂商';


--
-- Name: COLUMN wvp_platform_channel.custom_model; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform_channel.custom_model IS '自定义型号';


--
-- Name: COLUMN wvp_platform_channel.custom_owner; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform_channel.custom_owner IS '自定义归属';


--
-- Name: COLUMN wvp_platform_channel.custom_civil_code; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform_channel.custom_civil_code IS '自定义行政区划';


--
-- Name: COLUMN wvp_platform_channel.custom_block; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform_channel.custom_block IS '自定义区域';


--
-- Name: COLUMN wvp_platform_channel.custom_address; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform_channel.custom_address IS '自定义地址';


--
-- Name: COLUMN wvp_platform_channel.custom_parental; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform_channel.custom_parental IS '自定义父/子标识';


--
-- Name: COLUMN wvp_platform_channel.custom_parent_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform_channel.custom_parent_id IS '自定义父节点';


--
-- Name: COLUMN wvp_platform_channel.custom_safety_way; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform_channel.custom_safety_way IS '自定义安全防范';


--
-- Name: COLUMN wvp_platform_channel.custom_register_way; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform_channel.custom_register_way IS '自定义注册方式';


--
-- Name: COLUMN wvp_platform_channel.custom_cert_num; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform_channel.custom_cert_num IS '自定义证书编号';


--
-- Name: COLUMN wvp_platform_channel.custom_certifiable; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform_channel.custom_certifiable IS '自定义可认证标志';


--
-- Name: COLUMN wvp_platform_channel.custom_err_code; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform_channel.custom_err_code IS '自定义错误码';


--
-- Name: COLUMN wvp_platform_channel.custom_end_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform_channel.custom_end_time IS '自定义截止时间';


--
-- Name: COLUMN wvp_platform_channel.custom_secrecy; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform_channel.custom_secrecy IS '自定义保密级别';


--
-- Name: COLUMN wvp_platform_channel.custom_ip_address; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform_channel.custom_ip_address IS '自定义IP';


--
-- Name: COLUMN wvp_platform_channel.custom_port; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform_channel.custom_port IS '自定义端口';


--
-- Name: COLUMN wvp_platform_channel.custom_password; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform_channel.custom_password IS '自定义密码';


--
-- Name: COLUMN wvp_platform_channel.custom_status; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform_channel.custom_status IS '自定义状态';


--
-- Name: COLUMN wvp_platform_channel.custom_longitude; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform_channel.custom_longitude IS '自定义经度';


--
-- Name: COLUMN wvp_platform_channel.custom_latitude; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform_channel.custom_latitude IS '自定义纬度';


--
-- Name: COLUMN wvp_platform_channel.custom_ptz_type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform_channel.custom_ptz_type IS '自定义云台类型';


--
-- Name: COLUMN wvp_platform_channel.custom_position_type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform_channel.custom_position_type IS '自定义点位类型';


--
-- Name: COLUMN wvp_platform_channel.custom_room_type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform_channel.custom_room_type IS '自定义房间类型';


--
-- Name: COLUMN wvp_platform_channel.custom_use_type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform_channel.custom_use_type IS '自定义用途';


--
-- Name: COLUMN wvp_platform_channel.custom_supply_light_type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform_channel.custom_supply_light_type IS '自定义补光';


--
-- Name: COLUMN wvp_platform_channel.custom_direction_type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform_channel.custom_direction_type IS '自定义朝向';


--
-- Name: COLUMN wvp_platform_channel.custom_resolution; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform_channel.custom_resolution IS '自定义分辨率';


--
-- Name: COLUMN wvp_platform_channel.custom_business_group_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform_channel.custom_business_group_id IS '自定义业务分组';


--
-- Name: COLUMN wvp_platform_channel.custom_download_speed; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform_channel.custom_download_speed IS '自定义码流速率';


--
-- Name: COLUMN wvp_platform_channel.custom_svc_space_support_mod; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform_channel.custom_svc_space_support_mod IS '自定义空域SVC';


--
-- Name: COLUMN wvp_platform_channel.custom_svc_time_support_mode; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform_channel.custom_svc_time_support_mode IS '自定义时域SVC';


--
-- Name: wvp_platform_channel_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.wvp_platform_channel_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.wvp_platform_channel_id_seq OWNER TO postgres;

--
-- Name: wvp_platform_channel_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.wvp_platform_channel_id_seq OWNED BY public.wvp_platform_channel.id;


--
-- Name: wvp_platform_group; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.wvp_platform_group (
    id integer NOT NULL,
    platform_id integer,
    group_id integer
);


ALTER TABLE public.wvp_platform_group OWNER TO postgres;

--
-- Name: TABLE wvp_platform_group; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.wvp_platform_group IS '平台与分组（行政区划/组织）关系';


--
-- Name: COLUMN wvp_platform_group.id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform_group.id IS '主键ID';


--
-- Name: COLUMN wvp_platform_group.platform_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform_group.platform_id IS '平台ID';


--
-- Name: COLUMN wvp_platform_group.group_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform_group.group_id IS '分组ID';


--
-- Name: wvp_platform_group_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.wvp_platform_group_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.wvp_platform_group_id_seq OWNER TO postgres;

--
-- Name: wvp_platform_group_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.wvp_platform_group_id_seq OWNED BY public.wvp_platform_group.id;


--
-- Name: wvp_platform_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.wvp_platform_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.wvp_platform_id_seq OWNER TO postgres;

--
-- Name: wvp_platform_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.wvp_platform_id_seq OWNED BY public.wvp_platform.id;


--
-- Name: wvp_platform_region; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.wvp_platform_region (
    id integer NOT NULL,
    platform_id integer,
    region_id integer
);


ALTER TABLE public.wvp_platform_region OWNER TO postgres;

--
-- Name: TABLE wvp_platform_region; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.wvp_platform_region IS '平台与区域关系';


--
-- Name: COLUMN wvp_platform_region.id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform_region.id IS '主键ID';


--
-- Name: COLUMN wvp_platform_region.platform_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform_region.platform_id IS '平台ID';


--
-- Name: COLUMN wvp_platform_region.region_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_platform_region.region_id IS '区域ID';


--
-- Name: wvp_platform_region_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.wvp_platform_region_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.wvp_platform_region_id_seq OWNER TO postgres;

--
-- Name: wvp_platform_region_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.wvp_platform_region_id_seq OWNED BY public.wvp_platform_region.id;


--
-- Name: wvp_record_plan; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.wvp_record_plan (
    id integer NOT NULL,
    snap boolean DEFAULT false,
    name character varying(255) NOT NULL,
    create_time character varying(50),
    update_time character varying(50)
);


ALTER TABLE public.wvp_record_plan OWNER TO postgres;

--
-- Name: TABLE wvp_record_plan; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.wvp_record_plan IS '录像计划基础信息';


--
-- Name: COLUMN wvp_record_plan.id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_record_plan.id IS '主键ID';


--
-- Name: COLUMN wvp_record_plan.snap; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_record_plan.snap IS '是否抓图计划';


--
-- Name: COLUMN wvp_record_plan.name; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_record_plan.name IS '计划名称';


--
-- Name: COLUMN wvp_record_plan.create_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_record_plan.create_time IS '创建时间';


--
-- Name: COLUMN wvp_record_plan.update_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_record_plan.update_time IS '更新时间';


--
-- Name: wvp_record_plan_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.wvp_record_plan_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.wvp_record_plan_id_seq OWNER TO postgres;

--
-- Name: wvp_record_plan_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.wvp_record_plan_id_seq OWNED BY public.wvp_record_plan.id;


--
-- Name: wvp_record_plan_item; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.wvp_record_plan_item (
    id integer NOT NULL,
    start integer,
    stop integer,
    week_day integer,
    plan_id integer,
    create_time character varying(50),
    update_time character varying(50)
);


ALTER TABLE public.wvp_record_plan_item OWNER TO postgres;

--
-- Name: TABLE wvp_record_plan_item; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.wvp_record_plan_item IS '录像计划条目表';


--
-- Name: COLUMN wvp_record_plan_item.id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_record_plan_item.id IS '主键ID';


--
-- Name: COLUMN wvp_record_plan_item.start; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_record_plan_item.start IS '开始时间（分钟）';


--
-- Name: COLUMN wvp_record_plan_item.stop; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_record_plan_item.stop IS '结束时间（分钟）';


--
-- Name: COLUMN wvp_record_plan_item.week_day; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_record_plan_item.week_day IS '星期（0-6）';


--
-- Name: COLUMN wvp_record_plan_item.plan_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_record_plan_item.plan_id IS '所属录像计划ID';


--
-- Name: COLUMN wvp_record_plan_item.create_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_record_plan_item.create_time IS '创建时间';


--
-- Name: COLUMN wvp_record_plan_item.update_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_record_plan_item.update_time IS '更新时间';


--
-- Name: wvp_record_plan_item_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.wvp_record_plan_item_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.wvp_record_plan_item_id_seq OWNER TO postgres;

--
-- Name: wvp_record_plan_item_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.wvp_record_plan_item_id_seq OWNED BY public.wvp_record_plan_item.id;


--
-- Name: wvp_stream_proxy; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.wvp_stream_proxy (
    id integer NOT NULL,
    type character varying(50),
    app character varying(255),
    stream character varying(255),
    src_url character varying(255),
    timeout integer,
    ffmpeg_cmd_key character varying(255),
    rtsp_type character varying(50),
    media_server_id character varying(50),
    enable_audio boolean DEFAULT false,
    enable_mp4 boolean DEFAULT false,
    pulling boolean DEFAULT false,
    enable boolean DEFAULT false,
    create_time character varying(50),
    name character varying(255),
    update_time character varying(50),
    stream_key character varying(255),
    server_id character varying(50),
    enable_disable_none_reader boolean DEFAULT false,
    relates_media_server_id character varying(50)
);


ALTER TABLE public.wvp_stream_proxy OWNER TO postgres;

--
-- Name: TABLE wvp_stream_proxy; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.wvp_stream_proxy IS '拉流代理/转推配置';


--
-- Name: COLUMN wvp_stream_proxy.id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_stream_proxy.id IS '主键ID';


--
-- Name: COLUMN wvp_stream_proxy.type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_stream_proxy.type IS '代理类型（拉流/推流）';


--
-- Name: COLUMN wvp_stream_proxy.app; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_stream_proxy.app IS '应用名';


--
-- Name: COLUMN wvp_stream_proxy.stream; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_stream_proxy.stream IS '流ID';


--
-- Name: COLUMN wvp_stream_proxy.src_url; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_stream_proxy.src_url IS '源地址';


--
-- Name: COLUMN wvp_stream_proxy.timeout; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_stream_proxy.timeout IS '拉流超时时间';


--
-- Name: COLUMN wvp_stream_proxy.ffmpeg_cmd_key; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_stream_proxy.ffmpeg_cmd_key IS 'FFmpeg命令模板键';


--
-- Name: COLUMN wvp_stream_proxy.rtsp_type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_stream_proxy.rtsp_type IS 'RTSP拉流方式';


--
-- Name: COLUMN wvp_stream_proxy.media_server_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_stream_proxy.media_server_id IS '指定媒体服务器ID';


--
-- Name: COLUMN wvp_stream_proxy.enable_audio; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_stream_proxy.enable_audio IS '是否启用音频';


--
-- Name: COLUMN wvp_stream_proxy.enable_mp4; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_stream_proxy.enable_mp4 IS '是否录制MP4';


--
-- Name: COLUMN wvp_stream_proxy.pulling; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_stream_proxy.pulling IS '当前是否在拉流';


--
-- Name: COLUMN wvp_stream_proxy.enable; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_stream_proxy.enable IS '是否启用该代理';


--
-- Name: COLUMN wvp_stream_proxy.create_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_stream_proxy.create_time IS '创建时间';


--
-- Name: COLUMN wvp_stream_proxy.name; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_stream_proxy.name IS '代理名称';


--
-- Name: COLUMN wvp_stream_proxy.update_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_stream_proxy.update_time IS '更新时间';


--
-- Name: COLUMN wvp_stream_proxy.stream_key; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_stream_proxy.stream_key IS '唯一流标识';


--
-- Name: COLUMN wvp_stream_proxy.server_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_stream_proxy.server_id IS '信令服务器ID';


--
-- Name: COLUMN wvp_stream_proxy.enable_disable_none_reader; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_stream_proxy.enable_disable_none_reader IS '是否无人观看时自动停流';


--
-- Name: COLUMN wvp_stream_proxy.relates_media_server_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_stream_proxy.relates_media_server_id IS '关联的媒体服务器ID';


--
-- Name: wvp_stream_proxy_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.wvp_stream_proxy_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.wvp_stream_proxy_id_seq OWNER TO postgres;

--
-- Name: wvp_stream_proxy_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.wvp_stream_proxy_id_seq OWNED BY public.wvp_stream_proxy.id;


--
-- Name: wvp_stream_push; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.wvp_stream_push (
    id integer NOT NULL,
    app character varying(255),
    stream character varying(255),
    create_time character varying(50),
    media_server_id character varying(50),
    server_id character varying(50),
    push_time character varying(50),
    status boolean DEFAULT false,
    update_time character varying(50),
    pushing boolean DEFAULT false,
    self boolean DEFAULT false,
    start_offline_push boolean DEFAULT true
);


ALTER TABLE public.wvp_stream_push OWNER TO postgres;

--
-- Name: TABLE wvp_stream_push; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.wvp_stream_push IS '推流会话记录';


--
-- Name: COLUMN wvp_stream_push.id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_stream_push.id IS '主键ID';


--
-- Name: COLUMN wvp_stream_push.app; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_stream_push.app IS '应用名';


--
-- Name: COLUMN wvp_stream_push.stream; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_stream_push.stream IS '流ID';


--
-- Name: COLUMN wvp_stream_push.create_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_stream_push.create_time IS '创建时间';


--
-- Name: COLUMN wvp_stream_push.media_server_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_stream_push.media_server_id IS '推流所在媒体服务器';


--
-- Name: COLUMN wvp_stream_push.server_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_stream_push.server_id IS '信令服务器ID';


--
-- Name: COLUMN wvp_stream_push.push_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_stream_push.push_time IS '推流开始时间';


--
-- Name: COLUMN wvp_stream_push.status; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_stream_push.status IS '推流状态';


--
-- Name: COLUMN wvp_stream_push.update_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_stream_push.update_time IS '更新时间';


--
-- Name: COLUMN wvp_stream_push.pushing; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_stream_push.pushing IS '是否正在推流';


--
-- Name: COLUMN wvp_stream_push.self; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_stream_push.self IS '是否本地发起';


--
-- Name: COLUMN wvp_stream_push.start_offline_push; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_stream_push.start_offline_push IS '是否离线后自动重推';


--
-- Name: wvp_stream_push_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.wvp_stream_push_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.wvp_stream_push_id_seq OWNER TO postgres;

--
-- Name: wvp_stream_push_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.wvp_stream_push_id_seq OWNED BY public.wvp_stream_push.id;


--
-- Name: wvp_user; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.wvp_user (
    id integer NOT NULL,
    username character varying(255),
    password character varying(255),
    role_id integer,
    create_time character varying(50),
    update_time character varying(50),
    push_key character varying(50)
);


ALTER TABLE public.wvp_user OWNER TO postgres;

--
-- Name: TABLE wvp_user; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.wvp_user IS '平台用户信息';


--
-- Name: COLUMN wvp_user.id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_user.id IS '主键ID';


--
-- Name: COLUMN wvp_user.username; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_user.username IS '用户名';


--
-- Name: COLUMN wvp_user.password; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_user.password IS '密码（MD5）';


--
-- Name: COLUMN wvp_user.role_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_user.role_id IS '角色ID';


--
-- Name: COLUMN wvp_user.create_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_user.create_time IS '创建时间';


--
-- Name: COLUMN wvp_user.update_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_user.update_time IS '更新时间';


--
-- Name: COLUMN wvp_user.push_key; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_user.push_key IS '推送密钥';


--
-- Name: wvp_user_api_key; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.wvp_user_api_key (
    id integer NOT NULL,
    user_id bigint,
    app character varying(255),
    api_key text,
    expired_at bigint,
    remark character varying(255),
    enable boolean DEFAULT true,
    create_time character varying(50),
    update_time character varying(50)
);


ALTER TABLE public.wvp_user_api_key OWNER TO postgres;

--
-- Name: COLUMN wvp_user_api_key.id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_user_api_key.id IS '主键ID';


--
-- Name: COLUMN wvp_user_api_key.user_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_user_api_key.user_id IS '关联用户ID';


--
-- Name: COLUMN wvp_user_api_key.app; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_user_api_key.app IS '应用标识';


--
-- Name: COLUMN wvp_user_api_key.api_key; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_user_api_key.api_key IS 'API Key';


--
-- Name: COLUMN wvp_user_api_key.expired_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_user_api_key.expired_at IS '过期时间戳';


--
-- Name: COLUMN wvp_user_api_key.remark; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_user_api_key.remark IS '备注';


--
-- Name: COLUMN wvp_user_api_key.enable; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_user_api_key.enable IS '是否启用';


--
-- Name: COLUMN wvp_user_api_key.create_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_user_api_key.create_time IS '创建时间';


--
-- Name: COLUMN wvp_user_api_key.update_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_user_api_key.update_time IS '更新时间';


--
-- Name: wvp_user_api_key_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.wvp_user_api_key_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.wvp_user_api_key_id_seq OWNER TO postgres;

--
-- Name: wvp_user_api_key_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.wvp_user_api_key_id_seq OWNED BY public.wvp_user_api_key.id;


--
-- Name: wvp_user_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.wvp_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.wvp_user_id_seq OWNER TO postgres;

--
-- Name: wvp_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.wvp_user_id_seq OWNED BY public.wvp_user.id;


--
-- Name: wvp_user_role; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.wvp_user_role (
    id integer NOT NULL,
    name character varying(50),
    authority character varying(50),
    create_time character varying(50),
    update_time character varying(50)
);


ALTER TABLE public.wvp_user_role OWNER TO postgres;

--
-- Name: TABLE wvp_user_role; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.wvp_user_role IS '用户角色信息';


--
-- Name: COLUMN wvp_user_role.id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_user_role.id IS '主键ID';


--
-- Name: COLUMN wvp_user_role.name; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_user_role.name IS '角色名称';


--
-- Name: COLUMN wvp_user_role.authority; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_user_role.authority IS '权限标识';


--
-- Name: COLUMN wvp_user_role.create_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_user_role.create_time IS '创建时间';


--
-- Name: COLUMN wvp_user_role.update_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.wvp_user_role.update_time IS '更新时间';


--
-- Name: wvp_user_role_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.wvp_user_role_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.wvp_user_role_id_seq OWNER TO postgres;

--
-- Name: wvp_user_role_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.wvp_user_role_id_seq OWNED BY public.wvp_user_role.id;


--
-- Name: wvp_cloud_record id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_cloud_record ALTER COLUMN id SET DEFAULT nextval('public.wvp_cloud_record_id_seq'::regclass);


--
-- Name: wvp_common_group id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_common_group ALTER COLUMN id SET DEFAULT nextval('public.wvp_common_group_id_seq'::regclass);


--
-- Name: wvp_common_region id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_common_region ALTER COLUMN id SET DEFAULT nextval('public.wvp_common_region_id_seq'::regclass);


--
-- Name: wvp_device id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_device ALTER COLUMN id SET DEFAULT nextval('public.wvp_device_id_seq'::regclass);


--
-- Name: wvp_device_alarm id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_device_alarm ALTER COLUMN id SET DEFAULT nextval('public.wvp_device_alarm_id_seq'::regclass);


--
-- Name: wvp_device_channel id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_device_channel ALTER COLUMN id SET DEFAULT nextval('public.wvp_device_channel_id_seq'::regclass);


--
-- Name: wvp_device_mobile_position id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_device_mobile_position ALTER COLUMN id SET DEFAULT nextval('public.wvp_device_mobile_position_id_seq'::regclass);


--
-- Name: wvp_jt_channel id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_jt_channel ALTER COLUMN id SET DEFAULT nextval('public.wvp_jt_channel_id_seq'::regclass);


--
-- Name: wvp_jt_terminal id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_jt_terminal ALTER COLUMN id SET DEFAULT nextval('public.wvp_jt_terminal_id_seq'::regclass);


--
-- Name: wvp_platform id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_platform ALTER COLUMN id SET DEFAULT nextval('public.wvp_platform_id_seq'::regclass);


--
-- Name: wvp_platform_channel id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_platform_channel ALTER COLUMN id SET DEFAULT nextval('public.wvp_platform_channel_id_seq'::regclass);


--
-- Name: wvp_platform_group id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_platform_group ALTER COLUMN id SET DEFAULT nextval('public.wvp_platform_group_id_seq'::regclass);


--
-- Name: wvp_platform_region id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_platform_region ALTER COLUMN id SET DEFAULT nextval('public.wvp_platform_region_id_seq'::regclass);


--
-- Name: wvp_record_plan id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_record_plan ALTER COLUMN id SET DEFAULT nextval('public.wvp_record_plan_id_seq'::regclass);


--
-- Name: wvp_record_plan_item id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_record_plan_item ALTER COLUMN id SET DEFAULT nextval('public.wvp_record_plan_item_id_seq'::regclass);


--
-- Name: wvp_stream_proxy id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_stream_proxy ALTER COLUMN id SET DEFAULT nextval('public.wvp_stream_proxy_id_seq'::regclass);


--
-- Name: wvp_stream_push id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_stream_push ALTER COLUMN id SET DEFAULT nextval('public.wvp_stream_push_id_seq'::regclass);


--
-- Name: wvp_user id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_user ALTER COLUMN id SET DEFAULT nextval('public.wvp_user_id_seq'::regclass);


--
-- Name: wvp_user_api_key id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_user_api_key ALTER COLUMN id SET DEFAULT nextval('public.wvp_user_api_key_id_seq'::regclass);


--
-- Name: wvp_user_role id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_user_role ALTER COLUMN id SET DEFAULT nextval('public.wvp_user_role_id_seq'::regclass);


--
-- Data for Name: wvp_cloud_record; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.wvp_cloud_record (id, app, stream, call_id, start_time, end_time, media_server_id, server_id, file_name, folder, file_path, collect, file_size, time_len) FROM stdin;
\.


--
-- Data for Name: wvp_common_group; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.wvp_common_group (id, device_id, name, parent_id, parent_device_id, business_group, create_time, update_time, civil_code, alias) FROM stdin;
\.


--
-- Data for Name: wvp_common_region; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.wvp_common_region (id, device_id, name, parent_id, parent_device_id, create_time, update_time) FROM stdin;
\.


--
-- Data for Name: wvp_device; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.wvp_device (id, device_id, name, manufacturer, model, firmware, transport, stream_mode, on_line, register_time, keepalive_time, ip, create_time, update_time, port, expires, subscribe_cycle_for_catalog, subscribe_cycle_for_mobile_position, mobile_position_submission_interval, subscribe_cycle_for_alarm, host_address, charset, ssrc_check, geo_coord_sys, media_server_id, custom_name, sdp_ip, local_ip, password, as_message_channel, heart_beat_interval, heart_beat_count, position_capability, broadcast_push_after_ack, server_id) FROM stdin;
\.


--
-- Data for Name: wvp_device_alarm; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.wvp_device_alarm (id, device_id, channel_id, alarm_priority, alarm_method, alarm_time, alarm_description, longitude, latitude, alarm_type, create_time) FROM stdin;
\.


--
-- Data for Name: wvp_device_channel; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.wvp_device_channel (id, device_id, name, manufacturer, model, owner, civil_code, block, address, parental, parent_id, safety_way, register_way, cert_num, certifiable, err_code, end_time, secrecy, ip_address, port, password, status, longitude, latitude, ptz_type, position_type, room_type, use_type, supply_light_type, direction_type, resolution, business_group_id, download_speed, svc_space_support_mod, svc_time_support_mode, create_time, update_time, sub_count, stream_id, has_audio, gps_time, stream_identification, channel_type, map_level, gb_device_id, gb_name, gb_manufacturer, gb_model, gb_owner, gb_civil_code, gb_block, gb_address, gb_parental, gb_parent_id, gb_safety_way, gb_register_way, gb_cert_num, gb_certifiable, gb_err_code, gb_end_time, gb_secrecy, gb_ip_address, gb_port, gb_password, gb_status, gb_longitude, gb_latitude, gb_business_group_id, gb_ptz_type, gb_position_type, gb_room_type, gb_use_type, gb_supply_light_type, gb_direction_type, gb_resolution, gb_download_speed, gb_svc_space_support_mod, gb_svc_time_support_mode, record_plan_id, data_type, data_device_id, gps_speed, gps_altitude, gps_direction, enable_broadcast) FROM stdin;
\.


--
-- Data for Name: wvp_device_mobile_position; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.wvp_device_mobile_position (id, device_id, channel_id, device_name, "time", longitude, latitude, altitude, speed, direction, report_source, create_time) FROM stdin;
\.


--
-- Data for Name: wvp_jt_channel; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.wvp_jt_channel (id, terminal_db_id, channel_id, has_audio, name, update_time, create_time) FROM stdin;
\.


--
-- Data for Name: wvp_jt_terminal; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.wvp_jt_terminal (id, phone_number, terminal_id, province_id, province_text, city_id, city_text, maker_id, model, plate_color, plate_no, longitude, latitude, status, register_time, update_time, create_time, geo_coord_sys, media_server_id, sdp_ip) FROM stdin;
\.


--
-- Data for Name: wvp_media_server; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.wvp_media_server (id, ip, hook_ip, sdp_ip, stream_ip, http_port, http_ssl_port, rtmp_port, rtmp_ssl_port, rtp_proxy_port, rtsp_port, rtsp_ssl_port, flv_port, flv_ssl_port, mp4_port, mp4_ssl_port, ws_flv_port, ws_flv_ssl_port, jtt_proxy_port, auto_config, secret, type, rtp_enable, rtp_port_range, send_rtp_port_range, record_assist_port, default_server, create_time, update_time, hook_alive_interval, record_path, record_day, transcode_suffix, server_id) FROM stdin;
\.


--
-- Data for Name: wvp_platform; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.wvp_platform (id, enable, name, server_gb_id, server_gb_domain, server_ip, server_port, device_gb_id, device_ip, device_port, username, password, expires, keep_timeout, transport, civil_code, manufacturer, model, address, character_set, ptz, rtcp, status, catalog_group, register_way, secrecy, create_time, update_time, as_message_channel, catalog_with_platform, catalog_with_group, catalog_with_region, auto_push_channel, send_stream_ip, server_id) FROM stdin;
\.


--
-- Data for Name: wvp_platform_channel; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.wvp_platform_channel (id, platform_id, device_channel_id, custom_device_id, custom_name, custom_manufacturer, custom_model, custom_owner, custom_civil_code, custom_block, custom_address, custom_parental, custom_parent_id, custom_safety_way, custom_register_way, custom_cert_num, custom_certifiable, custom_err_code, custom_end_time, custom_secrecy, custom_ip_address, custom_port, custom_password, custom_status, custom_longitude, custom_latitude, custom_ptz_type, custom_position_type, custom_room_type, custom_use_type, custom_supply_light_type, custom_direction_type, custom_resolution, custom_business_group_id, custom_download_speed, custom_svc_space_support_mod, custom_svc_time_support_mode) FROM stdin;
\.


--
-- Data for Name: wvp_platform_group; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.wvp_platform_group (id, platform_id, group_id) FROM stdin;
\.


--
-- Data for Name: wvp_platform_region; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.wvp_platform_region (id, platform_id, region_id) FROM stdin;
\.


--
-- Data for Name: wvp_record_plan; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.wvp_record_plan (id, snap, name, create_time, update_time) FROM stdin;
\.


--
-- Data for Name: wvp_record_plan_item; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.wvp_record_plan_item (id, start, stop, week_day, plan_id, create_time, update_time) FROM stdin;
\.


--
-- Data for Name: wvp_stream_proxy; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.wvp_stream_proxy (id, type, app, stream, src_url, timeout, ffmpeg_cmd_key, rtsp_type, media_server_id, enable_audio, enable_mp4, pulling, enable, create_time, name, update_time, stream_key, server_id, enable_disable_none_reader, relates_media_server_id) FROM stdin;
\.


--
-- Data for Name: wvp_stream_push; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.wvp_stream_push (id, app, stream, create_time, media_server_id, server_id, push_time, status, update_time, pushing, self, start_offline_push) FROM stdin;
\.


--
-- Data for Name: wvp_user; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.wvp_user (id, username, password, role_id, create_time, update_time, push_key) FROM stdin;
1	admin	21232f297a57a5a743894a0e4a801fc3	1	2021-04-13 14:14:57	2021-04-13 14:14:57	3e80d1762a324d5b0ff636e0bd16f1e3
\.


--
-- Data for Name: wvp_user_api_key; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.wvp_user_api_key (id, user_id, app, api_key, expired_at, remark, enable, create_time, update_time) FROM stdin;
\.


--
-- Data for Name: wvp_user_role; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.wvp_user_role (id, name, authority, create_time, update_time) FROM stdin;
1	admin	0	2021-04-13 14:14:57	2021-04-13 14:14:57
\.


--
-- Name: wvp_cloud_record_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.wvp_cloud_record_id_seq', 1, false);


--
-- Name: wvp_common_group_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.wvp_common_group_id_seq', 1, false);


--
-- Name: wvp_common_region_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.wvp_common_region_id_seq', 1, false);


--
-- Name: wvp_device_alarm_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.wvp_device_alarm_id_seq', 1, false);


--
-- Name: wvp_device_channel_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.wvp_device_channel_id_seq', 1, false);


--
-- Name: wvp_device_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.wvp_device_id_seq', 1, false);


--
-- Name: wvp_device_mobile_position_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.wvp_device_mobile_position_id_seq', 1, false);


--
-- Name: wvp_jt_channel_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.wvp_jt_channel_id_seq', 1, false);


--
-- Name: wvp_jt_terminal_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.wvp_jt_terminal_id_seq', 1, false);


--
-- Name: wvp_platform_channel_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.wvp_platform_channel_id_seq', 1, false);


--
-- Name: wvp_platform_group_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.wvp_platform_group_id_seq', 1, false);


--
-- Name: wvp_platform_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.wvp_platform_id_seq', 1, false);


--
-- Name: wvp_platform_region_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.wvp_platform_region_id_seq', 1, false);


--
-- Name: wvp_record_plan_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.wvp_record_plan_id_seq', 1, false);


--
-- Name: wvp_record_plan_item_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.wvp_record_plan_item_id_seq', 1, false);


--
-- Name: wvp_stream_proxy_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.wvp_stream_proxy_id_seq', 1, false);


--
-- Name: wvp_stream_push_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.wvp_stream_push_id_seq', 1, false);


--
-- Name: wvp_user_api_key_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.wvp_user_api_key_id_seq', 1, false);


--
-- Name: wvp_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.wvp_user_id_seq', 1, false);


--
-- Name: wvp_user_role_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.wvp_user_role_id_seq', 1, false);


--
-- Name: wvp_common_group uk_common_group_device_platform; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_common_group
    ADD CONSTRAINT uk_common_group_device_platform UNIQUE (device_id);


--
-- Name: wvp_common_region uk_common_region_device_id; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_common_region
    ADD CONSTRAINT uk_common_region_device_id UNIQUE (device_id);


--
-- Name: wvp_device uk_device_device; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_device
    ADD CONSTRAINT uk_device_device UNIQUE (device_id);


--
-- Name: wvp_jt_channel uk_jt_channel_id_device_id; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_jt_channel
    ADD CONSTRAINT uk_jt_channel_id_device_id UNIQUE (terminal_db_id, channel_id);


--
-- Name: wvp_jt_terminal uk_jt_device_id_device_id; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_jt_terminal
    ADD CONSTRAINT uk_jt_device_id_device_id UNIQUE (id, phone_number);


--
-- Name: wvp_media_server uk_media_server_unique_ip_http_port; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_media_server
    ADD CONSTRAINT uk_media_server_unique_ip_http_port UNIQUE (ip, http_port, server_id);


--
-- Name: wvp_platform_channel uk_platform_gb_channel_device_id; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_platform_channel
    ADD CONSTRAINT uk_platform_gb_channel_device_id UNIQUE (custom_device_id);


--
-- Name: wvp_platform_channel uk_platform_gb_channel_platform_id_catalog_id_device_channel_id; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_platform_channel
    ADD CONSTRAINT uk_platform_gb_channel_platform_id_catalog_id_device_channel_id UNIQUE (platform_id, device_channel_id);


--
-- Name: wvp_platform uk_platform_unique_server_gb_id; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_platform
    ADD CONSTRAINT uk_platform_unique_server_gb_id UNIQUE (server_gb_id);


--
-- Name: wvp_stream_proxy uk_stream_proxy_app_stream; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_stream_proxy
    ADD CONSTRAINT uk_stream_proxy_app_stream UNIQUE (app, stream);


--
-- Name: wvp_stream_push uk_stream_push_app_stream; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_stream_push
    ADD CONSTRAINT uk_stream_push_app_stream UNIQUE (app, stream);


--
-- Name: wvp_user uk_user_username; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_user
    ADD CONSTRAINT uk_user_username UNIQUE (username);


--
-- Name: wvp_platform_group uk_wvp_platform_group_platform_id_group_id; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_platform_group
    ADD CONSTRAINT uk_wvp_platform_group_platform_id_group_id UNIQUE (platform_id, group_id);


--
-- Name: wvp_platform_region uk_wvp_platform_region_platform_id_group_id; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_platform_region
    ADD CONSTRAINT uk_wvp_platform_region_platform_id_group_id UNIQUE (platform_id, region_id);


--
-- Name: wvp_device_channel uk_wvp_unique_channel; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_device_channel
    ADD CONSTRAINT uk_wvp_unique_channel UNIQUE (gb_device_id);


--
-- Name: wvp_cloud_record wvp_cloud_record_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_cloud_record
    ADD CONSTRAINT wvp_cloud_record_pkey PRIMARY KEY (id);


--
-- Name: wvp_common_group wvp_common_group_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_common_group
    ADD CONSTRAINT wvp_common_group_pkey PRIMARY KEY (id);


--
-- Name: wvp_common_region wvp_common_region_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_common_region
    ADD CONSTRAINT wvp_common_region_pkey PRIMARY KEY (id);


--
-- Name: wvp_device_alarm wvp_device_alarm_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_device_alarm
    ADD CONSTRAINT wvp_device_alarm_pkey PRIMARY KEY (id);


--
-- Name: wvp_device_channel wvp_device_channel_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_device_channel
    ADD CONSTRAINT wvp_device_channel_pkey PRIMARY KEY (id);


--
-- Name: wvp_device_mobile_position wvp_device_mobile_position_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_device_mobile_position
    ADD CONSTRAINT wvp_device_mobile_position_pkey PRIMARY KEY (id);


--
-- Name: wvp_device wvp_device_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_device
    ADD CONSTRAINT wvp_device_pkey PRIMARY KEY (id);


--
-- Name: wvp_jt_channel wvp_jt_channel_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_jt_channel
    ADD CONSTRAINT wvp_jt_channel_pkey PRIMARY KEY (id);


--
-- Name: wvp_jt_terminal wvp_jt_terminal_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_jt_terminal
    ADD CONSTRAINT wvp_jt_terminal_pkey PRIMARY KEY (id);


--
-- Name: wvp_media_server wvp_media_server_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_media_server
    ADD CONSTRAINT wvp_media_server_pkey PRIMARY KEY (id);


--
-- Name: wvp_platform_channel wvp_platform_channel_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_platform_channel
    ADD CONSTRAINT wvp_platform_channel_pkey PRIMARY KEY (id);


--
-- Name: wvp_platform_group wvp_platform_group_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_platform_group
    ADD CONSTRAINT wvp_platform_group_pkey PRIMARY KEY (id);


--
-- Name: wvp_platform wvp_platform_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_platform
    ADD CONSTRAINT wvp_platform_pkey PRIMARY KEY (id);


--
-- Name: wvp_platform_region wvp_platform_region_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_platform_region
    ADD CONSTRAINT wvp_platform_region_pkey PRIMARY KEY (id);


--
-- Name: wvp_record_plan_item wvp_record_plan_item_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_record_plan_item
    ADD CONSTRAINT wvp_record_plan_item_pkey PRIMARY KEY (id);


--
-- Name: wvp_record_plan wvp_record_plan_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_record_plan
    ADD CONSTRAINT wvp_record_plan_pkey PRIMARY KEY (id);


--
-- Name: wvp_stream_proxy wvp_stream_proxy_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_stream_proxy
    ADD CONSTRAINT wvp_stream_proxy_pkey PRIMARY KEY (id);


--
-- Name: wvp_stream_push wvp_stream_push_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_stream_push
    ADD CONSTRAINT wvp_stream_push_pkey PRIMARY KEY (id);


--
-- Name: wvp_user_api_key wvp_user_api_key_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_user_api_key
    ADD CONSTRAINT wvp_user_api_key_pkey PRIMARY KEY (id);


--
-- Name: wvp_user wvp_user_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_user
    ADD CONSTRAINT wvp_user_pkey PRIMARY KEY (id);


--
-- Name: wvp_user_role wvp_user_role_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wvp_user_role
    ADD CONSTRAINT wvp_user_role_pkey PRIMARY KEY (id);


--
-- Name: idx_data_device_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_data_device_id ON public.wvp_device_channel USING btree (data_device_id);


--
-- Name: idx_data_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_data_type ON public.wvp_device_channel USING btree (data_type);


--
-- PostgreSQL database dump complete
--

\unrestrict eFhTWSxuHf2af2JEdSHaLgUZhNpAddNlm7bKAUcel6gbo3lbiNzqBIyS5aTigmF

