<template>
  <div id="plate-library">
    <PlateModelSetupPanel
      v-if="!modelReady"
      :checking="!modelStatusChecked"
      :model-status="modelStatus"
      @ready="onModelPanelReady"
    />

    <template v-else>
      <!-- 表格模式 -->
      <BasicTable v-if="viewMode === 'table'" @register="registerTable">
        <template #toolbar>
          <Button type="primary" @click="handleCreate">新建车牌库</Button>
          <a-badge :count="pendingCount" :offset="[4, -2]">
            <Button type="default" preIcon="ant-design:appstore-outlined" @click="handleOpenWorkbench">
              待入库工作台
            </Button>
          </a-badge>
          <Button type="default" @click="handleToggleViewMode" preIcon="ant-design:swap-outlined">
            切换视图
          </Button>
        </template>
        <template #bodyCell="{ column, record }">
          <template v-if="column.dataIndex === 'business_tags'">
            <template v-if="record.business_tags?.length">
              <a-tag
                v-for="tag in record.business_tags"
                :key="tag"
                size="small"
                style="margin-bottom: 4px"
              >{{ tag }}</a-tag>
            </template>
            <span v-else class="text-muted">-</span>
          </template>
          <template v-else-if="column.dataIndex === 'is_enabled'">
            <a-switch :checked="record.is_enabled" @change="handleToggleEnabled(record)" />
          </template>
          <template v-else-if="column.dataIndex === 'action'">
            <TableAction :actions="getTableActions(record)" />
          </template>
        </template>
      </BasicTable>

      <!-- 卡片模式 -->
      <div v-else class="plate-library-card-list-wrapper p-2">
        <div class="p-4 bg-white" style="margin-bottom: 10px">
          <BasicForm @register="registerForm" @reset="handleSubmit" />
        </div>
        <div class="p-2 bg-white">
          <Spin :spinning="loading">
            <List
              :grid="{ gutter: 12, xs: 1, sm: 2, md: 3, lg: 4, xl: 4, xxl: 4 }"
              :data-source="libraryList"
              :pagination="paginationProp"
            >
              <template #header>
                <div
                  style="display: flex; align-items: center; justify-content: space-between; flex-direction: row"
                >
                  <span style="padding-left: 7px; font-size: 16px; font-weight: 500; line-height: 24px">车牌库列表</span>
                  <div style="display: flex; gap: 8px">
                    <Button type="primary" @click="handleCreate">新建车牌库</Button>
                    <a-badge :count="pendingCount" :offset="[4, -2]">
                      <Button
                        type="default"
                        preIcon="ant-design:appstore-outlined"
                        @click="handleOpenWorkbench"
                      >
                        待入库工作台
                      </Button>
                    </a-badge>
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
                <ListItem :class="item.is_enabled ? 'library-item normal' : 'library-item error'">
                  <div class="library-info">
                    <div class="status">{{ item.is_enabled ? '启用' : '停用' }}</div>
                    <div class="title o2" :title="item.name">{{ item.name }}</div>
                    <div class="props">
                      <div class="prop prop-code">
                        <div class="label">库编码</div>
                        <div class="value">{{ item.code || '--' }}</div>
                      </div>
                      <div class="prop prop-count">
                        <div class="label">车牌数量</div>
                        <div class="value">{{ item.plate_count ?? 0 }} 条</div>
                      </div>
                      <div v-if="item.auto_enroll_running" class="prop prop-auto">
                        <div class="label">自动录入</div>
                        <div class="value running-text">运行中</div>
                      </div>
                    </div>
                    <div class="btns">
                      <div class="btn" title="车牌管理" @click="handleManageEntries(item)">
                        <Icon icon="ant-design:car-outlined" :size="15" color="#3B82F6" />
                      </div>
                      <div class="btn" title="摄像头自动录入配置" @click="handleAutoEnroll(item)">
                        <Icon icon="ant-design:setting-outlined" :size="15" color="#3B82F6" />
                      </div>
                      <div
                        class="btn"
                        :class="{ 'btn-running': item.auto_enroll_running }"
                        :title="item.auto_enroll_running ? '关闭摄像头自动录入' : '开启摄像头自动录入'"
                        @click="handleToggleAutoEnroll(item, $event)"
                      >
                        <Icon
                          :icon="item.auto_enroll_running ? 'ant-design:video-camera-filled' : 'ant-design:video-camera-outlined'"
                          :size="15"
                          :color="item.auto_enroll_running ? '#DC2626' : '#3B82F6'"
                        />
                      </div>
                      <div class="btn" title="查看" @click="handleView(item)">
                        <Icon icon="ant-design:eye-filled" :size="15" color="#3B82F6" />
                      </div>
                      <div class="btn" title="编辑" @click="handleEdit(item)">
                        <Icon icon="ant-design:edit-filled" :size="15" color="#3B82F6" />
                      </div>
                      <div
                        class="btn"
                        :title="item.is_enabled ? '停用车牌库' : '启用车牌库'"
                        @click="handleToggleEnabled(item)"
                      >
                        <Icon
                          :icon="item.is_enabled ? 'ant-design:pause-circle-outlined' : 'ant-design:play-circle-outlined'"
                          :size="15"
                          color="#3B82F6"
                        />
                      </div>
                      <Popconfirm
                        title="确定删除此车牌库？库内所有车牌将一并删除。"
                        ok-text="是"
                        cancel-text="否"
                        @confirm="handleDelete(item)"
                      >
                        <div class="btn delete-btn" title="删除">
                          <Icon icon="material-symbols:delete-outline-rounded" :size="15" color="#DC2626" />
                        </div>
                      </Popconfirm>
                    </div>
                  </div>
                  <div class="library-img" @click="handleManageEntries(item)">
                    <img :src="PLATE_LIBRARY_IMAGE" alt="" class="img" />
                  </div>
                </ListItem>
              </template>
            </List>
          </Spin>
        </div>
      </div>

      <PlateLibraryModal @register="registerLibraryModal" @success="handleSuccess" />
      <PlateAutoEnrollDrawer @register="registerAutoEnrollDrawer" @success="handleSuccess" />
      <PlatePendingWorkbench @register="registerWorkbench" @stats-change="onWorkbenchStatsChange" />
    </template>
  </div>
</template>

<script lang="ts" setup>
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { List, Modal, Popconfirm, Spin } from 'ant-design-vue';
import { BasicForm, useForm } from '@/components/Form';
import { BasicTable, TableAction, useTable } from '@/components/Table';
import { useDrawer } from '@/components/Drawer';
import { useMessage } from '@/hooks/web/useMessage';
import { Icon } from '@/components/Icon';
import {
  deletePlateLibrary,
  getPlateModelStatus,
  isAutoEnrollConfigError,
  listPlateLibraries,
  parsePlateApiError,
  startPlateAutoEnroll,
  stopPlateAutoEnroll,
  updatePlateLibrary,
  type PlateLibrary,
  type PlateModelStatus,
} from '@/api/device/plate_library';
import { getBasicColumns, getFormConfig } from './Data';
import PlateLibraryModal from './PlateLibraryModal.vue';
import PlateAutoEnrollDrawer from './PlateAutoEnrollDrawer.vue';
import PlateModelSetupPanel from './PlateModelSetupPanel.vue';
import PlatePendingWorkbench from '../PendingEnroll/PlatePendingWorkbench.vue';
import { getPendingStats, type PendingEnrollStats } from '@/api/device/pending_enroll';
import PLATE_LIBRARY_IMAGE from '@/assets/images/video/snap-task.png';
import { Button } from '@/components/Button'
const ListItem = List.Item;

defineOptions({ name: 'PlateLibrary' });

const { createMessage } = useMessage();
const router = useRouter();
const [registerLibraryModal, { openDrawer: openLibraryDrawer }] = useDrawer();
const [registerAutoEnrollDrawer, { openDrawer: openAutoEnrollDrawer }] = useDrawer();
const [registerWorkbench, { openDrawer: openWorkbench }] = useDrawer();

const pendingCount = ref(0);

async function refreshPendingStats() {
  try {
    const res = await getPendingStats('plate');
    pendingCount.value = res?.data?.pending ?? 0;
  } catch (e) {
    console.warn('查询待入库统计失败', e);
  }
}

function handleOpenWorkbench() {
  // 本项目 useDrawerInner 回调由 data 触发（见 useDrawer.ts watchEffect），必须携带 payload 才会执行加载
  openWorkbench(true, { openedAt: Date.now() });
}

function onWorkbenchStatsChange(stats: PendingEnrollStats) {
  pendingCount.value = stats?.pending ?? 0;
}

const viewMode = ref<'table' | 'card'>('card');
const libraryList = ref<PlateLibrary[]>([]);
const allLibraries = ref<PlateLibrary[]>([]);
const loading = ref(false);
const autoEnrollTogglingId = ref<number | null>(null);

const modelStatusChecked = ref(false);
const modelStatus = ref<PlateModelStatus | null>(null);
const modelReady = computed(() => !!modelStatus.value?.exists);

const page = ref(1);
const pageSize = ref(8);
const searchParams = ref<{ search?: string; is_enabled?: number | string }>({});

const filteredLibraries = computed(() => {
  let list = allLibraries.value;
  const { search, is_enabled } = searchParams.value;
  if (search?.trim()) {
    const kw = search.trim().toLowerCase();
    list = list.filter(
      (item) =>
        item.name?.toLowerCase().includes(kw) || item.code?.toLowerCase().includes(kw),
    );
  }
  if (is_enabled !== undefined && is_enabled !== '') {
    const enabled = is_enabled === 1 || is_enabled === '1';
    list = list.filter((item) => item.is_enabled === enabled);
  }
  return list;
});

const total = computed(() => filteredLibraries.value.length);

const paginationProp = computed(() => ({
  showSizeChanger: false,
  showQuickJumper: true,
  pageSize: pageSize.value,
  current: page.value,
  total: total.value,
  showTotal: (t: number) => `总 ${t} 条`,
  onChange: (p: number, pz: number) => {
    page.value = p;
    pageSize.value = pz;
    syncPagedList();
  },
  onShowSizeChange: (_current: number, size: number) => {
    pageSize.value = size;
    page.value = 1;
    syncPagedList();
  },
}));

function syncPagedList() {
  const start = (page.value - 1) * pageSize.value;
  libraryList.value = filteredLibraries.value.slice(start, start + pageSize.value);
}

const [registerTable, { reload }] = useTable({
  title: '车牌库列表',
  api: async (params) => {
    const response = await listPlateLibraries({
      search: params.search || undefined,
      is_enabled:
        params.is_enabled === '' || params.is_enabled === undefined
          ? undefined
          : params.is_enabled === 1 || params.is_enabled === '1',
    });
    return {
      items: response.data || [],
      total: response.total || (response.data?.length ?? 0),
    };
  },
  beforeFetch: (params) => {
    let is_enabled: boolean | undefined;
    if (params.is_enabled !== '' && params.is_enabled !== undefined) {
      is_enabled = params.is_enabled === 1 || params.is_enabled === '1';
    }
    return {
      search: params.search || undefined,
      is_enabled,
    };
  },
  columns: getBasicColumns(),
  useSearchForm: true,
  formConfig: getFormConfig(),
  pagination: true,
  rowKey: 'id',
  fetchSetting: {
    listField: 'items',
    totalField: 'total',
  },
});

async function refreshModelStatus() {
  try {
    const res = await getPlateModelStatus();
    if (res?.data) {
      modelStatus.value = res.data;
    }
  } catch (error: unknown) {
    console.warn('查询车牌模型状态失败', error);
  } finally {
    modelStatusChecked.value = true;
  }
}

function onModelPanelReady() {
  modelStatus.value = { ...modelStatus.value, exists: true } as PlateModelStatus;
  if (viewMode.value === 'card') {
    loadLibraryList();
  }
}

async function loadLibraryList() {
  loading.value = true;
  try {
    const response = await listPlateLibraries({});
    if (response.code === 0) {
      allLibraries.value = response.data || [];
      syncPagedList();
    } else {
      createMessage.error(response.msg || '加载车牌库列表失败');
      allLibraries.value = [];
      libraryList.value = [];
    }
  } catch {
    createMessage.error('加载车牌库列表失败');
    allLibraries.value = [];
    libraryList.value = [];
  } finally {
    loading.value = false;
  }
}

async function handleSubmit() {
  const params = await validate();
  searchParams.value = params || {};
  page.value = 1;
  if (viewMode.value === 'card') {
    syncPagedList();
  } else {
    reload();
  }
}

const [registerForm, { validate }] = useForm({
  ...getFormConfig(),
  autoSubmitOnEnter: true,
  submitFunc: handleSubmit,
});

function handleToggleViewMode() {
  viewMode.value = viewMode.value === 'table' ? 'card' : 'table';
  if (viewMode.value === 'card') loadLibraryList();
}

function handleCreate() {
  openLibraryDrawer(true, { type: 'create' });
}

function handleView(record: PlateLibrary) {
  openLibraryDrawer(true, { type: 'view', record });
}

function handleEdit(record: PlateLibrary) {
  openLibraryDrawer(true, { type: 'edit', record });
}

function handleManageEntries(record: PlateLibrary) {
  router.push({ name: 'PlateManage', params: { libraryId: record.id } });
}

function handleAutoEnroll(record: PlateLibrary) {
  openAutoEnrollDrawer(true, { library: record });
}

async function handleToggleAutoEnroll(record: PlateLibrary, e?: Event) {
  e?.stopPropagation();
  if (autoEnrollTogglingId.value === record.id) return;
  const running = !!record.auto_enroll_running;
  autoEnrollTogglingId.value = record.id;
  try {
    if (running) {
      await stopPlateAutoEnroll(record.id);
      createMessage.success('已关闭摄像头自动录入');
    } else {
      await startPlateAutoEnroll(record.id);
      createMessage.success('已开启摄像头自动录入');
    }
    handleSuccess();
  } catch (error: unknown) {
    if (!running && isAutoEnrollConfigError(error)) {
      Modal.confirm({
        title: '请先完成摄像头配置',
        content:
          '开启摄像头自动录入前，请至少绑定一个摄像头并保存配置。保存后即可一键开启。',
        okText: '前往配置',
        cancelText: '知道了',
        onOk: () => openAutoEnrollDrawer(true, { library: record }),
      });
      return;
    }
    createMessage.error(
      parsePlateApiError(error, running ? '关闭摄像头自动录入失败' : '开启摄像头自动录入失败'),
    );
  } finally {
    autoEnrollTogglingId.value = null;
  }
}

async function handleDelete(record: PlateLibrary) {
  try {
    await deletePlateLibrary(record.id);
    createMessage.success('删除成功');
    handleSuccess();
  } catch (error: unknown) {
    createMessage.error(parsePlateApiError(error, '删除失败'));
  }
}

async function handleToggleEnabled(record: PlateLibrary) {
  try {
    await updatePlateLibrary(record.id, { is_enabled: !record.is_enabled });
    createMessage.success(record.is_enabled ? '已停用' : '已启用');
    handleSuccess();
  } catch (error: unknown) {
    createMessage.error(parsePlateApiError(error, '操作失败'));
  }
}

function getTableActions(record: PlateLibrary) {
  return [
    {
      icon: 'ant-design:car-outlined',
      tooltip: '车牌管理',
      onClick: () => handleManageEntries(record),
    },
    {
      icon: 'ant-design:setting-outlined',
      tooltip: '摄像头自动录入配置',
      onClick: () => handleAutoEnroll(record),
    },
    {
      icon: record.auto_enroll_running
        ? 'ant-design:video-camera-filled'
        : 'ant-design:video-camera-outlined',
      tooltip: record.auto_enroll_running ? '关闭摄像头自动录入' : '开启摄像头自动录入',
      onClick: () => handleToggleAutoEnroll(record),
    },
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
        title: '确定删除此车牌库？库内所有车牌将一并删除。',
        confirm: () => handleDelete(record),
      },
    },
  ];
}

function handleSuccess() {
  if (viewMode.value === 'table') {
    reload();
  } else {
    loadLibraryList();
  }
}

defineExpose({ refresh: handleSuccess });

onMounted(async () => {
  await refreshModelStatus();
  if (modelReady.value && viewMode.value === 'card') {
    loadLibraryList();
  }
  if (modelReady.value) {
    void refreshPendingStats();
  }
});
</script>

<style scoped lang="less">
#plate-library {
  .text-muted {
    color: rgba(0, 0, 0, 0.25);
  }
}

.plate-library-card-list-wrapper {
  :deep(.ant-list-header) {
    border-block-end: 0;
    padding-top: 0;
    padding-bottom: 8px;
  }
  :deep(.ant-list) {
    padding: 6px;
  }
  :deep(.ant-list-item) {
    margin: 6px;
  }
  :deep(.library-item) {
    overflow: hidden;
    box-shadow: 0 0 4px #00000026;
    border-radius: 8px;
    padding: 16px 0;
    position: relative;
    background-color: #fff;
    background-repeat: no-repeat;
    background-position: center center;
    background-size: 104% 104%;
    transition: all 0.5s;
    min-height: 208px;
    height: 100%;

    &.normal {
      background-image: url('@/assets/images/product/blue-bg.719b437a.png');

      .library-info .status {
        background: #d9dffd;
        color: #266cfbff;
      }
    }

    &.error {
      background-image: url('@/assets/images/product/red-bg.101af5ac.png');

      .library-info .status {
        background: #fad7d9;
        color: #d43030;
      }
    }

    .library-info {
      flex-direction: column;
      max-width: calc(100% - 128px);
      padding-left: 16px;

      .status {
        min-width: 90px;
        height: 25px;
        border-radius: 6px 0 0 6px;
        font-size: 12px;
        font-weight: 500;
        line-height: 25px;
        text-align: center;
        position: absolute;
        right: 0;
        top: 16px;
        padding: 0 8px;
        white-space: nowrap;
      }

      .title {
        font-size: 16px;
        font-weight: 600;
        color: #050708;
        line-height: 20px;
        height: 40px;
        padding-right: 90px;
      }

      .props {
        margin-top: 10px;
        display: grid;
        grid-template-columns: auto 1fr;
        column-gap: 32px;
        row-gap: 10px;

        .prop {
          margin-bottom: 0;
          min-width: 0;

          .label {
            font-size: 12px;
            font-weight: 400;
            color: #666;
            line-height: 14px;
          }

          .value {
            font-size: 14px;
            font-weight: 600;
            color: #050708;
            line-height: 14px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            margin-top: 6px;
          }

          .running-text {
            color: #dc2626;
          }
        }

        .prop-code .value {
          overflow: visible;
          text-overflow: unset;
        }
      }

      .btns {
        display: flex;
        position: absolute;
        left: 16px;
        bottom: 16px;
        margin-top: 20px;
        width: 280px;
        height: 28px;
        border-radius: 45px;
        justify-content: space-around;
        padding: 0 10px;
        align-items: center;
        border: 2px solid #266cfbff;

        .btn {
          width: 28px;
          text-align: center;
          position: relative;
          cursor: pointer;

          &:before {
            content: '';
            display: block;
            position: absolute;
            width: 1px;
            height: 7px;
            background-color: #e2e2e2;
            left: 0;
            top: 9px;
          }

          &:first-child:before {
            display: none;
          }

          :deep(.anticon) {
            display: flex;
            align-items: center;
            justify-content: center;
            color: #3b82f6;
            transition: color 0.3s;
          }

          &:hover :deep(.anticon) {
            color: #5ba3f5;
          }

          &.delete-btn {
            :deep(.anticon) {
              color: #dc2626;
            }

            &:hover :deep(.anticon) {
              color: #dc2626;
            }
          }

          &.btn-running :deep(.anticon) {
            color: #dc2626;
          }
        }
      }
    }

    .library-img {
      position: absolute;
      right: 20px;
      top: 50px;

      img {
        cursor: pointer;
        width: 120px;
      }
    }
  }
}
</style>
