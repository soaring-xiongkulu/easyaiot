<script lang="ts" setup>
import { computed, ref, watch } from 'vue';
import { Form, FormItem, Radio, Space } from 'ant-design-vue';
import { CodeEditor } from '@/components/CodeEditor';
import { CollapseContainer } from '@/components/Container';
import { Button } from '@/components/Button';
import { useMessage } from '@/hooks/web/useMessage';
import { copyText } from '@/utils/copyTextToClipboard';
import {
  checkStorageStackBySsh,
  checkStorageMountBySsh,
  deployStorageOsdBySsh,
  deployStorageClientBySsh,
  deployStoragePoolBySsh,
  stopStorageOsdBySsh,
  unmountStorageBySsh,
  type StorageStackCheckResult as StorageCheckData,
  type StorageMountCheckResult,
} from '@/api/device/node';
import {
  buildStorageManualContent,
  getStorageStackGuideState,
  STORAGE_STACK_DEPLOY_PENDING_STEPS,
  SETUP_COPY,
  SETUP_FORM_LABEL_COL,
  SETUP_FORM_WRAPPER_COL,
  type StorageStackScriptParams,
} from '../../utils/constants';
import { resolveDeployMessage, type DeployResultState } from '../../utils/deployLog';
import DeployProgressPanel from '../DeployProgressPanel/index.vue';
import StorageStackCheckResult from '../StorageStackCheckResult/index.vue';
import SetupStepShell from '../SetupStepShell/index.vue';

defineOptions({ name: 'StorageStackSetupPanel' });

const emit = defineEmits<{ deployed: [success: boolean] }>();

const props = defineProps<{
  active?: boolean;
  formValues?: StorageStackScriptParams & {
    nodeRole?: string;
    nodeId?: number;
    sshUsername?: string;
    sshCredentialConfigured?: boolean;
    sshLastTestOk?: boolean;
    sshPort?: number;
  };
}>();

const { createMessage } = useMessage();

type DeployMode = 'auto' | 'manual';
const deployMode = ref<DeployMode>('auto');
const deploying = ref(false);
const deployAction = ref<'osd' | 'pool' | 'client' | null>(null);
const deployResult = ref<DeployResultState | null>(null);
const deployAbort = ref<AbortController | null>(null);
const checking = ref(false);
const checkResult = ref<StorageCheckData | null>(null);
const mountChecking = ref(false);
const mountCheckResult = ref<StorageMountCheckResult | null>(null);
const storageOpLoading = ref<'stop-osd' | 'unmount' | null>(null);
const storageOpResult = ref<DeployResultState | null>(null);
const hasAutoChecked = ref(false);

const guide = computed(() => getStorageStackGuideState(props.formValues));

const canOperate = computed(
  () =>
    guide.value.isReady &&
    !!props.formValues?.nodeId &&
    (!!props.formValues?.sshUsername?.trim() || props.formValues?.sshCredentialConfigured === true),
);

const manualContent = computed(() => {
  if (!guide.value.isReady) return '';
  return buildStorageManualContent(props.formValues || {});
});

function handleCopy(text: string, label: string) {
  if (!text?.trim()) {
    createMessage.warning(`${label}为空，无法复制`);
    return;
  }
  copyText(text, `${label}已复制`);
}

function handleStopDeploy() {
  deployAbort.value?.abort();
}

async function handleCheckDeploy() {
  const nodeId = props.formValues?.nodeId;
  if (!nodeId || checking.value) return;
  checking.value = true;
  checkResult.value = null;
  try {
    checkResult.value = await checkStorageStackBySsh(nodeId);
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '检测请求失败';
    checkResult.value = { success: false, message: msg, steps: [{ name: '检测中断', status: 'failed', output: msg }] };
  } finally {
    checking.value = false;
  }
}

async function handleCheckMount() {
  const nodeId = props.formValues?.nodeId;
  if (!nodeId || mountChecking.value) return;
  mountChecking.value = true;
  mountCheckResult.value = null;
  try {
    mountCheckResult.value = await checkStorageMountBySsh(nodeId);
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '检测请求失败';
    mountCheckResult.value = { success: false, message: msg, steps: [{ name: '检测中断', status: 'failed', output: msg }] };
  } finally {
    mountChecking.value = false;
  }
}

async function runDeploy(action: 'osd' | 'pool' | 'client') {
  const nodeId = props.formValues?.nodeId;
  if (!nodeId || deploying.value) return;
  deploying.value = true;
  deployAction.value = action;
  deployResult.value = null;
  deployAbort.value = new AbortController();
  const fn =
    action === 'osd'
      ? deployStorageOsdBySsh
      : action === 'pool'
        ? deployStoragePoolBySsh
        : deployStorageClientBySsh;
  try {
    const data = await fn(nodeId, { signal: deployAbort.value.signal });
    deployResult.value = {
      success: !!data?.success,
      message: resolveDeployMessage(data || {}),
      steps: data?.steps || [],
    };
    emit('deployed', !!deployResult.value.success);
    if (data?.success) checkResult.value = null;
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '部署请求失败';
    deployResult.value = { success: false, message: msg, steps: [{ name: '部署中断', status: 'failed', output: msg }] };
    emit('deployed', false);
  } finally {
    deploying.value = false;
    deployAction.value = null;
    deployAbort.value = null;
  }
}

async function runStorageOp(op: 'stop-osd' | 'unmount', request: () => Promise<{ success?: boolean; message?: string; steps?: DeployResultState['steps'] }>, okMsg: string) {
  const nodeId = props.formValues?.nodeId;
  if (!nodeId || storageOpLoading.value) return;
  storageOpLoading.value = op;
  storageOpResult.value = null;
  try {
    const data = await request();
    storageOpResult.value = {
      success: !!data?.success,
      message: resolveDeployMessage(data || {}),
      steps: data?.steps || [],
    };
    if (data?.success) createMessage.success(okMsg);
    else createMessage.error(storageOpResult.value.message || '操作失败');
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '操作失败';
    storageOpResult.value = { success: false, message: msg, steps: [{ name: '操作中断', status: 'failed', output: msg }] };
    createMessage.error(msg);
  } finally {
    storageOpLoading.value = null;
  }
}

function handleStopOsd() {
  const nodeId = props.formValues?.nodeId;
  if (!nodeId) return;
  runStorageOp('stop-osd', () => stopStorageOsdBySsh(nodeId), 'OSD 服务已停止');
}

function handleUnmount() {
  const nodeId = props.formValues?.nodeId;
  if (!nodeId) return;
  runStorageOp('unmount', () => unmountStorageBySsh(nodeId), 'CephFS 已卸载');
}

watch(
  () => [props.active, props.formValues?.nodeId, canOperate.value] as const,
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
  <SetupStepShell v-if="guide.isStorageRole">
    <CollapseContainer v-if="guide.isReady" :title="SETUP_COPY.deployConfig" :can-expan="false">
      <Form :label-col="SETUP_FORM_LABEL_COL" :wrapper-col="SETUP_FORM_WRAPPER_COL" class="setup-resource-form">
        <FormItem :label="SETUP_COPY.deployMode">
          <Radio.Group v-model:value="deployMode">
            <Radio value="auto">{{ SETUP_COPY.deployModeAuto }}</Radio>
            <Radio value="manual">{{ SETUP_COPY.deployModeManual }}</Radio>
          </Radio.Group>
        </FormItem>

        <FormItem label="NFS 健康检测">
          <Space wrap>
            <Button :loading="checking" :disabled="!canOperate || deploying" @click="handleCheckDeploy">
              {{ SETUP_COPY.deployCheck }}
            </Button>
            <Button :loading="mountChecking" :disabled="!canOperate || deploying" @click="handleCheckMount">
              检测 NFS 挂载
            </Button>
          </Space>
          <StorageStackCheckResult v-if="canOperate && checkResult" :result="checkResult" @close="checkResult = null" />
          <div v-else-if="mountCheckResult" class="form-hint">
            {{ mountCheckResult.message || (mountCheckResult.mountReady ? 'NFS 已挂载' : 'NFS 未挂载') }}
          </div>
        </FormItem>

        <template v-if="deployMode === 'auto'">
          <FormItem :label="SETUP_COPY.remoteDeploy">
            <Space wrap>
              <Button type="primary" :loading="deploying && deployAction === 'pool'" :disabled="!canOperate || deploying" @click="runDeploy('pool')">
                初始化 Export
              </Button>
              <Button :loading="deploying && deployAction === 'osd'" :disabled="!canOperate || deploying" @click="runDeploy('osd')">
                安装 NFS 服务端
              </Button>
              <Button :loading="deploying && deployAction === 'client'" :disabled="!canOperate || deploying" @click="runDeploy('client')">
                挂载 NFS 客户端
              </Button>
              <Button v-if="deploying" danger @click="handleStopDeploy">停止部署</Button>
            </Space>
          </FormItem>

          <FormItem :label="SETUP_COPY.ops">
            <Space wrap>
              <Button :loading="storageOpLoading === 'stop-osd'" :disabled="!canOperate || deploying || !!storageOpLoading" @click="handleStopOsd">
                停止 OSD
              </Button>
              <Button danger :loading="storageOpLoading === 'unmount'" :disabled="!canOperate || deploying || !!storageOpLoading" @click="handleUnmount">
                卸载 CephFS
              </Button>
            </Space>
          </FormItem>
        </template>

        <FormItem v-else :label="SETUP_COPY.deployScript">
          <div class="script-toolbar">
            <Button size="small" preIcon="tdesign:copy-filled" @click="handleCopy(manualContent, SETUP_COPY.deployScript)">
              复制全部步骤
            </Button>
          </div>
          <CodeEditor class="script-editor script-editor--manual" :value="manualContent" readonly bordered />
        </FormItem>
      </Form>
    </CollapseContainer>

    <CollapseContainer
      v-if="deployMode === 'auto' && guide.isReady && (deploying || deployResult || storageOpLoading || storageOpResult)"
      :title="SETUP_COPY.deployProgress"
      :can-expan="false"
    >
      <DeployProgressPanel
        :loading="deploying || !!storageOpLoading"
        :result="deployResult || storageOpResult"
        :pending-steps="[...STORAGE_STACK_DEPLOY_PENDING_STEPS]"
        :show-stop="deploying"
        @stop="handleStopDeploy"
      />
    </CollapseContainer>
  </SetupStepShell>
</template>

<style lang="less" scoped>
@import '../../utils/setup-panel.less';

.pending-list {
  margin: 4px 0 0;
  padding-left: 18px;
  font-size: @node-font-caption;

  li {
    line-height: 1.8;
    color: @node-text-secondary;

    &.done {
      color: @node-text-muted;
      text-decoration: line-through;
    }
  }
}
</style>
