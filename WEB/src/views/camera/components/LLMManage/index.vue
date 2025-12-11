<template>
  <div id="llm-manage">
    <!-- 表格模式 -->
    <BasicTable v-if="viewMode === 'table'" @register="registerTable">
      <template #toolbar>
        <div class="toolbar-buttons">
          <a-button type="primary" @click="handleCreate">
            <template #icon>
              <PlusOutlined />
            </template>
            新建大模型
          </a-button>
          <a-button type="default" @click="handleVisionInference">
            <template #icon>
              <Icon icon="ant-design:eye-outlined" />
            </template>
            视觉推理
          </a-button>
          <a-button type="default" @click="handleVideoInference">
            <template #icon>
              <Icon icon="ant-design:video-camera-outlined" />
            </template>
            视频推理
          </a-button>
          <a-button @click="handleToggleViewMode" type="default">
            <template #icon>
              <SwapOutlined />
            </template>
            切换视图
          </a-button>
        </div>
      </template>
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'status'">
          <a-tag :color="getStatusColor(record.status)">
            {{ getStatusText(record.status) }}
          </a-tag>
        </template>
        <template v-else-if="column.dataIndex === 'is_active'">
          <a-tag :color="record.is_active ? 'green' : 'default'">
            {{ record.is_active ? '已激活' : '未激活' }}
          </a-tag>
        </template>
        <template v-else-if="column.dataIndex === 'action'">
          <TableAction :actions="getTableActions(record)" />
        </template>
      </template>
    </BasicTable>

    <!-- 卡片模式 -->
    <div v-else class="llm-manage-card-list-wrapper p-2">
      <div class="p-4 bg-white" style="margin-bottom: 10px">
        <BasicForm @register="registerForm" @reset="handleSubmit" />
      </div>
      <div class="p-2 bg-white">
        <Spin :spinning="loading">
          <List
            :grid="{ gutter: 12, xs: 1, sm: 2, md: 3, lg: 4, xl: 4, xxl: 4 }"
            :data-source="modelList"
            :pagination="paginationProp"
          >
            <template #header>
              <div style="display: flex; align-items: center; justify-content: space-between; flex-direction: row;">
                <span style="padding-left: 7px; font-size: 16px; font-weight: 500; line-height: 24px;">大模型列表</span>
                <div style="display: flex; gap: 8px;">
                  <a-button type="primary" @click="handleCreate">
                    <template #icon>
                      <PlusOutlined />
                    </template>
                    新建大模型
                  </a-button>
                  <a-button type="default" @click="handleVisionInference">
                    <template #icon>
                      <Icon icon="ant-design:eye-outlined" />
                    </template>
                    视觉推理
                  </a-button>
                  <a-button type="default" @click="handleVideoInference">
                    <template #icon>
                      <Icon icon="ant-design:video-camera-outlined" />
                    </template>
                    视频推理
                  </a-button>
                  <a-button @click="handleToggleViewMode" type="default">
                    <template #icon>
                      <SwapOutlined />
                    </template>
                    切换视图
                  </a-button>
                </div>
              </div>
            </template>
            <template #renderItem="{ item }">
              <ListItem :class="item.is_active ? 'model-item active' : 'model-item'">
                <div class="model-info">
                  <div class="status-badge">
                    <a-tag :color="getStatusColor(item.status)" size="small">
                      {{ getStatusText(item.status) }}
                    </a-tag>
                    <a-tag v-if="item.is_active" color="green" size="small">已激活</a-tag>
                  </div>
                  <div class="title">{{ item.name }}</div>
                  <div class="props">
                    <div class="prop">
                      <div class="label">服务类型</div>
                      <div class="value">{{ getServiceTypeText(item.service_type) }}</div>
                    </div>
                    <div class="prop">
                      <div class="label">供应商</div>
                      <div class="value">{{ getVendorText(item.vendor) }}</div>
                    </div>
                    <div class="prop">
                      <div class="label">模型类型</div>
                      <div class="value">{{ getModelTypeText(item.model_type) }}</div>
                    </div>
                    <div class="prop">
                      <div class="label">模型标识</div>
                      <div class="value">{{ item.model_name }}</div>
                    </div>
                  </div>
                  <div class="btns">
                    <div class="btn" @click="handleView(item)">
                      <Icon icon="ant-design:eye-filled" :size="15" color="#3B82F6" />
                    </div>
                    <div class="btn" @click="handleEdit(item)">
                      <Icon icon="ant-design:edit-filled" :size="15" color="#10B981" />
                    </div>
                    <div class="btn" @click="handleTest(item)">
                      <Icon icon="ant-design:thunderbolt-filled" :size="15" color="#F59E0B" />
                    </div>
                    <div class="btn" @click="handleDelete(item)">
                      <Icon icon="material-symbols:delete-outline-rounded" :size="15" color="#EF4444" />
                    </div>
                    <div v-if="!item.is_active" class="btn" @click="handleActivate(item)">
                      <Icon icon="ant-design:check-circle-filled" :size="15" color="#10B981" />
                    </div>
                  </div>
                </div>
              </ListItem>
            </template>
          </List>
        </Spin>
      </div>
    </div>

    <!-- 大模型配置模态框 -->
    <LLMModal @register="registerModal" @success="handleSuccess" />
    
    <!-- 视觉推理模态框 -->
    <VisionInferenceModal @register="registerVisionModal" />
    
    <!-- 视频推理模态框 -->
    <VideoInferenceModal @register="registerVideoModal" />
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted } from 'vue';
import { BasicTable, TableAction, useTable } from '@/components/Table';
import { BasicForm, useForm } from '@/components/Form';
import { useModal } from '@/components/Modal';
import { List, ListItem, Spin } from 'ant-design-vue';
import { PlusOutlined, SwapOutlined } from '@ant-design/icons-vue';
import { Icon } from '@/components/Icon';
import { useMessage } from '@/hooks/web/useMessage';
import { getBasicColumns, getFormConfig } from './Data';
import { getLLMList, deleteLLM, activateLLM, testLLM, type LLMModel } from '@/api/device/llm';
import LLMModal from './LLMModal.vue';
import VisionInferenceModal from './VisionInferenceModal.vue';
import VideoInferenceModal from './VideoInferenceModal.vue';

defineOptions({ name: 'LLMManage' });

const { createMessage } = useMessage();
const [registerModal, { openModal }] = useModal();
const [registerVisionModal, { openModal: openVisionModal }] = useModal();
const [registerVideoModal, { openModal: openVideoModal }] = useModal();

// 视图模式
const viewMode = ref<'table' | 'card'>('card');
const loading = ref(false);
const modelList = ref<LLMModel[]>([]);
const paginationProp = reactive({
  current: 1,
  pageSize: 12,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  onChange: (page: number, pageSize: number) => {
    paginationProp.current = page;
    paginationProp.pageSize = pageSize;
    fetchData();
  },
  onShowSizeChange: (current: number, size: number) => {
    paginationProp.current = 1;
    paginationProp.pageSize = size;
    fetchData();
  },
});

// 表格配置
const [registerTable, { reload }] = useTable({
  canResize: true,
  showIndexColumn: false,
  title: '大模型列表',
  api: getLLMList,
  columns: getBasicColumns(),
  useSearchForm: true,
  showTableSetting: false,
  pagination: true,
  formConfig: getFormConfig(),
  fetchSetting: {
    listField: 'data.list',
    totalField: 'data.total',
  },
  rowKey: 'id',
});

// 表单配置（卡片模式搜索）
const [registerForm] = useForm({
  labelWidth: 80,
  baseColProps: { span: 6 },
  schemas: [
    {
      field: 'name',
      label: '模型名称',
      component: 'Input',
      componentProps: {
        placeholder: '请输入模型名称',
      },
    },
    {
      field: 'service_type',
      label: '服务类型',
      component: 'Select',
      componentProps: {
        placeholder: '请选择服务类型',
        options: [
          { label: '全部', value: '' },
          { label: '线上服务', value: 'online' },
          { label: '本地服务', value: 'local' },
        ],
      },
    },
    {
      field: 'vendor',
      label: '供应商',
      component: 'Select',
      componentProps: {
        placeholder: '请选择供应商',
        options: [
          { label: '全部', value: '' },
          { label: '阿里云', value: 'aliyun' },
          { label: 'OpenAI', value: 'openai' },
          { label: 'Anthropic', value: 'anthropic' },
          { label: '本地服务', value: 'local' },
        ],
      },
    },
    {
      field: 'model_type',
      label: '模型类型',
      component: 'Select',
      componentProps: {
        placeholder: '请选择模型类型',
        options: [
          { label: '全部', value: '' },
          { label: '文本', value: 'text' },
          { label: '视觉', value: 'vision' },
          { label: '多模态', value: 'multimodal' },
        ],
      },
    },
  ],
});

// 获取状态文本
const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    active: '正常',
    inactive: '未激活',
    error: '错误',
  };
  return statusMap[status] || status;
};

// 获取状态颜色
const getStatusColor = (status: string) => {
  const colorMap: Record<string, string> = {
    active: 'green',
    inactive: 'default',
    error: 'red',
  };
  return colorMap[status] || 'default';
};

// 获取服务类型文本
const getServiceTypeText = (serviceType?: string) => {
  const serviceTypeMap: Record<string, string> = {
    online: '线上服务',
    local: '本地服务',
  };
  return serviceTypeMap[serviceType || 'online'] || '线上服务';
};

// 获取供应商文本
const getVendorText = (vendor: string) => {
  const vendorMap: Record<string, string> = {
    aliyun: '阿里云',
    openai: 'OpenAI',
    anthropic: 'Anthropic',
    local: '本地服务',
  };
  return vendorMap[vendor] || vendor;
};

// 获取模型类型文本
const getModelTypeText = (modelType: string) => {
  const typeMap: Record<string, string> = {
    text: '文本',
    vision: '视觉',
    multimodal: '多模态',
  };
  return typeMap[modelType] || modelType;
};

// 获取表格操作按钮
const getTableActions = (record: LLMModel) => {
  const actions = [
    {
      icon: 'ant-design:eye-filled',
      tooltip: '查看',
      onClick: () => handleView(record),
    },
    {
      icon: 'ant-design:edit-filled',
      tooltip: '编辑',
      onClick: () => handleEdit(record),
    },
    {
      icon: 'ant-design:thunderbolt-filled',
      tooltip: '测试',
      onClick: () => handleTest(record),
    },
    {
      icon: 'material-symbols:delete-outline-rounded',
      tooltip: '删除',
      popConfirm: {
        title: '确定删除此大模型配置？',
        confirm: () => handleDelete(record),
      },
    },
  ];

  if (!record.is_active) {
    actions.splice(3, 0, {
      icon: 'ant-design:check-circle-filled',
      tooltip: '激活',
      onClick: () => handleActivate(record),
    });
  }

  return actions;
};

// 切换视图模式
const handleToggleViewMode = () => {
  viewMode.value = viewMode.value === 'table' ? 'card' : 'table';
  if (viewMode.value === 'card') {
    fetchData();
  }
};

// 获取数据（卡片模式）
const fetchData = async () => {
  try {
    loading.value = true;
    const formValues = await registerForm.getFieldsValue();
    const response = await getLLMList({
      page: paginationProp.current,
      pageSize: paginationProp.pageSize,
      name: formValues.name,
      service_type: formValues.service_type,
      vendor: formValues.vendor,
      model_type: formValues.model_type,
    });
    if (response.code === 0) {
      modelList.value = response.data.list;
      paginationProp.total = response.data.total;
    }
  } catch (error) {
    console.error('获取大模型列表失败', error);
  } finally {
    loading.value = false;
  }
};

// 表单提交（搜索）
const handleSubmit = () => {
  paginationProp.current = 1;
  fetchData();
};

// 创建
const handleCreate = () => {
  openModal(true, {
    type: 'create',
  });
};

// 查看
const handleView = (record: LLMModel) => {
  openModal(true, {
    type: 'view',
    record,
  });
};

// 编辑
const handleEdit = (record: LLMModel) => {
  openModal(true, {
    type: 'edit',
    record,
  });
};

// 删除
const handleDelete = async (record: LLMModel) => {
  try {
    await deleteLLM(record.id!);
    createMessage.success('删除成功');
    handleSuccess();
  } catch (error) {
    console.error('删除失败', error);
    createMessage.error('删除失败');
  }
};

// 激活
const handleActivate = async (record: LLMModel) => {
  try {
    createMessage.loading({ content: '正在激活...', key: 'activate' });
    const response = await activateLLM(record.id!);
    if (response.code === 0) {
      createMessage.success({ content: '激活成功', key: 'activate' });
      handleSuccess();
    } else {
      createMessage.error({ content: response.msg || '激活失败', key: 'activate' });
    }
  } catch (error) {
    console.error('激活失败', error);
    createMessage.error({ content: '激活失败', key: 'activate' });
  }
};

// 测试
const handleTest = async (record: LLMModel) => {
  try {
    createMessage.loading({ content: '正在测试连接...', key: 'test' });
    const response = await testLLM(record.id!);
    if (response.code === 0) {
      if (response.data.success) {
        createMessage.success({ content: response.data.message || '测试成功', key: 'test' });
      } else {
        createMessage.warning({ content: response.data.message || '测试失败', key: 'test' });
      }
      handleSuccess();
    } else {
      createMessage.error({ content: response.msg || '测试失败', key: 'test' });
    }
  } catch (error) {
    console.error('测试失败', error);
    createMessage.error({ content: '测试失败', key: 'test' });
  }
};

// 视觉推理
const handleVisionInference = () => {
  // 直接打开视觉推理模态框，后端会检查是否有激活的模型
  openVisionModal(true);
};

// 视频推理
const handleVideoInference = () => {
  // 直接打开视频推理模态框，后端会检查是否有激活的模型
  openVideoModal(true);
};

// 成功回调
const handleSuccess = () => {
  if (viewMode.value === 'table') {
    reload();
  } else {
    fetchData();
  }
};

// 刷新方法（供父组件调用）
const refresh = () => {
  handleSuccess();
};

// 暴露给父组件
defineExpose({
  refresh,
});

onMounted(() => {
  if (viewMode.value === 'card') {
    fetchData();
  }
});
</script>

<style lang="less" scoped>
#llm-manage {
  .toolbar-buttons {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .llm-manage-card-list-wrapper {
    .model-item {
      background: #fff;
      border: 1px solid #e5e7eb;
      border-radius: 8px;
      padding: 16px;
      transition: all 0.3s;
      cursor: pointer;

      &:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        border-color: #3b82f6;
      }

      &.active {
        border-color: #10b981;
        background: #f0fdf4;
      }

      .model-info {
        .status-badge {
          display: flex;
          gap: 8px;
          margin-bottom: 12px;
        }

        .title {
          font-size: 16px;
          font-weight: 600;
          color: #111827;
          margin-bottom: 12px;
        }

        .props {
          margin-bottom: 16px;

          .prop {
            margin-bottom: 8px;

            .label {
              font-size: 12px;
              color: #6b7280;
              margin-bottom: 4px;
            }

            .value {
              font-size: 14px;
              color: #111827;
              word-break: break-all;
            }
          }
        }

        .btns {
          display: flex;
          gap: 8px;
          justify-content: flex-end;
          padding-top: 12px;
          border-top: 1px solid #e5e7eb;

          .btn {
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.2s;

            &:hover {
              background: #f3f4f6;
            }
          }
        }
      }
    }
  }
}
</style>
