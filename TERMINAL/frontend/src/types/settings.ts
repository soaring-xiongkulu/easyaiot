export const SUPPORTED_LOCALES = [
  'zh-CN', 'zh-TW', 'en', 'ja', 'ko', 'de', 'es', 'fr', 'ru'
] as const

export type Locale = typeof SUPPORTED_LOCALES[number]
export type Language = Locale | 'system'
export type Theme = 'dark' | 'deep-blue' | 'light' | 'system'
export type TerminalTheme = 'terminal-dark' | 'terminal-light' | 'solarized-dark' | 'solarized-light' | 'monokai' | 'dracula' | 'molokai' | 'tomorrow-night' | 'tomorrow-night-bright' | 'tomorrow' | 'one-dark' | 'one-light' | 'github-dark' | 'github-light' | 'gotham' | 'hybrid' | 'nord' | 'gruvbox-dark' | 'gruvbox-light' | 'catppuccin-mocha' | 'catppuccin-latte' | 'tokyo-night' | 'tokyo-day' | 'rose-pine' | 'rose-pine-dawn' | 'everforest-dark' | 'everforest-light' | 'xshell-xterm' | 'xshell-ansi-black' | 'xshell-new-black' | 'mobaxterm-default' | 'mobaxterm-ubuntu' | 'finalshell-dark' | 'finalshell-light'

// Magic value for `AppSettings.terminal.theme`: the effective built-in theme
// is derived from the current app theme (dark / deep-blue -> terminal-dark,
// light -> terminal-light) instead of being fixed. Kept out of TERMINAL_THEMES
// because it has no color palette of its own.
export const FOLLOW_APP_THEME = 'follow-app'

// xterm.js's ITheme shape: the 4 base colors plus the 16 ANSI colors, all as hex strings.
export interface TerminalThemeColors {
  background: string
  foreground: string
  cursor: string
  selection: string
  black: string
  red: string
  green: string
  yellow: string
  blue: string
  magenta: string
  cyan: string
  white: string
  brightBlack: string
  brightRed: string
  brightGreen: string
  brightYellow: string
  brightBlue: string
  brightMagenta: string
  brightCyan: string
  brightWhite: string
}

// A user-defined terminal color scheme. Stored alongside (not inside)
// TerminalSettings since a theme is a reusable resource, not a single
// terminal session's property.
export interface CustomTerminalTheme {
  id: string
  name: string
  type: 'dark' | 'light'
  colors: TerminalThemeColors
}

// ⚠️ PERSISTENCE CONTRACT — every field added to this interface (and to
// AppSettings / AISettings / AIModelConfig below) MUST get a matching field
// in `backend/store/settings_store.go` (TerminalSettings / AppSettings / ...),
// otherwise the value silently fails to persist: settings round-trip through
// the Go struct on Save/Load, and Go drops unknown JSON keys. Add it with a
// pointer + omitempty for optional fields so older settings.json files still
// load, then run `wails3 generate bindings`.
export interface TerminalSettings {
  theme: TerminalTheme | string
  fontFamily: string
  // Secondary font family for glyphs the primary font lacks (most useful for
  // CJK: the first font usually covers Latin only, and the browser falls back
  // to this one for CJK characters). Empty means no explicit fallback; the CSS
  // generic `monospace` covers anything else. Rendered as
  // `"fontFamily", "fallbackFont", monospace`.
  fallbackFont: string
  // Weight of regular terminal text (normal/SemiBold/etc. fire on the bundled
  // JetBrains Mono Variable through its variable weight axis; fixed fonts map
  // to their nearest available weight). ANSI-bold text stays a step heavier.
  fontWeight: number
  fontSize: number
  selectionAction: 'none' | 'copy'
  rightClickAction: 'menu' | 'paste'
  middleClickAction: 'paste' | 'menu'
  // Ctrl/Cmd + mouse wheel zooms the terminal font. Can be turned off (issue
  // #671) for scroll-sensitive mice; defaults to enabled.
  ctrlWheelZoom?: boolean
  maxHistoryLines: number
  smartCompletion: boolean
  aiTranscription: boolean
  highlightEnabled: boolean
  cursorBlink: boolean
  // Cursor shape when the terminal is focused, mapped straight onto xterm's
  // `cursorStyle` option.
  cursorStyle: 'block' | 'underline' | 'bar'
  // Minimum text/background contrast ratio (F-039). xterm auto-brightens or
  // darkens the foreground until this ratio is met, only for cells below it,
  // so low-contrast pairings (e.g. ls's colored blocks for 777 dirs) stay
  // readable. 1 = xterm's no-op default = disabled.
  minimumContrast: number
  // Override for the session output log directory. Empty means the
  // OS default under ~/Documents/Terminal/logs.
  sessionLogDir: string
  // Default local directory for files received with ZMODEM sz. Empty keeps
  // the existing behavior of asking for a directory on every transfer.
  zmodemDownloadDir: string
  // Filename template: %S session, %H host, %M month, %D day, %h hour, %m minute.
  sessionLogFilename: string
  // Characters that act as word boundaries for xterm.js's double-click
  // word selection. Default mirrors the built-in xterm separators
  // extended with the most common shell / path punctuation, so that
  // e.g. `foo;bar` selects only `foo` on double-click.
  wordSeparator: string
  // Show a line-number gutter along the left edge of the terminal.
  // Wrapped continuation rows show no number (so a wrapped command reads as
  // one logical line). Defaults to off; the right-click menu can toggle it.
  showLineNumbers: boolean
  // Show a timestamp column recording when each logical line first appeared —
  // the prompt line when its command was executed, output lines when they
  // arrived. Wrapped continuation rows stay blank. Defaults to off.
  showTimestamps: boolean
  // Display template for the timestamp column. Tokenized: YYYY/YY (year),
  // MM/DD (month/day), HH/mm/ss (hour/minute/second), literals pass through.
  timestampFormat: string
}

export interface AIModelConfig {
  id: string
  name: string
  apiKey: string
  baseURL: string
  model: string
  protocol: 'anthropic' | 'openai' | 'responses'
  // See the persistence-contract note on TerminalSettings: this field MUST
  // also exist in the Go AIModelConfig (backend/store/settings_store.go).
  userAgent?: string
  // Reference to a saved outbound proxy (proxies.json) for all traffic to
  // this model's baseURL. Empty/undefined = direct connection.
  proxyId?: string
}

export const USER_AGENT_PRESETS: { label: string; value: string }[] = [
  { label: 'Terminal', value: 'Terminal' },
  { label: 'Claude Code', value: 'claude-code/1.0' },
  { label: 'Cursor', value: 'Cursor/1.0' },
  { label: 'Cline', value: 'Cline/1.0' },
  { label: 'OpenCode', value: 'opencode' },
  { label: 'ChatGPT Desktop', value: 'ChatGPT-Desktop/1.0' },
]

export interface AISettings {
  maxTurns: number
  models: AIModelConfig[]
  activeModelId: string
}

export type ShortcutAction =
  | 'nextTab' | 'prevTab'
  | 'newConnection' | 'toggleSidebar' | 'openQuickCommands'
  | 'focusAI' | 'focusTerminal' | 'lockAI'
  | 'maximizePanel'
  | 'closePanel'
  | 'navigatePrev' | 'navigateNext'
  | 'duplicateSession'
  | 'terminalSearch'
  | 'openSettings'
  | 'copy'
  | 'paste'
  | 'toggleLineNumbers'
  | 'toggleTimestamps'
  | 'zoomFontIn'
  | 'zoomFontOut'

// User-facing bindings only use ctrl/shift/alt. On macOS the runtime mirrors
// every ctrl combo to Cmd (per-action shortcuts register both; the digit
// shortcuts treat Ctrl and Cmd as one modifier), so Cmd is always covered by
// ctrl. Alt bindings answer to the Option key (same key event).
export interface KeyBinding {
  ctrl: boolean
  shift: boolean
  alt: boolean
  key: string
}

// tabSwitchModifier / panelSwitchModifier are not per-action bindings: only
// their modifier flags (ctrl/meta/shift/alt) are read, their `key` stays
// empty. The configured combo held together with a digit key (1-9) switches
// to that tab / workspace panel, handled by onPlatformSystemShortcut in
// App.vue. Unset = platform default (tabs: Ctrl on Windows/Linux, Cmd on
// macOS; panels: Alt/Option); an entry with no modifier set disables that
// digit family entirely. When both resolve to the same combo, tab switching
// wins and the panel digit shortcuts are suppressed.
export type KeyboardSettings = Partial<Record<ShortcutAction, KeyBinding>> & {
  tabSwitchModifier?: KeyBinding
  panelSwitchModifier?: KeyBinding
  // Global (system-wide) show/hide hotkey for the tray. Not an in-app action:
  // it is registered with the OS and fires even without focus. A binding with
  // an empty key (the "cleared" state) disables it.
  trayShowHide?: KeyBinding
}

export const SHORTCUT_LABELS: Record<ShortcutAction, string> = {
  newConnection: 'shortcut.newConnection',
  nextTab: 'shortcut.nextTab',
  prevTab: 'shortcut.prevTab',
  navigatePrev: 'shortcut.navigatePrev',
  navigateNext: 'shortcut.navigateNext',
  maximizePanel: 'shortcut.maximizePanel',
  closePanel: 'shortcut.closePanel',
  toggleSidebar: 'shortcut.toggleSidebar',
  openQuickCommands: 'shortcut.openQuickCommands',
  focusTerminal: 'shortcut.focusTerminal',
  focusAI: 'shortcut.focusAI',
  lockAI: 'shortcut.lockAI',
  duplicateSession: 'shortcut.duplicateSession',
  terminalSearch: 'shortcut.terminalSearch',
  openSettings: 'shortcut.openSettings',
  copy: 'shortcut.copy',
  paste: 'shortcut.paste',
  toggleLineNumbers: 'shortcut.toggleLineNumbers',
  toggleTimestamps: 'shortcut.toggleTimestamps',
  zoomFontIn: 'shortcut.zoomFontIn',
  zoomFontOut: 'shortcut.zoomFontOut',
}

export const DEFAULT_KEYBOARD: KeyboardSettings = {
  nextTab: { ctrl: true, shift: false, alt: false, key: 'tab' },
  prevTab: { ctrl: true, shift: true, alt: false, key: 'tab' },
  newConnection: { ctrl: true, shift: true, alt: false, key: 'n' },
  toggleSidebar: { ctrl: true, shift: true, alt: false, key: 'h' },
  openQuickCommands: { ctrl: true, shift: true, alt: false, key: 'm' },
  focusTerminal: { ctrl: true, shift: true, alt: false, key: 'j' },
  focusAI: { ctrl: true, shift: true, alt: false, key: 'k' },
  closePanel: { ctrl: true, shift: true, alt: false, key: 'q' },
  maximizePanel: { ctrl: true, shift: true, alt: false, key: 'enter' },
  navigatePrev: { ctrl: false, shift: false, alt: true, key: 'arrowleft' },
  navigateNext: { ctrl: false, shift: false, alt: true, key: 'arrowright' },
  lockAI: { ctrl: true, shift: true, alt: false, key: 'l' },
  duplicateSession: { ctrl: true, shift: true, alt: false, key: 'd' },
  terminalSearch: { ctrl: true, shift: true, alt: false, key: 'f' },
  openSettings: { ctrl: true, shift: false, alt: false, key: ',' },
  copy: { ctrl: true, shift: true, alt: false, key: 'c' },
  paste: { ctrl: true, shift: true, alt: false, key: 'v' },
  toggleLineNumbers: { ctrl: true, shift: true, alt: false, key: 'g' },
  toggleTimestamps: { ctrl: true, shift: true, alt: false, key: 't' },
  zoomFontIn: { ctrl: true, shift: false, alt: false, key: '=' },
  zoomFontOut: { ctrl: true, shift: false, alt: false, key: '-' },
  trayShowHide: { ctrl: true, shift: false, alt: false, key: 'm' },
}

// Older settings.json files may carry a `meta` flag on bindings. Ctrl now
// covers Cmd on macOS, so legacy meta-only bindings migrate to ctrl and the
// flag itself is dropped; untouched actions fall back to their platform
// defaults.
export function normalizeKeyBindings(kb: KeyboardSettings): KeyboardSettings {
  const out = { ...DEFAULT_KEYBOARD, ...kb } as KeyboardSettings & Record<string, KeyBinding | undefined>
  for (const key of Object.keys(out)) {
    const b = out[key] as (KeyBinding & { meta?: boolean }) | undefined
    if (b && b.meta) {
      const migrated = { ...b, ctrl: true }
      delete migrated.meta
      out[key] = migrated
    }
  }
  return out
}

export interface SFTPBookmarks {
  localPaths: string[]
  remotePaths: string[]
}

export interface AppSettings {
  theme: Theme
  language: Language
  /** UI design baseline in px; the rem root derives from it (uiFontSize/12*16). */
  uiFontSize: number
  terminal: TerminalSettings
  ai: AISettings
  keyboard: KeyboardSettings
  autoCheckUpdate: boolean
  // Update source for checks and downloads: "auto" picks by UI language with
  // cross-source fallback; "github" forces the official source; "gitee"
  // forces the domestic mirror.
  updateSource: 'auto' | 'github' | 'gitee'
  closeTabPrompt: boolean
  closeAppPrompt: boolean
  sftpBookmarks: SFTPBookmarks
  // Whether the dual-pane SFTP tab's transfer panel starts out visible.
  // The panel auto-pops on every new transfer task regardless of this flag;
  // the flag only remembers the last visibility across restarts.
  sftpTransferPanelVisible: boolean
  customTerminalThemes: CustomTerminalTheme[]
  defaultLocalShell: string
  // Which side of the tab the close (X) button sits on.
  tabCloseButton: 'left' | 'right'
  // Whether the per-tab numeric shortcut hint (e.g. Ctrl+1) is drawn on the
  // tab itself; the hover tooltips elsewhere are unaffected.
  showTabShortcutHints: boolean
  // How the host list opens the connection menu: hover "⋯"/star buttons
  // ("button") or right-click only, with the hover buttons hidden
  // ("rightclick"). The right-click menu works in both modes.
  hostListMenuStyle: 'button' | 'rightclick'
  // Which connection-sidebar tab icons are visible, keyed by view id.
  // Missing keys fall back to SIDEBAR_TAB_DEFAULTS.
  sidebarTabs: Record<string, boolean>
}

// Default visibility per sidebar view. "connections" is the primary view and
// is always shown (never hidden by either the settings card or the tab-strip
// context menu); every tab ships visible by default.
export const SIDEBAR_TAB_DEFAULTS: Record<string, boolean> = {
  connections: true,
  files: true,
  monitor: true,
  tunnels: true,
  quickCommands: true,
  history: true,
  personalization: true,
}

// Canonical sidebar tab order shared by the tab-strip context menu and the
// Settings card. `labelKey` is the existing i18n key for each tab's title.
export const SIDEBAR_TAB_ORDER: { key: string; labelKey: string }[] = [
  { key: 'connections', labelKey: 'header.connections' },
  { key: 'files', labelKey: 'header.files' },
  { key: 'monitor', labelKey: 'header.monitor' },
  { key: 'tunnels', labelKey: 'tunnels.tunnelsTab' },
  { key: 'quickCommands', labelKey: 'quickCommands.quickCommandsTab' },
  { key: 'history', labelKey: 'quickCommands.historyTab' },
  { key: 'personalization', labelKey: 'sidebar.personalization' },
]

// Platform UI text baseline: macOS native text runs larger than the
// Windows 12px design size. Mirrors index.html's pre-paint detection.
export const DEFAULT_UI_FONT_SIZE = /Mac|iPhone|iPad|iPod/.test(navigator.platform) ? 14 : 12

export const DEFAULT_SETTINGS: AppSettings = {
  theme: 'dark',
  language: 'system',
  uiFontSize: DEFAULT_UI_FONT_SIZE,
  terminal: {
    theme: FOLLOW_APP_THEME,
    fontFamily: 'JetBrains Mono Variable',
    fallbackFont: '',
    fontWeight: 400,
    fontSize: 14,
    selectionAction: 'none',
    rightClickAction: 'menu',
    middleClickAction: 'paste',
    maxHistoryLines: 2500,
    smartCompletion: true,
    aiTranscription: true,
    highlightEnabled: true,
    cursorBlink: true,
    ctrlWheelZoom: true,
    cursorStyle: 'block',
    minimumContrast: 4.5,
    sessionLogDir: '',
    zmodemDownloadDir: '',
    sessionLogFilename: '%S_%H_%M%D_%h%m.log',
    wordSeparator: '\\ :;~`!@#$%^&*()=+|[]{}\'",<>?',
    showLineNumbers: false,
    showTimestamps: false,
    timestampFormat: 'HH:mm:ss'
  },
  ai: {
    maxTurns: 20,
    models: [
      {
        id: 'model-default',
        name: 'Default',
        apiKey: '',
        baseURL: 'https://api.openai.com/v1',
        model: 'gpt-4o',
        protocol: 'anthropic' as const
      }
    ],
    activeModelId: 'model-default'
  },
  keyboard: { ...DEFAULT_KEYBOARD },
  autoCheckUpdate: true,
  updateSource: 'auto',
  closeTabPrompt: true,
  closeAppPrompt: true,
  sftpBookmarks: {
    localPaths: [],
    remotePaths: []
  },
  sftpTransferPanelVisible: false,
  customTerminalThemes: [],
  defaultLocalShell: '',
  tabCloseButton: 'left',
  showTabShortcutHints: true,
  hostListMenuStyle: 'button',
  sidebarTabs: { ...SIDEBAR_TAB_DEFAULTS }
}

export interface TerminalThemeEntry { label: string; value: string; type: 'dark' | 'light' }
export const TERMINAL_THEMES: TerminalThemeEntry[] = [
  { label: 'Terminal Dark', value: 'terminal-dark', type: 'dark' },
  { label: 'Terminal Light', value: 'terminal-light', type: 'light' },
  { label: 'Solarized Dark', value: 'solarized-dark', type: 'dark' },
  { label: 'Solarized Light', value: 'solarized-light', type: 'light' },
  { label: 'Monokai', value: 'monokai', type: 'dark' },
  { label: 'Dracula', value: 'dracula', type: 'dark' },
  { label: 'Molokai', value: 'molokai', type: 'dark' },
  { label: 'Tomorrow Night', value: 'tomorrow-night', type: 'dark' },
  { label: 'Tomorrow Night Bright', value: 'tomorrow-night-bright', type: 'dark' },
  { label: 'Tomorrow', value: 'tomorrow', type: 'light' },
  { label: 'One Dark', value: 'one-dark', type: 'dark' },
  { label: 'One Light', value: 'one-light', type: 'light' },
  { label: 'GitHub Dark', value: 'github-dark', type: 'dark' },
  { label: 'GitHub Light', value: 'github-light', type: 'light' },
  { label: 'Gotham', value: 'gotham', type: 'dark' },
  { label: 'Hybrid', value: 'hybrid', type: 'dark' },
  { label: 'Nord', value: 'nord', type: 'dark' },
  { label: 'Gruvbox Dark', value: 'gruvbox-dark', type: 'dark' },
  { label: 'Gruvbox Light', value: 'gruvbox-light', type: 'light' },
  { label: 'Catppuccin Mocha', value: 'catppuccin-mocha', type: 'dark' },
  { label: 'Catppuccin Latte', value: 'catppuccin-latte', type: 'light' },
  { label: 'Tokyo Night', value: 'tokyo-night', type: 'dark' },
  { label: 'Tokyo Day', value: 'tokyo-day', type: 'light' },
  { label: 'Rosé Pine', value: 'rose-pine', type: 'dark' },
  { label: 'Rosé Pine Dawn', value: 'rose-pine-dawn', type: 'light' },
  { label: 'Everforest Dark', value: 'everforest-dark', type: 'dark' },
  { label: 'Everforest Light', value: 'everforest-light', type: 'light' },
  // Popular SSH client defaults
  { label: 'Xshell XTerm', value: 'xshell-xterm', type: 'dark' },
  { label: 'Xshell ANSI on Black', value: 'xshell-ansi-black', type: 'dark' },
  { label: 'Xshell New Black', value: 'xshell-new-black', type: 'dark' },
  { label: 'MobaXterm Default', value: 'mobaxterm-default', type: 'dark' },
  { label: 'MobaXterm Ubuntu', value: 'mobaxterm-ubuntu', type: 'dark' },
  { label: 'FinalShell Dark', value: 'finalshell-dark', type: 'dark' },
  { label: 'FinalShell Light', value: 'finalshell-light', type: 'light' },
]

export const FONT_OPTIONS: { label: string; value: string }[] = [
  { label: 'Consolas', value: 'Consolas, "Courier New", monospace' },
  { label: 'Courier New', value: '"Courier New", Courier, monospace' },
  { label: 'Monaco', value: 'Monaco, "Courier New", monospace' },
  { label: 'Fira Code', value: '"Fira Code", monospace' },
  { label: 'JetBrains Mono', value: '"JetBrains Mono", monospace' },
  { label: 'Source Code Pro', value: '"Source Code Pro", monospace' }
]

// Terminal font-weight presets. `labelKey` is an i18n key (the option text is
// translated via `t(labelKey)`); the value is the CSS/JS number passed to
// xterm.js — the bundled JetBrains Mono Variable honors each exactly, fixed
// fonts snap to the nearest available weight.
export const FONT_WEIGHT_OPTIONS: { labelKey: string; value: number }[] = [
  { labelKey: 'settings.weightNormal', value: 400 },
  { labelKey: 'settings.weightMedium', value: 500 },
  { labelKey: 'settings.weightSemiBold', value: 600 },
  { labelKey: 'settings.weightBold', value: 700 }
]

export const SELECTION_ACTIONS: { label: string; value: TerminalSettings['selectionAction'] }[] = [
  { label: 'None', value: 'none' },
  { label: 'Copy to clipboard', value: 'copy' }
]

// Timestamp column display formats. `value` is a tokenized template consumed
// by formatTimestampMs (see utils/terminalGutter.ts); the option text is its
// i18n label.
export const TIMESTAMP_FORMATS: { labelKey: string; value: string; sample: string }[] = [
  { labelKey: 'settings.timestampFormatTime', value: 'HH:mm:ss', sample: '12:34:56' },
  { labelKey: 'settings.timestampFormatDateTime', value: 'YYYY-MM-DD HH:mm:ss', sample: '2026-08-18 12:34:56' },
]

export const CURSOR_STYLES: { labelKey: string; value: TerminalSettings['cursorStyle'] }[] = [
  { labelKey: 'settings.cursorStyleBlock', value: 'block' },
  { labelKey: 'settings.cursorStyleUnderline', value: 'underline' },
  { labelKey: 'settings.cursorStyleBar', value: 'bar' }
]

export const RIGHT_CLICK_ACTIONS: { label: string; value: TerminalSettings['rightClickAction'] }[] = [
  { label: 'Show context menu', value: 'menu' },
  { label: 'Paste from clipboard', value: 'paste' }
]

export const LANGUAGE_OPTIONS: { value: Locale; label: string; native: string }[] = [
  { value: 'zh-CN', label: '简体中文', native: '简体中文' },
  { value: 'zh-TW', label: '繁體中文', native: '繁體中文' },
  { value: 'en', label: 'English', native: 'English' },
  { value: 'ja', label: '日本語', native: '日本語' },
  { value: 'ko', label: '한국어', native: '한국어' },
  { value: 'de', label: 'Deutsch', native: 'Deutsch' },
  { value: 'es', label: 'Español', native: 'Español' },
  { value: 'fr', label: 'Français', native: 'Français' },
  { value: 'ru', label: 'Русский', native: 'Русский' },
]

export interface UpdateAsset {
  name: string
  url: string
  sha256: string
  source: 'github' | 'gitee'
}

export interface UpdateInfo {
  hasUpdate: boolean
  current: string
  latest: string
  releaseUrl: string
  changelog: string
  assets: UpdateAsset[]
}
