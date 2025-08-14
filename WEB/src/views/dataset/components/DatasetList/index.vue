<template>
  <div>
    <BasicTable @register="registerTable" v-if="state.isTableMode">
      <template #toolbar>
        <a-button type="primary" @click="openAddModal(true, { type: 'add' })">新增数据集
        </a-button>
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
                onClick: goDatasetDetail.bind(record),
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
    <div v-else>
      <DatasetCardList :params="params" :api="getDatasetPage" @get-method="getMethod"
                       @delete="handleDel"
                       @view="handleView" @edit="handleEdit">
        <template #header>
          <a-button type="primary" @click="openAddModal(true, { isEdit: false, isView: false })">
            新增数据集
          </a-button>
          <a-button type="default" @click="handleClickSwap" preIcon="ant-design:swap-outlined">
            切换视图
          </a-button>
        </template>
      </DatasetCardList>
    </div>
    <DatasetModal @register="registerAddModel" @success="handleSuccess"/>
  </div>
</template>
<script lang="ts" setup name="noticeSetting">
import {reactive} from 'vue';
import {BasicTable, TableAction, useTable} from '@/components/Table';
import {useMessage} from '@/hooks/web/useMessage';
import {getBasicColumns, getFormConfig} from "./Data";
import DatasetModal from "@/views/dataset/components/DatasetModal/index.vue";
import {useModal} from "@/components/Modal";
import {useRouter} from "vue-router";
import {deleteDataset, getDatasetPage} from "@/api/device/dataset";

import DatasetCardList from "@/views/dataset/components/DatasetCardList/index.vue";

const [registerAddModel, {openModal: openAddModal}] = useModal();

const router = useRouter();

defineOptions({name: 'DatasetList'})

const state = reactive({
  isTableMode: false,
  activeKey: '1',
  pushActiveKey: '1',
  historyActiveKey: '1',
  SmsActiveKey: '1',
});

// 请求api时附带参数
const params = {};

let cardListReload = () => {
};

// 获取内部fetch方法;
function getMethod(m: any) {
  cardListReload = m;
}

//详情按钮事件
function handleView(record) {
  goDatasetDetail(record);
}

//编辑按钮事件
function handleEdit(record) {
  openAddModal(true, {isEdit: true, isView: false, record: record});
}

//删除按钮事件
function handleDel(record) {
  handleDelete(record);
  cardListReload();
}

// 切换视图
function handleClickSwap() {
  state.isTableMode = !state.isTableMode;
}

// 表格刷新
function handleSuccess() {
  reload({
    page: 0,
  });
  cardListReload();
}

const {createMessage} = useMessage();
const [
  registerTable,
  {
    // setLoading,
    // setColumns,
    // getColumns,
    // getDataSource,
    // getRawDataSource,
    reload,
    // getPaginationRef,
    // setPagination,
    // getSelectRows,
    // getSelectRowKeys,
    // setSelectedRowKeys,
    // clearSelectedRowKeys,
  },
] = useTable({
  canResize: true,
  showIndexColumn: false,
  title: '数据集管理',
  api: getDatasetPage,
  columns: getBasicColumns(),
  useSearchForm: true,
  showTableSetting: false,
  pagination: true,
  formConfig: getFormConfig(),
  fetchSetting: {
    listField: 'data.list',
    totalField: 'data.total',
  },
  rowKey: 'id',
});

const goDatasetDetail = async (record) => {
  const params = {
    id: record.id,
  };
  router.push({name: 'DatasetDetail', params});
};

const handleDelete = async (record) => {
  try {
    await deleteDataset(record['id']);
    createMessage.success('删除成功');
    handleSuccess();
  } catch (error) {
    console.error(error)
    createMessage.success('删除失败');
    console.log('handleDelete', error);
  }
};
</script>
