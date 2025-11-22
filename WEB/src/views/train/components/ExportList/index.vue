<template>
  <div class="model-export-container">
    <!-- 标题与描述 -->
    <div class="header-section">
      <h2 class="page-title">模型导出管理</h2>
      <p class="page-description">管理已导出的模型文件，支持下载或删除操作</p>
    </div>

    <!-- 搜索过滤区 -->
    <div class="filter-section">
      <a-input-search
        v-model:value="searchValue"
        placeholder="搜索模型名称"
        @search="handleSearch"
        class="search-input"
      />
      <a-select
        v-model:value="formatFilter"
        placeholder="筛选导出格式"
        class="format-filter"
        :options="formatOptions"
      />
    </div>

    <!-- 表格主体 -->
    <BasicTable
      @register="registerTable"
      :bordered="true"
      :row-selection="false"
      class="model-table"
    >
      <!-- 工具栏：导出按钮 -->
      <template #toolbar>
        <a-dropdown>
          <template #overlay>
            <a-menu @click="handleFormatSelect">
              <a-menu-item v-for="format in exportFormats" :key="format.value">
                {{ format.label }}
              </a-menu-item>
            </a-menu>
          </template>
          <a-button type="primary" class="export-btn">
            <template #icon>
              <ExportOutlined />
            </template>
            导出模型
          </a-button>
        </a-dropdown>
      </template>

      <!-- 空状态提示 -->
      <template #empty>
        <a-empty description="暂无导出记录" image="/images/empty.svg">
          <p class="empty-tip">提示：导出任务通常需要3-5分钟完成</p>
          <a-button type="primary" @click="openExportModal">立即导出</a-button>
        </a-empty>
      </template>

      <!-- 列自定义渲染 -->
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'format'">
          <a-tag :color="formatColors[record.format]">
            {{ formatLabels[record.format] || record.format }}
          </a-tag>
        </template>
        <template v-else-if="column.dataIndex === 'status'">
          <a-tag :color="statusColors[record.status]">
            {{ statusLabels[record.status] }}
          </a-tag>
        </template>
        <template v-else-if="column.dataIndex === 'created_at'">
          {{ formatDate(record.created_at) }}
        </template>
        <template v-else-if="column.dataIndex === 'size'">
          {{ record.size ? formatFileSize(record.size) : '-' }}
        </template>
        <template v-else-if="column.dataIndex === 'action'">
          <TableAction
            :actions="[
              {
                label: '下载',
                icon: 'ant-design:download-filled',
                color: 'primary',
                disabled: record.status !== 'COMPLETED',
                tooltip: record.status !== 'COMPLETED' ? '等待导出完成' : '',
                onClick: () => handleDownload(record),
              },
              {
                label: '删除',
                icon: 'material-symbols:delete-outline-rounded',
                color: 'error',
                popConfirm: {
                  placement: 'topRight',
                  title: '确定删除此导出记录?',
                  okText: '确认',
                  cancelText: '取消',
                  confirm: () => handleDelete(record),
                },
              },
            ]"
          />
        </template>
      </template>
    </BasicTable>

    <!-- 导出配置模态框 -->
    <a-modal
      v-model:visible="exportModalVisible"
      title="模型导出配置"
      :footer="null"
      width="600px"
      centered
      :destroyOnClose="true"
    >
      <a-form
        :model="exportForm"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 16 }"
        @finish="handleExportSubmit"
      >
        <a-form-item label="目标平台" v-if="selectedFormat === 'rknn'">
          <a-select v-model:value="exportForm.target_platform">
            <a-select-option value="rk3588">RK3588</a-select-option>
            <a-select-option value="rk3566">RK3566</a-select-option>
            <a-select-option value="rk3399">RK3399</a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="量化配置" v-if="selectedFormat === 'rknn'">
          <a-switch v-model:checked="exportForm.quantization" />
          <a-tooltip title="量化可减少模型大小但可能影响精度">
            <question-circle-outlined class="info-icon" />
          </a-tooltip>
        </a-form-item>

        <a-form-item label="图像尺寸">
          <a-input-number v-model:value="exportForm.img_size" :min="128" :max="1024" />
        </a-form-item>

        <a-form-item label="OPSet版本" v-if="selectedFormat === 'onnx'">
          <a-input-number v-model:value="exportForm.opset" :min="10" :max="15" />
        </a-form-item>

        <a-form-item :wrapper-col="{ span: 14, offset: 6 }">
          <a-button type="primary" html-type="submit" :loading="exportLoading">
            开始导出
          </a-button>
          <a-button style="margin-left: 10px" @click="exportModalVisible = false">
            取消
          </a-button>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import {
  BasicTable,
  useTable,
  TableAction
} from '@/components/Table';
import {
  ExportOutlined,
  QuestionCircleOutlined
} from '@ant-design/icons-vue';
import {
  Empty,
  message
} from 'ant-design-vue';
import {
  deleteExportedModel,
  downloadExportedModel,
  getExportModelList,
  exportModel,
  getExportStatus // 新增状态查询接口
} from '@/api/device/model';
import { getExportModelColumns } from './data';
import dayjs from 'dayjs';

const route = useRoute();
const modelId = ref(route.params.modelId ? parseInt(route.params.modelId as string) : 0);

// 导出格式选项
const exportFormats = [
  { value: 'rknn', label: 'RKNN格式' },
  { value: 'onnx', label: 'ONNX格式' },
  { value: 'torchscript', label: 'TorchScript格式' },
  { value: 'tensorrt', label: 'TensorRT格式' },
  { value: 'openvino', label: 'OpenVINO格式' },
];

// 格式标签映射
const formatLabels = {
  rknn: 'RKNN',
  onnx: 'ONNX',
  torchscript: 'TorchScript',
  tensorrt: 'TensorRT',
  openvino: 'OpenVINO',
};

// 格式颜色映射
const formatColors = {
  rknn: 'blue',
  onnx: 'green',
  torchscript: 'purple',
  tensorrt: 'volcano',
  openvino: 'cyan',
};

// 状态常量（新增）
const exportStatus = {
  PENDING: 'PENDING',
  PROCESSING: 'PROCESSING',
  COMPLETED: 'COMPLETED',
  FAILED: 'FAILED'
};

const statusLabels = {
  PENDING: '等待中',
  PROCESSING: '处理中',
  COMPLETED: '已完成',
  FAILED: '失败'
};

const statusColors = {
  PENDING: 'orange',
  PROCESSING: 'blue',
  COMPLETED: 'green',
  FAILED: 'red'
};

// 搜索和过滤
const searchValue = ref('');
const formatFilter = ref('');
const formatOptions = exportFormats.map(f => ({ value: f.value, label: f.label }));

// 导出模态框状态
const exportModalVisible = ref(false);
const exportLoading = ref(false);
const selectedFormat = ref('');
const exportForm = reactive({
  target_platform: 'rk3588',
  quantization: true,
  img_size: 640,
  opset: 12,
  dataset: '',
});

// 表格配置
const [registerTable, { reload, updateTableDataRecord }] = useTable({
  title: '',
  api: async (params) => {
    const { page, pageSize, ...queryParams } = params;
    const res = await getExportModelList({
      model_id: modelId.value,
      format: formatFilter.value,
      search: searchValue.value,
      page,
      page_size: pageSize,
    });
    // 后端返回的是items，需要转换为list
    return {
      list: res.data.items || res.data.list || [],
      total: res.data.total || 0,
    };
  },
  columns: getExportModelColumns(),
  useSearchForm: false,
  rowKey: 'id',
  pagination: { pageSize: 8 },
});

// 初始化加载数据
onMounted(() => {
  reload();
});

// 处理搜索
const handleSearch = () => {
  reload();
};

// 选择导出格式
const handleFormatSelect = ({ key }) => {
  selectedFormat.value = key;
  exportModalVisible.value = true;

  // 重置表单
  Object.assign(exportForm, {
    target_platform: 'rk3588',
    quantization: true,
    img_size: 640,
    opset: 12,
    dataset: '',
  });
};

// 提交导出（重构）
const handleExportSubmit = async () => {
  exportLoading.value = true;
  try {
    const res = await exportModel(modelId.value, selectedFormat.value, exportForm);
    message.success('导出任务已提交，请稍后刷新查看');

    // 添加临时记录到表格
    const tempRecord = {
      id: Date.now(), // 临时ID
      exportId: res.exportId,
      model_name: currentModelName,
      format: selectedFormat.value,
      status: exportStatus.PENDING,
      created_at: new Date().toISOString(),
      size: 0
    };

    // 添加到表格数据（伪代码，需根据实际表格实现）
    addTableRow(tempRecord);

    // 开始轮询状态
    startPolling(res.exportId);
  } catch (error) {
    message.error(`导出失败: ${error.message}`);
  } finally {
    exportLoading.value = false;
    exportModalVisible.value = false;
  }
};

// 状态轮询（新增）
const startPolling = (exportId: string) => {
  const pollingInterval = setInterval(async () => {
    try {
      const statusRes = await getExportStatus(exportId);

      // 更新表格中对应记录的状态
      updateRecordStatus(exportId, statusRes.status, statusRes.size);

      if (statusRes.status === exportStatus.COMPLETED ||
        statusRes.status === exportStatus.FAILED) {
        clearInterval(pollingInterval);

        if (statusRes.status === exportStatus.FAILED) {
          message.error(`导出失败: ${statusRes.errorMessage}`);
        }
      }
    } catch (error) {
      console.error('状态检查失败', error);
    }
  }, 5000); // 每5秒检查一次
};

// 下载模型（重构）
const handleDownload = async (record) => {
  if (record.status !== exportStatus.COMPLETED) {
    message.warning('导出任务尚未完成，请稍后再试');
    return;
  }

  try {
    // 调用新接口获取文件流
    const blob = await downloadExportedModel(record.exportId);

    // 创建下载链接
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${record.model_name}_${record.format}.${getFileExtension(record.format)}`;
    document.body.appendChild(link);
    link.click();

    // 清理资源
    setTimeout(() => {
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    }, 100);

    message.success('文件下载成功');
  } catch (error) {
    // 细化错误处理
    if (error.response?.status === 404) {
      message.error('文件不存在，请重新导出');
      updateRecordStatus(record.exportId, exportStatus.FAILED);
    } else if (error.response?.status === 403) {
      message.error('无下载权限，请联系管理员');
    } else {
      message.error(`下载失败: ${error.message}`);
    }
  }
};

// 删除模型
const handleDelete = async (record) => {
  try {
    await deleteExportedModel(record.id);
    message.success(`已删除 ${record.model_name} 的导出记录`);
    reload();
  } catch (error) {
    message.error('删除操作失败');
    console.error('模型删除异常:', error);
  }
};

// 辅助函数：获取文件扩展名（新增）
const getFileExtension = (format: string) => {
  const extensions = {
    rknn: 'rknn',
    onnx: 'onnx',
    torchscript: 'pt',
    tensorrt: 'engine',
    openvino: 'xml'
  };
  return extensions[format] || 'bin';
};

// 辅助函数：格式化文件大小（新增）
const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// 日期格式化（优化）
const formatDate = (dateString: string) => {
  return dayjs(dateString).fromNow() + ` (${dayjs(dateString).format('MM-DD HH:mm')})`;
};

// 表格操作方法（新增）
const addTableRow = (record) => {
  // 根据实际表格组件的API实现添加行逻辑
};

const updateRecordStatus = (exportId: string, status: string, size?: number) => {
  // 根据实际表格组件的API实现更新行逻辑
};
</script>

<style lang="less" scoped>
.model-export-container {
  padding: 24px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;

  .header-section {
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid #f0f0f0;

    .page-title {
      margin-bottom: 8px;
      font-weight: 600;
      color: #1f2c3d;
      font-size: 20px;
    }

    .page-description {
      color: #5e6d82;
      font-size: 14px;
    }
  }

  .filter-section {
    display: flex;
    gap: 16px;
    margin-bottom: 24px;

    .search-input {
      width: 300px;
    }

    .format-filter {
      width: 200px;
    }
  }

  .export-btn {
    margin-bottom: 16px;
    box-shadow: 0 2px 8px rgba(24, 144, 255, 0.3);
    transition: all 0.3s;

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(24, 144, 255, 0.4);
    }
  }

  :deep(.model-table) {
    .ant-table-thead > tr > th {
      background-color: #f8fbff;
      font-weight: 600;
      color: #1f2c3d;
    }

    .ant-table-row {
      transition: background 0.3s;

      &:hover {
        background-color: #f9fafc;
      }
    }
  }

  .info-icon {
    margin-left: 8px;
    color: #8c8c8c;
    cursor: pointer;
  }

  /* 新增状态标签样式 */
  .ant-tag {
    &-orange { background: #fff7e6; border-color: #ffd591; color: #fa8c16; }
    &-blue { background: #e6f7ff; border-color: #91d5ff; color: #1890ff; }
    &-green { background: #f6ffed; border-color: #b7eb8f; color: #52c41a; }
    &-red { background: #fff1f0; border-color: #ffa39e; color: #f5222d; }
  }

  /* 禁用按钮样式 */
  .ant-btn[disabled] {
    opacity: 0.6;
    cursor: not-allowed;
  }

  /* 空状态提示 */
  .empty-tip {
    color: #8c8c8c;
    margin-bottom: 16px;
    font-size: 13px;
  }
}
</style>
