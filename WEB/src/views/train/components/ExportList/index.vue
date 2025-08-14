<template>
  <div>
    <BasicTable @register="registerTable">
      <!-- 工具栏 -->
      <template #toolbar>
        <a-button type="primary" @click="openExportModal">导出模型</a-button>
      </template>

      <!-- 列自定义渲染 -->
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'action'">
          <TableAction
            :actions="[
              {
                tooltip: '下载',
                icon: 'ant-design:download-filled',
                onClick: handleDownload.bind(null, record),
              },
              {
                tooltip: '删除',
                icon: 'material-symbols:delete-outline-rounded',
                popConfirm: {
                  placement: 'topRight',
                  title: '确定删除此导出模型?',
                  confirm: handleDelete.bind(null, record),
                },
              },
            ]"
          />
        </template>
      </template>
    </BasicTable>

    <ExportModelModal @register="registerExportModal" @success="handleSuccess"/>
  </div>
</template>

<script lang="ts" setup>
import { BasicTable, useTable, TableAction } from '@/components/Table';
import { useModal } from '@/components/Modal';
import { useMessage } from '@/hooks/web/useMessage';
import {
  deleteExportedModel,
  downloadExportedModel,
  exportModel
} from '@/api/device/train';
import ExportModelModal from '../ExportModelModal/index.vue';
import { getExportModelColumns, getSearchFormConfig } from './data';

const { createMessage } = useMessage();

// 注册模态框
const [registerExportModal, { openModal: openExportModal }] = useModal();

const [
  registerTable,
  { reload }
] = useTable({
  title: '导出模型列表',
  api: exportModel,
  columns: getExportModelColumns(),
  useSearchForm: true,
  formConfig: getSearchFormConfig(),
  rowKey: 'model_id',
  fetchSetting: {
    listField: 'data.list',
    totalField: 'data.total',
  },
});

// 下载模型
const handleDownload = async (record) => {
  try {
    await downloadExportedModel(record.model_id);
    createMessage.success('下载成功');
  } catch (error) {
    createMessage.error('下载失败');
    console.error('模型下载失败:', error);
  }
};

// 删除导出模型
const handleDelete = async (record) => {
  try {
    await deleteExportedModel(record.model_id);
    createMessage.success('删除成功');
    reload();
  } catch (error) {
    createMessage.error('删除失败');
    console.error('删除模型失败:', error);
  }
};

// 处理成功回调
const handleSuccess = () => {
  reload();
};
</script>
