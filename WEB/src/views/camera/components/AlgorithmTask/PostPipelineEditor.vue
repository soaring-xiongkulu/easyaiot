<template>
  <div class="post-pipeline-editor">
    <a-alert
      class="mb-3"
      type="info"
      show-icon
      message="后处理规则链在 POST 定制研判服务中执行，与「业务脚本」相互独立。未自定义时使用默认：区域闸门 → 标准放行。"
    />

    <div class="toolbar">
      <a-space wrap>
        <a-tag v-if="isDefaultMode" color="processing">默认规则链</a-tag>
        <a-tag v-else color="blue">自定义规则链</a-tag>
        <Button v-if="isDefaultMode && !disabled" size="small" @click="enableCustom">启用自定义</Button>
        <Button v-if="!isDefaultMode && !disabled" size="small" @click="resetDefault">恢复默认</Button>
        <Button size="small" type="primary" ghost @click="openDebug('pipeline')">规则调试</Button>
      </a-space>
    </div>

    <!-- 可视化流程预览 -->
    <div class="flow-banner">
      <template v-for="(step, idx) in previewSteps" :key="`${step.plugin}-${idx}`">
        <div
          class="flow-node"
          :class="{ active: selectedIndex === idx, disabled: step.enabled === false }"
          @click="selectStep(idx)"
        >
          <div class="flow-node__kind">
            <a-tag v-for="k in pluginKinds(step.plugin)" :key="k" :color="kindColor(k)" size="small">
              {{ kindLabel(k) }}
            </a-tag>
          </div>
          <div class="flow-node__name">{{ pluginLabel(allPlugins, step.plugin) }}</div>
          <div class="flow-node__id">{{ step.plugin }}</div>
        </div>
        <div v-if="idx < previewSteps.length - 1" class="flow-arrow" />
      </template>
    </div>

    <div class="editor-grid">
      <!-- 插件面板 -->
      <div class="panel palette-panel">
        <div class="panel-title">插件库</div>
        <a-input v-model:value="paletteFilter" allow-clear placeholder="搜索插件" size="small" class="mb-2" />
        <div class="palette-groups">
          <div class="palette-group">
            <div class="group-title">内置插件</div>
            <div
              v-for="item in filteredBuiltins"
              :key="item.id"
              class="palette-item"
              :class="{ disabled: disabled || isDefaultMode }"
              @click="addPlugin(item)"
            >
              <div class="palette-item__name">{{ item.name }}</div>
              <div class="palette-item__desc">{{ item.description }}</div>
            </div>
          </div>
          <div v-if="externalPlugins.length" class="palette-group">
            <div class="group-title">外置插件</div>
            <div
              v-for="item in filteredExternals"
              :key="item.id"
              class="palette-item"
              :class="{ disabled: disabled || isDefaultMode }"
              @click="addPlugin(item)"
            >
              <div class="palette-item__name">{{ item.name }}</div>
              <div class="palette-item__desc">{{ item.description || item.id }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 步骤列表 -->
      <div class="panel steps-panel">
        <div class="panel-title">规则链步骤</div>
        <div v-if="isDefaultMode" class="default-hint">
          当前使用平台默认规则链。点击「启用自定义」后可拖拽排序与增删步骤。
        </div>
        <draggable
          v-else
          v-model="localSteps"
          item-key="plugin"
          handle=".drag-handle"
          :disabled="disabled"
          class="step-list"
          @end="emitChange"
        >
          <template #item="{ element, index }">
            <div
              class="step-card"
              :class="{ active: selectedIndex === index, off: element.enabled === false }"
              @click="selectStep(index)"
            >
              <span class="drag-handle" title="拖拽排序">⋮⋮</span>
              <div class="step-card__main">
                <div class="step-card__title">
                  <span>{{ index + 1 }}. {{ pluginLabel(allPlugins, element.plugin) }}</span>
                  <a-switch
                    v-model:checked="element.enabled"
                    :disabled="disabled"
                    size="small"
                    checked-children="开"
                    un-checked-children="关"
                    @change="emitChange"
                    @click.stop
                  />
                </div>
                <div class="step-card__meta">{{ element.plugin }}</div>
              </div>
              <a-space @click.stop>
                <Button size="small" type="link" @click="openDebug('plugin', element.plugin)">调试</Button>
                <Button
                  size="small"
                  type="link"
                  danger
                  :disabled="disabled || element.plugin === 'default_pass'"
                  @click="removeStep(index)"
                >
                  删除
                </Button>
              </a-space>
            </div>
          </template>
        </draggable>
      </div>

      <!-- 参数面板 -->
      <div class="panel config-panel">
        <div class="panel-title">步骤配置</div>
        <template v-if="selectedStep">
          <a-form layout="vertical" size="small">
            <a-form-item label="插件">
              <a-input :value="selectedStep.plugin" disabled />
            </a-form-item>
            <a-form-item label="版本">
              <a-input
                v-model:value="selectedStep.version"
                :disabled="disabled || isDefaultMode"
                placeholder="可选"
                @change="emitChange"
              />
            </a-form-item>
            <a-form-item label="失败策略">
              <a-select
                v-model:value="selectedStep.fail_strategy"
                :disabled="disabled || isDefaultMode"
                @change="emitChange"
              >
                <a-select-option value="fail_open">fail_open（跳过继续）</a-select-option>
                <a-select-option value="fail_closed">fail_closed（丢弃）</a-select-option>
              </a-select>
            </a-form-item>
            <a-form-item v-if="!isBuiltinPlugin(selectedStep.plugin)" label="Endpoint">
              <a-input
                v-model:value="selectedStep.endpoint"
                :disabled="disabled || isDefaultMode"
                placeholder="http://host:port"
                @change="emitChange"
              />
            </a-form-item>

            <a-divider orientation="left">插件参数</a-divider>
            <template v-for="field in paramFields" :key="field.key">
              <a-form-item :label="field.title">
                <a-select
                  v-if="field.enum"
                  v-model:value="selectedStep.params[field.key]"
                  :disabled="disabled || isDefaultMode"
                  allow-clear
                  @change="emitChange"
                >
                  <a-select-option v-for="opt in field.enum" :key="opt" :value="opt">{{ opt }}</a-select-option>
                </a-select>
                <a-input-number
                  v-else-if="field.type === 'number' || field.type === 'integer'"
                  v-model:value="selectedStep.params[field.key]"
                  :disabled="disabled || isDefaultMode"
                  style="width: 100%"
                  @change="emitChange"
                />
                <a-select
                  v-else-if="field.type === 'array'"
                  v-model:value="selectedStep.params[field.key]"
                  mode="tags"
                  :disabled="disabled || isDefaultMode"
                  placeholder="输入后回车"
                  @change="emitChange"
                />
                <a-input
                  v-else
                  v-model:value="selectedStep.params[field.key]"
                  :disabled="disabled || isDefaultMode"
                  @change="emitChange"
                />
              </a-form-item>
            </template>
            <a-empty v-if="!paramFields.length" description="此插件无可配置参数" />
          </a-form>
        </template>
        <a-empty v-else description="请选择左侧步骤" />
      </div>
    </div>

    <PostPipelineDebugDrawer
      @register="registerDebugDrawer"
      :task-id="taskId"
      :task-context="taskContext"
      :pipeline-steps="previewSteps"
      :all-plugins="allPlugins"
    />
  </div>
</template>

<script lang="ts" setup>
import { computed, onMounted, ref, watch } from 'vue';
import draggable from 'vuedraggable';
import { Button } from '@/components/Button';
import { useDrawer } from '@/components/Drawer';
import { useMessage } from '@/hooks/web/useMessage';
import {
  getPostPluginCatalog,
  type PostPipelineStep,
  type PostPluginMeta,
} from '@/api/device/post_pipeline';
import PostPipelineDebugDrawer from './PostPipelineDebugDrawer.vue';
import {
  clonePipeline,
  createStepFromPlugin,
  effectiveSteps,
  KIND_COLORS,
  KIND_LABELS,
  pluginLabel,
} from './postPipelineCatalog';

defineOptions({ name: 'PostPipelineEditor' });

const props = defineProps<{
  modelValue: PostPipelineStep[] | null;
  disabled?: boolean;
  taskId?: number | null;
  postProcessEnabled?: boolean;
  taskContext?: {
    id?: number | null;
    task_name?: string;
    task_type?: string;
    device_ids?: string[];
  };
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', v: PostPipelineStep[] | null): void;
}>();

const { createMessage } = useMessage();
const [registerDebugDrawer, { openDrawer: openDebugDrawer }] = useDrawer();

const isDefaultMode = computed(() => props.modelValue === null);
const localSteps = ref<PostPipelineStep[]>(clonePipeline(props.modelValue));
const selectedIndex = ref(0);
const paletteFilter = ref('');
const builtinPlugins = ref<PostPluginMeta[]>([]);
const externalPlugins = ref<PostPluginMeta[]>([]);

const allPlugins = computed(() => [...builtinPlugins.value, ...externalPlugins.value]);
const previewSteps = computed(() => effectiveSteps(localSteps.value));
const selectedStep = computed(() => localSteps.value[selectedIndex.value] || null);

const filteredBuiltins = computed(() => filterPlugins(builtinPlugins.value));
const filteredExternals = computed(() => filterPlugins(externalPlugins.value));

interface ParamField {
  key: string;
  title: string;
  type?: string;
  enum?: string[];
}

const paramFields = computed<ParamField[]>(() => {
  const step = selectedStep.value;
  if (!step) return [];
  const meta = allPlugins.value.find((p) => p.id === step.plugin);
  const schema = (meta?.params_schema || {}) as Record<string, any>;
  const propsMap = schema.properties || {};
  if (!step.params) step.params = {};
  return Object.entries(propsMap).map(([key, val]: [string, any]) => ({
    key,
    title: val.title || key,
    type: val.type,
    enum: val.enum,
  }));
});

watch(
  () => props.modelValue,
  (val) => {
    localSteps.value = clonePipeline(val);
    if (selectedIndex.value >= localSteps.value.length) {
      selectedIndex.value = Math.max(0, localSteps.value.length - 1);
    }
  },
);

onMounted(loadCatalog);

async function loadCatalog() {
  try {
    const data = await getPostPluginCatalog();
    builtinPlugins.value = data?.builtins || [];
    externalPlugins.value = data?.externals || [];
  } catch {
    createMessage.warning('插件目录加载失败，仍可编辑已有步骤');
  }
}

function filterPlugins(list: PostPluginMeta[]) {
  const q = paletteFilter.value.trim().toLowerCase();
  if (!q) return list;
  return list.filter(
    (p) =>
      p.id.toLowerCase().includes(q) ||
      (p.name || '').toLowerCase().includes(q) ||
      (p.description || '').toLowerCase().includes(q),
  );
}

function kindLabel(k: string) {
  return KIND_LABELS[k] || k;
}

function kindColor(k: string) {
  return KIND_COLORS[k] || 'default';
}

function pluginKinds(pluginId: string) {
  return allPlugins.value.find((p) => p.id === pluginId)?.kinds || ['filter'];
}

function isBuiltinPlugin(pluginId: string) {
  const hit = allPlugins.value.find((p) => p.id === pluginId);
  return hit?.builtin !== false;
}

function selectStep(index: number) {
  selectedIndex.value = index;
}

function emitChange() {
  if (isDefaultMode.value) return;
  emit('update:modelValue', localSteps.value.map(normalizeStep));
}

function normalizeStep(step: PostPipelineStep): PostPipelineStep {
  return {
    plugin: step.plugin,
    version: step.version || undefined,
    enabled: step.enabled !== false,
    params: step.params || {},
    fail_strategy: step.fail_strategy || 'fail_open',
    endpoint: step.endpoint || undefined,
  };
}

function enableCustom() {
  localSteps.value = clonePipeline(null);
  selectedIndex.value = 0;
  emit('update:modelValue', localSteps.value.map(normalizeStep));
}

function resetDefault() {
  localSteps.value = clonePipeline(null);
  selectedIndex.value = 0;
  emit('update:modelValue', null);
}

function addPlugin(plugin: PostPluginMeta) {
  if (props.disabled || isDefaultMode.value) return;
  if (plugin.id === 'default_pass') {
    createMessage.info('标准放行会自动追加到链尾');
    return;
  }
  const exists = localSteps.value.some((s) => s.plugin === plugin.id);
  if (exists) {
    createMessage.warning('该插件已在规则链中');
    return;
  }
  const passIdx = localSteps.value.findIndex((s) => s.plugin === 'default_pass');
  const step = createStepFromPlugin(plugin);
  if (passIdx >= 0) {
    localSteps.value.splice(passIdx, 0, step);
    selectedIndex.value = passIdx;
  } else {
    localSteps.value.push(step);
    selectedIndex.value = localSteps.value.length - 1;
  }
  emitChange();
}

function removeStep(index: number) {
  if (props.disabled || isDefaultMode.value) return;
  const step = localSteps.value[index];
  if (step?.plugin === 'default_pass') return;
  localSteps.value.splice(index, 1);
  if (selectedIndex.value >= localSteps.value.length) {
    selectedIndex.value = Math.max(0, localSteps.value.length - 1);
  }
  emitChange();
}

function openDebug(mode: 'pipeline' | 'plugin', plugin?: string) {
  openDebugDrawer(true, { mode, plugin });
}
</script>

<style lang="less" scoped>
.post-pipeline-editor {
  padding: 4px 0 12px;
}

.toolbar {
  margin-bottom: 12px;
}

.flow-banner {
  display: flex;
  align-items: stretch;
  overflow-x: auto;
  padding: 12px;
  margin-bottom: 16px;
  border: 1px solid #e5e6eb;
  border-radius: 8px;
  background: linear-gradient(180deg, #fafbfc 0%, #f7f8fa 100%);
  gap: 0;
}

.flow-node {
  min-width: 132px;
  max-width: 160px;
  padding: 10px 12px;
  border: 1px solid #e5e6eb;
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
  transition: all 0.15s ease;

  &.active {
    border-color: #165dff;
    box-shadow: 0 0 0 2px rgba(22, 93, 255, 0.12);
  }

  &.disabled {
    opacity: 0.55;
  }
}

.flow-node__kind {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 6px;
}

.flow-node__name {
  font-weight: 600;
  font-size: 13px;
  line-height: 1.3;
}

.flow-node__id {
  margin-top: 4px;
  color: #86909c;
  font-size: 11px;
  word-break: break-all;
}

.flow-arrow {
  align-self: center;
  width: 28px;
  height: 2px;
  margin: 0 4px;
  background: #c9cdd4;
  position: relative;
  flex-shrink: 0;

  &::after {
    content: '';
    position: absolute;
    right: -1px;
    top: -4px;
    border: 5px solid transparent;
    border-left-color: #c9cdd4;
  }
}

.editor-grid {
  display: grid;
  grid-template-columns: 240px 1fr 300px;
  gap: 12px;
  min-height: 420px;
}

.panel {
  border: 1px solid #e5e6eb;
  border-radius: 8px;
  background: #fff;
  padding: 12px;
  min-height: 360px;
}

.panel-title {
  font-weight: 600;
  margin-bottom: 10px;
}

.palette-groups {
  max-height: 520px;
  overflow: auto;
}

.group-title {
  font-size: 12px;
  color: #86909c;
  margin: 8px 0 6px;
}

.palette-item {
  padding: 8px 10px;
  border: 1px solid #f2f3f5;
  border-radius: 6px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: background 0.15s;

  &:hover:not(.disabled) {
    background: #f7f8fa;
    border-color: #e5e6eb;
  }

  &.disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.palette-item__name {
  font-weight: 600;
  font-size: 13px;
}

.palette-item__desc {
  margin-top: 4px;
  color: #86909c;
  font-size: 11px;
  line-height: 1.4;
}

.default-hint {
  color: #86909c;
  font-size: 13px;
  line-height: 1.6;
  padding: 12px;
  background: #f7f8fa;
  border-radius: 6px;
}

.step-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 520px;
  overflow: auto;
}

.step-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border: 1px solid #e5e6eb;
  border-radius: 6px;
  cursor: pointer;

  &.active {
    border-color: #165dff;
    background: #f0f5ff;
  }

  &.off {
    opacity: 0.6;
  }
}

.drag-handle {
  cursor: grab;
  color: #c9cdd4;
  user-select: none;
  font-weight: 700;
}

.step-card__main {
  flex: 1;
  min-width: 0;
}

.step-card__title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  font-weight: 600;
}

.step-card__meta {
  margin-top: 2px;
  color: #86909c;
  font-size: 11px;
}

@media (max-width: 1200px) {
  .editor-grid {
    grid-template-columns: 1fr;
  }
}
</style>
