<template>
  <div>
    <BasicTable @register="registerTable" v-if="state.isTableMode">
      <template #toolbar>
        <a-button type="primary" @click="openAddModal(true, { type: 'add' })">新增数据仓</a-button>
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
                tooltip: { title: '详情', placement: 'top' },
                onClick: openAddModal.bind(null, true, { isEdit: false, isView: true, record }),
              },
              {
                tooltip: { title: '编辑', placement: 'top' },
                icon: 'ant-design:edit-filled',
                onClick: openAddModal.bind(null, true, { isEdit: true, isView: false, record }),
              },
              {
                tooltip: { title: '管理数据集', placement: 'top' },
                icon: 'ant-design:link-outlined',
                onClick: manageDatasets.bind(null, record),
              },
              {
                tooltip: { title: '删除', placement: 'top' },
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
      <WarehouseCardList
        :params="params"
        :api="getWarehousePage"
        @get-method="getMethod"
        @delete="handleDel"
        @view="handleView"
        @edit="handleEdit"
        @manage="manageDatasets"
      >
        <template #header>
          <a-button type="primary" @click="openAddModal(true, { isEdit: false, isView: false })">
            新增数据仓
          </a-button>
          <a-button type="default" @click="handleClickSwap" preIcon="ant-design:swap-outlined">
            切换视图
          </a-button>
        </template>
      </WarehouseCardList>
    </div>
    <WarehouseModal @register="registerAddModel" @success="handleSuccess"/>
  </div>
</template>

<script lang="ts" setup name="warehouseManagement">
import {reactive} from 'vue';
import {BasicTable, TableAction, useTable} from '@/components/Table';
import {useMessage} from '@/hooks/web/useMessage';
import {getBasicColumns, getFormConfig} from "./Data";
import WarehouseModal from "@/views/dataset/components/WarehouseModal/index.vue";
import {useModal} from "@/components/Modal";
import {useRouter} from "vue-router";
import {deleteWarehouse, getWarehousePage} from "@/api/device/dataset";
import WarehouseCardList from "@/views/dataset/components/WarehouseCardList/index.vue";

const [registerAddModel, {openModal: openAddModal}] = useModal();
const router = useRouter();
const {createMessage} = useMessage();

defineOptions({name: 'WarehouseList'});

const state = reactive({
  isTableMode: false,
});

// 请求参数
const params = {};

let cardListReload = () => {
};

// 获取内部fetch方法
function getMethod(m: any) {
  cardListReload = m;
}

// 详情按钮事件
function handleView(record) {
  openAddModal(true, {isEdit: false, isView: true, record: record});
}

// 编辑按钮事件
function handleEdit(record) {
  openAddModal(true, {isEdit: true, isView: false, record: record});
}

// 删除按钮事件
function handleDel(record) {
  handleDelete(record);
  cardListReload();
}

// 管理数据集
function manageDatasets(record) {
  router.push({name: 'WarehouseDetail', params: {id: record.id}});
}

// 切换视图
function handleClickSwap() {
  state.isTableMode = !state.isTableMode;
}

// 表格刷新
function handleSuccess() {
  reload();
  cardListReload();
}

const [
  registerTable,
  {
    reload,
  },
] = useTable({
  canResize: true,
  showIndexColumn: false,
  title: '数据仓管理',
  api: getWarehousePage,
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

const goWarehouseDetail = async (record) => {
  router.push({name: 'WarehouseDetail', params: {id: record.id}});
};

const handleDelete = async (record) => {
  try {
    await deleteWarehouse(record.id);
    createMessage.success('删除成功');
    handleSuccess();
  } catch (error) {
    console.error(error);
    createMessage.error('删除失败');
  }
};
</script>
