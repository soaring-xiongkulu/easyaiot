<template>
  <div class="llm-card-list-wrapper">
    <div class="p-4 bg-white" style="margin-bottom: 10px">
      <BasicForm @register="registerForm" @reset="handleSubmit" @field-value-change="handleFieldValueChange"/>
    </div>
    <div class="bg-white">
      <Spin :spinning="state.loading">
        <List
          :grid="{ gutter: 12, xs: 1, sm: 2, md: 3, lg: 4, xl: 4, xxl: 4 }"
          :data-source="data"
          :pagination="paginationProp"
        >
          <template #header>
            <div
              style="display: flex;align-items: center;justify-content: space-between;flex-direction: row;">
              <span style="padding-left: 7px;font-size: 16px;font-weight: 500;line-height: 24px;">大模型列表</span>
              <div class="space-x-2">
                <slot name="header"></slot>
              </div>
            </div>
          </template>
          <template #renderItem="{ item }">
            <ListItem :class="getItemClass(item)">
              <div class="model-info">
                <div class="status">{{ getStatusDisplayText(item) }}</div>
                <div class="title o2">{{ item.name }}</div>
                <div class="props">
                  <div class="flex" style="justify-content: space-between;">
                    <div class="prop">
                      <div class="label">服务类型</div>
                      <div class="value">{{ getServiceTypeText(item.service_type) }}</div>
                    </div>
                    <div class="prop">
                      <div class="label">供应商</div>
                      <div class="value">{{ getVendorText(item.vendor) }}</div>
                    </div>
                  </div>
                  <div class="flex" style="justify-content: space-between;">
                    <div class="prop">
                      <div class="label">模型类型</div>
                      <div class="value">{{ getModelTypeText(item.model_type) }}</div>
                    </div>
                    <div class="prop">
                      <div class="label">模型标识</div>
                      <div class="value">{{ item.model_name }}</div>
                    </div>
                  </div>
                </div>
                <div class="btns">
                  <div class="btn" @click="handleView(item)">
                    <Icon icon="ant-design:eye-filled" :size="15" color="#3B82F6" />
                  </div>
                  <div class="btn" @click="handleEdit(item)">
                    <Icon icon="ant-design:edit-filled" :size="15" color="#3B82F6" />
                  </div>
                  <div v-if="item.is_active" class="btn" @click="handleDeactivate(item)">
                    <Icon icon="ant-design:pause-circle-outlined" :size="15" color="#3B82F6" />
                  </div>
                  <div v-else class="btn" @click="handleActivate(item)">
                    <Icon icon="ant-design:play-circle-outlined" :size="15" color="#3B82F6" />
                  </div>
                  <Popconfirm
                    title="是否确认删除？"
                    ok-text="是"
                    cancel-text="否"
                    @confirm="handleDelete(item)"
                  >
                    <div class="btn delete-btn">
                      <Icon icon="material-symbols:delete-outline-rounded" :size="15" color="#DC2626" />
                    </div>
                  </Popconfirm>
                </div>
              </div>
              <div class="model-img">
                <img
                  :src="getModelImage(item)"
                  alt="" 
                  class="img" 
                  @click="handleView(item)">
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
import {List, Popconfirm, Spin} from 'ant-design-vue';
import {BasicForm, useForm} from '@/components/Form';
import {propTypes} from '@/utils/propTypes';
import {isFunction} from '@/utils/is';
import {Icon} from '@/components/Icon';
import AI_TASK_IMAGE from '@/assets/images/video/ai-task.png';

defineOptions({name: 'LLMManageCardList'})

const ListItem = List.Item;

const props = defineProps({
  params: propTypes.object.def({}),
  api: propTypes.func,
});

const emit = defineEmits(['getMethod', 'delete', 'view', 'edit', 'activate', 'deactivate', 'field-value-change']);

const data = ref([]);
const state = reactive({
  loading: true,
});

const [registerForm, {validate, updateSchema}] = useForm({
  schemas: [
    {
      field: `name`,
      label: `模型名称`,
      component: 'Input',
      componentProps: {
        placeholder: '请输入模型名称',
        allowClear: true,
      },
    },
    {
      field: `vendor`,
      label: `供应商`,
      component: 'Select',
      componentProps: {
        placeholder: '请选择供应商',
        allowClear: true,
        options: [
          {label: '全部', value: ''},
          {label: '阿里云', value: 'aliyun'},
          {label: 'OpenAI', value: 'openai'},
          {label: 'Anthropic', value: 'anthropic'},
          {label: '本地服务', value: 'local'},
        ],
      },
    },
    {
      field: `model_type`,
      label: `模型类型`,
      component: 'Select',
      componentProps: {
        placeholder: '请选择模型类型',
        allowClear: true,
        options: [
          {label: '全部', value: ''},
          {label: '文本', value: 'text'},
          {label: '视觉', value: 'vision'},
          {label: '多模态', value: 'multimodal'},
        ],
      },
    },
  ],
  labelWidth: 80,
  baseColProps: {span: 6},
  actionColOptions: {span: 6}, // 让按钮在第一行显示
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
      console.error('获取大模型列表失败:', error);
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

// 获取供应商文本
function getVendorText(vendor: string) {
  const vendorMap: Record<string, string> = {
    aliyun: '阿里云',
    openai: 'OpenAI',
    anthropic: 'Anthropic',
    local: '本地服务',
  };
  return vendorMap[vendor] || vendor || '--';
}

// 获取模型类型文本
function getModelTypeText(modelType: string) {
  const typeMap: Record<string, string> = {
    text: '文本',
    vision: '视觉',
    multimodal: '多模态',
  };
  return typeMap[modelType] || modelType || '--';
}

// 获取服务类型文本
function getServiceTypeText(serviceType?: string) {
  const serviceTypeMap: Record<string, string> = {
    online: '线上服务',
    local: '本地服务',
  };
  return serviceTypeMap[serviceType || 'online'] || '线上服务';
}

// 获取卡片类名（只基于is_active判断）
function getItemClass(item: any) {
  // 只根据is_active判断，不再使用status字段
  return item.is_active ? 'model-item normal' : 'model-item error';
}

// 获取状态显示文本（只基于is_active判断）
function getStatusDisplayText(item: any) {
  // 只根据is_active判断，不再使用status字段
  return item.is_active ? '已激活' : '未激活';
}

// 根据模型类型获取图片
function getModelImage(item: any) {
  // 如果模型有上传的图标URL，优先使用
  if (item.icon_url) {
    return item.icon_url;
  }
  // 否则使用默认图片
  return AI_TASK_IMAGE;
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

function handleActivate(record: object) {
  emit('activate', record);
}

function handleDeactivate(record: object) {
  emit('deactivate', record);
}
</script>

<style lang="less" scoped>
.llm-card-list-wrapper {
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
  :deep(.model-item) {
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

      .model-info .status {
        background: #d9dffd;
        color: #266CFBFF;
      }
    }

    &.error {
      background-image: url('@/assets/images/product/red-bg.101af5ac.png');

      .model-info .status {
        background: #fad7d9;
        color: #d43030;
      }
    }

    .model-info {
      flex-direction: column;
      max-width: calc(100% - 128px);
      padding-left: 16px;

      .status {
        min-width: 90px;
        height: 25px;
        border-radius: 6px 0 0 6px;
        font-size: 12px;
        font-weight: 500;
        line-height: 25px;
        text-align: center;
        position: absolute;
        right: 0;
        top: 16px;
        padding: 0 8px;
        white-space: nowrap;
      }

      .title {
        font-size: 16px;
        font-weight: 600;
        color: #050708;
        line-height: 20px;
        height: 40px;
        padding-right: 90px;
        overflow: hidden;
        text-overflow: ellipsis;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;

        &.o2 {
          -webkit-line-clamp: 2;
        }
      }

      .props {
        margin-top: 10px;

        .flex {
          display: flex;
        }

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
        width: 220px;
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
            color: #3B82F6;
            transition: color 0.3s;
          }

          &:hover :deep(.anticon) {
            color: #5BA3F5;
          }

          &.disabled {
            cursor: not-allowed;
            opacity: 0.4;

            :deep(.anticon) {
              color: #ccc;
            }

            &:hover :deep(.anticon) {
              color: #ccc;
            }
          }

          &.delete-btn {
            :deep(.anticon) {
              color: #DC2626;
            }

            &:hover :deep(.anticon) {
              color: #DC2626;
            }
          }
        }
      }
    }

    .model-img {
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
