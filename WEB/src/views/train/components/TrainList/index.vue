<template>
  <div class="train-container bg-white p-6 rounded-xl shadow-lg transition-all duration-300">
    <!-- 标题和操作区域 -->
    <div class="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
      <div class="flex items-center">
        <i class="el-icon-cpu text-3xl text-blue-500 mr-3"></i>
        <div>
          <h2 class="text-2xl font-bold text-gray-800">模型训练管理</h2>
          <p class="text-sm text-gray-500 mt-1">管理您的模型训练任务和进度</p>
        </div>
      </div>

      <a-button
        type="primary"
        @click="openStartTrainingModal"
        class="flex items-center bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 shadow-md hover:shadow-lg transition-all"
      >
        <i class="el-icon-circle-plus mr-2"></i>
        启动新训练
      </a-button>
    </div>

    <!-- 表格区域 -->
    <BasicTable
      @register="registerTable"
      class="rounded-xl overflow-hidden border border-gray-100 shadow-sm"
    >
      <template #toolbar>
        <!-- 搜索区域已通过配置集成 -->
      </template>

      <template #bodyCell="{ column, record }">
        <!-- 状态列美化 -->
        <template v-if="column.dataIndex === 'status'">
          <a-tag
            :color="statusColors[record.status]"
            class="px-3 py-1 rounded-full font-medium flex items-center"
          >
            <i :class="statusIcons[record.status]" class="mr-1.5"></i>
            {{ statusLabels[record.status] }}
          </a-tag>
        </template>

        <!-- 操作列美化 -->
        <template v-else-if="column.dataIndex === 'action'">
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
                @click="handleOpenLogsModal(record)"
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

    <!-- 模态框组件 -->
    <StartTrainingModal @register="registerStartModal" @success="handleSuccess"/>
    <TrainingLogsModal @register="registerLogsModal"/>
  </div>
</template>

<script lang="ts" setup>
import {ref, watch} from 'vue';
import {BasicTable, useTable} from '@/components/Table';
import {useModal} from '@/components/Modal';
import {useRoute, useRouter} from 'vue-router';
import {useMessage} from '@/hooks/web/useMessage';
import {
  deleteTrainingRecord,
  getTrainingRecordPage,
  startTraining,
  stopTraining
} from '@/api/device/model';
import StartTrainingModal from '../StartTrainingModal/index.vue';
import TrainingLogsModal from '../TrainingLogsModal/index.vue';
import {getSearchFormConfig, getTrainTableColumns} from './data';

const {createMessage} = useMessage();
const router = useRouter();
const route = useRoute();

const statusColors = {
  running: 'blue',
  completed: 'green',
  failed: 'red',
  stopped: 'orange',
  pending: 'gray'
};

const statusIcons = {
  running: 'el-icon-loading animate-spin',
  completed: 'el-icon-success',
  failed: 'el-icon-error',
  stopped: 'el-icon-warning',
  pending: 'el-icon-time'
};

const statusLabels = {
  running: '运行中',
  completed: '已完成',
  failed: '失败',
  stopped: '已停止',
  pending: '等待中'
};

// 获取路由参数 modelId
const modelId = ref<string>(route.params.modelId?.toString() || '');

// 监听路由参数变化
watch(() => route.params.modelId, (newId) => {
  modelId.value = newId?.toString() || '';
  reload();
});

// 注册模态框
const [registerStartModal, {openModal: openStartModal}] = useModal();
const [registerLogsModal, {openModal: openLogsModal}] = useModal();

// 使用 useTable 封装表格逻辑
const [registerTable, {reload}] = useTable({
  canResize: true,
  showIndexColumn: false,
  title: '',
  api: async (params) => {
    // 处理时间范围参数
    const requestParams = {...params};
    if (params.timeRange && params.timeRange.length === 2) {
      requestParams.startTimeFrom = params.timeRange[0];
      requestParams.startTimeTo = params.timeRange[1];
      delete requestParams.timeRange;
    }
    return getTrainingRecordPage({...requestParams, modelId: modelId.value});
  },
  columns: getTrainTableColumns(),
  useSearchForm: true,
  showTableSetting: true,
  pagination: true,
  formConfig: {
    ...getSearchFormConfig(),
    schemas: [
      ...getSearchFormConfig().schemas,
      // 新增训练状态筛选
      {
        field: 'status',
        label: '训练状态',
        component: 'Select',
        componentProps: {
          placeholder: '请选择状态',
          options: [
            {label: '运行中', value: 'running'},
            {label: '已完成', value: 'completed'},
            {label: '失败', value: 'failed'},
            {label: '已停止', value: 'stopped'},
            {label: '等待中', value: 'pending'},
          ],
          allowClear: true,
        },
        colProps: {span: 6},
      },
      // 新增时间范围筛选
      {
        field: 'timeRange',
        label: '训练时间',
        component: 'RangePicker',
        componentProps: {
          format: 'YYYY-MM-DD',
          placeholder: ['开始日期', '结束日期'],
          showTime: false,
        },
        colProps: {span: 8},
      },
    ],
  },
  fetchSetting: {
    listField: 'data.list',
    totalField: 'data.total',
  },
  rowKey: 'task_id',
});

// 打开启动训练模态框
const openStartTrainingModal = () => {
  openStartModal(true, {
    type: 'start',
    modelId: modelId.value
  });
};

// 查看训练详情
const openTrainingDetail = (record) => {
  router.push({
    name: 'TrainingDetail',
    params: {id: record.task_id},
    query: {modelId: modelId.value}
  });
};

// 打开日志模态框
const handleOpenLogsModal = (record) => {
  openLogsModal(true, {
    taskId: record.task_id,
    modelId: modelId.value,
    taskName: record.task_name
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

// 处理成功回调
const handleSuccess = () => {
  reload();
};
</script>

<style lang="less" scoped>
.train-container {
  :deep(.ant-table) {
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);

    thead > tr > th {
    @apply bg-gray-50 text-gray-700 font-semibold;
      border-bottom: 1px solid #f0f0f0;
    }

    tbody > tr {
      transition: background-color 0.2s;

      &:hover {
      @apply bg-blue-50;
      }

      td {
        border-bottom: 1px solid #f5f5f5;
      }
    }
  }

  :deep(.ant-btn-primary) {
    box-shadow: 0 4px 6px rgba(59, 130, 246, 0.4);
    transition: all 0.3s;

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 10px rgba(59, 130, 246, 0.6);
    }
  }

  :deep(.ant-tag) {
    border: none;
    font-weight: 500;
    padding: 4px 12px;
  }

  :deep(.ant-table-pagination) {
    margin: 20px 0;
    padding: 0 16px;
  }

  :deep(.ant-form) {
    background: #f9fafb;
    padding: 16px;
    border-radius: 12px;
    margin-bottom: 20px;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  }
}

// 响应式调整
@media (max-width: 768px) {
  .train-container {
    padding: 16px;

    .flex.justify-between {
      flex-direction: column;
      align-items: flex-start;
      gap: 16px;

      h2 {
        margin-bottom: 8px;
      }
    }

    :deep(.ant-table) {
      border-radius: 8px;
    }

    :deep(.ant-form) {
      padding: 12px;
    }
  }
}
</style>
