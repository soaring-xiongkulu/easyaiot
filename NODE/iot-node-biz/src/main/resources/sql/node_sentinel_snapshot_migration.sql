ALTER TABLE IF EXISTS public.node_sentinel_snapshot
    ADD COLUMN IF NOT EXISTS environment_profile jsonb NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE IF EXISTS public.node_sentinel_snapshot
    ADD COLUMN IF NOT EXISTS declared_capabilities jsonb NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE IF EXISTS public.node_sentinel_snapshot
    ADD COLUMN IF NOT EXISTS operational_state character varying(32) DEFAULT 'unknown';
ALTER TABLE IF EXISTS public.node_sentinel_snapshot
    ADD COLUMN IF NOT EXISTS remediation jsonb NOT NULL DEFAULT '{}'::jsonb;
