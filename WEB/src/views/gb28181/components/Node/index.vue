<template>
  <div class="node-wrapper">
    <BasicTable @register="registerTable" v-if="state.isTableMode">
      <template #toolbar>
        <a-button type="primary" @click="openAddModal(true, { type: 'add' })"
                  preIcon="ant-design:plus-outlined">
          新增测试设备
        </a-button>
        <a-button type="default" @click="batchValidation"
                  preIcon="ant-design:partition-outlined">
          批量测试
        </a-button>
        <a-button type="default" @click="handleClickSwap" preIcon="ant-design:swap-outlined">
          切换视图
        </a-button>
        <PopConfirmButton
          placement="topRight"
          @confirm="handleDeleteAll"
          type="primary"
          color="error"
          :disabled="!checkedKeys.length"
          :title="`您确定要批量删除数据?`"
          preIcon="ant-design:delete-outlined"
        >批量删除
        </PopConfirmButton>
      </template>
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'action'">
          <TableAction
            :actions="[
              {
                tooltip: {
                  title: '删除',
                  placement: 'top',
                },
                icon: 'material-symbols:delete-outline-rounded',

                popConfirm: {
                  placement: 'topRight',
                  title: '是否确认删除？',
                  confirm: handleDeleteProduct.bind(null, record),
                },
              },
            ]"
          />
        </template>
      </template>
    </BasicTable>
    <div v-else>
      <NodeCardList :params="params" :api="getMediaServerList"
                    @get-method="getMethod" @delete="handleDel"
                    @edit="handleEdit">
        <template #header>
          <a-button type="primary" @click="openAddModal(true, { type: 'add' })"
                    preIcon="ant-design:plus-outlined">
            添加代理
          </a-button>
          <a-button type="default" @click="handleClickSwap" preIcon="ant-design:swap-outlined">
            切换视图
          </a-button>
        </template>
      </NodeCardList>
    </div>
    <NodeModal title="媒体节点" @register="registerAddModel" @success="handleSuccess"/>
  </div>
</template>
<script setup lang="ts">
import {reactive, ref} from 'vue';
import {BasicTable, TableAction, useTable} from "@/components/Table";
import {PopConfirmButton} from "@/components/Button";
import moment from "moment/moment";
import {getBasicColumns, getFormConfig} from "./Data";
import NodeCardList from "@/views/gb28181/components/NodeCardList/index.vue";
import {useMessage} from "@/hooks/web/useMessage";
import {useModal} from "@/components/Modal";
import {useRoute, useRouter} from "vue-router";
import {batchPushUpgradePackage, deleteOtaVerification} from "@/api/device/ota";
import NodeModal from "@/views/gb28181/components/NodeModal/index.vue";
import {deleteMediaServer, getMediaServerList, queryChannelList} from "@/api/device/gb28181";

defineOptions({name: 'PullProxy'})

const checkedKeys = ref<Array<string | number>>([]);
const {createMessage} = useMessage();
const route = useRoute()

const [registerAddModel, {openModal: openAddModal}] = useModal();

const router = useRouter();

const state = reactive({
  isTableMode: false,
  totalTargetDevices: 0,
  targetWait: 0,
  targetStart: 0,
  targetSuccess: 0,
  targetFailures: 0,
});

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
  actionColOptions: {span: 4},
  title: '通道列表',
  api: queryChannelList,
  beforeFetch: (data) => {
    const {pageSize, page, order} = data;
    let params = {
      page,
      pageSize,
      sortOrder: order == 'descend' ? 'DESC' : 'ASC',
      deviceIdentification: route.params.deviceIdentification,
    };
    return params;
  },
  afterFetch: (data) => {
    const list = data.map((res) => {
      let newDate = new Date(res.createdTime);
      res.createdTime = moment(newDate)?.format?.('YYYY-MM-DD HH:mm:ss') ?? res.createdTime;
      return res;
    });
    return list;
  },
  columns: getBasicColumns(),
  useSearchForm: true,
  formConfig: getFormConfig(),
  fetchSetting: {
    listField: 'data',
    totalField: 'total',
  },
  rowKey: 'id',
  onChange,
  rowSelection: {
    type: 'checkbox',
    selectedRowKeys: checkedKeys,
    onSelect: onSelect,
    onSelectAll: onSelectAll,
    getCheckboxProps(record) {
      if (record.default || record.referencedByDevice) {
        return {disabled: true};
      } else {
        return {disabled: false};
      }
    },
  },
  onColumnsChange: (data) => {
    //console.log('ColumnsChanged', data);
  },
});

// 切换视图
function handleClickSwap() {
  state.isTableMode = !state.isTableMode;
}

// 批量测试
function batchValidation() {
  if (state.totalTargetDevices === 0) {
    createMessage.warn('请添加测试设备');
    return;
  }
  if (state.totalTargetDevices === state.targetSuccess) {
    createMessage.warn('不存在需要验证的设备');
    return;
  }
  batchPushUpgradePackage({versionId: route.params.versionId})
    .then(() => {
      createMessage.success('批量推送成功');
      handleSuccess();
    })
    .catch((e) => {
      createMessage.error(e.message);
    });
}

function onSelect(record, selected) {
  if (selected) {
    checkedKeys.value = [...checkedKeys.value, record.id];
  } else {
    checkedKeys.value = checkedKeys.value.filter((id) => id !== record.id);
  }
}

function onSelectAll(selected, selectedRows, changeRows) {
  const changeIds = changeRows.map((item) => item.id);
  if (selected) {
    checkedKeys.value = [...checkedKeys.value, ...changeIds];
  } else {
    checkedKeys.value = checkedKeys.value.filter((id) => {
      return !changeIds.includes(id);
    });
  }
}

async function handleDeleteAll() {
  // //console.log('checkedKeys ...', checkedKeys);
  try {
    await Promise.all([deleteOtaVerification(checkedKeys.value)]);
    createMessage.success('删除成功');
  }catch (error) {
    console.error(error)
    createMessage.error('删除失败');
  }
  reloadList();
}

async function handleDeleteProduct(record) {
  try {
    const {id} = record;
    await deleteOtaVerification([id]);
    reloadList();
    //console.log('ret ...', ret);
    createMessage.success('删除成功');
  }catch (error) {
    console.error(error)
    createMessage.error('删除失败');
  }
}

function reloadList() {
  checkedKeys.value = [];
  reload({page: 0});
  cardListReload();
}

function onChange() {
  //console.log('onChange', arguments);
}

// 请求api时附带参数
const params = {};

let cardListReload = () => {
};

// 获取内部fetch方法;
function getMethod(m: any) {
  cardListReload = m;
}

//编辑按钮事件
function handleEdit(record) {
  openAddModal(true, {type: 'edit', record: record});
  cardListReload();
}

function handleDel(record) {
  deleteMediaServer(record['id']).then(() => {
    cardListReload();
  });
}

// 表格刷新
function handleSuccess() {
  reload({
    page: 0,
  });
  cardListReload();
}
</script>

<style lang="less" scoped>
:deep(.product-image) {
  width: 30px;
  height: 30px;
  margin-right: auto;
  margin-left: auto;

  img {
    width: 100%;
    height: 100%;
  }
}

:deep(.vben-basic-table-action.left) {
  justify-content: center;
}

.node-wrapper {
  height: 100%;
  background-color: #f0f2f5;

  :deep(.ant-tabs-nav) {
    padding: 5px 0 0 25px;
  }

  :deep(.ant-form-item) {
    margin-bottom: 10px;
  }

  :deep(.card-list) {
    margin: 16px;
    display: flex;
    align-items: center;
    justify-content: flex-start;
    gap: 24px;
    flex-wrap: wrap;

    .card {
      flex: 0 0 calc(25% - 18px);
      background-color: #fff;
      min-width: 200px;
      min-height: 130px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: space-around;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
      transition: all 0.3s;
      border: 1px solid #e8e8e8;

      &:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
        transform: translateY(-2px);
      }

      img {
        width: 100px;
        transition: all linear 0.3s;
      }

      .info {
        display: flex;
        flex-direction: column;
        align-items: center;

        .num {
          font-size: 26px;
          font-weight: 600;
          color: #333;
        }

        .label {
          font-weight: 600;
          color: #666;
          font-size: 14px;
        }
      }
    }
  }
}
</style>
