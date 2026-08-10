<template>
  <wd-popup v-model="visible" position="bottom" custom-style="border-radius: 24rpx 24rpx 0 0; max-height: 90vh;">
    <view class="p-32rpx">
      <view class="mb-24rpx text-center text-32rpx font-semibold">
        {{ isEdit ? '编辑算法任务' : '新建算法任务' }}
      </view>

      <scroll-view scroll-y class="max-h-70vh">
        <view class="mb-24rpx">
          <view class="mb-12rpx text-26rpx text-[#666]">
            任务名称 <text class="text-[#f56c6c]">*</text>
          </view>
          <wd-input v-model="form.task_name" placeholder="请输入任务名称" clearable />
        </view>

        <view class="mb-24rpx">
          <view class="mb-12rpx text-26rpx text-[#666]">
            任务类型 <text class="text-[#f56c6c]">*</text>
          </view>
          <wd-radio-group v-model="form.task_mode" type="button" :disabled="isEdit">
            <wd-radio value="realtime_cpp">实时(高性能)</wd-radio>
            <wd-radio value="snap_cpp">抓拍(高性能)</wd-radio>
            <wd-radio value="patrol_cpp">巡检(高性能)</wd-radio>
            <wd-radio value="realtime">实时</wd-radio>
            <wd-radio value="snap">抓拍</wd-radio>
            <wd-radio value="patrol">巡检</wd-radio>
          </wd-radio-group>
        </view>

        <view class="mb-24rpx">
          <view class="mb-12rpx text-26rpx text-[#666]">
            关联摄像头 <text class="text-[#f56c6c]">*</text>
          </view>
          <view
            class="flex items-center justify-between rounded-8rpx bg-[#f7f8f9] px-24rpx py-20rpx"
            @click="devicePickerVisible = true"
          >
            <text class="text-28rpx" :class="selectedDeviceLabel ? 'text-[#333]' : 'text-[#999]'">
              {{ selectedDeviceLabel || '请选择摄像头（可多选）' }}
            </text>
            <wd-icon name="arrow-right" size="16px" color="#999" />
          </view>
        </view>

        <view class="mb-24rpx">
          <view class="mb-12rpx text-26rpx text-[#666]">
            关联模型 <text class="text-[#f56c6c]">*</text>
          </view>
          <view
            class="flex items-center justify-between rounded-8rpx bg-[#f7f8f9] px-24rpx py-20rpx"
            @click="modelPickerVisible = true"
          >
            <text class="text-28rpx" :class="selectedModelLabel ? 'text-[#333]' : 'text-[#999]'">
              {{ selectedModelLabel || '请选择模型（可多选）' }}
            </text>
            <wd-icon name="arrow-right" size="16px" color="#999" />
          </view>
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

        <view v-if="form.schedule_policy === 'auto'" class="mb-24rpx flex items-center justify-between">
          <view class="text-26rpx text-[#666]">
            优先 GPU 节点
          </view>
          <wd-switch v-model="form.prefer_gpu" />
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

        <view v-if="baseTaskType(form.task_mode) === 'realtime'" class="mb-24rpx">
          <view class="mb-12rpx text-26rpx text-[#666]">
            抽帧间隔
          </view>
          <wd-input v-model="extractIntervalText" type="number" placeholder="每 N 帧抽一次（默认 25）" clearable />
        </view>

        <view v-if="baseTaskType(form.task_mode) === 'realtime'" class="mb-24rpx flex items-center justify-between">
          <view class="text-26rpx text-[#666]">
            启用运动补检
          </view>
          <wd-switch v-model="form.motion_gate_enabled" />
        </view>

        <view v-if="baseTaskType(form.task_mode) === 'snap'" class="mb-24rpx">
          <view class="mb-12rpx text-26rpx text-[#666]">
            Cron 表达式 <text class="text-[#f56c6c]">*</text>
          </view>
          <wd-input v-model="form.cron_expression" placeholder="如 0 */5 * * * ?" clearable />
        </view>

        <view v-if="baseTaskType(form.task_mode) === 'patrol'" class="mb-24rpx">
          <view class="mb-12rpx text-26rpx text-[#666]">
            巡检间隔(秒)
          </view>
          <wd-input v-model="patrolIntervalText" type="number" placeholder="默认 10" clearable />
        </view>

        <view class="mb-24rpx flex items-center justify-between">
          <view class="text-26rpx text-[#666]">
            启用告警事件
          </view>
          <wd-switch v-model="form.alert_event_enabled" />
        </view>
      </scroll-view>

      <view class="mt-24rpx flex gap-24rpx">
        <wd-button class="flex-1" plain @click="visible = false">
          取消
        </wd-button>
        <wd-button class="flex-1" type="primary" :loading="submitting" @click="handleSubmit">
          提交
        </wd-button>
      </view>
    </view>

    <!-- 摄像头多选 -->
    <wd-popup v-model="devicePickerVisible" position="bottom" custom-style="border-radius: 24rpx 24rpx 0 0; max-height: 70vh;">
      <view class="p-32rpx">
        <view class="mb-24rpx text-center text-30rpx font-semibold">
          选择摄像头
        </view>
        <view class="mb-16rpx">
          <wd-input v-model="deviceSearch" placeholder="搜索设备名称" clearable />
        </view>
        <scroll-view scroll-y class="max-h-50vh">
          <view
            v-for="device in filteredDeviceOptions"
            :key="device.value"
            class="mb-16rpx flex items-center justify-between rounded-8rpx px-24rpx py-20rpx"
            :class="isDeviceSelected(device.value) ? 'bg-[#e6f4ff]' : 'bg-[#f7f8f9]'"
            @click="toggleDevice(device.value)"
          >
            <text class="text-28rpx text-[#333]">{{ device.label }}</text>
            <wd-icon
              v-if="isDeviceSelected(device.value)"
              name="check"
              size="18px"
              color="#1890ff"
            />
          </view>
        </scroll-view>
        <wd-button type="primary" block class="mt-24rpx" @click="devicePickerVisible = false">
          确定
        </wd-button>
      </view>
    </wd-popup>

    <!-- 模型多选 -->
    <wd-popup v-model="modelPickerVisible" position="bottom" custom-style="border-radius: 24rpx 24rpx 0 0; max-height: 70vh;">
      <view class="p-32rpx">
        <view class="mb-24rpx text-center text-30rpx font-semibold">
          选择模型
        </view>
        <view class="mb-16rpx">
          <wd-input v-model="modelSearch" placeholder="搜索模型名称" clearable />
        </view>
        <scroll-view scroll-y class="max-h-50vh">
          <view
            v-for="model in filteredModelOptions"
            :key="model.value"
            class="mb-16rpx flex items-center justify-between rounded-8rpx px-24rpx py-20rpx"
            :class="isModelSelected(model.value) ? 'bg-[#e6f4ff]' : 'bg-[#f7f8f9]'"
            @click="toggleModel(model.value)"
          >
            <text class="text-28rpx text-[#333]">{{ model.label }}</text>
            <wd-icon
              v-if="isModelSelected(model.value)"
              name="check"
              size="18px"
              color="#1890ff"
            />
          </view>
        </scroll-view>
        <wd-button type="primary" block class="mt-24rpx" @click="modelPickerVisible = false">
          确定
        </wd-button>
      </view>
    </wd-popup>

    <!-- 节点选择 -->
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
import type { AlgorithmTask } from '@/api/video/algorithm'
import { computed, reactive, ref } from 'vue'
import { useToast } from '@wot-ui/ui/components/wd-toast'
import { getModelPage } from '@/api/model'
import { getDeviceList } from '@/api/video/camera'
import {
  createAlgorithmTask,
  updateAlgorithmTask,
} from '@/api/video/algorithm'
import { getNodePage } from '@/api/video/node'
import { parseListResponse } from '@/utils/listResponse'

const emit = defineEmits<{ success: [] }>()
const toast = useToast()
const visible = ref(false)
const isEdit = ref(false)
const taskId = ref<number | null>(null)
const submitting = ref(false)
const devicePickerVisible = ref(false)
const modelPickerVisible = ref(false)
const nodePickerVisible = ref(false)
const deviceOptions = ref<Array<{ label: string, value: string }>>([])
const modelOptions = ref<Array<{ label: string, value: number }>>([])
const nodeOptions = ref<Array<{ label: string, value: number }>>([])
const deviceSearch = ref('')
const modelSearch = ref('')

function baseTaskType(modeOrType?: string): 'realtime' | 'snap' | 'patrol' {
  const raw = String(modeOrType || 'realtime')
  const v = raw.endsWith('_cpp') ? raw.slice(0, -4) : raw
  if (v === 'snap' || v === 'patrol') return v
  return 'realtime'
}
function toTaskMode(taskType?: string, executor?: string): string {
  const base = baseTaskType(taskType)
  const ex = String(executor || 'python').toLowerCase()
  return (ex === 'cpp' || ex === 'c++' || ex === 'runtime' || ex === 'cxx') ? `${base}_cpp` : base
}
function fromTaskMode(mode?: string): { task_type: 'realtime' | 'snap' | 'patrol'; executor: 'python' | 'cpp' } {
  const m = String(mode || 'realtime')
  if (m.endsWith('_cpp')) return { task_type: baseTaskType(m), executor: 'cpp' }
  return { task_type: baseTaskType(m), executor: 'python' }
}

const form = reactive({
  task_name: '',
  task_mode: 'realtime_cpp' as string,
  device_ids: [] as string[],
  model_ids: [] as number[],
  schedule_policy: 'local' as 'local' | 'auto' | 'node',
  prefer_gpu: true,
  target_node_id: undefined as number | undefined,
  extract_interval: undefined as number | undefined,
  motion_gate_enabled: false,
  cron_expression: '',
  patrol_interval_sec: undefined as number | undefined,
  alert_event_enabled: false,
})

const extractIntervalText = computed({
  get: () => form.extract_interval == null ? '' : String(form.extract_interval),
  set: (val: string) => {
    form.extract_interval = val === '' ? undefined : Number(val)
  },
})

const patrolIntervalText = computed({
  get: () => form.patrol_interval_sec == null ? '' : String(form.patrol_interval_sec),
  set: (val: string) => {
    form.patrol_interval_sec = val === '' ? undefined : Number(val)
  },
})

const filteredDeviceOptions = computed(() => {
  const q = deviceSearch.value.trim().toLowerCase()
  if (!q)
    return deviceOptions.value
  return deviceOptions.value.filter(d => d.label.toLowerCase().includes(q))
})

const filteredModelOptions = computed(() => {
  const q = modelSearch.value.trim().toLowerCase()
  if (!q)
    return modelOptions.value
  return modelOptions.value.filter(m => m.label.toLowerCase().includes(q))
})

const selectedDeviceLabel = computed(() => {
  if (!form.device_ids.length)
    return ''
  const labels = form.device_ids
    .map(id => deviceOptions.value.find(d => d.value === id)?.label || id)
  if (labels.length <= 2)
    return labels.join('、')
  return `${labels.slice(0, 2).join('、')} 等 ${labels.length} 个`
})

const selectedModelLabel = computed(() => {
  if (!form.model_ids.length)
    return ''
  const labels = form.model_ids
    .map(id => modelOptions.value.find(m => m.value === id)?.label || String(id))
  if (labels.length <= 2)
    return labels.join('、')
  return `${labels.slice(0, 2).join('、')} 等 ${labels.length} 个`
})

const selectedNodeLabel = computed(() => {
  if (!form.target_node_id)
    return ''
  return nodeOptions.value.find(n => n.value === form.target_node_id)?.label || String(form.target_node_id)
})

function resetForm() {
  form.task_name = ''
  form.task_mode = 'realtime_cpp'
  form.device_ids = []
  form.model_ids = []
  form.schedule_policy = 'local'
  form.prefer_gpu = true
  form.target_node_id = undefined
  form.extract_interval = undefined
  form.motion_gate_enabled = false
  form.cron_expression = ''
  form.patrol_interval_sec = undefined
  form.alert_event_enabled = false
}

async function loadOptions() {
  try {
    const { data } = await getDeviceList({ pageNo: 1, pageSize: 1000 })
    deviceOptions.value = data.map(d => ({
      label: d.name || d.id,
      value: d.id,
    }))
  }
  catch {
    deviceOptions.value = []
  }

  try {
    const res = await getModelPage({ pageNo: 1, pageSize: 200 })
    const { list } = parseListResponse<any>(res, ['data'])
    modelOptions.value = list.map((m: any) => ({
      label: m.name || String(m.id),
      value: m.id,
    }))
  }
  catch {
    modelOptions.value = []
  }

  try {
    const res = await getNodePage({ pageNo: 1, pageSize: 200, status: 'online' })
    const { list } = parseListResponse<any>(res, ['list', 'data'])
    nodeOptions.value = list
      .filter((n: any) => ['compute', 'gpu', 'hybrid'].includes(n.nodeRole))
      .map((n: any) => ({
        label: `${n.name} (${n.host})`,
        value: n.id,
      }))
  }
  catch {
    nodeOptions.value = []
  }
}

function isDeviceSelected(deviceId: string) {
  return form.device_ids.includes(deviceId)
}

function toggleDevice(deviceId: string) {
  const idx = form.device_ids.indexOf(deviceId)
  if (idx >= 0)
    form.device_ids.splice(idx, 1)
  else
    form.device_ids.push(deviceId)
}

function isModelSelected(modelId: number) {
  return form.model_ids.includes(modelId)
}

function toggleModel(modelId: number) {
  const idx = form.model_ids.indexOf(modelId)
  if (idx >= 0)
    form.model_ids.splice(idx, 1)
  else
    form.model_ids.push(modelId)
}

function handleNodeConfirm({ value }: { value: number }) {
  form.target_node_id = value
}

async function handleSubmit() {
  if (!form.task_name.trim()) {
    toast.warning('请输入任务名称')
    return
  }
  if (!form.device_ids.length) {
    toast.warning('请选择关联摄像头')
    return
  }
  if (!form.model_ids.length) {
    toast.warning('请选择关联模型')
    return
  }
  if (form.schedule_policy === 'node' && !form.target_node_id) {
    toast.warning('请选择目标节点')
    return
  }
  if (baseTaskType(form.task_mode) === 'snap' && !form.cron_expression.trim()) {
    toast.warning('请输入 Cron 表达式')
    return
  }

  const mapped = fromTaskMode(form.task_mode)
  const payload: Record<string, any> = {
    task_name: form.task_name.trim(),
    task_type: mapped.task_type,
    executor: mapped.executor,
    device_ids: form.device_ids,
    model_ids: form.model_ids,
    schedule_policy: form.schedule_policy,
    alert_event_enabled: form.alert_event_enabled,
    is_enabled: false,
  }

  if (form.schedule_policy === 'auto')
    payload.prefer_gpu = form.prefer_gpu
  if (form.schedule_policy === 'node')
    payload.target_node_id = form.target_node_id
  else
    payload.target_node_id = null

  if (baseTaskType(form.task_mode) === 'realtime' && form.extract_interval != null)
    payload.extract_interval = form.extract_interval
  if (baseTaskType(form.task_mode) === 'realtime') {
    payload.motion_gate_enabled = form.motion_gate_enabled
    payload.motion_gate_config = form.motion_gate_enabled
      ? { preset: 'conservative' }
      : null
  }
  if (baseTaskType(form.task_mode) === 'snap')
    payload.cron_expression = form.cron_expression.trim()
  if (baseTaskType(form.task_mode) === 'patrol' && form.patrol_interval_sec != null)
    payload.patrol_interval_sec = form.patrol_interval_sec

  submitting.value = true
  try {
    if (isEdit.value && taskId.value) {
      await updateAlgorithmTask(taskId.value, payload)
      toast.success('更新成功')
    }
    else {
      await createAlgorithmTask(payload as any)
      toast.success('创建成功')
    }
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
  isEdit.value = false
  taskId.value = null
  resetForm()
  await loadOptions()
  visible.value = true
}

async function openEdit(item: AlgorithmTask) {
  isEdit.value = true
  taskId.value = item.id
  resetForm()
  await loadOptions()
  form.task_name = item.task_name
  form.task_mode = toTaskMode(item.task_type, (item as any).executor)
  form.device_ids = [...(item.device_ids || [])]
  form.model_ids = [...(item.model_ids || [])]
  form.schedule_policy = item.schedule_policy || 'local'
  form.prefer_gpu = item.prefer_gpu !== false
  form.target_node_id = item.target_node_id ?? undefined
  form.extract_interval = item.extract_interval
  form.motion_gate_enabled = item.motion_gate_enabled === true
  form.cron_expression = item.cron_expression || ''
  form.patrol_interval_sec = (item as any).patrol_interval_sec
  form.alert_event_enabled = item.alert_event_enabled === true
  visible.value = true
}

defineExpose({ openCreate, openEdit })
</script>
