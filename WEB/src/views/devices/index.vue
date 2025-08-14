<template>
  <div class="device-wrapper">
    <div class="device-info">
      <div class="ant-row" style="margin-left: -10px; margin-right: -10px; row-gap: 0px;">
        <div class="ant-col ant-col-10" style="padding-left: 10px; padding-right: 10px;">
          <div class="ant-card">
            <div class="ant-card-body">
              <div class="card-box"><img :src="DEVICE_TOTAL_IMAGE" alt="" class="img">
                <div class="info-box">
                  <div class="title">设备总数</div>
                  <div class="list">
                    <div class="item">
                      <div class="num" style="color: rgb(255, 187, 84);">
                        {{ state['deviceTotal']['commonDeviceAmount'] ?? 0 }}
                      </div>
                      <div class="name">普通设备</div>
                    </div>
                    <div class="item">
                      <div class="num" style="color: rgb(255, 187, 84);">
                        {{ state['deviceTotal']['gatewayDeviceAmount'] ?? 0 }}
                      </div>
                      <div class="name">网关设备</div>
                    </div>
                    <div class="item">
                      <div class="num" style="color: rgb(255, 187, 84);">
                        {{ state['deviceTotal']['subsetDeviceAmount'] ?? 0 }}
                      </div>
                      <div class="name">子设备</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="ant-col ant-col-7" style="padding-left: 10px; padding-right: 10px;">
          <div class="ant-card">
            <div class="ant-card-body">
              <div class="card-box"><img :src="DEVICE_CONNECT_STATUS_IMAGE" alt="" class="img">
                <div class="info-box">
                  <div class="title">连接状态</div>
                  <div class="list">
                    <div class="item">
                      <div class="num" style="color: rgb(0, 97, 255);">
                        {{ state['deviceConnectStatus']['onlineStatusAmount'] ?? 0 }}
                      </div>
                      <div class="name">在线</div>
                    </div>
                    <div class="item">
                      <div class="num" style="color: rgb(106, 162, 254);">
                        {{ state['deviceConnectStatus']['offlineStatusAmount'] ?? 0 }}
                      </div>
                      <div class="name">离线</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="ant-col ant-col-7" style="padding-left: 10px; padding-right: 10px;">
          <div class="ant-card">
            <div class="ant-card-body">
              <div class="card-box"><img :src="DEVICE_ACTIVE_STATUS_IMAGE" alt="" class="img">
                <div class="info-box">
                  <div class="title">设备状态</div>
                  <div class="list">
                    <div class="item">
                      <div class="num" style="color: rgb(52, 168, 83);">
                        {{ state['deviceEnabledStatus']['activatedAmount'] ?? 0 }}
                      </div>
                      <div class="name">已激活</div>
                    </div>
                    <div class="item">
                      <div class="num" style="color: rgba(52, 168, 83, 0.8);">
                        {{ state['deviceEnabledStatus']['inactivatedAmount'] ?? 0 }}
                      </div>
                      <div class="name">未激活</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="device-tab">
      <Tabs
        :animated="{ inkBar: true, tabPane: true }"
        :activeKey="state.activeKey"
        :tabBarGutter="60"
        @tabClick="handleTabClick"
      >
        <TabPane key="1" tab="设备列表">
          <BasicTable @register="registerTable" v-if="state.isTableMode">
            <template #toolbar>
              <a-button type="primary" @click="handleClickAdd" preIcon="ant-design:plus-outlined">
                添加设备
              </a-button>
              <a-button type="default" @click="handleClickSwap"
                        preIcon="ant-design:swap-outlined">切换视图
              </a-button>
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
                onClick: openAddModal.bind(null, true, { record }),
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
          <div v-else>
            <DeviceCardList :params="params" :api="getDevicesList" @get-method="getMethod"
                            @delete="handleDel" @edit="handleEdit" @view="handleView">
              <template #header>
                <a-button type="primary" @click="handleClickAdd" preIcon="ant-design:plus-outlined">
                  添加设备
                </a-button>
                <a-button type="default" @click="handleClickSwap"
                          preIcon="ant-design:swap-outlined">切换视图
                </a-button>
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
        </TabPane>
      </Tabs>
    </div>
    <DeviceModal title="添加设备" @register="registerAddModel" @success="handleSuccess"/>
  </div>
</template>

<script setup lang="ts">
import moment from 'moment';
import {onMounted, reactive, ref} from 'vue';
import {
  deleteDevices,
  getConnectStatusStatistics,
  getDevicesList,
  getDeviceStatistics,
  getDeviceStatusStatistics,
} from '@/api/device/devices';
import {TabPane, Tabs, Tag} from 'ant-design-vue';
import {getBasicColumns, getFormConfig} from './Data';
import {PopConfirmButton} from '@/components/Button';
import {useMessage} from '@/hooks/web/useMessage';
import {BasicTable, TableAction, useTable} from '@/components/Table';
import {useModal} from '@/components/Modal';
import DeviceModal from "@/views/devices/components/Addmodel/DeviceModal.vue";
import {useRouter} from "vue-router";
import {getDeviceProfiles} from "@/api/device/product";
import DeviceCardList from "@/views/devices/components/CardList/DeviceCardList.vue";
import DEVICE_TOTAL_IMAGE from "@/assets/images/device/device_total.png";
import DEVICE_CONNECT_STATUS_IMAGE from "@/assets/images/device/device_connect_status.png";
import DEVICE_ACTIVE_STATUS_IMAGE from "@/assets/images/device/device_active_status.png";

defineOptions({name: 'Devices'})

const {createMessage} = useMessage();
const [registerAddModel, {openModal: openAddModal}] = useModal();
const selectDevices = ref<string>('');
const checkedKeys = ref<Array<string | number>>([]);

const state = reactive({
  isTableMode: false,
  activeKey: '1',
  productMap: {},
  deviceTotal: {},
  deviceConnectStatus: {},
  deviceEnabledStatus: {},
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
  goDeviceDrawer(record);
}

//编辑按钮事件
function handleEdit(record) {
  openAddModal(true, {record});
  handleSuccess();
}

//删除按钮事件
function handleDel(record) {
  handleClickDelete(record);
  handleSuccess();
}

const handleTabClick = (activeKey) => {
  state.activeKey = activeKey;
};

const [registerTable, {reload}] = useTable({
  title: '设备信息档案列表',
  api: getDevicesList,
  beforeFetch: (data) => {
    // 接口请求前 参数处理
    //console.log('beforeFetch-------', data);
    const {page, pageSize, order, field, textSearch, onlineStatus} = data;
    let params = {
      ...data,
      page,
      pageSize,
      textSearch,
      onlineStatus,
      deviceProfileIdStr: selectDevices.value,
      sortOrder: order == 'descend' ? 'DESC' : 'ASC',
      sortProperty: field,
      filterNoCustomer: 1,
    };
    return params;
  },
  afterFetch: (data) => {
    //请求之后对返回值进行处理
    //console.log('afterFetch', data);
    let list = data.map((res) => {
      const {lastUpdateTime, additionalInfo} = res;
      const newDate = new Date(lastUpdateTime);
      res.lastUpdateTime = lastUpdateTime
        ? moment(newDate)?.format?.('YYYY-MM-DD HH:mm:ss')
        : '-';
      res.gateway = additionalInfo?.gateway;
      res.productName = state.productMap[res['productIdentification']];
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

// 删除选中
async function handleClickDeleteAll() {
  try {
    await Promise.all([...checkedKeys.value.map((item) => deleteDevices(item + ''))]);
    createMessage.success('删除成功');
  } catch (error) {
    console.error(error)
    //console.log(error);
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
    //console.log(error);
    createMessage.error('删除失败');
  }
  handleSuccess();
}

// 新增
function handleClickAdd() {
  openAddModal(true);
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
  initDeviceStatistics();
}

async function initProductList() {
  const record = await getDeviceProfiles({page: 1, pageSize: 100});
  record.data.forEach((item) => {
    state.productMap[item.productIdentification] = item.productName;
  });
}

//获取设备统计信息
function initDeviceStatistics() {
  getDeviceStatistics().then((record) => {
    state.deviceTotal = record;
  });
  getConnectStatusStatistics().then((record) => {
    state.deviceConnectStatus = record;
  });
  getDeviceStatusStatistics().then((record) => {
    state.deviceEnabledStatus = record;
  });
}

onMounted(() => {
  initProductList();
  initDeviceStatistics();
})
</script>

<style lang="less" scoped>
.device-wrapper {
  :deep(.ant-tabs-nav) {
    padding: 5px 0 0 25px;
  }

  :deep(.ant-form-item) {
    margin-bottom: 10px;
  }

  .device-info {
    padding: 16px 16px 0;

    .ant-row {
      display: flex;
      flex-flow: row wrap;

      .ant-col {
        margin-top: 6px !important;
        margin-bottom: 6px !important;
        position: relative;
        min-height: 1px;

        .ant-card {
          box-sizing: border-box;
          margin: 0;
          padding: 0;
          color: #000000d9;
          font-size: 14px;
          font-variant: tabular-nums;
          line-height: 1.5715;
          list-style: none;
          font-feature-settings: tnum;
          position: relative;
          background: #fff;
          border-radius: 2px;
          box-shadow: 0 0 4px #00000026;

          .ant-card-body {
            padding: 24px;

            .card-box {
              display: flex;

              .img {
                width: 104px;
                margin-right: 8px;
                border-radius: 10px;
              }

              .info-box {
                flex: 1;

                .title {
                  font-size: 12px;
                  line-height: 1;
                  font-weight: 600;
                  margin-bottom: 10px;
                  padding-left: 8px;
                }

                .list {
                  display: flex;

                  .item {
                    flex: 1;
                    text-align: center;

                    .num {
                      font-size: 26px;
                      font-weight: 600;
                    }

                    .name {
                      font-weight: 600;
                    }
                  }
                }
              }
            }
          }

          .ant-card-body:before {
            display: table;
            content: "";
          }

          .ant-card-body:after {
            display: table;
            clear: both;
            content: "";
          }
        }
      }
    }

    .ant-col-7 {
      display: block;
      flex: 0 0 29.1%;
      max-width: 29.1%;
    }

    .ant-col-10 {
      display: block;
      flex: 0 0 41.6%;
      max-width: 41.6%;
    }
  }

  .device-tab {
    padding: 16px 19px 0 15px;

    .ant-tabs {
      background-color: #FFFFFF;
    }
  }
}
</style>
