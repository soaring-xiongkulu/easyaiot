<template>
  <div class="kset">
    <div class="kset__toolbar">
      <a-input v-model:value="keyword" allow-clear placeholder="搜索知识集名称" class="w-240" />
      <a-button type="primary" @click="openEditor()">
        <template #icon><PlusOutlined /></template>
        新建知识集
      </a-button>
    </div>

    <a-empty v-if="!filteredSets.length" class="kset__empty" description="暂无知识集，点击右上角新建，或到「知识片段」勾选后一键创建" />

    <div v-else class="kset__grid">
      <article v-for="item in filteredSets" :key="item.id" class="kset-card">
        <header class="kset-card__head">
          <div class="kset-card__icon"><FolderOutlined /></div>
          <div class="kset-card__title-box">
            <h3 :title="item.name">{{ item.name }}</h3>
            <a-tag color="cyan">{{ item.category }}</a-tag>
          </div>
        </header>
        <p class="kset-card__desc">{{ item.description || '暂无说明' }}</p>
        <div class="kset-card__metrics">
          <div><b>{{ item.document_count }}</b><small>来源文档</small></div>
          <div><b>{{ item.segment_count }}</b><small>知识片段</small></div>
          <div><b>{{ item.expert_count }}</b><small>专家引用</small></div>
        </div>
        <footer class="kset-card__foot">
          <a-button type="link" size="small" @click="openTest(item)">
            <template #icon><SearchOutlined /></template>
            检索验证
          </a-button>
          <div class="kset-card__actions">
            <a-button type="text" size="small" @click="openEditor(item)">
              <template #icon><EditOutlined /></template>
              编辑
            </a-button>
            <a-popconfirm
              title="确认删除知识集？原文档和片段将保留，引用它的专家将解除关联。"
              ok-text="删除"
              cancel-text="取消"
              @confirm="removeSet(item)"
            >
              <a-button danger type="text" size="small">
                <template #icon><DeleteOutlined /></template>
              </a-button>
            </a-popconfirm>
          </div>
        </footer>
      </article>
    </div>

    <!-- 新建 / 编辑：双栏选段器 -->
    <a-drawer
      v-model:open="editorOpen"
      :width="1060"
      :title="editingId ? '编辑知识集' : '新建知识集'"
      destroy-on-close
    >
      <div class="kset-editor">
        <a-form layout="vertical" class="kset-editor__meta">
          <div class="kset-editor__row">
            <a-form-item label="知识集名称" required class="kset-editor__name">
              <a-input v-model:value="form.name" placeholder="如：皮带机故障处置手册" :maxlength="60" />
            </a-form-item>
            <a-form-item label="业务分类" required class="kset-editor__cat">
              <a-auto-complete
                v-model:value="form.category"
                :options="categoryOptions"
                placeholder="选择或输入分类"
                :filter-option="filterCategory"
              />
            </a-form-item>
          </div>
          <a-form-item label="说明">
            <a-textarea v-model:value="form.description" :rows="2" placeholder="描述该知识集的适用场景，方便专家编排时选择" />
          </a-form-item>
        </a-form>

        <div class="kset-editor__pick">
          <div class="kset-pane">
            <div class="kset-pane__head">
              <span class="kset-pane__title">候选知识片段</span>
              <span class="kset-pane__count">{{ candidates.length }} 项</span>
            </div>
            <div class="kset-pane__filters">
              <a-select
                v-model:value="pickFilter.documentId"
                allow-clear
                size="small"
                placeholder="全部文档"
                class="filter-doc"
                :options="documentOptions"
              />
              <a-select
                v-model:value="pickFilter.tag"
                allow-clear
                size="small"
                placeholder="全部标签"
                class="filter-tag"
                :options="tagOptions"
              />
              <a-input v-model:value="pickFilter.keyword" size="small" allow-clear placeholder="搜索标题/内容" class="filter-search" />
            </div>
            <div class="kset-pane__list">
              <div
                v-for="item in candidates"
                :key="item.id"
                class="kset-pick-row"
                :class="{ off: !item.is_enabled, 'is-added': form.segment_ids.includes(item.id) }"
                @click="addSegment(item.id)"
              >
                <div class="kset-pick-row__main">
                  <div class="kset-pick-row__title">
                    <span class="kset-pick-row__name" :title="item.title">{{ item.title }}</span>
                    <span v-if="!item.is_enabled" class="kset-pick-row__off">已停用</span>
                  </div>
                  <div class="kset-pick-row__desc">
                    <a-tag color="blue">{{ item.document_name }}</a-tag>
                    <span>{{ previewContent(item.content) }}</span>
                  </div>
                </div>
                <a-button size="small" type="link" :disabled="form.segment_ids.includes(item.id)">
                  {{ form.segment_ids.includes(item.id) ? '已加入' : '加入' }}
                </a-button>
              </div>
              <div v-if="!candidates.length" class="kset-pane__empty">没有匹配的片段</div>
            </div>
          </div>

          <div class="kset-pane kset-pane--target">
            <div class="kset-pane__head">
              <span class="kset-pane__title">已加入知识集</span>
              <span class="kset-pane__count">{{ form.segment_ids.length }} 项</span>
            </div>
            <div class="kset-pane__list">
              <div v-for="(id, index) in form.segment_ids" :key="id" class="kset-pick-row kset-pick-row--picked">
                <span class="kset-pick-row__order">{{ index + 1 }}</span>
                <div class="kset-pick-row__main">
                  <div class="kset-pick-row__title">
                    <span class="kset-pick-row__name" :title="segmentById(id)?.title">{{ segmentById(id)?.title || `片段 #${id}` }}</span>
                  </div>
                  <div class="kset-pick-row__desc">
                    <a-tag color="blue">{{ segmentById(id)?.document_name || '-' }}</a-tag>
                    <span>{{ previewContent(segmentById(id)?.content, 48) }}</span>
                  </div>
                </div>
                <a-button danger type="text" size="small" @click="removeSegment(id)">移除</a-button>
              </div>
              <div v-if="!form.segment_ids.length" class="kset-pane__empty">从左侧选择知识片段<br />同一片段可被多个知识集复用</div>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="kset-editor__footer">
          <a-button @click="editorOpen = false">取消</a-button>
          <a-button type="primary" :loading="saving" @click="handleSave">保存知识集</a-button>
        </div>
      </template>
    </a-drawer>

    <!-- 检索验证 -->
    <a-drawer v-model:open="testOpen" :width="860" :title="testTitle" destroy-on-close>
      <div class="kset-test">
        <div class="kset-test__ask">
          <a-input
            v-model:value="testQuery"
            size="large"
            placeholder="输入真实业务问题，验证该知识集能召回哪些片段"
            @press-enter="runTest"
          />
          <a-input-number v-model:value="testTopK" :min="1" :max="10" addon-before="Top" style="width: 110px" />
          <a-button type="primary" size="large" :loading="testing" @click="runTest">检索</a-button>
        </div>
        <a-empty v-if="!testSources.length && !testing" description="输入问题后查看命中片段与相关度" />
        <div v-for="(item, index) in testSources" :key="item.segment_id" class="kset-hit">
          <div class="kset-hit__head">
            <span class="kset-hit__rank">No.{{ index + 1 }}</span>
            <a-tag color="blue">{{ item.document_name }}</a-tag>
            <div class="kset-hit__score">
              <div class="kset-hit__score-bar"><div class="kset-hit__score-fill" :style="{ width: scorePercent(item) + '%' }" /></div>
              <span class="kset-hit__score-num">{{ scorePercent(item) }}%</span>
            </div>
          </div>
          <p class="kset-hit__content">{{ item.content }}</p>
        </div>
      </div>
    </a-drawer>
  </div>
</template>

<script lang="ts" setup>
import { computed, reactive, ref } from 'vue';
import {
  Drawer as ADrawer,
  Form as AForm,
  FormItem as AFormItem,
  Input as AInput,
  Textarea as ATextarea,
  Select as ASelect,
  AutoComplete as AAutoComplete,
  InputNumber as AInputNumber,
  Button as AButton,
  Tag as ATag,
  Popconfirm as APopconfirm,
  Empty as AEmpty,
} from 'ant-design-vue';
import { DeleteOutlined, EditOutlined, FolderOutlined, PlusOutlined, SearchOutlined } from '@ant-design/icons-vue';
import { useMessage } from '@/hooks/web/useMessage';
import {
  createKnowledgeSet,
  deleteKnowledgeSet,
  searchKnowledgeSet,
  updateKnowledgeSet,
  type KnowledgeDocument,
  type KnowledgeSegment,
  type KnowledgeSet,
  type RagSource,
} from '@/api/device/rag';
import { formatApiErrorMessage } from '@/views/camera/utils/apiErrorMessage';
import { RAG_CATEGORIES, previewContent } from './ragPresets';

defineOptions({ name: 'RagKnowledgeSetPanel' });

const props = defineProps<{
  sets: KnowledgeSet[];
  segments: KnowledgeSegment[];
  documents: KnowledgeDocument[];
}>();

const emit = defineEmits(['changed']);

const { createMessage } = useMessage();
const RENDER_LIMIT = 60;

const keyword = ref('');
const editorOpen = ref(false);
const saving = ref(false);
const editingId = ref<number>();
const form = reactive({ name: '', category: '', description: '', segment_ids: [] as number[] });
const pickFilter = reactive({ documentId: undefined as number | undefined, tag: undefined as string | undefined, keyword: '' });

const testOpen = ref(false);
const testing = ref(false);
const testingSet = ref<KnowledgeSet>();
const testQuery = ref('');
const testTopK = ref(8);
const testSources = ref<RagSource[]>([]);

const filteredSets = computed(() => {
  const key = keyword.value.trim().toLowerCase();
  return props.sets.filter((s) => !key || s.name.toLowerCase().includes(key)).slice(0, RENDER_LIMIT);
});
const categoryOptions = computed(() => {
  const known = new Set(props.sets.map((s) => s.category));
  return [...new Set([...RAG_CATEGORIES, ...known])].map((c) => ({ label: c, value: c }));
});
const documentOptions = computed(() => props.documents.map((d) => ({ label: d.name, value: d.id })));
const tagOptions = computed(() => {
  const counter = new Map<string, number>();
  props.segments.forEach((s) => (s.tags || []).forEach((t) => counter.set(t, (counter.get(t) || 0) + 1)));
  return [...counter.entries()].map(([tag]) => ({ label: tag, value: tag }));
});

const candidates = computed(() => {
  const key = pickFilter.keyword.trim().toLowerCase();
  const list = props.segments.filter((s) => {
    if (pickFilter.documentId && s.document_id !== pickFilter.documentId) return false;
    if (pickFilter.tag && !(s.tags || []).includes(pickFilter.tag)) return false;
    if (key && !`${s.title}${s.content}`.toLowerCase().includes(key)) return false;
    return true;
  });
  // 已加入的沉底避免干扰挑选，其余按文档分组、按原文切片顺序排列，方便连续勾选
  const added = (s: KnowledgeSegment) => (form.segment_ids.includes(s.id) ? 1 : 0);
  return list.sort(
    (a, b) =>
      added(a) - added(b) ||
      a.document_name.localeCompare(b.document_name, 'zh-Hans-CN') ||
      a.index - b.index,
  );
});

const testTitle = computed(() => `${testingSet.value?.name || ''} · 知识检索验证`);

function segmentById(id: number) {
  return props.segments.find((s) => s.id === id);
}

function filterCategory(input: string, option: any) {
  return String(option?.label || '').toLowerCase().includes(input.toLowerCase());
}

function openEditor(item?: KnowledgeSet) {
  editingId.value = item?.id;
  Object.assign(form, {
    name: item?.name || '',
    category: item?.category || '',
    description: item?.description || '',
    segment_ids: [...(item?.segment_ids || [])],
  });
  Object.assign(pickFilter, { documentId: undefined, tag: undefined, keyword: '' });
  editorOpen.value = true;
}

function addSegment(id: number) {
  if (!form.segment_ids.includes(id)) form.segment_ids.push(id);
}

/** 供父组件桥接：新建知识集并预选片段（片段工作台「创建为知识集」入口） */
function openCreate(segmentIds: number[] = []) {
  openEditor();
  form.segment_ids = [...new Set(segmentIds)];
}

defineExpose({ openCreate });

function removeSegment(id: number) {
  form.segment_ids = form.segment_ids.filter((v) => v !== id);
}

async function handleSave() {
  if (!form.name.trim()) return createMessage.warning('请填写知识集名称');
  if (!form.category.trim()) return createMessage.warning('请填写业务分类');
  if (!form.segment_ids.length) return createMessage.warning('请至少选择一个知识片段');
  saving.value = true;
  try {
    const payload = {
      name: form.name.trim(),
      category: form.category.trim(),
      description: form.description.trim() || undefined,
      segment_ids: form.segment_ids,
    };
    if (editingId.value) {
      await updateKnowledgeSet(editingId.value, payload);
      createMessage.success('知识集已更新');
    } else {
      await createKnowledgeSet(payload);
      createMessage.success('知识集已创建');
    }
    editorOpen.value = false;
    emit('changed');
  } catch (error: any) {
    createMessage.error(formatApiErrorMessage(error, '保存知识集失败'));
  } finally {
    saving.value = false;
  }
}

async function removeSet(item: KnowledgeSet) {
  try {
    await deleteKnowledgeSet(item.id);
    createMessage.success('知识集已删除');
    emit('changed');
  } catch (error: any) {
    createMessage.error(formatApiErrorMessage(error, '删除知识集失败'));
  }
}

function openTest(item: KnowledgeSet) {
  testingSet.value = item;
  testQuery.value = '';
  testSources.value = [];
  testOpen.value = true;
}

async function runTest() {
  if (!testingSet.value || !testQuery.value.trim()) return createMessage.warning('请输入检索内容');
  testing.value = true;
  try {
    const res: any = await searchKnowledgeSet(testingSet.value.id, testQuery.value.trim(), testTopK.value);
    testSources.value = res?.data || res || [];
    if (!testSources.value.length) createMessage.warning('未检索到相关片段，可检查片段是否启用、或换个问法');
  } catch (error: any) {
    createMessage.error(formatApiErrorMessage(error, '检索失败'));
  } finally {
    testing.value = false;
  }
}

function scorePercent(item: RagSource) {
  // 混合检索得分理论上限约 1.0（向量 0.75 + 关键词加权 0.25）
  return Math.max(1, Math.min(100, Math.round(item.score * 100)));
}
</script>

<style lang="less" scoped>
@kset-primary: #08979c;

.kset__toolbar {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.w-240 { width: 240px; }

.kset__empty {
  padding: 60px 0;
}

.kset__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(330px, 1fr));
  gap: 14px;
}

.kset-card {
  display: flex;
  flex-direction: column;
  padding: 16px 18px;
  border: 1px solid #e8e8ec;
  border-radius: 10px;
  background: #fff;
  transition: border-color 0.2s, box-shadow 0.2s;

  &:hover {
    border-color: fade(@kset-primary, 55%);
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
    background: #e6fffb;
    color: @kset-primary;
    font-size: 18px;
    flex-shrink: 0;
  }

  &__title-box {
    min-width: 0;

    h3 {
      margin: 0 0 4px;
      font-size: 15px;
      font-weight: 600;
      color: rgba(0, 0, 0, 0.88);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    :deep(.ant-tag) {
      margin: 0;
    }
  }

  &__desc {
    display: -webkit-box;
    overflow: hidden;
    margin: 10px 0;
    color: rgba(0, 0, 0, 0.55);
    font-size: 12.5px;
    line-height: 1.7;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
    min-height: 42px;
  }

  &__metrics {
    display: flex;
    padding: 10px 12px;
    border-radius: 8px;
    background: #fafbfc;

    > div {
      flex: 1;
      text-align: center;

      b {
        font-size: 17px;
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
    margin-top: 10px;
    padding-top: 6px;
    border-top: 1px solid #f2f2f5;
  }

  &__actions {
    display: flex;
    align-items: center;
  }
}

/* ===== 编辑抽屉：双栏选段器 ===== */
.kset-editor__row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 240px;
  gap: 16px;
}

.kset-editor__meta {
  margin-bottom: 14px;
}

.kset-editor__pick {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.kset-pane {
  display: flex;
  flex-direction: column;
  border: 1px solid #e8e8ec;
  border-radius: 10px;
  overflow: hidden;
  min-height: 420px;

  &--target {
    background: #fafffe;
    border-color: #b5f0ec;
  }

  &__head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 14px;
    border-bottom: 1px solid #f0f1f5;
    background: #fafbfc;
  }

  &__title {
    font-size: 13px;
    font-weight: 600;
    color: rgba(0, 0, 0, 0.8);
  }

  &__count {
    font-size: 12px;
    color: rgba(0, 0, 0, 0.4);
  }

  &__filters {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    padding: 10px 12px;
    border-bottom: 1px solid #f0f1f5;

    /* 显式宽度写在组件自身模板的 class 上，不依赖后代选择器命中子组件根节点 */
    .filter-doc {
      width: 148px;
      flex-shrink: 0;
    }

    .filter-tag {
      width: 122px;
      flex-shrink: 0;
    }

    .filter-search {
      flex: 1;
      min-width: 110px;
    }
  }

  &__list {
    flex: 1;
    overflow-y: auto;
    max-height: 430px;
  }

  &__empty {
    display: grid;
    place-items: center;
    height: 160px;
    color: rgba(0, 0, 0, 0.35);
    font-size: 12.5px;
    text-align: center;
    line-height: 1.8;
  }
}

.kset-pick-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 12px;
  border-bottom: 1px solid #f5f5f8;
  cursor: pointer;
  transition: background 0.15s;

  &:hover {
    background: #f7fbff;
  }

  &.off .kset-pick-row__name,
  &.off .kset-pick-row__desc {
    opacity: 0.5;
  }

  &.is-added {
    background: #fafbfc;

    .kset-pick-row__name {
      color: rgba(0, 0, 0, 0.45);
    }
  }

  &--picked {
    cursor: default;

    &:hover {
      background: #f3fdfc;
    }
  }

  &__order {
    display: grid;
    place-items: center;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: #e6fffb;
    color: @kset-primary;
    font-size: 11px;
    font-weight: 600;
    flex-shrink: 0;
  }

  &__main {
    flex: 1;
    min-width: 0;
  }

  &__title {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  &__name {
    font-size: 13px;
    font-weight: 500;
    color: rgba(0, 0, 0, 0.85);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__off {
    flex-shrink: 0;
    font-size: 11px;
    color: rgba(0, 0, 0, 0.4);
  }

  &__desc {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-top: 3px;
    font-size: 12px;
    color: rgba(0, 0, 0, 0.45);
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;

    :deep(.ant-tag) {
      margin: 0;
      flex-shrink: 0;
      font-size: 11px;
      line-height: 16px;
      padding: 0 5px;
    }

    span {
      overflow: hidden;
      text-overflow: ellipsis;
    }
  }
}

.kset-editor__footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

/* ===== 检索验证 ===== */
.kset-test__ask {
  display: flex;
  gap: 10px;
  margin-bottom: 18px;

  .ant-input-affix-wrapper,
  .ant-input { flex: 1; }
}

.kset-hit {
  padding: 12px 14px;
  margin-bottom: 10px;
  border: 1px solid #e8e8ec;
  border-radius: 10px;

  &__head {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  &__rank {
    font-size: 12px;
    font-weight: 700;
    color: @kset-primary;
  }

  &__score {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-left: auto;
    width: 180px;
  }

  &__score-bar {
    flex: 1;
    height: 6px;
    border-radius: 3px;
    background: #f0f1f5;
    overflow: hidden;
  }

  &__score-fill {
    height: 100%;
    border-radius: 3px;
    background: linear-gradient(90deg, #87e8de, @kset-primary);
  }

  &__score-num {
    font-size: 12px;
    font-weight: 600;
    color: @kset-primary;
    width: 38px;
    text-align: right;
  }

  &__content {
    margin: 10px 0 0;
    font-size: 12.5px;
    line-height: 1.8;
    color: rgba(0, 0, 0, 0.7);
    white-space: pre-wrap;
    word-break: break-word;
  }
}
</style>
