<template>
  <div class="inference-container">
    <BasicTable
      @register="registerTable"
      :row-class-name="getRowClassName"
    >
      <template #toolbar>
        <a-space>
          <a-button type="primary" @click="openExecuteModal">
            <template #icon>
              <PlayCircleOutlined/>
            </template>
            新增推理任务
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

        <!-- 操作列（新增执行按钮） -->
        <template v-else-if="column.dataIndex === 'action'">
          <TableAction
            :actions="[
              {
                icon: 'ant-design:play-circle-filled',
                tooltip: '执行',
                onClick: () => handleExecute(record),
                ifShow: () => record.status !== 'PROCESSING'
              },
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
    <!-- 模态框组件 -->
    <ExecuteInferenceModal @register="registerExecuteModal"/>
    <InferenceDetailModal @register="registerDetailModal" :record="state.currentRecord"/>
    <InferenceResultViewer @register="registerResultModal" :record="state.currentRecord"/>
  </div>
</template>

<script lang="ts" setup>
import {reactive} from 'vue';
import {PlayCircleOutlined} from '@ant-design/icons-vue';
import {BasicTable, TableAction, useTable} from '@/components/Table';
import {useModal} from '@/components/Modal';
import {useMessage} from '@/hooks/web/useMessage';
import {getInferenceColumns, getInferenceFormConfig} from "./Data";
import ExecuteInferenceModal from "../ExecuteInferenceModal/index.vue";
import InferenceDetailModal from "../InferenceDetailModal/index.vue";
import InferenceResultViewer from "../InferenceResultViewer/index.vue";
import {deleteInferenceRecord, getInferenceTasks, runInference} from "@/api/device/model";
import {getBasicColumns, getFormConfig} from "@/views/train/components/TrainList/Data";

const params = {};

// 状态管理
const state = reactive({
  records: [],
  currentRecord: {},
  eventSources: {},
  executing: false  // 防止重复执行
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
  title: '推理任务列表',
  api: getInferenceTasks,
  columns: getInferenceColumns(),
  useSearchForm: true,
  formConfig: getInferenceFormConfig(),
  pagination: {pageSize: 10},
  rowKey: 'id',
  showTableSetting: true,
  fetchSetting: {
    listField: 'data',
    totalField: 'total',
  },
});

// 模态框注册
const [registerExecuteModal, {openModal: openExecuteModal}] = useModal();
const [registerDetailModal, {openModal: openDetailModal}] = useModal();
const [registerResultModal, {openModal: openResultModal}] = useModal();

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
  } catch (error) {
    console.error('删除错误:', error);
    createMessage.error('删除失败');
  }
};

// 新增推理任务
const handleExecute = async (record) => {
  if (state.executing) return;

  try {
    state.executing = true;
    createMessage.loading({content: '任务执行中...', key: 'executing', duration: 0});

    // 准备执行参数
    const params = {
      inference_type: record.inference_type,
      input_source: record.input_source
    };

    // 调用API新增推理任务
    const result = await runInference(record.model_id, params);

    if (result.code === 0) {
      createMessage.success({content: '任务执行成功', key: 'executing'});

      // 添加新记录到列表
      const newRecord = {
        ...result.data,
        start_time: formatDateTime(result.data.start_time)
      };

      state.records.unshift(newRecord);
    } else {
      createMessage.error({content: result.msg || '执行失败', key: 'executing'});
    }
  } catch (error) {
    createMessage.error({content: `执行失败: ${error.message}`, key: 'executing'});
    console.error('执行错误:', error);
  } finally {
    state.executing = false;
  }
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
