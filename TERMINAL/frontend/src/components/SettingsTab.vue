<template>
  <div class="settings-tab" ref="settingsTabRef" :class="{ narrow: isNarrow }">
    <div class="settings-sidebar" :class="{ collapsed: sidebarCollapsed }">
      <button
        class="sidebar-collapse-btn"
        :title="t('settings.toggleSidebar')"
        @click="sidebarCollapsed = !sidebarCollapsed"
      >
        <el-icon><component :is="sidebarCollapsed ? ChevronRight : ChevronLeft" /></el-icon>
      </button>
      <div
        v-for="cat in categories"
        :key="cat.key"
        class="settings-category"
        :class="{ active: settingsStore.activeCategory === cat.key }"
        @click="settingsStore.activeCategory = cat.key"
      >
        <el-icon class="category-icon"><component :is="cat.icon" /></el-icon>
        <span v-if="!sidebarCollapsed" class="category-label">{{ cat.label }}</span>
      </div>
    </div>

    <div class="settings-panel">
      <!-- 基础设置 -->
      <div v-if="settingsStore.activeCategory === 'basic'" class="settings-section">
        <h2 class="section-title">{{ t('settings.appearance') }}</h2>
        <div class="settings-group">
          <div class="setting-card">
            <div class="setting-info">
              <div class="setting-title">{{ t('settings.theme') }}</div>
              <div class="setting-desc">{{ t('settings.themeDesc') }}</div>
            </div>
            <div class="setting-control">
              <el-select v-model="settingsStore.settings.theme" @change="settingsStore.save()">
                <el-option :label="t('settings.themeDark')" value="dark" />
                <el-option :label="t('settings.themeDeepBlue')" value="deep-blue" />
                <el-option :label="t('settings.themeLight')" value="light" />
                <el-option :label="t('settings.themeSystem')" value="system" />
              </el-select>
            </div>
          </div>

          <div class="setting-card">
            <div class="setting-info">
              <div class="setting-title">{{ t('settings.language') }}</div>
              <div class="setting-desc">{{ t('settings.languageDesc') }}</div>
            </div>
            <div class="setting-control">
              <el-select :model-value="settingsStore.settings.language" @change="settingsStore.updateLanguage">
                <el-option
                  v-for="lang in LANGUAGE_OPTIONS"
                  :key="lang.value"
                  :label="lang.native"
                  :value="lang.value"
                />
                <el-option :label="t('settings.langSystem')" value="system" />
              </el-select>
            </div>
          </div>

          <div class="setting-card">
            <div class="setting-info">
              <div class="setting-title">{{ t('settings.uiFontSize') }}</div>
              <div class="setting-desc">{{ t('settings.uiFontSizeDesc') }}</div>
            </div>
            <div class="setting-control">
              <el-input-number
                v-model="settingsStore.settings.uiFontSize"
                :min="10"
                :max="18"
                :step="1"
                @change="settingsStore.save()"
              />
            </div>
          </div>

          <!-- No OS window title bar on mobile -->
          <div v-if="!isMobile" class="setting-card">
            <div class="setting-info">
              <div class="setting-title">{{ t('settings.systemTitleBar') }}</div>
              <div class="setting-desc">{{ t('settings.systemTitleBarDesc') }}</div>
            </div>
            <div class="setting-control">
              <el-switch
                :model-value="localStateStore.state.systemTitleBar"
                @update:model-value="(v: boolean) => onToggleSystemTitleBar(v)"
              />
            </div>
          </div>

          <div class="setting-card">
            <div class="setting-info">
              <div class="setting-title">{{ t('settings.bgEnable') }}</div>
              <div class="setting-desc">{{ t('settings.bgEnableDesc') }}</div>
            </div>
            <div class="setting-control">
              <el-switch
                :model-value="localStateStore.state.backgroundEnabled"
                @update:model-value="(v: boolean) => localStateStore.update({ backgroundEnabled: v })"
              />
            </div>
          </div>

          <template v-if="localStateStore.state.backgroundEnabled">
            <div class="setting-card">
              <div class="setting-info">
                <div class="setting-title">{{ t('settings.bgImage') }}</div>
              </div>
              <div class="setting-control">
                <div class="bg-image-row">
                  <div
                    v-if="bgPreview"
                    class="bg-thumb"
                    :style="{ backgroundImage: `url('${bgPreview}')` }"
                  ></div>
                  <el-button size="small" @click="chooseBackground">{{ t('settings.bgChoose') }}</el-button>
                  <el-button
                    v-if="localStateStore.state.backgroundImage"
                    size="small"
                    @click="clearBackground"
                  >{{ t('settings.bgClear') }}</el-button>
                </div>
              </div>
            </div>

            <div class="setting-card">
              <div class="setting-info">
                <div class="setting-title">{{ t('settings.bgOpacity') }}</div>
              </div>
              <div class="setting-control">
                <el-slider
                  :model-value="localStateStore.state.backgroundOpacity"
                  :min="0" :max="100"
                  @update:model-value="(v: number) => localStateStore.update({ backgroundOpacity: v as number })"
                />
              </div>
            </div>

            <div class="setting-card">
              <div class="setting-info">
                <div class="setting-title">{{ t('settings.bgBlur') }}</div>
              </div>
              <div class="setting-control">
                <el-slider
                  :model-value="localStateStore.state.backgroundBlur"
                  :min="0" :max="20"
                  @update:model-value="(v: number) => localStateStore.update({ backgroundBlur: v as number })"
                />
              </div>
            </div>

            <div class="setting-card">
              <div class="setting-info">
                <div class="setting-title">{{ t('settings.bgFit') }}</div>
              </div>
              <div class="setting-control">
                <el-select
                  :model-value="localStateStore.state.backgroundFit"
                  @update:model-value="(v: string) => localStateStore.update({ backgroundFit: v })"
                >
                  <el-option :label="t('settings.bgFitCover')" value="cover" />
                  <el-option :label="t('settings.bgFitContain')" value="contain" />
                  <el-option :label="t('settings.bgFitCenter')" value="center" />
                  <el-option :label="t('settings.bgFitTile')" value="tile" />
                </el-select>
              </div>
            </div>
          </template>

          <div class="setting-card">
            <div class="setting-info">
              <div class="setting-title">{{ t('settings.tabCloseButton') }}</div>
              <div class="setting-desc">{{ t('settings.tabCloseButtonDesc') }}</div>
            </div>
            <div class="setting-control">
              <el-select v-model="settingsStore.settings.tabCloseButton" @change="settingsStore.save()">
                <el-option :label="t('settings.tabCloseButtonLeft')" value="left" />
                <el-option :label="t('settings.tabCloseButtonRight')" value="right" />
              </el-select>
            </div>
          </div>

          <div class="setting-card">
            <div class="setting-info">
              <div class="setting-title">{{ t('settings.showTabShortcutHints') }}</div>
              <div class="setting-desc">{{ t('settings.showTabShortcutHintsDesc') }}</div>
            </div>
            <div class="setting-control">
              <el-switch v-model="settingsStore.settings.showTabShortcutHints" @change="settingsStore.save()" />
            </div>
          </div>

          <div class="setting-card">
            <div class="setting-info">
              <div class="setting-title">{{ t('settings.hostListMenuStyle') }}</div>
              <div class="setting-desc">{{ t('settings.hostListMenuStyleDesc') }}</div>
            </div>
            <div class="setting-control">
              <el-select v-model="settingsStore.settings.hostListMenuStyle" @change="settingsStore.save()">
                <el-option :label="t('settings.hostListMenuStyleButton')" value="button" />
                <el-option :label="t('settings.hostListMenuStyleRightClick')" value="rightclick" />
              </el-select>
            </div>
          </div>

          <div class="setting-card">
            <div class="setting-info">
              <div class="setting-title">{{ t('settings.sidebarTabs') }}</div>
              <div class="setting-desc">{{ t('settings.sidebarTabsDesc') }}</div>
            </div>
            <div class="setting-control">
              <el-select
                v-model="visibleSidebarTabs"
                multiple
                collapse-tags
                :collapse-tags-limit="3"
                @change="onSidebarTabsChange"
              >
                <!-- "connections" is fixed and never rendered as an option;
                     the computed keeps it force-selected. -->
                <el-option
                  v-for="tab in SIDEBAR_TAB_ORDER.filter(tab => tab.key !== 'connections')"
                  :key="tab.key"
                  :label="t(tab.labelKey)"
                  :value="tab.key"
                />
              </el-select>
            </div>
          </div>

          </div>

        <h2 class="section-title">{{ t('settings.interaction') }}</h2>
        <div class="settings-group">
          <div class="setting-card">
            <div class="setting-info">
              <div class="setting-title">{{ t('settings.closeTabPrompt') }}</div>
            </div>
            <div class="setting-control">
              <el-switch v-model="settingsStore.settings.closeTabPrompt" @change="settingsStore.save()" />
            </div>
          </div>

          <!-- Mobile apps don't "quit" (back button = background) -->
          <div v-if="!isMobile" class="setting-card">
            <div class="setting-info">
              <div class="setting-title">{{ t('settings.closeAppPrompt') }}</div>
            </div>
            <div class="setting-control">
              <el-switch v-model="settingsStore.settings.closeAppPrompt" @change="settingsStore.save()" />
            </div>
          </div>

          <!-- No local CLI editors on mobile -->
          <div v-if="!isMobile" class="setting-card">
            <div class="setting-info">
              <div class="setting-title">{{ t('settings.externalEditor') }}</div>
              <div class="setting-desc">{{ t('settings.externalEditorDesc') }}</div>
            </div>
            <div class="setting-control">
              <el-select
                :model-value="localStateStore.state.externalEditor"
                class="editor-select"
                filterable
                allow-create
                default-first-option
                clearable
                placeholder='code -w'
                @update:model-value="(v: string) => localStateStore.update({ externalEditor: v as string })"
              >
                <el-option
                  v-for="p in detectedEditors"
                  :key="p.value"
                  :label="p.label"
                  :value="p.value"
                />
              </el-select>
            </div>
          </div>
        </div>

        <!-- Hidden entirely on mobile: data dir is OS-managed and keychain
             encryption is the only supported mode, so nothing is configurable -->
        <template v-if="!isMobile">
          <h2 class="section-title">{{ t('settings.storageSecurity') }}</h2>
          <div class="settings-group">
          <div class="setting-card">
            <div class="setting-info">
              <div class="setting-title">{{ t('config.dataDir') }}</div>
              <div class="setting-desc">{{ t('config.dataDirDesc') }}</div>
            </div>
            <div class="setting-control">
              <div class="config-value">{{ dataDirTypeLabel }}</div>
              <el-button size="small" @click="openDataDirChange">{{ t('config.changeDir') }}</el-button>
            </div>
          </div>

          <div class="setting-card">
            <div class="setting-info">
              <div class="setting-title">{{ t('config.encryption') }}</div>
              <div class="setting-desc">{{ t('config.encryptionDesc') }}</div>
            </div>
            <div class="setting-control">
              <el-select v-model="modeSelect" @change="onModeChange" popper-class="mode-select-popper" style="width: 100%">
                <el-option v-if="!credStore.status.mode" :label="t('config.notConfigured')" value="" disabled />
                <el-option :label="t('encrypt.keychain')" value="keychain">
                  <div class="mode-option">
                    <div class="mode-option-title">{{ t('encrypt.keychain') }}</div>
                    <div class="mode-option-desc">{{ t('config.switchKeychainHint') }}</div>
                  </div>
                </el-option>
                <el-option :label="t('encrypt.masterPassword')" value="master-password">
                  <div class="mode-option">
                    <div class="mode-option-title">{{ t('encrypt.masterPassword') }}</div>
                    <div class="mode-option-desc">{{ t('config.switchMasterHint') }}</div>
                  </div>
                </el-option>
              </el-select>
            </div>
          </div>

          <div v-if="credStore.status.mode === 'master-password'" class="setting-card">
            <div class="setting-info">
              <div class="setting-title">{{ t('config.masterPassword') }}</div>
              <div class="setting-desc">{{ t('config.changePasswordDesc') }}</div>
            </div>
            <div class="setting-control">
              <el-button size="small" @click="openChangePassword">{{ t('config.changePassword') }}</el-button>
            </div>
          </div>
          </div>
        </template>
      </div>

      <!-- 终端配置 -->
      <div v-if="settingsStore.activeCategory === 'terminal'" class="settings-section">
        <h2 class="section-title">{{ t('settings.appearance') }}</h2>

        <div class="settings-group">
          <div class="setting-card">
            <div class="setting-info">
              <div class="setting-title">{{ t('settings.colorScheme') }}</div>
              <div class="setting-desc">{{ t('settings.colorSchemeDesc') }}</div>
            </div>
            <div class="setting-control">
              <div class="theme-select-row">
                <el-select v-model="settingsStore.settings.terminal.theme" @change="settingsStore.save()" popper-class="theme-select-popper">
                  <el-option :label="t('settings.followAppTheme')" :value="FOLLOW_APP_THEME" />
                  <el-option-group
                    v-for="group in terminalThemeGroups"
                    :key="group.label"
                    :label="group.label"
                  >
                    <el-option
                      v-for="th in group.options"
                      :key="th.value"
                      :label="th.label"
                      :value="th.value"
                    />
                  </el-option-group>
                </el-select>
                <button class="btn btn-ghost btn-icon btn-sm" :title="t('theme.newTitle')" @click="openThemeEditor()">
                  <Plus :size="'0.875rem'" />
                </button>
                <button
                  v-if="isCustomTheme(settingsStore.settings.terminal.theme)"
                  class="btn btn-ghost btn-icon btn-sm"
                  :title="t('theme.editTitle')"
                  @click="openThemeEditor(settingsStore.settings.terminal.theme)"
                >
                  <Pencil :size="'0.875rem'" />
                </button>
              </div>
            </div>
          </div>

          <div class="setting-card">
            <div class="setting-info">
              <div class="setting-title">{{ t('settings.fontPrimary') }}</div>
              <div class="setting-desc">{{ t('settings.fontDesc') }}</div>
            </div>
            <div class="setting-control">
              <el-select v-model="settingsStore.settings.terminal.fontFamily" @change="settingsStore.save()">
                <template #header>
                  <div style="padding:0.25rem 0.75rem">
                    <el-checkbox v-model="firstMonoOnly" @click.stop>{{ t('settings.fontMonoOnly') }}</el-checkbox>
                  </div>
                </template>
                <el-option
                  v-for="f in fontOptions"
                  :key="f.value"
                  :label="f.label"
                  :value="f.value"
                  :style="{ fontFamily: formatFontFamily(f.value) }"
                />
              </el-select>
            </div>
          </div>

          <div class="setting-card">
            <div class="setting-info">
              <div class="setting-title">{{ t('settings.fontFallback') }}</div>
              <div class="setting-desc">{{ t('settings.fontFallbackDesc') }}</div>
            </div>
            <div class="setting-control">
              <el-select v-model="settingsStore.settings.terminal.fallbackFont" @change="settingsStore.save()">
                <template #header>
                  <div style="padding:0.25rem 0.75rem">
                    <el-checkbox v-model="secondMonoOnly" @click.stop>{{ t('settings.fontMonoOnly') }}</el-checkbox>
                  </div>
                </template>
                <el-option value="" :label="t('settings.fontNone')" />
                <el-option
                  v-for="f in secondFontOptions"
                  :key="f.value"
                  :label="f.label"
                  :value="f.value"
                  :style="{ fontFamily: formatFontFamily(f.value) }"
                />
              </el-select>
            </div>
          </div>

          <div class="setting-card">
            <div class="setting-info">
              <div class="setting-title">{{ t('settings.fontWeight') }}</div>
              <div class="setting-desc">{{ t('settings.fontWeightDesc') }}</div>
            </div>
            <div class="setting-control">
              <el-select v-model="settingsStore.settings.terminal.fontWeight" @change="settingsStore.save()">
                <el-option
                  v-for="w in FONT_WEIGHT_OPTIONS"
                  :key="w.value"
                  :label="t(w.labelKey)"
                  :value="w.value"
                />
              </el-select>
            </div>
          </div>

          <div class="setting-card">
            <div class="setting-info">
              <div class="setting-title">{{ t('settings.fontSize') }}</div>
              <div class="setting-desc">{{ t('settings.fontSizeDesc') }}</div>
            </div>
            <div class="setting-control">
              <el-input-number
                v-model="settingsStore.settings.terminal.fontSize"
                :min="8"
                :max="32"
                @change="settingsStore.save()"
              />
            </div>
          </div>

          <div class="setting-card">
            <div class="setting-info">
              <div class="setting-title">{{ t('settings.cursorBlink') }}</div>
              <div class="setting-desc">{{ t('settings.cursorBlinkDesc') }}</div>
            </div>
            <div class="setting-control">
              <el-switch :model-value="settingsStore.settings.terminal.cursorBlink ?? true" @update:model-value="(v: boolean) => { settingsStore.settings.terminal.cursorBlink = v; settingsStore.save() }" />
            </div>
          </div>

          <div class="setting-card">
            <div class="setting-info">
              <div class="setting-title">{{ t('settings.cursorStyle') }}</div>
              <div class="setting-desc">{{ t('settings.cursorStyleDesc') }}</div>
            </div>
            <div class="setting-control">
              <el-select v-model="settingsStore.settings.terminal.cursorStyle" @change="settingsStore.save()">
                <el-option v-for="opt in cursorStyleOptions" :key="opt.value" :label="t(opt.labelKey)" :value="opt.value" />
              </el-select>
            </div>
          </div>

          <div class="setting-card">
            <div class="setting-info">
              <div class="setting-title">{{ t('settings.terminalContrast') }}</div>
              <div class="setting-desc">{{ t('settings.terminalContrastDesc') }}</div>
            </div>
            <div class="setting-control">
              <el-select v-model="settingsStore.settings.terminal.minimumContrast" @change="settingsStore.save()">
                <el-option :label="t('settings.contrastOff')" :value="1" />
                <el-option :label="t('settings.contrastStandard')" :value="4.5" />
                <el-option :label="t('settings.contrastHigh')" :value="7" />
              </el-select>
            </div>
          </div>

          <div class="setting-card">
            <div class="setting-info">
              <div class="setting-title">{{ t('settings.highlight') }}</div>
              <div class="setting-desc">{{ t('settings.highlightDesc') }}</div>
            </div>
            <div class="setting-control">
              <el-switch :model-value="settingsStore.settings.terminal.highlightEnabled ?? true" @update:model-value="(v: boolean) => { settingsStore.settings.terminal.highlightEnabled = v; settingsStore.save() }" />
            </div>
          </div>

          <div class="setting-card">
            <div class="setting-info">
              <div class="setting-title">{{ t('settings.showLineNumbers') }}</div>
              <div class="setting-desc">{{ t('settings.showLineNumbersDesc') }}</div>
            </div>
            <div class="setting-control">
              <el-switch :model-value="settingsStore.settings.terminal.showLineNumbers ?? false" @update:model-value="(v: boolean) => { settingsStore.settings.terminal.showLineNumbers = v; settingsStore.save() }" />
            </div>
          </div>

          <div class="setting-card">
            <div class="setting-info">
              <div class="setting-title">{{ t('settings.showTimestamps') }}</div>
              <div class="setting-desc">{{ t('settings.showTimestampsDesc') }}</div>
            </div>
            <div class="setting-control">
              <el-switch :model-value="settingsStore.settings.terminal.showTimestamps ?? false" @update:model-value="(v: boolean) => { settingsStore.settings.terminal.showTimestamps = v; settingsStore.save() }" />
            </div>
          </div>

          <div class="setting-card">
            <div class="setting-info">
              <div class="setting-title">{{ t('settings.timestampFormat') }}</div>
            </div>
            <div class="setting-control">
              <el-select v-model="settingsStore.settings.terminal.timestampFormat" @change="settingsStore.save()">
                <el-option v-for="opt in TIMESTAMP_FORMATS" :key="opt.value" :label="t(opt.labelKey)" :value="opt.value" />
              </el-select>
            </div>
          </div>
        </div>

        <h2 class="section-title">{{ t('settings.interaction') }}</h2>
        <div class="settings-group">
          <div class="setting-card">
            <div class="setting-info">
              <div class="setting-title">{{ t('settings.selectionAction') }}</div>
              <div class="setting-desc">{{ t('settings.selectionActionDesc') }}</div>
            </div>
            <div class="setting-control">
              <el-select v-model="settingsStore.settings.terminal.selectionAction" @change="settingsStore.save()">
                <el-option :label="t('settings.selectionNone')" value="none" />
                <el-option :label="t('settings.selectionCopy')" value="copy" />
              </el-select>
            </div>
          </div>

          <div class="setting-card">
            <div class="setting-info">
              <div class="setting-title">{{ t('settings.wordSeparator') }}</div>
              <div class="setting-desc">{{ t('settings.wordSeparatorDesc') }}</div>
            </div>
            <div class="setting-control">
              <el-input
                v-model="settingsStore.settings.terminal.wordSeparator"
                :placeholder="defaultWordSeparator"
                clearable
                @change="settingsStore.save()"
              />
            </div>
          </div>

          <!-- No mouse buttons on touch screens -->
          <div v-if="!isMobile" class="setting-card">
            <div class="setting-info">
              <div class="setting-title">{{ t('settings.rightClick') }}</div>
              <div class="setting-desc">{{ t('settings.rightClickDesc') }}</div>
            </div>
            <div class="setting-control">
              <el-select v-model="settingsStore.settings.terminal.rightClickAction" @change="settingsStore.save()">
                <el-option :label="t('settings.rightClickMenu')" value="menu" />
                <el-option :label="t('settings.rightClickPaste')" value="paste" />
              </el-select>
            </div>
          </div>

          <div v-if="!isMobile" class="setting-card">
            <div class="setting-info">
              <div class="setting-title">{{ t('settings.middleClick') }}</div>
              <div class="setting-desc">{{ t('settings.middleClickDesc') }}</div>
            </div>
            <div class="setting-control">
              <el-select v-model="settingsStore.settings.terminal.middleClickAction" @change="settingsStore.save()">
                <el-option :label="t('settings.rightClickPaste')" value="paste" />
                <el-option :label="t('settings.rightClickMenu')" value="menu" />
              </el-select>
            </div>
          </div>

          <div v-if="!isMobile" class="setting-card">
            <div class="setting-info">
              <div class="setting-title">{{ t('settings.ctrlWheelZoom') }}</div>
              <div class="setting-desc">{{ t('settings.ctrlWheelZoomDesc') }}</div>
            </div>
            <div class="setting-control">
              <el-switch :model-value="settingsStore.settings.terminal.ctrlWheelZoom ?? true" @update:model-value="(v: boolean) => { settingsStore.settings.terminal.ctrlWheelZoom = v; settingsStore.save() }" />
            </div>
          </div>

          <div class="setting-card">
            <div class="setting-info">
              <div class="setting-title">{{ t('settings.smartCompletion') }}</div>
              <div class="setting-desc">{{ t('settings.smartCompletionDesc') }}</div>
            </div>
            <div class="setting-control">
              <el-switch v-model="settingsStore.settings.terminal.smartCompletion" @change="settingsStore.save()" />
            </div>
          </div>
        </div>

        <h2 class="section-title">{{ t('settings.session') }}</h2>
        <div class="settings-group">
          <!-- No user shells exist on mobile (same reason the start page hides
               the local terminal button) -->
          <div v-if="!isMobile" class="setting-card">
            <div class="setting-info">
              <div class="setting-title">{{ t('settings.defaultLocalShell') }}</div>
              <div class="setting-desc">{{ t('settings.defaultLocalShellDesc') }}</div>
            </div>
            <div class="setting-control">
              <el-select v-model="settingsStore.settings.defaultLocalShell" @change="settingsStore.save()">
                <el-option
                  v-for="sh in settingsStore.availableShells"
                  :key="sh"
                  :label="getShellLabel(sh)"
                  :value="sh"
                />
              </el-select>
            </div>
          </div>

          <div class="setting-card">
            <div class="setting-info">
              <div class="setting-title">{{ t('settings.maxHistory') }}</div>
              <div class="setting-desc">{{ t('settings.maxHistoryDesc') }}</div>
            </div>
            <div class="setting-control">
              <el-input-number
                v-model="settingsStore.settings.terminal.maxHistoryLines"
                :min="100"
                :max="50000"
                :step="100"
                @change="settingsStore.save()"
              />
            </div>
          </div>

          <!-- Local dirs are not user-selectable under mobile scoped storage -->
          <div v-if="!isMobile" class="setting-card">
            <div class="setting-info">
              <div class="setting-title">{{ t('settings.sessionLogDir') }}</div>
              <div class="setting-desc">{{ t('settings.sessionLogDirDesc', { path: defaultLogDir }) }}</div>
            </div>
            <div class="setting-control">
              <el-input
                v-model="settingsStore.settings.terminal.sessionLogDir"
                :placeholder="defaultLogDir"
                class="dir-input"
                @change="settingsStore.save()"
                clearable
              >
                <template #append>
                  <el-tooltip :content="t('settings.browse')" placement="top">
                    <el-button :aria-label="t('settings.browse')" @click="pickLogDir">
                      <el-icon><FolderOpen :size="'1rem'" /></el-icon>
                    </el-button>
                  </el-tooltip>
                </template>
              </el-input>
            </div>
          </div>

          <div v-if="!isMobile" class="setting-card">
            <div class="setting-info">
              <div class="setting-title">{{ t('settings.zmodemDownloadDir') }}</div>
              <div class="setting-desc">{{ t('settings.zmodemDownloadDirDesc') }}</div>
            </div>
            <div class="setting-control">
              <el-input
                v-model="settingsStore.settings.terminal.zmodemDownloadDir"
                :placeholder="t('settings.zmodemDownloadDirPlaceholder')"
                class="dir-input"
                @change="settingsStore.save()"
                clearable
              >
                <template #append>
                  <el-tooltip :content="t('settings.browse')" placement="top">
                    <el-button :aria-label="t('settings.browse')" @click="pickZmodemDownloadDir">
                      <el-icon><FolderOpen :size="'1rem'" /></el-icon>
                    </el-button>
                  </el-tooltip>
                </template>
              </el-input>
            </div>
          </div>

          <!-- Session logs go to the app-private dir on mobile; the filename
               pattern is not user-serviceable there -->
          <div v-if="!isMobile" class="setting-card">
            <div class="setting-info">
              <div class="setting-title">{{ t('settings.sessionLogFilename') }}</div>
              <div class="setting-desc">{{ t('settings.sessionLogFilenameDesc') }}</div>
            </div>
            <div class="setting-control">
              <el-input
                v-model="settingsStore.settings.terminal.sessionLogFilename"
                placeholder="%S_%H_%M%D_%h%m.log"
                @change="settingsStore.save()"
                clearable
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Commands -->
      <div v-if="settingsStore.activeCategory === 'commands'" class="settings-section">
        <h2 class="section-title">{{ t('settings.commands') }}</h2>
        <p class="section-desc">{{ t('settings.commandsDesc') }}</p>
        <CommandsManager />
      </div>

      <!-- Sync settings -->
      <div v-if="settingsStore.activeCategory === 'sync'" class="settings-section sync-settings">
        <h2 class="section-title">{{ t('settings.sync') }}</h2>
        <p class="section-desc">{{ t('settings.syncDesc') }}</p>

        <!-- Empty state: no repo configured -->
        <div v-if="!syncStore.config.repoUrl" class="sync-card">
          <div class="sync-card-header">{{ t('settings.syncRepoCard') }}</div>
          <div class="sync-card-body empty-state">
            <p class="empty-text">{{ t('settings.syncEmptyDesc') }}</p>
            <el-button type="primary" @click="syncStore.showAddRepo = true">
              {{ t('settings.syncAddRepo') }}
            </el-button>
          </div>
        </div>

        <!-- Configured state -->
        <template v-else>
          <!-- Repo config card -->
          <div class="sync-card">
            <div class="sync-card-header">
              <span>{{ t('settings.syncRepoCard') }}</span>
              <el-button text @click="openEditRepo">{{ t('settings.syncEdit') }}</el-button>
            </div>
            <div class="sync-card-body">
              <div class="repo-info">
                <div class="repo-info-row">
                  <span class="repo-label">{{ t('settings.syncRepoUrl') }}</span>
                  <span class="repo-value">{{ syncStore.config.repoUrl }}</span>
                </div>
                <div class="repo-info-row">
                  <span class="repo-label">{{ t('settings.syncUsername') }}</span>
                  <span class="repo-value">{{ syncStore.config.username }}</span>
                </div>
              </div>
              <div class="repo-actions">
                <el-button @click="syncStore.showChangePassword = true">{{ t('settings.syncChangePassword') }}</el-button>
                <el-button @click="syncStore.showDeleteRepo = true">{{ t('settings.syncDeleteRepo') }}</el-button>
              </div>
            </div>
          </div>

          <!-- Sync card -->
          <div class="sync-card">
            <div class="sync-card-header">{{ t('settings.syncSyncCard') }}</div>
            <div class="sync-card-body">
              <div class="sync-status">
                <div class="sync-status-row">
                  <span class="sync-label">{{ t('settings.syncLastSync') }}</span>
                  <span class="sync-value">{{ syncStore.formatSyncTime() }}</span>
                  <span v-if="syncStore.config.lastSyncStatus === 'success'" class="sync-tag success">{{ t('settings.syncStatusSuccess') }}</span>
                  <span v-else-if="syncStore.config.lastSyncStatus === 'failed'" class="sync-tag failed">{{ t('settings.syncStatusFailed') }}</span>
                </div>
                <div v-if="syncStore.config.lastSyncStatus === 'failed' && syncStore.config.lastSyncError" class="sync-status-row sync-error">
                  <span class="sync-label">{{ t('settings.syncReason') }}</span>
                  <span class="sync-value error-text">{{ syncStore.config.lastSyncError }}</span>
                </div>
              </div>
              <div class="sync-actions-row">
                <el-button
                  type="primary"
                  :loading="syncStore.syncing"
                  @click="handleSyncNow"
                >
                  {{ t('settings.syncNow') }}
                </el-button>
              </div>
              <div class="sync-auto-row">
                <span class="sync-auto-label">{{ t('settings.syncAuto') }}</span>
                <span class="sync-auto-desc">{{ t('settings.syncAutoDesc') }}</span>
                <el-switch v-model="syncStore.config.autoSync" @change="handleAutoSyncToggle" />
              </div>
            </div>
          </div>
        </template>
      </div>

      <!-- 密钥库 -->
      <div v-if="settingsStore.activeCategory === 'identities'" class="settings-section">
        <h2 class="section-title">{{ t('settings.identities') }}</h2>
        <p class="section-desc">{{ t('settings.identitiesDesc') }}</p>
        <el-button type="primary" @click="openIdentityDialog()">{{ t('settings.addIdentity') }}</el-button>
        <el-table :data="identityStore.identities" size="small" style="margin-top: 0.75rem">
          <el-table-column prop="name" :label="t('conn.name')" />
          <el-table-column prop="username" :label="t('conn.user')" />
          <el-table-column :label="t('conn.authType')">
            <template #default="{ row }">{{ row.authType === 'password' ? t('conn.password') : row.authType === 'keyText' ? t('conn.keyText') : t('conn.keyPath') }}</template>
          </el-table-column>
          <el-table-column :label="t('common.actions')" :width="uiPx(160)">
            <template #default="{ row }">
              <el-button size="small" @click="openIdentityDialog(row)">{{ t('common.edit') }}</el-button>
              <el-button size="small" type="danger" @click="removeIdentity(row)">{{ t('common.delete') }}</el-button>
            </template>
          </el-table-column>
        </el-table>
        <IdentityEditDialog v-model:visible="identityDialogVisible" :identity="editingIdentity" @saved="identityStore.load()" />
      </div>

      <!-- 代理 -->
      <div v-if="settingsStore.activeCategory === 'proxies'" class="settings-section">
        <h2 class="section-title">{{ t('settings.proxies') }}</h2>
        <p class="section-desc">{{ t('settings.proxiesDesc') }}</p>
        <el-button type="primary" @click="openProxyDialog()">{{ t('settings.addProxy') }}</el-button>
        <el-table :data="proxyStore.proxies" size="small" style="margin-top: 0.75rem">
          <el-table-column prop="name" :label="t('conn.name')" />
          <el-table-column prop="kind" :label="t('conn.proxyType')" :width="uiPx(100)" />
          <el-table-column :label="t('settings.proxyHost')">
            <template #default="{ row }">{{ row.host }}:{{ row.port }}</template>
          </el-table-column>
          <el-table-column :label="t('settings.enabled')" :width="uiPx(80)">
            <template #default="{ row }">
              <el-switch
                :model-value="row.enabled !== false"
                size="small"
                @change="(v: boolean) => toggleProxy(row, v)"
              />
            </template>
          </el-table-column>
          <el-table-column :label="t('common.actions')" :width="uiPx(160)">
            <template #default="{ row }">
              <el-button size="small" @click="openProxyDialog(row)">{{ t('common.edit') }}</el-button>
              <el-button size="small" type="danger" @click="removeProxy(row)">{{ t('common.delete') }}</el-button>
            </template>
          </el-table-column>
        </el-table>
        <ProxyEditDialog v-model:visible="proxyDialogVisible" :proxy="editingProxy" @saved="proxyStore.load()" />
      </div>

      <!-- 隧道 -->
      <div v-if="settingsStore.activeCategory === 'tunnels'" class="settings-section">
        <h2 class="section-title">{{ t('settings.tunnels') }}</h2>
        <p class="section-desc">{{ t('settings.tunnelsDesc') }}</p>
        <el-button type="primary" @click="openTunnelDialog()">{{ t('tunnels.addTunnel') }}</el-button>
        <el-table :data="tunnelStore.tunnels" size="small" style="margin-top: 0.75rem">
          <el-table-column prop="name" :label="t('tunnels.name')" />
          <el-table-column :label="t('tunnels.modeCol')" :width="uiPx(100)">
            <template #default="{ row }">{{ modeName(row.mode) }}</template>
          </el-table-column>
          <el-table-column :label="t('tunnels.listenCol')" :width="uiPx(120)">
            <template #default="{ row }">:{{ effPort(row) }}</template>
          </el-table-column>
          <el-table-column :label="t('tunnels.statusCol')" :width="uiPx(120)">
            <template #default="{ row }">
              <el-switch
                :model-value="statusOf(row.id) === 'running'"
                @change="toggleRun(row)"
                :loading="togglingTunnelId === row.id"
              />
            </template>
          </el-table-column>
          <el-table-column :label="t('common.actions')" :width="uiPx(160)">
            <template #default="{ row }">
              <!-- Editing a running tunnel would desync the form from what's
                   actually running; edits require a stop first. -->
              <el-button
                size="small"
                :disabled="tunnelStore.statusOf(row.id) === 'running'"
                @click="openTunnelDialog(row)"
              >{{ t('common.edit') }}</el-button>
              <el-button size="small" type="danger" @click="removeTunnel(row)">{{ t('common.delete') }}</el-button>
            </template>
          </el-table-column>
        </el-table>
        <TunnelEditDialog v-model="tunnelDialogVisible" :editing-id="editingTunnelId" />
      </div>

      <!-- 关于 -->
      <div v-if="settingsStore.activeCategory === 'about'" class="settings-section">
        <h2 class="section-title">{{ t('settings.about') }}</h2>
        <div class="about-content">
          <div class="about-appname">Terminal</div>
          <p class="about-desc">{{ t('settings.aboutDesc') }}</p>
          <div class="about-version">
            {{ t('settings.version') }}: {{ appVersion || '...' }}
          </div>
          <div class="about-links">
            <a href="#" class="about-link" @click.prevent="Browser.OpenURL('https://uniterm.net')">
              <Globe :size="'0.875rem'" class="about-link-icon" />
              {{ t('settings.homepage') }}
            </a>
            <a href="#" class="about-link" @click.prevent="Browser.OpenURL(locale === 'zh-CN' ? 'https://uniterm.net/guide/zh/introduction' : 'https://uniterm.net/guide/en/introduction')">
              <BookOpen :size="'0.875rem'" class="about-link-icon" />
              {{ t('settings.userManual') }}
            </a>
            <a href="#" class="about-link" @click.prevent="Browser.OpenURL('https://github.com/ys-ll/uniterm')">
              <svg class="about-link-icon" viewBox="0 0 16 16" width="0.875rem" height="0.875rem" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27s1.36.09 2 .27c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8z"/></svg>
              GitHub
            </a>
            <a href="#" class="about-link" @click.prevent="Browser.OpenURL('https://gitee.com/ys-l/uniterm')">
              <svg class="about-link-icon" viewBox="0 0 24 24" width="0.875rem" height="0.875rem" fill="currentColor"><path d="M11.984 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.016 0zm6.09 5.333c.328 0 .593.266.592.593v1.482a.594.594 0 0 1-.593.592H9.777c-.982 0-1.778.796-1.778 1.778v5.63c0 .327.266.592.593.592h5.63c.982 0 1.778-.796 1.778-1.778v-.296a.593.593 0 0 0-.592-.593h-4.15a.592.592 0 0 1-.592-.592v-1.482a.593.593 0 0 1 .593-.592h6.815c.327 0 .593.265.593.592v3.408a4 4 0 0 1-4 4H5.926a.593.593 0 0 1-.593-.593V9.778a4.444 4.444 0 0 1 4.445-4.444h8.296z"/></svg>
              Gitee
            </a>
          </div>
        </div>
      </div>

      <!-- 快捷键设置 -->
      <div v-if="settingsStore.activeCategory === 'keyboard' && !isMobile" class="settings-section">
        <p v-if="isMac" class="kb-hint kb-modifier-note">{{ t('shortcut.modifierNote') }}</p>
        <template v-for="cat in shortcutCategories" :key="cat.key">
          <h2 class="section-title">{{ t(cat.label) }}</h2>
          <table class="kb-table">
            <thead>
              <tr>
                <th>{{ t('shortcut.colFunction') }}</th>
                <th>{{ t('shortcut.colBinding') }}</th>
                <th style="width:11.875rem;">{{ t('shortcut.colActions') }}</th>
              </tr>
            </thead>
            <tbody>
              <template v-if="cat.key === 'tabs'">
                <tr>
                  <td>{{ t('shortcut.switchToTabByIndex') }}</td>
                  <td><kbd class="kb-key">{{ tabSwitchBindingDisplay() }}</kbd></td>
                  <td class="kb-actions">
                    <el-button
                      :type="rebindingTabSwitch ? 'warning' : 'default'"
                      @click="startRebindTabSwitch()"
                    >
                      {{ rebindingTabSwitch ? t('shortcut.pressModifier') : t('shortcut.edit') }}
                    </el-button>
                    <el-button
                      v-if="rebindingTabSwitch"
                      @click="stopRebind()"
                    >
                      {{ t('shortcut.cancel') }}
                    </el-button>
                    <el-button
                      v-if="rebindingTabSwitch"
                      type="danger"
                      @click="clearTabSwitchModifier()"
                    >
                      {{ t('shortcut.clear') }}
                    </el-button>
                    <el-button
                      v-if="!isTabSwitchModifierUnset() && !rebindingTabSwitch"
                      type="danger"
                      @click="resetTabSwitchModifier()"
                    >
                      {{ t('shortcut.reset') }}
                    </el-button>
                  </td>
                </tr>
                <tr>
                  <td>{{ t('shortcut.switchToPanelByIndex') }}</td>
                  <td><kbd class="kb-key">{{ panelSwitchBindingDisplay() }}</kbd></td>
                  <td class="kb-actions">
                    <el-button
                      :type="rebindingPanelSwitch ? 'warning' : 'default'"
                      @click="startRebindPanelSwitch()"
                    >
                      {{ rebindingPanelSwitch ? t('shortcut.pressModifier') : t('shortcut.edit') }}
                    </el-button>
                    <el-button
                      v-if="rebindingPanelSwitch"
                      @click="stopRebind()"
                    >
                      {{ t('shortcut.cancel') }}
                    </el-button>
                    <el-button
                      v-if="rebindingPanelSwitch"
                      type="danger"
                      @click="clearPanelSwitchModifier()"
                    >
                      {{ t('shortcut.clear') }}
                    </el-button>
                    <el-button
                      v-if="!isPanelSwitchModifierUnset() && !rebindingPanelSwitch"
                      type="danger"
                      @click="resetPanelSwitchModifier()"
                    >
                      {{ t('shortcut.reset') }}
                    </el-button>
                  </td>
                </tr>
              </template>
              <tr
                v-for="action in cat.actions"
                :key="action"
              >
                <td>{{ t(SHORTCUT_LABELS[action] || action) }}</td>
                <td><kbd class="kb-key">{{ bindingDisplay(action) }}</kbd></td>
                <td class="kb-actions">
                  <el-button

                    :type="rebindingAction === action ? 'warning' : 'default'"
                    @click="startRebind(action)"
                  >
                    {{ rebindingAction === action ? t('shortcut.pressKey') : t('shortcut.edit') }}
                  </el-button>
                  <el-button
                    v-if="rebindingAction === action"

                    @click="stopRebind()"
                  >
                    {{ t('shortcut.cancel') }}
                  </el-button>
                  <el-button
                    v-if="rebindingAction === action"

                    type="danger"
                    @click="clearBinding(action)"
                  >
                    {{ t('shortcut.clear') }}
                  </el-button>
                  <el-button
                    v-if="!isDefaultBinding(action) && rebindingAction !== action"

                    type="danger"
                    @click="resetBinding(action)"
                  >
                    {{ t('shortcut.reset') }}
                  </el-button>
                </td>
              </tr>
            </tbody>
          </table>
        </template>

        <!-- 系统全局热键（托盘等，系统级生效） -->
        <h2 class="section-title">{{ t('shortcut.globalHotkeys') }}</h2>
        <table class="kb-table">
          <thead>
            <tr>
              <th>{{ t('shortcut.colFunction') }}</th>
              <th>{{ t('shortcut.colBinding') }}</th>
              <th style="width:11.875rem;">{{ t('shortcut.colActions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>{{ t('shortcut.trayHotkeyRow') }}</td>
              <td><kbd class="kb-key">{{ trayHotkeyDisplay() }}</kbd></td>
              <td class="kb-actions">
                <el-button
                  :type="rebindingTrayHotkey ? 'warning' : 'default'"
                  @click="startRebindTrayHotkey()"
                >
                  {{ rebindingTrayHotkey ? t('shortcut.pressKey') : t('shortcut.edit') }}
                </el-button>
                <el-button
                  v-if="rebindingTrayHotkey"
                  @click="stopRebind()"
                >
                  {{ t('shortcut.cancel') }}
                </el-button>
                <el-button
                  v-if="rebindingTrayHotkey"
                  type="danger"
                  @click="clearTrayHotkey()"
                >
                  {{ t('shortcut.clear') }}
                </el-button>
                <el-button
                  v-if="!isTrayHotkeyDefault() && !rebindingTrayHotkey"
                  type="danger"
                  @click="resetTrayHotkey()"
                >
                  {{ t('shortcut.reset') }}
                </el-button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Sync dialogs -->
    <AddRepoDialog />
    <EditRepoDialog />
    <ChangePasswordDialog />
    <DeleteRepoDialog />
    <CustomThemeEditor v-model="themeEditorVisible" :source-theme-id="themeEditorSourceId" />

    <!-- Config dialogs -->
    <DataDirDialog v-model:visible="dataDirVisible" :first-run="false" @done="onDataDirChange" />

    <el-dialog append-to-body v-model="showSetupMaster" :title="t('config.setupMasterTitle')" width="27.5rem">
      <el-form label-width="6.25rem" class="settings-form" @submit.prevent="doSetupMaster">
        <el-form-item :label="t('encrypt.password')">
          <el-input v-model="setupPw" type="password" show-password />
        </el-form-item>
        <el-form-item :label="t('encrypt.confirm')">
          <el-input v-model="setupPw2" type="password" show-password />
        </el-form-item>
      </el-form>
      <div v-if="setupError" class="form-error">{{ setupError }}</div>
      <template #footer>
        <el-button @click="showSetupMaster = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="setupSubmitting" @click="doSetupMaster">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog append-to-body v-model="showVerifyMaster" :title="t('config.verifyMasterTitle')" width="27.5rem">
      <el-form label-width="6.25rem" class="settings-form" @submit.prevent="doVerifyMaster">
        <el-form-item :label="t('config.verifyCurrentPassword')">
          <div class="verify-field">
            <el-input v-model="verifyPw" type="password" show-password />
            <div class="switch-mode-hint">{{ t('config.verifyCurrentHint') }}</div>
          </div>
        </el-form-item>
      </el-form>
      <div v-if="verifyError" class="form-error">{{ verifyError }}</div>
      <template #footer>
        <el-button @click="showVerifyMaster = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="verifySubmitting" @click="doVerifyMaster">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog append-to-body v-model="showChangePassword" :title="t('config.changePassword')" width="27.5rem">
      <el-form label-width="6.25rem" class="settings-form" @submit.prevent="doChangePassword">
        <el-form-item :label="t('config.oldPassword')">
          <el-input v-model="oldPw" type="password" show-password />
        </el-form-item>
        <el-form-item :label="t('config.newPassword')">
          <el-input v-model="newPw" type="password" show-password />
        </el-form-item>
        <el-form-item :label="t('encrypt.confirm')">
          <el-input v-model="newPw2" type="password" show-password />
        </el-form-item>
      </el-form>
      <div v-if="changePwError" class="form-error">{{ changePwError }}</div>
      <template #footer>
        <el-button @click="showChangePassword = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="changePwSubmitting" @click="doChangePassword">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted, onUnmounted } from 'vue'
import { Settings, Monitor, Info, RefreshCw, Pencil, Globe, Keyboard, Plus, BookOpen, Wrench, FolderOpen, Key, Network, ArrowRightLeft, ChevronLeft, ChevronRight } from '@lucide/vue'
import { msg } from '../services/message'
import { GetPlatform, GetAppInfo, GetAllFonts, GetDefaultSessionLogDir, OpenDirectoryDialog, OpenFileDialogFiltered, SetBackgroundImage, ClearBackgroundImage, GetBackgroundImage, RelaunchApp, ListExternalEditors } from '../../bindings/easyaiot/terminal/app'
import { useSettingsStore } from '../stores/settingsStore'
import { useSyncStore } from '../stores/syncStore'
import { useLocalStateStore } from '../stores/localStateStore'
import { useI18n, locale } from '../i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { FONT_OPTIONS, FONT_WEIGHT_OPTIONS, LANGUAGE_OPTIONS, DEFAULT_KEYBOARD, DEFAULT_SETTINGS, SHORTCUT_LABELS, FOLLOW_APP_THEME, CURSOR_STYLES, TIMESTAMP_FORMATS, SIDEBAR_TAB_ORDER, SIDEBAR_TAB_DEFAULTS } from '../types/settings'
import { formatFontFamily, normalizeFontFamilyValue } from '../utils/formatFontFamily'
import { backendErrorText } from '../utils/backendError'
import { getShellLabel as getShellLabelBase } from '../utils/shellLabel'
import CommandsManager from './CommandsManager.vue'
import type { ShortcutAction, KeyBinding, KeyboardSettings } from '../types/settings'
import { useTerminalThemeOptions } from '../composables/useTerminalThemeOptions'
import { uninstallGlobalListener, installGlobalListener, formatKeyBinding, digitModifierCollides, digitModifierFlagsEqual, TAB_DEFAULT_FLAGS, PANEL_DEFAULT_FLAGS, setRebinding } from '../composables/useKeyboardShortcuts'
import AddRepoDialog from './AddRepoDialog.vue'
import EditRepoDialog from './EditRepoDialog.vue'
import ChangePasswordDialog from './ChangePasswordDialog.vue'
import DeleteRepoDialog from './DeleteRepoDialog.vue'
import CustomThemeEditor from './CustomThemeEditor.vue'
import DataDirDialog from './DataDirDialog.vue'
import IdentityEditDialog from './IdentityEditDialog.vue'
import ProxyEditDialog from './ProxyEditDialog.vue'
import TunnelEditDialog from './TunnelEditDialog.vue'
import { useCredentialStore } from '../stores/credentialStore'
import { useIdentityStore } from '../stores/identityStore'
import { useProxyStore } from '../stores/proxyStore'
import { useTunnelStore } from '../stores/tunnelStore'
import { useTunnelCredentials } from '../composables/useTunnelCredentials'
import type { Tunnel, TunnelMode } from '../stores/tunnelStore'
import type { Identity } from '../types/identity'
import { Browser } from '@wailsio/runtime'
import { isMobilePlatform } from '../utils/platform'
import type { Proxy } from '../types/proxy'
import { uiPx } from '../utils/uiScale'

const settingsStore = useSettingsStore()
const syncStore = useSyncStore()
const localStateStore = useLocalStateStore()
const { t } = useI18n()
const { resolveTunnelCredentials } = useTunnelCredentials()
// Mobile (android/ios) has no OS window, no mouse, no local shell and a
// system-managed data dir — settings that only make sense on the desktop are
// hidden there via `v-if="!isMobile"` / category filtering below.
const isMobile = isMobilePlatform()
const platform = ref('')
const appVersion = ref('')
const isMac = computed(() => platform.value === 'darwin')

// Editors detected on this host (from the backend). The dropdown shows exactly
// these; empty means no editor was found installed, so nothing is listed.
const detectedEditors = ref<{ label: string; value: string }[]>([])

// ── Config management (data dir + encryption mode) ──
const credStore = useCredentialStore()
const dataDirVisible = ref(false)
const showSetupMaster = ref(false)
const showVerifyMaster = ref(false)
const showChangePassword = ref(false)

const dataDirTypeLabel = computed(() => {
  if (!credStore.dataDirInfo.dataDir) return t('config.notSet')
  switch (credStore.dataDirInfo.type) {
    case 'default': return t('dataDir.default')
    case 'portable': return t('dataDir.portable')
    case 'custom': return t('dataDir.custom')
    default: return t('config.notSet')
  }
})

function openDataDirChange() {
  dataDirVisible.value = true   // reuse DataDirDialog (change mode: migrate checkbox visible)
}
function onDataDirChange(restart: boolean) {
  if (restart) {
    RelaunchApp()
  }
}
async function openChangePassword() { showChangePassword.value = true }

// Encryption-mode dropdown. The select mirrors the live mode; choosing a
// different option reverts immediately and opens the matching directional
// dialog instead. modeSelect only advances after a successful switch (via the
// watch below), so cancelling a dialog leaves the dropdown unchanged.
const modeSelect = ref<string>('')
watch(() => credStore.status.mode, (m) => { modeSelect.value = m || '' }, { immediate: true })

function onModeChange(val: string) {
  modeSelect.value = credStore.status.mode || ''  // revert until the switch actually lands
  if (!val || val === credStore.status.mode) return
  if (credStore.status.mode === '') {
    // No credentials configured yet: no existing password to verify.
    if (val === 'keychain') doSetupKeychain()
    else showSetupMaster.value = true
    return
  }
  if (val === 'master-password') showSetupMaster.value = true
  else showVerifyMaster.value = true
}

// keychain → master-password (or first-run master-password): configure a new password.
const setupPw = ref(''); const setupPw2 = ref('')
const setupError = ref(''); const setupSubmitting = ref(false)
watch(showSetupMaster, (v) => { if (v) { setupPw.value = ''; setupPw2.value = ''; setupError.value = '' } })

async function doSetupMaster() {
  if (setupSubmitting.value) return
  setupError.value = ''
  if (!setupPw.value) { setupError.value = t('encrypt.passwordRequired'); return }
  if (setupPw.value !== setupPw2.value) { setupError.value = t('encrypt.mismatch'); return }
  setupSubmitting.value = true
  try {
    if (credStore.status.mode === '') await credStore.setup('master-password', setupPw.value)
    else await credStore.switchMode('master-password', setupPw.value)
    showSetupMaster.value = false
    msg.success(t('config.switchDone'))
  } catch (e: any) { setupError.value = backendErrorText(e) }
  finally { setupSubmitting.value = false }
}

// master-password → keychain: verify the current master password once.
const verifyPw = ref('')
const verifyError = ref(''); const verifySubmitting = ref(false)
watch(showVerifyMaster, (v) => { if (v) { verifyPw.value = ''; verifyError.value = '' } })

async function doVerifyMaster() {
  if (verifySubmitting.value) return
  verifyError.value = ''
  if (!verifyPw.value) { verifyError.value = t('encrypt.passwordRequired'); return }
  verifySubmitting.value = true
  try {
    await credStore.switchMode('keychain', verifyPw.value)
    showVerifyMaster.value = false
    msg.success(t('config.switchDone'))
  } catch (e: any) { verifyError.value = backendErrorText(e) }
  finally { verifySubmitting.value = false }
}

// first-run / unconfigured → keychain: no password needed.
async function doSetupKeychain() {
  try {
    await credStore.setup('keychain', '')
    msg.success(t('config.switchDone'))
  } catch (e: any) { msg.error(backendErrorText(e)) }
}

const oldPw = ref(''); const newPw = ref(''); const newPw2 = ref('')
const changePwError = ref(''); const changePwSubmitting = ref(false)

// Clear fields each time the dialog opens so a previous password isn't shown.
watch(showChangePassword, (v) => {
  if (v) {
    oldPw.value = ''
    newPw.value = ''
    newPw2.value = ''
    changePwError.value = ''
  }
})

async function doChangePassword() {
  if (changePwSubmitting.value) return
  changePwError.value = ''
  if (!oldPw.value || !newPw.value) { changePwError.value = t('config.oldPassword') + ' / ' + t('config.newPassword'); return }
  if (newPw.value !== newPw2.value) { changePwError.value = t('encrypt.mismatch'); return }
  changePwSubmitting.value = true
  try {
    await credStore.changeMasterPassword(oldPw.value, newPw.value)
    showChangePassword.value = false
    msg.success(t('config.changeDone'))
  } catch (e: any) { changePwError.value = backendErrorText(e) }
  finally { changePwSubmitting.value = false }
}

function openEditRepo() {
  syncStore.showEditRepo = true
}

async function handleSyncNow() {
  const result = await syncStore.doSync()
  if (!result) {
    msg.error(syncStore.lastResult || t('settings.syncFailed'))
    return
  }
  if (result.direction === 3) {
    return  // conflict — handled by SyncConflictDialog
  }
  msg.success(result.message || t('settings.syncSuccess'))
}

async function handleAutoSyncToggle() {
  try {
    await syncStore.saveConfig()
  } catch (e) {
    console.error('Failed to save auto sync toggle:', e)
  }
}

syncStore.loadConfig()

// ── Terminal fonts ──
// Single source: GetAllFonts returns every installed family with its mono
// flag (the bundled JetBrains Mono Variable is pinned first). The per-select
// "monospace only" checkbox (inside each dropdown) filters this client-side.
const allFonts = ref<{ Name: string; IsMono: boolean }[]>([])
const firstMonoOnly = ref(true)
const secondMonoOnly = ref(true)

const toFontOption = (name: string) => ({ label: name, value: name })
const fontOptions = computed(() =>
  allFonts.value.length > 0
    ? allFonts.value.filter(f => !firstMonoOnly.value || f.IsMono).map(f => toFontOption(f.Name))
    : FONT_OPTIONS
)
const secondFontOptions = computed(() =>
  allFonts.value.length > 0
    ? allFonts.value.filter(f => !secondMonoOnly.value || f.IsMono).map(f => toFontOption(f.Name))
    : FONT_OPTIONS
)

const { terminalThemeGroups, isCustomTheme } = useTerminalThemeOptions()

const cursorStyleOptions = CURSOR_STYLES

const themeEditorVisible = ref(false)
const themeEditorSourceId = ref<string | undefined>(undefined)
function openThemeEditor(sourceThemeId?: string) {
  themeEditorSourceId.value = sourceThemeId
  themeEditorVisible.value = true
}

// ── Sidebar collapse ──
// The category sidebar (11.25rem) pushes the settings panel off-screen on
// narrow windows (phone portrait). Collapse to icons-only below the width
// where the expanded layout stops fitting; the button toggles it manually
// and the auto rule re-applies whenever the window crosses the threshold.
const settingsTabRef = ref<HTMLElement | null>(null)
const sidebarCollapsed = ref(false)
// Below the same threshold the side-by-side setting cards (info + fixed-width
// control) cannot fit either, so the panel stacks them vertically.
const isNarrow = ref(false)

function updateSidebarCollapse() {
  const el = settingsTabRef.value
  if (!el) return
  const rem = parseFloat(getComputedStyle(document.documentElement).fontSize)
  // Expanded layout needs ~13.1rem sidebar + ~29rem panel => 42rem minimum.
  isNarrow.value = el.clientWidth < 42 * rem
  sidebarCollapsed.value = isNarrow.value
}

let sidebarResizeObserver: ResizeObserver | null = null

onMounted(() => {
  updateSidebarCollapse()
  if (settingsTabRef.value) {
    sidebarResizeObserver = new ResizeObserver(updateSidebarCollapse)
    sidebarResizeObserver.observe(settingsTabRef.value)
  }
})

onUnmounted(() => {
  sidebarResizeObserver?.disconnect()
  sidebarResizeObserver = null
})

onMounted(async () => {
  try {
    platform.value = await GetPlatform()
  } catch {
    platform.value = ''
  }
  try {
    appVersion.value = (await GetAppInfo()).version
  } catch {
    appVersion.value = ''
  }
  // Populate the external-editor dropdown with editors actually installed on
  // this host; fall back to the curated presets if detection returns nothing.
  try {
    const editors = await ListExternalEditors()
    detectedEditors.value = (editors || []).map(e => ({ label: e.label, value: e.value }))
  } catch {
    detectedEditors.value = []
  }
  try {
    const fonts = await GetAllFonts()
    if (fonts && fonts.length > 0) {
      allFonts.value = fonts
      // Migrate a legacy full-stack fontFamily down to its bare family name so
      // it matches a dropdown option (and the new single-name default) — the
      // old stored value was a raw CSS stack this picker can't show cleanly.
      const names = new Set(allFonts.value.map(f => f.Name))
      const cur = settingsStore.settings.terminal.fontFamily
      const normalized = normalizeFontFamilyValue(cur, names)
      if (normalized !== cur) {
        settingsStore.settings.terminal.fontFamily = normalized
        settingsStore.save()
      }
    }
  } catch {
    // Fall back to FONT_OPTIONS
  }
  try {
    defaultLogDir.value = await GetDefaultSessionLogDir()
  } catch {
    defaultLogDir.value = ''
  }
  try {
    await refreshBgPreview()
  } catch {
    // Ignore preview errors
  }
  try {
    await identityStore.load()
  } catch {
    // Ignore identity load errors
  }
  try {
    await proxyStore.load()
  } catch {
    // Ignore proxy load errors
  }
  try {
    await tunnelStore.load()
  } catch {
    // Ignore tunnel load errors
  }
})

// Session log directory: shown as placeholder when the setting is
// empty. Value comes from backend on mount and reflects the OS
// default plus any current override (so if the user cleared their
// override, the placeholder shows the fallback path).
const defaultLogDir = ref('')

// Default word separator for xterm's double-click selection; shown in
// the settings input as a placeholder so the user can see what to
// reset to.
const defaultWordSeparator = '\\ :;~`!@#$%^&*()=+|[]{}\'",<>?'

async function pickLogDir() {
  try {
    const chosen = await OpenDirectoryDialog()
    if (chosen) {
      settingsStore.settings.terminal.sessionLogDir = chosen
      await settingsStore.save()
    }
  } catch (e: any) {
    msg.error(String(e?.message ?? e))
  }
}

async function pickZmodemDownloadDir() {
  try {
    const chosen = await OpenDirectoryDialog()
    if (chosen) {
      settingsStore.settings.terminal.zmodemDownloadDir = chosen
      await settingsStore.save()
    }
  } catch (e: any) {
    msg.error(String(e?.message ?? e))
  }
}

watch(() => settingsStore.openCategory, (cat) => {
  if (cat && (cat === 'basic' || cat === 'terminal' || cat === 'sync' || cat === 'about' || (cat === 'keyboard' && !isMobile) || cat === 'identities' || cat === 'proxies' || cat === 'tunnels')) {
    settingsStore.activeCategory = cat
    settingsStore.openCategory = null
  }
})

// ── Keyboard rebinding ──
const rebindingAction = ref<ShortcutAction | null>(null)

// Capture mode for the modifier+digit tab/panel-switch rows: unlike
// per-action bindings, only the modifier flags are stored and `key` stays
// empty.
const rebindingTabSwitch = ref(false)
const rebindingPanelSwitch = ref(false)
const rebindingTrayHotkey = ref(false)

// Display grouping for the keyboard settings table: related shortcuts share
// a sub-heading so the long list stays scannable. The two digit-modifier
// rows are hardcoded in the 'tabs' section (custom edit/clear controls).
// Every ShortcutAction must appear exactly once.
const shortcutCategories: { key: string; label: string; actions: ShortcutAction[] }[] = [
  {
    key: 'tabs',
    label: 'shortcut.catTabs',
    actions: ['newConnection', 'nextTab', 'prevTab', 'navigatePrev', 'navigateNext', 'closePanel', 'duplicateSession', 'maximizePanel'],
  },
  {
    key: 'sidebar',
    label: 'shortcut.catSidebar',
    actions: ['toggleSidebar', 'openQuickCommands', 'openSettings'],
  },
  {
    key: 'terminal',
    label: 'shortcut.catTerminal',
    actions: ['focusTerminal', 'copy', 'paste', 'terminalSearch', 'zoomFontIn', 'zoomFontOut', 'toggleLineNumbers', 'toggleTimestamps'],
  },
]

function bindingDisplay(action: ShortcutAction): string {
  const b = settingsStore.settings.keyboard[action]
  if (!b) return ''
  return formatKeyBinding(b, isMac.value)
}

function isDefaultBinding(action: ShortcutAction): boolean {
  const current = settingsStore.settings.keyboard[action]
  const def = DEFAULT_KEYBOARD[action]
  if (!current || !def) return true
  return current.ctrl === def.ctrl && current.shift === def.shift
    && current.alt === def.alt && current.key === def.key
}

function resetBinding(action: ShortcutAction) {
  settingsStore.settings.keyboard = {
    ...settingsStore.settings.keyboard,
    [action]: { ...DEFAULT_KEYBOARD[action] }
  }
  settingsStore.save()
}

let rebindListenerActive = false

function startRebind(action: ShortcutAction) {
  rebindingAction.value = action
  uninstallGlobalListener()
  setRebinding(true)
  if (!rebindListenerActive) {
    rebindListenerActive = true
    document.addEventListener('keydown', onRebindKeydown, true)
    window.addEventListener('blur', onRebindBlur)
  }
}

function stopRebind() {
  if (rebindListenerActive) {
    rebindListenerActive = false
    document.removeEventListener('keydown', onRebindKeydown, true)
    window.removeEventListener('blur', onRebindBlur)
  }
  rebindingAction.value = null
  rebindingTabSwitch.value = false
  rebindingPanelSwitch.value = false
  rebindingTrayHotkey.value = false
  setRebinding(false)
  installGlobalListener()
}

function clearBinding(action: ShortcutAction) {
  settingsStore.settings.keyboard = {
    ...settingsStore.settings.keyboard,
    [action]: { ctrl: false, shift: false, alt: false, key: '' }
  }
  settingsStore.save()
  stopRebind()
}

function onRebindKeydown(e: KeyboardEvent) {
  if (rebindingTrayHotkey.value) return onRebindTrayHotkeyKeydown(e)
  if (rebindingTabSwitch.value) return onRebindTabSwitchKeydown(e)
  if (rebindingPanelSwitch.value) return onRebindPanelSwitchKeydown(e)
  if (!rebindingAction.value) return stopRebind()
  e.preventDefault()
  e.stopPropagation()
  const key = e.key
  if (key === 'Escape') return stopRebind()
  if (key === 'Control' || key === 'Shift' || key === 'Alt' || key === 'Meta') return
  if (!e.ctrlKey && !e.metaKey && !e.shiftKey && !e.altKey) {
    // Bare keys are never valid bindings — they would break normal typing.
    msg.warning(t('shortcut.needsModifier'))
    return
  }

  const binding: KeyBinding = {
    // macOS: Cmd is recorded as ctrl — ctrl combos mirror to Cmd at runtime.
    ctrl: e.ctrlKey || e.metaKey,
    shift: e.shiftKey,
    alt: e.altKey,
    key: key.toLowerCase(),
  }

  // Check for conflicts and clear them
  const conflictAction = findConflict(binding)
  const kb = { ...settingsStore.settings.keyboard }
  kb[rebindingAction.value] = binding
  if (conflictAction) {
    kb[conflictAction] = { ctrl: false, shift: false, alt: false, key: '' }
  }
  settingsStore.settings.keyboard = kb as KeyboardSettings
  settingsStore.save()
  stopRebind()
}

function findConflict(binding: KeyBinding): ShortcutAction | null {
  const targetKey = bindingKey(binding)
  const kb = settingsStore.settings.keyboard
  for (const [action, b] of Object.entries(kb) as [ShortcutAction, KeyBinding][]) {
    if (action === rebindingAction.value) continue
    if (!b.key) continue
    if (bindingKey(b) === targetKey) return action
  }
  return null
}

function bindingKey(binding: KeyBinding): string {
  return `${binding.ctrl ? 'ctrl+' : ''}${binding.shift ? 'shift+' : ''}${binding.alt ? 'alt+' : ''}${binding.key.toLowerCase()}`
}

// ── Configurable digit modifiers (tab/panel switching) ──
//
// Only the modifier flags are stored (`key` stays empty). Unset = platform
// default (tabs: Ctrl on Windows/Linux, Cmd on macOS; panels: Alt/Option);
// cleared (no modifier) disables that digit family; any configured combo
// moves it there. When both families resolve to the same combo, tab
// switching wins and the panel digit shortcuts are suppressed (their badges
// hide too — see panelDigitShortcutsSuppressed).

type DigitModifierKey = 'tabSwitchModifier' | 'panelSwitchModifier'

function digitModifierBindingDisplay(key: DigitModifierKey, defaultMods: string): string {
  const b = settingsStore.settings.keyboard[key]
  if (!b) {
    // Effective platform default, shown so the row never reads as "off".
    return `${defaultMods} + ${t('shortcut.digitKeys')}`
  }
  if (!b.ctrl && !b.shift && !b.alt) {
    // Cleared = the family is disabled; show an empty binding.
    return ''
  }
  // formatKeyBinding pushes the (empty) key too, leaving a trailing '+'
  const mods = formatKeyBinding({ ctrl: !!b.ctrl, shift: !!b.shift, alt: !!b.alt, key: '' }, isMac.value).replace(/\++$/, '')
  return `${mods} + ${t('shortcut.digitKeys')}`
}

function tabSwitchBindingDisplay(): string {
  // Mac default shows the ⌘ symbol (not the word "Cmd") so the row matches
  // the symbol style of formatKeyBinding and every other binding row.
  return digitModifierBindingDisplay('tabSwitchModifier', isMac.value ? '⌘' : 'Ctrl')
}

function panelSwitchBindingDisplay(): string {
  return digitModifierBindingDisplay('panelSwitchModifier', isMac.value ? '⌥' : 'Alt')
}

function isTabSwitchModifierUnset(): boolean {
  return !settingsStore.settings.keyboard.tabSwitchModifier
}

function isPanelSwitchModifierUnset(): boolean {
  return !settingsStore.settings.keyboard.panelSwitchModifier
}

function setDigitModifier(key: DigitModifierKey, binding: KeyBinding | null) {
  const kb: KeyboardSettings = { ...settingsStore.settings.keyboard }
  if (binding) {
    const isTab = key === 'tabSwitchModifier'
    // The two digit families are mutually exclusive: assigning one clears the
    // other when it claims the same combo. An unset other family still counts
    // through its own platform default — otherwise e.g. panels set to Ctrl
    // would silently lose to the default tab switching. This runs BEFORE the
    // own-default check below: recording e.g. Ctrl back onto tabs must clear
    // a conflicting panel binding even though Ctrl is also the tab default.
    const otherKey: DigitModifierKey = isTab ? 'panelSwitchModifier' : 'tabSwitchModifier'
    const otherDefault = isTab ? PANEL_DEFAULT_FLAGS : TAB_DEFAULT_FLAGS
    if (digitModifierCollides(kb[otherKey], otherDefault, binding)) {
      kb[otherKey] = { ctrl: false, shift: false, alt: false, key: '' }
    }
    const ownDefault = isTab ? TAB_DEFAULT_FLAGS : PANEL_DEFAULT_FLAGS
    // Recording a family's own platform default (Ctrl for tabs, Alt for
    // panels) is the same as never having configured it — store nothing so
    // the row keeps showing the default and reset stays hidden.
    if (digitModifierFlagsEqual(binding, ownDefault)) {
      delete kb[key]
    } else {
      kb[key] = binding
      // Mirror the per-action conflict rule: an action explicitly bound to
      // the same combo with a digit key would shadow the family for that
      // digit (the global keybinding listener runs before the platform
      // handler), so clear it like findConflict does for regular rebinds.
      for (const [action, b] of Object.entries(kb) as [ShortcutAction, KeyBinding][]) {
        if ((action as string) === key) continue
        if (!b || !b.key || !/^[1-9]$/.test(b.key)) continue
        if (digitModifierFlagsEqual(b, binding)) {
          kb[action] = { ctrl: false, shift: false, alt: false, key: '' }
        }
      }
    }
  } else {
    delete kb[key]
  }
  settingsStore.settings.keyboard = kb
  settingsStore.save()
}

function setTabSwitchModifier(binding: KeyBinding | null) {
  setDigitModifier('tabSwitchModifier', binding)
}

function setPanelSwitchModifier(binding: KeyBinding | null) {
  setDigitModifier('panelSwitchModifier', binding)
}

function resetTabSwitchModifier() {
  // Back to unset = platform default (Ctrl/Cmd+digit tabs, Alt/Option+digit
  // workspace panels).
  setDigitModifier('tabSwitchModifier', null)
}

function resetPanelSwitchModifier() {
  // Back to unset = platform default (Alt/Option+digit workspace panels).
  setDigitModifier('panelSwitchModifier', null)
}

function clearTabSwitchModifier() {
  // All flags off = digit tab switching disabled; panels keep their digits.
  setDigitModifier('tabSwitchModifier', { ctrl: false, shift: false, alt: false, key: '' })
  stopRebind()
}

function clearPanelSwitchModifier() {
  // All flags off = panel digit switching disabled; tabs keep their digits.
  setDigitModifier('panelSwitchModifier', { ctrl: false, shift: false, alt: false, key: '' })
  stopRebind()
}

function startRebindTabSwitch() {
  rebindingTabSwitch.value = true
  uninstallGlobalListener()
  setRebinding(true)
  if (!rebindListenerActive) {
    rebindListenerActive = true
    document.addEventListener('keydown', onRebindKeydown, true)
    window.addEventListener('blur', onRebindBlur)
  }
}

function startRebindPanelSwitch() {
  rebindingPanelSwitch.value = true
  uninstallGlobalListener()
  setRebinding(true)
  if (!rebindListenerActive) {
    rebindListenerActive = true
    document.addEventListener('keydown', onRebindKeydown, true)
    window.addEventListener('blur', onRebindBlur)
  }
}

// Modifier-only capture: bare modifier presses are ignored so the user can
// build the combo (e.g. Ctrl+Alt); the next non-modifier key press confirms
// the held modifiers — its own key is discarded.
function onRebindModifierKeydown(e: KeyboardEvent, apply: (binding: KeyBinding) => void) {
  e.preventDefault()
  e.stopPropagation()
  if (e.key === 'Escape') return stopRebind()
  if (e.key === 'Control' || e.key === 'Shift' || e.key === 'Alt' || e.key === 'Meta') return
  if (!e.ctrlKey && !e.metaKey && !e.shiftKey && !e.altKey) {
    // Bare keys are never valid bindings — they would break normal typing.
    msg.warning(t('shortcut.needsModifier'))
    return
  }
  // macOS: Cmd is recorded as ctrl — ctrl combos mirror to Cmd at runtime.
  apply({ ctrl: e.ctrlKey || e.metaKey, shift: e.shiftKey, alt: e.altKey, key: '' })
  stopRebind()
}

function onRebindTabSwitchKeydown(e: KeyboardEvent) {
  onRebindModifierKeydown(e, setTabSwitchModifier)
}

function onRebindPanelSwitchKeydown(e: KeyboardEvent) {
  onRebindModifierKeydown(e, setPanelSwitchModifier)
}

// ── Global show/hide hotkey (tray, system-wide) ──

function trayHotkeyDisplay(): string {
  const b = settingsStore.settings.keyboard.trayShowHide
  return b ? formatKeyBinding(b, isMac.value) : ''
}

function isTrayHotkeyDefault(): boolean {
  const b = settingsStore.settings.keyboard.trayShowHide
  const def = DEFAULT_KEYBOARD.trayShowHide
  if (!b || !def) return b === def
  return b.ctrl === def.ctrl && b.shift === def.shift && b.alt === def.alt && b.key === def.key
}

function startRebindTrayHotkey() {
  rebindingTrayHotkey.value = true
  rebindingAction.value = null
  rebindingTabSwitch.value = false
  rebindingPanelSwitch.value = false
  uninstallGlobalListener()
  setRebinding(true)
  if (!rebindListenerActive) {
    rebindListenerActive = true
    document.addEventListener('keydown', onRebindKeydown, true)
    window.addEventListener('blur', onRebindBlur)
  }
}

function onRebindTrayHotkeyKeydown(e: KeyboardEvent) {
  e.preventDefault()
  e.stopPropagation()
  if (e.key === 'Escape') return stopRebind()
  if (e.key === 'Control' || e.key === 'Shift' || e.key === 'Alt' || e.key === 'Meta') return
  if (!e.ctrlKey && !e.metaKey && !e.shiftKey && !e.altKey) {
    // Bare keys are never valid bindings — they would break normal typing.
    msg.warning(t('shortcut.needsModifier'))
    return
  }
  // macOS: Cmd is recorded as ctrl — ctrl combos mirror to Cmd at runtime.
  settingsStore.settings.keyboard = {
    ...settingsStore.settings.keyboard,
    trayShowHide: {
      ctrl: e.ctrlKey || e.metaKey,
      shift: e.shiftKey,
      alt: e.altKey,
      key: e.key.toLowerCase()
    }
  }
  settingsStore.save()
  stopRebind()
}

function clearTrayHotkey() {
  // All flags off + empty key = binding removed, hotkey unregistered.
  settingsStore.settings.keyboard = {
    ...settingsStore.settings.keyboard,
    trayShowHide: { ctrl: false, shift: false, alt: false, key: '' }
  }
  settingsStore.save()
  stopRebind()
}

function resetTrayHotkey() {
  const def = DEFAULT_KEYBOARD.trayShowHide
  if (!def) return
  settingsStore.settings.keyboard = {
    ...settingsStore.settings.keyboard,
    trayShowHide: { ...def }
  }
  settingsStore.save()
}

function onRebindBlur() {
  stopRebind()
}

const categories = computed(() => {
  // Explicitly read language to ensure reactivity tracking
  void settingsStore.settings.language
  const cats = [
    { key: 'basic', label: t('settings.basic'), icon: Settings },
    { key: 'terminal', label: t('settings.terminal'), icon: Monitor },
    // Keyboard shortcuts still WORK on mobile (physical keyboards), but the
    // rebinding UI is desktop-only and hidden from the category list there.
    ...(!isMobile ? [{ key: 'keyboard', label: t('shortcut.title'), icon: Keyboard }] : []),
    { key: 'commands', label: t('settings.commands'), icon: Wrench },
    { key: 'identities', label: t('settings.identities'), icon: Key },
    { key: 'proxies', label: t('settings.proxies'), icon: Network },
    { key: 'tunnels', label: t('settings.tunnels'), icon: ArrowRightLeft },
    { key: 'sync', label: t('settings.sync'), icon: RefreshCw },
    { key: 'about', label: t('settings.about'), icon: Info },
  ]
  return cats
})

// A persisted 'keyboard' active category would show an empty settings page on
// mobile — fall back to basic.
watch(categories, (cats) => {
  if (isMobile && settingsStore.activeCategory === 'keyboard' && !cats.some(c => c.key === 'keyboard')) {
    settingsStore.activeCategory = 'basic'
  }
}, { immediate: true })

// ── Identities (密钥库) ──
const identityStore = useIdentityStore()
const identityDialogVisible = ref(false)
const editingIdentity = ref<Identity | null>(null)
function openIdentityDialog(id?: Identity) {
  editingIdentity.value = id ?? null
  identityDialogVisible.value = true
}
async function removeIdentity(row: Identity) {
  await identityStore.remove(row.id)
  ElMessage.success(t('settings.deleted'))
}

// ── Proxies (代理) ──
const proxyStore = useProxyStore()
const proxyDialogVisible = ref(false)
const editingProxy = ref<Proxy | null>(null)
function openProxyDialog(p?: Proxy) {
  editingProxy.value = p ?? null
  proxyDialogVisible.value = true
}
async function removeProxy(row: Proxy) {
  await proxyStore.remove(row.id)
}

// Enable toggle (issue #749): a disabled proxy is skipped on connect and the
// referencing connection dials directly.
async function toggleProxy(row: Proxy, v: boolean) {
  await proxyStore.update({ ...row, enabled: v })
}

// ── Tunnels (隧道) ──
const tunnelStore = useTunnelStore()
const tunnelDialogVisible = ref(false)
const editingTunnelId = ref<string | undefined>(undefined)
const togglingTunnelId = ref<string | undefined>(undefined)

// ── Sidebar tab visibility ──
// Writable computed over AppSettings.sidebarTabs. "connections" never appears
// in the select (no option, no tag) — it is forced on at the data level.
const visibleSidebarTabs = computed<string[]>({
  get: () => SIDEBAR_TAB_ORDER
    .map(tab => tab.key)
    .filter(key => key !== 'connections')
    .filter(key => settingsStore.settings.sidebarTabs?.[key] ?? SIDEBAR_TAB_DEFAULTS[key] ?? true),
  set: (keys: string[]) => {
    const tabs = settingsStore.settings.sidebarTabs
    for (const tab of SIDEBAR_TAB_ORDER) {
      tabs[tab.key] = tab.key === 'connections' || keys.includes(tab.key)
    }
  },
})
function onSidebarTabsChange() {
  settingsStore.save()
}
function openTunnelDialog(t?: Tunnel) {
  editingTunnelId.value = t?.id
  tunnelDialogVisible.value = true
}
async function removeTunnel(row: Tunnel) {
  await tunnelStore.deleteTunnel(row.id)
}
const modeName = (m: TunnelMode) => t(`tunnels.mode.${m}`)
const effPort = (t: Tunnel) => tunnelStore.states[t.id]?.localPort || t.listenPort
const statusOf = (id: string) => tunnelStore.statusOf(id)
async function toggleRun(row: Tunnel) {
  if (statusOf(row.id) === 'running') {
    togglingTunnelId.value = row.id
    await tunnelStore.stop(row.id)
    togglingTunnelId.value = undefined
  } else {
    // Exit connection without saved credentials: prompt for user/password and
    // pass them inline (backend fills only empty fields). Cancel aborts.
    const creds = await resolveTunnelCredentials(row.sshConnId)
    if (!creds) return
    togglingTunnelId.value = row.id
    const st = await tunnelStore.start(row.id, creds.user, creds.password)
    togglingTunnelId.value = undefined
    if (st.status === 'error') {
      msg.error(st.error || t('tunnels.startFailed'))
    }
  }
}

function getShellLabel(path: string): string {
  return getShellLabelBase(path, 'Local')
}

const bgPreview = ref('')

async function refreshBgPreview() {
  const name = localStateStore.state.backgroundImage
  bgPreview.value = name ? await GetBackgroundImage(name).catch(() => '') : ''
}

async function chooseBackground() {
  const path = await OpenFileDialogFiltered(
    t('settings.bgChoose'),
    'Images',
    '*.png;*.jpg;*.jpeg;*.webp'
  )
  if (!path) return
  try {
    const name = await SetBackgroundImage(path)
    await localStateStore.update({ backgroundImage: name, backgroundEnabled: true })
    await refreshBgPreview()
  } catch {
    msg.error(t('settings.bgUnsupported'))
  }
}

async function clearBackground() {
  await ClearBackgroundImage()
  await localStateStore.update({ backgroundImage: '' })
  bgPreview.value = ''
}

// The window frame is fixed at startup (Wails limitation) — changing it needs
// a restart. Persist the choice, then offer to quit so the user can reopen.
async function onToggleSystemTitleBar(v: boolean) {
  await localStateStore.update({ systemTitleBar: v })
  try {
    await ElMessageBox.confirm(
      t('settings.titleBarRestartMsg'),
      t('settings.titleBarRestartTitle'),
      { confirmButtonText: t('settings.restartNow'), cancelButtonText: t('conn.cancel'), type: 'warning' }
    )
  } catch {
    return
  }
  await RelaunchApp()
}
</script>

<style scoped>
.settings-tab {
  display: flex;
  width: 100%;
  height: 100%;
  background: var(--bg-base);
  color: var(--text-primary);
}

.settings-sidebar {
  width: 11.25rem;
  flex-shrink: 0;
  margin-left: 1.25rem;
  margin-right: 0.625rem;
  padding: 1rem 0;
  border-right: 1px solid var(--border-hover);
  transition: width 0.15s ease;
  /* Scroll independently when the window is too short for every category */
  overflow-y: auto;
  overflow-x: hidden;
}

.sidebar-collapse-btn {
  position: sticky;
  top: 0;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1.75rem;
  height: 1.75rem;
  margin: 0 0.5rem 0.5rem;
  margin-left: auto;
  padding: 0;
  background: var(--bg-base);
  border: none;
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.12s ease;
}

.sidebar-collapse-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

/* Collapsed: icons only, centered */
.settings-sidebar.collapsed {
  width: 3.5rem;
  margin-left: 0.625rem;
  margin-right: 0.375rem;
}

.settings-sidebar.collapsed .sidebar-collapse-btn {
  margin-left: auto;
}

.settings-sidebar.collapsed .settings-category {
  justify-content: center;
  padding: 0.625rem 0.5rem;
  margin: 0 0.375rem;
  gap: 0;
}

.settings-category {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.625rem 1rem;
  margin: 0 0.5rem;
  font-size: 0.8125rem;
  font-family: var(--font-ui);
  cursor: pointer;
  user-select: none;
  color: var(--text-secondary);
  border-radius: var(--radius-sm);
  transition: all 0.12s ease;
  border-left: 0.1875rem solid transparent;
}

.settings-category:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.settings-category.active {
  background: var(--accent-subtle);
  color: var(--accent);
  border-left-color: var(--accent);
  backdrop-filter: blur(0.5rem);
}

.category-icon {
  font-size: 1rem;
}

.category-label {
  line-height: 1;
}

.settings-panel {
  flex: 1;
  padding: 1.5rem 2rem;
  overflow-y: auto;
}

.settings-section {
  min-width: min(25rem, 100%);
  max-width: 1000px;
  margin: 0 auto;
}

/* Narrow windows (phone portrait): stack each setting card vertically so the
   control gets the full row instead of squeezing the title into one char
   per line. */
.settings-tab.narrow .setting-card {
  flex-direction: column;
  align-items: stretch;
  gap: 0.625rem;
}

.settings-tab.narrow .setting-control {
  min-width: 0;
}

.settings-tab.narrow .setting-control .el-select,
.settings-tab.narrow .setting-control .editor-select.el-select {
  width: 100%;
}

.section-title {
  font-size: 1.125rem;
  font-weight: 600;
  font-family: var(--font-ui);
  margin: 1.25rem 0 1.25rem 0;
  color: var(--text-primary);
}

.settings-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.setting-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.875rem 1.125rem;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  transition: all 0.12s ease;
  backdrop-filter: blur(0.5rem);
}

.setting-card:hover {
  border-color: var(--border-hover);
}

.setting-info {
  flex: 1;
  min-width: 0;
}

.setting-title {
  font-size: 0.8125rem;
  font-weight: 500;
  font-family: var(--font-ui);
  color: var(--text-primary);
  margin-bottom: 0.125rem;
}

.setting-desc {
  font-size: 0.6875rem;
  font-family: var(--font-ui);
  color: var(--text-muted);
  line-height: 1.4;
}

.setting-control {
  flex-shrink: 0;
  min-width: 13.125rem;
}

/* Keep the external-editor combobox the same width as the other select
   controls instead of the default 100% (the free-input form stretches). */
.setting-control .editor-select.el-select {
  width: 13.125rem;
}


/* The append button's width adds to the input's, so pin the whole group to
   the 13.125rem the sibling selects render at instead of letting it overflow. */
.setting-control .dir-input {
  width: 13.125rem;
}

.config-value {
  font-size: 0.8125rem;
  color: var(--text-secondary);
}

.settings-form { display: flex; flex-direction: column; gap: 0.25rem; }
.switch-mode-hint { font-size: 0.75rem; color: var(--text-muted); line-height: 1.4; }
.verify-field { display: flex; flex-direction: column; gap: 0.25rem; width: 100%; }

.form-error { color: var(--el-color-danger); font-size: 0.8125rem; margin-top: 0.5rem; }

.setting-control .el-select,
.setting-control .el-input-number {
  width: 100%;
}

.theme-select-row {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  width: 100%;
}

.theme-select-row .el-select {
  flex: 1;
  min-width: 0;
  width: auto;
}

/* Model cards */
.about-content {
  text-align: left;
  padding: 1.25rem 0;
}
.about-appname {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 0.75rem;
}
.about-desc {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin: 0 0 1.5rem 0;
  line-height: 1.6;
  max-width: 25rem;
}
.about-version {
  font-size: 0.75rem;
  color: var(--text-muted);
  font-family: var(--font-mono);
}
.about-links {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-top: 0.75rem;
}
.about-link {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.75rem;
  color: var(--accent);
  text-decoration: none;
  transition: opacity 0.12s ease;
}
.about-link:hover {
  opacity: 0.8;
  text-decoration: underline;
}
.about-link-icon {
  flex-shrink: 0;
  opacity: 0.7;
}

.section-desc {
  font-size: 0.8125rem;
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.5;
}

.sync-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  margin-bottom: 1rem;
  overflow: hidden;
}

.sync-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.8125rem;
  font-weight: 600;
  font-family: var(--font-ui);
  color: var(--text-primary);
  padding: 0.5rem 0.75rem 0.5rem 1.125rem;
  background: var(--bg-hover);
  border-bottom: 1px solid var(--border-subtle);
}

.sync-card-body {
  padding: 1rem 1.125rem;
}

.sync-card-body.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 1.75rem 1.125rem;
}

.empty-text {
  font-size: 0.8125rem;
  color: var(--text-muted);
  margin: 0;
}

/* Repo config */
.repo-info {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  margin-bottom: 0.75rem;
}

.repo-info-row {
  display: flex;
  gap: 0.75rem;
  font-size: 0.8125rem;
}

.repo-label {
  color: var(--text-muted);
  min-width: 4.375rem;
  flex-shrink: 0;
}

.repo-value {
  color: var(--text-primary);
  font-family: var(--font-mono);
  word-break: break-all;
}

.repo-warning {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 0.875rem;
  background: var(--el-color-warning-light-9);
  border: 1px solid var(--el-color-warning-light-5);
  border-radius: 0.375rem;
  margin-bottom: 0.875rem;
  color: var(--el-color-warning-dark-2);
  font-size: 0.75rem;
  line-height: 1.5;
}

.repo-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.repo-actions-left {
  display: flex;
  gap: 0.5rem;
}

/* Sync status */
.sync-status {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  margin-bottom: 0.875rem;
}

.sync-status-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8125rem;
}

.sync-label {
  color: var(--text-muted);
  min-width: 4.375rem;
  flex-shrink: 0;
}

.sync-value {
  color: var(--text-primary);
}

.sync-tag {
  font-size: 0.6875rem;
  padding: 0.125rem 0.5rem;
  border-radius: 0.625rem;
  font-weight: 500;
}

.sync-tag.success {
  background: var(--el-color-success-light-9);
  color: var(--el-color-success-dark-2);
}

.sync-tag.failed {
  background: var(--el-color-danger-light-9);
  color: var(--el-color-danger-dark-2);
}

.sync-error {
  align-items: flex-start;
}

.error-text {
  color: var(--el-color-danger);
}

.sync-actions-row {
  margin-bottom: 0.875rem;
}

.sync-auto-row {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding-top: 0.875rem;
  border-top: 1px solid var(--border-subtle);
}

.sync-auto-label {
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--text-primary);
}

.sync-auto-desc {
  font-size: 0.75rem;
  color: var(--text-muted);
  flex: 1;
}

.kb-key {
  display: inline-block;
  padding: 0.125rem 0.5rem;
  background: var(--bg-overlay);
  border: 1px solid var(--border-subtle);
  border-radius: 0.25rem;
  /* UI font so macOS modifier symbols (⌘⌥⇧) render with their native
     system-font shapes instead of the thin mono fallback glyphs. */
  font-family: var(--font-ui);
  font-size: 0.75rem;
  color: var(--text-primary);
}

.kb-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8125rem;
}

.kb-table th, .kb-table td {
  padding: 0.625rem 0.75rem;
  text-align: left;
  border-bottom: 1px solid var(--border-subtle);
}

.kb-table th {
  color: var(--text-muted);
  font-weight: 500;
  font-size: 0.75rem;
  text-transform: uppercase;
}

.kb-table tbody tr:hover {
  background: var(--bg-hover);
}

.kb-hint {
  margin-top: 0.125rem;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.kb-modifier-note {
  margin: 0 0 0.625rem;
}

.kb-actions {
  display: flex;
  gap: 0.375rem;
}

.bg-image-row { display: flex; align-items: center; gap: 0.5rem; }
.bg-thumb {
  width: 4rem; height: 2.5rem; border-radius: 0.25rem;
  background-size: cover; background-position: center;
  border: 1px solid var(--border-subtle);
}
</style>
