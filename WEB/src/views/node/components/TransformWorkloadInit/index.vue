<template>
  <div class="transform-workload-init">
    <p class="hint">
      推荐「全量分发」走完整链路：无镜像则控制面
      <b>打包→gzip 压缩→SSH 分发→docker load→Agent 拉起容器→Kafka 心跳验收</b>
      （约定 topic <code>iot_transform_heartbeat</code>；端口可变，不以固定 HTTP 端口判断）。
      NODE 偏<strong>节点维</strong>（装哪、起几个）；TRANSFORM「系统对接」偏<strong>业务维</strong>（规则 + 集群 ONLINE 总览，同源 PG）。
      <br />
      本机控制面默认已有 TRANSFORM（出现在系统对接概览），分发列表<strong>不含本机</strong>，只选其他计算节点。
    </p>
    <ClusterNodeSelector
      v-model:selected-node-ids="selectedNodeIds"
      role-filter="computeWorkload"
      :exclude-platform="true"
      :initial-node-ids="initialNodeIds"
      placeholder="选择其他 compute / gpu / hybrid 节点（不含本机控制面）"
    />

    <Tabs
      v-model:activeKey="activeBundleKey"
      class="bundle-tabs-bar"
      type="card"
      :animated="{ inkBar: true, tabPane: false }"
    >
      <TabPane v-for="bundle in TRANSFORM_WORKLOAD_BUNDLE_TYPES" :key="bundle.key" :tab="bundle.label" />
    </Tabs>

    <div class="bundle-tab-content">
      <template v-for="bundle in TRANSFORM_WORKLOAD_BUNDLE_TYPES" :key="bundle.key">
        <WorkloadBundlePanel
          v-if="bundleMounted[bundle.key]"
          v-show="activeBundleKey === bundle.key"
          :bundle="bundle"
          :node-ids="selectedNodeIds"
        />
      </template>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { reactive, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { TabPane, Tabs } from 'ant-design-vue';
import { TRANSFORM_WORKLOAD_BUNDLE_TYPES } from '../../utils/constants';
import ClusterNodeSelector from '../ClusterNodeSelector/index.vue';
import WorkloadBundlePanel from '../WorkloadBundleBatch/WorkloadBundlePanel.vue';

defineOptions({ name: 'TransformWorkloadInit' });

defineProps<{
  initialNodeIds?: number[];
}>();

const route = useRoute();
const selectedNodeIds = ref<number[]>([]);
const bundleFromQuery = String(route.query.bundle || '');
const defaultBundle =
  TRANSFORM_WORKLOAD_BUNDLE_TYPES.find((b) => b.key === bundleFromQuery)?.key ||
  TRANSFORM_WORKLOAD_BUNDLE_TYPES[0]?.key ||
  'transform_runtime';
const activeBundleKey = ref(defaultBundle);
const bundleMounted = reactive<Record<string, boolean>>({
  [defaultBundle]: true,
});

watch(activeBundleKey, (key) => {
  bundleMounted[key] = true;
});
</script>

<style scoped lang="less">
.transform-workload-init {
  padding: 16px 20px 24px;
  min-height: 480px;

  .hint {
    margin: 0 0 12px;
    color: #5b6b7c;
    font-size: 13px;
    line-height: 1.6;
  }

  :deep(.bundle-tabs-bar .ant-tabs-content-holder) {
    display: none;
  }
}
</style>
