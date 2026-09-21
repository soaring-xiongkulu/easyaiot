<template>
  <!-- Group header -->
  <div
    class="group-header"
    :class="{
      'drag-over': dragOverId === node.group.id,
      'drop-before': dropIndicator?.id === node.group.id && dropIndicator?.position === 'before',
      'drop-after': dropIndicator?.id === node.group.id && dropIndicator?.position === 'after',
    }"
    :style="{ paddingLeft: (6 + depth * 16) + 'px' }"
    draggable="true"
    @click="onToggle"
    @contextmenu.prevent="onCtxMenu"
    @dragstart.stop="onGrpDragStart"
    @dragover.prevent="onGrpDragOver"
    @dragleave="onGrpDragLeave"
    @drop.prevent="onGrpDrop"
  >
    <span class="group-arrow">
      <el-icon v-if="expanded.has(node.group.id)"><ChevronDown :size="'0.875rem'" /></el-icon>
      <el-icon v-else><ChevronRight :size="'0.875rem'" /></el-icon>
    </span>
    <span class="group-name">{{ node.group.name }}</span>
    <span v-if="totalCount > 0" class="group-count">{{ totalCount }}</span>
  </div>

  <!-- Children (when expanded): child groups first, then connections -->
  <template v-if="expanded.has(node.group.id)">
    <!-- Child groups (recursive) -->
    <GroupTreeItem
      v-for="child in node.children"
      :key="child.group.id"
      :node="child"
      :depth="depth + 1"
    />

    <!-- Connections -->
    <div
      v-for="conn in node.connections"
      :key="conn.id"
      class="connection-item indented"
      :data-conn-id="conn.id"
      :class="{
        active: selected.has(conn.id),
        'has-session': openConns.has(conn.id),
        'drop-before': dropIndicator?.id === conn.id && dropIndicator?.position === 'before',
        'drop-after': dropIndicator?.id === conn.id && dropIndicator?.position === 'after',
      }"
      :style="{ paddingLeft: (24 + depth * 16) + 'px' }"
      draggable="true"
      @dragstart="onConnDragStart($event, conn)"
      @dragend="onConnDragEnd"
      @dragover.prevent="onConnDragOver($event, conn)"
      @drop.prevent="onConnDrop($event, conn)"
      @click="onItemClick($event, conn)"
      @dblclick="onItemDblClick(conn)"
      @contextmenu.prevent="onConnCtxMenu($event, conn)"
    >
      <span class="conn-icon"><component :is="connIcon(conn)" :size="'0.875rem'" /></span>
      <div class="conn-details">
        <span class="name">{{ conn.name }}</span>
        <span class="conn-meta">
          <span class="host">{{ getSubtitle(conn) }}</span>
        </span>
      </div>
      <button
        v-if="showHostRowButtons"
        class="conn-fav-btn"
        :class="{ on: favoriteStore.isFavorite(conn.id) }"
        :title="favoriteStore.isFavorite(conn.id) ? t('sidebar.removeFromFavorites') : t('sidebar.addToFavorites')"
        @click.stop="favoriteStore.toggle(conn.id)"
      >
        <Star :size="'0.75rem'" />
      </button>
      <button v-if="showHostRowButtons" class="conn-more-btn" @click.stop="onMoreClick($event, conn)" :title="t('terminal.more')">
        <MoreHorizontal :size="'0.875rem'" />
      </button>
    </div>
  </template>
</template>

<script setup lang="ts">
import { inject, computed } from 'vue'
import { ChevronDown, ChevronRight, MoreHorizontal, Star } from '@lucide/vue'
import type { ConnectionConfig, ConnectionGroup } from '../types/session'
import type { GroupTreeNode } from '../stores/connectionStore'
import { useFavoriteStore } from '../stores/favoriteStore'
import { useSettingsStore } from '../stores/settingsStore'

const props = defineProps<{
  node: GroupTreeNode
  depth: number
}>()

// Recursive count of all connections in this subtree
const totalCount = computed(() => {
  function count(node: GroupTreeNode): number {
    let n = node.connections.length
    for (const child of node.children) n += count(child)
    return n
  }
  return count(props.node)
})

// Injected from Sidebar
const expanded = inject<Set<string>>('expandedGroups')!
const selected = inject<Set<string>>('selectedIds')!
const openConns = inject<Set<string>>('openPanelConnIds')!
const dragOverId = inject<any>('dragOverGroupId')!
const dropIndicator = inject<any>('dropIndicator')!
const handlers = inject<any>('groupHandlers')!
const utils = inject<any>('utils')!

const { connIcon, getSubtitle, t } = utils

const favoriteStore = useFavoriteStore()
const settingsStore = useSettingsStore()
// Mirrors Sidebar: "right-click menu" host-list mode hides the hover
// star/⋯ buttons; the menu itself stays reachable via right-click (#934).
const showHostRowButtons = computed(() => settingsStore.settings.hostListMenuStyle !== 'rightclick')

function onToggle() {
  handlers.onToggleGroup(props.node.group.id)
}

function onCtxMenu(e: MouseEvent) {
  handlers.onGroupContextMenu(e, props.node.group)
}

function onGrpDragStart(e: DragEvent) {
  e.dataTransfer!.setData('text/plain', JSON.stringify({ type: 'group', id: props.node.group.id }))
  e.dataTransfer!.effectAllowed = 'move'
}

function onGrpDragOver(e: DragEvent) {
  handlers.onGroupDragOver(props.node.group.id, e)
}

function onGrpDragLeave() {
  handlers.onGroupDragLeave(props.node.group.id)
}

function onGrpDrop(e: DragEvent) {
  handlers.onGroupDrop(props.node.group.id, e)
}

function onConnDragStart(e: DragEvent, conn: ConnectionConfig) {
  handlers.onDragStart(e, conn)
}

function onConnDragEnd() {
  handlers.onDragEnd()
}

function onConnDragOver(e: DragEvent, conn: ConnectionConfig) {
  handlers.onConnDragOver(e, conn)
}

function onConnDrop(e: DragEvent, conn: ConnectionConfig) {
  handlers.onConnDrop(e, conn)
}

function onItemClick(e: MouseEvent, conn: ConnectionConfig) {
  handlers.onItemClick(e, conn)
}

function onItemDblClick(conn: ConnectionConfig) {
  handlers.onItemDblClick(conn)
}

function onConnCtxMenu(e: MouseEvent, conn: ConnectionConfig) {
  handlers.onContextMenu(e, conn)
}

function onMoreClick(e: MouseEvent, conn: ConnectionConfig) {
  handlers.onConnMoreClick(e, conn)
}
</script>

<style scoped>
.group-header {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.375rem 0.625rem 0.375rem 0;
  cursor: pointer;
  user-select: none;
  border-radius: var(--radius-sm);
  transition: background 0.12s ease;
  font-family: var(--font-ui);
  font-size: 0.75rem;
  color: var(--text-secondary);
}
.group-header:hover {
  background: var(--bg-hover);
}
.group-header.drag-over {
  background: var(--accent-subtle);
  box-shadow: inset 0 0 0 1px var(--accent);
}
/* Insertion line for reordering (siblings) */
.group-header,
.connection-item {
  position: relative;
}
.group-header.drop-before::before,
.connection-item.drop-before::before,
.group-header.drop-after::after,
.connection-item.drop-after::after {
  content: '';
  position: absolute;
  left: 0.375rem;
  right: 0.375rem;
  height: 0.125rem;
  background: var(--accent);
  border-radius: 1px;
  z-index: 2;
  pointer-events: none;
}
.group-header.drop-before::before,
.connection-item.drop-before::before {
  top: -1px;
}
.group-header.drop-after::after,
.connection-item.drop-after::after {
  bottom: -1px;
}
.group-arrow {
  display: inline-flex;
  align-items: center;
  width: 1rem;
  color: var(--text-disabled);
  flex-shrink: 0;
}
.group-name {
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.group-count {
  margin-left: auto;
  font-size: 0.625rem;
  color: var(--text-disabled);
  background: var(--bg-subtle);
  padding: 0 0.3125rem;
  border-radius: 0.5rem;
  flex-shrink: 0;
}

/* Connection item styles (mirror Sidebar.vue) */
.connection-item {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 0.625rem;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.12s ease;
  margin-bottom: 0.125rem;
  user-select: none;
}
.connection-item.indented {
  padding-left: 1.5rem;
}
.connection-item:hover {
  background: var(--bg-hover);
}
.connection-item.active {
  background: var(--accent-subtle);
  box-shadow: inset 0 0 0 1px var(--accent);
}
.connection-item.active .name {
  color: var(--accent);
}

/* Connection has an open session → highlight its icon with the AI-lock amber */
.connection-item.has-session .conn-icon {
  color: var(--warning);
}

.conn-more-btn {
  display: none;
  align-items: center;
  justify-content: center;
  width: 1.5rem;
  height: 1.5rem;
  border: none;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
  margin-left: 0;
  padding: 0;
}
.connection-item:hover .conn-more-btn {
  display: flex;
}
.conn-more-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

/* Favorite toggle: always reserves its slot and sits at the right edge so
   rows align; revealed on hover and while favorited */
.conn-fav-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1.5rem;
  height: 1.5rem;
  border: none;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
  margin-left: auto;
  padding: 0;
  opacity: 0;
  pointer-events: none;
}
.connection-item:hover .conn-fav-btn,
.conn-fav-btn.on {
  opacity: 1;
  pointer-events: auto;
}
.conn-fav-btn.on {
  color: var(--warning);
}
.conn-fav-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.conn-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1rem;
  flex-shrink: 0;
  color: var(--text-muted);
}

.conn-details {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
  min-width: 0;
}

.name {
  font-family: var(--font-ui);
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.4;
}

.host {
  font-family: var(--font-ui);
  font-size: 0.6875rem;
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.4;
}

.conn-meta {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  min-width: 0;
}
</style>
