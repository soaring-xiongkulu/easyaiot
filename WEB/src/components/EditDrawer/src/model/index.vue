<template>
  <div class="modal-warpper">
    <BasicTable @register="registerTable" v-if="state.isTableMode">
      <template #toolbar>
        <a-button type="primary" @click="handleClickSwap"
                  preIcon="ant-design:swap-outlined">切换视图
        </a-button>
      </template>
      <template #action="{ record }">
        <TableAction
            :actions="[
            {
              tooltip: {
                title: '刷新',
                placement: 'top',
              },
              icon: 'ant-design:redo-outlined',
              onClick: () => handleRefresh(),
            },
            {
              icon: 'ant-design:eye-filled',
              tooltip: {
                title: '详情',
                placement: 'top',
              },
              onClick: handleView.bind(null, record),
            },
          ]"
        />
      </template>
    </BasicTable>
    <div v-else>
      <TingModelCardList :params="params" :api="getDevicethingModels" @get-method="getMethod"
                         @refresh="handleRefresh" @view="handleView">
        <template #header>
          <a-button type="primary" @click="handleClickSwap"
                    preIcon="ant-design:swap-outlined">切换视图
          </a-button>
        </template>
      </TingModelCardList>
    </div>
    <Detail @register="registerModal"/>
  </div>
</template>
<script lang="ts" setup>
import {BasicTable, TableAction, useTable} from '@/components/Table';
import {getBasicColumns, getFormConfig} from './tableData';
import {getDevicethingModels} from '@/api/device/devices';
import Detail from './components/Detail.vue';
import {useModal} from '@/components/Modal';
import {useMessage} from '@/hooks/web/useMessage';
import {useRoute} from "vue-router";
import {reactive} from "vue";
import TingModelCardList from "@/components/EditDrawer/src/model/components/CardList/TingModelCardList.vue";

const route = useRoute()
const {createMessage} = useMessage();

const state = reactive({
  isTableMode: false,
});

const [registerTable, {reload}] = useTable({
  resizeHeightOffset: 16,
  // title: '物模型数据',
  api: getDevicethingModels,
  beforeFetch: (data) => {
    data['id'] = route.params.id;
    return {
      ...data,
    };
  },
  columns: getBasicColumns(),
  formConfig: getFormConfig(),
  useSearchForm: true,
  showIndexColumn: false,
  showTableSetting: false,
  tableSetting: {fullScreen: true},
  fetchSetting: {
    listField: 'data',
    totalField: 'total',
  },
  actionColumn: {
    title: '操作',
    dataIndex: 'action',
    fixed: 'right',
    slots: {customRender: 'action'},
  },
});

const [registerModal, {openModal}] = useModal();

// 请求api时附带参数
const params = {
  id: route.params.id,
};

let cardListReload = () => {
};

// 获取内部fetch方法;
function getMethod(m: any) {
  cardListReload = m;
}

//详情刷新事件
const handleRefresh = () => {
  reload();
  createMessage.success('刷新成功');
};

//详情按钮事件
function handleView(record) {
  openModal(true, {
    data: record,
  });
}

// 切换视图
function handleClickSwap() {
  state.isTableMode = !state.isTableMode;
}
</script>
<style lang="less" scoped>
button {
  margin-right: 10px;
}

.modal-warpper {
  background-color: #FFFFFF;
}
</style>
