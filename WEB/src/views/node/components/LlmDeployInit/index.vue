<template>
  <div class="llm-deploy-init">
    <ClusterNodeSelector
      v-model:selected-node-ids="selectedNodeIds"
      role-filter="gpuWorkload"
      :initial-node-ids="initialNodeIds"
      placeholder="选择已勾选大模型功能的节点（可多选）"
    />

    <Tabs v-model:activeKey="activeTab" type="card" class="inner-tabs mt-4">
      <TabPane key="deploy" tab="一键部署" />
      <TabPane key="runtime" tab="运行时分发" />
      <TabPane key="instances" tab="已部署实例" />
    </Tabs>

    <div class="tab-body">
      <LlmDeployPanel
        v-show="activeTab === 'deploy'"
        :node-ids="selectedNodeIds"
        @deployed="refreshInstances"
      />

      <WorkloadBundlePanel
        v-if="llmBundleMounted"
        v-show="activeTab === 'runtime'"
        :bundle="llmBundle"
        :node-ids="selectedNodeIds"
      />

      <div v-show="activeTab === 'instances'" class="instances-panel">
        <Table
          :columns="columns"
          :data-source="instances"
          :loading="loadingInstances"
          row-key="id"
          size="small"
          :pagination="{ pageSize: 10 }"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'status'">
              <Tag :color="statusColor(record.status)">{{ statusText(record.status) }}</Tag>
            </template>
            <template v-else-if="column.key === 'api_endpoint'">
              <TypographyText v-if="record.api_endpoint" copyable>{{ record.api_endpoint }}</TypographyText>
              <span v-else>-</span>
            </template>
            <template v-else-if="column.key === 'action'">
              <Space>
                <Button size="small" danger @click="handleStop(record)">停止</Button>
                <Button size="small" danger ghost @click="handleDelete(record)">删除</Button>
              </Space>
            </template>
          </template>
        </Table>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed, onMounted, ref } from 'vue';
import { Space, TabPane, Table, Tabs, Tag, TypographyText } from 'ant-design-vue';
import { Button } from '@/components/Button';
import { useMessage } from '@/hooks/web/useMessage';
import {
  deleteLlmDeploy,
  getLlmDeployList,
  stopLlmDeploy,
  type LLMDeployService,
} from '@/api/device/llmDeploy';
import { WORKLOAD_BUNDLE_TYPES } from '../../utils/constants';
import ClusterNodeSelector from '../ClusterNodeSelector/index.vue';
import LlmDeployPanel from '../LlmDeployPanel/index.vue';
import WorkloadBundlePanel from '../WorkloadBundleBatch/WorkloadBundlePanel.vue';

defineOptions({ name: 'LlmDeployInit' });

defineProps<{
  initialNodeIds?: number[];
}>();

const { createMessage } = useMessage();
const selectedNodeIds = ref<number[]>([]);
const activeTab = ref('deploy');
const llmBundleMounted = ref(false);
const instances = ref<LLMDeployService[]>([]);
const loadingInstances = ref(false);

const llmBundle = computed(() => WORKLOAD_BUNDLE_TYPES.find((b) => b.key === 'llm_service')!);

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
  { title: '服务名', dataIndex: 'service_name', key: 'service_name' },
  { title: '模型', dataIndex: 'qwen_model_key', key: 'qwen_model_key' },
  { title: '节点 IP', dataIndex: 'server_ip', key: 'server_ip', width: 130 },
  { title: '端口', dataIndex: 'port', key: 'port', width: 70 },
  { title: '接入地址', key: 'api_endpoint', width: 280 },
  { title: '状态', key: 'status', width: 90 },
  { title: '操作', key: 'action', width: 140 },
];

function statusColor(status?: string) {
  const map: Record<string, string> = {
    running: 'success',
    deploying: 'processing',
    stopped: 'default',
    error: 'error',
  };
  return map[status || ''] || 'default';
}

function statusText(status?: string) {
  const map: Record<string, string> = {
    running: '运行中',
    deploying: '部署中',
    stopped: '已停止',
    error: '异常',
  };
  return map[status || ''] || status || '-';
}

async function refreshInstances() {
  loadingInstances.value = true;
  try {
    const res = await getLlmDeployList({ page: 1, pageSize: 100 });
    instances.value = res?.data?.list || [];
  } finally {
    loadingInstances.value = false;
  }
}

async function handleStop(record: LLMDeployService) {
  if (!record.id) return;
  await stopLlmDeploy(record.id);
  createMessage.success('已停止');
  refreshInstances();
}

async function handleDelete(record: LLMDeployService) {
  if (!record.id) return;
  await deleteLlmDeploy(record.id);
  createMessage.success('已删除');
  refreshInstances();
}

onMounted(() => {
  llmBundleMounted.value = true;
  refreshInstances();
});
</script>

<style scoped lang="less">
.llm-deploy-init {
  padding: 16px 20px 24px;
  min-height: 480px;
}

.instances-panel {
  margin-top: 8px;
}
</style>
