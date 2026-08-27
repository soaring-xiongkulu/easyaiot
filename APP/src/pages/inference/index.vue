<template>
  <view class="yd-page-container yd-page-container-paging">
    <wd-navbar title="模型推理" placeholder safe-area-inset-top fixed>
      <template #right>
        <AppNavUserButton />
      </template>
    </wd-navbar>

    <!-- 推理工作台 -->
    <view class="work-card mx-24rpx mt-16rpx p-28rpx">
      <view class="card-head">
        <view class="section-bar" />
        <text class="card-title">图片推理</text>
      </view>

      <!-- 选择模型 -->
      <view class="field-label">
        选择模型
      </view>
      <view class="model-row" hover-class="model-row--pressed" :hover-stay-time="60" @click="pickerVisible = true">
        <text class="model-row-text" :class="{ 'model-row-text--placeholder': !selectedModelLabel }">
          {{ selectedModelLabel || '请选择模型' }}
        </text>
        <wd-icon name="arrow-right" size="15px" color="#c0c7d3" />
      </view>
      <wd-picker
        v-model:visible="pickerVisible"
        :model-value="selectedModelValue"
        :columns="modelOptions"
        label-key="label"
        value-key="value"
        @confirm="handleModelConfirm"
      />

      <!-- 输入图片 -->
      <view class="field-label">
        输入图片
      </view>
      <view
        class="upload-zone"
        hover-class="upload-zone--pressed"
        :hover-stay-time="60"
        @click="chooseImage"
      >
        <image
          v-if="inputImagePath"
          :src="inputImagePath"
          mode="aspectFit"
          class="h-full w-full rounded-24rpx"
        />
        <view v-else class="center flex-col">
          <view class="i-carbon-image text-64rpx text-[#7fa9ff]" />
          <view class="mt-12rpx text-26rpx text-[#98a2b3]">
            点击选择图片
          </view>
        </view>
      </view>

      <!-- 开始推理 -->
      <view
        class="run-btn"
        :class="{ 'run-btn--disabled': !canInfer }"
        @click="handleInfer"
      >
        <wd-loading v-if="inferencing" size="16px" color="#ffffff" />
        <wd-icon v-else name="thunderbolt" size="30rpx" color="#ffffff" />
        <text>{{ inferencing ? '推理中…' : '开始推理' }}</text>
      </view>

      <ResultPanel
        :input-image-url="displayInputUrl"
        :result-image-url="displayResultUrl"
        :detection-count="detectionCount"
        :average-confidence="averageConfidence"
      />
    </view>

    <!-- 历史记录 -->
    <view class="history-title mx-24rpx mb-16rpx mt-28rpx">
      推理历史
    </view>

    <z-paging
      ref="pagingRef"
      v-model="historyList"
      :fixed="false"
      class="min-h-0 flex-1"
      :default-page-size="10"
      empty-view-text="暂无推理记录"
      @query="queryHistory"
    >
      <view class="px-24rpx pb-24rpx">
        <view
          v-for="item in historyList"
          :key="item.id"
          class="hist-card"
          :class="{ 'hist-card--active': activeHistoryId === item.id }"
          hover-class="hist-card--pressed"
          :hover-stay-time="60"
          @click="handleHistoryClick(item)"
        >
          <image
            v-if="getHistoryThumb(item)"
            :src="getHistoryThumb(item)"
            mode="aspectFill"
            class="hist-thumb"
          />
          <view v-else class="hist-thumb hist-thumb--empty">
            <view class="i-carbon-image text-44rpx text-[#b3bccb]" />
          </view>
          <view class="min-w-0 flex-1">
            <view class="truncate text-28rpx font-semibold" style="color: var(--app-text-1, #10131a)">
              {{ item.model_name || `模型 #${item.model_id}` }}
            </view>
            <view class="mt-6rpx truncate text-23rpx" style="color: var(--app-text-3, #98a2b3)">
              {{ formatDateTime(item.create_time) }}
            </view>
            <view class="mt-10rpx">
              <text class="status-chip">{{ item.status || '完成' }}</text>
            </view>
          </view>
        </view>
      </view>
    </z-paging>
  </view>
</template>

<script lang="ts" setup>
import type { InferenceTask } from '@/api/model/inference'
import type { ModelInfo } from '@/api/model'
import { computed, onMounted, ref } from 'vue'
import { useToast } from '@wot-ui/ui/components/wd-toast'
import { getModelPage } from '@/api/model'
import {
  getInferenceTaskDetail,
  getInferenceTasks,
  isPresetModelId,
  PRESET_MODEL_OPTIONS,
  runImageInference,
} from '@/api/model/inference'
import AppNavUserButton from '@/components/app-nav-user-button.vue'
import { formatDateTime } from '@/utils/date'
import { parseListResponse } from '@/utils/listResponse'
import { parseInferenceHistoryItem, parseInferenceResult } from '@/utils/model/inferenceResult'
import ResultPanel from './components/result-panel.vue'

definePage({
  style: {
    navigationStyle: 'custom',
  },
})

const toast = useToast()
const models = ref<ModelInfo[]>([])
const pickerVisible = ref(false)
const selectedModelValue = ref<string>('')
const selectedModelId = ref<string | number>('')
const inputImagePath = ref('')
const displayInputUrl = ref('')
const displayResultUrl = ref('')
const detectionCount = ref<number | undefined>()
const averageConfidence = ref<number | undefined>()
const inferencing = ref(false)
const historyList = ref<InferenceTask[]>([])
const pagingRef = ref<any>()
const activeHistoryId = ref<number | null>(null)

const modelOptions = computed(() => {
  const preset = PRESET_MODEL_OPTIONS.map(o => ({ value: o.value, label: o.label }))
  const custom = models.value.map(m => ({ value: String(m.id), label: `${m.name} (v${m.version || '-'})` }))
  return preset.concat(custom)
})

const selectedModelLabel = computed(() => {
  return modelOptions.value.find(o => o.value === selectedModelValue.value)?.label || ''
})

const canInfer = computed(() => !!selectedModelId.value && !!inputImagePath.value && !inferencing.value)

function applyResultView(view: ReturnType<typeof parseInferenceResult>, fallbackInput?: string) {
  displayInputUrl.value = view.inputImageUrl || fallbackInput || displayInputUrl.value
  displayResultUrl.value = view.resultImageUrl || ''
  detectionCount.value = view.detectionCount
  averageConfidence.value = view.averageConfidence
}

async function loadModels() {
  try {
    const res = await getModelPage({ pageNo: 1, pageSize: 200 })
    const { list } = parseListResponse<ModelInfo>(res, ['data'])
    models.value = list
  } catch {
    models.value = []
  }
}

function handleModelConfirm({ value }: { value: string[] }) {
  selectedModelValue.value = value[0] || ''
  selectedModelId.value = selectedModelValue.value
}

function chooseImage() {
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: (res) => {
      inputImagePath.value = res.tempFilePaths[0]
      displayInputUrl.value = res.tempFilePaths[0]
      displayResultUrl.value = ''
      detectionCount.value = undefined
      averageConfidence.value = undefined
      activeHistoryId.value = null
    },
  })
}

async function handleInfer() {
  if (!canInfer.value)
    return
  inferencing.value = true
  displayInputUrl.value = inputImagePath.value
  try {
    const res = await runImageInference(selectedModelId.value, inputImagePath.value)
    const view = parseInferenceResult(res)
    applyResultView(view, inputImagePath.value)
    if (view.resultImageUrl) {
      toast.success(`推理完成，检测到 ${view.detectionCount ?? 0} 个目标`)
    } else {
      toast.success('推理完成')
    }
    activeHistoryId.value = view.recordId ?? null
    pagingRef.value?.reload()
  } catch {
    toast.error('推理失败')
  } finally {
    inferencing.value = false
  }
}

function getHistoryThumb(item: InferenceTask) {
  const view = parseInferenceHistoryItem(item)
  return view.resultImageUrl || view.inputImageUrl || ''
}

async function queryHistory(pageNo: number, pageSize: number) {
  try {
    const params: Record<string, any> = { pageNo, pageSize }
    if (selectedModelId.value && !isPresetModelId(selectedModelId.value)) {
      params.model_id = Number(selectedModelId.value)
    }
    const res = await getInferenceTasks(params)
    const { list, total } = parseListResponse<InferenceTask>(res, ['data', 'list'])
    pagingRef.value?.completeByTotal(list, total)
  } catch {
    pagingRef.value?.complete(false)
  }
}

async function handleHistoryClick(item: InferenceTask) {
  activeHistoryId.value = item.id
  try {
    const detail = await getInferenceTaskDetail(item.id)
    const view = parseInferenceResult({ ...item, ...detail })
    applyResultView(view)
    uni.pageScrollTo?.({ scrollTop: 0, duration: 200 })
  } catch {
    const view = parseInferenceHistoryItem(item)
    applyResultView(view)
  }
}

onMounted(() => {
  loadModels()
})
</script>

<style lang="scss" scoped>
.work-card {
  background: var(--app-card-bg, #ffffff);
  border-radius: 28rpx;
  box-shadow: var(--app-card-shadow);
}

.card-head {
  display: flex;
  align-items: center;
  gap: 14rpx;
  margin-bottom: 26rpx;
}

.section-bar {
  width: 8rpx;
  height: 30rpx;
  border-radius: 4rpx;
  background: linear-gradient(180deg, #4a8bff, #2f6bff);
}

.card-title {
  font-size: 30rpx;
  font-weight: 700;
  color: var(--app-text-1, #10131a);
}

.field-label {
  margin-bottom: 12rpx;
  font-size: 24rpx;
  color: var(--app-text-3, #98a2b3);
}

.model-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14rpx;
  margin-bottom: 24rpx;
  padding: 22rpx 24rpx;
  border-radius: 18rpx;
  background: #f7f9fd;
  transition: opacity 0.12s ease;

  &--pressed {
    opacity: 0.85;
  }
}

.model-row-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 27rpx;
  font-weight: 600;
  color: var(--app-text-1, #10131a);

  &--placeholder {
    color: var(--app-text-3, #98a2b3);
    font-weight: 400;
  }
}

.upload-zone {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 280rpx;
  margin-bottom: 28rpx;
  border: 2rpx dashed #c9d8ff;
  border-radius: 24rpx;
  background: linear-gradient(180deg, #f7faff 0%, #eff4ff 100%);
  transition: opacity 0.12s ease;

  &--pressed {
    opacity: 0.85;
  }
}

.run-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
  height: 84rpx;
  border-radius: 999rpx;
  color: #ffffff;
  font-size: 29rpx;
  font-weight: 700;
  background: linear-gradient(135deg, #4a8bff, #2f6bff);
  box-shadow: 0 10rpx 24rpx rgba(47, 107, 255, 0.3);
  transition: all 0.15s ease;

  &:active {
    transform: scale(0.98);
  }

  &--disabled {
    opacity: 0.45;
    box-shadow: none;

    &:active {
      transform: none;
    }
  }
}

.history-title {
  font-size: 28rpx;
  font-weight: 700;
  color: var(--app-text-1, #10131a);
}

.hist-card {
  display: flex;
  gap: 18rpx;
  margin-bottom: 16rpx;
  padding: 20rpx 22rpx;
  border: 3rpx solid transparent;
  background: var(--app-card-bg, #ffffff);
  border-radius: 26rpx;
  box-shadow: var(--app-card-shadow);
  transition: all 0.12s ease;

  &--pressed {
    transform: scale(0.98);
    opacity: 0.92;
  }

  &--active {
    border-color: rgba(47, 107, 255, 0.55);
    background: #f7faff;
  }
}

.hist-thumb {
  width: 110rpx;
  height: 110rpx;
  border-radius: 18rpx;
  background: #f0f2f6;
  flex-shrink: 0;

  &--empty {
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #f5f8ff 0%, #eef2fa 100%);
  }
}

.status-chip {
  padding: 2rpx 14rpx;
  border-radius: 999rpx;
  font-size: 20rpx;
  font-weight: 600;
  color: #0fa36e;
  background: #e6f7f1;
}
</style>
