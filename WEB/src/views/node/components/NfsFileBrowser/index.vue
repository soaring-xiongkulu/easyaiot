<template>
  <div class="nfs-file-ops" :class="{ 'nfs-file-ops--manager': isManager }">
    <aside class="node-picker">
      <div class="node-picker__head">
        <div class="node-picker__title">选择节点</div>
        <Button
          type="default"
          size="small"
          preIcon="ant-design:reload-outlined"
          :loading="nodesLoading"
          @click="loadMountableNodes"
        >
          刷新
        </Button>
      </div>

      <Empty v-if="!nodesLoading && !mountableNodes.length" description="暂无节点" />

      <ScrollContainer v-else class="node-chips-scroll">
        <div class="node-chips">
          <Card
            v-for="node in mountableNodes"
            :key="node.nodeId"
            size="small"
            hoverable
            class="node-chip"
            :class="{
              'is-active': currentNodeId === node.nodeId,
              'is-disabled': !canBrowseNode(node),
            }"
            @click="selectNode(node.nodeId)"
          >
            <div class="node-chip__name" :title="nodeChipTitle(node)">{{ node.name || node.host }}</div>
            <div class="node-chip__meta">
              <Tag :color="kindColor(node.kind)" class="node-chip__tag">{{ kindLabel(node) }}</Tag>
              <Tag :color="mountTone(node)" class="node-chip__tag">{{ mountLabel(node) }}</Tag>
            </div>
            <div class="node-chip__host">
              {{ node.host }} · {{ node.nfsMountPath || node.cephMountPath || '-' }}
            </div>
          </Card>
        </div>
      </ScrollContainer>
    </aside>

    <section class="file-main">
      <Empty v-if="!currentNodeId" class="ops-empty" description="请选择节点" />

      <template v-else>
        <div class="path-panel">
          <div class="path-panel__top">
            <div class="path-panel__info">
              <Tag color="blue">挂载根 {{ list?.mountRoot || currentNode?.nfsMountPath || '…' }}</Tag>
              <Tag>{{ kindLabel(currentNode) }}</Tag>
              <span class="path-panel__node">{{ currentNode?.name }} ({{ currentNode?.host }})</span>
            </div>
            <Space wrap :size="8">
              <Button
                type="default"
                preIcon="ant-design:arrow-up-outlined"
                :disabled="!relativePath"
                @click="goUp"
              >
                上级目录
              </Button>
              <Button type="default" preIcon="ant-design:copy-outlined" @click="copyCurrentPath">
                复制路径
              </Button>
              <Button
                type="default"
                preIcon="ant-design:reload-outlined"
                :loading="loading"
                @click="reload"
              >
                刷新
              </Button>
            </Space>
          </div>

          <Breadcrumb class="path-row__crumb">
            <Breadcrumb.Item>
              <a @click.prevent="goPath('')">媒体根</a>
            </Breadcrumb.Item>
            <Breadcrumb.Item v-for="(seg, idx) in breadcrumbs" :key="idx">
              <a @click.prevent="goPath(breadcrumbs.slice(0, idx + 1).join('/'))">{{ seg }}</a>
            </Breadcrumb.Item>
          </Breadcrumb>
          <div class="path-abs">{{ absolutePathDisplay }}</div>

          <div class="action-row">
            <Space wrap :size="8">
              <Button type="default" preIcon="ant-design:folder-add-outlined" @click="openMkdir">
                新建目录
              </Button>
              <Upload
                :show-upload-list="false"
                :before-upload="beforeUpload"
                :disabled="uploading"
                multiple
              >
                <Button type="primary" preIcon="ant-design:upload-outlined" :loading="uploading">
                  上传文件
                </Button>
              </Upload>
              <PopConfirmButton
                placement="topRight"
                type="primary"
                color="error"
                preIcon="ant-design:delete-outlined"
                :disabled="!selectedRows.length"
                :loading="batchDeleting"
                :title="batchDeleteTitle"
                @confirm="runBatchDelete"
              >
                删除所选{{ selectedRows.length ? ` (${selectedRows.length})` : '' }}
              </PopConfirmButton>
            </Space>
            <Input
              v-model:value="keyword"
              allow-clear
              placeholder="过滤当前目录（名称）"
              class="filter-input"
            >
              <template #prefix>
                <Icon icon="ant-design:search-outlined" :size="14" />
              </template>
            </Input>
          </div>
        </div>

        <div v-if="uploadJobs.length" class="upload-panel">
          <div class="upload-head">
            <span class="ops-hint">
              上传进度 {{ uploadDoneCount }}/{{ uploadJobs.length }}
              <template v-if="uploadFailCount"> · 失败 {{ uploadFailCount }}</template>
            </span>
            <Button
              v-if="!uploading"
              type="link"
              size="small"
              preIcon="ant-design:close-outlined"
              @click="uploadJobs = []"
            >
              清除
            </Button>
          </div>
          <Progress
            :percent="uploadPercent"
            :status="uploadFailCount ? 'exception' : uploading ? 'active' : 'success'"
            size="small"
          />
          <div class="upload-list">
            <div v-for="job in uploadJobs" :key="job.id" class="upload-item">
              <span class="upload-item__name" :title="job.name">{{ job.name }}</span>
              <Tag :color="jobStatusColor(job.status)">{{ jobStatusText(job.status) }}</Tag>
              <span v-if="job.message" class="upload-item__msg" :title="job.message">{{ job.message }}</span>
            </div>
          </div>
        </div>

        <div
          class="drop-zone"
          :class="{ 'drop-zone--active': dragOver }"
          @dragover.prevent="dragOver = true"
          @dragleave.prevent="onDragLeave"
          @drop.prevent="onDrop"
        >
          <div class="drop-banner">
            <Icon icon="ant-design:cloud-upload-outlined" :size="18" />
            <span>拖拽文件到此处上传</span>
          </div>

          <div class="table-wrap">
            <Table
              size="middle"
              row-key="relativePath"
              :loading="loading"
              :pagination="tablePagination"
              :data-source="filteredEntries"
              :columns="columns"
              :row-selection="rowSelection"
              :scroll="tableScroll"
              :locale="{ emptyText: emptyText }"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'name'">
                  <a
                    v-if="record.directory"
                    class="name-link"
                    @click.prevent="goPath(record.relativePath)"
                  >
                    <Icon icon="ant-design:folder-filled" :size="15" class="name-link__icon" />
                    {{ record.name }}/
                  </a>
                  <span v-else class="name-file">
                    <Icon icon="ant-design:file-outlined" :size="14" class="name-link__icon" />
                    {{ record.name }}
                  </span>
                </template>
                <template v-else-if="column.key === 'size'">
                  {{ record.directory ? '-' : formatSize(record.size) }}
                </template>
                <template v-else-if="column.key === 'mtime'">
                  {{ formatMtime(record.mtime) }}
                </template>
                <template v-else-if="column.key === 'action'">
                  <TableAction :actions="buildRowActions(record)" />
                </template>
              </template>
            </Table>
          </div>
        </div>
      </template>
    </section>

    <BasicModal
      @register="registerMkdirModal"
      title="新建目录"
      ok-text="创建"
      cancel-text="取消"
      :min-height="120"
      :can-fullscreen="false"
      destroy-on-close
      @ok="submitMkdir"
    >
      <div class="modal-hint">位置：{{ absolutePathDisplay }}</div>
      <Input
        v-model:value="mkdirName"
        placeholder="目录名，例如 playbacks-backup"
        allow-clear
        @pressEnter="submitMkdir"
      />
    </BasicModal>

    <BasicModal
      @register="registerRenameModal"
      title="重命名"
      ok-text="确定"
      cancel-text="取消"
      :min-height="120"
      :can-fullscreen="false"
      destroy-on-close
      @ok="submitRename"
    >
      <div class="modal-hint">原名称：{{ renameTarget?.name }}</div>
      <Input
        v-model:value="renameName"
        placeholder="新名称"
        allow-clear
        @pressEnter="submitRename"
      />
    </BasicModal>

    <BasicModal
      @register="registerConflictModal"
      title="发现同名文件"
      :footer="null"
      :min-height="120"
      :can-fullscreen="false"
      destroy-on-close
      @cancel="resolveConflict('cancel')"
    >
      <div class="modal-hint">
        已存在：{{ conflictNames.slice(0, 10).join('、')
        }}{{ conflictNames.length > 10 ? '…' : '' }}
      </div>
      <div class="conflict-actions">
        <Button
          type="primary"
          color="error"
          preIcon="ant-design:swap-outlined"
          @click="resolveConflict('overwrite')"
        >
          覆盖这些文件
        </Button>
        <Button type="default" preIcon="ant-design:forward-outlined" @click="resolveConflict('skip')">
          跳过同名，只传新文件
        </Button>
        <Button type="default" @click="resolveConflict('cancel')">取消全部</Button>
      </div>
    </BasicModal>
  </div>
</template>

<script lang="ts" setup>
import { computed, onMounted, ref, watch } from 'vue';
import {
  Breadcrumb,
  Card,
  Empty,
  Input,
  Progress,
  Space,
  Table,
  Tag,
  Upload,
} from 'ant-design-vue';
import type { TableProps } from 'ant-design-vue';
import { Button, PopConfirmButton } from '@/components/Button';
import { ScrollContainer } from '@/components/Container';
import { Icon } from '@/components/Icon';
import { BasicModal, useModal } from '@/components/Modal';
import { TableAction } from '@/components/Table';
import { useMessage } from '@/hooks/web/useMessage';
import {
  deleteNfsMediaPath,
  downloadNfsMediaFile,
  getCephTopology,
  listNfsMediaFiles,
  mkdirNfsMediaDir,
  renameNfsMediaPath,
  uploadNfsMediaFile,
  type CephTopologyNodeVO,
  type NfsFileEntry,
  type NfsFileListResult,
} from '@/api/device/node';

defineOptions({ name: 'NfsFileBrowser' });

const props = withDefaults(
  defineProps<{
    initialNodeId?: number;
    /** stack=页内堆叠；manager=大抽屉左右分栏 */
    layout?: 'stack' | 'manager';
  }>(),
  { layout: 'stack' },
);

const isManager = computed(() => props.layout === 'manager');
const tableScroll = computed(() => (isManager.value ? { y: 'calc(100vh - 380px)' } : undefined));

const MAX_UPLOAD_BYTES = 50 * 1024 * 1024;

type UploadJobStatus = 'pending' | 'uploading' | 'done' | 'skipped' | 'error';
interface UploadJob {
  id: string;
  name: string;
  file: File;
  status: UploadJobStatus;
  message?: string;
}

const { createMessage } = useMessage();
const [registerMkdirModal, { openModal: openMkdirModal, setModalProps: setMkdirProps, closeModal: closeMkdirModal }] =
  useModal();
const [
  registerRenameModal,
  { openModal: openRenameModal, setModalProps: setRenameProps, closeModal: closeRenameModal },
] = useModal();
const [registerConflictModal, { openModal: openConflictModal, closeModal: closeConflictModal }] = useModal();

const selectedIds = ref<number[]>([]);
const mountableNodes = ref<CephTopologyNodeVO[]>([]);
const nodesLoading = ref(false);
const relativePath = ref('');
const keyword = ref('');
const loading = ref(false);
const uploading = ref(false);
const batchDeleting = ref(false);
const dragOver = ref(false);
const mkdirName = ref('');
const renameName = ref('');
const renameTarget = ref<NfsFileEntry | null>(null);
const conflictNames = ref<string[]>([]);
let conflictResolve: ((v: 'overwrite' | 'skip' | 'cancel') => void) | null = null;
const downloading = ref<string | null>(null);
const list = ref<NfsFileListResult | null>(null);
const selectedRowKeys = ref<string[]>([]);
const selectedRows = ref<NfsFileEntry[]>([]);
const uploadJobs = ref<UploadJob[]>([]);
const pendingUploadFiles = ref<File[]>([]);
let uploadFlushTimer: ReturnType<typeof setTimeout> | null = null;

const currentNodeId = computed(() => selectedIds.value[0] || null);
const currentNode = computed(
  () => mountableNodes.value.find((n) => n.nodeId === currentNodeId.value) || null,
);

const batchDeleteTitle = computed(() => {
  const names = selectedRows.value.map((r) => r.name).slice(0, 8);
  return `删除所选 ${selectedRows.value.length} 项：${names.join('、')}${
    selectedRows.value.length > 8 ? '…' : ''
  }。目录会递归删除，不可恢复。`;
});

function clusterRoleOf(node?: CephTopologyNodeVO | null) {
  if (!node) return '';
  if (node.nfsClusterRole) return node.nfsClusterRole;
  if (node.kind === 'nfs_primary' || node.kind === 'storage_nfs' || node.kind === 'storage_osd') return 'primary';
  if (node.kind === 'nfs_standby') return 'standby';
  if (node.kind === 'nfs_client' || node.kind === 'ceph_client') return 'client';
  if (node.kind === 'nfs_candidate') return 'candidate';
  if (node.kind === 'platform') return isNfsServerNode(node) ? 'primary' : 'client';
  return '';
}

function isNfsServerNode(node?: CephTopologyNodeVO | null) {
  return clusterRoleOf(node) === 'primary';
}

function kindLabel(node?: CephTopologyNodeVO | null) {
  if (!node) return '-';
  const role = clusterRoleOf(node);
  if (node.kind === 'platform' || node.isPlatform) {
    if (role === 'primary') return '控制面·主服务端';
    if (role === 'standby') return '控制面·备服务端';
    if (role === 'client') return '控制面·客户端';
    return '控制面';
  }
  if (role === 'primary') return '主服务端';
  if (role === 'standby') return '备服务端';
  if (role === 'candidate') return '存储候选';
  if (role === 'client') return '客户端';
  return node.kind || '-';
}

function kindColor(kind?: string) {
  if (kind === 'platform') return 'blue';
  if (kind === 'nfs_primary' || kind === 'storage_nfs' || kind === 'storage_osd') return 'purple';
  if (kind === 'nfs_standby') return 'geekblue';
  if (kind === 'nfs_candidate') return 'default';
  return 'cyan';
}

function mountLabel(node: CephTopologyNodeVO) {
  const ready = !!(node.nfsMountReady ?? node.cephMountReady);
  const role = clusterRoleOf(node);
  if (role === 'primary') {
    if (node.nfsExportReady) return 'Export就绪';
    if (ready) return '本机目录就绪';
    return 'Export未就绪';
  }
  if (role === 'standby') return ready ? '备机就绪' : '备机未就绪';
  if (role === 'candidate') return '未分配';
  return ready ? '已挂载' : '未挂载';
}

function mountTone(node: CephTopologyNodeVO) {
  if (clusterRoleOf(node) === 'candidate') return 'default';
  if (clusterRoleOf(node) === 'primary') {
    if (node.nfsExportReady) return 'success';
    if (node.nfsMountReady ?? node.cephMountReady) return 'processing';
    return 'warning';
  }
  return (node.nfsMountReady ?? node.cephMountReady) ? 'success' : 'warning';
}

function canBrowseNode(node?: CephTopologyNodeVO | null) {
  if (!node) return false;
  return !!node.sshCredentialConfigured || !!node.isPlatform || node.kind === 'platform';
}

function nodeChipTitle(node: CephTopologyNodeVO) {
  const parts = [
    kindLabel(node),
    node.host,
    node.nfsMountPath || node.cephMountPath || '-',
    canBrowseNode(node) ? (node.kind === 'platform' || node.isPlatform ? '本机可操作' : 'SSH 已配置') : 'SSH 未配置',
  ];
  return parts.join(' · ');
}

function pickDefaultNodeId(nodes: CephTopologyNodeVO[], preferred?: number) {
  const browsable = nodes.filter((n) => canBrowseNode(n));
  if (preferred && browsable.some((n) => n.nodeId === preferred)) {
    return preferred;
  }
  const platform = browsable.find((n) => n.kind === 'platform' || n.isPlatform);
  if (platform?.nodeId) return platform.nodeId;
  const readyClient = browsable.find(
    (n) =>
      (n.kind === 'nfs_client' || n.kind === 'ceph_client') &&
      (n.nfsMountReady ?? n.cephMountReady),
  );
  if (readyClient?.nodeId) return readyClient.nodeId;
  const anyClient = browsable.find((n) => n.kind === 'nfs_client' || n.kind === 'ceph_client');
  if (anyClient?.nodeId) return anyClient.nodeId;
  const storage = browsable.find((n) => n.kind === 'storage_nfs' || n.kind === 'storage_osd');
  if (storage?.nodeId) return storage.nodeId;
  return browsable[0]?.nodeId;
}

async function loadMountableNodes() {
  nodesLoading.value = true;
  try {
    const data = await getCephTopology();
    const nodes = (data.nodes || []).filter((n) => !!n.nodeId);
    mountableNodes.value = nodes;
    const nextId = pickDefaultNodeId(nodes, props.initialNodeId || currentNodeId.value || undefined);
    if (nextId && selectedIds.value[0] !== nextId) {
      selectedIds.value = [nextId];
    } else if (!nextId) {
      selectedIds.value = [];
    }
  } catch (e: any) {
    mountableNodes.value = [];
    createMessage.error(e?.message || '加载可管理节点失败');
  } finally {
    nodesLoading.value = false;
  }
}

function selectNode(nodeId?: number) {
  if (!nodeId) return;
  const node = mountableNodes.value.find((n) => n.nodeId === nodeId);
  if (!canBrowseNode(node)) {
    createMessage.warning('该节点暂不可浏览文件');
    return;
  }
  selectedIds.value = [nodeId];
}

const breadcrumbs = computed(() =>
  relativePath.value ? relativePath.value.split('/').filter(Boolean) : [],
);

const absolutePathDisplay = computed(() => {
  const root =
    (list.value?.mountRoot || currentNode.value?.nfsMountPath || currentNode.value?.cephMountPath || '')
      .replace(/\/+$/, '') || '（加载中…）';
  if (!relativePath.value) return root || '/';
  return `${root}/${relativePath.value}`;
});

const sortedEntries = computed(() => {
  const entries = [...(list.value?.entries || [])];
  entries.sort((a, b) => {
    if (!!a.directory !== !!b.directory) return a.directory ? -1 : 1;
    return String(a.name || '').localeCompare(String(b.name || ''), 'zh');
  });
  return entries;
});

const filteredEntries = computed(() => {
  const q = keyword.value.trim().toLowerCase();
  if (!q) return sortedEntries.value;
  return sortedEntries.value.filter((e) => String(e.name || '').toLowerCase().includes(q));
});

const emptyText = computed(() => {
  if (keyword.value.trim()) return '无匹配';
  return '空目录';
});

const columns = [
  { title: '名称', key: 'name', dataIndex: 'name' },
  { title: '大小', key: 'size', dataIndex: 'size', width: 110 },
  { title: '修改时间', key: 'mtime', dataIndex: 'mtime', width: 170 },
  { title: '操作', key: 'action', width: 220 },
];

const tablePagination = computed(() => {
  if (filteredEntries.value.length <= 50) return false as const;
  return { pageSize: 50, showSizeChanger: true, pageSizeOptions: ['50', '100', '200'] };
});

const rowSelection = computed<TableProps['rowSelection']>(() => ({
  selectedRowKeys: selectedRowKeys.value,
  onChange: (keys, rows) => {
    selectedRowKeys.value = keys as string[];
    selectedRows.value = rows as NfsFileEntry[];
  },
}));

const uploadDoneCount = computed(
  () => uploadJobs.value.filter((j) => j.status === 'done' || j.status === 'skipped').length,
);
const uploadFailCount = computed(() => uploadJobs.value.filter((j) => j.status === 'error').length);
const uploadPercent = computed(() => {
  if (!uploadJobs.value.length) return 0;
  const finished = uploadJobs.value.filter((j) =>
    ['done', 'skipped', 'error'].includes(j.status),
  ).length;
  return Math.round((finished / uploadJobs.value.length) * 100);
});

function formatSize(size?: number) {
  if (size == null) return '-';
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

function formatMtime(mtime?: number | string) {
  if (mtime == null || mtime === '') return '-';
  const n = typeof mtime === 'string' ? Number(mtime) : mtime;
  if (!Number.isFinite(n) || n <= 0) return String(mtime);
  const ms = n > 1e12 ? n : n * 1000;
  const d = new Date(ms);
  if (Number.isNaN(d.getTime())) return String(mtime);
  const pad = (x: number) => String(x).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function jobStatusColor(s: UploadJobStatus) {
  if (s === 'done') return 'success';
  if (s === 'error') return 'error';
  if (s === 'skipped') return 'default';
  if (s === 'uploading') return 'processing';
  return 'warning';
}

function jobStatusText(s: UploadJobStatus) {
  const map: Record<UploadJobStatus, string> = {
    pending: '等待',
    uploading: '上传中',
    done: '完成',
    skipped: '已跳过',
    error: '失败',
  };
  return map[s];
}

function clearSelection() {
  selectedRowKeys.value = [];
  selectedRows.value = [];
}

function buildRowActions(record: NfsFileEntry) {
  const actions: Array<Record<string, unknown>> = [];
  if (record.directory) {
    actions.push({
      label: '打开',
      icon: 'ant-design:folder-open-outlined',
      onClick: () => goPath(record.relativePath),
    });
  } else {
    actions.push({
      label: '下载',
      icon: 'ant-design:download-outlined',
      loading: downloading.value === record.relativePath,
      onClick: () => download(record),
    });
  }
  actions.push({
    label: '重命名',
    icon: 'ant-design:edit-outlined',
    onClick: () => openRename(record),
  });
  actions.push({
    label: '删除',
    icon: 'material-symbols:delete-outline-rounded',
    danger: true,
    popConfirm: {
      placement: 'topRight',
      title: record.directory
        ? `确认删除目录「${record.name}」及其全部内容？不可恢复。`
        : `确认删除文件「${record.name}」？不可恢复。`,
      confirm: () => runDelete(record),
    },
  });
  return actions;
}

function resolveConflict(v: 'overwrite' | 'skip' | 'cancel') {
  closeConflictModal();
  const resolver = conflictResolve;
  conflictResolve = null;
  resolver?.(v);
}

function waitConflict(names: string[]) {
  conflictNames.value = names;
  openConflictModal(true);
  return new Promise<'overwrite' | 'skip' | 'cancel'>((resolve) => {
    conflictResolve = resolve;
  });
}

async function reload() {
  if (!currentNodeId.value) {
    list.value = null;
    clearSelection();
    return;
  }
  loading.value = true;
  try {
    list.value = await listNfsMediaFiles(currentNodeId.value, relativePath.value);
    clearSelection();
  } catch (e: any) {
    list.value = null;
    createMessage.error(e?.message || '列出文件失败');
  } finally {
    loading.value = false;
  }
}

function goPath(path?: string) {
  keyword.value = '';
  relativePath.value = path || '';
}

function goUp() {
  const parts = breadcrumbs.value;
  if (!parts.length) return;
  goPath(parts.slice(0, -1).join('/'));
}

async function copyCurrentPath() {
  const text = absolutePathDisplay.value;
  try {
    await navigator.clipboard.writeText(text);
    createMessage.success('路径已复制');
  } catch {
    createMessage.info(text);
  }
}

function openMkdir() {
  mkdirName.value = '';
  openMkdirModal(true);
}

async function submitMkdir() {
  if (!currentNodeId.value) return;
  const name = mkdirName.value.trim();
  if (!name) {
    createMessage.warning('请输入目录名');
    return;
  }
  setMkdirProps({ confirmLoading: true });
  try {
    const r = await mkdirNfsMediaDir(currentNodeId.value, name, relativePath.value);
    createMessage.success(r.message || '目录已创建');
    closeMkdirModal();
    await reload();
  } catch (e: any) {
    createMessage.error(e?.message || '创建失败');
  } finally {
    setMkdirProps({ confirmLoading: false });
  }
}

function openRename(record: NfsFileEntry) {
  renameTarget.value = record;
  renameName.value = record.name || '';
  openRenameModal(true);
}

async function submitRename() {
  if (!currentNodeId.value || !renameTarget.value?.relativePath) return;
  const name = renameName.value.trim();
  if (!name) {
    createMessage.warning('请输入新名称');
    return;
  }
  if (name === renameTarget.value.name) {
    closeRenameModal();
    return;
  }
  setRenameProps({ confirmLoading: true });
  try {
    const r = await renameNfsMediaPath(currentNodeId.value, renameTarget.value.relativePath, name);
    createMessage.success(r.message || '已重命名');
    closeRenameModal();
    await reload();
  } catch (e: any) {
    createMessage.error(e?.message || '重命名失败');
  } finally {
    setRenameProps({ confirmLoading: false });
  }
}

function findExistingByName(name: string) {
  return sortedEntries.value.find((e) => e.name === name);
}

async function runUploadBatch(files: File[]) {
  if (!currentNodeId.value || !files.length) return;

  const valid: File[] = [];
  for (const f of files) {
    if (f.size > MAX_UPLOAD_BYTES) {
      createMessage.error(`${f.name} 超过 50MB，已忽略`);
      continue;
    }
    valid.push(f);
  }
  if (!valid.length) return;

  const dirConflicts = valid.filter((f) => findExistingByName(f.name)?.directory);
  if (dirConflicts.length) {
    createMessage.error(`无法上传：与目录同名 — ${dirConflicts.map((f) => f.name).join('、')}`);
    return;
  }

  const conflicts = valid.filter((f) => {
    const exist = findExistingByName(f.name);
    return exist && !exist.directory;
  });

  let mode: 'overwrite' | 'skip' | 'all' = 'all';
  if (conflicts.length) {
    const action = await waitConflict(conflicts.map((f) => f.name));
    if (action === 'cancel') return;
    mode = action;
  }

  const jobs: UploadJob[] = valid.map((f, i) => ({
    id: `${Date.now()}-${i}-${f.name}`,
    name: f.name,
    file: f,
    status: 'pending',
  }));
  uploadJobs.value = jobs;
  uploading.value = true;

  try {
    for (const job of jobs) {
      const exist = findExistingByName(job.name);
      if (exist && !exist.directory && mode === 'skip') {
        job.status = 'skipped';
        job.message = '同名已跳过';
        continue;
      }
      job.status = 'uploading';
      try {
        const r = await uploadNfsMediaFile(currentNodeId.value!, job.file, relativePath.value);
        job.status = 'done';
        job.message = r.message;
      } catch (e: any) {
        job.status = 'error';
        job.message = e?.message || '上传失败';
      }
    }
    const ok = jobs.filter((j) => j.status === 'done').length;
    const skip = jobs.filter((j) => j.status === 'skipped').length;
    const fail = jobs.filter((j) => j.status === 'error').length;
    if (fail) createMessage.warning(`上传结束：成功 ${ok}，跳过 ${skip}，失败 ${fail}`);
    else createMessage.success(`上传完成：成功 ${ok}${skip ? `，跳过 ${skip}` : ''}`);
    await reload();
  } finally {
    uploading.value = false;
  }
}

function beforeUpload(file: File) {
  pendingUploadFiles.value.push(file);
  if (uploadFlushTimer) clearTimeout(uploadFlushTimer);
  uploadFlushTimer = setTimeout(() => {
    const batch = pendingUploadFiles.value.slice();
    pendingUploadFiles.value = [];
    runUploadBatch(batch);
  }, 80);
  return false;
}

function onDragLeave(ev: DragEvent) {
  const el = ev.currentTarget as HTMLElement | null;
  const related = ev.relatedTarget as Node | null;
  if (el && related && el.contains(related)) return;
  dragOver.value = false;
}

async function onDrop(ev: DragEvent) {
  dragOver.value = false;
  const files = Array.from(ev.dataTransfer?.files || []);
  if (!files.length) return;
  await runUploadBatch(files);
}

async function download(record: NfsFileEntry) {
  if (!currentNodeId.value || !record.relativePath) return;
  downloading.value = record.relativePath;
  try {
    const blob = await downloadNfsMediaFile(currentNodeId.value, record.relativePath);
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = record.name || 'file';
    a.click();
    URL.revokeObjectURL(url);
  } catch (e: any) {
    createMessage.error(e?.message || '下载失败');
  } finally {
    downloading.value = null;
  }
}

async function runDelete(record: NfsFileEntry) {
  if (!currentNodeId.value || !record.relativePath) return;
  try {
    const r = await deleteNfsMediaPath(currentNodeId.value, record.relativePath);
    createMessage.success(r.message || '已删除');
    await reload();
  } catch (e: any) {
    createMessage.error(e?.message || '删除失败');
  }
}

async function runBatchDelete() {
  if (!currentNodeId.value || !selectedRows.value.length) return;
  batchDeleting.value = true;
  let ok = 0;
  let fail = 0;
  try {
    for (const row of selectedRows.value) {
      if (!row.relativePath) continue;
      try {
        await deleteNfsMediaPath(currentNodeId.value!, row.relativePath);
        ok += 1;
      } catch {
        fail += 1;
      }
    }
    if (fail) createMessage.warning(`删除结束：成功 ${ok}，失败 ${fail}`);
    else createMessage.success(`已删除 ${ok} 项`);
    await reload();
  } finally {
    batchDeleting.value = false;
  }
}

watch(currentNodeId, () => {
  relativePath.value = '';
  keyword.value = '';
  uploadJobs.value = [];
  reload();
});

watch(relativePath, () => reload());

watch(
  () => props.initialNodeId,
  (id) => {
    if (!id) return;
    const hit = mountableNodes.value.find((n) => n.nodeId === id && canBrowseNode(n));
    if (hit) selectedIds.value = [id];
  },
);

onMounted(() => {
  loadMountableNodes();
});
</script>

<style scoped lang="less">
.nfs-file-ops {
  .node-picker {
    margin-bottom: 14px;
    padding: 14px 16px;
    border: 1px solid #f0f0f0;
    border-radius: 10px;
    background: #fafafa;
  }

  .node-picker__head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 12px;
  }

  .node-picker__title {
    font-size: 15px;
    font-weight: 600;
    color: #262626;
  }

  .node-chips-scroll {
    max-height: 280px;
  }

  .node-chips {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 10px;
  }

  .node-chip {
    cursor: pointer;
    border-color: #e8e8e8;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;

    :deep(.ant-card-body) {
      padding: 12px;
    }
  }

  .node-chip:hover:not(.is-disabled) {
    border-color: #91caff;
  }

  .node-chip.is-active {
    border-color: #1677ff;
    box-shadow: 0 0 0 2px rgba(22, 119, 255, 0.12);
  }

  .node-chip.is-disabled {
    opacity: 0.55;
    cursor: not-allowed;
  }

  .node-chip__name {
    font-weight: 600;
    color: #262626;
    margin-bottom: 6px;
  }

  .node-chip__meta {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    margin-bottom: 6px;
  }

  .node-chip__tag {
    margin: 0;
  }

  .node-chip__host {
    font-size: 12px;
    color: #8c8c8c;
    word-break: break-all;
  }

  .ops-empty {
    margin-top: 40px;
  }

  .path-panel {
    margin-bottom: 12px;
    padding: 14px 16px;
    border: 1px solid #f0f0f0;
    border-radius: 10px;
    background: #fff;
  }

  .path-panel__top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    flex-wrap: wrap;
    margin-bottom: 10px;
  }

  .path-panel__info {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 4px;
    min-width: 0;
  }

  .path-panel__node {
    margin-left: 8px;
    color: #595959;
    font-size: 13px;
  }

  .path-row__crumb {
    margin-bottom: 6px;
  }

  .path-abs {
    margin-bottom: 12px;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 12px;
    color: #595959;
    word-break: break-all;
  }

  .action-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    flex-wrap: wrap;
  }

  .filter-input {
    width: 260px;
    max-width: 100%;
  }

  .upload-panel {
    margin-bottom: 12px;
    padding: 12px 14px;
    border: 1px solid #f0f0f0;
    border-radius: 10px;
    background: #fff;
  }

  .upload-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;
  }

  .ops-hint {
    font-size: 12px;
    color: #8c8c8c;
  }

  .drop-zone {
    padding: 12px;
    border: 1px solid #f0f0f0;
    border-radius: 10px;
    background: #fff;
    transition: border-color 0.15s ease, background 0.15s ease;
  }

  .drop-zone--active {
    border-color: #1677ff;
    background: rgba(22, 119, 255, 0.06);
  }

  .drop-banner {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    margin-bottom: 12px;
    padding: 14px 12px;
    border: 1px dashed #d9d9d9;
    border-radius: 8px;
    color: #8c8c8c;
    font-size: 13px;
    text-align: center;
    background: #fafafa;
  }

  .name-link,
  .name-file {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-weight: 500;
  }

  .name-link__icon {
    color: #1677ff;
    flex-shrink: 0;
  }

  .name-file .name-link__icon {
    color: #8c8c8c;
  }

  .upload-list {
    margin-top: 8px;
    max-height: 160px;
    overflow: auto;
  }

  .upload-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 4px 0;
    font-size: 12px;
  }

  .upload-item__name {
    min-width: 140px;
    max-width: 40%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .upload-item__msg {
    color: #8c8c8c;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .modal-hint {
    margin-bottom: 8px;
    color: #666;
    font-size: 13px;
    word-break: break-all;
    white-space: pre-wrap;
  }

  .conflict-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 16px;
  }

  &.nfs-file-ops--manager {
    display: grid;
    grid-template-columns: 300px minmax(0, 1fr);
    gap: 16px;
    height: 100%;
    min-height: 0;

    .node-picker {
      margin-bottom: 0;
      height: 100%;
      min-height: 0;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    .node-chips-scroll {
      flex: 1;
      min-height: 0;
      max-height: none;
    }

    .node-chips {
      grid-template-columns: 1fr;
      padding-right: 2px;
      padding-bottom: 4px;
    }

    .file-main {
      display: flex;
      flex-direction: column;
      min-width: 0;
      min-height: 0;
      height: 100%;
    }

    .path-panel,
    .upload-panel {
      flex: none;
    }

    .drop-zone {
      flex: 1;
      min-height: 0;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    .table-wrap {
      flex: 1;
      min-height: 320px;
      overflow: hidden;

      :deep(.ant-table-placeholder) {
        min-height: 280px;
      }

      :deep(.vben-basic-table-action) {
        flex-wrap: wrap;
        justify-content: flex-start;
      }
    }

    .ops-empty {
      margin: auto;
    }

    .filter-input {
      width: 280px;
    }
  }
}

@media (max-width: 960px) {
  .nfs-file-ops.nfs-file-ops--manager {
    grid-template-columns: 1fr;
    height: auto;
    min-height: calc(100vh - 180px);

    .node-picker {
      max-height: 240px;
    }

    .node-chips {
      grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    }
  }
}
</style>
