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
          <a-tag :color="getStatusColor(record.status, record.is_active)">
            {{ getStatusText(record.status, record.is_active) }}
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
    <div v-else>
      <LLMManageCardList
        :params="params"
        :api="getLLMListApi"
        @get-method="getMethod"
        @delete="handleDel"
        @view="handleView"
        @edit="handleEdit"
        @activate="handleActivate"
        @deactivate="handleDeactivate"
        @field-value-change="handleFieldValueChange"
      >
        <template #header>
          <a-button type="primary" @click="handleCreate">
            <template #icon>
              <PlusOutlined />
            </template>
            新建大模型
          </a-button>
          <a-button @click="handleToggleViewMode" type="default">
            <template #icon>
              <SwapOutlined />
            </template>
            切换视图
          </a-button>
        </template>
      </LLMManageCardList>
    </div>

    <!-- 大模型配置模态框 -->
    <LLMModal @register="registerModal" @success="handleSuccess" />
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { BasicTable, TableAction, useTable } from '@/components/Table';
import { useModal } from '@/components/Modal';
import { Col } from 'ant-design-vue';
import { PlusOutlined, SwapOutlined } from '@ant-design/icons-vue';
import { useMessage } from '@/hooks/web/useMessage';
import { getBasicColumns, getFormConfig } from './Data';
import { getLLMList, deleteLLM, activateLLM, deactivateLLM, testLLM, type LLMModel } from '@/api/device/llm';
import LLMModal from './LLMModal.vue';
import LLMManageCardList from './LLMManageCardList.vue';

defineOptions({ name: 'LLMManage' });

const { createMessage } = useMessage();
const router = useRouter();
const [registerModal, { openModal }] = useModal();

// 视图模式
const viewMode = ref<'table' | 'card'>('card');
const params = {};
let cardListReload = () => {};

function getMethod(m: any) {
  cardListReload = m;
}

// 表格配置
const [registerTable, { reload, getForm }] = useTable({
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

// 大模型列表API（卡片模式）
const getLLMListApi = async (params: any) => {
  try {
    const response = await getLLMList({
      page: params.page || 1,
      pageSize: params.pageSize || 18,
      name: params.name || undefined,
      vendor: params.vendor || undefined,
      model_type: params.model_type || undefined,
    });
    
    // HTTP 转换器可能返回两种格式：
    // 1. { code: 0, data: { list: [], total: 0 }, msg: 'success' }
    // 2. { list: [], total: 0 } (转换器自动解包了 data.data，当 total 在 data.data.total 中时)
    let items: LLMModel[] = [];
    let total = 0;
    
    if (response && typeof response === 'object') {
      if ('code' in response && response.code === 0 && response.data) {
        // 标准格式：包含 code 和 data
        items = response.data.list || [];
        total = response.data.total || 0;
      } else if ('list' in response && Array.isArray(response.list)) {
        // 转换器已解包的格式：直接包含 list 和 total
        items = response.list;
        total = response.total || 0;
      }
    }
    
    return {
      success: true,
      data: {
        items,
        total,
      },
    };
  } catch (error) {
    console.error('获取大模型列表失败', error);
    return {
      success: false,
      data: {
        items: [],
        total: 0,
      },
    };
  }
};

// 获取状态文本（基于is_active，不再使用status字段）
const getStatusText = (status: string, isActive: boolean) => {
  // 只根据is_active判断，不再使用status字段
  return isActive ? '已激活' : '未激活';
};

// 获取状态颜色（基于is_active，不再使用status字段）
const getStatusColor = (status: string, isActive: boolean) => {
  // 只根据is_active判断，不再使用status字段
  return isActive ? 'green' : 'default';
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
  ];

  if (record.is_active) {
    actions.push({
      icon: 'ant-design:pause-circle-outlined',
      tooltip: '禁用',
      onClick: () => handleDeactivate(record),
    });
  } else {
    actions.push({
      icon: 'ant-design:play-circle-outlined',
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
    cardListReload();
  }
};

// 处理表单字段值变化（卡片模式，实时监听）
function handleFieldValueChange(field: string, value: any) {
  // 可以在这里处理字段值变化
}

// 重置表单（表格模式）
const handleTableReset = async () => {
  const form = getForm();
  await form.resetFields();
  reload();
};

// 提交表单（表格模式）
const handleTableSubmit = async () => {
  const form = getForm();
  await form.submit();
};

// 创建
const handleCreate = () => {
  openModal(true, {
    isUpdate: false,
  });
};

// 查看
const handleView = (record: LLMModel) => {
  openModal(true, {
    isUpdate: false,
    record,
  });
};

// 编辑
const handleEdit = (record: LLMModel) => {
  openModal(true, {
    isUpdate: true,
    record,
  });
};

// 删除（卡片模式）
const handleDel = async (record: LLMModel) => {
  await handleDelete(record);
  cardListReload();
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
    let testSuccess = false;
    if (response && typeof response === 'object' && 'code' in response) {
      // 响应包含 code 字段，使用标准格式判断
      if (response.code === 0) {
        if (response.data && response.data.success) {
          testSuccess = true;
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
          testSuccess = true;
          createMessage.success({ content: response.message || '测试成功', key: 'test' });
        } else {
          createMessage.warning({ content: response.message || '测试失败', key: 'test' });
        }
        handleSuccess();
      } else {
        // 无法判断格式，默认成功
        testSuccess = true;
        createMessage.success({ content: '测试完成', key: 'test' });
        handleSuccess();
      }
    }
    
    // 测试成功后，跳转到模型推理页面，并传递大模型ID
    if (testSuccess && record.id) {
      // 跳转到训练页面，并切换到模型推理tab（key="2"），传递大模型ID
      router.push({
        path: '/train',
        query: {
          tab: '2',
          llmId: record.id.toString()
        }
      });
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

// 成功回调
const handleSuccess = () => {
  if (viewMode.value === 'table') {
    reload();
  } else {
    cardListReload();
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
  // 卡片模式会在组件内部自动加载数据
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
</style>
