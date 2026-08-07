<template>
  <div class="runtime-cpp-batch-panel">
    <Alert type="warning" show-icon class="mb-3" :message="WORKLOAD_BUNDLE_COPY.runtimeCppHint" />
    <div class="path-hints mb-3">
      <span class="label">安装路径：</span><code>{{ WORKLOAD_BUNDLE_COPY.runtimeCppPath }}</code>
    </div>
    <Space wrap class="mb-3">
      <Button :loading="loading === 'check'" :disabled="!canOperate" @click="run('check')">
        {{ WORKLOAD_BUNDLE_COPY.runtimeCppCheck }}
      </Button>
      <Button type="primary" :loading="loading === 'deploy'" :disabled="!canOperate" @click="run('deploy')">
        {{ WORKLOAD_BUNDLE_COPY.runtimeCppDeploy }}
      </Button>
      <Button danger :loading="loading === 'remove'" :disabled="!canOperate" @click="confirmRemove">
        {{ WORKLOAD_BUNDLE_COPY.runtimeCppRemove }}
      </Button>
    </Space>
    <Alert
      v-if="lastResult"
      class="mb-3"
      :type="lastResult.success ? 'success' : 'error'"
      show-icon
      :message="lastResult.message"
    />
    <div v-if="nodeResults.length">
      <div v-for="item in nodeResults" :key="item.nodeId" class="node-result-item">
        <Tag :color="item.success ? 'success' : 'error'">{{ item.success ? '成功' : '失败' }}</Tag>
        <span>{{ item.nodeName || item.host }} — {{ item.message }}</span>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed, ref } from 'vue';
import { Alert, Modal, Space, Tag } from 'ant-design-vue';
import { Button } from '@/components/Button';
import { useMessage } from '@/hooks/web/useMessage';
import {
  batchCheckRuntimeCppBySsh,
  batchDeployRuntimeCppBySsh,
  batchRemoveRuntimeCppBySsh,
  type WorkloadBundleNodeResult,
} from '@/api/device/node';
import { WORKLOAD_BUNDLE_COPY } from '../../utils/constants';

defineOptions({ name: 'RuntimeCppBatchPanel' });

const props = defineProps<{ nodeIds: number[] }>();

const { createMessage } = useMessage();
const loading = ref<'check' | 'deploy' | 'remove' | null>(null);
const lastResult = ref<{ success: boolean; message: string } | null>(null);
const nodeResults = ref<WorkloadBundleNodeResult[]>([]);

const canOperate = computed(() => props.nodeIds.length > 0);

async function run(action: 'check' | 'deploy' | 'remove') {
  if (!canOperate.value) {
    createMessage.warning('请先选择目标节点');
    return;
  }
  loading.value = action;
  lastResult.value = null;
  nodeResults.value = [];
  const payload = { nodeIds: props.nodeIds };
  try {
    const data =
      action === 'check'
        ? await batchCheckRuntimeCppBySsh(payload)
        : action === 'deploy'
          ? await batchDeployRuntimeCppBySsh(payload)
          : await batchRemoveRuntimeCppBySsh(payload);
    nodeResults.value = data?.results || [];
    lastResult.value = { success: !!data?.success, message: data?.message || '' };
    data?.success ? createMessage.success(data.message || '完成') : createMessage.error(data?.message || '失败');
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '请求失败';
    lastResult.value = { success: false, message: msg };
    createMessage.error(msg);
  } finally {
    loading.value = null;
  }
}

function confirmRemove() {
  Modal.confirm({
    title: '确认删除 RUNTIME？',
    content: `将对 ${props.nodeIds.length} 个节点卸载 /opt/easyaiot/RUNTIME`,
    okType: 'danger',
    onOk: () => run('remove'),
  });
}
</script>

<style scoped lang="less">
.runtime-cpp-batch-panel {
  padding: 4px 0;
}

.path-hints {
  font-size: 13px;
  color: rgba(0, 0, 0, 0.65);

  .label {
    margin-right: 6px;
  }

  code {
    font-size: 12px;
  }
}

.node-result-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  font-size: 13px;
}
</style>
