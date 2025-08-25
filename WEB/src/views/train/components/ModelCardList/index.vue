<template>
  <div class="model-card-list-wrapper p-2">
    <div class="p-4 bg-white" style="margin-bottom: 10px">
      <BasicForm @register="registerForm" @reset="handleSubmit"/>
    </div>
    <div class="p-2 bg-white">
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
            <ListItem
              style="padding: 0; background: #FFFFFF; box-shadow: 0px 0px 4px 0px rgba(24, 24, 24, 0.1); height: 100%; transition: all 0.3s;">
              <div class="model-card-box">
                <div class="model-card-cont" style="padding: 15px">
                  <div class="model-image-container">
                    <img
                      :src="item.imageUrl"
                      alt="模型图片"
                      class="model-image"
                      @error="handleImageError"
                    />
                  </div>

                  <h6 class="model-card-title">
                    <a>{{ item.name }}</a>
                  </h6>

                  <div class="model-meta">
                    <div class="model-meta-item">
                      <span class="meta-label">ID:</span>
                      <span>{{ item.id }}</span>
                    </div>
                    <div class="model-meta-item">
                      <span class="meta-label">状态:</span>
                      <Tag :color="getStatusColor(item.status)">
                        {{ getStatusText(item.status) }}
                      </Tag>
                    </div>
                    <div class="model-meta-item">
                      <span class="meta-label">创建时间:</span>
                      <span>{{ formatDate(item.created_at) }}</span>
                    </div>
                  </div>

                  <div class="model-description">
                    {{ item.description || '暂无描述' }}
                  </div>

                  <div class="btns"
                       style="padding-top: 15px; display: flex; justify-content: space-between;">
                    <div class="btn-group">
                      <div class="btn" @click="handleView(item)">
                        <EyeOutlined style="font-size: 16px;"/>
                      </div>
                      <div class="btn" @click="handleEdit(item)">
                        <EditOutlined style="font-size: 16px;"/>
                      </div>
                      <div class="btn" @click="handleTrain(item)" title="训练模型">
                        <ExperimentOutlined style="font-size: 16px;"/>
                      </div>
                      <Popconfirm
                        title="是否确认删除？"
                        ok-text="是"
                        cancel-text="否"
                        @confirm="handleDelete(item)"
                      >
                        <div class="btn">
                          <DeleteOutlined style="font-size: 16px;"/>
                        </div>
                      </Popconfirm>
                    </div>
                    <div class="btn" @click="handleDeploy(item)" title="部署模型">
                      <CloudUploadOutlined style="font-size: 16px;"/>
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
import {
  CloudUploadOutlined,
  DeleteOutlined,
  EditOutlined,
  ExperimentOutlined,
  EyeOutlined
} from '@ant-design/icons-vue';

defineOptions({name: 'ModelCardList'})

const ListItem = List.Item;

const props = defineProps({
  params: propTypes.object.def({}),
  api: propTypes.func,
});

const emit = defineEmits(['getMethod', 'delete', 'edit', 'view', 'deploy', 'train']);

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
      field: `status`,
      label: `状态`,
      component: 'Select',
      componentProps: {
        options: [
          {label: '未部署', value: 0},
          {label: '已部署', value: 1},
          {label: '训练中', value: 2},
          {label: '已下线', value: 3},
        ],
      },
    },
  ],
  labelWidth: 80,
  baseColProps: {span: 6},
  actionColOptions: {span: 18},
  autoSubmitOnEnter: true,
  submitFunc: handleSubmit,
});

onMounted(() => {
  fetch();
  emit('getMethod', fetch);
});

async function handleSubmit() {
  const data = await validate();
  await fetch(data);
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

function pageSizeChange(_current, size: number) {
  pageSize.value = size;
  fetch();
}

function getStatusColor(status: number) {
  switch (status) {
    case 0:
      return '#8c8c8c'; // 未部署
    case 1:
      return '#52c41a'; // 已部署
    case 2:
      return '#fa8c16'; // 训练中
    case 3:
      return '#ff4d4f'; // 已下线
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
  if (!dateString) return '--';
  const date = new Date(dateString);
  return date.toLocaleDateString();
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

function handleTrain(record: object) {
  emit('train', record);
}

// 图片错误处理
function handleImageError(e) {
  e.target.src = 'placeholder.jpg';
}
</script>

<style lang="less" scoped>
.model-card-list-wrapper {
  :deep(.ant-list-header) {
    border: 0;
  }
}

.model-card-box {
  background: #FFFFFF;
  box-shadow: 0px 0px 4px 0px rgba(24, 24, 24, 0.1);
  height: 100%;
  transition: all 0.3s;
  border-radius: 8px;
  overflow: hidden;
}

.model-card-title {
  font-size: 18px;
  font-weight: 600;
  line-height: 1.36em;
  color: #181818;
  margin-bottom: 12px;
}

.model-meta {
  margin-bottom: 12px;

  .model-meta-item {
    display: flex;
    margin-bottom: 6px;
    font-size: 13px;
    color: #595959;

    .meta-label {
      font-weight: 500;
      margin-right: 6px;
      min-width: 60px;
    }
  }
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
}

.btns {
  display: flex;
  justify-content: space-between;
  align-items: center;

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

    &:hover {
      background: #e6f7ff;
      color: #1890ff;
    }
  }
}

/* 新增图片容器样式 */
.model-image-container {
  height: 180px;
  overflow: hidden;
  margin-bottom: 12px;
  border-radius: 4px;
  background-color: #f5f5f5;
  display: flex;
  align-items: center;
  justify-content: center;
}

.model-image {
  max-height: 100%;
  max-width: 100%;
  object-fit: contain;
}
</style>
