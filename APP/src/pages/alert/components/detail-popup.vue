<template>
  <wd-popup v-model="visible" position="bottom" custom-style="border-radius: 24rpx 24rpx 0 0; max-height: 85vh;">
    <view class="p-32rpx">
      <view class="mb-24rpx text-center text-32rpx font-semibold">
        告警详情
      </view>
      <view v-if="record" class="max-h-70vh overflow-y-auto">
        <image
          v-if="displayImageUrl"
          :src="displayImageUrl"
          mode="widthFix"
          class="mb-24rpx w-full rounded-12rpx"
          @click="previewImage"
        />

        <view class="mb-16rpx text-34rpx font-semibold text-[#333]">
          {{ formatAlertListTitle(record) }}
        </view>

        <!-- 大模型研判 -->
        <view
          v-if="record.llm_judge_status"
          class="mb-24rpx rounded-12rpx border p-24rpx"
          :class="llmJudgeSectionClass"
        >
          <view class="mb-12rpx flex items-center gap-12rpx">
            <text class="text-26rpx font-semibold">AI 研判</text>
            <wd-tag :type="llmJudgeTagType" size="small" plain>
              {{ formatLlmJudgeStatus(record.llm_judge_status) }}
            </wd-tag>
          </view>
          <view v-if="llmJudgeReason" class="text-26rpx leading-relaxed text-[#555]">
            {{ llmJudgeReason }}
          </view>
          <view v-else class="text-26rpx text-[#999]">
            {{ llmJudgeHint }}
          </view>
        </view>

        <!-- 告警录像 -->
        <view class="mb-24rpx rounded-12rpx bg-[#f7f8f9] p-24rpx">
          <view class="mb-16rpx flex items-center justify-between">
            <view class="text-28rpx font-semibold text-[#333]">
              告警录像
            </view>
            <wd-tag v-if="isSnapTask" type="warning" plain>
              抓拍无录像
            </wd-tag>
          </view>

          <view v-if="isSnapTask" class="text-26rpx text-[#999]">
            抓拍类算法任务不产生告警录像
          </view>
          <template v-else>
            <LiveStreamPlayer
              v-if="videoUrl"
              :play-url="videoUrl"
              :vod-mode="isVodVideo"
              height="360rpx"
            />
            <view v-else-if="videoLoading" class="flex h-200rpx items-center justify-center text-26rpx text-[#999]">
              正在加载录像...
            </view>
            <view v-else-if="videoError" class="text-26rpx text-[#faad14]">
              {{ videoError }}
            </view>

            <wd-button
              v-if="!videoUrl && !videoLoading"
              type="primary"
              size="small"
              block
              @click="loadVideo"
            >
              加载告警录像
            </wd-button>
            <wd-button
              v-else-if="videoUrl"
              plain
              size="small"
              block
              class="mt-12rpx"
              @click="loadVideo"
            >
              重新加载
            </wd-button>
          </template>
        </view>

        <view class="rounded-12rpx bg-[#f7f8f9] p-24rpx">
          <view v-for="row in detailRows" :key="row.label" class="mb-16rpx flex text-28rpx last:mb-0">
            <view class="w-160rpx flex-shrink-0 text-[#999]">
              {{ row.label }}
            </view>
            <view class="flex-1 break-all text-[#333]">
              {{ row.value }}
            </view>
          </view>
        </view>
      </view>
    </view>
  </wd-popup>
</template>

<script lang="ts" setup>
import type { AlertRecord } from '@/api/video/alert'
import { computed, ref, watch } from 'vue'
import { useToast } from '@wot-ui/ui/components/wd-toast'
import {
  formatAlertEvent,
  formatAlertListTitle,
  formatLlmJudgeConclusion,
  formatLlmJudgeStatus,
  getLlmJudgeTagType,
  getTaskTypeText,
  isSnapAlertTask,
} from '@/utils/video/alertDisplay'
import { resolveAlertRecordVideoUrl, isVodPlaybackUrl } from '@/utils/video/alertRecord'
import { resolveAlertImageDisplayUrl } from '@/utils/mediaDisplay'
import { formatDateTime } from '@/utils/date'
import LiveStreamPlayer from '@/components/live-stream-player.vue'

const toast = useToast()
const visible = ref(false)
const record = ref<AlertRecord | null>(null)
const videoUrl = ref('')
const videoLoading = ref(false)
const videoError = ref('')

const isSnapTask = computed(() => record.value ? isSnapAlertTask(record.value) : false)
const isVodVideo = computed(() => isVodPlaybackUrl(videoUrl.value))

const displayImageUrl = computed(() => resolveAlertImageDisplayUrl(record.value?.image_url))

const LLM_JUDGE_HINTS: Record<string, string> = {
  not_sampled: '该告警未命中比例抽检，未进入大模型研判队列',
  pending: '已进入大模型研判队列，结论产出后自动回挂本告警',
  confirmed: '大模型确认告警事件成立',
  rejected: '大模型判定该告警为误报',
  error: '大模型研判执行失败，请检查模型服务',
  rate_limited: '命中比例抽检但处于最小研判间隔内，本次跳过',
  skipped: '因规则配置被跳过，未进入研判队列',
}

const llmJudgeTagType = computed(() => getLlmJudgeTagType(record.value?.llm_judge_status))
const llmJudgeSectionClass = computed(() => {
  const status = record.value?.llm_judge_status
  if (status === 'confirmed')
    return 'border-[#95de64] bg-[#f6ffed]'
  if (status === 'rejected' || status === 'rate_limited' || status === 'skipped')
    return 'border-[#ffe58f] bg-[#fffbe6]'
  if (status === 'error')
    return 'border-[#ffccc7] bg-[#fff2f0]'
  return 'border-[#d9d9d9] bg-[#fafafa]'
})
const llmJudgeReason = computed(() => {
  const status = record.value?.llm_judge_status
  if (status === 'confirmed' || status === 'rejected') {
    return formatLlmJudgeConclusion(record.value?.llm_judge_detail)
  }
  return ''
})
const llmJudgeHint = computed(() => {
  const status = record.value?.llm_judge_status
  return (status && LLM_JUDGE_HINTS[status]) || '该告警已进入大模型研判链路'
})

const detailRows = computed(() => {
  if (!record.value)
    return []
  const r = record.value
  return [
    { label: '告警时间', value: formatDateTime(r.time) || '-' },
    { label: '设备', value: r.device_name || r.device_id || '-' },
    { label: '算法任务', value: r.task_name || '-' },
    { label: '任务类型', value: getTaskTypeText(r.task_type) },
    { label: '告警事件', value: formatAlertEvent(r.event) },
    { label: '告警对象', value: r.object || '-' },
    { label: '业务标签', value: r.business_tags?.join('、') || '-' },
  ]
})

watch(visible, (val) => {
  if (!val) {
    videoUrl.value = ''
    videoError.value = ''
    videoLoading.value = false
  }
})

function previewImage() {
  if (displayImageUrl.value) {
    uni.previewImage({ urls: [displayImageUrl.value] })
  }
}

async function loadVideo() {
  if (!record.value || isSnapTask.value)
    return
  if (!record.value.device_id || !record.value.time) {
    videoError.value = '缺少设备或时间信息，无法查询录像'
    return
  }

  videoLoading.value = true
  videoError.value = ''
  videoUrl.value = ''
  try {
    const url = await resolveAlertRecordVideoUrl(record.value)
    if (url) {
      videoUrl.value = url
    }
    else {
      videoError.value = '未找到匹配的告警录像，请稍后重试'
    }
  }
  catch (e: any) {
    videoError.value = e?.msg || e?.message || '录像加载失败'
    toast.error(videoError.value)
  }
  finally {
    videoLoading.value = false
  }
}

function open(item: AlertRecord) {
  record.value = item
  visible.value = true
  videoUrl.value = ''
  videoError.value = ''
  if (!isSnapAlertTask(item))
    loadVideo()
}

defineExpose({ open })
</script>
