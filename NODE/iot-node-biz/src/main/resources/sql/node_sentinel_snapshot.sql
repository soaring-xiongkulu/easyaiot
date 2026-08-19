CREATE TABLE IF NOT EXISTS public.node_sentinel_snapshot (
    node_id bigint NOT NULL PRIMARY KEY,
    node_profile character varying(256) DEFAULT '',
    sentinel_version character varying(32),
    probe_level character varying(8) DEFAULT 'L0',
    components jsonb NOT NULL DEFAULT '[]'::jsonb,
    schedulable_capabilities jsonb NOT NULL DEFAULT '{}'::jsonb,
    summary jsonb NOT NULL DEFAULT '{}'::jsonb,
    environment_profile jsonb NOT NULL DEFAULT '{}'::jsonb,
    declared_capabilities jsonb NOT NULL DEFAULT '{}'::jsonb,
    operational_state character varying(32) DEFAULT 'unknown',
    remediation jsonb NOT NULL DEFAULT '{}'::jsonb,
    last_probe_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creator character varying(64),
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updater character varying(64),
    update_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    deleted smallint DEFAULT 0 NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_node_sentinel_snapshot_probe
    ON public.node_sentinel_snapshot (last_probe_at DESC);
