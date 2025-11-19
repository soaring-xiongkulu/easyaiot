<template>
  <div class="model-wrapper">
    <div class="tab-content">
      <!-- 共享的搜索表单 -->
      <div class="search-form-wrapper">
        <BasicForm @register="registerForm"/>
      </div>

      <!-- 统一的标题和工具栏 -->
      <div class="view-header">
        <div class="view-title">设备运行状态</div>
        <div class="view-actions">
          <ButtonGroup>
            <Button
              :type="activeKey === 'card' ? 'primary' : 'default'"
              @click="handleTabChange('card')"
            >
              <template #icon>
                <Icon icon="ant-design:appstore-outlined" />
              </template>
              卡片视图
            </Button>
            <Button
              :type="activeKey === 'table' ? 'primary' : 'default'"
              @click="handleTabChange('table')"
            >
              <template #icon>
                <Icon icon="ant-design:table-outlined" />
              </template>
              表格视图
            </Button>
          </ButtonGroup>
        </div>
      </div>

      <!-- 卡片视图 -->
      <div v-show="activeKey === 'card'">
        <TingModelCardList 
          :params="params" 
          :api="getDevicethingModels" 
          :active-key="activeKey"
          :search-params="searchParams"
          @get-method="getMethod"
          @refresh="handleRefresh" 
          @view="handleView"
          @tab-change="handleTabChange"
        />
      </div>

      <!-- 表格视图 -->
      <div v-show="activeKey === 'table'">
        <BasicTable @register="registerTable">
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
      </div>
    </div>
    <Detail @register="registerModal"/>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive } from "vue";
import { Button, ButtonGroup } from 'ant-design-vue';
import { Icon } from '@/components/Icon';
import { BasicTable, TableAction, useTable } from '@/components/Table';
import { BasicForm, useForm } from '@/components/Form';
import { getBasicColumns, getFormConfig } from './tableData';
import { getDevicethingModels } from '@/api/device/devices';
import Detail from './components/Detail.vue';
import { useModal } from '@/components/Modal';
import { useMessage } from '@/hooks/web/useMessage';
import { useRoute } from "vue-router";
import TingModelCardList from "./components/CardList/TingModelCardList.vue";

const route = useRoute();
const { createMessage } = useMessage();

const activeKey = ref<string>('card');
const searchParams = reactive({});

// 共享的搜索表单
const [registerForm, { validate, getFieldsValue, resetFields }] = useForm({
  schemas: [
    {
      field: `name`,
      label: `健/名称`,
      component: 'Input',
    }
  ],
  labelWidth: 70,
  baseColProps: {span: 10},
  actionColOptions: {span: 6, offset: 8},
  autoSubmitOnEnter: true,
  submitFunc: handleSearchSubmit,
});

// 搜索表单提交
async function handleSearchSubmit() {
  const formData = await validate();
  Object.assign(searchParams, formData);
  // 触发当前视图的刷新
  if (activeKey.value === 'table') {
    reload();
  } else {
    cardListReload();
  }
}

const [registerTable, { reload }] = useTable({
  resizeHeightOffset: 16,
  api: getDevicethingModels,
  beforeFetch: (data) => {
    data['id'] = route.params.id;
    // 合并搜索参数
    return {
      ...data,
      ...searchParams,
    };
  },
  columns: getBasicColumns(),
  formConfig: getFormConfig(),
  useSearchForm: false, // 禁用表格内置的搜索表单，使用共享的表单
  showIndexColumn: false,
  showTableSetting: false,
  tableSetting: { fullScreen: true },
  fetchSetting: {
    listField: 'data',
    totalField: 'total',
  },
  actionColumn: {
    title: '操作',
    dataIndex: 'action',
    fixed: 'right',
    slots: { customRender: 'action' },
  },
});

const [registerModal, { openModal }] = useModal();

// 请求api时附带参数
const params = {
  id: route.params.id,
};

let cardListReload = () => {};

// 获取内部fetch方法;
function getMethod(m: any) {
  cardListReload = m;
}

//详情刷新事件
const handleRefresh = () => {
  if (activeKey.value === 'table') {
    reload();
  } else {
    cardListReload();
  }
  createMessage.success('刷新成功');
};

//详情按钮事件
function handleView(record) {
  openModal(true, {
    data: record,
  });
}

// 切换标签页
function handleTabChange(key: string) {
  activeKey.value = key;
  // 切换视图后，使用当前搜索参数刷新数据
  if (key === 'table') {
    reload();
  } else {
    cardListReload();
  }
}
</script>

<style lang="less" scoped>
.model-wrapper {
  background-color: #ffffff;
  border-radius: 12px;
  overflow: hidden;
  min-height: 100%;

  .tab-content {
    padding: 28px;
    background: #ffffff;
    min-height: 400px;
    animation: fadeIn 0.3s ease-in-out;

    .search-form-wrapper {
      padding: 16px;
      background: #ffffff;
      margin-bottom: 16px;
      border-radius: 8px;
    }

    .view-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 8px;
      margin-bottom: 20px;

      .view-title {
        font-size: 16px;
        font-weight: 600;
        line-height: 24px;
        color: #262626;
      }

      .view-actions {
        :deep(.ant-btn-group) {
          .ant-btn {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 6px 14px;
            font-size: 13px;
            font-weight: 500;
            border-radius: 6px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            height: 32px;

            &:first-child {
              border-top-right-radius: 0;
              border-bottom-right-radius: 0;
            }

            &:last-child {
              border-top-left-radius: 0;
              border-bottom-left-radius: 0;
            }

            &:hover:not(.ant-btn-primary) {
              color: #1890ff;
              border-color: #1890ff;
              background: rgba(24, 144, 255, 0.06);
            }

            &.ant-btn-primary {
              background: #1890ff;
              border-color: #1890ff;
              box-shadow: 0 2px 4px rgba(24, 144, 255, 0.2);
            }
          }
        }
      }
    }
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>

