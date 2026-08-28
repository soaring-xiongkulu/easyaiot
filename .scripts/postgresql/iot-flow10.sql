--
-- PostgreSQL database dump
--

\restrict o26nKSoizOO52ZnGpzq3GK5reCHJwKK23GCACIoiQZabrZghqecgJZJoI4fAXyd

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

DROP DATABASE IF EXISTS "iot-flow20";
--
-- Name: iot-flow20; Type: DATABASE; Schema: -; Owner: -
--

CREATE DATABASE "iot-flow20" WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'en_US.utf8';


\unrestrict o26nKSoizOO52ZnGpzq3GK5reCHJwKK23GCACIoiQZabrZghqecgJZJoI4fAXyd
\encoding SQL_ASCII
\connect -reuse-previous=on "dbname='iot-flow20'"
\restrict o26nKSoizOO52ZnGpzq3GK5reCHJwKK23GCACIoiQZabrZghqecgJZJoI4fAXyd

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
-- Name: act_evt_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.act_evt_log (
    log_nr_ integer NOT NULL,
    type_ character varying(64),
    proc_def_id_ character varying(64),
    proc_inst_id_ character varying(64),
    execution_id_ character varying(64),
    task_id_ character varying(64),
    time_stamp_ timestamp without time zone NOT NULL,
    user_id_ character varying(255),
    data_ bytea,
    lock_owner_ character varying(255),
    lock_time_ timestamp without time zone,
    is_processed_ smallint DEFAULT 0
);


--
-- Name: act_evt_log_log_nr__seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.act_evt_log_log_nr__seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: act_evt_log_log_nr__seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.act_evt_log_log_nr__seq OWNED BY public.act_evt_log.log_nr_;


--
-- Name: act_ge_bytearray; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.act_ge_bytearray (
    id_ character varying(64) NOT NULL,
    rev_ integer,
    name_ character varying(255),
    deployment_id_ character varying(64),
    bytes_ bytea,
    generated_ boolean
);


--
-- Name: act_ge_property; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.act_ge_property (
    name_ character varying(64) NOT NULL,
    value_ character varying(300),
    rev_ integer
);


--
-- Name: act_hi_actinst; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.act_hi_actinst (
    id_ character varying(64) NOT NULL,
    rev_ integer DEFAULT 1,
    proc_def_id_ character varying(64) NOT NULL,
    proc_inst_id_ character varying(64) NOT NULL,
    execution_id_ character varying(64) NOT NULL,
    act_id_ character varying(255) NOT NULL,
    task_id_ character varying(64),
    call_proc_inst_id_ character varying(64),
    act_name_ character varying(255),
    act_type_ character varying(255) NOT NULL,
    assignee_ character varying(255),
    start_time_ timestamp without time zone NOT NULL,
    end_time_ timestamp without time zone,
    transaction_order_ integer,
    duration_ bigint,
    delete_reason_ character varying(4000),
    tenant_id_ character varying(255) DEFAULT ''::character varying
);


--
-- Name: act_hi_attachment; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.act_hi_attachment (
    id_ character varying(64) NOT NULL,
    rev_ integer,
    user_id_ character varying(255),
    name_ character varying(255),
    description_ character varying(4000),
    type_ character varying(255),
    task_id_ character varying(64),
    proc_inst_id_ character varying(64),
    url_ character varying(4000),
    content_id_ character varying(64),
    time_ timestamp without time zone
);


--
-- Name: act_hi_comment; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.act_hi_comment (
    id_ character varying(64) NOT NULL,
    type_ character varying(255),
    time_ timestamp without time zone NOT NULL,
    user_id_ character varying(255),
    task_id_ character varying(64),
    proc_inst_id_ character varying(64),
    action_ character varying(255),
    message_ character varying(4000),
    full_msg_ bytea
);


--
-- Name: act_hi_detail; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.act_hi_detail (
    id_ character varying(64) NOT NULL,
    type_ character varying(255) NOT NULL,
    proc_inst_id_ character varying(64),
    execution_id_ character varying(64),
    task_id_ character varying(64),
    act_inst_id_ character varying(64),
    name_ character varying(255) NOT NULL,
    var_type_ character varying(64),
    rev_ integer,
    time_ timestamp without time zone NOT NULL,
    bytearray_id_ character varying(64),
    double_ double precision,
    long_ bigint,
    text_ character varying(4000),
    text2_ character varying(4000)
);


--
-- Name: act_hi_entitylink; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.act_hi_entitylink (
    id_ character varying(64) NOT NULL,
    link_type_ character varying(255),
    create_time_ timestamp without time zone,
    scope_id_ character varying(255),
    sub_scope_id_ character varying(255),
    scope_type_ character varying(255),
    scope_definition_id_ character varying(255),
    parent_element_id_ character varying(255),
    ref_scope_id_ character varying(255),
    ref_scope_type_ character varying(255),
    ref_scope_definition_id_ character varying(255),
    root_scope_id_ character varying(255),
    root_scope_type_ character varying(255),
    hierarchy_type_ character varying(255)
);


--
-- Name: act_hi_identitylink; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.act_hi_identitylink (
    id_ character varying(64) NOT NULL,
    group_id_ character varying(255),
    type_ character varying(255),
    user_id_ character varying(255),
    task_id_ character varying(64),
    create_time_ timestamp without time zone,
    proc_inst_id_ character varying(64),
    scope_id_ character varying(255),
    sub_scope_id_ character varying(255),
    scope_type_ character varying(255),
    scope_definition_id_ character varying(255)
);


--
-- Name: act_hi_procinst; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.act_hi_procinst (
    id_ character varying(64) NOT NULL,
    rev_ integer DEFAULT 1,
    proc_inst_id_ character varying(64) NOT NULL,
    business_key_ character varying(255),
    proc_def_id_ character varying(64) NOT NULL,
    start_time_ timestamp without time zone NOT NULL,
    end_time_ timestamp without time zone,
    duration_ bigint,
    start_user_id_ character varying(255),
    start_act_id_ character varying(255),
    end_act_id_ character varying(255),
    super_process_instance_id_ character varying(64),
    delete_reason_ character varying(4000),
    tenant_id_ character varying(255) DEFAULT ''::character varying,
    name_ character varying(255),
    callback_id_ character varying(255),
    callback_type_ character varying(255),
    reference_id_ character varying(255),
    reference_type_ character varying(255),
    propagated_stage_inst_id_ character varying(255),
    business_status_ character varying(255)
);


--
-- Name: act_hi_taskinst; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.act_hi_taskinst (
    id_ character varying(64) NOT NULL,
    rev_ integer DEFAULT 1,
    proc_def_id_ character varying(64),
    task_def_id_ character varying(64),
    task_def_key_ character varying(255),
    proc_inst_id_ character varying(64),
    execution_id_ character varying(64),
    scope_id_ character varying(255),
    sub_scope_id_ character varying(255),
    scope_type_ character varying(255),
    scope_definition_id_ character varying(255),
    propagated_stage_inst_id_ character varying(255),
    name_ character varying(255),
    parent_task_id_ character varying(64),
    description_ character varying(4000),
    owner_ character varying(255),
    assignee_ character varying(255),
    start_time_ timestamp without time zone NOT NULL,
    claim_time_ timestamp without time zone,
    end_time_ timestamp without time zone,
    duration_ bigint,
    delete_reason_ character varying(4000),
    priority_ integer,
    due_date_ timestamp without time zone,
    form_key_ character varying(255),
    category_ character varying(255),
    tenant_id_ character varying(255) DEFAULT ''::character varying,
    last_updated_time_ timestamp without time zone
);


--
-- Name: act_hi_tsk_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.act_hi_tsk_log (
    id_ integer NOT NULL,
    type_ character varying(64),
    task_id_ character varying(64) NOT NULL,
    time_stamp_ timestamp without time zone NOT NULL,
    user_id_ character varying(255),
    data_ character varying(4000),
    execution_id_ character varying(64),
    proc_inst_id_ character varying(64),
    proc_def_id_ character varying(64),
    scope_id_ character varying(255),
    scope_definition_id_ character varying(255),
    sub_scope_id_ character varying(255),
    scope_type_ character varying(255),
    tenant_id_ character varying(255) DEFAULT ''::character varying
);


--
-- Name: act_hi_tsk_log_id__seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.act_hi_tsk_log_id__seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: act_hi_tsk_log_id__seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.act_hi_tsk_log_id__seq OWNED BY public.act_hi_tsk_log.id_;


--
-- Name: act_hi_varinst; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.act_hi_varinst (
    id_ character varying(64) NOT NULL,
    rev_ integer DEFAULT 1,
    proc_inst_id_ character varying(64),
    execution_id_ character varying(64),
    task_id_ character varying(64),
    name_ character varying(255) NOT NULL,
    var_type_ character varying(100),
    scope_id_ character varying(255),
    sub_scope_id_ character varying(255),
    scope_type_ character varying(255),
    bytearray_id_ character varying(64),
    double_ double precision,
    long_ bigint,
    text_ character varying(4000),
    text2_ character varying(4000),
    create_time_ timestamp without time zone,
    last_updated_time_ timestamp without time zone
);


--
-- Name: act_id_bytearray; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.act_id_bytearray (
    id_ character varying(64) NOT NULL,
    rev_ integer,
    name_ character varying(255),
    bytes_ bytea
);


--
-- Name: act_id_group; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.act_id_group (
    id_ character varying(64) NOT NULL,
    rev_ integer,
    name_ character varying(255),
    type_ character varying(255)
);


--
-- Name: act_id_info; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.act_id_info (
    id_ character varying(64) NOT NULL,
    rev_ integer,
    user_id_ character varying(64),
    type_ character varying(64),
    key_ character varying(255),
    value_ character varying(255),
    password_ bytea,
    parent_id_ character varying(255)
);


--
-- Name: act_id_membership; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.act_id_membership (
    user_id_ character varying(64) NOT NULL,
    group_id_ character varying(64) NOT NULL
);


--
-- Name: act_id_priv; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.act_id_priv (
    id_ character varying(64) NOT NULL,
    name_ character varying(255) NOT NULL
);


--
-- Name: act_id_priv_mapping; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.act_id_priv_mapping (
    id_ character varying(64) NOT NULL,
    priv_id_ character varying(64) NOT NULL,
    user_id_ character varying(255),
    group_id_ character varying(255)
);


--
-- Name: act_id_property; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.act_id_property (
    name_ character varying(64) NOT NULL,
    value_ character varying(300),
    rev_ integer
);


--
-- Name: act_id_token; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.act_id_token (
    id_ character varying(64) NOT NULL,
    rev_ integer,
    token_value_ character varying(255),
    token_date_ timestamp without time zone,
    ip_address_ character varying(255),
    user_agent_ character varying(255),
    user_id_ character varying(255),
    token_data_ character varying(2000)
);


--
-- Name: act_id_user; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.act_id_user (
    id_ character varying(64) NOT NULL,
    rev_ integer,
    first_ character varying(255),
    last_ character varying(255),
    display_name_ character varying(255),
    email_ character varying(255),
    pwd_ character varying(255),
    picture_id_ character varying(64),
    tenant_id_ character varying(255) DEFAULT ''::character varying
);


--
-- Name: act_procdef_info; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.act_procdef_info (
    id_ character varying(64) NOT NULL,
    proc_def_id_ character varying(64) NOT NULL,
    rev_ integer,
    info_json_id_ character varying(64)
);


--
-- Name: act_re_deployment; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.act_re_deployment (
    id_ character varying(64) NOT NULL,
    name_ character varying(255),
    category_ character varying(255),
    key_ character varying(255),
    tenant_id_ character varying(255) DEFAULT ''::character varying,
    deploy_time_ timestamp without time zone,
    derived_from_ character varying(64),
    derived_from_root_ character varying(64),
    parent_deployment_id_ character varying(255),
    engine_version_ character varying(255)
);


--
-- Name: act_re_model; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.act_re_model (
    id_ character varying(64) NOT NULL,
    rev_ integer,
    name_ character varying(255),
    key_ character varying(255),
    category_ character varying(255),
    create_time_ timestamp without time zone,
    last_update_time_ timestamp without time zone,
    version_ integer,
    meta_info_ character varying(4000),
    deployment_id_ character varying(64),
    editor_source_value_id_ character varying(64),
    editor_source_extra_value_id_ character varying(64),
    tenant_id_ character varying(255) DEFAULT ''::character varying
);


--
-- Name: act_re_procdef; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.act_re_procdef (
    id_ character varying(64) NOT NULL,
    rev_ integer,
    category_ character varying(255),
    name_ character varying(255),
    key_ character varying(255) NOT NULL,
    version_ integer NOT NULL,
    deployment_id_ character varying(64),
    resource_name_ character varying(4000),
    dgrm_resource_name_ character varying(4000),
    description_ character varying(4000),
    has_start_form_key_ boolean,
    has_graphical_notation_ boolean,
    suspension_state_ integer,
    tenant_id_ character varying(255) DEFAULT ''::character varying,
    derived_from_ character varying(64),
    derived_from_root_ character varying(64),
    derived_version_ integer DEFAULT 0 NOT NULL,
    engine_version_ character varying(255)
);


--
-- Name: act_ru_actinst; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.act_ru_actinst (
    id_ character varying(64) NOT NULL,
    rev_ integer DEFAULT 1,
    proc_def_id_ character varying(64) NOT NULL,
    proc_inst_id_ character varying(64) NOT NULL,
    execution_id_ character varying(64) NOT NULL,
    act_id_ character varying(255) NOT NULL,
    task_id_ character varying(64),
    call_proc_inst_id_ character varying(64),
    act_name_ character varying(255),
    act_type_ character varying(255) NOT NULL,
    assignee_ character varying(255),
    start_time_ timestamp without time zone NOT NULL,
    end_time_ timestamp without time zone,
    duration_ bigint,
    transaction_order_ integer,
    delete_reason_ character varying(4000),
    tenant_id_ character varying(255) DEFAULT ''::character varying
);


--
-- Name: act_ru_deadletter_job; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.act_ru_deadletter_job (
    id_ character varying(64) NOT NULL,
    rev_ integer,
    category_ character varying(255),
    type_ character varying(255) NOT NULL,
    exclusive_ boolean,
    execution_id_ character varying(64),
    process_instance_id_ character varying(64),
    proc_def_id_ character varying(64),
    element_id_ character varying(255),
    element_name_ character varying(255),
    scope_id_ character varying(255),
    sub_scope_id_ character varying(255),
    scope_type_ character varying(255),
    scope_definition_id_ character varying(255),
    correlation_id_ character varying(255),
    exception_stack_id_ character varying(64),
    exception_msg_ character varying(4000),
    duedate_ timestamp without time zone,
    repeat_ character varying(255),
    handler_type_ character varying(255),
    handler_cfg_ character varying(4000),
    custom_values_id_ character varying(64),
    create_time_ timestamp without time zone,
    tenant_id_ character varying(255) DEFAULT ''::character varying
);


--
-- Name: act_ru_entitylink; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.act_ru_entitylink (
    id_ character varying(64) NOT NULL,
    rev_ integer,
    create_time_ timestamp without time zone,
    link_type_ character varying(255),
    scope_id_ character varying(255),
    sub_scope_id_ character varying(255),
    scope_type_ character varying(255),
    scope_definition_id_ character varying(255),
    parent_element_id_ character varying(255),
    ref_scope_id_ character varying(255),
    ref_scope_type_ character varying(255),
    ref_scope_definition_id_ character varying(255),
    root_scope_id_ character varying(255),
    root_scope_type_ character varying(255),
    hierarchy_type_ character varying(255)
);


--
-- Name: act_ru_event_subscr; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.act_ru_event_subscr (
    id_ character varying(64) NOT NULL,
    rev_ integer,
    event_type_ character varying(255) NOT NULL,
    event_name_ character varying(255),
    execution_id_ character varying(64),
    proc_inst_id_ character varying(64),
    activity_id_ character varying(64),
    configuration_ character varying(255),
    created_ timestamp without time zone NOT NULL,
    proc_def_id_ character varying(64),
    sub_scope_id_ character varying(64),
    scope_id_ character varying(64),
    scope_definition_id_ character varying(64),
    scope_type_ character varying(64),
    lock_time_ timestamp without time zone,
    lock_owner_ character varying(255),
    tenant_id_ character varying(255) DEFAULT ''::character varying
);


--
-- Name: act_ru_execution; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.act_ru_execution (
    id_ character varying(64) NOT NULL,
    rev_ integer,
    proc_inst_id_ character varying(64),
    business_key_ character varying(255),
    parent_id_ character varying(64),
    proc_def_id_ character varying(64),
    super_exec_ character varying(64),
    root_proc_inst_id_ character varying(64),
    act_id_ character varying(255),
    is_active_ boolean,
    is_concurrent_ boolean,
    is_scope_ boolean,
    is_event_scope_ boolean,
    is_mi_root_ boolean,
    suspension_state_ integer,
    cached_ent_state_ integer,
    tenant_id_ character varying(255) DEFAULT ''::character varying,
    name_ character varying(255),
    start_act_id_ character varying(255),
    start_time_ timestamp without time zone,
    start_user_id_ character varying(255),
    lock_time_ timestamp without time zone,
    lock_owner_ character varying(255),
    is_count_enabled_ boolean,
    evt_subscr_count_ integer,
    task_count_ integer,
    job_count_ integer,
    timer_job_count_ integer,
    susp_job_count_ integer,
    deadletter_job_count_ integer,
    external_worker_job_count_ integer,
    var_count_ integer,
    id_link_count_ integer,
    callback_id_ character varying(255),
    callback_type_ character varying(255),
    reference_id_ character varying(255),
    reference_type_ character varying(255),
    propagated_stage_inst_id_ character varying(255),
    business_status_ character varying(255)
);


--
-- Name: act_ru_external_job; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.act_ru_external_job (
    id_ character varying(64) NOT NULL,
    rev_ integer,
    category_ character varying(255),
    type_ character varying(255) NOT NULL,
    lock_exp_time_ timestamp without time zone,
    lock_owner_ character varying(255),
    exclusive_ boolean,
    execution_id_ character varying(64),
    process_instance_id_ character varying(64),
    proc_def_id_ character varying(64),
    element_id_ character varying(255),
    element_name_ character varying(255),
    scope_id_ character varying(255),
    sub_scope_id_ character varying(255),
    scope_type_ character varying(255),
    scope_definition_id_ character varying(255),
    correlation_id_ character varying(255),
    retries_ integer,
    exception_stack_id_ character varying(64),
    exception_msg_ character varying(4000),
    duedate_ timestamp without time zone,
    repeat_ character varying(255),
    handler_type_ character varying(255),
    handler_cfg_ character varying(4000),
    custom_values_id_ character varying(64),
    create_time_ timestamp without time zone,
    tenant_id_ character varying(255) DEFAULT ''::character varying
);


--
-- Name: act_ru_history_job; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.act_ru_history_job (
    id_ character varying(64) NOT NULL,
    rev_ integer,
    lock_exp_time_ timestamp without time zone,
    lock_owner_ character varying(255),
    retries_ integer,
    exception_stack_id_ character varying(64),
    exception_msg_ character varying(4000),
    handler_type_ character varying(255),
    handler_cfg_ character varying(4000),
    custom_values_id_ character varying(64),
    adv_handler_cfg_id_ character varying(64),
    create_time_ timestamp without time zone,
    scope_type_ character varying(255),
    tenant_id_ character varying(255) DEFAULT ''::character varying
);


--
-- Name: act_ru_identitylink; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.act_ru_identitylink (
    id_ character varying(64) NOT NULL,
    rev_ integer,
    group_id_ character varying(255),
    type_ character varying(255),
    user_id_ character varying(255),
    task_id_ character varying(64),
    proc_inst_id_ character varying(64),
    proc_def_id_ character varying(64),
    scope_id_ character varying(255),
    sub_scope_id_ character varying(255),
    scope_type_ character varying(255),
    scope_definition_id_ character varying(255)
);


--
-- Name: act_ru_job; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.act_ru_job (
    id_ character varying(64) NOT NULL,
    rev_ integer,
    category_ character varying(255),
    type_ character varying(255) NOT NULL,
    lock_exp_time_ timestamp without time zone,
    lock_owner_ character varying(255),
    exclusive_ boolean,
    execution_id_ character varying(64),
    process_instance_id_ character varying(64),
    proc_def_id_ character varying(64),
    element_id_ character varying(255),
    element_name_ character varying(255),
    scope_id_ character varying(255),
    sub_scope_id_ character varying(255),
    scope_type_ character varying(255),
    scope_definition_id_ character varying(255),
    correlation_id_ character varying(255),
    retries_ integer,
    exception_stack_id_ character varying(64),
    exception_msg_ character varying(4000),
    duedate_ timestamp without time zone,
    repeat_ character varying(255),
    handler_type_ character varying(255),
    handler_cfg_ character varying(4000),
    custom_values_id_ character varying(64),
    create_time_ timestamp without time zone,
    tenant_id_ character varying(255) DEFAULT ''::character varying
);


--
-- Name: act_ru_suspended_job; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.act_ru_suspended_job (
    id_ character varying(64) NOT NULL,
    rev_ integer,
    category_ character varying(255),
    type_ character varying(255) NOT NULL,
    exclusive_ boolean,
    execution_id_ character varying(64),
    process_instance_id_ character varying(64),
    proc_def_id_ character varying(64),
    element_id_ character varying(255),
    element_name_ character varying(255),
    scope_id_ character varying(255),
    sub_scope_id_ character varying(255),
    scope_type_ character varying(255),
    scope_definition_id_ character varying(255),
    correlation_id_ character varying(255),
    retries_ integer,
    exception_stack_id_ character varying(64),
    exception_msg_ character varying(4000),
    duedate_ timestamp without time zone,
    repeat_ character varying(255),
    handler_type_ character varying(255),
    handler_cfg_ character varying(4000),
    custom_values_id_ character varying(64),
    create_time_ timestamp without time zone,
    tenant_id_ character varying(255) DEFAULT ''::character varying
);


--
-- Name: act_ru_task; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.act_ru_task (
    id_ character varying(64) NOT NULL,
    rev_ integer,
    execution_id_ character varying(64),
    proc_inst_id_ character varying(64),
    proc_def_id_ character varying(64),
    task_def_id_ character varying(64),
    scope_id_ character varying(255),
    sub_scope_id_ character varying(255),
    scope_type_ character varying(255),
    scope_definition_id_ character varying(255),
    propagated_stage_inst_id_ character varying(255),
    name_ character varying(255),
    parent_task_id_ character varying(64),
    description_ character varying(4000),
    task_def_key_ character varying(255),
    owner_ character varying(255),
    assignee_ character varying(255),
    delegation_ character varying(64),
    priority_ integer,
    create_time_ timestamp without time zone,
    due_date_ timestamp without time zone,
    category_ character varying(255),
    suspension_state_ integer,
    tenant_id_ character varying(255) DEFAULT ''::character varying,
    form_key_ character varying(255),
    claim_time_ timestamp without time zone,
    is_count_enabled_ boolean,
    var_count_ integer,
    id_link_count_ integer,
    sub_task_count_ integer
);


--
-- Name: act_ru_timer_job; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.act_ru_timer_job (
    id_ character varying(64) NOT NULL,
    rev_ integer,
    category_ character varying(255),
    type_ character varying(255) NOT NULL,
    lock_exp_time_ timestamp without time zone,
    lock_owner_ character varying(255),
    exclusive_ boolean,
    execution_id_ character varying(64),
    process_instance_id_ character varying(64),
    proc_def_id_ character varying(64),
    element_id_ character varying(255),
    element_name_ character varying(255),
    scope_id_ character varying(255),
    sub_scope_id_ character varying(255),
    scope_type_ character varying(255),
    scope_definition_id_ character varying(255),
    correlation_id_ character varying(255),
    retries_ integer,
    exception_stack_id_ character varying(64),
    exception_msg_ character varying(4000),
    duedate_ timestamp without time zone,
    repeat_ character varying(255),
    handler_type_ character varying(255),
    handler_cfg_ character varying(4000),
    custom_values_id_ character varying(64),
    create_time_ timestamp without time zone,
    tenant_id_ character varying(255) DEFAULT ''::character varying
);


--
-- Name: act_ru_variable; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.act_ru_variable (
    id_ character varying(64) NOT NULL,
    rev_ integer,
    type_ character varying(255) NOT NULL,
    name_ character varying(255) NOT NULL,
    execution_id_ character varying(64),
    proc_inst_id_ character varying(64),
    task_id_ character varying(64),
    scope_id_ character varying(255),
    sub_scope_id_ character varying(255),
    scope_type_ character varying(255),
    bytearray_id_ character varying(64),
    double_ double precision,
    long_ bigint,
    text_ character varying(4000),
    text2_ character varying(4000)
);


--
-- Name: flow_alert_record; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.flow_alert_record (
    id bigint NOT NULL,
    alert_id bigint NOT NULL,
    alert_source character varying(32) DEFAULT 'VIDEO_TASK'::character varying NOT NULL,
    alert_snapshot text,
    process_instance_id character varying(64),
    process_definition_key character varying(64),
    process_instance_status integer DEFAULT 1 NOT NULL,
    current_task_name character varying(128),
    current_assignees character varying(500),
    finish_time timestamp without time zone,
    creator character varying(64) DEFAULT ''::character varying,
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updater character varying(64) DEFAULT ''::character varying,
    update_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    deleted smallint DEFAULT 0 NOT NULL
);


--
-- Name: flow_alert_record_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.flow_alert_record_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: flow_alert_record_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.flow_alert_record_id_seq OWNED BY public.flow_alert_record.id;


--
-- Name: flow_alert_route_rule; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.flow_alert_route_rule (
    id bigint NOT NULL,
    rule_name character varying(64) NOT NULL,
    priority integer DEFAULT 0 NOT NULL,
    process_definition_key character varying(64) NOT NULL,
    match_conditions text DEFAULT '[]'::text NOT NULL,
    dedup_window_seconds integer DEFAULT 300 NOT NULL,
    enabled boolean DEFAULT true NOT NULL,
    start_user_id bigint,
    remark character varying(500),
    creator character varying(64) DEFAULT ''::character varying,
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updater character varying(64) DEFAULT ''::character varying,
    update_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    deleted smallint DEFAULT 0 NOT NULL
);


--
-- Name: flow_alert_route_rule_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.flow_alert_route_rule_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: flow_alert_route_rule_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.flow_alert_route_rule_id_seq OWNED BY public.flow_alert_route_rule.id;


--
-- Name: flow_category; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.flow_category (
    id bigint NOT NULL,
    name character varying(64) NOT NULL,
    code character varying(64) NOT NULL,
    status smallint DEFAULT 0 NOT NULL,
    sort integer DEFAULT 0 NOT NULL,
    description character varying(500),
    tenant_id bigint DEFAULT 0 NOT NULL,
    creator character varying(64) DEFAULT ''::character varying,
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updater character varying(64) DEFAULT ''::character varying,
    update_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    deleted smallint DEFAULT 0 NOT NULL
);


--
-- Name: flow_category_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.flow_category_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: flow_category_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.flow_category_id_seq OWNED BY public.flow_category.id;


--
-- Name: flow_copy; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.flow_copy (
    id bigint NOT NULL,
    process_instance_id character varying(64) NOT NULL,
    process_instance_name character varying(200),
    category character varying(64),
    task_id character varying(64),
    task_name character varying(128),
    activity_id character varying(64),
    start_user_id bigint,
    reason character varying(500),
    user_id bigint NOT NULL,
    tenant_id bigint DEFAULT 0 NOT NULL,
    creator character varying(64) DEFAULT ''::character varying,
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updater character varying(64) DEFAULT ''::character varying,
    update_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    deleted smallint DEFAULT 0 NOT NULL
);


--
-- Name: flow_copy_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.flow_copy_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: flow_copy_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.flow_copy_id_seq OWNED BY public.flow_copy.id;


--
-- Name: flow_user_group; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.flow_user_group (
    id bigint NOT NULL,
    name character varying(64) NOT NULL,
    description character varying(500),
    member_user_ids character varying(2000) DEFAULT '[]'::character varying NOT NULL,
    status smallint DEFAULT 0 NOT NULL,
    tenant_id bigint DEFAULT 0 NOT NULL,
    creator character varying(64) DEFAULT ''::character varying,
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updater character varying(64) DEFAULT ''::character varying,
    update_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    deleted smallint DEFAULT 0 NOT NULL
);


--
-- Name: flow_user_group_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.flow_user_group_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: flow_user_group_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.flow_user_group_id_seq OWNED BY public.flow_user_group.id;


--
-- Name: flw_channel_definition; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.flw_channel_definition (
    id_ character varying(255) NOT NULL,
    name_ character varying(255),
    version_ integer,
    key_ character varying(255),
    category_ character varying(255),
    deployment_id_ character varying(255),
    create_time_ timestamp(3) without time zone,
    tenant_id_ character varying(255),
    resource_name_ character varying(255),
    description_ character varying(255),
    type_ character varying(255),
    implementation_ character varying(255)
);


--
-- Name: flw_ev_databasechangelog; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.flw_ev_databasechangelog (
    id character varying(255) NOT NULL,
    author character varying(255) NOT NULL,
    filename character varying(255) NOT NULL,
    dateexecuted timestamp without time zone NOT NULL,
    orderexecuted integer NOT NULL,
    exectype character varying(10) NOT NULL,
    md5sum character varying(35),
    description character varying(255),
    comments character varying(255),
    tag character varying(255),
    liquibase character varying(20),
    contexts character varying(255),
    labels character varying(255),
    deployment_id character varying(10)
);


--
-- Name: flw_ev_databasechangeloglock; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.flw_ev_databasechangeloglock (
    id integer NOT NULL,
    locked boolean NOT NULL,
    lockgranted timestamp without time zone,
    lockedby character varying(255)
);


--
-- Name: flw_event_definition; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.flw_event_definition (
    id_ character varying(255) NOT NULL,
    name_ character varying(255),
    version_ integer,
    key_ character varying(255),
    category_ character varying(255),
    deployment_id_ character varying(255),
    tenant_id_ character varying(255),
    resource_name_ character varying(255),
    description_ character varying(255)
);


--
-- Name: flw_event_deployment; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.flw_event_deployment (
    id_ character varying(255) NOT NULL,
    name_ character varying(255),
    category_ character varying(255),
    deploy_time_ timestamp(3) without time zone,
    tenant_id_ character varying(255),
    parent_deployment_id_ character varying(255)
);


--
-- Name: flw_event_resource; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.flw_event_resource (
    id_ character varying(255) NOT NULL,
    name_ character varying(255),
    deployment_id_ character varying(255),
    resource_bytes_ bytea
);


--
-- Name: flw_ru_batch; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.flw_ru_batch (
    id_ character varying(64) NOT NULL,
    rev_ integer,
    type_ character varying(64) NOT NULL,
    search_key_ character varying(255),
    search_key2_ character varying(255),
    create_time_ timestamp without time zone NOT NULL,
    complete_time_ timestamp without time zone,
    status_ character varying(255),
    batch_doc_id_ character varying(64),
    tenant_id_ character varying(255) DEFAULT ''::character varying
);


--
-- Name: flw_ru_batch_part; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.flw_ru_batch_part (
    id_ character varying(64) NOT NULL,
    rev_ integer,
    batch_id_ character varying(64),
    type_ character varying(64) NOT NULL,
    scope_id_ character varying(64),
    sub_scope_id_ character varying(64),
    scope_type_ character varying(64),
    search_key_ character varying(255),
    search_key2_ character varying(255),
    create_time_ timestamp without time zone NOT NULL,
    complete_time_ timestamp without time zone,
    status_ character varying(255),
    result_doc_id_ character varying(64),
    tenant_id_ character varying(255) DEFAULT ''::character varying
);


--
-- Name: act_evt_log log_nr_; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_evt_log ALTER COLUMN log_nr_ SET DEFAULT nextval('public.act_evt_log_log_nr__seq'::regclass);


--
-- Name: act_hi_tsk_log id_; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_hi_tsk_log ALTER COLUMN id_ SET DEFAULT nextval('public.act_hi_tsk_log_id__seq'::regclass);


--
-- Name: flow_alert_record id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.flow_alert_record ALTER COLUMN id SET DEFAULT nextval('public.flow_alert_record_id_seq'::regclass);


--
-- Name: flow_alert_route_rule id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.flow_alert_route_rule ALTER COLUMN id SET DEFAULT nextval('public.flow_alert_route_rule_id_seq'::regclass);


--
-- Name: flow_category id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.flow_category ALTER COLUMN id SET DEFAULT nextval('public.flow_category_id_seq'::regclass);


--
-- Name: flow_copy id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.flow_copy ALTER COLUMN id SET DEFAULT nextval('public.flow_copy_id_seq'::regclass);


--
-- Name: flow_user_group id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.flow_user_group ALTER COLUMN id SET DEFAULT nextval('public.flow_user_group_id_seq'::regclass);


--
-- Data for Name: act_evt_log; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.act_evt_log (log_nr_, type_, proc_def_id_, proc_inst_id_, execution_id_, task_id_, time_stamp_, user_id_, data_, lock_owner_, lock_time_, is_processed_) FROM stdin;
\.


--
-- Data for Name: act_ge_bytearray; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.act_ge_bytearray (id_, rev_, name_, deployment_id_, bytes_, generated_) FROM stdin;
4483d611-a29a-11f1-b3db-aefacda18209	1	source	\N	\\x7b226e616d65223a22e4babae59198e585a5e4beb5e5918ae8ada6e5a484e79086222c226964223a22726f6f74222c2274797065223a302c226368696c644e6f6465223a7b226964223a2273746172745f757365725f31222c2274797065223a31302c226e616d65223a22e58f91e8b5b7e4baba222c2273686f7754657874223a6e756c6c2c226368696c644e6f6465223a7b226964223a227461736b5f31222c2274797065223a31312c226e616d65223a22e5aea1e689b9e4baba222c2273686f7754657874223a6e756c6c2c226368696c644e6f6465223a7b226964223a22656e645f31222c2274797065223a312c226e616d65223a22e7bb93e69d9f222c2273686f7754657874223a6e756c6c2c226368696c644e6f6465223a6e756c6c2c22636f6e646974696f6e4e6f646573223a6e756c6c2c22617070726f766554797065223a6e756c6c2c2263616e6469646174655374726174656779223a6e756c6c2c2263616e646964617465506172616d223a6e756c6c2c22617070726f76654d6574686f64223a6e756c6c2c22617070726f7665526174696f223a6e756c6c2c22726561736f6e52657175697265223a6e756c6c2c2274696d656f757448616e646c6572223a6e756c6c2c2272656a65637448616e646c6572223a6e756c6c2c2261737369676e456d70747948616e646c6572223a6e756c6c2c2261737369676e53746172745573657248616e646c657254797065223a6e756c6c2c22636f6e646974696f6e53657474696e67223a6e756c6c2c2264656c617953657474696e67223a6e756c6c7d2c22636f6e646974696f6e4e6f646573223a6e756c6c2c22617070726f766554797065223a6e756c6c2c2263616e6469646174655374726174656779223a33302c2263616e646964617465506172616d223a2231222c22617070726f76654d6574686f64223a332c22617070726f7665526174696f223a6e756c6c2c22726561736f6e52657175697265223a6e756c6c2c2274696d656f757448616e646c6572223a6e756c6c2c2272656a65637448616e646c6572223a6e756c6c2c2261737369676e456d70747948616e646c6572223a6e756c6c2c2261737369676e53746172745573657248616e646c657254797065223a6e756c6c2c22636f6e646974696f6e53657474696e67223a6e756c6c2c2264656c617953657474696e67223a6e756c6c7d2c22636f6e646974696f6e4e6f646573223a6e756c6c2c22617070726f766554797065223a6e756c6c2c2263616e6469646174655374726174656779223a6e756c6c2c2263616e646964617465506172616d223a6e756c6c2c22617070726f76654d6574686f64223a6e756c6c2c22617070726f7665526174696f223a6e756c6c2c22726561736f6e52657175697265223a6e756c6c2c2274696d656f757448616e646c6572223a6e756c6c2c2272656a65637448616e646c6572223a6e756c6c2c2261737369676e456d70747948616e646c6572223a6e756c6c2c2261737369676e53746172745573657248616e646c657254797065223a6e756c6c2c22636f6e646974696f6e53657474696e67223a6e756c6c2c2264656c617953657474696e67223a6e756c6c7d7d	\N
a2baa4f0-a29a-11f1-9a15-aefacda18209	1	alert_intrusion.bpmn	a2baa4ef-a29a-11f1-9a15-aefacda18209	\\x3c3f786d6c2076657273696f6e3d22312e302220656e636f64696e673d225554462d38223f3e0a3c646566696e6974696f6e7320786d6c6e733d22687474703a2f2f7777772e6f6d672e6f72672f737065632f42504d4e2f32303130303532342f4d4f44454c2220786d6c6e733a7873693d22687474703a2f2f7777772e77332e6f72672f323030312f584d4c536368656d612d696e7374616e63652220786d6c6e733a7873643d22687474703a2f2f7777772e77332e6f72672f323030312f584d4c536368656d612220786d6c6e733a666c6f7761626c653d22687474703a2f2f666c6f7761626c652e6f72672f62706d6e2220786d6c6e733a62706d6e64693d22687474703a2f2f7777772e6f6d672e6f72672f737065632f42504d4e2f32303130303532342f44492220786d6c6e733a6f6d6764633d22687474703a2f2f7777772e6f6d672e6f72672f737065632f44442f32303130303532342f44432220786d6c6e733a6f6d6764693d22687474703a2f2f7777772e6f6d672e6f72672f737065632f44442f32303130303532342f44492220747970654c616e67756167653d22687474703a2f2f7777772e77332e6f72672f323030312f584d4c536368656d61222065787072657373696f6e4c616e67756167653d22687474703a2f2f7777772e77332e6f72672f313939392f585061746822207461726765744e616d6573706163653d22687474703a2f2f7777772e666c6f7761626c652e6f72672f74657374223e0a20203c70726f636573732069643d22616c6572745f696e74727573696f6e22206e616d653d22e4babae59198e585a5e4beb5e5918ae8ada6e5a484e790862220697345786563757461626c653d2274727565223e0a202020203c73746172744576656e742069643d2273746172745f6576656e7422206e616d653d22e5bc80e5a78b223e3c2f73746172744576656e743e0a202020203c757365725461736b2069643d227461736b5f3122206e616d653d22e5aea1e689b9e4baba223e0a2020202020203c657874656e73696f6e456c656d656e74733e0a20202020202020203c666c6f7761626c653a63616e646964617465436f6e6620786d6c6e733a666c6f7761626c653d22687474703a2f2f666c6f7761626c652e6f72672f62706d6e2220666c6f7761626c653a63616e64696461746553747261746567793d2233302220666c6f7761626c653a63616e646964617465506172616d3d22312220666c6f7761626c653a617070726f76654d6574686f643d2233223e3c2f666c6f7761626c653a63616e646964617465436f6e663e0a2020202020203c2f657874656e73696f6e456c656d656e74733e0a202020203c2f757365725461736b3e0a202020203c73657175656e6365466c6f772069643d22666c6f775f7461736b5f312220736f757263655265663d2273746172745f6576656e7422207461726765745265663d227461736b5f31223e3c2f73657175656e6365466c6f773e0a202020203c656e644576656e742069643d22656e645f3122206e616d653d22e7bb93e69d9f223e3c2f656e644576656e743e0a202020203c73657175656e6365466c6f772069643d22666c6f775f656e645f312220736f757263655265663d227461736b5f3122207461726765745265663d22656e645f31223e3c2f73657175656e6365466c6f773e0a20203c2f70726f636573733e0a20203c62706d6e64693a42504d4e4469616772616d2069643d2242504d4e4469616772616d5f616c6572745f696e74727573696f6e223e0a202020203c62706d6e64693a42504d4e506c616e652062706d6e456c656d656e743d22616c6572745f696e74727573696f6e222069643d2242504d4e506c616e655f616c6572745f696e74727573696f6e223e3c2f62706d6e64693a42504d4e506c616e653e0a20203c2f62706d6e64693a42504d4e4469616772616d3e0a3c2f646566696e6974696f6e733e	f
3da637e7-a29b-11f1-8fa2-aefacda18209	1	alert_intrusion.bpmn	3da637e6-a29b-11f1-8fa2-aefacda18209	\\x3c3f786d6c2076657273696f6e3d22312e302220656e636f64696e673d225554462d38223f3e0a3c646566696e6974696f6e7320786d6c6e733d22687474703a2f2f7777772e6f6d672e6f72672f737065632f42504d4e2f32303130303532342f4d4f44454c2220786d6c6e733a7873693d22687474703a2f2f7777772e77332e6f72672f323030312f584d4c536368656d612d696e7374616e63652220786d6c6e733a7873643d22687474703a2f2f7777772e77332e6f72672f323030312f584d4c536368656d612220786d6c6e733a666c6f7761626c653d22687474703a2f2f666c6f7761626c652e6f72672f62706d6e2220786d6c6e733a62706d6e64693d22687474703a2f2f7777772e6f6d672e6f72672f737065632f42504d4e2f32303130303532342f44492220786d6c6e733a6f6d6764633d22687474703a2f2f7777772e6f6d672e6f72672f737065632f44442f32303130303532342f44432220786d6c6e733a6f6d6764693d22687474703a2f2f7777772e6f6d672e6f72672f737065632f44442f32303130303532342f44492220747970654c616e67756167653d22687474703a2f2f7777772e77332e6f72672f323030312f584d4c536368656d61222065787072657373696f6e4c616e67756167653d22687474703a2f2f7777772e77332e6f72672f313939392f585061746822207461726765744e616d6573706163653d22616c6572745f68616e646c65223e0a20203c70726f636573732069643d22616c6572745f696e74727573696f6e22206e616d653d22e4babae59198e585a5e4beb5e5918ae8ada6e5a484e790862220697345786563757461626c653d2274727565223e0a202020203c73746172744576656e742069643d2273746172745f6576656e7422206e616d653d22e5bc80e5a78b223e3c2f73746172744576656e743e0a202020203c757365725461736b2069643d227461736b5f3122206e616d653d22e5aea1e689b9e4baba223e0a2020202020203c657874656e73696f6e456c656d656e74733e0a20202020202020203c666c6f7761626c653a63616e646964617465436f6e6620786d6c6e733a666c6f7761626c653d22687474703a2f2f666c6f7761626c652e6f72672f62706d6e2220666c6f7761626c653a63616e64696461746553747261746567793d2233302220666c6f7761626c653a63616e646964617465506172616d3d22312220666c6f7761626c653a617070726f76654d6574686f643d2233223e3c2f666c6f7761626c653a63616e646964617465436f6e663e0a2020202020203c2f657874656e73696f6e456c656d656e74733e0a202020203c2f757365725461736b3e0a202020203c73657175656e6365466c6f772069643d22666c6f775f7461736b5f312220736f757263655265663d2273746172745f6576656e7422207461726765745265663d227461736b5f31223e3c2f73657175656e6365466c6f773e0a202020203c656e644576656e742069643d22656e645f3122206e616d653d22e7bb93e69d9f223e3c2f656e644576656e743e0a202020203c73657175656e6365466c6f772069643d22666c6f775f656e645f312220736f757263655265663d227461736b5f3122207461726765745265663d22656e645f31223e3c2f73657175656e6365466c6f773e0a20203c2f70726f636573733e0a20203c62706d6e64693a42504d4e4469616772616d2069643d2242504d4e4469616772616d5f616c6572745f696e74727573696f6e223e0a202020203c62706d6e64693a42504d4e506c616e652062706d6e456c656d656e743d22616c6572745f696e74727573696f6e222069643d2242504d4e506c616e655f616c6572745f696e74727573696f6e223e3c2f62706d6e64693a42504d4e506c616e653e0a20203c2f62706d6e64693a42504d4e4469616772616d3e0a3c2f646566696e6974696f6e733e	f
5623a25d-a2a7-11f1-ae25-fe31f4546ab1	1	alert_fire_smoke.bpmn	5623a25c-a2a7-11f1-ae25-fe31f4546ab1	\\x3c3f786d6c2076657273696f6e3d22312e302220656e636f64696e673d225554462d38223f3e0a3c646566696e6974696f6e7320786d6c6e733d22687474703a2f2f7777772e6f6d672e6f72672f737065632f42504d4e2f32303130303532342f4d4f44454c2220786d6c6e733a7873693d22687474703a2f2f7777772e77332e6f72672f323030312f584d4c536368656d612d696e7374616e63652220786d6c6e733a7873643d22687474703a2f2f7777772e77332e6f72672f323030312f584d4c536368656d612220786d6c6e733a666c6f7761626c653d22687474703a2f2f666c6f7761626c652e6f72672f62706d6e2220786d6c6e733a62706d6e64693d22687474703a2f2f7777772e6f6d672e6f72672f737065632f42504d4e2f32303130303532342f44492220786d6c6e733a6f6d6764633d22687474703a2f2f7777772e6f6d672e6f72672f737065632f44442f32303130303532342f44432220786d6c6e733a6f6d6764693d22687474703a2f2f7777772e6f6d672e6f72672f737065632f44442f32303130303532342f44492220747970654c616e67756167653d22687474703a2f2f7777772e77332e6f72672f323030312f584d4c536368656d61222065787072657373696f6e4c616e67756167653d22687474703a2f2f7777772e77332e6f72672f313939392f585061746822207461726765744e616d6573706163653d22616c6572745f68616e646c65223e0a20203c70726f636573732069643d22616c6572745f666972655f736d6f6b6522206e616d653d22e7839fe6849fe781abe68385e5918ae8ada6e5a484e790862220697345786563757461626c653d2274727565223e0a202020203c73746172744576656e742069643d2273746172745f6576656e7422206e616d653d22e5bc80e5a78b223e3c2f73746172744576656e743e0a202020203c757365725461736b2069643d227461736b5f7370656369616c69737422206e616d653d22e5ae89e585a8e4b893e59198e5889de5aea1223e0a2020202020203c657874656e73696f6e456c656d656e74733e0a20202020202020203c666c6f7761626c653a63616e646964617465436f6e6620786d6c6e733a666c6f7761626c653d22687474703a2f2f666c6f7761626c652e6f72672f62706d6e2220666c6f7761626c653a63616e64696461746553747261746567793d2233302220666c6f7761626c653a63616e646964617465506172616d3d223130342220666c6f7761626c653a617070726f76654d6574686f643d22332220666c6f7761626c653a726561736f6e526571756972653d2266616c7365223e3c2f666c6f7761626c653a63616e646964617465436f6e663e0a2020202020203c2f657874656e73696f6e456c656d656e74733e0a202020203c2f757365725461736b3e0a202020203c73657175656e6365466c6f772069643d22666c6f775f7461736b5f7370656369616c6973742220736f757263655265663d2273746172745f6576656e7422207461726765745265663d227461736b5f7370656369616c697374223e3c2f73657175656e6365466c6f773e0a202020203c757365725461736b2069643d227461736b5f6d616e616765725f7369676e22206e616d653d22e4b8bbe7aea1e4bc9ae7adbee7a1aee8aea42220666c6f7761626c653a61737369676e65653d22247b61737369676e65657d223e0a2020202020203c657874656e73696f6e456c656d656e74733e0a20202020202020203c666c6f7761626c653a63616e646964617465436f6e6620786d6c6e733a666c6f7761626c653d22687474703a2f2f666c6f7761626c652e6f72672f62706d6e2220666c6f7761626c653a63616e64696461746553747261746567793d2233302220666c6f7761626c653a63616e646964617465506172616d3d223130302c3130342220666c6f7761626c653a617070726f76654d6574686f643d22322220666c6f7761626c653a617070726f7665526174696f3d223130302220666c6f7761626c653a726561736f6e526571756972653d22747275652220666c6f7761626c653a72656a65637448616e646c6572547970653d22322220666c6f7761626c653a72656a65637452657475726e4e6f646549643d227461736b5f7370656369616c697374223e3c2f666c6f7761626c653a63616e646964617465436f6e663e0a2020202020203c2f657874656e73696f6e456c656d656e74733e0a2020202020203c6d756c7469496e7374616e63654c6f6f7043686172616374657269737469637320697353657175656e7469616c3d2266616c73652220666c6f7761626c653a636f6c6c656374696f6e3d226d695f61737369676e6565735f7461736b5f6d616e616765725f7369676e2220666c6f7761626c653a656c656d656e745661726961626c653d2261737369676e6565223e0a20202020202020203c636f6d706c6574696f6e436f6e646974696f6e3e247b6e724f66436f6d706c65746564496e7374616e636573203d3d206e724f66496e7374616e636573207c7c206e724f66436f6d706c65746564496e7374616e636573202a20313030202667743b3d206e724f66496e7374616e636573202a203130307d3c2f636f6d706c6574696f6e436f6e646974696f6e3e0a2020202020203c2f6d756c7469496e7374616e63654c6f6f704368617261637465726973746963733e0a202020203c2f757365725461736b3e0a202020203c73657175656e6365466c6f772069643d22666c6f775f7461736b5f6d616e616765725f7369676e2220736f757263655265663d227461736b5f7370656369616c69737422207461726765745265663d227461736b5f6d616e616765725f7369676e223e3c2f73657175656e6365466c6f773e0a202020203c656e644576656e742069643d22656e645f7461736b5f6d616e616765725f7369676e22206e616d653d22e7bb93e69d9f223e3c2f656e644576656e743e0a202020203c73657175656e6365466c6f772069643d22666c6f775f656e645f7461736b5f6d616e616765725f7369676e2220736f757263655265663d227461736b5f6d616e616765725f7369676e22207461726765745265663d22656e645f7461736b5f6d616e616765725f7369676e223e3c2f73657175656e6365466c6f773e0a20203c2f70726f636573733e0a20203c62706d6e64693a42504d4e4469616772616d2069643d2242504d4e4469616772616d5f616c6572745f666972655f736d6f6b65223e0a202020203c62706d6e64693a42504d4e506c616e652062706d6e456c656d656e743d22616c6572745f666972655f736d6f6b65222069643d2242504d4e506c616e655f616c6572745f666972655f736d6f6b65223e3c2f62706d6e64693a42504d4e506c616e653e0a20203c2f62706d6e64693a42504d4e4469616772616d3e0a3c2f646566696e6974696f6e733e	f
50bbd08b-a2a7-11f1-ae25-fe31f4546ab1	4	source	\N	\\x7b226e616d65223a22e7839fe6849fe781abe68385e5918ae8ada6e5a484e79086222c226964223a22726f6f74222c2274797065223a302c226368696c644e6f6465223a7b226964223a2273746172745f757365725f31222c2274797065223a31302c226e616d65223a22e58f91e8b5b7e4baba222c2273686f7754657874223a6e756c6c2c226368696c644e6f6465223a7b226964223a227461736b5f7370656369616c697374222c2274797065223a31312c226e616d65223a22e5ae89e585a8e4b893e59198e5889de5aea1222c2273686f7754657874223a6e756c6c2c2263616e6469646174655374726174656779223a33302c2263616e646964617465506172616d223a2231222c22617070726f76654d6574686f64223a332c22726561736f6e52657175697265223a66616c73652c226368696c644e6f6465223a7b226964223a227461736b5f6d616e616765725f7369676e222c2274797065223a31312c226e616d65223a22e4b8bbe7aea1e4bc9ae7adbee7a1aee8aea4222c2273686f7754657874223a6e756c6c2c2263616e6469646174655374726174656779223a33302c2263616e646964617465506172616d223a22312c313034222c22617070726f76654d6574686f64223a322c22617070726f7665526174696f223a3130302c22726561736f6e52657175697265223a747275652c2272656a65637448616e646c6572223a7b2274797065223a322c2272657475726e4e6f64654964223a227461736b5f7370656369616c697374227d2c226368696c644e6f6465223a6e756c6c7d7d7d7d	\N
a033e680-a2a7-11f1-ae25-fe31f4546ab1	1	alert_fire_smoke.bpmn	a033e67f-a2a7-11f1-ae25-fe31f4546ab1	\\x3c3f786d6c2076657273696f6e3d22312e302220656e636f64696e673d225554462d38223f3e0a3c646566696e6974696f6e7320786d6c6e733d22687474703a2f2f7777772e6f6d672e6f72672f737065632f42504d4e2f32303130303532342f4d4f44454c2220786d6c6e733a7873693d22687474703a2f2f7777772e77332e6f72672f323030312f584d4c536368656d612d696e7374616e63652220786d6c6e733a7873643d22687474703a2f2f7777772e77332e6f72672f323030312f584d4c536368656d612220786d6c6e733a666c6f7761626c653d22687474703a2f2f666c6f7761626c652e6f72672f62706d6e2220786d6c6e733a62706d6e64693d22687474703a2f2f7777772e6f6d672e6f72672f737065632f42504d4e2f32303130303532342f44492220786d6c6e733a6f6d6764633d22687474703a2f2f7777772e6f6d672e6f72672f737065632f44442f32303130303532342f44432220786d6c6e733a6f6d6764693d22687474703a2f2f7777772e6f6d672e6f72672f737065632f44442f32303130303532342f44492220747970654c616e67756167653d22687474703a2f2f7777772e77332e6f72672f323030312f584d4c536368656d61222065787072657373696f6e4c616e67756167653d22687474703a2f2f7777772e77332e6f72672f313939392f585061746822207461726765744e616d6573706163653d22616c6572745f68616e646c65223e0a20203c70726f636573732069643d22616c6572745f666972655f736d6f6b6522206e616d653d22e7839fe6849fe781abe68385e5918ae8ada6e5a484e790862220697345786563757461626c653d2274727565223e0a202020203c73746172744576656e742069643d2273746172745f6576656e7422206e616d653d22e5bc80e5a78b223e3c2f73746172744576656e743e0a202020203c757365725461736b2069643d227461736b5f7370656369616c69737422206e616d653d22e5ae89e585a8e4b893e59198e5889de5aea1223e0a2020202020203c657874656e73696f6e456c656d656e74733e0a20202020202020203c666c6f7761626c653a63616e646964617465436f6e6620786d6c6e733a666c6f7761626c653d22687474703a2f2f666c6f7761626c652e6f72672f62706d6e2220666c6f7761626c653a63616e64696461746553747261746567793d2233302220666c6f7761626c653a63616e646964617465506172616d3d22312220666c6f7761626c653a617070726f76654d6574686f643d22332220666c6f7761626c653a726561736f6e526571756972653d2266616c7365223e3c2f666c6f7761626c653a63616e646964617465436f6e663e0a2020202020203c2f657874656e73696f6e456c656d656e74733e0a202020203c2f757365725461736b3e0a202020203c73657175656e6365466c6f772069643d22666c6f775f7461736b5f7370656369616c6973742220736f757263655265663d2273746172745f6576656e7422207461726765745265663d227461736b5f7370656369616c697374223e3c2f73657175656e6365466c6f773e0a202020203c757365725461736b2069643d227461736b5f6d616e616765725f7369676e22206e616d653d22e4b8bbe7aea1e4bc9ae7adbee7a1aee8aea42220666c6f7761626c653a61737369676e65653d22247b61737369676e65657d223e0a2020202020203c657874656e73696f6e456c656d656e74733e0a20202020202020203c666c6f7761626c653a63616e646964617465436f6e6620786d6c6e733a666c6f7761626c653d22687474703a2f2f666c6f7761626c652e6f72672f62706d6e2220666c6f7761626c653a63616e64696461746553747261746567793d2233302220666c6f7761626c653a63616e646964617465506172616d3d22312c3130302220666c6f7761626c653a617070726f76654d6574686f643d22322220666c6f7761626c653a617070726f7665526174696f3d223130302220666c6f7761626c653a726561736f6e526571756972653d22747275652220666c6f7761626c653a72656a65637448616e646c6572547970653d22322220666c6f7761626c653a72656a65637452657475726e4e6f646549643d227461736b5f7370656369616c697374223e3c2f666c6f7761626c653a63616e646964617465436f6e663e0a2020202020203c2f657874656e73696f6e456c656d656e74733e0a2020202020203c6d756c7469496e7374616e63654c6f6f7043686172616374657269737469637320697353657175656e7469616c3d2266616c73652220666c6f7761626c653a636f6c6c656374696f6e3d226d695f61737369676e6565735f7461736b5f6d616e616765725f7369676e2220666c6f7761626c653a656c656d656e745661726961626c653d2261737369676e6565223e0a20202020202020203c636f6d706c6574696f6e436f6e646974696f6e3e247b6e724f66436f6d706c65746564496e7374616e636573203d3d206e724f66496e7374616e636573207c7c206e724f66436f6d706c65746564496e7374616e636573202a20313030202667743b3d206e724f66496e7374616e636573202a203130307d3c2f636f6d706c6574696f6e436f6e646974696f6e3e0a2020202020203c2f6d756c7469496e7374616e63654c6f6f704368617261637465726973746963733e0a202020203c2f757365725461736b3e0a202020203c73657175656e6365466c6f772069643d22666c6f775f7461736b5f6d616e616765725f7369676e2220736f757263655265663d227461736b5f7370656369616c69737422207461726765745265663d227461736b5f6d616e616765725f7369676e223e3c2f73657175656e6365466c6f773e0a202020203c656e644576656e742069643d22656e645f7461736b5f6d616e616765725f7369676e22206e616d653d22e7bb93e69d9f223e3c2f656e644576656e743e0a202020203c73657175656e6365466c6f772069643d22666c6f775f656e645f7461736b5f6d616e616765725f7369676e2220736f757263655265663d227461736b5f6d616e616765725f7369676e22207461726765745265663d22656e645f7461736b5f6d616e616765725f7369676e223e3c2f73657175656e6365466c6f773e0a20203c2f70726f636573733e0a20203c62706d6e64693a42504d4e4469616772616d2069643d2242504d4e4469616772616d5f616c6572745f666972655f736d6f6b65223e0a202020203c62706d6e64693a42504d4e506c616e652062706d6e456c656d656e743d22616c6572745f666972655f736d6f6b65222069643d2242504d4e506c616e655f616c6572745f666972655f736d6f6b65223e3c2f62706d6e64693a42504d4e506c616e653e0a20203c2f62706d6e64693a42504d4e4469616772616d3e0a3c2f646566696e6974696f6e733e	f
b49b715f-a2a7-11f1-ae25-fe31f4546ab1	1	hist.var-mi_assignees_task_manager_sign	\N	\\xaced0005737200136a6176612e7574696c2e41727261794c6973747881d21d99c7619d03000149000473697a657870000000017704000000017372000e6a6176612e6c616e672e4c6f6e673b8be490cc8f23df0200014a000576616c7565787200106a6176612e6c616e672e4e756d62657286ac951d0b94e08b0200007870000000000000000178	\N
b4a5d1b8-a2a7-11f1-ae25-fe31f4546ab1	1	var-mi_assignees_task_manager_sign	\N	\\xaced0005737200136a6176612e7574696c2e41727261794c6973747881d21d99c7619d03000149000473697a657870000000017704000000017372000e6a6176612e6c616e672e4c6f6e673b8be490cc8f23df0200014a000576616c7565787200106a6176612e6c616e672e4e756d62657286ac951d0b94e08b0200007870000000000000000178	\N
b4a5d1ba-a2a7-11f1-ae25-fe31f4546ab1	1	hist.var-mi_assignees_task_manager_sign	\N	\\xaced0005737200136a6176612e7574696c2e41727261794c6973747881d21d99c7619d03000149000473697a657870000000017704000000017372000e6a6176612e6c616e672e4c6f6e673b8be490cc8f23df0200014a000576616c7565787200106a6176612e6c616e672e4e756d62657286ac951d0b94e08b0200007870000000000000000178	\N
202bc1bc-a2a8-11f1-ae25-fe31f4546ab1	1	alert_fire_smoke.bpmn	202bc1bb-a2a8-11f1-ae25-fe31f4546ab1	\\x3c3f786d6c2076657273696f6e3d22312e302220656e636f64696e673d225554462d38223f3e0a3c646566696e6974696f6e7320786d6c6e733d22687474703a2f2f7777772e6f6d672e6f72672f737065632f42504d4e2f32303130303532342f4d4f44454c2220786d6c6e733a7873693d22687474703a2f2f7777772e77332e6f72672f323030312f584d4c536368656d612d696e7374616e63652220786d6c6e733a7873643d22687474703a2f2f7777772e77332e6f72672f323030312f584d4c536368656d612220786d6c6e733a666c6f7761626c653d22687474703a2f2f666c6f7761626c652e6f72672f62706d6e2220786d6c6e733a62706d6e64693d22687474703a2f2f7777772e6f6d672e6f72672f737065632f42504d4e2f32303130303532342f44492220786d6c6e733a6f6d6764633d22687474703a2f2f7777772e6f6d672e6f72672f737065632f44442f32303130303532342f44432220786d6c6e733a6f6d6764693d22687474703a2f2f7777772e6f6d672e6f72672f737065632f44442f32303130303532342f44492220747970654c616e67756167653d22687474703a2f2f7777772e77332e6f72672f323030312f584d4c536368656d61222065787072657373696f6e4c616e67756167653d22687474703a2f2f7777772e77332e6f72672f313939392f585061746822207461726765744e616d6573706163653d22616c6572745f68616e646c65223e0a20203c70726f636573732069643d22616c6572745f666972655f736d6f6b6522206e616d653d22e7839fe6849fe781abe68385e5918ae8ada6e5a484e790862220697345786563757461626c653d2274727565223e0a202020203c73746172744576656e742069643d2273746172745f6576656e7422206e616d653d22e5bc80e5a78b223e3c2f73746172744576656e743e0a202020203c757365725461736b2069643d227461736b5f7370656369616c69737422206e616d653d22e5ae89e585a8e4b893e59198e5889de5aea1223e0a2020202020203c657874656e73696f6e456c656d656e74733e0a20202020202020203c666c6f7761626c653a63616e646964617465436f6e6620786d6c6e733a666c6f7761626c653d22687474703a2f2f666c6f7761626c652e6f72672f62706d6e2220666c6f7761626c653a63616e64696461746553747261746567793d2233302220666c6f7761626c653a63616e646964617465506172616d3d22312220666c6f7761626c653a617070726f76654d6574686f643d22332220666c6f7761626c653a726561736f6e526571756972653d2266616c7365223e3c2f666c6f7761626c653a63616e646964617465436f6e663e0a2020202020203c2f657874656e73696f6e456c656d656e74733e0a202020203c2f757365725461736b3e0a202020203c73657175656e6365466c6f772069643d22666c6f775f7461736b5f7370656369616c6973742220736f757263655265663d2273746172745f6576656e7422207461726765745265663d227461736b5f7370656369616c697374223e3c2f73657175656e6365466c6f773e0a202020203c757365725461736b2069643d227461736b5f6d616e616765725f7369676e22206e616d653d22e4b8bbe7aea1e4bc9ae7adbee7a1aee8aea42220666c6f7761626c653a61737369676e65653d22247b61737369676e65657d223e0a2020202020203c657874656e73696f6e456c656d656e74733e0a20202020202020203c666c6f7761626c653a63616e646964617465436f6e6620786d6c6e733a666c6f7761626c653d22687474703a2f2f666c6f7761626c652e6f72672f62706d6e2220666c6f7761626c653a63616e64696461746553747261746567793d2233302220666c6f7761626c653a63616e646964617465506172616d3d22312c3130342220666c6f7761626c653a617070726f76654d6574686f643d22322220666c6f7761626c653a617070726f7665526174696f3d223130302220666c6f7761626c653a726561736f6e526571756972653d22747275652220666c6f7761626c653a72656a65637448616e646c6572547970653d22322220666c6f7761626c653a72656a65637452657475726e4e6f646549643d227461736b5f7370656369616c697374223e3c2f666c6f7761626c653a63616e646964617465436f6e663e0a2020202020203c2f657874656e73696f6e456c656d656e74733e0a2020202020203c6d756c7469496e7374616e63654c6f6f7043686172616374657269737469637320697353657175656e7469616c3d2266616c73652220666c6f7761626c653a636f6c6c656374696f6e3d226d695f61737369676e6565735f7461736b5f6d616e616765725f7369676e2220666c6f7761626c653a656c656d656e745661726961626c653d2261737369676e6565223e0a20202020202020203c636f6d706c6574696f6e436f6e646974696f6e3e247b6e724f66436f6d706c65746564496e7374616e636573203d3d206e724f66496e7374616e636573207c7c206e724f66436f6d706c65746564496e7374616e636573202a20313030202667743b3d206e724f66496e7374616e636573202a203130307d3c2f636f6d706c6574696f6e436f6e646974696f6e3e0a2020202020203c2f6d756c7469496e7374616e63654c6f6f704368617261637465726973746963733e0a202020203c2f757365725461736b3e0a202020203c73657175656e6365466c6f772069643d22666c6f775f7461736b5f6d616e616765725f7369676e2220736f757263655265663d227461736b5f7370656369616c69737422207461726765745265663d227461736b5f6d616e616765725f7369676e223e3c2f73657175656e6365466c6f773e0a202020203c656e644576656e742069643d22656e645f7461736b5f6d616e616765725f7369676e22206e616d653d22e7bb93e69d9f223e3c2f656e644576656e743e0a202020203c73657175656e6365466c6f772069643d22666c6f775f656e645f7461736b5f6d616e616765725f7369676e2220736f757263655265663d227461736b5f6d616e616765725f7369676e22207461726765745265663d22656e645f7461736b5f6d616e616765725f7369676e223e3c2f73657175656e6365466c6f773e0a20203c2f70726f636573733e0a20203c62706d6e64693a42504d4e4469616772616d2069643d2242504d4e4469616772616d5f616c6572745f666972655f736d6f6b65223e0a202020203c62706d6e64693a42504d4e506c616e652062706d6e456c656d656e743d22616c6572745f666972655f736d6f6b65222069643d2242504d4e506c616e655f616c6572745f666972655f736d6f6b65223e3c2f62706d6e64693a42504d4e506c616e653e0a20203c2f62706d6e64693a42504d4e4469616772616d3e0a3c2f646566696e6974696f6e733e	f
27192221-a2a8-11f1-ae25-fe31f4546ab1	1	var-mi_assignees_task_manager_sign	\N	\\xaced0005737200136a6176612e7574696c2e41727261794c6973747881d21d99c7619d03000149000473697a657870000000027704000000027372000e6a6176612e6c616e672e4c6f6e673b8be490cc8f23df0200014a000576616c7565787200106a6176612e6c616e672e4e756d62657286ac951d0b94e08b020000787000000000000000017371007e0002000000000000006878	\N
27192223-a2a8-11f1-ae25-fe31f4546ab1	1	hist.var-mi_assignees_task_manager_sign	\N	\\xaced0005737200136a6176612e7574696c2e41727261794c6973747881d21d99c7619d03000149000473697a657870000000027704000000027372000e6a6176612e6c616e672e4c6f6e673b8be490cc8f23df0200014a000576616c7565787200106a6176612e6c616e672e4e756d62657286ac951d0b94e08b020000787000000000000000017371007e0002000000000000006878	\N
\.


--
-- Data for Name: act_ge_property; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.act_ge_property (name_, value_, rev_) FROM stdin;
common.schema.version	6.8.0.0	1
next.dbid	1	1
identitylink.schema.version	6.8.0.0	1
entitylink.schema.version	6.8.0.0	1
eventsubscription.schema.version	6.8.0.0	1
task.schema.version	6.8.0.0	1
variable.schema.version	6.8.0.0	1
job.schema.version	6.8.0.0	1
batch.schema.version	6.8.0.0	1
schema.version	6.8.0.0	1
schema.history	create(6.8.0.0)	1
cfg.execution-related-entities-count	true	1
cfg.task-related-entities-count	true	1
\.


--
-- Data for Name: act_hi_actinst; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.act_hi_actinst (id_, rev_, proc_def_id_, proc_inst_id_, execution_id_, act_id_, task_id_, call_proc_inst_id_, act_name_, act_type_, assignee_, start_time_, end_time_, transaction_order_, duration_, delete_reason_, tenant_id_) FROM stdin;
3dba5c2e-a29b-11f1-8fa2-aefacda18209	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	3dba0e09-a29b-11f1-8fa2-aefacda18209	3dba5c2d-a29b-11f1-8fa2-aefacda18209	start_event	\N	\N	开始	startEvent	\N	2026-08-28 12:45:06.446	2026-08-28 12:45:06.447	1	1	\N	
3dbad15f-a29b-11f1-8fa2-aefacda18209	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	3dba0e09-a29b-11f1-8fa2-aefacda18209	3dba5c2d-a29b-11f1-8fa2-aefacda18209	flow_task_1	\N	\N	\N	sequenceFlow	\N	2026-08-28 12:45:06.448	2026-08-28 12:45:06.448	2	0	\N	
59c13207-a29b-11f1-8fa2-aefacda18209	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	3dba0e09-a29b-11f1-8fa2-aefacda18209	3dba5c2d-a29b-11f1-8fa2-aefacda18209	flow_end_1	\N	\N	\N	sequenceFlow	\N	2026-08-28 12:45:53.466	2026-08-28 12:45:53.466	1	0	\N	
59c15918-a29b-11f1-8fa2-aefacda18209	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	3dba0e09-a29b-11f1-8fa2-aefacda18209	3dba5c2d-a29b-11f1-8fa2-aefacda18209	end_1	\N	\N	结束	endEvent	\N	2026-08-28 12:45:53.467	2026-08-28 12:45:53.469	2	2	\N	
3dbad160-a29b-11f1-8fa2-aefacda18209	2	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	3dba0e09-a29b-11f1-8fa2-aefacda18209	3dba5c2d-a29b-11f1-8fa2-aefacda18209	task_1	3dbc30f1-a29b-11f1-8fa2-aefacda18209	\N	审批人	userTask	\N	2026-08-28 12:45:06.448	2026-08-28 12:45:53.466	3	47018	\N	
68bb939e-a29b-11f1-8fa2-aefacda18209	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	68bb9399-a29b-11f1-8fa2-aefacda18209	68bb939d-a29b-11f1-8fa2-aefacda18209	start_event	\N	\N	开始	startEvent	\N	2026-08-28 12:46:18.595	2026-08-28 12:46:18.595	1	0	\N	
68bb939f-a29b-11f1-8fa2-aefacda18209	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	68bb9399-a29b-11f1-8fa2-aefacda18209	68bb939d-a29b-11f1-8fa2-aefacda18209	flow_task_1	\N	\N	\N	sequenceFlow	\N	2026-08-28 12:46:18.595	2026-08-28 12:46:18.595	2	0	\N	
68bb93a0-a29b-11f1-8fa2-aefacda18209	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	68bb9399-a29b-11f1-8fa2-aefacda18209	68bb939d-a29b-11f1-8fa2-aefacda18209	task_1	68bbbab1-a29b-11f1-8fa2-aefacda18209	\N	审批人	userTask	\N	2026-08-28 12:46:18.595	\N	3	\N	\N	
b1b00791-a29b-11f1-9eaa-aefacda18209	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	b1afb96c-a29b-11f1-9eaa-aefacda18209	b1b00790-a29b-11f1-9eaa-aefacda18209	start_event	\N	\N	开始	startEvent	\N	2026-08-28 12:48:20.993	2026-08-28 12:48:20.994	1	1	\N	
b1b055b2-a29b-11f1-9eaa-aefacda18209	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	b1afb96c-a29b-11f1-9eaa-aefacda18209	b1b00790-a29b-11f1-9eaa-aefacda18209	flow_task_1	\N	\N	\N	sequenceFlow	\N	2026-08-28 12:48:20.995	2026-08-28 12:48:20.995	2	0	\N	
3dc2a458-a29c-11f1-9eaa-aefacda18209	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	3dc27d39-a29c-11f1-9eaa-aefacda18209	3dc2a457-a29c-11f1-9eaa-aefacda18209	start_event	\N	\N	开始	startEvent	\N	2026-08-28 12:52:15.996	2026-08-28 12:52:15.997	1	1	\N	
3dc2cb69-a29c-11f1-9eaa-aefacda18209	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	3dc27d39-a29c-11f1-9eaa-aefacda18209	3dc2a457-a29c-11f1-9eaa-aefacda18209	flow_task_1	\N	\N	\N	sequenceFlow	\N	2026-08-28 12:52:15.997	2026-08-28 12:52:15.997	2	0	\N	
4c8cf541-a29c-11f1-9eaa-aefacda18209	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	3dc27d39-a29c-11f1-9eaa-aefacda18209	3dc2a457-a29c-11f1-9eaa-aefacda18209	flow_end_1	\N	\N	\N	sequenceFlow	\N	2026-08-28 12:52:40.81	2026-08-28 12:52:40.81	1	0	\N	
4c8cf542-a29c-11f1-9eaa-aefacda18209	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	3dc27d39-a29c-11f1-9eaa-aefacda18209	3dc2a457-a29c-11f1-9eaa-aefacda18209	end_1	\N	\N	结束	endEvent	\N	2026-08-28 12:52:40.81	2026-08-28 12:52:40.811	2	1	\N	
3dc2cb6a-a29c-11f1-9eaa-aefacda18209	2	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	3dc27d39-a29c-11f1-9eaa-aefacda18209	3dc2a457-a29c-11f1-9eaa-aefacda18209	task_1	3dc2cb6b-a29c-11f1-9eaa-aefacda18209	\N	审批人	userTask	\N	2026-08-28 12:52:15.997	2026-08-28 12:52:40.809	3	24812	\N	
7a1b8e24-a29c-11f1-90a8-aefacda18209	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	7a1b6706-a29c-11f1-90a8-aefacda18209	7a1b8e23-a29c-11f1-90a8-aefacda18209	start_event	\N	\N	开始	startEvent	\N	2026-08-28 12:53:57.242	2026-08-28 12:53:57.244	1	2	\N	
7a1bdc45-a29c-11f1-90a8-aefacda18209	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	7a1b6706-a29c-11f1-90a8-aefacda18209	7a1b8e23-a29c-11f1-90a8-aefacda18209	flow_task_1	\N	\N	\N	sequenceFlow	\N	2026-08-28 12:53:57.244	2026-08-28 12:53:57.244	2	0	\N	
7d41864d-a29c-11f1-90a8-aefacda18209	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	7a1b6706-a29c-11f1-90a8-aefacda18209	7a1b8e23-a29c-11f1-90a8-aefacda18209	flow_end_1	\N	\N	\N	sequenceFlow	\N	2026-08-28 12:54:02.524	2026-08-28 12:54:02.524	1	0	\N	
7d41ad5e-a29c-11f1-90a8-aefacda18209	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	7a1b6706-a29c-11f1-90a8-aefacda18209	7a1b8e23-a29c-11f1-90a8-aefacda18209	end_1	\N	\N	结束	endEvent	\N	2026-08-28 12:54:02.525	2026-08-28 12:54:02.528	2	3	\N	
7a1c0356-a29c-11f1-90a8-aefacda18209	2	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	7a1b6706-a29c-11f1-90a8-aefacda18209	7a1b8e23-a29c-11f1-90a8-aefacda18209	task_1	7a1d89f7-a29c-11f1-90a8-aefacda18209	\N	审批人	userTask	\N	2026-08-28 12:53:57.245	2026-08-28 12:54:02.523	3	5278	\N	
623f6419-a29e-11f1-befa-02ee22a453e8	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	b1afb96c-a29b-11f1-9eaa-aefacda18209	b1b00790-a29b-11f1-9eaa-aefacda18209	flow_end_1	\N	\N	\N	sequenceFlow	\N	2026-08-28 13:07:36.205	2026-08-28 13:07:36.205	1	0	\N	
623f8b2a-a29e-11f1-befa-02ee22a453e8	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	b1afb96c-a29b-11f1-9eaa-aefacda18209	b1b00790-a29b-11f1-9eaa-aefacda18209	end_1	\N	\N	结束	endEvent	\N	2026-08-28 13:07:36.206	2026-08-28 13:07:36.207	2	1	\N	
b1b055b3-a29b-11f1-9eaa-aefacda18209	2	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	b1afb96c-a29b-11f1-9eaa-aefacda18209	b1b00790-a29b-11f1-9eaa-aefacda18209	task_1	b1b1dc54-a29b-11f1-9eaa-aefacda18209	\N	审批人	userTask	\N	2026-08-28 12:48:20.995	2026-08-28 13:07:36.204	3	1155209	\N	
b4175c1d-a2a1-11f1-aee5-5a91bd373cd1	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	b4173508-a2a1-11f1-aee5-5a91bd373cd1	b4175c1c-a2a1-11f1-aee5-5a91bd373cd1	start_event	\N	\N	开始	startEvent	\N	2026-08-28 13:31:22.006	2026-08-28 13:31:22.008	1	2	\N	
b417d14e-a2a1-11f1-aee5-5a91bd373cd1	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	b4173508-a2a1-11f1-aee5-5a91bd373cd1	b4175c1c-a2a1-11f1-aee5-5a91bd373cd1	flow_task_1	\N	\N	\N	sequenceFlow	\N	2026-08-28 13:31:22.009	2026-08-28 13:31:22.009	2	0	\N	
b417d14f-a2a1-11f1-aee5-5a91bd373cd1	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	b4173508-a2a1-11f1-aee5-5a91bd373cd1	b4175c1c-a2a1-11f1-aee5-5a91bd373cd1	task_1	b418e2c0-a2a1-11f1-aee5-5a91bd373cd1	\N	审批人	userTask	\N	2026-08-28 13:31:22.009	\N	3	\N	\N	
eccf2a77-a2a1-11f1-a0a7-f2ebdc74e900	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	eccedc52-a2a1-11f1-a0a7-f2ebdc74e900	eccf2a76-a2a1-11f1-a0a7-f2ebdc74e900	start_event	\N	\N	开始	startEvent	\N	2026-08-28 13:32:57.163	2026-08-28 13:32:57.165	1	2	\N	
eccf7898-a2a1-11f1-a0a7-f2ebdc74e900	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	eccedc52-a2a1-11f1-a0a7-f2ebdc74e900	eccf2a76-a2a1-11f1-a0a7-f2ebdc74e900	flow_task_1	\N	\N	\N	sequenceFlow	\N	2026-08-28 13:32:57.165	2026-08-28 13:32:57.165	2	0	\N	
eccf7899-a2a1-11f1-a0a7-f2ebdc74e900	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	eccedc52-a2a1-11f1-a0a7-f2ebdc74e900	eccf2a76-a2a1-11f1-a0a7-f2ebdc74e900	task_1	ecd0b11a-a2a1-11f1-a0a7-f2ebdc74e900	\N	审批人	userTask	\N	2026-08-28 13:32:57.165	\N	3	\N	\N	
0d755204-a2a2-11f1-a0a7-f2ebdc74e900	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	0d7551ff-a2a2-11f1-a0a7-f2ebdc74e900	0d755203-a2a2-11f1-a0a7-f2ebdc74e900	start_event	\N	\N	开始	startEvent	\N	2026-08-28 13:33:51.939	2026-08-28 13:33:51.939	1	0	\N	
0d755205-a2a2-11f1-a0a7-f2ebdc74e900	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	0d7551ff-a2a2-11f1-a0a7-f2ebdc74e900	0d755203-a2a2-11f1-a0a7-f2ebdc74e900	flow_task_1	\N	\N	\N	sequenceFlow	\N	2026-08-28 13:33:51.939	2026-08-28 13:33:51.939	2	0	\N	
0d755206-a2a2-11f1-a0a7-f2ebdc74e900	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	0d7551ff-a2a2-11f1-a0a7-f2ebdc74e900	0d755203-a2a2-11f1-a0a7-f2ebdc74e900	task_1	0d755207-a2a2-11f1-a0a7-f2ebdc74e900	\N	审批人	userTask	\N	2026-08-28 13:33:51.939	\N	3	\N	\N	
42983993-a2a2-11f1-a551-3a17ebed01a9	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	4298127d-a2a2-11f1-a551-3a17ebed01a9	42983992-a2a2-11f1-a551-3a17ebed01a9	start_event	\N	\N	开始	startEvent	\N	2026-08-28 13:35:21.087	2026-08-28 13:35:21.088	1	1	\N	
429887b4-a2a2-11f1-a551-3a17ebed01a9	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	4298127d-a2a2-11f1-a551-3a17ebed01a9	42983992-a2a2-11f1-a551-3a17ebed01a9	flow_task_1	\N	\N	\N	sequenceFlow	\N	2026-08-28 13:35:21.089	2026-08-28 13:35:21.089	2	0	\N	
ea92b26b-a2a2-11f1-a551-3a17ebed01a9	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	4298127d-a2a2-11f1-a551-3a17ebed01a9	42983992-a2a2-11f1-a551-3a17ebed01a9	flow_end_1	\N	\N	\N	sequenceFlow	\N	2026-08-28 13:40:02.908	2026-08-28 13:40:02.908	1	0	\N	
ea92b26c-a2a2-11f1-a551-3a17ebed01a9	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	4298127d-a2a2-11f1-a551-3a17ebed01a9	42983992-a2a2-11f1-a551-3a17ebed01a9	end_1	\N	\N	结束	endEvent	\N	2026-08-28 13:40:02.908	2026-08-28 13:40:02.91	2	2	\N	
429887b5-a2a2-11f1-a551-3a17ebed01a9	2	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	4298127d-a2a2-11f1-a551-3a17ebed01a9	42983992-a2a2-11f1-a551-3a17ebed01a9	task_1	429a0e56-a2a2-11f1-a551-3a17ebed01a9	\N	审批人	userTask	\N	2026-08-28 13:35:21.089	2026-08-28 13:40:02.907	3	281818	\N	
b47a7ba3-a2a7-11f1-ae25-fe31f4546ab1	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	b47a0662-a2a7-11f1-ae25-fe31f4546ab1	b47a7ba2-a2a7-11f1-ae25-fe31f4546ab1	start_event	\N	\N	开始	startEvent	\N	2026-08-28 14:14:19.636	2026-08-28 14:14:19.637	1	1	\N	
b47ac9c4-a2a7-11f1-ae25-fe31f4546ab1	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	b47a0662-a2a7-11f1-ae25-fe31f4546ab1	b47a7ba2-a2a7-11f1-ae25-fe31f4546ab1	flow_task_1	\N	\N	\N	sequenceFlow	\N	2026-08-28 14:14:19.638	2026-08-28 14:14:19.638	2	0	\N	
b487c22b-a2a7-11f1-ae25-fe31f4546ab1	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	b4879b0a-a2a7-11f1-ae25-fe31f4546ab1	b487c22a-a2a7-11f1-ae25-fe31f4546ab1	start_event	\N	\N	开始	startEvent	\N	2026-08-28 14:14:19.723	2026-08-28 14:14:19.723	1	0	\N	
b487c22c-a2a7-11f1-ae25-fe31f4546ab1	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	b4879b0a-a2a7-11f1-ae25-fe31f4546ab1	b487c22a-a2a7-11f1-ae25-fe31f4546ab1	flow_task_1	\N	\N	\N	sequenceFlow	\N	2026-08-28 14:14:19.723	2026-08-28 14:14:19.723	2	0	\N	
b48f3c53-a2a7-11f1-ae25-fe31f4546ab1	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	b48f1532-a2a7-11f1-ae25-fe31f4546ab1	b48f3c52-a2a7-11f1-ae25-fe31f4546ab1	start_event	\N	\N	开始	startEvent	\N	2026-08-28 14:14:19.772	2026-08-28 14:14:19.772	1	0	\N	
b48f3c54-a2a7-11f1-ae25-fe31f4546ab1	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	b48f1532-a2a7-11f1-ae25-fe31f4546ab1	b48f3c52-a2a7-11f1-ae25-fe31f4546ab1	flow_task_1	\N	\N	\N	sequenceFlow	\N	2026-08-28 14:14:19.772	2026-08-28 14:14:19.772	2	0	\N	
b49b987e-a2a7-11f1-ae25-fe31f4546ab1	1	alert_fire_smoke:2:a035bb41-a2a7-11f1-ae25-fe31f4546ab1	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	b49b987d-a2a7-11f1-ae25-fe31f4546ab1	start_event	\N	\N	开始	startEvent	\N	2026-08-28 14:14:19.853	2026-08-28 14:14:19.853	1	0	\N	
b49b987f-a2a7-11f1-ae25-fe31f4546ab1	1	alert_fire_smoke:2:a035bb41-a2a7-11f1-ae25-fe31f4546ab1	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	b49b987d-a2a7-11f1-ae25-fe31f4546ab1	flow_task_specialist	\N	\N	\N	sequenceFlow	\N	2026-08-28 14:14:19.853	2026-08-28 14:14:19.853	2	0	\N	
b4a5d1c9-a2a7-11f1-ae25-fe31f4546ab1	1	alert_fire_smoke:2:a035bb41-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	b4a5d1c8-a2a7-11f1-ae25-fe31f4546ab1	start_event	\N	\N	开始	startEvent	\N	2026-08-28 14:14:19.92	2026-08-28 14:14:19.92	1	0	\N	
b4a5d1ca-a2a7-11f1-ae25-fe31f4546ab1	1	alert_fire_smoke:2:a035bb41-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	b4a5d1c8-a2a7-11f1-ae25-fe31f4546ab1	flow_task_specialist	\N	\N	\N	sequenceFlow	\N	2026-08-28 14:14:19.92	2026-08-28 14:14:19.92	2	0	\N	
b4b33f61-a2a7-11f1-ae25-fe31f4546ab1	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	b4b33f60-a2a7-11f1-ae25-fe31f4546ab1	start_event	\N	\N	开始	startEvent	\N	2026-08-28 14:14:20.008	2026-08-28 14:14:20.008	1	0	\N	
b4b33f62-a2a7-11f1-ae25-fe31f4546ab1	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	b4b33f60-a2a7-11f1-ae25-fe31f4546ab1	flow_task_1	\N	\N	\N	sequenceFlow	\N	2026-08-28 14:14:20.008	2026-08-28 14:14:20.008	2	0	\N	
b48f3c55-a2a7-11f1-ae25-fe31f4546ab1	2	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	b48f1532-a2a7-11f1-ae25-fe31f4546ab1	b48f3c52-a2a7-11f1-ae25-fe31f4546ab1	task_1	b48f3c56-a2a7-11f1-ae25-fe31f4546ab1	\N	审批人	userTask	\N	2026-08-28 14:14:19.772	2026-08-28 14:15:08.107	3	48335	cancel:重复告警，与东门事件为同一人员，合并处理	
b487c22d-a2a7-11f1-ae25-fe31f4546ab1	3	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	b4879b0a-a2a7-11f1-ae25-fe31f4546ab1	b487c22a-a2a7-11f1-ae25-fe31f4546ab1	task_1	b487c22e-a2a7-11f1-ae25-fe31f4546ab1	\N	审批人	userTask	1	2026-08-28 14:14:19.723	2026-08-28 14:15:08.036	3	48313	reject:复核为误报：画面为动物轮廓，非人员闯入	
b4a5d1cb-a2a7-11f1-ae25-fe31f4546ab1	3	alert_fire_smoke:2:a035bb41-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	b4a5d1c8-a2a7-11f1-ae25-fe31f4546ab1	task_specialist	b4a5d1cc-a2a7-11f1-ae25-fe31f4546ab1	\N	安全专员初审	userTask	1	2026-08-28 14:14:19.92	2026-08-28 14:15:08.417	3	48497	\N	
b4b33f63-a2a7-11f1-ae25-fe31f4546ab1	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	b4b33f60-a2a7-11f1-ae25-fe31f4546ab1	task_1	b4b33f64-a2a7-11f1-ae25-fe31f4546ab1	\N	审批人	userTask	\N	2026-08-28 14:14:20.008	\N	3	\N	\N	
d145172b-a2a7-11f1-ae25-fe31f4546ab1	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	b47a0662-a2a7-11f1-ae25-fe31f4546ab1	b47a7ba2-a2a7-11f1-ae25-fe31f4546ab1	flow_end_1	\N	\N	\N	sequenceFlow	\N	2026-08-28 14:15:07.94	2026-08-28 14:15:07.94	1	0	\N	
d145172c-a2a7-11f1-ae25-fe31f4546ab1	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	b47a0662-a2a7-11f1-ae25-fe31f4546ab1	b47a7ba2-a2a7-11f1-ae25-fe31f4546ab1	end_1	\N	\N	结束	endEvent	\N	2026-08-28 14:15:07.94	2026-08-28 14:15:07.941	2	1	\N	
b47ac9c5-a2a7-11f1-ae25-fe31f4546ab1	3	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	b47a0662-a2a7-11f1-ae25-fe31f4546ab1	b47a7ba2-a2a7-11f1-ae25-fe31f4546ab1	task_1	b47b17e6-a2a7-11f1-ae25-fe31f4546ab1	\N	审批人	userTask	1	2026-08-28 14:14:19.638	2026-08-28 14:15:07.94	3	48302	\N	
d169dd47-a2a7-11f1-ae25-fe31f4546ab1	1	alert_fire_smoke:2:a035bb41-a2a7-11f1-ae25-fe31f4546ab1	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	b49b987d-a2a7-11f1-ae25-fe31f4546ab1	flow_task_manager_sign	\N	\N	\N	sequenceFlow	\N	2026-08-28 14:15:08.181	2026-08-28 14:15:08.181	1	0	\N	
b49b9880-a2a7-11f1-ae25-fe31f4546ab1	3	alert_fire_smoke:2:a035bb41-a2a7-11f1-ae25-fe31f4546ab1	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	b49b987d-a2a7-11f1-ae25-fe31f4546ab1	task_specialist	b49b9881-a2a7-11f1-ae25-fe31f4546ab1	\N	安全专员初审	userTask	1	2026-08-28 14:14:19.853	2026-08-28 14:15:08.181	3	48328	\N	
d177bf04-a2a7-11f1-ae25-fe31f4546ab1	1	alert_fire_smoke:2:a035bb41-a2a7-11f1-ae25-fe31f4546ab1	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	d177bf03-a2a7-11f1-ae25-fe31f4546ab1	flow_end_task_manager_sign	\N	\N	\N	sequenceFlow	\N	2026-08-28 14:15:08.272	2026-08-28 14:15:08.272	1	0	\N	
d177bf05-a2a7-11f1-ae25-fe31f4546ab1	1	alert_fire_smoke:2:a035bb41-a2a7-11f1-ae25-fe31f4546ab1	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	d177bf03-a2a7-11f1-ae25-fe31f4546ab1	end_task_manager_sign	\N	\N	结束	endEvent	\N	2026-08-28 14:15:08.272	2026-08-28 14:15:08.272	2	0	\N	
d16a2b6f-a2a7-11f1-ae25-fe31f4546ab1	2	alert_fire_smoke:2:a035bb41-a2a7-11f1-ae25-fe31f4546ab1	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	d16a2b6c-a2a7-11f1-ae25-fe31f4546ab1	task_manager_sign	d16a2b70-a2a7-11f1-ae25-fe31f4546ab1	\N	主管会签确认	userTask	1	2026-08-28 14:15:08.183	2026-08-28 14:15:08.266	2	83	\N	
d18ddf19-a2a7-11f1-ae25-fe31f4546ab1	1	alert_fire_smoke:2:a035bb41-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	b4a5d1c8-a2a7-11f1-ae25-fe31f4546ab1	flow_task_manager_sign	\N	\N	\N	sequenceFlow	\N	2026-08-28 14:15:08.417	2026-08-28 14:15:08.417	1	0	\N	
d19f4447-a2a7-11f1-ae25-fe31f4546ab1	1	alert_fire_smoke:2:a035bb41-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	d19f4446-a2a7-11f1-ae25-fe31f4546ab1	task_specialist	d19f4448-a2a7-11f1-ae25-fe31f4546ab1	\N	安全专员初审	userTask	\N	2026-08-28 14:15:08.531	\N	1	\N	\N	
d18ea271-a2a7-11f1-ae25-fe31f4546ab1	2	alert_fire_smoke:2:a035bb41-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	d18e7b5e-a2a7-11f1-ae25-fe31f4546ab1	task_manager_sign	d18ea272-a2a7-11f1-ae25-fe31f4546ab1	\N	主管会签确认	userTask	1	2026-08-28 14:15:08.422	2026-08-28 14:15:08.528	2	106	Change parent activity to task_specialist	
27192232-a2a8-11f1-ae25-fe31f4546ab1	1	alert_fire_smoke:3:202ef60d-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	27192231-a2a8-11f1-ae25-fe31f4546ab1	start_event	\N	\N	开始	startEvent	\N	2026-08-28 14:17:31.937	2026-08-28 14:17:31.937	1	0	\N	
27194943-a2a8-11f1-ae25-fe31f4546ab1	1	alert_fire_smoke:3:202ef60d-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	27192231-a2a8-11f1-ae25-fe31f4546ab1	flow_task_specialist	\N	\N	\N	sequenceFlow	\N	2026-08-28 14:17:31.937	2026-08-28 14:17:31.937	2	0	\N	
2722e64a-a2a8-11f1-ae25-fe31f4546ab1	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	2722e649-a2a8-11f1-ae25-fe31f4546ab1	start_event	\N	\N	开始	startEvent	\N	2026-08-28 14:17:32	2026-08-28 14:17:32	1	0	\N	
2722e64b-a2a8-11f1-ae25-fe31f4546ab1	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	2722e649-a2a8-11f1-ae25-fe31f4546ab1	flow_task_1	\N	\N	\N	sequenceFlow	\N	2026-08-28 14:17:32	2026-08-28 14:17:32	2	0	\N	
2722e64c-a2a8-11f1-ae25-fe31f4546ab1	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	2722e649-a2a8-11f1-ae25-fe31f4546ab1	task_1	2722e64d-a2a8-11f1-ae25-fe31f4546ab1	\N	审批人	userTask	\N	2026-08-28 14:17:32	\N	3	\N	\N	
3160350e-a2a8-11f1-ae25-fe31f4546ab1	2	alert_fire_smoke:3:202ef60d-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	31603509-a2a8-11f1-ae25-fe31f4546ab1	task_manager_sign	3160350f-a2a8-11f1-ae25-fe31f4546ab1	\N	主管会签确认	userTask	1	2026-08-28 14:17:49.179	2026-08-28 14:17:49.291	2	112	\N	
31600df4-a2a8-11f1-ae25-fe31f4546ab1	1	alert_fire_smoke:3:202ef60d-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	27192231-a2a8-11f1-ae25-fe31f4546ab1	flow_task_manager_sign	\N	\N	\N	sequenceFlow	\N	2026-08-28 14:17:49.178	2026-08-28 14:17:49.178	1	0	\N	
31653e22-a2a8-11f1-ae25-fe31f4546ab1	1	alert_fire_smoke:3:202ef60d-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	3160350a-a2a8-11f1-ae25-fe31f4546ab1	task_manager_sign	31656533-a2a8-11f1-ae25-fe31f4546ab1	\N	主管会签确认	userTask	104	2026-08-28 14:17:49.212	\N	3	\N	\N	
27194944-a2a8-11f1-ae25-fe31f4546ab1	3	alert_fire_smoke:3:202ef60d-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	27192231-a2a8-11f1-ae25-fe31f4546ab1	task_specialist	27194945-a2a8-11f1-ae25-fe31f4546ab1	\N	安全专员初审	userTask	1	2026-08-28 14:17:31.937	2026-08-28 14:17:49.177	3	17240	\N	
40efd540-a2ac-11f1-83a4-6e81fb0021bd	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	40ef870f-a2ac-11f1-83a4-6e81fb0021bd	40efd53f-a2ac-11f1-83a4-6e81fb0021bd	start_event	\N	\N	开始	startEvent	\N	2026-08-28 14:46:53.273	2026-08-28 14:46:53.275	1	2	\N	
40f02361-a2ac-11f1-83a4-6e81fb0021bd	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	40ef870f-a2ac-11f1-83a4-6e81fb0021bd	40efd53f-a2ac-11f1-83a4-6e81fb0021bd	flow_task_1	\N	\N	\N	sequenceFlow	\N	2026-08-28 14:46:53.275	2026-08-28 14:46:53.275	2	0	\N	
48269aba-a2ac-11f1-83a4-6e81fb0021bd	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	40ef870f-a2ac-11f1-83a4-6e81fb0021bd	40efd53f-a2ac-11f1-83a4-6e81fb0021bd	flow_end_1	\N	\N	\N	sequenceFlow	\N	2026-08-28 14:47:05.376	2026-08-28 14:47:05.376	1	0	\N	
48269abb-a2ac-11f1-83a4-6e81fb0021bd	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	40ef870f-a2ac-11f1-83a4-6e81fb0021bd	40efd53f-a2ac-11f1-83a4-6e81fb0021bd	end_1	\N	\N	结束	endEvent	\N	2026-08-28 14:47:05.376	2026-08-28 14:47:05.377	2	1	\N	
40f02362-a2ac-11f1-83a4-6e81fb0021bd	3	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	40ef870f-a2ac-11f1-83a4-6e81fb0021bd	40efd53f-a2ac-11f1-83a4-6e81fb0021bd	task_1	40f10dc3-a2ac-11f1-83a4-6e81fb0021bd	\N	审批人	userTask	1	2026-08-28 14:46:53.275	2026-08-28 14:47:05.376	3	12101	\N	
\.


--
-- Data for Name: act_hi_attachment; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.act_hi_attachment (id_, rev_, user_id_, name_, description_, type_, task_id_, proc_inst_id_, url_, content_id_, time_) FROM stdin;
\.


--
-- Data for Name: act_hi_comment; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.act_hi_comment (id_, type_, time_, user_id_, task_id_, proc_inst_id_, action_, message_, full_msg_) FROM stdin;
3dbf1724-a29b-11f1-8fa2-aefacda18209	event	2026-08-28 12:45:06.476	1	3dbc30f1-a29b-11f1-8fa2-aefacda18209	\N	AddUserLink	1_|_candidate	\N
68bd4154-a29b-11f1-8fa2-aefacda18209	event	2026-08-28 12:46:18.606	1	68bbbab1-a29b-11f1-8fa2-aefacda18209	\N	AddUserLink	1_|_candidate	\N
b1b47467-a29b-11f1-9eaa-aefacda18209	event	2026-08-28 12:48:21.022	1	b1b1dc54-a29b-11f1-9eaa-aefacda18209	\N	AddUserLink	1_|_candidate	\N
3dc4c73e-a29c-11f1-9eaa-aefacda18209	event	2026-08-28 12:52:16.01	1	3dc2cb6b-a29c-11f1-9eaa-aefacda18209	\N	AddUserLink	1_|_candidate	\N
7a3111fa-a29c-11f1-90a8-aefacda18209	event	2026-08-28 12:53:57.383	1	7a1d89f7-a29c-11f1-90a8-aefacda18209	\N	AddUserLink	1_|_candidate	\N
b41c1713-a2a1-11f1-aee5-5a91bd373cd1	event	2026-08-28 13:31:22.037	1	b418e2c0-a2a1-11f1-aee5-5a91bd373cd1	\N	AddUserLink	1_|_candidate	\N
ecd3703d-a2a1-11f1-a0a7-f2ebdc74e900	event	2026-08-28 13:32:57.191	1	ecd0b11a-a2a1-11f1-a0a7-f2ebdc74e900	\N	AddUserLink	1_|_candidate	\N
0d763c6a-a2a2-11f1-a0a7-f2ebdc74e900	event	2026-08-28 13:33:51.945	1	0d755207-a2a2-11f1-a0a7-f2ebdc74e900	\N	AddUserLink	1_|_candidate	\N
429ccd79-a2a2-11f1-a551-3a17ebed01a9	event	2026-08-28 13:35:21.117	1	429a0e56-a2a2-11f1-a551-3a17ebed01a9	\N	AddUserLink	1_|_candidate	\N
b47c7779-a2a7-11f1-ae25-fe31f4546ab1	event	2026-08-28 14:14:19.649	1	b47b17e6-a2a7-11f1-ae25-fe31f4546ab1	\N	AddUserLink	1_|_candidate	\N
b4888581-a2a7-11f1-ae25-fe31f4546ab1	event	2026-08-28 14:14:19.728	1	b487c22e-a2a7-11f1-ae25-fe31f4546ab1	\N	AddUserLink	1_|_candidate	\N
b490ea09-a2a7-11f1-ae25-fe31f4546ab1	event	2026-08-28 14:14:19.783	1	b48f3c56-a2a7-11f1-ae25-fe31f4546ab1	\N	AddUserLink	1_|_candidate	\N
b49c34c4-a2a7-11f1-ae25-fe31f4546ab1	event	2026-08-28 14:14:19.857	1	b49b9881-a2a7-11f1-ae25-fe31f4546ab1	\N	AddUserLink	1_|_candidate	\N
b4a6e33f-a2a7-11f1-ae25-fe31f4546ab1	event	2026-08-28 14:14:19.927	1	b4a5d1cc-a2a7-11f1-ae25-fe31f4546ab1	\N	AddUserLink	1_|_candidate	\N
b4b402b7-a2a7-11f1-ae25-fe31f4546ab1	event	2026-08-28 14:14:20.013	1	b4b33f64-a2a7-11f1-ae25-fe31f4546ab1	\N	AddUserLink	1_|_candidate	\N
d1427f19-a2a7-11f1-ae25-fe31f4546ab1	event	2026-08-28 14:15:07.923	\N	b47b17e6-a2a7-11f1-ae25-fe31f4546ab1	\N	AddUserLink	1_|_assignee	\N
d151733e-a2a7-11f1-ae25-fe31f4546ab1	event	2026-08-28 14:15:08.021	\N	b487c22e-a2a7-11f1-ae25-fe31f4546ab1	\N	AddUserLink	1_|_assignee	\N
d168a4c5-a2a7-11f1-ae25-fe31f4546ab1	event	2026-08-28 14:15:08.173	\N	b49b9881-a2a7-11f1-ae25-fe31f4546ab1	\N	AddUserLink	1_|_assignee	\N
d18c3167-a2a7-11f1-ae25-fe31f4546ab1	event	2026-08-28 14:15:08.406	\N	b4a5d1cc-a2a7-11f1-ae25-fe31f4546ab1	\N	AddUserLink	1_|_assignee	\N
d1a0f1fa-a2a7-11f1-ae25-fe31f4546ab1	event	2026-08-28 14:15:08.542	\N	d19f4448-a2a7-11f1-ae25-fe31f4546ab1	\N	AddUserLink	1_|_candidate	\N
271a81c8-a2a8-11f1-ae25-fe31f4546ab1	event	2026-08-28 14:17:31.945	1	27194945-a2a8-11f1-ae25-fe31f4546ab1	\N	AddUserLink	1_|_candidate	\N
27246cf0-a2a8-11f1-ae25-fe31f4546ab1	event	2026-08-28 14:17:32.01	1	2722e64d-a2a8-11f1-ae25-fe31f4546ab1	\N	AddUserLink	1_|_candidate	\N
315f2392-a2a8-11f1-ae25-fe31f4546ab1	event	2026-08-28 14:17:49.172	\N	27194945-a2a8-11f1-ae25-fe31f4546ab1	\N	AddUserLink	1_|_assignee	\N
40f26d56-a2ac-11f1-83a4-6e81fb0021bd	event	2026-08-28 14:46:53.29	1	40f10dc3-a2ac-11f1-83a4-6e81fb0021bd	\N	AddUserLink	1_|_candidate	\N
4824ed08-a2ac-11f1-83a4-6e81fb0021bd	event	2026-08-28 14:47:05.365	\N	40f10dc3-a2ac-11f1-83a4-6e81fb0021bd	\N	AddUserLink	1_|_assignee	\N
\.


--
-- Data for Name: act_hi_detail; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.act_hi_detail (id_, type_, proc_inst_id_, execution_id_, task_id_, act_inst_id_, name_, var_type_, rev_, time_, bytearray_id_, double_, long_, text_, text2_) FROM stdin;
\.


--
-- Data for Name: act_hi_entitylink; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.act_hi_entitylink (id_, link_type_, create_time_, scope_id_, sub_scope_id_, scope_type_, scope_definition_id_, parent_element_id_, ref_scope_id_, ref_scope_type_, ref_scope_definition_id_, root_scope_id_, root_scope_type_, hierarchy_type_) FROM stdin;
\.


--
-- Data for Name: act_hi_identitylink; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.act_hi_identitylink (id_, group_id_, type_, user_id_, task_id_, create_time_, proc_inst_id_, scope_id_, sub_scope_id_, scope_type_, scope_definition_id_) FROM stdin;
3dba0e0a-a29b-11f1-8fa2-aefacda18209	\N	starter	1	\N	2026-08-28 12:45:06.444	3dba0e09-a29b-11f1-8fa2-aefacda18209	\N	\N	\N	\N
3dbf1722-a29b-11f1-8fa2-aefacda18209	\N	candidate	1	3dbc30f1-a29b-11f1-8fa2-aefacda18209	2026-08-28 12:45:06.476	\N	\N	\N	\N	\N
3dbf1723-a29b-11f1-8fa2-aefacda18209	\N	participant	1	\N	2026-08-28 12:45:06.476	3dba0e09-a29b-11f1-8fa2-aefacda18209	\N	\N	\N	\N
68bb939a-a29b-11f1-8fa2-aefacda18209	\N	starter	1	\N	2026-08-28 12:46:18.595	68bb9399-a29b-11f1-8fa2-aefacda18209	\N	\N	\N	\N
68bd4152-a29b-11f1-8fa2-aefacda18209	\N	candidate	1	68bbbab1-a29b-11f1-8fa2-aefacda18209	2026-08-28 12:46:18.606	\N	\N	\N	\N	\N
68bd4153-a29b-11f1-8fa2-aefacda18209	\N	participant	1	\N	2026-08-28 12:46:18.606	68bb9399-a29b-11f1-8fa2-aefacda18209	\N	\N	\N	\N
b1afe07d-a29b-11f1-9eaa-aefacda18209	\N	starter	1	\N	2026-08-28 12:48:20.992	b1afb96c-a29b-11f1-9eaa-aefacda18209	\N	\N	\N	\N
b1b44d55-a29b-11f1-9eaa-aefacda18209	\N	candidate	1	b1b1dc54-a29b-11f1-9eaa-aefacda18209	2026-08-28 12:48:21.021	\N	\N	\N	\N	\N
b1b47466-a29b-11f1-9eaa-aefacda18209	\N	participant	1	\N	2026-08-28 12:48:21.022	b1afb96c-a29b-11f1-9eaa-aefacda18209	\N	\N	\N	\N
3dc27d3a-a29c-11f1-9eaa-aefacda18209	\N	starter	1	\N	2026-08-28 12:52:15.995	3dc27d39-a29c-11f1-9eaa-aefacda18209	\N	\N	\N	\N
3dc4a02c-a29c-11f1-9eaa-aefacda18209	\N	candidate	1	3dc2cb6b-a29c-11f1-9eaa-aefacda18209	2026-08-28 12:52:16.009	\N	\N	\N	\N	\N
3dc4c73d-a29c-11f1-9eaa-aefacda18209	\N	participant	1	\N	2026-08-28 12:52:16.01	3dc27d39-a29c-11f1-9eaa-aefacda18209	\N	\N	\N	\N
7a1b6707-a29c-11f1-90a8-aefacda18209	\N	starter	1	\N	2026-08-28 12:53:57.241	7a1b6706-a29c-11f1-90a8-aefacda18209	\N	\N	\N	\N
7a3111f8-a29c-11f1-90a8-aefacda18209	\N	candidate	1	7a1d89f7-a29c-11f1-90a8-aefacda18209	2026-08-28 12:53:57.383	\N	\N	\N	\N	\N
7a3111f9-a29c-11f1-90a8-aefacda18209	\N	participant	1	\N	2026-08-28 12:53:57.383	7a1b6706-a29c-11f1-90a8-aefacda18209	\N	\N	\N	\N
b4173509-a2a1-11f1-aee5-5a91bd373cd1	\N	starter	1	\N	2026-08-28 13:31:22.005	b4173508-a2a1-11f1-aee5-5a91bd373cd1	\N	\N	\N	\N
b41bf001-a2a1-11f1-aee5-5a91bd373cd1	\N	candidate	1	b418e2c0-a2a1-11f1-aee5-5a91bd373cd1	2026-08-28 13:31:22.036	\N	\N	\N	\N	\N
b41c1712-a2a1-11f1-aee5-5a91bd373cd1	\N	participant	1	\N	2026-08-28 13:31:22.037	b4173508-a2a1-11f1-aee5-5a91bd373cd1	\N	\N	\N	\N
eccf0363-a2a1-11f1-a0a7-f2ebdc74e900	\N	starter	1	\N	2026-08-28 13:32:57.162	eccedc52-a2a1-11f1-a0a7-f2ebdc74e900	\N	\N	\N	\N
ecd3492b-a2a1-11f1-a0a7-f2ebdc74e900	\N	candidate	1	ecd0b11a-a2a1-11f1-a0a7-f2ebdc74e900	2026-08-28 13:32:57.19	\N	\N	\N	\N	\N
ecd3703c-a2a1-11f1-a0a7-f2ebdc74e900	\N	participant	1	\N	2026-08-28 13:32:57.191	eccedc52-a2a1-11f1-a0a7-f2ebdc74e900	\N	\N	\N	\N
0d755200-a2a2-11f1-a0a7-f2ebdc74e900	\N	starter	1	\N	2026-08-28 13:33:51.939	0d7551ff-a2a2-11f1-a0a7-f2ebdc74e900	\N	\N	\N	\N
0d763c68-a2a2-11f1-a0a7-f2ebdc74e900	\N	candidate	1	0d755207-a2a2-11f1-a0a7-f2ebdc74e900	2026-08-28 13:33:51.945	\N	\N	\N	\N	\N
0d763c69-a2a2-11f1-a0a7-f2ebdc74e900	\N	participant	1	\N	2026-08-28 13:33:51.945	0d7551ff-a2a2-11f1-a0a7-f2ebdc74e900	\N	\N	\N	\N
4298127e-a2a2-11f1-a551-3a17ebed01a9	\N	starter	1	\N	2026-08-28 13:35:21.086	4298127d-a2a2-11f1-a551-3a17ebed01a9	\N	\N	\N	\N
429ccd77-a2a2-11f1-a551-3a17ebed01a9	\N	candidate	1	429a0e56-a2a2-11f1-a551-3a17ebed01a9	2026-08-28 13:35:21.117	\N	\N	\N	\N	\N
429ccd78-a2a2-11f1-a551-3a17ebed01a9	\N	participant	1	\N	2026-08-28 13:35:21.117	4298127d-a2a2-11f1-a551-3a17ebed01a9	\N	\N	\N	\N
b47a2d73-a2a7-11f1-ae25-fe31f4546ab1	\N	starter	1	\N	2026-08-28 14:14:19.634	b47a0662-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N
b47c7777-a2a7-11f1-ae25-fe31f4546ab1	\N	candidate	1	b47b17e6-a2a7-11f1-ae25-fe31f4546ab1	2026-08-28 14:14:19.649	\N	\N	\N	\N	\N
b47c7778-a2a7-11f1-ae25-fe31f4546ab1	\N	participant	1	\N	2026-08-28 14:14:19.649	b47a0662-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N
b4879b0b-a2a7-11f1-ae25-fe31f4546ab1	\N	starter	1	\N	2026-08-28 14:14:19.722	b4879b0a-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N
b488857f-a2a7-11f1-ae25-fe31f4546ab1	\N	candidate	1	b487c22e-a2a7-11f1-ae25-fe31f4546ab1	2026-08-28 14:14:19.728	\N	\N	\N	\N	\N
b4888580-a2a7-11f1-ae25-fe31f4546ab1	\N	participant	1	\N	2026-08-28 14:14:19.728	b4879b0a-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N
b48f1533-a2a7-11f1-ae25-fe31f4546ab1	\N	starter	1	\N	2026-08-28 14:14:19.772	b48f1532-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N
b490ea07-a2a7-11f1-ae25-fe31f4546ab1	\N	candidate	1	b48f3c56-a2a7-11f1-ae25-fe31f4546ab1	2026-08-28 14:14:19.783	\N	\N	\N	\N	\N
b490ea08-a2a7-11f1-ae25-fe31f4546ab1	\N	participant	1	\N	2026-08-28 14:14:19.783	b48f1532-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N
b49afc2b-a2a7-11f1-ae25-fe31f4546ab1	\N	starter	1	\N	2026-08-28 14:14:19.849	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N
b49c34c2-a2a7-11f1-ae25-fe31f4546ab1	\N	candidate	1	b49b9881-a2a7-11f1-ae25-fe31f4546ab1	2026-08-28 14:14:19.857	\N	\N	\N	\N	\N
b49c34c3-a2a7-11f1-ae25-fe31f4546ab1	\N	participant	1	\N	2026-08-28 14:14:19.857	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N
b4a5aaa6-a2a7-11f1-ae25-fe31f4546ab1	\N	starter	1	\N	2026-08-28 14:14:19.919	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N
b4a6e33d-a2a7-11f1-ae25-fe31f4546ab1	\N	candidate	1	b4a5d1cc-a2a7-11f1-ae25-fe31f4546ab1	2026-08-28 14:14:19.927	\N	\N	\N	\N	\N
b4a6e33e-a2a7-11f1-ae25-fe31f4546ab1	\N	participant	1	\N	2026-08-28 14:14:19.927	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N
b4b31841-a2a7-11f1-ae25-fe31f4546ab1	\N	starter	1	\N	2026-08-28 14:14:20.007	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N
b4b3dba5-a2a7-11f1-ae25-fe31f4546ab1	\N	candidate	1	b4b33f64-a2a7-11f1-ae25-fe31f4546ab1	2026-08-28 14:14:20.013	\N	\N	\N	\N	\N
b4b402b6-a2a7-11f1-ae25-fe31f4546ab1	\N	participant	1	\N	2026-08-28 14:14:20.013	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N
d1427f18-a2a7-11f1-ae25-fe31f4546ab1	\N	assignee	1	b47b17e6-a2a7-11f1-ae25-fe31f4546ab1	2026-08-28 14:15:07.923	\N	\N	\N	\N	\N
d151733d-a2a7-11f1-ae25-fe31f4546ab1	\N	assignee	1	b487c22e-a2a7-11f1-ae25-fe31f4546ab1	2026-08-28 14:15:08.021	\N	\N	\N	\N	\N
d168a4c4-a2a7-11f1-ae25-fe31f4546ab1	\N	assignee	1	b49b9881-a2a7-11f1-ae25-fe31f4546ab1	2026-08-28 14:15:08.173	\N	\N	\N	\N	\N
d16a5181-a2a7-11f1-ae25-fe31f4546ab1	\N	assignee	1	d16a2b70-a2a7-11f1-ae25-fe31f4546ab1	2026-08-28 14:15:08.184	\N	\N	\N	\N	\N
d18be346-a2a7-11f1-ae25-fe31f4546ab1	\N	assignee	1	b4a5d1cc-a2a7-11f1-ae25-fe31f4546ab1	2026-08-28 14:15:08.404	\N	\N	\N	\N	\N
d18ea273-a2a7-11f1-ae25-fe31f4546ab1	\N	assignee	1	d18ea272-a2a7-11f1-ae25-fe31f4546ab1	2026-08-28 14:15:08.422	\N	\N	\N	\N	\N
d1a0cae9-a2a7-11f1-ae25-fe31f4546ab1	\N	candidate	1	d19f4448-a2a7-11f1-ae25-fe31f4546ab1	2026-08-28 14:15:08.541	\N	\N	\N	\N	\N
2718fb0f-a2a8-11f1-ae25-fe31f4546ab1	\N	starter	1	\N	2026-08-28 14:17:31.936	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N
271a81c6-a2a8-11f1-ae25-fe31f4546ab1	\N	candidate	1	27194945-a2a8-11f1-ae25-fe31f4546ab1	2026-08-28 14:17:31.945	\N	\N	\N	\N	\N
271a81c7-a2a8-11f1-ae25-fe31f4546ab1	\N	participant	1	\N	2026-08-28 14:17:31.945	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N
2722bf2a-a2a8-11f1-ae25-fe31f4546ab1	\N	starter	1	\N	2026-08-28 14:17:31.999	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N
27246cee-a2a8-11f1-ae25-fe31f4546ab1	\N	candidate	1	2722e64d-a2a8-11f1-ae25-fe31f4546ab1	2026-08-28 14:17:32.01	\N	\N	\N	\N	\N
27246cef-a2a8-11f1-ae25-fe31f4546ab1	\N	participant	1	\N	2026-08-28 14:17:32.01	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N
315f2391-a2a8-11f1-ae25-fe31f4546ab1	\N	assignee	1	27194945-a2a8-11f1-ae25-fe31f4546ab1	2026-08-28 14:17:49.172	\N	\N	\N	\N	\N
31603510-a2a8-11f1-ae25-fe31f4546ab1	\N	assignee	1	3160350f-a2a8-11f1-ae25-fe31f4546ab1	2026-08-28 14:17:49.179	\N	\N	\N	\N	\N
31656534-a2a8-11f1-ae25-fe31f4546ab1	\N	assignee	104	31656533-a2a8-11f1-ae25-fe31f4546ab1	2026-08-28 14:17:49.213	\N	\N	\N	\N	\N
31656535-a2a8-11f1-ae25-fe31f4546ab1	\N	participant	104	\N	2026-08-28 14:17:49.213	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N
40ef8710-a2ac-11f1-83a4-6e81fb0021bd	\N	starter	1	\N	2026-08-28 14:46:53.272	40ef870f-a2ac-11f1-83a4-6e81fb0021bd	\N	\N	\N	\N
40f26d54-a2ac-11f1-83a4-6e81fb0021bd	\N	candidate	1	40f10dc3-a2ac-11f1-83a4-6e81fb0021bd	2026-08-28 14:46:53.29	\N	\N	\N	\N	\N
40f26d55-a2ac-11f1-83a4-6e81fb0021bd	\N	participant	1	\N	2026-08-28 14:46:53.29	40ef870f-a2ac-11f1-83a4-6e81fb0021bd	\N	\N	\N	\N
48249ee7-a2ac-11f1-83a4-6e81fb0021bd	\N	assignee	1	40f10dc3-a2ac-11f1-83a4-6e81fb0021bd	2026-08-28 14:47:05.363	\N	\N	\N	\N	\N
\.


--
-- Data for Name: act_hi_procinst; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.act_hi_procinst (id_, rev_, proc_inst_id_, business_key_, proc_def_id_, start_time_, end_time_, duration_, start_user_id_, start_act_id_, end_act_id_, super_process_instance_id_, delete_reason_, tenant_id_, name_, callback_id_, callback_type_, reference_id_, reference_type_, propagated_stage_inst_id_, business_status_) FROM stdin;
b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	2	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	alert:40005	alert_fire_smoke:2:a035bb41-a2a7-11f1-ae25-fe31f4546ab1	2026-08-28 14:14:19.919	\N	\N	1	start_event	\N	\N	\N		烟感火情告警处理（告警#40005）	\N	\N	\N	\N	\N	\N
3dba0e09-a29b-11f1-8fa2-aefacda18209	3	3dba0e09-a29b-11f1-8fa2-aefacda18209	\N	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	2026-08-28 12:45:06.443	2026-08-28 12:45:53.482	47039	1	start_event	end_1	\N	\N		人员入侵告警处理	\N	\N	\N	\N	\N	\N
68bb9399-a29b-11f1-8fa2-aefacda18209	2	68bb9399-a29b-11f1-8fa2-aefacda18209	alert:10001	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	2026-08-28 12:46:18.595	\N	\N	1	start_event	\N	\N	\N		人员入侵告警处理（告警#10001）	\N	\N	\N	\N	\N	\N
b4b31840-a2a7-11f1-ae25-fe31f4546ab1	2	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	alert:40006	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	2026-08-28 14:14:20.007	\N	\N	1	start_event	\N	\N	\N		人员入侵告警处理（告警#40006）	\N	\N	\N	\N	\N	\N
3dc27d39-a29c-11f1-9eaa-aefacda18209	3	3dc27d39-a29c-11f1-9eaa-aefacda18209	alert:20001	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	2026-08-28 12:52:15.995	2026-08-28 12:52:40.836	24841	1	start_event	end_1	\N	\N		人员入侵告警处理（告警#20001）	\N	\N	\N	\N	\N	\N
b47a0662-a2a7-11f1-ae25-fe31f4546ab1	3	b47a0662-a2a7-11f1-ae25-fe31f4546ab1	alert:40001	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	2026-08-28 14:14:19.633	2026-08-28 14:15:07.954	48321	1	start_event	end_1	\N	\N		人员入侵告警处理（告警#40001）	\N	\N	\N	\N	\N	\N
7a1b6706-a29c-11f1-90a8-aefacda18209	3	7a1b6706-a29c-11f1-90a8-aefacda18209	alert:20002	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	2026-08-28 12:53:57.24	2026-08-28 12:54:02.57	5330	1	start_event	end_1	\N	\N		人员入侵告警处理（告警#20002）	\N	\N	\N	\N	\N	\N
b1afb96c-a29b-11f1-9eaa-aefacda18209	3	b1afb96c-a29b-11f1-9eaa-aefacda18209	alert:10002	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	2026-08-28 12:48:20.991	2026-08-28 13:07:36.243	1155252	1	start_event	end_1	\N	\N		人员入侵告警处理（告警#10002）	\N	\N	\N	\N	\N	\N
b4173508-a2a1-11f1-aee5-5a91bd373cd1	2	b4173508-a2a1-11f1-aee5-5a91bd373cd1	alert:30001	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	2026-08-28 13:31:22.005	\N	\N	1	start_event	\N	\N	\N		人员入侵告警处理（告警#30001）	\N	\N	\N	\N	\N	\N
eccedc52-a2a1-11f1-a0a7-f2ebdc74e900	2	eccedc52-a2a1-11f1-a0a7-f2ebdc74e900	alert:30002	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	2026-08-28 13:32:57.161	\N	\N	1	start_event	\N	\N	\N		人员入侵告警处理（告警#30002）	\N	\N	\N	\N	\N	\N
0d7551ff-a2a2-11f1-a0a7-f2ebdc74e900	2	0d7551ff-a2a2-11f1-a0a7-f2ebdc74e900	alert:30003	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	2026-08-28 13:33:51.938	\N	\N	1	start_event	\N	\N	\N		人员入侵告警处理（告警#30003）	\N	\N	\N	\N	\N	\N
b4879b0a-a2a7-11f1-ae25-fe31f4546ab1	3	b4879b0a-a2a7-11f1-ae25-fe31f4546ab1	alert:40002	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	2026-08-28 14:14:19.722	2026-08-28 14:15:08.037	48315	1	start_event	\N	\N	reject:复核为误报：画面为动物轮廓，非人员闯入		人员入侵告警处理（告警#40002）	\N	\N	\N	\N	\N	\N
4298127d-a2a2-11f1-a551-3a17ebed01a9	3	4298127d-a2a2-11f1-a551-3a17ebed01a9	alert:30004	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	2026-08-28 13:35:21.086	2026-08-28 13:40:02.938	281852	1	start_event	end_1	\N	\N		人员入侵告警处理（告警#30004）	\N	\N	\N	\N	\N	\N
b48f1532-a2a7-11f1-ae25-fe31f4546ab1	3	b48f1532-a2a7-11f1-ae25-fe31f4546ab1	alert:40003	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	2026-08-28 14:14:19.771	2026-08-28 14:15:08.111	48340	1	start_event	\N	\N	cancel:重复告警，与东门事件为同一人员，合并处理		人员入侵告警处理（告警#40003）	\N	\N	\N	\N	\N	\N
b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	3	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	alert:40004	alert_fire_smoke:2:a035bb41-a2a7-11f1-ae25-fe31f4546ab1	2026-08-28 14:14:19.849	2026-08-28 14:15:08.286	48437	1	start_event	end_task_manager_sign	\N	\N		烟感火情告警处理（告警#40004）	\N	\N	\N	\N	\N	\N
2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	2	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	alert:40007	alert_fire_smoke:3:202ef60d-a2a8-11f1-ae25-fe31f4546ab1	2026-08-28 14:17:31.935	\N	\N	1	start_event	\N	\N	\N		烟感火情告警处理（告警#40007）	\N	\N	\N	\N	\N	\N
2722bf29-a2a8-11f1-ae25-fe31f4546ab1	2	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	alert:40008	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	2026-08-28 14:17:31.999	\N	\N	1	start_event	\N	\N	\N		人员入侵告警处理（告警#40008）	\N	\N	\N	\N	\N	\N
40ef870f-a2ac-11f1-83a4-6e81fb0021bd	3	40ef870f-a2ac-11f1-83a4-6e81fb0021bd	alert:40009	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	2026-08-28 14:46:53.271	2026-08-28 14:47:05.393	12122	1	start_event	end_1	\N	\N		人员入侵告警处理（告警#40009）	\N	\N	\N	\N	\N	\N
\.


--
-- Data for Name: act_hi_taskinst; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.act_hi_taskinst (id_, rev_, proc_def_id_, task_def_id_, task_def_key_, proc_inst_id_, execution_id_, scope_id_, sub_scope_id_, scope_type_, scope_definition_id_, propagated_stage_inst_id_, name_, parent_task_id_, description_, owner_, assignee_, start_time_, claim_time_, end_time_, duration_, delete_reason_, priority_, due_date_, form_key_, category_, tenant_id_, last_updated_time_) FROM stdin;
b48f3c56-a2a7-11f1-ae25-fe31f4546ab1	2	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	\N	task_1	b48f1532-a2a7-11f1-ae25-fe31f4546ab1	b48f3c52-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	审批人	\N	\N	\N	\N	2026-08-28 14:14:19.772	\N	2026-08-28 14:15:08.102	48330	cancel:重复告警，与东门事件为同一人员，合并处理	50	\N	\N	\N		2026-08-28 14:15:08.102
68bbbab1-a29b-11f1-8fa2-aefacda18209	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	\N	task_1	68bb9399-a29b-11f1-8fa2-aefacda18209	68bb939d-a29b-11f1-8fa2-aefacda18209	\N	\N	\N	\N	\N	审批人	\N	\N	\N	\N	2026-08-28 12:46:18.595	\N	\N	\N	\N	50	\N	\N	\N		2026-08-28 12:46:18.596
40f10dc3-a2ac-11f1-83a4-6e81fb0021bd	3	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	\N	task_1	40ef870f-a2ac-11f1-83a4-6e81fb0021bd	40efd53f-a2ac-11f1-83a4-6e81fb0021bd	\N	\N	\N	\N	\N	审批人	\N	\N	\N	1	2026-08-28 14:46:53.275	\N	2026-08-28 14:47:05.375	12100	\N	50	\N	\N	\N		2026-08-28 14:47:05.375
b49b9881-a2a7-11f1-ae25-fe31f4546ab1	3	alert_fire_smoke:2:a035bb41-a2a7-11f1-ae25-fe31f4546ab1	\N	task_specialist	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	b49b987d-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	安全专员初审	\N	\N	\N	1	2026-08-28 14:14:19.853	\N	2026-08-28 14:15:08.18	48327	\N	50	\N	\N	\N		2026-08-28 14:15:08.18
b418e2c0-a2a1-11f1-aee5-5a91bd373cd1	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	\N	task_1	b4173508-a2a1-11f1-aee5-5a91bd373cd1	b4175c1c-a2a1-11f1-aee5-5a91bd373cd1	\N	\N	\N	\N	\N	审批人	\N	\N	\N	\N	2026-08-28 13:31:22.009	\N	\N	\N	\N	50	\N	\N	\N		2026-08-28 13:31:22.016
ecd0b11a-a2a1-11f1-a0a7-f2ebdc74e900	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	\N	task_1	eccedc52-a2a1-11f1-a0a7-f2ebdc74e900	eccf2a76-a2a1-11f1-a0a7-f2ebdc74e900	\N	\N	\N	\N	\N	审批人	\N	\N	\N	\N	2026-08-28 13:32:57.165	\N	\N	\N	\N	50	\N	\N	\N		2026-08-28 13:32:57.174
0d755207-a2a2-11f1-a0a7-f2ebdc74e900	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	\N	task_1	0d7551ff-a2a2-11f1-a0a7-f2ebdc74e900	0d755203-a2a2-11f1-a0a7-f2ebdc74e900	\N	\N	\N	\N	\N	审批人	\N	\N	\N	\N	2026-08-28 13:33:51.939	\N	\N	\N	\N	50	\N	\N	\N		2026-08-28 13:33:51.939
d16a2b70-a2a7-11f1-ae25-fe31f4546ab1	2	alert_fire_smoke:2:a035bb41-a2a7-11f1-ae25-fe31f4546ab1	\N	task_manager_sign	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	d16a2b6c-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	主管会签确认	\N	\N	\N	1	2026-08-28 14:15:08.183	\N	2026-08-28 14:15:08.262	79	\N	50	\N	\N	\N		2026-08-28 14:15:08.262
3dbc30f1-a29b-11f1-8fa2-aefacda18209	2	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	\N	task_1	3dba0e09-a29b-11f1-8fa2-aefacda18209	3dba5c2d-a29b-11f1-8fa2-aefacda18209	\N	\N	\N	\N	\N	审批人	\N	\N	\N	1	2026-08-28 12:45:06.448	\N	2026-08-28 12:45:53.463	47015	\N	50	\N	\N	\N		2026-08-28 12:45:53.463
3dc2cb6b-a29c-11f1-9eaa-aefacda18209	2	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	\N	task_1	3dc27d39-a29c-11f1-9eaa-aefacda18209	3dc2a457-a29c-11f1-9eaa-aefacda18209	\N	\N	\N	\N	\N	审批人	\N	\N	\N	1	2026-08-28 12:52:15.997	\N	2026-08-28 12:52:40.807	24810	\N	50	\N	\N	\N		2026-08-28 12:52:40.807
7a1d89f7-a29c-11f1-90a8-aefacda18209	2	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	\N	task_1	7a1b6706-a29c-11f1-90a8-aefacda18209	7a1b8e23-a29c-11f1-90a8-aefacda18209	\N	\N	\N	\N	\N	审批人	\N	\N	\N	1	2026-08-28 12:53:57.245	\N	2026-08-28 12:54:02.52	5275	\N	50	\N	\N	\N		2026-08-28 12:54:02.52
b1b1dc54-a29b-11f1-9eaa-aefacda18209	2	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	\N	task_1	b1afb96c-a29b-11f1-9eaa-aefacda18209	b1b00790-a29b-11f1-9eaa-aefacda18209	\N	\N	\N	\N	\N	审批人	\N	\N	\N	1	2026-08-28 12:48:20.995	\N	2026-08-28 13:07:36.201	1155206	\N	50	\N	\N	\N		2026-08-28 13:07:36.201
429a0e56-a2a2-11f1-a551-3a17ebed01a9	2	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	\N	task_1	4298127d-a2a2-11f1-a551-3a17ebed01a9	42983992-a2a2-11f1-a551-3a17ebed01a9	\N	\N	\N	\N	\N	审批人	\N	\N	\N	1	2026-08-28 13:35:21.089	\N	2026-08-28 13:40:02.903	281814	\N	50	\N	\N	\N		2026-08-28 13:40:02.903
b4b33f64-a2a7-11f1-ae25-fe31f4546ab1	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	\N	task_1	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	b4b33f60-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	审批人	\N	\N	\N	\N	2026-08-28 14:14:20.008	\N	\N	\N	\N	50	\N	\N	\N		2026-08-28 14:14:20.008
b47b17e6-a2a7-11f1-ae25-fe31f4546ab1	3	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	\N	task_1	b47a0662-a2a7-11f1-ae25-fe31f4546ab1	b47a7ba2-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	审批人	\N	\N	\N	1	2026-08-28 14:14:19.638	\N	2026-08-28 14:15:07.938	48300	\N	50	\N	\N	\N		2026-08-28 14:15:07.938
b487c22e-a2a7-11f1-ae25-fe31f4546ab1	3	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	\N	task_1	b4879b0a-a2a7-11f1-ae25-fe31f4546ab1	b487c22a-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	审批人	\N	\N	\N	1	2026-08-28 14:14:19.723	\N	2026-08-28 14:15:08.031	48308	reject:复核为误报：画面为动物轮廓，非人员闯入	50	\N	\N	\N		2026-08-28 14:15:08.031
b4a5d1cc-a2a7-11f1-ae25-fe31f4546ab1	3	alert_fire_smoke:2:a035bb41-a2a7-11f1-ae25-fe31f4546ab1	\N	task_specialist	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	b4a5d1c8-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	安全专员初审	\N	\N	\N	1	2026-08-28 14:14:19.92	\N	2026-08-28 14:15:08.414	48494	\N	50	\N	\N	\N		2026-08-28 14:15:08.414
d19f4448-a2a7-11f1-ae25-fe31f4546ab1	1	alert_fire_smoke:2:a035bb41-a2a7-11f1-ae25-fe31f4546ab1	\N	task_specialist	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	d19f4446-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	安全专员初审	\N	\N	\N	\N	2026-08-28 14:15:08.531	\N	\N	\N	\N	50	\N	\N	\N		2026-08-28 14:15:08.531
d18ea272-a2a7-11f1-ae25-fe31f4546ab1	2	alert_fire_smoke:2:a035bb41-a2a7-11f1-ae25-fe31f4546ab1	\N	task_manager_sign	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	d18e7b5e-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	主管会签确认	\N	\N	\N	1	2026-08-28 14:15:08.422	\N	2026-08-28 14:15:08.529	107	Change parent activity to task_specialist	50	\N	\N	\N		2026-08-28 14:15:08.529
2722e64d-a2a8-11f1-ae25-fe31f4546ab1	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	\N	task_1	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	2722e649-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	审批人	\N	\N	\N	\N	2026-08-28 14:17:32	\N	\N	\N	\N	50	\N	\N	\N		2026-08-28 14:17:32
31656533-a2a8-11f1-ae25-fe31f4546ab1	1	alert_fire_smoke:3:202ef60d-a2a8-11f1-ae25-fe31f4546ab1	\N	task_manager_sign	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	3160350a-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	主管会签确认	\N	\N	\N	104	2026-08-28 14:17:49.213	\N	\N	\N	\N	50	\N	\N	\N		2026-08-28 14:17:49.213
27194945-a2a8-11f1-ae25-fe31f4546ab1	3	alert_fire_smoke:3:202ef60d-a2a8-11f1-ae25-fe31f4546ab1	\N	task_specialist	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	27192231-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	安全专员初审	\N	\N	\N	1	2026-08-28 14:17:31.937	\N	2026-08-28 14:17:49.177	17240	\N	50	\N	\N	\N		2026-08-28 14:17:49.177
3160350f-a2a8-11f1-ae25-fe31f4546ab1	2	alert_fire_smoke:3:202ef60d-a2a8-11f1-ae25-fe31f4546ab1	\N	task_manager_sign	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	31603509-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	主管会签确认	\N	\N	\N	1	2026-08-28 14:17:49.179	\N	2026-08-28 14:17:49.289	110	\N	50	\N	\N	\N		2026-08-28 14:17:49.289
\.


--
-- Data for Name: act_hi_tsk_log; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.act_hi_tsk_log (id_, type_, task_id_, time_stamp_, user_id_, data_, execution_id_, proc_inst_id_, proc_def_id_, scope_id_, scope_definition_id_, sub_scope_id_, scope_type_, tenant_id_) FROM stdin;
\.


--
-- Data for Name: act_hi_varinst; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.act_hi_varinst (id_, rev_, proc_inst_id_, execution_id_, task_id_, name_, var_type_, scope_id_, sub_scope_id_, scope_type_, bytearray_id_, double_, long_, text_, text2_, create_time_, last_updated_time_) FROM stdin;
3dba351b-a29b-11f1-8fa2-aefacda18209	0	3dba0e09-a29b-11f1-8fa2-aefacda18209	3dba0e09-a29b-11f1-8fa2-aefacda18209	\N	alertLevel	string	\N	\N	\N	\N	\N	\N	high	\N	2026-08-28 12:45:06.445	2026-08-28 12:45:06.445
3dba5c2c-a29b-11f1-8fa2-aefacda18209	0	3dba0e09-a29b-11f1-8fa2-aefacda18209	3dba0e09-a29b-11f1-8fa2-aefacda18209	\N	PROCESS_START_USER_ID	long	\N	\N	\N	\N	\N	1	1	\N	2026-08-28 12:45:06.445	2026-08-28 12:45:06.445
3dcc84a5-a29b-11f1-8fa2-aefacda18209	0	3dba0e09-a29b-11f1-8fa2-aefacda18209	3dba0e09-a29b-11f1-8fa2-aefacda18209	\N	PROCESS_INSTANCE_NAME	string	\N	\N	\N	\N	\N	\N	人员入侵告警处理	\N	2026-08-28 12:45:06.564	2026-08-28 12:45:06.564
59be72e6-a29b-11f1-8fa2-aefacda18209	0	3dba0e09-a29b-11f1-8fa2-aefacda18209	3dba5c2d-a29b-11f1-8fa2-aefacda18209	3dbc30f1-a29b-11f1-8fa2-aefacda18209	reason	string	\N	\N	\N	\N	\N	\N	确认告警属实，已处理	\N	2026-08-28 12:45:53.448	2026-08-28 12:45:53.448
68bb939b-a29b-11f1-8fa2-aefacda18209	0	68bb9399-a29b-11f1-8fa2-aefacda18209	68bb9399-a29b-11f1-8fa2-aefacda18209	\N	PROCESS_START_USER_ID	long	\N	\N	\N	\N	\N	1	1	\N	2026-08-28 12:46:18.595	2026-08-28 12:46:18.595
68bb939c-a29b-11f1-8fa2-aefacda18209	0	68bb9399-a29b-11f1-8fa2-aefacda18209	68bb9399-a29b-11f1-8fa2-aefacda18209	\N	alertId	long	\N	\N	\N	\N	\N	10001	10001	\N	2026-08-28 12:46:18.595	2026-08-28 12:46:18.595
68c00075-a29b-11f1-8fa2-aefacda18209	0	68bb9399-a29b-11f1-8fa2-aefacda18209	68bb9399-a29b-11f1-8fa2-aefacda18209	\N	PROCESS_INSTANCE_NAME	string	\N	\N	\N	\N	\N	\N	人员入侵告警处理（告警#10001）	\N	2026-08-28 12:46:18.624	2026-08-28 12:46:18.624
b1afe07e-a29b-11f1-9eaa-aefacda18209	0	b1afb96c-a29b-11f1-9eaa-aefacda18209	b1afb96c-a29b-11f1-9eaa-aefacda18209	\N	PROCESS_START_USER_ID	long	\N	\N	\N	\N	\N	1	1	\N	2026-08-28 12:48:20.993	2026-08-28 12:48:20.993
b1b0078f-a29b-11f1-9eaa-aefacda18209	0	b1afb96c-a29b-11f1-9eaa-aefacda18209	b1afb96c-a29b-11f1-9eaa-aefacda18209	\N	alertId	long	\N	\N	\N	\N	\N	10002	10002	\N	2026-08-28 12:48:20.993	2026-08-28 12:48:20.993
b1b95668-a29b-11f1-9eaa-aefacda18209	0	b1afb96c-a29b-11f1-9eaa-aefacda18209	b1afb96c-a29b-11f1-9eaa-aefacda18209	\N	PROCESS_INSTANCE_NAME	string	\N	\N	\N	\N	\N	\N	人员入侵告警处理（告警#10002）	\N	2026-08-28 12:48:21.054	2026-08-28 12:48:21.054
3dc27d3b-a29c-11f1-9eaa-aefacda18209	0	3dc27d39-a29c-11f1-9eaa-aefacda18209	3dc27d39-a29c-11f1-9eaa-aefacda18209	\N	PROCESS_START_USER_ID	long	\N	\N	\N	\N	\N	1	1	\N	2026-08-28 12:52:15.995	2026-08-28 12:52:15.995
3dc2a44c-a29c-11f1-9eaa-aefacda18209	0	3dc27d39-a29c-11f1-9eaa-aefacda18209	3dc27d39-a29c-11f1-9eaa-aefacda18209	\N	taskType	string	\N	\N	\N	\N	\N	\N	intrusion	\N	2026-08-28 12:52:15.996	2026-08-28 12:52:15.996
3dc2a44d-a29c-11f1-9eaa-aefacda18209	0	3dc27d39-a29c-11f1-9eaa-aefacda18209	3dc27d39-a29c-11f1-9eaa-aefacda18209	\N	imageUrl	string	\N	\N	\N	\N	\N	\N	/data/images/20001.jpg	\N	2026-08-28 12:52:15.996	2026-08-28 12:52:15.996
3dc2a44e-a29c-11f1-9eaa-aefacda18209	0	3dc27d39-a29c-11f1-9eaa-aefacda18209	3dc27d39-a29c-11f1-9eaa-aefacda18209	\N	taskName	string	\N	\N	\N	\N	\N	\N	周界入侵检测	\N	2026-08-28 12:52:15.996	2026-08-28 12:52:15.996
3dc2a44f-a29c-11f1-9eaa-aefacda18209	0	3dc27d39-a29c-11f1-9eaa-aefacda18209	3dc27d39-a29c-11f1-9eaa-aefacda18209	\N	alertObject	string	\N	\N	\N	\N	\N	\N	person	\N	2026-08-28 12:52:15.996	2026-08-28 12:52:15.996
3dc2a450-a29c-11f1-9eaa-aefacda18209	0	3dc27d39-a29c-11f1-9eaa-aefacda18209	3dc27d39-a29c-11f1-9eaa-aefacda18209	\N	alertId	integer	\N	\N	\N	\N	\N	20001	20001	\N	2026-08-28 12:52:15.996	2026-08-28 12:52:15.996
3dc2a451-a29c-11f1-9eaa-aefacda18209	0	3dc27d39-a29c-11f1-9eaa-aefacda18209	3dc27d39-a29c-11f1-9eaa-aefacda18209	\N	alertEvent	string	\N	\N	\N	\N	\N	\N	人员入侵	\N	2026-08-28 12:52:15.996	2026-08-28 12:52:15.996
3dc2a452-a29c-11f1-9eaa-aefacda18209	0	3dc27d39-a29c-11f1-9eaa-aefacda18209	3dc27d39-a29c-11f1-9eaa-aefacda18209	\N	alertTime	long	\N	\N	\N	\N	\N	1787892551000	1787892551000	\N	2026-08-28 12:52:15.996	2026-08-28 12:52:15.996
3dc2a453-a29c-11f1-9eaa-aefacda18209	0	3dc27d39-a29c-11f1-9eaa-aefacda18209	3dc27d39-a29c-11f1-9eaa-aefacda18209	\N	deviceId	string	\N	\N	\N	\N	\N	\N	cam-007	\N	2026-08-28 12:52:15.996	2026-08-28 12:52:15.996
3dc2a454-a29c-11f1-9eaa-aefacda18209	0	3dc27d39-a29c-11f1-9eaa-aefacda18209	3dc27d39-a29c-11f1-9eaa-aefacda18209	\N	deviceName	string	\N	\N	\N	\N	\N	\N	北门摄像头	\N	2026-08-28 12:52:15.996	2026-08-28 12:52:15.996
3dc2a455-a29c-11f1-9eaa-aefacda18209	0	3dc27d39-a29c-11f1-9eaa-aefacda18209	3dc27d39-a29c-11f1-9eaa-aefacda18209	\N	nodeId	string	\N	\N	\N	\N	\N	\N	edge-01	\N	2026-08-28 12:52:15.996	2026-08-28 12:52:15.996
3dc2a456-a29c-11f1-9eaa-aefacda18209	0	3dc27d39-a29c-11f1-9eaa-aefacda18209	3dc27d39-a29c-11f1-9eaa-aefacda18209	\N	taskId	string	\N	\N	\N	\N	\N	\N	vid-task-9	\N	2026-08-28 12:52:15.996	2026-08-28 12:52:15.996
3dc9a93f-a29c-11f1-9eaa-aefacda18209	0	3dc27d39-a29c-11f1-9eaa-aefacda18209	3dc27d39-a29c-11f1-9eaa-aefacda18209	\N	PROCESS_INSTANCE_NAME	string	\N	\N	\N	\N	\N	\N	人员入侵告警处理（告警#20001）	\N	2026-08-28 12:52:16.042	2026-08-28 12:52:16.042
4c8b4790-a29c-11f1-9eaa-aefacda18209	0	3dc27d39-a29c-11f1-9eaa-aefacda18209	3dc2a457-a29c-11f1-9eaa-aefacda18209	3dc2cb6b-a29c-11f1-9eaa-aefacda18209	reason	string	\N	\N	\N	\N	\N	\N	已到现场处置	\N	2026-08-28 12:52:40.799	2026-08-28 12:52:40.799
7a1b6708-a29c-11f1-90a8-aefacda18209	0	7a1b6706-a29c-11f1-90a8-aefacda18209	7a1b6706-a29c-11f1-90a8-aefacda18209	\N	PROCESS_START_USER_ID	long	\N	\N	\N	\N	\N	1	1	\N	2026-08-28 12:53:57.242	2026-08-28 12:53:57.242
7a1b8e19-a29c-11f1-90a8-aefacda18209	0	7a1b6706-a29c-11f1-90a8-aefacda18209	7a1b6706-a29c-11f1-90a8-aefacda18209	\N	taskType	string	\N	\N	\N	\N	\N	\N	helmet	\N	2026-08-28 12:53:57.242	2026-08-28 12:53:57.242
7a1b8e1a-a29c-11f1-90a8-aefacda18209	0	7a1b6706-a29c-11f1-90a8-aefacda18209	7a1b6706-a29c-11f1-90a8-aefacda18209	\N	imageUrl	string	\N	\N	\N	\N	\N	\N	/data/images/20002.jpg	\N	2026-08-28 12:53:57.242	2026-08-28 12:53:57.242
7a1b8e1b-a29c-11f1-90a8-aefacda18209	0	7a1b6706-a29c-11f1-90a8-aefacda18209	7a1b6706-a29c-11f1-90a8-aefacda18209	\N	taskName	string	\N	\N	\N	\N	\N	\N	安全帽检测	\N	2026-08-28 12:53:57.242	2026-08-28 12:53:57.242
7a1b8e1c-a29c-11f1-90a8-aefacda18209	0	7a1b6706-a29c-11f1-90a8-aefacda18209	7a1b6706-a29c-11f1-90a8-aefacda18209	\N	alertObject	string	\N	\N	\N	\N	\N	\N	helmet	\N	2026-08-28 12:53:57.242	2026-08-28 12:53:57.242
7a1b8e1d-a29c-11f1-90a8-aefacda18209	0	7a1b6706-a29c-11f1-90a8-aefacda18209	7a1b6706-a29c-11f1-90a8-aefacda18209	\N	alertId	integer	\N	\N	\N	\N	\N	20002	20002	\N	2026-08-28 12:53:57.242	2026-08-28 12:53:57.242
7a1b8e1e-a29c-11f1-90a8-aefacda18209	0	7a1b6706-a29c-11f1-90a8-aefacda18209	7a1b6706-a29c-11f1-90a8-aefacda18209	\N	alertEvent	string	\N	\N	\N	\N	\N	\N	未戴安全帽	\N	2026-08-28 12:53:57.242	2026-08-28 12:53:57.242
7a1b8e1f-a29c-11f1-90a8-aefacda18209	0	7a1b6706-a29c-11f1-90a8-aefacda18209	7a1b6706-a29c-11f1-90a8-aefacda18209	\N	alertTime	long	\N	\N	\N	\N	\N	1787893000000	1787893000000	\N	2026-08-28 12:53:57.242	2026-08-28 12:53:57.242
7a1b8e20-a29c-11f1-90a8-aefacda18209	0	7a1b6706-a29c-11f1-90a8-aefacda18209	7a1b6706-a29c-11f1-90a8-aefacda18209	\N	deviceId	string	\N	\N	\N	\N	\N	\N	cam-008	\N	2026-08-28 12:53:57.242	2026-08-28 12:53:57.242
7a1b8e21-a29c-11f1-90a8-aefacda18209	0	7a1b6706-a29c-11f1-90a8-aefacda18209	7a1b6706-a29c-11f1-90a8-aefacda18209	\N	deviceName	string	\N	\N	\N	\N	\N	\N	东区摄像头	\N	2026-08-28 12:53:57.242	2026-08-28 12:53:57.242
7a1b8e22-a29c-11f1-90a8-aefacda18209	0	7a1b6706-a29c-11f1-90a8-aefacda18209	7a1b6706-a29c-11f1-90a8-aefacda18209	\N	taskId	string	\N	\N	\N	\N	\N	\N	vid-task-10	\N	2026-08-28 12:53:57.242	2026-08-28 12:53:57.242
7a3816db-a29c-11f1-90a8-aefacda18209	0	7a1b6706-a29c-11f1-90a8-aefacda18209	7a1b6706-a29c-11f1-90a8-aefacda18209	\N	PROCESS_INSTANCE_NAME	string	\N	\N	\N	\N	\N	\N	人员入侵告警处理（告警#20002）	\N	2026-08-28 12:53:57.429	2026-08-28 12:53:57.429
7d3e51fc-a29c-11f1-90a8-aefacda18209	0	7a1b6706-a29c-11f1-90a8-aefacda18209	7a1b8e23-a29c-11f1-90a8-aefacda18209	7a1d89f7-a29c-11f1-90a8-aefacda18209	reason	string	\N	\N	\N	\N	\N	\N	复核完成，闭环	\N	2026-08-28 12:54:02.503	2026-08-28 12:54:02.503
623d6848-a29e-11f1-befa-02ee22a453e8	0	b1afb96c-a29b-11f1-9eaa-aefacda18209	b1b00790-a29b-11f1-9eaa-aefacda18209	b1b1dc54-a29b-11f1-9eaa-aefacda18209	reason	string	\N	\N	\N	\N	\N	\N	已现场核实并处置	\N	2026-08-28 13:07:36.192	2026-08-28 13:07:36.192
b417350a-a2a1-11f1-aee5-5a91bd373cd1	0	b4173508-a2a1-11f1-aee5-5a91bd373cd1	b4173508-a2a1-11f1-aee5-5a91bd373cd1	\N	PROCESS_START_USER_ID	long	\N	\N	\N	\N	\N	1	1	\N	2026-08-28 13:31:22.006	2026-08-28 13:31:22.006
b4175c1b-a2a1-11f1-aee5-5a91bd373cd1	0	b4173508-a2a1-11f1-aee5-5a91bd373cd1	b4173508-a2a1-11f1-aee5-5a91bd373cd1	\N	alertId	long	\N	\N	\N	\N	\N	30001	30001	\N	2026-08-28 13:31:22.006	2026-08-28 13:31:22.006
b422f4e4-a2a1-11f1-aee5-5a91bd373cd1	0	b4173508-a2a1-11f1-aee5-5a91bd373cd1	b4173508-a2a1-11f1-aee5-5a91bd373cd1	\N	PROCESS_INSTANCE_NAME	string	\N	\N	\N	\N	\N	\N	人员入侵告警处理（告警#30001）	\N	2026-08-28 13:31:22.082	2026-08-28 13:31:22.082
eccf0364-a2a1-11f1-a0a7-f2ebdc74e900	0	eccedc52-a2a1-11f1-a0a7-f2ebdc74e900	eccedc52-a2a1-11f1-a0a7-f2ebdc74e900	\N	PROCESS_START_USER_ID	long	\N	\N	\N	\N	\N	1	1	\N	2026-08-28 13:32:57.163	2026-08-28 13:32:57.163
eccf2a75-a2a1-11f1-a0a7-f2ebdc74e900	0	eccedc52-a2a1-11f1-a0a7-f2ebdc74e900	eccedc52-a2a1-11f1-a0a7-f2ebdc74e900	\N	alertId	long	\N	\N	\N	\N	\N	30002	30002	\N	2026-08-28 13:32:57.163	2026-08-28 13:32:57.163
ece1c81e-a2a1-11f1-a0a7-f2ebdc74e900	0	eccedc52-a2a1-11f1-a0a7-f2ebdc74e900	eccedc52-a2a1-11f1-a0a7-f2ebdc74e900	\N	PROCESS_INSTANCE_NAME	string	\N	\N	\N	\N	\N	\N	人员入侵告警处理（告警#30002）	\N	2026-08-28 13:32:57.285	2026-08-28 13:32:57.285
0d755201-a2a2-11f1-a0a7-f2ebdc74e900	0	0d7551ff-a2a2-11f1-a0a7-f2ebdc74e900	0d7551ff-a2a2-11f1-a0a7-f2ebdc74e900	\N	PROCESS_START_USER_ID	long	\N	\N	\N	\N	\N	1	1	\N	2026-08-28 13:33:51.939	2026-08-28 13:33:51.939
0d755202-a2a2-11f1-a0a7-f2ebdc74e900	0	0d7551ff-a2a2-11f1-a0a7-f2ebdc74e900	0d7551ff-a2a2-11f1-a0a7-f2ebdc74e900	\N	alertId	long	\N	\N	\N	\N	\N	30003	30003	\N	2026-08-28 13:33:51.939	2026-08-28 13:33:51.939
0d7f642b-a2a2-11f1-a0a7-f2ebdc74e900	0	0d7551ff-a2a2-11f1-a0a7-f2ebdc74e900	0d7551ff-a2a2-11f1-a0a7-f2ebdc74e900	\N	PROCESS_INSTANCE_NAME	string	\N	\N	\N	\N	\N	\N	人员入侵告警处理（告警#30003）	\N	2026-08-28 13:33:52.005	2026-08-28 13:33:52.005
4298398f-a2a2-11f1-a551-3a17ebed01a9	0	4298127d-a2a2-11f1-a551-3a17ebed01a9	4298127d-a2a2-11f1-a551-3a17ebed01a9	\N	PROCESS_START_USER_ID	long	\N	\N	\N	\N	\N	1	1	\N	2026-08-28 13:35:21.087	2026-08-28 13:35:21.087
42983990-a2a2-11f1-a551-3a17ebed01a9	0	4298127d-a2a2-11f1-a551-3a17ebed01a9	4298127d-a2a2-11f1-a551-3a17ebed01a9	\N	alertId	long	\N	\N	\N	\N	\N	30004	30004	\N	2026-08-28 13:35:21.087	2026-08-28 13:35:21.087
42983991-a2a2-11f1-a551-3a17ebed01a9	1	4298127d-a2a2-11f1-a551-3a17ebed01a9	4298127d-a2a2-11f1-a551-3a17ebed01a9	\N	PROCESS_INSTANCE_NAME	string	\N	\N	\N	\N	\N	\N	人员入侵告警处理（告警#30004）	\N	2026-08-28 13:35:21.087	2026-08-28 13:35:21.182
ea90416a-a2a2-11f1-a551-3a17ebed01a9	0	4298127d-a2a2-11f1-a551-3a17ebed01a9	42983992-a2a2-11f1-a551-3a17ebed01a9	429a0e56-a2a2-11f1-a551-3a17ebed01a9	reason	string	\N	\N	\N	\N	\N	\N	确认告警属实，已派人员处理	\N	2026-08-28 13:40:02.892	2026-08-28 13:40:02.892
b47a5485-a2a7-11f1-ae25-fe31f4546ab1	0	b47a0662-a2a7-11f1-ae25-fe31f4546ab1	b47a0662-a2a7-11f1-ae25-fe31f4546ab1	\N	deviceId	string	\N	\N	\N	\N	\N	\N	cam-east-001	\N	2026-08-28 14:14:19.635	2026-08-28 14:14:19.635
b47a5486-a2a7-11f1-ae25-fe31f4546ab1	0	b47a0662-a2a7-11f1-ae25-fe31f4546ab1	b47a0662-a2a7-11f1-ae25-fe31f4546ab1	\N	deviceName	string	\N	\N	\N	\N	\N	\N	东门摄像头-01	\N	2026-08-28 14:14:19.635	2026-08-28 14:14:19.635
b47a5487-a2a7-11f1-ae25-fe31f4546ab1	0	b47a0662-a2a7-11f1-ae25-fe31f4546ab1	b47a0662-a2a7-11f1-ae25-fe31f4546ab1	\N	PROCESS_START_USER_ID	long	\N	\N	\N	\N	\N	1	1	\N	2026-08-28 14:14:19.635	2026-08-28 14:14:19.635
b47a5488-a2a7-11f1-ae25-fe31f4546ab1	0	b47a0662-a2a7-11f1-ae25-fe31f4546ab1	b47a0662-a2a7-11f1-ae25-fe31f4546ab1	\N	edgeNodeId	integer	\N	\N	\N	\N	\N	3	3	\N	2026-08-28 14:14:19.635	2026-08-28 14:14:19.635
b47a5489-a2a7-11f1-ae25-fe31f4546ab1	0	b47a0662-a2a7-11f1-ae25-fe31f4546ab1	b47a0662-a2a7-11f1-ae25-fe31f4546ab1	\N	taskType	string	\N	\N	\N	\N	\N	\N	realtime	\N	2026-08-28 14:14:19.635	2026-08-28 14:14:19.635
b47a548a-a2a7-11f1-ae25-fe31f4546ab1	0	b47a0662-a2a7-11f1-ae25-fe31f4546ab1	b47a0662-a2a7-11f1-ae25-fe31f4546ab1	\N	imageUrl	string	\N	\N	\N	\N	\N	\N	http://localhost:9003/static/images/demo-alert-intrusion.png	\N	2026-08-28 14:14:19.635	2026-08-28 14:14:19.635
b47a548b-a2a7-11f1-ae25-fe31f4546ab1	0	b47a0662-a2a7-11f1-ae25-fe31f4546ab1	b47a0662-a2a7-11f1-ae25-fe31f4546ab1	\N	taskName	string	\N	\N	\N	\N	\N	\N	周界入侵检测	\N	2026-08-28 14:14:19.635	2026-08-28 14:14:19.635
b47a548c-a2a7-11f1-ae25-fe31f4546ab1	0	b47a0662-a2a7-11f1-ae25-fe31f4546ab1	b47a0662-a2a7-11f1-ae25-fe31f4546ab1	\N	alertObject	string	\N	\N	\N	\N	\N	\N	person	\N	2026-08-28 14:14:19.635	2026-08-28 14:14:19.635
b47a548d-a2a7-11f1-ae25-fe31f4546ab1	0	b47a0662-a2a7-11f1-ae25-fe31f4546ab1	b47a0662-a2a7-11f1-ae25-fe31f4546ab1	\N	alertId	integer	\N	\N	\N	\N	\N	40001	40001	\N	2026-08-28 14:14:19.635	2026-08-28 14:14:19.635
b47a548e-a2a7-11f1-ae25-fe31f4546ab1	0	b47a0662-a2a7-11f1-ae25-fe31f4546ab1	b47a0662-a2a7-11f1-ae25-fe31f4546ab1	\N	alertEvent	string	\N	\N	\N	\N	\N	\N	intrusion	\N	2026-08-28 14:14:19.635	2026-08-28 14:14:19.635
b47a548f-a2a7-11f1-ae25-fe31f4546ab1	0	b47a0662-a2a7-11f1-ae25-fe31f4546ab1	b47a0662-a2a7-11f1-ae25-fe31f4546ab1	\N	alertTime	string	\N	\N	\N	\N	\N	\N	2026-08-28 13:52:17	\N	2026-08-28 14:14:19.635	2026-08-28 14:14:19.635
b47a5490-a2a7-11f1-ae25-fe31f4546ab1	0	b47a0662-a2a7-11f1-ae25-fe31f4546ab1	b47a0662-a2a7-11f1-ae25-fe31f4546ab1	\N	nodeId	integer	\N	\N	\N	\N	\N	12	12	\N	2026-08-28 14:14:19.636	2026-08-28 14:14:19.636
b47a7ba1-a2a7-11f1-ae25-fe31f4546ab1	0	b47a0662-a2a7-11f1-ae25-fe31f4546ab1	b47a0662-a2a7-11f1-ae25-fe31f4546ab1	\N	taskId	integer	\N	\N	\N	\N	\N	50101	50101	\N	2026-08-28 14:14:19.636	2026-08-28 14:14:19.636
b47a2d74-a2a7-11f1-ae25-fe31f4546ab1	1	b47a0662-a2a7-11f1-ae25-fe31f4546ab1	b47a0662-a2a7-11f1-ae25-fe31f4546ab1	\N	PROCESS_INSTANCE_NAME	string	\N	\N	\N	\N	\N	\N	人员入侵告警处理（告警#40001）	\N	2026-08-28 14:14:19.635	2026-08-28 14:14:19.698
b4879b0d-a2a7-11f1-ae25-fe31f4546ab1	0	b4879b0a-a2a7-11f1-ae25-fe31f4546ab1	b4879b0a-a2a7-11f1-ae25-fe31f4546ab1	\N	deviceId	string	\N	\N	\N	\N	\N	\N	cam-south-003	\N	2026-08-28 14:14:19.722	2026-08-28 14:14:19.722
b4879b0e-a2a7-11f1-ae25-fe31f4546ab1	0	b4879b0a-a2a7-11f1-ae25-fe31f4546ab1	b4879b0a-a2a7-11f1-ae25-fe31f4546ab1	\N	deviceName	string	\N	\N	\N	\N	\N	\N	南墙摄像头-03	\N	2026-08-28 14:14:19.722	2026-08-28 14:14:19.722
b4879b0f-a2a7-11f1-ae25-fe31f4546ab1	0	b4879b0a-a2a7-11f1-ae25-fe31f4546ab1	b4879b0a-a2a7-11f1-ae25-fe31f4546ab1	\N	PROCESS_START_USER_ID	long	\N	\N	\N	\N	\N	1	1	\N	2026-08-28 14:14:19.722	2026-08-28 14:14:19.722
b4879b10-a2a7-11f1-ae25-fe31f4546ab1	0	b4879b0a-a2a7-11f1-ae25-fe31f4546ab1	b4879b0a-a2a7-11f1-ae25-fe31f4546ab1	\N	edgeNodeId	integer	\N	\N	\N	\N	\N	3	3	\N	2026-08-28 14:14:19.722	2026-08-28 14:14:19.722
b4879b11-a2a7-11f1-ae25-fe31f4546ab1	0	b4879b0a-a2a7-11f1-ae25-fe31f4546ab1	b4879b0a-a2a7-11f1-ae25-fe31f4546ab1	\N	taskType	string	\N	\N	\N	\N	\N	\N	realtime	\N	2026-08-28 14:14:19.722	2026-08-28 14:14:19.722
b4879b12-a2a7-11f1-ae25-fe31f4546ab1	0	b4879b0a-a2a7-11f1-ae25-fe31f4546ab1	b4879b0a-a2a7-11f1-ae25-fe31f4546ab1	\N	imageUrl	string	\N	\N	\N	\N	\N	\N	http://localhost:9003/static/images/demo-alert-intrusion.png	\N	2026-08-28 14:14:19.722	2026-08-28 14:14:19.722
b4879b13-a2a7-11f1-ae25-fe31f4546ab1	0	b4879b0a-a2a7-11f1-ae25-fe31f4546ab1	b4879b0a-a2a7-11f1-ae25-fe31f4546ab1	\N	taskName	string	\N	\N	\N	\N	\N	\N	周界入侵检测	\N	2026-08-28 14:14:19.722	2026-08-28 14:14:19.722
b4879b0c-a2a7-11f1-ae25-fe31f4546ab1	1	b4879b0a-a2a7-11f1-ae25-fe31f4546ab1	b4879b0a-a2a7-11f1-ae25-fe31f4546ab1	\N	PROCESS_INSTANCE_NAME	string	\N	\N	\N	\N	\N	\N	人员入侵告警处理（告警#40002）	\N	2026-08-28 14:14:19.722	2026-08-28 14:14:19.75
b4879b14-a2a7-11f1-ae25-fe31f4546ab1	0	b4879b0a-a2a7-11f1-ae25-fe31f4546ab1	b4879b0a-a2a7-11f1-ae25-fe31f4546ab1	\N	alertObject	string	\N	\N	\N	\N	\N	\N	person	\N	2026-08-28 14:14:19.722	2026-08-28 14:14:19.722
b4879b15-a2a7-11f1-ae25-fe31f4546ab1	0	b4879b0a-a2a7-11f1-ae25-fe31f4546ab1	b4879b0a-a2a7-11f1-ae25-fe31f4546ab1	\N	alertId	integer	\N	\N	\N	\N	\N	40002	40002	\N	2026-08-28 14:14:19.722	2026-08-28 14:14:19.722
b4879b16-a2a7-11f1-ae25-fe31f4546ab1	0	b4879b0a-a2a7-11f1-ae25-fe31f4546ab1	b4879b0a-a2a7-11f1-ae25-fe31f4546ab1	\N	alertEvent	string	\N	\N	\N	\N	\N	\N	intrusion	\N	2026-08-28 14:14:19.722	2026-08-28 14:14:19.722
b4879b17-a2a7-11f1-ae25-fe31f4546ab1	0	b4879b0a-a2a7-11f1-ae25-fe31f4546ab1	b4879b0a-a2a7-11f1-ae25-fe31f4546ab1	\N	alertTime	string	\N	\N	\N	\N	\N	\N	2026-08-28 13:58:41	\N	2026-08-28 14:14:19.722	2026-08-28 14:14:19.722
b487c228-a2a7-11f1-ae25-fe31f4546ab1	0	b4879b0a-a2a7-11f1-ae25-fe31f4546ab1	b4879b0a-a2a7-11f1-ae25-fe31f4546ab1	\N	nodeId	integer	\N	\N	\N	\N	\N	12	12	\N	2026-08-28 14:14:19.723	2026-08-28 14:14:19.723
b487c229-a2a7-11f1-ae25-fe31f4546ab1	0	b4879b0a-a2a7-11f1-ae25-fe31f4546ab1	b4879b0a-a2a7-11f1-ae25-fe31f4546ab1	\N	taskId	integer	\N	\N	\N	\N	\N	50102	50102	\N	2026-08-28 14:14:19.723	2026-08-28 14:14:19.723
b48f3c45-a2a7-11f1-ae25-fe31f4546ab1	0	b48f1532-a2a7-11f1-ae25-fe31f4546ab1	b48f1532-a2a7-11f1-ae25-fe31f4546ab1	\N	deviceId	string	\N	\N	\N	\N	\N	\N	cam-west-002	\N	2026-08-28 14:14:19.772	2026-08-28 14:14:19.772
b48f3c46-a2a7-11f1-ae25-fe31f4546ab1	0	b48f1532-a2a7-11f1-ae25-fe31f4546ab1	b48f1532-a2a7-11f1-ae25-fe31f4546ab1	\N	deviceName	string	\N	\N	\N	\N	\N	\N	西门摄像头-02	\N	2026-08-28 14:14:19.772	2026-08-28 14:14:19.772
b48f3c47-a2a7-11f1-ae25-fe31f4546ab1	0	b48f1532-a2a7-11f1-ae25-fe31f4546ab1	b48f1532-a2a7-11f1-ae25-fe31f4546ab1	\N	PROCESS_START_USER_ID	long	\N	\N	\N	\N	\N	1	1	\N	2026-08-28 14:14:19.772	2026-08-28 14:14:19.772
b48f3c48-a2a7-11f1-ae25-fe31f4546ab1	0	b48f1532-a2a7-11f1-ae25-fe31f4546ab1	b48f1532-a2a7-11f1-ae25-fe31f4546ab1	\N	edgeNodeId	integer	\N	\N	\N	\N	\N	3	3	\N	2026-08-28 14:14:19.772	2026-08-28 14:14:19.772
b48f3c49-a2a7-11f1-ae25-fe31f4546ab1	0	b48f1532-a2a7-11f1-ae25-fe31f4546ab1	b48f1532-a2a7-11f1-ae25-fe31f4546ab1	\N	taskType	string	\N	\N	\N	\N	\N	\N	realtime	\N	2026-08-28 14:14:19.772	2026-08-28 14:14:19.772
b48f3c4a-a2a7-11f1-ae25-fe31f4546ab1	0	b48f1532-a2a7-11f1-ae25-fe31f4546ab1	b48f1532-a2a7-11f1-ae25-fe31f4546ab1	\N	imageUrl	string	\N	\N	\N	\N	\N	\N	http://localhost:9003/static/images/demo-alert-intrusion.png	\N	2026-08-28 14:14:19.772	2026-08-28 14:14:19.772
b48f3c4b-a2a7-11f1-ae25-fe31f4546ab1	0	b48f1532-a2a7-11f1-ae25-fe31f4546ab1	b48f1532-a2a7-11f1-ae25-fe31f4546ab1	\N	taskName	string	\N	\N	\N	\N	\N	\N	周界入侵检测	\N	2026-08-28 14:14:19.772	2026-08-28 14:14:19.772
b48f3c4c-a2a7-11f1-ae25-fe31f4546ab1	0	b48f1532-a2a7-11f1-ae25-fe31f4546ab1	b48f1532-a2a7-11f1-ae25-fe31f4546ab1	\N	alertObject	string	\N	\N	\N	\N	\N	\N	person	\N	2026-08-28 14:14:19.772	2026-08-28 14:14:19.772
b48f3c4d-a2a7-11f1-ae25-fe31f4546ab1	0	b48f1532-a2a7-11f1-ae25-fe31f4546ab1	b48f1532-a2a7-11f1-ae25-fe31f4546ab1	\N	alertId	integer	\N	\N	\N	\N	\N	40003	40003	\N	2026-08-28 14:14:19.772	2026-08-28 14:14:19.772
b48f3c4e-a2a7-11f1-ae25-fe31f4546ab1	0	b48f1532-a2a7-11f1-ae25-fe31f4546ab1	b48f1532-a2a7-11f1-ae25-fe31f4546ab1	\N	alertEvent	string	\N	\N	\N	\N	\N	\N	intrusion	\N	2026-08-28 14:14:19.772	2026-08-28 14:14:19.772
b48f3c4f-a2a7-11f1-ae25-fe31f4546ab1	0	b48f1532-a2a7-11f1-ae25-fe31f4546ab1	b48f1532-a2a7-11f1-ae25-fe31f4546ab1	\N	alertTime	string	\N	\N	\N	\N	\N	\N	2026-08-28 14:02:05	\N	2026-08-28 14:14:19.772	2026-08-28 14:14:19.772
b48f3c50-a2a7-11f1-ae25-fe31f4546ab1	0	b48f1532-a2a7-11f1-ae25-fe31f4546ab1	b48f1532-a2a7-11f1-ae25-fe31f4546ab1	\N	nodeId	integer	\N	\N	\N	\N	\N	12	12	\N	2026-08-28 14:14:19.772	2026-08-28 14:14:19.772
b48f3c51-a2a7-11f1-ae25-fe31f4546ab1	0	b48f1532-a2a7-11f1-ae25-fe31f4546ab1	b48f1532-a2a7-11f1-ae25-fe31f4546ab1	\N	taskId	integer	\N	\N	\N	\N	\N	50103	50103	\N	2026-08-28 14:14:19.772	2026-08-28 14:14:19.772
b48f3c44-a2a7-11f1-ae25-fe31f4546ab1	1	b48f1532-a2a7-11f1-ae25-fe31f4546ab1	b48f1532-a2a7-11f1-ae25-fe31f4546ab1	\N	PROCESS_INSTANCE_NAME	string	\N	\N	\N	\N	\N	\N	人员入侵告警处理（告警#40003）	\N	2026-08-28 14:14:19.772	2026-08-28 14:14:19.813
b49b715e-a2a7-11f1-ae25-fe31f4546ab1	0	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	\N	mi_assignees_task_manager_sign	serializable	\N	\N	\N	b49b715f-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	2026-08-28 14:14:19.852	2026-08-28 14:14:19.852
b49b7160-a2a7-11f1-ae25-fe31f4546ab1	0	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	\N	deviceId	string	\N	\N	\N	\N	\N	\N	smoke-wh-a	\N	2026-08-28 14:14:19.852	2026-08-28 14:14:19.852
b49b7161-a2a7-11f1-ae25-fe31f4546ab1	0	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	\N	deviceName	string	\N	\N	\N	\N	\N	\N	仓库A烟感探头	\N	2026-08-28 14:14:19.852	2026-08-28 14:14:19.852
b49b7162-a2a7-11f1-ae25-fe31f4546ab1	0	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	\N	PROCESS_START_USER_ID	long	\N	\N	\N	\N	\N	1	1	\N	2026-08-28 14:14:19.852	2026-08-28 14:14:19.852
b49b7163-a2a7-11f1-ae25-fe31f4546ab1	0	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	\N	edgeNodeId	integer	\N	\N	\N	\N	\N	3	3	\N	2026-08-28 14:14:19.852	2026-08-28 14:14:19.852
b49b7164-a2a7-11f1-ae25-fe31f4546ab1	0	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	\N	taskType	string	\N	\N	\N	\N	\N	\N	realtime	\N	2026-08-28 14:14:19.852	2026-08-28 14:14:19.852
b49b7165-a2a7-11f1-ae25-fe31f4546ab1	0	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	\N	imageUrl	string	\N	\N	\N	\N	\N	\N	http://localhost:9003/static/images/demo-alert-smoke.png	\N	2026-08-28 14:14:19.852	2026-08-28 14:14:19.852
b49b7166-a2a7-11f1-ae25-fe31f4546ab1	0	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	\N	taskName	string	\N	\N	\N	\N	\N	\N	烟感火情识别	\N	2026-08-28 14:14:19.852	2026-08-28 14:14:19.852
b49b7167-a2a7-11f1-ae25-fe31f4546ab1	0	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	\N	alertObject	string	\N	\N	\N	\N	\N	\N	smoke	\N	2026-08-28 14:14:19.852	2026-08-28 14:14:19.852
b49b7168-a2a7-11f1-ae25-fe31f4546ab1	0	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	\N	alertId	integer	\N	\N	\N	\N	\N	40004	40004	\N	2026-08-28 14:14:19.852	2026-08-28 14:14:19.852
b49b7169-a2a7-11f1-ae25-fe31f4546ab1	0	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	\N	alertEvent	string	\N	\N	\N	\N	\N	\N	smoke_fire	\N	2026-08-28 14:14:19.852	2026-08-28 14:14:19.852
b49b716a-a2a7-11f1-ae25-fe31f4546ab1	0	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	\N	alertTime	string	\N	\N	\N	\N	\N	\N	2026-08-28 14:05:33	\N	2026-08-28 14:14:19.853	2026-08-28 14:14:19.853
b49b987b-a2a7-11f1-ae25-fe31f4546ab1	0	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	\N	nodeId	integer	\N	\N	\N	\N	\N	12	12	\N	2026-08-28 14:14:19.853	2026-08-28 14:14:19.853
b49b987c-a2a7-11f1-ae25-fe31f4546ab1	0	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	\N	taskId	integer	\N	\N	\N	\N	\N	50104	50104	\N	2026-08-28 14:14:19.853	2026-08-28 14:14:19.853
b49afc2c-a2a7-11f1-ae25-fe31f4546ab1	1	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	\N	PROCESS_INSTANCE_NAME	string	\N	\N	\N	\N	\N	\N	烟感火情告警处理（告警#40004）	\N	2026-08-28 14:14:19.849	2026-08-28 14:14:19.891
b4a5d1b9-a2a7-11f1-ae25-fe31f4546ab1	0	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	\N	mi_assignees_task_manager_sign	serializable	\N	\N	\N	b4a5d1ba-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	2026-08-28 14:14:19.92	2026-08-28 14:14:19.92
b4a5d1b7-a2a7-11f1-ae25-fe31f4546ab1	1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	\N	PROCESS_INSTANCE_NAME	string	\N	\N	\N	\N	\N	\N	烟感火情告警处理（告警#40005）	\N	2026-08-28 14:14:19.92	2026-08-28 14:14:19.971
b4a5d1bb-a2a7-11f1-ae25-fe31f4546ab1	0	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	\N	deviceId	string	\N	\N	\N	\N	\N	\N	smoke-power-01	\N	2026-08-28 14:14:19.92	2026-08-28 14:14:19.92
b4a5d1bc-a2a7-11f1-ae25-fe31f4546ab1	0	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	\N	deviceName	string	\N	\N	\N	\N	\N	\N	配电房烟感探头	\N	2026-08-28 14:14:19.92	2026-08-28 14:14:19.92
b4a5d1bd-a2a7-11f1-ae25-fe31f4546ab1	0	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	\N	PROCESS_START_USER_ID	long	\N	\N	\N	\N	\N	1	1	\N	2026-08-28 14:14:19.92	2026-08-28 14:14:19.92
b4a5d1be-a2a7-11f1-ae25-fe31f4546ab1	0	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	\N	edgeNodeId	integer	\N	\N	\N	\N	\N	3	3	\N	2026-08-28 14:14:19.92	2026-08-28 14:14:19.92
b4a5d1bf-a2a7-11f1-ae25-fe31f4546ab1	0	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	\N	taskType	string	\N	\N	\N	\N	\N	\N	realtime	\N	2026-08-28 14:14:19.92	2026-08-28 14:14:19.92
b4a5d1c0-a2a7-11f1-ae25-fe31f4546ab1	0	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	\N	imageUrl	string	\N	\N	\N	\N	\N	\N	http://localhost:9003/static/images/demo-alert-smoke.png	\N	2026-08-28 14:14:19.92	2026-08-28 14:14:19.92
b4a5d1c1-a2a7-11f1-ae25-fe31f4546ab1	0	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	\N	taskName	string	\N	\N	\N	\N	\N	\N	烟感火情识别	\N	2026-08-28 14:14:19.92	2026-08-28 14:14:19.92
b4a5d1c2-a2a7-11f1-ae25-fe31f4546ab1	0	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	\N	alertObject	string	\N	\N	\N	\N	\N	\N	smoke	\N	2026-08-28 14:14:19.92	2026-08-28 14:14:19.92
b4a5d1c3-a2a7-11f1-ae25-fe31f4546ab1	0	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	\N	alertId	integer	\N	\N	\N	\N	\N	40005	40005	\N	2026-08-28 14:14:19.92	2026-08-28 14:14:19.92
b4a5d1c4-a2a7-11f1-ae25-fe31f4546ab1	0	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	\N	alertEvent	string	\N	\N	\N	\N	\N	\N	smoke_fire	\N	2026-08-28 14:14:19.92	2026-08-28 14:14:19.92
b4a5d1c5-a2a7-11f1-ae25-fe31f4546ab1	0	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	\N	alertTime	string	\N	\N	\N	\N	\N	\N	2026-08-28 14:07:12	\N	2026-08-28 14:14:19.92	2026-08-28 14:14:19.92
b4a5d1c6-a2a7-11f1-ae25-fe31f4546ab1	0	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	\N	nodeId	integer	\N	\N	\N	\N	\N	12	12	\N	2026-08-28 14:14:19.92	2026-08-28 14:14:19.92
b4a5d1c7-a2a7-11f1-ae25-fe31f4546ab1	0	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	\N	taskId	integer	\N	\N	\N	\N	\N	50105	50105	\N	2026-08-28 14:14:19.92	2026-08-28 14:14:19.92
b4b31843-a2a7-11f1-ae25-fe31f4546ab1	0	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	\N	deviceId	string	\N	\N	\N	\N	\N	\N	cam-park-in	\N	2026-08-28 14:14:20.007	2026-08-28 14:14:20.007
b4b31844-a2a7-11f1-ae25-fe31f4546ab1	0	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	\N	deviceName	string	\N	\N	\N	\N	\N	\N	停车场入口摄像头	\N	2026-08-28 14:14:20.007	2026-08-28 14:14:20.007
b4b31845-a2a7-11f1-ae25-fe31f4546ab1	0	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	\N	PROCESS_START_USER_ID	long	\N	\N	\N	\N	\N	1	1	\N	2026-08-28 14:14:20.007	2026-08-28 14:14:20.007
b4b31846-a2a7-11f1-ae25-fe31f4546ab1	0	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	\N	edgeNodeId	integer	\N	\N	\N	\N	\N	3	3	\N	2026-08-28 14:14:20.007	2026-08-28 14:14:20.007
b4b31847-a2a7-11f1-ae25-fe31f4546ab1	0	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	\N	taskType	string	\N	\N	\N	\N	\N	\N	realtime	\N	2026-08-28 14:14:20.007	2026-08-28 14:14:20.007
b4b31848-a2a7-11f1-ae25-fe31f4546ab1	0	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	\N	imageUrl	string	\N	\N	\N	\N	\N	\N	http://localhost:9003/static/images/demo-alert-parking.png	\N	2026-08-28 14:14:20.007	2026-08-28 14:14:20.007
b4b31849-a2a7-11f1-ae25-fe31f4546ab1	0	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	\N	taskName	string	\N	\N	\N	\N	\N	\N	车辆违停检测	\N	2026-08-28 14:14:20.007	2026-08-28 14:14:20.007
b4b3184a-a2a7-11f1-ae25-fe31f4546ab1	0	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	\N	alertObject	string	\N	\N	\N	\N	\N	\N	car	\N	2026-08-28 14:14:20.007	2026-08-28 14:14:20.007
b4b3184b-a2a7-11f1-ae25-fe31f4546ab1	0	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	\N	alertId	integer	\N	\N	\N	\N	\N	40006	40006	\N	2026-08-28 14:14:20.007	2026-08-28 14:14:20.007
b4b3184c-a2a7-11f1-ae25-fe31f4546ab1	0	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	\N	alertEvent	string	\N	\N	\N	\N	\N	\N	illegal_parking	\N	2026-08-28 14:14:20.007	2026-08-28 14:14:20.007
b4b3184d-a2a7-11f1-ae25-fe31f4546ab1	0	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	\N	alertTime	string	\N	\N	\N	\N	\N	\N	2026-08-28 14:10:48	\N	2026-08-28 14:14:20.007	2026-08-28 14:14:20.007
b4b3184e-a2a7-11f1-ae25-fe31f4546ab1	0	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	\N	nodeId	integer	\N	\N	\N	\N	\N	12	12	\N	2026-08-28 14:14:20.007	2026-08-28 14:14:20.007
b4b33f5f-a2a7-11f1-ae25-fe31f4546ab1	0	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	\N	taskId	integer	\N	\N	\N	\N	\N	50106	50106	\N	2026-08-28 14:14:20.008	2026-08-28 14:14:20.008
b4b31842-a2a7-11f1-ae25-fe31f4546ab1	1	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	\N	PROCESS_INSTANCE_NAME	string	\N	\N	\N	\N	\N	\N	人员入侵告警处理（告警#40006）	\N	2026-08-28 14:14:20.007	2026-08-28 14:14:20.04
d143b79a-a2a7-11f1-ae25-fe31f4546ab1	0	b47a0662-a2a7-11f1-ae25-fe31f4546ab1	b47a7ba2-a2a7-11f1-ae25-fe31f4546ab1	b47b17e6-a2a7-11f1-ae25-fe31f4546ab1	reason	string	\N	\N	\N	\N	\N	\N	确认告警属实，已通知安保前往东门处置	\N	2026-08-28 14:15:07.931	2026-08-28 14:15:07.931
d151c15f-a2a7-11f1-ae25-fe31f4546ab1	0	b4879b0a-a2a7-11f1-ae25-fe31f4546ab1	b487c22a-a2a7-11f1-ae25-fe31f4546ab1	b487c22e-a2a7-11f1-ae25-fe31f4546ab1	reason	string	\N	\N	\N	\N	\N	\N	复核为误报：画面为动物轮廓，非人员闯入	\N	2026-08-28 14:15:08.023	2026-08-28 14:15:08.023
d1520f80-a2a7-11f1-ae25-fe31f4546ab1	0	b4879b0a-a2a7-11f1-ae25-fe31f4546ab1	b4879b0a-a2a7-11f1-ae25-fe31f4546ab1	\N	PROCESS_STATUS	integer	\N	\N	\N	\N	\N	3	3	\N	2026-08-28 14:15:08.025	2026-08-28 14:15:08.025
d1525da1-a2a7-11f1-ae25-fe31f4546ab1	0	b4879b0a-a2a7-11f1-ae25-fe31f4546ab1	b4879b0a-a2a7-11f1-ae25-fe31f4546ab1	\N	PROCESS_REASON	string	\N	\N	\N	\N	\N	\N	复核为误报：画面为动物轮廓，非人员闯入	\N	2026-08-28 14:15:08.027	2026-08-28 14:15:08.027
d15bfa92-a2a7-11f1-ae25-fe31f4546ab1	0	b48f1532-a2a7-11f1-ae25-fe31f4546ab1	b48f1532-a2a7-11f1-ae25-fe31f4546ab1	\N	PROCESS_STATUS	integer	\N	\N	\N	\N	\N	4	4	\N	2026-08-28 14:15:08.09	2026-08-28 14:15:08.09
d15c96d3-a2a7-11f1-ae25-fe31f4546ab1	0	b48f1532-a2a7-11f1-ae25-fe31f4546ab1	b48f1532-a2a7-11f1-ae25-fe31f4546ab1	\N	PROCESS_REASON	string	\N	\N	\N	\N	\N	\N	重复告警，与东门事件为同一人员，合并处理	\N	2026-08-28 14:15:08.094	2026-08-28 14:15:08.094
d16919f6-a2a7-11f1-ae25-fe31f4546ab1	0	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	b49b987d-a2a7-11f1-ae25-fe31f4546ab1	b49b9881-a2a7-11f1-ae25-fe31f4546ab1	reason	string	\N	\N	\N	\N	\N	\N	已调取实时画面，确认烟雾，启动消防预案	\N	2026-08-28 14:15:08.176	2026-08-28 14:15:08.176
d16a2b69-a2a7-11f1-ae25-fe31f4546ab1	0	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	d16a0458-a2a7-11f1-ae25-fe31f4546ab1	\N	nrOfInstances	integer	\N	\N	\N	\N	\N	1	1	\N	2026-08-28 14:15:08.183	2026-08-28 14:15:08.183
d16a2b6d-a2a7-11f1-ae25-fe31f4546ab1	0	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	d16a2b6c-a2a7-11f1-ae25-fe31f4546ab1	\N	assignee	long	\N	\N	\N	\N	\N	1	1	\N	2026-08-28 14:15:08.183	2026-08-28 14:15:08.183
d16a2b6e-a2a7-11f1-ae25-fe31f4546ab1	0	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	d16a2b6c-a2a7-11f1-ae25-fe31f4546ab1	\N	loopCounter	integer	\N	\N	\N	\N	\N	0	0	\N	2026-08-28 14:15:08.183	2026-08-28 14:15:08.183
d175ea42-a2a7-11f1-ae25-fe31f4546ab1	0	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	d16a2b6c-a2a7-11f1-ae25-fe31f4546ab1	d16a2b70-a2a7-11f1-ae25-fe31f4546ab1	reason	string	\N	\N	\N	\N	\N	\N	现场复核确认，明火已扑灭，无人员伤亡	\N	2026-08-28 14:15:08.26	2026-08-28 14:15:08.26
d16a2b6a-a2a7-11f1-ae25-fe31f4546ab1	1	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	d16a0458-a2a7-11f1-ae25-fe31f4546ab1	\N	nrOfCompletedInstances	integer	\N	\N	\N	\N	\N	1	1	\N	2026-08-28 14:15:08.183	2026-08-28 14:15:08.269
d16a2b6b-a2a7-11f1-ae25-fe31f4546ab1	1	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	d16a0458-a2a7-11f1-ae25-fe31f4546ab1	\N	nrOfActiveInstances	integer	\N	\N	\N	\N	\N	0	0	\N	2026-08-28 14:15:08.183	2026-08-28 14:15:08.27
d18cf4b8-a2a7-11f1-ae25-fe31f4546ab1	0	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	b4a5d1c8-a2a7-11f1-ae25-fe31f4546ab1	b4a5d1cc-a2a7-11f1-ae25-fe31f4546ab1	reason	string	\N	\N	\N	\N	\N	\N	转主管会签复核	\N	2026-08-28 14:15:08.411	2026-08-28 14:15:08.411
d18e7b5b-a2a7-11f1-ae25-fe31f4546ab1	0	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	d18e062a-a2a7-11f1-ae25-fe31f4546ab1	\N	nrOfInstances	integer	\N	\N	\N	\N	\N	1	1	\N	2026-08-28 14:15:08.421	2026-08-28 14:15:08.421
d18e7b5c-a2a7-11f1-ae25-fe31f4546ab1	0	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	d18e062a-a2a7-11f1-ae25-fe31f4546ab1	\N	nrOfCompletedInstances	bpmnParallelMultiInstanceCompleted	\N	\N	\N	\N	\N	\N	d18e062a-a2a7-11f1-ae25-fe31f4546ab1	completed	2026-08-28 14:15:08.421	2026-08-28 14:15:08.421
d18e7b5d-a2a7-11f1-ae25-fe31f4546ab1	0	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	d18e062a-a2a7-11f1-ae25-fe31f4546ab1	\N	nrOfActiveInstances	bpmnParallelMultiInstanceCompleted	\N	\N	\N	\N	\N	\N	d18e062a-a2a7-11f1-ae25-fe31f4546ab1	active	2026-08-28 14:15:08.421	2026-08-28 14:15:08.421
d18ea26f-a2a7-11f1-ae25-fe31f4546ab1	0	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	d18e7b5e-a2a7-11f1-ae25-fe31f4546ab1	\N	assignee	long	\N	\N	\N	\N	\N	1	1	\N	2026-08-28 14:15:08.422	2026-08-28 14:15:08.422
d18ea270-a2a7-11f1-ae25-fe31f4546ab1	0	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	d18e7b5e-a2a7-11f1-ae25-fe31f4546ab1	\N	loopCounter	integer	\N	\N	\N	\N	\N	0	0	\N	2026-08-28 14:15:08.422	2026-08-28 14:15:08.422
d19d9694-a2a7-11f1-ae25-fe31f4546ab1	0	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	d18e7b5e-a2a7-11f1-ae25-fe31f4546ab1	d18ea272-a2a7-11f1-ae25-fe31f4546ab1	reason	string	\N	\N	\N	\N	\N	\N	配电房例行检修粉尘误报，退回重新核实	\N	2026-08-28 14:15:08.52	2026-08-28 14:15:08.52
d19de4b5-a2a7-11f1-ae25-fe31f4546ab1	0	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	\N	PROCESS_REASON	string	\N	\N	\N	\N	\N	\N	配电房例行检修粉尘误报，退回重新核实	\N	2026-08-28 14:15:08.522	2026-08-28 14:15:08.522
27192222-a2a8-11f1-ae25-fe31f4546ab1	0	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	mi_assignees_task_manager_sign	serializable	\N	\N	\N	27192223-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	2026-08-28 14:17:31.936	2026-08-28 14:17:31.936
27192224-a2a8-11f1-ae25-fe31f4546ab1	0	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	deviceId	string	\N	\N	\N	\N	\N	\N	smoke-wh-b	\N	2026-08-28 14:17:31.936	2026-08-28 14:17:31.936
27192225-a2a8-11f1-ae25-fe31f4546ab1	0	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	deviceName	string	\N	\N	\N	\N	\N	\N	仓库B烟感探头	\N	2026-08-28 14:17:31.936	2026-08-28 14:17:31.936
27192226-a2a8-11f1-ae25-fe31f4546ab1	0	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	PROCESS_START_USER_ID	long	\N	\N	\N	\N	\N	1	1	\N	2026-08-28 14:17:31.936	2026-08-28 14:17:31.936
27192227-a2a8-11f1-ae25-fe31f4546ab1	0	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	edgeNodeId	integer	\N	\N	\N	\N	\N	3	3	\N	2026-08-28 14:17:31.936	2026-08-28 14:17:31.936
27192228-a2a8-11f1-ae25-fe31f4546ab1	0	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	taskType	string	\N	\N	\N	\N	\N	\N	realtime	\N	2026-08-28 14:17:31.936	2026-08-28 14:17:31.936
27192229-a2a8-11f1-ae25-fe31f4546ab1	0	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	imageUrl	string	\N	\N	\N	\N	\N	\N	http://localhost:9003/static/images/demo-alert-smoke.png	\N	2026-08-28 14:17:31.936	2026-08-28 14:17:31.936
2719222a-a2a8-11f1-ae25-fe31f4546ab1	0	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	taskName	string	\N	\N	\N	\N	\N	\N	烟感火情识别	\N	2026-08-28 14:17:31.936	2026-08-28 14:17:31.936
2719222b-a2a8-11f1-ae25-fe31f4546ab1	0	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	alertObject	string	\N	\N	\N	\N	\N	\N	smoke	\N	2026-08-28 14:17:31.936	2026-08-28 14:17:31.936
2719222c-a2a8-11f1-ae25-fe31f4546ab1	0	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	alertId	integer	\N	\N	\N	\N	\N	40007	40007	\N	2026-08-28 14:17:31.936	2026-08-28 14:17:31.936
2719222d-a2a8-11f1-ae25-fe31f4546ab1	0	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	alertEvent	string	\N	\N	\N	\N	\N	\N	smoke_fire	\N	2026-08-28 14:17:31.936	2026-08-28 14:17:31.936
2719222e-a2a8-11f1-ae25-fe31f4546ab1	0	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	alertTime	string	\N	\N	\N	\N	\N	\N	2026-08-28 14:22:36	\N	2026-08-28 14:17:31.936	2026-08-28 14:17:31.936
2719222f-a2a8-11f1-ae25-fe31f4546ab1	0	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	nodeId	integer	\N	\N	\N	\N	\N	12	12	\N	2026-08-28 14:17:31.936	2026-08-28 14:17:31.936
27192230-a2a8-11f1-ae25-fe31f4546ab1	0	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	taskId	integer	\N	\N	\N	\N	\N	50107	50107	\N	2026-08-28 14:17:31.936	2026-08-28 14:17:31.936
27192220-a2a8-11f1-ae25-fe31f4546ab1	1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	PROCESS_INSTANCE_NAME	string	\N	\N	\N	\N	\N	\N	烟感火情告警处理（告警#40007）	\N	2026-08-28 14:17:31.936	2026-08-28 14:17:31.972
2722bf2c-a2a8-11f1-ae25-fe31f4546ab1	0	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	\N	deviceId	string	\N	\N	\N	\N	\N	\N	cam-yard-004	\N	2026-08-28 14:17:31.999	2026-08-28 14:17:31.999
2722bf2d-a2a8-11f1-ae25-fe31f4546ab1	0	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	\N	deviceName	string	\N	\N	\N	\N	\N	\N	后院摄像头-04	\N	2026-08-28 14:17:31.999	2026-08-28 14:17:31.999
2722bf2e-a2a8-11f1-ae25-fe31f4546ab1	0	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	\N	PROCESS_START_USER_ID	long	\N	\N	\N	\N	\N	1	1	\N	2026-08-28 14:17:31.999	2026-08-28 14:17:31.999
2722bf2b-a2a8-11f1-ae25-fe31f4546ab1	1	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	\N	PROCESS_INSTANCE_NAME	string	\N	\N	\N	\N	\N	\N	人员入侵告警处理（告警#40008）	\N	2026-08-28 14:17:31.999	2026-08-28 14:17:32.057
2722bf2f-a2a8-11f1-ae25-fe31f4546ab1	0	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	\N	edgeNodeId	integer	\N	\N	\N	\N	\N	3	3	\N	2026-08-28 14:17:31.999	2026-08-28 14:17:31.999
2722bf30-a2a8-11f1-ae25-fe31f4546ab1	0	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	\N	taskType	string	\N	\N	\N	\N	\N	\N	realtime	\N	2026-08-28 14:17:31.999	2026-08-28 14:17:31.999
2722bf31-a2a8-11f1-ae25-fe31f4546ab1	0	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	\N	imageUrl	string	\N	\N	\N	\N	\N	\N	http://localhost:9003/static/images/demo-alert-intrusion.png	\N	2026-08-28 14:17:31.999	2026-08-28 14:17:31.999
2722bf32-a2a8-11f1-ae25-fe31f4546ab1	0	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	\N	taskName	string	\N	\N	\N	\N	\N	\N	夜间徘徊检测	\N	2026-08-28 14:17:31.999	2026-08-28 14:17:31.999
2722bf33-a2a8-11f1-ae25-fe31f4546ab1	0	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	\N	alertObject	string	\N	\N	\N	\N	\N	\N	person	\N	2026-08-28 14:17:31.999	2026-08-28 14:17:31.999
2722bf34-a2a8-11f1-ae25-fe31f4546ab1	0	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	\N	alertId	integer	\N	\N	\N	\N	\N	40008	40008	\N	2026-08-28 14:17:31.999	2026-08-28 14:17:31.999
2722bf35-a2a8-11f1-ae25-fe31f4546ab1	0	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	\N	alertEvent	string	\N	\N	\N	\N	\N	\N	loitering	\N	2026-08-28 14:17:31.999	2026-08-28 14:17:31.999
2722bf36-a2a8-11f1-ae25-fe31f4546ab1	0	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	\N	alertTime	string	\N	\N	\N	\N	\N	\N	2026-08-28 14:20:02	\N	2026-08-28 14:17:31.999	2026-08-28 14:17:31.999
2722e647-a2a8-11f1-ae25-fe31f4546ab1	0	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	\N	nodeId	integer	\N	\N	\N	\N	\N	12	12	\N	2026-08-28 14:17:32	2026-08-28 14:17:32
2722e648-a2a8-11f1-ae25-fe31f4546ab1	0	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	\N	taskId	integer	\N	\N	\N	\N	\N	50108	50108	\N	2026-08-28 14:17:32	2026-08-28 14:17:32
315f71b3-a2a8-11f1-ae25-fe31f4546ab1	0	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	27192231-a2a8-11f1-ae25-fe31f4546ab1	27194945-a2a8-11f1-ae25-fe31f4546ab1	reason	string	\N	\N	\N	\N	\N	\N	画面确认有烟雾，转主管会签	\N	2026-08-28 14:17:49.174	2026-08-28 14:17:49.174
31603506-a2a8-11f1-ae25-fe31f4546ab1	0	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	31600df5-a2a8-11f1-ae25-fe31f4546ab1	\N	nrOfInstances	integer	\N	\N	\N	\N	\N	2	2	\N	2026-08-28 14:17:49.179	2026-08-28 14:17:49.179
31603507-a2a8-11f1-ae25-fe31f4546ab1	0	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	31600df5-a2a8-11f1-ae25-fe31f4546ab1	\N	nrOfCompletedInstances	bpmnParallelMultiInstanceCompleted	\N	\N	\N	\N	\N	\N	31600df5-a2a8-11f1-ae25-fe31f4546ab1	completed	2026-08-28 14:17:49.179	2026-08-28 14:17:49.179
31603508-a2a8-11f1-ae25-fe31f4546ab1	0	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	31600df5-a2a8-11f1-ae25-fe31f4546ab1	\N	nrOfActiveInstances	bpmnParallelMultiInstanceCompleted	\N	\N	\N	\N	\N	\N	31600df5-a2a8-11f1-ae25-fe31f4546ab1	active	2026-08-28 14:17:49.179	2026-08-28 14:17:49.179
3160350b-a2a8-11f1-ae25-fe31f4546ab1	0	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	31603509-a2a8-11f1-ae25-fe31f4546ab1	\N	assignee	long	\N	\N	\N	\N	\N	1	1	\N	2026-08-28 14:17:49.179	2026-08-28 14:17:49.179
3160350c-a2a8-11f1-ae25-fe31f4546ab1	0	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	3160350a-a2a8-11f1-ae25-fe31f4546ab1	\N	assignee	long	\N	\N	\N	\N	\N	104	104	\N	2026-08-28 14:17:49.179	2026-08-28 14:17:49.179
3160350d-a2a8-11f1-ae25-fe31f4546ab1	0	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	31603509-a2a8-11f1-ae25-fe31f4546ab1	\N	loopCounter	integer	\N	\N	\N	\N	\N	0	0	\N	2026-08-28 14:17:49.179	2026-08-28 14:17:49.179
31653e21-a2a8-11f1-ae25-fe31f4546ab1	0	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	3160350a-a2a8-11f1-ae25-fe31f4546ab1	\N	loopCounter	integer	\N	\N	\N	\N	\N	1	1	\N	2026-08-28 14:17:49.212	2026-08-28 14:17:49.212
3170d6e6-a2a8-11f1-ae25-fe31f4546ab1	0	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	31603509-a2a8-11f1-ae25-fe31f4546ab1	3160350f-a2a8-11f1-ae25-fe31f4546ab1	reason	string	\N	\N	\N	\N	\N	\N	已安排值守，等待测试号复核	\N	2026-08-28 14:17:49.288	2026-08-28 14:17:49.288
40efae22-a2ac-11f1-83a4-6e81fb0021bd	0	40ef870f-a2ac-11f1-83a4-6e81fb0021bd	40ef870f-a2ac-11f1-83a4-6e81fb0021bd	\N	deviceId	string	\N	\N	\N	\N	\N	\N	cam-north-005	\N	2026-08-28 14:46:53.272	2026-08-28 14:46:53.272
40efae23-a2ac-11f1-83a4-6e81fb0021bd	0	40ef870f-a2ac-11f1-83a4-6e81fb0021bd	40ef870f-a2ac-11f1-83a4-6e81fb0021bd	\N	deviceName	string	\N	\N	\N	\N	\N	\N	北门摄像头-05	\N	2026-08-28 14:46:53.272	2026-08-28 14:46:53.272
40efae24-a2ac-11f1-83a4-6e81fb0021bd	0	40ef870f-a2ac-11f1-83a4-6e81fb0021bd	40ef870f-a2ac-11f1-83a4-6e81fb0021bd	\N	PROCESS_START_USER_ID	long	\N	\N	\N	\N	\N	1	1	\N	2026-08-28 14:46:53.272	2026-08-28 14:46:53.272
40efae25-a2ac-11f1-83a4-6e81fb0021bd	0	40ef870f-a2ac-11f1-83a4-6e81fb0021bd	40ef870f-a2ac-11f1-83a4-6e81fb0021bd	\N	edgeNodeId	integer	\N	\N	\N	\N	\N	3	3	\N	2026-08-28 14:46:53.272	2026-08-28 14:46:53.272
40efae26-a2ac-11f1-83a4-6e81fb0021bd	0	40ef870f-a2ac-11f1-83a4-6e81fb0021bd	40ef870f-a2ac-11f1-83a4-6e81fb0021bd	\N	taskType	string	\N	\N	\N	\N	\N	\N	realtime	\N	2026-08-28 14:46:53.272	2026-08-28 14:46:53.272
40efae27-a2ac-11f1-83a4-6e81fb0021bd	0	40ef870f-a2ac-11f1-83a4-6e81fb0021bd	40ef870f-a2ac-11f1-83a4-6e81fb0021bd	\N	imageUrl	string	\N	\N	\N	\N	\N	\N	http://localhost:9003/static/images/demo-alert-intrusion.png	\N	2026-08-28 14:46:53.272	2026-08-28 14:46:53.272
40efae28-a2ac-11f1-83a4-6e81fb0021bd	0	40ef870f-a2ac-11f1-83a4-6e81fb0021bd	40ef870f-a2ac-11f1-83a4-6e81fb0021bd	\N	taskName	string	\N	\N	\N	\N	\N	\N	周界入侵检测	\N	2026-08-28 14:46:53.272	2026-08-28 14:46:53.272
40efae29-a2ac-11f1-83a4-6e81fb0021bd	0	40ef870f-a2ac-11f1-83a4-6e81fb0021bd	40ef870f-a2ac-11f1-83a4-6e81fb0021bd	\N	alertObject	string	\N	\N	\N	\N	\N	\N	person	\N	2026-08-28 14:46:53.272	2026-08-28 14:46:53.272
40efae2a-a2ac-11f1-83a4-6e81fb0021bd	0	40ef870f-a2ac-11f1-83a4-6e81fb0021bd	40ef870f-a2ac-11f1-83a4-6e81fb0021bd	\N	alertId	integer	\N	\N	\N	\N	\N	40009	40009	\N	2026-08-28 14:46:53.272	2026-08-28 14:46:53.272
40efae2b-a2ac-11f1-83a4-6e81fb0021bd	0	40ef870f-a2ac-11f1-83a4-6e81fb0021bd	40ef870f-a2ac-11f1-83a4-6e81fb0021bd	\N	alertEvent	string	\N	\N	\N	\N	\N	\N	intrusion	\N	2026-08-28 14:46:53.272	2026-08-28 14:46:53.272
40efae2c-a2ac-11f1-83a4-6e81fb0021bd	0	40ef870f-a2ac-11f1-83a4-6e81fb0021bd	40ef870f-a2ac-11f1-83a4-6e81fb0021bd	\N	alertTime	string	\N	\N	\N	\N	\N	\N	2026-08-28 14:47:52	\N	2026-08-28 14:46:53.272	2026-08-28 14:46:53.272
40efae2d-a2ac-11f1-83a4-6e81fb0021bd	0	40ef870f-a2ac-11f1-83a4-6e81fb0021bd	40ef870f-a2ac-11f1-83a4-6e81fb0021bd	\N	nodeId	integer	\N	\N	\N	\N	\N	12	12	\N	2026-08-28 14:46:53.273	2026-08-28 14:46:53.273
40efd53e-a2ac-11f1-83a4-6e81fb0021bd	0	40ef870f-a2ac-11f1-83a4-6e81fb0021bd	40ef870f-a2ac-11f1-83a4-6e81fb0021bd	\N	taskId	integer	\N	\N	\N	\N	\N	50109	50109	\N	2026-08-28 14:46:53.273	2026-08-28 14:46:53.273
40efae21-a2ac-11f1-83a4-6e81fb0021bd	1	40ef870f-a2ac-11f1-83a4-6e81fb0021bd	40ef870f-a2ac-11f1-83a4-6e81fb0021bd	\N	PROCESS_INSTANCE_NAME	string	\N	\N	\N	\N	\N	\N	人员入侵告警处理（告警#40009）	\N	2026-08-28 14:46:53.272	2026-08-28 14:46:53.341
4825b059-a2ac-11f1-83a4-6e81fb0021bd	0	40ef870f-a2ac-11f1-83a4-6e81fb0021bd	40efd53f-a2ac-11f1-83a4-6e81fb0021bd	40f10dc3-a2ac-11f1-83a4-6e81fb0021bd	reason	string	\N	\N	\N	\N	\N	\N	北门复核通过（重放脚本新建路径验证）	\N	2026-08-28 14:47:05.37	2026-08-28 14:47:05.37
\.


--
-- Data for Name: act_id_bytearray; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.act_id_bytearray (id_, rev_, name_, bytes_) FROM stdin;
\.


--
-- Data for Name: act_id_group; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.act_id_group (id_, rev_, name_, type_) FROM stdin;
\.


--
-- Data for Name: act_id_info; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.act_id_info (id_, rev_, user_id_, type_, key_, value_, password_, parent_id_) FROM stdin;
\.


--
-- Data for Name: act_id_membership; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.act_id_membership (user_id_, group_id_) FROM stdin;
\.


--
-- Data for Name: act_id_priv; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.act_id_priv (id_, name_) FROM stdin;
\.


--
-- Data for Name: act_id_priv_mapping; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.act_id_priv_mapping (id_, priv_id_, user_id_, group_id_) FROM stdin;
\.


--
-- Data for Name: act_id_property; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.act_id_property (name_, value_, rev_) FROM stdin;
schema.version	6.8.0.0	1
\.


--
-- Data for Name: act_id_token; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.act_id_token (id_, rev_, token_value_, token_date_, ip_address_, user_agent_, user_id_, token_data_) FROM stdin;
\.


--
-- Data for Name: act_id_user; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.act_id_user (id_, rev_, first_, last_, display_name_, email_, pwd_, picture_id_, tenant_id_) FROM stdin;
\.


--
-- Data for Name: act_procdef_info; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.act_procdef_info (id_, proc_def_id_, rev_, info_json_id_) FROM stdin;
\.


--
-- Data for Name: act_re_deployment; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.act_re_deployment (id_, name_, category_, key_, tenant_id_, deploy_time_, derived_from_, derived_from_root_, parent_deployment_id_, engine_version_) FROM stdin;
a2baa4ef-a29a-11f1-9a15-aefacda18209	人员入侵告警处理	alert_handle	alert_intrusion		2026-08-28 12:40:46.4	\N	\N	a2baa4ef-a29a-11f1-9a15-aefacda18209	\N
3da637e6-a29b-11f1-8fa2-aefacda18209	人员入侵告警处理	alert_handle	alert_intrusion		2026-08-28 12:45:06.313	\N	\N	3da637e6-a29b-11f1-8fa2-aefacda18209	\N
5623a25c-a2a7-11f1-ae25-fe31f4546ab1	烟感火情告警处理	alert_handle	alert_fire_smoke		2026-08-28 14:11:41.361	\N	\N	5623a25c-a2a7-11f1-ae25-fe31f4546ab1	\N
a033e67f-a2a7-11f1-ae25-fe31f4546ab1	烟感火情告警处理	alert_handle	alert_fire_smoke		2026-08-28 14:13:45.619	\N	\N	a033e67f-a2a7-11f1-ae25-fe31f4546ab1	\N
202bc1bb-a2a8-11f1-ae25-fe31f4546ab1	烟感火情告警处理	alert_handle	alert_fire_smoke		2026-08-28 14:17:20.314	\N	\N	202bc1bb-a2a8-11f1-ae25-fe31f4546ab1	\N
\.


--
-- Data for Name: act_re_model; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.act_re_model (id_, rev_, name_, key_, category_, create_time_, last_update_time_, version_, meta_info_, deployment_id_, editor_source_value_id_, editor_source_extra_value_id_, tenant_id_) FROM stdin;
4481b330-a29a-11f1-b3db-aefacda18209	4	人员入侵告警处理	alert_intrusion	alert_handle	2026-08-28 12:38:08.321	2026-08-28 12:45:06.38	1	{"formType":10,"deploymentId":"3da637e6-a29b-11f1-8fa2-aefacda18209","name":"人员入侵告警处理","category":"alert_handle","type":1}	\N	4483d611-a29a-11f1-b3db-aefacda18209	\N	
50bb0d3a-a2a7-11f1-ae25-fe31f4546ab1	5	烟感火情告警处理	alert_fire_smoke	alert_handle	2026-08-28 14:11:32.287	2026-08-28 14:17:20.342	1	{"formType":10,"deploymentId":"202bc1bb-a2a8-11f1-ae25-fe31f4546ab1","name":"烟感火情告警处理","category":"alert_handle","type":1}	\N	50bbd08b-a2a7-11f1-ae25-fe31f4546ab1	\N	
\.


--
-- Data for Name: act_re_procdef; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.act_re_procdef (id_, rev_, category_, name_, key_, version_, deployment_id_, resource_name_, dgrm_resource_name_, description_, has_start_form_key_, has_graphical_notation_, suspension_state_, tenant_id_, derived_from_, derived_from_root_, derived_version_, engine_version_) FROM stdin;
alert_intrusion:1:a2c441e1-a29a-11f1-9a15-aefacda18209	1	http://www.flowable.org/test	人员入侵告警处理	alert_intrusion	1	a2baa4ef-a29a-11f1-9a15-aefacda18209	alert_intrusion.bpmn	\N	\N	f	f	1		\N	\N	0	\N
alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	1	alert_handle	人员入侵告警处理	alert_intrusion	2	3da637e6-a29b-11f1-8fa2-aefacda18209	alert_intrusion.bpmn	\N	\N	f	f	1		\N	\N	0	\N
alert_fire_smoke:1:562cca1e-a2a7-11f1-ae25-fe31f4546ab1	1	alert_handle	烟感火情告警处理	alert_fire_smoke	1	5623a25c-a2a7-11f1-ae25-fe31f4546ab1	alert_fire_smoke.bpmn	\N	\N	f	f	1		\N	\N	0	\N
alert_fire_smoke:2:a035bb41-a2a7-11f1-ae25-fe31f4546ab1	1	alert_handle	烟感火情告警处理	alert_fire_smoke	2	a033e67f-a2a7-11f1-ae25-fe31f4546ab1	alert_fire_smoke.bpmn	\N	\N	f	f	1		\N	\N	0	\N
alert_fire_smoke:3:202ef60d-a2a8-11f1-ae25-fe31f4546ab1	1	alert_handle	烟感火情告警处理	alert_fire_smoke	3	202bc1bb-a2a8-11f1-ae25-fe31f4546ab1	alert_fire_smoke.bpmn	\N	\N	f	f	1		\N	\N	0	\N
\.


--
-- Data for Name: act_ru_actinst; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.act_ru_actinst (id_, rev_, proc_def_id_, proc_inst_id_, execution_id_, act_id_, task_id_, call_proc_inst_id_, act_name_, act_type_, assignee_, start_time_, end_time_, duration_, transaction_order_, delete_reason_, tenant_id_) FROM stdin;
68bb939e-a29b-11f1-8fa2-aefacda18209	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	68bb9399-a29b-11f1-8fa2-aefacda18209	68bb939d-a29b-11f1-8fa2-aefacda18209	start_event	\N	\N	开始	startEvent	\N	2026-08-28 12:46:18.595	2026-08-28 12:46:18.595	0	1	\N	
68bb939f-a29b-11f1-8fa2-aefacda18209	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	68bb9399-a29b-11f1-8fa2-aefacda18209	68bb939d-a29b-11f1-8fa2-aefacda18209	flow_task_1	\N	\N	\N	sequenceFlow	\N	2026-08-28 12:46:18.595	2026-08-28 12:46:18.595	0	2	\N	
68bb93a0-a29b-11f1-8fa2-aefacda18209	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	68bb9399-a29b-11f1-8fa2-aefacda18209	68bb939d-a29b-11f1-8fa2-aefacda18209	task_1	68bbbab1-a29b-11f1-8fa2-aefacda18209	\N	审批人	userTask	\N	2026-08-28 12:46:18.595	\N	\N	3	\N	
b4175c1d-a2a1-11f1-aee5-5a91bd373cd1	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	b4173508-a2a1-11f1-aee5-5a91bd373cd1	b4175c1c-a2a1-11f1-aee5-5a91bd373cd1	start_event	\N	\N	开始	startEvent	\N	2026-08-28 13:31:22.006	2026-08-28 13:31:22.008	2	1	\N	
b417d14e-a2a1-11f1-aee5-5a91bd373cd1	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	b4173508-a2a1-11f1-aee5-5a91bd373cd1	b4175c1c-a2a1-11f1-aee5-5a91bd373cd1	flow_task_1	\N	\N	\N	sequenceFlow	\N	2026-08-28 13:31:22.009	2026-08-28 13:31:22.009	0	2	\N	
b417d14f-a2a1-11f1-aee5-5a91bd373cd1	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	b4173508-a2a1-11f1-aee5-5a91bd373cd1	b4175c1c-a2a1-11f1-aee5-5a91bd373cd1	task_1	b418e2c0-a2a1-11f1-aee5-5a91bd373cd1	\N	审批人	userTask	\N	2026-08-28 13:31:22.009	\N	\N	3	\N	
eccf2a77-a2a1-11f1-a0a7-f2ebdc74e900	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	eccedc52-a2a1-11f1-a0a7-f2ebdc74e900	eccf2a76-a2a1-11f1-a0a7-f2ebdc74e900	start_event	\N	\N	开始	startEvent	\N	2026-08-28 13:32:57.163	2026-08-28 13:32:57.165	2	1	\N	
eccf7898-a2a1-11f1-a0a7-f2ebdc74e900	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	eccedc52-a2a1-11f1-a0a7-f2ebdc74e900	eccf2a76-a2a1-11f1-a0a7-f2ebdc74e900	flow_task_1	\N	\N	\N	sequenceFlow	\N	2026-08-28 13:32:57.165	2026-08-28 13:32:57.165	0	2	\N	
eccf7899-a2a1-11f1-a0a7-f2ebdc74e900	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	eccedc52-a2a1-11f1-a0a7-f2ebdc74e900	eccf2a76-a2a1-11f1-a0a7-f2ebdc74e900	task_1	ecd0b11a-a2a1-11f1-a0a7-f2ebdc74e900	\N	审批人	userTask	\N	2026-08-28 13:32:57.165	\N	\N	3	\N	
0d755204-a2a2-11f1-a0a7-f2ebdc74e900	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	0d7551ff-a2a2-11f1-a0a7-f2ebdc74e900	0d755203-a2a2-11f1-a0a7-f2ebdc74e900	start_event	\N	\N	开始	startEvent	\N	2026-08-28 13:33:51.939	2026-08-28 13:33:51.939	0	1	\N	
0d755205-a2a2-11f1-a0a7-f2ebdc74e900	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	0d7551ff-a2a2-11f1-a0a7-f2ebdc74e900	0d755203-a2a2-11f1-a0a7-f2ebdc74e900	flow_task_1	\N	\N	\N	sequenceFlow	\N	2026-08-28 13:33:51.939	2026-08-28 13:33:51.939	0	2	\N	
0d755206-a2a2-11f1-a0a7-f2ebdc74e900	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	0d7551ff-a2a2-11f1-a0a7-f2ebdc74e900	0d755203-a2a2-11f1-a0a7-f2ebdc74e900	task_1	0d755207-a2a2-11f1-a0a7-f2ebdc74e900	\N	审批人	userTask	\N	2026-08-28 13:33:51.939	\N	\N	3	\N	
b4a5d1c9-a2a7-11f1-ae25-fe31f4546ab1	1	alert_fire_smoke:2:a035bb41-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	b4a5d1c8-a2a7-11f1-ae25-fe31f4546ab1	start_event	\N	\N	开始	startEvent	\N	2026-08-28 14:14:19.92	2026-08-28 14:14:19.92	0	1	\N	
b4a5d1ca-a2a7-11f1-ae25-fe31f4546ab1	1	alert_fire_smoke:2:a035bb41-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	b4a5d1c8-a2a7-11f1-ae25-fe31f4546ab1	flow_task_specialist	\N	\N	\N	sequenceFlow	\N	2026-08-28 14:14:19.92	2026-08-28 14:14:19.92	0	2	\N	
b4b33f61-a2a7-11f1-ae25-fe31f4546ab1	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	b4b33f60-a2a7-11f1-ae25-fe31f4546ab1	start_event	\N	\N	开始	startEvent	\N	2026-08-28 14:14:20.008	2026-08-28 14:14:20.008	0	1	\N	
b4b33f62-a2a7-11f1-ae25-fe31f4546ab1	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	b4b33f60-a2a7-11f1-ae25-fe31f4546ab1	flow_task_1	\N	\N	\N	sequenceFlow	\N	2026-08-28 14:14:20.008	2026-08-28 14:14:20.008	0	2	\N	
b4b33f63-a2a7-11f1-ae25-fe31f4546ab1	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	b4b33f60-a2a7-11f1-ae25-fe31f4546ab1	task_1	b4b33f64-a2a7-11f1-ae25-fe31f4546ab1	\N	审批人	userTask	\N	2026-08-28 14:14:20.008	\N	\N	3	\N	
d18ddf19-a2a7-11f1-ae25-fe31f4546ab1	1	alert_fire_smoke:2:a035bb41-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	b4a5d1c8-a2a7-11f1-ae25-fe31f4546ab1	flow_task_manager_sign	\N	\N	\N	sequenceFlow	\N	2026-08-28 14:15:08.417	2026-08-28 14:15:08.417	0	1	\N	
b4a5d1cb-a2a7-11f1-ae25-fe31f4546ab1	3	alert_fire_smoke:2:a035bb41-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	b4a5d1c8-a2a7-11f1-ae25-fe31f4546ab1	task_specialist	b4a5d1cc-a2a7-11f1-ae25-fe31f4546ab1	\N	安全专员初审	userTask	1	2026-08-28 14:14:19.92	2026-08-28 14:15:08.417	48497	3	\N	
d19f4447-a2a7-11f1-ae25-fe31f4546ab1	1	alert_fire_smoke:2:a035bb41-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	d19f4446-a2a7-11f1-ae25-fe31f4546ab1	task_specialist	d19f4448-a2a7-11f1-ae25-fe31f4546ab1	\N	安全专员初审	userTask	\N	2026-08-28 14:15:08.531	\N	\N	1	\N	
d18ea271-a2a7-11f1-ae25-fe31f4546ab1	2	alert_fire_smoke:2:a035bb41-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	d18e7b5e-a2a7-11f1-ae25-fe31f4546ab1	task_manager_sign	d18ea272-a2a7-11f1-ae25-fe31f4546ab1	\N	主管会签确认	userTask	1	2026-08-28 14:15:08.422	2026-08-28 14:15:08.528	106	2	Change parent activity to task_specialist	
27192232-a2a8-11f1-ae25-fe31f4546ab1	1	alert_fire_smoke:3:202ef60d-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	27192231-a2a8-11f1-ae25-fe31f4546ab1	start_event	\N	\N	开始	startEvent	\N	2026-08-28 14:17:31.937	2026-08-28 14:17:31.937	0	1	\N	
27194943-a2a8-11f1-ae25-fe31f4546ab1	1	alert_fire_smoke:3:202ef60d-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	27192231-a2a8-11f1-ae25-fe31f4546ab1	flow_task_specialist	\N	\N	\N	sequenceFlow	\N	2026-08-28 14:17:31.937	2026-08-28 14:17:31.937	0	2	\N	
2722e64a-a2a8-11f1-ae25-fe31f4546ab1	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	2722e649-a2a8-11f1-ae25-fe31f4546ab1	start_event	\N	\N	开始	startEvent	\N	2026-08-28 14:17:32	2026-08-28 14:17:32	0	1	\N	
2722e64b-a2a8-11f1-ae25-fe31f4546ab1	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	2722e649-a2a8-11f1-ae25-fe31f4546ab1	flow_task_1	\N	\N	\N	sequenceFlow	\N	2026-08-28 14:17:32	2026-08-28 14:17:32	0	2	\N	
2722e64c-a2a8-11f1-ae25-fe31f4546ab1	1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	2722e649-a2a8-11f1-ae25-fe31f4546ab1	task_1	2722e64d-a2a8-11f1-ae25-fe31f4546ab1	\N	审批人	userTask	\N	2026-08-28 14:17:32	\N	\N	3	\N	
31600df4-a2a8-11f1-ae25-fe31f4546ab1	1	alert_fire_smoke:3:202ef60d-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	27192231-a2a8-11f1-ae25-fe31f4546ab1	flow_task_manager_sign	\N	\N	\N	sequenceFlow	\N	2026-08-28 14:17:49.178	2026-08-28 14:17:49.178	0	1	\N	
31653e22-a2a8-11f1-ae25-fe31f4546ab1	1	alert_fire_smoke:3:202ef60d-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	3160350a-a2a8-11f1-ae25-fe31f4546ab1	task_manager_sign	31656533-a2a8-11f1-ae25-fe31f4546ab1	\N	主管会签确认	userTask	104	2026-08-28 14:17:49.212	\N	\N	3	\N	
27194944-a2a8-11f1-ae25-fe31f4546ab1	3	alert_fire_smoke:3:202ef60d-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	27192231-a2a8-11f1-ae25-fe31f4546ab1	task_specialist	27194945-a2a8-11f1-ae25-fe31f4546ab1	\N	安全专员初审	userTask	1	2026-08-28 14:17:31.937	2026-08-28 14:17:49.177	17240	3	\N	
3160350e-a2a8-11f1-ae25-fe31f4546ab1	2	alert_fire_smoke:3:202ef60d-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	31603509-a2a8-11f1-ae25-fe31f4546ab1	task_manager_sign	3160350f-a2a8-11f1-ae25-fe31f4546ab1	\N	主管会签确认	userTask	1	2026-08-28 14:17:49.179	2026-08-28 14:17:49.291	112	2	\N	
\.


--
-- Data for Name: act_ru_deadletter_job; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.act_ru_deadletter_job (id_, rev_, category_, type_, exclusive_, execution_id_, process_instance_id_, proc_def_id_, element_id_, element_name_, scope_id_, sub_scope_id_, scope_type_, scope_definition_id_, correlation_id_, exception_stack_id_, exception_msg_, duedate_, repeat_, handler_type_, handler_cfg_, custom_values_id_, create_time_, tenant_id_) FROM stdin;
\.


--
-- Data for Name: act_ru_entitylink; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.act_ru_entitylink (id_, rev_, create_time_, link_type_, scope_id_, sub_scope_id_, scope_type_, scope_definition_id_, parent_element_id_, ref_scope_id_, ref_scope_type_, ref_scope_definition_id_, root_scope_id_, root_scope_type_, hierarchy_type_) FROM stdin;
\.


--
-- Data for Name: act_ru_event_subscr; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.act_ru_event_subscr (id_, rev_, event_type_, event_name_, execution_id_, proc_inst_id_, activity_id_, configuration_, created_, proc_def_id_, sub_scope_id_, scope_id_, scope_definition_id_, scope_type_, lock_time_, lock_owner_, tenant_id_) FROM stdin;
\.


--
-- Data for Name: act_ru_execution; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.act_ru_execution (id_, rev_, proc_inst_id_, business_key_, parent_id_, proc_def_id_, super_exec_, root_proc_inst_id_, act_id_, is_active_, is_concurrent_, is_scope_, is_event_scope_, is_mi_root_, suspension_state_, cached_ent_state_, tenant_id_, name_, start_act_id_, start_time_, start_user_id_, lock_time_, lock_owner_, is_count_enabled_, evt_subscr_count_, task_count_, job_count_, timer_job_count_, susp_job_count_, deadletter_job_count_, external_worker_job_count_, var_count_, id_link_count_, callback_id_, callback_type_, reference_id_, reference_type_, propagated_stage_inst_id_, business_status_) FROM stdin;
2722bf29-a2a8-11f1-ae25-fe31f4546ab1	3	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	alert:40008	\N	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	\N	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	\N	t	f	t	f	f	1	\N		人员入侵告警处理（告警#40008）	start_event	2026-08-28 14:17:31.999	1	\N	\N	t	0	0	0	0	0	0	0	0	0	\N	\N	\N	\N	\N	\N
31600df5-a2a8-11f1-ae25-fe31f4546ab1	1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	alert_fire_smoke:3:202ef60d-a2a8-11f1-ae25-fe31f4546ab1	\N	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	task_manager_sign	f	f	f	f	t	1	\N		\N	\N	2026-08-28 14:17:49.178	\N	\N	\N	t	0	0	0	0	0	0	0	3	0	\N	\N	\N	\N	\N	\N
68bb939d-a29b-11f1-8fa2-aefacda18209	1	68bb9399-a29b-11f1-8fa2-aefacda18209	\N	68bb9399-a29b-11f1-8fa2-aefacda18209	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	\N	68bb9399-a29b-11f1-8fa2-aefacda18209	task_1	t	f	f	f	f	1	\N		\N	\N	2026-08-28 12:46:18.595	\N	\N	\N	t	0	1	0	0	0	0	0	0	0	\N	\N	\N	\N	\N	\N
68bb9399-a29b-11f1-8fa2-aefacda18209	3	68bb9399-a29b-11f1-8fa2-aefacda18209	alert:10001	\N	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	\N	68bb9399-a29b-11f1-8fa2-aefacda18209	\N	t	f	t	f	f	1	\N		人员入侵告警处理（告警#10001）	start_event	2026-08-28 12:46:18.595	1	\N	\N	t	0	0	0	0	0	0	0	0	0	\N	\N	\N	\N	\N	\N
b4175c1c-a2a1-11f1-aee5-5a91bd373cd1	1	b4173508-a2a1-11f1-aee5-5a91bd373cd1	\N	b4173508-a2a1-11f1-aee5-5a91bd373cd1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	\N	b4173508-a2a1-11f1-aee5-5a91bd373cd1	task_1	t	f	f	f	f	1	\N		\N	\N	2026-08-28 13:31:22.006	\N	\N	\N	t	0	1	0	0	0	0	0	0	0	\N	\N	\N	\N	\N	\N
b4173508-a2a1-11f1-aee5-5a91bd373cd1	3	b4173508-a2a1-11f1-aee5-5a91bd373cd1	alert:30001	\N	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	\N	b4173508-a2a1-11f1-aee5-5a91bd373cd1	\N	t	f	t	f	f	1	\N		人员入侵告警处理（告警#30001）	start_event	2026-08-28 13:31:22.005	1	\N	\N	t	0	0	0	0	0	0	0	0	0	\N	\N	\N	\N	\N	\N
eccf2a76-a2a1-11f1-a0a7-f2ebdc74e900	1	eccedc52-a2a1-11f1-a0a7-f2ebdc74e900	\N	eccedc52-a2a1-11f1-a0a7-f2ebdc74e900	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	\N	eccedc52-a2a1-11f1-a0a7-f2ebdc74e900	task_1	t	f	f	f	f	1	\N		\N	\N	2026-08-28 13:32:57.163	\N	\N	\N	t	0	1	0	0	0	0	0	0	0	\N	\N	\N	\N	\N	\N
eccedc52-a2a1-11f1-a0a7-f2ebdc74e900	3	eccedc52-a2a1-11f1-a0a7-f2ebdc74e900	alert:30002	\N	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	\N	eccedc52-a2a1-11f1-a0a7-f2ebdc74e900	\N	t	f	t	f	f	1	\N		人员入侵告警处理（告警#30002）	start_event	2026-08-28 13:32:57.161	1	\N	\N	t	0	0	0	0	0	0	0	0	0	\N	\N	\N	\N	\N	\N
0d755203-a2a2-11f1-a0a7-f2ebdc74e900	1	0d7551ff-a2a2-11f1-a0a7-f2ebdc74e900	\N	0d7551ff-a2a2-11f1-a0a7-f2ebdc74e900	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	\N	0d7551ff-a2a2-11f1-a0a7-f2ebdc74e900	task_1	t	f	f	f	f	1	\N		\N	\N	2026-08-28 13:33:51.939	\N	\N	\N	t	0	1	0	0	0	0	0	0	0	\N	\N	\N	\N	\N	\N
0d7551ff-a2a2-11f1-a0a7-f2ebdc74e900	3	0d7551ff-a2a2-11f1-a0a7-f2ebdc74e900	alert:30003	\N	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	\N	0d7551ff-a2a2-11f1-a0a7-f2ebdc74e900	\N	t	f	t	f	f	1	\N		人员入侵告警处理（告警#30003）	start_event	2026-08-28 13:33:51.938	1	\N	\N	t	0	0	0	0	0	0	0	0	0	\N	\N	\N	\N	\N	\N
b4b31840-a2a7-11f1-ae25-fe31f4546ab1	3	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	alert:40006	\N	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	\N	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	\N	t	f	t	f	f	1	\N		人员入侵告警处理（告警#40006）	start_event	2026-08-28 14:14:20.007	1	\N	\N	t	0	0	0	0	0	0	0	0	0	\N	\N	\N	\N	\N	\N
b4b33f60-a2a7-11f1-ae25-fe31f4546ab1	1	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	\N	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	\N	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	task_1	t	f	f	f	f	1	\N		\N	\N	2026-08-28 14:14:20.008	\N	\N	\N	t	0	1	0	0	0	0	0	0	0	\N	\N	\N	\N	\N	\N
b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	4	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	alert:40005	\N	alert_fire_smoke:2:a035bb41-a2a7-11f1-ae25-fe31f4546ab1	\N	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	\N	t	f	t	f	f	1	\N		烟感火情告警处理（告警#40005）	start_event	2026-08-28 14:14:19.919	1	\N	\N	t	0	0	0	0	0	0	0	0	0	\N	\N	\N	\N	\N	\N
d19f4446-a2a7-11f1-ae25-fe31f4546ab1	1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	\N	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	alert_fire_smoke:2:a035bb41-a2a7-11f1-ae25-fe31f4546ab1	\N	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	task_specialist	t	f	f	f	f	1	\N		\N	\N	2026-08-28 14:15:08.53	\N	\N	\N	t	0	1	0	0	0	0	0	0	0	\N	\N	\N	\N	\N	\N
2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	3	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	alert:40007	\N	alert_fire_smoke:3:202ef60d-a2a8-11f1-ae25-fe31f4546ab1	\N	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	t	f	t	f	f	1	\N		烟感火情告警处理（告警#40007）	start_event	2026-08-28 14:17:31.935	1	\N	\N	t	0	0	0	0	0	0	0	0	0	\N	\N	\N	\N	\N	\N
2722e649-a2a8-11f1-ae25-fe31f4546ab1	1	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	\N	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	\N	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	task_1	t	f	f	f	f	1	\N		\N	\N	2026-08-28 14:17:32	\N	\N	\N	t	0	1	0	0	0	0	0	0	0	\N	\N	\N	\N	\N	\N
31603509-a2a8-11f1-ae25-fe31f4546ab1	2	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	31600df5-a2a8-11f1-ae25-fe31f4546ab1	alert_fire_smoke:3:202ef60d-a2a8-11f1-ae25-fe31f4546ab1	\N	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	task_manager_sign	f	f	f	f	f	1	\N		\N	\N	2026-08-28 14:17:49.179	\N	\N	\N	t	0	0	1	0	0	0	0	2	0	\N	\N	\N	\N	\N	\N
3160350a-a2a8-11f1-ae25-fe31f4546ab1	1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	31600df5-a2a8-11f1-ae25-fe31f4546ab1	alert_fire_smoke:3:202ef60d-a2a8-11f1-ae25-fe31f4546ab1	\N	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	task_manager_sign	t	f	f	f	f	1	\N		\N	\N	2026-08-28 14:17:49.179	\N	\N	\N	t	0	1	0	0	0	0	0	2	0	\N	\N	\N	\N	\N	\N
\.


--
-- Data for Name: act_ru_external_job; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.act_ru_external_job (id_, rev_, category_, type_, lock_exp_time_, lock_owner_, exclusive_, execution_id_, process_instance_id_, proc_def_id_, element_id_, element_name_, scope_id_, sub_scope_id_, scope_type_, scope_definition_id_, correlation_id_, retries_, exception_stack_id_, exception_msg_, duedate_, repeat_, handler_type_, handler_cfg_, custom_values_id_, create_time_, tenant_id_) FROM stdin;
\.


--
-- Data for Name: act_ru_history_job; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.act_ru_history_job (id_, rev_, lock_exp_time_, lock_owner_, retries_, exception_stack_id_, exception_msg_, handler_type_, handler_cfg_, custom_values_id_, adv_handler_cfg_id_, create_time_, scope_type_, tenant_id_) FROM stdin;
\.


--
-- Data for Name: act_ru_identitylink; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.act_ru_identitylink (id_, rev_, group_id_, type_, user_id_, task_id_, proc_inst_id_, proc_def_id_, scope_id_, sub_scope_id_, scope_type_, scope_definition_id_) FROM stdin;
68bb939a-a29b-11f1-8fa2-aefacda18209	1	\N	starter	1	\N	68bb9399-a29b-11f1-8fa2-aefacda18209	\N	\N	\N	\N	\N
68bd4152-a29b-11f1-8fa2-aefacda18209	1	\N	candidate	1	68bbbab1-a29b-11f1-8fa2-aefacda18209	\N	\N	\N	\N	\N	\N
68bd4153-a29b-11f1-8fa2-aefacda18209	1	\N	participant	1	\N	68bb9399-a29b-11f1-8fa2-aefacda18209	\N	\N	\N	\N	\N
b4173509-a2a1-11f1-aee5-5a91bd373cd1	1	\N	starter	1	\N	b4173508-a2a1-11f1-aee5-5a91bd373cd1	\N	\N	\N	\N	\N
b41bf001-a2a1-11f1-aee5-5a91bd373cd1	1	\N	candidate	1	b418e2c0-a2a1-11f1-aee5-5a91bd373cd1	\N	\N	\N	\N	\N	\N
b41c1712-a2a1-11f1-aee5-5a91bd373cd1	1	\N	participant	1	\N	b4173508-a2a1-11f1-aee5-5a91bd373cd1	\N	\N	\N	\N	\N
eccf0363-a2a1-11f1-a0a7-f2ebdc74e900	1	\N	starter	1	\N	eccedc52-a2a1-11f1-a0a7-f2ebdc74e900	\N	\N	\N	\N	\N
ecd3492b-a2a1-11f1-a0a7-f2ebdc74e900	1	\N	candidate	1	ecd0b11a-a2a1-11f1-a0a7-f2ebdc74e900	\N	\N	\N	\N	\N	\N
ecd3703c-a2a1-11f1-a0a7-f2ebdc74e900	1	\N	participant	1	\N	eccedc52-a2a1-11f1-a0a7-f2ebdc74e900	\N	\N	\N	\N	\N
0d755200-a2a2-11f1-a0a7-f2ebdc74e900	1	\N	starter	1	\N	0d7551ff-a2a2-11f1-a0a7-f2ebdc74e900	\N	\N	\N	\N	\N
0d763c68-a2a2-11f1-a0a7-f2ebdc74e900	1	\N	candidate	1	0d755207-a2a2-11f1-a0a7-f2ebdc74e900	\N	\N	\N	\N	\N	\N
0d763c69-a2a2-11f1-a0a7-f2ebdc74e900	1	\N	participant	1	\N	0d7551ff-a2a2-11f1-a0a7-f2ebdc74e900	\N	\N	\N	\N	\N
b4a5aaa6-a2a7-11f1-ae25-fe31f4546ab1	1	\N	starter	1	\N	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N
b4a6e33e-a2a7-11f1-ae25-fe31f4546ab1	1	\N	participant	1	\N	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N
b4b31841-a2a7-11f1-ae25-fe31f4546ab1	1	\N	starter	1	\N	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N
b4b3dba5-a2a7-11f1-ae25-fe31f4546ab1	1	\N	candidate	1	b4b33f64-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N
b4b402b6-a2a7-11f1-ae25-fe31f4546ab1	1	\N	participant	1	\N	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N
d1a0cae9-a2a7-11f1-ae25-fe31f4546ab1	1	\N	candidate	1	d19f4448-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N
2718fb0f-a2a8-11f1-ae25-fe31f4546ab1	1	\N	starter	1	\N	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N
271a81c7-a2a8-11f1-ae25-fe31f4546ab1	1	\N	participant	1	\N	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N
2722bf2a-a2a8-11f1-ae25-fe31f4546ab1	1	\N	starter	1	\N	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N
27246cee-a2a8-11f1-ae25-fe31f4546ab1	1	\N	candidate	1	2722e64d-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N
27246cef-a2a8-11f1-ae25-fe31f4546ab1	1	\N	participant	1	\N	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N
31656535-a2a8-11f1-ae25-fe31f4546ab1	1	\N	participant	104	\N	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N
\.


--
-- Data for Name: act_ru_job; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.act_ru_job (id_, rev_, category_, type_, lock_exp_time_, lock_owner_, exclusive_, execution_id_, process_instance_id_, proc_def_id_, element_id_, element_name_, scope_id_, sub_scope_id_, scope_type_, scope_definition_id_, correlation_id_, retries_, exception_stack_id_, exception_msg_, duedate_, repeat_, handler_type_, handler_cfg_, custom_values_id_, create_time_, tenant_id_) FROM stdin;
31719a38-a2a8-11f1-ae25-fe31f4546ab1	1	\N	message	\N	\N	t	31603509-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	alert_fire_smoke:3:202ef60d-a2a8-11f1-ae25-fe31f4546ab1	task_manager_sign	主管会签确认	\N	\N	\N	\N	31719a37-a2a8-11f1-ae25-fe31f4546ab1	3	\N	\N	\N	\N	parallel-multi-instance-complete	\N	\N	2026-08-28 14:17:49.293	
\.


--
-- Data for Name: act_ru_suspended_job; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.act_ru_suspended_job (id_, rev_, category_, type_, exclusive_, execution_id_, process_instance_id_, proc_def_id_, element_id_, element_name_, scope_id_, sub_scope_id_, scope_type_, scope_definition_id_, correlation_id_, retries_, exception_stack_id_, exception_msg_, duedate_, repeat_, handler_type_, handler_cfg_, custom_values_id_, create_time_, tenant_id_) FROM stdin;
\.


--
-- Data for Name: act_ru_task; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.act_ru_task (id_, rev_, execution_id_, proc_inst_id_, proc_def_id_, task_def_id_, scope_id_, sub_scope_id_, scope_type_, scope_definition_id_, propagated_stage_inst_id_, name_, parent_task_id_, description_, task_def_key_, owner_, assignee_, delegation_, priority_, create_time_, due_date_, category_, suspension_state_, tenant_id_, form_key_, claim_time_, is_count_enabled_, var_count_, id_link_count_, sub_task_count_) FROM stdin;
68bbbab1-a29b-11f1-8fa2-aefacda18209	1	68bb939d-a29b-11f1-8fa2-aefacda18209	68bb9399-a29b-11f1-8fa2-aefacda18209	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	\N	\N	\N	\N	\N	\N	审批人	\N	\N	task_1	\N	\N	\N	50	2026-08-28 12:46:18.595	\N	\N	1		\N	\N	t	0	1	0
b418e2c0-a2a1-11f1-aee5-5a91bd373cd1	1	b4175c1c-a2a1-11f1-aee5-5a91bd373cd1	b4173508-a2a1-11f1-aee5-5a91bd373cd1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	\N	\N	\N	\N	\N	\N	审批人	\N	\N	task_1	\N	\N	\N	50	2026-08-28 13:31:22.009	\N	\N	1		\N	\N	t	0	1	0
ecd0b11a-a2a1-11f1-a0a7-f2ebdc74e900	1	eccf2a76-a2a1-11f1-a0a7-f2ebdc74e900	eccedc52-a2a1-11f1-a0a7-f2ebdc74e900	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	\N	\N	\N	\N	\N	\N	审批人	\N	\N	task_1	\N	\N	\N	50	2026-08-28 13:32:57.165	\N	\N	1		\N	\N	t	0	1	0
0d755207-a2a2-11f1-a0a7-f2ebdc74e900	1	0d755203-a2a2-11f1-a0a7-f2ebdc74e900	0d7551ff-a2a2-11f1-a0a7-f2ebdc74e900	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	\N	\N	\N	\N	\N	\N	审批人	\N	\N	task_1	\N	\N	\N	50	2026-08-28 13:33:51.939	\N	\N	1		\N	\N	t	0	1	0
d19f4448-a2a7-11f1-ae25-fe31f4546ab1	1	d19f4446-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	alert_fire_smoke:2:a035bb41-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	安全专员初审	\N	\N	task_specialist	\N	\N	\N	50	2026-08-28 14:15:08.531	\N	\N	1		\N	\N	t	0	1	0
b4b33f64-a2a7-11f1-ae25-fe31f4546ab1	1	b4b33f60-a2a7-11f1-ae25-fe31f4546ab1	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	\N	\N	\N	\N	\N	\N	审批人	\N	\N	task_1	\N	\N	\N	50	2026-08-28 14:14:20.008	\N	\N	1		\N	\N	t	0	1	0
2722e64d-a2a8-11f1-ae25-fe31f4546ab1	1	2722e649-a2a8-11f1-ae25-fe31f4546ab1	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	alert_intrusion:2:3dac7978-a29b-11f1-8fa2-aefacda18209	\N	\N	\N	\N	\N	\N	审批人	\N	\N	task_1	\N	\N	\N	50	2026-08-28 14:17:32	\N	\N	1		\N	\N	t	0	1	0
31656533-a2a8-11f1-ae25-fe31f4546ab1	1	3160350a-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	alert_fire_smoke:3:202ef60d-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	主管会签确认	\N	\N	task_manager_sign	\N	104	\N	50	2026-08-28 14:17:49.213	\N	\N	1		\N	\N	t	0	0	0
\.


--
-- Data for Name: act_ru_timer_job; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.act_ru_timer_job (id_, rev_, category_, type_, lock_exp_time_, lock_owner_, exclusive_, execution_id_, process_instance_id_, proc_def_id_, element_id_, element_name_, scope_id_, sub_scope_id_, scope_type_, scope_definition_id_, correlation_id_, retries_, exception_stack_id_, exception_msg_, duedate_, repeat_, handler_type_, handler_cfg_, custom_values_id_, create_time_, tenant_id_) FROM stdin;
\.


--
-- Data for Name: act_ru_variable; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.act_ru_variable (id_, rev_, type_, name_, execution_id_, proc_inst_id_, task_id_, scope_id_, sub_scope_id_, scope_type_, bytearray_id_, double_, long_, text_, text2_) FROM stdin;
27192220-a2a8-11f1-ae25-fe31f4546ab1	1	string	PROCESS_INSTANCE_NAME	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	\N	烟感火情告警处理（告警#40007）	\N
27192222-a2a8-11f1-ae25-fe31f4546ab1	1	serializable	mi_assignees_task_manager_sign	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	27192221-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N
27192224-a2a8-11f1-ae25-fe31f4546ab1	1	string	deviceId	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	\N	smoke-wh-b	\N
27192225-a2a8-11f1-ae25-fe31f4546ab1	1	string	deviceName	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	\N	仓库B烟感探头	\N
68bb939b-a29b-11f1-8fa2-aefacda18209	1	long	PROCESS_START_USER_ID	68bb9399-a29b-11f1-8fa2-aefacda18209	68bb9399-a29b-11f1-8fa2-aefacda18209	\N	\N	\N	\N	\N	\N	1	1	\N
68bb939c-a29b-11f1-8fa2-aefacda18209	1	long	alertId	68bb9399-a29b-11f1-8fa2-aefacda18209	68bb9399-a29b-11f1-8fa2-aefacda18209	\N	\N	\N	\N	\N	\N	10001	10001	\N
68c00075-a29b-11f1-8fa2-aefacda18209	1	string	PROCESS_INSTANCE_NAME	68bb9399-a29b-11f1-8fa2-aefacda18209	68bb9399-a29b-11f1-8fa2-aefacda18209	\N	\N	\N	\N	\N	\N	\N	人员入侵告警处理（告警#10001）	\N
27192226-a2a8-11f1-ae25-fe31f4546ab1	1	long	PROCESS_START_USER_ID	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	1	1	\N
27192227-a2a8-11f1-ae25-fe31f4546ab1	1	integer	edgeNodeId	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	3	3	\N
27192228-a2a8-11f1-ae25-fe31f4546ab1	1	string	taskType	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	\N	realtime	\N
27192229-a2a8-11f1-ae25-fe31f4546ab1	1	string	imageUrl	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	\N	http://localhost:9003/static/images/demo-alert-smoke.png	\N
2719222a-a2a8-11f1-ae25-fe31f4546ab1	1	string	taskName	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	\N	烟感火情识别	\N
2719222b-a2a8-11f1-ae25-fe31f4546ab1	1	string	alertObject	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	\N	smoke	\N
2719222c-a2a8-11f1-ae25-fe31f4546ab1	1	integer	alertId	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	40007	40007	\N
2719222d-a2a8-11f1-ae25-fe31f4546ab1	1	string	alertEvent	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	\N	smoke_fire	\N
2719222e-a2a8-11f1-ae25-fe31f4546ab1	1	string	alertTime	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	\N	2026-08-28 14:22:36	\N
2719222f-a2a8-11f1-ae25-fe31f4546ab1	1	integer	nodeId	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	12	12	\N
27192230-a2a8-11f1-ae25-fe31f4546ab1	1	integer	taskId	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	50107	50107	\N
2722bf2b-a2a8-11f1-ae25-fe31f4546ab1	1	string	PROCESS_INSTANCE_NAME	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	\N	人员入侵告警处理（告警#40008）	\N
2722bf2c-a2a8-11f1-ae25-fe31f4546ab1	1	string	deviceId	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	\N	cam-yard-004	\N
2722bf2d-a2a8-11f1-ae25-fe31f4546ab1	1	string	deviceName	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	\N	后院摄像头-04	\N
2722bf2e-a2a8-11f1-ae25-fe31f4546ab1	1	long	PROCESS_START_USER_ID	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	1	1	\N
2722bf2f-a2a8-11f1-ae25-fe31f4546ab1	1	integer	edgeNodeId	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	3	3	\N
2722bf30-a2a8-11f1-ae25-fe31f4546ab1	1	string	taskType	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	\N	realtime	\N
2722bf31-a2a8-11f1-ae25-fe31f4546ab1	1	string	imageUrl	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	\N	http://localhost:9003/static/images/demo-alert-intrusion.png	\N
2722bf32-a2a8-11f1-ae25-fe31f4546ab1	1	string	taskName	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	\N	夜间徘徊检测	\N
2722bf33-a2a8-11f1-ae25-fe31f4546ab1	1	string	alertObject	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	\N	person	\N
2722bf34-a2a8-11f1-ae25-fe31f4546ab1	1	integer	alertId	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	40008	40008	\N
2722bf35-a2a8-11f1-ae25-fe31f4546ab1	1	string	alertEvent	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	\N	loitering	\N
2722bf36-a2a8-11f1-ae25-fe31f4546ab1	1	string	alertTime	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	\N	2026-08-28 14:20:02	\N
2722e647-a2a8-11f1-ae25-fe31f4546ab1	1	integer	nodeId	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	12	12	\N
b417350a-a2a1-11f1-aee5-5a91bd373cd1	1	long	PROCESS_START_USER_ID	b4173508-a2a1-11f1-aee5-5a91bd373cd1	b4173508-a2a1-11f1-aee5-5a91bd373cd1	\N	\N	\N	\N	\N	\N	1	1	\N
b4175c1b-a2a1-11f1-aee5-5a91bd373cd1	1	long	alertId	b4173508-a2a1-11f1-aee5-5a91bd373cd1	b4173508-a2a1-11f1-aee5-5a91bd373cd1	\N	\N	\N	\N	\N	\N	30001	30001	\N
b422f4e4-a2a1-11f1-aee5-5a91bd373cd1	1	string	PROCESS_INSTANCE_NAME	b4173508-a2a1-11f1-aee5-5a91bd373cd1	b4173508-a2a1-11f1-aee5-5a91bd373cd1	\N	\N	\N	\N	\N	\N	\N	人员入侵告警处理（告警#30001）	\N
eccf0364-a2a1-11f1-a0a7-f2ebdc74e900	1	long	PROCESS_START_USER_ID	eccedc52-a2a1-11f1-a0a7-f2ebdc74e900	eccedc52-a2a1-11f1-a0a7-f2ebdc74e900	\N	\N	\N	\N	\N	\N	1	1	\N
eccf2a75-a2a1-11f1-a0a7-f2ebdc74e900	1	long	alertId	eccedc52-a2a1-11f1-a0a7-f2ebdc74e900	eccedc52-a2a1-11f1-a0a7-f2ebdc74e900	\N	\N	\N	\N	\N	\N	30002	30002	\N
ece1c81e-a2a1-11f1-a0a7-f2ebdc74e900	1	string	PROCESS_INSTANCE_NAME	eccedc52-a2a1-11f1-a0a7-f2ebdc74e900	eccedc52-a2a1-11f1-a0a7-f2ebdc74e900	\N	\N	\N	\N	\N	\N	\N	人员入侵告警处理（告警#30002）	\N
0d755201-a2a2-11f1-a0a7-f2ebdc74e900	1	long	PROCESS_START_USER_ID	0d7551ff-a2a2-11f1-a0a7-f2ebdc74e900	0d7551ff-a2a2-11f1-a0a7-f2ebdc74e900	\N	\N	\N	\N	\N	\N	1	1	\N
0d755202-a2a2-11f1-a0a7-f2ebdc74e900	1	long	alertId	0d7551ff-a2a2-11f1-a0a7-f2ebdc74e900	0d7551ff-a2a2-11f1-a0a7-f2ebdc74e900	\N	\N	\N	\N	\N	\N	30003	30003	\N
0d7f642b-a2a2-11f1-a0a7-f2ebdc74e900	1	string	PROCESS_INSTANCE_NAME	0d7551ff-a2a2-11f1-a0a7-f2ebdc74e900	0d7551ff-a2a2-11f1-a0a7-f2ebdc74e900	\N	\N	\N	\N	\N	\N	\N	人员入侵告警处理（告警#30003）	\N
2722e648-a2a8-11f1-ae25-fe31f4546ab1	1	integer	taskId	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	50108	50108	\N
31603506-a2a8-11f1-ae25-fe31f4546ab1	1	integer	nrOfInstances	31600df5-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	2	2	\N
31603507-a2a8-11f1-ae25-fe31f4546ab1	1	bpmnParallelMultiInstanceCompleted	nrOfCompletedInstances	31600df5-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	\N	31600df5-a2a8-11f1-ae25-fe31f4546ab1	completed
31603508-a2a8-11f1-ae25-fe31f4546ab1	1	bpmnParallelMultiInstanceCompleted	nrOfActiveInstances	31600df5-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	\N	31600df5-a2a8-11f1-ae25-fe31f4546ab1	active
3160350b-a2a8-11f1-ae25-fe31f4546ab1	1	long	assignee	31603509-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	1	1	\N
3160350c-a2a8-11f1-ae25-fe31f4546ab1	1	long	assignee	3160350a-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	104	104	\N
3160350d-a2a8-11f1-ae25-fe31f4546ab1	1	integer	loopCounter	31603509-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	0	0	\N
31653e21-a2a8-11f1-ae25-fe31f4546ab1	1	integer	loopCounter	3160350a-a2a8-11f1-ae25-fe31f4546ab1	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	1	1	\N
b4a5d1b7-a2a7-11f1-ae25-fe31f4546ab1	1	string	PROCESS_INSTANCE_NAME	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	\N	烟感火情告警处理（告警#40005）	\N
b4a5d1b9-a2a7-11f1-ae25-fe31f4546ab1	1	serializable	mi_assignees_task_manager_sign	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	b4a5d1b8-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N
b4a5d1bb-a2a7-11f1-ae25-fe31f4546ab1	1	string	deviceId	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	\N	smoke-power-01	\N
b4a5d1bc-a2a7-11f1-ae25-fe31f4546ab1	1	string	deviceName	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	\N	配电房烟感探头	\N
b4a5d1bd-a2a7-11f1-ae25-fe31f4546ab1	1	long	PROCESS_START_USER_ID	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	1	1	\N
b4a5d1be-a2a7-11f1-ae25-fe31f4546ab1	1	integer	edgeNodeId	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	3	3	\N
b4a5d1bf-a2a7-11f1-ae25-fe31f4546ab1	1	string	taskType	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	\N	realtime	\N
b4a5d1c0-a2a7-11f1-ae25-fe31f4546ab1	1	string	imageUrl	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	\N	http://localhost:9003/static/images/demo-alert-smoke.png	\N
b4a5d1c1-a2a7-11f1-ae25-fe31f4546ab1	1	string	taskName	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	\N	烟感火情识别	\N
b4a5d1c2-a2a7-11f1-ae25-fe31f4546ab1	1	string	alertObject	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	\N	smoke	\N
b4a5d1c3-a2a7-11f1-ae25-fe31f4546ab1	1	integer	alertId	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	40005	40005	\N
b4a5d1c4-a2a7-11f1-ae25-fe31f4546ab1	1	string	alertEvent	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	\N	smoke_fire	\N
b4a5d1c5-a2a7-11f1-ae25-fe31f4546ab1	1	string	alertTime	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	\N	2026-08-28 14:07:12	\N
b4a5d1c6-a2a7-11f1-ae25-fe31f4546ab1	1	integer	nodeId	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	12	12	\N
b4a5d1c7-a2a7-11f1-ae25-fe31f4546ab1	1	integer	taskId	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	50105	50105	\N
b4b31842-a2a7-11f1-ae25-fe31f4546ab1	1	string	PROCESS_INSTANCE_NAME	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	\N	人员入侵告警处理（告警#40006）	\N
b4b31843-a2a7-11f1-ae25-fe31f4546ab1	1	string	deviceId	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	\N	cam-park-in	\N
b4b31844-a2a7-11f1-ae25-fe31f4546ab1	1	string	deviceName	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	\N	停车场入口摄像头	\N
b4b31845-a2a7-11f1-ae25-fe31f4546ab1	1	long	PROCESS_START_USER_ID	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	1	1	\N
b4b31846-a2a7-11f1-ae25-fe31f4546ab1	1	integer	edgeNodeId	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	3	3	\N
b4b31847-a2a7-11f1-ae25-fe31f4546ab1	1	string	taskType	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	\N	realtime	\N
b4b31848-a2a7-11f1-ae25-fe31f4546ab1	1	string	imageUrl	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	\N	http://localhost:9003/static/images/demo-alert-parking.png	\N
b4b31849-a2a7-11f1-ae25-fe31f4546ab1	1	string	taskName	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	\N	车辆违停检测	\N
b4b3184a-a2a7-11f1-ae25-fe31f4546ab1	1	string	alertObject	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	\N	car	\N
b4b3184b-a2a7-11f1-ae25-fe31f4546ab1	1	integer	alertId	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	40006	40006	\N
b4b3184c-a2a7-11f1-ae25-fe31f4546ab1	1	string	alertEvent	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	\N	illegal_parking	\N
b4b3184d-a2a7-11f1-ae25-fe31f4546ab1	1	string	alertTime	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	\N	2026-08-28 14:10:48	\N
b4b3184e-a2a7-11f1-ae25-fe31f4546ab1	1	integer	nodeId	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	12	12	\N
b4b33f5f-a2a7-11f1-ae25-fe31f4546ab1	1	integer	taskId	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	50106	50106	\N
d19de4b5-a2a7-11f1-ae25-fe31f4546ab1	1	string	PROCESS_REASON	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	\N	\N	\N	\N	\N	\N	\N	配电房例行检修粉尘误报，退回重新核实	\N
\.


--
-- Data for Name: flow_alert_record; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.flow_alert_record (id, alert_id, alert_source, alert_snapshot, process_instance_id, process_definition_key, process_instance_status, current_task_name, current_assignees, finish_time, creator, create_time, updater, update_time, deleted) FROM stdin;
2093198465696944130	10001	VIDEO_TASK	{"manualTrigger":true,"alertId":10001}	68bb9399-a29b-11f1-8fa2-aefacda18209	alert_intrusion	1	\N	\N	\N	1	2026-08-28 12:46:18.626572	1	2026-08-28 12:46:18.626572	0
2093220616123170818	40001	VIDEO_TASK	{"alertId":40001,"taskId":50101,"taskName":"周界入侵检测","deviceId":"cam-east-001","deviceName":"东门摄像头-01","nodeId":12,"edgeNodeId":3,"eventId":"evt-40001","timestamp":"2026-08-28 13:52:17","alert":{"object":"person","event":"intrusion","region":"周界围栏A段","information":{"confidence":0.94,"count":1},"imagePath":"http://localhost:9003/static/images/demo-alert-intrusion.png","recordPath":"","time":"2026-08-28 13:52:17","taskType":"realtime"}}	b47a0662-a2a7-11f1-ae25-fe31f4546ab1	alert_intrusion	2	\N	\N	2026-08-28 14:15:07.952755	\N	2026-08-28 14:14:19.700679	\N	2026-08-28 14:14:19.708565	0
2093220616337080322	40002	VIDEO_TASK	{"alertId":40002,"taskId":50102,"taskName":"周界入侵检测","deviceId":"cam-south-003","deviceName":"南墙摄像头-03","nodeId":12,"edgeNodeId":3,"eventId":"evt-40002","timestamp":"2026-08-28 13:58:41","alert":{"object":"person","event":"intrusion","region":"南墙绿化带","information":{"confidence":0.71,"remark":"疑似动物轮廓"},"imagePath":"http://localhost:9003/static/images/demo-alert-intrusion.png","recordPath":"","time":"2026-08-28 13:58:41","taskType":"realtime"}}	b4879b0a-a2a7-11f1-ae25-fe31f4546ab1	alert_intrusion	3	\N	\N	2026-08-28 14:15:08.034604	\N	2026-08-28 14:14:19.751628	\N	2026-08-28 14:14:19.760966	0
2093199964825112578	20001	VIDEO_TASK	{"alertId":20001,"source":"VIDEO_TASK","alert":{"event":"人员入侵","object":"person","imagePath":"/data/images/20001.jpg","time":1787892551000,"taskType":"intrusion"},"taskId":"vid-task-9","taskName":"周界入侵检测","deviceId":"cam-007","deviceName":"北门摄像头","nodeId":"edge-01"}	3dc27d39-a29c-11f1-9eaa-aefacda18209	alert_intrusion	2	审批人	IoT	2026-08-28 12:52:40.834028	\N	2026-08-28 12:52:16.047429	1	2026-08-28 12:52:40.834296	0
2093200390081425409	20002	VIDEO_TASK	{"alertId":20002,"source":"VIDEO_TASK","alert":{"event":"未戴安全帽","object":"helmet","imagePath":"/data/images/20002.jpg","time":1787893000000,"taskType":"helmet"},"taskId":"vid-task-10","taskName":"安全帽检测","deviceId":"cam-008","deviceName":"东区摄像头"}	7a1b6706-a29c-11f1-90a8-aefacda18209	alert_intrusion	2	\N	\N	2026-08-28 12:54:02.56627	\N	2026-08-28 12:53:57.435685	\N	2026-08-28 12:53:57.457501	0
2093198979226587137	10002	VIDEO_TASK	{"manualTrigger":true,"alertId":10002}	b1afb96c-a29b-11f1-9eaa-aefacda18209	alert_intrusion	2	\N	\N	2026-08-28 13:07:36.232864	1	2026-08-28 12:48:21.061936	1	2026-08-28 12:48:21.088236	0
2093209804830527490	30001	VIDEO_TASK	{"manualTrigger":true,"alertId":30001}	b4173508-a2a1-11f1-aee5-5a91bd373cd1	alert_intrusion	1	审批人	IoT	\N	\N	2026-08-28 13:31:22.087311	\N	2026-08-28 13:31:22.103425	0
2093210204140724226	30002	VIDEO_TASK	{"manualTrigger":true,"alertId":30002}	eccedc52-a2a1-11f1-a0a7-f2ebdc74e900	alert_intrusion	1	审批人	IoT	\N	\N	2026-08-28 13:32:57.290266	\N	2026-08-28 13:32:57.310624	0
2093210433640456193	30003	VIDEO_TASK	{"manualTrigger":true,"alertId":30003}	0d7551ff-a2a2-11f1-a0a7-f2ebdc74e900	alert_intrusion	1	审批人	IoT	\N	\N	2026-08-28 13:33:52.007236	\N	2026-08-28 13:33:52.014135	0
2093210807697002497	30004	VIDEO_TASK	{"manualTrigger":true,"alertId":30004}	4298127d-a2a2-11f1-a551-3a17ebed01a9	alert_intrusion	2	\N	\N	2026-08-28 13:40:02.932737	\N	2026-08-28 13:35:21.188839	\N	2026-08-28 13:35:21.21338	0
2093220617268215809	40005	VIDEO_TASK	{"alertId":40005,"taskId":50105,"taskName":"烟感火情识别","deviceId":"smoke-power-01","deviceName":"配电房烟感探头","nodeId":12,"edgeNodeId":3,"eventId":"evt-40005","timestamp":"2026-08-28 14:07:12","alert":{"object":"smoke","event":"smoke_fire","region":"配电室2号柜","information":{"confidence":0.82,"temperature":"41.0C"},"imagePath":"http://localhost:9003/static/images/demo-alert-smoke.png","recordPath":"","time":"2026-08-28 14:07:12","taskType":"realtime"}}	b4a5aaa5-a2a7-11f1-ae25-fe31f4546ab1	alert_fire_smoke	1	安全专员初审	IoT	\N	\N	2026-08-28 14:14:19.974002	1	2026-08-28 14:15:08.55195	0
2093220617557622785	40006	VIDEO_TASK	{"alertId":40006,"taskId":50106,"taskName":"车辆违停检测","deviceId":"cam-park-in","deviceName":"停车场入口摄像头","nodeId":12,"edgeNodeId":3,"eventId":"evt-40006","timestamp":"2026-08-28 14:10:48","alert":{"object":"car","event":"illegal_parking","region":"车位 Z-017","information":{"confidence":0.9,"staySeconds":1820},"imagePath":"http://localhost:9003/static/images/demo-alert-parking.png","recordPath":"","time":"2026-08-28 14:10:48","taskType":"realtime"}}	b4b31840-a2a7-11f1-ae25-fe31f4546ab1	alert_intrusion	1	审批人	IoT	\N	\N	2026-08-28 14:14:20.04221	\N	2026-08-28 14:14:20.050723	0
2093220616601321474	40003	VIDEO_TASK	{"alertId":40003,"taskId":50103,"taskName":"周界入侵检测","deviceId":"cam-west-002","deviceName":"西门摄像头-02","nodeId":12,"edgeNodeId":3,"eventId":"evt-40003","timestamp":"2026-08-28 14:02:05","alert":{"object":"person","event":"intrusion","region":"西门岗亭旁","information":{"confidence":0.88,"count":2},"imagePath":"http://localhost:9003/static/images/demo-alert-intrusion.png","recordPath":"","time":"2026-08-28 14:02:05","taskType":"realtime"}}	b48f1532-a2a7-11f1-ae25-fe31f4546ab1	alert_intrusion	4	\N	\N	2026-08-28 14:15:08.105805	\N	2026-08-28 14:14:19.814623	\N	2026-08-28 14:14:19.823718	0
2093220616928477185	40004	VIDEO_TASK	{"alertId":40004,"taskId":50104,"taskName":"烟感火情识别","deviceId":"smoke-wh-a","deviceName":"仓库A烟感探头","nodeId":12,"edgeNodeId":3,"eventId":"evt-40004","timestamp":"2026-08-28 14:05:33","alert":{"object":"smoke","event":"smoke_fire","region":"货架B排","information":{"confidence":0.97,"temperature":"58.3C"},"imagePath":"http://localhost:9003/static/images/demo-alert-smoke.png","recordPath":"","time":"2026-08-28 14:05:33","taskType":"realtime"}}	b49afc2a-a2a7-11f1-ae25-fe31f4546ab1	alert_fire_smoke	2	\N	\N	2026-08-28 14:15:08.283183	\N	2026-08-28 14:14:19.892957	1	2026-08-28 14:15:08.192968	0
2093228810310332417	40009	VIDEO_TASK	{"alertId":40009,"taskId":50109,"taskName":"周界入侵检测","deviceId":"cam-north-005","deviceName":"北门摄像头-05","nodeId":12,"edgeNodeId":3,"eventId":"evt-40009","timestamp":"2026-08-28 14:47:52","alert":{"object":"person","event":"intrusion","region":"北门停车场","information":{"confidence":0.91,"count":1},"imagePath":"http://localhost:9003/static/images/demo-alert-intrusion.png","recordPath":"","time":"2026-08-28 14:47:52","taskType":"realtime"}}	40ef870f-a2ac-11f1-83a4-6e81fb0021bd	alert_intrusion	2	\N	\N	2026-08-28 14:47:05.390054	\N	2026-08-28 14:46:53.346282	\N	2026-08-28 14:46:53.359168	0
2093221422935293954	40008	VIDEO_TASK	{"alertId":40008,"taskId":50108,"taskName":"夜间徘徊检测","deviceId":"cam-yard-004","deviceName":"后院摄像头-04","nodeId":12,"edgeNodeId":3,"eventId":"evt-40008","timestamp":"2026-08-28 14:20:02","alert":{"object":"person","event":"loitering","region":"后院器材区","information":{"confidence":0.86,"staySeconds":640},"imagePath":"http://localhost:9003/static/images/demo-alert-intrusion.png","recordPath":"","time":"2026-08-28 14:20:02","taskType":"realtime"}}	2722bf29-a2a8-11f1-ae25-fe31f4546ab1	alert_intrusion	1	审批人	IoT	\N	\N	2026-08-28 14:17:32.05985	\N	2026-08-28 14:17:32.071198	0
2093221422578778113	40007	VIDEO_TASK	{"alertId":40007,"taskId":50107,"taskName":"烟感火情识别","deviceId":"smoke-wh-b","deviceName":"仓库B烟感探头","nodeId":12,"edgeNodeId":3,"eventId":"evt-40007","timestamp":"2026-08-28 14:22:36","alert":{"object":"smoke","event":"smoke_fire","region":"货架D排","information":{"confidence":0.93,"temperature":"52.1C"},"imagePath":"http://localhost:9003/static/images/demo-alert-smoke.png","recordPath":"","time":"2026-08-28 14:22:36","taskType":"realtime"}}	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	alert_fire_smoke	1	主管会签确认	测试号	\N	\N	2026-08-28 14:17:31.974974	1	2026-08-28 14:17:49.221853	0
\.


--
-- Data for Name: flow_alert_route_rule; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.flow_alert_route_rule (id, rule_name, priority, process_definition_key, match_conditions, dedup_window_seconds, enabled, start_user_id, remark, creator, create_time, updater, update_time, deleted) FROM stdin;
2093198465420120066	人员入侵默认路由	10	alert_intrusion	[]	300	t	\N	冒烟测试	1	2026-08-28 12:46:18.561064	1	2026-08-28 12:46:18.561064	0
2093219977922068481	烟感火情路由	20	alert_fire_smoke	[{"field":"taskName","op":"EQ","value":"烟感火情识别"}]	300	t	\N	demo：按算法任务名路由到会签流程	1	2026-08-28 14:11:47.541258	1	2026-08-28 14:54:42.730426	0
\.


--
-- Data for Name: flow_category; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.flow_category (id, name, code, status, sort, description, tenant_id, creator, create_time, updater, update_time, deleted) FROM stdin;
2093196409074520065	告警处理	alert_handle	0	1	\N	1	1	2026-08-28 12:38:08.290131	1	2026-08-28 12:38:08.290131	0
\.


--
-- Data for Name: flow_copy; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.flow_copy (id, process_instance_id, process_instance_name, category, task_id, task_name, activity_id, start_user_id, reason, user_id, tenant_id, creator, create_time, updater, update_time, deleted) FROM stdin;
2093215977831120898	0d7551ff-a2a2-11f1-a0a7-f2ebdc74e900	人员入侵告警处理（告警#30003）	\N	0d755207-a2a2-11f1-a0a7-f2ebdc74e900	审批人	task_1	1	APP 抄送验证	1	1	1	2026-08-28 13:55:53.845187	1	2026-08-28 13:55:53.845187	0
2093220818590613506	b47a0662-a2a7-11f1-ae25-fe31f4546ab1	人员入侵告警处理（告警#40001）	\N	b47b17e6-a2a7-11f1-ae25-fe31f4546ab1	审批人	task_1	1	请知悉东门入侵处理结果	100	1	1	2026-08-28 14:15:07.972941	1	2026-08-28 14:15:07.972941	0
2093220818926157825	b4879b0a-a2a7-11f1-ae25-fe31f4546ab1	人员入侵告警处理（告警#40002）	\N	b487c22e-a2a7-11f1-ae25-fe31f4546ab1	审批人	task_1	1	误报记录归档备查	1	1	1	2026-08-28 14:15:08.052374	1	2026-08-28 14:15:08.052374	0
2093221629999693826	2718fb0e-a2a8-11f1-ae25-fe31f4546ab1	烟感火情告警处理（告警#40007）	\N	3160350f-a2a8-11f1-ae25-fe31f4546ab1	主管会签确认	task_manager_sign	1	仓库B火情会签进展抄送，请关注	1	1	1	2026-08-28 14:18:21.427012	1	2026-08-28 14:18:21.427012	0
2093228860969136129	40ef870f-a2ac-11f1-83a4-6e81fb0021bd	人员入侵告警处理（告警#40009）	\N	40f10dc3-a2ac-11f1-83a4-6e81fb0021bd	审批人	task_1	1	北门结果抄送（脚本路径验证）	100	1	1	2026-08-28 14:47:05.424972	1	2026-08-28 14:47:05.424972	0
\.


--
-- Data for Name: flow_user_group; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.flow_user_group (id, name, description, member_user_ids, status, tenant_id, creator, create_time, updater, update_time, deleted) FROM stdin;
\.


--
-- Data for Name: flw_channel_definition; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.flw_channel_definition (id_, name_, version_, key_, category_, deployment_id_, create_time_, tenant_id_, resource_name_, description_, type_, implementation_) FROM stdin;
\.


--
-- Data for Name: flw_ev_databasechangelog; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.flw_ev_databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) FROM stdin;
1	flowable	org/flowable/eventregistry/db/liquibase/flowable-eventregistry-db-changelog.xml	2026-08-28 12:35:13.667499	1	EXECUTED	8:1b0c48c9cf7945be799d868a2626d687	createTable tableName=FLW_EVENT_DEPLOYMENT; createTable tableName=FLW_EVENT_RESOURCE; createTable tableName=FLW_EVENT_DEFINITION; createIndex indexName=ACT_IDX_EVENT_DEF_UNIQ, tableName=FLW_EVENT_DEFINITION; createTable tableName=FLW_CHANNEL_DEFIN...		\N	4.9.1	\N	\N	7891713592
2	flowable	org/flowable/eventregistry/db/liquibase/flowable-eventregistry-db-changelog.xml	2026-08-28 12:35:13.678372	2	EXECUTED	8:0ea825feb8e470558f0b5754352b9cda	addColumn tableName=FLW_CHANNEL_DEFINITION; addColumn tableName=FLW_CHANNEL_DEFINITION		\N	4.9.1	\N	\N	7891713592
3	flowable	org/flowable/eventregistry/db/liquibase/flowable-eventregistry-db-changelog.xml	2026-08-28 12:35:13.715431	3	EXECUTED	8:3c2bb293350b5cbe6504331980c9dcee	customChange		\N	4.9.1	\N	\N	7891713592
\.


--
-- Data for Name: flw_ev_databasechangeloglock; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.flw_ev_databasechangeloglock (id, locked, lockgranted, lockedby) FROM stdin;
1	f	\N	\N
\.


--
-- Data for Name: flw_event_definition; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.flw_event_definition (id_, name_, version_, key_, category_, deployment_id_, tenant_id_, resource_name_, description_) FROM stdin;
\.


--
-- Data for Name: flw_event_deployment; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.flw_event_deployment (id_, name_, category_, deploy_time_, tenant_id_, parent_deployment_id_) FROM stdin;
\.


--
-- Data for Name: flw_event_resource; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.flw_event_resource (id_, name_, deployment_id_, resource_bytes_) FROM stdin;
\.


--
-- Data for Name: flw_ru_batch; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.flw_ru_batch (id_, rev_, type_, search_key_, search_key2_, create_time_, complete_time_, status_, batch_doc_id_, tenant_id_) FROM stdin;
\.


--
-- Data for Name: flw_ru_batch_part; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.flw_ru_batch_part (id_, rev_, batch_id_, type_, scope_id_, sub_scope_id_, scope_type_, search_key_, search_key2_, create_time_, complete_time_, status_, result_doc_id_, tenant_id_) FROM stdin;
\.


--
-- Name: act_evt_log_log_nr__seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.act_evt_log_log_nr__seq', 1, false);


--
-- Name: act_hi_tsk_log_id__seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.act_hi_tsk_log_id__seq', 1, false);


--
-- Name: flow_alert_record_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.flow_alert_record_id_seq', 1, false);


--
-- Name: flow_alert_route_rule_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.flow_alert_route_rule_id_seq', 1, false);


--
-- Name: flow_category_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.flow_category_id_seq', 1, false);


--
-- Name: flow_copy_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.flow_copy_id_seq', 1, false);


--
-- Name: flow_user_group_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.flow_user_group_id_seq', 1, false);


--
-- Name: flw_channel_definition FLW_CHANNEL_DEFINITION_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.flw_channel_definition
    ADD CONSTRAINT "FLW_CHANNEL_DEFINITION_pkey" PRIMARY KEY (id_);


--
-- Name: flw_event_definition FLW_EVENT_DEFINITION_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.flw_event_definition
    ADD CONSTRAINT "FLW_EVENT_DEFINITION_pkey" PRIMARY KEY (id_);


--
-- Name: flw_event_deployment FLW_EVENT_DEPLOYMENT_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.flw_event_deployment
    ADD CONSTRAINT "FLW_EVENT_DEPLOYMENT_pkey" PRIMARY KEY (id_);


--
-- Name: flw_event_resource FLW_EVENT_RESOURCE_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.flw_event_resource
    ADD CONSTRAINT "FLW_EVENT_RESOURCE_pkey" PRIMARY KEY (id_);


--
-- Name: act_evt_log act_evt_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_evt_log
    ADD CONSTRAINT act_evt_log_pkey PRIMARY KEY (log_nr_);


--
-- Name: act_ge_bytearray act_ge_bytearray_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ge_bytearray
    ADD CONSTRAINT act_ge_bytearray_pkey PRIMARY KEY (id_);


--
-- Name: act_ge_property act_ge_property_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ge_property
    ADD CONSTRAINT act_ge_property_pkey PRIMARY KEY (name_);


--
-- Name: act_hi_actinst act_hi_actinst_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_hi_actinst
    ADD CONSTRAINT act_hi_actinst_pkey PRIMARY KEY (id_);


--
-- Name: act_hi_attachment act_hi_attachment_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_hi_attachment
    ADD CONSTRAINT act_hi_attachment_pkey PRIMARY KEY (id_);


--
-- Name: act_hi_comment act_hi_comment_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_hi_comment
    ADD CONSTRAINT act_hi_comment_pkey PRIMARY KEY (id_);


--
-- Name: act_hi_detail act_hi_detail_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_hi_detail
    ADD CONSTRAINT act_hi_detail_pkey PRIMARY KEY (id_);


--
-- Name: act_hi_entitylink act_hi_entitylink_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_hi_entitylink
    ADD CONSTRAINT act_hi_entitylink_pkey PRIMARY KEY (id_);


--
-- Name: act_hi_identitylink act_hi_identitylink_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_hi_identitylink
    ADD CONSTRAINT act_hi_identitylink_pkey PRIMARY KEY (id_);


--
-- Name: act_hi_procinst act_hi_procinst_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_hi_procinst
    ADD CONSTRAINT act_hi_procinst_pkey PRIMARY KEY (id_);


--
-- Name: act_hi_procinst act_hi_procinst_proc_inst_id__key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_hi_procinst
    ADD CONSTRAINT act_hi_procinst_proc_inst_id__key UNIQUE (proc_inst_id_);


--
-- Name: act_hi_taskinst act_hi_taskinst_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_hi_taskinst
    ADD CONSTRAINT act_hi_taskinst_pkey PRIMARY KEY (id_);


--
-- Name: act_hi_tsk_log act_hi_tsk_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_hi_tsk_log
    ADD CONSTRAINT act_hi_tsk_log_pkey PRIMARY KEY (id_);


--
-- Name: act_hi_varinst act_hi_varinst_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_hi_varinst
    ADD CONSTRAINT act_hi_varinst_pkey PRIMARY KEY (id_);


--
-- Name: act_id_bytearray act_id_bytearray_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_id_bytearray
    ADD CONSTRAINT act_id_bytearray_pkey PRIMARY KEY (id_);


--
-- Name: act_id_group act_id_group_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_id_group
    ADD CONSTRAINT act_id_group_pkey PRIMARY KEY (id_);


--
-- Name: act_id_info act_id_info_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_id_info
    ADD CONSTRAINT act_id_info_pkey PRIMARY KEY (id_);


--
-- Name: act_id_membership act_id_membership_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_id_membership
    ADD CONSTRAINT act_id_membership_pkey PRIMARY KEY (user_id_, group_id_);


--
-- Name: act_id_priv_mapping act_id_priv_mapping_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_id_priv_mapping
    ADD CONSTRAINT act_id_priv_mapping_pkey PRIMARY KEY (id_);


--
-- Name: act_id_priv act_id_priv_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_id_priv
    ADD CONSTRAINT act_id_priv_pkey PRIMARY KEY (id_);


--
-- Name: act_id_property act_id_property_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_id_property
    ADD CONSTRAINT act_id_property_pkey PRIMARY KEY (name_);


--
-- Name: act_id_token act_id_token_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_id_token
    ADD CONSTRAINT act_id_token_pkey PRIMARY KEY (id_);


--
-- Name: act_id_user act_id_user_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_id_user
    ADD CONSTRAINT act_id_user_pkey PRIMARY KEY (id_);


--
-- Name: act_procdef_info act_procdef_info_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_procdef_info
    ADD CONSTRAINT act_procdef_info_pkey PRIMARY KEY (id_);


--
-- Name: act_re_deployment act_re_deployment_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_re_deployment
    ADD CONSTRAINT act_re_deployment_pkey PRIMARY KEY (id_);


--
-- Name: act_re_model act_re_model_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_re_model
    ADD CONSTRAINT act_re_model_pkey PRIMARY KEY (id_);


--
-- Name: act_re_procdef act_re_procdef_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_re_procdef
    ADD CONSTRAINT act_re_procdef_pkey PRIMARY KEY (id_);


--
-- Name: act_ru_actinst act_ru_actinst_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_actinst
    ADD CONSTRAINT act_ru_actinst_pkey PRIMARY KEY (id_);


--
-- Name: act_ru_deadletter_job act_ru_deadletter_job_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_deadletter_job
    ADD CONSTRAINT act_ru_deadletter_job_pkey PRIMARY KEY (id_);


--
-- Name: act_ru_entitylink act_ru_entitylink_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_entitylink
    ADD CONSTRAINT act_ru_entitylink_pkey PRIMARY KEY (id_);


--
-- Name: act_ru_event_subscr act_ru_event_subscr_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_event_subscr
    ADD CONSTRAINT act_ru_event_subscr_pkey PRIMARY KEY (id_);


--
-- Name: act_ru_execution act_ru_execution_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_execution
    ADD CONSTRAINT act_ru_execution_pkey PRIMARY KEY (id_);


--
-- Name: act_ru_external_job act_ru_external_job_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_external_job
    ADD CONSTRAINT act_ru_external_job_pkey PRIMARY KEY (id_);


--
-- Name: act_ru_history_job act_ru_history_job_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_history_job
    ADD CONSTRAINT act_ru_history_job_pkey PRIMARY KEY (id_);


--
-- Name: act_ru_identitylink act_ru_identitylink_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_identitylink
    ADD CONSTRAINT act_ru_identitylink_pkey PRIMARY KEY (id_);


--
-- Name: act_ru_job act_ru_job_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_job
    ADD CONSTRAINT act_ru_job_pkey PRIMARY KEY (id_);


--
-- Name: act_ru_suspended_job act_ru_suspended_job_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_suspended_job
    ADD CONSTRAINT act_ru_suspended_job_pkey PRIMARY KEY (id_);


--
-- Name: act_ru_task act_ru_task_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_task
    ADD CONSTRAINT act_ru_task_pkey PRIMARY KEY (id_);


--
-- Name: act_ru_timer_job act_ru_timer_job_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_timer_job
    ADD CONSTRAINT act_ru_timer_job_pkey PRIMARY KEY (id_);


--
-- Name: act_ru_variable act_ru_variable_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_variable
    ADD CONSTRAINT act_ru_variable_pkey PRIMARY KEY (id_);


--
-- Name: act_procdef_info act_uniq_info_procdef; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_procdef_info
    ADD CONSTRAINT act_uniq_info_procdef UNIQUE (proc_def_id_);


--
-- Name: act_id_priv act_uniq_priv_name; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_id_priv
    ADD CONSTRAINT act_uniq_priv_name UNIQUE (name_);


--
-- Name: act_re_procdef act_uniq_procdef; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_re_procdef
    ADD CONSTRAINT act_uniq_procdef UNIQUE (key_, version_, derived_version_, tenant_id_);


--
-- Name: flow_alert_record flow_alert_record_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.flow_alert_record
    ADD CONSTRAINT flow_alert_record_pkey PRIMARY KEY (id);


--
-- Name: flow_alert_route_rule flow_alert_route_rule_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.flow_alert_route_rule
    ADD CONSTRAINT flow_alert_route_rule_pkey PRIMARY KEY (id);


--
-- Name: flow_category flow_category_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.flow_category
    ADD CONSTRAINT flow_category_pkey PRIMARY KEY (id);


--
-- Name: flow_copy flow_copy_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.flow_copy
    ADD CONSTRAINT flow_copy_pkey PRIMARY KEY (id);


--
-- Name: flow_user_group flow_user_group_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.flow_user_group
    ADD CONSTRAINT flow_user_group_pkey PRIMARY KEY (id);


--
-- Name: flw_ev_databasechangeloglock flw_ev_databasechangeloglock_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.flw_ev_databasechangeloglock
    ADD CONSTRAINT flw_ev_databasechangeloglock_pkey PRIMARY KEY (id);


--
-- Name: flw_ru_batch_part flw_ru_batch_part_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.flw_ru_batch_part
    ADD CONSTRAINT flw_ru_batch_part_pkey PRIMARY KEY (id_);


--
-- Name: flw_ru_batch flw_ru_batch_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.flw_ru_batch
    ADD CONSTRAINT flw_ru_batch_pkey PRIMARY KEY (id_);


--
-- Name: act_idx_athrz_procedef; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_athrz_procedef ON public.act_ru_identitylink USING btree (proc_def_id_);


--
-- Name: act_idx_bytear_depl; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_bytear_depl ON public.act_ge_bytearray USING btree (deployment_id_);


--
-- Name: act_idx_channel_def_uniq; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX act_idx_channel_def_uniq ON public.flw_channel_definition USING btree (key_, version_, tenant_id_);


--
-- Name: act_idx_deadletter_job_correlation_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_deadletter_job_correlation_id ON public.act_ru_deadletter_job USING btree (correlation_id_);


--
-- Name: act_idx_deadletter_job_custom_values_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_deadletter_job_custom_values_id ON public.act_ru_deadletter_job USING btree (custom_values_id_);


--
-- Name: act_idx_deadletter_job_exception_stack_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_deadletter_job_exception_stack_id ON public.act_ru_deadletter_job USING btree (exception_stack_id_);


--
-- Name: act_idx_deadletter_job_execution_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_deadletter_job_execution_id ON public.act_ru_deadletter_job USING btree (execution_id_);


--
-- Name: act_idx_deadletter_job_proc_def_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_deadletter_job_proc_def_id ON public.act_ru_deadletter_job USING btree (proc_def_id_);


--
-- Name: act_idx_deadletter_job_process_instance_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_deadletter_job_process_instance_id ON public.act_ru_deadletter_job USING btree (process_instance_id_);


--
-- Name: act_idx_djob_scope; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_djob_scope ON public.act_ru_deadletter_job USING btree (scope_id_, scope_type_);


--
-- Name: act_idx_djob_scope_def; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_djob_scope_def ON public.act_ru_deadletter_job USING btree (scope_definition_id_, scope_type_);


--
-- Name: act_idx_djob_sub_scope; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_djob_sub_scope ON public.act_ru_deadletter_job USING btree (sub_scope_id_, scope_type_);


--
-- Name: act_idx_ejob_scope; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_ejob_scope ON public.act_ru_external_job USING btree (scope_id_, scope_type_);


--
-- Name: act_idx_ejob_scope_def; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_ejob_scope_def ON public.act_ru_external_job USING btree (scope_definition_id_, scope_type_);


--
-- Name: act_idx_ejob_sub_scope; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_ejob_sub_scope ON public.act_ru_external_job USING btree (sub_scope_id_, scope_type_);


--
-- Name: act_idx_ent_lnk_ref_scope; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_ent_lnk_ref_scope ON public.act_ru_entitylink USING btree (ref_scope_id_, ref_scope_type_, link_type_);


--
-- Name: act_idx_ent_lnk_root_scope; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_ent_lnk_root_scope ON public.act_ru_entitylink USING btree (root_scope_id_, root_scope_type_, link_type_);


--
-- Name: act_idx_ent_lnk_scope; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_ent_lnk_scope ON public.act_ru_entitylink USING btree (scope_id_, scope_type_, link_type_);


--
-- Name: act_idx_ent_lnk_scope_def; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_ent_lnk_scope_def ON public.act_ru_entitylink USING btree (scope_definition_id_, scope_type_, link_type_);


--
-- Name: act_idx_event_def_uniq; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX act_idx_event_def_uniq ON public.flw_event_definition USING btree (key_, version_, tenant_id_);


--
-- Name: act_idx_event_subscr; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_event_subscr ON public.act_ru_event_subscr USING btree (execution_id_);


--
-- Name: act_idx_event_subscr_config_; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_event_subscr_config_ ON public.act_ru_event_subscr USING btree (configuration_);


--
-- Name: act_idx_event_subscr_scoperef_; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_event_subscr_scoperef_ ON public.act_ru_event_subscr USING btree (scope_id_, scope_type_);


--
-- Name: act_idx_exe_parent; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_exe_parent ON public.act_ru_execution USING btree (parent_id_);


--
-- Name: act_idx_exe_procdef; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_exe_procdef ON public.act_ru_execution USING btree (proc_def_id_);


--
-- Name: act_idx_exe_procinst; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_exe_procinst ON public.act_ru_execution USING btree (proc_inst_id_);


--
-- Name: act_idx_exe_root; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_exe_root ON public.act_ru_execution USING btree (root_proc_inst_id_);


--
-- Name: act_idx_exe_super; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_exe_super ON public.act_ru_execution USING btree (super_exec_);


--
-- Name: act_idx_exec_buskey; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_exec_buskey ON public.act_ru_execution USING btree (business_key_);


--
-- Name: act_idx_exec_ref_id_; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_exec_ref_id_ ON public.act_ru_execution USING btree (reference_id_);


--
-- Name: act_idx_external_job_correlation_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_external_job_correlation_id ON public.act_ru_external_job USING btree (correlation_id_);


--
-- Name: act_idx_external_job_custom_values_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_external_job_custom_values_id ON public.act_ru_external_job USING btree (custom_values_id_);


--
-- Name: act_idx_external_job_exception_stack_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_external_job_exception_stack_id ON public.act_ru_external_job USING btree (exception_stack_id_);


--
-- Name: act_idx_hi_act_inst_end; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_hi_act_inst_end ON public.act_hi_actinst USING btree (end_time_);


--
-- Name: act_idx_hi_act_inst_exec; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_hi_act_inst_exec ON public.act_hi_actinst USING btree (execution_id_, act_id_);


--
-- Name: act_idx_hi_act_inst_procinst; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_hi_act_inst_procinst ON public.act_hi_actinst USING btree (proc_inst_id_, act_id_);


--
-- Name: act_idx_hi_act_inst_start; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_hi_act_inst_start ON public.act_hi_actinst USING btree (start_time_);


--
-- Name: act_idx_hi_detail_act_inst; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_hi_detail_act_inst ON public.act_hi_detail USING btree (act_inst_id_);


--
-- Name: act_idx_hi_detail_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_hi_detail_name ON public.act_hi_detail USING btree (name_);


--
-- Name: act_idx_hi_detail_proc_inst; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_hi_detail_proc_inst ON public.act_hi_detail USING btree (proc_inst_id_);


--
-- Name: act_idx_hi_detail_task_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_hi_detail_task_id ON public.act_hi_detail USING btree (task_id_);


--
-- Name: act_idx_hi_detail_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_hi_detail_time ON public.act_hi_detail USING btree (time_);


--
-- Name: act_idx_hi_ent_lnk_ref_scope; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_hi_ent_lnk_ref_scope ON public.act_hi_entitylink USING btree (ref_scope_id_, ref_scope_type_, link_type_);


--
-- Name: act_idx_hi_ent_lnk_root_scope; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_hi_ent_lnk_root_scope ON public.act_hi_entitylink USING btree (root_scope_id_, root_scope_type_, link_type_);


--
-- Name: act_idx_hi_ent_lnk_scope; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_hi_ent_lnk_scope ON public.act_hi_entitylink USING btree (scope_id_, scope_type_, link_type_);


--
-- Name: act_idx_hi_ent_lnk_scope_def; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_hi_ent_lnk_scope_def ON public.act_hi_entitylink USING btree (scope_definition_id_, scope_type_, link_type_);


--
-- Name: act_idx_hi_ident_lnk_procinst; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_hi_ident_lnk_procinst ON public.act_hi_identitylink USING btree (proc_inst_id_);


--
-- Name: act_idx_hi_ident_lnk_scope; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_hi_ident_lnk_scope ON public.act_hi_identitylink USING btree (scope_id_, scope_type_);


--
-- Name: act_idx_hi_ident_lnk_scope_def; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_hi_ident_lnk_scope_def ON public.act_hi_identitylink USING btree (scope_definition_id_, scope_type_);


--
-- Name: act_idx_hi_ident_lnk_sub_scope; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_hi_ident_lnk_sub_scope ON public.act_hi_identitylink USING btree (sub_scope_id_, scope_type_);


--
-- Name: act_idx_hi_ident_lnk_task; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_hi_ident_lnk_task ON public.act_hi_identitylink USING btree (task_id_);


--
-- Name: act_idx_hi_ident_lnk_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_hi_ident_lnk_user ON public.act_hi_identitylink USING btree (user_id_);


--
-- Name: act_idx_hi_pro_i_buskey; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_hi_pro_i_buskey ON public.act_hi_procinst USING btree (business_key_);


--
-- Name: act_idx_hi_pro_inst_end; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_hi_pro_inst_end ON public.act_hi_procinst USING btree (end_time_);


--
-- Name: act_idx_hi_pro_super_procinst; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_hi_pro_super_procinst ON public.act_hi_procinst USING btree (super_process_instance_id_);


--
-- Name: act_idx_hi_procvar_exe; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_hi_procvar_exe ON public.act_hi_varinst USING btree (execution_id_);


--
-- Name: act_idx_hi_procvar_name_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_hi_procvar_name_type ON public.act_hi_varinst USING btree (name_, var_type_);


--
-- Name: act_idx_hi_procvar_proc_inst; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_hi_procvar_proc_inst ON public.act_hi_varinst USING btree (proc_inst_id_);


--
-- Name: act_idx_hi_procvar_task_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_hi_procvar_task_id ON public.act_hi_varinst USING btree (task_id_);


--
-- Name: act_idx_hi_task_inst_procinst; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_hi_task_inst_procinst ON public.act_hi_taskinst USING btree (proc_inst_id_);


--
-- Name: act_idx_hi_task_scope; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_hi_task_scope ON public.act_hi_taskinst USING btree (scope_id_, scope_type_);


--
-- Name: act_idx_hi_task_scope_def; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_hi_task_scope_def ON public.act_hi_taskinst USING btree (scope_definition_id_, scope_type_);


--
-- Name: act_idx_hi_task_sub_scope; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_hi_task_sub_scope ON public.act_hi_taskinst USING btree (sub_scope_id_, scope_type_);


--
-- Name: act_idx_hi_var_scope_id_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_hi_var_scope_id_type ON public.act_hi_varinst USING btree (scope_id_, scope_type_);


--
-- Name: act_idx_hi_var_sub_id_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_hi_var_sub_id_type ON public.act_hi_varinst USING btree (sub_scope_id_, scope_type_);


--
-- Name: act_idx_ident_lnk_group; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_ident_lnk_group ON public.act_ru_identitylink USING btree (group_id_);


--
-- Name: act_idx_ident_lnk_scope; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_ident_lnk_scope ON public.act_ru_identitylink USING btree (scope_id_, scope_type_);


--
-- Name: act_idx_ident_lnk_scope_def; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_ident_lnk_scope_def ON public.act_ru_identitylink USING btree (scope_definition_id_, scope_type_);


--
-- Name: act_idx_ident_lnk_sub_scope; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_ident_lnk_sub_scope ON public.act_ru_identitylink USING btree (sub_scope_id_, scope_type_);


--
-- Name: act_idx_ident_lnk_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_ident_lnk_user ON public.act_ru_identitylink USING btree (user_id_);


--
-- Name: act_idx_idl_procinst; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_idl_procinst ON public.act_ru_identitylink USING btree (proc_inst_id_);


--
-- Name: act_idx_job_correlation_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_job_correlation_id ON public.act_ru_job USING btree (correlation_id_);


--
-- Name: act_idx_job_custom_values_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_job_custom_values_id ON public.act_ru_job USING btree (custom_values_id_);


--
-- Name: act_idx_job_exception_stack_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_job_exception_stack_id ON public.act_ru_job USING btree (exception_stack_id_);


--
-- Name: act_idx_job_execution_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_job_execution_id ON public.act_ru_job USING btree (execution_id_);


--
-- Name: act_idx_job_proc_def_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_job_proc_def_id ON public.act_ru_job USING btree (proc_def_id_);


--
-- Name: act_idx_job_process_instance_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_job_process_instance_id ON public.act_ru_job USING btree (process_instance_id_);


--
-- Name: act_idx_job_scope; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_job_scope ON public.act_ru_job USING btree (scope_id_, scope_type_);


--
-- Name: act_idx_job_scope_def; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_job_scope_def ON public.act_ru_job USING btree (scope_definition_id_, scope_type_);


--
-- Name: act_idx_job_sub_scope; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_job_sub_scope ON public.act_ru_job USING btree (sub_scope_id_, scope_type_);


--
-- Name: act_idx_memb_group; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_memb_group ON public.act_id_membership USING btree (group_id_);


--
-- Name: act_idx_memb_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_memb_user ON public.act_id_membership USING btree (user_id_);


--
-- Name: act_idx_model_deployment; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_model_deployment ON public.act_re_model USING btree (deployment_id_);


--
-- Name: act_idx_model_source; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_model_source ON public.act_re_model USING btree (editor_source_value_id_);


--
-- Name: act_idx_model_source_extra; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_model_source_extra ON public.act_re_model USING btree (editor_source_extra_value_id_);


--
-- Name: act_idx_priv_group; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_priv_group ON public.act_id_priv_mapping USING btree (group_id_);


--
-- Name: act_idx_priv_mapping; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_priv_mapping ON public.act_id_priv_mapping USING btree (priv_id_);


--
-- Name: act_idx_priv_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_priv_user ON public.act_id_priv_mapping USING btree (user_id_);


--
-- Name: act_idx_procdef_info_json; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_procdef_info_json ON public.act_procdef_info USING btree (info_json_id_);


--
-- Name: act_idx_procdef_info_proc; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_procdef_info_proc ON public.act_procdef_info USING btree (proc_def_id_);


--
-- Name: act_idx_ru_acti_end; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_ru_acti_end ON public.act_ru_actinst USING btree (end_time_);


--
-- Name: act_idx_ru_acti_exec; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_ru_acti_exec ON public.act_ru_actinst USING btree (execution_id_);


--
-- Name: act_idx_ru_acti_exec_act; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_ru_acti_exec_act ON public.act_ru_actinst USING btree (execution_id_, act_id_);


--
-- Name: act_idx_ru_acti_proc; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_ru_acti_proc ON public.act_ru_actinst USING btree (proc_inst_id_);


--
-- Name: act_idx_ru_acti_proc_act; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_ru_acti_proc_act ON public.act_ru_actinst USING btree (proc_inst_id_, act_id_);


--
-- Name: act_idx_ru_acti_start; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_ru_acti_start ON public.act_ru_actinst USING btree (start_time_);


--
-- Name: act_idx_ru_acti_task; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_ru_acti_task ON public.act_ru_actinst USING btree (task_id_);


--
-- Name: act_idx_ru_var_scope_id_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_ru_var_scope_id_type ON public.act_ru_variable USING btree (scope_id_, scope_type_);


--
-- Name: act_idx_ru_var_sub_id_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_ru_var_sub_id_type ON public.act_ru_variable USING btree (sub_scope_id_, scope_type_);


--
-- Name: act_idx_sjob_scope; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_sjob_scope ON public.act_ru_suspended_job USING btree (scope_id_, scope_type_);


--
-- Name: act_idx_sjob_scope_def; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_sjob_scope_def ON public.act_ru_suspended_job USING btree (scope_definition_id_, scope_type_);


--
-- Name: act_idx_sjob_sub_scope; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_sjob_sub_scope ON public.act_ru_suspended_job USING btree (sub_scope_id_, scope_type_);


--
-- Name: act_idx_suspended_job_correlation_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_suspended_job_correlation_id ON public.act_ru_suspended_job USING btree (correlation_id_);


--
-- Name: act_idx_suspended_job_custom_values_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_suspended_job_custom_values_id ON public.act_ru_suspended_job USING btree (custom_values_id_);


--
-- Name: act_idx_suspended_job_exception_stack_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_suspended_job_exception_stack_id ON public.act_ru_suspended_job USING btree (exception_stack_id_);


--
-- Name: act_idx_suspended_job_execution_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_suspended_job_execution_id ON public.act_ru_suspended_job USING btree (execution_id_);


--
-- Name: act_idx_suspended_job_proc_def_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_suspended_job_proc_def_id ON public.act_ru_suspended_job USING btree (proc_def_id_);


--
-- Name: act_idx_suspended_job_process_instance_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_suspended_job_process_instance_id ON public.act_ru_suspended_job USING btree (process_instance_id_);


--
-- Name: act_idx_task_create; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_task_create ON public.act_ru_task USING btree (create_time_);


--
-- Name: act_idx_task_exec; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_task_exec ON public.act_ru_task USING btree (execution_id_);


--
-- Name: act_idx_task_procdef; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_task_procdef ON public.act_ru_task USING btree (proc_def_id_);


--
-- Name: act_idx_task_procinst; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_task_procinst ON public.act_ru_task USING btree (proc_inst_id_);


--
-- Name: act_idx_task_scope; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_task_scope ON public.act_ru_task USING btree (scope_id_, scope_type_);


--
-- Name: act_idx_task_scope_def; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_task_scope_def ON public.act_ru_task USING btree (scope_definition_id_, scope_type_);


--
-- Name: act_idx_task_sub_scope; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_task_sub_scope ON public.act_ru_task USING btree (sub_scope_id_, scope_type_);


--
-- Name: act_idx_timer_job_correlation_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_timer_job_correlation_id ON public.act_ru_timer_job USING btree (correlation_id_);


--
-- Name: act_idx_timer_job_custom_values_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_timer_job_custom_values_id ON public.act_ru_timer_job USING btree (custom_values_id_);


--
-- Name: act_idx_timer_job_duedate; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_timer_job_duedate ON public.act_ru_timer_job USING btree (duedate_);


--
-- Name: act_idx_timer_job_exception_stack_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_timer_job_exception_stack_id ON public.act_ru_timer_job USING btree (exception_stack_id_);


--
-- Name: act_idx_timer_job_execution_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_timer_job_execution_id ON public.act_ru_timer_job USING btree (execution_id_);


--
-- Name: act_idx_timer_job_proc_def_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_timer_job_proc_def_id ON public.act_ru_timer_job USING btree (proc_def_id_);


--
-- Name: act_idx_timer_job_process_instance_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_timer_job_process_instance_id ON public.act_ru_timer_job USING btree (process_instance_id_);


--
-- Name: act_idx_tjob_scope; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_tjob_scope ON public.act_ru_timer_job USING btree (scope_id_, scope_type_);


--
-- Name: act_idx_tjob_scope_def; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_tjob_scope_def ON public.act_ru_timer_job USING btree (scope_definition_id_, scope_type_);


--
-- Name: act_idx_tjob_sub_scope; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_tjob_sub_scope ON public.act_ru_timer_job USING btree (sub_scope_id_, scope_type_);


--
-- Name: act_idx_tskass_task; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_tskass_task ON public.act_ru_identitylink USING btree (task_id_);


--
-- Name: act_idx_var_bytearray; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_var_bytearray ON public.act_ru_variable USING btree (bytearray_id_);


--
-- Name: act_idx_var_exe; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_var_exe ON public.act_ru_variable USING btree (execution_id_);


--
-- Name: act_idx_var_procinst; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_var_procinst ON public.act_ru_variable USING btree (proc_inst_id_);


--
-- Name: act_idx_variable_task_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX act_idx_variable_task_id ON public.act_ru_variable USING btree (task_id_);


--
-- Name: flw_idx_batch_part; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX flw_idx_batch_part ON public.flw_ru_batch_part USING btree (batch_id_);


--
-- Name: idx_flow_alert_record_instance; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_flow_alert_record_instance ON public.flow_alert_record USING btree (process_instance_id);


--
-- Name: idx_flow_alert_route_rule_enabled; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_flow_alert_route_rule_enabled ON public.flow_alert_route_rule USING btree (enabled, priority DESC);


--
-- Name: idx_flow_copy_instance; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_flow_copy_instance ON public.flow_copy USING btree (process_instance_id);


--
-- Name: idx_flow_copy_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_flow_copy_user ON public.flow_copy USING btree (user_id, create_time DESC);


--
-- Name: uk_flow_alert_record_alert; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uk_flow_alert_record_alert ON public.flow_alert_record USING btree (alert_id, process_definition_key, deleted);


--
-- Name: uk_flow_category_code; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uk_flow_category_code ON public.flow_category USING btree (code, tenant_id, deleted);


--
-- Name: act_ru_identitylink act_fk_athrz_procedef; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_identitylink
    ADD CONSTRAINT act_fk_athrz_procedef FOREIGN KEY (proc_def_id_) REFERENCES public.act_re_procdef(id_);


--
-- Name: act_ge_bytearray act_fk_bytearr_depl; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ge_bytearray
    ADD CONSTRAINT act_fk_bytearr_depl FOREIGN KEY (deployment_id_) REFERENCES public.act_re_deployment(id_);


--
-- Name: act_ru_deadletter_job act_fk_deadletter_job_custom_values; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_deadletter_job
    ADD CONSTRAINT act_fk_deadletter_job_custom_values FOREIGN KEY (custom_values_id_) REFERENCES public.act_ge_bytearray(id_);


--
-- Name: act_ru_deadletter_job act_fk_deadletter_job_exception; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_deadletter_job
    ADD CONSTRAINT act_fk_deadletter_job_exception FOREIGN KEY (exception_stack_id_) REFERENCES public.act_ge_bytearray(id_);


--
-- Name: act_ru_deadletter_job act_fk_deadletter_job_execution; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_deadletter_job
    ADD CONSTRAINT act_fk_deadletter_job_execution FOREIGN KEY (execution_id_) REFERENCES public.act_ru_execution(id_);


--
-- Name: act_ru_deadletter_job act_fk_deadletter_job_proc_def; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_deadletter_job
    ADD CONSTRAINT act_fk_deadletter_job_proc_def FOREIGN KEY (proc_def_id_) REFERENCES public.act_re_procdef(id_);


--
-- Name: act_ru_deadletter_job act_fk_deadletter_job_process_instance; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_deadletter_job
    ADD CONSTRAINT act_fk_deadletter_job_process_instance FOREIGN KEY (process_instance_id_) REFERENCES public.act_ru_execution(id_);


--
-- Name: act_ru_event_subscr act_fk_event_exec; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_event_subscr
    ADD CONSTRAINT act_fk_event_exec FOREIGN KEY (execution_id_) REFERENCES public.act_ru_execution(id_);


--
-- Name: act_ru_execution act_fk_exe_parent; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_execution
    ADD CONSTRAINT act_fk_exe_parent FOREIGN KEY (parent_id_) REFERENCES public.act_ru_execution(id_);


--
-- Name: act_ru_execution act_fk_exe_procdef; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_execution
    ADD CONSTRAINT act_fk_exe_procdef FOREIGN KEY (proc_def_id_) REFERENCES public.act_re_procdef(id_);


--
-- Name: act_ru_execution act_fk_exe_procinst; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_execution
    ADD CONSTRAINT act_fk_exe_procinst FOREIGN KEY (proc_inst_id_) REFERENCES public.act_ru_execution(id_);


--
-- Name: act_ru_execution act_fk_exe_super; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_execution
    ADD CONSTRAINT act_fk_exe_super FOREIGN KEY (super_exec_) REFERENCES public.act_ru_execution(id_);


--
-- Name: act_ru_external_job act_fk_external_job_custom_values; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_external_job
    ADD CONSTRAINT act_fk_external_job_custom_values FOREIGN KEY (custom_values_id_) REFERENCES public.act_ge_bytearray(id_);


--
-- Name: act_ru_external_job act_fk_external_job_exception; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_external_job
    ADD CONSTRAINT act_fk_external_job_exception FOREIGN KEY (exception_stack_id_) REFERENCES public.act_ge_bytearray(id_);


--
-- Name: act_ru_identitylink act_fk_idl_procinst; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_identitylink
    ADD CONSTRAINT act_fk_idl_procinst FOREIGN KEY (proc_inst_id_) REFERENCES public.act_ru_execution(id_);


--
-- Name: act_procdef_info act_fk_info_json_ba; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_procdef_info
    ADD CONSTRAINT act_fk_info_json_ba FOREIGN KEY (info_json_id_) REFERENCES public.act_ge_bytearray(id_);


--
-- Name: act_procdef_info act_fk_info_procdef; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_procdef_info
    ADD CONSTRAINT act_fk_info_procdef FOREIGN KEY (proc_def_id_) REFERENCES public.act_re_procdef(id_);


--
-- Name: act_ru_job act_fk_job_custom_values; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_job
    ADD CONSTRAINT act_fk_job_custom_values FOREIGN KEY (custom_values_id_) REFERENCES public.act_ge_bytearray(id_);


--
-- Name: act_ru_job act_fk_job_exception; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_job
    ADD CONSTRAINT act_fk_job_exception FOREIGN KEY (exception_stack_id_) REFERENCES public.act_ge_bytearray(id_);


--
-- Name: act_ru_job act_fk_job_execution; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_job
    ADD CONSTRAINT act_fk_job_execution FOREIGN KEY (execution_id_) REFERENCES public.act_ru_execution(id_);


--
-- Name: act_ru_job act_fk_job_proc_def; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_job
    ADD CONSTRAINT act_fk_job_proc_def FOREIGN KEY (proc_def_id_) REFERENCES public.act_re_procdef(id_);


--
-- Name: act_ru_job act_fk_job_process_instance; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_job
    ADD CONSTRAINT act_fk_job_process_instance FOREIGN KEY (process_instance_id_) REFERENCES public.act_ru_execution(id_);


--
-- Name: act_id_membership act_fk_memb_group; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_id_membership
    ADD CONSTRAINT act_fk_memb_group FOREIGN KEY (group_id_) REFERENCES public.act_id_group(id_);


--
-- Name: act_id_membership act_fk_memb_user; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_id_membership
    ADD CONSTRAINT act_fk_memb_user FOREIGN KEY (user_id_) REFERENCES public.act_id_user(id_);


--
-- Name: act_re_model act_fk_model_deployment; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_re_model
    ADD CONSTRAINT act_fk_model_deployment FOREIGN KEY (deployment_id_) REFERENCES public.act_re_deployment(id_);


--
-- Name: act_re_model act_fk_model_source; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_re_model
    ADD CONSTRAINT act_fk_model_source FOREIGN KEY (editor_source_value_id_) REFERENCES public.act_ge_bytearray(id_);


--
-- Name: act_re_model act_fk_model_source_extra; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_re_model
    ADD CONSTRAINT act_fk_model_source_extra FOREIGN KEY (editor_source_extra_value_id_) REFERENCES public.act_ge_bytearray(id_);


--
-- Name: act_id_priv_mapping act_fk_priv_mapping; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_id_priv_mapping
    ADD CONSTRAINT act_fk_priv_mapping FOREIGN KEY (priv_id_) REFERENCES public.act_id_priv(id_);


--
-- Name: act_ru_suspended_job act_fk_suspended_job_custom_values; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_suspended_job
    ADD CONSTRAINT act_fk_suspended_job_custom_values FOREIGN KEY (custom_values_id_) REFERENCES public.act_ge_bytearray(id_);


--
-- Name: act_ru_suspended_job act_fk_suspended_job_exception; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_suspended_job
    ADD CONSTRAINT act_fk_suspended_job_exception FOREIGN KEY (exception_stack_id_) REFERENCES public.act_ge_bytearray(id_);


--
-- Name: act_ru_suspended_job act_fk_suspended_job_execution; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_suspended_job
    ADD CONSTRAINT act_fk_suspended_job_execution FOREIGN KEY (execution_id_) REFERENCES public.act_ru_execution(id_);


--
-- Name: act_ru_suspended_job act_fk_suspended_job_proc_def; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_suspended_job
    ADD CONSTRAINT act_fk_suspended_job_proc_def FOREIGN KEY (proc_def_id_) REFERENCES public.act_re_procdef(id_);


--
-- Name: act_ru_suspended_job act_fk_suspended_job_process_instance; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_suspended_job
    ADD CONSTRAINT act_fk_suspended_job_process_instance FOREIGN KEY (process_instance_id_) REFERENCES public.act_ru_execution(id_);


--
-- Name: act_ru_task act_fk_task_exe; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_task
    ADD CONSTRAINT act_fk_task_exe FOREIGN KEY (execution_id_) REFERENCES public.act_ru_execution(id_);


--
-- Name: act_ru_task act_fk_task_procdef; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_task
    ADD CONSTRAINT act_fk_task_procdef FOREIGN KEY (proc_def_id_) REFERENCES public.act_re_procdef(id_);


--
-- Name: act_ru_task act_fk_task_procinst; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_task
    ADD CONSTRAINT act_fk_task_procinst FOREIGN KEY (proc_inst_id_) REFERENCES public.act_ru_execution(id_);


--
-- Name: act_ru_timer_job act_fk_timer_job_custom_values; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_timer_job
    ADD CONSTRAINT act_fk_timer_job_custom_values FOREIGN KEY (custom_values_id_) REFERENCES public.act_ge_bytearray(id_);


--
-- Name: act_ru_timer_job act_fk_timer_job_exception; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_timer_job
    ADD CONSTRAINT act_fk_timer_job_exception FOREIGN KEY (exception_stack_id_) REFERENCES public.act_ge_bytearray(id_);


--
-- Name: act_ru_timer_job act_fk_timer_job_execution; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_timer_job
    ADD CONSTRAINT act_fk_timer_job_execution FOREIGN KEY (execution_id_) REFERENCES public.act_ru_execution(id_);


--
-- Name: act_ru_timer_job act_fk_timer_job_proc_def; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_timer_job
    ADD CONSTRAINT act_fk_timer_job_proc_def FOREIGN KEY (proc_def_id_) REFERENCES public.act_re_procdef(id_);


--
-- Name: act_ru_timer_job act_fk_timer_job_process_instance; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_timer_job
    ADD CONSTRAINT act_fk_timer_job_process_instance FOREIGN KEY (process_instance_id_) REFERENCES public.act_ru_execution(id_);


--
-- Name: act_ru_identitylink act_fk_tskass_task; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_identitylink
    ADD CONSTRAINT act_fk_tskass_task FOREIGN KEY (task_id_) REFERENCES public.act_ru_task(id_);


--
-- Name: act_ru_variable act_fk_var_bytearray; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_variable
    ADD CONSTRAINT act_fk_var_bytearray FOREIGN KEY (bytearray_id_) REFERENCES public.act_ge_bytearray(id_);


--
-- Name: act_ru_variable act_fk_var_exe; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_variable
    ADD CONSTRAINT act_fk_var_exe FOREIGN KEY (execution_id_) REFERENCES public.act_ru_execution(id_);


--
-- Name: act_ru_variable act_fk_var_procinst; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_ru_variable
    ADD CONSTRAINT act_fk_var_procinst FOREIGN KEY (proc_inst_id_) REFERENCES public.act_ru_execution(id_);


--
-- Name: flw_ru_batch_part flw_fk_batch_part_parent; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.flw_ru_batch_part
    ADD CONSTRAINT flw_fk_batch_part_parent FOREIGN KEY (batch_id_) REFERENCES public.flw_ru_batch(id_);


--
-- PostgreSQL database dump complete
--

\unrestrict o26nKSoizOO52ZnGpzq3GK5reCHJwKK23GCACIoiQZabrZghqecgJZJoI4fAXyd

