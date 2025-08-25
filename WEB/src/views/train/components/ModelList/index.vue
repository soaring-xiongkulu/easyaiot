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
                onClick: goModelDetail.bind(record),
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
                  title: '训练模型',
                  placement: 'top',
                },
                icon: 'ant-design:experiment-outlined', // 训练图标
                onClick: handleTrain.bind(null, record),
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
        @deploy="handleDeploy"
        @train="handleTrain"
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
import { deleteModel, getModelPage } from "@/api/device/model";
import ModelCardList from "../ModelCardList/index.vue";

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
  goModelDetail(record);
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

// 新增部署处理函数
function handleDeploy(record) {
  console.log('处理模型部署', record);
  // 实际部署逻辑
}

// 新增训练处理函数
const handleTrain = async (record) => {
  try {
    // 使用Vue Router跳转到训练页面
    router.push({
      name: 'ModelTraining',
      params: { modelId: record.id },
      query: { modelName: record.name }
    });
  } catch (error) {
    console.error('跳转到训练页面失败:', error);
    createMessage.error('跳转到训练页面失败');
  }
};

const { createMessage } = useMessage();
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

const goModelDetail = async (record) => {
  router.push({ name: 'ModelDetail', params: { id: record.id } });
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
</script>
