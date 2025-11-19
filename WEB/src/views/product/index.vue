<template>
  <div class="device-wrapper">
    <BasicTable @register="registerTable" v-if="state.isTableMode">
      <template #toolbar>
        <a-button type="primary" @click="handleOpenProductMolal(true, { type: true })"
                  preIcon="ant-design:plus-outlined">
          添加产品
        </a-button>
        <a-button type="default" @click="handleClickSwap"
                  preIcon="ant-design:swap-outlined">切换视图
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
        </PopConfirmButton
        >
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
                onClick: handleOpenProductMolal.bind(null, true, { type: false, record }),
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
    <div v-else>
      <ProductCardList :params="params" :api="getDeviceProfiles" @get-method="getMethod"
                       @delete="handleDel" @edit="handleEdit" @view="handleView">
        <template #header>
          <a-button type="primary" @click="handleOpenProductMolal(true, { type: true })"
                    preIcon="ant-design:plus-outlined">
            添加产品
          </a-button>
          <a-button type="default" @click="handleClickSwap"
                    preIcon="ant-design:swap-outlined">切换视图
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
      </ProductCardList>
    </div>
    <ProductModal @register="productModalRegister" @update="reloadList"/>
  </div>
</template>

<script lang="ts" setup name="productPage">
import {reactive, ref} from 'vue';
import {BasicTable, TableAction, useTable} from '@/components/Table';
import {PopConfirmButton} from '@/components/Button';
import {getBasicColumns, getFormConfig} from './Data';
import {deleteDeviceProfile, getDeviceProfiles,} from '@/api/device/product';
import {useMessage} from '@/hooks/web/useMessage';
import moment from 'moment';
import {useModal} from '@/components/Modal';
import ProductModal from './components/ProductModal.vue';
import {useRouter} from 'vue-router';
import ProductCardList from "@/views/product/components/CardList/ProductCardList.vue";

defineOptions({name: 'Product'})

const checkedKeys = ref<Array<string | number>>([]);
const {createMessage} = useMessage();
const [productModalRegister, {openModal: handleOpenProductMolal}] = useModal();
const router = useRouter();

const state = reactive({
  isTableMode: false,
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
    const {productName, model, manufacturerName, pageSize, page, order} = data;
    let params = {
      page,
      pageSize,
      productName, model, manufacturerName,
      sortOrder: order == 'descend' ? 'DESC' : 'ASC',
    };
    return params;
  },
  afterFetch: (data) => {
    // alert(data);
    console.info("data...", data);
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
  // alert(JSON.stringify(record));
  const params = {
    id: record.id,
    templateIdentification: (record.templateIdentification == '' ? "xxx" : record.templateIdentification),
    productIdentification: record.productIdentification
  };
  // alert(JSON.stringify(params))
  router.push({name: 'ProductDetail', params});
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
  handleOpenProductMolal(true, {record});
  cardListReload();
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
  :deep(.ant-tabs-nav) {
    padding: 5px 0 0 25px;
  }

  :deep(.ant-form-item) {
    margin-bottom: 10px;
  }

  .device-tab {
    padding: 16px 19px 0 15px;

    .ant-tabs {
      background-color: #FFFFFF;

      :deep(.ant-tabs-nav) {
        padding: 5px 0 0 25px;
      }
    }
  }
}
</style>

