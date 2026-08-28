<script lang="ts" setup>
/**
 * 节点卡片外壳：图标、标题（行内编辑）、摘要文案、删除按钮、状态徽标（查看器）
 * 具体节点组件（审批/抄送/延迟…）复用此外壳并挂接各自的配置抽屉。
 */
import { computed, inject, ref } from 'vue'
import { Input } from 'ant-design-vue'
import { Icon } from '@/components/Icon'
import type { SimpleFlowNode } from '../consts'
import { NODE_DEFAULT_TEXT, NODE_VISUALS } from '../consts'
import { nodeDisplayText } from '../helpers'

defineOptions({ name: 'FlowNodeCard' })

const props = defineProps<{
  node: SimpleFlowNode
  /** 是否可删除（发起人节点不可删） */
  deletable?: boolean
}>()

const emit = defineEmits<{
  delete: []
  click: []
}>()

const isReadonly = inject<boolean>('fpd-readonly', false)

const visual = computed(() => NODE_VISUALS[props.node.type] ?? { icon: 'ant-design:appstore-outlined', color: '#0a7cff' })

const editing = ref(false)

const displayText = computed(() => nodeDisplayText(props.node))
const emptyText = computed(() => !displayText.value)

const STATUS_BADGES: Record<number, { icon: string; cls: string }> = {
  1: { icon: 'ant-design:loading-outlined', cls: 'running' },
  2: { icon: 'ant-design:check-outlined', cls: 'success' },
  3: { icon: 'ant-design:close-outlined', cls: 'reject' },
  4: { icon: 'ant-design:minus-outlined', cls: 'cancel' },
}

const statusBadge = computed(() => {
  const status = props.node.activityStatus
  if (!status) {
    return null
  }
  if ([0, 1, 7].includes(status)) {
    return STATUS_BADGES[1]
  }
  return STATUS_BADGES[status] ?? null
})

const statusClass = computed(() => {
  const status = props.node.activityStatus
  if (!status) {
    return ''
  }
  if ([0, 1, 7].includes(status)) {
    return 'fpd-node__box--status-running'
  }
  if (status === 2) {
    return 'fpd-node__box--status-success'
  }
  if (status === 3) {
    return 'fpd-node__box--status-reject'
  }
  return 'fpd-node__box--status-cancel'
})

function finishRename() {
  editing.value = false
  if (!props.node.name || !props.node.name.trim()) {
    props.node.name = '未命名节点'
  }
}
</script>

<template>
  <div class="fpd-node">
    <div class="fpd-node__box fpd-node__box--editable" :class="[statusClass, { 'fpd-node__box--error': emptyText && !isReadonly }]" @click="!isReadonly && emit('click')">
      <div v-if="deletable && !isReadonly" class="fpd-node__toolbar" @click.stop>
        <span class="fpd-node__del" title="删除节点" @click="emit('delete')">
          <Icon icon="ant-design:close-outlined" />
        </span>
      </div>
      <div class="fpd-node__head">
        <div class="fpd-node__icon" :style="{ backgroundColor: visual.color }">
          <Icon :icon="visual.icon" />
        </div>
        <Input
          v-if="editing"
          v-model:value="node.name"
          size="small"
          class="fpd-node__title-input"
          @click.stop
          @blur="finishRename"
          @press-enter="finishRename"
        />
        <span v-else class="fpd-node__title" @click.stop="!isReadonly && (editing = true)">{{ node.name }}</span>
      </div>
      <div class="fpd-node__text">
        <span class="fpd-node__text-value" :class="{ 'fpd-node__text-value--empty': emptyText }" :title="displayText || NODE_DEFAULT_TEXT.get(node.type)">
          {{ displayText || NODE_DEFAULT_TEXT.get(node.type) }}
        </span>
        <Icon class="fpd-node__arrow" icon="ant-design:right-outlined" />
      </div>
    </div>
    <!-- 查看器状态徽标 -->
    <div v-if="statusBadge" class="fpd-node__status-badge" :class="`fpd-node__status-badge--${statusBadge.cls}`">
      <Icon :icon="statusBadge.icon" />
    </div>
  </div>
</template>
