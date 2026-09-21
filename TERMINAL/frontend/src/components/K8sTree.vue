<template>
  <div class="db-tree-panel">
    <div class="tree-content">
      <template v-for="group in groups" :key="group.key">
        <div
          class="db-header"
          :class="{ selected: false }"
          @click="toggle(group.key)"
        >
          <span class="db-arrow">
            <component :is="expanded.has(group.key) ? ChevronDown : ChevronRight" :size="'0.75rem'" />
          </span>
          <component :is="groupIcon(group.key)" class="db-icon" :size="'0.875rem'" />
          <span class="db-name">{{ group.label }}</span>
        </div>
        <template v-if="expanded.has(group.key)">
          <div
            v-for="r in group.resources"
            :key="r.key"
            class="table-item"
            :class="{ selected: modelValue === r.key }"
            @click="$emit('update:modelValue', r.key)"
          >
            <span class="table-icon-spacer" />
            <component :is="iconOf(r.icon)" class="table-icon" :size="'0.875rem'" />
            <span class="table-name">{{ r.label }}</span>
          </div>
          <div v-if="group.resources.length === 0" class="empty-hint">
            (empty)
          </div>
        </template>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import {
  ChevronDown, ChevronRight,
  Box, Boxes, Layers, GitFork, CirclePlay, Clock, Copy,
  Network, Globe,
  File, FileText, Lock,
  HardDrive, Database,
  Server, Folder, Bell,
  BrickWallShield, Cable, Component, Package2, CircleGauge,
  Package,   // 兜底
} from '@lucide/vue'
import { RESOURCES, type ResourceGroup, type ResourceDescriptor } from '../services/k8sResources'

defineProps<{ modelValue: string }>()
defineEmits<{ (e: 'update:modelValue', key: string): void }>()

interface Group {
  key: ResourceGroup
  label: string
  resources: ResourceDescriptor[]
}

const GROUP_ORDER: ResourceGroup[] = ['workloads', 'network', 'config', 'storage', 'rbac', 'cluster']
const GROUP_LABELS: Record<ResourceGroup, string> = {
  workloads: 'Workloads',
  network: 'Network',
  config: 'Config',
  storage: 'Storage',
  rbac: 'RBAC',
  cluster: 'Cluster',
}

const groups = computed<Group[]>(() =>
  GROUP_ORDER.map(g => ({
    key: g,
    label: GROUP_LABELS[g],
    resources: RESOURCES.filter(r => r.group === g),
  }))
)

// 默认全部展开
const expanded = ref<Set<string>>(new Set(GROUP_ORDER))
function toggle(k: string) {
  if (expanded.value.has(k)) expanded.value.delete(k)
  else expanded.value.add(k)
  expanded.value = new Set(expanded.value)
}

// lucide 名 → 组件映射（预加载所需，避免运行时 dynamic import）
// PlayCircle 在 @lucide/vue 已更名为 CirclePlay，这里保留描述器里的 'PlayCircle' 键。
const ICON_MAP: Record<string, any> = {
  Box, Boxes, Layers, GitFork, PlayCircle: CirclePlay, Clock, Copy,
  Network, Globe,
  File, FileText, Lock,
  HardDrive, Database,
  Server, Folder, Bell,
  BrickWallShield, Cable, Component, Package2, CircleGauge,
}
function iconOf(name: string) {
  return ICON_MAP[name] || Package
}
function groupIcon(_g: ResourceGroup) {
  return Folder
}
</script>

<style scoped>
/* 完全复用 DBTreePanel 的样式规则；class 同名，粘贴过来避免跨组件 scoped 冲突。 */
.db-tree-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.tree-content {
  flex: 1;
  overflow: auto;
}
.db-header {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.375rem 0.5rem;
  cursor: pointer;
  user-select: none;
  transition: background 0.12s ease;
}
.db-header:hover {
  background: var(--bg-hover);
}
.db-header.selected {
  background: var(--bg-hover);
}
.db-arrow {
  width: 0.75rem;
  flex-shrink: 0;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  cursor: pointer;
}
.db-arrow:hover {
  color: var(--text-primary);
}
.db-icon {
  flex-shrink: 0;
  color: var(--text-muted);
}
.db-name {
  font-family: var(--font-ui);
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.table-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.375rem 0.5rem;
  cursor: pointer;
  user-select: none;
  transition: background 0.12s ease;
}
.table-item:hover {
  background: var(--bg-hover);
}
.table-item.selected {
  background: var(--bg-hover);
}
.table-icon-spacer {
  width: 1.875rem;
  flex-shrink: 0;
}
.table-icon {
  flex-shrink: 0;
  color: var(--text-muted);
}
.table-name {
  font-family: var(--font-ui);
  font-size: 0.8125rem;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.empty-hint {
  padding: 0.25rem 0.5rem 0.25rem 1.75rem;
  font-family: var(--font-ui);
  font-size: 0.75rem;
  color: var(--text-muted);
}
</style>
