<template>
  <div v-if="selectedHint || summary" class="media-path-readiness">
    <Space wrap align="center">
      <template v-if="selectedHint">
        <span>{{ selectedHint.name }}</span>
        <Tag :color="selectedHint.ready ? 'success' : 'warning'">
          {{ selectedHint.ready ? '挂载就绪' : '挂载未就绪' }}
        </Tag>
        <span v-if="selectedHint.mountPath" class="path">{{ selectedHint.mountPath }}</span>
      </template>
      <template v-else-if="summary">
        <span>
          覆盖 {{ coverageReady }}/{{ coverageTotal }}（{{ coveragePercent }}%）
        </span>
      </template>
      <Button type="link" size="small" :loading="loading" @click="reload">刷新</Button>
      <Button type="link" size="small" @click="goStorageTopology">NFS 集群管理</Button>
    </Space>
  </div>
</template>

<script lang="ts" setup>
import { computed, onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { Space, Tag } from 'ant-design-vue';
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
  return {
    name: node.name || `#${node.id}`,
    host: node.host || '-',
    ready: mount.status === 'ready',
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
  navigateToStorageSubTab(router, 'manage', props.selectedNode?.id);
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
  padding: 8px 12px;
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  background: #fafafa;
  font-size: 13px;
  color: #595959;

  .path {
    color: #8c8c8c;
  }
}
</style>
