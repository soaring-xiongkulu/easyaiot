<template>
  <div class="export-card-list-wrapper">
    <div class="p-4 bg-white" style="margin-bottom: 10px">
      <BasicForm @register="registerForm" @reset="handleSubmit" @field-value-change="handleFieldValueChange"/>
    </div>
    <div class="bg-white">
      <Spin :spinning="state.loading">
        <List
          :grid="{ gutter: 2, xs: 1, sm: 2, md: 4, lg: 4, xl: 6, xxl: 6 }"
          :data-source="data"
          :pagination="paginationProp"
        >
          <template #header>
            <div
              style="display: flex;align-items: center;justify-content: space-between;flex-direction: row;">
              <span style="padding-left: 7px;font-size: 16px;font-weight: 500;line-height: 24px;">导出记录列表</span>
              <div class="space-x-2">
                <slot name="header"></slot>
              </div>
            </div>
          </template>
          <template #renderItem="{ item }">
            <ListItem class="export-list-item">
              <div class="export-card-box">
                <div class="export-card-cont">
                  <!-- 格式图标 -->
                  <div class="export-format-container">
                    <div class="format-icon" :class="`format-${item.format}`">
                      {{ item.format === 'onnx' ? 'ONNX' : 'OV' }}
                    </div>
                  </div>

                  <h6 class="export-card-title">
                    <a>导出记录 #{{ item.id }}</a>
                  </h6>

                  <!-- 标签区域 -->
                  <div class="export-tags">
                    <Tag color="#1890ff">模型ID: {{ item.model_id }}</Tag>
                    <Tag :color="getStatusColor(item.status)">{{ getStatusText(item.status) }}</Tag>
                    <Tag color="#8c8c8c">{{ formatDate(item.created_at) }}</Tag>
                  </div>

                  <div class="export-info">
                    <div class="info-item">
                      <span class="info-label">格式:</span>
                      <span class="info-value">{{ item.format === 'onnx' ? 'ONNX' : 'OpenVINO' }}</span>
                    </div>
                    <div class="info-item" v-if="item.model_name">
                      <span class="info-label">模型:</span>
                      <span class="info-value">{{ item.model_name }}</span>
                    </div>
                  </div>

                  <div class="btns">
                    <div class="btn-group">
                      <div 
                        class="btn" 
                        @click="handleDownload(item)" 
                        title="下载"
                        :class="{ disabled: item.status !== 'COMPLETED' }"
                      >
                        <DownloadOutlined style="font-size: 16px;"/>
                      </div>
                      <Popconfirm
                        title="是否确认删除？"
                        @confirm="handleDelete(item)"
                      >
                        <div class="btn">
                          <DeleteOutlined style="font-size: 16px;"/>
                        </div>
                      </Popconfirm>
                    </div>
                  </div>
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
import {onMounted, reactive, ref, computed, watch} from 'vue';
import {List, Popconfirm, Spin, Tag} from 'ant-design-vue';
import {BasicForm, useForm} from '@/components/Form';
import {propTypes} from '@/utils/propTypes';
import {isFunction} from '@/utils/is';
import {DeleteOutlined, DownloadOutlined} from '@ant-design/icons-vue';

defineOptions({name: 'ModelExportCardList'})

const ListItem = List.Item;

const props = defineProps({
  params: propTypes.object.def({}),
  api: propTypes.func,
  modelOptions: propTypes.array.def([]),
});

const emit = defineEmits(['getMethod', 'delete', 'download', 'modelChange', 'field-value-change']);

const data = ref([]);
const state = reactive({
  loading: true,
});

const [registerForm, {validate, updateSchema}] = useForm({
  schemas: [
    {
      field: `status`,
      label: `状态`,
      component: 'Select',
      componentProps: {
        placeholder: '请选择状态',
        allowClear: true,
        options: [
          {label: '等待中', value: 'PENDING'},
          {label: '处理中', value: 'PROCESSING'},
          {label: '已完成', value: 'COMPLETED'},
          {label: '失败', value: 'FAILED'},
        ],
      },
    },
  ],
  labelWidth: 80,
  baseColProps: {span: 6},
  actionColOptions: {span: 24}, // 让按钮在第一行显示
  autoSubmitOnEnter: true,
  submitFunc: handleSubmit,
});


onMounted(() => {
  fetch();
  emit('getMethod', fetch);
});

// 监听params变化，自动刷新数据
watch(() => props.params, () => {
  fetch();
}, { deep: true });

async function handleSubmit() {
  const formData = await validate();
  await fetch(formData);
}

// 处理表单字段值变化，实时通知父组件
function handleFieldValueChange(field: string, value: any) {
  emit('field-value-change', field, value);
}

async function fetch(p = {}) {
  const {api, params} = props;
  if (api && isFunction(api)) {
    state.loading = true;
    try {
      const res = await api({...params, page: page.value, pageSize: pageSize.value, ...p});
      if (res.success && res.data) {
        data.value = res.data.items || res.data.list || [];
        total.value = res.data.total || 0;
      } else {
        data.value = res.data?.items || res.data?.list || res.data || [];
        total.value = res.data?.total || res.total || 0;
      }
    } catch (error) {
      console.error('获取导出列表失败:', error);
      data.value = [];
      total.value = 0;
    } finally {
      state.loading = false;
    }
  }
}

const page = ref(1);
const pageSize = ref(18);
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

function pageSizeChange(_current: number, size: number) {
  pageSize.value = size;
  fetch();
}

function getStatusColor(status: string) {
  const statusMap: Record<string, string> = {
    'PENDING': '#8c8c8c',
    'PROCESSING': '#1890ff',
    'COMPLETED': '#52c41a',
    'FAILED': '#ff4d4f',
  };
  return statusMap[status] || '#d9d9d9';
}

function getStatusText(status: string) {
  const statusMap: Record<string, string> = {
    'PENDING': '等待中',
    'PROCESSING': '处理中',
    'COMPLETED': '已完成',
    'FAILED': '失败',
  };
  return statusMap[status] || '未知';
}

function formatDate(dateString: string) {
  if (!dateString) return '--';
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN');
  } catch (e) {
    return dateString;
  }
}

function handleDelete(record: object) {
  emit('delete', record);
}

function handleDownload(record: object) {
  emit('download', record);
}
</script>

<style lang="less" scoped>
.export-card-list-wrapper {
  :deep(.ant-list-header) {
    border: 0;
  }

  :deep(.ant-list) {
    padding: 6px;
  }

  :deep(.ant-list-item) {
    margin: 6px;
    padding: 0 !important;
  }
}

.export-list-item {
  padding: 0 !important;
  height: 100%;
  display: flex;
}

.export-card-box {
  background: #FFFFFF;
  box-shadow: 0px 0px 4px 0px rgba(24, 24, 24, 0.1);
  height: 100%;
  width: 100%;
  transition: all 0.3s;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 300px;
}

.export-card-cont {
  padding: 15px;
  display: flex;
  flex-direction: column;
  height: 100%;
  flex: 1;
}

.export-format-container {
  width: 100%;
  padding-bottom: 60%;
  overflow: hidden;
  margin-bottom: 12px;
  border-radius: 4px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  position: relative;
}

.format-icon {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 24px;
  font-weight: 600;
  color: #fff;
  
  &.format-onnx {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  }
  
  &.format-openvino {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  }
}

.export-card-title {
  font-size: 18px;
  font-weight: 600;
  line-height: 1.36em;
  color: #181818;
  margin-bottom: 12px;
  flex-shrink: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;

  a {
    display: block;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.export-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
  flex-shrink: 0;
  align-items: center;
}

.export-info {
  font-size: 14px;
  color: #8c8c8c;
  line-height: 1.5;
  margin-bottom: 12px;
  flex: 1;
  min-height: 60px;
  
  .info-item {
    display: flex;
    margin-bottom: 8px;
    
    .info-label {
      min-width: 50px;
      font-weight: 500;
    }
    
    .info-value {
      flex: 1;
      word-break: break-word;
    }
  }
}

.btns {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 15px;
  flex-shrink: 0;
  margin-top: auto;
}

.btn-group {
  display: flex;
  gap: 8px;
}

.btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.3s;

  &:hover:not(.disabled) {
    background: #e6f7ff;
    color: #1890ff;
  }
  
  &.disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .anticon {
    color: #266CFB;
    font-size: 16px;
  }
}

:deep(.ant-tag) {
  border-radius: 4px;
  font-size: 12px;
  padding: 0 8px;
  height: 24px;
  line-height: 22px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex-shrink: 1;
  max-width: 100%;
}
</style>

