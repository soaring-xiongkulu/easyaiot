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
        <BasicForm @register="registerForm" @submit="handleSubmit" @reset="handleSubmit" />
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
                    <div class="btn" @click="handleTest(item)">
                      <Icon icon="ant-design:thunderbolt-filled" :size="15" color="#3B82F6" />
                    </div>
                    <div v-if="item.is_active" class="btn" @click="handleDeactivate(item)">
                      <Icon icon="ant-design:pause-circle-filled" :size="15" color="#3B82F6" />
                    </div>
                    <div v-else class="btn" @click="handleActivate(item)">
                      <Icon icon="ant-design:play-circle-filled" :size="15" color="#3B82F6" />
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
import { List, ListItem, Spin, Popconfirm } from 'ant-design-vue';
import { PlusOutlined, SwapOutlined } from '@ant-design/icons-vue';
import { Icon } from '@/components/Icon';
import AI_TASK_IMAGE from '@/assets/images/video/ai-task.png';
import { useMessage } from '@/hooks/web/useMessage';
import { getBasicColumns, getFormConfig } from './Data';
import { getLLMList, deleteLLM, activateLLM, deactivateLLM, testLLM, type LLMModel } from '@/api/device/llm';
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
const [registerForm, { getFieldsValue }] = useForm({
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

// 获取卡片类名
const getItemClass = (item: LLMModel) => {
  // 如果已激活且状态为 active，使用 normal 样式
  // 否则使用 error 样式
  if (item.is_active && item.status === 'active') {
    return 'model-item normal';
  }
  return 'model-item error';
};

// 获取状态显示文本
const getStatusDisplayText = (item: LLMModel) => {
  if (item.is_active && item.status === 'active') {
    return '已激活';
  }
  if (item.status === 'error') {
    return '错误';
  }
  return '未激活';
};

// 根据模型类型获取图片
const getModelImage = (item: LLMModel) => {
  // 如果模型有上传的图标URL，优先使用
  if (item.icon_url) {
    return item.icon_url;
  }
  // 否则使用默认图片
  return AI_TASK_IMAGE;
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
  ];

  if (record.is_active) {
    actions.push({
      icon: 'ant-design:pause-circle-filled',
      tooltip: '禁用',
      onClick: () => handleDeactivate(record),
    });
  } else {
    actions.push({
      icon: 'ant-design:play-circle-filled',
      tooltip: '激活',
      onClick: () => handleActivate(record),
    });
  }

  actions.push({
    icon: 'material-symbols:delete-outline-rounded',
    tooltip: '删除',
    popConfirm: {
      title: '确定删除此大模型配置？',
      confirm: () => handleDelete(record),
    },
  });

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
    const formValues = await getFieldsValue();
    const response = await getLLMList({
      page: paginationProp.current,
      pageSize: paginationProp.pageSize,
      name: formValues.name,
      service_type: formValues.service_type,
      vendor: formValues.vendor,
      model_type: formValues.model_type,
    });
    // HTTP 转换器可能返回两种格式：
    // 1. { code: 0, data: { list: [], total: 0 }, msg: 'success' }
    // 2. { list: [], total: 0 } (转换器自动解包了 data.data，当 total 在 data.data.total 中时)
    if (response && typeof response === 'object') {
      if ('code' in response && response.code === 0 && response.data) {
        // 标准格式：包含 code 和 data
        modelList.value = response.data.list || [];
        paginationProp.total = response.data.total || 0;
      } else if ('list' in response && Array.isArray(response.list)) {
        // 转换器已解包的格式：直接包含 list 和 total
        modelList.value = response.list;
        paginationProp.total = response.total || 0;
      } else {
        // 兜底处理
        modelList.value = [];
        paginationProp.total = 0;
      }
    } else {
      modelList.value = [];
      paginationProp.total = 0;
    }
  } catch (error) {
    console.error('获取大模型列表失败', error);
    modelList.value = [];
    paginationProp.total = 0;
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
    // 检查响应格式：如果响应转换器已经处理过，可能只返回 data，也可能返回完整对象
    if (response && typeof response === 'object' && 'code' in response) {
      if (response.code === 0) {
        createMessage.success({ content: response.msg || '激活成功', key: 'activate' });
        handleSuccess();
      } else {
        createMessage.error({ content: response.msg || '激活失败', key: 'activate' });
      }
    } else {
      // 响应转换器已经处理过，直接返回了数据，说明操作成功
      createMessage.success({ content: '激活成功', key: 'activate' });
      handleSuccess();
    }
  } catch (error: any) {
    console.error('激活失败', error);
    // 从异常中提取后端返回的错误信息
    const backendMsg = error?.response?.data?.msg;
    if (backendMsg) {
      createMessage.error({ content: backendMsg, key: 'activate' });
    } else {
      createMessage.error({ content: '激活失败', key: 'activate' });
    }
  }
};

// 禁用
const handleDeactivate = async (record: LLMModel) => {
  try {
    createMessage.loading({ content: '正在禁用...', key: 'deactivate' });
    const response = await deactivateLLM(record.id!);
    // 检查响应格式：如果响应转换器已经处理过，可能只返回 data，也可能返回完整对象
    if (response && typeof response === 'object' && 'code' in response) {
      if (response.code === 0) {
        createMessage.success({ content: response.msg || '禁用成功', key: 'deactivate' });
        handleSuccess();
      } else {
        createMessage.error({ content: response.msg || '禁用失败', key: 'deactivate' });
      }
    } else {
      // 响应转换器已经处理过，直接返回了数据，说明操作成功
      createMessage.success({ content: '禁用成功', key: 'deactivate' });
      handleSuccess();
    }
  } catch (error: any) {
    console.error('禁用失败', error);
    // 从异常中提取后端返回的错误信息
    const backendMsg = error?.response?.data?.msg;
    if (backendMsg) {
      createMessage.error({ content: backendMsg, key: 'deactivate' });
    } else {
      createMessage.error({ content: '禁用失败', key: 'deactivate' });
    }
  }
};

// 测试
const handleTest = async (record: LLMModel) => {
  try {
    createMessage.loading({ content: '正在测试连接...', key: 'test' });
    const response = await testLLM(record.id!);
    // 检查响应格式：如果响应转换器已经处理过，可能只返回 data，也可能返回完整对象
    if (response && typeof response === 'object' && 'code' in response) {
      // 响应包含 code 字段，使用标准格式判断
      if (response.code === 0) {
        if (response.data && response.data.success) {
          createMessage.success({ content: response.data.message || '测试成功', key: 'test' });
        } else {
          createMessage.warning({ content: response.data?.message || response.msg || '测试失败', key: 'test' });
        }
        handleSuccess();
      } else {
        createMessage.error({ content: response.msg || '测试失败', key: 'test' });
      }
    } else {
      // 响应转换器已经处理过，直接返回了 data 对象
      // 此时 response 就是 { success: boolean, message: string, ... }
      if (response && 'success' in response) {
        if (response.success) {
          createMessage.success({ content: response.message || '测试成功', key: 'test' });
        } else {
          createMessage.warning({ content: response.message || '测试失败', key: 'test' });
        }
        handleSuccess();
      } else {
        // 无法判断格式，默认成功
        createMessage.success({ content: '测试完成', key: 'test' });
        handleSuccess();
      }
    }
  } catch (error: any) {
    console.error('测试失败', error);
    // 从异常中提取后端返回的错误信息
    const backendMsg = error?.response?.data?.msg;
    if (backendMsg) {
      createMessage.error({ content: backendMsg, key: 'test' });
    } else {
      createMessage.error({ content: '测试失败', key: 'test' });
    }
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
    gap: 10px;
  }
}

.llm-manage-card-list-wrapper {
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
