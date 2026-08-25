<template>
  <Spin :spinning="state.scanning || state.registering">
    <DeviceCreatePanelLayout result-title="扫描结果">
      <template #form>
        <BasicForm @register="registerForm">
          <template #targets="{ model, field }">
            <SegmentScanTargetsField
              :value="String(model?.[field] ?? '')"
              :mode="state.mode"
              :disabled="state.scanning || state.registering"
              :refresh-token="historyRefreshToken"
              @update:value="(v) => setFieldsValue({ [field]: v })"
              @apply-history="applyHistoryEntry"
            />
          </template>
          <template #credentials>
            <div class="credentials-block">
              <div v-for="(cred, idx) in credentials" :key="idx" class="credential-row">
                <Input
                  v-model:value="cred.username"
                  placeholder="用户名"
                  :disabled="state.scanning"
                  class="cred-user"
                  allow-clear
                />
                <Input.Password
                  v-model:value="cred.password"
                  :placeholder="state.mode === 'nvr' ? '密码（必填）' : '密码'"
                  :disabled="state.scanning"
                  class="cred-pass"
                  allow-clear
                />
                <Button
                  type="link"
                  danger
                  size="small"
                  :disabled="state.scanning || credentials.length <= 1"
                  @click="removeCredential(idx)"
                >
                  删除
                </Button>
              </div>
              <Button type="dashed" block :disabled="state.scanning" @click="addCredential">添加凭证</Button>
            </div>
          </template>
        </BasicForm>
      </template>
      <template #actions>
        <Button type="primary" :loading="state.scanning" preIcon="ant-design:search-outlined" @click="handleScan">
          开始跨网段扫描
        </Button>
        <span v-if="state.scanProgress" class="dc-action-tip">{{ state.scanProgress }}</span>
      </template>
      <template v-if="state.devices.length" #resultExtra>
        <Button
          type="primary"
          :loading="state.batchRegistering"
          :disabled="registrableCount === 0"
          @click="handleBatchRegister"
        >
          {{ batchRegisterButtonText }}
        </Button>
        <span v-if="state.batchProgress" class="dc-action-tip">{{ state.batchProgress }}</span>
      </template>
      <template #result>
        <Table
          v-if="state.devices.length"
          :columns="mode === 'camera' ? cameraColumns : nvrColumns"
          :data-source="state.devices"
          :pagination="tablePagination"
          :scroll="{ x: 1000, y: 300 }"
          row-key="ip"
          size="small"
          bordered
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.dataIndex === 'register_status'">
              <Tag :color="registerStatusColor(record.ip)">{{ registerStatusLabel(record.ip, record) }}</Tag>
            </template>
            <template v-else-if="column.dataIndex === 'action'">
              <Button
                type="link"
                size="small"
                :disabled="!canRegisterRecord(record)"
                :loading="state.registeringIp === record.ip"
                @click="mode === 'nvr' ? handleRegisterNvr(record) : handleRegisterCamera(record)"
              >
                {{ mode === 'nvr' ? '登记' : '注册' }}
              </Button>
            </template>
          </template>
        </Table>
        <Empty v-else description="填写扫描参数并点击「开始跨网段扫描」" />
      </template>
    </DeviceCreatePanelLayout>
  </Spin>
</template>

<script lang="ts" setup>
import { computed, nextTick, reactive, ref, watch } from 'vue';
import { Empty, Input, Spin, Table, Tag } from 'ant-design-vue';
import { BasicForm, useForm } from '@/components/Form';
import { Button } from '@/components/Button';
import { useMessage } from '@/hooks/web/useMessage';
import DeviceCreatePanelLayout from '../DeviceCreatePanelLayout.vue';
import SegmentScanTargetsField from '../SegmentScanTargetsField.vue';
import { SEGMENT_SCAN_TARGETS_PLACEHOLDER } from '../segmentScanGuide';
import {
  DEVICE_CREATE_COL_LINE,
  DEVICE_CREATE_FORM_GRID,
  DEVICE_CREATE_NUMBER_PROPS,
} from '../deviceCreateForm';
import {
  registerDevice,
  registerNvrWithChannels,
  scanSegmentDevices,
  type CredentialPair,
  type NvrInfo,
  type SegmentScanDeviceRow,
} from '@/api/device/camera';
import { getCameraScanColumns, getNvrScanColumns } from '@/views/camera/components/SegmentScanModal/Data';
import {
  hasSegmentScanRegisterPayload,
  isSegmentScanCredentialAccessible,
  resolveSegmentScanRtsp,
} from '@/views/camera/utils/segmentScanRegister';
import {
  cloneCredentials,
  saveSegmentScanHistory,
  type SegmentScanHistoryEntry,
} from '@/views/camera/utils/segmentScanHistory';
import {
  formatNvrRegisterHint,
  nvrRegisterRegisteredCount,
} from '@/views/camera/utils/nvrRegisterMessage';
import {
  computeSegmentScanWallSeconds,
  segmentScanTargetsFormRule,
  validateSegmentScanTargets,
} from '@/views/camera/utils/segmentScanTargetsValidate';

const props = defineProps<{ mode?: 'camera' | 'nvr'; ingressNodeId?: number }>();
const emit = defineEmits<{ success: [] }>();

const { createMessage } = useMessage();

type RegisterStatus = 'idle' | 'success' | 'failed' | 'skipped';

const state = reactive({
  mode: 'camera' as 'camera' | 'nvr',
  scanning: false,
  registering: false,
  batchRegistering: false,
  registeringIp: '' as string,
  devices: [] as SegmentScanDeviceRow[],
  scanProgress: '',
  batchProgress: '',
  registerStatusMap: {} as Record<string, RegisterStatus>,
});

const credentials = reactive<CredentialPair[]>([{ username: 'admin', password: '' }]);
const historyRefreshToken = ref(0);

const [registerForm, { validate, getFieldsValue, setFieldsValue, updateSchema }] = useForm({
  ...DEVICE_CREATE_FORM_GRID,
  schemas: [
    {
      field: 'targets',
      label: '目标网段 / IP',
      component: 'InputTextArea',
      slot: 'targets',
      required: true,
      colProps: { ...DEVICE_CREATE_COL_LINE, class: 'segment-scan-targets' },
      componentProps: {
        autoSize: { minRows: 3, maxRows: 8 },
        placeholder: SEGMENT_SCAN_TARGETS_PLACEHOLDER,
      },
      rules: [
        segmentScanTargetsFormRule(() => String(getFieldsValue().ports || '').trim() || undefined),
      ],
    },
    {
      field: 'ports',
      label: 'Web 端口',
      component: 'Input',
      defaultValue: '80,443,8000,8443',
    },
    {
      field: '_credentials',
      label: '登录凭证',
      component: 'Input',
      colProps: { ...DEVICE_CREATE_COL_LINE, class: 'segment-scan-credentials' },
      slot: 'credentials',
      itemProps: { autoLink: false },
      rules: [],
      dynamicRules: () => {
        if (state.mode === 'nvr') {
          const validCreds = credentials
            .map((c) => ({ username: (c.username || '').trim(), password: c.password || '' }))
            .filter((c) => c.username);
          if (validCreds.length === 0) {
            return [{ required: true, message: '请至少填写一组登录凭证' }];
          }
          if (!validCreds.some((c) => !!c.password)) {
            return [{ required: true, message: '登记 NVR 须填写 Web 登录密码' }];
          }
        }
        return [];
      },
    },
    {
      field: 'concurrency',
      label: '并发数',
      component: 'InputNumber',
      defaultValue: 200,
      componentProps: { min: 1, max: 2000, ...DEVICE_CREATE_NUMBER_PROPS },
    },
    {
      field: 'timeout',
      label: '单点超时(秒)',
      component: 'InputNumber',
      defaultValue: 3,
      helpMessage:
        '每个 IP+端口探测的最长等待时间；网段过大时会提示缩小范围。请求总时长将按目标数量自动估算（约 45 秒–5 分钟）',
      componentProps: { min: 0.5, max: 30, step: 0.5, ...DEVICE_CREATE_NUMBER_PROPS },
    },
    {
      field: 'only_hits',
      label: '结果过滤',
      component: 'Switch',
      defaultValue: true,
      componentProps: {
        checkedChildren: '已识别',
        unCheckedChildren: '全部',
      },
    },
  ],
});

watch(
  () => props.mode,
  async (m) => {
    state.mode = m || 'camera';
    state.devices = [];
    resetCredentials();
    resetRegisterStatus();
    await nextTick();
    try {
      await updateSchema([
        {
          field: '_credentials',
          label: state.mode === 'nvr' ? 'Web 登录凭证' : '登录凭证',
          helpMessage:
            state.mode === 'nvr'
              ? '登记 NVR 及枚举通道须填写正确密码；按列表顺序依次尝试'
              : undefined,
        },
      ]);
    } catch {
      /* 表单尚未挂载（immediate 首次触发） */
    }
  },
  { immediate: true },
);

watch(
  () => props.ingressNodeId,
  () => {
    state.devices = [];
    resetRegisterStatus();
  },
);

watch(
  () => state.scanning,
  (scanning) => {
    updateSchema([
      {
        field: 'targets',
        componentProps: {
          disabled: scanning,
          autoSize: { minRows: 3, maxRows: 8 },
          placeholder: SEGMENT_SCAN_TARGETS_PLACEHOLDER,
        },
      },
      { field: 'ports', componentProps: { disabled: scanning } },
      {
        field: 'concurrency',
        componentProps: { disabled: scanning, min: 1, max: 2000, ...DEVICE_CREATE_NUMBER_PROPS },
      },
      {
        field: 'timeout',
        componentProps: { disabled: scanning, min: 0.5, max: 60, step: 0.5, ...DEVICE_CREATE_NUMBER_PROPS },
      },
      { field: 'only_hits', componentProps: { disabled: scanning } },
    ]);
  },
);

const mode = computed(() => state.mode);
const cameraColumns = getCameraScanColumns();
const nvrColumns = getNvrScanColumns();
const tablePagination = {
  pageSize: 10,
  size: 'small' as const,
  showSizeChanger: false,
  showTotal: (total: number) => `共 ${total} 条`,
};

function getValidCredentials(): CredentialPair[] {
  return credentials
    .map((c) => ({ username: (c.username || '').trim(), password: c.password || '' }))
    .filter((c) => c.username);
}

function hasNvrRegisterPassword(): boolean {
  return getValidCredentials().some((c) => !!c.password);
}

function resetCredentials() {
  credentials.splice(0, credentials.length, { username: 'admin', password: '' });
}

function applyHistoryEntry(entry: SegmentScanHistoryEntry) {
  setFieldsValue({
    targets: entry.targets,
    ports: entry.ports,
    concurrency: entry.concurrency,
    timeout: entry.timeout,
    only_hits: entry.only_hits,
  });
  const creds = cloneCredentials(entry.credentials);
  credentials.splice(0, credentials.length, ...(creds.length ? creds : [{ username: 'admin', password: '' }]));
  state.devices = [];
  resetRegisterStatus();
}

function persistScanHistory(values: Record<string, unknown>, creds: CredentialPair[], deviceCount: number) {
  saveSegmentScanHistory({
    mode: state.mode,
    targets: String(values.targets || '').trim(),
    ports: String(values.ports || '').trim() || '80,443,8000,8443',
    credentials: creds,
    concurrency: Number(values.concurrency) || 200,
    timeout: Number(values.timeout) || 3,
    only_hits: !!values.only_hits,
    lastDeviceCount: deviceCount,
  });
  historyRefreshToken.value += 1;
}

function addCredential() {
  credentials.push({ username: '', password: '' });
}

function removeCredential(index: number) {
  if (credentials.length <= 1) return;
  credentials.splice(index, 1);
}

function resolveCredential(authUsername: string | undefined, credentials: CredentialPair[]): CredentialPair {
  if (authUsername) {
    const found = credentials.find((c) => c.username === authUsername);
    if (found) return found;
  }
  return credentials[0];
}

function hasFormCredentials(): boolean {
  return getValidCredentials().length > 0;
}

function isCredentialAccessible(record: SegmentScanDeviceRow): boolean {
  return isSegmentScanCredentialAccessible(record, state.mode, hasFormCredentials());
}

function hasRegisterPayload(record: SegmentScanDeviceRow): boolean {
  const creds = getValidCredentials();
  const cred = resolveCredential(record.auth_username, creds);
  return hasSegmentScanRegisterPayload(
    record,
    state.mode,
    cred,
    isCredentialAccessible(record),
  );
}

function isAlreadyRegistered(ip: string): boolean {
  return state.registerStatusMap[ip] === 'success';
}

/** 单台是否满足登记条件（不含全局 busy，供 registerOne* 使用） */
function isRecordRegistrable(record: SegmentScanDeviceRow): boolean {
  if (isAlreadyRegistered(record.ip)) return false;
  return hasRegisterPayload(record);
}

function canRegisterRecord(record: SegmentScanDeviceRow): boolean {
  if (state.batchRegistering || state.registering) return false;
  return isRecordRegistrable(record);
}

function warnCannotRegisterNvr(record: SegmentScanDeviceRow) {
  if (!hasFormCredentials()) {
    createMessage.warning('请至少填写一组登录凭证');
  } else if (state.mode === 'nvr' && !hasNvrRegisterPassword()) {
    createMessage.warning('登记 NVR 须填写 Web 登录密码');
  } else if (isAlreadyRegistered(record.ip)) {
    createMessage.warning('该 NVR 已登记');
  } else if (!record.is_nvr && !record.is_recognized && !record.vendor) {
    createMessage.warning('该设备未识别为 NVR，无法登记');
  } else {
    createMessage.warning('缺少登记所需信息，请确认登录凭证与扫描结果');
  }
}

function getRegistrableDevices(): SegmentScanDeviceRow[] {
  return state.devices.filter((d) => isRecordRegistrable(d));
}

const registrableCount = computed(() => getRegistrableDevices().length);

const batchRegisterButtonText = computed(() => {
  const n = registrableCount.value;
  if (state.mode === 'nvr') {
    return n > 0 ? `批量登记（${n}）` : '批量登记';
  }
  return n > 0 ? `批量注册（${n}）` : '批量注册';
});

function registerStatusLabel(ip: string, record: SegmentScanDeviceRow): string {
  const st = state.registerStatusMap[ip];
  if (st === 'success') return '已注册';
  if (st === 'failed') return '注册失败';
  if (!isCredentialAccessible(record)) {
    return state.mode === 'nvr' && hasFormCredentials() ? '待凭证探测' : '未认证';
  }
  if (!hasRegisterPayload(record)) return state.mode === 'nvr' ? '不可登记' : '无 RTSP';
  return state.mode === 'nvr' ? '可登记' : '可注册';
}

function registerStatusColor(ip: string): string {
  const st = state.registerStatusMap[ip];
  if (st === 'success') return 'success';
  if (st === 'failed') return 'error';
  return 'processing';
}

function resetRegisterStatus() {
  state.registerStatusMap = {};
  state.batchProgress = '';
  state.registeringIp = '';
}

function vendorToCameraType(vendor?: string): string {
  if (vendor === 'hikvision') return 'hikvision';
  if (vendor === 'dahua') return 'dahua';
  return 'custom';
}

async function handleScan() {
  try {
    await validate();
  } catch {
    return;
  }
  const values = getFieldsValue();
  const targetCheck = validateSegmentScanTargets(
    values.targets,
    String(values.ports || '').trim() || undefined,
  );
  if (!targetCheck.valid) {
    createMessage.warning(targetCheck.message || '扫描目标格式无效');
    return;
  }
  const creds = getValidCredentials();
  if (!creds.length) {
    createMessage.warning('请至少填写一组登录凭证');
    return;
  }
  if (state.mode === 'nvr' && !hasNvrRegisterPassword()) {
    createMessage.warning('NVR 模式请填写 Web 登录密码后再扫描/登记');
    return;
  }
  state.scanning = true;
  const scanPayload = {
    targets: String(values.targets || '').trim(),
    credentials: creds,
    ports: String(values.ports || '').trim() || undefined,
    concurrency: values.concurrency,
    timeout: values.timeout,
    only_hits: !!values.only_hits,
    nvr_only: state.mode === 'nvr',
    exclude_nvr: state.mode === 'camera',
    ingress_node_id: props.ingressNodeId,
  };
  const estSec = computeSegmentScanWallSeconds(scanPayload);
  state.scanProgress = `正在跨网段扫描，预计最多 ${estSec} 秒…`;
  state.devices = [];
  resetRegisterStatus();
  try {
    const res = await scanSegmentDevices(scanPayload);
    const list = (res as { data?: SegmentScanDeviceRow[] })?.data ?? (res as SegmentScanDeviceRow[]) ?? [];
    state.devices = Array.isArray(list) ? list : [];
    persistScanHistory(values, creds, state.devices.length);
    if (!state.devices.length) {
      createMessage.info(state.mode === 'nvr' ? '未发现 NVR 设备' : '未发现可识别设备');
    } else {
      createMessage.success(`扫描完成，共 ${state.devices.length} 台`);
    }
  } catch (e: unknown) {
    const err = e as { msg?: string; message?: string };
    createMessage.error(err?.msg || err?.message || '扫描失败');
  } finally {
    state.scanning = false;
    state.scanProgress = '';
  }
}

async function registerOneNvr(record: SegmentScanDeviceRow, credentials: CredentialPair[], timeout: number, silent = false): Promise<boolean> {
  if (!isRecordRegistrable(record)) {
    if (!silent) warnCannotRegisterNvr(record);
    return false;
  }
  const cred = resolveCredential(record.auth_username, credentials);
  if (!cred.password) {
    if (!silent) createMessage.warning('登记 NVR 须填写 Web 登录密码');
    return false;
  }
  const nvrTimeout = Math.max(timeout, 15);
  state.registeringIp = record.ip;
  if (!state.batchRegistering) state.registering = true;
  try {
    const res = await registerNvrWithChannels({
      ip: record.ip,
      port: record.port || 80,
      username: cred.username,
      password: cred.password,
      credentials,
      timeout: nvrTimeout,
      vendor: record.vendor,
      name: record.device_name,
      model: record.model,
      serial_number: record.serial,
      rtsp_url: record.rtsp_url,
      scheme: record.port && [443, 8443].includes(record.port) ? 'https' : 'http',
      ingress_node_id: props.ingressNodeId,
    });
    const n = nvrRegisterRegisteredCount(res);
    if (n > 0) {
      state.registerStatusMap[record.ip] = 'success';
      if (!silent) {
        createMessage.success(`NVR ${record.ip} 已登记，已挂载 ${n} 路通道`);
      }
      return true;
    }
    state.registerStatusMap[record.ip] = 'failed';
    if (!silent) {
      createMessage.warning(`NVR ${record.ip} 登记失败：${formatNvrRegisterHint(res)}`);
    }
    return false;
  } catch (e: unknown) {
    state.registerStatusMap[record.ip] = 'failed';
    if (!silent) {
      const err = e as { msg?: string; message?: string };
      createMessage.error(err?.msg || err?.message || `NVR ${record.ip} 登记失败`);
    }
    return false;
  } finally {
    if (state.registeringIp === record.ip) state.registeringIp = '';
    if (!state.batchRegistering) state.registering = false;
  }
}

async function registerOneCamera(record: SegmentScanDeviceRow, credentials: CredentialPair[], timeout: number, silent = false): Promise<boolean> {
  if (!isRecordRegistrable(record)) {
    if (!silent) {
      if (!isCredentialAccessible(record)) {
        createMessage.warning('该设备未通过凭证认证，无法注册');
      } else {
        createMessage.warning('无 RTSP 地址，请确认凭证正确或设备已识别（当前仅支持海康/大华 IPC）');
      }
    }
    return false;
  }
  const cred = resolveCredential(record.auth_username, credentials);
  const source = resolveSegmentScanRtsp(record, cred);
  if (!source) {
    if (!silent) createMessage.warning('无法生成 RTSP 地址');
    return false;
  }
  state.registeringIp = record.ip;
  if (!state.batchRegistering) state.registering = true;
  try {
    await registerDevice({
      name: record.device_name || `${record.vendor_label || '设备'}-${record.ip}`,
      source,
      ip: record.ip,
      port: 554,
      username: cred.username,
      password: cred.password,
      cameraType: vendorToCameraType(record.vendor),
      skip_onvif: true,
      stream: 0,
      manufacturer: record.vendor_label,
      model: record.model,
      serial_number: record.serial,
      ingress_node_id: props.ingressNodeId,
    });
    state.registerStatusMap[record.ip] = 'success';
    if (!silent) createMessage.success(`摄像头 ${record.ip} 注册成功`);
    return true;
  } catch (e: unknown) {
    state.registerStatusMap[record.ip] = 'failed';
    if (!silent) {
      const err = e as { msg?: string; message?: string };
      createMessage.error(err?.msg || err?.message || `摄像头 ${record.ip} 注册失败`);
    }
    return false;
  } finally {
    if (state.registeringIp === record.ip) state.registeringIp = '';
    if (!state.batchRegistering) state.registering = false;
  }
}

async function handleRegisterNvr(record: SegmentScanDeviceRow) {
  const values = getFieldsValue();
  const creds = getValidCredentials();
  if (await registerOneNvr(record, creds, Number(values.timeout) || 3)) emit('success');
}

async function handleRegisterCamera(record: SegmentScanDeviceRow) {
  const values = getFieldsValue();
  const creds = getValidCredentials();
  if (await registerOneCamera(record, creds, Number(values.timeout) || 3)) emit('success');
}

async function handleBatchRegister() {
  const list = getRegistrableDevices();
  if (!list.length) {
    createMessage.warning('没有可注册的设备');
    return;
  }
  const values = getFieldsValue();
  const creds = getValidCredentials();
  const timeout = Number(values.timeout) || 3;
  state.batchRegistering = true;
  state.registering = true;
  let okCount = 0;
  let failCount = 0;
  const isNvr = state.mode === 'nvr';
  try {
    for (let i = 0; i < list.length; i++) {
      const record = list[i];
      state.batchProgress = `正在处理 ${i + 1}/${list.length}：${record.ip}`;
      const ok = isNvr
        ? await registerOneNvr(record, creds, timeout, true)
        : await registerOneCamera(record, creds, timeout, true);
      if (ok) okCount += 1;
      else failCount += 1;
    }
    if (okCount > 0) emit('success');
    const action = isNvr ? '登记' : '注册';
    if (failCount === 0) createMessage.success(`批量${action}完成：成功 ${okCount} 台`);
    else createMessage.warning(`批量${action}完成：成功 ${okCount} 台，失败 ${failCount} 台`);
  } finally {
    state.batchRegistering = false;
    state.registering = false;
    state.batchProgress = '';
  }
}
</script>

<style lang="less" scoped>
:deep(.segment-scan-credentials) {
  .credentials-block {
    max-width: 100%;
  }
}

.credentials-block {
  width: 100%;
}

.credential-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;

  .cred-user,
  .cred-pass {
    flex: 1;
    min-width: 0;
  }
}

:deep(.ant-spin-nested-loading),
:deep(.ant-spin-container) {
  height: 100%;
  min-height: 0;
}
</style>
