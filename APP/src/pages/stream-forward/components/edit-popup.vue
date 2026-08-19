<template>
  <wd-popup v-model="visible" position="bottom" custom-style="border-radius: 24rpx 24rpx 0 0; max-height: 90vh;">
    <view class="p-32rpx">
      <view class="mb-24rpx text-center text-32rpx font-semibold">
        {{ isEdit ? '编辑推流任务' : '新建推流任务' }}
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

        <view class="mb-24rpx">
          <view class="mb-12rpx text-26rpx text-[#666]">
            输出格式
          </view>
          <wd-radio-group v-model="form.output_format" type="button">
            <wd-radio value="rtmp">
              RTMP
            </wd-radio>
            <wd-radio value="rtsp">
              RTSP
            </wd-radio>
          </wd-radio-group>
        </view>

        <view class="mb-24rpx">
          <view class="mb-12rpx text-26rpx text-[#666]">
            输出质量
          </view>
          <wd-radio-group v-model="form.output_quality" type="button">
            <wd-radio value="low">
              低
            </wd-radio>
            <wd-radio value="medium">
              中
            </wd-radio>
            <wd-radio value="high">
              高
            </wd-radio>
          </wd-radio-group>
        </view>

        <view class="mb-24rpx">
          <view class="mb-12rpx text-26rpx text-[#666]">
            输出码率
          </view>
          <wd-input v-model="form.output_bitrate" placeholder="如 512k、1M（留空自动）" clearable />
        </view>

        <view class="mb-24rpx">
          <view class="mb-12rpx text-26rpx text-[#666]">
            任务描述
          </view>
          <wd-textarea v-model="form.description" placeholder="可选" :maxlength="500" show-word-limit />
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
import type { StreamForwardTask } from '@/api/video/streamForward'
import { computed, reactive, ref } from 'vue'
import { useToast } from '@wot-ui/ui/components/wd-toast'
import { getDeviceList } from '@/api/video/camera'
import { getNodePage } from '@/api/video/node'
import {
  createStreamForwardTask,
  updateStreamForwardTask,
} from '@/api/video/streamForward'
import { parseListResponse } from '@/utils/listResponse'

const emit = defineEmits<{ success: [] }>()
const toast = useToast()
const visible = ref(false)
const isEdit = ref(false)
const taskId = ref<number | null>(null)
const submitting = ref(false)
const devicePickerVisible = ref(false)
const nodePickerVisible = ref(false)
const deviceOptions = ref<Array<{ label: string, value: string }>>([])
const nodeOptions = ref<Array<{ label: string, value: number }>>([])
const deviceSearch = ref('')

const filteredDeviceOptions = computed(() => {
  const q = deviceSearch.value.trim().toLowerCase()
  if (!q)
    return deviceOptions.value
  return deviceOptions.value.filter(d => d.label.toLowerCase().includes(q))
})

const form = reactive({
  task_name: '',
  device_ids: [] as string[],
  schedule_policy: 'local' as 'local' | 'auto' | 'node',
  prefer_gpu: true,
  target_node_id: undefined as number | undefined,
  output_format: 'rtmp' as 'rtmp' | 'rtsp',
  output_quality: 'high' as 'low' | 'medium' | 'high',
  output_bitrate: '',
  description: '',
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

const selectedNodeLabel = computed(() => {
  if (!form.target_node_id)
    return ''
  return nodeOptions.value.find(n => n.value === form.target_node_id)?.label || String(form.target_node_id)
})

function resetForm() {
  form.task_name = ''
  form.device_ids = []
  form.schedule_policy = 'local'
  form.prefer_gpu = true
  form.target_node_id = undefined
  form.output_format = 'rtmp'
  form.output_quality = 'high'
  form.output_bitrate = ''
  form.description = ''
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
    const res = await getNodePage({ pageNo: 1, pageSize: 200, status: 'online' })
    const { list } = parseListResponse<any>(res, ['list', 'data'])
    nodeOptions.value = list
      .filter((n: any) => {
        const fns = Array.isArray(n.functions) ? n.functions : String(n.nodeRole || '').split(',')
        return fns.includes('forward')
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
  if (form.schedule_policy === 'node' && !form.target_node_id) {
    toast.warning('请选择目标节点')
    return
  }

  const payload: Record<string, any> = {
    task_name: form.task_name.trim(),
    device_ids: form.device_ids,
    schedule_policy: form.schedule_policy,
    output_format: form.output_format,
    output_quality: form.output_quality,
    output_bitrate: form.output_bitrate || undefined,
    description: form.description || undefined,
    is_enabled: false,
  }
  if (form.schedule_policy === 'auto')
    payload.prefer_gpu = form.prefer_gpu
  if (form.schedule_policy === 'node')
    payload.target_node_id = form.target_node_id
  else
    payload.target_node_id = null

  submitting.value = true
  try {
    if (isEdit.value && taskId.value) {
      const res = await updateStreamForwardTask(taskId.value, payload)
      const syncAction = (res as any)?.sync_action
      if (syncAction === 'full_restart')
        toast.success('更新成功，任务已全量重启')
      else if (syncAction === 'rebalance')
        toast.success('更新成功，正在重平衡部署')
      else
        toast.success('更新成功')
    }
    else {
      await createStreamForwardTask(payload as any)
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

async function openEdit(item: StreamForwardTask) {
  isEdit.value = true
  taskId.value = item.id
  resetForm()
  await loadOptions()
  form.task_name = item.task_name
  form.device_ids = [...(item.device_ids || [])]
  form.schedule_policy = item.schedule_policy || 'local'
  form.prefer_gpu = item.prefer_gpu !== false
  form.target_node_id = item.target_node_id ?? undefined
  form.output_format = item.output_format || 'rtmp'
  form.output_quality = item.output_quality || 'high'
  form.output_bitrate = item.output_bitrate || ''
  form.description = item.description || ''
  visible.value = true
}

defineExpose({ openCreate, openEdit })
</script>
