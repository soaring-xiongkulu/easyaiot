<script lang="ts" setup>
import { computed, h, ref, watch } from 'vue';
import { Alert, Divider, Form, FormItem, Input, Radio, Space } from 'ant-design-vue';
import { CodeEditor } from '@/components/CodeEditor';
import { Description, useDescription } from '@/components/Description';
import type { DescItem } from '@/components/Description';
import { CollapseContainer } from '@/components/Container';
import { Icon } from '@/components/Icon';
import { Button } from '@/components/Button';
import { useMessage } from '@/hooks/web/useMessage';
import { copyText } from '@/utils/copyTextToClipboard';
import {
  checkAgentBySsh,
  checkAgentPortBySsh,
  deployAgentBySsh,
  removeAgentBySsh,
  stopAgentBySsh,
  type ComputeNodeVO,
  type PortCheckResult as PortCheckData,
} from '@/api/device/node';
import {
  AGENT_INSTALL_DIR,
  buildAgentDeployScript,
  buildAgentEnvContent,
  isLocalControlPlaneUrl,
  SETUP_COPY,
  NODE_TERM,
  SETUP_FORM_LABEL_COL,
  SETUP_FORM_WRAPPER_COL,
} from '../../utils/constants';
import { resolveDeployMessage, type DeployResultState } from '../../utils/deployLog';
import AgentCheckResult from '../AgentCheckResult/index.vue';
import DeployProgressPanel from '../DeployProgressPanel/index.vue';
import PortCheckResult from '../PortCheckResult/index.vue';
import SetupStepShell from '../SetupStepShell/index.vue';

defineOptions({ name: 'AgentDeployPanel' });

const props = defineProps<{
  node?: ComputeNodeVO | null;
  agentToken?: string;
  active?: boolean;
}>();

const controlPlaneUrl = defineModel<string>('controlPlaneUrl', { required: true });

const emit = defineEmits<{ deployed: [success: boolean] }>();

const { createMessage } = useMessage();

type DeployMode = 'auto' | 'manual';
const deployMode = ref<DeployMode>('auto');
const showAdvanced = ref(false);
const deploying = ref(false);
const deployResult = ref<DeployResultState | null>(null);
const checking = ref(false);
const checkResult = ref<Awaited<ReturnType<typeof checkAgentBySsh>> | null>(null);
const portChecking = ref(false);
const portCheckResult = ref<PortCheckData | null>(null);
const agentOpLoading = ref<'stop' | 'remove' | null>(null);
const agentOpResult = ref<DeployResultState | null>(null);
const hasAutoChecked = ref(false);

const agentExists = computed(() => {
  const r = checkResult.value;
  if (!r?.success) return false;
  return !!(r.deployed || r.serviceRunning || r.installDirReady);
});

const deployPendingSteps = computed(() =>
  agentExists.value
    ? [`停止${NODE_TERM.agent}`, `删除${NODE_TERM.agent}`, 'SSH 连接', '端口占用检测', '准备离线 pip 包', 'Python 运行时', '同步文件', '部署启动', '服务验证']
    : ['SSH 连接', '端口占用检测', '准备离线 pip 包', 'Python 运行时', '同步文件', '部署启动', '服务验证'],
);

const deployBtnLabel = computed(() =>
  agentExists.value ? SETUP_COPY.redeployAgentBtn : SETUP_COPY.deployAgentBtn,
);

const deployHint = computed(() => {
  if (autoDisabledReason.value) return autoDisabledReason.value;
  if (agentExists.value) return SETUP_COPY.redeployAgentHint;
  return `通过 SSH 连接 ${props.node?.host}，自动同步并部署至 ${AGENT_INSTALL_DIR}`;
});

const agentParams = computed(() => ({
  id: props.node?.id,
  agentPort: props.node?.agentPort,
  agentToken: props.agentToken || props.node?.agentToken,
  host: props.node?.host,
  controlPlaneUrl: controlPlaneUrl.value,
  functions: props.node?.functions,
  nodeRole: props.node?.nodeRole,
}));

const envContent = computed(() =>
  buildAgentEnvContent({
    ...agentParams.value,
    controlPlaneUrl: controlPlaneUrl.value,
  }),
);
const deployScript = computed(() =>
  buildAgentDeployScript({
    ...agentParams.value,
    controlPlaneUrl: controlPlaneUrl.value,
  }),
);
const tokenValue = computed(() => props.agentToken || props.node?.agentToken || '');

const credentialData = computed(() => ({
  nodeId: props.node?.id,
  agentToken: tokenValue.value,
  controlPlaneUrl: controlPlaneUrl.value,
}));

const controlPlaneLocalhostWarn = computed(() => isLocalControlPlaneUrl(controlPlaneUrl.value));

const canCheckDeploy = computed(
  () => !!props.node?.id && (!!props.node?.sshUsername?.trim() || props.node?.sshCredentialConfigured === true),
);

const canAutoDeploy = computed(() => canCheckDeploy.value);

const autoDisabledReason = computed(() => {
  if (!props.node?.id) return '请先保存节点信息';
  if (!props.node?.sshUsername?.trim() && props.node?.sshCredentialConfigured !== true) {
    return '请先在节点配置中填写 SSH 用户名及认证凭据';
  }
  return '';
});

function handleCopy(text: string, label: string) {
  if (!text?.trim()) {
    createMessage.warning(`${label}为空，无法复制`);
    return;
  }
  copyText(text, `${label}已复制`);
}

function renderCopyIcon(text: string, label: string) {
  return h(Icon, {
    icon: 'tdesign:copy-filled',
    class: 'copy-icon',
    onClick: () => handleCopy(text, label),
  });
}

const credentialSchema: DescItem[] = [
  {
    field: 'nodeId',
    label: '节点 ID',
    render: (val) =>
      h('span', { class: 'mono-text' }, [val ?? '-', renderCopyIcon(String(val ?? ''), '节点 ID')]),
  },
  {
    field: 'agentToken',
    label: '访问令牌',
    span: 2,
    render: (val) =>
      h('span', { class: 'mono-text mono-text--ellipsis', title: val }, [
        val || '未生成',
        val ? renderCopyIcon(String(val), '访问令牌') : null,
      ]),
  },
  {
    field: 'controlPlaneUrl',
    label: NODE_TERM.platformUrl,
    span: 2,
    render: (val) =>
      h('span', { class: 'mono-text' }, [val, renderCopyIcon(String(val ?? ''), NODE_TERM.platformUrl)]),
  },
];

const [registerCredentialDesc] = useDescription({
  useCollapse: false,
  column: 2,
  schema: credentialSchema,
  data: credentialData,
});

async function handleCheckDeploy() {
  const nodeId = props.node?.id;
  if (!nodeId || checking.value) return;
  checking.value = true;
  checkResult.value = null;
  try {
    checkResult.value = await checkAgentBySsh(nodeId, controlPlaneUrl.value);
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '检测请求失败';
    checkResult.value = {
      success: false,
      message: msg,
      steps: [{ name: '检测中断', status: 'failed', output: msg }],
    };
  } finally {
    checking.value = false;
  }
}

async function handleCheckPorts() {
  const nodeId = props.node?.id;
  if (!nodeId || portChecking.value) return;
  portChecking.value = true;
  portCheckResult.value = null;
  try {
    portCheckResult.value = await checkAgentPortBySsh(nodeId);
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '检测请求失败';
    portCheckResult.value = {
      success: false,
      portsReady: false,
      message: msg,
      steps: [{ name: '检测中断', status: 'failed', output: msg }],
    };
  } finally {
    portChecking.value = false;
  }
}

async function runAgentOp(
  op: 'stop' | 'remove',
  request: () => Promise<{ success?: boolean; message?: string; steps?: DeployResultState['steps'] }>,
  successMsg: string,
) {
  const nodeId = props.node?.id;
  if (!nodeId || agentOpLoading.value) return;
  agentOpLoading.value = op;
  agentOpResult.value = null;
  try {
    const data = await request();
    agentOpResult.value = {
      success: !!data?.success,
      message: resolveDeployMessage(data || {}),
      steps: data?.steps || [],
    };
    if (data?.success) {
      createMessage.success(successMsg);
      checkResult.value = null;
    } else {
      createMessage.error(agentOpResult.value.message || '操作失败');
    }
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '操作请求失败';
    agentOpResult.value = {
      success: false,
      message: msg,
      steps: [{ name: '操作中断', status: 'failed', output: msg }],
    };
    createMessage.error(msg);
  } finally {
    agentOpLoading.value = null;
  }
}

function handleStopAgent() {
  const nodeId = props.node?.id;
  if (!nodeId) return;
  runAgentOp('stop', () => stopAgentBySsh(nodeId), `${NODE_TERM.agent}已停止`);
}

function handleRemoveAgent() {
  const nodeId = props.node?.id;
  if (!nodeId) return;
  runAgentOp('remove', () => removeAgentBySsh(nodeId), `${NODE_TERM.agent}已删除`);
}

async function handleAutoDeploy() {
  const nodeId = props.node?.id;
  if (!nodeId || deploying.value) return;
  if (agentExists.value) {
    await handleRedeployAgent();
    return;
  }
  await runDeploy(nodeId);
}

async function handleRedeployAgent() {
  const nodeId = props.node?.id;
  if (!nodeId || deploying.value) return;
  deploying.value = true;
  deployResult.value = null;
  agentOpResult.value = null;
  const mergedSteps: NonNullable<DeployResultState['steps']> = [];
  let message = '';

  try {
    const stopData = await stopAgentBySsh(nodeId);
    mergedSteps.push(...(stopData.steps || []));
    if (!stopData.success) {
      message = resolveDeployMessage(stopData);
    }

    const removeData = await removeAgentBySsh(nodeId);
    mergedSteps.push(...(removeData.steps || []));
    if (!removeData.success) {
      message = message || resolveDeployMessage(removeData);
    }

    const deployData = await deployAgentBySsh(nodeId, controlPlaneUrl.value);
    mergedSteps.push(...(deployData.steps || []));
    const success = !!deployData.success;
    message = success ? resolveDeployMessage(deployData) : resolveDeployMessage(deployData) || message;

    deployResult.value = { success, message, steps: mergedSteps };
    emit('deployed', success);
    if (success) {
      createMessage.success(`${NODE_TERM.agent}${NODE_TERM.redeploy}完成`);
      await handleCheckDeploy();
    } else {
      createMessage.error(message || '重新部署失败');
    }
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '重新部署请求失败';
    deployResult.value = {
      success: false,
      message: msg,
      steps: [...mergedSteps, { name: '重新部署中断', status: 'failed', output: msg }],
    };
    emit('deployed', false);
    createMessage.error(msg);
  } finally {
    deploying.value = false;
  }
}

async function runDeploy(nodeId: number) {
  deploying.value = true;
  deployResult.value = null;
  try {
    const data = await deployAgentBySsh(nodeId, controlPlaneUrl.value);
    deployResult.value = {
      success: !!data?.success,
      message: resolveDeployMessage(data || {}),
      steps: data?.steps || [],
    };
    emit('deployed', !!deployResult.value.success);
    if (deployResult.value.success) {
      await handleCheckDeploy();
    }
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '部署请求失败';
    deployResult.value = {
      success: false,
      message: msg,
      steps: [{ name: '部署中断', status: 'failed', output: msg }],
    };
    emit('deployed', false);
  } finally {
    deploying.value = false;
  }
}

watch(
  () => [props.active, props.node?.id, canCheckDeploy.value] as const,
  ([active, nodeId, canCheck]) => {
    if (!active) {
      hasAutoChecked.value = false;
      return;
    }
    if (active && nodeId && canCheck && !hasAutoChecked.value) {
      hasAutoChecked.value = true;
      handleCheckDeploy();
    }
  },
  { immediate: true },
);
</script>

<template>
  <SetupStepShell v-if="node">
    <CollapseContainer :title="SETUP_COPY.deployConfig" :can-expan="false">
      <Form
        :label-col="SETUP_FORM_LABEL_COL"
        :wrapper-col="SETUP_FORM_WRAPPER_COL"
        class="setup-resource-form"
      >
        <FormItem :label="SETUP_COPY.deployMode">
          <Radio.Group v-model:value="deployMode">
            <Radio value="auto">{{ SETUP_COPY.deployModeAuto }}</Radio>
            <Radio value="manual">{{ SETUP_COPY.deployModeManual }}</Radio>
          </Radio.Group>
        </FormItem>

        <FormItem :label="SETUP_COPY.verifyExpectedUrl">
          <Input
            v-model:value="controlPlaneUrl"
            placeholder="http://平台IP:48080/admin-api/node/agent"
            allow-clear
          />
          <Alert
            v-if="controlPlaneLocalhostWarn"
            type="warning"
            show-icon
            class="control-plane-warn"
            :message="`${NODE_TERM.platformUrl}含 localhost，远程${NODE_TERM.agent}无法访问。请填写目标服务器能访问到的平台 Gateway 地址。`"
          />
          <div v-else class="form-hint">
            写入 agent.env 的 CONTROL_PLANE_URL，需为目标服务器可达的平台地址（通常为 Gateway IP:48080）
          </div>
        </FormItem>

        <FormItem :label="SETUP_COPY.agentPortCheck">
          <Space wrap>
            <Button
              :loading="portChecking"
              :disabled="!canCheckDeploy || deploying || !!agentOpLoading || checking"
              @click="handleCheckPorts"
            >
              {{ SETUP_COPY.checkAgentPortBtn }}
            </Button>
          </Space>
          <div v-if="!canCheckDeploy" class="form-hint">{{ autoDisabledReason || '请先保存节点并配置 SSH' }}</div>
          <PortCheckResult v-else-if="portCheckResult" :result="portCheckResult" @close="portCheckResult = null" />
          <div v-else class="form-hint">
            检测监测代理监听端口（agentPort）是否被其他进程占用
          </div>
        </FormItem>

        <FormItem :label="SETUP_COPY.agentDeployCheck">
          <Space wrap>
            <Button :loading="checking" :disabled="!canCheckDeploy || deploying || !!agentOpLoading" @click="handleCheckDeploy">
              {{ SETUP_COPY.checkAgentDeployBtn }}
            </Button>
          </Space>
          <div v-if="!canCheckDeploy" class="form-hint">{{ autoDisabledReason || '请先保存节点并配置 SSH' }}</div>
          <AgentCheckResult v-else-if="checkResult" :result="checkResult" @close="checkResult = null" />
          <div v-else class="form-hint">
            通过 SSH 探测目标机安装目录、systemd 服务与健康检查，不会修改目标机
          </div>
        </FormItem>

        <template v-if="deployMode === 'auto'">
          <FormItem :label="SETUP_COPY.remoteDeploy">
            <Space wrap>
              <Button
                type="primary"
                :loading="deploying"
                :disabled="!canAutoDeploy || !!agentOpLoading"
                @click="handleAutoDeploy"
              >
                {{ deployBtnLabel }}
              </Button>
            </Space>
            <div class="form-hint">
              {{ deployHint }}
            </div>
            <div v-if="canAutoDeploy" class="form-hint">
              部署前将自动检测目标机 Agent 监听端口是否可用
            </div>
          </FormItem>

          <FormItem :label="SETUP_COPY.agentOps">
            <Space wrap>
              <Button
                :loading="agentOpLoading === 'stop'"
                :disabled="!canCheckDeploy || deploying || !!agentOpLoading"
                @click="handleStopAgent"
              >
                {{ SETUP_COPY.stopAgentBtn }}
              </Button>
              <Button
                danger
                :loading="agentOpLoading === 'remove'"
                :disabled="!canCheckDeploy || deploying || !!agentOpLoading"
                @click="handleRemoveAgent"
              >
                {{ SETUP_COPY.removeAgentBtn }}
              </Button>
            </Space>
            <div v-if="!canCheckDeploy" class="form-hint">{{ autoDisabledReason || '请先保存节点并配置 SSH' }}</div>
            <div v-else class="form-hint">
              通过 SSH 在目标机执行停止/删除操作；停止仅终止服务，删除会移除 systemd 单元及 {{ AGENT_INSTALL_DIR }} 安装目录
            </div>
          </FormItem>
        </template>

        <template v-else>
          <FormItem :label="SETUP_COPY.deployScript">
            <div class="script-toolbar">
              <Button size="small" preIcon="tdesign:copy-filled" @click="handleCopy(deployScript, SETUP_COPY.deployScript)">
                复制
              </Button>
            </div>
            <CodeEditor class="script-editor script-editor--manual" :value="deployScript" readonly bordered />
            <div class="form-hint">
              请在本机（平台服务器）执行 rsync 同步，再 SSH 登录目标主机运行脚本中的安装命令
            </div>
          </FormItem>
        </template>

        <FormItem :label="SETUP_COPY.credentials">
          <Button type="link" size="small" class="advanced-toggle" @click="showAdvanced = !showAdvanced">
            {{ showAdvanced ? '收起' : '查看' }}{{ SETUP_COPY.credentials }}
          </Button>
        </FormItem>
      </Form>
    </CollapseContainer>

    <CollapseContainer v-if="showAdvanced" :title="SETUP_COPY.credentials" :can-expan="false">
      <div class="setup-desc">
        <Description @register="registerCredentialDesc" />
      </div>
      <Divider orientation="left">agent.env</Divider>
      <div class="env-block">
        <div class="script-toolbar">
          <Button size="small" preIcon="tdesign:copy-filled" @click="handleCopy(envContent, 'agent.env')">
            复制 agent.env
          </Button>
        </div>
        <CodeEditor class="env-editor" :value="envContent" readonly bordered />
        <div class="form-hint">保存为 agent.env，供{{ SETUP_COPY.agentName }}读取接入配置</div>
      </div>
    </CollapseContainer>

    <CollapseContainer
      v-if="deployMode === 'auto' && (deploying || deployResult || agentOpLoading || agentOpResult)"
      :title="SETUP_COPY.deployProgress"
      :can-expan="false"
    >
      <DeployProgressPanel
        :loading="deploying || !!agentOpLoading"
        :result="deployResult || agentOpResult"
        :pending-steps="deployPendingSteps"
      />
    </CollapseContainer>
  </SetupStepShell>
</template>

<style lang="less" scoped>
@import '../../utils/setup-panel.less';

.advanced-toggle {
  padding-left: 0;
  height: auto;
  margin-top: 4px;
}

.control-plane-warn {
  margin-top: 8px;
}

.env-editor {
  height: 200px;
}

.env-block {
  margin-top: 4px;
}

:deep(.mono-text) {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-family: Consolas, 'Courier New', monospace;
  font-size: 13px;
  word-break: break-all;

  &--ellipsis {
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

:deep(.copy-icon) {
  flex-shrink: 0;
  cursor: pointer;
  color: #4287fc;
  font-size: 15px;

  &:hover {
    color: #1677ff;
  }
}
</style>
