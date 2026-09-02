<template>
  <div class="model-card-list-wrapper">
    <div class="search-bar">
      <BasicForm @register="registerForm" @reset="handleSubmit"/>
    </div>
    <div class="list-panel">
      <Spin :spinning="state.loading">
        <List
          :grid="{ gutter: 18, xs: 2, sm: 3, md: 4, lg: 5, xl: 6, xxl: 6 }"
          :data-source="data"
          :pagination="paginationProp"
        >
          <template #header>
            <div class="list-header">
              <span class="list-title">模型列表</span>
              <div class="list-actions">
                <slot name="header"></slot>
              </div>
            </div>
          </template>
          <template #renderItem="{ item }">
            <ListItem class="model-list-item">
              <div class="model-card" @mouseenter="hoverId = item.id" @mouseleave="hoverId = null">
                <!-- 封面图区域 -->
                <div class="model-card-cover" @click="handleView(item)">
                  <div class="model-card-cover-inner">
                    <img
                      :src="getModelImage(item)"
                      alt="模型图片"
                      class="model-card-image"
                      @error="onImageError"
                    />
                  </div>
                  <button
                    v-if="(item.family_size ?? 1) > 1"
                    type="button"
                    class="model-card-version-ribbon"
                    title="该模型含多个版本，点击进入版本管理"
                    @click.stop="handleFamily(item)"
                  >
                    {{ getFamilySummaryText(item) }}
                  </button>
                  <div
                    v-show="hoverId === item.id"
                    class="model-card-overlay"
                    @click="handleView(item)"
                  >
                    <div class="overlay-actions" @click.stop>
                      <Tooltip title="查看详情">
                        <button class="overlay-btn" @click="handleView(item)">
                          <EyeOutlined />
                        </button>
                      </Tooltip>
                      <Tooltip title="编辑模型">
                        <button class="overlay-btn" @click="handleEdit(item)">
                          <EditOutlined />
                        </button>
                      </Tooltip>
                      <Tooltip title="版本管理">
                        <button class="overlay-btn" @click="handleFamily(item)">
                          <BranchesOutlined />
                        </button>
                      </Tooltip>
                      <Tooltip title="下载模型">
                        <button class="overlay-btn" @click="handleDownload(item)">
                          <DownloadOutlined />
                        </button>
                      </Tooltip>
                      <Popconfirm
                        :title="`删除后不可恢复，确认删除模型「${item.name}」？`"
                        @confirm="handleDelete(item)"
                      >
                        <Tooltip title="删除">
                          <button class="overlay-btn overlay-btn--danger">
                            <DeleteOutlined />
                          </button>
                        </Tooltip>
                      </Popconfirm>
                    </div>
                  </div>
                </div>

                <div class="model-card-badge">
                  <svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="20" cy="20" r="18" stroke="#266CFB" stroke-width="1.5" fill="#fff"/>
                    <text x="20" y="17" text-anchor="middle" fill="#266CFB" font-size="9" font-weight="700">AI</text>
                    <text x="20" y="27" text-anchor="middle" fill="#266CFB" font-size="11" font-weight="700">+</text>
                  </svg>
                </div>

                <!-- 文字内容区 -->
                <div class="model-card-body">
                  <h3 class="model-card-title" :title="item.name" @click="handleView(item)">
                    {{ item.name }}
                  </h3>
                  <p v-if="modelDescription(item)" class="model-card-desc" :title="modelDescription(item)">
                    {{ modelDescription(item) }}
                  </p>
                  <p class="model-card-meta" :title="getMetaText(item)">
                    {{ getMetaText(item) }}
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
import {onMounted, reactive, ref} from 'vue';
import {List, Popconfirm, Spin, Tooltip} from 'ant-design-vue';
import {BasicForm, useForm} from '@/components/Form';
import {propTypes} from '@/utils/propTypes';
import {isFunction} from '@/utils/is';
import {BranchesOutlined, DeleteOutlined, DownloadOutlined, EditOutlined, EyeOutlined} from '@ant-design/icons-vue';
import {getFormConfig} from './Data';
import DEFAULT_MODEL_IMAGE from '@/assets/images/video/ai-task.png';
import { formatModelVersionDisplay } from '../../utils/modelVersionUtils';
import { resolveModelImageDisplayUrl } from '@/utils/alertMinioImage';

defineOptions({name: 'ModelCardList'});

const ListItem = List.Item;

const props = defineProps({
  params: propTypes.object.def({}),
  api: propTypes.func,
});

const emit = defineEmits(['getMethod', 'delete', 'edit', 'view', 'train', 'download', 'family']);

const data = ref([]);
const hoverId = ref<number | null>(null);
const state = reactive({
  loading: true,
});

const [registerForm, {validate}] = useForm({
  schemas: getFormConfig(),
  labelWidth: 80,
  baseColProps: {span: 6},
  actionColOptions: {span: 12},
  autoSubmitOnEnter: true,
  submitFunc: handleSubmit,
});

onMounted(() => {
  fetch();
  emit('getMethod', reload);
});

async function handleSubmit() {
  const formData = await validate();
  page.value = 1;
  await fetch(formData);
}

async function reload(opts?: { resetPage?: boolean }) {
  if (opts?.resetPage) {
    page.value = 1;
  }
  state.loading = true;
  await fetch();
}

async function fetch(p = {}) {
  const {api, params} = props;
  if (api && isFunction(api)) {
    try {
      state.loading = true;
      const res = await api({...params, pageNo: page.value, pageSize: pageSize.value, ...p});
      data.value = res?.data ?? [];
      total.value = res?.total ?? 0;
    } catch (error) {
      console.error('获取模型列表失败:', error);
      data.value = [];
      total.value = 0;
    } finally {
      state.loading = false;
    }
  }
}

const page = ref(1);
const pageSize = ref(12);
const total = ref(0);
const paginationProp = ref({
  showSizeChanger: false,
  showQuickJumper: true,
  pageSize,
  current: page,
  total,
  showTotal: (total: number) => `共 ${total} 条`,
  onChange: pageChange,
  onShowSizeChange: pageSizeChange,
});

function pageChange(p: number, pz: number) {
  page.value = p;
  pageSize.value = pz;
  fetch();
}

function pageSizeChange(_current: number, size: number) {
  pageSize.value = size;
  page.value = 1;
  fetch();
}

function getModelImage(item: any): string {
  const url = item.imageUrl || item.image_url;
  return url ? resolveModelImageDisplayUrl(url) : DEFAULT_MODEL_IMAGE;
}

function onImageError(e: Event) {
  const img = e.target as HTMLImageElement;
  if (img && img.src !== DEFAULT_MODEL_IMAGE) {
    img.src = DEFAULT_MODEL_IMAGE;
  }
}

function getFormatText(item: any): string {
  if (item.onnx_model_path) return 'ONNX';
  if (item.model_path) {
    const path = item.model_path.toLowerCase();
    if (path.endsWith('.onnx')) return 'ONNX';
    if (path.endsWith('.pt') || path.endsWith('.pth')) return 'PyTorch';
    if (path.includes('openvino')) return 'OpenVINO';
    if (path.endsWith('.tflite')) return 'TensorFlow Lite';
    return 'PyTorch';
  }
  return '';
}

/** 描述整行展示（CSS 省略），不再按字符硬截断 */
function modelDescription(item: any): string {
  return (item.description || '').trim();
}

/** 元信息行：框架 · 版本 */
function getMetaText(item: any): string {
  const parts: string[] = [];
  const format = getFormatText(item);
  if (format) parts.push(format);
  if (item.version) parts.push(formatModelVersionDisplay(item.version));
  if (!parts.length) parts.push(`ID: ${item.id}`);
  return parts.join(' · ');
}

/** 封面右上角版本角标：N 个版本 · 生效 vX */
function getFamilySummaryText(item: any): string {
  const size = item.family_size ?? 1;
  const version = formatModelVersionDisplay(item.family_effective_version || item.version);
  return `${size} 个版本 · 生效 ${version}`;
}

function handleDelete(record: object) {
  emit('delete', record);
}

function handleView(record: object) {
  emit('view', record);
}

function handleFamily(item: any): void {
  emit('family', item);
}

function handleEdit(record: object) {
  emit('edit', record);
}

function handleDownload(record: object) {
  emit('download', record);
}
</script>

<style lang="less" scoped>
.model-card-list-wrapper {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  background: #fff;
}

.search-bar {
  flex-shrink: 0;
  padding: 16px 16px 0;
  margin-bottom: 10px;
  background: #fff;
}

.list-panel {
  flex: 1;
  min-height: 0;
  padding: 0 8px 16px;
  overflow: hidden auto;
  background: #fff;

  :deep(.ant-list-header) {
    padding: 8px 12px 16px;
    background: transparent;
    border: 0;
  }

  :deep(.ant-list) {
    padding: 0 8px;
  }

  :deep(.ant-row) {
    display: flex;
    flex-wrap: wrap;
    row-gap: 18px;
  }

  :deep(.ant-col) {
    display: flex;
  }

  :deep(.ant-list-item) {
    display: flex;
    width: 100%;
    height: 100%;
    padding: 0 !important;
    margin-bottom: 0;
    border: none;
  }

  :deep(.ant-spin-nested-loading),
  :deep(.ant-spin-container) {
    height: auto !important;
    background: transparent;
  }

  :deep(.ant-list-pagination) {
    margin-top: 20px;
    margin-bottom: 8px;
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

.model-list-item {
  width: 100%;
}

@cover-height: 200px;
@body-height: 104px;
@card-height: @cover-height + @body-height;

.model-card {
  position: relative;
  display: flex;
  flex-direction: column;
  width: 100%;
  height: @card-height;
  overflow: hidden;
  cursor: default;
  background: #fff;
  border-radius: 6px;
  box-shadow: 0 1px 4px rgb(24 24 24 / 10%);
  transition: box-shadow 0.25s ease, transform 0.25s ease;

  &:hover {
    box-shadow: 0 3px 12px rgb(0 0 0 / 12%);
    transform: translateY(-1px);
  }
}

.model-card-cover {
  position: relative;
  flex-shrink: 0;
  width: 100%;
  height: @cover-height;
  overflow: hidden;
  cursor: pointer;
  background: #fafafa;
}

.model-card-cover-inner {
  position: absolute;
  inset: 0;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px;
}

.model-card-image {
  display: block;
  width: auto;
  max-width: 100%;
  height: auto;
  max-height: 100%;
  object-fit: contain;
  object-position: center;
}

.model-card-overlay {
  position: absolute;
  inset: 0;
  z-index: 3;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background: rgb(0 0 0 / 45%);
  border-radius: 6px 6px 0 0;
}

.model-card-version-ribbon {
  position: absolute;
  top: 0;
  right: 0;
  z-index: 4;
  display: inline-flex;
  align-items: center;
  max-width: calc(100% - 4px);
  padding: 4px 10px 4px 12px;
  overflow: hidden;
  font-size: 12px;
  font-weight: 500;
  line-height: 1.5;
  color: #fff;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: pointer;
  background: #266cfb;
  border: none;
  border-radius: 0 6px 0 8px;
  box-shadow: 0 1px 3px rgb(38 108 251 / 35%);
  transition: background 0.2s ease;

  &:hover {
    background: #1e5ae0;
  }
}

.overlay-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
  padding: 0 8px;
}

.overlay-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  font-size: 16px;
  color: #266cfb;
  cursor: pointer;
  background: rgb(255 255 255 / 92%);
  border: none;
  border-radius: 50%;
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

.model-card-badge {
  position: absolute;
  top: @cover-height - 20px;
  right: 14px;
  z-index: 4;
  width: 40px;
  height: 40px;
  pointer-events: none;

  svg {
    width: 40px;
    height: 40px;
    filter: drop-shadow(0 2px 6px rgb(38 108 251 / 20%));
  }
}

.model-card-body {
  box-sizing: border-box;
  flex-shrink: 0;
  height: @body-height;
  padding: 14px 16px 12px;
  overflow: hidden;
}

.model-card-title {
  margin: 0 0 6px;
  overflow: hidden;
  font-size: 15px;
  font-weight: 600;
  line-height: 1.45;
  color: #181818;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: pointer;

  &:hover {
    color: #266cfb;
  }
}

.model-card-desc {
  margin: 0 0 2px;
  overflow: hidden;
  font-size: 13px;
  line-height: 1.5;
  color: rgb(0 0 0 / 65%);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.model-card-meta {
  margin: 0;
  overflow: hidden;
  font-size: 12px;
  line-height: 1.5;
  color: rgb(0 0 0 / 45%);
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
