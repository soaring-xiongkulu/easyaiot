<template>
  <Spin :spinning="state.scanning">
    <DeviceCreatePanelLayout result-title="扫描结果">
      <template #actions>
        <Button type="primary" :loading="state.scanning" preIcon="ant-design:search-outlined" @click="handleScan">
          扫描局域网
        </Button>
        <span v-if="state.scanProgress" class="dc-action-tip">{{ state.scanProgress }}</span>
      </template>
      <template #result>
        <Table
          v-if="state.devices.length"
          :columns="columns"
          :data-source="state.devices"
          :pagination="tablePagination"
          :scroll="{ x: 720, y: 300 }"
          row-key="ip"
          size="small"
          bordered
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.dataIndex === 'mac'">
              {{ formatOnvifMac(record.mac) }}
            </template>
            <template v-else-if="column.dataIndex === 'hardware_name'">
              {{ record.hardware_name || '—' }}
            </template>
            <template v-else-if="column.dataIndex === 'action'">
              <Button
                type="link"
                size="small"
                :loading="state.registeringIp === record.ip"
                @click="openRegisterModal(record)"
              >
                注册
              </Button>
            </template>
          </template>
        </Table>
        <Empty v-else description="点击「扫描局域网」发现同网段 ONVIF 设备" />
      </template>
    </DeviceCreatePanelLayout>
    <VideoRegisterModal @register="registerVideoRegisterModal" @success="handleRegisterSuccess" />
  </Spin>
</template>

<script lang="ts" setup>
import { reactive, watch } from 'vue';
import { Empty, Spin, Table } from 'ant-design-vue';
import { Button } from '@/components/Button';
import { useModal } from '@/components/Modal';
import { useMessage } from '@/hooks/web/useMessage';
import { discoverDevices, registerDeviceByOnvif } from '@/api/device/camera';
import VideoRegisterModal from '@/views/camera/components/VideoRegisterModal/index.vue';
import {
  formatOnvifMac,
  getOnvifDiscoveryTableColumns,
  type OnvifDiscoveryRow,
} from '@/views/camera/components/VideoModal/Data';
import DeviceCreatePanelLayout from '../DeviceCreatePanelLayout.vue';

const emit = defineEmits<{ success: [] }>();
const props = defineProps<{ ingressNodeId?: number }>();

const { createMessage } = useMessage();
const [registerVideoRegisterModal, { openModal: openVideoRegisterModal }] = useModal();

const state = reactive({
  scanning: false,
  registeringIp: '' as string,
  devices: [] as OnvifDiscoveryRow[],
  scanProgress: '',
});

const columns = getOnvifDiscoveryTableColumns();

const tablePagination = {
  pageSize: 10,
  size: 'small' as const,
  showSizeChanger: false,
  showTotal: (total: number) => `共 ${total} 台`,
};

watch(() => props.ingressNodeId, () => {
  state.devices = [];
  state.scanProgress = '';
});

function normalizeDiscoveryList(res: unknown): OnvifDiscoveryRow[] {
  if (Array.isArray(res)) {
    return res as OnvifDiscoveryRow[];
  }
  const data = (res as { data?: unknown })?.data ?? res;
  if (Array.isArray(data)) {
    return data as OnvifDiscoveryRow[];
  }
  return [];
}

async function handleScan() {
  state.scanning = true;
  state.scanProgress = '正在扫描局域网 ONVIF 设备…';
  state.devices = [];
  try {
    const res = await discoverDevices(props.ingressNodeId);
    state.devices = normalizeDiscoveryList(res);
    if (!state.devices.length) {
      createMessage.info('未发现 ONVIF 设备，请确认设备与所选接入节点网络互通');
    } else {
      createMessage.success(`扫描完成，共 ${state.devices.length} 台`);
    }
  } catch (error: unknown) {
    const err = error as { msg?: string; message?: string };
    createMessage.error(err?.msg || err?.message || '扫描失败');
  } finally {
    state.scanning = false;
    state.scanProgress = '';
  }
}

function openRegisterModal(record: OnvifDiscoveryRow) {
  openVideoRegisterModal(true, { record });
}

async function handleRegisterSuccess(payload: Record<string, unknown>) {
  const ip = String(payload.ip ?? '');
  const username = String(payload.username ?? '').trim();
  const password = String(payload.password ?? '');
  if (!ip || !password) {
    createMessage.error('IP 或密码不能为空');
    return;
  }
  if (!username) {
    createMessage.error('用户名不能为空');
    return;
  }
  const rawPort = payload.port;
  const port =
    rawPort !== undefined && rawPort !== null && rawPort !== '' ? Number(rawPort) : 80;
  state.registeringIp = ip;
  try {
    await registerDeviceByOnvif({
      ip,
      port: Number.isFinite(port) ? port : 80,
      username,
      password,
      ingress_node_id: props.ingressNodeId,
    });
    createMessage.success('设备注册成功');
    state.devices = state.devices.filter((d) => d.ip !== ip);
    emit('success');
  } catch (error: unknown) {
    const err = error as { msg?: string; message?: string };
    createMessage.error(err?.msg || err?.message || '注册失败');
  } finally {
    if (state.registeringIp === ip) {
      state.registeringIp = '';
    }
  }
}
</script>

<style lang="less" scoped>
:deep(.ant-spin-nested-loading),
:deep(.ant-spin-container) {
  height: 100%;
  min-height: 0;
}
</style>
