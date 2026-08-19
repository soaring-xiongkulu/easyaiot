CREATE TABLE IF NOT EXISTS public.node_sentinel_remediate_log (
    id bigserial PRIMARY KEY,
    node_id bigint NOT NULL,
    component_id character varying(64) NOT NULL,
    mark character varying(32),
    action character varying(64),
    success boolean,
    exhausted boolean DEFAULT false,
    attempt_count integer DEFAULT 0,
    max_attempts integer DEFAULT 3,
    probe_state character varying(32),
    message text,
    logs jsonb NOT NULL DEFAULT '[]'::jsonb,
    creator character varying(64),
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updater character varying(64),
    update_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    deleted smallint DEFAULT 0 NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_node_sentinel_remediate_log_node
    ON public.node_sentinel_remediate_log (node_id, create_time DESC);
