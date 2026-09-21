<template>
  <div
    class="app-header"
    :class="`platform-${platform}`"
    @dblclick="onDblClick"
  >
    <!-- macOS: custom traffic lights (Wails frameless hides the native ones) -->
    <WindowControls
      v-if="showWindowControls && platform === 'darwin'"
      variant="mac"
      :is-maximised="isMaximised"
      @minimise="onMinimise"
      @maximise="onMaximise"
      @close="onClose"
    />

    <!-- Connections button (icon only, leftmost) -->
    <button class="header-btn" @click="emit('toggle-sidebar')" :title="t('header.connections') + shortcutSuffix('toggleSidebar')">
      <el-icon><PanelLeft :size="'0.875rem'" /></el-icon>
    </button>


    <!-- Tabs list -->
    <div class="header-tabs">
      <TabsList
        @close-tab="(id: string) => emit('close-tab', id)"
        @close-tab-batch="(ids: string[]) => emit('close-tab-batch', ids)"
        @toggle-ai-lock="(panelId: string) => emit('toggle-ai-lock', panelId)"
        @tab-dragstart="(e: DragEvent, tabId: string) => emit('tab-dragstart', e, tabId)"
      />
    </div>

    <!-- AI button -->
    <button class="header-btn" @click="emit('toggle-ai')" :title="t('header.ai') + shortcutSuffix('focusAI')">
      <el-icon><Bot :size="'0.875rem'" /></el-icon>
    </button>

    <!-- Settings button opens a dropdown menu with common settings items -->
    <div class="settings-wrap">
      <button ref="settingsBtnRef" class="header-btn" @click.stop="toggleSettingsMenu" :title="t('header.menu')">
        <el-icon><MenuIcon :size="'0.875rem'" /></el-icon>
      </button>

      <!-- Settings dropdown (theme / language / ai / identities / proxies / settings / check update) -->
      <Menu ref="settingsMenuRef" align="end" v-model:visible="showSettingsMenu">
        <!-- 主题 -->
        <MenuSubmenu :label="t('settings.theme')">
          <MenuItem
            v-for="opt in themeOptions"
            :key="opt.value"
            :class="{ active: settingsStore.settings.theme === opt.value }"
            @click="applyTheme(opt.value)"
          >{{ opt.label }}</MenuItem>
        </MenuSubmenu>

        <!-- 语言 -->
        <MenuSubmenu :label="t('settings.language')">
          <MenuItem
            v-for="lang in LANGUAGE_OPTIONS"
            :key="lang.value"
            :class="{ active: settingsStore.settings.language === lang.value }"
            @click="applyLanguage(lang.value)"
          >{{ lang.native }}</MenuItem>
          <MenuItem
            :class="{ active: settingsStore.settings.language === 'system' }"
            @click="applyLanguage('system')"
          >{{ t('settings.langSystem') }}</MenuItem>
        </MenuSubmenu>

        <MenuDivider />

        <!-- AI模型 / 密钥库 / 代理 -->
        <MenuItem @click="openCategory('ai')">{{ t('settings.ai') }}</MenuItem>
        <MenuItem @click="openCategory('identities')">{{ t('settings.identities') }}</MenuItem>
        <MenuItem @click="openCategory('proxies')">{{ t('settings.proxies') }}</MenuItem>
        <MenuItem @click="openCategory('tunnels')">{{ t('settings.tunnels') }}</MenuItem>

        <MenuDivider />

        <!-- 导入 / 导出连接 -->
        <MenuItem @click="openImport">{{ t('importExport.import') }}</MenuItem>
        <MenuItem @click="openExport">{{ t('importExport.export') }}</MenuItem>

        <MenuDivider />

        <!-- 设置 / 关于 / 检查更新 -->
        <MenuItem :shortcut="menuShortcut('openSettings')" @click="openCategory('basic')">{{ t('settings.title') }}</MenuItem>
        <MenuItem @click="openCategory('about')">{{ t('settings.about') }}</MenuItem>
        <!-- In-app update download is desktop-only -->
        <MenuItem v-if="!isMobilePlatform(platform.value)" @click="checkUpdate">{{ t('settings.checkUpdate') }}</MenuItem>
      </Menu>

      <ImportDialog v-model:visible="showImportDialog" />
      <ExportDialog v-model:visible="showExportDialog" />
    </div>

    <!-- Windows/Linux: window controls right -->
    <WindowControls
      v-if="showWindowControls && platform !== 'darwin'"
      :is-maximised="isMaximised"
      @minimise="onMinimise"
      @maximise="onMaximise"
      @close="onClose"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, h } from 'vue'
import { Menu as MenuIcon, PanelLeft, Bot } from '@lucide/vue'
import { ElMessageBox, ElCheckbox } from 'element-plus'
import { useI18n } from '../i18n'
import { useTabStore } from '../stores/tabStore'
import { usePanelStore } from '../stores/panelStore'
import { useSessionStore } from '../stores/sessionStore'
import { useSettingsStore } from '../stores/settingsStore'
import { formatKeyBinding } from '../composables/useKeyboardShortcuts'
import { useLocalStateStore } from '../stores/localStateStore'
import { useUpdateCheck } from '../composables/useUpdateCheck'
import { LANGUAGE_OPTIONS } from '../types/settings'
import type { AppSettings, ShortcutAction } from '../types/settings'
import { detectPlatformSync, isMobilePlatform } from '../utils/platform'
import WindowControls from './WindowControls.vue'
import TabsList from './TabsList.vue'
import ImportDialog from './ImportDialog.vue'
import ExportDialog from './ExportDialog.vue'
import Menu from './Menu.vue'
import MenuItem from './MenuItem.vue'
import MenuSubmenu from './MenuSubmenu.vue'
import MenuDivider from './MenuDivider.vue'
import { Application, Screens, System, Window } from '@wailsio/runtime'
import { SaveWindowState } from '../../bindings/easyaiot/terminal/app'

const { t } = useI18n()
const tabStore = useTabStore()
const panelStore = usePanelStore()
const sessionStore = useSessionStore()
const settingsStore = useSettingsStore()
const localStateStore = useLocalStateStore()
// Window frame is fixed at startup (Wails limitation): the OS title bar only
// appears after a relaunch. Snapshot the choice now instead of following the
// live store, so toggling it in settings doesn't strip our own window
// controls (close/min/max) before the restart takes effect (issue #935).
const systemTitleBarAtStartup = localStateStore.state.systemTitleBar

// ── Settings dropdown menu ──
const updateCheck = useUpdateCheck()
const showSettingsMenu = ref(false)
const settingsBtnRef = ref<HTMLElement | null>(null)
const settingsMenuRef = ref<InstanceType<typeof Menu> | null>(null)

const themeOptions = computed(() => [
  { value: 'dark' as const, label: t('settings.themeDark') },
  { value: 'deep-blue' as const, label: t('settings.themeDeepBlue') },
  { value: 'light' as const, label: t('settings.themeLight') },
  { value: 'system' as const, label: t('settings.themeSystem') },
])

function toggleSettingsMenu() {
  settingsMenuRef.value?.toggle(settingsBtnRef.value!)
}

function closeSettingsMenu() {
  showSettingsMenu.value = false
}

// ── 导入 / 导出（对话框自包含，菜单关闭后由对话框接管） ──
const showImportDialog = ref(false)
const showExportDialog = ref(false)

function openImport() {
  closeSettingsMenu()
  showImportDialog.value = true
}

function openExport() {
  closeSettingsMenu()
  showExportDialog.value = true
}

function applyTheme(value: AppSettings['theme']) {
  settingsStore.updateTheme(value)
  closeSettingsMenu()
}

function applyLanguage(value: AppSettings['language']) {
  settingsStore.updateLanguage(value)
  closeSettingsMenu()
}

function openCategory(category?: string) {
  emit('open-settings', category)
  closeSettingsMenu()
}

function checkUpdate() {
  updateCheck.checkForUpdate(true)
  closeSettingsMenu()
}

const isMac = /Mac|iPhone|iPad/.test(navigator.userAgent)

// " (Ctrl+Shift+K)" suffix for a shortcut action's tooltip, '' when unset.
// Reactive via settingsStore, so tooltips update when the user rebinds keys.
function shortcutSuffix(action: 'focusAI' | 'toggleSidebar'): string {
  const b = settingsStore.settings.keyboard[action]
  if (!b) return ''
  const key = formatKeyBinding(b, isMac)
  return key ? ` (${key})` : ''
}

// Right-aligned keybinding hint for a menu item, '' when unset. Reactive via
// settingsStore, so hints follow the user's rebinds.
function menuShortcut(action: ShortcutAction): string {
  const b = settingsStore.settings.keyboard[action]
  if (!b) return ''
  return formatKeyBinding(b, isMac)
}

const hasActiveConnections = computed(() =>
  tabStore.tabs.some(t => {
    if (t.type === 'start' || t.type === 'settings') return false
    const panelIds = t.type === 'workspace' ? t.panelIds : 'panelId' in t ? [t.panelId] : []
    return panelIds.some(pid => {
      const p = panelStore.getPanel(pid)
      if (!p?.sessionId) return false
      return sessionStore.getStatus(p.sessionId) === 'connected'
    })
  })
)

const emit = defineEmits<{
  'toggle-ai': []
  'toggle-sidebar': []
  'open-settings': [category?: string]
  'close-tab': [id: string]
  'close-tab-batch': [ids: string[]]
  'toggle-ai-lock': [panelId: string]
  'tab-dragstart': [e: DragEvent, tabId: string]
}>()

const platform = ref(detectPlatformSync())
const isMaximised = ref(false)

// The app draws its own window controls on every platform — but not when the
// user opted into the OS native title bar at startup, which already provides
// them, and never on mobile (no OS window to minimise/maximise/close). On
// macOS they render as traffic lights on the left (see template).
const showWindowControls = computed(
  () => !systemTitleBarAtStartup && !isMobilePlatform(platform.value)
)

async function updateMaximisedState() {
  try {
    isMaximised.value = await Window.IsMaximised()
  } catch {
    // ignore
  }
}

function onMinimise() {
  Window.Minimise()
}

async function onMaximise() {
  if (platform.value === 'linux') {
    await linuxMaximise()
  } else {
    Window.ToggleMaximise()
  }
  setTimeout(() => {
    updateMaximisedState()
    saveWindowState()
  }, 100)
}

async function linuxMaximise() {
  const maximised = await Window.IsMaximised()
  if (maximised) {
    // Restore: use native unmaximise, then clear max size constraint
    Window.UnMaximise()
    Window.SetMaxSize(0, 0)
  } else {
    // Before native maximise, set max size to current screen dimensions
    // to prevent GTK from clamping to the wrong monitor's size.
    try {
      const screens = await Screens.GetAll()
      const current = screens.find((s: { isCurrent: boolean }) => s.isCurrent) || screens[0]
      if (current) {
        Window.SetMaxSize(current.Size.Width, current.Size.Height)
      }
    } catch {
      // Fallback: set large max size to disable any constraint
      Window.SetMaxSize(9999, 9999)
    }
    Window.Maximise()
  }
}

let saveTimer: ReturnType<typeof setTimeout> | null = null

async function saveWindowState() {
  try {
    // Do not save geometry when minimised — the position is off-screen
    // and the size is the tiny taskbar thumbnail.
    if (await Window.IsMinimised()) return
    const maxed = await Window.IsMaximised()
    const { x, y } = await Window.Position()
    const { width, height } = await Window.Size()
    SaveWindowState(x, y, width, height, maxed)
  } catch {
    // ignore
  }
}

async function onClose() {
  if (hasActiveConnections.value) {
    if (!settingsStore.settings.closeAppPrompt) {
      // skip dialog, proceed to quit
    } else {
      const dontShowAgain = ref(false)
      // Hide the native RDP window so the dialog isn't covered by it (issue #346)
      window.dispatchEvent(new CustomEvent('rdp:overlay-push'))
      try {
        await ElMessageBox.confirm(
          h('div', { style: 'display:flex;flex-direction:column;gap:0.625rem' }, [
            h('span', t('app.closeConfirm')),
            h(ElCheckbox, {
              'onUpdate:modelValue': (v: boolean) => { dontShowAgain.value = v }
            }, () => t('app.dontShowAgain'))
          ]),
          t('app.closeTitle'),
          { confirmButtonText: t('tab.close'), cancelButtonText: t('conn.cancel'), type: 'warning' }
        )
      } catch {
        return // user cancelled
      } finally {
        window.dispatchEvent(new CustomEvent('rdp:overlay-pop'))
      }
      if (dontShowAgain.value) {
        settingsStore.settings.closeAppPrompt = false
        settingsStore.save()
      }
    }
  }
  await saveWindowState()
  Application.Quit()
}

function onDblClick(e: MouseEvent) {
  const target = e.target as HTMLElement
  if (target.closest('button, input, textarea, select, a, [role="button"], .tab-item, .tab-more, .window-controls')) return
  onMaximise()
}

function onWindowResize() {
  updateMaximisedState()
  // Debounce save to avoid frequent writes during drag-resize
  if (saveTimer) clearTimeout(saveTimer)
  saveTimer = setTimeout(saveWindowState, 500)
}

onMounted(async () => {
  try {
    const env = await System.Environment()
    const p = env.OS.toLowerCase()
    if (p === 'darwin') platform.value = 'darwin'
    else if (p === 'linux') platform.value = 'linux'
    else if (p === 'android') platform.value = 'android'
    else if (p === 'ios') platform.value = 'ios'
    else platform.value = 'windows'
  } catch {
    platform.value = 'windows'
  }
  updateMaximisedState()
  window.addEventListener('resize', onWindowResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', onWindowResize)
})
</script>

<style scoped>
.app-header {
  display: flex;
  align-items: center;
  height: 2.75rem;
  padding: 0 0.5rem;
  gap: 0.125rem;
  background: var(--bg-elevated);
  flex-shrink: 0;
  position: relative;
  z-index: 10;
  --wails-draggable: drag;
}

.app-header::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent 0%,
    var(--accent-subtle) 20%,
    var(--accent-glow) 50%,
    var(--accent-subtle) 80%,
    transparent 100%
  );
}

.header-tabs {
  display: flex;
  flex: 1;
  min-width: 0;
  overflow: hidden;
  justify-content: flex-start;
  align-items: center;
}

.header-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 1.75rem;
  padding: 0.3125rem 0.5rem;
  font-family: var(--font-ui);
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--text-secondary);
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
  flex-shrink: 0;
  --wails-draggable: no-drag;
}

.header-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.header-btn.active {
  background: var(--bg-active, var(--bg-hover));
  color: var(--accent, var(--text-primary));
}

.header-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.header-btn:disabled:hover {
  background: transparent;
  color: var(--text-secondary);
}

.header-btn .el-icon {
  font-size: 0.875rem;
}

[data-theme="light"] .app-header::after {
  background: linear-gradient(
    90deg,
    transparent 0%,
    var(--accent-subtle) 20%,
    var(--accent-glow) 50%,
    var(--accent-subtle) 80%,
    transparent 100%
  );
}

.app-header :deep(.window-controls) {
  --wails-draggable: no-drag;
}

/* ── Settings dropdown menu ── */
.settings-wrap {
  position: relative;
  flex-shrink: 0;
  --wails-draggable: no-drag;
}

</style>
