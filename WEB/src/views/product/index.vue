<template>
  <div class="device-wrapper">
    <div class="device-tab page-content-card">
      <Tabs
        v-model:activeKey="state.activeKey"
        :animated="{ inkBar: true, tabPane: false }"
        :destroyInactiveTabPane="true"
        :tabBarGutter="60"
      >
        <TabPane key="list" tab="产品列表">
          <div class="device-list-pane">
            <BasicTable @register="registerTable" v-if="state.isTableMode">
              <template #toolbar>
                <Button type="primary" @click="handleOpenProductDrawer(true, { isEdit: false })"
                          preIcon="ant-design:plus-outlined">
                  添加产品
                </Button>
                <Button type="default" @click="handleClickSwap"
                          preIcon="ant-design:swap-outlined">切换视图
                </Button>
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
                        icon: 'ant-design:eye-outlined',
                        tooltip: {
                          title: '详情',
                          placement: 'top',
                        },
                        onClick: goProductDrawer.bind(null, record),
                      },
                      {
                        icon: 'ant-design:edit-filled',
                        tooltip: {
                          title: '编辑',
                          placement: 'top',
                        },
                        onClick: handleOpenProductDrawer.bind(null, true, { isEdit: true, record }),
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
                          confirm: handleDeleteProduct.bind(null, record),
                        },
                      },
                    ]"
                  />
                </template>
              </template>
            </BasicTable>
            <div v-else class="device-card-wrap">
              <ProductCardList :params="params" :api="getDeviceProfiles" @get-method="getMethod"
                               @delete="handleDel" @edit="handleEdit" @view="handleView">
                <template #header>
                  <Button type="primary" @click="handleOpenProductDrawer(true, { isEdit: false })"
                            preIcon="ant-design:plus-outlined">
                    添加产品
                  </Button>
                  <Button type="default" @click="handleClickSwap"
                            preIcon="ant-design:swap-outlined">切换视图
                  </Button>
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
              </ProductCardList>
            </div>
            <ProductModal @register="productDrawerRegister" @success="reloadList"/>
          </div>
        </TabPane>
        <TabPane key="apppanel" tab="APP面板">
          <AppPanelIndex />
        </TabPane>
      </Tabs>
    </div>
  </div>
</template>

<script lang="ts" setup name="productPage">
import {reactive, ref} from 'vue';
import {Tabs} from 'ant-design-vue';
import {BasicTable, TableAction, useTable} from '@/components/Table';
import {Button, PopConfirmButton} from '@/components/Button';
import {getBasicColumns, getFormConfig} from './Data';
import {deleteDeviceProfile, getDeviceProfiles,} from '@/api/device/product';
import {useMessage} from '@/hooks/web/useMessage';
import moment from 'moment';
import AppPanelIndex from '../apppanel/index.vue';
import {useDrawer} from '@/components/Drawer';
import ProductModal from './components/ProductModal.vue';
import {useRouter} from 'vue-router';
import ProductCardList from "@/views/product/components/CardList/ProductCardList.vue";

defineOptions({name: 'Product'})

const TabPane = Tabs.TabPane;

const checkedKeys = ref<Array<string | number>>([]);
const {createMessage} = useMessage();
const [productDrawerRegister, {openDrawer: handleOpenProductDrawer}] = useDrawer();
const router = useRouter();

const state = reactive({
  isTableMode: false,
  activeKey: 'list',
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
  title: '产品模型列表',
  api: getDeviceProfiles,
  beforeFetch: (data) => {
    const {productName, model, manufacturerName, pageSize, pageNo, order} = data;
    return {
      pageNum: pageNo,
      pageSize,
      productName,
      model,
      manufacturerName,
      sortOrder: order == 'descend' ? 'DESC' : 'ASC',
    };
  },
  afterFetch: (data) => {
    return data.map((res) => {
      if (res.createTime) {
        res.createdTime = moment(res.createTime)?.format?.('YYYY-MM-DD HH:mm:ss') ?? res.createTime;
      }
      return res;
    });
  },
  columns: getBasicColumns(),
  useSearchForm: true,
  formConfig: getFormConfig(),
  fetchSetting: {
    listField: 'data',
    totalField: 'total',
  },
  // defSort: {
  //   field: 'name',
  //   order: 'ascend',
  // },
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

function goProductDrawer(record) {
  const params = {
    id: record.id,
    productIdentification: record.productIdentification,
    // 兼容旧菜单 path: detail/:id/:templateIdentification/:productIdentification
    // 执行 migrate_product_detail_route.sql 后可忽略该参数
    templateIdentification: record.templateIdentification || 'none',
  };
  router.push({ name: 'ProductDetail', params });
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
    await Promise.all([deleteDeviceProfile(checkedKeys.value)]);
    createMessage.success('删除成功');
  } catch (error) {
    console.error(error)
    //console.log(error);
    // createMessage.error('删除失败');
    createMessage.error(error.response.data.message);
  }
  reloadList();
}

async function handleDeleteProduct(record) {
  try {
    const {id} = record;
    await deleteDeviceProfile([id]);
    reloadList();
    //console.log('ret ...', ret);
    createMessage.success('删除成功');
  } catch (error) {
    console.error(error)
    createMessage.error(error.response.data.message);
    //console.log('handleDeleteProduct ...', error);
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

//详情按钮事件
function handleView(record) {
  goProductDrawer(record);
}

//编辑按钮事件
function handleEdit(record) {
  handleOpenProductDrawer(true, { isEdit: true, record });
}

//删除按钮事件
function handleDel(record) {
  handleDeleteProduct(record);
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
