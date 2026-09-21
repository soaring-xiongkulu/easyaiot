<template>
  <el-dialog append-to-body :model-value="visible" :title="t('conn.newGroupTitle')" width="25rem" @update:model-value="(v: boolean) => emit('update:visible', v)">
    <el-form label-width="5rem" @submit.prevent="onConfirm">
      <el-form-item :label="t('conn.groupName')">
        <el-input
          ref="nameInputRef"
          v-model="name"
          :placeholder="t('conn.groupNamePlaceholder')"
          @keyup.enter="onConfirm"
        />
      </el-form-item>
      <el-form-item :label="t('conn.parentGroup')">
        <el-tree-select
          v-model="parentId"
          :data="groupTreeData"
          :render-after-expand="false"
          check-strictly
          clearable
          :placeholder="t('conn.noGroup')"
          style="width:100%"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="emit('update:visible', false)">{{ t('conn.cancel') }}</el-button>
      <el-button type="primary" @click="onConfirm">{{ t('conn.save') }}</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
// Shared "new group" dialog: group name + parent tree. The parent decides
// what to do with the confirmed (name, parentId) — plain addGroup, or
// create-then-move flows.
import { computed, ref, watch, nextTick } from 'vue'
import { useI18n } from '../i18n'
import { useConnectionStore } from '../stores/connectionStore'

const props = defineProps<{
  visible: boolean
  // Pre-selected parent group (undefined = no group).
  parentId?: string
}>()

const emit = defineEmits<{
  (e: 'update:visible', v: boolean): void
  // parentId is undefined for the root; '__none__' is normalized away.
  (e: 'confirm', name: string, parentId: string | undefined): void
}>()

const { t } = useI18n()
const connectionStore = useConnectionStore()

interface TreeOption {
  value: string
  label: string
  children?: TreeOption[]
}
const name = ref('')
const parentId = ref<string | undefined>(undefined)
const nameInputRef = ref()

watch(() => props.visible, (open) => {
  if (!open) return
  name.value = ''
  parentId.value = props.parentId
  nextTick(() => nameInputRef.value?.focus())
})

// Group tree for the parent selector, shared shape across consumers.
const groupTreeData = computed<TreeOption[]>(() => {
  function buildTree(nodes: any[]): TreeOption[] {
    return nodes.map((node: any) => ({
      value: node.group.id,
      label: node.group.name,
      children: node.children.length > 0 ? buildTree(node.children) : undefined,
    }))
  }
  return [
    { value: '__none__', label: t('conn.noGroup') },
    ...buildTree(connectionStore.groupedConnections.roots),
  ]
})

function onConfirm() {
  const trimmed = name.value.trim()
  if (!trimmed) return
  emit('update:visible', false)
  emit('confirm', trimmed, parentId.value === '__none__' ? undefined : parentId.value)
  name.value = ''
  parentId.value = undefined
}
</script>
