<template>
  <div class="service-container bg-white p-6 rounded-xl shadow-lg transition-all duration-300">
    <!-- 标题和操作区域 -->
    <div class="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
      <div class="flex items-center">
        <i class="el-icon-cloud-check text-3xl text-blue-500 mr-3"></i>
        <div>
          <h2 class="text-2xl font-bold text-gray-800">模型服务管理</h2>
          <p class="text-sm text-gray-500 mt-1">部署、监控和管理您的模型推理服务</p>
        </div>
      </div>

      <div class="flex space-x-3">
        <a-button
          type="primary"
          @click="handleOpenDeployModal"
          class="flex items-center bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 shadow-md hover:shadow-lg transition-all"
        >
          <i class="el-icon-circle-plus mr-2"></i>
          部署新服务
        </a-button>
        <a-button
          @click="handleClickSwap"
          class="flex items-center border border-gray-300 hover:bg-gray-50"
        >
          <i :class="state.isTableMode ? 'el-icon-menu' : 'el-icon-s-grid'" class="mr-2"></i>
          {{ state.isTableMode ? '卡片视图' : '表格视图' }}
        </a-button>
      </div>
    </div>

    <!-- 表格视图 -->
    <BasicTable
      v-if="state.isTableMode"
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

        <!-- 性能指标列 -->
        <template v-else-if="column.dataIndex === 'performance'">
          <div class="flex items-center">
            <a-progress
              :percent="record.cpu_usage"
              size="small"
              status="active"
              stroke-color="#3498db"
              class="w-24 mr-3"
            />
            <span class="text-sm text-gray-600">{{ record.latency }}ms</span>
          </div>
        </template>

        <!-- 操作列美化 -->
        <template v-else-if="column.dataIndex === 'action'">
          <div class="flex space-x-2">
            <a-tooltip title="服务详情" placement="top">
              <a-button
                type="text"
                shape="circle"
                class="text-blue-500 hover:text-blue-700 hover:bg-blue-50"
                @click="openDetailModal(record)"
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

            <a-tooltip :title="record.status === 'running' ? '停止服务' : '启动服务'" placement="top">
              <a-button
                type="text"
                shape="circle"
                :class="record.status === 'running'
                  ? 'text-yellow-500 hover:text-yellow-700 hover:bg-yellow-50'
                  : 'text-green-500 hover:text-green-700 hover:bg-green-50'"
                @click="toggleServiceStatus(record)"
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
              title="确定删除此服务?"
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

    <!-- 卡片视图 -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
      <a-card
        v-for="service in serviceList"
        :key="`${service.model_id}-${service.task_id}`"
        class="rounded-xl shadow-sm hover:shadow-md transition-shadow"
        :class="{
          'border-l-4 border-blue-500': service.status === 'running',
          'border-l-4 border-gray-300': service.status !== 'running'
        }"
      >
        <template #title>
          <div class="flex justify-between items-center">
            <span class="font-medium text-lg">{{ service.model_name }}</span>
            <a-tag :color="statusColors[service.status]">
              {{ statusLabels[service.status] }}
            </a-tag>
          </div>
        </template>

        <div class="space-y-3">
          <div class="flex items-center text-sm">
            <i class="el-icon-cpu text-blue-500 mr-2"></i>
            <span>CPU: {{ service.cpu_usage }}%</span>
          </div>

          <div class="flex items-center text-sm">
            <i class="el-icon-time text-green-500 mr-2"></i>
            <span>延迟: {{ service.latency }}ms</span>
          </div>

          <div class="flex items-center text-sm">
            <i class="el-icon-refresh text-purple-500 mr-2"></i>
            <span>请求量: {{ service.request_count }}/分钟</span>
          </div>

          <div class="flex justify-end space-x-2 mt-4">
            <a-button type="text" size="small" @click="openDetailModal(service)">
              <i class="ant-design:info-circle-filled text-blue-500"></i>
            </a-button>
            <a-button
              type="text"
              size="small"
              @click="toggleServiceStatus(service)"
            >
              <i
                :class="service.status === 'running'
                  ? 'ant-design:pause-circle-filled text-yellow-500'
                  : 'ant-design:play-circle-filled text-green-500'"
              ></i>
            </a-button>
            <a-popconfirm
              title="确定删除此服务?"
              @confirm="handleDelete(service)"
            >
              <a-button type="text" size="small">
                <i class="material-symbols:delete-outline-rounded text-red-500"></i>
              </a-button>
            </a-popconfirm>
          </div>
        </div>
      </a-card>
    </div>

    <!-- 模态框组件 -->
    <DeployModelModal @register="registerDeployModal" @success="handleSuccess"/>
    <ServiceDetailModal @register="registerServiceDetailModal"/>
    <TrainingLogsModal @register="registerLogsModal"/>
  </div>
</template>

<script lang="ts" setup>
import { reactive, ref } from 'vue';
import { BasicTable, useTable } from '@/components/Table';
import { useModal } from '@/components/Modal';
import { useMessage } from '@/hooks/web/useMessage';
import {
  getTrainingRecordPage,
  startTraining,
  stopTraining,
  deleteTrainingRecord
} from '@/api/device/model';
import DeployModelModal from '../DeployModelModal/index.vue';
import ServiceDetailModal from '../ServiceDetailModal/index.vue';
import TrainingLogsModal from '../TrainingLogsModal/index.vue';
import { getModelServiceColumns, getSearchFormConfig } from './data';

const { createMessage } = useMessage();

// 状态美化配置
const statusColors = {
  running: 'blue',
  deploying: 'cyan',
  stopped: 'gray',
  error: 'red',
  pending: 'orange'
};

const statusIcons = {
  running: 'el-icon-loading animate-spin',
  deploying: 'el-icon-refresh animate-spin',
  stopped: 'el-icon-switch-button',
  error: 'el-icon-circle-close',
  pending: 'el-icon-time'
};

const statusLabels = {
  running: '运行中',
  deploying: '部署中',
  stopped: '已停止',
  error: '运行异常',
  pending: '等待启动'
};

// 状态管理
const state = reactive({
  isTableMode: true,
});

const serviceList = ref<any[]>([]);

// 注册模态框
const [registerDeployModal, { openModal: openDeployModalHandler }] = useModal();
const [registerServiceDetailModal, { openModal: openServiceDetailModal }] = useModal();
const [registerLogsModal, { openModal: openLogsModal }] = useModal();

// 使用useTable封装表格逻辑
const [registerTable, { reload, getDataSource }] = useTable({
  canResize: true,
  showIndexColumn: false,
  title: '',
  api: async (params) => {
    // 处理时间范围参数
    const requestParams = { ...params };
    if (params.timeRange && params.timeRange.length === 2) {
      requestParams.startTimeFrom = params.timeRange[0];
      requestParams.startTimeTo = params.timeRange[1];
      delete requestParams.timeRange;
    }
    return getTrainingRecordPage({ ...requestParams }); // 使用正确的API
  },
  columns: getModelServiceColumns(),
  useSearchForm: true,
  showTableSetting: true,
  pagination: true,
  formConfig: {
    ...getSearchFormConfig(),
    schemas: [
      ...getSearchFormConfig().schemas,
      // 新增服务状态筛选
      {
        field: 'status',
        label: '服务状态',
        component: 'Select',
        componentProps: {
          placeholder: '请选择状态',
          options: [
            { label: '运行中', value: 'running' },
            { label: '已停止', value: 'stopped' },
            { label: '部署中', value: 'deploying' },
            { label: '运行异常', value: 'error' },
          ],
          allowClear: true,
        },
        colProps: { span: 6 },
      },
      // 新增时间范围筛选
      {
        field: 'timeRange',
        label: '创建时间',
        component: 'RangePicker',
        componentProps: {
          format: 'YYYY-MM-DD',
          placeholder: ['开始日期', '结束日期'],
          showTime: false,
        },
        colProps: { span: 8 },
      },
    ],
  },
  fetchSetting: {
    listField: 'data.list',
    totalField: 'data.total',
  },
  rowKey: (record) => `${record.model_id}-${record.task_id}`, // 确保唯一键值
  afterFetch: (res) => {
    serviceList.value = res.data.list || [];
    return res;
  }
});

// 打开部署模态框
const handleOpenDeployModal = () => {
  openDeployModalHandler(true);
};

// 查看服务详情
const openDetailModal = (record) => {
  openServiceDetailModal(true, {
    service: record,
    taskId: record.task_id,
    taskName: record.task_name
  });
};

// 打开日志模态框
const handleOpenLogsModal = (record) => {
  openLogsModal(true, {
    taskId: record.task_id, // 使用正确的参数名
    modelId: record.model_id,
    taskName: record.task_name
  });
};

// 切换服务状态（修正API调用）
const toggleServiceStatus = async (record) => {
  try {
    if (record.status === 'running') {
      // 使用正确的API和参数
      await stopTraining(record.model_id, record.task_id);
      createMessage.success('服务已停止');
    } else {
      // 使用正确的API和参数
      await startTraining(record.model_id, { task_id: record.task_id });
      createMessage.success('服务已启动');
    }
    reload();
  } catch (error) {
    createMessage.error('操作失败');
    console.error('服务状态切换失败:', error);
  }
};

// 删除服务（修正API调用）
const handleDelete = async (record) => {
  try {
    // 使用正确的API
    await deleteTrainingRecord(record.task_id);
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

<style lang="less" scoped>
.service-container {
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

  .ant-card {
    transition: transform 0.3s, box-shadow 0.3s;

    &:hover {
      transform: translateY(-3px);
      box-shadow: 0 6px 12px rgba(0, 0, 0, 0.08);
    }
  }
}

// 响应式调整
@media (max-width: 768px) {
  .service-container {
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
