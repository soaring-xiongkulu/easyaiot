<template>
  <wd-popup
    v-model="visible"
    position="bottom"
    custom-style="border-radius: 24rpx 24rpx 0 0; height: 50%"
    safe-area-inset-bottom
    @close="visible = false"
  >
    <view class="h-full flex flex-col p-32rpx">
      <!-- 标题 -->
      <view class="mb-32rpx flex items-center justify-between">
        <view class="text-36rpx text-[#333] font-semibold">
          消息详情
        </view>
        <view class="p-8rpx" @click="visible = false">
          <wd-icon name="close" size="20px" color="#999" />
        </view>
      </view>

      <!-- 详情内容 -->
      <view v-if="formData" class="flex flex-1 flex-col overflow-hidden space-y-24rpx">
        <view class="flex items-start">
          <text class="w-160rpx shrink-0 text-28rpx text-[#999]">发送人</text>
          <text class="text-28rpx text-[#333]">{{ formData.templateNickname }}</text>
        </view>
        <view class="flex items-start">
          <text class="w-160rpx shrink-0 text-28rpx text-[#999]">发送时间</text>
          <text class="text-28rpx text-[#333]">{{ formatDateTime(formData.createTime) }}</text>
        </view>
        <view class="flex items-start">
          <text class="w-160rpx shrink-0 text-28rpx text-[#999]">消息类型</text>
          <text class="text-28rpx text-[#333]">
            {{ getDictLabel(DICT_TYPE.SYSTEM_NOTIFY_TEMPLATE_TYPE, formData.templateType) }}
          </text>
        </view>
        <view class="flex items-start">
          <text class="w-160rpx shrink-0 text-28rpx text-[#999]">是否已读</text>
          <wd-tag v-if="formData.readStatus" type="success" variant="plain">
            已读
          </wd-tag>
          <wd-tag v-else type="warning" variant="plain">
            未读
          </wd-tag>
        </view>
        <view v-if="formData.readStatus" class="flex items-start">
          <text class="w-160rpx shrink-0 text-28rpx text-[#999]">阅读时间</text>
          <text class="text-28rpx text-[#333]">{{ formatDateTime(formData.readTime) || '-' }}</text>
        </view>
        <view class="flex flex-1 flex-col overflow-hidden">
          <text class="mb-12rpx w-160rpx shrink-0 text-28rpx text-[#999]">消息内容</text>
          <view class="flex-1 rounded-12rpx bg-[#f5f5f5] p-24rpx">
            <text class="text-28rpx text-[#333]">{{ formData.templateContent }}</text>
          </view>
        </view>

        <!-- 工作流 deepLink：flow://instance/{processInstanceId}?taskId={taskId} → 跳审批详情 -->
        <wd-button v-if="flowLink" block type="primary" class="shrink-0" @click="handleGoFlow">
          去处理
        </wd-button>
      </view>
    </view>
  </wd-popup>
</template>

<script lang="ts" setup>
import type { NotifyMessage } from '@/api/system/notify/message'
import { computed, ref } from 'vue'
import { parseFlowDeepLink } from '@/api/flow'
import { getDictLabel } from '@/hooks/useDict'
import { DICT_TYPE } from '@/utils/constants'
import { formatDateTime } from '@/utils/date'

const visible = ref(false) // 详情弹窗显示状态
const formData = ref<NotifyMessage>() // 详情数据

/** 解析工作流 deepLink（无则不展示“去处理”） */
const flowLink = computed(() => parseFlowDeepLink(formData.value?.templateContent))

function handleGoFlow() {
  if (!flowLink.value) return
  const { processInstanceId, taskId } = flowLink.value
  visible.value = false
  uni.navigateTo({
    url: `/pages/flow/detail/index?id=${processInstanceId}${taskId ? `&taskId=${taskId}` : ''}`,
  })
}

/** 打开弹窗 */
function open(data: NotifyMessage) {
  formData.value = data
  visible.value = true
}

/** 关闭弹窗 */
function close() {
  visible.value = false
}

defineExpose({ open, close })
</script>
