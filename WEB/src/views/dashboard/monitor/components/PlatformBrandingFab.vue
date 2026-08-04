<template>
  <div class="branding-fab-anchor">
    <!-- 隐藏后：透明热区，不占标题布局、无可见痕迹 -->
    <div
      v-show="fabHidden"
      class="branding-fab-hit-area"
      title="平台标识设置"
      @mouseenter="handleEdgeEnter"
      @mouseleave="handleEdgeLeave"
    />

    <!-- 悬浮球：始终挂载，通过 CSS 过渡显隐 -->
    <div
      class="branding-fab-wrap"
      :class="{ visible: ballVisible }"
      @mouseenter="handleFabEnter"
      @mouseleave="handleFabLeave"
    >
      <button type="button" class="branding-fab-ball" title="平台标识设置" @click="panelOpen = true">
        <Icon icon="ant-design:setting-outlined" :size="20" />
      </button>
    </div>
  </div>

  <Teleport to="body">
    <!-- 设置面板 -->
    <Transition name="branding-panel-fade">
      <div v-if="panelOpen" class="branding-panel-backdrop">
        <div class="branding-panel">
          <div class="panel-header">
            <div class="panel-title">
              <Icon icon="ant-design:skin-outlined" :size="18" />
              <span>平台标识设置</span>
            </div>
            <button type="button" class="panel-close-btn" @click="handleClosePanel">
              <Icon icon="ant-design:close-outlined" :size="16" />
            </button>
          </div>

          <div class="panel-body">
            <section class="form-section">
              <h4 class="section-label">管理后台</h4>
              <BrandingField label="平台名称" hint="侧边栏、浏览器标题等">
                <input
                  v-model="form.platformName"
                  type="text"
                  class="field-input"
                  placeholder="请输入平台名称"
                />
              </BrandingField>
              <BrandingImageField
                label="平台 Logo"
                :preview="form.platformLogo"
                @upload="(image) => updateImage('platformLogo', image)"
              />
            </section>

            <section class="form-section">
              <h4 class="section-label">监控大屏</h4>
              <BrandingField label="大屏标题">
                <input
                  v-model="form.dashboardTitle"
                  type="text"
                  class="field-input"
                  placeholder="请输入大屏标题"
                />
              </BrandingField>
            </section>

            <section class="form-section">
              <h4 class="section-label">登录界面</h4>
              <BrandingField label="登录页名称">
                <input
                  v-model="form.loginName"
                  type="text"
                  class="field-input"
                  placeholder="登录页左侧显示名称"
                />
              </BrandingField>
              <BrandingImageField
                label="登录页 Logo"
                :preview="form.loginLogo"
                @upload="(image) => updateImage('loginLogo', image)"
              />
              <BrandingField label="登录表单标题" hint="留空则使用系统默认文案">
                <input
                  v-model="form.loginFormTitle"
                  type="text"
                  class="field-input"
                  placeholder="如：账号登录"
                />
              </BrandingField>
              <BrandingImageField
                label="浅色背景图"
                :preview="form.loginBgLight"
                accept-hint="建议 1920×1080"
                @upload="(image) => updateImage('loginBgLight', image)"
              />
              <BrandingImageField
                label="深色背景图"
                :preview="form.loginBgDark"
                accept-hint="建议 1920×1080"
                @upload="(image) => updateImage('loginBgDark', image)"
              />
            </section>
          </div>

          <div class="panel-footer">
            <button
              type="button"
              class="panel-btn primary save-btn"
              :disabled="!hasUnsavedChanges || saving"
              @click="handleSave"
            >
              <Icon icon="ant-design:save-outlined" :size="14" />
              {{ saving ? '保存中…' : '保存' }}
            </button>
            <div class="panel-footer-right">
              <button type="button" class="panel-btn" @click="handleHideFab">
                <Icon icon="ant-design:vertical-left-outlined" :size="14" />
                暂时隐藏
              </button>
              <button v-if="fabHidden" type="button" class="panel-btn" @click="handlePinFab">
                <Icon icon="ant-design:pushpin-outlined" :size="14" />
                固定显示悬浮球
              </button>
              <button type="button" class="panel-btn danger" @click="handleReset">
                <Icon icon="ant-design:undo-outlined" :size="14" />
                重置为初始设置
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script lang="ts" setup>
import { computed, defineComponent, h, reactive, ref, watch } from 'vue'
import type { PlatformBrandingImageVO } from '@/api/infra/platformBranding'
import { uploadPlatformBrandingImage } from '@/api/infra/platformBranding'
import { Icon } from '@/components/Icon'
import { useMessage } from '@/hooks/web/useMessage'
import { usePlatformBranding } from '@/hooks/web/usePlatformBranding'
import type { PlatformBrandingConfig } from '@/utils/platformBrandingStorage'
import { Modal } from 'ant-design-vue'

defineOptions({ name: 'PlatformBrandingFab' })

const MAX_IMAGE_SIZE = 3 * 1024 * 1024
const MAX_STORED_IMAGE_SIZE = 600 * 1024
const MAX_IMAGE_WIDTH = 1920
const MAX_IMAGE_HEIGHT = 1080
const IMAGE_QUALITIES = [0.86, 0.72, 0.6, 0.5]

const { createMessage } = useMessage()
const { config, fabHidden, updateConfig, resetConfig, setFabHidden } = usePlatformBranding()

const panelOpen = ref(false)
const fabPeek = ref(false)
const saving = ref(false)
let peekTimer: ReturnType<typeof setTimeout> | null = null

const PEEK_LEAVE_DELAY = 380

const ballVisible = computed(() => !fabHidden.value || fabPeek.value || panelOpen.value)

const form = reactive<PlatformBrandingConfig>({ ...config.value })

const hasUnsavedChanges = computed(() => {
  const saved = config.value
  return (Object.keys(form) as Array<keyof PlatformBrandingConfig>).some(
    (key) => form[key] !== saved[key],
  )
})

function syncFormFromConfig() {
  Object.assign(form, config.value)
}

watch(
  config,
  () => {
    if (!panelOpen.value) {
      syncFormFromConfig()
    }
  },
  { deep: true },
)

watch(panelOpen, (open) => {
  if (open) {
    syncFormFromConfig()
    clearPeekTimer()
    if (fabHidden.value) {
      fabPeek.value = true
    }
    return
  }
  syncFormFromConfig()
  if (fabHidden.value) {
    schedulePeekHide()
  }
})

async function handleSave() {
  if (saving.value) return
  saving.value = true
  try {
    await updateConfig({ ...form })
    syncFormFromConfig()
    createMessage.success('操作成功')
  }
  catch (error) {
    console.error(error)
    createMessage.error(getErrorMessage(error, '平台配置保存失败'))
  }
  finally {
    saving.value = false
  }
}

function handleClosePanel() {
  syncFormFromConfig()
  panelOpen.value = false
}

type BrandingImageFieldKey = 'platformLogo' | 'loginLogo' | 'loginBgLight' | 'loginBgDark'
type BrandingImageFileIdKey = 'platformLogoFileId' | 'loginLogoFileId' | 'loginBgLightFileId' | 'loginBgDarkFileId'

const imageFileIdFields: Record<BrandingImageFieldKey, BrandingImageFileIdKey> = {
  platformLogo: 'platformLogoFileId',
  loginLogo: 'loginLogoFileId',
  loginBgLight: 'loginBgLightFileId',
  loginBgDark: 'loginBgDarkFileId',
}

function updateImage(field: BrandingImageFieldKey, image: PlatformBrandingImageVO) {
  form[field] = image.url
  form[imageFileIdFields[field]] = image.fileId
}

function clearPeekTimer() {
  if (peekTimer) {
    clearTimeout(peekTimer)
    peekTimer = null
  }
}

function schedulePeekHide() {
  if (panelOpen.value) return
  clearPeekTimer()
  peekTimer = setTimeout(() => {
    fabPeek.value = false
  }, PEEK_LEAVE_DELAY)
}

function handleEdgeEnter() {
  clearPeekTimer()
  fabPeek.value = true
}

function handleEdgeLeave() {
  if (fabHidden.value) {
    schedulePeekHide()
  }
}

function handleFabEnter() {
  clearPeekTimer()
  if (fabHidden.value) {
    fabPeek.value = true
  }
}

function handleFabLeave() {
  if (fabHidden.value) {
    schedulePeekHide()
  }
}

function handleHideFab() {
  syncFormFromConfig()
  panelOpen.value = false
  fabPeek.value = false
  setFabHidden(true)
  createMessage.success('已隐藏，鼠标移至标题左侧空白处可再次唤出')
}

function handlePinFab() {
  setFabHidden(false)
  fabPeek.value = false
  createMessage.success('悬浮球已固定显示')
}

function handleReset() {
  Modal.confirm({
    title: '重置平台标识',
    content: '确定恢复为初始设置吗？平台名称、Logo、登录背景及大屏标题将全部还原。',
    okText: '确定重置',
    cancelText: '取消',
    onOk: async () => {
      try {
        await resetConfig()
        syncFormFromConfig()
        createMessage.success('已恢复并持久化为初始设置')
      }
      catch (error) {
        console.error(error)
        createMessage.error(getErrorMessage(error, '平台配置重置失败'))
        throw error
      }
    },
  })
}

function getErrorMessage(error: unknown, fallback: string): string {
  return error instanceof Error && error.message ? error.message : fallback
}

/** 图片上传表单项 */
const BrandingImageField = defineComponent({
  name: 'BrandingImageField',
  props: {
    label: { type: String, required: true },
    preview: { type: String, default: '' },
    acceptHint: { type: String, default: 'PNG / JPG / SVG' },
  },
  emits: ['upload'],
  setup(props, { emit }) {
    const inputRef = ref<HTMLInputElement | null>(null)
    const uploading = ref(false)

    async function onFileChange(e: Event) {
      const file = (e.target as HTMLInputElement).files?.[0]
      if (!file) return
      if (!file.type.startsWith('image/')) {
        createMessage.error('请选择图片文件')
        return
      }
      if (file.size > MAX_IMAGE_SIZE) {
        createMessage.error('图片大小不能超过 3MB')
        return
      }
      try {
        uploading.value = true
        const { blob, compressed } = await optimizeImage(file)
        const filename = compressed ? `${file.name.replace(/\.[^.]+$/, '') || 'branding'}.webp` : file.name
        const uploaded = await uploadPlatformBrandingImage(blob, filename)
        emit('upload', uploaded)
        if (compressed) {
          createMessage.info('图片已自动压缩后上传')
        }
      }
      catch (error) {
        console.error(error)
        createMessage.error(getErrorMessage(error, '图片上传失败，请稍后重试'))
      }
      finally {
        uploading.value = false
      }
      if (inputRef.value) {
        inputRef.value.value = ''
      }
    }

    return () =>
      h('div', { class: 'branding-image-field' }, [
        h('div', { class: 'field-label-row' }, [
          h('span', { class: 'field-label' }, props.label),
          h('span', { class: 'field-hint' }, props.acceptHint),
        ]),
        h('div', { class: 'image-upload-row' }, [
          h('div', { class: 'image-preview' }, [
            props.preview
              ? h('img', { src: props.preview, alt: props.label })
              : h('span', { class: 'preview-empty' }, '暂无'),
          ]),
          h('div', { class: 'upload-actions' }, [
            h(
              'button',
              {
                type: 'button',
                class: 'upload-btn',
                disabled: uploading.value,
                onClick: () => inputRef.value?.click(),
              },
              uploading.value ? '上传中…' : '选择图片',
            ),
            h('input', {
              ref: inputRef,
              type: 'file',
              accept: 'image/*',
              style: 'display:none',
              onChange: onFileChange,
            }),
          ]),
        ]),
      ])
  },
})

const BrandingField = defineComponent({
  name: 'BrandingField',
  props: {
    label: { type: String, required: true },
    hint: { type: String, default: '' },
  },
  setup(props, { slots }) {
    return () =>
      h('div', { class: 'branding-field' }, [
        h('div', { class: 'field-label-row' }, [
          h('span', { class: 'field-label' }, props.label),
          props.hint ? h('span', { class: 'field-hint' }, props.hint) : null,
        ]),
        slots.default?.(),
      ])
  },
})

/** 压缩大尺寸位图，降低平台图片的网络传输与存储开销 */
async function optimizeImage(file: File): Promise<{ blob: Blob; compressed: boolean }> {
  if (file.type === 'image/svg+xml') {
    if (file.size > MAX_STORED_IMAGE_SIZE) {
      throw new Error('SVG 图片超过可持久化大小')
    }
    return { blob: file, compressed: false }
  }

  const image = await loadImage(file)
  const initialScale = Math.min(1, MAX_IMAGE_WIDTH / image.naturalWidth, MAX_IMAGE_HEIGHT / image.naturalHeight)
  if (file.size <= MAX_STORED_IMAGE_SIZE && initialScale === 1) {
    return { blob: file, compressed: false }
  }

  let width = Math.max(1, Math.round(image.naturalWidth * initialScale))
  let height = Math.max(1, Math.round(image.naturalHeight * initialScale))
  let candidate: Blob | null = null

  for (let resizeAttempt = 0; resizeAttempt < 4; resizeAttempt += 1) {
    const canvas = document.createElement('canvas')
    canvas.width = width
    canvas.height = height
    const context = canvas.getContext('2d')
    if (!context) {
      throw new Error('浏览器不支持图片压缩')
    }
    context.drawImage(image, 0, 0, width, height)

    for (const quality of IMAGE_QUALITIES) {
      candidate = await canvasToBlob(canvas, quality)
      if (candidate.size <= MAX_STORED_IMAGE_SIZE) {
        return { blob: candidate, compressed: true }
      }
    }

    width = Math.max(1, Math.round(width * 0.82))
    height = Math.max(1, Math.round(height * 0.82))
  }

  throw new Error(`图片压缩后仍超过 ${MAX_STORED_IMAGE_SIZE} 字节`)
}

function loadImage(file: File): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const objectUrl = URL.createObjectURL(file)
    const image = new Image()
    image.onload = () => {
      URL.revokeObjectURL(objectUrl)
      resolve(image)
    }
    image.onerror = () => {
      URL.revokeObjectURL(objectUrl)
      reject(new Error('图片读取失败'))
    }
    image.src = objectUrl
  })
}

function canvasToBlob(canvas: HTMLCanvasElement, quality: number): Promise<Blob> {
  return new Promise((resolve, reject) => {
    canvas.toBlob((blob) => {
      if (blob) {
        resolve(blob)
        return
      }
      reject(new Error('图片压缩失败'))
    }, 'image/webp', quality)
  })
}
</script>

<style lang="less" scoped>
.branding-fab-anchor {
  position: absolute;
  right: calc(100% + 16px);
  top: 50%;
  transform: translateY(-50%);
  width: 44px;
  height: 44px;
  z-index: 2;
  pointer-events: none;
}

.branding-fab-hit-area {
  position: absolute;
  inset: 0;
  pointer-events: auto;
  cursor: pointer;
  background: transparent;
  z-index: 1;
}

.branding-fab-wrap {
  position: absolute;
  inset: 0;
  z-index: 2;
  opacity: 0;
  visibility: hidden;
  transform: translateX(-16px) scale(0.78);
  pointer-events: none;
  transition:
    opacity 0.34s cubic-bezier(0.22, 1, 0.36, 1),
    transform 0.34s cubic-bezier(0.22, 1, 0.36, 1),
    visibility 0.34s cubic-bezier(0.22, 1, 0.36, 1);

  &.visible {
    opacity: 1;
    visibility: visible;
    transform: translateX(0) scale(1);
    pointer-events: auto;
  }
}

.branding-fab-ball {
  width: 44px;
  height: 44px;
  flex-shrink: 0;
  border-radius: 50%;
  border: 1px solid rgba(120, 190, 255, 0.65);
  background: radial-gradient(circle at 30% 25%, rgba(120, 190, 255, 0.98), rgba(48, 82, 174, 0.94) 55%, rgba(15, 34, 73, 0.98));
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow:
    0 0 22px rgba(52, 134, 218, 0.65),
    0 4px 14px rgba(0, 0, 0, 0.35);
  transition: transform 0.25s ease, box-shadow 0.25s ease;
  animation: fab-glow 2.4s ease-in-out infinite;
}

.branding-fab-wrap.visible .branding-fab-ball:hover {
  transform: scale(1.1);
  box-shadow:
    0 0 32px rgba(52, 134, 218, 0.85),
    0 6px 18px rgba(0, 0, 0, 0.4);
  animation: none;
}

.branding-fab-wrap.visible .branding-fab-ball:active {
  transform: scale(0.96);
}

@keyframes fab-glow {
  0%,
  100% {
    box-shadow:
      0 0 18px rgba(52, 134, 218, 0.55),
      0 4px 14px rgba(0, 0, 0, 0.35);
  }
  50% {
    box-shadow:
      0 0 28px rgba(52, 134, 218, 0.8),
      0 4px 16px rgba(0, 0, 0, 0.35);
  }
}

/* 须低于大屏统一弹层 z-index（10050），否则 Modal.confirm 会被挡住 */
.branding-panel-backdrop {
  position: fixed;
  inset: 0;
  z-index: 10045;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.branding-panel {
  width: min(680px, 100%);
  max-height: min(86vh, 720px);
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, rgba(8, 20, 45, 0.98), rgba(12, 28, 58, 0.96));
  border: 1px solid rgba(52, 134, 218, 0.35);
  border-radius: 12px;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(12px);
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(52, 134, 218, 0.2);
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #fff;
}

.panel-close-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.04);
  color: rgba(255, 255, 255, 0.65);
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    color: #fff;
    border-color: rgba(255, 255, 255, 0.25);
  }
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px 20px 8px;
}

.form-section {
  margin-bottom: 16px;

  .section-label {
    margin: 0 0 10px;
    font-size: 13px;
    font-weight: 600;
    color: rgba(120, 190, 255, 0.9);
    letter-spacing: 0.04em;
  }
}

:deep(.branding-field),
:deep(.branding-image-field) {
  margin-bottom: 12px;
}

:deep(.field-label-row) {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 6px;
}

:deep(.field-label) {
  font-size: 13px;
  color: rgba(220, 235, 255, 0.92);
}

:deep(.field-hint) {
  font-size: 11px;
  color: rgba(200, 220, 255, 0.45);
}

:deep(.field-input) {
  width: 100%;
  height: 36px;
  padding: 0 12px;
  border-radius: 6px;
  border: 1px solid rgba(52, 134, 218, 0.35);
  background: rgba(255, 255, 255, 0.06);
  color: #fff;
  font-size: 13px;
  outline: none;
  transition: border-color 0.2s;

  &:focus {
    border-color: rgba(52, 134, 218, 0.75);
  }

  &::placeholder {
    color: rgba(200, 220, 255, 0.35);
  }
}

:deep(.image-upload-row) {
  display: flex;
  align-items: center;
  gap: 12px;
}

:deep(.image-preview) {
  width: 72px;
  height: 48px;
  border-radius: 6px;
  border: 1px solid rgba(52, 134, 218, 0.25);
  background: rgba(0, 0, 0, 0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;

  img {
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
  }

  .preview-empty {
    font-size: 11px;
    color: rgba(200, 220, 255, 0.35);
  }
}

:deep(.upload-btn) {
  height: 32px;
  padding: 0 14px;
  border-radius: 6px;
  border: 1px solid rgba(52, 134, 218, 0.45);
  background: rgba(52, 134, 218, 0.18);
  color: #d6ebff;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    background: rgba(52, 134, 218, 0.32);
    color: #fff;
  }
}

.panel-footer {
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 20px 16px;
  border-top: 1px solid rgba(52, 134, 218, 0.2);
}

.panel-footer-right {
  display: flex;
  flex-wrap: nowrap;
  flex-shrink: 0;
  justify-content: flex-end;
  gap: 8px;
}

.panel-btn {
  display: inline-flex;
  align-items: center;
  flex-shrink: 0;
  gap: 6px;
  height: 34px;
  padding: 0 14px;
  border-radius: 6px;
  border: 1px solid rgba(52, 134, 218, 0.35);
  background: rgba(255, 255, 255, 0.05);
  color: rgba(220, 235, 255, 0.9);
  font-size: 13px;
  white-space: nowrap;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    background: rgba(52, 134, 218, 0.2);
    color: #fff;
  }

  &.primary {
    border-color: rgba(52, 134, 218, 0.55);
    background: rgba(52, 134, 218, 0.25);
  }

  &.save-btn {
    min-width: 96px;
    justify-content: center;
    font-weight: 600;
  }

  &:disabled {
    opacity: 0.45;
    cursor: not-allowed;
  }

  &.danger {
    border-color: rgba(255, 100, 100, 0.4);
    color: #ffb4b4;

    &:hover {
      background: rgba(255, 80, 80, 0.18);
      color: #ffd0d0;
    }
  }
}

.branding-panel-fade-enter-active,
.branding-panel-fade-leave-active {
  transition: opacity 0.25s;
}

.branding-panel-fade-enter-from,
.branding-panel-fade-leave-to {
  opacity: 0;
}
</style>
