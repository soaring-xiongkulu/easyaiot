<template>
  <BasicDrawer
    v-bind="$attrs"
    @register="register"
    width="1400"
    placement="right"
    :showFooter="false"
    :destroyOnClose="true"
  >
    <!-- 库信息摘要 -->
    <div class="library-summary" v-if="library">
      <div class="stat-item">
        <span class="stat-value">{{ library.face_count ?? entries.length }}</span>
        <span class="stat-label">已录入人脸</span>
      </div>
      <div class="stat-divider" />
      <div class="stat-item">
        <span class="stat-value">{{ library.code }}</span>
        <span class="stat-label">库编号</span>
      </div>
      <div class="stat-divider" />
      <div class="stat-item">
        <span class="stat-value">{{ formatThreshold(library.similarity_threshold) }}</span>
        <span class="stat-label">相似度阈值</span>
      </div>
      <div class="stat-divider" />
      <div class="stat-item">
        <a-tag :color="library.is_enabled ? 'green' : 'default'">
          {{ library.is_enabled ? '已启用' : '已停用' }}
        </a-tag>
        <span class="stat-label">库状态</span>
      </div>
    </div>

    <!-- 工具栏 -->
    <div class="entry-toolbar">
      <a-input-search
        v-if="viewMode === 'card'"
        v-model:value="searchText"
        placeholder="搜索姓名 / 编号"
        allow-clear
        style="width: 240px"
        @search="loadEntries"
      />
      <div class="toolbar-actions">
        <Button type="primary" @click="handleAdd">
          <template #icon><PlusOutlined /></template>
          录入人脸
        </Button>
        <Button @click="handleToggleViewMode">
          <template #icon><SwapOutlined /></template>
          {{ viewMode === 'card' ? '表格视图' : '卡片视图' }}
        </Button>
        <Button @click="handleNormalize">
          <template #icon><MergeCellsOutlined /></template>
          人脸归一化
        </Button>
      </div>
    </div>

    <!-- 表格模式 -->
    <BasicTable v-if="viewMode === 'table'" @register="registerTable">
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'image_url'">
          <a-avatar :size="48" :src="faceImageUrl(record.image_url)" shape="square">
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
    <div v-else class="entry-card-list">
      <a-spin :spinning="loading">
        <a-row :gutter="[16, 16]">
          <a-col :xs="12" :sm="8" :md="6" :lg="4" :xl="3" v-for="item in filteredEntries" :key="item.id">
            <a-card :hoverable="true" class="entry-card" :class="{ disabled: !item.is_enabled }">
              <div class="entry-avatar" @click="handleView(item)">
                <a-image
                  v-if="item.image_url"
                  :src="faceImageUrl(item.image_url)"
                  :width="100"
                  :height="100"
                  style="object-fit: cover; border-radius: 8px; cursor: pointer"
                  :preview="{ mask: '预览' }"
                  :fallback="fallbackImg"
                />
                <a-avatar v-else :size="100" shape="square">
                  <template #icon><UserOutlined style="font-size: 40px" /></template>
                </a-avatar>
                <a-tag class="status-tag" :color="item.is_enabled ? 'green' : 'default'" size="small">
                  {{ item.is_enabled ? '启用' : '停用' }}
                </a-tag>
              </div>
              <div class="entry-info">
                <div class="person-name" :title="item.person_name">{{ item.person_name }}</div>
                <div class="person-code" v-if="item.person_code">{{ item.person_code }}</div>
              </div>
              <div class="entry-actions">
                <a-tooltip title="编辑">
                  <Button type="text" size="small" @click="handleEdit(item)">
                    <EditOutlined />
                  </Button>
                </a-tooltip>
                <PopConfirmButton
                  type="text"
                  size="small"
                  danger
                  title="确认删除该人脸？"
                  @confirm="handleDelete(item.id)"
                >
                  <a-tooltip title="删除">
                    <DeleteOutlined />
                  </a-tooltip>
                </PopConfirmButton>
              </div>
            </a-card>
          </a-col>
        </a-row>
        <a-empty
          v-if="!loading && filteredEntries.length === 0"
          :description="searchText ? '未找到匹配的人脸' : '暂无人脸，点击「录入人脸」开始添加'"
        />
      </a-spin>
    </div>

    <FaceEntryModal @register="registerEntryModal" @success="handleEntrySuccess" />
    <FaceNormalizeModal @register="registerNormalizeModal" @success="handleNormalizeSuccess" />
  </BasicDrawer>
</template>

<script lang="ts" setup>
import { computed, ref } from 'vue';
import {
  DeleteOutlined,
  EditOutlined,
  MergeCellsOutlined,
  PlusOutlined,
  SwapOutlined,
  UserOutlined,
} from '@ant-design/icons-vue';
import { BasicDrawer, useDrawer, useDrawerInner } from '@/components/Drawer';
import { useModal } from '@/components/Modal';
import { BasicTable, TableAction, useTable } from '@/components/Table';
import { useMessage } from '@/hooks/web/useMessage';
import {
  deleteFaceEntry,
  listFaceEntries,
  resolveFaceImageDisplayUrl,
  type FaceEntry,
  type FaceLibrary,
} from '@/api/device/face_library';
import { getEntryColumns } from './Data';
import FaceEntryModal from './FaceEntryModal.vue';
import FaceNormalizeModal from './FaceNormalizeModal.vue';
import {
  Avatar as AAvatar,
  Card as ACard,
  Col as ACol,
  Empty as AEmpty,
  Image as AImage,
  InputSearch as AInputSearch,
  Row as ARow,
  Spin as ASpin,
  Tag as ATag,
  Tooltip as ATooltip,
} from 'ant-design-vue';
import { Button, PopConfirmButton } from '@/components/Button'
defineOptions({ name: 'FaceEntryDrawer' });

const emit = defineEmits(['success', 'register']);
const { createMessage } = useMessage();

const library = ref<FaceLibrary | null>(null);
const loading = ref(false);
const entries = ref<FaceEntry[]>([]);
const viewMode = ref<'table' | 'card'>('card');
const searchText = ref('');
const [registerEntryModal, { openDrawer: openEntryModal }] = useDrawer();
const [registerNormalizeModal, { openModal: openNormalizeModal }] = useModal();

const fallbackImg =
  'data:image/svg+xml,' +
  encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><rect fill="#f0f0f0" width="100" height="100"/></svg>');

function faceImageUrl(url?: string | null) {
  return resolveFaceImageDisplayUrl(url);
}

const DRAWER_WIDTH = 1400;

function syncDrawerHeader(lib: FaceLibrary | null) {
  setDrawerProps({
    title: `人脸管理 · ${lib?.name || ''}`,
    width: DRAWER_WIDTH,
  });
}

const filteredEntries = computed(() => {
  const kw = searchText.value.trim().toLowerCase();
  if (!kw) return entries.value;
  return entries.value.filter(
    (e) =>
      e.person_name?.toLowerCase().includes(kw) ||
      e.person_code?.toLowerCase().includes(kw),
  );
});

function formatThreshold(val?: number) {
  return val != null ? Number(val).toFixed(2) : '-';
}

const [registerTable, { reload, setProps }] = useTable({
  title: '',
  api: async (params) => {
    if (!library.value?.id) return { items: [], total: 0 };
    const response = await listFaceEntries(library.value.id, {
      search: params.search || undefined,
    });
    const data = response.data || [];
    entries.value = data;
    return { items: data, total: response.total ?? data.length };
  },
  columns: getEntryColumns(),
  useSearchForm: true,
  formConfig: {
    labelWidth: 70,
    schemas: [
      {
        field: 'search',
        label: '搜索',
        component: 'Input',
        componentProps: {
          placeholder: '姓名 / 编号',
        },
      },
    ],
  },
  pagination: false,
  rowKey: 'id',
  immediate: false,
  fetchSetting: {
    listField: 'items',
    totalField: 'total',
  },
});

const [register, { setDrawerProps }] = useDrawerInner(async (data) => {
  const lib = data?.library || null;
  library.value = lib;
  entries.value = [];
  searchText.value = '';
  viewMode.value = 'card';
  syncDrawerHeader(lib);
  await loadEntries();
  if (library.value?.id) {
    setProps({
      api: async (params) => {
        const response = await listFaceEntries(library.value!.id, {
          search: params.search || undefined,
        });
        const list = response.data || [];
        entries.value = list;
        return { items: list, total: response.total ?? list.length };
      },
    });
  }
});

async function loadEntries() {
  if (!library.value?.id) return;
  loading.value = true;
  try {
    const res = await listFaceEntries(library.value.id, {
      search: searchText.value || undefined,
    });
    entries.value = Array.isArray(res?.data) ? res.data : [];
  } catch (e: any) {
    createMessage.error(e?.message || '加载人脸列表失败');
    entries.value = [];
  } finally {
    loading.value = false;
  }
}

function handleToggleViewMode() {
  viewMode.value = viewMode.value === 'table' ? 'card' : 'table';
  if (viewMode.value === 'table') reload();
  else loadEntries();
}

function handleAdd() {
  openEntryModal(true, { type: 'create', library: library.value });
}

function handleNormalize() {
  openNormalizeModal(true, { library: library.value });
}

function handleNormalizeSuccess() {
  handleEntrySuccess();
}

function handleView(record: FaceEntry) {
  openEntryModal(true, { type: 'view', library: library.value, record });
}

function handleEdit(record: FaceEntry) {
  openEntryModal(true, { type: 'edit', library: library.value, record });
}

async function handleDelete(entryId: number) {
  try {
    await deleteFaceEntry(entryId);
    createMessage.success('删除成功');
    handleEntrySuccess();
  } catch (e: any) {
    createMessage.error(e?.message || '删除失败');
  }
}

function getTableActions(record: FaceEntry) {
  return [
    {
      icon: 'ant-design:eye-filled',
      tooltip: '查看',
      onClick: () => handleView(record),
    },
    {
      icon: 'ant-design:edit-filled',
      tooltip: '编辑',
      onClick: () => handleEdit(record),
    },
    {
      icon: 'material-symbols:delete-outline-rounded',
      tooltip: '删除',
      popConfirm: {
        title: '确认删除该人脸？',
        confirm: () => handleDelete(record.id),
      },
    },
  ];
}

function handleEntrySuccess() {
  if (viewMode.value === 'table') reload();
  else loadEntries();
  emit('success');
}

defineExpose({ refresh: loadEntries });
</script>

<style lang="less" scoped>
.library-summary {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 16px 20px;
  margin-bottom: 16px;
  background: #fafafa;
  border-radius: 8px;
  border: 1px solid #f0f0f0;

  .stat-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;

    .stat-value {
      font-size: 18px;
      font-weight: 600;
      color: rgba(0, 0, 0, 0.85);
    }

    .stat-label {
      font-size: 12px;
      color: rgba(0, 0, 0, 0.45);
    }
  }

  .stat-divider {
    width: 1px;
    height: 36px;
    background: #e8e8e8;
  }
}

.entry-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;

  .toolbar-actions {
    display: flex;
    gap: 8px;
    margin-left: auto;
  }
}

.entry-card-list {
  min-height: 200px;

  .entry-card {
    text-align: center;
    transition: box-shadow 0.2s;

    &.disabled {
      opacity: 0.6;
    }

    &:hover {
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }

    .entry-avatar {
      position: relative;
      display: flex;
      justify-content: center;
      margin-bottom: 10px;

      .status-tag {
        position: absolute;
        top: 2px;
        right: 2px;
      }
    }

    .entry-info {
      margin-bottom: 4px;

      .person-name {
        font-size: 14px;
        font-weight: 600;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .person-code {
        font-size: 12px;
        color: rgba(0, 0, 0, 0.45);
        margin-top: 2px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
    }

    .entry-actions {
      display: flex;
      justify-content: center;
      gap: 4px;
      border-top: 1px solid #f0f0f0;
      padding-top: 6px;
      margin-top: 6px;
    }
  }
}
</style>
