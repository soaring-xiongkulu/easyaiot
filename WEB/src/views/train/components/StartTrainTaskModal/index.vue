<template>
  <BasicDrawer
    v-bind="$attrs"
    @register="registerDrawer"
    :title="drawerTitle"
    width="1400"
    placement="right"
    :showFooter="true"
    :showOkBtn="false"
    :showCancelBtn="false"
    destroy-on-close
  >
    <template #footer>
      <div class="footer-buttons">
        <Button @click="handleCancel">取消</Button>
        <Button type="primary" :loading="uploading" @click="startTrain">
          {{ submitButtonText }}
        </Button>
      </div>
    </template>

    <Spin :spinning="gpuLoading || customModelsLoading">
      <div class="train-drawer-content">
        <Alert
          v-if="isResumeMode"
          type="info"
          show-icon
          class="resume-alert"
          :message="resumeHint"
        />

        <BasicForm @register="registerForm" />

        <Divider orientation="left">模型配置</Divider>
        <Form
          :label-col="formLabelCol"
          :wrapper-col="formWrapperCol"
          class="resource-form"
        >
          <FormItem label="预训练权重" required>
            <Select
              v-model:value="selectedModelPath"
              placeholder="请选择预训练权重"
              :loading="customModelsLoading"
              :disabled="modelPathDisabled"
              show-search
              option-filter-prop="label"
              style="width: 100%"
            >
              <SelectOptGroup label="系统模型">
                <SelectOption
                  v-for="item in presetModelOptions"
                  :key="item.value"
                  :value="item.value"
                  :label="item.label"
                >
                  {{ item.label }}
                </SelectOption>
              </SelectOptGroup>
              <SelectOptGroup v-if="customWeightOptions.length" label="用户模型">
                <SelectOption
                  v-for="item in customWeightOptions"
                  :key="item.value"
                  :value="item.value"
                  :label="item.label"
                >
                  {{ item.label }}
                </SelectOption>
              </SelectOptGroup>
            </Select>
            <div class="form-hint">系统模型为 Ultralytics 官方权重；用户模型来自模型管理上传的 .pt 文件</div>
          </FormItem>
          <FormItem
            v-if="selectedSchedulePolicy !== 'node' && gpuStatus.devices?.length"
            label="GPU 设备"
          >
            <div class="gpu-device-panel">
              <div
                v-for="dev in gpuStatus.devices"
                :key="dev.index"
                class="gpu-device-item"
              >
                <Tag color="blue">GPU {{ dev.index }}</Tag>
                <span>{{ dev.name }}（{{ dev.total_memory_gb }} GB）</span>
              </div>
            </div>
          </FormItem>
        </Form>

        <Divider orientation="left">数据集配置</Divider>
        <Form
          :label-col="formLabelCol"
          :wrapper-col="formWrapperCol"
          class="resource-form"
        >
          <FormItem label="数据来源">
            <Radio.Group
              v-model:value="datasetSourceTab"
              :disabled="isResumeMode"
              @change="onDatasetSourceChange"
            >
              <Radio value="local">本地上传</Radio>
              <Radio value="cloud">云端数据集</Radio>
            </Radio.Group>
          </FormItem>
          <FormItem v-if="datasetSourceTab === 'local'" label="上传文件">
            <Upload
              accept=".zip"
              :file-list="localFileList"
              :show-upload-list="true"
              :max-count="1"
              :disabled="isResumeMode"
              :before-upload="beforeLocalDatasetUpload"
              @remove="handleLocalFileRemove"
            >
              <Button type="primary" :disabled="isResumeMode">
                {{ localFileList?.length ? '重新选择压缩包' : '上传数据集压缩包' }}
              </Button>
            </Upload>
            <div class="form-hint">
              上传 YOLO 或 COCO 格式数据集 ZIP 压缩包（含 YAML 配置），单文件最大 5GB
            </div>
          </FormItem>
          <FormItem v-else label="选择数据集">
            <Select
              v-model:value="selectedDatasetId"
              placeholder="请选择已同步到 Minio 的云端数据集"
              :loading="cloudDatasetLoading"
              :options="cloudDatasetOptions"
              :disabled="isResumeMode"
              allow-clear
              show-search
              style="width: 100%"
              :filter-option="filterCloudDataset"
            />
            <div class="form-hint">请先在数据集管理中完成：标注 → 划分用途 → 同步到 Minio</div>
            <p v-if="selectedCloudDataset && !selectedCloudDataset.zipUrl" class="form-hint-warn">
              该数据集尚未同步到 Minio，请先完成划分用途并同步
            </p>
            <Empty
              v-if="!cloudDatasetLoading && !cloudDatasetOptions.length"
              description="暂无云端数据集"
            />
          </FormItem>
        </Form>
      </div>
    </Spin>
  </BasicDrawer>
</template>

<script lang="ts" setup>
import { computed, ref, watch } from 'vue';
import type { UploadProps } from 'ant-design-vue';
import {
  Alert,
  Divider,
  Empty,
  Form,
  FormItem,
  Radio,
  Select,
  SelectOption,
  SelectOptGroup,
  Spin,
  Tag,
  Upload,
} from 'ant-design-vue';
import { BasicDrawer, useDrawerInner } from '@/components/Drawer';
import { BasicForm, useForm } from '@/components/Form';
import { getDatasetPage } from '@/api/device/dataset';
import { getModelPage } from '@/api/device/model';
import { getNodePage, type ComputeNodeVO } from '@/api/device/node';
import { getTrainGpuStatus, uploadTrainDataset } from '@/api/device/train';
import { useMessage } from '@/hooks/web/useMessage';
import { Button } from '@/components/Button';
import {
  getCompletedEpochs,
  isCloudDatasetPath,
  parseTrainHyperparameters,
  resolveLocalDatasetDisplayName,
  resolveTaskBaseNameFromRecord,
} from '../TrainTaskList/trainTaskUtils';
import {
  defaultAutoBatchSize,
  recommendTrainBatchSize,
  type TrainTaskLaunchMode,
} from '../../utils/trainBatchSize';
import { formatModelVersionDisplay } from '../../utils/modelVersionUtils';

interface GpuDeviceInfo {
  index: number;
  name: string;
  total_memory_gb: number;
  free_memory_gb?: number;
  used_memory_gb?: number;
}

interface GpuStatusData {
  cuda_available: boolean;
  visible_gpu_ids: number[];
  multi_gpu: boolean;
  devices: GpuDeviceInfo[];
}

interface DatasetItem {
  id: string | number;
  name: string;
  version: string;
  zipUrl?: string;
  isAllocated?: number;
  isSyncMinio?: number;
  totalImages?: number;
  annotatedImages?: number;
}

type DatasetSourceTab = 'local' | 'cloud';

interface CustomWeightOption {
  value: string;
  label: string;
}

const presetModels = ['yolov8n.pt', 'yolo11n.pt', 'yolo26n.pt'];

const presetModelOptions: CustomWeightOption[] = [
  { label: 'Yolov8 (yolov8n.pt)', value: 'yolov8n.pt' },
  { label: 'Yolo11 (yolo11n.pt)', value: 'yolo11n.pt' },
  { label: 'Yolo26 (yolo26n.pt)', value: 'yolo26n.pt' },
];

const schedulePolicyOptions = [
  { label: '自动调度', value: 'auto' },
  { label: '本机训练', value: 'local' },
  { label: '指定节点', value: 'node' },
];

const nodeOptions = ref<Array<{ label: string; value: number }>>([]);
const nodeRecords = ref<ComputeNodeVO[]>([]);
const selectedSchedulePolicy = ref('auto');
const selectedTargetNodeId = ref<number>();

const { createMessage } = useMessage();

const formLabelCol = { style: { width: '100px' } };
const formWrapperCol = { span: 21 };

const selectedModelPath = ref(presetModels[0]);
const modelPathDisabled = ref(false);

const defaultGpuStatus = (): GpuStatusData => ({
  cuda_available: false,
  visible_gpu_ids: [],
  multi_gpu: false,
  devices: [],
});

const gpuLoading = ref(false);
const gpuStatus = ref<GpuStatusData>(defaultGpuStatus());
const localGpuOptions = computed(() =>
  gpuStatus.value.visible_gpu_ids.map((gpuId) => {
    const device = gpuStatus.value.devices.find((item) => item.index === gpuId);
    const detail = device
      ? `${device.name}${device.total_memory_gb ? ` (${device.total_memory_gb} GB)` : ''}`
      : '可用 GPU';
    return {
      label: `GPU ${gpuId} - ${detail}`,
      value: gpuId,
    };
  }),
);

function parseNodeGpuDevices(node?: ComputeNodeVO): GpuDeviceInfo[] {
  if (!node?.gpuInfo) return [];
  try {
    const parsed = JSON.parse(node.gpuInfo);
    if (!Array.isArray(parsed)) return [];
    return parsed
      .map((item, index) => {
        const totalMemoryGb = Number(
          item?.total_memory_gb
          ?? item?.memory_total_gb
          ?? item?.mem_total_gb
          ?? (Number(item?.memory_total_mb ?? item?.mem_total_mb ?? 0) / 1024),
        ) || 0;
        const usedMemoryGb = Number(
          item?.used_memory_gb
          ?? item?.memory_used_gb
          ?? item?.mem_used_gb
          ?? (Number(item?.memory_used_mb ?? item?.mem_used_mb ?? 0) / 1024),
        ) || 0;
        return {
          index: Number(item?.id ?? item?.index ?? index),
          name: String(item?.name || item?.gpu_name || 'GPU'),
          total_memory_gb: totalMemoryGb,
          used_memory_gb: usedMemoryGb,
          free_memory_gb: totalMemoryGb > 0
            ? Math.max(0, totalMemoryGb - usedMemoryGb)
            : undefined,
        };
      })
      .filter((item) => Number.isInteger(item.index) && item.index >= 0)
      .filter((item, index, items) => items.findIndex((candidate) => candidate.index === item.index) === index)
      .sort((left, right) => left.index - right.index);
  } catch {
    return [];
  }
}

function nodeGpuCount(node?: ComputeNodeVO): number {
  const configuredCount = Number(node?.maxGpuCount);
  if (Number.isFinite(configuredCount) && configuredCount >= 0) {
    return Math.floor(configuredCount);
  }
  return parseNodeGpuDevices(node).length;
}

const selectedTargetNode = computed(() =>
  nodeRecords.value.find((node) => Number(node.id) === Number(selectedTargetNodeId.value)),
);

const gpuOptions = computed(() => {
  if (selectedSchedulePolicy.value === 'node') {
    const node = selectedTargetNode.value;
    const devices = parseNodeGpuDevices(node);
    const gpuCount = nodeGpuCount(node);
    const gpuIds = devices.slice(0, gpuCount).map((item) => item.index);
    for (let gpuId = 0; gpuIds.length < gpuCount; gpuId += 1) {
      if (!gpuIds.includes(gpuId)) gpuIds.push(gpuId);
    }
    return gpuIds.map((gpuId) => {
      const device = devices.find((item) => item.index === gpuId);
      const detail = device
        ? `${device.name}${device.total_memory_gb ? ` (${device.total_memory_gb.toFixed(2)} GB)` : ''}`
        : '目标节点 GPU';
      return { label: `GPU ${gpuId} - ${detail}`, value: gpuId };
    });
  }
  if (selectedSchedulePolicy.value === 'auto') {
    const maxGpuCount = Math.max(
      gpuStatus.value.visible_gpu_ids.length,
      ...nodeRecords.value.map((node) => nodeGpuCount(node)),
      0,
    );
    return Array.from({ length: maxGpuCount }, (_, index) => ({
      label: `GPU ${index}`,
      value: index,
    }));
  }
  return localGpuOptions.value;
});

const availableGpuIds = computed(() => gpuOptions.value.map((option) => option.value));
const uploading = ref(false);
const customModelsLoading = ref(false);
const customWeightOptions = ref<CustomWeightOption[]>([]);

function parseModelPageResponse(response: unknown): Array<Record<string, any>> {
  if (Array.isArray(response)) {
    return response;
  }
  if (response && typeof response === 'object') {
    const payload = response as Record<string, unknown>;
    // 与 ModelCardList 一致：分页接口返回 { data, total }
    if (Array.isArray(payload.data)) {
      return payload.data as Array<Record<string, any>>;
    }
    if (Array.isArray(payload.list)) {
      return payload.list as Array<Record<string, any>>;
    }
    if (Array.isArray(payload.items)) {
      return payload.items as Array<Record<string, any>>;
    }
  }
  return [];
}

function hasManualGpuSelection(raw: unknown): boolean {
  try {
    const hyperparameters = typeof raw === 'string' ? JSON.parse(raw) : raw;
    return !!hyperparameters
      && typeof hyperparameters === 'object'
      && (hyperparameters as Record<string, unknown>).gpu_selection_manual === true;
  } catch {
    return false;
  }
}

function resolveTrainModelPath(model: Record<string, any>): string {
  return String(model.model_path || model.filePath || model.modelPath || '').trim();
}

/** 与 ModelCardList.getFormatText 一致：有 model_path 且非 ONNX 即为 PyTorch 权重 */
function isTrainablePtModel(model: Record<string, any>): boolean {
  const path = resolveTrainModelPath(model);
  if (!path) {
    return false;
  }
  const lower = path.toLowerCase();
  if (lower.endsWith('.onnx') || /\.onnx(\?|#|$)/i.test(path)) {
    return false;
  }
  return true;
}

const gpuHelpMessage = computed(() => {
  if (gpuLoading.value) return '正在探测 GPU...';
  if (selectedSchedulePolicy.value === 'node') {
    if (!selectedTargetNode.value) return '请先选择目标节点';
    if (!gpuOptions.value.length) return '目标节点未上报可用 GPU';
    return `目标节点可用 ${gpuOptions.value.length} 张 GPU，可指定单卡或多卡`;
  }
  if (selectedSchedulePolicy.value === 'auto') {
    return gpuOptions.value.length
      ? '自动调度仅使用所选数量，具体 GPU 编号由目标节点分配'
      : '当前没有上报可用 GPU 的计算节点';
  }
  if (gpuStatus.value.multi_gpu) {
    return `已探测 ${gpuStatus.value.visible_gpu_ids.length} 张 GPU，可选择单卡或多卡；多选启用 DDP`;
  }
  if (gpuStatus.value.visible_gpu_ids.length === 1) {
    const dev = gpuStatus.value.devices?.[0];
    return dev ? `单卡: ${dev.name} (${dev.total_memory_gb} GB)` : '单卡模式';
  }
  if (gpuStatus.value.visible_gpu_ids.length === 0) {
    return '未检测到可用 GPU，将回退 CPU';
  }
  return '';
});

const loadCustomModels = async () => {
  customModelsLoading.value = true;
  try {
    const res = await getModelPage({ pageNo: 1, pageSize: 1000 });
    const allModels = parseModelPageResponse(res);
    customWeightOptions.value = allModels
      .filter(isTrainablePtModel)
      .map((model) => ({
        value: resolveTrainModelPath(model),
        label: `${model.name || '未命名'} (${formatModelVersionDisplay(model.version) || '—'})`,
      }))
      .filter((item) => item.value && !presetModels.includes(item.value));
  } catch (e) {
    customWeightOptions.value = [];
    console.error('加载用户模型失败', e);
  } finally {
    customModelsLoading.value = false;
  }
};

const loadNodes = async () => {
  try {
    const res = await getNodePage({ pageNo: 1, pageSize: 200, status: 'online' });
    const page = (res as { data?: { list?: unknown[] }; list?: unknown[] })?.data || res;
    const list = (((page as { list?: unknown[] })?.list || []) as ComputeNodeVO[]).filter(
      (node) =>
        node.nodeRole === 'compute' || node.nodeRole === 'gpu' || node.nodeRole === 'hybrid',
    );
    nodeRecords.value = list;
    nodeOptions.value = list
      .filter((node): node is ComputeNodeVO & { id: number } => Number.isInteger(Number(node.id)))
      .map((node) => ({
        label: `${node.name || '节点'} (${node.host || '-'})`,
        value: Number(node.id),
      }));
    updateSchema({
      field: 'target_node_id',
      componentProps: {
        options: nodeOptions.value,
        placeholder: '选择在线 GPU/计算节点',
        showSearch: true,
        allowClear: true,
        onChange: (value?: number) => {
          selectedTargetNodeId.value = value;
          void refreshGpuSelection();
        },
        filterOption: (input: string, option: { label?: string }) =>
          (option?.label ?? '').toLowerCase().includes(input.toLowerCase()),
      },
    });
  } catch (e) {
    console.error('加载节点列表失败', e);
    nodeOptions.value = [];
    nodeRecords.value = [];
  }
};

const refreshGpuSelection = async () => {
  const values = await getFieldsValue();
  const currentGpuIds = Array.isArray(values.gpu_ids)
    ? values.gpu_ids.map((gpuId: string | number) => Number(gpuId))
    : [];
  const validGpuIds = currentGpuIds.filter((gpuId) => availableGpuIds.value.includes(gpuId));
  const defaultGpuIds = validGpuIds.length
    ? validGpuIds
    : (availableGpuIds.value.length ? [availableGpuIds.value[0]] : undefined);
  const gpuSourceResolved = selectedSchedulePolicy.value !== 'node' || !!selectedTargetNode.value;
  await setFieldsValue({
    use_gpu: availableGpuIds.value.length > 0
      ? values.use_gpu !== false
      : (gpuSourceResolved ? false : values.use_gpu !== false),
    gpu_ids: defaultGpuIds,
  });
  updateSchema([
    {
      field: 'gpu_ids',
      componentProps: {
        mode: 'multiple',
        options: gpuOptions.value,
        placeholder: '请选择训练使用的 GPU',
        allowClear: false,
        onChange: (gpuIds: Array<string | number>) => {
          void refreshAutoBatchSize({ gpu_ids: gpuIds });
        },
      },
    },
    { field: 'use_gpu', helpMessage: gpuHelpMessage.value },
  ]);
  await refreshAutoBatchSize();
};

const datasetSourceTab = ref<DatasetSourceTab>('local');
const cloudDatasetsLoaded = ref(false);
const cloudDatasetLoading = ref(false);
const localDatasetFile = ref<File | null>(null);
const localDatasetPath = ref('');
const localDatasetDisplayName = ref('');
const localFileList = ref<UploadProps['fileList']>([]);

const loadGpuStatus = async () => {
  gpuLoading.value = true;
  updateSchema({
    field: 'use_gpu',
    helpMessage: '正在探测 GPU...',
  });
  try {
    const res = await getTrainGpuStatus();
    const data = (res?.data ?? res) as GpuStatusData;
    gpuStatus.value = {
      cuda_available: !!data?.cuda_available,
      visible_gpu_ids: data?.visible_gpu_ids ?? [],
      multi_gpu: !!data?.multi_gpu,
      devices: data?.devices ?? [],
    };
    await refreshGpuSelection();
  } catch (e) {
    gpuStatus.value = defaultGpuStatus();
    await refreshGpuSelection();
    console.error(e);
  } finally {
    gpuLoading.value = false;
    updateSchema({
      field: 'use_gpu',
      helpMessage: gpuHelpMessage.value,
    });
  }
};

const resetDatasetSelection = () => {
  localDatasetFile.value = null;
  localDatasetPath.value = '';
  localDatasetDisplayName.value = '';
  localFileList.value = [];
  selectedDatasetId.value = undefined;
};

const onDatasetSourceChange = (e: { target: { value: DatasetSourceTab } }) => {
  onDatasetTabChange(e.target.value);
};

const onDatasetTabChange = (key: string | number) => {
  if (isResumeMode.value) return;
  resetDatasetSelection();
  if (key === 'cloud' && !cloudDatasetsLoaded.value) {
    loadDatasets().finally(() => {
      cloudDatasetsLoaded.value = true;
    });
  }
};

const isRetrainMode = ref(false);
const isResumeMode = ref(false);
const retrainTaskId = ref<number | undefined>();
const completedEpochs = ref(0);
const resumeDatasetPath = ref('');
const resumeDatasetName = ref('');
const resumeDatasetVersion = ref('');

const drawerTitle = computed(() => {
  if (isResumeMode.value) return '继续训练';
  if (isRetrainMode.value) return '重新训练';
  return '训练参数配置';
});

const submitButtonText = computed(() => {
  if (isResumeMode.value) return '继续训练';
  if (isRetrainMode.value) return '重新训练';
  return '开始训练';
});

const resumeHint = computed(() =>
  `将从第 ${completedEpochs.value} epoch 断点继续，请设置大于 ${completedEpochs.value} 的总迭代次数。`,
);

const [registerForm, { setFieldsValue, validate, resetFields, updateSchema, getFieldsValue }] = useForm({
  labelWidth: 100,
  baseColProps: { span: 24 },
  showActionButtonGroup: false,
  schemas: [
    {
      field: 'task_name',
      label: '任务名称',
      component: 'Input',
      required: true,
      componentProps: {
        placeholder: '请输入训练任务名称',
      },
    },
    {
      field: 'epochs',
      label: '迭代次数',
      component: 'InputNumber',
      required: true,
      defaultValue: 100,
      componentProps: {
        min: 10,
        max: 1000,
        style: { width: '100%' },
        placeholder: 'epochs',
      },
      helpMessage: '推荐 100-300',
    },
    {
      field: 'auto_batch_size',
      label: '自动批量',
      component: 'Switch',
      defaultValue: defaultAutoBatchSize('new'),
      componentProps: {
        checkedChildren: '是',
        unCheckedChildren: '否',
        onChange: (value: boolean) => {
          void handleAutoBatchChange(value);
        },
      },
      helpMessage: '根据所选 GPU、可用显存和图像尺寸自动计算',
    },
    {
      field: 'batch_size',
      label: '批量大小',
      component: 'InputNumber',
      required: true,
      defaultValue: 16,
      componentProps: {
        min: 1,
        max: 64,
        style: { width: '100%' },
        placeholder: 'batch_size',
        disabled: true,
      },
      helpMessage: '正在根据训练资源计算推荐值',
    },
    {
      field: 'imgsz',
      label: '图像尺寸',
      component: 'InputNumber',
      required: true,
      defaultValue: 640,
      componentProps: {
        min: 320,
        max: 1280,
        step: 32,
        style: { width: '100%' },
        placeholder: '640',
        onChange: (value: number) => {
          void refreshAutoBatchSize({ imgsz: value });
        },
      },
      helpMessage: 'YOLO 默认 640',
    },
    {
      field: 'use_gpu',
      label: 'GPU 训练',
      component: 'Switch',
      defaultValue: true,
      componentProps: {
        checkedChildren: '是',
        unCheckedChildren: '否',
        onChange: (value: boolean) => {
          void refreshAutoBatchSize({ use_gpu: value });
        },
      },
      helpMessage: '正在探测 GPU...',
    },
    {
      field: 'gpu_ids',
      label: '训练 GPU',
      component: 'Select',
      componentProps: {
        mode: 'multiple',
        options: [],
        placeholder: '请选择训练使用的 GPU',
        allowClear: false,
        onChange: (gpuIds: Array<string | number>) => {
          void refreshAutoBatchSize({ gpu_ids: gpuIds });
        },
      },
      ifShow: ({ values }) => values.use_gpu && availableGpuIds.value.length > 0,
      required: ({ values }) => values.use_gpu && availableGpuIds.value.length > 0,
      helpMessage: '选择一张 GPU 为单卡训练；选择多张 GPU 将启用 DDP 并行训练',
    },
    {
      field: 'schedule_policy',
      label: '调度策略',
      component: 'Select',
      defaultValue: 'auto',
      componentProps: {
        options: schedulePolicyOptions,
        onChange: (value: string) => {
          selectedSchedulePolicy.value = value;
          if (value !== 'node') selectedTargetNodeId.value = undefined;
          void refreshGpuSelection();
        },
      },
      helpMessage:
        '优先调度 GPU 节点；无可用 GPU 时自动回落到 CPU 节点（含中心节点）。集群模式需 CephFS 与 model_train Bundle',
    },
    {
      field: 'target_node_id',
      label: '目标节点',
      component: 'Select',
      componentProps: {
        options: [],
        placeholder: '选择在线 GPU/计算节点',
        showSearch: true,
        allowClear: true,
        onChange: (value?: number) => {
          selectedTargetNodeId.value = value;
          void refreshGpuSelection();
        },
      },
      ifShow: ({ values }) => values.schedule_policy === 'node',
      required: ({ values }) => values.schedule_policy === 'node',
    },
  ],
});

function selectedGpuIdsFromValues(values: Record<string, any>): number[] {
  if (values.use_gpu === false || !Array.isArray(values.gpu_ids)) return [];
  return [...new Set(
    values.gpu_ids
      .map((gpuId: string | number) => Number(gpuId))
      .filter((gpuId: number) => Number.isInteger(gpuId) && gpuId >= 0),
  )];
}

function recommendationDevices(gpuIds: number[]): GpuDeviceInfo[] {
  if (!gpuIds.length) return [];
  if (selectedSchedulePolicy.value === 'local') {
    return gpuStatus.value.devices.filter((device) => gpuIds.includes(device.index));
  }
  if (selectedSchedulePolicy.value === 'node') {
    return parseNodeGpuDevices(selectedTargetNode.value)
      .filter((device) => gpuIds.includes(device.index));
  }

  const gpuCount = gpuIds.length;
  const candidates: GpuDeviceInfo[] = [];
  if (gpuStatus.value.devices.length >= gpuCount) {
    candidates.push(...gpuStatus.value.devices.slice(0, gpuCount));
  }
  nodeRecords.value.forEach((node) => {
    if (nodeGpuCount(node) < gpuCount) return;
    const devices = parseNodeGpuDevices(node);
    if (devices.length >= gpuCount) candidates.push(...devices.slice(0, gpuCount));
  });
  return candidates;
}

function updateBatchSizeMode(autoBatchSize: boolean) {
  updateSchema({
    field: 'batch_size',
    componentProps: { disabled: autoBatchSize },
    helpMessage: autoBatchSize
      ? '正在根据训练资源计算推荐值'
      : '手动设置时，多卡训练的总批量需能被 GPU 数量整除',
  });
}

async function handleAutoBatchChange(autoBatchSize: boolean) {
  updateBatchSizeMode(autoBatchSize);
  if (autoBatchSize) {
    await refreshAutoBatchSize({ auto_batch_size: true });
  }
}

async function refreshAutoBatchSize(overrides: Record<string, unknown> = {}) {
  const values = { ...(await getFieldsValue()), ...overrides };
  if (values.auto_batch_size === false) return;
  const gpuIds = selectedGpuIdsFromValues(values);
  const devices = recommendationDevices(gpuIds).map((device) => ({
    totalMemoryGb: device.total_memory_gb,
    freeMemoryGb: device.free_memory_gb,
  }));
  const recommendation = recommendTrainBatchSize({
    gpuCount: gpuIds.length,
    devices,
    imageSize: Number(values.imgsz) || 640,
  });

  await setFieldsValue({ batch_size: recommendation.batchSize });

  const resourceText = recommendation.gpuCount
    ? `${recommendation.gpuCount} 张 GPU，每卡 ${recommendation.perGpuBatchSize}`
    : 'CPU 模式';
  const memoryText = recommendation.limitingMemoryGb == null
    ? ''
    : `，最低安全显存 ${recommendation.limitingMemoryGb} GB`;
  updateSchema({
    field: 'batch_size',
    helpMessage: `自动推荐总批量 ${recommendation.batchSize}（${resourceText}${memoryText}）`,
  });
}

const resetTrainForm = async () => {
  isRetrainMode.value = false;
  isResumeMode.value = false;
  retrainTaskId.value = undefined;
  completedEpochs.value = 0;
  resumeDatasetPath.value = '';
  resumeDatasetName.value = '';
  resumeDatasetVersion.value = '';
  datasetSourceTab.value = 'local';
  cloudDatasetsLoaded.value = false;
  datasetList.value = [];
  customWeightOptions.value = [];
  nodeRecords.value = [];
  selectedSchedulePolicy.value = 'auto';
  selectedTargetNodeId.value = undefined;
  gpuStatus.value = defaultGpuStatus();
  selectedModelPath.value = presetModels[0];
  modelPathDisabled.value = false;
  await resetFields();
  resetDatasetSelection();
  updateSchema([
    { field: 'task_name', componentProps: { disabled: false } },
    { field: 'epochs', componentProps: { min: 10 }, helpMessage: '推荐 100-300' },
    {
      field: 'batch_size',
      componentProps: { disabled: true },
      helpMessage: '正在根据训练资源计算推荐值',
    },
  ]);
};

const applyResumeFormState = () => {
  const disabled = isResumeMode.value;
  modelPathDisabled.value = disabled;
  updateSchema([
    { field: 'task_name', componentProps: { disabled } },
    {
      field: 'epochs',
      componentProps: { min: completedEpochs.value + 1 },
      helpMessage: `需大于已完成 ${completedEpochs.value} epoch`,
    },
  ]);
};

const drawerOpenData = ref<Record<string, unknown>>({});

async function initTrainDrawer(data: Record<string, unknown> = {}) {
  await resetTrainForm();
  await Promise.all([loadCustomModels(), loadNodes()]);

  const fillFromRecord = async (
    record: Record<string, unknown>,
    launchMode: Exclude<TrainTaskLaunchMode, 'new'>,
  ) => {
    const autoBatchSize = defaultAutoBatchSize(launchMode);
    retrainTaskId.value = record.id as number;
    updateBatchSizeMode(autoBatchSize);

    const hp = parseTrainHyperparameters(record.hyperparameters);
    completedEpochs.value = getCompletedEpochs(record);

    await setFieldsValue({
      task_name: hp.taskName || resolveTaskBaseNameFromRecord(record),
      epochs: hp.epochs ?? 100,
      auto_batch_size: autoBatchSize,
      batch_size: hp.batch_size ?? 16,
      imgsz: hp.imgsz ?? 640,
      schedule_policy: (record.schedule_policy as string) || 'auto',
      target_node_id: record.target_node_id ?? undefined,
    });
    selectedSchedulePolicy.value = String(record.schedule_policy || 'auto');
    selectedTargetNodeId.value = record.target_node_id == null
      ? undefined
      : Number(record.target_node_id);
    selectedModelPath.value = hp.modelPath || presetModels[0];

    const datasetPath = String(record.dataset_path || '');
    resumeDatasetPath.value = datasetPath;
    resumeDatasetName.value = String(record.dataset_name || '');
    resumeDatasetVersion.value = String(record.dataset_version || '');
    const datasetSource = hp.datasetSource || (isCloudDatasetPath(datasetPath) ? 'cloud' : 'local');
    datasetSourceTab.value = datasetSource as DatasetSourceTab;

    if (datasetSource === 'local' && datasetPath) {
      localDatasetPath.value = datasetPath;
      const displayName = resolveLocalDatasetDisplayName(
        datasetPath,
        String(record.dataset_name || ''),
      );
      localDatasetDisplayName.value = displayName;
      localFileList.value = [{ uid: '-1', name: displayName, status: 'done' }];
    } else if (datasetSource === 'cloud') {
      await loadDatasets();
      cloudDatasetsLoaded.value = true;
      const matched = datasetList.value.find((item) => item.zipUrl === datasetPath)
        || datasetList.value.find(
          (item) => item.name === record.dataset_name && item.version === record.dataset_version,
        );
      if (matched) {
        selectedDatasetId.value = matched.id;
      }
    }
  };

  if (data?.isResume && data?.record) {
    isResumeMode.value = true;
    await fillFromRecord(data.record as Record<string, unknown>, 'resume');
    const values = await getFieldsValue();
    if ((values.epochs ?? 100) <= completedEpochs.value) {
      await setFieldsValue({ epochs: completedEpochs.value + 1 });
    }
  } else if (data?.isRetrain && data?.record) {
    isRetrainMode.value = true;
    await fillFromRecord(data.record as Record<string, unknown>, 'retrain');
  } else if (data?.datasetId) {
    datasetSourceTab.value = 'cloud';
    await loadDatasets();
    cloudDatasetsLoaded.value = true;
    const matched = datasetList.value.find(
      (item) => String(item.id) === String(data.datasetId) && !!item.zipUrl,
    );
    if (matched) {
      selectedDatasetId.value = matched.id;
    } else {
      createMessage.warning('当前数据集不可用于训练，请确认 MinIO 同步状态');
    }
  }

  await loadGpuStatus();

  if ((data?.isRetrain || data?.isResume) && data?.record) {
    const hp = parseTrainHyperparameters(data.record.hyperparameters);
    if (hp.use_gpu !== undefined) {
      const savedGpuIds = hasManualGpuSelection(data.record.hyperparameters)
      && Array.isArray(hp.gpu_ids)
        ? hp.gpu_ids
          .map((gpuId) => Number(gpuId))
          .filter((gpuId) => availableGpuIds.value.includes(gpuId))
        : [];
      await setFieldsValue({
        use_gpu: hp.use_gpu && availableGpuIds.value.length > 0,
        gpu_ids: savedGpuIds.length
          ? savedGpuIds
          : (availableGpuIds.value.length ? [availableGpuIds.value[0]] : undefined),
      });
    }
  }

  if (isRetrainMode.value) {
    await refreshAutoBatchSize();
  }

  if (isResumeMode.value || isRetrainMode.value) {
    applyResumeFormState();
  }
}

const [registerDrawer, { closeDrawer, getOpen }] = useDrawerInner((data) => {
  drawerOpenData.value = (data ?? {}) as Record<string, unknown>;
});

watch(
  () => getOpen.value,
  (open) => {
    if (!open) {
      return;
    }
    void initTrainDrawer({ ...drawerOpenData.value });
    drawerOpenData.value = {};
  },
);

const datasetList = ref<DatasetItem[]>([]);
const selectedDatasetId = ref<string | number | undefined>(undefined);

const selectedCloudDataset = computed(() =>
  datasetList.value.find((item) => item.id === selectedDatasetId.value),
);

const cloudDatasetOptions = computed(() =>
  datasetList.value.map((item) => {
    const trainable = !!item.zipUrl;
    const statusHint = trainable
      ? '可用于训练'
      : item.isAllocated === 1
        ? '待同步 Minio'
        : (item.annotatedImages ?? 0) >= (item.totalImages ?? 0) && (item.totalImages ?? 0) > 0
          ? '待划分用途'
          : '未完成标注/同步';
    return {
      label: `${item.name}（${item.version || '—'}）— ${statusHint}`,
      value: item.id,
      disabled: !trainable,
    };
  }),
);

const filterCloudDataset = (input: string, option?: { label?: string }) =>
  (option?.label ?? '').toLowerCase().includes(input.toLowerCase());

const emit = defineEmits(['success']);

const loadDatasets = async () => {
  cloudDatasetLoading.value = true;
  try {
    const res = await getDatasetPage({ page: 1, size: 100 });
    datasetList.value = res.data?.list || res.data || [];
  } catch (e) {
    createMessage.error('加载云端数据集失败');
    console.error(e);
  } finally {
    cloudDatasetLoading.value = false;
  }
};

const beforeLocalDatasetUpload: UploadProps['beforeUpload'] = (file) => {
  const isZip = file.name.toLowerCase().endsWith('.zip');
  if (!isZip) {
    createMessage.warn('请选择 ZIP 格式的数据集压缩包');
    return false;
  }
  const maxSize = 5 * 1024 * 1024 * 1024;
  if (file.size > maxSize) {
    createMessage.warn('数据集压缩包不能超过 5GB');
    return false;
  }
  localDatasetFile.value = file;
  localDatasetPath.value = '';
  localDatasetDisplayName.value = file.name;
  localFileList.value = [{ uid: '-1', name: file.name, status: 'done' }];
  return false;
};

const handleLocalFileRemove = () => {
  localDatasetFile.value = null;
  localDatasetPath.value = '';
  localDatasetDisplayName.value = '';
  localFileList.value = [];
};

const uploadLocalDatasetIfNeeded = async (): Promise<string | null> => {
  if (localDatasetPath.value) {
    return localDatasetPath.value;
  }
  if (!localDatasetFile.value) {
    return null;
  }
  const formData = new FormData();
  formData.append('file', localDatasetFile.value);
  const res = await uploadTrainDataset(formData);
  const payload = (res as { path?: string; fileName?: string; data?: { path?: string; fileName?: string } }) ?? {};
  const path = payload.path ?? payload.data?.path;
  if (!path) {
    throw new Error('数据集上传失败');
  }
  localDatasetPath.value = path;
  const fileName = payload.fileName ?? payload.data?.fileName;
  if (fileName) {
    localDatasetDisplayName.value = fileName;
  }
  return path;
};

const startTrain = async () => {
  let values: Record<string, any>;
  try {
    values = await validate();
  } catch {
    return;
  }

  if (isResumeMode.value && Number(values.epochs) <= completedEpochs.value) {
    createMessage.warn(`总 epochs 必须大于已完成 epoch(${completedEpochs.value})`);
    return;
  }

  if (!selectedModelPath.value) {
    createMessage.warn('请选择预训练权重');
    return;
  }

  if (values.schedule_policy === 'node' && !values.target_node_id) {
    createMessage.warn('请选择目标节点');
    return;
  }

  const selectedGpuIds = values.use_gpu && Array.isArray(values.gpu_ids)
    ? [...new Set(values.gpu_ids.map((gpuId: string | number) => Number(gpuId)))]
    : [];
  if (values.use_gpu) {
    if (!selectedGpuIds.length) {
      createMessage.warn('请至少选择一张训练 GPU');
      return;
    }
    const invalidGpuIds = selectedGpuIds.filter(
      (gpuId) => !Number.isInteger(gpuId) || !availableGpuIds.value.includes(gpuId),
    );
    if (invalidGpuIds.length) {
      createMessage.warn(`GPU ${invalidGpuIds.join(', ')} 当前不可用，请重新选择`);
      return;
    }
    if (selectedGpuIds.length > 1 && Number(values.batch_size) % selectedGpuIds.length !== 0) {
      const nextBatchSize = Math.ceil(Number(values.batch_size) / selectedGpuIds.length)
        * selectedGpuIds.length;
      createMessage.warn(
        `多卡训练的批次大小必须能被 GPU 数量 ${selectedGpuIds.length} 整除，建议改为 ${nextBatchSize}`,
      );
      return;
    }
  }

  let datasetPath = '';
  let datasetName = '';
  let datasetVersion = '';
  const datasetSource = datasetSourceTab.value;

  if (isResumeMode.value) {
    datasetPath = resumeDatasetPath.value || localDatasetPath.value;
    datasetName = resumeDatasetName.value || (localDatasetDisplayName.value || '本地数据集').replace(/\.zip$/i, '');
    datasetVersion = resumeDatasetVersion.value || '';
    if (!datasetPath) {
      createMessage.warn('续训任务缺少数据集信息，请使用重新训练');
      return;
    }
  } else if (datasetSource === 'local') {
    if (!localDatasetFile.value && !localDatasetPath.value) {
      createMessage.warn('请选择本地数据集 ZIP 压缩包');
      return;
    }
    uploading.value = true;
    try {
      const path = await uploadLocalDatasetIfNeeded();
      if (!path) {
        createMessage.warn('本地数据集上传失败，请重试');
        return;
      }
      datasetPath = path;
      datasetName = (localDatasetDisplayName.value || '本地数据集').replace(/\.zip$/i, '');
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '本地数据集上传失败';
      createMessage.error(msg);
      return;
    } finally {
      uploading.value = false;
    }
  } else {
    if (!selectedDatasetId.value) {
      createMessage.warn('请选择云端数据集');
      return;
    }
    const dataset = datasetList.value.find((item) => item.id === selectedDatasetId.value);
    if (!dataset) {
      createMessage.warn('请选择云端数据集');
      return;
    }
    if (!dataset.zipUrl) {
      if (dataset.isAllocated !== 1) {
        createMessage.warn('该数据集尚未划分用途，请先在数据集管理中点击「按比例划分数据集用途」');
      } else if (dataset.isSyncMinio !== 1) {
        createMessage.warn('该数据集尚未同步到 Minio，请先在数据集管理中点击「一键同步到 Minio」');
      } else {
        createMessage.warn('该数据集训练包尚未就绪，请完成划分用途并同步到 Minio 后再训练');
      }
      return;
    }
    datasetPath = dataset.zipUrl;
    datasetName = dataset.name;
    datasetVersion = dataset.version || '';
  }

  emit('success', {
    epochs: values.epochs,
    batch_size: values.batch_size,
    imgsz: values.imgsz,
    taskName: String(values.task_name || '').trim(),
    modelPath: selectedModelPath.value,
    datasetSource,
    datasetPath,
    datasetName,
    datasetVersion,
    use_gpu: values.use_gpu,
    gpu_ids: values.use_gpu ? selectedGpuIds : undefined,
    gpu_selection_manual: true,
    schedulePolicy: values.schedule_policy,
    targetNodeId: values.schedule_policy === 'node' ? values.target_node_id : null,
    ...(retrainTaskId.value ? { taskId: retrainTaskId.value } : {}),
    ...(isResumeMode.value ? { resume: true } : {}),
  });
  closeDrawer();
};

const handleCancel = () => closeDrawer();
</script>

<style lang="less" scoped>
.train-drawer-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.resume-alert {
  margin-bottom: 4px;
}

.resource-form {
  :deep(.ant-form-item) {
    margin-bottom: 16px;
  }
}

.gpu-device-panel {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
  padding: 10px 12px;
  background: #fafafa;
  border: 1px solid #f0f0f0;
  border-radius: 6px;
}

.gpu-device-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: rgba(0, 0, 0, 0.65);

  :deep(.ant-tag) {
    margin: 0;
  }
}

.form-hint {
  margin-top: 4px;
  color: rgba(0, 0, 0, 0.45);
  font-size: 13px;
  line-height: 1.5;
}

.form-hint-warn {
  margin: 8px 0 0;
  font-size: 13px;
  color: #fa8c16;
  line-height: 1.5;
}

.footer-buttons {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
}
</style>
