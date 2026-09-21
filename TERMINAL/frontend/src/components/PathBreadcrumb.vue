<template>
  <div
    ref="breadcrumbRef"
    class="sftp-breadcrumb"
    @click.self="startEdit"
  >
    <template v-if="editing">
      <span v-if="label" class="breadcrumb-label">{{ label }}</span>
      <el-input
        ref="inputRef"
        v-model="pathInput"
       
        class="path-input"
        @keyup.enter="commitEdit"
        @blur="commitEdit"
        @keyup.escape="cancelEdit"
      />
    </template>
    <template v-else>
      <span v-if="label" class="breadcrumb-label">{{ label }}</span>
      <template v-for="(item, idx) in visibleParts" :key="idx">
        <span
          v-if="item === '...'"
          class="breadcrumb-part breadcrumb-ellipsis"
          @click.stop="onEllipsisClick"
        ><MoreHorizontal :size="'0.875rem'" /></span>
        <span
          v-else-if="isWindowsPath && item === pathParts[0]"
          class="breadcrumb-part breadcrumb-drive"
          @click.stop="driveMenuRef?.toggle($event.currentTarget)"
        >
          {{ item }}
          <span class="drive-arrow">&#9660;</span>
        </span>
        <span
          v-else
          class="breadcrumb-part"
          @click="onBreadcrumbClick(item)"
        >
          {{ item }}
        </span>
        <span v-if="idx < visibleParts.length - 1" class="separator" @click.stop>&gt;</span>
      </template>
      <button
        v-if="bookmarkMode"
        class="bookmark-btn"
        :title="t('sftp.bookmark.title')"
        @click.stop="bookmarkMenuRef?.toggle($event.currentTarget)"
      >
        <Bookmark :size="'0.875rem'" :class="{ 'bookmark-active': hasCurrentPathBookmarked }" />
      </button>
    </template>

    <!-- Drive dropdown -->
    <Menu ref="driveMenuRef" align="start" v-model:visible="driveMenuVisible">
      <MenuItem
        v-for="drive in drives"
        :key="drive"
        class="mono"
        :class="{ active: drive === currentDrive }"
        @click="onDriveSelect(drive)"
      >
        {{ drive }}
      </MenuItem>
    </Menu>

    <!-- Bookmark dropdown -->
    <Menu ref="bookmarkMenuRef" align="end" v-model:visible="bookmarkMenuVisible">
      <MenuItem
        v-if="!hasCurrentPathBookmarked"
        iconic
        :icon="BookmarkPlus"
        class="bookmark-save"
        @click="onSaveBookmark"
      >
        {{ t('sftp.bookmark.saveCurrent') }}
      </MenuItem>
      <MenuItem
        v-else
        iconic
        :icon="BookmarkCheck"
        class="bookmark-saved-hint"
      >
        {{ t('sftp.bookmark.saved') }}
      </MenuItem>
      <MenuDivider />
      <MenuItem
        v-for="savedPath in savedPaths"
        :key="savedPath"
        iconic
        class="mono bookmark-path-item"
        :class="{ active: savedPath === currentPath }"
        @click="onBookmarkClick(savedPath)"
      >
        <span class="bookmark-path-text" :title="savedPath">{{ savedPath }}</span>
        <template #trailing>
          <button
            class="bookmark-remove-btn"
            @click.stop="onRemoveBookmark(savedPath)"
            :title="t('sftp.bookmark.remove')"
          >
            <Trash2 :size="'0.75rem'" />
          </button>
        </template>
      </MenuItem>
      <MenuItem
        v-if="savedPaths.length === 0"
        class="bookmark-empty"
      >
        {{ t('sftp.bookmark.empty') }}
      </MenuItem>
    </Menu>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, nextTick, watch, onMounted, onUnmounted } from 'vue'
import { Bookmark, BookmarkPlus, BookmarkCheck, Trash2, MoreHorizontal } from '@lucide/vue'
import { useI18n } from '../i18n'
import Menu from './Menu.vue'
import MenuItem from './MenuItem.vue'
import MenuDivider from './MenuDivider.vue'

const { t } = useI18n()

const props = defineProps<{
  path: string
  label?: string
  drives?: string[]
  savedPaths?: string[]
  bookmarkMode?: 'local' | 'remote'
}>()

const emit = defineEmits<{
  navigate: [path: string]
  saveBookmark: [path: string]
  removeBookmark: [path: string]
}>()

const isWindowsPath = computed(() => {
  return /^[A-Za-z]:[\\\/]/.test(props.path)
})

const currentDrive = computed(() => {
  if (!isWindowsPath.value) return ''
  const match = props.path.match(/^([A-Za-z]:)/)
  return match ? match[1] + '\\' : ''
})

const pathParts = computed(() => {
  if (isWindowsPath.value) {
    const clean = props.path.replace(/\\/g, '/')
    const parts = clean.split('/').filter(Boolean)
    return parts
  }

  const clean = props.path.replace(/\\/g, '/')
  if (!clean || clean === '/') return ['/']
  const parts = clean.split('/').filter(Boolean)
  return ['/', ...parts]
})

// Overflow collapse
const containerWidth = ref(0)
const collapsedCount = ref(0)
const breadcrumbRef = ref<HTMLElement>()

const visibleParts = computed(() => {
  const parts = pathParts.value
  if (collapsedCount.value <= 0 || parts.length <= 2) return [...parts]
  const hidden = Math.min(collapsedCount.value, parts.length - 2)
  return [parts[0], '...', ...parts.slice(1 + hidden)]
})

let resizeObserver: ResizeObserver | null = null

function recalcOverflow() {
  nextTick(() => {
    const el = breadcrumbRef.value
    if (!el) return
    const maxCollapse = Math.max(0, pathParts.value.length - 2)
    // Only ever collapse more within a layout pass. Expanding is handled by
    // resetting collapsedCount to 0 on path/size change. Mixing increment and
    // decrement here causes an infinite flip-flop when a path sits exactly at
    // the overflow boundary (e.g. a single very long segment), freezing the UI.
    if (el.scrollWidth > el.clientWidth && collapsedCount.value < maxCollapse) {
      collapsedCount.value++
    }
  })
}

watch(() => props.path, () => {
  collapsedCount.value = 0
  recalcOverflow()
})

watch(containerWidth, () => {
  // Recompute from scratch so a wider container can re-expand collapsed parts.
  collapsedCount.value = 0
  recalcOverflow()
})

watch(collapsedCount, () => {
  recalcOverflow()
})

onMounted(() => {
  if (breadcrumbRef.value) {
    resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        containerWidth.value = entry.contentRect.width
      }
    })
    resizeObserver.observe(breadcrumbRef.value)
  }
})

onUnmounted(() => {
  resizeObserver?.disconnect()
})

// Path edit mode
const editing = ref(false)
const pathInput = ref('')
const inputRef = ref()

function startEdit() {
  // Build current path string from parts
  if (isWindowsPath.value) {
    pathInput.value = pathParts.value.join('\\')
    if (pathParts.value.length === 1 && /^[A-Za-z]:$/.test(pathParts.value[0])) {
      pathInput.value += '\\'
    }
  } else {
    pathInput.value = '/' + pathParts.value.slice(1).join('/')
    if (pathInput.value === '') pathInput.value = '/'
  }
  editing.value = true
  nextTick(() => {
    inputRef.value?.focus()
  })
}

function commitEdit() {
  if (!editing.value) return
  editing.value = false
  const val = pathInput.value.trim()
  if (val && val !== props.path) {
    emit('navigate', val)
  }
}

function cancelEdit() {
  editing.value = false
}

// Drive menu
const driveMenuVisible = ref(false)
const driveMenuRef = ref<InstanceType<typeof Menu> | null>(null)

function onGlobalContextMenu(e: MouseEvent) {
  const target = e.target as HTMLElement
  if (!target.closest('.sftp-breadcrumb')) {
    driveMenuVisible.value = false
  }
}

function onGlobalBookmarkContextMenu(e: MouseEvent) {
  const target = e.target as HTMLElement
  if (!target.closest('.sftp-breadcrumb')) {
    bookmarkMenuVisible.value = false
  }
}

onMounted(() => {
  document.addEventListener('contextmenu', onGlobalContextMenu)
  document.addEventListener('contextmenu', onGlobalBookmarkContextMenu)
})

onUnmounted(() => {
  document.removeEventListener('contextmenu', onGlobalContextMenu)
  document.removeEventListener('contextmenu', onGlobalBookmarkContextMenu)
})

function onDriveSelect(drive: string) {
  driveMenuVisible.value = false
  emit('navigate', drive)
}

function onEllipsisClick() {
  const parts = pathParts.value
  const lastHidden = collapsedCount.value
  const selected = parts.slice(0, lastHidden + 1)
  if (isWindowsPath.value) {
    let target = selected.join('\\')
    emit('navigate', target)
  } else {
    let target = selected.join('/').replace(/\/+/g, '/')
    if (!target.startsWith('/')) target = '/' + target
    emit('navigate', target)
  }
}

function onBreadcrumbClick(part: string) {
  if (part === '...') return
  const parts = pathParts.value
  const index = parts.indexOf(part)
  if (index < 0) return
  if (isWindowsPath.value && index === 0) return // handled by dropdown

  const selected = parts.slice(0, index + 1)

  if (isWindowsPath.value) {
    let target = selected.join('\\')
    if (selected.length === 1 && /^[A-Za-z]:$/.test(selected[0])) {
      target += '\\'
    }
    emit('navigate', target)
    return
  }

  let target = selected.join('/').replace(/\/+/g, '/')
  if (!target.startsWith('/')) target = '/' + target
  emit('navigate', target)
}

// Bookmark menu
const bookmarkMenuVisible = ref(false)
const bookmarkMenuRef = ref<InstanceType<typeof Menu> | null>(null)
const currentPath = computed(() => props.path)
const hasCurrentPathBookmarked = computed(() => {
  return (props.savedPaths || []).includes(props.path)
})

function onSaveBookmark() {
  emit('saveBookmark', props.path)
  bookmarkMenuVisible.value = false
}

function onRemoveBookmark(path: string) {
  emit('removeBookmark', path)
}

function onBookmarkClick(path: string) {
  bookmarkMenuVisible.value = false
  if (path !== props.path) {
    emit('navigate', path)
  }
}
</script>

<style scoped>
.sftp-breadcrumb {
  display: flex;
  align-items: center;
  padding: 0.25rem 0.75rem;
  font-size: 0.75rem;
  font-family: var(--font-mono);
  color: var(--text-primary);
  background: var(--bg-elevated);
  border-bottom: 1px solid var(--border-subtle);
  overflow: hidden;
  white-space: nowrap;
}
.path-input {
  flex: 1;
}
.breadcrumb-part {
  cursor: pointer;
  padding: 0.125rem 0.25rem;
  border-radius: var(--radius-sm);
  transition: all 0.1s ease;
  flex-shrink: 0;
}
.breadcrumb-part:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}
.breadcrumb-drive {
  cursor: pointer;
  user-select: none;
}
.breadcrumb-ellipsis {
  color: var(--text-disabled);
  cursor: pointer;
  padding: 0.125rem 0.375rem;
}
.drive-arrow {
  font-size: 0.5rem;
  margin-left: 0.25rem;
  color: var(--text-disabled);
}
.breadcrumb-label {
  color: var(--accent);
  font-weight: 600;
  margin-right: 0.5rem;
  flex-shrink: 0;
}
.separator {
  color: var(--text-disabled);
  margin: 0 0.125rem;
  flex-shrink: 0;
}
.bookmark-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1.5rem;
  height: 1.5rem;
  margin-left: auto;
  flex-shrink: 0;
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.1s ease;
}
.bookmark-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}
.bookmark-btn .bookmark-active {
  color: var(--accent);
}
</style>

<style>
/* Bookmark accent / remove-button specifics. */
.bookmark-save,
.bookmark-saved-hint {
  color: var(--accent);
  font-family: var(--font-ui);
}
.bookmark-path-item {
  justify-content: space-between;
}
.bookmark-path-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  min-width: 0;
}
.bookmark-remove-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1.125rem;
  height: 1.125rem;
  flex-shrink: 0;
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--text-muted);
  cursor: pointer;
  padding: 0;
}
.bookmark-remove-btn:hover {
  background: var(--bg-hover);
  color: var(--error);
}
.bookmark-empty {
  font-family: var(--font-ui);
  color: var(--text-disabled);
  cursor: default;
}
</style>
