<template>
  <div class="ota-card-list-wrapper">
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
            <ListItem class="ota-card-item normal">
              <div class="card-info">
                <div class="status" :class="statusMeta(item.status)?.cls || 's-gray'">
                  {{ statusMeta(item.status)?.label || '未知' }}
                </div>
                <div class="title">
                  {{ item.name }}
                  <span v-if="item.productIdentification" class="sub">适用产品：{{ item.productIdentification }}</span>
                </div>
                <div class="props">
                  <div class="flex" style="justify-content: space-between; gap: 8px;">
                    <div class="prop">
                      <div class="label">包类型</div>
                      <div class="value">{{ typeMeta(item.type)?.label || '未知' }}</div>
                    </div>
                    <div class="prop">
                      <div class="label">升级方式</div>
                      <div class="value">{{ Number(item.upgradeMode) === 1 ? '强制' : '非强制' }}</div>
                    </div>
                  </div>
                  <div class="flex" style="justify-content: space-between; gap: 8px;">
                    <div class="prop">
                      <div class="label">包版本号</div>
                      <div class="value">{{ item.version || '-' }}</div>
                    </div>
                    <div class="prop">
                      <div class="label">上传时间</div>
                      <div class="value">{{ formatTime(item.uploadTime) }}</div>
                    </div>
                  </div>
                  <div class="prop" v-if="Number(item.publishStrategy) === 1">
                    <div class="label">灰度阶梯</div>
                    <div class="value">{{ GRAY_LADDER_MAP[item.grayLadder] || GRAY_LADDER_MAP[Number(item.grayLadder)] || '-' }}</div>
                  </div>
                </div>
                <div class="foot">
                  <span class="btns">
                    <span class="btn" @click="handleDownload(item)">
                      <Icon icon="ant-design:download-outlined" :size="15" color="#3B82F6" />
                    </span>
                    <span class="btn" @click="handleView(item)">
                      <Icon icon="ant-design:eye-filled" :size="15" color="#3B82F6" />
                    </span>
                    <span class="btn" @click="handleEdit(item)">
                      <Icon icon="ant-design:edit-filled" :size="15" color="#3B82F6" />
                    </span>
                    <span class="btn" title="升级记录" @click="handleRecords(item)">
                      <Icon icon="ant-design:profile-outlined" :size="15" color="#3B82F6" />
                    </span>
                    <Popconfirm
                      title="是否确认删除？"
                      ok-text="是"
                      cancel-text="否"
                      @confirm="handleDelete(item)"
                    >
                      <span class="btn">
                        <Icon icon="material-symbols:delete-outline-rounded" :size="15" color="#DC2626" />
                      </span>
                    </Popconfirm>
                    <Dropdown :trigger="['click']">
                      <span class="btn">
                        <Icon icon="ant-design:more-outlined" :size="15" color="#3B82F6" />
                      </span>
                      <template #overlay>
                        <Menu @click="onMenuClick($event, item)">
                          <MenuItem v-if="Number(item.status) === 0" key="submit-test">提交测试</MenuItem>
                          <MenuItem v-if="Number(item.status) === 1" key="test-result">测试结果录入</MenuItem>
                          <MenuItem v-if="Number(item.status) !== 2" key="publish">发布</MenuItem>
                          <MenuItem v-if="canGrayOps(item)" key="expand">扩大灰度范围</MenuItem>
                          <MenuItem v-if="canGrayOps(item)" key="promote">灰度升阶</MenuItem>
                          <MenuItem v-if="Number(item.status) === 2" key="withdraw">撤回发布</MenuItem>
                          <MenuItem key="records">升级记录</MenuItem>
                          <MenuItem key="stats">升级统计</MenuItem>
                        </Menu>
                      </template>
                    </Dropdown>
                  </span>
                </div>
              </div>
              <div class="card-img">
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
import { Icon } from '@/components/Icon';
import moment from 'moment';

import { TYPE_MAP, STATUS_MAP, GRAY_LADDER_MAP } from '../../Data';

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

// 暴露内部方法
const emit = defineEmits(['getMethod', 'delete', 'edit', 'view', 'download', 'records', 'action']);

function typeMeta(type) {
  return TYPE_MAP[type] || TYPE_MAP[Number(type)];
}

function statusMeta(status) {
  const meta = STATUS_MAP[status] || STATUS_MAP[Number(status)];
  if (!meta) {
    return null;
  }
  const clsMap = { default: 's-gray', processing: 's-blue', success: 's-green', warning: 's-orange', error: 's-red' };
  return { label: meta.label, cls: clsMap[meta.color] || 's-gray' };
}

function formatTime(time: string) {
  if (!time) return '-';
  return moment(time).format('YYYY-MM-DD HH:mm');
}

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

async function handleRecords(record: object) {
  emit('records', record);
}
</script>

<style lang="less" scoped>
@import '../ota-card-shared.less';
</style>
