<script lang="ts" setup>
import { computed, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { Empty, Pagination, Spin } from 'ant-design-vue';
import type { ClusterLaneVO, ComputeNodeVO } from '@/api/device/node';
import { deleteNode } from '@/api/device/node';
import { useMessage } from '@/hooks/web/useMessage';
import ClusterLaneRow from './ClusterLaneRow.vue';
import { navigateToNodeBatchTab, navigateToOnboardService } from '../../utils/nodeNavigation';
import { isPlatformNode } from '../../utils/platformNode';

defineOptions({ name: 'ClusterSwimlane' });

const props = defineProps<{
  lanes: ClusterLaneVO[];
  loading?: boolean;
}>();

const emit = defineEmits<{
  view: [node: ComputeNodeVO];
  edit: [node: ComputeNodeVO];
  refresh: [];
}>();

const PAGE_SIZE = 4;

const router = useRouter();
const { createMessage, createConfirm } = useMessage();
const page = ref(1);

const pagedLanes = computed(() => {
  const start = (page.value - 1) * PAGE_SIZE;
  return props.lanes.slice(start, start + PAGE_SIZE);
});

watch(
  () => props.lanes,
  (list) => {
    const maxPage = Math.max(1, Math.ceil(list.length / PAGE_SIZE) || 1);
    if (page.value > maxPage) page.value = maxPage;
  },
);

function handleBatchNavigate(tab: string, nodeIds: number[]) {
  navigateToNodeBatchTab(router, tab, nodeIds);
}

async function handleDelete(node: ComputeNodeVO) {
  if (isPlatformNode(node) || node.isRemote || !node.id) return;
  createConfirm({
    iconType: 'warning',
    title: '确认删除该节点？',
    onOk: async () => {
      await deleteNode(node.id!);
      createMessage.success('删除成功');
      emit('refresh');
    },
  });
}
</script>

<template>
  <Spin :spinning="!!loading">
    <div v-if="lanes.length" class="node-cards__grid">
      <ClusterLaneRow
        v-for="lane in pagedLanes"
        :key="lane.laneKey"
        :lane="lane"
        @view="(node) => emit('view', node)"
        @edit="(node) => emit('edit', node)"
        @delete="handleDelete"
        @continue-setup="(node) => navigateToOnboardService(router, node)"
        @batch-navigate="handleBatchNavigate"
        @refresh="emit('refresh')"
      />
    </div>

    <div v-if="lanes.length > PAGE_SIZE" class="node-cards__pager">
      <Pagination
        v-model:current="page"
        :total="lanes.length"
        :page-size="PAGE_SIZE"
        size="small"
        :show-size-changer="false"
        :show-total="(total) => `共 ${total} 个中心节点`"
      />
    </div>

    <Empty
      v-if="!loading && !lanes.length"
      class="node-cards__empty"
      description="暂无中心节点，请先添加中心节点或纳管工作节点"
    />
  </Spin>
</template>

<style lang="less" scoped>
@import '../../utils/theme.less';

.node-cards__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.node-cards__pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}

.node-cards__empty {
  padding: 48px 0;
}

@media (max-width: 900px) {
  .node-cards__grid {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
