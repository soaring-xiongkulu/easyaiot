<template>
  <wd-popup v-model="visible" position="bottom" custom-style="border-radius: 24rpx 24rpx 0 0; max-height: 90vh;">
    <view class="p-32rpx">
      <view class="mb-24rpx text-center text-32rpx font-semibold">
        {{ popupTitle }}
      </view>

      <scroll-view scroll-y class="max-h-70vh">
        <view v-if="mode === 'resume'" class="mb-24rpx rounded-8rpx bg-[#e6f4ff] px-24rpx py-16rpx text-24rpx text-[#1890ff]">
          将从第 {{ completedEpochs }} epoch 断点继续，总迭代次数需大于 {{ completedEpochs }}
        </view>

        <view class="mb-24rpx">
          <view class="mb-12rpx text-26rpx text-[#666]">
            任务名称 <text class="text-[#f56c6c]">*</text>
          </view>
          <wd-input v-model="form.task_name" placeholder="请输入训练任务名称" :disabled="mode === 'resume'" clearable />
        </view>

        <view class="mb-24rpx">
          <view class="mb-12rpx text-26rpx text-[#666]">
            迭代次数 <text class="text-[#f56c6c]">*</text>
          </view>
          <wd-input v-model="epochsText" type="number" placeholder="推荐 100-300" clearable />
        </view>

        <view class="mb-24rpx">
          <view class="mb-12rpx text-26rpx text-[#666]">
            批量大小 <text class="text-[#f56c6c]">*</text>
          </view>
          <wd-input v-model="batchSizeText" type="number" placeholder="如 16" clearable />
        </view>

        <view class="mb-24rpx">
          <view class="mb-12rpx text-26rpx text-[#666]">
            图像尺寸 <text class="text-[#f56c6c]">*</text>
          </view>
          <wd-input v-model="imgszText" type="number" placeholder="默认 640" clearable />
        </view>

        <view class="mb-24rpx">
          <view class="mb-12rpx text-26rpx text-[#666]">
            预训练权重 <text class="text-[#f56c6c]">*</text>
          </view>
          <wd-radio-group v-model="form.modelPath" type="button" :disabled="mode === 'resume'">
            <wd-radio v-for="m in presetModels" :key="m" :value="m">
              {{ m }}
            </wd-radio>
          </wd-radio-group>
        </view>

        <view v-if="mode === 'create'" class="mb-24rpx">
          <view class="mb-12rpx text-26rpx text-[#666]">
            数据集路径 <text class="text-[#f56c6c]">*</text>
          </view>
          <wd-input v-model="form.datasetPath" placeholder="上传后返回的路径或云端 zipUrl" clearable />
          <view class="mt-8rpx text-22rpx text-[#999]">
            移动端暂仅支持填写已上传的数据集路径
          </view>
        </view>

        <view v-else class="mb-24rpx rounded-8rpx bg-[#f7f8f9] px-24rpx py-16rpx text-26rpx text-[#666]">
          数据集：{{ resumeDatasetLabel || '沿用原任务数据集' }}
        </view>

        <view class="mb-24rpx flex items-center justify-between">
          <view class="text-26rpx text-[#666]">
            GPU 训练
          </view>
          <wd-switch v-model="form.use_gpu" />
        </view>

        <view class="mb-24rpx">
          <view class="mb-12rpx text-26rpx text-[#666]">
            调度策略
          </view>
          <wd-radio-group v-model="form.schedule_policy" type="button">
            <wd-radio value="local">
              本机
            </wd-radio>
            <wd-radio value="auto">
              自动
            </wd-radio>
            <wd-radio value="node">
              指定节点
            </wd-radio>
          </wd-radio-group>
        </view>

        <view v-if="form.schedule_policy === 'node'" class="mb-24rpx">
          <view class="mb-12rpx text-26rpx text-[#666]">
            目标节点 <text class="text-[#f56c6c]">*</text>
          </view>
          <view
            class="flex items-center justify-between rounded-8rpx bg-[#f7f8f9] px-24rpx py-20rpx"
            @click="nodePickerVisible = true"
          >
            <text class="text-28rpx" :class="selectedNodeLabel ? 'text-[#333]' : 'text-[#999]'">
              {{ selectedNodeLabel || '请选择在线计算节点' }}
            </text>
            <wd-icon name="arrow-right" size="16px" color="#999" />
          </view>
        </view>
      </scroll-view>

      <view class="mt-24rpx flex gap-24rpx">
        <wd-button class="flex-1" plain @click="visible = false">
          取消
        </wd-button>
        <wd-button class="flex-1" type="primary" :loading="submitting" @click="handleSubmit">
          {{ submitButtonText }}
        </wd-button>
      </view>
    </view>

    <wd-picker
      v-model:visible="nodePickerVisible"
      :model-value="form.target_node_id"
      :columns="nodeOptions"
      label-key="label"
      value-key="value"
      @confirm="handleNodeConfirm"
    />
  </wd-popup>
</template>

<script lang="ts" setup>
import type { TrainTask } from '@/api/model/train'
import { computed, reactive, ref } from 'vue'
import { useToast } from '@wot-ui/ui/components/wd-toast'
import { startTrain } from '@/api/model/train'
import { getNodePage } from '@/api/video/node'
import {
  getCompletedEpochs,
  parseTrainHyperparameters,
  resolveTaskBaseNameFromRecord,
} from '@/utils/model/trainTaskUtils'
import { parseListResponse } from '@/utils/listResponse'

type TrainMode = 'create' | 'resume' | 'retrain'

const presetModels = ['yolov8n.pt', 'yolo11n.pt', 'yolo26n.pt']

const emit = defineEmits<{ success: [] }>()
const toast = useToast()
const visible = ref(false)
const mode = ref<TrainMode>('create')
const taskId = ref<number | null>(null)
const completedEpochs = ref(0)
const submitting = ref(false)
const nodePickerVisible = ref(false)
const nodeOptions = ref<Array<{ label: string, value: number }>>([])
const resumeDatasetPath = ref('')
const resumeDatasetName = ref('')
const resumeDatasetVersion = ref('')

const form = reactive({
  task_name: '',
  epochs: 100,
  batch_size: 16,
  imgsz: 640,
  modelPath: presetModels[0],
  datasetPath: '',
  use_gpu: true,
  schedule_policy: 'auto' as 'local' | 'auto' | 'node',
  target_node_id: undefined as number | undefined,
})

const popupTitle = computed(() => {
  if (mode.value === 'resume')
    return '继续训练'
  if (mode.value === 'retrain')
    return '重新训练'
  return '新建训练任务'
})

const submitButtonText = computed(() => {
  if (mode.value === 'resume')
    return '继续训练'
  if (mode.value === 'retrain')
    return '重新训练'
  return '开始训练'
})

const resumeDatasetLabel = computed(() => {
  const parts = [resumeDatasetName.value, resumeDatasetVersion.value].filter(Boolean)
  return parts.join(' · ')
})

const epochsText = computed({
  get: () => String(form.epochs),
  set: (val: string) => { form.epochs = Number(val) || 0 },
})

const batchSizeText = computed({
  get: () => String(form.batch_size),
  set: (val: string) => { form.batch_size = Number(val) || 0 },
})

const imgszText = computed({
  get: () => String(form.imgsz),
  set: (val: string) => { form.imgsz = Number(val) || 0 },
})

const selectedNodeLabel = computed(() => {
  if (!form.target_node_id)
    return ''
  return nodeOptions.value.find(n => n.value === form.target_node_id)?.label || String(form.target_node_id)
})

function resetForm() {
  form.task_name = ''
  form.epochs = 100
  form.batch_size = 16
  form.imgsz = 640
  form.modelPath = presetModels[0]
  form.datasetPath = ''
  form.use_gpu = true
  form.schedule_policy = 'auto'
  form.target_node_id = undefined
  resumeDatasetPath.value = ''
  resumeDatasetName.value = ''
  resumeDatasetVersion.value = ''
}

async function loadNodes() {
  try {
    const res = await getNodePage({ pageNo: 1, pageSize: 200, status: 'online' })
    const { list } = parseListResponse<any>(res, ['list', 'data'])
    nodeOptions.value = list
      .filter((n: any) => {
        const fns = Array.isArray(n.functions) ? n.functions : String(n.nodeRole || '').split(',')
        return fns.includes('train')
      })
      .map((n: any) => ({
        label: `${n.name} (${n.host})`,
        value: n.id,
      }))
  }
  catch {
    nodeOptions.value = []
  }
}

function handleNodeConfirm({ value }: { value: number }) {
  form.target_node_id = value
}

function fillFromTask(item: TrainTask) {
  const hp = parseTrainHyperparameters(item.hyperparameters)
  completedEpochs.value = getCompletedEpochs(item as any)
  taskId.value = item.id
  form.task_name = hp.taskName || resolveTaskBaseNameFromRecord(item as any)
  form.epochs = Math.max(hp.epochs ?? 100, completedEpochs.value + 1)
  form.batch_size = hp.batch_size ?? 16
  form.imgsz = hp.imgsz ?? 640
  form.modelPath = hp.modelPath || presetModels[0]
  form.use_gpu = hp.use_gpu !== false
  form.schedule_policy = (item.schedule_policy as any) || 'auto'
  form.target_node_id = (item as any).target_node_id ?? undefined
  resumeDatasetPath.value = String((item as any).dataset_path || '')
  resumeDatasetName.value = item.dataset_name || ''
  resumeDatasetVersion.value = item.dataset_version || ''
}

async function handleSubmit() {
  if (!form.task_name.trim()) {
    toast.warning('请输入任务名称')
    return
  }
  if (form.epochs <= 0 || form.batch_size <= 0 || form.imgsz <= 0) {
    toast.warning('请填写有效的训练参数')
    return
  }
  if (mode.value === 'resume' && form.epochs <= completedEpochs.value) {
    toast.warning(`总迭代次数需大于已完成 ${completedEpochs.value} epoch`)
    return
  }
  if (form.schedule_policy === 'node' && !form.target_node_id) {
    toast.warning('请选择目标节点')
    return
  }

  let datasetPath = ''
  let datasetName = ''
  let datasetVersion = ''

  if (mode.value === 'create') {
    datasetPath = form.datasetPath.trim()
    if (!datasetPath) {
      toast.warning('请输入数据集路径')
      return
    }
    datasetName = '本地数据集'
  }
  else {
    datasetPath = resumeDatasetPath.value
    datasetName = resumeDatasetName.value || '本地数据集'
    datasetVersion = resumeDatasetVersion.value
    if (!datasetPath) {
      toast.warning('续训/重训缺少数据集信息')
      return
    }
  }

  submitting.value = true
  try {
    await startTrain({
      epochs: form.epochs,
      batch_size: form.batch_size,
      imgsz: form.imgsz,
      taskName: form.task_name.trim(),
      modelPath: form.modelPath,
      datasetSource: 'local',
      datasetPath,
      datasetName,
      datasetVersion,
      use_gpu: form.use_gpu,
      schedule_policy: form.schedule_policy,
      target_node_id: form.schedule_policy === 'node' ? form.target_node_id : null,
      ...(taskId.value && mode.value !== 'create' ? { taskId: taskId.value } : {}),
      ...(mode.value === 'resume' ? { resume: true } : {}),
    })
    toast.success(mode.value === 'create' ? '训练已启动' : submitButtonText.value + '成功')
    visible.value = false
    emit('success')
  }
  catch (err: any) {
    toast.error(err?.msg || err?.message || '提交失败')
  }
  finally {
    submitting.value = false
  }
}

async function openCreate() {
  mode.value = 'create'
  taskId.value = null
  completedEpochs.value = 0
  resetForm()
  await loadNodes()
  visible.value = true
}

async function openResume(item: TrainTask) {
  mode.value = 'resume'
  resetForm()
  fillFromTask(item)
  await loadNodes()
  visible.value = true
}

async function openRetrain(item: TrainTask) {
  mode.value = 'retrain'
  resetForm()
  fillFromTask(item)
  await loadNodes()
  visible.value = true
}

defineExpose({ openCreate, openResume, openRetrain })
</script>
