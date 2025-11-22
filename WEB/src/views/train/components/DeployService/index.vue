<template>
  <div class="deploy-service-container bg-white p-6 rounded-xl shadow-lg transition-all duration-300">
    <BasicTable
      v-if="state.isTableMode"
      @register="registerTable"
      class="rounded-xl overflow-hidden border border-gray-100 shadow-sm"
    >
      <template #toolbar>
        <a-button type="primary" @click="openDeployModal(true, {isEdit: false, isView: false})">
          <Icon icon="ant-design:plus-circle-outlined"/>
          模型部署
        </a-button>
        <a-button type="default" @click="handleClickSwap" preIcon="ant-design:swap-outlined">
          切换视图
        </a-button>
      </template>
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'status'">
          <Tag :color="getStatusColor(record.status)">
            {{ getStatusText(record.status) }}
          </Tag>
        </template>
        <template v-if="column.dataIndex === 'action'">
          <TableAction
            :actions="[
              {
                icon: 'mdi:play-outline',
                tooltip: { title: '启动', placement: 'top' },
                onClick: () => handleStart(record),
                disabled: record.status === 'running',
                style: 'color: #52c41a; padding: 0 8px; font-size: 16px;'
              },
              {
                icon: 'mdi:stop-outline',
                tooltip: { title: '停止', placement: 'top' },
                onClick: () => handleStop(record),
                disabled: record.status !== 'running',
                style: 'color: #ff4d4f; padding: 0 8px; font-size: 16px;'
              },
              {
                icon: 'mdi:restart',
                tooltip: { title: '重启', placement: 'top' },
                onClick: () => handleRestart(record),
                disabled: record.status !== 'running',
                style: 'color: #1890ff; padding: 0 8px; font-size: 16px;'
              },
              {
                icon: 'mdi:file-document-outline',
                tooltip: { title: '查看日志', placement: 'top' },
                onClick: () => handleViewLogs(record),
                style: 'color: #1890ff; padding: 0 8px; font-size: 16px;'
              },
              {
                icon: 'mdi:delete-outline',
                tooltip: { title: '删除', placement: 'top' },
                popConfirm: {
                  placement: 'topRight',
                  title: '确定删除此部署服务?',
                  confirm: () => handleDelete(record)
                },
                style: 'color: #ff4d4f; padding: 0 8px; font-size: 16px;'
              }
            ]"
            :action-style="{
              display: 'flex',
              flexWrap: 'nowrap',
              gap: '4px',
              alignItems: 'center',
              marginRight: '0'
            }"
          />
        </template>
      </template>
    </BasicTable>
    <div v-else>
      <DeployServiceCardList
        :params="params"
        :api="getDeployServicePage"
        @get-method="getMethod"
        @view-logs="handleViewLogs"
      >
        <template #header>
          <a-button type="primary" @click="openDeployModal(true, {isEdit: false, isView: false})">
            <Icon icon="ant-design:plus-circle-outlined"/>
            部署新服务
          </a-button>
          <a-button type="default" @click="handleClickSwap" preIcon="ant-design:swap-outlined">
            切换视图
          </a-button>
        </template>
      </DeployServiceCardList>
    </div>
    <DeployModal @register="registerDeployModal" @success="handleDeploySuccess"/>
    <ServiceLogsModal
      v-if="showLogsModal"
      @register="registerLogsModal"
      @close="handleLogsModalClose"
    />
  </div>
</template>

<script lang="ts" setup>
import {nextTick, onBeforeUnmount, onMounted, reactive, ref, watch} from 'vue';
import {BasicTable, TableAction, useTable} from '@/components/Table';
import {useMessage} from '@/hooks/web/useMessage';
import {useModal} from '@/components/Modal';
import {
  deleteDeployService,
  getDeployServicePage,
  getModelPage,
  restartDeployService,
  startDeployService,
  stopDeployService
} from '@/api/device/model';
import DeployModal from '../DeployModal/DeployModal.vue';
import DeployServiceCardList from '../DeployServiceCardList/index.vue';
import ServiceLogsModal from '../ServiceLogsModal/ServiceLogsModal.vue';
import {getBasicColumns, getFormConfig} from './Data';
import {Tag} from 'ant-design-vue';
import {Icon} from "@/components/Icon";

const {createMessage} = useMessage();

// 模型选项列表
const modelOptions = ref<any[]>([]);

// 加载模型列表
const loadModelOptions = async () => {
  try {
    const res = await getModelPage({pageNo: 1, pageSize: 1000});
    const models = res.data || [];
    modelOptions.value = models.map((model) => ({
      label: `${model.name} (${model.version})`,
      value: model.id,
    }));
  } catch (error) {
    console.error('获取模型列表失败:', error);
    modelOptions.value = [];
  }
};

const showLogsModal = ref(false);
const state = reactive({
  isTableMode: false, // 默认使用卡片模式
});

const params = {};
let cardListReload = () => {};

function getMethod(m: any) {
  cardListReload = m;
}

function handleClickSwap() {
  state.isTableMode = !state.isTableMode;
}

const [registerDeployModal, {openModal: openDeployModal}] = useModal();
const [registerLogsModal, {
  openModal: openServiceLogsModal,
  closeModal: closeServiceLogsModal
}] = useModal();

// 表格刷新
function handleDeploySuccess() {
  reload({
    page: 0,
  });
  cardListReload();
}

// 启动服务
const handleStart = async (record) => {
  try {
    await startDeployService(record.id);
    createMessage.success('服务启动成功');
    reload();
  } catch (error) {
    createMessage.error('服务启动失败');
    console.error('服务启动失败:', error);
  }
};

// 停止服务
const handleStop = async (record) => {
  try {
    await stopDeployService(record.id);
    createMessage.success('服务停止成功');
    reload();
  } catch (error) {
    createMessage.error('服务停止失败');
    console.error('服务停止失败:', error);
  }
};

// 重启服务
const handleRestart = async (record) => {
  try {
    await restartDeployService(record.id);
    createMessage.success('服务重启成功');
    reload();
  } catch (error) {
    createMessage.error('服务重启失败');
    console.error('服务重启失败:', error);
  }
};

// 查看日志
const handleViewLogs = (record) => {
  showLogsModal.value = true;
  nextTick(() => {
    openServiceLogsModal(true, {record});
  });
};

const handleLogsModalClose = () => {
  showLogsModal.value = false;
};

// 删除服务
const handleDelete = async (record) => {
  try {
    await deleteDeployService(record.id);
    createMessage.success('删除成功');
    reload();
  } catch (error) {
    createMessage.error('删除失败');
    console.error('删除失败:', error);
  }
};

// 状态相关
const getStatusColor = (status) => {
  const colorMap = {
    'running': 'green',
    'stopped': 'default',
    'error': 'red'
  };
  return colorMap[status] || 'default';
};

const getStatusText = (status) => {
  const textMap = {
    'running': '运行中',
    'stopped': '已停止',
    'error': '错误'
  };
  return textMap[status] || status;
};

// 轮询相关
const pollingInterval = ref<number>(10000); // 默认10秒
const pollingTimer = ref<NodeJS.Timeout | null>(null);
const isPollingActive = ref<boolean>(true);

const [registerTable, {reload, getForm}] = useTable({
  canResize: true,
  showIndexColumn: false,
  title: '',
  api: async (params) => {
    const requestParams = {...params};
    // 将model_id传递给后端，如果为空则删除该参数
    if (requestParams.model_id === '' || requestParams.model_id === undefined) {
      delete requestParams.model_id;
    }
    return getDeployServicePage(requestParams);
  },
  columns: getBasicColumns(),
  useSearchForm: true,
  showTableSetting: true,
  pagination: true,
  formConfig: getFormConfig(modelOptions.value),
  fetchSetting: {
    listField: 'data',
    totalField: 'total',
  },
  rowKey: 'id',
});

const startPolling = async () => {
  if (!isPollingActive.value) return;
  
  // 只有在表格模式下才进行轮询刷新
  if (!state.isTableMode) {
    pollingTimer.value = setTimeout(startPolling, pollingInterval.value);
    return;
  }

  try {
    await reload();
  } catch (error) {
    console.error('轮询请求失败:', error);
  } finally {
    pollingTimer.value = setTimeout(startPolling, pollingInterval.value);
  }
};

onMounted(() => {
  loadModelOptions();
  // 使用 nextTick 确保表格已经注册
  nextTick(() => {
    startPolling();
  });
});

onBeforeUnmount(() => {
  if (pollingTimer.value) {
    clearTimeout(pollingTimer.value);
    pollingTimer.value = null;
  }
});

// 监听表格模式切换，切换到表格模式时立即刷新
watch(() => state.isTableMode, (isTableMode) => {
  if (isTableMode) {
    // 切换到表格模式时，等待表格注册完成后再刷新
    nextTick(() => {
      try {
        reload();
      } catch (error) {
        // 如果表格还未注册，忽略错误，等待下次轮询
        console.warn('表格尚未注册，跳过刷新');
      }
    });
  }
});

// 监听模型选项变化，更新表单配置
watch(() => modelOptions.value, (newOptions) => {
  if (newOptions.length > 0) {
    const form = getForm();
    if (form) {
      form.updateSchema({
        field: 'model_id',
        componentProps: {
          options: [
            {label: '全部', value: ''},
            ...newOptions,
          ],
        },
      });
    }
  }
}, {deep: true});
</script>

<style lang="less" scoped>
.deploy-service-container {
  // 样式可以根据需要添加
}
</style>

