<template>
  <div>
    <BasicTable @register="registerTable">
      <template #toolbar>
        <a-button type="primary" @click="openStartTrainingModal">启动训练</a-button>
      </template>
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'action'">
          <TableAction
            :actions="[
              {
                icon: 'ant-design:info-circle-filled',
                tooltip: {
                  title: '训练详情',
                  placement: 'top',
                },
                onClick: openTrainingDetail.bind(null, record),
              },
              {
                tooltip: {
                  title: '查看日志',
                  placement: 'top',
                },
                icon: 'ant-design:file-text-filled',
                onClick: handleOpenLogsModal.bind(null, record),
              },
              {
                tooltip: record.status === 'running' ? '停止训练' : '重新开始',
                icon: record.status === 'running'
                  ? 'ant-design:pause-circle-filled'
                  : 'ant-design:play-circle-filled',
                onClick: toggleTrainingStatus.bind(null, record),
              },
              {
                tooltip: {
                  title: '删除',
                  placement: 'top',
                },
                icon: 'material-symbols:delete-outline-rounded',
                popConfirm: {
                  placement: 'topRight',
                  title: '确定删除此模型训练?',
                  confirm: handleDelete.bind(null, record),
                },
              },
            ]"
          />
        </template>
      </template>
    </BasicTable>
    <StartTrainingModal @register="registerStartModal" @success="handleSuccess"/>
    <TrainingLogsModal @register="registerLogsModal"/>
  </div>
</template>

<script lang="ts" setup>
import {reactive} from 'vue';
import {BasicTable, TableAction, useTable} from '@/components/Table';
import {useModal} from '@/components/Modal';
import {useRouter} from 'vue-router';
import {useMessage} from '@/hooks/web/useMessage';
import {deleteTraining, listTrainings, updateTrainingStatus} from '@/api/device/train';
import StartTrainingModal from '../StartTrainingModal/index.vue';
import TrainingLogsModal from '../TrainingLogsModal/index.vue';
import {getSearchFormConfig, getTrainTableColumns} from './data';

const {createMessage} = useMessage();
const router = useRouter();

// 状态管理
const state = reactive({
  isTableMode: true, // 默认显示表格视图
});

// 注册模态框
const [registerStartModal, {openModal: openStartModal}] = useModal();
const [registerLogsModal, {openModal: openLogsModal}] = useModal();

// 使用useTable封装表格逻辑
const [
  registerTable,
  {reload}
] = useTable({
  canResize: true,
  showIndexColumn: false,
  title: '模型训练列表',
  api: listTrainings,
  columns: getTrainTableColumns(),
  useSearchForm: true,
  showTableSetting: false,
  pagination: true,
  formConfig: getSearchFormConfig(),
  fetchSetting: {
    listField: 'data.list',
    totalField: 'data.total',
  },
  rowKey: 'task_id',
});

// 打开启动训练模态框
const openStartTrainingModal = () => {
  openStartModal(true, {type: 'start'});
};

// 查看训练详情
const openTrainingDetail = (record) => {
  router.push({
    name: 'TrainingDetail',
    params: {id: record.task_id}
  });
};

// 打开日志模态框
const handleOpenLogsModal = (record) => {
  openLogsModal(true, {
    taskId: record.task_id,
    taskName: record.task_name
  });
};

// 切换训练状态
const toggleTrainingStatus = async (record) => {
  try {
    const newStatus = record.status === 'running' ? 'stopped' : 'running';
    await updateTrainingStatus(record.task_id, newStatus);
    createMessage.success(`训练已${newStatus === 'running' ? '开始' : '停止'}`);
    reload();
  } catch (error) {
    createMessage.error('状态切换失败');
    console.error('状态切换失败:', error);
  }
};

// 删除模型训练
const handleDelete = async (record) => {
  try {
    await deleteTraining(record.task_id);
    createMessage.success('删除成功');
    reload();
  } catch (error) {
    createMessage.error('删除失败');
    console.error('删除失败:', error);
  }
};

// 处理成功回调
const handleSuccess = () => {
  reload();
};

// 切换视图
const handleClickSwap = () => {
  state.isTableMode = !state.isTableMode;
};
</script>
