<template>
  <Menu ref="menuRef" :align="align" v-model:visible="visible">
    <MenuItem :class="{ active: modelValue === 'all' }" @click="onSelect('all')">{{ t('sidebar.filterAll') }}</MenuItem>
    <MenuSubmenu v-for="grp in groups" :key="grp.key" :label="grp.label">
      <MenuItem
        v-for="it in grp.items"
        :key="it.key"
        :class="{ active: modelValue === it.key }"
        @click="onSelect(it.key)"
      >{{ it.label }}</MenuItem>
    </MenuSubmenu>
  </Menu>
</template>

<script setup lang="ts">
// Shared two-level type filter menu (category → type), derived from the
// connectionTypes registry. Types present in the connection list but not in
// the registry catalog (legacy/hidden kinds) are appended under their
// category, and categories without catalog entries (e.g. 'other') get their
// own trailing group.
import { computed, ref } from 'vue'
import Menu from './Menu.vue'
import MenuItem from './MenuItem.vue'
import MenuSubmenu from './MenuSubmenu.vue'
import { useI18n } from '../i18n'
import { useConnectionStore } from '../stores/connectionStore'
import { CATEGORY_META, connectionTypeLabel } from '../utils/connectionTypes'
import type { ConnectionCategory } from '../utils/connectionTypes'
import { formatTypeFilterLabel, getConnectionTypeKey, getTypeCategory, getTypeFilterCatalog } from '../utils/quickConnect'

withDefaults(defineProps<{
  align?: 'start' | 'end'
  modelValue: string
}>(), { align: 'end' })

const emit = defineEmits<{
  (e: 'update:modelValue', v: string): void
}>()

const { t } = useI18n()
const connectionStore = useConnectionStore()

const menuRef = ref<InstanceType<typeof Menu> | null>(null)
defineExpose({
  toggle: (target?: EventTarget | null) => menuRef.value?.toggle(target as HTMLElement),
  openAt: (x: number, y: number, data?: unknown) => menuRef.value?.openAt(x, y, data),
})

const visible = ref(false)

function onSelect(key: string) {
  visible.value = false
  emit('update:modelValue', key)
}

const groups = computed(() => {
  const connKeys = new Set(connectionStore.connections.map(c => getConnectionTypeKey(c)))
  const catalog = getTypeFilterCatalog(t)
  const catalogKeys = new Set(catalog.flatMap(g => g.items.map(i => i.key)))

  const extras = new Map<string, { key: string; label: string }[]>()
  for (const k of connKeys) {
    if (catalogKeys.has(k)) continue
    const cat = getTypeCategory(k)
    if (!extras.has(cat)) extras.set(cat, [])
    extras.get(cat)!.push({ key: k, label: connectionTypeLabel(k) || formatTypeFilterLabel(k) })
  }

  const list = catalog
    .map(g => ({
      key: g.key,
      label: g.label,
      items: [...g.items.filter(i => connKeys.has(i.key)), ...(extras.get(g.key) || [])],
    }))
  // Categories that exist only as extras (e.g. 'other' for monitor) get their
  // own trailing group.
  for (const [cat, items] of extras) {
    if (!list.some(g => g.key === cat)) {
      list.push({ key: cat as ConnectionCategory, label: t(CATEGORY_META[cat as ConnectionCategory].labelKey), items })
    }
  }
  return list.filter(g => g.items.length > 0)
})
</script>
