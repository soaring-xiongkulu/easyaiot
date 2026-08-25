<template>
  <div class="face-manage-page">
    <div class="page-header">
      <div class="header-left">
        <Button type="text" class="back-btn" @click="goBack">
          <ArrowLeftOutlined /> 返回人脸库
        </Button>
      </div>
    </div>

    <!-- 表格模式 -->
    <BasicTable v-if="viewMode === 'table'" @register="registerTable">
      <template #toolbar>
        <Button type="primary" @click="handleAddPerson">录入人脸</Button>
        <Button @click="handleNormalize">人脸归一化</Button>
        <PopConfirmButton
          placement="topRight"
          type="primary"
          color="error"
          :disabled="!checkedKeys.length"
          title="确定批量删除所选人员？其全部人脸照片将一并删除。"
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
        <template v-if="column.dataIndex === 'cover_image_url'">
          <a-avatar :size="48" :src="faceImageUrl(record.cover_image_url)" shape="square">
            <template #icon><UserOutlined /></template>
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
            :data-source="personList"
            :pagination="paginationProp"
          >
            <template #header>
              <div class="list-header">
                <span class="list-title">人员列表</span>
                <div class="list-actions">
                  <Button type="primary" @click="handleAddPerson">录入人脸</Button>
                  <Button @click="handleNormalize">人脸归一化</Button>
                  <PopConfirmButton
                    placement="topRight"
                    type="primary"
                    color="error"
                    :disabled="!checkedKeys.length"
                    title="确定批量删除所选人员？其全部人脸照片将一并删除。"
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
              <ListItem class="person-list-item">
                <div
                  class="person-card"
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
                  <div class="person-card-cover" @click="openPersonDetail(item)">
                    <div class="person-card-cover-inner">
                      <img
                        :src="faceImageUrl(item.cover_image_url) || defaultFaceImg"
                        alt="封面"
                        class="person-card-image"
                        @error="onImageError"
                      />
                    </div>
                    <div v-if="item.face_count > 1" class="face-count-badge">
                      {{ item.face_count }} 张
                    </div>
                    <div v-show="hoverId === item.id" class="person-card-overlay" @click.stop>
                      <div class="overlay-actions">
                        <Tooltip title="查看详情">
                          <button class="overlay-btn" @click="openPersonDetail(item)">
                            <EyeOutlined />
                          </button>
                        </Tooltip>
                        <Tooltip title="添加照片">
                          <button class="overlay-btn" @click="handleAddPhoto(item)">
                            <PlusOutlined />
                          </button>
                        </Tooltip>
                      </div>
                    </div>
                  </div>

                  <div class="person-card-body">
                    <h3
                      class="person-card-title"
                      :title="item.person_name"
                      @click="openPersonDetail(item)"
                    >
                      {{ item.person_name }}
                    </h3>
                    <p class="person-card-meta" :title="getMetaText(item)">
                      {{ getMetaText(item) }}
                    </p>
                  </div>
                </div>
              </ListItem>
            </template>
            <template #empty>
              <Empty description="暂无人员，点击「录入人脸」开始添加" />
            </template>
          </List>
        </Spin>
      </div>
    </div>

    <FaceEntryModal @register="registerEntryModal" @success="handleSuccess" />
    <PersonDetailDrawer @register="registerPersonDrawer" @success="handleSuccess" />
    <FaceNormalizeModal @register="registerNormalizeModal" @success="handleSuccess" />
  </div>
</template>

<script lang="ts" setup>
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import {
  ArrowLeftOutlined,
  EyeOutlined,
  PlusOutlined,
  UserOutlined,
} from '@ant-design/icons-vue';
import { Empty, List, Spin, Tooltip } from 'ant-design-vue';
import { Button, PopConfirmButton } from '@/components/Button';
import { BasicForm, useForm } from '@/components/Form';
import { BasicTable, TableAction, useTable } from '@/components/Table';
import { useDrawer } from '@/components/Drawer';
import { useModal } from '@/components/Modal';
import { useMessage } from '@/hooks/web/useMessage';
import {
  batchDeleteFacePersons,
  deleteFacePerson,
  getFaceLibrary,
  listFacePersons,
  unwrapFaceApiEntity,
  resolveFaceImageDisplayUrl,
  type FaceLibrary,
  type FacePerson,
} from '@/api/device/face_library';
import FaceEntryModal from '@/views/camera/components/FaceLibrary/FaceEntryModal.vue';
import FaceNormalizeModal from '@/views/camera/components/FaceLibrary/FaceNormalizeModal.vue';
import PersonDetailDrawer from './components/PersonDetailDrawer.vue';
import { getPersonColumns, getPersonFormConfig } from './Data';
import DEFAULT_FACE_IMAGE from '@/assets/images/video/snap-task.png';

defineOptions({ name: 'FaceManagePage' });

const ListItem = List.Item;
const route = useRoute();
const router = useRouter();
const { createMessage } = useMessage();

const libraryId = computed(() => Number(route.params.libraryId));
const library = ref<FaceLibrary | null>(null);
const personList = ref<FacePerson[]>([]);
const personTotal = ref(0);
const loading = ref(false);
const hoverId = ref<number | null>(null);
const viewMode = ref<'table' | 'card'>('card');
const checkedKeys = ref<number[]>([]);
const page = ref(1);
const pageSize = ref(18);
const searchText = ref('');

const defaultFaceImg = DEFAULT_FACE_IMAGE;

function faceImageUrl(url?: string | null) {
  return resolveFaceImageDisplayUrl(url);
}

const [registerEntryModal, { openDrawer: openEntryModal }] = useDrawer();
const [registerPersonDrawer, { openDrawer: openPersonDrawer }] = useDrawer();
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

const [registerForm, { validate }] = useForm({
  ...getPersonFormConfig(),
  autoSubmitOnEnter: true,
  submitFunc: handleSearch,
});

const paginationProp = computed(() => ({
  showSizeChanger: false,
  showQuickJumper: true,
  pageSize: pageSize.value,
  current: page.value,
  total: personTotal.value,
  showTotal: (t: number) => `总 ${t} 人`,
  onChange: (p: number, pz: number) => {
    page.value = p;
    pageSize.value = pz;
    loadPersons();
  },
}));

const [registerTable, { reload }] = useTable({
  title: '人员列表',
  api: async (params) => {
    if (!libraryId.value) return { items: [], total: 0 };
    const res = await listFacePersons(libraryId.value, {
      search: params.search || undefined,
      page: params.page || 1,
      pageSize: params.pageSize || 10,
    });
    return {
      items: res.data || [],
      total: res.total ?? (res.data?.length ?? 0),
    };
  },
  columns: getPersonColumns(),
  useSearchForm: true,
  formConfig: getPersonFormConfig(),
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
    onSelect(record: FacePerson, selected: boolean) {
      if (selected) {
        checkedKeys.value = [...checkedKeys.value, record.id];
      } else {
        checkedKeys.value = checkedKeys.value.filter((id) => id !== record.id);
      }
    },
    onSelectAll(selected: boolean, _rows: FacePerson[], changeRows: FacePerson[]) {
      const changeIds = changeRows.map((r) => r.id);
      if (selected) {
        checkedKeys.value = [...new Set([...checkedKeys.value, ...changeIds])];
      } else {
        checkedKeys.value = checkedKeys.value.filter((id) => !changeIds.includes(id));
      }
    },
  },
});

function getMetaText(item: FacePerson) {
  const parts: string[] = [];
  if (item.person_code) parts.push(item.person_code);
  parts.push(item.face_count > 1 ? `${item.face_count} 张照片` : '单张照片');
  if (!item.is_enabled) parts.push('已停用');
  return parts.join(' · ');
}

function onImageError(e: Event) {
  const img = e.target as HTMLImageElement;
  if (img && img.src !== defaultFaceImg) img.src = defaultFaceImg;
}

function goBack() {
  router.push({ path: '/camera/index', query: { tab: '10' } });
}

async function loadLibrary() {
  if (!libraryId.value) return;
  try {
    const res = await getFaceLibrary(libraryId.value);
    library.value = unwrapFaceApiEntity(res);
  } catch (e: any) {
    createMessage.error(e?.message || '加载人脸库失败');
  }
}

async function loadPersons() {
  if (!libraryId.value) return;
  loading.value = true;
  try {
    const res = await listFacePersons(libraryId.value, {
      search: searchText.value || undefined,
      page: page.value,
      pageSize: pageSize.value,
    });
    personList.value = res.data || [];
    personTotal.value = res.total ?? personList.value.length;
    checkedKeys.value = checkedKeys.value.filter((id) =>
      personList.value.some((p) => p.id === id),
    );
  } catch (e: any) {
    createMessage.error(e?.message || '加载人员列表失败');
    personList.value = [];
    personTotal.value = 0;
  } finally {
    loading.value = false;
  }
}

async function handleSearch() {
  const values = await validate();
  searchText.value = values?.search || '';
  page.value = 1;
  if (viewMode.value === 'table') {
    reload();
  } else {
    await loadPersons();
  }
}

function handleToggleViewMode() {
  viewMode.value = viewMode.value === 'table' ? 'card' : 'table';
  clearSelection();
  if (viewMode.value === 'table') {
    reload();
  } else {
    loadPersons();
  }
}

function handleSuccess() {
  clearSelection();
  loadLibrary();
  if (viewMode.value === 'table') {
    reload();
  } else {
    loadPersons();
  }
}

function handleAddPerson() {
  const lib = library.value ?? ({ id: libraryId.value } as FaceLibrary);
  openEntryModal(true, { type: 'create', library: lib });
}

function handleAddPhoto(person: FacePerson) {
  const lib = library.value ?? ({ id: libraryId.value } as FaceLibrary);
  openEntryModal(true, {
    type: 'create',
    library: lib,
    person,
    addToPerson: true,
  });
}

function openPersonDetail(person: FacePerson) {
  openPersonDrawer(true, { library: library.value, person });
}

function handleNormalize() {
  openNormalizeModal(true, { library: library.value });
}

async function handleDeletePerson(record: FacePerson) {
  try {
    await deleteFacePerson(record.id);
    createMessage.success('删除成功');
    handleSuccess();
  } catch (e: any) {
    createMessage.error(e?.message || '删除失败');
  }
}

async function handleBatchDelete() {
  if (!checkedKeys.value.length) return;
  try {
    const res = await batchDeleteFacePersons([...checkedKeys.value]);
    const n = res.data?.deleted ?? checkedKeys.value.length;
    createMessage.success(`已删除 ${n} 人`);
    handleSuccess();
  } catch (e: any) {
    createMessage.error(e?.message || '批量删除失败');
  }
}

function getTableActions(record: FacePerson) {
  return [
    {
      icon: 'ant-design:eye-filled',
      tooltip: '查看',
      onClick: () => openPersonDetail(record),
    },
    {
      icon: 'ant-design:plus-circle-outlined',
      tooltip: '添加照片',
      onClick: () => handleAddPhoto(record),
    },
    {
      icon: 'material-symbols:delete-outline-rounded',
      tooltip: '删除',
      popConfirm: {
        title: '确定删除该人员？其全部人脸照片将一并删除。',
        confirm: () => handleDeletePerson(record),
      },
    },
  ];
}

onMounted(async () => {
  if (!libraryId.value || Number.isNaN(libraryId.value)) {
    createMessage.error('无效的人脸库 ID');
    goBack();
    return;
  }
  await loadLibrary();
  if (viewMode.value === 'card') {
    await loadPersons();
  } else {
    reload();
  }
});
</script>

<style lang="less" scoped>
.face-manage-page {
  min-height: 100%;
  background: #fff;
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

.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  width: 100%;
}

.list-title {
  padding-left: 7px;
  font-size: 16px;
  font-weight: 500;
  line-height: 24px;
  color: #181818;
}

@cover-height: 200px;
@body-height: 88px;

.person-card {
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

.person-card-cover {
  position: relative;
  height: @cover-height;
  cursor: pointer;
  background: #fafafa;
  overflow: hidden;
}

.person-card-cover-inner {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px;
}

.person-card-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.face-count-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 2;
  padding: 2px 8px;
  border-radius: 10px;
  background: rgba(38, 108, 251, 0.88);
  color: #fff;
  font-size: 12px;
  font-weight: 500;
}

.person-card-overlay {
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

.person-card-body {
  height: @body-height;
  padding: 14px 14px 10px;
  overflow: hidden;
}

.person-card-title {
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

.person-card-meta {
  margin: 0;
  font-size: 13px;
  color: #999;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
