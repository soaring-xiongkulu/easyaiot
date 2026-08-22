<template>
  <div class="post-plugin-page">
    <div class="toolbar">
      <a-space>
        <a-button type="primary" @click="openRegister">登记插件</a-button>
        <a-button @click="load">刷新</a-button>
      </a-space>
      <span class="hint">
        登记并启动插件后，可在算法任务「后处理规则」中引用。内置的区域闸门、越线检测、区域进出、停留超时、人数阈值、放行、用户脚本无需登记。
      </span>
    </div>
    <a-table
      :columns="columns"
      :data-source="list"
      :loading="loading"
      row-key="id"
      :pagination="false"
      size="middle"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'enabled'">
          <a-switch :checked="record.enabled" @change="(v: boolean) => onToggle(record, v)" />
        </template>
        <template v-else-if="column.key === 'status'">
          <a-tag :color="statusColor(record.service?.status)">
            {{ record.service?.status || 'stopped' }}
          </a-tag>
          <span v-if="record.service?.replicas" class="muted"> ×{{ record.service.replicas }}</span>
        </template>
        <template v-else-if="column.key === 'endpoint'">
          <span class="mono">{{ record.service?.endpoint || '—' }}</span>
        </template>
        <template v-else-if="column.key === 'action'">
          <a-space wrap>
            <a-button size="small" type="link" @click="openManifest(record)">详情</a-button>
            <a-button size="small" type="link" @click="openRefs(record)">引用</a-button>
            <a-button size="small" type="link" @click="openStart(record)">启动</a-button>
            <a-button size="small" type="link" @click="onStop(record)">停止</a-button>
            <a-button size="small" type="link" @click="openScale(record)">扩缩</a-button>
            <a-popconfirm title="确认卸载？" @confirm="onDelete(record)">
              <a-button size="small" type="link" danger>卸载</a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>

    <a-modal
      v-model:open="regOpen"
      title="登记插件"
      @ok="submitRegister"
      :confirm-loading="saving"
      width="720px"
    >
      <a-form layout="vertical">
        <a-form-item label="插件描述 JSON" required>
          <a-textarea v-model:value="regManifest" :rows="14" class="mono" />
        </a-form-item>
        <a-form-item label="服务地址（可选，联调用）">
          <a-input v-model:value="regEndpoint" placeholder="http://127.0.0.1:8091" />
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal
      v-model:open="startOpen"
      title="启动插件服务"
      @ok="submitStart"
      :confirm-loading="saving"
      width="560px"
    >
      <a-form layout="vertical">
        <a-form-item label="部署模式">
          <a-radio-group v-model:value="startMode">
            <a-radio value="endpoint">指定服务地址</a-radio>
            <a-radio value="docker">部署到计算节点</a-radio>
          </a-radio-group>
        </a-form-item>
        <a-form-item v-if="startMode === 'endpoint'" label="服务地址" required>
          <a-input v-model:value="startEndpoint" placeholder="http://host:8091" />
        </a-form-item>
        <a-form-item v-else label="目标计算节点" required>
          <a-select
            v-model:value="startNodeId"
            show-search
            allow-clear
            placeholder="选择在线算法节点"
            :options="nodeOptions"
            :filter-option="filterNode"
            style="width: 100%"
          />
        </a-form-item>
        <a-form-item label="副本数">
          <a-input-number v-model:value="startReplicas" :min="1" :max="16" style="width: 100%" />
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal v-model:open="scaleOpen" title="扩缩副本" @ok="submitScale" :confirm-loading="saving">
      <a-input-number v-model:value="scaleReplicas" :min="1" :max="16" style="width: 100%" />
    </a-modal>

    <a-modal v-model:open="manifestOpen" title="插件详情" :footer="null" width="720px">
      <pre class="debug-out mono">{{ manifestText }}</pre>
    </a-modal>

    <a-modal v-model:open="refsOpen" :title="`任务引用 · ${refsPluginId}`" :footer="null" width="640px">
      <a-spin :spinning="refsLoading">
        <a-empty v-if="!refsLoading && !refsList.length" description="暂无任务引用该插件" />
        <a-table
          v-else
          size="small"
          :pagination="false"
          row-key="id"
          :data-source="refsList"
          :columns="refColumns"
        />
      </a-spin>
    </a-modal>
  </div>
</template>

<script lang="ts" setup>
import { onMounted, ref } from 'vue';
import { useMessage } from '@/hooks/web/useMessage';
import {
  deletePostPlugin,
  listPostPluginTasks,
  listPostPlugins,
  registerPostPlugin,
  scalePostPlugin,
  startPostPlugin,
  stopPostPlugin,
  updatePostPlugin,
  type PostPluginItem,
  type PostPluginTaskRef,
} from '@/api/device/post_plugin';
import { getNodePage } from '@/api/device/node';
import { nodeHasFunction } from '@/views/node/utils/constants';

defineOptions({ name: 'PostPluginManage' });

const { createMessage } = useMessage();
const loading = ref(false);
const saving = ref(false);
const list = ref<PostPluginItem[]>([]);
const nodeOptions = ref<{ label: string; value: number }[]>([]);

const columns = [
  { title: '插件 ID', dataIndex: 'id', key: 'id', width: 160 },
  { title: '名称', dataIndex: 'name', key: 'name', width: 140 },
  { title: '版本', dataIndex: 'latest_version', key: 'latest_version', width: 90 },
  { title: 'Runtime', dataIndex: 'runtime', key: 'runtime', width: 80 },
  { title: '启用', key: 'enabled', width: 70 },
  { title: '状态', key: 'status', width: 120 },
  { title: '服务地址', key: 'endpoint', ellipsis: true },
  { title: '操作', key: 'action', width: 320 },
];

const refColumns = [
  { title: '任务 ID', dataIndex: 'id', width: 90 },
  { title: '名称', dataIndex: 'task_name' },
  { title: '类型', dataIndex: 'task_type', width: 90 },
  { title: '运行态', dataIndex: 'run_status', width: 100 },
  {
    title: '启用',
    dataIndex: 'is_enabled',
    width: 70,
    customRender: ({ text }: any) => (text ? '是' : '否'),
  },
];

const regOpen = ref(false);
const regManifest = ref('');
const regEndpoint = ref('');

const startOpen = ref(false);
const startTarget = ref<PostPluginItem | null>(null);
const startMode = ref<'endpoint' | 'docker'>('endpoint');
const startEndpoint = ref('');
const startReplicas = ref(1);
const startNodeId = ref<number | undefined>(undefined);

const scaleOpen = ref(false);
const scaleTarget = ref<PostPluginItem | null>(null);
const scaleReplicas = ref(1);

const manifestOpen = ref(false);
const manifestText = ref('');

const refsOpen = ref(false);
const refsLoading = ref(false);
const refsPluginId = ref('');
const refsList = ref<PostPluginTaskRef[]>([]);

const ECHO_SAMPLE = `{
  "spec_version": "1",
  "id": "acme.echo",
  "name": "Echo Enrich",
  "version": "1.0.0",
  "kinds": ["enrich"],
  "runtime": "http",
  "entrypoint": {
    "image": "easyaiot/post-plugin-echo:1.0.0",
    "port": 8091,
    "path": "/v1/process",
    "health": "/healthz",
    "timeout_ms": 2000
  },
  "scaling": { "min_replicas": 1, "max_replicas": 4, "stateless": true }
}`;

function statusColor(st?: string) {
  if (st === 'running') return 'green';
  if (st === 'error' || st === 'failed') return 'red';
  return 'default';
}

function filterNode(input: string, option: any) {
  return String(option?.label || '')
    .toLowerCase()
    .includes(String(input || '').toLowerCase());
}

async function loadNodes() {
  try {
    const res = await getNodePage({ pageNo: 1, pageSize: 200, status: 'online' });
    const page = (res as any)?.data || res;
    const rows = (page?.list || []).filter((node: any) => nodeHasFunction(node, 'algorithm'));
    nodeOptions.value = rows.map((node: any) => ({
      label: `${node.name} (${node.host})`,
      value: node.id,
    }));
  } catch {
    nodeOptions.value = [];
  }
}

async function load() {
  loading.value = true;
  try {
    const data = await listPostPlugins();
    list.value = Array.isArray(data) ? data : (data as any)?.data || [];
  } catch (e: any) {
    createMessage.error(e?.message || '加载失败');
  } finally {
    loading.value = false;
  }
}

function openRegister() {
  regManifest.value = ECHO_SAMPLE;
  regEndpoint.value = '';
  regOpen.value = true;
}

async function submitRegister() {
  saving.value = true;
  try {
    let manifest: Record<string, any>;
    try {
      manifest = JSON.parse(regManifest.value);
    } catch {
      createMessage.error('插件描述不是合法 JSON');
      return;
    }
    if (!manifest?.id) {
      createMessage.error('插件描述缺少 id');
      return;
    }
    await registerPostPlugin({
      manifest,
      endpoint: regEndpoint.value.trim() || undefined,
    });
    createMessage.success('已登记');
    regOpen.value = false;
    await load();
  } catch (e: any) {
    createMessage.error(e?.message || '登记失败');
  } finally {
    saving.value = false;
  }
}

async function onToggle(record: PostPluginItem, enabled: boolean) {
  try {
    await updatePostPlugin(record.id, { enabled });
    createMessage.success(enabled ? '已启用' : '已禁用');
    await load();
  } catch (e: any) {
    createMessage.error(e?.message || '更新失败');
  }
}

function openManifest(record: PostPluginItem) {
  manifestText.value = JSON.stringify(record.manifest || {}, null, 2);
  manifestOpen.value = true;
}

async function openRefs(record: PostPluginItem) {
  refsPluginId.value = record.id;
  refsOpen.value = true;
  refsLoading.value = true;
  refsList.value = [];
  try {
    const data = await listPostPluginTasks(record.id);
    refsList.value = Array.isArray(data) ? data : (data as any)?.data || [];
  } catch (e: any) {
    createMessage.error(e?.message || '加载引用失败');
  } finally {
    refsLoading.value = false;
  }
}

function openStart(record: PostPluginItem) {
  startTarget.value = record;
  startMode.value = (record.service?.deploy_mode as any) === 'docker' ? 'docker' : 'endpoint';
  startEndpoint.value = record.service?.endpoint || '';
  startReplicas.value = record.service?.replicas || 1;
  const bindingNode = record.service?.binding?.target_node_id || record.service?.binding?.node_id;
  startNodeId.value = bindingNode ? Number(bindingNode) : undefined;
  startOpen.value = true;
  if (!nodeOptions.value.length) loadNodes();
}

async function submitStart() {
  if (!startTarget.value) return;
  if (startMode.value === 'endpoint' && !startEndpoint.value.trim()) {
    createMessage.warning('请填写服务地址');
    return;
  }
  if (startMode.value === 'docker' && !startNodeId.value) {
    createMessage.warning('请选择目标计算节点');
    return;
  }
  saving.value = true;
  try {
    await startPostPlugin(startTarget.value.id, {
      deploy_mode: startMode.value,
      endpoint: startMode.value === 'endpoint' ? startEndpoint.value.trim() : undefined,
      replicas: startReplicas.value,
      target_node_id: startMode.value === 'docker' ? startNodeId.value : undefined,
    });
    createMessage.success('已启动');
    startOpen.value = false;
    await load();
  } catch (e: any) {
    createMessage.error(e?.message || '启动失败');
  } finally {
    saving.value = false;
  }
}

async function onStop(record: PostPluginItem) {
  try {
    await stopPostPlugin(record.id);
    createMessage.success('已停止');
    await load();
  } catch (e: any) {
    createMessage.error(e?.message || '停止失败');
  }
}

function openScale(record: PostPluginItem) {
  scaleTarget.value = record;
  scaleReplicas.value = record.service?.replicas || 1;
  scaleOpen.value = true;
}

async function submitScale() {
  if (!scaleTarget.value) return;
  saving.value = true;
  try {
    await scalePostPlugin(scaleTarget.value.id, scaleReplicas.value);
    createMessage.success('已更新副本');
    scaleOpen.value = false;
    await load();
  } catch (e: any) {
    createMessage.error(e?.message || '扩缩失败');
  } finally {
    saving.value = false;
  }
}

async function onDelete(record: PostPluginItem) {
  try {
    await deletePostPlugin(record.id, true);
    createMessage.success('已卸载');
    await load();
  } catch (e: any) {
    createMessage.error(e?.message || '卸载失败');
  }
}

onMounted(() => {
  load();
  loadNodes();
});
</script>

<style scoped>
.post-plugin-page {
  padding: 16px;
}
.toolbar {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.hint,
.muted {
  color: #666;
  font-size: 13px;
}
.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 12px;
}
.debug-out {
  max-height: 480px;
  overflow: auto;
  background: #f5f5f5;
  padding: 8px;
  border-radius: 4px;
}
</style>
