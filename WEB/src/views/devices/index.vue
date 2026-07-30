<template>
  <div class="device-wrapper">
    <div class="device-tab page-content-card">
      <Tabs
        v-model:activeKey="state.activeKey"
        :animated="{ inkBar: true, tabPane: false }"
        :destroyInactiveTabPane="true"
        :tabBarGutter="60"
        @change="handleTabChange"
      >
        <TabPane key="map" tab="地图分布">
          <DeviceMapDistribution ref="deviceMapDistributionRef" />
        </TabPane>
        <TabPane key="list" tab="设备列表">
          <div class="device-list-pane">
            <BasicTable @register="registerTable" v-if="state.isTableMode">
              <template #toolbar>
                <Button type="primary" @click="handleClickAdd" preIcon="ant-design:plus-outlined">
                  添加设备
                </Button>
                <Button type="default" @click="handleClickSwap"
                          preIcon="ant-design:swap-outlined">切换视图
                </Button>
                <PopConfirmButton
                  placement="topRight"
                  @confirm="handleClickDeleteAll"
                  type="primary"
                  color="error"
                  :disabled="!checkedKeys.length"
                  :title="`您确定要批量删除数据?`"
                  preIcon="ant-design:delete-outlined"
                >批量删除
                </PopConfirmButton>
              </template>
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'connectStatus'">
                  <Tag :color="record.connectStatus === 'ONLINE' ? 'green' : 'red'">{{
                      record.connectStatus === 'ONLINE' ? '在线' : '离线'
                    }}
                  </Tag>
                </template>
                <template v-if="column.key === 'activeStatus'">
                  <Tag :color="record.activeStatus === 1 ? 'green' : 'red'">{{
                      record.activeStatus === 1 ? '已激活' : '未激活'
                    }}
                  </Tag>
                </template>
                <template v-if="column.dataIndex === 'action'">
                  <TableAction
                    :stopButtonPropagation="true"
                    :actions="[
                      {
                        icon: 'ant-design:eye-outlined',
                        tooltip: {
                          title: '详情',
                          placement: 'top',
                        },
                        onClick: goDeviceDrawer.bind(null, record),
                      },
                      {
                        icon: 'ant-design:edit-filled',
                        tooltip: {
                          title: '编辑',
                          placement: 'top',
                        },
                        onClick: openAddModal.bind(null, true, { isEdit: true, record }),
                      },
                      {
                        icon: 'material-symbols:delete-outline-rounded',
                        tooltip: {
                          title: '删除',
                          placement: 'top',
                        },
                        popConfirm: {
                          title: `是否确认删除？`,
                          placement: 'topRight',
                          confirm: handleClickDelete.bind(null, record),
                        },
                      },
                    ]"
                  />
                </template>
              </template>
            </BasicTable>
            <div v-else class="device-card-wrap">
              <DeviceCardList :params="params" :api="getDevicesList" @get-method="getMethod"
                              @delete="handleDel" @edit="handleEdit" @view="handleView">
                <template #header>
                  <Button type="primary" @click="handleClickAdd" preIcon="ant-design:plus-outlined">
                    添加设备
                  </Button>
                  <Button type="default" @click="handleClickSwap"
                            preIcon="ant-design:swap-outlined">切换视图
                  </Button>
                  <PopConfirmButton
                    placement="topRight"
                    @confirm="handleClickDeleteAll"
                    type="primary"
                    color="error"
                    :disabled="!checkedKeys.length"
                    :title="`您确定要批量删除数据?`"
                    preIcon="ant-design:delete-outlined"
                  >批量删除
                  </PopConfirmButton>
                </template>
              </DeviceCardList>
            </div>
            <DeviceModal @register="registerAddModel" @success="handleSuccess"/>
          </div>
        </TabPane>
      </Tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import moment from 'moment';
import {nextTick, onMounted, reactive, ref} from 'vue';
import {
  deleteDevices,
  getDevicesList,
} from '@/api/device/devices';
import {Tabs, Tag} from 'ant-design-vue';
import {getBasicColumns, getFormConfig} from './Data';
import {Button, PopConfirmButton} from '@/components/Button';
import {useMessage} from '@/hooks/web/useMessage';
import {BasicTable, TableAction, useTable} from '@/components/Table';
import {useDrawer} from '@/components/Drawer';
import DeviceModal from "@/views/devices/components/DeviceModalForm/DeviceModal.vue";
import {useRouter} from "vue-router";
import {getDeviceProfiles} from "@/api/device/product";
import DeviceCardList from "@/views/devices/components/CardList/DeviceCardList.vue";
import DeviceMapDistribution from "@/views/devices/components/MapDistribution/index.vue";

defineOptions({name: 'Devices'})

const TabPane = Tabs.TabPane;

const DEVICE_TAB_KEYS = {
  MAP: 'map',
  LIST: 'list',
} as const;

const {createMessage} = useMessage();
const [registerAddModel, {openDrawer: openAddModal}] = useDrawer();
const selectDevices = ref<string>('');
const checkedKeys = ref<Array<string | number>>([]);
const deviceMapDistributionRef = ref<InstanceType<typeof DeviceMapDistribution> | null>(null);

const state = reactive({
  isTableMode: false,
  activeKey: DEVICE_TAB_KEYS.MAP as string,
  productMap: {} as Record<string, { productName: string; protocolType: string }>,
});

const params = {};

let cardListReload = () => {
};

function getMethod(m: any) {
  cardListReload = m;
}

function handleView(record) {
  goDeviceDrawer(record);
}

function handleEdit(record) {
  openAddModal(true, { isEdit: true, record });
}

function handleDel(record) {
  handleClickDelete(record);
  handleSuccess();
}

const [registerTable, {reload}] = useTable({
  title: '设备信息档案列表',
  api: getDevicesList,
  beforeFetch: (data) => {
    const {page, pageSize, pageNo, order, field, textSearch, onlineStatus} = data;
    return {
      ...data,
      pageNum: pageNo || page,
      pageSize,
      textSearch,
      onlineStatus,
      deviceProfileIdStr: selectDevices.value,
      sortOrder: order == 'descend' ? 'DESC' : (order == 'ascend' ? 'ASC' : 'DESC'),
      sortProperty: field || 'updateTime',
      filterNoCustomer: 1,
    };
  },
  afterFetch: (data) => {
    let list = data.map((res) => {
      const {lastUpdateTime, additionalInfo} = res;
      const newDate = new Date(lastUpdateTime);
      res.lastUpdateTime = lastUpdateTime
        ? moment(newDate)?.format?.('YYYY-MM-DD HH:mm:ss')
        : '-';
      res.gateway = additionalInfo?.gateway;
      res.productName = state.productMap[res['productIdentification']]?.productName;
      res.protocolType = state.productMap[res['productIdentification']]?.protocolType;
      return res;
    });
    return list;
  },
  columns: getBasicColumns(),
  useSearchForm: true,
  formConfig: getFormConfig(),
  showTableSetting: false,
  tableSetting: {fullScreen: true},
  showIndexColumn: false,
  rowKey: 'id',
  fetchSetting: {
    listField: 'data',
    totalField: 'total',
  },
  rowSelection: {
    type: 'checkbox',
    selectedRowKeys: checkedKeys,
    onSelect: onSelect,
    onSelectAll: onSelectAll,
  },
});

const router = useRouter();

function goDeviceDrawer(record) {
  const params = {
    id: record.id,
    productIdentification: record.productIdentification,
    deviceIdentification: record.deviceIdentification,
    deviceType: record.deviceType,
  };
  router.push({name: 'DeviceDetail', params});
}

function onSelect(record, selected) {
  if (selected) {
    checkedKeys.value = [...checkedKeys.value, record.id];
  } else {
    checkedKeys.value = checkedKeys.value.filter((id) => id !== record.id);
  }
}

function onSelectAll(selected, _, changeRows) {
  const changeIds = changeRows.map((item) => item.id);
  if (selected) {
    checkedKeys.value = [...checkedKeys.value, ...changeIds];
  } else {
    checkedKeys.value = checkedKeys.value.filter((id) => {
      return !changeIds.includes(id);
    });
  }
}

async function handleClickDeleteAll() {
  try {
    await Promise.all([...checkedKeys.value.map((item) => deleteDevices(item + ''))]);
    createMessage.success('删除成功');
  } catch (error) {
    console.error(error)
    createMessage.error('删除失败');
  }
  handleSuccess();
}

async function handleClickDelete(record) {
  try {
    await deleteDevices(record.id);
    createMessage.success('删除成功');
  } catch (error) {
    console.error(error)
    createMessage.error('删除失败');
  }
  handleSuccess();
}

function handleClickAdd() {
  openAddModal(true, { isEdit: false });
}

function handleClickSwap() {
  state.isTableMode = !state.isTableMode;
}

function handleTabChange(key: string | number) {
  state.activeKey = String(key);
  if (String(key) === DEVICE_TAB_KEYS.MAP) {
    void nextTick(() => {
      deviceMapDistributionRef.value?.refresh?.();
    });
  }
}

function handleSuccess() {
  reload({
    page: 0,
  });
  cardListReload();
}

async function initProductList() {
  const record = await getDeviceProfiles({ pageNum: 1, pageSize: 500 });
  record.data.forEach((item) => {
    state.productMap[item.productIdentification] = {
      productName: item.productName,
      protocolType: item.protocolType,
    };
  });
}

onMounted(() => {
  initProductList();
})
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
