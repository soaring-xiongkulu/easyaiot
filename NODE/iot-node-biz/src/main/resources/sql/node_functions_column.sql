ALTER TABLE public.compute_node ALTER COLUMN node_role TYPE character varying(256);
COMMENT ON COLUMN public.compute_node.node_role IS '节点功能 CSV：algorithm,forward,live,train,llm,label,infer,mqtt,nfs,transform';
ALTER TABLE public.node_sentinel_snapshot ALTER COLUMN node_profile TYPE character varying(256);
COMMENT ON COLUMN public.node_sentinel_snapshot.node_profile IS '节点功能 CSV，与 NODE_FUNCTIONS 一致';
