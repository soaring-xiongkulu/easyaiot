CREATE SEQUENCE IF NOT EXISTS public.node_storage_op_log_id_seq START WITH 1 INCREMENT BY 1;

CREATE TABLE IF NOT EXISTS public.node_storage_op_log (
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
    deleted smallint DEFAULT 0 NOT NULL,
    CONSTRAINT node_storage_op_log_pkey PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS idx_node_storage_op_log_node_time
    ON public.node_storage_op_log (node_id, create_time DESC)
    WHERE deleted = 0;
