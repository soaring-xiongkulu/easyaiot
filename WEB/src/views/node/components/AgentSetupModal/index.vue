<script lang="ts" setup>
import { computed, ref, watch } from 'vue';
import { Steps } from 'ant-design-vue';
import { BasicDrawer, useDrawerInner } from '@/components/Drawer';
import { BasicTitle } from '@/components/Basic';
import { Icon } from '@/components/Icon';
import { Button } from '@/components/Button';
import { useMessage } from '@/hooks/web/useMessage';
import { getAgentSetup, testNodeSsh, type ComputeNodeVO } from '@/api/device/node';
import {
  SETUP_COPY,
  SETUP_STEP_LABELS,
  NODE_TERM,
  loadNodeControlPlaneUrlAsync,
  saveNodeControlPlaneUrl,
  readMediaPortsFromTags,
  readMqttPortsFromTags,
  nodeHasAnyFunction,
  nodeHasFunction,
  formatNodeFunctions,
  primaryNodeFunction,
} from '../../utils/constants';
import NodeMetaBadge from '../NodeMetaBadge/index.vue';
import SetupOverviewPanel from '../SetupOverviewPanel/index.vue';
import MediaStackSetupPanel from '../MediaStackSetupPanel/index.vue';
import MqttStackSetupPanel from '../MqttStackSetupPanel/index.vue';
import AgentDeployPanel from '../AgentDeployPanel/index.vue';
import SetupVerifyPanel from '../SetupVerifyPanel/index.vue';

defineOptions({ name: 'AgentSetupDrawer' });

type SetupStepKey = 'overview' | 'media' | 'mqtt' | 'agent' | 'verify';

interface SetupStep {
  key: SetupStepKey;
  title: string;
  description: string;
}

const emit = defineEmits(['register', 'success', 'edit']);

const { createMessage } = useMessage();

const nodeInfo = ref<ComputeNodeVO | null>(null);
const agentToken = ref('');
const currentStep = ref(0);
const mediaDeployed = ref(false);
const mqttDeployed = ref(false);
const agentDeployed = ref(false);
const verifyOnline = ref(false);
const testingSsh = ref(false);
const controlPlaneUrl = ref('');
const skipControlPlanePersist = ref(false);

watch(controlPlaneUrl, (url) => {
  if (skipControlPlanePersist.value) return;
  if (nodeInfo.value?.id) saveNodeControlPlaneUrl(nodeInfo.value.id, url);
});

const isMediaNode = computed(() => nodeHasAnyFunction(nodeInfo.value, ['live', 'forward']));

const isMqttNode = computed(() => nodeHasFunction(nodeInfo.value, 'mqtt'));

const steps = computed<SetupStep[]>(() => {
  const list: SetupStep[] = [
    { key: 'overview', ...SETUP_STEP_LABELS.overview },
  ];
  if (isMediaNode.value) {
    list.push({ key: 'media', ...SETUP_STEP_LABELS.media });
  }
  if (isMqttNode.value) {
    list.push({ key: 'mqtt', ...SETUP_STEP_LABELS.mqtt });
  }
  list.push(
    { key: 'agent', ...SETUP_STEP_LABELS.agent },
    { key: 'verify', ...SETUP_STEP_LABELS.verify },
  );
  return list;
});

const activeStepKey = computed(() => steps.value[currentStep.value]?.key ?? 'overview');
const isFirstStep = computed(() => currentStep.value === 0);
const isLastStep = computed(() => currentStep.value === steps.value.length - 1);

const mediaFormValues = computed(() => {
  const node = nodeInfo.value;
  if (!node) return undefined;
  const tags = node.tags || {};
  return {
    nodeRole: node.nodeRole,
    functions: node.functions,
    nodeId: node.id,
    name: node.name,
    host: node.host,
    sshUsername: node.sshUsername,
    sshCredentialConfigured: node.sshCredentialConfigured,
    sshLastTestOk: node.sshLastTestOk,
    sshPort: node.sshPort,
    ...readMediaPortsFromTags(tags),
  };
});

const mqttFormValues = computed(() => {
  const node = nodeInfo.value;
  if (!node) return undefined;
  const tags = node.tags || {};
  return {
    nodeRole: node.nodeRole,
    functions: node.functions,
    nodeId: node.id,
    name: node.name,
    host: node.host,
    sshUsername: node.sshUsername,
    sshCredentialConfigured: node.sshCredentialConfigured,
    sshLastTestOk: node.sshLastTestOk,
    sshPort: node.sshPort,
    ...readMqttPortsFromTags(tags),
  };
});

const stepItems = computed(() =>
  steps.value.map((step, index) => ({
    title: step.title,
    description: step.description,
    status: getStepStatus(step.key, index),
  })),
);

function getStepStatus(key: SetupStepKey, index: number): 'wait' | 'process' | 'finish' | 'error' {
  if (index < currentStep.value) return 'finish';
  if (index === currentStep.value) return 'process';
  if (key === 'media' && mediaDeployed.value && index > currentStep.value) return 'finish';
  if (key === 'mqtt' && mqttDeployed.value && index > currentStep.value) return 'finish';
  if (key === 'agent' && agentDeployed.value && index > currentStep.value) return 'finish';
  if (key === 'verify' && verifyOnline.value) return 'finish';
  return 'wait';
}

function resetState() {
  currentStep.value = 0;
  mediaDeployed.value = false;
  mqttDeployed.value = false;
  agentDeployed.value = false;
  verifyOnline.value = false;
}

async function reloadNodeInfo(id: number) {
  try {
    const setup = await getAgentSetup(id);
    nodeInfo.value = { ...nodeInfo.value, ...setup } as ComputeNodeVO;
    if (setup?.agentToken) agentToken.value = setup.agentToken;
  } catch {
    // 保留已有节点信息
  }
}

const [registerDrawer, { closeDrawer }] = useDrawerInner(async (data) => {
  resetState();
  nodeInfo.value = data?.record ?? null;
  agentToken.value = data?.agentToken ?? data?.record?.agentToken ?? '';
  skipControlPlanePersist.value = true;
  controlPlaneUrl.value = await loadNodeControlPlaneUrlAsync(nodeInfo.value?.id);
  skipControlPlanePersist.value = false;
  if (nodeInfo.value?.status === 'online') verifyOnline.value = true;
  if (data?.resume && nodeInfo.value?.id) await reloadNodeInfo(nodeInfo.value.id);
});

function handlePrev() {
  if (!isFirstStep.value) currentStep.value -= 1;
}

function handleNext() {
  if (!isLastStep.value) currentStep.value += 1;
}

function handleClose() {
  closeDrawer();
}

function handleOpenChange(open: boolean) {
  if (!open) emit('success');
}

async function handleTestSsh() {
  if (!nodeInfo.value?.id) return;
  testingSsh.value = true;
  try {
    await testNodeSsh(nodeInfo.value.id);
    createMessage.success('SSH 连接成功');
    await reloadNodeInfo(nodeInfo.value.id);
  } catch {
    createMessage.error('SSH 连接失败，请检查用户名与认证凭据');
  } finally {
    testingSsh.value = false;
  }
}

function handleEdit() {
  if (nodeInfo.value) emit('edit', nodeInfo.value);
}

function handleMediaDeployed(success: boolean) {
  if (success) {
    mediaDeployed.value = true;
    createMessage.success(`${SETUP_COPY.mediaService}${NODE_TERM.deploy}完成，请继续${NODE_TERM.deploy}${SETUP_COPY.agentName}`);
    if (activeStepKey.value === 'media' && !isLastStep.value) currentStep.value += 1;
  }
}

function handleMqttDeployed(success: boolean) {
  if (success) {
    mqttDeployed.value = true;
    createMessage.success(`${SETUP_COPY.mqttService}${NODE_TERM.deploy}完成，请继续${NODE_TERM.deploy}${SETUP_COPY.agentName}`);
    if (activeStepKey.value === 'mqtt' && !isLastStep.value) currentStep.value += 1;
  }
}

function handleAgentDeployed(success: boolean) {
  if (success) {
    agentDeployed.value = true;
    createMessage.success(`${SETUP_COPY.agentName}${NODE_TERM.deploy}完成，请${NODE_TERM.verifyOnline}`);
    if (activeStepKey.value === 'agent' && !isLastStep.value) currentStep.value += 1;
  }
}

function handleVerifyOnline() {
  verifyOnline.value = true;
}
</script>

<template>
  <BasicDrawer
    v-bind="$attrs"
    @register="registerDrawer"
    @open-change="handleOpenChange"
    width="1400"
    placement="right"
    :showFooter="true"
    :showOkBtn="false"
    :showCancelBtn="false"
    destroy-on-close
    root-class-name="node-setup-drawer"
  >
    <template #title>
      <div class="setup-drawer-header">
        <div class="setup-drawer-header__main">
          <div class="setup-drawer-header__icon">
            <Icon icon="ant-design:cluster-outlined" :size="22" />
          </div>
          <div>
            <BasicTitle span class="setup-drawer-header__title">{{ NODE_TERM.onboardDrawer }}</BasicTitle>
            <div v-if="nodeInfo" class="setup-drawer-header__meta">
              <span>{{ nodeInfo.name }}</span>
              <span class="meta-sep">·</span>
              <span>{{ nodeInfo.host }}</span>
            </div>
          </div>
        </div>
        <div v-if="nodeInfo" class="setup-drawer-header__tags">
          <NodeMetaBadge type="status" :status="nodeInfo.status" size="lg" />
          <NodeMetaBadge type="role" :role="primaryNodeFunction(nodeInfo)" :label="formatNodeFunctions(nodeInfo)" size="lg" />
        </div>
      </div>
    </template>

    <template #footer>
      <div class="footer-buttons">
        <Button @click="handleClose">{{ verifyOnline ? SETUP_COPY.completeOnboard : '关闭' }}</Button>
        <div class="footer-nav">
          <Button v-if="!isFirstStep" @click="handlePrev">上一步</Button>
          <Button v-if="!isLastStep" type="primary" @click="handleNext">
            {{
              (activeStepKey === 'media' && !mediaDeployed)
                || (activeStepKey === 'mqtt' && !mqttDeployed)
                ? '下一步（可跳过）'
                : '下一步'
            }}
          </Button>
        </div>
      </div>
    </template>

    <div v-if="nodeInfo" class="setup-drawer-content">
      <div class="setup-steps-card">
        <Steps
          class="setup-steps"
          :current="currentStep"
          :items="stepItems"
          @change="(idx) => (currentStep = idx)"
        />
      </div>

      <div class="setup-content-card">
        <SetupOverviewPanel
          v-show="activeStepKey === 'overview'"
          :node="nodeInfo"
          :testing-ssh="testingSsh"
          @edit="handleEdit"
          @test-ssh="handleTestSsh"
        />

        <MediaStackSetupPanel
          v-show="activeStepKey === 'media'"
          :active="activeStepKey === 'media'"
          :form-values="mediaFormValues"
          @deployed="handleMediaDeployed"
        />

        <MqttStackSetupPanel
          v-show="activeStepKey === 'mqtt'"
          :active="activeStepKey === 'mqtt'"
          :form-values="mqttFormValues"
          @deployed="handleMqttDeployed"
        />

        <AgentDeployPanel
          v-show="activeStepKey === 'agent'"
          v-model:control-plane-url="controlPlaneUrl"
          :active="activeStepKey === 'agent'"
          :node="nodeInfo"
          :agent-token="agentToken"
          @deployed="handleAgentDeployed"
        />

        <SetupVerifyPanel
          v-show="activeStepKey === 'verify'"
          v-model:control-plane-url="controlPlaneUrl"
          :node-id="nodeInfo.id"
          :active="activeStepKey === 'verify'"
          :ssh-ready="
            !!nodeInfo.sshUsername?.trim() || nodeInfo.sshCredentialConfigured === true
          "
          @online="handleVerifyOnline"
        />
      </div>
    </div>
  </BasicDrawer>
</template>

<style lang="less" scoped>
@import '../../utils/setup-panel.less';

.setup-drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  width: 100%;
  padding-right: 32px;
}

.setup-drawer-header__main {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.setup-drawer-header__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, #eef4ff, #dce8ff);
  color: @node-primary;
  flex-shrink: 0;
}

.setup-drawer-header__title {
  font-size: 18px !important;
  font-weight: 600 !important;
}

.setup-drawer-header__meta {
  margin-top: 2px;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.meta-sep {
  margin: 0 6px;
}

.setup-drawer-header__tags {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
  align-items: center;
}

.setup-drawer-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 100%;
  padding: 4px 0 8px;
}

.setup-steps-card {
  padding: 16px 22px;
  border-radius: @setup-panel-radius;
  background: #fff;
  border: 1px solid rgba(0, 0, 0, 0.06);
  box-shadow: @setup-panel-shadow;
}

.setup-steps {
  :deep(.ant-steps-item) {
    flex: 1;
    min-width: 0;
  }

  :deep(.ant-steps-item-container) {
    padding-bottom: 2px;
  }

  :deep(.ant-steps-item-icon) {
    width: 28px;
    height: 28px;
    line-height: 28px;
    font-size: 13px;
    margin-inline-end: 8px !important;
  }

  :deep(.ant-steps-item-content) {
    min-height: auto;
  }

  :deep(.ant-steps-item-title) {
    font-size: 14px;
    font-weight: 500;
    line-height: 1.4;
    padding-inline-end: 10px;
  }

  :deep(.ant-steps-item-description) {
    font-size: 12px;
    line-height: 1.4;
    max-width: none;
    color: rgba(0, 0, 0, 0.45);
  }

  :deep(.ant-steps-item-tail) {
    top: 14px;
    padding: 0 6px;
  }

  :deep(.ant-steps-item-process .ant-steps-item-icon) {
    background: @node-primary;
    border-color: @node-primary;
  }
}

.setup-content-card {
  flex: 1;
}

.footer-buttons {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.footer-nav {
  display: flex;
  gap: 8px;
}
</style>

<style lang="less">
.node-setup-drawer {
  .ant-drawer-header {
    padding: 16px 24px;
    border-bottom: 1px solid #f0f0f0;
  }

  .ant-drawer-body {
    background: linear-gradient(180deg, #f7f9fc 0%, #ffffff 120px);
  }

  .scrollbar__wrap {
    padding: 20px 24px !important;
  }

  .ant-drawer-footer {
    padding: 12px 24px;
    border-top: 1px solid #f0f0f0;
    background: #fff;
  }
}
</style>
