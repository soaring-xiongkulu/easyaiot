<template>
  <div>
    <BasicTable @register="registerTable" v-if="state.isTableMode">
      <template #toolbar>
        <a-button type="primary" @click="openAddModal(true, { type: 'add' })">新增设备版本
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
                icon: 'ant-design:bug-twotone',
                tooltip: {
                  title: '测试验证',
                  placement: 'top',
                },
                onClick: handleVerification.bind(null, record),
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
                icon: 'ant-design:rocket-twotone',
                tooltip: {
                  title: '发布',
                  placement: 'top',
                },
                disabled: record['status'] == 1? false : record['status'] !== 3,
                onClick: openAddModal.bind(null, true, { isEdit: false, isView: true, record }),
              },
              {
                icon: 'ant-design:rollback-outlined',
                tooltip: {
                  title: '撤销发布',
                  placement: 'top',
                },
                disabled: record['status'] !== 2,
                popConfirm: {
                  placement: 'topRight',
                  title: '是否确认撤销发布？',
                  confirm: handlePublishedRevoke.bind(null, record),
                },
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
      <VideoCardList :params="params" :api="queryVideoList" @get-method="getMethod"
                     @edit="handleEdit" @refresh="handleRefresh">
        <template #header>
          <a-button type="default" @click="handleClickSwap" preIcon="ant-design:swap-outlined">
            切换视图
          </a-button>
        </template>
      </VideoCardList>
    </div>
    <VideoModal title="编辑视频设备" @register="registerAddModel" @success="handleSuccess"/>
  </div>
</template>
<script lang="ts" setup name="noticeSetting">
import {reactive} from 'vue';
import {BasicTable, TableAction, useTable} from '@/components/Table';
import {useMessage} from '@/hooks/web/useMessage';
import {deleteVersion, publishedRevoke} from '/@/api/device/ota';
import {getBasicColumns, getFormConfig} from "./Data";
import {useModal} from "@/components/Modal";
import {useRouter} from "vue-router";
import VideoCardList from "@/views/gb28181/components/VideoCardList/index.vue";
import {queryVideoList, refreshChannelList} from "@/api/device/gb28181";
import VideoModal from "@/views/gb28181/components/VideoModal/index.vue";

const [registerAddModel, {openModal: openAddModal}] = useModal();

const router = useRouter();

defineOptions({name: 'Video'})

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
  openAddModal(true, {isEdit: false, isView: true, record: record});
}

//编辑按钮事件
function handleEdit(record) {
  openAddModal(true, {isEdit: true, isView: false, record: record});
}

//刷新通道列表
function handleRefresh(record) {
  try {
    refreshChannelList(record['deviceIdentification']);
    createMessage.success('开始同步');
    setTimeout(() => {
      createMessage.success('通道同步完成');
    }, 2000);
    handleSuccess();
  }catch (error) {
    console.error(error)
    createMessage.success('通道同步失败');
    console.log('handleRefresh', error);
  }
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

//详情按钮事件
function handleVerification(record) {
  goOtaVerification(record);
}

function goOtaVerification(record) {
  const params = {
    productIdentification: record.productIdentification,
    versionId: record.id,
    osPkgId: record.osPkgId,
    appPkgId: record.appPkgId,
  };
  router.push({name: 'OtaVerification', params});
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
  title: '国标设备列表',
  api: queryVideoList,
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
    await deleteVersion(record['id']);
    createMessage.success('删除成功');
    handleSuccess();
  }catch (error) {
    console.error(error)
    createMessage.success('删除失败');
    console.log('handleDelete', error);
  }
};

const handlePublishedRevoke = async (record) => {
  publishedRevoke({id: record.id})
    .then(() => {
      createMessage.success('撤销成功');
      handleSuccess();
    })
    .catch((e) => {
      createMessage.error(e.message);
    });
};
</script>
