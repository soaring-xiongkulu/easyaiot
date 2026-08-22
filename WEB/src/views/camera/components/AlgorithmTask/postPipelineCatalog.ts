import type { PostPipelineStep, PostPluginMeta } from '@/api/device/post_pipeline';

export const DEFAULT_PIPELINE: PostPipelineStep[] = [
  { plugin: 'region_gate', enabled: true, params: { hit_mode: 'center' } },
  { plugin: 'default_pass', enabled: true, params: {} },
];

export const KIND_LABELS: Record<string, string> = {
  filter: '过滤',
  enrich: '富化',
  render: '渲染',
  decide: '决策',
};

export const KIND_COLORS: Record<string, string> = {
  filter: 'blue',
  enrich: 'purple',
  render: 'cyan',
  decide: 'green',
};

export function clonePipeline(steps: PostPipelineStep[] | null | undefined): PostPipelineStep[] {
  if (!steps || !steps.length) {
    return DEFAULT_PIPELINE.map((s) => ({ ...s, params: { ...(s.params || {}) } }));
  }
  return steps.map((s) => ({
    ...s,
    params: s.params ? { ...s.params } : {},
  }));
}

export function effectiveSteps(steps: PostPipelineStep[]): PostPipelineStep[] {
  const enabled = steps.filter((s) => s.enabled !== false);
  if (!enabled.length) {
    return [{ plugin: 'default_pass', enabled: true, params: {} }];
  }
  const hasPass = enabled.some((s) => s.plugin === 'default_pass');
  if (hasPass) return enabled;
  return [...enabled, { plugin: 'default_pass', enabled: true, params: {} }];
}

export function pluginLabel(catalog: PostPluginMeta[], pluginId: string): string {
  const hit = catalog.find((p) => p.id === pluginId);
  return hit?.name || pluginId;
}

export function buildDefaultParams(schema?: Record<string, unknown>): Record<string, unknown> {
  const props = (schema?.properties || {}) as Record<string, Record<string, unknown>>;
  const out: Record<string, unknown> = {};
  for (const [key, meta] of Object.entries(props)) {
    if (meta.default !== undefined) {
      out[key] = meta.default;
    }
  }
  return out;
}

export function createStepFromPlugin(plugin: PostPluginMeta): PostPipelineStep {
  return {
    plugin: plugin.id,
    version: plugin.version,
    enabled: true,
    params: buildDefaultParams(plugin.params_schema),
    fail_strategy: 'fail_open',
    endpoint: plugin.builtin ? undefined : (plugin.service?.endpoint as string | undefined),
  };
}

export function localSampleEvent(taskContext?: {
  id?: number | null;
  task_name?: string;
  task_type?: string;
  device_ids?: string[];
}): Record<string, unknown> {
  const now = new Date().toISOString();
  const deviceId = taskContext?.device_ids?.[0] || 'demo-device';
  return {
    schema: 'infer_event.v1',
    event_kind: 'infer',
    correlation_id: `local-debug-${Date.now()}`,
    task_id: Number(taskContext?.id || 1),
    task_name: taskContext?.task_name || '',
    task_type: taskContext?.task_type || 'realtime',
    device_id: deviceId,
    timestamp: now,
    frame_width: 1920,
    frame_height: 1080,
    detections: [
      {
        bbox: [0.42, 0.38, 0.58, 0.72],
        class_id: 0,
        class_name: 'person',
        confidence: 0.86,
        track_id: 1,
      },
    ],
  };
}
