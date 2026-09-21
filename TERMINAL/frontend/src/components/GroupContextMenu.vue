<template>
  <Menu ref="menuRef" v-model:visible="visible">
    <MenuItem @click="close(); emit('newGroup')">{{ t('conn.newGroupTitle') }}</MenuItem>
    <MenuItem @click="close(); emit('newConnection')">{{ t('sidebar.newConnection') }}</MenuItem>
    <!-- The virtual (No Group) / ungrouped pseudo-group is not a real group:
         rename / move / delete make no sense for it. -->
    <template v-if="!isVirtual">
      <MenuDivider />
      <MenuItem @click="close(); emit('rename')">{{ t('conn.renameGroup') }}</MenuItem>
      <MenuItem @click="close(); emit('changeParent')">{{ t('conn.moveTo') }}</MenuItem>
      <MenuDivider />
      <MenuItem class="danger" @click="close(); emit('deleteGroup')">{{ t('conn.deleteGroup') }}</MenuItem>
    </template>
  </Menu>
</template>

<script setup lang="ts">
// Shared group context menu. Actions are emitted with the target group; the
// virtual (No Group) pseudo-group hides the destructive/renaming items.
import { computed, ref } from 'vue'
import Menu from './Menu.vue'
import MenuItem from './MenuItem.vue'
import MenuDivider from './MenuDivider.vue'
import { useI18n } from '../i18n'

const props = defineProps<{
  group: { id: string; name: string } | null
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'update:visible', v: boolean): void
  (e: 'newGroup'): void
  (e: 'newConnection'): void
  (e: 'rename'): void
  (e: 'changeParent'): void
  (e: 'deleteGroup'): void
}>()

const { t } = useI18n()

const menuRef = ref<InstanceType<typeof Menu> | null>(null)
defineExpose({ openAt: (x: number, y: number, data?: unknown) => menuRef.value?.openAt(x, y, data) })

const visible = computed({
  get: () => props.visible,
  set: v => emit('update:visible', v),
})

const isVirtual = computed(() => !props.group || props.group.id === '__ungrouped__')

function close() {
  emit('update:visible', false)
}
</script>
