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
          <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
            <Tag :color="getStatusColor(record.status)">
              {{ getStatusText(record.status, record.running_count) }}
            </Tag>
            <Tag v-if="record.stopped_count !== undefined && record.stopped_count > 0" color="default">
              停止中：{{ record.stopped_count }}
            </Tag>
          </div>
        </template>
        <template v-if="column.dataIndex === 'replicas'">
          <span class="replica-tag-table" v-if="record.replica_count" @click="handleViewReplicas(record)">
            副本数: {{ record.replica_count }}
          </span>
          <span v-else>--</span>
        </template>
        <template v-if="column.dataIndex === 'action'">
          <TableAction
            :actions="[
              {
                icon: 'mdi:play-outline',
                tooltip: { title: '批量启动', placement: 'top' },
                onClick: () => handleBatchStart(record),
                disabled: record.status === 'running',
                style: 'color: #52c41a; padding: 0 8px; font-size: 16px;'
              },
              {
                icon: 'mdi:stop-outline',
                tooltip: { title: '批量停止', placement: 'top' },
                onClick: () => handleBatchStop(record),
                disabled: record.status !== 'running',
                style: 'color: #ff4d4f; padding: 0 8px; font-size: 16px;'
              },
              {
                icon: 'mdi:restart',
                tooltip: { title: '批量重启', placement: 'top' },
                onClick: () => handleBatchRestart(record),
                disabled: record.status !== 'running',
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
        @view-replicas="handleViewReplicas"
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
    <ReplicasDrawer
      @register="registerReplicasDrawer"
      @refresh="handleReplicasRefresh"
    />
  </div>
</template>

<script lang="ts" setup>
import {nextTick, onBeforeUnmount, onMounted, reactive, ref, watch} from 'vue';
import {BasicTable, TableAction, useTable} from '@/components/Table';
import {useMessage} from '@/hooks/web/useMessage';
const {createMessage} = useMessage();
import {useModal} from '@/components/Modal';
import {useDrawer} from '@/components/Drawer';
import {
  deleteDeployService,
  getDeployServicePage,
  getModelPage,
  restartDeployService,
  startDeployService,
  stopDeployService,
  batchStartDeployService,
  batchStopDeployService,
  batchRestartDeployService,
  getDeployServiceReplicas
} from '@/api/device/model';
import DeployModal from '../DeployModal/DeployModal.vue';
import DeployServiceCardList from '../DeployServiceCardList/index.vue';
import ServiceLogsModal from '../ServiceLogsModal/ServiceLogsModal.vue';
import ReplicasDrawer from '../ReplicasDrawer/index.vue';
import {getBasicColumns, getFormConfig} from './Data';
import {Tag} from 'ant-design-vue';
import {Icon} from "@/components/Icon";


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
const [registerReplicasDrawer, {openDrawer: openReplicasDrawer}] = useDrawer();

// 表格刷新
function handleDeploySuccess() {
  reload({
    page: 0,
  });
  cardListReload();
}

// 批量启动服务
const handleBatchStart = async (record) => {
  try {
    const result = await batchStartDeployService(record.service_name);
    
    // 现在 API 返回完整响应对象（包含 code、msg、data）
    // 当 isTransformResponse: false 时，实际数据在 result.data 中
    const responseData = result?.data || {};
    if (result && responseData.code === 0) {
      const data = responseData.data || {};
      const successCount = data.success_count || 0;
      const failCount = data.fail_count || 0;
      const errors = data.errors || [];
      
      // 优先使用后台返回的 msg
      if (responseData.msg) {
        // 根据成功/失败情况选择消息类型
        if (failCount === 0) {
          createMessage.success(responseData.msg);
        } else if (successCount === 0) {
          createMessage.error(responseData.msg);
        } else {
          createMessage.warning(responseData.msg);
        }
      } else {
        // 如果后台没有返回 msg，则根据数据判断
        // 如果全部成功
        if (failCount === 0) {
          createMessage.success('批量启动成功');
        } 
        // 如果全部失败
        else if (successCount === 0) {
          // 检查是否是模型文件相关错误
          let errorMessage = '批量启动失败';
          
          if (errors.length > 0) {
            const hasModelError = errors.some(err => 
              err.includes('MinIO') || 
              err.includes('Minio') || 
              err.includes('模型文件不存在') || 
              err.includes('模型文件下载失败')
            );
            
            if (hasModelError) {
              errorMessage = '模型不存在，启动失败';
            } else {
              // 其他错误，显示第一个错误信息
              errorMessage = errors[0] || '批量启动失败';
            }
          }
          
          createMessage.error(errorMessage);
        } 
        // 如果部分成功部分失败
        else {
          // 检查是否有模型文件相关错误
          let warningMessage = `批量启动部分成功：成功 ${successCount} 个，失败 ${failCount} 个`;
          
          if (errors.length > 0) {
            const hasModelError = errors.some(err => 
              err.includes('MinIO') || 
              err.includes('Minio') || 
              err.includes('模型文件不存在') || 
              err.includes('模型文件下载失败')
            );
            
            if (hasModelError) {
              warningMessage = `部分服务启动失败：模型不存在，启动失败（成功 ${successCount} 个，失败 ${failCount} 个）`;
            }
          }
          
          createMessage.warning(warningMessage);
        }
      }
    } else {
      // code !== 0 的情况
      createMessage.error(responseData?.msg || '批量启动失败');
    }
    
    reload();
    cardListReload();
  } catch (error: any) {
    // 如果进入 catch，说明请求失败
    console.error('批量启动异常:', error);
    const errorData = error?.response?.data || error?.data || {};
    const errorMsg = errorData.msg || error?.message || '批量启动失败，请检查网络连接';
    createMessage.error(`批量启动失败：${errorMsg}`);
  }
};

// 批量停止服务
const handleBatchStop = async (record) => {
  try {
    const result = await batchStopDeployService(record.service_name);
    // 当 isTransformResponse: false 时，实际数据在 result.data 中
    const responseData = result?.data || {};
    if (responseData.code === 0) {
      createMessage.success(responseData.msg || '批量停止成功');
    } else {
      createMessage.error(responseData.msg || '批量停止失败');
    }
    reload();
    cardListReload();
  } catch (error) {
    createMessage.error('批量停止失败');
    console.error('批量停止失败:', error);
  }
};

// 批量重启服务
const handleBatchRestart = async (record) => {
  try {
    const result = await batchRestartDeployService(record.service_name);
    // 当 isTransformResponse: false 时，实际数据在 result.data 中
    const responseData = result?.data || {};
    if (responseData.code === 0) {
      createMessage.success(responseData.msg || '批量重启成功');
    } else {
      createMessage.error(responseData.msg || '批量重启失败');
    }
    reload();
    cardListReload();
  } catch (error) {
    createMessage.error('批量重启失败');
    console.error('批量重启失败:', error);
  }
};

// 查看副本详情
const handleViewReplicas = async (record) => {
  // 直接打开抽屉，由抽屉组件通过API获取数据（支持后端分页）
  openReplicasDrawer(true, {
    serviceName: record.service_name,
    modelId: record.model_id
  });
};

// 副本刷新回调
const handleReplicasRefresh = () => {
  reload();
  cardListReload();
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
    cardListReload();
  } catch (error) {
    createMessage.error('删除失败');
    console.error('删除失败:', error);
  }
};

// 状态相关
const getStatusColor = (status) => {
  const colorMap = {
    'running': 'green',
    'stopped': 'default'
  };
  return colorMap[status] || 'default';
};

const getStatusText = (status, runningCount) => {
  const textMap = {
    'running': '运行中',
    'stopped': '已停止'
  };
  const baseText = textMap[status] || status;
  // 如果是运行中状态且有running_count，显示"运行中：3"格式
  if (status === 'running' && runningCount !== undefined && runningCount > 0) {
    return `${baseText}：${runningCount}`;
  }
  return baseText;
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

.replica-tag-table {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
  border: 1px solid;
  background: #e6f7ff;
  border-color: #91d5ff;
  color: #1890ff;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    background: #bae7ff;
    border-color: #69c0ff;
    color: #0050b3;
  }
}
</style>

