<template>
  <div class="llm-deploy-panel">
    <Alert type="info" show-icon class="mb-4">
      <template #message>
        选择 Qwen 模型版本与目标 GPU 节点，一键部署 vLLM OpenAI 兼容推理服务。部署成功后自动注册到「大模型管理」供业务调用。
      </template>
    </Alert>

    <Form :label-col="{ span: 5 }" :wrapper-col="{ span: 19 }" class="deploy-form">
      <FormItem label="Qwen 模型" required>
        <Select
          v-model:value="form.qwen_model_key"
          placeholder="选择模型版本"
          :options="modelOptions"
          show-search
          :filter-option="filterOption"
          @change="onModelChange"
        />
        <div v-if="selectedPreset" class="model-hint">
          部署约需 {{ requiredVramGb }} GB 可用显存（含 {{ tensorParallelSize }} 卡张量并行与安全余量），推荐
          {{ selectedPreset.recommended_gpu_count }} 卡
          <span v-if="selectedPreset.description"> — {{ selectedPreset.description }}</span>
        </div>
      </FormItem>

      <FormItem v-if="form.deploy_target === 'node'" label="显存预检">
        <Alert
          v-if="vramChecking"
          type="info"
          show-icon
          message="正在比对节点显存…"
        />
        <Alert
          v-else-if="vramCheck"
          :type="vramCheck.ok ? 'success' : 'error'"
          show-icon
          :message="vramCheckMessage"
        />
        <span v-else-if="form.target_node_id" class="field-tip">请选择模型与节点后自动预检</span>
        <span v-else class="field-tip">选择目标节点后将自动比对显存</span>
      </FormItem>

      <FormItem label="部署目标">
        <Select v-model:value="form.deploy_target" :options="deployTargetOptions" />
      </FormItem>

      <FormItem v-if="form.deploy_target === 'node'" label="目标节点" required>
        <Select
          v-model:value="form.target_node_id"
          placeholder="选择在线 GPU 节点"
          :options="nodeOptions"
          show-search
          :filter-option="filterOption"
          allow-clear
        />
      </FormItem>

      <FormItem label="张量并行">
        <InputNumber v-model:value="form.tensor_parallel_size" :min="1" :max="8" />
        <span class="field-tip">使用的 GPU 卡数（vLLM tensor-parallel-size）</span>
      </FormItem>

      <FormItem label="最大上下文">
        <InputNumber v-model:value="form.max_model_len" :min="2048" :max="131072" :step="1024" />
      </FormItem>

      <FormItem label="起始端口">
        <InputNumber v-model:value="form.start_port" :min="8100" :max="65535" />
        <span class="field-tip">占用时自动递增寻找可用端口</span>
      </FormItem>

      <FormItem :wrapper-col="{ offset: 5, span: 19 }">
        <Button type="primary" :loading="deploying" :disabled="!canDeploy" @click="handleDeploy">
          一键部署
        </Button>
      </FormItem>
    </Form>

    <DeployProgressPanel
      v-if="deployResult"
      class="mt-4"
      :loading="deploying"
      :result="deployResult"
    />
  </div>
</template>

<script lang="ts" setup>
import { computed, onMounted, reactive, ref, watch } from 'vue';
import { Alert, Form, FormItem, InputNumber, Select } from 'ant-design-vue';
import { Button } from '@/components/Button';
import { useMessage } from '@/hooks/web/useMessage';
import { getNodePage } from '@/api/device/node';
import {
  checkLlmDeployVram,
  deployLlmModel,
  getLlmDeployCatalog,
  type LLMVramCheckResult,
  type QwenModelPreset,
} from '@/api/device/llmDeploy';
import { parseGpuInfo } from '../../utils/constants';
import type { DeployResultState } from '../../utils/deployLog';
import DeployProgressPanel from '../DeployProgressPanel/index.vue';

defineOptions({ name: 'LlmDeployPanel' });

const props = defineProps<{
  nodeIds: number[];
}>();

const emit = defineEmits<{ (e: 'deployed'): void }>();

const { createMessage } = useMessage();

const presets = ref<QwenModelPreset[]>([]);
const nodeOptions = ref<{ label: string; value: number }[]>([]);
const deploying = ref(false);
const deployResult = ref<DeployResultState | null>(null);
const vramChecking = ref(false);
const vramCheck = ref<LLMVramCheckResult | null>(null);
const vramCheckMessage = ref('');

const form = reactive({
  qwen_model_key: '',
  deploy_target: 'node' as 'node' | 'auto',
  target_node_id: undefined as number | undefined,
  tensor_parallel_size: 1,
  max_model_len: 8192,
  start_port: 8100,
});

const deployTargetOptions = [
  { label: '指定节点', value: 'node' },
  { label: '自动调度 GPU 节点', value: 'auto' },
];

const modelOptions = computed(() =>
  presets.value.map((p) => ({
    label: `${p.label}（≥${p.min_vram_gb}GB）`,
    value: p.key,
  })),
);

const selectedPreset = computed(() =>
  presets.value.find((p) => p.key === form.qwen_model_key),
);

const tensorParallelSize = computed(() => form.tensor_parallel_size || 1);

const requiredVramGb = computed(() => {
  const preset = selectedPreset.value;
  if (!preset) return '-';
  const rec = preset.recommended_gpu_count || 1;
  const tp = tensorParallelSize.value;
  let base = preset.min_vram_gb;
  if (tp < rec) base *= rec / tp;
  return Math.ceil((base + 2) * 10) / 10;
});

const canDeploy = computed(() => {
  if (!form.qwen_model_key) return false;
  if (form.deploy_target === 'node') {
    if (!form.target_node_id) return false;
    if (vramCheck.value && !vramCheck.value.ok) return false;
    return true;
  }
  return true;
});

function filterOption(input: string, option: { label?: string; value?: string | number }) {
  return String(option?.label || '').toLowerCase().includes(input.toLowerCase());
}

function onModelChange(key: string) {
  const preset = presets.value.find((p) => p.key === key);
  if (preset) {
    form.tensor_parallel_size = preset.recommended_gpu_count;
    form.max_model_len = preset.max_model_len_default;
  }
}

async function loadCatalog() {
  const res = await getLlmDeployCatalog();
  presets.value = res?.data || [];
  if (!form.qwen_model_key && presets.value.length) {
    form.qwen_model_key = presets.value.find((p) => p.key === 'qwen3-4b-instruct-2507')?.key || presets.value[0].key;
    onModelChange(form.qwen_model_key);
  }
}

async function loadNodes() {
  const res = await getNodePage({ pageNo: 1, pageSize: 200, status: 'online' });
  const list = res?.list || [];
  nodeOptions.value = list
    .filter((n: { functions?: string[]; nodeRole?: string }) => {
      const fns = n.functions?.length ? n.functions : String(n.nodeRole || '').split(',');
      return fns.includes('llm');
    })
    .map((n: { id: number; name?: string; host?: string; gpuInfo?: string }) => {
      const gpus = parseGpuInfo(n.gpuInfo);
      const freeGb = gpus.reduce(
        (sum, g) => sum + Math.max(0, (g.mem_total_mb || 0) - (g.mem_used_mb || 0)),
        0,
      ) / 1024;
      const gpuHint = gpus.length ? `，剩余 ${freeGb.toFixed(1)} GB` : '';
      return {
        label: `${n.name || n.host} (${n.host}${gpuHint})`,
        value: n.id,
      };
    });
}

async function runVramCheck() {
  vramCheck.value = null;
  vramCheckMessage.value = '';
  if (form.deploy_target !== 'node' || !form.target_node_id || !form.qwen_model_key) {
    return;
  }
  vramChecking.value = true;
  try {
    const res = await checkLlmDeployVram({
      qwen_model_key: form.qwen_model_key,
      target_node_id: form.target_node_id,
      tensor_parallel_size: form.tensor_parallel_size,
    });
    vramCheck.value = res?.data || null;
    vramCheckMessage.value = res?.msg || '';
  } catch (e: unknown) {
    vramCheck.value = { ok: false };
    vramCheckMessage.value = e instanceof Error ? e.message : '显存预检失败';
  } finally {
    vramChecking.value = false;
  }
}

watch(
  () => [form.qwen_model_key, form.target_node_id, form.tensor_parallel_size, form.deploy_target] as const,
  () => {
    void runVramCheck();
  },
);

watch(
  () => props.nodeIds,
  (ids) => {
    if (ids?.length === 1) {
      form.deploy_target = 'node';
      form.target_node_id = ids[0];
    }
  },
  { immediate: true },
);

async function handleDeploy() {
  if (!canDeploy.value) {
    createMessage.warning(vramCheck.value && !vramCheck.value.ok ? vramCheckMessage.value : '请完善部署参数');
    return;
  }
  deploying.value = true;
  deployResult.value = {
    success: false,
    message: '正在下发部署…',
    steps: [{ title: '调度 GPU 节点', status: 'process' }],
  };
  try {
    const res = await deployLlmModel({
      qwen_model_key: form.qwen_model_key,
      target_node_id: form.deploy_target === 'node' ? form.target_node_id : undefined,
      auto_schedule: form.deploy_target === 'auto',
      start_port: form.start_port,
      tensor_parallel_size: form.tensor_parallel_size,
      max_model_len: form.max_model_len,
    });
    deployResult.value = {
      success: true,
      message: res?.msg || '部署已下发，vLLM 启动中',
      steps: [
        { title: '调度 GPU 节点', status: 'finish' },
        { title: '启动 vLLM 服务', status: 'process', description: `实例 ID: ${res?.data?.id}` },
      ],
    };
    createMessage.success(res?.msg || '部署已下发');
    emit('deployed');
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '部署失败';
    deployResult.value = {
      success: false,
      message: msg,
      steps: [{ title: '部署失败', status: 'error', description: msg }],
    };
  } finally {
    deploying.value = false;
  }
}

onMounted(() => {
  loadCatalog();
  loadNodes();
});
</script>

<style scoped lang="less">
.llm-deploy-panel {
  max-width: 720px;
}

.model-hint,
.field-tip {
  margin-top: 6px;
  font-size: 12px;
  color: #666;
}

.deploy-form {
  margin-top: 8px;
}
</style>
