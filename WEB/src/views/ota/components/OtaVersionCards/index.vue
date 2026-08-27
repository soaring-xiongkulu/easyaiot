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
              <span class="list-title">设备版本档案</span>
              <div class="list-actions">
                <slot name="header"></slot>
              </div>
            </div>
          </template>

          <template #renderItem="{ item }">
            <ListItem class="ota-card-item normal">
              <div class="card-info">
                <div class="status" :class="Number(item.upgradeMode) === 1 ? 's-orange' : 's-blue'">
                  {{ Number(item.upgradeMode) === 1 ? '强制升级' : '非强制升级' }}
                </div>
                <div class="title">
                  {{ item.productIdentification || '-' }}
                  <span v-if="item.deviceVersion" class="sub">设备版本号：{{ item.deviceVersion }}</span>
                </div>
                <div class="props">
                  <div class="prop">
                    <div class="label">设备版本号</div>
                    <div class="value">{{ item.deviceVersion || '-' }}</div>
                  </div>
                  <div class="flex" style="justify-content: space-between; gap: 8px;">
                    <div class="prop">
                      <div class="label">绑定软件包</div>
                      <div class="value" :class="{muted: !item.appPkgName}">{{ item.appPkgName || '未绑定' }}</div>
                    </div>
                    <div class="prop">
                      <div class="label">绑定固件包</div>
                      <div class="value" :class="{muted: !item.osPkgName}">{{ item.osPkgName || '未绑定' }}</div>
                    </div>
                  </div>
                  <div class="prop" v-if="item.remark">
                    <div class="label">描述</div>
                    <div class="value">{{ item.remark }}</div>
                  </div>
                </div>
                <div class="foot">
                  <span class="foot-meta">更新时间：{{ formatTime(item.updatedTime || item.createdTime) }}</span>
                  <span class="btns">
                    <span class="btn" title="编辑" @click="handleEdit(item)">
                      <Icon icon="ant-design:edit-filled" :size="15" color="#3B82F6" />
                    </span>
                    <Popconfirm title="确认删除该版本档案？" @confirm="handleDelete(item)">
                      <span class="btn" title="删除">
                        <Icon icon="material-symbols:delete-outline-rounded" :size="15" color="#DC2626" />
                      </span>
                    </Popconfirm>
                  </span>
                </div>
              </div>
              <div class="card-img">
                <img :src="OTA" alt="" class="img" @click="handleEdit(item)">
              </div>
            </ListItem>
          </template>
        </List>
      </Spin>
    </div>
  </div>
</template>

<script lang="ts" setup>
import {onMounted, reactive, ref} from 'vue';
import {List, Popconfirm, Spin} from 'ant-design-vue';
import {BasicForm, useForm} from '@/components/Form';
import {propTypes} from '@/utils/propTypes';
import {isFunction} from '@/utils/is';
import {Icon} from '@/components/Icon';
import moment from 'moment';
import {getDeviceProfiles} from '@/api/device/product';
import OTA from '@/assets/images/ota/ota.png';

defineOptions({name: 'OtaVersionCards'});

const ListItem = List.Item;

// 组件接收参数
const props = defineProps({
  // 请求API的参数
  params: propTypes.object.def({}),
  // api
  api: propTypes.func,
});

// 暴露内部方法
const emit = defineEmits(['getMethod', 'edit', 'delete']);

// 数据
const data = ref([]);
const state = reactive({
  loading: true,
});

// 表单（与版本档案表格搜索项保持一致：按产品过滤）
const [registerForm, {validate, updateSchema}] = useForm({
  schemas: [
    {
      field: `productIdentification`,
      label: `产品`,
      component: 'Select',
      componentProps: {
        placeholder: '全部产品',
        allowClear: true,
        showSearch: true,
        optionFilterProp: 'label',
        options: [],
      },
    },
  ],
  labelWidth: 80,
  baseColProps: {span: 6},
  actionColOptions: {span: 6},
  autoSubmitOnEnter: true,
  submitFunc: handleSubmit,
});

//加载产品下拉选项
async function loadProductOptions() {
  try {
    const res = await getDeviceProfiles({page: 1, pageSize: 200});
    const options = (res.data || []).map((p) => ({
      label: p.productName,
      value: p.productIdentification,
    }));
    updateSchema({field: 'productIdentification', componentProps: {options}});
  } catch (e) {
    console.error(e);
  }
}

function formatTime(time: string) {
  if (!time) return '-';
  return moment(time).format('YYYY-MM-DD HH:mm');
}

// 表单提交
async function handleSubmit() {
  const formData = await validate();
  await fetch(formData);
}

// 自动请求并暴露内部方法
onMounted(() => {
  loadProductOptions();
  fetch();
  emit('getMethod', fetch);
});

async function fetch(p = {}) {
  const {api, params} = props;
  if (api && isFunction(api)) {
    try {
      state.loading = true;
      const res = await api({...params, pageNo: page.value, pageSize: pageSize.value, ...p});
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

async function handleEdit(record: object) {
  emit('edit', record);
}

async function handleDelete(record: object) {
  emit('delete', record);
}

defineExpose({fetch});
</script>

<style lang="less" scoped>
@import '../ota-card-shared.less';
</style>
