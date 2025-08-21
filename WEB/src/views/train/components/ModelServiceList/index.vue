<template>
  <div>
    <BasicTable @register="registerTable">
      <!-- 工具栏 -->
      <template #toolbar>
        <a-button type="primary" @click="openDeployModal">部署模型</a-button>
      </template>
      <!-- 操作列自定义渲染 -->
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'action'">
          <TableAction
            :actions="[
              {
                icon: 'ant-design:info-circle-filled',
                tooltip: {
                  title: '服务详情',
                  placement: 'top',
                },
                onClick: openDetailModal.bind(null, record),
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
                tooltip: record.status === 'running' ? '停止服务' : '启动服务',
                icon: record.status === 'running'
                  ? 'ant-design:pause-circle-filled'
                  : 'ant-design:play-circle-filled',
                onClick: toggleServiceStatus.bind(null, record),
              },
              {
                tooltip: {
                  title: '删除',
                  placement: 'top',
                },
                icon: 'material-symbols:delete-outline-rounded',
                popConfirm: {
                  placement: 'topRight',
                  title: '确定删除此服务?',
                  confirm: handleDelete.bind(null, record),
                },
              },
            ]"
          />
        </template>
      </template>
    </BasicTable>
    <DeployModelModal @register="registerDeployModal" @success="handleSuccess"/>
    <ServiceDetailModal @register="registerServiceDetailModal"/>
    <TrainingLogsModal @register="registerLogsModal"/>
  </div>
</template>

<script lang="ts" setup>
import {reactive} from 'vue';
import {BasicTable, TableAction, useTable} from '@/components/Table';
import {useModal} from '@/components/Modal';
import {useRouter} from 'vue-router';
import {useMessage} from '@/hooks/web/useMessage';
import {
  deleteModelService,
  listModelServices,
  startModelService,
  stopModelService
} from '@/api/device/train';
import DeployModelModal from '../DeployModelModal/index.vue';
import ServiceDetailModal from '../ServiceDetailModal/index.vue';
import TrainingLogsModal from '../TrainingLogsModal/index.vue';
import {getModelServiceColumns, getSearchFormConfig} from './data';

const {createMessage} = useMessage();
const router = useRouter();

// 状态管理
const state = reactive({
  isTableMode: true, // 默认显示表格视图
});

// 注册模态框
const [registerDeployModal, {openModal: openDeployModal}] = useModal();
const [registerServiceDetailModal, {openModal: openServiceDetailModal}] = useModal();
const [registerLogsModal, {openModal: openLogsModal}] = useModal();

// 使用useTable封装表格逻辑
const [
  registerTable,
  {reload}
] = useTable({
  canResize: true,
  showIndexColumn: false,
  title: '模型服务列表',
  api: listModelServices,
  columns: getModelServiceColumns(),
  useSearchForm: true,
  showTableSetting: false,
  pagination: true,
  formConfig: getSearchFormConfig(),
  fetchSetting: {
    listField: 'data.list',
    totalField: 'data.total',
  },
  rowKey: 'model_id', // 明确指定行标识字段
});

// 查看服务详情
const openDetailModal = (record) => {
  openServiceDetailModal(true, {
    service: record,
    taskId: record.model_id,
    taskName: record.model_name
  });
};

// 打开日志模态框
const handleOpenLogsModal = (record) => {
  openLogsModal(true, {
    taskId: record.model_id,
    taskName: record.model_name
  });
};

// 切换服务状态
const toggleServiceStatus = async (record) => {
  try {
    if (record.status === 'running') {
      await stopModelService(record.model_id);
      createMessage.success('服务已停止');
    } else {
      await startModelService(record.model_id);
      createMessage.success('服务已启动');
    }
    reload();
  } catch (error) {
    createMessage.error('操作失败');
    console.error('服务状态切换失败:', error);
  }
};

// 删除服务
const handleDelete = async (record) => {
  try {
    await deleteModelService(record.model_id);
    createMessage.success('删除成功');
    reload();
  } catch (error) {
    createMessage.error('删除失败');
    console.error('删除服务失败:', error);
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
