/** POST 后处理规则链类型与工具 */

export interface PostPipelineStep {
  plugin: string;
  version?: string;
  enabled?: boolean;
  params?: Record<string, unknown>;
  fail_strategy?: string;
  endpoint?: string;
}

export interface PostPluginCatalogItem {
  id: string;
  name: string;
  kinds: string[];
  builtin: boolean;
  description?: string;
  params_schema?: {
    type?: string;
    properties?: Record<
      string,
      {
        type?: string;
        title?: string;
        default?: unknown;
        enum?: string[];
        items?: { type?: string };
      }
    >;
  };
  version?: string;
  service?: Record<string, unknown>;
}

export interface PostPipelineTaskContext {
  id?: number | null;
  task_name?: string;
  task_type?: string;
  device_ids?: string[];
}

export interface PostPipelineDebugResult {
  result?: string;
  drop_reason?: string;
  trace?: Array<Record<string, unknown>>;
  alert_payload?: Record<string, unknown> | null;
  error?: string;
}

/** 规则链首尾固定插件（各仅 1 个，不可增删） */
export const FIXED_HEAD_PLUGIN = 'region_gate';
export const FIXED_TAIL_PLUGIN = 'default_pass';
export const FIXED_PLUGINS = new Set([FIXED_HEAD_PLUGIN, FIXED_TAIL_PLUGIN]);

export const DEFAULT_PIPELINE: PostPipelineStep[] = [
  { plugin: FIXED_HEAD_PLUGIN, enabled: true, params: { hit_mode: 'center' } },
  { plugin: FIXED_TAIL_PLUGIN, enabled: true, params: {} },
];

export const PLUGIN_KIND_LABEL: Record<string, string> = {
  filter: '过滤',
  decide: '决策',
  enrich: '富化',
};

export const PLUGIN_KIND_COLOR: Record<string, string> = {
  filter: '#1677ff',
  decide: '#52c41a',
  enrich: '#722ed1',
};

/** UI 展示名（避免「闸门」等非专业表述） */
export const PLUGIN_DISPLAY_NAME: Record<string, string> = {
  region_gate: '区域过滤',
  default_pass: '告警输出',
  line_cross: '越线检测',
  region_enter_exit: '区域进出',
  dwell_timer: '停留超时',
  headcount_gate: '人数阈值',
  user_script: '业务脚本',
};

export const PARAM_ENUM_LABEL: Record<string, Record<string, string>> = {
  hit_mode: { center: '中心点', any: '任意点', all: '全部点' },
  direction: { both: '双向', forward: '正向', backward: '反向' },
  sample_point: { center: '中心点', bottom: '底边中点' },
  event_type: { enter: '进入', exit: '离开', both: '进入或离开' },
  operator: { gte: '≥', lte: '≤', eq: '=' },
  count_mode: { in_regions: '区域内', all: '全部目标' },
};

export const BUILTIN_PLUGIN_CATALOG: PostPluginCatalogItem[] = [
  {
    id: 'region_gate',
    name: '区域过滤',
    kinds: ['filter'],
    builtin: true,
    description: '首步：按检测区域过滤目标，区域外的检测结果将被忽略',
    params_schema: {
      properties: {
        hit_mode: {
          type: 'string',
          title: '命中判定',
          default: 'center',
          enum: ['center', 'any', 'all'],
        },
      },
    },
  },
  {
    id: 'line_cross',
    name: '越线检测',
    kinds: ['filter', 'decide'],
    builtin: true,
    description: '检测目标越过检测线时触发（需开启目标追踪，并配置 line 类型区域）',
    params_schema: {
      properties: {
        direction: {
          type: 'string',
          enum: ['both', 'forward', 'backward'],
          default: 'both',
          title: '越线方向',
        },
        sample_point: {
          type: 'string',
          enum: ['center', 'bottom'],
          default: 'center',
          title: '采样点',
        },
        target_classes: { type: 'array', items: { type: 'string' }, title: '目标类别' },
      },
    },
  },
  {
    id: 'region_enter_exit',
    name: '区域进出',
    kinds: ['filter', 'decide'],
    builtin: true,
    description: '检测目标进入或离开多边形区域（需开启目标追踪）',
    params_schema: {
      properties: {
        event_type: {
          type: 'string',
          enum: ['enter', 'exit', 'both'],
          default: 'both',
          title: '事件类型',
        },
        hit_mode: {
          type: 'string',
          enum: ['center', 'any'],
          default: 'center',
          title: '命中判定',
        },
        target_classes: { type: 'array', items: { type: 'string' }, title: '目标类别' },
      },
    },
  },
  {
    id: 'dwell_timer',
    name: '停留超时',
    kinds: ['filter', 'decide'],
    builtin: true,
    description: '目标在区域内停留超过阈值时触发（需开启目标追踪）',
    params_schema: {
      properties: {
        min_dwell_sec: { type: 'number', default: 5, title: '最短停留（秒）' },
        hit_mode: {
          type: 'string',
          enum: ['center', 'any'],
          default: 'center',
          title: '命中判定',
        },
        target_classes: { type: 'array', items: { type: 'string' }, title: '目标类别' },
      },
    },
  },
  {
    id: 'headcount_gate',
    name: '人数阈值',
    kinds: ['filter', 'decide'],
    builtin: true,
    description: '区域内目标数量满足阈值条件时放行',
    params_schema: {
      properties: {
        threshold: { type: 'integer', default: 1, title: '人数阈值' },
        operator: {
          type: 'string',
          enum: ['gte', 'lte', 'eq'],
          default: 'gte',
          title: '比较方式',
        },
        count_mode: {
          type: 'string',
          enum: ['in_regions', 'all'],
          default: 'in_regions',
          title: '计数范围',
        },
        hit_mode: {
          type: 'string',
          enum: ['center', 'any'],
          default: 'center',
          title: '命中判定',
        },
        target_classes: { type: 'array', items: { type: 'string' }, title: '目标类别' },
      },
    },
  },
  {
    id: 'user_script',
    name: '业务脚本',
    kinds: ['enrich'],
    builtin: true,
    description: '调用外部脚本服务做业务富化（与 Python 业务脚本 Worker 独立）',
    params_schema: { properties: {} },
  },
  {
    id: 'default_pass',
    name: '告警输出',
    kinds: ['decide'],
    builtin: true,
    description: '末步：前面步骤全部通过后，将本次检测正式写入告警记录',
    params_schema: { properties: {} },
  },
];

export function clonePipeline(steps: PostPipelineStep[] | null | undefined): PostPipelineStep[] {
  if (!Array.isArray(steps) || steps.length === 0) {
    return DEFAULT_PIPELINE.map((s) => ({ ...s, params: { ...(s.params || {}) } }));
  }
  return normalizePipelineStructure(steps);
}

export function normalizePipelineStructure(steps: PostPipelineStep[]): PostPipelineStep[] {
  const seen = new Set<string>();
  const middle: PostPipelineStep[] = [];
  let head: PostPipelineStep = { ...DEFAULT_PIPELINE[0], params: { ...DEFAULT_PIPELINE[0].params! } };
  let tail: PostPipelineStep = { ...DEFAULT_PIPELINE[1], params: {} };

  for (const step of steps) {
    const normalized: PostPipelineStep = {
      ...step,
      params: step.params ? { ...step.params } : {},
    };
    if (step.plugin === FIXED_HEAD_PLUGIN) {
      head = { ...normalized, enabled: true };
    } else if (step.plugin === FIXED_TAIL_PLUGIN) {
      tail = { ...normalized, enabled: true };
    } else if (!seen.has(step.plugin)) {
      seen.add(step.plugin);
      middle.push(normalized);
    }
  }
  return [head, ...middle, tail];
}

export function isCustomPipeline(steps: PostPipelineStep[] | null | undefined): boolean {
  return Array.isArray(steps) && steps.length > 0 && !isSameAsDefaultPipeline(steps);
}

export function isSameAsDefaultPipeline(steps: PostPipelineStep[] | null | undefined): boolean {
  if (!Array.isArray(steps) || steps.length === 0) {
    return true;
  }
  const normalized = normalizePipelineStructure(steps);
  const def = DEFAULT_PIPELINE;
  if (normalized.length !== def.length) {
    return false;
  }
  return normalized.every((step, index) => {
    const baseline = def[index];
    return (
      step.plugin === baseline.plugin
      && step.enabled !== false
      && JSON.stringify(step.params || {}) === JSON.stringify(baseline.params || {})
    );
  });
}

export function effectiveSteps(steps: PostPipelineStep[]): PostPipelineStep[] {
  const normalized = normalizePipelineStructure(steps);
  const enabled = normalized.filter((s) => s.enabled !== false);
  if (enabled.length === 0) {
    return [{ plugin: FIXED_TAIL_PLUGIN, enabled: true, params: {} }];
  }
  const hasTail = enabled.some((s) => s.plugin === FIXED_TAIL_PLUGIN);
  if (!hasTail) {
    return [...enabled, { plugin: FIXED_TAIL_PLUGIN, enabled: true, params: {} }];
  }
  return enabled;
}

export function summarizePipeline(steps: PostPipelineStep[] | null | undefined): string {
  if (!Array.isArray(steps) || steps.length === 0 || isSameAsDefaultPipeline(steps)) {
    return '在业务场景配置后处理规则链';
  }
  const normalized = normalizePipelineStructure(steps);
  const middleCount = normalized.filter(
    (s) => s.enabled !== false && !FIXED_PLUGINS.has(s.plugin),
  ).length;
  if (middleCount === 0) {
    return '已调整首尾步骤参数';
  }
  return `已配置 ${middleCount} 个中间步骤`;
}

export const STEP_UI_SUMMARY: Record<string, string> = {
  region_gate: '首步：只保留检测区域内的目标',
  default_pass: '末步：前面都通过，才产生告警',
  line_cross: '判断目标是否越过检测线',
  region_enter_exit: '判断目标进入或离开区域',
  dwell_timer: '判断目标在区域内停留是否超时',
  headcount_gate: '判断区域内目标数量是否达到阈值',
  user_script: '调用外部脚本补充业务判断',
};

export function stepUiSummary(pluginId: string, catalog: PostPluginCatalogItem[]): string {
  if (STEP_UI_SUMMARY[pluginId]) {
    return STEP_UI_SUMMARY[pluginId];
  }
  const meta = findPluginMeta(catalog, pluginId);
  if (meta?.description) {
    return meta.description.length > 56 ? `${meta.description.slice(0, 56)}…` : meta.description;
  }
  return pluginId;
}

export function findPluginMeta(
  catalog: PostPluginCatalogItem[],
  pluginId: string,
): PostPluginCatalogItem | undefined {
  return catalog.find((p) => p.id === pluginId);
}

export function pluginDisplayName(
  catalog: PostPluginCatalogItem[],
  pluginId: string,
): string {
  return (
    findPluginMeta(catalog, pluginId)?.name
    || PLUGIN_DISPLAY_NAME[pluginId]
    || pluginId
  );
}

export function isFixedPlugin(pluginId: string): boolean {
  return FIXED_PLUGINS.has(pluginId);
}

export function buildStepFromPlugin(plugin: PostPluginCatalogItem): PostPipelineStep {
  const params: Record<string, unknown> = {};
  const props = plugin.params_schema?.properties || {};
  for (const [key, schema] of Object.entries(props)) {
    if (schema.default !== undefined) {
      params[key] = schema.default;
    }
  }
  const step: PostPipelineStep = {
    plugin: plugin.id,
    enabled: true,
    params,
  };
  if (!plugin.builtin && plugin.version) {
    step.version = plugin.version;
    step.fail_strategy = 'fail_open';
  }
  return step;
}

export function enumOptionLabel(fieldKey: string, value: string): string {
  return PARAM_ENUM_LABEL[fieldKey]?.[value] || value;
}
