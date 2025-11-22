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
                  <div class="export-format-container" :class="`format-${item.format}`">
                    <div class="format-icon">
                      {{ item.format === 'onnx' ? 'ONNX' : 'OpenVINO' }}
                    </div>
                  </div>

                  <h6 class="export-card-title">
                    <a>
                      {{ item.model_name || `模型${item.model_id}` }}{{ item.model_version ? `（v${item.model_version}）` : '' }}
                    </a>
                  </h6>

                  <!-- 标签区域 -->
                  <div class="export-tags">
                    <Tag class="model-id-tag">模型ID: {{ item.model_id }}</Tag>
                    <Tag :class="`status-tag status-${item.status?.toLowerCase()}`">{{ getStatusText(item.status) }}</Tag>
                  </div>

                  <div class="export-info">
                    <div class="info-item">
                      <span class="info-label">导出时间:</span>
                      <span class="info-value">{{ formatDateTime(item.created_at) }}</span>
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
    'PENDING': '#6b7280',
    'PROCESSING': '#3b82f6',
    'COMPLETED': '#10b981',
    'FAILED': '#ef4444',
  };
  return statusMap[status] || '#9ca3af';
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

function formatDateTime(dateString: string) {
  if (!dateString) return '--';
  try {
    // 解析ISO格式时间字符串（可能包含时区信息）
    const date = new Date(dateString);
    // 检查日期是否有效
    if (isNaN(date.getTime())) {
      return dateString;
    }
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
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
    padding: 16px 20px;
    background: transparent;
  }

  :deep(.ant-list) {
    padding: 8px;
  }

  :deep(.ant-list-item) {
    margin: 8px;
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
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.06);
  height: 100%;
  width: 100%;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 260px;
  border: 1px solid rgba(0, 0, 0, 0.06);

  &:hover {
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12), 0 2px 4px rgba(0, 0, 0, 0.08);
    transform: translateY(-2px);
    border-color: rgba(0, 0, 0, 0.1);
  }
}

.export-card-cont {
  padding: 16px;
  display: flex;
  flex-direction: column;
  height: 100%;
  flex: 1;
}

.export-format-container {
  width: 100%;
  padding-bottom: 35%;
  overflow: hidden;
  margin-bottom: 12px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  position: relative;
  border: 1px solid rgba(0, 0, 0, 0.08);
  
  &.format-onnx {
    // ONNX 专业配色：深灰蓝系
    background: linear-gradient(135deg, #2c3e50 0%, #34495e 50%, #2c3e50 100%);
  }
  
  &.format-openvino {
    // OpenVINO 专业配色：深灰紫系
    background: linear-gradient(135deg, #3d3d3d 0%, #4a4a4a 50%, #3d3d3d 100%);
  }
}

.format-icon {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 14px;
  font-weight: 600;
  color: #e8e8e8;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.export-card-title {
  font-size: 15px;
  font-weight: 600;
  line-height: 1.4em;
  color: #1a1a1a;
  margin-bottom: 10px;
  flex-shrink: 0;
  min-height: 36px;
  display: flex;
  align-items: flex-start;

  a {
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
    color: #1a1a1a;
    transition: color 0.2s;
    word-break: break-word;
    line-height: 1.5em;
    max-height: 3em;
    overflow: hidden;

    &:hover {
      color: #1890ff;
    }
  }
}

.export-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
  flex-shrink: 0;
  align-items: center;
}

.export-info {
  font-size: 13px;
  color: #595959;
  line-height: 1.5;
  margin-bottom: 10px;
  flex: 1;
  min-height: 40px;
  
  .info-item {
    display: flex;
    margin-bottom: 8px;
    
    .info-label {
      min-width: 52px;
      font-weight: 500;
      color: #8c8c8c;
    }
    
    .info-value {
      flex: 1;
      word-break: break-word;
      color: #262626;
      font-weight: 400;
    }
  }
}

.btns {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  flex-shrink: 0;
  margin-top: auto;
  border-top: 1px solid #f0f0f0;
}

.btn-group {
  display: flex;
  gap: 10px;
}

.btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fafafa;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid #e8e8e8;

  &:hover:not(.disabled) {
    background: #262626;
    border-color: #262626;
    transform: translateY(-1px);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.12);
    
    .anticon {
      color: #fff;
    }
  }
  
  &.disabled {
    opacity: 0.4;
    cursor: not-allowed;
    background: #f5f5f5;
  }

  .anticon {
    color: #8c8c8c;
    font-size: 16px;
    transition: color 0.25s;
  }
}

:deep(.ant-tag) {
  border-radius: 6px;
  font-size: 12px;
  padding: 2px 10px;
  height: 26px;
  line-height: 22px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex-shrink: 1;
  max-width: 100%;
  border: none;
  font-weight: 500;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.model-id-tag {
  background: #f5f5f5;
  color: #595959;
  border: 1px solid #e8e8e8;
}

.date-tag {
  background: #f3f4f6;
  color: #6b7280;
  border: 1px solid #e5e7eb;
}

.status-tag {
  font-weight: 500;
  
  &.status-pending {
    background: #f5f5f5;
    color: #8c8c8c;
    border: 1px solid #e8e8e8;
  }
  
  &.status-processing {
    background: #e6f7ff;
    color: #1890ff;
    border: 1px solid #91d5ff;
  }
  
  &.status-completed {
    background: #f6ffed;
    color: #52c41a;
    border: 1px solid #b7eb8f;
  }
  
  &.status-failed {
    background: #fff2f0;
    color: #ff4d4f;
    border: 1px solid #ffccc7;
  }
}
</style>

