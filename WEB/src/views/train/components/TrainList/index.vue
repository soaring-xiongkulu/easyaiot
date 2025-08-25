<template>
  <div class="train-container bg-white p-6 rounded-xl shadow-lg transition-all duration-300">
    <BasicTable
      @register="registerTable"
      class="rounded-xl overflow-hidden border border-gray-100 shadow-sm"
    >
      <template #toolbar>
        <a-button type="primary" @click="openAddModal(true,{isEdit: false, isView: false})">
          启动新训练
        </a-button>
      </template>
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'action'">
          <div class="flex space-x-2">
            <a-tooltip title="训练详情" placement="top">
              <a-button
                type="text"
                shape="circle"
                class="text-blue-500 hover:text-blue-700 hover:bg-blue-50"
                @click="openTrainingDetail(record)"
              >
                <i class="ant-design:info-circle-filled text-lg"></i>
              </a-button>
            </a-tooltip>
            <a-tooltip title="查看日志" placement="top">
              <a-button
                type="text"
                shape="circle"
                class="text-green-500 hover:text-green-700 hover:bg-green-50"
                @click="handleOpenTrainingLogsModal(record)"
              >
                <i class="ant-design:file-text-filled text-lg"></i>
              </a-button>
            </a-tooltip>
            <a-tooltip :title="record.status === 'running' ? '停止训练' : '重新开始'"
                       placement="top">
              <a-button
                type="text"
                shape="circle"
                :class="record.status === 'running'
                  ? 'text-yellow-500 hover:text-yellow-700 hover:bg-yellow-50'
                  : 'text-green-500 hover:text-green-700 hover:bg-green-50'"
                @click="toggleTrainingStatus(record)"
              >
                <i
                  :class="record.status === 'running'
                    ? 'ant-design:pause-circle-filled'
                    : 'ant-design:play-circle-filled'"
                  class="text-lg"
                ></i>
              </a-button>
            </a-tooltip>

            <a-popconfirm
              title="确定删除此模型训练?"
              placement="topRight"
              ok-text="确定"
              cancel-text="取消"
              @confirm="handleDelete(record)"
            >
              <a-tooltip title="删除" placement="top">
                <a-button
                  type="text"
                  shape="circle"
                  class="text-red-500 hover:text-red-700 hover:bg-red-50"
                >
                  <i class="material-symbols:delete-outline-rounded text-lg"></i>
                </a-button>
              </a-tooltip>
            </a-popconfirm>
          </div>
        </template>
      </template>
    </BasicTable>
    <StartTrainingModal @register="registerAddModel" @success="handleStartTraining"/>
    <TrainingLogsModal @register="registerTrainingLogsModal" @success="handleSuccess"/>
  </div>
</template>

<script lang="ts" setup>
import {ref, watch} from 'vue';
import {BasicTable, useTable} from '@/components/Table';
import {useRoute, useRouter} from 'vue-router';
import {useMessage} from '@/hooks/web/useMessage';
import {useModal} from '@/components/Modal';
import {
  deleteTrainingRecord,
  getTrainingRecordPage,
  startTraining,
  stopTraining
} from '@/api/device/model';
import StartTrainingModal from '../StartTrainingModal/index.vue';
import TrainingLogsModal from '../TrainingLogsModal/index.vue';
import {getFormConfig} from './data';
import {getBasicColumns} from "@/views/dataset/components/DatasetList/Data";

const {createMessage} = useMessage();
const router = useRouter();
const route = useRoute();

const [registerAddModel, {openModal: openAddModal}] = useModal();

const [registerTrainingLogsModal, {
  openModal: openTrainingLogsModal,
  closeModal: closeTrainingLogsModal
}] = useModal();

// 表格刷新
function handleSuccess() {
  reload({
    page: 0,
  });
}

// 处理开始训练
const handleStartTraining = async (config) => {
  try {
    console.log(JSON.stringify(config))
    await startTraining(modelId.value, config);
    createMessage.success('训练任务已启动');
    startModalVisible.value = false;
    reload();
  } catch (error) {
    createMessage.error('启动训练失败');
    console.error('启动训练失败:', error);
  }
};

// 查看训练详情
const openTrainingDetail = (record) => {
  router.push({
    name: 'TrainingDetail',
    params: {id: record.task_id},
    query: {modelId: modelId.value}
  });
};

// 切换训练状态
const toggleTrainingStatus = async (record) => {
  try {
    if (record.status === 'running') {
      await stopTraining(modelId.value);
      createMessage.success('训练已停止');
    } else {
      await startTraining(modelId.value, {task_id: record.task_id});
      createMessage.success('训练已开始');
    }
    reload();
  } catch (error) {
    createMessage.error('状态切换失败');
    console.error('状态切换失败:', error);
  }
};

// 删除模型训练
const handleDelete = async (record) => {
  try {
    await deleteTrainingRecord(record.task_id);
    createMessage.success('删除成功');
    reload();
  } catch (error) {
    createMessage.error('删除失败');
    console.error('删除失败:', error);
  }
};

const handleOpenTrainingLogsModal = () => {
  openTrainingLogsModal(true);
};

// 模态框状态
const startModalVisible = ref(false);
const startModalTitle = ref('启动新训练');

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
    return getTrainingRecordPage({...requestParams, modelId: modelId.value});
  },
  columns: getBasicColumns(),
  useSearchForm: true,
  showTableSetting: true,
  pagination: true,
  formConfig: getFormConfig(),
  fetchSetting: {
    listField: 'data.list',
    totalField: 'data.total',
  },
  rowKey: 'task_id',
});
</script>
