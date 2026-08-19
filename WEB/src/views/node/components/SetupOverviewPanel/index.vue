<script lang="ts" setup>
import { computed } from 'vue';
import { Alert } from 'ant-design-vue';
import { CheckCircleFilled, CloseCircleFilled } from '@ant-design/icons-vue';
import { Description, useDescription } from '@/components/Description';
import { CollapseContainer } from '@/components/Container';
import { Button } from '@/components/Button';
import type { ComputeNodeVO } from '@/api/device/node';
import { nodeSetupSummarySchema } from '../../Data';
import { getMediaStackGuideState, getMqttStackGuideState, formatNodeFunctions, SETUP_COPY, readMediaPortsFromTags, readMqttPortsFromTags, nodeHasAnyFunction, nodeHasFunction } from '../../utils/constants';
import { formatSshUsername, isSshUsernameConfigured } from '../../utils/nodeDisplay';
import SetupStepShell from '../SetupStepShell/index.vue';
import NodeMetaBadge from '../NodeMetaBadge/index.vue';

defineOptions({ name: 'SetupOverviewPanel' });

const props = withDefaults(
  defineProps<{
    node?: ComputeNodeVO | null;
    testingSsh?: boolean;
    /** 嵌入节点详情等场景：不包 SetupStepShell、不展示流程 intro */
    embedded?: boolean;
    /** 是否展示节点信息描述块（详情页已在「节点配置」中展示时可关闭） */
    showNodeInfo?: boolean;
  }>(),
  {
    embedded: false,
    showNodeInfo: true,
  },
);

const emit = defineEmits<{ edit: []; testSsh: [] }>();

const isMediaNode = computed(() => nodeHasAnyFunction(props.node, ['live', 'forward']));

const isMqttNode = computed(() => nodeHasFunction(props.node, 'mqtt'));

const mediaParams = computed(() => {
  const node = props.node;
  if (!node) return undefined;
  const tags = node.tags || {};
  return {
    nodeRole: node.nodeRole,
    functions: node.functions,
    host: node.host,
    name: node.name,
    ...readMediaPortsFromTags(tags),
  };
});

const mediaGuide = computed(() => getMediaStackGuideState(mediaParams.value));

const mqttParams = computed(() => {
  const node = props.node;
  if (!node) return undefined;
  const tags = node.tags || {};
  return {
    nodeRole: node.nodeRole,
    functions: node.functions,
    host: node.host,
    name: node.name,
    ...readMqttPortsFromTags(tags),
  };
});

const mqttGuide = computed(() => getMqttStackGuideState(mqttParams.value));

const checklist = computed(() => {
  const node = props.node;
  const items = [
    {
      key: 'host',
      label: '主机地址已填写',
      ok: !!node?.host?.trim(),
      hint: node?.host?.trim() || '未填写',
    },
    {
      key: 'sshUser',
      label: 'SSH 用户名已配置',
      ok: isSshUsernameConfigured(node),
      hint: isSshUsernameConfigured(node)
        ? formatSshUsername(node?.sshUsername, node)
        : '请在编辑节点中填写',
    },
    {
      key: 'sshTest',
      label: 'SSH 连通性',
      ok: node?.sshLastTestOk === true,
      hint:
        node?.sshLastTestOk === true
          ? '最近检测通过'
          : node?.sshLastTestOk === false
            ? '最近检测失败，请检查凭据与网络'
            : '建议先检测 SSH 连通性，确保可远程部署',
    },
  ];

  if (isMediaNode.value) {
    items.push({
      key: 'mediaPorts',
      label: SETUP_COPY.mediaPortConfigured,
      ok: mediaGuide.value.isReady,
      hint: mediaGuide.value.isReady
        ? '端口配置完整'
        : `待完善：${mediaGuide.value.pendingItems.filter((i) => !i.done).map((i) => i.label).join('、') || '端口信息'}`,
    });
  }

  if (isMqttNode.value) {
    items.push({
      key: 'mqttPorts',
      label: SETUP_COPY.mqttPortConfigured,
      ok: mqttGuide.value.isReady,
      hint: mqttGuide.value.isReady
        ? '端口配置完整'
        : `待完善：${mqttGuide.value.pendingItems.filter((i) => !i.done).map((i) => i.label).join('、') || '端口信息'}`,
    });
  }

  return items;
});

const allReady = computed(() => checklist.value.every((item) => item.ok));
const roleDesc = computed(() => formatNodeFunctions(props.node));

const flowSummary = computed(() => {
  const steps = isMqttNode.value
    ? SETUP_COPY.flowMqtt
    : isMediaNode.value
      ? SETUP_COPY.flowMedia
      : nodeHasFunction(props.node, 'nfs')
        ? SETUP_COPY.flowStorageLite
        : SETUP_COPY.flowCompute;
  return roleDesc.value ? `${steps} · ${roleDesc.value}` : steps;
});

const [registerSummary] = useDescription({
  useCollapse: false,
  bordered: true,
  column: 2,
  schema: nodeSetupSummarySchema,
  data: computed(() => props.node),
});
</script>

<template>
  <component :is="embedded ? 'div' : SetupStepShell" v-if="node" :class="{ 'setup-overview-embedded': embedded }">
    <template v-if="!embedded" #intro>
      <Alert type="info" show-icon :message="flowSummary" />
    </template>

    <CollapseContainer v-if="showNodeInfo" :title="SETUP_COPY.nodeInfo" :can-expan="false">
      <div class="setup-desc">
        <Description @register="registerSummary" />
      </div>
    </CollapseContainer>

    <CollapseContainer v-if="!embedded" :title="SETUP_COPY.preCheck" :can-expan="false">
      <template #action>
        <NodeMetaBadge type="readiness" :ready="allReady" />
      </template>

      <ul class="checklist">
        <li v-for="item in checklist" :key="item.key" :class="{ ok: item.ok }">
          <CheckCircleFilled v-if="item.ok" class="check-icon check-icon--ok" />
          <CloseCircleFilled v-else class="check-icon check-icon--fail" />
          <div class="check-body">
            <span class="check-label">{{ item.label }}</span>
            <span class="check-hint">{{ item.hint }}</span>
          </div>
        </li>
      </ul>

      <div class="checklist-actions">
        <Button @click="emit('edit')">{{ SETUP_COPY.editNode }}</Button>
        <Button type="primary" ghost :loading="testingSsh" @click="emit('testSsh')">
          {{ SETUP_COPY.sshConnectivity }}
        </Button>
      </div>
    </CollapseContainer>

    <template v-else>
      <div class="checklist-head">
        <NodeMetaBadge type="readiness" :ready="allReady" />
      </div>
      <ul class="checklist">
        <li v-for="item in checklist" :key="item.key" :class="{ ok: item.ok }">
          <CheckCircleFilled v-if="item.ok" class="check-icon check-icon--ok" />
          <CloseCircleFilled v-else class="check-icon check-icon--fail" />
          <div class="check-body">
            <span class="check-label">{{ item.label }}</span>
            <span class="check-hint">{{ item.hint }}</span>
          </div>
        </li>
      </ul>

      <div class="checklist-actions">
        <Button @click="emit('edit')">{{ SETUP_COPY.editNode }}</Button>
        <Button type="primary" ghost :loading="testingSsh" @click="emit('testSsh')">
          {{ SETUP_COPY.sshConnectivity }}
        </Button>
      </div>
    </template>
  </component>
</template>

<style lang="less" scoped>
@import '../../utils/setup-panel.less';

.checklist {
  margin: 0;
  padding: 0;
  list-style: none;
}

.checklist li {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 1px dashed #f0f0f0;

  &:first-child {
    padding-top: 2px;
  }

  &:last-child {
    border-bottom: none;
    padding-bottom: 0;
  }
}

.check-icon {
  margin-top: 2px;
  font-size: 16px;

  &--ok {
    color: #52c41a;
  }

  &--fail {
    color: #ff4d4f;
  }
}

.check-body {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.check-label {
  font-size: 14px;
  color: #262626;
}

.check-hint {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
}

.checklist-actions {
  display: flex;
  gap: 8px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.checklist-head {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 8px;
}
</style>
