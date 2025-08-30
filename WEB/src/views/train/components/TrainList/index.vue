<template>
  <div class="train-container bg-white p-6 rounded-xl shadow-lg transition-all duration-300">
    <BasicTable
      @register="registerTable"
      class="rounded-xl overflow-hidden border border-gray-100 shadow-sm"
    >
      <template #toolbar>
        <a-button type="primary" @click="openAddModal(true,{isEdit: false, isView: false})">
          <Icon icon="ant-design:plus-circle-outlined"/>
          启动新训练
        </a-button>
      </template>
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'action'">
          <TableAction
            :actions="[
              {
                icon: 'mdi:file-document-outline',
                tooltip: { title: '查看日志', placement: 'top' },
                onClick: () => handleOpenTrainLogsModal(record),
                style: 'color: #1890ff; padding: 0 8px; font-size: 16px;'
              },
              {
                icon: 'mdi:image-outline',
                tooltip: { title: '查看训练结果', placement: 'top' },
                onClick: () => handleViewTrainResults(record),
                style: 'color: #1890ff; padding: 0 8px; font-size: 16px;'
              },
              {
                icon: 'mdi:cloud-upload-outline',
                tooltip: { title: '发布为正式模型', placement: 'top' },
                onClick: () => handlePublish(record),
                style: 'color: #1890ff; padding: 0 8px; font-size: 16px;'
              },
              {
                icon: 'mdi:delete-outline',
                tooltip: { title: '删除', placement: 'top' },
                popConfirm: {
                  placement: 'topRight',
                  title: '确定删除此模型训练?',
                  confirm: () => handleDelete(record)
                },
                style: 'color: #ff4d4f; padding: 0 8px; font-size: 16px;'
              }
            ]"
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
    <StartTrainModal @register="registerAddModel" @success="handleStartTrain"/>
    <TrainLogsModal
      v-if="showLogsModal"
      @register="registerTrainLogsModal"
      @success="handleSuccess"
      @close="handleLogsModalClose"
    />

    <!-- 新增训练结果图片模态框 -->
    <a-modal
      v-model:visible="showResultsModal"
      title="训练结果"
      :footer="null"
      width="80%"
    >
      <img :src="currentImageUrl" style="width: 100%" v-if="currentImageUrl"/>
      <div v-else class="text-center py-8">
        <a-empty description="暂无训练结果图片"/>
      </div>
    </a-modal>
  </div>
</template>

<script lang="ts" setup>
import {nextTick, onBeforeUnmount, onMounted, ref, watch} from 'vue';
import {BasicTable, TableAction, useTable} from '@/components/Table';
import {useRoute, useRouter} from 'vue-router';
import {useMessage} from '@/hooks/web/useMessage';
import {useModal} from '@/components/Modal';
import {
  deleteInferenceTask,
  getTrainPage,
  publishInferenceTask,
  startTrain
} from '@/api/device/model';
import StartTrainModal from '@/views/train/components/StartTrainModal/index.vue';
import TrainLogsModal from '@/views/train/components/TrainLogsModal/index.vue';
import {getBasicColumns, getFormConfig} from './Data';
import {Empty as AEmpty, Modal as AModal} from 'ant-design-vue';
import {Icon} from "@/components/Icon"; // 引入新组件

const {createMessage} = useMessage();
const router = useRouter();
const route = useRoute();

const showLogsModal = ref(false);
const showResultsModal = ref(false); // 控制训练结果图片模态框
const currentImageUrl = ref(''); // 当前展示的图片URL

const [registerAddModel, {openModal: openAddModal}] = useModal();

const [registerTrainLogsModal, {
  openModal: openTrainLogsModal,
  closeModal: closeTrainLogsModal
}] = useModal();

// 表格刷新
function handleSuccess() {
  reload({
    page: 0,
  });
}

// 处理开始训练
const handleStartTrain = async (config) => {
  try {
    await startTrain(modelId.value, config).then((data) => {
      createMessage.success(data['msg']);
    });
    isPollingActive.value = true;
    startModalVisible.value = false;
    reload();
  } catch (error) {
    createMessage.error('启动训练失败');
    console.error('启动训练失败:', error);
  }
};

// 查看训练结果图片
const handleViewTrainResults = (record) => {
  if (record.train_results_path) {
    currentImageUrl.value = record.train_results_path;
    showResultsModal.value = true;
  } else {
    createMessage.warning('此训练记录没有结果图片');
  }
};

// 发布为正式模型
const handlePublish = async (record) => {
  try {
    publishInferenceTask(record.id).then(() => {
      createMessage.success('模型发布成功');
      reload();
    });
  } catch (error) {
    createMessage.error('模型发布失败');
    console.error('模型发布失败:', error);
  }
};

// 删除模型训练
const handleDelete = async (record) => {
  try {
    await deleteInferenceTask(record.id);
    createMessage.success('删除成功');
    reload();
  } catch (error) {
    createMessage.error('删除失败');
    console.error('删除失败:', error);
  }
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

const pollingInterval = ref<number>(10000); // 默认10秒
const pollingTimer = ref<NodeJS.Timeout | null>(null);
const isPollingActive = ref<boolean>(true); // 轮询开关

const startPolling = async () => {
  if (!isPollingActive.value) return;

  try {
    await reload(); // 调用表格刷新方法
  } catch (error) {
    console.error('轮询请求失败:', error);
  } finally {
    pollingTimer.value = setTimeout(startPolling, pollingInterval.value);
  }
};

// 启动轮询
onMounted(() => {
  startPolling();
});

// 组件销毁时停止轮询
onBeforeUnmount(() => {
  if (pollingTimer.value) {
    clearTimeout(pollingTimer.value);
    pollingTimer.value = null;
  }
});

// 模态框状态
const startModalVisible = ref(false);

// 获取路由参数 modelId
const modelId = ref<string>(route.params.modelId?.toString() || '');

watch(() => route.params.modelId, (newId) => {
  modelId.value = newId?.toString() || '';
  reload();
});

const [registerTable, {reload}] = useTable({
  canResize: true,
  showIndexColumn: false,
  title: '',
  api: async (params) => {
    const requestParams = {...params};
    if (params.timeRange && params.timeRange.length === 2) {
      requestParams.startTimeFrom = params.timeRange[0];
      requestParams.startTimeTo = params.timeRange[1];
      delete requestParams.timeRange;
    }
    return getTrainPage({...requestParams, modelId: modelId.value});
  },
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
