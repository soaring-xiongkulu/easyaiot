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
          <TableAction
            :actions="[
              {
                icon: 'mdi:information-outline', // 训练详情图标
                tooltip: { title: '训练详情', placement: 'top' },
                onClick: () => openTrainingDetail(record),
                style: 'color: #1890ff; padding: 0 8px; font-size: 16px;'
              },
              {
                icon: 'mdi:file-document-outline', // 查看日志图标
                tooltip: { title: '查看日志', placement: 'top' },
                onClick: () => handleOpenTrainingLogsModal(record),
                style: 'color: #1890ff; padding: 0 8px; font-size: 16px;'
              },
              {
                icon: record.status === 'running'
                  ? 'mdi:stop-circle-outline'  // 停止图标
                  : 'mdi:play-circle-outline', // 开始图标
                tooltip: {
                  title: record.status === 'running' ? '停止训练' : '重新开始',
                  placement: 'top'
                },
                onClick: () => toggleTrainingStatus(record),
                style: `color: ${record.status === 'running' ? '#faad14' : '#52c41a'};
                        padding: 0 8px;
                        font-size: 16px;`
              },
              {
                icon: 'mdi:delete-outline', // 删除图标
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
    <StartTrainingModal @register="registerAddModel" @success="handleStartTraining"/>
    <TrainingLogsModal @register="registerTrainingLogsModal" @success="handleSuccess"/>
  </div>
</template>

<script lang="ts" setup>
import {ref, watch} from 'vue';
import {BasicTable, TableAction, useTable} from '@/components/Table';
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
import {getBasicColumns, getFormConfig} from './Data';

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
    await startTraining(modelId.value, config).then((data)=>{
      createMessage.success(data['msg']);
    });
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
      await startTraining(modelId.value, {taskId: record.task_id});
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
    await deleteTrainingRecord(record.id);
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
    listField: 'data',
    totalField: 'total',
  },
  rowKey: 'id',
});
</script>
