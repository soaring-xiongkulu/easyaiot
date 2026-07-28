<template>
  <div id="train-task-list" class="train-container bg-white p-6 rounded-xl shadow-lg transition-all duration-300">
    <!-- 表格模式 -->
    <BasicTable
      v-if="viewMode === 'table'"
      @register="registerTable"
      class="rounded-xl overflow-hidden border border-gray-100 shadow-sm"
    >
      <template #toolbar>
        <div class="toolbar-buttons">
          <Button type="primary" @click="openTrainDrawer(true, {})">
            <Icon icon="ant-design:plus-circle-outlined"/>
            启动新训练
          </Button>
          <Button type="default" @click="handleToggleViewMode">
            <template #icon>
              <SwapOutlined />
            </template>
            切换视图
          </Button>
        </div>
      </template>
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'action'">
          <TableAction
            :actions="getTableActions(record)"
            :action-style="{
              display: 'flex',
              flexWrap: 'nowrap',
              gap: '4px',
              alignItems: 'center',
              marginRight: '0'
            }"
          />
        </template>
      </template>
    </BasicTable>

    <!-- 卡片模式 -->
    <div v-else>
      <TrainTaskCardList
        :params="params"
        :api="getTrainTaskListApi"
        @get-method="getMethod"
        @view-logs="handleOpenTrainLogsModal"
        @view-results="handleViewTrainResults"
        @download="handleDownloadWeights"
        @stop="handleStopTrain"
        @resume="handleResume"
        @retrain="handleRetrain"
        @delete="handleCardDelete"
        @publish="handlePublishTrainModel"
      >
        <template #header>
          <Button type="primary" @click="openTrainDrawer(true, {})">
            <Icon icon="ant-design:plus-circle-outlined"/>
            启动新训练
          </Button>
          <Button type="default" @click="handleToggleViewMode">
            <template #icon>
              <SwapOutlined />
            </template>
            切换视图
          </Button>
        </template>
      </TrainTaskCardList>
    </div>

    <StartTrainModal @register="registerAddModel" @success="handleStartTrain"/>
    <TrainLogsModal
      v-if="showLogsModal"
      @register="registerTrainLogsModal"
      @success="handleSuccess"
      @close="handleLogsModalClose"
    />
    <PublishTrainModelModal
      @register="registerPublishModal"
      @success="handlePublishSuccess"
    />

    <a-modal
      v-model:visible="showResultsModal"
      title="训练结果"
      :footer="null"
      width="80%"
      @afterClose="revokeResultsBlobUrl"
    >
      <img
        v-if="currentImageUrl && !resultsImageError"
        :src="currentImageUrl"
        style="width: 100%"
        alt="训练结果"
        @error="resultsImageError = true"
      />
      <div v-else class="text-center py-8">
        <a-empty :description="resultsImageError ? '训练结果图片加载失败' : '暂无训练结果图片'"/>
      </div>
    </a-modal>
  </div>
</template>

<script lang="ts" setup>
import {computed, nextTick, onUnmounted, ref, watch} from 'vue';
import {SwapOutlined} from '@ant-design/icons-vue';
import {BasicTable, TableAction, useTable} from '@/components/Table';
import {useMessage} from '@/hooks/web/useMessage';
import {useDrawer} from '@/components/Drawer';
import {useModal} from '@/components/Modal';
import {deleteTrainTask, getTrainTaskPage, startTrain, stopTrain} from '@/api/device/train';
import {getDatasetPage} from '@/api/device/dataset';
import StartTrainModal from '@/views/train/components/StartTrainTaskModal/index.vue';
import TrainLogsModal from '@/views/train/components/TrainTaskLogsModal/index.vue';
import TrainTaskCardList from '@/views/train/components/TrainTaskCardList/index.vue';
import PublishTrainModelModal from '@/views/train/components/PublishTrainModelModal/index.vue';
import {getBasicColumns, getFormConfig} from './Data';
import {canPublishTrainTask, canResumeTrainTask, canRetrainTrainTask, getPublishedModelId, buildTrainTaskDisplayName, isLegacyBadDatasetName, isTrainTaskActive, resolveTaskBaseNameFromRecord} from './trainTaskUtils';
import {Empty as AEmpty, Modal as AModal} from 'ant-design-vue';
import {Icon} from '@/components/Icon';
import {resolveTrainResultsDisplayUrl} from '@/utils/alertMinioImage';
import { Button } from '@/components/Button'
defineOptions({name: 'TrainTaskList'});

const props = withDefaults(defineProps<{
  /** 模型训练 Tab 是否处于激活状态 */
  tabActive?: boolean;
  autoOpen?: boolean;
  initialDatasetId?: string;
}>(), {
  tabActive: true,
  autoOpen: false,
  initialDatasetId: undefined,
});

const {createMessage} = useMessage();

const POLL_INTERVAL_MS = 10_000;
const ACTION_REFRESH_DELAY_MS = 2_000;

const viewMode = ref<'table' | 'card'>('card');
const params = {};
const latestRecords = ref<Record<string, unknown>[]>([]);
let cardListReload: (opts?: { silent?: boolean }) => void = () => {};
let pollTimer: ReturnType<typeof setInterval> | null = null;
let actionRefreshTimer: ReturnType<typeof setTimeout> | null = null;

const hasActiveTrainingTasks = computed(() =>
  latestRecords.value.some((record) => isTrainTaskActive(String(record.status))),
);

const showLogsModal = ref(false);
const showResultsModal = ref(false);
const currentImageUrl = ref('');
const resultsImageError = ref(false);
let resultsBlobUrl: string | null = null;

const [registerAddModel, {openDrawer: openTrainDrawer}] = useDrawer();
const [registerTrainLogsModal, {openModal: openTrainLogsModal}] = useModal();
const [registerPublishModal, {openModal: openPublishModal}] = useModal();
const initialLaunchHandled = ref(false);

watch(
  () => [props.tabActive, props.autoOpen, props.initialDatasetId] as const,
  ([tabActive, autoOpen, datasetId]) => {
    if (!tabActive || !autoOpen || !datasetId || initialLaunchHandled.value) {
      return;
    }
    initialLaunchHandled.value = true;
    nextTick(() => openTrainDrawer(true, {datasetId}));
  },
  {immediate: true},
);

function getMethod(m: () => void) {
  cardListReload = m;
}

function handleToggleViewMode() {
  viewMode.value = viewMode.value === 'table' ? 'card' : 'table';
  if (viewMode.value === 'card') {
    cardListReload();
  }
}

function updateLatestRecords(records: unknown) {
  latestRecords.value = Array.isArray(records) ? records as Record<string, unknown>[] : [];
}

async function refreshList(opts?: { silent?: boolean }) {
  if (viewMode.value === 'table') {
    await reload();
    return;
  }
  await cardListReload(opts);
}

function stopAutoRefresh() {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

function syncAutoRefresh() {
  stopAutoRefresh();
  if (!props.tabActive || !hasActiveTrainingTasks.value) {
    return;
  }
  pollTimer = setInterval(() => {
    if (!props.tabActive) {
      stopAutoRefresh();
      return;
    }
    void refreshList({silent: true}).then(() => {
      if (!hasActiveTrainingTasks.value) {
        stopAutoRefresh();
      }
    });
  }, POLL_INTERVAL_MS);
}

function scheduleActionRefresh() {
  if (actionRefreshTimer) {
    clearTimeout(actionRefreshTimer);
  }
  actionRefreshTimer = setTimeout(() => {
    actionRefreshTimer = null;
    void refreshList({silent: true}).then(() => syncAutoRefresh());
  }, ACTION_REFRESH_DELAY_MS);
}

async function handleSuccess() {
  await refreshList();
  syncAutoRefresh();
  scheduleActionRefresh();
}

let datasetUrlMap: Record<string, { name: string; version: string }> | null = null;

async function ensureDatasetUrlMap() {
  if (datasetUrlMap) return;
  try {
    const res = await getDatasetPage({page: 1, size: 500});
    const list = res?.data?.list || res?.data || [];
    datasetUrlMap = {};
    for (const item of list) {
      if (item.zipUrl) {
        datasetUrlMap[item.zipUrl] = {
          name: item.name || '',
          version: item.version || '',
        };
      }
    }
  } catch {
    datasetUrlMap = {};
  }
}

function enrichTrainTaskRecords(records: Record<string, unknown>[]) {
  if (!records?.length) return;
  for (const record of records) {
    if (!record.dataset_name || isLegacyBadDatasetName(String(record.dataset_name))) {
      const matched = datasetUrlMap?.[record.dataset_path as string];
      if (matched?.name) {
        record.dataset_name = matched.name;
        record.dataset_version = matched.version;
      }
    }

    const displayName = (record.name as string) || '';
    const taskId = record.id as number;
    const dsName = (record.dataset_name as string) || '';
    const dsVersion = (record.dataset_version as string) || '';
    const expectedName = buildTrainTaskDisplayName(
      resolveTaskBaseNameFromRecord(record),
      dsName,
      dsVersion,
      taskId,
    );
    const needsRename =
      !displayName ||
      displayName.includes('训练任务') ||
      displayName === '未命名任务' ||
      displayName.startsWith('train_task_') ||
      displayName !== expectedName;

    if (needsRename) {
      record.name = expectedName;
    }
  }
}

function buildRequestParams(params: Record<string, unknown>) {
  const requestParams = {...params};
  if (requestParams.timeRange && Array.isArray(requestParams.timeRange) && requestParams.timeRange.length === 2) {
    requestParams.startTimeFrom = requestParams.timeRange[0];
    requestParams.startTimeTo = requestParams.timeRange[1];
    delete requestParams.timeRange;
  }
  if (requestParams.model_name) {
    requestParams.task_name = requestParams.model_name;
    delete requestParams.model_name;
  }
  if (requestParams.task_name === '') {
    delete requestParams.task_name;
  }
  if (requestParams.progress_filter === '') {
    delete requestParams.progress_filter;
  }
  return requestParams;
}

async function fetchTrainTasks(params: Record<string, unknown>) {
  await ensureDatasetUrlMap();
  const result = await getTrainTaskPage(buildRequestParams(params));
  const records = result?.data ?? result?.list ?? [];
  if (Array.isArray(records)) {
    enrichTrainTaskRecords(records);
    updateLatestRecords(records);
  } else {
    updateLatestRecords([]);
  }
  return result;
}

const getTrainTaskListApi = async (queryParams: Record<string, unknown>) => {
  const result = await fetchTrainTasks(queryParams);
  return {
    data: result?.data ?? result?.list ?? [],
    total: result?.total ?? 0,
  };
};

const getTableActions = (record: Record<string, unknown>) => {
  const actions = [
    {
      icon: 'mdi:file-document-outline',
      tooltip: {title: '查看日志', placement: 'top'},
      onClick: () => handleOpenTrainLogsModal(record),
      style: 'color: #1890ff; padding: 0 8px; font-size: 16px;',
    },
    {
      icon: 'mdi:image-outline',
      tooltip: {title: '查看训练结果', placement: 'top'},
      onClick: () => handleViewTrainResults(record),
      style: 'color: #1890ff; padding: 0 8px; font-size: 16px;',
    },
  ];

  if (isTrainTaskActive(String(record.status))) {
    actions.push({
      icon: 'ant-design:pause-circle-outlined',
      tooltip: {title: '停止训练', placement: 'top'},
      popConfirm: {
        placement: 'topRight',
        title: '确定停止此训练任务? 停止后可从断点继续训练。',
        confirm: () => handleStopTrain(record),
      },
      style: 'color: #faad14; padding: 0 8px; font-size: 16px;',
    });
  }

  if (canResumeTrainTask(record as { status?: string; can_resume?: boolean; checkpoint_dir?: string })) {
    actions.push({
      icon: 'mdi:play-circle-outline',
      tooltip: {title: '继续训练', placement: 'top'},
      onClick: () => handleResume(record),
      style: 'color: #52c41a; padding: 0 8px; font-size: 16px;',
    });
  }

  if (canRetrainTrainTask(String(record.status))) {
    actions.push({
      icon: 'mdi:restart',
      tooltip: {title: '重新训练', placement: 'top'},
      onClick: () => handleRetrain(record),
      style: 'color: #1890ff; padding: 0 8px; font-size: 16px;',
    });
  }

  if (record.minio_model_path) {
    actions.push({
      icon: 'ant-design:download-outlined',
      tooltip: {title: '下载训练权重', placement: 'top'},
      onClick: () => handleDownloadWeights(record),
      style: 'color: #1890ff; padding: 0 8px; font-size: 16px;',
    });
  }

  if (canPublishTrainTask(record as { status?: string; minio_model_path?: string })) {
    const publishedModelId = getPublishedModelId(record as { published_model_id?: number; hyperparameters?: unknown });
    actions.push({
      icon: 'ant-design:cloud-upload-outlined',
      tooltip: {
        title: publishedModelId ? `更新发布（模型 ID: ${publishedModelId}）` : '发布到模型管理',
        placement: 'top',
      },
      onClick: () => handlePublishTrainModel(record),
      style: 'color: #722ed1; padding: 0 8px; font-size: 16px;',
    });
  }

  actions.push({
    icon: 'mdi:delete-outline',
    tooltip: {title: '删除', placement: 'top'},
    popConfirm: {
      placement: 'topRight',
      title: '确定删除此训练任务?',
      confirm: () => handleDelete(record),
    },
    style: 'color: #ff4d4f; padding: 0 8px; font-size: 16px;',
  });

  return actions;
};

const handleStartTrain = async (config) => {
  try {
    const response = await startTrain(config);
    const isResume = !!config.resume;
    const isRetrain = !!config.taskId && !isResume;
    if (response && (response.code === 0 || response.success === true)) {
      createMessage.success(
        response.msg || (isResume ? '训练已继续' : isRetrain ? '重新训练已启动' : '训练已启动'),
      );
      await handleSuccess();
    } else {
      createMessage.error(
        response?.msg || (isResume ? '继续训练失败' : isRetrain ? '重新训练失败' : '启动训练失败'),
      );
    }
  } catch (error) {
    const isResume = !!config.resume;
    const isRetrain = !!config.taskId && !isResume;
    const errorMsg =
      error?.response?.data?.msg
      || error?.message
      || (isResume ? '继续训练失败' : isRetrain ? '重新训练失败' : '启动训练失败');
    createMessage.error(errorMsg);
  }
};

const handleStopTrain = async (record) => {
  try {
    const response = await stopTrain(record.id);
    if (response && (response.code === 0 || response.success === true)) {
      createMessage.success(response.msg || '已发送停止请求，将在当前 epoch 结束后保存断点');
      await handleSuccess();
    } else {
      createMessage.error(response?.msg || '暂停训练失败');
    }
  } catch (error) {
    const errorMsg = error?.response?.data?.msg || error?.message || '暂停训练失败';
    createMessage.error(errorMsg);
  }
};

const handleRetrain = (record) => {
  openTrainDrawer(true, {isRetrain: true, record});
};

const handleResume = (record) => {
  openTrainDrawer(true, {isResume: true, record});
};

function revokeResultsBlobUrl() {
  if (resultsBlobUrl) {
    window.URL.revokeObjectURL(resultsBlobUrl);
    resultsBlobUrl = null;
  }
}

const handleViewTrainResults = async (record) => {
  if (!record.train_results_path) {
    createMessage.warning('此训练记录没有结果图片');
    return;
  }
  revokeResultsBlobUrl();
  resultsImageError.value = false;
  currentImageUrl.value = '';
  showResultsModal.value = true;

  const fetchUrl = resolveTrainResultsDisplayUrl(record.train_results_path);
  try {
    const token = localStorage.getItem('jwt_token');
    const response = await fetch(fetchUrl, {
      method: 'GET',
      headers: token ? {'X-Authorization': `Bearer ${token}`} : {},
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const blob = await response.blob();
    resultsBlobUrl = window.URL.createObjectURL(blob);
    currentImageUrl.value = resultsBlobUrl;
  } catch {
    resultsImageError.value = true;
    createMessage.error('训练结果图片加载失败，请确认 MinIO 中文件存在或重新训练');
  }
};

const handleDownloadWeights = async (record) => {
  const url = record.minio_model_path;
  if (!url) {
    createMessage.warning('暂无可下载的训练权重');
    return;
  }
  try {
    const token = localStorage.getItem('jwt_token');
    const response = await fetch(resolveTrainResultsDisplayUrl(url), {
      method: 'GET',
      headers: {'X-Authorization': 'Bearer ' + token},
    });
    if (!response.ok) {
      throw new Error('下载失败');
    }
    const blob = await response.blob();
    const link = document.createElement('a');
    link.href = window.URL.createObjectURL(blob);
    link.download = `${record.name || 'train'}_${record.id}.pt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(link.href);
    createMessage.success('下载成功');
  } catch {
    createMessage.error('下载训练权重失败');
  }
};

const handleDelete = async (record) => {
  try {
    const response = await deleteTrainTask(record.id);
    if (response && (response.code === 0 || response.success === true)) {
      createMessage.success(response.msg || '删除成功');
      await handleSuccess();
    } else {
      createMessage.error(response?.msg || '删除失败');
    }
  } catch (error) {
    const errorMsg = error?.response?.data?.msg || error?.message || '删除失败，请稍后重试';
    createMessage.error(errorMsg);
  }
};

const handleCardDelete = async (record) => {
  await handleDelete(record);
};

const handlePublishTrainModel = (record) => {
  openPublishModal(true, {record});
};

const handlePublishSuccess = async () => {
  await handleSuccess();
};

const handleOpenTrainLogsModal = (record) => {
  showLogsModal.value = true;
  nextTick(() => {
    openTrainLogsModal(true, {record});
  });
};

const handleLogsModalClose = () => {
  showLogsModal.value = false;
};

watch(() => props.tabActive, (active) => {
  if (active) {
    void refreshList({silent: true}).then(() => syncAutoRefresh());
  } else {
    stopAutoRefresh();
  }
});

watch(hasActiveTrainingTasks, () => {
  if (props.tabActive) {
    syncAutoRefresh();
  }
});

onUnmounted(() => {
  stopAutoRefresh();
  if (actionRefreshTimer) {
    clearTimeout(actionRefreshTimer);
    actionRefreshTimer = null;
  }
});

const [registerTable, {reload}] = useTable({
  canResize: true,
  showIndexColumn: false,
  title: '模型训练',
  api: fetchTrainTasks,
  columns: getBasicColumns(),
  useSearchForm: true,
  showTableSetting: true,
  pagination: true,
  formConfig: getFormConfig(),
  fetchSetting: {
    listField: 'data',
    totalField: 'total',
  },
  rowKey: 'id',
});
</script>

<style lang="less" scoped>
#train-task-list {
  .toolbar-buttons {
    display: flex;
    align-items: center;
    gap: 10px;
  }
}
</style>
