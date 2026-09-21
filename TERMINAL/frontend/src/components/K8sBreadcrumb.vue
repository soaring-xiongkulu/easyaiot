<template>
  <div class="db-breadcrumb">
    <el-select
      v-if="showNsSelect"
      :model-value="namespace"
      size="small"
      class="k8s-ns-select"
      placeholder="all namespaces"
      filterable
      allow-create
      default-first-option
      clearable
      @update:model-value="v => $emit('update:namespace', v || '')"
    >
      <el-option label="all namespaces" value="" />
      <el-option v-for="opt in namespaceOptions" :key="opt" :label="opt" :value="opt" />
    </el-select>

    <template v-for="(c, i) in crumbs" :key="i">
      <span v-if="i > 0" class="crumb-sep">/</span>
      <span
        class="crumb"
        :class="{ clickable: c.clickable, current: c.current }"
        @click="c.clickable ? $emit('pop', c.frameIndex) : null"
      >{{ c.text }}</span>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ElSelect, ElOption } from 'element-plus'
import { getResource } from '../services/k8sResources'
import type { NavFrame } from '../types/k8s'

const props = defineProps<{ stack: NavFrame[]; namespace: string; namespaceOptions: string[] }>()
defineEmits<{ (e: 'pop', index: number): void; (e: 'update:namespace', ns: string): void }>()

const showNsSelect = computed(() => {
  const top = props.stack[props.stack.length - 1]
  if (!top) return false
  if (top.kind === 'list') return !!getResource(top.resourceKey)?.namespaced
  if (top.kind === 'owned') return !!getResource(top.resourceKey)?.namespaced
  if (top.kind === 'custom') return top.crd.scope === 'Namespaced'
  return false
})

interface Crumb { text: string; clickable: boolean; current: boolean; frameIndex: number }

const crumbs = computed<Crumb[]>(() => {
  const out: Crumb[] = []
  props.stack.forEach((f, idx) => {
    const isLast = idx === props.stack.length - 1
    const prevIsList = idx > 0 && props.stack[idx - 1].kind === 'list'
    if (f.kind === 'list') {
      out.push({ text: getResource(f.resourceKey)?.label || f.resourceKey, clickable: !isLast, current: isLast, frameIndex: idx })
    } else if (f.kind === 'owned') {
      // parent resource-type crumb only when there's no preceding list frame to supply it (edge case: plain, not clickable)
      if (!prevIsList) {
        out.push({ text: getResource(f.ownerKind.toLowerCase() + 's')?.label || f.ownerKind, clickable: false, current: false, frameIndex: idx })
      }
      out.push({ text: f.ownerName, clickable: false, current: false, frameIndex: idx })
      out.push({ text: getResource(f.resourceKey)?.label || f.resourceKey, clickable: false, current: isLast, frameIndex: idx })
    } else if (f.kind === 'custom') {
      if (!prevIsList) {
        out.push({ text: 'CRDs', clickable: false, current: false, frameIndex: idx })
      }
      out.push({ text: f.crd.kind, clickable: false, current: isLast, frameIndex: idx })
    }
  })
  return out
})
</script>

<style scoped>
.db-breadcrumb {
  display: flex;
  align-items: center;
  padding: 0.25rem 0.75rem;
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: var(--text-secondary);
  background: var(--bg-elevated);
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
  white-space: nowrap;
  overflow: hidden;
}
.crumb {
  padding: 0.125rem 0.375rem;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
}
.crumb.clickable {
  cursor: pointer;
  transition: all 0.1s ease;
}
.crumb.clickable:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}
.crumb.current {
  color: var(--text-primary);
  font-weight: 600;
}
.crumb-sep {
  color: var(--text-disabled);
  margin: 0 0.125rem;
  flex-shrink: 0;
}
.k8s-ns-select { width: 11.25rem; margin-right: 0.5rem; }
</style>
