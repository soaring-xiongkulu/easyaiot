<template>
  <div class="inference-container">
    <!-- 表格视图 -->
    <BasicTable
      v-if="state.isTableMode"
      @register="registerTable"
      :row-class-name="getRowClassName"
    >
      <template #toolbar>
        <a-space>
          <a-button type="primary" @click="openExecuteModal">
            <template #icon>
              <PlayCircleOutlined/>
            </template>
            执行推理
          </a-button>
          <a-button @click="handleClickSwap" preIcon="ant-design:swap-outlined">
            切换视图
          </a-button>
        </a-space>
      </template>

      <template #bodyCell="{ column, record }">
        <!-- 状态列 -->
        <template v-if="column.dataIndex === 'status'">
          <a-tag :color="getStatusColor(record?.status)">
            {{ statusLabels[record?.status] || '-' }}
          </a-tag>
        </template>

        <!-- 进度列 -->
        <template v-else-if="column.dataIndex === 'progress'">
          <a-progress
            v-if="record?.status === 'PROCESSING'"
            :percent="calculateProgress(record)"
            status="active"
            size="small"
          />
          <span v-else>-</span>
        </template>

        <!-- 操作列 -->
        <template v-else-if="column.dataIndex === 'action'">
          <TableAction
            :actions="[
              {
                icon: 'ant-design:eye-filled',
                tooltip: '详情',
                onClick: () => handleViewDetail(record)
              },
              {
                icon: 'ant-design:file-image-filled',
                tooltip: '查看结果',
                onClick: () => handleViewResult(record)
              },
              {
                icon: 'ant-design:delete-outlined',
                tooltip: '删除',
                popConfirm: {
                  title: '确认删除此记录？',
                  onConfirm: () => handleDelete(record)
                }
              }
            ]"
          />
        </template>
      </template>
    </BasicTable>

    <!-- 卡片视图 -->
    <div v-else class="card-view">
      <InferenceCardList
        :records="state.records"
        @view="handleViewDetail"
        @result="handleViewResult"
        @delete="handleDelete"
      >
        <template #header>
          <a-space>
            <a-button type="primary" @click="openExecuteModal">
              <template #icon>
                <PlayCircleOutlined/>
              </template>
              执行推理
            </a-button>
            <a-button @click="handleClickSwap" preIcon="ant-design:swap-outlined">
              切换视图
            </a-button>
          </a-space>
        </template>
      </InferenceCardList>
    </div>

    <!-- 模态框组件 -->
    <ExecuteInferenceModal @register="registerExecuteModal" @success="handleExecuteSuccess"/>
    <InferenceDetailModal @register="registerDetailModal" :record="state.currentRecord"/>
    <InferenceResultViewer @register="registerResultModal" :record="state.currentRecord"/>
  </div>
</template>

<script lang="ts" setup>
import {onBeforeUnmount, onMounted, reactive} from 'vue';
import {PlayCircleOutlined} from '@ant-design/icons-vue';
import {BasicTable, TableAction, useTable} from '@/components/Table';
import {useModal} from '@/components/Modal';
import {useMessage} from '@/hooks/web/useMessage';
import {getInferenceColumns, getInferenceFormConfig} from "./Data";
import ExecuteInferenceModal from "../ExecuteInferenceModal/index.vue";
import InferenceDetailModal from "../InferenceDetailModal/index.vue";
import InferenceResultViewer from "../InferenceResultViewer/index.vue";
import InferenceCardList from "../InferenceCardList/index.vue";
import {
  deleteInferenceRecord,
  getInferenceRecords,
  streamInferenceProgress
} from "@/api/device/model";

// 状态管理
const state = reactive({
  isTableMode: true,
  records: [],
  currentRecord: {},
  eventSources: {}
});

const statusLabels = {
  PROCESSING: '处理中',
  COMPLETED: '已完成',
  FAILED: '失败'
};

const {createMessage} = useMessage();
const [registerTable, {reload}] = useTable({
  canResize: true,
  showIndexColumn: false,
  title: '推理记录管理',
  api: getInferenceRecords,
  columns: getInferenceColumns(),
  useSearchForm: true,
  formConfig: getInferenceFormConfig(),
  pagination: {pageSize: 10},
  rowKey: 'id',
});

// 模态框注册
const [registerExecuteModal, {openModal: openExecuteModal}] = useModal();
const [registerDetailModal, {openModal: openDetailModal}] = useModal();
const [registerResultModal, {openModal: openResultModal}] = useModal();

// 组件挂载时加载数据
onMounted(() => {
  loadRecords();
});

// 组件卸载前关闭所有SSE连接
onBeforeUnmount(() => {
  Object.values(state.eventSources).forEach(source => source.close());
});

// 加载推理记录
const loadRecords = async () => {
  try {
    const response = await getInferenceRecords();
    state.records = response.items.map(record => ({
      ...record,
      start_time: formatDateTime(record.start_time)
    }));

    // 为处理中的记录启动进度监听
    state.records.forEach(record => {
      if (record['status'] === 'PROCESSING') {
        startProgressListener(record['id']);
      }
    });
  } catch (error) {
    createMessage.error('加载推理记录失败');
    console.error('加载记录错误:', error);
  }
};

// 启动进度监听
const startProgressListener = (recordId: number) => {
  // 关闭已存在的连接
  if (state.eventSources[recordId]) {
    state.eventSources[recordId].close();
  }

  // 创建新的EventSource连接
  const eventSource = streamInferenceProgress(recordId);
  state.eventSources[recordId] = eventSource;

  eventSource.onmessage = (event) => {
    const progress = JSON.parse(event.data);
    updateRecordProgress(recordId, progress);
  };

  eventSource.onerror = (error) => {
    console.error('SSE连接错误:', error);
    eventSource.close();
    delete state.eventSources[recordId];
  };
};

// 更新记录进度
const updateRecordProgress = (recordId: number, progress: any) => {
  const recordIndex = state.records.findIndex(r => r['id'] === recordId);
  if (recordIndex === -1) return;

  const updatedRecord = {...state.records[recordIndex]};

  // 更新处理帧数
  if (progress.processed_frames !== undefined) {
    updatedRecord.processed_frames = progress.processed_frames;
  }

  // 更新总帧数（视频处理）
  if (progress.total_frames !== undefined) {
    updatedRecord.total_frames = progress.total_frames;
  }

  // 状态更新
  if (progress.status && progress.status !== 'PROCESSING') {
    updatedRecord.status = progress.status;
    updatedRecord.end_time = formatDateTime(new Date().toISOString());

    if (progress.processing_time) {
      updatedRecord.processing_time = progress.processing_time;
    }

    // 关闭SSE连接
    if (state.eventSources[recordId]) {
      state.eventSources[recordId].close();
      delete state.eventSources[recordId];
    }
  }

  // 错误处理
  if (progress.error_message) {
    updatedRecord.error_message = progress.error_message;
  }

  // 更新记录
  state.records.splice(recordIndex, 1, updatedRecord);
};

// 计算进度百分比
const calculateProgress = (record): number => {
  if (!record?.processed_frames || !record?.total_frames) return 0;
  return Math.round((record.processed_frames / record.total_frames) * 100);
};

// 获取状态标签颜色
const getStatusColor = (status: string): string => {
  const statusColors = {
    COMPLETED: 'green',
    PROCESSING: 'blue',
    FAILED: 'red'
  };
  return statusColors[status] || 'gray';
};

// 表格行样式
const getRowClassName = (record) => {
  return record?.status === 'FAILED' ? 'error-row' : '';
};

// 查看详情
const handleViewDetail = (record) => {
  state.currentRecord = record || {};
  openDetailModal(true);
};

// 查看结果
const handleViewResult = (record) => {
  state.currentRecord = record || {};
  openResultModal(true);
};

// 删除记录
const handleDelete = async (record) => {
  try {
    await deleteInferenceRecord(record.id);
    createMessage.success('删除成功');

    // 关闭该记录的EventSource连接
    if (state.eventSources[record.id]) {
      state.eventSources[record.id].close();
      delete state.eventSources[record.id];
    }

    // 重新加载记录
    await loadRecords();
  } catch (error) {
    console.error('删除错误:', error);
    createMessage.error('删除失败');
  }
};

// 切换视图
const handleClickSwap = () => {
  state.isTableMode = !state.isTableMode;
};

// 执行推理成功回调
const handleExecuteSuccess = (newRecord) => {
  createMessage.success('推理任务已启动');

  // 添加新记录到列表
  state.records.unshift({
    ...newRecord,
    start_time: formatDateTime(newRecord.start_time)
  });

  // 启动进度监听
  startProgressListener(newRecord.id);
};

// 日期时间格式化
const formatDateTime = (dateString: string): string => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
};
</script>

<style lang="less" scoped>
.inference-container {
  padding: 16px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.card-view {
  margin-top: 16px;
}

:deep(.error-row) {
  background-color: #fff1f0;
}
</style>
