<template>
  <BasicDrawer
    v-bind="$attrs"
    @register="register"
    width="98%"
    placement="right"
    :showFooter="true"
    :showCancelBtn="false"
    :showOkBtn="false"
    destroy-on-close
    :z-index="1200"
    root-class-name="post-pipeline-drawer"
  >
    <template #title>
      <div class="pp-drawer-title">
        <div class="pp-drawer-title__main">
          <Icon icon="mdi:source-branch" :size="22" class="pp-drawer-title__icon" />
          <div>
            <div class="pp-drawer-title__text">后处理规则链</div>
            <div class="pp-drawer-title__sub">{{ headerSubtitle }}</div>
          </div>
        </div>
        <div class="pp-drawer-title__actions">
          <Button size="small" :disabled="disabled" @click="openDebugDrawer">
            <template #icon><ExperimentOutlined /></template>
            在线调试
          </Button>
        </div>
      </div>
    </template>

    <template #footer>
      <div class="pp-footer">
        <div class="pp-footer__hint">
          <InfoCircleOutlined />
          <span>推理完成后依次执行：区域过滤 → 中间业务判断（可选）→ 告警输出；仅当末步通过时才产生告警。</span>
        </div>
        <div class="pp-footer__btns">
          <Button @click="handleReset" :disabled="disabled">恢复默认</Button>
          <Button @click="closeDrawer">取消</Button>
          <Button type="primary" :disabled="disabled" @click="handleApply">保存配置</Button>
        </div>
      </div>
    </template>

    <Spin :spinning="loading">
      <div class="pp-shell">
        <a-alert
          class="pp-intro"
          type="info"
          show-icon
          message="启用告警事件后，此处配置检测完成后的过滤与告警判定流程；保存任务后生效。"
        />

        <div class="pp-workspace">
          <aside class="pp-panel pp-panel--library">
            <div class="pp-panel__head pp-panel__head--library">
              <span class="pp-panel__title">可选插件</span>
              <a-input-search
                v-model:value="pluginSearch"
                class="pp-panel__search"
                allow-clear
                placeholder="搜索"
                size="small"
              />
            </div>
            <div class="pp-plugin-list">
              <template v-if="groupedAddablePlugins.builtin.length">
                <div class="pp-plugin-group">内置</div>
                <div
                  v-for="plugin in groupedAddablePlugins.builtin"
                  :key="plugin.id"
                  class="pp-plugin-card"
                  :class="{ disabled: disabled }"
                  @click="addPlugin(plugin)"
                >
                  <div class="pp-plugin-card__top">
                    <span class="pp-plugin-card__name">{{ plugin.name }}</span>
                    <a-tag v-for="k in plugin.kinds" :key="k" :color="kindColor(k)" size="small">
                      {{ kindLabelText(k) }}
                    </a-tag>
                  </div>
                  <div class="pp-plugin-card__desc">{{ plugin.description || plugin.id }}</div>
                  <PlusOutlined class="pp-plugin-card__add" />
                </div>
              </template>

              <template v-if="groupedAddablePlugins.external.length">
                <div class="pp-plugin-group">外置</div>
                <div
                  v-for="plugin in groupedAddablePlugins.external"
                  :key="plugin.id"
                  class="pp-plugin-card external"
                  :class="{ disabled: disabled }"
                  @click="addPlugin(plugin)"
                >
                  <div class="pp-plugin-card__top">
                    <span class="pp-plugin-card__name">{{ plugin.name }}</span>
                    <a-tag color="orange" size="small">外置</a-tag>
                  </div>
                  <div class="pp-plugin-card__desc">{{ plugin.description || plugin.id }}</div>
                  <PlusOutlined class="pp-plugin-card__add" />
                </div>
              </template>

              <a-empty
                v-if="!groupedAddablePlugins.builtin.length && !groupedAddablePlugins.external.length"
                :description="usedPluginIds.size ? '所有可选插件已添加' : '无匹配插件'"
                :image="false"
              />
            </div>
          </aside>

          <section class="pp-panel pp-panel--steps">
            <div class="pp-panel__head">
              <span>执行步骤</span>
              <span class="pp-panel__meta">{{ localSteps.length }} 步</span>
            </div>
            <div class="pp-steps-body" @click="clearSelection">
              <a-alert
                v-if="middleStepCount === 0"
                class="pp-steps-tip"
                type="info"
                show-icon
                message="默认仅含首尾两步。如需越线、停留、人数等判定，请从左侧添加中间步骤。"
                @click.stop
              />
              <div class="pp-steps-list">
                <template v-for="(step, index) in localSteps" :key="step.uid">
                  <div v-if="index > 0" class="pp-step-connector" aria-hidden="true">
                    <span class="pp-step-connector__line" />
                    <span class="pp-step-connector__arrow">↓</span>
                  </div>
                  <div
                    class="pp-step-card"
                    :class="{
                      active: selectedIndex === index && !isFixedPlugin(step.plugin),
                      'is-pinned': isFixedPlugin(step.plugin),
                      off: step.enabled === false,
                    }"
                    @click.stop="selectStep(index)"
                  >
                    <div class="pp-step-card__badge">
                      <LockOutlined v-if="isFixedPlugin(step.plugin)" class="pp-step-lock" />
                      <span class="pp-step-index">{{ index + 1 }}</span>
                    </div>
                    <div class="pp-step-card__body">
                      <div class="pp-step-card__title">
                        {{ pluginName(step.plugin) }}
                        <a-tag v-if="step.enabled === false && !isFixedPlugin(step.plugin)" color="default" size="small">已禁用</a-tag>
                      </div>
                      <div class="pp-step-card__sub">{{ getStepSummary(step.plugin) }}</div>
                    </div>
                    <div
                      v-if="!isFixedPlugin(step.plugin)"
                      class="pp-step-card__actions"
                      @click.stop
                    >
                      <a-tooltip title="上移">
                        <Button
                          type="text"
                          size="small"
                          :disabled="disabled || index <= 1"
                          @click="moveStep(index, -1)"
                        >
                          <ArrowUpOutlined />
                        </Button>
                      </a-tooltip>
                      <a-tooltip title="下移">
                        <Button
                          type="text"
                          size="small"
                          :disabled="disabled || index >= localSteps.length - 2"
                          @click="moveStep(index, 1)"
                        >
                          <ArrowDownOutlined />
                        </Button>
                      </a-tooltip>
                      <a-switch
                        :checked="step.enabled !== false"
                        size="small"
                        :disabled="disabled"
                        @change="(v: boolean) => toggleStep(index, v)"
                      />
                      <a-tooltip title="移除">
                        <Button
                          type="text"
                          size="small"
                          danger
                          :disabled="disabled"
                          @click="removeStep(index)"
                        >
                          <DeleteOutlined />
                        </Button>
                      </a-tooltip>
                    </div>
                  </div>
                </template>
              </div>
            </div>
          </section>

          <aside class="pp-panel pp-panel--config">
            <div class="pp-panel__head">
              <span>步骤参数</span>
            </div>
            <div v-if="selectedStep" class="pp-config-body">
              <div class="pp-config-head">
                <div class="pp-config-head__name">{{ pluginName(selectedStep.plugin) }}</div>
                <div class="pp-config-head__tags">
                  <a-tag v-for="k in pluginKinds(selectedStep.plugin)" :key="k" :color="kindColor(k)">
                    {{ kindLabelText(k) }}
                  </a-tag>
                </div>
                <div v-if="selectedMeta?.description" class="pp-config-head__desc">
                  {{ selectedMeta.description }}
                </div>
              </div>

              <a-alert
                v-if="selectedStep.plugin === 'default_pass'"
                type="info"
                show-icon
                class="mb-3"
                message="当前面所有步骤均未拦截本次检测时，本步骤会正式产生一条告警记录；任一步骤拦截则不会产生告警。"
              />

              <a-alert
                v-if="selectedStep.plugin === 'region_gate'"
                type="info"
                show-icon
                class="mb-3"
                message="根据摄像头已配置的检测区域过滤目标，区域外的检测框不会进入后续步骤。"
              />

              <a-alert
                v-if="needsTracking(selectedStep.plugin)"
                type="warning"
                show-icon
                class="mb-3"
                message="此插件依赖目标追踪，请在任务基础配置中开启「启用目标追踪」。"
              />

              <a-alert
                v-if="selectedStep.plugin === 'user_script' && !postProcessEnabled"
                type="warning"
                show-icon
                class="mb-3"
                message="业务脚本插件需配置 USER_SCRIPT_URL 环境变量；与 Python 业务脚本 Worker 为独立通道。"
              />

              <div v-if="!selectedMeta?.builtin" class="pp-ext-fields mb-3">
                <div class="pp-field">
                  <label>服务 Endpoint</label>
                  <a-input
                    v-model:value="selectedStep.endpoint"
                    :disabled="disabled"
                    placeholder="http://host:port/v1/process"
                  />
                </div>
                <div class="pp-field">
                  <label>失败策略</label>
                  <a-select
                    v-model:value="selectedStep.fail_strategy"
                    :disabled="disabled"
                    :options="failStrategyOptions"
                    style="width: 100%"
                  />
                </div>
              </div>

              <div class="pp-params">
                <div class="pp-params__title">参数配置</div>
                <template v-if="paramFields.length">
                  <div v-for="field in paramFields" :key="field.key" class="pp-field">
                    <label>{{ field.title }}</label>
                    <a-select
                      v-if="field.enum"
                      v-model:value="selectedStep.params![field.key]"
                      :disabled="disabled"
                      :options="field.enum.map((v) => ({
                        label: enumOptionLabel(field.key, v),
                        value: v,
                      }))"
                      style="width: 100%"
                    />
                    <a-input-number
                      v-else-if="field.type === 'integer'"
                      v-model:value="selectedStep.params![field.key]"
                      :disabled="disabled"
                      style="width: 100%"
                    />
                    <a-input-number
                      v-else-if="field.type === 'number'"
                      v-model:value="selectedStep.params![field.key]"
                      :disabled="disabled"
                      :step="0.1"
                      style="width: 100%"
                    />
                    <a-select
                      v-else-if="field.type === 'array'"
                      v-model:value="selectedStep.params![field.key]"
                      mode="tags"
                      :disabled="disabled"
                      placeholder="输入后回车"
                      style="width: 100%"
                    />
                    <a-input
                      v-else
                      v-model:value="selectedStep.params![field.key]"
                      :disabled="disabled"
                    />
                  </div>
                </template>
                <a-empty v-else description="此步骤无可配置参数" :image="false" />
              </div>
            </div>
            <a-empty v-else description="请选择步骤查看参数" :image="false" class="pp-config-empty" />
          </aside>
        </div>
      </div>
    </Spin>

    <PostPipelineDebugDrawer
      @register="registerDebugDrawer"
      :task-id="taskContext.id"
      :task-context="taskContext"
      :pipeline-steps="previewSteps"
      :all-plugins="catalog"
    />
  </BasicDrawer>
</template>

<script lang="ts" setup>
import { computed, ref, watch } from 'vue';
import {
  ArrowDownOutlined,
  ArrowUpOutlined,
  DeleteOutlined,
  ExperimentOutlined,
  InfoCircleOutlined,
  LockOutlined,
  PlusOutlined,
} from '@ant-design/icons-vue';
import { Spin } from 'ant-design-vue';
import { BasicDrawer, useDrawer, useDrawerInner } from '@/components/Drawer';
import { Button } from '@/components/Button';
import { Icon } from '@/components/Icon';
import { useMessage } from '@/hooks/web/useMessage';
import { getPostPluginCatalog } from '@/api/device/post_pipeline';
import PostPipelineDebugDrawer from './PostPipelineDebugDrawer.vue';
import {
  buildStepFromPlugin,
  BUILTIN_PLUGIN_CATALOG,
  clonePipeline,
  DEFAULT_PIPELINE,
  effectiveSteps,
  enumOptionLabel,
  findPluginMeta,
  FIXED_PLUGINS,
  isFixedPlugin,
  isSameAsDefaultPipeline,
  normalizePipelineStructure,
  PLUGIN_KIND_COLOR,
  PLUGIN_KIND_LABEL,
  PLUGIN_DISPLAY_NAME,
  pluginDisplayName,
  stepUiSummary as resolveStepUiSummary,
  type PostPipelineStep,
  type PostPluginCatalogItem,
  type PostPipelineTaskContext,
} from './postPipelineTypes';

defineOptions({ name: 'PostPipelineDrawer' });

interface LocalStep extends PostPipelineStep {
  uid: string;
}

const TRACKING_PLUGINS = new Set([
  'line_cross',
  'region_enter_exit',
  'dwell_timer',
]);

let uidSeq = 0;
function nextUid() {
  uidSeq += 1;
  return `step-${uidSeq}`;
}

function toLocalSteps(steps: PostPipelineStep[]): LocalStep[] {
  return normalizePipelineStructure(steps).map((s) => ({
    ...s,
    uid: nextUid(),
    params: { ...(s.params || {}) },
  }));
}

function fromLocalSteps(steps: LocalStep[]): PostPipelineStep[] {
  return normalizePipelineStructure(
    steps.map(({ uid, ...rest }) => ({
      ...rest,
      params: rest.params && Object.keys(rest.params).length ? rest.params : {},
    })),
  );
}

const { createMessage } = useMessage();
const [registerDebugDrawer, { openDrawer: openDebugDrawerInner }] = useDrawer();

const loading = ref(false);
const disabled = ref(false);
const postProcessEnabled = ref(false);
const taskContext = ref<PostPipelineTaskContext>({});
const onApplyRef = ref<((pipeline: PostPipelineStep[] | null) => void) | null>(null);

const catalog = ref<PostPluginCatalogItem[]>([]);
const localSteps = ref<LocalStep[]>([]);
const selectedIndex = ref(-1);
const pluginSearch = ref('');

const failStrategyOptions = [
  { label: 'fail_open（失败时跳过继续）', value: 'fail_open' },
  { label: 'fail_closed（失败时拦截丢弃）', value: 'fail_closed' },
];

const headerSubtitle = computed(() => {
  const ctx = taskContext.value;
  if (ctx.task_name) {
    return `${ctx.task_name}${ctx.task_type ? ` · ${ctx.task_type}` : ''}`;
  }
  return '配置推理事件的后处理过滤与告警输出流程';
});

const previewSteps = computed(() => effectiveSteps(fromLocalSteps(localSteps.value)));
const middleStepCount = computed(() => Math.max(0, localSteps.value.length - 2));
const selectedStep = computed(() => localSteps.value[selectedIndex.value] || null);
const selectedMeta = computed(() =>
  selectedStep.value ? findPluginMeta(catalog.value, selectedStep.value.plugin) : undefined,
);

const usedPluginIds = computed(() => new Set(localSteps.value.map((s) => s.plugin)));

const addablePlugins = computed(() => {
  const q = pluginSearch.value.trim().toLowerCase();
  const used = usedPluginIds.value;
  return catalog.value.filter((p) => {
    if (FIXED_PLUGINS.has(p.id) || used.has(p.id)) return false;
    if (!q) return true;
    return (
      p.id.toLowerCase().includes(q)
      || p.name.toLowerCase().includes(q)
      || (p.description || '').toLowerCase().includes(q)
    );
  });
});

const groupedAddablePlugins = computed(() => ({
  builtin: addablePlugins.value.filter((p) => p.builtin),
  external: addablePlugins.value.filter((p) => !p.builtin),
}));

const paramFields = computed(() => {
  const schema = selectedMeta.value?.params_schema?.properties || {};
  return Object.entries(schema).map(([key, val]) => ({
    key,
    title: val.title || key,
    type: val.type,
    enum: val.enum,
  }));
});

function kindLabelText(kind: string) {
  return PLUGIN_KIND_LABEL[kind] || kind;
}

function kindColor(kind: string) {
  return PLUGIN_KIND_COLOR[kind] || 'default';
}

function pluginName(pluginId: string) {
  return pluginDisplayName(catalog.value, pluginId);
}

function pluginKinds(pluginId: string) {
  return findPluginMeta(catalog.value, pluginId)?.kinds || [];
}

const getStepSummary = (pluginId: string) => resolveStepUiSummary(pluginId, catalog.value);

function needsTracking(pluginId: string) {
  return TRACKING_PLUGINS.has(pluginId);
}

function resolveDefaultSelectedIndex(steps: LocalStep[] = localSteps.value): number {
  if (steps.length > 2) return 1;
  return -1;
}

function reconcileSteps() {
  localSteps.value = toLocalSteps(fromLocalSteps(localSteps.value));
  if (selectedIndex.value >= localSteps.value.length) {
    selectedIndex.value = resolveDefaultSelectedIndex();
  }
}

function moveStep(index: number, direction: -1 | 1) {
  if (disabled.value) return;
  const target = index + direction;
  if (target <= 0 || target >= localSteps.value.length - 1) return;
  const steps = [...localSteps.value];
  [steps[index], steps[target]] = [steps[target], steps[index]];
  localSteps.value = steps;
  selectedIndex.value = target;
}

function clearSelection() {
  selectedIndex.value = -1;
}

function selectStep(index: number) {
  selectedIndex.value = index;
  ensureStepParams(localSteps.value[index]);
}

function ensureStepParams(step?: LocalStep | null) {
  if (!step) return;
  if (!step.params) step.params = {};
  const meta = findPluginMeta(catalog.value, step.plugin);
  const props = meta?.params_schema?.properties || {};
  for (const [key, schema] of Object.entries(props)) {
    if (step.params![key] === undefined && schema.default !== undefined) {
      step.params![key] = schema.default;
    }
  }
}

function addPlugin(plugin: PostPluginCatalogItem) {
  if (disabled.value) return;
  if (FIXED_PLUGINS.has(plugin.id)) {
    createMessage.info('区域过滤与告警输出为默认首尾步骤，无需手动添加');
    return;
  }
  if (usedPluginIds.value.has(plugin.id)) {
    createMessage.warning('该插件已在规则链中，每种插件仅可添加一次');
    return;
  }
  const step = { ...buildStepFromPlugin(plugin), uid: nextUid() };
  const insertAt = Math.max(1, localSteps.value.length - 1);
  localSteps.value.splice(insertAt, 0, step);
  selectedIndex.value = insertAt;
  ensureStepParams(step);
}

function removeStep(index: number) {
  if (disabled.value) return;
  const step = localSteps.value[index];
  if (!step || isFixedPlugin(step.plugin)) return;
  localSteps.value.splice(index, 1);
  reconcileSteps();
  if (selectedIndex.value >= localSteps.value.length) {
    selectedIndex.value = resolveDefaultSelectedIndex();
  }
}

function toggleStep(index: number, enabled: boolean) {
  if (disabled.value) return;
  const step = localSteps.value[index];
  if (!step || isFixedPlugin(step.plugin)) return;
  step.enabled = enabled;
}

function handleReset() {
  localSteps.value = toLocalSteps(DEFAULT_PIPELINE);
  selectedIndex.value = resolveDefaultSelectedIndex();
}

async function loadCatalog() {
  loading.value = true;
  try {
    const data = await getPostPluginCatalog();
    const builtins = data?.builtins || [];
    const externals = data?.externals || [];
    catalog.value = [...builtins, ...externals].map((p) => {
      const fallback = BUILTIN_PLUGIN_CATALOG.find((item) => item.id === p.id);
      return {
        ...p,
        name: PLUGIN_DISPLAY_NAME[p.id] || p.name,
        description: fallback?.description || p.description,
      };
    });
  } catch (e) {
    console.error(e);
    createMessage.warning('插件目录加载失败，已使用内置插件列表');
    catalog.value = [...BUILTIN_PLUGIN_CATALOG];
  } finally {
    loading.value = false;
  }
}

function openDebugDrawer() {
  openDebugDrawerInner(true, {});
}

function handleApply() {
  const steps = fromLocalSteps(localSteps.value);
  const pipeline = isSameAsDefaultPipeline(steps) ? null : steps;
  onApplyRef.value?.(pipeline);
  createMessage.success(pipeline ? '规则链已保存，提交任务后生效' : '已恢复默认规则链');
  closeDrawer();
}

const [register, { closeDrawer, setDrawerProps }] = useDrawerInner(async (data?: {
  pipeline?: PostPipelineStep[] | null;
  taskContext?: PostPipelineTaskContext;
  disabled?: boolean;
  postProcessEnabled?: boolean;
  onApply?: (pipeline: PostPipelineStep[] | null) => void;
}) => {
  disabled.value = !!data?.disabled;
  postProcessEnabled.value = !!data?.postProcessEnabled;
  taskContext.value = data?.taskContext || {};
  onApplyRef.value = data?.onApply || null;

  const initial = clonePipeline(
    Array.isArray(data?.pipeline) && data!.pipeline!.length ? data!.pipeline! : DEFAULT_PIPELINE,
  );
  localSteps.value = toLocalSteps(initial);
  selectedIndex.value = resolveDefaultSelectedIndex();
  pluginSearch.value = '';

  setDrawerProps({ open: true });
  await loadCatalog();
  if (selectedIndex.value >= 0) {
    ensureStepParams(localSteps.value[selectedIndex.value]);
  }
});

watch(localSteps, () => {
  if (localSteps.value.length < 2) {
    localSteps.value = toLocalSteps(DEFAULT_PIPELINE);
  }
  if (selectedIndex.value >= localSteps.value.length) {
    selectedIndex.value = resolveDefaultSelectedIndex();
  }
}, { deep: true });
</script>

<style lang="less" scoped>
.pp-drawer-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  width: 100%;
  padding-right: 8px;

  &__main {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  &__icon {
    color: #1677ff;
  }

  &__text {
    font-size: 16px;
    font-weight: 600;
    line-height: 1.3;
  }

  &__sub {
    font-size: 12px;
    color: rgba(0, 0, 0, 0.45);
    margin-top: 2px;
  }
}

.pp-shell {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: calc(100vh - 160px);
  width: 100%;
  max-width: 100%;
  overflow-x: hidden;
  box-sizing: border-box;
}

.pp-intro {
  margin-bottom: 0;
}

.pp-workspace {
  display: grid;
  grid-template-columns: minmax(240px, 280px) minmax(0, 1fr) minmax(280px, 340px);
  gap: 14px;
  flex: 1;
  min-height: 520px;
  align-items: stretch;
  width: 100%;
  max-width: 100%;
  overflow: hidden;
  box-sizing: border-box;

  > * {
    min-width: 0;
  }
}

.pp-panel {
  display: flex;
  flex-direction: column;
  background: #fff;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  overflow: hidden;
  min-height: 480px;
  max-height: calc(100vh - 260px);
  min-width: 0;
  width: 100%;
  box-sizing: border-box;

  &--steps {
    overflow: hidden;
  }

  &--config {
    overflow: hidden;
  }

  &__head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    flex-wrap: nowrap;
    padding: 12px 14px;
    font-weight: 600;
    border-bottom: 1px solid #f0f0f0;
    background: #fafafa;

    &--library {
      .pp-panel__title {
        flex-shrink: 0;
        white-space: nowrap;
      }

      .pp-panel__search {
        flex: 1 1 auto;
        min-width: 72px;
        max-width: 148px;
      }
    }
  }

  &__title {
    line-height: 1.4;
  }

  &__meta {
    font-size: 12px;
    font-weight: normal;
    color: rgba(0, 0, 0, 0.45);
  }
}

.pp-plugin-group {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
  margin: 4px 0 8px;
}

.pp-plugin-list {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.pp-plugin-card {
  position: relative;
  padding: 10px 12px 10px 12px;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;

  &:hover:not(.disabled) {
    border-color: #1677ff;
    background: #f6faff;
  }

  &.disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  &__top {
    display: flex;
    flex-wrap: nowrap;
    align-items: center;
    gap: 6px;
    padding-right: 24px;
    min-width: 0;
    overflow: hidden;

    :deep(.ant-tag) {
      flex-shrink: 0;
      white-space: nowrap;
      margin: 0;
    }
  }

  &__name {
    font-weight: 600;
    font-size: 13px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    min-width: 0;
  }

  &__desc {
    margin-top: 6px;
    font-size: 12px;
    color: rgba(0, 0, 0, 0.55);
    line-height: 1.45;
  }

  &__add {
    position: absolute;
    top: 10px;
    right: 10px;
    color: #1677ff;
  }
}

.pp-steps-body {
  flex: 1;
  min-height: 0;
  min-width: 0;
  width: 100%;
  overflow-x: hidden;
  overflow-y: auto;
  padding: 10px;
  box-sizing: border-box;
  cursor: default;
}

.pp-steps-tip {
  margin-bottom: 10px;
}

.pp-steps-list {
  display: flex;
  flex-direction: column;
  width: 100%;
  min-width: 0;
}

.pp-step-connector {
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 6px;
  margin: 0;
  color: rgba(0, 0, 0, 0.2);

  &__line {
    width: 1px;
    flex: 1;
    background: #d9d9d9;
  }

  &__arrow {
    display: none;
  }
}

.pp-step-card {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  width: 100%;
  min-width: 0;
  box-sizing: border-box;
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;
  background: #fff;

  &__badge {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    flex-shrink: 0;
    width: 32px;
  }

  &__body {
    flex: 1;
    min-width: 0;
  }

  &__title {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 6px;
    font-weight: 600;
    font-size: 14px;
    line-height: 1.4;
    word-break: break-word;
  }

  &__sub {
    margin-top: 4px;
    font-size: 12px;
    color: rgba(0, 0, 0, 0.55);
    line-height: 1.5;
    word-break: break-word;
  }

  &__actions {
    display: flex;
    align-items: center;
    gap: 2px;
    flex-shrink: 0;
  }

  &.active {
    border-color: #1677ff;
    background: #f6faff;
    box-shadow: 0 0 0 1px rgba(22, 119, 255, 0.15);
  }

  &.is-pinned {
    background: #fff;
    border-color: #d9d9d9;
  }

  &.off {
    opacity: 0.65;
  }
}

.pp-step-lock {
  color: rgba(0, 0, 0, 0.35);
  font-size: 12px;
}

.pp-step-index {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: #1677ff;
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.pp-config-body {
  flex: 1;
  min-width: 0;
  overflow-x: hidden;
  overflow-y: auto;
  padding: 14px;
  box-sizing: border-box;
}

.pp-config-head {
  margin-bottom: 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
  overflow: hidden;

  &__name {
    font-size: 15px;
    font-weight: 600;
    line-height: 1.4;
    word-break: break-word;
  }

  &__tags {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 8px;
  }

  &__desc {
    margin-top: 8px;
    font-size: 12px;
    color: rgba(0, 0, 0, 0.55);
    line-height: 1.5;
  }
}

.pp-config-empty {
  margin-top: 80px;
}

.pp-field {
  margin-bottom: 12px;

  label {
    display: block;
    font-size: 12px;
    color: rgba(0, 0, 0, 0.65);
    margin-bottom: 4px;
  }
}

.pp-params__title {
  font-weight: 600;
  margin-bottom: 10px;
  font-size: 13px;
}

.pp-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  width: 100%;

  &__hint {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    color: rgba(0, 0, 0, 0.45);
    max-width: 60%;
  }

  &__btns {
    display: flex;
    gap: 8px;
    flex-shrink: 0;
  }
}

@media (max-width: 1280px) {
  .pp-workspace {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto auto;
  }
}
</style>

<style lang="less">
.post-pipeline-drawer {
  .ant-drawer-content-wrapper {
    max-width: none !important;
  }

  .ant-drawer-body {
    overflow-x: hidden;
  }
}
</style>
