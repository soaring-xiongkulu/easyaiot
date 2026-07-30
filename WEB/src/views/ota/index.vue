<template>
  <div class="device-wrapper">
    <div class="device-tab page-content-card">
      <Tabs
        v-model:activeKey="state.activeKey"
        :animated="{ inkBar: true, tabPane: false }"
        :destroyInactiveTabPane="true"
        :tabBarGutter="60"
      >
        <TabPane key="list" tab="升级包列表">
          <div class="device-list-pane">
            <BasicTable v-if="state.isTableMode" @register="registerTable">
              <template #toolbar>
                <Button type="primary" @click="openAddModal(true, { type: 'add' })"
                          preIcon="ant-design:plus-outlined">
                  新增OTA升级包
                </Button>
                <Button type="default" @click="handleClickSwap"
                          preIcon="ant-design:swap-outlined">切换视图
                </Button>
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
            <div v-else class="device-card-wrap">
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
                  <Button type="primary" @click="openAddModal(true, { type: 'add' })"
                            preIcon="ant-design:plus-outlined">
                    新增OTA升级包
                  </Button>
                  <Button type="default" @click="handleClickSwap"
                            preIcon="ant-design:swap-outlined">切换视图
                  </Button>
                </template>
              </OtaPackageCards>
            </div>
            <OtaPackageModal title="新增OTA升级包" @register="registerAddModel" @success="handleSuccess"/>
          </div>
        </TabPane>
      </Tabs>
    </div>
  </div>
</template>

<script lang="ts" setup>
import {reactive} from 'vue';
import {Tabs} from 'ant-design-vue';
import {BasicTable, TableAction, useTable} from '@/components/Table';
import {useMessage} from '@/hooks/web/useMessage';
import {deleteOtaApp, fetchPkgList} from '/@/api/device/ota';
import {getBasicColumns, getFormConfig} from './Data';
import OtaPackageModal from '@/views/ota/components/OtaPackageModal/index.vue';
import OtaPackageCards from '@/views/ota/components/OtaPackageCards/index.vue';
import {useDrawer} from '@/components/Drawer';
import {downloadByUrl} from '@/utils/file/download';
import {Button} from '@/components/Button';

defineOptions({name: 'OtaVersion'});

const TabPane = Tabs.TabPane;
const [registerAddModel, {openDrawer: openAddModal}] = useDrawer();

const state = reactive({
  isTableMode: false,
  activeKey: 'list',
});

const params = {};

let cardListReload = () => {
};

function getMethod(m: any) {
  cardListReload = m;
}

function handleClickSwap() {
  state.isTableMode = !state.isTableMode;
}

function handleSuccess() {
  reload({
    page: 0,
  });
  cardListReload();
}

function handleCardView(record) {
  openAddModal(true, {isEdit: false, isView: true, record});
}

function handleCardEdit(record) {
  openAddModal(true, {isEdit: true, isView: false, record});
}

function handleCardDelete(record) {
  handleDelete(record);
}

function handleCardDownload(record) {
  handleDownload(record);
}

const {createMessage} = useMessage();
const [registerTable, {reload}] = useTable({
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
    const id = record['id'];
    await deleteOtaApp(id);
    createMessage.success('删除成功');
    reload();
    cardListReload();
  } catch (error) {
    console.error(error);
    createMessage.error('删除失败');
  }
};

const handleDownload = async (record) => {
  downloadByUrl({url: record['url']});
};
</script>

<style lang="less" scoped>
:deep(.iot-basic-table-action.left) {
  justify-content: center;
}

.device-wrapper {
  padding: 0;
  box-sizing: border-box;
  min-height: calc(100vh - 88px);
  background: #ffffff;

  .page-content-card {
    background: #fff;
    border-radius: 0;
    overflow: hidden;
  }

  .device-tab {
    :deep(.ant-tabs-nav) {
      padding: 5px 0 0 25px;
      margin-bottom: 0;
    }

    :deep(.ant-tabs) {
      background-color: #fff;
    }
  }

  .device-list-pane {
    min-height: calc(100vh - 200px);
  }

  .device-card-wrap {
    min-height: calc(100vh - 200px);
    background: #fff;
    display: flex;
    flex-direction: column;
  }

  :deep(.ant-form-item) {
    margin-bottom: 10px;
  }

  :deep(.iot-basic-table-form-container) {
    padding: 0;
    background: #fff;

    .ant-form {
      margin-bottom: 0;
      border-radius: 0;
      background: transparent;
      padding: 16px 16px 0;
    }
  }

  :deep(.ant-table-wrapper) {
    border-radius: 0;
    background: #fff;
    padding: 8px 16px 16px;
  }
}
</style>
