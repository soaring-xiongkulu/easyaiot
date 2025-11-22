<template>
  <div class="model-card-list-wrapper">
    <div class="p-4 bg-white" style="margin-bottom: 10px">
      <BasicForm @register="registerForm" @reset="handleSubmit"/>
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
              <span style="padding-left: 7px;font-size: 16px;font-weight: 500;line-height: 24px;">模型列表</span>
              <div class="space-x-2">
                <slot name="header"></slot>
              </div>
            </div>
          </template>
          <template #renderItem="{ item }">
            <ListItem class="model-list-item">
              <div class="model-card-box">
                <div class="model-card-cont">
                  <!-- 正方形图片容器 -->
                  <div class="model-image-container" @click="handleView(item)">
                    <img
                      :src="item.imageUrl"
                      alt="模型图片"
                      class="model-image"
                    />
                    <!-- 图片上的小卡片 -->
                    <div class="image-badges">
                      <div class="badge badge-format" v-if="getFormatText(item)">
                        {{ getFormatText(item) }}
                      </div>
                      <div class="badge badge-version" v-if="item.version">
                        v{{ item.version }}
                      </div>
                    </div>
                  </div>

                  <h6 class="model-card-title">
                    <a>{{ item.name }}</a>
                  </h6>

                  <!-- 标签区域 -->
                  <div class="model-tags">
                    <Tag color="#1890ff">ID: {{ item.id }}</Tag>
                    <Tag color="#52c41a">版本: {{ item.version || '未指定' }}</Tag>
                    <Tag color="#8c8c8c">{{ formatDate(item.created_at) }}</Tag>
                  </div>

                  <div class="model-description">
                    {{ item.description || '暂无描述' }}
                  </div>

                  <div class="btns">
                    <div class="btn-group">
                      <div class="btn" @click="handleView(item)" title="查看详情">
                        <EyeOutlined style="font-size: 16px;"/>
                      </div>
                      <div class="btn" @click="handleEdit(item)" title="编辑模型">
                        <EditOutlined style="font-size: 16px;"/>
                      </div>
                      <div class="btn" @click="handleDeploy(item)" title="部署模型">
                        <ExperimentOutlined style="font-size: 16px;"/>
                      </div>
                      <div class="btn" @click="handleDownload(item)" title="下载模型">
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
import {onMounted, reactive, ref} from 'vue';
import {List, Popconfirm, Spin, Tag} from 'ant-design-vue';
import {BasicForm, useForm} from '@/components/Form';
import {propTypes} from '@/utils/propTypes';
import {isFunction} from '@/utils/is';
import {DeleteOutlined, DownloadOutlined, EditOutlined, ExperimentOutlined, EyeOutlined} from '@ant-design/icons-vue';

defineOptions({name: 'ModelCardList'})

const ListItem = List.Item;

const props = defineProps({
  params: propTypes.object.def({}),
  api: propTypes.func,
});

const emit = defineEmits(['getMethod', 'delete', 'edit', 'view', 'deploy', 'train', 'download']);

const data = ref([]);
const state = reactive({
  loading: true,
});

const [registerForm, {validate}] = useForm({
  schemas: [
    {
      field: `name`,
      label: `模型名称`,
      component: 'Input',
    },
    {
      field: `version`,
      label: `模型版本`,
      component: 'Input',
    },
  ],
  labelWidth: 80,
  baseColProps: {span: 6},
  actionColOptions: {span: 12},
  autoSubmitOnEnter: true,
  submitFunc: handleSubmit,
});

onMounted(() => {
  fetch();
  emit('getMethod', fetch);
});

async function handleSubmit() {
  const formData = await validate();
  await fetch(formData);
}

async function fetch(p = {}) {
  const {api, params} = props;
  if (api && isFunction(api)) {
    const res = await api({...params, pageNo: page.value, pageSize: pageSize.value, ...p});
    data.value = res.data;
    total.value = res.total;
    hideLoading();
  }
}

function hideLoading() {
  state.loading = false;
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

function getStatusColor(status: number) {
  switch (status) {
    case 0:
      return '#8c8c8c';
    case 1:
      return '#52c41a';
    case 2:
      return '#fa8c16';
    case 3:
      return '#ff4d4f';
    default:
      return '#d9d9d9';
  }
}

function getStatusText(status: number) {
  switch (status) {
    case 0:
      return '未部署';
    case 1:
      return '已部署';
    case 2:
      return '训练中';
    case 3:
      return '已下线';
    default:
      return '未知';
  }
}

function formatDate(dateString: string) {
  return dateString ? new Date(dateString).toLocaleDateString() : '--';
}

function getFormatText(item: any): string {
  // 根据模型路径判断格式
  if (item.onnx_model_path) {
    return 'ONNX';
  }
  if (item.model_path) {
    const path = item.model_path.toLowerCase();
    if (path.endsWith('.onnx')) {
      return 'ONNX';
    }
    if (path.endsWith('.pt') || path.endsWith('.pth')) {
      return 'PyTorch';
    }
    if (path.includes('openvino')) {
      return 'OpenVINO';
    }
    if (path.endsWith('.tflite')) {
      return 'TensorFlow Lite';
    }
    // 默认返回 PyTorch（因为大多数模型是 PyTorch 格式）
    return 'PyTorch';
  }
  // 如果没有路径信息，返回空字符串
  return '';
}

function handleDelete(record: object) {
  emit('delete', record);
}

function handleView(record: object) {
  emit('view', record);
}

function handleEdit(record: object) {
  emit('edit', record);
}

function handleDeploy(record: object) {
  emit('deploy', record);
}

function handleDownload(record: object) {
  emit('download', record);
}
</script>

<style lang="less" scoped>
.model-card-list-wrapper {
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

// 列表项样式
.model-list-item {
  padding: 0 !important;
  height: 100%;
  display: flex;
}

.model-card-box {
  background: #FFFFFF;
  box-shadow: 0px 0px 4px 0px rgba(24, 24, 24, 0.1);
  height: 100%;
  width: 100%;
  transition: all 0.3s;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 400px;
}

.model-card-cont {
  padding: 15px;
  display: flex;
  flex-direction: column;
  height: 100%;
  flex: 1;
}

.model-card-title {
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

.model-tags {
  display: flex;
  flex-wrap: nowrap;
  gap: 6px;
  margin-bottom: 12px;
  flex-shrink: 0;
  overflow: hidden;
  height: 24px;
  align-items: center;
}

.model-description {
  font-size: 14px;
  color: #8c8c8c;
  line-height: 1.5;
  margin-bottom: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  flex: 1;
  min-height: 63px; // 确保至少3行的高度
}

/* 优化后的按钮区域 */
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
  gap: 8px; /* 统一按钮间距 */
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

  &:hover {
    background: #e6f7ff;
    color: #1890ff;
  }

  .anticon {
    color: #266CFB; /* 蓝色图标 */
    font-size: 16px;
  }
}

/* 图片容器 */
.model-image-container {
  position: relative;
  width: 100%;
  padding-bottom: 100%;
  overflow: hidden;
  margin-bottom: 12px;
  border-radius: 4px;
  background-color: #f5f5f5;
  cursor: pointer;
  flex-shrink: 0;
}

.model-image {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* 图片上的小卡片 */
.image-badges {
  position: absolute;
  top: 8px;
  left: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  z-index: 10;
}

.badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  line-height: 1.2;
  white-space: nowrap;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(4px);
  color: #fff;
  
  &.badge-format {
    background: rgba(24, 144, 255, 0.85);
  }
  
  &.badge-version {
    background: rgba(82, 196, 26, 0.85);
  }
}

/* 标签样式 */
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
