<template>
  <div>
    <BasicTable v-if="state.isTableMode" @register="registerTable">
      <template #toolbar>
        <div style="display: flex; align-items: center; gap: 8px;">
          <a-button type="primary" @click="openAddModal(true, { type: 'add' })">新增OTA升级包
          </a-button>
          <a-button type="default" @click="handleClickSwap"
                    preIcon="ant-design:swap-outlined">切换视图
          </a-button>
        </div>
      </template>
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'action'">
          <TableAction
            :actions="[
              {
                icon: 'ant-design:download-outlined',
                tooltip: {
                  title: '下载',
                  placement: 'top',
                },
                onClick: handleDownload.bind(null, record)
              },
              {
                icon: 'ant-design:eye-filled',
                tooltip: {
                  title: '详情',
                  placement: 'top',
                },
                onClick: openAddModal.bind(null, true, { isEdit: false, isView: true, record }),
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
      <OtaPackageCards
        :api="fetchPkgList"
        :params="params"
        @getMethod="getMethod"
        @view="handleCardView"
        @edit="handleCardEdit"
        @delete="handleCardDelete"
        @download="handleCardDownload"
      >
        <template #header>
          <div style="display: flex; align-items: center; gap: 8px;">
            <a-button type="primary" @click="openAddModal(true, { type: 'add' })">新增OTA升级包
            </a-button>
            <a-button type="default" @click="handleClickSwap"
                      preIcon="ant-design:swap-outlined">切换视图
            </a-button>
          </div>
        </template>
      </OtaPackageCards>
    </div>
    <OtaPackageModal title="新增OTA升级包" @register="registerAddModel" @success="handleSuccess"/>
  </div>
</template>
<script lang="ts" setup name="noticeSetting">
import {reactive} from 'vue';
import {BasicTable, TableAction, useTable} from '@/components/Table';
import {useMessage} from '@/hooks/web/useMessage';
import {deleteOtaApp, fetchPkgList} from '/@/api/device/ota';
import {getBasicColumns, getFormConfig} from "./Data";
import OtaPackageModal from "@/views/ota/components/OtaPackageModal/index.vue";
import OtaPackageCards from "@/views/ota/components/OtaPackageCards/index.vue";
import {useModal} from "@/components/Modal";
import {downloadByUrl} from "@/utils/file/download";
import ALERT from "@/assets/images/product/product_normal.png";

const [registerAddModel, {openModal: openAddModal}] = useModal();

defineOptions({name: 'OtaVersion'})

const state = reactive({
  isTableMode: false,
});

// 请求api时附带参数
const params = {};

let cardListReload = () => {
};

// 获取内部fetch方法;
function getMethod(m: any) {
  cardListReload = m;
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

// 卡片视图事件处理
function handleCardView(record) {
  openAddModal(true, { isEdit: false, isView: true, record });
}

function handleCardEdit(record) {
  openAddModal(true, { isEdit: true, isView: false, record });
}

function handleCardDelete(record) {
  handleDelete(record);
}

function handleCardDownload(record) {
  handleDownload(record);
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
  title: 'OTA升级包管理',
  api: fetchPkgList,
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

const handleDelete = async (record) => {
  try {
    const id = record["id"];
    await deleteOtaApp(id);
    createMessage.success('删除成功');
    reload();
    cardListReload();
  }catch (error) {
    console.error(error)
    createMessage.success('删除失败');
    console.log('handleDelete', error);
  }
};

const handleDownload = async (record) => {
  downloadByUrl({ url: record['url']  })
}
</script>
