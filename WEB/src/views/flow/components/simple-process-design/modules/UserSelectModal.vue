<script lang="ts" setup>
/**
 * 用户多选弹窗（候选人指定成员 / 抄送人 / 加签 / 转办 等场景共用）
 */
import { computed, ref, watch } from 'vue'
import { Avatar, Checkbox, Empty, Input, Modal } from 'ant-design-vue'
import { Icon } from '@/components/Icon'
import { useCandidateOptions } from '../useCandidateOptions'

defineOptions({ name: 'FlowUserSelectModal' })

const props = defineProps<{
  open: boolean
  title?: string
  selectedIds?: number[]
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  confirm: [ids: number[], users: any[]]
}>()

const { users } = useCandidateOptions()

const keyword = ref('')
const checkedIds = ref<number[]>([])

watch(
  () => props.open,
  (val) => {
    if (val) {
      keyword.value = ''
      checkedIds.value = [...(props.selectedIds ?? [])]
    }
  },
)

const filteredUsers = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  if (!kw) {
    return users.value
  }
  return users.value.filter(user => user.nickname?.toLowerCase().includes(kw))
})

const checkedUsers = computed(() =>
  users.value.filter(user => checkedIds.value.includes(user.id)),
)

function toggle(user: any) {
  const index = checkedIds.value.indexOf(user.id)
  if (index >= 0) {
    checkedIds.value.splice(index, 1)
  }
  else {
    checkedIds.value.push(user.id)
  }
}

function handleOk() {
  emit('confirm', [...checkedIds.value], checkedUsers.value.map(user => ({ ...user })))
  emit('update:open', false)
}
</script>

<template>
  <Modal
    :open="open"
    :title="title ?? '选择成员'"
    :width="480"
    ok-text="确定"
    cancel-text="取消"
    @ok="handleOk"
    @cancel="emit('update:open', false)"
  >
    <Input
      v-model:value="keyword"
      allow-clear
      placeholder="搜索成员姓名"
      style="margin-bottom: 12px"
    >
      <template #prefix>
        <Icon icon="ant-design:search-outlined" />
      </template>
    </Input>
    <div class="flow-user-select__list">
      <Empty v-if="filteredUsers.length === 0" description="暂无成员" />
      <div
        v-for="user in filteredUsers"
        :key="user.id"
        class="flow-user-select__item"
        @click="toggle(user)"
      >
        <Checkbox :checked="checkedIds.includes(user.id)" @click.stop @change="toggle(user)" />
        <Avatar :size="28" style="background-color: #0a7cff; flex-shrink: 0">
          {{ (user.nickname || '?').slice(0, 1) }}
        </Avatar>
        <span class="flow-user-select__name">{{ user.nickname }}</span>
      </div>
    </div>
    <div class="flow-user-select__footer">已选 {{ checkedIds.length }} 人</div>
  </Modal>
</template>

<style lang="less" scoped>
.flow-user-select__list {
  max-height: 360px;
  overflow-y: auto;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
}

.flow-user-select__item {
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 8px 12px;
  cursor: pointer;
  transition: background-color 0.15s;

  &:hover {
    background-color: #f5f8ff;
  }
}

.flow-user-select__name {
  flex: 1;
  overflow: hidden;
  font-size: 13px;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.flow-user-select__footer {
  padding-top: 10px;
  color: #8c94a5;
  font-size: 12px;
  text-align: right;
}
</style>
