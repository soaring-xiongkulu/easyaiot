<template>
  <div class="nfs-file-ops">
    <CollapseContainer
      title="选择节点"
      :can-expan="false"
      help-message="仅管理该节点媒体挂载根内的文件"
      class="mb-3"
    >
      <ClusterNodeSelector
        v-model:selected-node-ids="selectedIds"
        role-filter="cephClient"
        :show-scope-bar="false"
        :multiple="false"
        placeholder="选择已配置 SSH 的 NFS 客户端节点"
      />
    </CollapseContainer>

    <Empty
      v-if="!currentNodeId"
      class="ops-empty"
      description="先选择一个已挂载 NFS 的客户端节点，即可浏览与管理媒体文件"
    />

    <template v-else>
      <CollapseContainer title="当前位置" :can-expan="false" class="mb-3">
        <div v-if="list?.mountRoot" class="mount-tag-row">
          <Tag color="blue">挂载根 {{ list.mountRoot }}</Tag>
        </div>

        <div class="path-row">
          <Breadcrumb class="path-row__crumb">
            <Breadcrumb.Item>
              <a @click.prevent="goPath('')">媒体根</a>
            </Breadcrumb.Item>
            <Breadcrumb.Item v-for="(seg, idx) in breadcrumbs" :key="idx">
              <a @click.prevent="goPath(breadcrumbs.slice(0, idx + 1).join('/'))">{{ seg }}</a>
            </Breadcrumb.Item>
          </Breadcrumb>
          <Space wrap size="small">
            <Button size="small" :disabled="!relativePath" @click="goUp">上级目录</Button>
            <Button size="small" @click="copyCurrentPath">复制路径</Button>
            <Button size="small" :loading="loading" @click="reload">刷新</Button>
          </Space>
        </div>
        <div class="path-abs">{{ absolutePathDisplay }}</div>

        <div class="action-row">
          <Space wrap>
            <Button type="primary" ghost @click="openMkdir">新建目录</Button>
            <Upload
              :show-upload-list="false"
              :before-upload="beforeUpload"
              :disabled="uploading"
              multiple
            >
              <Button type="primary" :loading="uploading">上传文件</Button>
            </Upload>
            <Button
              danger
              :disabled="!selectedRows.length"
              :loading="batchDeleting"
              @click="confirmBatchDelete"
            >
              删除所选（{{ selectedRows.length }}）
            </Button>
          </Space>
          <Input
            v-model:value="keyword"
            allow-clear
            placeholder="过滤当前目录（名称）"
            class="filter-input"
          />
        </div>
      </CollapseContainer>

      <CollapseContainer v-if="uploadJobs.length" title="上传进度" :can-expan="false" class="mb-3">
        <div class="upload-head">
          <span class="ops-hint">
            {{ uploadDoneCount }}/{{ uploadJobs.length }}
            <template v-if="uploadFailCount"> · 失败 {{ uploadFailCount }}</template>
          </span>
          <Button v-if="!uploading" type="link" size="small" @click="uploadJobs = []">清除</Button>
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
      </CollapseContainer>

      <div
        class="drop-zone"
        :class="{ 'drop-zone--active': dragOver }"
        @dragover.prevent="dragOver = true"
        @dragleave.prevent="onDragLeave"
        @drop.prevent="onDrop"
      >
        <div class="drop-banner">
          拖拽文件到此处即可上传（单文件 ≤50MB；同名会先确认是否覆盖）
        </div>

        <Table
          size="middle"
          row-key="relativePath"
          :loading="loading"
          :pagination="tablePagination"
          :data-source="filteredEntries"
          :columns="columns"
          :row-selection="rowSelection"
          :locale="{ emptyText: emptyText }"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'name'">
              <a v-if="record.directory" class="name-link" @click.prevent="goPath(record.relativePath)">
                {{ record.name }}/
              </a>
              <span v-else>{{ record.name }}</span>
            </template>
            <template v-else-if="column.key === 'size'">
              {{ record.directory ? '-' : formatSize(record.size) }}
            </template>
            <template v-else-if="column.key === 'mtime'">
              {{ formatMtime(record.mtime) }}
            </template>
            <template v-else-if="column.key === 'action'">
              <Space :size="0">
                <Button
                  v-if="record.directory"
                  type="link"
                  size="small"
                  @click="goPath(record.relativePath)"
                >
                  打开
                </Button>
                <Button
                  v-else
                  type="link"
                  size="small"
                  :loading="downloading === record.relativePath"
                  @click="download(record)"
                >
                  下载
                </Button>
                <Button type="link" size="small" @click="openRename(record)">重命名</Button>
                <Button
                  type="link"
                  size="small"
                  danger
                  :loading="deleting === record.relativePath"
                  @click="confirmDelete(record)"
                >
                  删除
                </Button>
              </Space>
            </template>
          </template>
        </Table>
      </div>
    </template>

    <Modal
      v-model:open="mkdirOpen"
      title="新建目录"
      ok-text="创建"
      cancel-text="取消"
      :confirm-loading="mkdirLoading"
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
    </Modal>

    <Modal
      v-model:open="renameOpen"
      title="重命名"
      ok-text="确定"
      cancel-text="取消"
      :confirm-loading="renameLoading"
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
    </Modal>

    <Modal
      v-model:open="conflictOpen"
      title="发现同名文件"
      :footer="null"
      :closable="true"
      destroy-on-close
      @cancel="resolveConflict('cancel')"
    >
      <div class="modal-hint">
        已存在：{{ conflictNames.slice(0, 10).join('、')
        }}{{ conflictNames.length > 10 ? '…' : '' }}
      </div>
      <div class="conflict-actions">
        <Button danger type="primary" @click="resolveConflict('overwrite')">覆盖这些文件</Button>
        <Button @click="resolveConflict('skip')">跳过同名，只传新文件</Button>
        <Button @click="resolveConflict('cancel')">取消全部</Button>
      </div>
    </Modal>
  </div>
</template>

<script lang="ts" setup>
import { computed, ref, watch } from 'vue';
import {
  Breadcrumb,
  Empty,
  Input,
  Modal,
  Progress,
  Space,
  Table,
  Tag,
  Upload,
} from 'ant-design-vue';
import type { TableProps } from 'ant-design-vue';
import { Button } from '@/components/Button';
import { CollapseContainer } from '@/components/Container';
import { useMessage } from '@/hooks/web/useMessage';
import {
  deleteNfsMediaPath,
  downloadNfsMediaFile,
  listNfsMediaFiles,
  mkdirNfsMediaDir,
  renameNfsMediaPath,
  uploadNfsMediaFile,
  type NfsFileEntry,
  type NfsFileListResult,
} from '@/api/device/node';
import ClusterNodeSelector from '../ClusterNodeSelector/index.vue';

defineOptions({ name: 'NfsFileBrowser' });

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
const selectedIds = ref<number[]>([]);
const relativePath = ref('');
const keyword = ref('');
const loading = ref(false);
const uploading = ref(false);
const batchDeleting = ref(false);
const dragOver = ref(false);
const mkdirOpen = ref(false);
const mkdirLoading = ref(false);
const mkdirName = ref('');
const renameOpen = ref(false);
const renameLoading = ref(false);
const renameName = ref('');
const renameTarget = ref<NfsFileEntry | null>(null);
const conflictOpen = ref(false);
const conflictNames = ref<string[]>([]);
let conflictResolve: ((v: 'overwrite' | 'skip' | 'cancel') => void) | null = null;
const downloading = ref<string | null>(null);
const deleting = ref<string | null>(null);
const list = ref<NfsFileListResult | null>(null);
const selectedRowKeys = ref<string[]>([]);
const selectedRows = ref<NfsFileEntry[]>([]);
const uploadJobs = ref<UploadJob[]>([]);
const pendingUploadFiles = ref<File[]>([]);
let uploadFlushTimer: ReturnType<typeof setTimeout> | null = null;

const currentNodeId = computed(() => selectedIds.value[0] || null);

const breadcrumbs = computed(() =>
  relativePath.value ? relativePath.value.split('/').filter(Boolean) : [],
);

const absolutePathDisplay = computed(() => {
  const root = (list.value?.mountRoot || '').replace(/\/+$/, '') || '（加载中…）';
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
  if (keyword.value.trim()) return '没有匹配的文件，试试清空过滤条件';
  return '当前目录为空，可新建目录或拖拽/上传文件';
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

function resolveConflict(v: 'overwrite' | 'skip' | 'cancel') {
  conflictOpen.value = false;
  const resolver = conflictResolve;
  conflictResolve = null;
  resolver?.(v);
}

function waitConflict(names: string[]) {
  conflictNames.value = names;
  conflictOpen.value = true;
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
  mkdirOpen.value = true;
}

async function submitMkdir() {
  if (!currentNodeId.value) return;
  const name = mkdirName.value.trim();
  if (!name) {
    createMessage.warning('请输入目录名');
    return;
  }
  mkdirLoading.value = true;
  try {
    const r = await mkdirNfsMediaDir(currentNodeId.value, name, relativePath.value);
    createMessage.success(r.message || '目录已创建');
    mkdirOpen.value = false;
    await reload();
  } catch (e: any) {
    createMessage.error(e?.message || '创建失败');
  } finally {
    mkdirLoading.value = false;
  }
}

function openRename(record: NfsFileEntry) {
  renameTarget.value = record;
  renameName.value = record.name || '';
  renameOpen.value = true;
}

async function submitRename() {
  if (!currentNodeId.value || !renameTarget.value?.relativePath) return;
  const name = renameName.value.trim();
  if (!name) {
    createMessage.warning('请输入新名称');
    return;
  }
  if (name === renameTarget.value.name) {
    renameOpen.value = false;
    return;
  }
  renameLoading.value = true;
  try {
    const r = await renameNfsMediaPath(currentNodeId.value, renameTarget.value.relativePath, name);
    createMessage.success(r.message || '已重命名');
    renameOpen.value = false;
    await reload();
  } catch (e: any) {
    createMessage.error(e?.message || '重命名失败');
  } finally {
    renameLoading.value = false;
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

function confirmDelete(record: NfsFileEntry) {
  if (!currentNodeId.value || !record.relativePath) return;
  const tip = record.directory
    ? `确认删除目录「${record.name}」及其全部内容？不可恢复。`
    : `确认删除文件「${record.name}」？不可恢复。`;
  Modal.confirm({
    title: '确认删除',
    content: tip,
    okText: '删除',
    okType: 'danger',
    cancelText: '取消',
    onOk: async () => {
      deleting.value = record.relativePath || null;
      try {
        const r = await deleteNfsMediaPath(currentNodeId.value!, record.relativePath!);
        createMessage.success(r.message || '已删除');
        await reload();
      } catch (e: any) {
        createMessage.error(e?.message || '删除失败');
        throw e;
      } finally {
        deleting.value = null;
      }
    },
  });
}

function confirmBatchDelete() {
  if (!currentNodeId.value || !selectedRows.value.length) return;
  const names = selectedRows.value.map((r) => r.name).slice(0, 8);
  Modal.confirm({
    title: `删除所选 ${selectedRows.value.length} 项`,
    content: `${names.join('、')}${selectedRows.value.length > 8 ? '…' : ''}。目录会递归删除，不可恢复。`,
    okText: '删除',
    okType: 'danger',
    cancelText: '取消',
    onOk: async () => {
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
    },
  });
}

watch(currentNodeId, () => {
  relativePath.value = '';
  keyword.value = '';
  uploadJobs.value = [];
  reload();
});

watch(relativePath, () => reload());
</script>

<style scoped lang="less">
.nfs-file-ops {
  .mb-3 {
    margin-bottom: 12px;
  }

  .ops-hint {
    font-size: 12px;
    color: #8c8c8c;
    margin-right: 8px;
  }

  .mount-tag-row {
    margin-bottom: 8px;
  }

  .upload-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;
  }

  .ops-empty {
    margin-top: 48px;
  }

  .path-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    flex-wrap: wrap;
  }

  .path-row__crumb {
    flex: 1;
    min-width: 200px;
  }

  .path-abs {
    margin-top: 6px;
    margin-bottom: 10px;
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
    width: 240px;
    max-width: 100%;
  }

  .drop-zone {
    padding: 12px;
    border: 1px solid #f0f0f0;
    border-radius: 6px;
    background: #fff;
    transition: border-color 0.15s ease, background 0.15s ease;
  }

  .drop-zone--active {
    border-color: #1677ff;
    background: rgba(22, 119, 255, 0.06);
  }

  .drop-banner {
    margin-bottom: 10px;
    padding: 8px 10px;
    border: 1px dashed #d9d9d9;
    border-radius: 6px;
    color: #8c8c8c;
    font-size: 12px;
    text-align: center;
    background: #fafafa;
  }

  .name-link {
    font-weight: 500;
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
}
</style>
