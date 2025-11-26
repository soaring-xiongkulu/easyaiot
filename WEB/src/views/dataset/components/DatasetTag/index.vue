<template>
  <div class="subDevice-wrapper">
    <BasicTable @register="registerTable">
      <template #toolbar>
        <a-button type="primary"
                  @click="openAddModal(true, { datasetId: route.params['id'], isEdit: false, isView: false })">
          新增数据集标签
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
                onClick: openAddModal.bind(null, true, { datasetId: route.params['id'], isEdit: false, isView: true, record }),
              },
              {
                tooltip: {
                  title: '编辑',
                  placement: 'top',
                },
                icon: 'ant-design:edit-filled',
                onClick: openAddModal.bind(null, true, { datasetId: route.params['id'], isEdit: true, isView: false, record }),
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
              },
            ]"
          />
        </template>
      </template>
    </BasicTable>
    <DatasetTagModal @register="registerAddModel" @success="handleSuccess"/>
  </div>
</template>

<script setup lang="ts" name="devicesPage">
import {getBasicColumns, getFormConfig} from './data';
import {useMessage} from '@/hooks/web/useMessage';
import {BasicTable, TableAction, useTable} from '@/components/Table';
import {useRoute} from "vue-router";
import {useModal} from "@/components/Modal";
import {deleteDatasetTag, getDatasetTagPage} from "@/api/device/dataset";
import DatasetTagModal from "@/views/dataset/components/DatasetTagModal/index.vue";

const {createMessage} = useMessage();

const [registerAddModel, {openModal: openAddModal}] = useModal();

defineOptions({name: 'DatasetTag'})

const route = useRoute()

const [registerTable, {reload}] = useTable({
  title: '数据集标签列表',
  api: getDatasetTagPage,
  columns: getBasicColumns(),
  useSearchForm: true,
  formConfig: getFormConfig(),
  // 添加beforeFetch钩子转换参数
  beforeFetch: (params) => {
    const {...rest} = params;
    rest['datasetId'] = route.params['id'];
    return rest;
  },
  showTableSetting: false,
  tableSetting: {fullScreen: true},
  showIndexColumn: false,
  rowKey: 'id',
  fetchSetting: {
    listField: 'list',
    totalField: 'total',
  },
});

// 表格刷新
function handleSuccess() {
  reload({
    page: 0,
  });
}

const handleDelete = async (record) => {
  try {
    await deleteDatasetTag(record['id']);
    createMessage.success('删除成功');
    handleSuccess();
  } catch (error) {
    console.error(error)
    createMessage.success('删除失败');
    console.log('handleDelete', error);
  }
};
</script>

<style lang="less" scoped>
.device-wrapper {
  :deep(.ant-tabs-nav) {
    padding: 5px 0 0 25px;
  }
}
</style>
