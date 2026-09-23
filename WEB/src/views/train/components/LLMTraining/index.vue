<template>
  <div class="rag-page">
    <!-- 页头：定位说明 + 向量库运行状态 -->
    <div class="page-heading">
      <div class="page-heading__text">
        <h2>RAG 知识与专家</h2>
        <p>
          文档沉淀为可追溯的知识片段，组成知识集后编排成 RAG 专家；
          在「算法任务 · 大模型后处理规则」中绑定专家，告警研判即自动携带知识库上下文
        </p>
      </div>
      <a-tooltip :title="healthTooltip">
        <span class="health-pill" :class="health?.ok ? 'is-ok' : 'is-bad'">
          <span class="health-pill__dot" />
          {{ health?.ok ? '向量库正常' : '向量库异常' }}
        </span>
      </a-tooltip>
    </div>

    <!-- 检索底座透明化：Embedding 未配置时明确告知降级影响与解法 -->
    <a-alert v-if="health?.embedding_mode === 'local-hash'" class="emb-alert" type="warning" show-icon>
      <template #message>
        当前使用<b>词频降级检索</b>（未配置 Embedding 服务）：知识可正常入库与召回，但只能按字词匹配、无法理解语义。
        在 AI 服务环境变量配置 RAG_EMBEDDING_BASE_URL 与 RAG_EMBEDDING_MODEL 后，新向量自动切换为语义检索。
      </template>
    </a-alert>

    <!-- 统计条：点击切换页签，同时充当流程导航 -->
    <div class="stat-strip">
      <button
        v-for="stat in stats"
        :key="stat.key"
        class="stat-strip__item"
        :class="{ active: view === stat.key }"
        type="button"
        @click="view = stat.key"
      >
        <span class="stat-strip__num">{{ stat.count }}</span>
        <span class="stat-strip__label">
          {{ stat.label }}
          <em v-if="stat.sub">{{ stat.sub }}</em>
        </span>
      </button>
    </div>

    <a-tabs v-model:activeKey="view" class="rag-tabs" destroy-inactive-tab-pane>
      <!-- ==================== 知识文档 ==================== -->
      <a-tab-pane key="documents" tab="知识文档">
        <div class="pane">
          <div class="pane__head">
            <div class="pane__head-text">
              <h3>知识文档</h3>
              <p>上传知识来源，平台自动解析为候选片段，再到「知识片段」人工审核标注</p>
            </div>
            <div class="pane__head-actions">
              <a-input v-model:value="keyword" allow-clear placeholder="搜索文档名称" class="w-240" />
              <a-button type="primary" @click="uploadOpen = true">
                <template #icon><UploadOutlined /></template>
                导入文档
              </a-button>
            </div>
          </div>

          <a-empty v-if="!filteredDocuments.length" class="pane__empty" description="暂无知识文档，先导入一份 TXT / Markdown 试试" />

          <div v-else class="doc-grid">
            <article v-for="item in filteredDocuments" :key="item.id" class="doc-card">
              <header class="doc-card__head">
                <div class="doc-card__icon"><FileTextOutlined /></div>
                <div class="doc-card__title-box">
                  <h3 :title="item.name">{{ item.name }}</h3>
                  <span class="doc-card__time">{{ formatTime(item.updated_at) }}</span>
                </div>
              </header>
              <div class="doc-card__metrics">
                <div><b>{{ formatChars(item.char_count) }}</b><small>字符</small></div>
                <div><b>{{ item.segment_count }}</b><small>片段</small></div>
                <div><b>{{ item.enabled_segment_count }}</b><small>参与检索</small></div>
              </div>
              <footer class="doc-card__foot">
                <a-button type="link" size="small" @click="openDocument(item)">
                  <template #icon><EyeOutlined /></template>
                  查看与标注
                </a-button>
                <a-popconfirm
                  title="删除文档会同时删除其片段并解除知识集引用，确定删除？"
                  ok-text="删除"
                  cancel-text="取消"
                  @confirm="removeDocument(item)"
                >
                  <a-button danger type="text" size="small">
                    <template #icon><DeleteOutlined /></template>
                  </a-button>
                </a-popconfirm>
              </footer>
            </article>
          </div>
        </div>
      </a-tab-pane>

      <!-- ==================== 知识片段 ==================== -->
      <a-tab-pane key="segments" tab="知识片段">
        <div class="pane">
          <SegmentWorkbench :segments="segments" :documents="documents" @changed="refresh" @create-set="handleCreateSet" />
        </div>
      </a-tab-pane>

      <!-- ==================== 知识集 ==================== -->
      <a-tab-pane key="sets" tab="知识集">
        <div class="pane">
          <KnowledgeSetPanel ref="setPanelRef" :sets="sets" :segments="segments" :documents="documents" @changed="refresh" />
        </div>
      </a-tab-pane>

      <!-- ==================== RAG 专家 ==================== -->
      <a-tab-pane key="experts" tab="RAG 专家">
        <div class="pane">
          <ExpertPanel :experts="experts" :sets="sets" @changed="refresh" />
        </div>
      </a-tab-pane>
    </a-tabs>

    <!-- 导入文档 -->
    <a-drawer v-model:open="uploadOpen" width="720" title="导入知识文档" destroy-on-close>
      <div class="upload-intro">
        <div class="upload-intro__icon"><FileTextOutlined /></div>
        <div>
          <b>导入知识来源</b>
          <p>平台按段落语义切片并逐块向量化，生成候选知识片段；建议上传前先按主题整理文档结构，单篇过长时拆分为多个文档更利于检索。</p>
        </div>
      </div>
      <a-upload-dragger
        class="large-upload"
        :show-upload-list="false"
        :accept="RAG_UPLOAD_ACCEPT"
        :before-upload="handleUpload"
      >
        <p class="ant-upload-drag-icon"><InboxOutlined /></p>
        <p class="ant-upload-text">点击或拖拽知识文档到此处</p>
        <p class="ant-upload-hint">TXT / Markdown / CSV / JSON / LOG · UTF-8 编码 · 单个不超过 {{ RAG_UPLOAD_MAX_MB }}MB</p>
      </a-upload-dragger>
      <a-alert
        class="upload-tip"
        type="info"
        show-icon
        message="切片策略：按空行分段聚合，约 900 字符一块、相邻块保留 120 字符重叠；上传完成后请到「知识片段」逐条审核标题与标签。"
      />
    </a-drawer>

    <!-- 文档详情：解析结果与片段标注 -->
    <a-drawer v-model:open="documentOpen" :width="980" :title="documentTitle" destroy-on-close>
      <div class="doc-detail">
        <aside class="doc-detail__aside">
          <div class="doc-detail__stat">
            <div><b>{{ formatChars(currentDocument?.char_count) }}</b><small>字符</small></div>
            <div><b>{{ documentSegments.length }}</b><small>片段</small></div>
            <div><b>{{ enabledDocSegmentCount }}</b><small>参与检索</small></div>
          </div>
          <a-alert type="info" show-icon message="自动切片是候选结果，建议逐条核对标题、内容与标签后再加入知识集。" />
          <a-button block type="dashed" @click="openNewSegment()">
            <template #icon><PlusOutlined /></template>
            人工标注新片段
          </a-button>
        </aside>
        <main class="doc-detail__main">
          <a-empty v-if="!documentSegments.length" description="该文档还没有片段" />
          <article v-for="item in documentSegments" :key="item.id" class="doc-seg-row" :class="{ off: !item.is_enabled }">
            <div class="doc-seg-row__main">
              <div class="doc-seg-row__tags">
                <a-tag>片段 {{ item.index + 1 }}</a-tag>
                <a-tag :color="item.is_enabled ? 'green' : 'default'">{{ item.is_enabled ? '参与检索' : '不参与检索' }}</a-tag>
                <a-tag v-for="tag in item.tags" :key="tag">{{ tag }}</a-tag>
              </div>
              <h4>{{ item.title }}</h4>
              <p>{{ item.content }}</p>
            </div>
            <a-button type="link" size="small" @click="openEditSegment(item)">编辑</a-button>
          </article>
        </main>
      </div>
    </a-drawer>

    <SegmentEditorDrawer
      v-model:open="segmentEditorOpen"
      :documents="documents"
      :segment="editingSegment"
      :default-document-id="currentDocument?.id"
      :known-tags="knownTags"
      @saved="onSegmentSaved"
    />
  </div>
</template>

<script lang="ts" setup>
import { computed, nextTick, onMounted, ref } from 'vue';
import {
  Tabs as ATabs,
  TabPane as ATabPane,
  Drawer as ADrawer,
  Input as AInput,
  Button as AButton,
  Tag as ATag,
  Alert as AAlert,
  Popconfirm as APopconfirm,
  Empty as AEmpty,
  Tooltip as ATooltip,
  UploadDragger as AUploadDragger,
} from 'ant-design-vue';
import {
  DeleteOutlined,
  EyeOutlined,
  FileTextOutlined,
  InboxOutlined,
  PlusOutlined,
  UploadOutlined,
} from '@ant-design/icons-vue';
import { useMessage } from '@/hooks/web/useMessage';
import {
  deleteKnowledgeDocument,
  getRagHealth,
  listKnowledgeDocuments,
  listKnowledgeSegments,
  listKnowledgeSets,
  listRagExperts,
  uploadKnowledgeDocument,
  type KnowledgeDocument,
  type KnowledgeSegment,
  type KnowledgeSet,
  type RagExpert,
  type RagHealth,
} from '@/api/device/rag';
import { formatApiErrorMessage } from '@/views/camera/utils/apiErrorMessage';
import { RAG_UPLOAD_ACCEPT, RAG_UPLOAD_MAX_MB } from './ragPresets';
import SegmentEditorDrawer from './SegmentEditorDrawer.vue';
import SegmentWorkbench from './SegmentWorkbench.vue';
import KnowledgeSetPanel from './KnowledgeSetPanel.vue';
import ExpertPanel from './ExpertPanel.vue';

defineOptions({ name: 'LLMTraining' });

const { createMessage } = useMessage();

const view = ref('documents');
const keyword = ref('');
const documents = ref<KnowledgeDocument[]>([]);
const segments = ref<KnowledgeSegment[]>([]);
const sets = ref<KnowledgeSet[]>([]);
const experts = ref<RagExpert[]>([]);
const health = ref<RagHealth>();

const uploadOpen = ref(false);
const documentOpen = ref(false);
const segmentEditorOpen = ref(false);
const currentDocument = ref<KnowledgeDocument>();
const documentSegments = ref<KnowledgeSegment[]>([]);
const editingSegment = ref<KnowledgeSegment | null>(null);
const setPanelRef = ref<InstanceType<typeof KnowledgeSetPanel>>();

/** 片段工作台「创建为知识集」：切到知识集页签并预选片段 */
async function handleCreateSet(segmentIds: number[]) {
  view.value = 'sets';
  await nextTick();
  setPanelRef.value?.openCreate(segmentIds);
}

const filteredDocuments = computed(() => {
  const key = keyword.value.trim().toLowerCase();
  return documents.value.filter((d) => !key || d.name.toLowerCase().includes(key));
});

const stats = computed(() => [
  { key: 'documents', label: '知识文档', count: documents.value.length, sub: '' },
  {
    key: 'segments',
    label: '知识片段',
    count: segments.value.length,
    sub: `启用 ${segments.value.filter((s) => s.is_enabled).length}`,
  },
  { key: 'sets', label: '知识集', count: sets.value.length, sub: '' },
  {
    key: 'experts',
    label: 'RAG 专家',
    count: experts.value.length,
    sub: `启用 ${experts.value.filter((e) => e.is_enabled).length}`,
  },
]);

const documentTitle = computed(() => `${currentDocument.value?.name || ''} · 文档解析与片段标注`);
const enabledDocSegmentCount = computed(() => documentSegments.value.filter((s) => s.is_enabled).length);
const knownTags = computed(() => {
  const counter = new Map<string, number>();
  segments.value.forEach((s) => (s.tags || []).forEach((t) => counter.set(t, (counter.get(t) || 0) + 1)));
  return [...counter.entries()].sort((a, b) => b[1] - a[1]).map(([tag]) => tag);
});
const healthTooltip = computed(() => {
  if (!health.value) return '正在检测向量库状态';
  return health.value.ok
    ? `Milvus ${health.value.uri} · 集合 ${health.value.collection} · ${health.value.dimensions} 维`
    : `连接失败：${health.value.error || '未知错误'}`;
});

async function refresh() {
  try {
    const [d, s, k, e]: any[] = await Promise.all([
      listKnowledgeDocuments(),
      listKnowledgeSegments(),
      listKnowledgeSets(),
      listRagExperts(),
    ]);
    documents.value = d?.data || d || [];
    segments.value = s?.data || s || [];
    sets.value = k?.data || k || [];
    experts.value = e?.data || e || [];
  } catch (error: any) {
    createMessage.error(formatApiErrorMessage(error, '加载 RAG 知识数据失败'));
  }
}

async function refreshHealth() {
  try {
    const res: any = await getRagHealth();
    health.value = res?.data || res;
  } catch {
    health.value = { ok: false, uri: '-', collection: '-', error: '无法连接 AI 服务' };
  }
}

async function handleUpload(file: File) {
  const maxSize = RAG_UPLOAD_MAX_MB * 1024 * 1024;
  if (file.size > maxSize) {
    createMessage.warning(`文件超过 ${RAG_UPLOAD_MAX_MB}MB 限制`);
    return false;
  }
  try {
    const res: any = await uploadKnowledgeDocument(file);
    const count = res?.data?.segment_count ?? res?.segment_count;
    createMessage.success(count ? `文档已解析，生成 ${count} 个候选片段，请到「知识片段」审核` : '文档解析完成');
    uploadOpen.value = false;
    await refresh();
    view.value = 'segments';
  } catch (error: any) {
    createMessage.error(formatApiErrorMessage(error, '文档解析失败'));
  }
  return false;
}

async function openDocument(item: KnowledgeDocument) {
  currentDocument.value = item;
  documentOpen.value = true;
  try {
    const res: any = await listKnowledgeSegments(item.id);
    documentSegments.value = res?.data || res || [];
  } catch (error: any) {
    createMessage.error(formatApiErrorMessage(error, '加载文档片段失败'));
    documentSegments.value = [];
  }
}

function openNewSegment() {
  editingSegment.value = null;
  segmentEditorOpen.value = true;
}

function openEditSegment(item: KnowledgeSegment) {
  editingSegment.value = item;
  segmentEditorOpen.value = true;
}

async function onSegmentSaved() {
  await refresh();
  if (currentDocument.value && documentOpen.value) {
    await openDocument(currentDocument.value);
  }
}

async function removeDocument(item: KnowledgeDocument) {
  try {
    await deleteKnowledgeDocument(item.id);
    createMessage.success('文档及其片段已删除');
    if (currentDocument.value?.id === item.id) {
      documentOpen.value = false;
      currentDocument.value = undefined;
    }
    await refresh();
  } catch (error: any) {
    createMessage.error(formatApiErrorMessage(error, '删除文档失败'));
  }
}

function formatTime(value?: string) {
  if (!value) return '-';
  return String(value).replace('T', ' ').slice(0, 16);
}

function formatChars(count?: number) {
  if (!count) return '0';
  if (count >= 10000) return `${(count / 10000).toFixed(1)} 万`;
  return String(count);
}

onMounted(() => {
  refresh();
  refreshHealth();
});
</script>

<style lang="less" scoped>
@rag-primary: #1677ff;

.rag-page {
  min-height: 100%;
  padding: 20px 24px 32px;
  background: #fff;
}

/* ===== 页头 ===== */
.page-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;

  h2 {
    margin: 0 0 6px;
    font-size: 20px;
    font-weight: 600;
    color: rgba(0, 0, 0, 0.88);
  }

  p {
    margin: 0;
    color: rgba(0, 0, 0, 0.45);
    font-size: 13px;
    max-width: 720px;
  }
}

.health-pill {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 5px 12px;
  border-radius: 20px;
  font-size: 12.5px;
  font-weight: 500;
  white-space: nowrap;
  cursor: default;

  &__dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
  }

  &.is-ok {
    color: #389e0d;
    background: #f6ffed;
    border: 1px solid #b7eb8f;

    .health-pill__dot {
      background: #52c41a;
    }
  }

  &.is-bad {
    color: #d4380d;
    background: #fff2e8;
    border: 1px solid #ffbb96;

    .health-pill__dot {
      background: #ff4d4f;
    }
  }
}

/* ===== 检索底座降级提示 ===== */
.emb-alert {
  margin-bottom: 14px;

  b {
    color: #d46b08;
  }
}

/* ===== 统计条 ===== */
.stat-strip {
  display: flex;
  gap: 12px;
  margin-bottom: 4px;
}

.stat-strip__item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  border: 1px solid #e8e8ec;
  border-radius: 10px;
  background: #fff;
  cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s;

  &:hover {
    border-color: fade(@rag-primary, 45%);
  }

  &.active {
    border-color: @rag-primary;
    box-shadow: 0 0 0 2px fade(@rag-primary, 10%);
  }

  &__num {
    font-size: 22px;
    font-weight: 700;
    color: rgba(0, 0, 0, 0.85);
    font-variant-numeric: tabular-nums;
  }

  &__label {
    display: flex;
    flex-direction: column;
    font-size: 12.5px;
    color: rgba(0, 0, 0, 0.55);
    text-align: left;

    em {
      font-style: normal;
      font-size: 11.5px;
      color: @rag-primary;
    }
  }
}

.w-240 {
  width: 240px;
}

/* ===== 页签容器 ===== */
.pane {
  min-height: 420px;
}

.pane__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;

  h3 {
    margin: 0 0 4px;
    font-size: 16px;
    font-weight: 600;
    color: rgba(0, 0, 0, 0.85);
  }

  p {
    margin: 0;
    font-size: 12.5px;
    color: rgba(0, 0, 0, 0.45);
  }
}

.pane__head-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.pane__empty {
  padding: 70px 0;
}

/* ===== 文档卡片 ===== */
.doc-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 14px;
}

.doc-card {
  padding: 16px 18px;
  border: 1px solid #e8e8ec;
  border-radius: 10px;
  background: #fff;
  transition: border-color 0.2s, box-shadow 0.2s;

  &:hover {
    border-color: fade(@rag-primary, 45%);
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  }

  &__head {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  &__icon {
    display: grid;
    place-items: center;
    width: 38px;
    height: 38px;
    border-radius: 9px;
    background: #e6f4ff;
    color: @rag-primary;
    font-size: 18px;
    flex-shrink: 0;
  }

  &__title-box {
    min-width: 0;

    h3 {
      margin: 0 0 3px;
      font-size: 14.5px;
      font-weight: 600;
      color: rgba(0, 0, 0, 0.88);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }

  &__time {
    font-size: 12px;
    color: rgba(0, 0, 0, 0.4);
  }

  &__metrics {
    display: flex;
    margin-top: 12px;
    padding: 10px 12px;
    border-radius: 8px;
    background: #fafbfc;

    > div {
      flex: 1;
      text-align: center;

      b {
        font-size: 16px;
        color: rgba(0, 0, 0, 0.85);
      }

      small {
        display: block;
        margin-top: 2px;
        font-size: 11px;
        color: rgba(0, 0, 0, 0.4);
      }
    }
  }

  &__foot {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 8px;
    padding-top: 4px;
    border-top: 1px solid #f2f2f5;
  }
}

/* ===== 上传抽屉 ===== */
.upload-intro {
  display: flex;
  gap: 14px;
  align-items: center;
  padding: 14px 16px;
  margin-bottom: 18px;
  border: 1px solid #bae0ff;
  border-radius: 10px;
  background: #f0f8ff;

  &__icon {
    font-size: 26px;
    color: @rag-primary;
  }

  b {
    font-size: 15px;
    color: rgba(0, 0, 0, 0.85);
  }

  p {
    margin: 4px 0 0;
    font-size: 12.5px;
    color: rgba(0, 0, 0, 0.5);
    line-height: 1.7;
  }
}

.large-upload {
  margin-bottom: 14px;
}

.upload-tip {
  margin-top: 14px;
}

/* ===== 文档详情 ===== */
.doc-detail {
  display: grid;
  grid-template-columns: 250px minmax(0, 1fr);
  gap: 18px;
  align-items: start;

  &__aside {
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 14px;
    border: 1px solid #e8e8ec;
    border-radius: 10px;
    position: sticky;
    top: 0;
  }

  &__stat {
    display: flex;

    > div {
      flex: 1;
      text-align: center;

      b {
        font-size: 17px;
        color: rgba(0, 0, 0, 0.85);
      }

      small {
        display: block;
        font-size: 11px;
        color: rgba(0, 0, 0, 0.4);
      }
    }
  }
}

.doc-seg-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 16px;
  margin-bottom: 10px;
  border: 1px solid #e8e8ec;
  border-radius: 10px;
  transition: border-color 0.2s;

  &:hover {
    border-color: fade(@rag-primary, 45%);
  }

  &.off .doc-seg-row__main {
    opacity: 0.55;
  }

  &__main {
    flex: 1;
    min-width: 0;
  }

  &__tags {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;

    :deep(.ant-tag) {
      margin: 0;
      font-size: 11px;
      line-height: 18px;
      padding: 0 6px;
    }
  }

  h4 {
    margin: 8px 0 4px;
    font-size: 13.5px;
    font-weight: 600;
    color: rgba(0, 0, 0, 0.85);
  }

  p {
    margin: 0;
    font-size: 12.5px;
    line-height: 1.75;
    color: rgba(0, 0, 0, 0.6);
    white-space: pre-wrap;
    word-break: break-word;
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 4;
    overflow: hidden;
  }
}

@media (max-width: 1100px) {
  .doc-detail {
    grid-template-columns: 1fr;
  }

  .stat-strip {
    flex-wrap: wrap;
  }
}
</style>
