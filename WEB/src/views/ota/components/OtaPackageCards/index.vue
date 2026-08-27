<template>
  <div class="ota-package-card-list-wrapper">
    <div class="search-bar">
      <BasicForm @register="registerForm"/>
    </div>
    <div class="list-panel">
      <Spin :spinning="state.loading">
        <List
          :grid="{ gutter: 2, xs: 1, sm: 2, md: 4, lg: 4, xl: 4, xxl: 4 }"
          :data-source="data"
          :pagination="paginationProp"
        >
          <template #header>
            <div class="list-header">
              <span class="list-title">OTA升级包列表</span>
              <div class="list-actions">
                <slot name="header"></slot>
              </div>
            </div>
          </template>

          <template #renderItem="{ item }">
            <ListItem class="package-item normal">
              <div class="package-info">
                <div class="title o2">{{ item.name }}</div>
                <div class="props">
                  <div class="flex" style="justify-content: space-between;">
                    <div class="prop">
                      <div class="label">包类型</div>
                      <div class="value">
                        {{ item.type === '0' ? '软件包' : item.type === '1' ? '固件包' : item.type === '2' ? 'APP包' : item.type === '3' ? 'PC包' : '未知' }}
                      </div>
                    </div>
                    <div class="prop">
                      <div class="label">升级方式</div>
                      <div class="value">
                        {{ item.upgradeMode === 0 ? '非强制' : item.upgradeMode === 1 ? '强制' : '-' }}
                      </div>
                    </div>
                  </div>
                  <div class="prop">
                    <div class="label">包版本号</div>
                    <div class="value">{{ item.version || '-' }}</div>
                  </div>
                  <div class="flex" style="justify-content: space-between;">
                    <div class="prop">
                      <div class="label">状态</div>
                      <div class="value">
                        {{ {0:'未验证',1:'测试中',2:'已发布',3:'待发布',4:'已撤回'}[Number(item.status)] || '-' }}
                      </div>
                    </div>
                    <div class="prop" v-if="Number(item.publishStrategy) === 1">
                      <div class="label">灰度</div>
                      <div class="value">{{ {1:'设备级',2:'产品级',3:'全量'}[Number(item.grayLadder)] || '-' }}</div>
                    </div>
                  </div>
                </div>
                <div class="btns">
                  <div class="btn" @click="handleDownload(item)">
                    <Icon icon="ant-design:download-outlined" :size="15" color="#3B82F6" />
                  </div>
                  <div class="btn" @click="handleView(item)">
                    <Icon icon="ant-design:eye-filled" :size="15" color="#3B82F6" />
                  </div>
                  <div class="btn" @click="handleEdit(item)">
                    <Icon icon="ant-design:edit-filled" :size="15" color="#3B82F6" />
                  </div>
                  <Popconfirm
                    title="是否确认删除？"
                    ok-text="是"
                    cancel-text="否"
                    @confirm="handleDelete(item)"
                  >
                    <div class="btn">
                      <Icon icon="material-symbols:delete-outline-rounded" :size="15" color="#DC2626" />
                    </div>
                  </Popconfirm>
                  <Dropdown :trigger="['click']">
                    <div class="btn">
                      <Icon icon="ant-design:more-outlined" :size="15" color="#3B82F6" />
                    </div>
                    <template #overlay>
                      <Menu @click="onMenuClick($event, item)">
                        <MenuItem v-if="Number(item.status) === 0" key="submit-test">提交测试</MenuItem>
                        <MenuItem v-if="Number(item.status) === 1" key="test-result">测试结果录入</MenuItem>
                        <MenuItem v-if="Number(item.status) !== 2" key="publish">发布</MenuItem>
                        <MenuItem v-if="canGrayOps(item)" key="expand">扩大灰度范围</MenuItem>
                        <MenuItem v-if="canGrayOps(item)" key="promote">灰度升阶</MenuItem>
                        <MenuItem v-if="Number(item.status) === 2" key="withdraw">撤回发布</MenuItem>
                        <MenuItem key="stats">升级统计</MenuItem>
                      </Menu>
                    </template>
                  </Dropdown>
                </div>
              </div>
              <div class="package-img">
                <img :src="OTA" alt="" class="img" @click="handleView(item)">
              </div>
            </ListItem>
          </template>
        </List>
      </Spin>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { onMounted, reactive, ref } from 'vue';
import { Dropdown, List, Menu, Popconfirm, Spin } from 'ant-design-vue';
import { BasicForm, useForm } from '@/components/Form';
import { propTypes } from '@/utils/propTypes';
import { isFunction } from '@/utils/is';
import { useMessage } from '@/hooks/web/useMessage';
import { Icon } from '@/components/Icon';
import moment from 'moment';

import OTA from "@/assets/images/ota/ota.png";

const ListItem = List.Item;
const MenuItem = Menu.Item;

// 组件接收参数
const props = defineProps({
  // 请求API的参数
  params: propTypes.object.def({}),
  // api
  api: propTypes.func,
});

const { createMessage } = useMessage();

// 暴露内部方法
const emit = defineEmits(['getMethod', 'delete', 'edit', 'view', 'download', 'action']);

//灰度中（设备级/产品级）才允许扩大范围或升阶
function canGrayOps(item) {
  return (
    Number(item.status) === 2 &&
    Number(item.publishStrategy) === 1 &&
    (Number(item.grayLadder) === 1 || Number(item.grayLadder) === 2)
  );
}

//生命周期菜单点击
function onMenuClick({ key }, item) {
  emit('action', String(key), item);
}

// 数据
const data = ref([]);
const state = reactive({
  loading: true,
});

// 表单
const [registerForm, { validate }] = useForm({
  schemas: [
    {
      field: `name`,
      label: `包名称`,
      component: 'Input',
    },
    {
      field: `type`,
      label: `包类型`,
      component: 'Select',
      componentProps: {
        options: [
          { value: '', label: '全部' },
          { value: '0', label: '软件包' },
          { value: '1', label: '固件包' },
          { value: '2', label: 'APP包' },
          { value: '3', label: 'PC包' },
        ],
      },
      defaultValue: '',
    },
    {
      field: `version`,
      label: `包版本号`,
      component: 'Input',
    },
  ],
  labelWidth: 80,
  baseColProps: { span: 6 },
  actionColOptions: { span: 6 },
  autoSubmitOnEnter: true,
  submitFunc: handleSubmit,
});

// 表单提交
async function handleSubmit() {
  const formData = await validate();
  await fetch(formData);
}

// 自动请求并暴露内部方法
onMounted(() => {
  fetch();
  emit('getMethod', fetch);
});

async function fetch(p = {}) {
  const { api, params } = props;
  if (api && isFunction(api)) {
    try {
      state.loading = true;
      const res = await api({ ...params, pageNo: page.value, pageSize: pageSize.value, ...p });
      // 根据表格配置，返回格式为 { data: [...], total: ... }
      data.value = res.data || [];
      total.value = res.total || 0;
    } catch (error) {
      console.error('获取数据失败:', error);
      data.value = [];
      total.value = 0;
    } finally {
      hideLoading();
    }
  }
}

function hideLoading() {
  state.loading = false;
}

// 分页相关
const page = ref(1);
const pageSize = ref(8);
const total = ref(0);
const paginationProp = ref({
  showSizeChanger: false,
  showQuickJumper: true,
  pageSize,
  current: page,
  total,
  showTotal: (total: number) => `总 ${total} 条`,
  onChange: pageChange,
  onShowSizeChange: pageSizeChange,
});

function pageChange(p: number, pz: number) {
  page.value = p;
  pageSize.value = pz;
  fetch();
}

function pageSizeChange(_current, size: number) {
  pageSize.value = size;
  fetch();
}

function formatTime(time: string) {
  if (!time) return '-';
  return moment(time).format('YYYY-MM-DD HH:mm:ss');
}

async function handleView(record: object) {
  emit('view', record);
}

async function handleEdit(record: object) {
  emit('edit', record);
}

async function handleDelete(record: object) {
  emit('delete', record);
}

async function handleDownload(record: object) {
  emit('download', record);
}
</script>

<style lang="less" scoped>
.ota-package-card-list-wrapper {
  background: #fff !important;
  flex: 1;
  height: 100%;
  min-height: 100%;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.search-bar {
  padding: 16px 16px 0;
  margin-bottom: 10px;
  background: #fff;
  flex-shrink: 0;
}

.list-panel {
  background: #fff;
  padding: 0 8px 16px;
  flex: 1;
  min-height: 0;

  :deep(.ant-list-header) {
    border: 0;
    padding: 8px 12px 16px;
    background: transparent;
  }

  :deep(.ant-list),
  :deep(.ant-list-items),
  :deep(.ant-row) {
    background: #fff !important;
  }

  :deep(.ant-spin-nested-loading),
  :deep(.ant-spin-container) {
    background: #fff !important;
  }

  :deep(.ant-list-pagination) {
    margin-top: 20px;
    text-align: center;
  }
}

.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.list-title {
  padding-left: 4px;
  font-size: 16px;
  font-weight: 500;
  line-height: 24px;
  color: #181818;
}

.list-actions {
  display: flex;
  gap: 8px;
}

.ota-package-card-list-wrapper {
  :deep(.ant-list-header) {
    border-block-end: 0;
  }
  :deep(.ant-list-header) {
    padding-top: 0;
    padding-bottom: 8px;
  }
  :deep(.ant-list) {
    padding: 6px;
  }
  :deep(.ant-list-item) {
    margin: 6px;
  }
  :deep(.package-item) {
    overflow: hidden;
    box-shadow: 0 0 4px #00000026;
    border-radius: 8px;
    padding: 16px 0;
    position: relative;
    background-color: #fff;
    background-repeat: no-repeat;
    background-position: center center;
    background-size: 104% 104%;
    transition: all 0.5s;
    min-height: 208px;
    height: 100%;

    &.normal {
      background-image: url('@/assets/images/product/blue-bg.719b437a.png');
    }

    &.error {
      background-image: url('@/assets/images/product/red-bg.101af5ac.png');
    }

    .package-info {
      flex-direction: column;
      max-width: calc(100% - 128px);
      padding-left: 16px;

      .title {
        font-size: 16px;
        font-weight: 600;
        color: #050708;
        line-height: 20px;
        height: 40px;
      }

      .props {
        margin-top: 10px;

        .prop {
          flex: 1;
          margin-bottom: 10px;

          .label {
            font-size: 12px;
            font-weight: 400;
            color: #666;
            line-height: 14px;
          }

          .value {
            font-size: 14px;
            font-weight: 600;
            color: #050708;
            line-height: 14px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            margin-top: 6px;
          }
        }
      }

      .btns {
        display: flex;
        position: absolute;
        left: 16px;
        bottom: 16px;
        margin-top: 20px;
        width: 130px;
        height: 28px;
        border-radius: 45px;
        justify-content: space-around;
        padding: 0 10px;
        align-items: center;
        border: 2px solid #266cfbff;

        .btn {
          width: 28px;
          text-align: center;
          position: relative;
          cursor: pointer;

          &:before {
            content: '';
            display: block;
            position: absolute;
            width: 1px;
            height: 7px;
            background-color: #e2e2e2;
            left: 0;
            top: 9px;
          }

          &:first-child:before {
            display: none;
          }

          :deep(.anticon) {
            display: flex;
            align-items: center;
            justify-content: center;
            color: #87CEEB;
            transition: color 0.3s;
          }

          &:hover :deep(.anticon) {
            color: #5BA3F5;
          }
        }
      }
    }

    .package-img {
      position: absolute;
      right: 20px;
      top: 50px;

      img {
        cursor: pointer;
        width: 120px;
      }
    }
  }
}
</style>

