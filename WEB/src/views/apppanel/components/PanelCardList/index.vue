<template>
  <div class="panel-card-list-wrapper">
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
              <span class="list-title">APP面板</span>
              <div class="list-actions">
                <slot name="header"></slot>
              </div>
            </div>
          </template>
          <template #renderItem="{ item }">
            <ListItem class="panel-list-item">
              <div class="panel-card" @mouseenter="hoverId = item.id" @mouseleave="hoverId = null">
                <!-- 封面：APP 模板手机预览（即模板截图） -->
                <div class="panel-card-cover" @click="handleView(item)">
                  <div class="panel-card-cover-inner">
                    <PanelPhonePreview :schema="item.panelSchema" :template-name="item.templateName" />
                  </div>
                  <div
                    v-show="hoverId === item.id"
                    class="panel-card-overlay"
                    @click="handleView(item)"
                  >
                    <div class="overlay-actions" @click.stop>
                      <Tooltip title="查看详情">
                        <button class="overlay-btn" @click="handleView(item)">
                          <EyeOutlined />
                        </button>
                      </Tooltip>
                      <Tooltip title="设计面板">
                        <button class="overlay-btn" @click="handleEdit(item)">
                          <EditOutlined />
                        </button>
                      </Tooltip>
                      <Tooltip :title="item.status === 'PUBLISHED' ? '停用' : '发布下发'">
                        <button class="overlay-btn" @click="handleTogglePublish(item)">
                          <RocketOutlined v-if="item.status !== 'PUBLISHED'" />
                          <PauseCircleOutlined v-else />
                        </button>
                      </Tooltip>
                      <Popconfirm title="是否确认删除？" @confirm="handleDelete(item)">
                        <Tooltip title="删除">
                          <button class="overlay-btn overlay-btn--danger">
                            <DeleteOutlined />
                          </button>
                        </Tooltip>
                      </Popconfirm>
                    </div>
                  </div>
                  <!-- 状态角标 -->
                  <div class="panel-card-status" :class="statusClass(item.status)">
                    {{ statusMeta(item.status).text }}
                  </div>
                </div>

                <!-- 文字内容区 -->
                <div class="panel-card-body">
                  <h3 class="panel-card-title" :title="item.templateName" @click="handleView(item)">
                    {{ item.templateName }}
                  </h3>
                  <p class="panel-card-tags" :title="getTagsText(item)">
                    {{ getTagsText(item) }}
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

<script lang="ts" setup name="PanelCardList">
import {onMounted, reactive, ref} from 'vue';
import {List, Popconfirm, Spin, Tooltip} from 'ant-design-vue';
import {BasicForm, useForm} from '@/components/Form';
import {propTypes} from '@/utils/propTypes';
import {isFunction} from '@/utils/is';
import {DeleteOutlined, EditOutlined, EyeOutlined, PauseCircleOutlined, RocketOutlined} from '@ant-design/icons-vue';
import PanelPhonePreview from '../PanelPhonePreview.vue';
import {getFormConfig} from './Data';
import {getDeviceProfiles} from '@/api/device/product';

defineOptions({name: 'PanelCardList'});

const ListItem = List.Item;

const props = defineProps({
  params: propTypes.object.def({}),
  api: propTypes.func,
});

const emit = defineEmits(['getMethod', 'delete', 'edit', 'view', 'publishToggle']);

const data = ref([]);
const hoverId = ref<number | null>(null);
const state = reactive({
  loading: true,
});
const productNameMap = ref<Record<string, string>>({});

const statusColorMap: Record<string, { color: string; text: string }> = {
  DRAFT: {color: 'default', text: '草稿'},
  PUBLISHED: {color: 'success', text: '已发布'},
  DISABLED: {color: 'error', text: '已停用'},
};
const statusMeta = (status?: string) => statusColorMap[status || 'DRAFT'] || statusColorMap.DRAFT;
const statusClass = (status?: string) => {
  const map: Record<string, string> = {DRAFT: 'st-draft', PUBLISHED: 'st-published', DISABLED: 'st-disabled'};
  return map[status || 'DRAFT'] || 'st-draft';
};

const [registerForm, {validate, updateSchema}] = useForm({
  schemas: getFormConfig(),
  labelWidth: 80,
  baseColProps: {span: 6},
  actionColOptions: {span: 12},
  autoSubmitOnEnter: true,
  submitFunc: handleSubmit,
});

// 产品下拉与表格视图同源（产品管理数据）
async function loadProducts() {
  try {
    const res = await getDeviceProfiles({pageNum: 1, pageSize: 500});
    const rows = res?.data ?? res ?? [];
    const map: Record<string, string> = {};
    (rows || []).forEach((r) => {
      if (r?.productIdentification) map[r.productIdentification] = r.productName;
    });
    productNameMap.value = map;
    const options = (rows || [])
      .filter((r) => r.productIdentification)
      .map((r) => ({label: `${r.productName}（${r.productIdentification}）`, value: r.productIdentification}));
    updateSchema([{field: 'productIdentification', componentProps: {options}}]);
  } catch (e) {
    console.warn('加载产品列表失败', e);
  }
}

onMounted(() => {
  fetch();
  loadProducts();
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
      data.value = (res?.data ?? []).map((r) => ({
        ...r,
        productName: productNameMap.value[r.productIdentification] || '',
      }));
      total.value = res?.total ?? 0;
    } catch (error) {
      console.error('获取模板列表失败:', error);
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
  showTotal: (total: number) => `总 ${total} 条`,
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

function getTagsText(item: any): string {
  const parts: string[] = [];
  const productName = item.productName || '';
  if (productName) parts.push(productName);
  if (item.productIdentification) parts.push(item.productIdentification);
  if (item.version) parts.push(`v${item.version}`);
  if (item.remark) {
    const remark = item.remark.trim();
    parts.push(remark.length <= 14 ? remark : remark.slice(0, 14) + '…');
  }
  if (!parts.length) parts.push(`ID: ${item.id}`);
  return parts.join('  |  ');
}

function handleDelete(record: object) {
  emit('delete', record);
}

function handleView(record: object) {
  emit('view', record);
}

function handleEdit(record: object) {
  emit('edit', record);
}

function handleTogglePublish(record: object) {
  emit('publishToggle', record);
}
</script>

<style lang="less" scoped>
.panel-card-list-wrapper {
  background: #fff;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.search-bar {
  padding: 16px 16px 0;
  margin-bottom: 10px;
  background: #fff;
  flex-shrink: 0;
}

.list-panel {
  background: #fff;
  padding: 0 8px 16px;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;

  :deep(.ant-list-header) {
    border: 0;
    padding: 8px 12px 16px;
    background: transparent;
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
    margin-bottom: 0;
    padding: 0 !important;
    border: none;
    width: 100%;
    height: 100%;
    display: flex;
  }

  :deep(.ant-spin-nested-loading),
  :deep(.ant-spin-container) {
    background: transparent;
    height: auto !important;
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

.panel-list-item {
  width: 100%;
}

@cover-height: 290px;
@body-height: 92px;
@card-height: @cover-height + @body-height;

.panel-card {
  position: relative;
  display: flex;
  flex-direction: column;
  width: 100%;
  height: @card-height;
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 1px 4px rgba(24, 24, 24, 0.1);
  overflow: hidden;
  transition: box-shadow 0.25s ease, transform 0.25s ease;
  cursor: default;

  &:hover {
    box-shadow: 0 3px 14px rgba(0, 0, 0, 0.14);
    transform: translateY(-2px);
  }
}

// 封面：iOS 桌面壁纸质感背景，手机竖屏预览居中悬浮
.panel-card-cover {
  position: relative;
  width: 100%;
  height: @cover-height;
  flex-shrink: 0;
  overflow: hidden;
  cursor: pointer;
  background:
    radial-gradient(circle at 18% 16%, rgba(255, 255, 255, 0.9) 0%, transparent 52%),
    radial-gradient(circle at 84% 82%, rgba(152, 190, 255, 0.35) 0%, transparent 55%),
    radial-gradient(circle at 70% 12%, rgba(255, 255, 255, 0.5) 0%, transparent 45%),
    linear-gradient(158deg, #d8e4fb 0%, #eef2f9 52%, #e2e9f6 100%);
}

.panel-card-cover-inner {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px 0;
  box-sizing: border-box;

  // 手机竖屏比例（9:16），宽度占封面 74%（上限 158px）为主角，四周留呼吸留白
  :deep(.phone-preview) {
    width: min(74%, 158px);
    height: auto;
    max-height: 100%;
    border-width: 4px;
    border-radius: 20px;
    box-shadow:
      0 18px 36px rgba(16, 19, 26, 0.34),
      0 4px 10px rgba(16, 19, 26, 0.18);
  }
}

.panel-card-overlay {
  position: absolute;
  inset: 0;
  z-index: 3;
  border-radius: 10px 10px 0 0;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(16, 19, 26, 0.55);
}

.overlay-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
  padding: 0 8px;
}

.overlay-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.92);
  color: #266cfb;
  font-size: 16px;
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

.panel-card-status {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 4;
  font-size: 10px;
  line-height: 1;
  padding: 4px 8px;
  border-radius: 99px;
  color: #fff;
  pointer-events: none;
  backdrop-filter: blur(4px);

  &.st-draft {
    background: rgba(140, 140, 140, 0.75);
  }

  &.st-published {
    background: rgba(22, 163, 121, 0.82);
  }

  &.st-disabled {
    background: rgba(245, 34, 45, 0.78);
  }
}

.panel-card-body {
  flex-shrink: 0;
  height: @body-height;
  padding: 22px 14px 12px;
  box-sizing: border-box;
  overflow: hidden;
}

.panel-card-title {
  margin: 0 0 8px;
  font-size: 15px;
  font-weight: 600;
  line-height: 1.45;
  color: #181818;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: pointer;

  &:hover {
    color: #266cfb;
  }
}

.panel-card-tags {
  margin: 0;
  font-size: 12px;
  line-height: 1.5;
  color: #999;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
