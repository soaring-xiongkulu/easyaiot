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
              <span class="list-title">测试白名单设备</span>
              <div class="list-actions">
                <slot name="header"></slot>
              </div>
            </div>
          </template>

          <template #renderItem="{ item }">
            <ListItem class="ota-card-item normal">
              <div class="card-info">
                <div class="status s-green">有效</div>
                <div class="title">
                  {{ item.deviceIdentification || '-' }}
                  <span v-if="item.deviceName && item.deviceName !== item.deviceIdentification" class="sub">
                    {{ item.deviceName }}
                  </span>
                </div>
                <div class="props">
                  <div class="flex" style="justify-content: space-between; gap: 8px;">
                    <div class="prop">
                      <div class="label">版本包</div>
                      <div class="value">{{ item.pkgName || '-' }}</div>
                    </div>
                    <div class="prop">
                      <div class="label">状态</div>
                      <div class="value">有效</div>
                    </div>
                  </div>
                  <div class="prop">
                    <div class="label">备注</div>
                    <div class="value" :class="{muted: !item.remark}">{{ item.remark || '-' }}</div>
                  </div>
                </div>
                <div class="foot">
                  <span class="foot-meta">添加时间：{{ formatTime(item.createdTime) }}</span>
                  <Popconfirm title="确认将该设备移出测试白名单？" @confirm="handleRemove(item)">
                    <span class="btns">
                      <span class="btn" title="移出白名单">
                        <Icon icon="material-symbols:delete-outline-rounded" :size="15" color="#DC2626" />
                      </span>
                    </span>
                  </Popconfirm>
                </div>
              </div>
              <div class="card-img">
                <img :src="OTA" alt="" class="img">
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
import {fetchPkgList} from '/@/api/device/ota';
import {TYPE_MAP} from '../../Data';
import OTA from '@/assets/images/ota/ota.png';

defineOptions({name: 'OtaWhiteListCards'});

const ListItem = List.Item;

// 组件接收参数
const props = defineProps({
  // 请求API的参数
  params: propTypes.object.def({}),
  // api
  api: propTypes.func,
});

// 暴露内部方法
const emit = defineEmits(['getMethod', 'remove']);

// 数据
const data = ref([]);
const state = reactive({
  loading: true,
});

// 表单（与白名单表格搜索项保持一致：按版本包过滤）
const [registerForm, {validate, updateSchema}] = useForm({
  schemas: [
    {
      field: `pkgId`,
      label: `版本包`,
      component: 'Select',
      componentProps: {
        placeholder: '全部版本包',
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

//加载版本包下拉选项
async function loadPkgOptions() {
  try {
    const res = await fetchPkgList({pageNo: 1, pageSize: 500});
    const options = (res.data || []).map((p) => {
      const meta = TYPE_MAP[p.type] || TYPE_MAP[Number(p.type)];
      return {label: `${p.name}（v${p.version} · ${meta ? meta.label : '-'}）`, value: p.id};
    });
    updateSchema({field: 'pkgId', componentProps: {options}});
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
  loadPkgOptions();
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

async function handleRemove(record: object) {
  emit('remove', record);
}

defineExpose({fetch});
</script>

<style lang="less" scoped>
@import '../ota-card-shared.less';
</style>
