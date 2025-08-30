<template>
  <div class="inference-card-list-wrapper p-2">
    <div class="p-4 bg-white" style="margin-bottom: 10px">
      <BasicForm @register="registerForm" @reset="handleSubmit" @submit="handleSubmit"/>
    </div>
    <div class="p-2 bg-white">
      <Spin :spinning="state.loading">
        <List
          :grid="{ gutter: 16, xs: 1, sm: 2, md: 2, lg: 3, xl: 3, xxl: 3 }"
          :data-source="data"
          :pagination="paginationProp"
        >
          <template #header>
            <div style="display: flex; align-items: center; justify-content: space-between;">
              <span style="padding-left: 7px; font-size: 16px; font-weight: 500;">推理任务</span>
              <div class="space-x-2">
                <slot name="header"></slot>
              </div>
            </div>
          </template>

          <template #renderItem="{ item }">
            <ListItem>
              <div
                class="card-item bg-white rounded-lg shadow-md overflow-hidden transition-all hover:shadow-lg"
                :class="{
                  'border-blue-500 border-2': item.status === 'PROCESSING',
                  'border-green-500': item.status === 'COMPLETED',
                  'border-red-500': item.status === 'FAILED'
                }"
              >
                <div class="card-header bg-gray-50 px-4 py-3 border-b">
                  <div class="flex justify-between items-center">
                    <span class="font-medium text-gray-900">#{{ item.id || '-' }}</span>
                    <a-tag :color="getStatusColor(item.status)">
                      {{ getStatusText(item.status) }}
                    </a-tag>
                  </div>
                  <div class="text-sm text-gray-500 mt-1">
                    {{ formatDateTime(item.start_time) }}
                  </div>
                </div>

                <div class="card-body p-4">
                  <div class="flex items-center mb-3">
                    <span class="text-gray-600 mr-2">模型:</span>
                    <span class="font-medium">{{ item.model?.name || '未知模型' }}</span>
                  </div>

                  <div class="mb-3">
                    <div class="text-gray-600 mb-1">输入源</div>
                    <div class="truncate text-sm">{{ item.input_source || '-' }}</div>
                  </div>

                  <div class="mb-3" v-if="item.processed_frames">
                    <div class="text-gray-600 mb-1">处理进度</div>
                    <a-progress
                      :percent="calculateProgress(item)"
                      status="active"
                      size="small"
                    />
                    <div class="text-xs text-gray-500 mt-1 text-right">
                      {{ item.processed_frames || 0 }}/{{ item.total_frames || 0 }} 帧
                    </div>
                  </div>
                </div>

                <div class="card-footer bg-gray-50 px-4 py-3 border-t flex justify-end space-x-2">
                  <a-button
                    size="small"
                    type="primary"
                    @click="handleExecute(item)"
                    preIcon="ant-design:play-circle-outlined"
                    :disabled="item.status === 'PROCESSING'"
                    v-if="item.status !== 'PROCESSING'"
                  >
                    执行
                  </a-button>

                  <a-button
                    size="small"
                    @click="handleView(item)"
                    preIcon="ant-design:eye-outlined"
                  >
                    详情
                  </a-button>
                  <a-button
                    size="small"
                    type="primary"
                    ghost
                    @click="handleResult(item)"
                    preIcon="ant-design:file-image-outlined"
                    :disabled="item.status !== 'COMPLETED'"
                  >
                    结果
                  </a-button>
                  <a-button
                    size="small"
                    danger
                    @click="handleDelete(item)"
                    preIcon="ant-design:delete-outlined"
                  >
                    删除
                  </a-button>
                </div>
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
import {List, Spin} from 'ant-design-vue';
import {propTypes} from '@/utils/propTypes';
import {isFunction} from '@/utils/is';
import {BasicForm, useForm} from "@/components/Form";

const ListItem = List.Item;

const props = defineProps({
  params: propTypes.object.def({}),
  api: propTypes.func,
  modelOptions: propTypes.array.def([]),
});

const emit = defineEmits(['view', 'result', 'delete', 'execute', 'getMethod']);

const data = ref([]);
const state = reactive({
  loading: true,
});

const page = ref(1);
const pageSize = ref(10);
const total = ref(0);

const paginationProp = ref({
  showSizeChanger: true,
  showQuickJumper: true,
  pageSize: pageSize.value,
  current: page.value,
  total: total.value,
  showTotal: (total: number) => `总 ${total} 条`,
  onChange: pageChange,
  onShowSizeChange: pageSizeChange,
});

onMounted(() => {
  fetch();
  emit('getMethod', fetch);
});


async function handleSubmit() {
  const formData = await validate();
  await fetch(formData);
}

// 新增表单配置
const [registerForm, {validate}] = useForm({
  schemas: [
    {
      field: 'model_id',
      label: '模型',
      component: 'Select',
      componentProps: {
        options: props.modelOptions,
        placeholder: '请选择模型',
        allowClear: true,
      },
    },
    {
      field: 'status',
      label: '状态',
      component: 'Select',
      componentProps: {
        options: [
          {label: '处理中', value: 'PROCESSING'},
          {label: '已完成', value: 'COMPLETED'},
          {label: '失败', value: 'FAILED'},
        ],
        placeholder: '请选择状态',
        allowClear: true,
      },
    },
    {
      field: 'start_time',
      label: '开始时间',
      component: 'DatePicker',
      componentProps: {
        type: 'daterange',
        rangeSeparator: '至',
        startPlaceholder: '开始日期',
        endPlaceholder: '结束日期',
        valueFormat: 'YYYY-MM-DD',
      },
    },
  ],
  labelWidth: 80,
  baseColProps: {span: 6},
  actionColOptions: {span: 12},
  autoSubmitOnEnter: true,
  submitFunc: handleSubmit,
});

async function fetch(p = {}) {
  const {api, params} = props;
  if (api && isFunction(api)) {
    state.loading = true;
    try {
      // 处理日期范围参数
      const formattedParams = {...p};
      if (p['start_time'] && Array.isArray(p['start_time'])) {
        formattedParams['start_time_from'] = p['start_time'][0];
        formattedParams['start_time_to'] = p['start_time'][1];
        delete formattedParams['start_time'];
      }

      const res = await api({
        ...params,
        pageNo: page.value,
        pageSize: pageSize.value,
        ...formattedParams
      });
      data.value = res.data;
      total.value = res.total;
    } catch (error) {
      console.error('获取推理任务失败:', error);
    } finally {
      state.loading = false;
    }
  }
}

function pageChange(p: number, pz: number) {
  page.value = p;
  pageSize.value = pz;
  fetch();
}

function pageSizeChange(_current: number, size: number) {
  pageSize.value = size;
  page.value = 1;
  fetch();
}

const handleExecute = (record: any) => {
  emit('execute', record);
};

const handleView = (record: any) => {
  emit('view', record);
};

const handleResult = (record: any) => {
  emit('result', record);
};

const handleDelete = (record: any) => {
  emit('delete', record);
};

const getStatusText = (status: string) => {
  const statusMap = {
    PROCESSING: '处理中',
    COMPLETED: '已完成',
    FAILED: '失败',
  };
  return statusMap[status] || status;
};

const getStatusColor = (status: string) => {
  const colors = {
    PROCESSING: 'blue',
    COMPLETED: 'green',
    FAILED: 'red',
  };
  return colors[status] || 'gray';
};

const formatDateTime = (dateString: string) => {
  if (!dateString) return '';
  return new Date(dateString).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
};

const calculateProgress = (record: any) => {
  if (!record.processed_frames || !record.total_frames) return 0;
  return Math.round((record.processed_frames / record.total_frames) * 100);
};
</script>

<style scoped>
.card-item {
  transition: transform 0.2s, box-shadow 0.2s;
}

.card-item:hover {
  transform: translateY(-4px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
}

.inference-card-list-wrapper {
  :deep(.ant-list-header) {
    border: 0;
    padding: 16px 0;
  }
}
</style>
