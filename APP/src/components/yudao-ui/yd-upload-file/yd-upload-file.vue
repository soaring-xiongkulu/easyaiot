<template>
  <view class="w-full">
    <yd-upload
      :model-value="list"
      :accept="accept"
      :multiple="!isSingle"
      :limit="limit"
      :directory="directory"
      :disabled="disabled"
      :file-size="fileSize"
      :file-type="fileType"
      @update:model-value="handleUpdate"
      @uploaded="emit('uploaded', $event)"
      @success="emit('success', $event)"
      @fail="emit('fail', $event)"
      @remove="emit('remove', $event)"
    >
      <!-- 自定义占位：文件上传用加号 + 数量，替代默认的相机图标 -->
      <view class="yd-upload-file__trigger">
        <wd-icon name="plus" custom-class="yd-upload-file__icon" />
        <text class="yd-upload-file__num">{{ list.length }}/{{ limit }}</text>
      </view>
    </yd-upload>
    <view v-if="isShowTip && tipText" class="mt-8rpx text-22rpx text-[#999]">
      <text>{{ tipText }}</text>
    </view>
  </view>
</template>

<script lang="ts" setup>
import type { UploadFileType } from '@wot-ui/ui/components/wd-upload/types'
import { computed } from 'vue'

// 文件上传：对外 v-model 兼容单文件 string 与多文件 string[]，对齐 PC 端 UploadFile
const props = withDefaults(defineProps<{
  modelValue?: string | string[] // 已上传文件的访问地址（单文件 string / 多文件 string[]）
  directory?: string // 上传目录
  accept?: UploadFileType // 文件类型，默认 all（任意文件）
  limit?: number // 最大上传数量
  disabled?: boolean // 是否禁用
  fileSize?: number // 文件大小限制（MB），不传则不限制
  fileType?: string[] // 文件扩展名限制，为空则不限制
  isShowTip?: boolean // 是否显示大小/格式提示
}>(), {
  modelValue: () => [],
  directory: '',
  accept: 'all',
  limit: 5,
  disabled: false,
  // fileSize 默认不限制；fileType 默认不限制（移动端拿不到扩展名时易误拒）
  fileType: () => [],
  isShowTip: true,
})

const emit = defineEmits<{
  'update:modelValue': [value: string | string[]]
  'uploaded': [value: string]
  'success': [value: any]
  'fail': [value: any]
  'remove': [value: any]
}>()

// 提示文案：大小/格式限制（都为空时不展示）
const tipText = computed(() => {
  const parts: string[] = []
  if (props.fileSize) {
    parts.push(`大小不超过 ${props.fileSize}MB`)
  }
  if (props.fileType.length) {
    parts.push(`格式为 ${props.fileType.join('/')}`)
  }
  return parts.join('，')
})

// 单文件模式：limit 为 1 或外部传入 string
const isSingle = computed(() => props.limit === 1 || typeof props.modelValue === 'string')

// 归一化为数组，适配内核 yd-upload
const list = computed<string[]>(() => {
  if (Array.isArray(props.modelValue)) {
    return props.modelValue
  }
  return props.modelValue ? [props.modelValue] : []
})

/** 按对外类型回传（单文件 string / 多文件 string[]） */
function handleUpdate(urls: string[]) {
  if (isSingle.value) {
    emit('update:modelValue', urls[0] || '')
  } else {
    emit('update:modelValue', urls)
  }
}
</script>

<style lang="scss" scoped>
.yd-upload-file__trigger {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 160rpx;
  height: 160rpx;
  border: 1rpx dashed #dcdee0;
  border-radius: 12rpx;
  background: #f7f8fa;
}

.yd-upload-file__num {
  margin-top: 8rpx;
  font-size: 24rpx;
  color: #969799;
}

:deep(.yd-upload-file__icon) {
  font-size: 56rpx;
  color: #c8c9cc;
}
</style>
