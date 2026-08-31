<template>
  <BasicDrawer
    v-bind="$attrs"
    @register="register"
    title="电子身份档案"
    width="92%"
    placement="right"
    :showFooter="false"
  >
    <a-alert
      class="mb-3"
      type="info"
      show-icon
      message="电子身份不要求真实姓名"
      description="系统用稳定 EID 归并同一个人，并持续记录跨摄像头轨迹；确认身份后可补充真实姓名，历史轨迹不会改变。"
    />
    <div class="identity-toolbar">
      <a-input-search
        v-model:value="search"
        placeholder="搜索电子编码 / 电子姓名 / 真实姓名"
        allow-clear
        style="width: 340px"
        @search="load"
      />
      <a-select v-model:value="status" allow-clear placeholder="全部状态" style="width: 140px" @change="load">
        <a-select-option value="anonymous">未知身份</a-select-option>
        <a-select-option value="confirmed">已确认</a-select-option>
        <a-select-option value="disabled">已停用</a-select-option>
      </a-select>
      <Button preIcon="ant-design:reload-outlined" :loading="loading" @click="load">刷新</Button>
      <Button :disabled="selectedIds.length < 2" preIcon="ant-design:merge-cells-outlined" @click="mergeSelected">
        合并所选（{{ selectedIds.length }}）
      </Button>
    </div>
    <a-table
      :data-source="rows"
      :columns="columns"
      :loading="loading"
      row-key="id"
      :row-selection="{ selectedRowKeys: selectedIds, onChange: onSelectionChange }"
      :pagination="{ current: page, pageSize, total, showSizeChanger: false }"
      @change="onTableChange"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'avatar'">
          <img :src="imageUrl(record.cover_image_path) || defaultFace" class="identity-avatar" alt="人脸" />
        </template>
        <template v-else-if="column.key === 'identity'">
          <div class="identity-name">{{ record.display_name }}</div>
          <div class="identity-code">{{ record.identity_code }}</div>
        </template>
        <template v-else-if="column.key === 'status'">
          <a-tag :color="record.status === 'confirmed' ? 'green' : record.status === 'anonymous' ? 'blue' : 'default'">
            {{ statusLabel(record.status) }}
          </a-tag>
        </template>
        <template v-else-if="column.key === 'action'">
          <a-space>
            <a-button type="link" size="small" @click="openTrajectory(record)">轨迹</a-button>
            <a-button type="link" size="small" @click="openEdit(record)">命名/确认</a-button>
          </a-space>
        </template>
      </template>
    </a-table>

    <a-drawer v-model:open="trajectoryOpen" title="电子身份轨迹" width="560" :get-container="false">
      <a-descriptions v-if="selected" bordered size="small" :column="1" class="mb-3">
        <a-descriptions-item label="电子姓名">{{ selected.display_name }}</a-descriptions-item>
        <a-descriptions-item label="电子编码">{{ selected.identity_code }}</a-descriptions-item>
        <a-descriptions-item label="累计出现">{{ selected.occurrence_count }} 次</a-descriptions-item>
      </a-descriptions>
      <a-timeline>
        <a-timeline-item v-for="point in trajectory" :key="point.record_id">
          <div>{{ formatTime(point.time) }} · {{ point.device_name || point.device_id }}</div>
          <img v-if="point.face_image_path" :src="imageUrl(point.face_image_path)" class="trajectory-face" alt="轨迹人脸" />
        </a-timeline-item>
      </a-timeline>
      <a-empty v-if="!trajectoryLoading && !trajectory.length" description="暂无轨迹" />
      <a-spin :spinning="trajectoryLoading" />
    </a-drawer>

    <a-modal v-model:open="editOpen" title="命名与确认电子身份" @ok="saveIdentity">
      <a-form layout="vertical">
        <a-form-item label="电子编码"><a-input :value="selected?.identity_code" disabled /></a-form-item>
        <a-form-item label="电子姓名"><a-input v-model:value="editForm.display_name" /></a-form-item>
        <a-form-item label="真实姓名"><a-input v-model:value="editForm.real_name" placeholder="未知可留空" /></a-form-item>
        <a-form-item label="备注"><a-textarea v-model:value="editForm.remark" :rows="3" /></a-form-item>
      </a-form>
    </a-modal>
  </BasicDrawer>
</template>

<script lang="ts" setup>
import { ref } from 'vue';
import { Modal } from 'ant-design-vue';
import { BasicDrawer, useDrawerInner } from '@/components/Drawer';
import { Button } from '@/components/Button';
import { useMessage } from '@/hooks/web/useMessage';
import {
  getFaceIdentityTrajectory,
  listFaceIdentities,
  mergeFaceIdentities,
  resolveFaceImageDisplayUrl,
  updateFaceIdentity,
  type FaceIdentity,
  type FaceIdentityTrajectoryPoint,
} from '@/api/device/face_library';
import DEFAULT_FACE_IMAGE from '@/assets/images/video/snap-task.png';

defineOptions({ name: 'FaceIdentityDrawer' });
const { createMessage } = useMessage();
const defaultFace = DEFAULT_FACE_IMAGE;
const rows = ref<FaceIdentity[]>([]);
const loading = ref(false);
const search = ref('');
const status = ref<string>();
const page = ref(1);
const pageSize = 20;
const total = ref(0);
const selected = ref<FaceIdentity>();
const selectedIds = ref<number[]>([]);
const trajectory = ref<FaceIdentityTrajectoryPoint[]>([]);
const trajectoryLoading = ref(false);
const trajectoryOpen = ref(false);
const editOpen = ref(false);
const editForm = ref({ display_name: '', real_name: '', remark: '' });
const columns = [
  { title: '人脸', key: 'avatar', width: 76 },
  { title: '电子身份', key: 'identity' },
  { title: '真实姓名', dataIndex: 'real_name', width: 130 },
  { title: '状态', key: 'status', width: 100 },
  { title: '出现次数', dataIndex: 'occurrence_count', width: 90 },
  { title: '样本', dataIndex: 'sample_count', width: 70 },
  { title: '最近出现', dataIndex: 'last_seen_at', width: 175 },
  { title: '操作', key: 'action', width: 150 },
];

const [register] = useDrawerInner(async () => {
  page.value = 1;
  await load();
});

function imageUrl(path?: string) {
  return resolveFaceImageDisplayUrl(path ? `/video/alert/image?path=${encodeURIComponent(path)}` : '');
}
function statusLabel(value: string) {
  return ({ anonymous: '未知身份', confirmed: '已确认', disabled: '已停用' } as Record<string, string>)[value] || value;
}
function formatTime(value?: string) {
  return value ? value.replace('T', ' ').replace('Z', '').slice(0, 19) : '—';
}
async function load() {
  loading.value = true;
  try {
    const res = await listFaceIdentities({ page: page.value, pageSize, status: status.value, search: search.value || undefined });
    rows.value = res.list || [];
    total.value = res.total || 0;
  } catch (error: any) {
    createMessage.error(error?.message || '加载电子身份失败');
  } finally {
    loading.value = false;
  }
}
function onTableChange(pagination: { current?: number }) {
  page.value = pagination.current || 1;
  void load();
}
function onSelectionChange(keys: Array<string | number>) {
  selectedIds.value = keys.map(Number);
}
async function openTrajectory(record: FaceIdentity) {
  selected.value = record;
  trajectoryOpen.value = true;
  trajectoryLoading.value = true;
  try {
    const res = await getFaceIdentityTrajectory(record.id, { limit: 500 });
    trajectory.value = res.data?.points || [];
  } finally {
    trajectoryLoading.value = false;
  }
}
function openEdit(record: FaceIdentity) {
  selected.value = record;
  editForm.value = { display_name: record.display_name || '', real_name: record.real_name || '', remark: record.remark || '' };
  editOpen.value = true;
}
async function saveIdentity() {
  if (!selected.value || !editForm.value.display_name.trim()) {
    createMessage.warning('电子姓名不能为空');
    return;
  }
  await updateFaceIdentity(selected.value.id, {
    display_name: editForm.value.display_name.trim(),
    real_name: editForm.value.real_name.trim() || undefined,
    remark: editForm.value.remark.trim() || undefined,
    status: editForm.value.real_name.trim() ? 'confirmed' : 'anonymous',
  });
  editOpen.value = false;
  createMessage.success('电子身份已更新');
  await load();
}
function mergeSelected() {
  if (selectedIds.value.length < 2) return;
  const [targetId, ...sourceIds] = selectedIds.value;
  Modal.confirm({
    title: '确认合并电子身份？',
    content: `将以 EID #${targetId} 为主身份，合并其余 ${sourceIds.length} 个身份；轨迹和样本会一并归集。`,
    okText: '确认合并',
    onOk: async () => {
      await mergeFaceIdentities(targetId, sourceIds);
      selectedIds.value = [];
      createMessage.success('电子身份已合并');
      await load();
    },
  });
}
</script>

<style scoped>
.identity-toolbar { display: flex; gap: 10px; margin-bottom: 14px; }
.identity-avatar { width: 52px; height: 52px; object-fit: cover; border-radius: 8px; background: #f0f2f5; }
.identity-name { font-weight: 600; }
.identity-code { margin-top: 3px; color: #64748b; font-family: monospace; font-size: 12px; }
.trajectory-face { width: 88px; height: 88px; margin-top: 6px; object-fit: cover; border-radius: 6px; }
</style>
