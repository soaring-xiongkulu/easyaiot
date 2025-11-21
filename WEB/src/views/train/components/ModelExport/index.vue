<template>
  <div class="model-export-container">
    <BasicTable 
      @register="registerTable" 
      v-if="state.isTableMode"
      @field-value-change="handleTableFieldValueChange"
    >
      <template #toolbar>
        <a-space :size="16">
          <a-button 
            type="primary" 
            @click="handleExport"
            :loading="exportLoading.onnx || exportLoading.openvino"
          >
            <template #icon>
              <ExportOutlined />
            </template>
            导出模型
          </a-button>
          <a-divider type="vertical" />
          <a-button type="default" @click="handleClickSwap" preIcon="ant-design:swap-outlined">
            切换视图
          </a-button>
        </a-space>
      </template>
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'format'">
          <a-tag :color="formatColors[record.format]" class="format-tag">
            {{ formatLabels[record.format] || record.format?.toUpperCase() || '--' }}
          </a-tag>
        </template>
        <template v-else-if="column.dataIndex === 'status'">
          <a-badge 
            :status="getStatusBadgeStatus(record.status)" 
            :text="statusLabels[record.status] || record.status"
            class="status-badge"
          />
        </template>
        <template v-else-if="column.dataIndex === 'created_at'">
          <div class="time-cell">
            <ClockCircleOutlined />
            <span>{{ formatDate(record.created_at) }}</span>
          </div>
        </template>
        <template v-else-if="column.dataIndex === 'action'">
          <a-space>
            <a-button
              type="link"
              size="small"
              :disabled="record.status !== 'COMPLETED'"
              @click="handleDownload(record)"
              class="action-btn"
            >
              <template #icon>
                <DownloadOutlined />
              </template>
              下载
            </a-button>
            <a-popconfirm
              title="确定删除此导出记录吗？"
              ok-text="确认"
              cancel-text="取消"
              @confirm="handleDelete(record)"
            >
              <a-button
                type="link"
                size="small"
                danger
                class="action-btn"
              >
                <template #icon>
                  <DeleteOutlined />
                </template>
                删除
              </a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </BasicTable>
    <div v-else>
      <ModelExportCardList
        :params="params"
        :api="getExportListApi"
        :model-options="modelOptions"
        @get-method="getMethod"
        @delete="handleDel"
        @download="handleDownload"
        @field-value-change="handleFieldValueChange"
      >
        <template #header>
          <a-space :size="16">
            <a-button 
              type="primary" 
              @click="handleExport"
              :loading="exportLoading.onnx || exportLoading.openvino"
            >
              <template #icon>
                <ExportOutlined />
              </template>
              导出模型
            </a-button>
            <a-divider type="vertical" />
            <a-button type="default" @click="handleClickSwap" preIcon="ant-design:swap-outlined">
              切换视图
            </a-button>
          </a-space>
        </template>
      </ModelExportCardList>
    </div>
    <ExportConfirmModal 
      @register="registerExportModal" 
      @confirm="handleExportConfirm"
      :model-options="modelOptions"
    />
  </div>
</template>

<script lang="ts" setup name="ModelExport">
import { reactive, ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue';
import { BasicTable, useTable } from '@/components/Table';
import { useMessage } from '@/hooks/web/useMessage';
import { getBasicColumns, getFormConfig } from './Data';
import ModelExportCardList from './ModelExportCardList.vue';
import ExportConfirmModal from './ExportConfirmModal.vue';
import { useModal } from '@/components/Modal';
import {
  getModelPage,
  exportModel,
  getExportModelList,
  deleteExportedModel,
  downloadExportedModel,
  getExportStatus,
} from '@/api/device/model';
import {
  DownloadOutlined,
  ExportOutlined,
  ClockCircleOutlined,
  DeleteOutlined,
} from '@ant-design/icons-vue';
import dayjs from 'dayjs';
import { message } from 'ant-design-vue';

defineOptions({ name: 'ModelExport' });

const { createMessage } = useMessage();

// 导出确认弹框
const [registerExportModal, { openModal: openExportModal, closeModal: closeExportModal }] = useModal();

// 格式标签映射
const formatLabels: Record<string, string> = {
  onnx: 'ONNX',
  openvino: 'OpenVINO',
};

// 格式颜色映射
const formatColors: Record<string, string> = {
  onnx: 'green',
  openvino: 'cyan',
};

// 状态标签映射
const statusLabels: Record<string, string> = {
  PENDING: '等待中',
  PROCESSING: '处理中',
  COMPLETED: '已完成',
  FAILED: '失败',
};

// 状态徽章映射
const getStatusBadgeStatus = (status: string): 'default' | 'processing' | 'success' | 'error' => {
  const statusMap: Record<string, 'default' | 'processing' | 'success' | 'error'> = {
    PENDING: 'default',
    PROCESSING: 'processing',
    COMPLETED: 'success',
    FAILED: 'error',
  };
  return statusMap[status] || 'default';
};

// 视图模式
const state = reactive({
  isTableMode: false,
});

// 数据状态
const models = ref<any[]>([]);
const modelOptions = ref<any[]>([]);
const exportLoading = reactive({
  onnx: false,
  openvino: false,
});
const pollingIntervals = ref<Map<number | string, NodeJS.Timeout>>(new Map());
const modelsLoading = ref(false);
const modelsLoaded = ref(false);

const params = {};
let cardListReload = () => {};

function getMethod(m: any) {
  cardListReload = m;
}

function handleClickSwap() {
  state.isTableMode = !state.isTableMode;
}

function handleSuccess() {
  reload({ page: 0 });
  cardListReload();
}

function handleDel(record: any) {
  handleDelete(record);
  cardListReload();
}

// 处理表单字段值变化（卡片模式，实时监听）
function handleFieldValueChange(field: string, value: any) {
  // 不再需要处理 model_id 变化
}

// 处理表格表单字段值变化（表格模式，实时监听）
function handleTableFieldValueChange(field: string, value: any) {
  // 不再需要处理 model_id 变化
}

// 判断是否为 pt 模型（可导出的模型）
const isPtModel = (model: any): boolean => {
  if (!model.model_path) {
    return false;
  }
  
  const modelPath = model.model_path.toLowerCase();
  return !modelPath.endsWith('.onnx') && (modelPath.endsWith('.pt') || !model.onnx_model_path);
};

// 加载模型列表（只加载 pt 格式的模型）
const loadModels = async () => {
  // 如果正在加载或已加载，避免重复请求
  if (modelsLoading.value || modelsLoaded.value) {
    return;
  }
  
  modelsLoading.value = true;
  try {
    const response = await getModelPage({ page: 1, size: 100 });
    // 处理响应数据：可能是转换后的数组，也可能是包含 code/data 的对象
    let allModels: any[] = [];
    if (Array.isArray(response)) {
      // 如果响应直接是数组（已转换）
      allModels = response;
    } else if (response && response.code === 0 && response.data) {
      // 如果响应包含 code 和 data
      allModels = Array.isArray(response.data) ? response.data : [];
    } else if (response && response.data && Array.isArray(response.data)) {
      // 如果响应有 data 字段且是数组
      allModels = response.data;
    } else if (response && Array.isArray(response)) {
      allModels = response;
    }
    
    models.value = allModels.filter(isPtModel);
    
    // 构建选项列表
    modelOptions.value = models.value.map((model: any) => ({
      label: `${model.name} (v${model.version})`,
      value: model.id,
    }));
    
    modelsLoaded.value = true;
    
    if (models.value.length === 0) {
      createMessage.info('当前没有可导出的 pt 模型');
    }
  } catch (error: any) {
    console.error('加载模型列表失败:', error);
    createMessage.error('加载模型列表失败');
    modelsLoaded.value = false; // 失败时重置，允许重试
  } finally {
    modelsLoading.value = false;
  }
};

// 导出列表API
const getExportListApi = async (params: any) => {
  try {
    const res = await getExportModelList({
      model_id: params.model_id || undefined,
      format: params.format || undefined,
      status: params.status || undefined,
      page: params.page || 1,
      per_page: params.pageSize || 10,
    });
    
    // transformResponseHook 会在 code === 0 时返回 data 部分
    // 所以 res 应该是 { items: [...], total: ... } 格式
    const data = res || {};
    
    // 为每个记录添加模型名称
    const items = (data.items || []).map((item: any) => {
      const model = models.value.find((m: any) => m.id === item.model_id);
      return {
        ...item,
        model_name: model?.name || `模型${item.model_id}`,
      };
    });
    
    return {
      success: true,
      data: {
        items,
        total: data.total || 0,
      },
    };
  } catch (error: any) {
    console.error('获取导出列表失败:', error);
    return {
      success: false,
      data: {
        items: [],
        total: 0,
      },
    };
  }
};

// 表格配置
const [registerTable, { reload, getForm }] = useTable({
  canResize: true,
  showIndexColumn: false,
  title: '模型导出记录',
  api: async (params) => {
    try {
      const res = await getExportListApi({
        ...params,
        page: params.page || 1,
        pageSize: params.pageSize || 10,
      });
      
      if (res.success && res.data) {
        return {
          list: res.data.items || [],
          total: res.data.total || 0,
        };
      }
      
      return {
        list: [],
        total: 0,
      };
    } catch (error) {
      console.error('获取导出列表失败:', error);
      return {
        list: [],
        total: 0,
      };
    }
  },
  columns: getBasicColumns(),
  useSearchForm: true,
  showTableSetting: false,
  pagination: true,
  formConfig: getFormConfig(),
  fetchSetting: {
    listField: 'list',
    totalField: 'total',
  },
  rowKey: 'id',
});


// 打开导出确认弹框
const handleExport = () => {
  // 打开确认弹框，让用户在弹框中选择模型和格式
  openExportModal(true, {});
};

// 确认导出后执行实际导出
const handleExportConfirm = async (data: {
  modelId: number;
  format: 'onnx' | 'openvino';
  exportParams: { img_size: number; opset: number };
}) => {
  const { modelId, format, exportParams } = data;

  if (!modelId || !format) {
    createMessage.warning('请选择PT模型和导出格式');
    return;
  }

  exportLoading[format] = true;
  try {
    const res = await exportModel(modelId, format, exportParams);
    
    // transformResponseHook 会在 code === 0 时返回 data 部分
    // 所以 res 应该是 { task_id, export_id, ... } 格式
    if (res) {
      createMessage.success('导出任务已提交，请稍后刷新查看');
      
      // 关闭弹框
      closeExportModal();
      
      // 刷新列表
      handleSuccess();
      
      // 开始轮询状态
      const taskId = res.task_id;
      const exportId = res.export_id;
      if (taskId) {
        startPollingByTaskId(taskId);
      } else if (exportId) {
        startPolling(exportId);
      }
    } else {
      throw new Error('导出失败');
    }
  } catch (error: any) {
    console.error('导出失败:', error);
    createMessage.error(error.message || '导出失败，请重试');
    // 导出失败时，关闭弹框（弹框会自动重置状态）
    setTimeout(() => {
      closeExportModal();
    }, 1500);
  } finally {
    exportLoading[format] = false;
  }
};

// 状态轮询（通过export_id）
const startPolling = (exportId: number) => {
  if (pollingIntervals.value.has(exportId)) {
    clearInterval(pollingIntervals.value.get(exportId)!);
  }

  const interval = setInterval(async () => {
    try {
      const statusRes = await getExportStatus(exportId);
      
      // transformResponseHook 会在 code === 0 时返回 data 部分
      // 所以 statusRes 应该是 { status, ... } 格式
      if (statusRes && (statusRes.status === 'COMPLETED' || statusRes.status === 'FAILED')) {
        clearInterval(interval);
        pollingIntervals.value.delete(exportId);
        
        if (statusRes.status === 'FAILED') {
          createMessage.error(`导出失败: ${statusRes.error || '未知错误'}`);
        } else {
          createMessage.success('导出完成');
        }
        
        handleSuccess();
      }
    } catch (error) {
      console.error('状态检查失败', error);
    }
  }, 5000);

  pollingIntervals.value.set(exportId, interval);
};

// 状态轮询（通过task_id）
const startPollingByTaskId = (taskId: string) => {
  if (pollingIntervals.value.has(taskId)) {
    clearInterval(pollingIntervals.value.get(taskId)!);
  }

  const interval = setInterval(async () => {
    try {
      const statusRes = await getExportStatus(taskId);
      
      // transformResponseHook 会在 code === 0 时返回 data 部分
      // 所以 statusRes 应该是 { status, ... } 格式
      if (statusRes && (statusRes.status === 'COMPLETED' || statusRes.status === 'FAILED')) {
        clearInterval(interval);
        pollingIntervals.value.delete(taskId);
        
        if (statusRes.status === 'FAILED') {
          createMessage.error(`导出失败: ${statusRes.error || '未知错误'}`);
        } else {
          createMessage.success('导出完成');
        }
        
        handleSuccess();
      }
    } catch (error) {
      console.error('状态检查失败', error);
    }
  }, 5000);

  pollingIntervals.value.set(taskId, interval);
};

// 下载导出文件
const handleDownload = async (record: any) => {
  if (record.status !== 'COMPLETED') {
    createMessage.warning('导出任务尚未完成，请稍后再试');
    return;
  }

  try {
    const response = await downloadExportedModel(record.id);
    
    // 处理blob响应
    let blob: Blob;
    if (response instanceof Blob) {
      blob = response;
    } else if (response.data instanceof Blob) {
      blob = response.data;
    } else {
      throw new Error('无效的响应格式');
    }
    
    // 创建下载链接
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    
    // 从响应头或记录中获取文件名
    const fileName = `${record.model_id || 'model'}_${record.format}.${getFileExtension(record.format)}`;
    link.download = fileName;
    
    document.body.appendChild(link);
    link.click();
    
    // 清理资源
    setTimeout(() => {
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    }, 100);

    createMessage.success('文件下载成功');
  } catch (error: any) {
    console.error('下载失败:', error);
    createMessage.error(error.message || '下载失败，请重试');
  }
};

// 删除导出记录
const handleDelete = async (record: any) => {
  try {
    await deleteExportedModel(record.id);
    createMessage.success('导出记录已删除');
    handleSuccess();
  } catch (error: any) {
    console.error('删除失败:', error);
    createMessage.error(error.message || '删除失败，请重试');
  }
};

// 获取文件扩展名
const getFileExtension = (format: string): string => {
  const extensions: Record<string, string> = {
    onnx: 'onnx',
    openvino: 'zip', // OpenVINO导出为目录，通常打包为zip
  };
  return extensions[format] || 'bin';
};

// 格式化日期
const formatDate = (dateString: string): string => {
  if (!dateString) return '--';
  try {
    return dayjs(dateString).format('YYYY-MM-DD HH:mm:ss');
  } catch (e) {
    return dateString;
  }
};

// 初始化
onMounted(() => {
  loadModels();
});

// 组件卸载时清理轮询
onUnmounted(() => {
  pollingIntervals.value.forEach((interval) => {
    clearInterval(interval);
  });
  pollingIntervals.value.clear();
});
</script>

<style lang="less" scoped>
.model-export-container {
  padding: 16px;
  background: #f0f2f5;
  min-height: calc(100vh - 200px);

  .format-tag {
    font-weight: 500;
    padding: 4px 12px;
    border-radius: 4px;
  }

  .status-badge {
    :deep(.ant-badge-status-text) {
      font-size: 13px;
      color: #1f2c3d;
    }
  }

  .time-cell {
    display: flex;
    align-items: center;
    gap: 6px;
    color: #666;
    font-size: 13px;

    :deep(.anticon) {
      color: #8c8c8c;
    }
  }

  .action-btn {
    padding: 0;
    height: auto;
    font-size: 13px;

    &:hover {
      color: #1890ff;
    }
  }
}
</style>
