import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import type { Ref } from 'vue'
import { Terminal } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import { SearchAddon } from '@xterm/addon-search'
import { WebLinksAddon } from '@xterm/addon-web-links'
import '@xterm/xterm/css/xterm.css'
import { SessionResize } from '../../bindings/easyaiot/terminal/app'
import { queuedSessionWrite } from '../services/sessionWriter'
import { useSettingsStore } from '../stores/settingsStore'
import { useLocalStateStore } from '../stores/localStateStore'
import { useSessionStore } from '../stores/sessionStore'
import { stripCursorBlink } from '../utils/cursor'
import { formatFontFamily } from '../utils/formatFontFamily'
import { resolveXtermBackground, applyTerminalBgVar, resolveTerminalThemeName } from './useTerminalTheme'
import { Browser, Events } from '@wailsio/runtime'
import type { CustomTerminalTheme } from '../types/settings'

export interface UseTerminalOptions {
  onSessionData?: (data: string) => void
  onSessionStatus?: (status: string) => void
}

export interface UseTerminalReturn {
  terminalRef: Ref<HTMLDivElement | undefined>
  terminal: Terminal | null
  fitAddon: FitAddon | null
  searchAddon: SearchAddon | null
  write: (data: string) => void
  resize: () => void
  getSelection: () => string
  clear: () => void
  focus: () => void
  setRetryOnEnter: (value: boolean) => void
}

export function getXtermTheme(name: string, customThemes?: CustomTerminalTheme[]): any {
  const custom = customThemes?.find(t => t.id === name)
  if (custom) {
    const c = custom.colors
    return {
      background: c.background,
      foreground: c.foreground,
      cursor: c.cursor,
      selectionBackground: c.selection,
      black: c.black,
      red: c.red,
      green: c.green,
      yellow: c.yellow,
      blue: c.blue,
      magenta: c.magenta,
      cyan: c.cyan,
      white: c.white,
      brightBlack: c.brightBlack,
      brightRed: c.brightRed,
      brightGreen: c.brightGreen,
      brightYellow: c.brightYellow,
      brightBlue: c.brightBlue,
      brightMagenta: c.brightMagenta,
      brightCyan: c.brightCyan,
      brightWhite: c.brightWhite
    }
  }
  const base = {
    background: '#18181b',
    foreground: '#e4e4e7',
    cursor: '#22d3ee',
    selectionBackground: 'rgba(34, 211, 238, 0.2)',
    black: '#3f3f46',
    red: '#f87171',
    green: '#34d399',
    yellow: '#fbbf24',
    blue: '#60a5fa',
    magenta: '#c084fc',
    cyan: '#22d3ee',
    white: '#b0b0b8',
    brightBlack: '#666670',
    brightRed: '#fca5a5',
    brightGreen: '#6ee7b7',
    brightYellow: '#fde68a',
    brightBlue: '#93c5fd',
    brightMagenta: '#d8b4fe',
    brightCyan: '#67e8f9',
    brightWhite: '#d0d0d8'
  }
  switch (name) {
    case 'terminal-dark':
      return base
    case 'terminal-light':
      // Bright canvas (matches the light app chrome's #f6f8fb banding) with a
      // GitHub-Light-inspired ANSI set: saturated enough to read on white,
      // muted enough to stay professional. brightWhite stays darker than
      // white on purpose — text asking for bright white must stay visible.
      return {
        background: '#f9fafc',
        foreground: '#24292f',
        cursor: '#0e7490',
        cursorAccent: '#ffffff',
        selectionBackground: 'rgba(14, 116, 144, 0.16)',
        black: '#24292f',
        red: '#cf222e',
        green: '#116329',
        yellow: '#9a6700',
        blue: '#0969da',
        magenta: '#8250df',
        cyan: '#0e7490',
        white: '#6e7781',
        brightBlack: '#57606a',
        brightRed: '#a40e26',
        brightGreen: '#1a7f37',
        brightYellow: '#bf8700',
        brightBlue: '#218bff',
        brightMagenta: '#a475f9',
        brightCyan: '#0898b8',
        brightWhite: '#8c959f'
      }
    case 'solarized-dark':
      return {
        background: '#002b36',
        foreground: '#839496',
        cursor: '#93a1a1',
        selectionBackground: 'rgba(147, 161, 161, 0.3)',
        black: '#073642',
        red: '#dc322f',
        green: '#859900',
        yellow: '#b58900',
        blue: '#268bd2',
        magenta: '#d33682',
        cyan: '#2aa198',
        white: '#eee8d5',
        brightBlack: '#002b36',
        brightRed: '#cb4b16',
        brightGreen: '#586e75',
        brightYellow: '#657b83',
        brightBlue: '#839496',
        brightMagenta: '#6c71c4',
        brightCyan: '#93a1a1',
        brightWhite: '#fdf6e3'
      }
    case 'solarized-light':
      return {
        background: '#fdf6e3',
        foreground: '#657b83',
        cursor: '#586e75',
        selectionBackground: 'rgba(88, 110, 117, 0.3)',
        black: '#002b36',
        red: '#dc322f',
        green: '#859900',
        yellow: '#b58900',
        blue: '#268bd2',
        magenta: '#d33682',
        cyan: '#2aa198',
        white: '#073642',
        brightBlack: '#eee8d5',
        brightRed: '#cb4b16',
        brightGreen: '#93a1a1',
        brightYellow: '#839496',
        brightBlue: '#657b83',
        brightMagenta: '#6c71c4',
        brightCyan: '#586e75',
        brightWhite: '#1e1e1e'
      }
    case 'monokai':
      return {
        background: '#272822',
        foreground: '#f8f8f2',
        cursor: '#f8f8f0',
        selectionBackground: 'rgba(248, 248, 240, 0.2)',
        black: '#272822',
        red: '#f92672',
        green: '#a6e22e',
        yellow: '#f4bf75',
        blue: '#66d9ef',
        magenta: '#ae81ff',
        cyan: '#a1efe4',
        white: '#f8f8f2',
        brightBlack: '#75715e',
        brightRed: '#f92672',
        brightGreen: '#a6e22e',
        brightYellow: '#f4bf75',
        brightBlue: '#66d9ef',
        brightMagenta: '#ae81ff',
        brightCyan: '#a1efe4',
        brightWhite: '#f9f8f5'
      }
    case 'dracula':
      return {
        background: '#282a36',
        foreground: '#f8f8f2',
        cursor: '#f8f8f0',
        selectionBackground: 'rgba(248, 248, 242, 0.2)',
        black: '#21222c', red: '#ff5555', green: '#50fa7b', yellow: '#f1fa8c',
        blue: '#bd93f9', magenta: '#ff79c6', cyan: '#8be9fd', white: '#f8f8f2',
        brightBlack: '#6272a4', brightRed: '#ff6e6e', brightGreen: '#69ff94',
        brightYellow: '#ffffa5', brightBlue: '#d6acff', brightMagenta: '#ff92df',
        brightCyan: '#a4ffff', brightWhite: '#ffffff'
      }
    case 'molokai':
      return {
        background: '#1b1d1e',
        foreground: '#f8f8f2',
        cursor: '#bbbbbb',
        selectionBackground: 'rgba(248, 248, 242, 0.2)',
        black: '#1b1d1e', red: '#f92672', green: '#a6e22e', yellow: '#e6db74',
        blue: '#66d9ef', magenta: '#ae81ff', cyan: '#a1efe4', white: '#f8f8f2',
        brightBlack: '#465457', brightRed: '#ff5995', brightGreen: '#b6e354',
        brightYellow: '#feed6c', brightBlue: '#8cedff', brightMagenta: '#9e6ffe',
        brightCyan: '#899ca1', brightWhite: '#ffffff'
      }
    case 'tomorrow-night':
      return {
        background: '#1d1f21',
        foreground: '#c5c8c6',
        cursor: '#c5c8c6',
        selectionBackground: 'rgba(197, 200, 198, 0.2)',
        black: '#1d1f21', red: '#cc6666', green: '#b5bd68', yellow: '#f0c674',
        blue: '#81a2be', magenta: '#b294bb', cyan: '#8abeb7', white: '#c5c8c6',
        brightBlack: '#969896', brightRed: '#cc6666', brightGreen: '#b5bd68',
        brightYellow: '#f0c674', brightBlue: '#81a2be', brightMagenta: '#b294bb',
        brightCyan: '#8abeb7', brightWhite: '#ffffff'
      }
    case 'tomorrow':
      return { background: '#ffffff', foreground: '#4d4d4c', cursor: '#4d4d4c', selectionBackground: 'rgba(77,77,76,0.2)', black: '#1d1f21', red: '#c82829', green: '#718c00', yellow: '#eab700', blue: '#4271ae', magenta: '#8959a8', cyan: '#3e999f', white: '#8e908c', brightBlack: '#969896', brightRed: '#c82829', brightGreen: '#718c00', brightYellow: '#eab700', brightBlue: '#4271ae', brightMagenta: '#8959a8', brightCyan: '#3e999f', brightWhite: '#4d4d4c' }
    case 'tomorrow-night-bright':
      return {
        background: '#000000',
        foreground: '#eaeaea',
        cursor: '#eaeaea',
        selectionBackground: 'rgba(234, 234, 234, 0.2)',
        black: '#000000', red: '#d54e53', green: '#b9ca4a', yellow: '#e7c547',
        blue: '#7aa6da', magenta: '#c397d8', cyan: '#70c0b1', white: '#eaeaea',
        brightBlack: '#666666', brightRed: '#ff3334', brightGreen: '#9ec400',
        brightYellow: '#e7c547', brightBlue: '#7aa6da', brightMagenta: '#b77ee0',
        brightCyan: '#54ced6', brightWhite: '#ffffff'
      }
    case 'one-dark':
      return {
        background: '#282c34',
        foreground: '#abb2bf',
        cursor: '#528bff',
        selectionBackground: 'rgba(171, 178, 191, 0.2)',
        black: '#282c34', red: '#e06c75', green: '#98c379', yellow: '#e5c07b',
        blue: '#61afef', magenta: '#c678dd', cyan: '#56b6c2', white: '#abb2bf',
        brightBlack: '#545862', brightRed: '#e06c75', brightGreen: '#98c379',
        brightYellow: '#e5c07b', brightBlue: '#61afef', brightMagenta: '#c678dd',
        brightCyan: '#56b6c2', brightWhite: '#c8ccd4'
      }
    case 'one-light':
      return {
        background: '#fafafa',
        foreground: '#383a42',
        cursor: '#526fff',
        selectionBackground: 'rgba(56, 58, 66, 0.2)',
        black: '#383a42', red: '#e45649', green: '#50a14f', yellow: '#c18401',
        blue: '#4078f2', magenta: '#a626a4', cyan: '#0184bc', white: '#fafafa',
        brightBlack: '#4f525e', brightRed: '#e06c75', brightGreen: '#98c379',
        brightYellow: '#e5c07b', brightBlue: '#61afef', brightMagenta: '#c678dd',
        brightCyan: '#56b6c2', brightWhite: '#ffffff'
      }
    case 'github-dark':
      return {
        background: '#0d1117',
        foreground: '#c9d1d9',
        cursor: '#c9d1d9',
        selectionBackground: 'rgba(201, 209, 217, 0.2)',
        black: '#0d1117', red: '#ff7b72', green: '#3fb950', yellow: '#d29922',
        blue: '#58a6ff', magenta: '#bc8cff', cyan: '#39c5cf', white: '#b1bac4',
        brightBlack: '#484f58', brightRed: '#ffa198', brightGreen: '#56d364',
        brightYellow: '#e3b341', brightBlue: '#79c0ff', brightMagenta: '#d2a8ff',
        brightCyan: '#56d4dd', brightWhite: '#f0f6fc'
      }
    case 'gotham':
      return {
        background: '#0a0f14',
        foreground: '#98d1ce',
        cursor: '#d3ebe9',
        selectionBackground: 'rgba(152, 209, 206, 0.2)',
        black: '#0a0f14', red: '#c33027', green: '#26a98b', yellow: '#edb54b',
        blue: '#195465', magenta: '#4e5165', cyan: '#33859e', white: '#98d1ce',
        brightBlack: '#10151b', brightRed: '#d26939', brightGreen: '#2a9b72',
        brightYellow: '#f1c83e', brightBlue: '#25525e', brightMagenta: '#696d87',
        brightCyan: '#4d97b1', brightWhite: '#d3ebe9'
      }
    case 'hybrid':
      return {
        background: '#1d1f21',
        foreground: '#c5c8c6',
        cursor: '#c5c8c6',
        selectionBackground: 'rgba(197, 200, 198, 0.2)',
        black: '#282a2e', red: '#a54242', green: '#8c9440', yellow: '#de935f',
        blue: '#5f819d', magenta: '#85678f', cyan: '#5e8d87', white: '#707880',
        brightBlack: '#373b41', brightRed: '#cc6666', brightGreen: '#b5bd68',
        brightYellow: '#f0c674', brightBlue: '#81a2be', brightMagenta: '#b294bb',
        brightCyan: '#8abeb7', brightWhite: '#c5c8c6'
      }
    case 'nord':
      return { background: '#2e3440', foreground: '#d8dee9', cursor: '#d8dee9', selectionBackground: 'rgba(216,222,233,0.2)', black: '#3b4252', red: '#bf616a', green: '#a3be8c', yellow: '#ebcb8b', blue: '#81a1c1', magenta: '#b48ead', cyan: '#88c0d0', white: '#e5e9f0', brightBlack: '#4c566a', brightRed: '#bf616a', brightGreen: '#a3be8c', brightYellow: '#ebcb8b', brightBlue: '#81a1c1', brightMagenta: '#b48ead', brightCyan: '#8fbcbb', brightWhite: '#eceff4' }
    case 'gruvbox-dark':
      return { background: '#282828', foreground: '#ebdbb2', cursor: '#ebdbb2', selectionBackground: 'rgba(235,219,178,0.2)', black: '#282828', red: '#cc241d', green: '#98971a', yellow: '#d79921', blue: '#458588', magenta: '#b16286', cyan: '#689d6a', white: '#a89984', brightBlack: '#928374', brightRed: '#fb4934', brightGreen: '#b8bb26', brightYellow: '#fabd2f', brightBlue: '#83a598', brightMagenta: '#d3869b', brightCyan: '#8ec07c', brightWhite: '#ebdbb2' }
    case 'gruvbox-light':
      return { background: '#fbf1c7', foreground: '#3c3836', cursor: '#3c3836', selectionBackground: 'rgba(60,56,54,0.2)', black: '#fbf1c7', red: '#cc241d', green: '#98971a', yellow: '#d79921', blue: '#458588', magenta: '#b16286', cyan: '#689d6a', white: '#7c6f64', brightBlack: '#928374', brightRed: '#9d0006', brightGreen: '#79740e', brightYellow: '#b57614', brightBlue: '#076678', brightMagenta: '#8f3f71', brightCyan: '#427b58', brightWhite: '#3c3836' }
    case 'catppuccin-mocha':
      return { background: '#1e1e2e', foreground: '#cdd6f4', cursor: '#f5e0dc', selectionBackground: 'rgba(205,214,244,0.2)', black: '#45475a', red: '#f38ba8', green: '#a6e3a1', yellow: '#f9e2af', blue: '#89b4fa', magenta: '#f5c2e7', cyan: '#94e2d5', white: '#bac2de', brightBlack: '#585b70', brightRed: '#f38ba8', brightGreen: '#a6e3a1', brightYellow: '#f9e2af', brightBlue: '#89b4fa', brightMagenta: '#f5c2e7', brightCyan: '#94e2d5', brightWhite: '#a6adc8' }
    case 'catppuccin-latte':
      return { background: '#eff1f5', foreground: '#4c4f69', cursor: '#dc8a78', selectionBackground: 'rgba(76,79,105,0.2)', black: '#5c5f77', red: '#d20f39', green: '#40a02b', yellow: '#df8e1d', blue: '#1e66f5', magenta: '#ea76cb', cyan: '#179299', white: '#acb0be', brightBlack: '#6c6f85', brightRed: '#d20f39', brightGreen: '#40a02b', brightYellow: '#df8e1d', brightBlue: '#1e66f5', brightMagenta: '#ea76cb', brightCyan: '#179299', brightWhite: '#bcc0cc' }
    case 'tokyo-night':
      return { background: '#1a1b26', foreground: '#c0caf5', cursor: '#c0caf5', selectionBackground: 'rgba(192,202,245,0.2)', black: '#15161e', red: '#f7768e', green: '#9ece6a', yellow: '#e0af68', blue: '#7aa2f7', magenta: '#bb9af7', cyan: '#7dcfff', white: '#a9b1d6', brightBlack: '#414868', brightRed: '#f7768e', brightGreen: '#9ece6a', brightYellow: '#e0af68', brightBlue: '#7aa2f7', brightMagenta: '#bb9af7', brightCyan: '#7dcfff', brightWhite: '#c0caf5' }
    case 'tokyo-day':
      return { background: '#f8fafc', foreground: '#334155', cursor: '#334155', selectionBackground: 'rgba(51,65,85,0.2)', black: '#e2e8f0', red: '#ef4444', green: '#22c55e', yellow: '#eab308', blue: '#3b82f6', magenta: '#8b5cf6', cyan: '#06b6d4', white: '#64748b', brightBlack: '#94a3b8', brightRed: '#ef4444', brightGreen: '#22c55e', brightYellow: '#eab308', brightBlue: '#3b82f6', brightMagenta: '#8b5cf6', brightCyan: '#06b6d4', brightWhite: '#1e293b' }
    case 'rose-pine':
      return { background: '#191724', foreground: '#e0def4', cursor: '#e0def4', selectionBackground: 'rgba(224,222,244,0.2)', black: '#26233a', red: '#eb6f92', green: '#31748f', yellow: '#f6c177', blue: '#9ccfd8', magenta: '#c4a7e7', cyan: '#ebbcba', white: '#e0def4', brightBlack: '#6e6a86', brightRed: '#eb6f92', brightGreen: '#31748f', brightYellow: '#f6c177', brightBlue: '#9ccfd8', brightMagenta: '#c4a7e7', brightCyan: '#ebbcba', brightWhite: '#e0def4' }
    case 'rose-pine-dawn':
      return { background: '#faf4ed', foreground: '#575279', cursor: '#575279', selectionBackground: 'rgba(87,82,121,0.2)', black: '#f2e9e1', red: '#b4637a', green: '#286983', yellow: '#ea9d34', blue: '#56949f', magenta: '#907aa9', cyan: '#d7827e', white: '#575279', brightBlack: '#9893a5', brightRed: '#b4637a', brightGreen: '#286983', brightYellow: '#ea9d34', brightBlue: '#56949f', brightMagenta: '#907aa9', brightCyan: '#d7827e', brightWhite: '#575279' }
    case 'github-light':
      return { background: '#ffffff', foreground: '#24292f', cursor: '#24292f', selectionBackground: 'rgba(36,41,47,0.2)', black: '#ffffff', red: '#cf222e', green: '#1a7f37', yellow: '#9a6700', blue: '#0969da', magenta: '#8250df', cyan: '#1b7c83', white: '#6e7781', brightBlack: '#57606a', brightRed: '#a40e26', brightGreen: '#116329', brightYellow: '#633d01', brightBlue: '#0550ae', brightMagenta: '#7339ac', brightCyan: '#126061', brightWhite: '#24292f' }
    case 'everforest-dark':
      return { background: '#2d353b', foreground: '#d3c6aa', cursor: '#d3c6aa', selectionBackground: 'rgba(211,198,170,0.2)', black: '#475258', red: '#e67e80', green: '#a7c080', yellow: '#dbbc7f', blue: '#7fbbb3', magenta: '#d699b6', cyan: '#83c092', white: '#d3c6aa', brightBlack: '#475258', brightRed: '#e67e80', brightGreen: '#a7c080', brightYellow: '#dbbc7f', brightBlue: '#7fbbb3', brightMagenta: '#d699b6', brightCyan: '#83c092', brightWhite: '#d3c6aa' }
    case 'everforest-light':
      return { background: '#fdf6e3', foreground: '#5c6a72', cursor: '#5c6a72', selectionBackground: 'rgba(92,106,114,0.2)', black: '#fdf6e3', red: '#f85552', green: '#8da101', yellow: '#dfa000', blue: '#3a94c5', magenta: '#df69ba', cyan: '#35a77c', white: '#5c6a72', brightBlack: '#a6b0a0', brightRed: '#f85552', brightGreen: '#8da101', brightYellow: '#dfa000', brightBlue: '#3a94c5', brightMagenta: '#df69ba', brightCyan: '#35a77c', brightWhite: '#5c6a72' }
    // Xshell built-in schemes (from ColorScheme Files *.scs)
    case 'xshell-xterm':
      return {
        background: '#000000', foreground: '#e5e5e5', cursor: '#ffffff',
        selectionBackground: 'rgba(229,229,229,0.25)',
        black: '#000000', red: '#bb0000', green: '#006400', yellow: '#c8af00',
        blue: '#1e90f5', magenta: '#bb00bb', cyan: '#00cdcd', white: '#ebebeb',
        brightBlack: '#555555', brightRed: '#ff5555', brightGreen: '#55ff55',
        brightYellow: '#fff555', brightBlue: '#50beff', brightMagenta: '#ff55ff',
        brightCyan: '#55ffff', brightWhite: '#ffffff'
      }
    case 'xshell-ansi-black':
      return {
        background: '#000000', foreground: '#ffffff', cursor: '#ffffff',
        selectionBackground: 'rgba(255,255,255,0.2)',
        black: '#000000', red: '#c00000', green: '#00c000', yellow: '#c0c000',
        blue: '#0000c0', magenta: '#c000c0', cyan: '#00c0c0', white: '#c0c0c0',
        brightBlack: '#808080', brightRed: '#ff0000', brightGreen: '#00ff00',
        brightYellow: '#ffff00', brightBlue: '#0000ff', brightMagenta: '#ff00ff',
        brightCyan: '#00ffff', brightWhite: '#ffffff'
      }
    case 'xshell-new-black':
      return {
        background: '#242424', foreground: '#f2f2f2', cursor: '#ffffff',
        selectionBackground: 'rgba(242,242,242,0.2)',
        black: '#36342e', red: '#a56434', green: '#008000', yellow: '#999606',
        blue: '#4646ff', magenta: '#7b5175', cyan: '#00a2c4', white: '#cfd8d3',
        brightBlack: '#535755', brightRed: '#cf9e72', brightGreen: '#1cc470',
        brightYellow: '#e2e234', brightBlue: '#6f6ff4', brightMagenta: '#a97ead',
        brightCyan: '#50ebfc', brightWhite: '#eceeee'
      }
    // MobaXterm default ANSI palette (official DefaultColorScheme=0)
    case 'mobaxterm-default':
      return {
        background: '#000000', foreground: '#ececec', cursor: '#b4b4c0',
        selectionBackground: 'rgba(236,236,236,0.2)',
        black: '#000000', red: '#ff6060', green: '#60ff60', yellow: '#ffff36',
        blue: '#6060ff', magenta: '#ff36ff', cyan: '#36ffff', white: '#ececec',
        brightBlack: '#363636', brightRed: '#ff8080', brightGreen: '#80ff80',
        brightYellow: '#ffff80', brightBlue: '#8080ff', brightMagenta: '#ff80ff',
        brightCyan: '#80ffff', brightWhite: '#ffffff'
      }
    // MobaXterm / GNOME Ubuntu terminal style (common built-in alternative)
    case 'mobaxterm-ubuntu':
      return {
        background: '#300a24', foreground: '#eeeeec', cursor: '#ffffff',
        selectionBackground: 'rgba(238,238,236,0.2)',
        black: '#2e3436', red: '#cc0000', green: '#4e9a06', yellow: '#c4a000',
        blue: '#3465a4', magenta: '#75507b', cyan: '#06989a', white: '#d3d7cf',
        brightBlack: '#555753', brightRed: '#ef2929', brightGreen: '#8ae234',
        brightYellow: '#fce94f', brightBlue: '#729fcf', brightMagenta: '#ad7fa8',
        brightCyan: '#34e2e2', brightWhite: '#eeeeec'
      }
    // FinalShell-style defaults (VS Code Dark+/Light aesthetic used by FS default)
    case 'finalshell-dark':
      return {
        background: '#1e1e1e', foreground: '#d4d4d4', cursor: '#aeafad',
        selectionBackground: 'rgba(38,79,120,0.55)',
        black: '#000000', red: '#cd3131', green: '#0dbc79', yellow: '#e5e510',
        blue: '#2472c8', magenta: '#bc3fbc', cyan: '#11a8cd', white: '#e5e5e5',
        brightBlack: '#666666', brightRed: '#f14c4c', brightGreen: '#23d18b',
        brightYellow: '#f5f543', brightBlue: '#3b8eea', brightMagenta: '#d670d6',
        brightCyan: '#29b8db', brightWhite: '#e5e5e5'
      }
    case 'finalshell-light':
      return {
        background: '#ffffff', foreground: '#1e1e1e', cursor: '#000000',
        selectionBackground: 'rgba(0,120,212,0.2)',
        black: '#000000', red: '#cd3131', green: '#00bc00', yellow: '#949800',
        blue: '#0451a5', magenta: '#bc05bc', cyan: '#0598bc', white: '#555555',
        brightBlack: '#666666', brightRed: '#cd3131', brightGreen: '#14ce14',
        brightYellow: '#b5ba00', brightBlue: '#0451a5', brightMagenta: '#bc05bc',
        brightCyan: '#0598bc', brightWhite: '#a5a5a5'
      }
    default:
      return base
  }
}

export function useTerminal(
  getSessionId: () => string | null | undefined,
  options?: UseTerminalOptions
): UseTerminalReturn {
  const settingsStore = useSettingsStore()
  const sessionStore = useSessionStore()

  const terminalRef = ref<HTMLDivElement>()
  let terminal: Terminal | null = null
  let fitAddon: FitAddon | null = null
  let searchAddon: SearchAddon | null = null
  // Track loaded addons for unmount dispose; some (e.g. WebLinks) leave
  // host elements behind after terminal.dispose() in older xterm.
  const loadedAddons: Array<{ dispose?: () => void }> = []
  let resizeObserver: ResizeObserver | null = null
  let intersectionObserver: IntersectionObserver | null = null
  let unsubscribe: (() => void) | null = null
  let statusUnsubscribe: (() => void) | null = null
  let onDocumentMouseUp: (() => void) | null = null
  let onMouseDownGlobal: ((e: MouseEvent) => void) | null = null

  let resizeTimer: ReturnType<typeof setTimeout> | null = null
  let isResizing = false
  let splitResizing = false
  let suppressResizeUntil = 0
  let retryOnEnter = false
  let hoverEl: HTMLDivElement | null = null
  let cachedCellWidth = 0
  let cachedCellHeight = 0
  let cachedFontKey = ''

  function getTerminalOptions() {
    const ts = settingsStore.settings.terminal
    const ls = useLocalStateStore()
    const themeName = resolveTerminalThemeName(ts.theme, settingsStore.resolvedAppTheme)
    const theme = resolveXtermBackground(
      getXtermTheme(themeName, settingsStore.settings.customTerminalThemes),
      ls.state.backgroundEnabled,
      ls.state.backgroundImage
    )
    return {
      fontSize: ts.fontSize || 13,
      fontFamily: formatFontFamily(ts.fontFamily, ts.fallbackFont),
      fontWeight: ts.fontWeight || 400,
      theme,
      cursorBlink: ts.cursorBlink ?? true,
      rightClickSelectsWord: false,
      scrollback: ts.maxHistoryLines || 2500,
      allowProposedApi: true,
      allowTransparency: true,
      wordSeparator: ts.wordSeparator || '\\ :;~`!@#$%^&*()=+|[]{}\'",<>?',
    }
  }

  // Wrap stripCursorBlink with current blink setting for convenience
  function stripBlink(data: string): string {
    return stripCursorBlink(data, settingsStore.settings.terminal.cursorBlink ?? true)
  }

  function resize() {
    const sessionId = getSessionId()
    if (!terminal || !fitAddon || !sessionId) return
    const el = terminalRef.value
    if (!el) return

    // Use getBoundingClientRect to get actual rendered size (bypasses
    // getComputedStyle caching issues during flex shrink).
    const rect = el.getBoundingClientRect()

    // Read xterm's internally-measured character dimensions.
    // Use try/catch because these are internal APIs that may change between versions.
    let cellWidth = 0
    let cellHeight = 0
    const fontKey = `${terminal.options.fontSize}|${terminal.options.fontFamily}`
    if (fontKey === cachedFontKey && cachedCellWidth > 0 && cachedCellHeight > 0) {
      cellWidth = cachedCellWidth
      cellHeight = cachedCellHeight
    } else {
      try {
        const core = (terminal as any)._core
        const dims = core?._renderService?.dimensions
        if (dims) {
          cellWidth = dims.css?.cell?.width || 0
          cellHeight = dims.css?.cell?.height || 0
        }
      } catch {
        cellWidth = 0
        cellHeight = 0
      }
      if (cellWidth > 0 && cellHeight > 0) {
        cachedCellWidth = cellWidth
        cachedCellHeight = cellHeight
        cachedFontKey = fontKey
      }
    }

    if (cellWidth === 0 || cellHeight === 0) {
      // Fallback to FitAddon if char dims aren't ready yet.
      fitAddon.fit()
      if (terminal.cols <= 0 || terminal.rows <= 0) return
      SessionResize(sessionId, terminal.cols, terminal.rows).catch(() => {})
      return
    }

    // Use the container's actual rendered size (rect) to compute cols/rows.
    // terminal.element's clientWidth may not shrink when the container shrinks
    // because xterm's internal screen/canvas width can hold it at the old size.
    const scrollbarWidth = (terminal as any)._core?.viewport?.scrollBarWidth || 0
    const cols = Math.floor((rect.width - scrollbarWidth) / cellWidth)
    const rows = Math.floor(rect.height / cellHeight)
    const newCols = Math.max(2, cols)
    const newRows = Math.max(1, rows)

    if (terminal.cols !== newCols || terminal.rows !== newRows) {
      terminal.resize(newCols, newRows)
      SessionResize(sessionId, newCols, newRows).catch(() => {})
    }
  }

  function write(data: string) {
    terminal?.write(data)
  }

  function getSelection(): string {
    return terminal?.getSelection() || ''
  }

  function clear() {
    terminal?.clear()
  }

  function focus() {
    terminal?.focus()
  }

  function setRetryOnEnter(value: boolean) {
    retryOnEnter = value
  }

  function onWindowResize() {
    const el = terminalRef.value
    if (!el) return
    if (!isResizing) {
      isResizing = true
      el.classList.add('resizing')
    }
    if (resizeTimer) clearTimeout(resizeTimer)
    resizeTimer = setTimeout(() => {
      isResizing = false
      el.classList.remove('resizing')
      resize()
    }, 400)
  }

  function onSplitResizeStart() {
    splitResizing = true
  }

  function onSplitResizeEnd() {
    splitResizing = false
    if (resizeTimer) {
      clearTimeout(resizeTimer)
      resizeTimer = null
    }
    suppressResizeUntil = Date.now() + 200
    nextTick(() => {
      setTimeout(() => {
        // Force layout so getComputedStyle returns up-to-date dimensions
        void terminalRef.value?.offsetWidth
        resize()
      }, 0)
    })
  }

  onMounted(() => {
    if (!terminalRef.value) return

    terminal = new Terminal(getTerminalOptions())

    fitAddon = new FitAddon()
    terminal.loadAddon(fitAddon)
    loadedAddons.push(fitAddon)
    // Register web links addon: underline http/https links, Ctrl+Click to open
    const webLinksAddon = new WebLinksAddon(
      (event, uri) => {
        if (event.ctrlKey || event.metaKey) {
          Browser.OpenURL(uri)
        }
      },
      {
        hover(event, _text, _location) {
          if (!hoverEl) {
            hoverEl = document.createElement('div')
            hoverEl.className = 'xterm-link-tooltip'
            terminal!.element!.appendChild(hoverEl)
          }
          const rect = terminal!.element!.getBoundingClientRect()
          hoverEl.textContent = 'Ctrl + Click to open'
          hoverEl.style.left = (event.clientX - rect.left + 12) + 'px'
          hoverEl.style.top = (event.clientY - rect.top - 28) + 'px'
          hoverEl.style.display = 'block'
        },
        leave() {
          if (hoverEl) {
            hoverEl.style.display = 'none'
          }
        }
      }
    )
    terminal.loadAddon(webLinksAddon)
    loadedAddons.push(webLinksAddon)

    searchAddon = new SearchAddon()
    terminal.loadAddon(searchAddon)
    loadedAddons.push(searchAddon)

    terminal.open(terminalRef.value)
    applyTerminalBgVar(terminal, terminal.options.theme ?? {})
    // Force synchronous layout so grid rows are sized before xterm measures
    void terminalRef.value.offsetHeight
    fitAddon.fit()

    // Restore terminal content from session buffer after tab move/merge
    const sessionId = getSessionId()
    if (sessionId) {
      const history = sessionStore.getData(sessionId)
      if (history) {
        terminal.write(stripBlink(history))
      }
    }

    // Retry resize: after a tab move/merge the layout may not be stable yet,
    // so fitAddon.fit() can compute 0 cols/rows and skip SessionResize.
    ;[100, 300, 600, 1000, 1500].forEach(d => setTimeout(() => resize(), d))

    terminal.onData((data) => {
      if (retryOnEnter && (data === '\r' || data === '\n')) {
        retryOnEnter = false
        if (options?.onSessionStatus) {
          options.onSessionStatus('retry')
        }
        return
      }
      const sid = getSessionId()
      if (sid) {
        queuedSessionWrite(sid, data)
      }
    })

    // Selection action: copy on mouse up (only when a new selection was made).
    // Use mouseDownOnThisTerminal to ensure copy only fires when the user
    // actually started selecting inside this terminal. Without this, clicking
    // another panel (or returning from another app) would trigger copy from
    // this terminal's leftover selection.
    let selectionStartText = ''
    let mouseDownOnThisTerminal = false
    onDocumentMouseUp = () => {
      if (!mouseDownOnThisTerminal) return
      mouseDownOnThisTerminal = false
      if (settingsStore.settings.terminal.selectionAction === 'copy') {
        const text = terminal?.getSelection()
        if (text && text !== selectionStartText) {
          navigator.clipboard.writeText(text)
        }
      }
    }
    document.addEventListener('mouseup', onDocumentMouseUp)
    terminal.element?.addEventListener('mousedown', () => {
      mouseDownOnThisTerminal = true
      selectionStartText = terminal?.getSelection() || ''
    })
    onMouseDownGlobal = (e: MouseEvent) => {
      if (!terminal || !terminal.element?.contains(e.target as Node)) {
        mouseDownOnThisTerminal = false
      }
    }
    document.addEventListener('mousedown', onMouseDownGlobal)

    unsubscribe =Events.On('session:data', (ev) => { const payload: { id: string; data: string } = ev.data; 
      const sid = getSessionId()
      if (payload.id === sid && terminal) {
        // Filter ED3 (erase scrollback). For ED2 (clear screen), replace with
        // newline scrolling + home so that current viewport content is pushed
        // into scrollback before clearing, matching standard terminal behavior.
        let data = stripBlink(payload.data).replace(/\x1b\[3J/g, '')
        if (data.includes('\x1b[2J')) {
          const rows = terminal.rows
          const scrollClear = '\n'.repeat(rows) + '\x1b[H'
          data = data.replace(/\x1b\[H\x1b\[2J/g, scrollClear)
          data = data.replace(/\x1b\[2J/g, scrollClear)
        }
        terminal.write(data)
        if (options?.onSessionData) {
          options.onSessionData(data)
        }
      }
     })

    retryOnEnter = false
    statusUnsubscribe =Events.On('session:status', (ev) => { const payload: { id: string; status: string } = ev.data; 
      const sid = getSessionId()
      if (payload.id !== sid) return
      if (payload.status === 'connected') {
        retryOnEnter = false
        if (options?.onSessionStatus) {
          options.onSessionStatus(payload.status)
        }
        // Force send current terminal size to sync the backend PTY after reconnect.
        const sid = getSessionId()
        if (sid && terminal && terminal.cols > 0 && terminal.rows > 0) {
          SessionResize(sid, terminal.cols, terminal.rows).catch(() => {})
        }
        resize()
      } else if (payload.status === 'error') {
        retryOnEnter = true
        if (options?.onSessionStatus) {
          options.onSessionStatus(payload.status)
        }
        terminal?.write('\r\n\x1b[31mConnection failed. Press Enter to retry.\x1b[0m\r\n')
      } else if (payload.status === 'disconnected') {
        retryOnEnter = true
        if (options?.onSessionStatus) {
          options.onSessionStatus(payload.status)
        }
      } else {
        if (options?.onSessionStatus) {
          options.onSessionStatus(payload.status)
        }
      }
     })

    window.addEventListener('resize', onWindowResize)
    window.addEventListener('split:resize-start', onSplitResizeStart)
    window.addEventListener('split:resize-end', onSplitResizeEnd)

    // Also handle container-only resize (AI sidebar drag, etc.)
    resizeObserver = new ResizeObserver(() => {
      if (isResizing || splitResizing || Date.now() < suppressResizeUntil) return
      const el = terminalRef.value
      if (!el) return
      if (resizeTimer) clearTimeout(resizeTimer)
      resizeTimer = setTimeout(() => resize(), 150)
    })
    resizeObserver.observe(terminalRef.value)

    intersectionObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          resize()
        }
      })
    })
    intersectionObserver.observe(terminalRef.value)
  })

  // Watch sessionId changes to rebind session data
  watch(() => getSessionId(), (newId) => {
    if (newId && terminal) {
      // Restore buffered session data that arrived before bindSession
      const history = sessionStore.getData(newId)
      if (history) {
        terminal.write(stripBlink(history))
      }
      // Retry resize multiple times with longer delays to ensure backend Connect is ready
      const delays = [200, 400, 600, 800, 1000, 1500, 2000]
      delays.forEach((delay) => {
        setTimeout(() => resize(), delay)
      })
    }
  })

  function applyXtermTheme(themeName: string) {
    if (!terminal) return
    const ls = useLocalStateStore()
    const theme = resolveXtermBackground(
      getXtermTheme(resolveTerminalThemeName(themeName, settingsStore.resolvedAppTheme), settingsStore.settings.customTerminalThemes),
      ls.state.backgroundEnabled,
      ls.state.backgroundImage
    )
    terminal.options.theme = theme
    applyTerminalBgVar(terminal, theme)
  }

  // Watch terminal settings changes
  watch(() => settingsStore.settings.terminal, (ts) => {
    if (!terminal) return
    if (ts.fontSize) terminal.options.fontSize = ts.fontSize
    if (ts.fontFamily) terminal.options.fontFamily = formatFontFamily(ts.fontFamily, ts.fallbackFont)
    if (ts.fontWeight) terminal.options.fontWeight = ts.fontWeight
    if (ts.maxHistoryLines) terminal.options.scrollback = ts.maxHistoryLines
    if (ts.theme) applyXtermTheme(ts.theme)
    if (typeof ts.cursorBlink === 'boolean') {
      terminal.options.cursorBlink = ts.cursorBlink
      if (!ts.cursorBlink) terminal.write('\x1b[?12l')
    }
    resize()
  }, { deep: true })

  // Watch for background image toggling to update terminal transparency
  const localStateStore = useLocalStateStore()
  watch(
    () => localStateStore.state.backgroundEnabled,
    () => applyXtermTheme(settingsStore.settings.terminal.theme || 'dark')
  )

  // Re-apply when the app theme flips so FOLLOW_APP_THEME tracks it live.
  watch(
    () => settingsStore.resolvedAppTheme,
    () => applyXtermTheme(settingsStore.settings.terminal.theme || 'dark')
  )

  onUnmounted(() => {
    resizeObserver?.disconnect()
    intersectionObserver?.disconnect()
    // Addons detach listeners through the terminal; dispose them first.
    for (const addon of loadedAddons) {
      try {
        addon.dispose?.()
      } catch {
        // ignore — some addons don't fully implement dispose
      }
    }
    loadedAddons.length = 0
    // Detach the tooltip element the WebLinksAddon may have left behind.
    if (hoverEl && hoverEl.parentElement) {
      hoverEl.parentElement.removeChild(hoverEl)
    }
    hoverEl = null
    terminal?.dispose()
    unsubscribe?.()
    statusUnsubscribe?.()
    if (onDocumentMouseUp) {
      document.removeEventListener('mouseup', onDocumentMouseUp)
      onDocumentMouseUp = null
    }
    if (onMouseDownGlobal) {
      document.removeEventListener('mousedown', onMouseDownGlobal)
      onMouseDownGlobal = null
    }
    window.removeEventListener('resize', onWindowResize)
    window.removeEventListener('split:resize-start', onSplitResizeStart)
    window.removeEventListener('split:resize-end', onSplitResizeEnd)
  })

  return {
    terminalRef,
    terminal,
    fitAddon,
    searchAddon,
    write,
    resize,
    getSelection,
    clear,
    focus,
    setRetryOnEnter
  }
}
