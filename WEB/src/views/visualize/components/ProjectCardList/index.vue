<template>
  <div class="project-card-list-wrapper">
    <div class="search-bar">
      <BasicForm @register="registerForm" @reset="handleSubmit" />
    </div>
    <div class="list-panel">
      <Spin :spinning="state.loading">
        <List
          :grid="{ gutter: 16, xs: 1, sm: 2, md: 3, lg: 4, xl: 5, xxl: 5 }"
          :data-source="data"
          :pagination="paginationProp"
        >
          <template #header>
            <div class="list-header">
              <span class="list-title">可视化项目</span>
              <div class="list-actions">
                <slot name="header"></slot>
              </div>
            </div>
          </template>
          <template #renderItem="{ item }">
            <ListItem class="project-list-item">
              <div
                class="project-card"
                :class="isScadaProject(item.projectType) ? 'project-card--scada' : 'project-card--dashboard'"
                @mouseenter="hoverId = item.id"
                @mouseleave="onCardMouseLeave(item.id)"
              >
                <div class="project-card-cover" @click="emit('view', item)">
                  <div class="project-card-cover-inner">
                    <div
                      v-if="item.indexImage && !brokenCovers[item.id]"
                      class="project-card-image"
                      role="img"
                      :aria-label="item.projectName || '封面'"
                      :style="{ backgroundImage: `url('${item.indexImage}')` }"
                    />
                    <div v-else class="cover-placeholder">
                      <span class="cover-placeholder-label">{{
                        isScadaProject(item.projectType) ? 'FUXA' : 'VISUALIZE'
                      }}</span>
                    </div>
                  </div>
                  <span class="project-type-ribbon" :class="isScadaProject(item.projectType) ? 'is-scada' : 'is-dashboard'">
                    {{ isScadaProject(item.projectType) ? '组态' : '大屏' }}
                  </span>
                  <div
                    v-show="isOverlayVisible(item.id)"
                    class="project-card-overlay"
                    @click="emit('view', item)"
                  >
                    <div class="overlay-actions" @click.stop>
                      <Tooltip v-if="!isFuxaDemoProject(item)" title="打开编辑器">
                        <button class="overlay-btn" @click="emit('open-editor', item)">
                          <FundProjectionScreenOutlined />
                        </button>
                      </Tooltip>
                      <Tooltip title="预览">
                        <button class="overlay-btn" @click="emit('preview', item)">
                          <EyeOutlined />
                        </button>
                      </Tooltip>
                      <Tooltip title="编辑信息">
                        <button class="overlay-btn" @click="emit('edit', item)">
                          <EditOutlined />
                        </button>
                      </Tooltip>
                      <Tooltip :title="Number(item.state) === 1 ? '取消发布' : '发布'">
                        <button class="overlay-btn" @click="emit('publish', item)">
                          <CheckCircleOutlined v-if="Number(item.state) !== 1" />
                          <StopOutlined v-else />
                        </button>
                      </Tooltip>
                      <Popconfirm
                        title="是否确认删除？"
                        placement="top"
                        :get-popup-container="getPopupContainer"
                        @open-change="(open) => onDeleteConfirmOpenChange(item.id, open)"
                        @confirm="emit('delete', item)"
                      >
                        <button
                          type="button"
                          class="overlay-btn overlay-btn--danger"
                          title="删除"
                          aria-label="删除"
                        >
                          <DeleteOutlined />
                        </button>
                      </Popconfirm>
                    </div>
                  </div>
                </div>

                <div class="project-card-body">
                  <h3
                    class="project-card-title"
                    :title="item.projectName"
                    @click="emit('view', item)"
                  >
                    {{ item.projectName }}
                  </h3>
                  <p class="project-card-meta">
                    <span
                      class="project-type-dot"
                      :class="isScadaProject(item.projectType) ? 'is-scada' : 'is-dashboard'"
                    ></span>
                    {{ getMetaText(item) }}
                  </p>
                  <p v-if="getRemarkText(item)" class="project-card-desc" :title="getRemarkText(item)">
                    {{ getRemarkText(item) }}
                  </p>
                </div>
              </div>
            </ListItem>
          </template>
        </List>
      </Spin>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { onMounted, reactive, ref } from 'vue'
import { List, Popconfirm, Spin, Tooltip } from 'ant-design-vue'
import {
  CheckCircleOutlined,
  DeleteOutlined,
  EditOutlined,
  EyeOutlined,
  FundProjectionScreenOutlined,
  StopOutlined,
} from '@ant-design/icons-vue'
import { BasicForm, useForm } from '@/components/Form'
import { propTypes } from '@/utils/propTypes'
import { isFunction } from '@/utils/is'
import { getProjectTypeLabel, isFuxaDemoProject, isScadaProject } from '@/utils/visualizeEditor'

defineOptions({ name: 'VisualizeProjectCardList' })

const ListItem = List.Item

const props = defineProps({
  params: propTypes.object.def({}),
  api: propTypes.func,
})

const emit = defineEmits(['getMethod', 'delete', 'edit', 'view', 'open-editor', 'preview', 'publish'])

const data = ref<any[]>([])
const hoverId = ref<number | null>(null)
/** 删除确认气泡打开时锁定对应卡片遮罩，避免移入弹层触发 mouseleave 导致确认失效 */
const deleteConfirmId = ref<number | string | null>(null)
const brokenCovers = reactive<Record<string | number, boolean>>({})
const state = reactive({ loading: true })
const page = ref(1)
const pageSize = ref(12)
const total = ref(0)

function isOverlayVisible(id: number | string) {
  return hoverId.value === id || deleteConfirmId.value === id
}

function onCardMouseLeave(id: number | string) {
  if (deleteConfirmId.value === id) return
  if (hoverId.value === id) hoverId.value = null
}

function onDeleteConfirmOpenChange(id: number | string, open: boolean) {
  deleteConfirmId.value = open ? id : null
}

function getPopupContainer() {
  return document.body
}

const [registerForm, { validate }] = useForm({
  schemas: [
    {
      field: 'projectName',
      label: '项目名称',
      component: 'Input',
      componentProps: { placeholder: '请输入项目名称' },
    },
    {
      field: 'projectType',
      label: '项目类型',
      component: 'Select',
      componentProps: {
        allowClear: true,
        options: [
          { label: '大屏', value: 'dashboard' },
          { label: '组态', value: 'scada' },
        ],
      },
    },
    {
      field: 'state',
      label: '发布状态',
      component: 'Select',
      componentProps: {
        allowClear: true,
        options: [
          { label: '未发布', value: -1 },
          { label: '已发布', value: 1 },
        ],
      },
    },
  ],
  labelWidth: 80,
  baseColProps: { span: 6 },
  actionColOptions: { span: 6 },
  autoSubmitOnEnter: true,
  submitFunc: handleSubmit,
})

onMounted(() => {
  fetch()
  emit('getMethod', reload)
})

async function handleSubmit() {
  const formData = await validate()
  page.value = 1
  await fetch(formData)
}

async function reload(opts?: { resetPage?: boolean }) {
  if (opts?.resetPage) page.value = 1
  state.loading = true
  await fetch()
}

async function fetch(p: Recordable = {}) {
  const { api, params } = props
  if (!api || !isFunction(api)) return
  try {
    state.loading = true
    const res = await api({ ...params, pageNo: page.value, pageSize: pageSize.value, ...p })
    data.value = res?.list ?? res?.data ?? []
    total.value = res?.total ?? 0
    data.value.forEach(prefetchCover)
  } catch (error) {
    console.error(error)
    data.value = []
    total.value = 0
  } finally {
    state.loading = false
  }
}

const paginationProp = ref({
  showSizeChanger: false,
  showQuickJumper: true,
  pageSize,
  current: page,
  total,
  showTotal: (t: number) => `总 ${t} 条`,
  onChange: pageChange,
  onShowSizeChange: pageSizeChange,
})

function pageChange(p: number, pz: number) {
  page.value = p
  pageSize.value = pz
  fetch()
}

function pageSizeChange(_current: number, size: number) {
  pageSize.value = size
  page.value = 1
  fetch()
}

function getMetaText(item: any): string {
  return Number(item.state) === 1 ? '已发布' : '未发布'
}

function getRemarkText(item: any): string {
  const desc = String(item?.remarks || '').trim()
  return desc
}

/** @deprecated 保留给列表视图等复用 */
function getTagsText(item: any): string {
  const type = getProjectTypeLabel(item.projectType)
  const parts = [`${type} · ${getMetaText(item)}`]
  const remark = getRemarkText(item)
  if (remark) parts.push(remark)
  else parts.push(`ID: ${item.id}`)
  return parts.join(' · ')
}

function prefetchCover(item: any) {
  const url = item?.indexImage
  if (!url || !item?.id) return
  const img = new Image()
  img.onerror = () => {
    brokenCovers[item.id] = true
  }
  img.src = url
}
</script>

<style lang="less" scoped>
.project-card-list-wrapper {
  background: #fff;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.search-bar {
  padding: 12px 16px 0;
  margin-bottom: 8px;
  background: #fff;
  flex-shrink: 0;
}

.list-panel {
  background: #fff;
  padding: 0 8px 12px;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;

  :deep(.ant-list-header) {
    border: 0;
    padding: 4px 12px 12px;
    background: transparent;
  }

  :deep(.ant-list) {
    padding: 0 8px;
  }

  :deep(.ant-row) {
    display: flex;
    flex-wrap: wrap;
    row-gap: 14px;
  }

  :deep(.ant-col) {
    display: flex;
  }

  :deep(.ant-list-item) {
    margin-bottom: 0;
    padding: 0 !important;
    border: none;
    width: 100%;
    height: auto;
    display: flex;
  }

  :deep(.ant-spin-nested-loading),
  :deep(.ant-spin-container) {
    background: transparent;
    height: auto !important;
  }

  :deep(.ant-list-pagination) {
    margin-top: 16px;
    text-align: center;
  }
}

.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.list-title {
  padding-left: 4px;
  font-size: 16px;
  font-weight: 500;
  line-height: 24px;
  color: #181818;
}

.list-actions {
  display: flex;
  gap: 8px;
}

.project-list-item {
  width: 100%;
}

@cover-height: 148px;
@type-dashboard: #266cfb;
@type-scada: #1a8f5c;

.project-card {
  position: relative;
  display: flex;
  flex-direction: column;
  width: 100%;
  height: auto;
  background: #fff;
  border-radius: 6px;
  box-shadow: 0 1px 4px rgba(24, 24, 24, 0.08);
  overflow: hidden;
  transition: box-shadow 0.25s ease, transform 0.25s ease;
  cursor: default;
  border: 1px solid #eef0f3;

  &::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 3px;
    z-index: 5;
  }

  &--dashboard::before {
    background: @type-dashboard;
  }

  &--scada::before {
    background: @type-scada;
  }

  &:hover {
    box-shadow: 0 3px 12px rgba(0, 0, 0, 0.1);
    transform: translateY(-1px);
  }
}

.project-card-cover {
  position: relative;
  width: 100%;
  height: @cover-height;
  flex-shrink: 0;
  overflow: hidden;
  cursor: pointer;
  background: #0b1220;
}

.project-card-cover-inner {
  position: absolute;
  inset: 0;
  overflow: hidden;
}

.project-card-image {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  background-color: #0b1220;
  background-repeat: no-repeat;
  background-position: center center;
  background-size: cover;
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(145deg, #eef3ff 0%, #dce7ff 45%, #c5d6ff 100%);
}

.cover-placeholder-label {
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 2px;
  color: #266cfb;
  opacity: 0.85;
}

.project-type-ribbon {
  position: absolute;
  left: 10px;
  top: 10px;
  z-index: 4;
  display: inline-flex;
  align-items: center;
  height: 22px;
  padding: 0 8px;
  border-radius: 3px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.4px;
  line-height: 1;
  color: #fff;
  pointer-events: none;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.2);

  &.is-dashboard {
    background: @type-dashboard;
  }

  &.is-scada {
    background: @type-scada;
  }
}

.project-card-overlay {
  position: absolute;
  inset: 0;
  z-index: 3;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.45);
}

.overlay-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: center;
  padding: 0 8px;
}

.overlay-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.92);
  color: #266cfb;
  font-size: 15px;
  cursor: pointer;
  transition: background 0.2s, color 0.2s, transform 0.2s;

  &:hover {
    background: #fff;
    transform: scale(1.08);
  }

  &--danger {
    color: #f5222d;

    &:hover {
      background: #fff1f0;
    }
  }
}

.project-card-body {
  flex-shrink: 0;
  padding: 10px 12px 12px;
  box-sizing: border-box;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.project-card-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  line-height: 1.35;
  color: #181818;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: pointer;
  flex-shrink: 0;

  &:hover {
    color: #266cfb;
  }
}

.project-card-meta {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  line-height: 1.35;
  color: #8c8c8c;
  flex-shrink: 0;
}

.project-type-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;

  &.is-dashboard {
    background: @type-dashboard;
  }

  &.is-scada {
    background: @type-scada;
  }
}

.project-card-desc {
  margin: 0;
  font-size: 12px;
  line-height: 1.35;
  color: #999;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
