<template>
  <wd-popup v-model="visible" position="bottom" custom-style="border-radius: 24rpx 24rpx 0 0; max-height: 80vh;">
    <view class="p-32rpx">
      <view class="mb-24rpx text-center text-32rpx font-semibold">
        任务详情
      </view>
      <view v-if="task" class="max-h-60vh overflow-y-auto">
        <view class="mb-24rpx flex items-center justify-between">
          <view class="text-34rpx font-semibold text-[#333]">
            {{ task.task_name }}
          </view>
          <wd-tag :type="task.is_enabled ? 'success' : 'default'" plain>
            {{ task.is_enabled ? '运行中' : '已停止' }}
          </wd-tag>
        </view>

        <view class="rounded-12rpx bg-[#f7f8f9] p-24rpx">
          <view v-for="row in detailRows" :key="row.label" class="mb-16rpx flex text-28rpx last:mb-0">
            <view class="w-180rpx flex-shrink-0 text-[#999]">
              {{ row.label }}
            </view>
            <view class="flex-1 break-all text-[#333]">
              {{ row.value }}
            </view>
          </view>
        </view>

        <view class="mt-32rpx flex gap-24rpx">
          <wd-button
            v-if="!task.is_enabled"
            class="flex-1"
            type="primary"
            :loading="actionLoading"
            @click="handleStart"
          >
            启动
          </wd-button>
          <wd-button
            v-else
            class="flex-1"
            type="warning"
            :loading="actionLoading"
            @click="handleStop"
          >
            停止
          </wd-button>
          <wd-button
            class="flex-1"
            plain
            :loading="actionLoading"
            @click="handleRestart"
          >
            重启
          </wd-button>
        </view>

        <view class="mt-16rpx flex gap-16rpx">
          <wd-button class="flex-1" plain :disabled="task.is_enabled" @click="handleEdit">
            编辑
          </wd-button>
          <wd-button class="flex-1" type="danger" plain :disabled="task.is_enabled" @click="handleDelete">
            删除
          </wd-button>
        </view>
      </view>
    </view>
  </wd-popup>
</template>

<script lang="ts" setup>
import type { AlgorithmTask } from '@/api/video/algorithm'
import { computed, ref } from 'vue'
import { useToast } from '@wot-ui/ui/components/wd-toast'
import {
  deleteAlgorithmTask,
  getAlgorithmTask,
  getAlgorithmTaskTypeText,
  restartAlgorithmTask,
  startAlgorithmTask,
  stopAlgorithmTask,
} from '@/api/video/algorithm'

const emit = defineEmits<{ refresh: [], edit: [task: AlgorithmTask] }>()
const toast = useToast()
const visible = ref(false)
const task = ref<AlgorithmTask | null>(null)
const actionLoading = ref(false)

const detailRows = computed(() => {
  if (!task.value)
    return []
  const t = task.value
  return [
    { label: '任务类型', value: getAlgorithmTaskTypeText(t.task_type, (t as any).executor) },
    { label: '关联设备', value: t.device_names?.join('、') || (t.device_ids?.length ? `${t.device_ids.length} 个设备` : '-') },
    { label: '关联模型', value: t.model_names || '-' },
    { label: '告警事件', value: t.alert_event_enabled ? '已启用' : '未启用' },
    { label: '累计帧数', value: String(t.total_frames ?? 0) },
    { label: '累计检测', value: String(t.total_detections ?? 0) },
    { label: '累计抓拍', value: String(t.total_captures ?? 0) },
    { label: '最近处理', value: t.last_process_time || '-' },
    { label: '异常原因', value: t.exception_reason || '-' },
  ]
})

async function reloadTask() {
  if (!task.value)
    return
  try {
    task.value = await getAlgorithmTask(task.value.id)
  }
  catch {
    // ignore
  }
}

async function handleStart() {
  if (!task.value)
    return
  actionLoading.value = true
  try {
    await startAlgorithmTask(task.value.id)
    toast.success('任务已启动')
    await reloadTask()
    emit('refresh')
  }
  catch {
    toast.error('启动失败')
  }
  finally {
    actionLoading.value = false
  }
}

async function handleStop() {
  if (!task.value)
    return
  actionLoading.value = true
  try {
    await stopAlgorithmTask(task.value.id)
    toast.success('任务已停止')
    await reloadTask()
    emit('refresh')
  }
  catch {
    toast.error('停止失败')
  }
  finally {
    actionLoading.value = false
  }
}

async function handleRestart() {
  if (!task.value)
    return
  actionLoading.value = true
  try {
    await restartAlgorithmTask(task.value.id)
    toast.success('任务已重启')
    await reloadTask()
    emit('refresh')
  }
  catch {
    toast.error('重启失败')
  }
  finally {
    actionLoading.value = false
  }
}

function handleEdit() {
  if (!task.value)
    return
  if (task.value.is_enabled) {
    toast.warning('请先停止任务再编辑')
    return
  }
  visible.value = false
  emit('edit', task.value)
}

function handleDelete() {
  if (!task.value)
    return
  if (task.value.is_enabled) {
    toast.warning('请先停止任务再删除')
    return
  }
  uni.showModal({
    title: '确认删除',
    content: `确定删除任务「${task.value.task_name}」吗？`,
    success: async (res) => {
      if (!res.confirm || !task.value)
        return
      actionLoading.value = true
      try {
        await deleteAlgorithmTask(task.value.id)
        toast.success('删除成功')
        visible.value = false
        emit('refresh')
      }
      catch {
        toast.error('删除失败')
      }
      finally {
        actionLoading.value = false
      }
    },
  })
}

async function open(item: AlgorithmTask) {
  visible.value = true
  task.value = item
  await reloadTask()
}

defineExpose({ open })
</script>
