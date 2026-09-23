<template>
  <div class="seg-work">
    <div class="seg-work__toolbar">
      <a-select
        v-model:value="filters.documentId"
        allow-clear
        placeholder="全部来源文档"
        class="w-200"
        :options="documentOptions"
      />
      <a-select
        v-model:value="filters.tag"
        allow-clear
        placeholder="全部标签"
        class="w-160"
        :options="tagOptions"
      />
      <a-select v-model:value="filters.status" class="w-140" :options="statusOptions" />
      <a-input v-model:value="filters.keyword" allow-clear placeholder="搜索标题或内容" class="w-240" />
      <div class="seg-work__toolbar-right">
        <template v-if="selectedIds.size">
          <span class="seg-work__selected">已选 {{ selectedIds.size }} 项</span>
          <a-tooltip title="用已启用的大模型为所选片段自动生成标题与业务标签">
            <a-button size="small" :loading="aiLoading" @click="aiCompleteMeta">
              <template #icon><RobotOutlined /></template>
              AI 补全
            </a-button>
          </a-tooltip>
          <a-popconfirm
            title="合并会删除所选片段并生成一个拼接后的新片段，知识集引用自动改挂到新片段，确定合并？"
            ok-text="合并"
            cancel-text="取消"
            @confirm="mergeSelected"
          >
            <a-button size="small" :loading="merging">合并所选</a-button>
          </a-popconfirm>
          <a-tooltip title="把所选片段直接组成一个新的知识集">
            <a-button size="small" type="primary" ghost @click="createSetFromSelection">
              <template #icon><FolderAddOutlined /></template>
              创建为知识集
            </a-button>
          </a-tooltip>
          <a-button size="small" :loading="batching" @click="batchSetEnabled(true)">批量启用</a-button>
          <a-button size="small" :loading="batching" @click="batchSetEnabled(false)">批量停用</a-button>
          <a-button size="small" type="text" @click="clearSelection">取消</a-button>
        </template>
        <a-button v-else type="primary" @click="openCreate()">
          <template #icon><PlusOutlined /></template>
          人工标注片段
        </a-button>
      </div>
    </div>

    <a-empty v-if="!filtered.length" class="seg-work__empty" description="没有匹配的知识片段" />

    <template v-else>
      <div class="seg-work__grid">
        <article
          v-for="item in visibleSegments"
          :key="item.id"
          class="seg-card"
          :class="{ off: !item.is_enabled }"
        >
          <header class="seg-card__head">
            <a-checkbox
              :checked="selectedIds.has(item.id)"
              @change="(e: any) => toggleSelected(item.id, e.target.checked)"
            />
            <a-tag class="seg-card__doc" color="blue" :title="item.document_name">{{ item.document_name }}</a-tag>
            <span class="seg-card__spacer" />
            <a-switch
              size="small"
              :checked="item.is_enabled"
              @change="(checked: any) => toggleEnabled(item, checked)"
            />
          </header>
          <h3 class="seg-card__title" :title="item.title">{{ item.title }}</h3>
          <p class="seg-card__content">{{ previewContent(item.content) }}</p>
          <footer class="seg-card__foot">
            <div class="seg-card__tags">
              <a-tag v-for="tag in item.tags.slice(0, 3)" :key="tag">{{ tag }}</a-tag>
              <a-tag v-if="item.tags.length > 3">+{{ item.tags.length - 3 }}</a-tag>
            </div>
            <span class="seg-card__meta">
              {{ item.knowledge_set_count ? `引用 ${item.knowledge_set_count}` : '未被引用' }}
            </span>
            <a-button type="link" size="small" @click="openEdit(item)">编辑</a-button>
          </footer>
        </article>
      </div>
      <div v-if="filtered.length > RENDER_LIMIT" class="seg-work__more">
        已显示前 {{ RENDER_LIMIT }} 条（共 {{ filtered.length }} 条），请使用筛选缩小范围后再操作
      </div>
    </template>

    <SegmentEditorDrawer
      v-model:open="editorOpen"
      :documents="documents"
      :segment="editingSegment"
      :known-tags="tagOptions.map((t) => t.value)"
      @saved="emit('changed')"
    />
  </div>
</template>

<script lang="ts" setup>
import { computed, reactive, ref, watch } from 'vue';
import {
  Select as ASelect,
  Input as AInput,
  Button as AButton,
  Tag as ATag,
  Switch as ASwitch,
  Checkbox as ACheckbox,
  Empty as AEmpty,
  Tooltip as ATooltip,
  Popconfirm as APopconfirm,
} from 'ant-design-vue';
import { FolderAddOutlined, PlusOutlined, RobotOutlined } from '@ant-design/icons-vue';
import { useMessage } from '@/hooks/web/useMessage';
import {
  autoMetaSegments,
  mergeSegments,
  updateKnowledgeSegment,
  type KnowledgeDocument,
  type KnowledgeSegment,
} from '@/api/device/rag';
import { formatApiErrorMessage } from '@/views/camera/utils/apiErrorMessage';
import { previewContent } from './ragPresets';
import SegmentEditorDrawer from './SegmentEditorDrawer.vue';

defineOptions({ name: 'RagSegmentWorkbench' });

const props = defineProps<{
  segments: KnowledgeSegment[];
  documents: KnowledgeDocument[];
}>();

const emit = defineEmits(['changed', 'createSet']);

const { createMessage } = useMessage();
const RENDER_LIMIT = 200;

const filters = reactive({ documentId: undefined as number | undefined, tag: undefined as string | undefined, status: 'all', keyword: '' });
const selectedIds = ref(new Set<number>());
const batching = ref(false);
const aiLoading = ref(false);
const merging = ref(false);
const editorOpen = ref(false);
const editingSegment = ref<KnowledgeSegment | null>(null);

const statusOptions = [
  { label: '全部状态', value: 'all' },
  { label: '已启用', value: 'enabled' },
  { label: '已停用', value: 'disabled' },
  { label: '未被知识集引用', value: 'unreferenced' },
];
const documentOptions = computed(() => props.documents.map((d) => ({ label: d.name, value: d.id })));
const tagOptions = computed(() => {
  const counter = new Map<string, number>();
  props.segments.forEach((s) => (s.tags || []).forEach((t) => counter.set(t, (counter.get(t) || 0) + 1)));
  return [...counter.entries()]
    .sort((a, b) => b[1] - a[1])
    .map(([tag]) => ({ label: tag, value: tag }));
});

const filtered = computed(() => {
  const keyword = filters.keyword.trim().toLowerCase();
  return props.segments.filter((s) => {
    if (filters.documentId && s.document_id !== filters.documentId) return false;
    if (filters.tag && !(s.tags || []).includes(filters.tag)) return false;
    if (filters.status === 'enabled' && !s.is_enabled) return false;
    if (filters.status === 'disabled' && s.is_enabled) return false;
    if (filters.status === 'unreferenced' && s.knowledge_set_count > 0) return false;
    if (keyword && !`${s.title}${s.content}`.toLowerCase().includes(keyword)) return false;
    return true;
  });
});
const visibleSegments = computed(() => filtered.value.slice(0, RENDER_LIMIT));

watch(
  () => props.segments,
  () => {
    // 列表刷新后清掉已不存在的选择，避免批量操作落空
    const alive = new Set(props.segments.map((s) => s.id));
    [...selectedIds.value].filter((id) => !alive.has(id)).forEach((id) => selectedIds.value.delete(id));
  },
);

function toggleSelected(id: number, checked: boolean) {
  const next = new Set(selectedIds.value);
  if (checked) next.add(id);
  else next.delete(id);
  selectedIds.value = next;
}

function clearSelection() {
  selectedIds.value = new Set();
}

function selectedSegments() {
  return props.segments.filter((s) => selectedIds.value.has(s.id));
}

/** AI 批量补全标题与标签（每次最多 20 条，超出时提示先缩小范围） */
async function aiCompleteMeta() {
  const ids = [...selectedIds.value];
  if (!ids.length) return;
  if (ids.length > 20) {
    createMessage.warning('单次最多补全 20 条，请先缩小选择范围');
    return;
  }
  aiLoading.value = true;
  try {
    const res: any = await autoMetaSegments(ids);
    const result = res?.data || res || {};
    const updated = result.updated ?? 0;
    const failed: string[] = result.failed || [];
    if (updated) createMessage.success(`已为 ${updated} 个片段补全标题与标签`);
    if (failed.length) createMessage.warning(`${failed.length} 个片段补全失败：${failed.slice(0, 3).join('、')}`);
    clearSelection();
    emit('changed');
  } catch (error: any) {
    createMessage.error(formatApiErrorMessage(error, 'AI 补全失败'));
  } finally {
    aiLoading.value = false;
  }
}

async function mergeSelected() {
  const items = selectedSegments();
  if (items.length < 2) {
    createMessage.warning('至少选择 2 个片段才能合并');
    return;
  }
  const documentIds = new Set(items.map((s) => s.document_id));
  if (documentIds.size > 1) {
    createMessage.warning('只能合并同一来源文档的片段，请先按文档筛选后再选择');
    return;
  }
  merging.value = true;
  try {
    // 按片段序号拼接，保证合并后内容顺序与文档一致
    await mergeSegments([...items].sort((a, b) => a.index - b.index).map((s) => s.id));
    createMessage.success(`已合并为 1 个片段，原 ${items.length} 个片段已删除`);
    clearSelection();
    emit('changed');
  } catch (error: any) {
    createMessage.error(formatApiErrorMessage(error, '合并片段失败'));
  } finally {
    merging.value = false;
  }
}

function createSetFromSelection() {
  const ids = [...selectedIds.value];
  if (!ids.length) return;
  emit('createSet', ids);
}

function openCreate() {
  editingSegment.value = null;
  editorOpen.value = true;
}

function openEdit(item: KnowledgeSegment) {
  editingSegment.value = item;
  editorOpen.value = true;
}

async function toggleEnabled(item: KnowledgeSegment, checked: boolean) {
  try {
    await updateKnowledgeSegment(item.id, { ...item, is_enabled: checked === true });
    item.is_enabled = checked === true;
  } catch (error: any) {
    createMessage.error(formatApiErrorMessage(error, '更新片段状态失败'));
    emit('changed');
  }
}

async function batchSetEnabled(enabled: boolean) {
  const ids = [...selectedIds.value];
  if (!ids.length) return;
  batching.value = true;
  let okCount = 0;
  try {
    // 内容未变化时后端不会重新向量化，逐条更新开销可接受
    await Promise.all(
      ids.map(async (id) => {
        const segment = props.segments.find((s) => s.id === id);
        if (!segment || segment.is_enabled === enabled) return;
        await updateKnowledgeSegment(id, { ...segment, is_enabled: enabled });
        okCount += 1;
      }),
    );
    createMessage.success(`已${enabled ? '启用' : '停用'} ${okCount} 个片段`);
    selectedIds.value = new Set();
    emit('changed');
  } catch (error: any) {
    createMessage.error(formatApiErrorMessage(error, '批量更新片段失败'));
    emit('changed');
  } finally {
    batching.value = false;
  }
}
</script>

<style lang="less" scoped>
.seg-work {
  width: 100%;
}

.seg-work__toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.seg-work__toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}

.seg-work__selected {
  font-size: 12.5px;
  color: rgba(0, 0, 0, 0.55);
}

.w-140 { width: 140px; }
.w-160 { width: 160px; }
.w-200 { width: 200px; }
.w-240 { width: 240px; }

.seg-work__empty {
  padding: 60px 0;
}

.seg-work__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 14px;
}

.seg-card {
  display: flex;
  flex-direction: column;
  min-width: 0;
  padding: 14px 16px;
  border: 1px solid #e8e8ec;
  border-radius: 10px;
  background: #fff;
  transition: border-color 0.2s, box-shadow 0.2s;

  &:hover {
    border-color: rgba(22, 119, 255, 0.45);
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  }

  &.off {
    background: #fafafa;

    .seg-card__title,
    .seg-card__content {
      opacity: 0.55;
    }
  }

  &__head {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  &__doc {
    max-width: 180px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    margin: 0;
  }

  &__spacer {
    flex: 1;
  }

  &__title {
    margin: 10px 0 6px;
    font-size: 14px;
    font-weight: 600;
    color: rgba(0, 0, 0, 0.88);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__content {
    display: -webkit-box;
    overflow: hidden;
    margin: 0;
    color: rgba(0, 0, 0, 0.6);
    font-size: 12.5px;
    line-height: 1.7;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 3;
    min-height: 64px;
  }

  &__foot {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-top: 10px;
    padding-top: 8px;
    border-top: 1px solid #f2f2f5;
  }

  &__tags {
    display: flex;
    gap: 4px;
    min-width: 0;
    overflow: hidden;

    :deep(.ant-tag) {
      margin: 0;
      font-size: 11px;
      line-height: 18px;
      padding: 0 6px;
    }
  }

  &__meta {
    margin-left: auto;
    flex-shrink: 0;
    font-size: 12px;
    color: rgba(0, 0, 0, 0.4);
  }
}

.seg-work__more {
  margin-top: 14px;
  padding: 10px;
  text-align: center;
  font-size: 12.5px;
  color: rgba(0, 0, 0, 0.45);
  background: #fafbfc;
  border-radius: 8px;
}
</style>
