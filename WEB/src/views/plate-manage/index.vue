<template>
  <div class="plate-manage-page">
    <div class="page-header">
      <div class="header-left">
        <Button type="text" class="back-btn" @click="goBack">
          <ArrowLeftOutlined /> 返回车牌库
        </Button>
        <div v-if="library" class="library-info">
          <h1 class="page-title">{{ library.name }}</h1>
          <div class="page-meta">
            <a-tag>{{ library.code }}</a-tag>
            <span>{{ entryTotal }} 条车牌</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 表格模式 -->
    <BasicTable v-if="viewMode === 'table'" @register="registerTable">
      <template #toolbar>
        <Button type="primary" @click="openEntryModal()">录入车牌</Button>
        <Button @click="handleNormalize">车牌归一化</Button>
        <PopConfirmButton
          placement="topRight"
          type="primary"
          color="error"
          :disabled="!checkedKeys.length"
          title="确定批量删除所选车牌？"
          preIcon="ant-design:delete-outlined"
          @confirm="handleBatchDelete"
        >
          批量删除{{ checkedKeys.length ? ` (${checkedKeys.length})` : '' }}
        </PopConfirmButton>
        <Button type="default" @click="handleToggleViewMode" preIcon="ant-design:swap-outlined">
          切换视图
        </Button>
      </template>
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'image_url'">
          <a-avatar :size="48" :src="plateImageUrl(record.image_url)" shape="square">
            <template #icon><CarOutlined /></template>
          </a-avatar>
        </template>
        <template v-else-if="column.dataIndex === 'is_enabled'">
          <a-tag :color="record.is_enabled ? 'green' : 'default'" size="small">
            {{ record.is_enabled ? '启用' : '停用' }}
          </a-tag>
        </template>
        <template v-else-if="column.dataIndex === 'action'">
          <TableAction :actions="getTableActions(record)" />
        </template>
      </template>
    </BasicTable>

    <!-- 卡片模式 -->
    <div v-else class="card-list-wrapper">
      <div class="search-panel">
        <BasicForm @register="registerForm" @reset="handleSearch" />
      </div>
      <div class="list-panel">
        <Spin :spinning="loading">
          <List
            :grid="{ gutter: 18, xs: 2, sm: 3, md: 4, lg: 5, xl: 6, xxl: 6 }"
            :data-source="entryList"
            :pagination="paginationProp"
          >
            <template #header>
              <div class="list-header">
                <span class="list-title">车牌列表</span>
                <div class="list-actions">
                  <Button type="primary" @click="openEntryModal()">录入车牌</Button>
                  <Button @click="handleNormalize">车牌归一化</Button>
                  <PopConfirmButton
                    placement="topRight"
                    type="primary"
                    color="error"
                    :disabled="!checkedKeys.length"
                    title="确定批量删除所选车牌？"
                    preIcon="ant-design:delete-outlined"
                    @confirm="handleBatchDelete"
                  >
                    批量删除{{ checkedKeys.length ? ` (${checkedKeys.length})` : '' }}
                  </PopConfirmButton>
                  <Button
                    type="default"
                    @click="handleToggleViewMode"
                    preIcon="ant-design:swap-outlined"
                  >
                    切换视图
                  </Button>
                </div>
              </div>
            </template>
            <template #renderItem="{ item }">
              <ListItem class="plate-list-item">
                <div
                  class="plate-card"
                  :class="{ disabled: !item.is_enabled, selected: isSelected(item.id) }"
                  @mouseenter="hoverId = item.id"
                  @mouseleave="hoverId = null"
                >
                  <div
                    class="card-checkbox"
                    :class="{ checked: isSelected(item.id) }"
                    @click.stop="toggleSelect(item.id)"
                  >
                    <span class="checkbox-inner" />
                  </div>
                  <div class="plate-card-cover" @click="openEntryModal(item)">
                    <div class="plate-card-cover-inner">
                      <img
                        :src="plateImageUrl(item.image_url) || defaultPlateImg"
                        alt="车牌"
                        class="plate-card-image"
                        @error="onImageError"
                      />
                    </div>
                    <div v-show="hoverId === item.id" class="plate-card-overlay" @click.stop>
                      <div class="overlay-actions">
                        <Tooltip title="编辑">
                          <button class="overlay-btn" @click="openEntryModal(item)">
                            <EditOutlined />
                          </button>
                        </Tooltip>
                      </div>
                    </div>
                  </div>
                  <div class="plate-card-body">
                    <h3
                      class="plate-card-title"
                      :title="item.plate_no"
                      @click="openEntryModal(item)"
                    >
                      {{ item.plate_no }}
                    </h3>
                    <p class="plate-card-meta" :title="getMetaText(item)">
                      {{ getMetaText(item) }}
                    </p>
                  </div>
                </div>
              </ListItem>
            </template>
            <template #empty>
              <Empty description="暂无车牌，点击「录入车牌」开始添加" />
            </template>
          </List>
        </Spin>
      </div>
    </div>

    <PlateEntryModal @register="registerEntryDrawer" @success="handleSuccess" />
    <PlateNormalizeModal @register="registerNormalizeModal" @success="handleSuccess" />
  </div>
</template>

<script lang="ts" setup>
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ArrowLeftOutlined, CarOutlined, EditOutlined } from '@ant-design/icons-vue';
import { Empty, List, Spin, Tooltip } from 'ant-design-vue';
import { Button, PopConfirmButton } from '@/components/Button';
import { BasicForm, useForm } from '@/components/Form';
import { useDrawer } from '@/components/Drawer';
import { useModal } from '@/components/Modal';
import { BasicTable, TableAction, useTable } from '@/components/Table';
import { useMessage } from '@/hooks/web/useMessage';
import {
  batchDeletePlateEntries,
  deletePlateEntry,
  getPlateLibrary,
  listPlateEntries,
  parsePlateApiError,
  resolvePlateImageDisplayUrl,
  type PlateEntry,
  type PlateLibrary,
} from '@/api/device/plate_library';
import { getPlateEntryFormConfig, getPlateManageColumns } from './Data';
import PlateEntryModal from '@/views/camera/components/PlateLibrary/PlateEntryModal.vue';
import PlateNormalizeModal from '@/views/camera/components/PlateLibrary/PlateNormalizeModal.vue';
import DEFAULT_PLATE_IMAGE from '@/assets/images/video/snap-task.png';

defineOptions({ name: 'PlateManagePage' });

const ListItem = List.Item;
const route = useRoute();
const router = useRouter();
const { createMessage } = useMessage();

const libraryId = computed(() => Number(route.params.libraryId));
const library = ref<PlateLibrary | null>(null);
const entryList = ref<PlateEntry[]>([]);
const entryTotal = ref(0);
const loading = ref(false);
const hoverId = ref<number | null>(null);
const viewMode = ref<'table' | 'card'>('card');
const checkedKeys = ref<number[]>([]);
const page = ref(1);
const pageSize = ref(18);
const searchText = ref('');
const defaultPlateImg = DEFAULT_PLATE_IMAGE;

function plateImageUrl(url?: string | null) {
  return resolvePlateImageDisplayUrl(url);
}

const [registerEntryDrawer, { openDrawer: openEntryDrawer }] = useDrawer();
const [registerNormalizeModal, { openModal: openNormalizeModal }] = useModal();

function isSelected(id: number) {
  return checkedKeys.value.includes(id);
}

function toggleSelect(id: number) {
  if (isSelected(id)) {
    checkedKeys.value = checkedKeys.value.filter((k) => k !== id);
  } else {
    checkedKeys.value = [...checkedKeys.value, id];
  }
}

function clearSelection() {
  checkedKeys.value = [];
}

const [registerForm, { validate: validateSearch }] = useForm({
  ...getPlateEntryFormConfig(),
  autoSubmitOnEnter: true,
  submitFunc: handleSearch,
});

const paginationProp = computed(() => ({
  showSizeChanger: false,
  showQuickJumper: true,
  pageSize: pageSize.value,
  current: page.value,
  total: entryTotal.value,
  showTotal: (t: number) => `总 ${t} 条`,
  onChange: (p: number, pz: number) => {
    page.value = p;
    pageSize.value = pz;
    loadEntries();
  },
}));

const [registerTable, { reload }] = useTable({
  title: '车牌列表',
  api: async (params) => {
    if (!libraryId.value) return { items: [], total: 0 };
    const res = await listPlateEntries(libraryId.value, {
      search: params.search || undefined,
      page: params.page || 1,
      page_size: params.pageSize || 10,
    });
    entryTotal.value = res.total ?? 0;
    return {
      items: res.list || [],
      total: res.total ?? 0,
    };
  },
  columns: getPlateManageColumns(),
  useSearchForm: true,
  formConfig: getPlateEntryFormConfig(),
  pagination: true,
  rowKey: 'id',
  immediate: false,
  fetchSetting: {
    listField: 'items',
    totalField: 'total',
  },
  rowSelection: {
    type: 'checkbox',
    selectedRowKeys: checkedKeys,
    onSelect(record: PlateEntry, selected: boolean) {
      if (selected) {
        checkedKeys.value = [...checkedKeys.value, record.id];
      } else {
        checkedKeys.value = checkedKeys.value.filter((id) => id !== record.id);
      }
    },
    onSelectAll(selected: boolean, _rows: PlateEntry[], changeRows: PlateEntry[]) {
      const changeIds = changeRows.map((r) => r.id);
      if (selected) {
        checkedKeys.value = [...new Set([...checkedKeys.value, ...changeIds])];
      } else {
        checkedKeys.value = checkedKeys.value.filter((id) => !changeIds.includes(id));
      }
    },
  },
});

function getMetaText(item: PlateEntry) {
  const parts: string[] = [];
  if (item.plate_color) parts.push(item.plate_color);
  if (item.owner_name) parts.push(item.owner_name);
  if (item.owner_phone) parts.push(item.owner_phone);
  if (!item.is_enabled) parts.push('已停用');
  return parts.length ? parts.join(' · ') : '—';
}

function onImageError(e: Event) {
  const img = e.target as HTMLImageElement;
  if (img && img.src !== defaultPlateImg) img.src = defaultPlateImg;
}

function goBack() {
  router.push({ path: '/camera/index', query: { tab: '11' } });
}

async function loadLibrary() {
  if (!libraryId.value) return;
  try {
    const res = await getPlateLibrary(libraryId.value);
    library.value = res.data || null;
  } catch (e: unknown) {
    createMessage.error(parsePlateApiError(e, '加载车牌库失败'));
  }
}

async function loadEntries() {
  if (!libraryId.value) return;
  loading.value = true;
  try {
    const res = await listPlateEntries(libraryId.value, {
      search: searchText.value || undefined,
      page: page.value,
      page_size: pageSize.value,
    });
    entryList.value = res.list || [];
    entryTotal.value = res.total ?? entryList.value.length;
    checkedKeys.value = checkedKeys.value.filter((id) =>
      entryList.value.some((e) => e.id === id),
    );
  } catch (e: unknown) {
    createMessage.error(parsePlateApiError(e, '加载车牌列表失败'));
    entryList.value = [];
    entryTotal.value = 0;
  } finally {
    loading.value = false;
  }
}

async function handleSearch() {
  const values = await validateSearch();
  searchText.value = values?.search || '';
  page.value = 1;
  if (viewMode.value === 'table') {
    reload();
  } else {
    await loadEntries();
  }
}

function handleToggleViewMode() {
  viewMode.value = viewMode.value === 'table' ? 'card' : 'table';
  clearSelection();
  if (viewMode.value === 'table') {
    reload();
  } else {
    loadEntries();
  }
}

function handleSuccess() {
  clearSelection();
  loadLibrary();
  if (viewMode.value === 'table') {
    reload();
  } else {
    loadEntries();
  }
}

function handleNormalize() {
  openNormalizeModal(true, { library: library.value });
}

function openEntryModal(record?: PlateEntry) {
  if (record) {
    openEntryDrawer(true, { type: 'edit', library: library.value, record });
  } else {
    openEntryDrawer(true, { type: 'create', library: library.value });
  }
}

async function handleDeleteEntry(record: PlateEntry) {
  try {
    await deletePlateEntry(record.id);
    createMessage.success('删除成功');
    handleSuccess();
  } catch (e: unknown) {
    createMessage.error(parsePlateApiError(e, '删除失败'));
  }
}

async function handleBatchDelete() {
  if (!checkedKeys.value.length) return;
  try {
    const res = await batchDeletePlateEntries([...checkedKeys.value]);
    const n = res.data?.deleted ?? checkedKeys.value.length;
    createMessage.success(`已删除 ${n} 条车牌`);
    handleSuccess();
  } catch (e: unknown) {
    createMessage.error(parsePlateApiError(e, '批量删除失败'));
  }
}

function getTableActions(record: PlateEntry) {
  const actions = [
    {
      icon: 'ant-design:edit-filled',
      tooltip: '编辑',
      onClick: () => openEntryModal(record),
    },
    {
      icon: 'material-symbols:delete-outline-rounded',
      tooltip: '删除',
      popConfirm: {
        title: '确定删除该车牌？',
        confirm: () => handleDeleteEntry(record),
      },
    },
  ];
  // 有车牌号才提供轨迹入口（无号码的条目无法按车牌检索轨迹）
  if (record.plate_no) {
    actions.unshift({
      icon: 'icon-park-outline:map-draw',
      tooltip: '出现轨迹',
      onClick: () => goPlateTrajectory(record.plate_no as string),
    });
  }
  return actions;
}

/** 跳转告警页地图分布：查看该车牌某天的出现轨迹 */
function goPlateTrajectory(plateNo: string) {
  router.push({
    path: '/alert',
    query: {
      tab: '1',
      trajectory_plate: plateNo,
      trajectory_date: new Date().toISOString().slice(0, 10),
    },
  });
}

onMounted(async () => {
  if (!libraryId.value || Number.isNaN(libraryId.value)) {
    createMessage.error('无效的车牌库 ID');
    goBack();
    return;
  }
  await loadLibrary();
  if (viewMode.value === 'card') {
    await loadEntries();
  } else {
    reload();
  }
});
</script>

<style lang="less" scoped>
.plate-manage-page {
  min-height: 100%;
  background: #fff;
}

.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  width: 100%;
}

.list-actions {
  display: flex;
  gap: 8px;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;

  .header-left {
    display: flex;
    flex-direction: column;
    gap: 8px;
    min-width: 0;
  }

  .back-btn {
    padding-left: 0;
    color: rgba(0, 0, 0, 0.45);
  }

  .page-title {
    margin: 0;
    font-size: 20px;
    font-weight: 600;
    color: #181818;
  }

  .page-meta {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px;
    font-size: 13px;
    color: rgba(0, 0, 0, 0.45);
  }
}

.card-list-wrapper {
  .search-panel {
    padding: 16px 20px 0;
  }

  .list-panel {
    padding: 0 12px 20px;

    :deep(.ant-list-header) {
      border: 0;
      padding: 8px 8px 16px;
    }

    :deep(.ant-list-item) {
      padding: 0 !important;
      border: none;
    }

    :deep(.ant-row) {
      row-gap: 18px;
    }
  }
}

.list-title {
  padding-left: 7px;
  font-size: 16px;
  font-weight: 500;
  line-height: 24px;
  color: #181818;
}

@cover-height: 160px;
@body-height: 88px;

.plate-card {
  position: relative;
  display: flex;
  flex-direction: column;
  width: 100%;
  height: @cover-height + @body-height;
  background: #fff;
  border-radius: 6px;
  box-shadow: 0 1px 4px rgba(24, 24, 24, 0.1);
  overflow: hidden;
  transition: box-shadow 0.25s ease, transform 0.25s ease, border-color 0.2s;
  border: 2px solid transparent;

  &.disabled {
    opacity: 0.65;
  }

  &.selected {
    border-color: #266cfb;
    box-shadow: 0 0 0 1px #266cfb, 0 3px 12px rgba(38, 108, 251, 0.15);
  }

  &:hover {
    box-shadow: 0 3px 12px rgba(0, 0, 0, 0.12);
    transform: translateY(-1px);
  }

  .card-checkbox {
    position: absolute;
    top: 8px;
    left: 8px;
    z-index: 4;
    width: 20px;
    height: 20px;
    border: 2px solid #d9d9d9;
    border-radius: 3px;
    background: #fff;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;

    .checkbox-inner {
      width: 12px;
      height: 12px;
      border-radius: 2px;
      background: transparent;
    }

    &.checked {
      border-color: #ff4d4f;

      .checkbox-inner {
        background: #ff4d4f;
      }
    }
  }
}

.plate-card-cover {
  position: relative;
  height: @cover-height;
  cursor: pointer;
  background: #fafafa;
  overflow: hidden;
}

.plate-card-cover-inner {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px;
}

.plate-card-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.plate-card-overlay {
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
}

.overlay-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border: none;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.92);
  color: #266cfb;
  font-size: 16px;
  cursor: pointer;

  &:hover {
    background: #fff;
    transform: scale(1.08);
  }
}

.plate-card-body {
  height: @body-height;
  padding: 14px 14px 10px;
  overflow: hidden;
}

.plate-card-title {
  margin: 0 0 6px;
  font-size: 15px;
  font-weight: 600;
  color: #181818;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: pointer;

  &:hover {
    color: #266cfb;
  }
}

.plate-card-meta {
  margin: 0;
  font-size: 13px;
  color: #999;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
