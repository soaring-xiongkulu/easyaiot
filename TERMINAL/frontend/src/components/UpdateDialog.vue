<template>
  <el-dialog
    :model-value="updateCheck.updateDialogVisible"
    :title="t('settings.updateDialogTitle')"
    width="33.75rem"
    :close-on-click-modal="false"
    :close-on-press-escape="!locked"
    :show-close="!locked"
    @update:model-value="(v: boolean) => { if (!v) updateCheck.closeUpdateDialog() }"
  >
    <div class="update-dialog">
      <div class="update-dialog-version">
        {{ t('settings.version') }} {{ updateCheck.updateInfo?.current || '...' }} → {{ updateCheck.updateInfo?.latest || '...' }}
      </div>

      <div class="update-dialog-hint">
        {{ t('settings.updatePackageManager') }}
      </div>

      <!-- Release notes are markdown; render as sanitized HTML -->
      <div v-if="changelogHtml" class="update-dialog-changelog" v-html="changelogHtml"></div>

      <div v-if="updateCheck.updatePhase === 'error'" class="update-dialog-error">
        {{ t('settings.updateFailed') }}: {{ updateCheck.updateError }}
      </div>

      <div v-if="updateCheck.updatePhase === 'downloading' || updateCheck.updatePhase === 'verifying'" class="update-dialog-progress">
        <el-progress :percentage="updateCheck.downloadProgress.percent" :stroke-width="10" :indeterminate="updateCheck.downloadProgress.total <= 0" />
        <div class="update-dialog-progress-label">
          {{ updateCheck.updatePhase === 'verifying' ? t('settings.updateVerifying') : t('settings.updateDownloading') }}
          <span v-if="updateCheck.updatePhase === 'downloading' && updateCheck.downloadProgress.received > 0" class="update-dialog-progress-size">
            ({{ fmtSize(updateCheck.downloadProgress.received) }}<template v-if="updateCheck.downloadProgress.total > 0"> / {{ fmtSize(updateCheck.downloadProgress.total) }}</template>)
          </span>
        </div>
      </div>

      <div v-if="updateCheck.updatePhase === 'applying'" class="update-dialog-progress-label">
        {{ t('settings.updateApplying') }}
      </div>
      <div v-if="updateCheck.updatePhase === 'restarting'" class="update-dialog-progress-label">
        {{ t('settings.updateRestarting') }}
      </div>
    </div>
    <template #footer>
      <el-button
        v-if="updateCheck.updatePhase === 'idle' || updateCheck.updatePhase === 'error'"
        :disabled="!releaseUrl"
        @click="openRelease"
      >
        {{ t('settings.openRelease') }}
      </el-button>
      <el-button v-if="updateCheck.updatePhase === 'idle' || updateCheck.updatePhase === 'error'" @click="updateCheck.closeUpdateDialog()">
        {{ t('settings.updateLater') }}
      </el-button>
      <el-button
        v-if="updateCheck.updatePhase === 'idle' || updateCheck.updatePhase === 'error'"
        type="primary"
        @click="updateCheck.startUpdate()"
      >
        {{ t('settings.updateInstall') }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Browser } from '@wailsio/runtime'
import { useUpdateCheck } from '../composables/useUpdateCheck'
import { useI18n, locale } from '../i18n'
import { renderMarkdownHtml, sanitizeRenderedHtml } from '../utils/markdown'

const { t } = useI18n()
const updateCheck = useUpdateCheck()

// Cannot dismiss the dialog while the binary is being replaced.
const locked = computed(() =>
  updateCheck.updatePhase === 'applying' || updateCheck.updatePhase === 'restarting'
)

// Release notes have a fixed layout: English section first, then the Chinese
// one under the "### 更新内容" heading. zh locales show the Chinese section,
// other locales the English part; if the marker is missing (unexpected
// format), fall back to the full body.
const changelogHtml = computed(() => {
  const body = updateCheck.updateInfo?.changelog || ''
  if (!body) return ''
  const zhIdx = body.search(/^#{2,3}\s+更新内容\s*$/m)
  if (zhIdx < 0) {
    return sanitizeRenderedHtml(renderMarkdownHtml(body))
  }
  const isZh = locale.value === 'zh-CN' || locale.value === 'zh-TW'
  if (!isZh) {
    return sanitizeRenderedHtml(renderMarkdownHtml(body.slice(0, zhIdx)))
  }
  // Keep the leading version heading (e.g. "## v1.9.2") above the Chinese section.
  const header = body.match(/^#{1,6}\s+[^\n]*\n?/)
  return sanitizeRenderedHtml(renderMarkdownHtml((header ? header[0] : '') + body.slice(zhIdx)))
})

const releaseUrl = computed(() => updateCheck.updateInfo?.releaseUrl || '')

function openRelease() {
  if (releaseUrl.value) Browser.OpenURL(releaseUrl.value)
}

function fmtSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  const units = ['KB', 'MB', 'GB']
  let v = bytes
  let i = -1
  do {
    v /= 1024
    i++
  } while (v >= 1024 && i < units.length - 1)
  return `${v.toFixed(1)} ${units[i]}`
}
</script>

<style scoped>
.update-dialog-version {
  font-size: 0.875rem;
  font-weight: 600;
  font-family: var(--font-ui);
  margin-bottom: 0.625rem;
}
.update-dialog-hint {
  font-size: 0.8125rem;
  color: var(--text-muted, #8a8a8a);
  margin-bottom: 0.625rem;
}
.update-dialog-changelog {
  max-height: 20rem;
  overflow-y: auto;
  background: var(--bg-overlay);
  border: 1px solid var(--border-subtle);
  border-radius: 0.375rem;
  padding: 0.625rem 0.75rem;
  margin-bottom: 0.75rem;
  font-size: 0.7813rem;
  line-height: 1.6;
  font-family: var(--font-ui);
  color: var(--text-primary);
}
.update-dialog-changelog :deep(h2) {
  font-size: 0.875rem;
  margin: 0 0 0.5rem;
}
.update-dialog-changelog :deep(h3) {
  font-size: 0.8125rem;
  margin: 0.75rem 0 0.375rem;
}
.update-dialog-changelog :deep(p) {
  margin: 0.375rem 0;
}
.update-dialog-changelog :deep(ul) {
  margin: 0.375rem 0;
  padding-left: 1.125rem;
}
.update-dialog-changelog :deep(li) {
  margin: 0.1875rem 0;
}
.update-dialog-changelog :deep(a) {
  color: var(--accent);
  text-decoration: none;
}
.update-dialog-changelog :deep(a:hover) {
  text-decoration: underline;
}
.update-dialog-changelog :deep(code) {
  background: var(--bg-overlay);
  border: 1px solid var(--border-subtle);
  border-radius: 0.1875rem;
  padding: 0 0.25rem;
  font-family: var(--font-mono);
  font-size: 0.7188rem;
}
.update-dialog-changelog :deep(hr) {
  border: none;
  border-top: 1px solid var(--border-subtle);
  margin: 0.625rem 0;
}
.update-dialog-error {
  color: #f56c6c;
  font-size: 0.8125rem;
  margin-bottom: 0.625rem;
  word-break: break-word;
}
.update-dialog-progress-label {
  font-size: 0.8125rem;
  margin-top: 0.5rem;
  color: var(--text-muted, #8a8a8a);
}
.update-dialog-progress-size {
  font-family: var(--font-mono);
}
</style>
