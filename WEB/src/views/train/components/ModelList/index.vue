<template>
  <div>
    <BasicTable @register="registerTable" v-if="state.isTableMode">
      <template #toolbar>
        <a-button type="primary" @click="openAddModal(true, { type: 'add' })">新增模型</a-button>
        <a-button type="default" @click="handleClickSwap" preIcon="ant-design:swap-outlined">
          切换视图
        </a-button>
      </template>
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'action'">
          <TableAction
            :actions="[
              {
                icon: 'ant-design:eye-filled',
                tooltip: {
                  title: '详情',
                  placement: 'top',
                },
                onClick: goTrainDetail.bind(record),
              },
              {
                tooltip: {
                  title: '编辑',
                  placement: 'top',
                },
                icon: 'ant-design:edit-filled',
                onClick: openAddModal.bind(null, true, { isEdit: true, isView: false, record }),
              },
              {
                tooltip: {
                  title: '下载模型',
                  placement: 'top',
                },
                icon: 'ant-design:download-outlined',
                onClick: handleDownload.bind(null, record),
              },
              {
                tooltip: {
                  title: '删除',
                  placement: 'top',
                },
                icon: 'material-symbols:delete-outline-rounded',
                popConfirm: {
                  placement: 'topRight',
                  title: '是否确认删除？',
                  confirm: handleDelete.bind(null, record),
                },
              }
            ]"
          />
        </template>
      </template>
    </BasicTable>
    <div v-else>
      <ModelCardList
        :params="params"
        :api="getModelPage"
        @get-method="getMethod"
        @delete="handleDel"
        @view="handleView"
        @edit="handleEdit"
        @train="handleTrain"
        @download="handleDownload"
      >
      <template #header>
        <a-button type="primary" @click="openAddModal(true, { isEdit: false, isView: false })">
          新增模型
        </a-button>
        <a-button type="default" @click="handleClickSwap" preIcon="ant-design:swap-outlined">
          切换视图
        </a-button>
      </template>
      </ModelCardList>
    </div>
    <ModelModal @register="registerAddModel" @success="handleSuccess"/>
  </div>
</template>

<script lang="ts" setup name="modelManagement">
import { reactive } from 'vue';
import { BasicTable, TableAction, useTable } from '@/components/Table';
import { useMessage } from '@/hooks/web/useMessage';
import { getBasicColumns, getFormConfig } from "./data";
import ModelModal from "../ModelModal/index.vue";
import { useModal } from "@/components/Modal";
import { useRouter } from "vue-router";
import { deleteModel, getModelPage, downloadModel } from "@/api/device/model";
import ModelCardList from "../ModelCardList/index.vue";

const { createMessage, createConfirm } = useMessage();

const [registerAddModel, { openModal: openAddModal }] = useModal();
const router = useRouter();

defineOptions({ name: 'ModelList' })

const state = reactive({
  isTableMode: false,
});

const params = {};
let cardListReload = () => {};

function getMethod(m: any) {
  cardListReload = m;
}

function handleView(record) {
  goTrainDetail(record);
}

function handleEdit(record) {
  openAddModal(true, { isEdit: true, isView: false, record });
}

function handleDel(record) {
  handleDelete(record);
  cardListReload();
}

function handleClickSwap() {
  state.isTableMode = !state.isTableMode;
}

function handleSuccess() {
  reload({ page: 0 });
  cardListReload();
}

// 新增训练处理函数
const handleTrain = async (record) => {
  try {
    // 使用Vue Router跳转到训练页面
    router.push({
      name: 'ModelTrain',
      params: { modelId: record.id },
      query: { modelName: record.name }
    });
  } catch (error) {
    console.error('跳转到训练页面失败:', error);
    createMessage.error('跳转到训练页面失败');
  }
};

const [registerTable, { reload }] = useTable({
  canResize: true,
  showIndexColumn: false,
  title: '模型管理',
  api: getModelPage,
  columns: getBasicColumns(),
  useSearchForm: true,
  showTableSetting: false,
  pagination: true,
  formConfig: getFormConfig(),
  fetchSetting: {
    listField: 'data',
    totalField: 'total',
  },
  rowKey: 'id',
});

const goTrainDetail = async (record) => {
  router.push({ name: 'TrainTaskDetail', params: { modelId: record.id } });
};

const handleDelete = async (record) => {
  try {
    await deleteModel(record.id);
    createMessage.success('删除成功');
    handleSuccess();
  } catch (error) {
    console.error(error);
    createMessage.error('删除失败');
  }
};

// 下载模型处理函数
const handleDownload = async (record) => {
  try {
    const token = localStorage.getItem('jwt_token');
    
    // 优先使用后台返回的 model_path 或 onnx_model_path（MinIO 路径）
    const modelPath = record.model_path || record.onnx_model_path;
    
    let downloadUrl;
    if (modelPath) {
      // 如果 model_path 是完整的 MinIO 路径（以 /api/v1/buckets 开头），直接使用
      // nginx 会自动代理到 MinIO
      if (modelPath.startsWith('/api/v1/buckets')) {
        downloadUrl = modelPath;
      } else if (modelPath.startsWith('http://') || modelPath.startsWith('https://')) {
        // 如果是完整的 HTTP URL，直接使用
        downloadUrl = modelPath;
      } else {
        // 如果是相对路径，可能需要添加前缀（根据实际情况调整）
        downloadUrl = modelPath;
      }
    } else {
      // 如果没有 model_path，使用后端下载接口作为备选方案
      downloadUrl = `/api/model/${record.id}/download`;
    }

    // 使用 fetch 下载文件（支持认证头）
    const response = await fetch(downloadUrl, {
      method: 'GET',
      headers: {
        'X-Authorization': 'Bearer ' + token,
      },
    });

    if (!response.ok) {
      // 如果是404，尝试解析错误消息
      if (response.status === 404) {
        const errorData = await response.json().catch(() => ({}));
        createMessage.warning(errorData.msg || '该模型没有可下载的文件');
        return;
      }
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.msg || '下载失败: ' + response.statusText);
    }

    // 获取文件 blob
    const blob = await response.blob();
    
    // 从响应头获取文件名，如果没有则根据模型路径确定
    const contentDisposition = response.headers.get('Content-Disposition');
    let fileName = `${record.name}_${record.version || 'v1.0.0'}.pt`;
    
    if (contentDisposition) {
      const fileNameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
      if (fileNameMatch && fileNameMatch[1]) {
        fileName = fileNameMatch[1].replace(/['"]/g, '');
      }
    } else if (modelPath) {
      // 从 MinIO 路径中提取文件名
      try {
        const urlObj = new URL(modelPath, window.location.origin);
        const prefix = urlObj.searchParams.get('prefix');
        if (prefix) {
          const pathParts = prefix.split('/');
          fileName = pathParts[pathParts.length - 1] || fileName;
        }
      } catch (e) {
        // 如果解析失败，根据模型类型确定扩展名
        const fileExt = record.onnx_model_path && !record.model_path ? '.onnx' : '.pt';
        fileName = `${record.name}_${record.version || 'v1.0.0'}${fileExt}`;
      }
    } else {
      // 根据模型路径确定文件扩展名
      const fileExt = record.onnx_model_path && !record.model_path ? '.onnx' : '.pt';
      fileName = `${record.name}_${record.version || 'v1.0.0'}${fileExt}`;
    }
    
    // 创建下载链接
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    
    createMessage.success('模型下载成功');
  } catch (error) {
    console.error('下载模型失败:', error);
    createMessage.error('下载模型失败: ' + (error.message || '未知错误'));
  }
};
</script>
