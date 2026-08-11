<template>
  <Alert class="media-path-readiness" type="info" show-icon>
    <template #message>媒体存储路径</template>
    <template #description>
      <div class="desc">
        <span>
          告警图与录像写入同一挂载根下的 <code>alert_images</code> / <code>playbacks</code>。
          NFS 集群运维与拓扑请前往「分布式存储」。
        </span>
        <div v-if="selectedHint" class="node-hint">
          当前节点 {{ selectedHint.name }}（{{ selectedHint.host }}）：
          <Tag :color="selectedHint.ready ? 'success' : 'warning'">
            {{ selectedHint.ready ? '挂载就绪' : '挂载未就绪' }}
          </Tag>
          <span v-if="selectedHint.mountPath" class="path">{{ selectedHint.mountPath }}</span>
        </div>
        <div v-else-if="summary" class="cluster-hint">
          客户端挂载覆盖 {{ coverageReady }} / {{ coverageTotal }}（{{ coveragePercent }}%）
          <span v-if="(summary.unprobedCount ?? 0) > 0"> · 未探测 {{ summary.unprobedCount }}</span>
        </div>
        <Space wrap class="actions">
          <Button type="link" size="small" :loading="loading" @click="reload">刷新</Button>
          <Button type="link" size="small" @click="goStorageTopology">
            查看 NFS 集群拓扑
          </Button>
        </Space>
      </div>
    </template>
  </Alert>
</template>

<script lang="ts" setup>
import { computed, onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { Alert, Space, Tag } from 'ant-design-vue';
import { Button } from '@/components/Button';
import { getCephTopology, type CephTopologySummaryVO, type ComputeNodeVO } from '@/api/device/node';
import { readCephMountFromTags } from '../../utils/constants';
import { navigateToStorageSubTab } from '../../utils/nodeNavigation';

defineOptions({ name: 'MediaPathReadinessBar' });

const props = defineProps<{
  selectedNode?: Pick<ComputeNodeVO, 'id' | 'name' | 'host' | 'tags'> | null;
}>();

const router = useRouter();
const loading = ref(false);
const summary = ref<CephTopologySummaryVO | null>(null);

const coverageTotal = computed(() => summary.value?.clientNodes ?? 0);
const coverageReady = computed(() => {
  const s = summary.value;
  if (!s) return 0;
  // mountReadyCount 含非客户端；覆盖展示优先用 coveragePercent 反推
  if (s.coveragePercent != null && coverageTotal.value > 0) {
    return Math.round((s.coveragePercent * coverageTotal.value) / 100);
  }
  return Math.min(s.mountReadyCount ?? 0, coverageTotal.value);
});
const coveragePercent = computed(() => summary.value?.coveragePercent ?? 0);

const selectedHint = computed(() => {
  const node = props.selectedNode;
  if (!node?.id) return null;
  const mount = readCephMountFromTags(node.tags);
  const ready = mount.status === 'ready';
  return {
    name: node.name || `#${node.id}`,
    host: node.host || '-',
    ready,
    mountPath: mount.mountPath,
  };
});

async function reload() {
  loading.value = true;
  try {
    const data = await getCephTopology();
    summary.value = data.summary || null;
  } catch {
    summary.value = null;
  } finally {
    loading.value = false;
  }
}

function goStorageTopology() {
  navigateToStorageSubTab(router, 'topology', props.selectedNode?.id);
}

onMounted(() => reload());

watch(
  () => props.selectedNode?.id,
  () => reload(),
);
</script>

<style scoped lang="less">
.media-path-readiness {
  margin-bottom: 16px;

  .desc {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .node-hint,
  .cluster-hint {
    color: #666;
    font-size: 13px;
  }

  .path {
    margin-left: 6px;
    color: #999;
  }

  code {
    padding: 0 4px;
    background: #f5f5f5;
    border-radius: 3px;
  }

  .actions {
    margin-top: 4px;
  }
}
</style>
