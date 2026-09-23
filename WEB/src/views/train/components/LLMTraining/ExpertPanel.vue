<template>
  <div class="expert">
    <div class="expert__toolbar">
      <a-input v-model:value="keyword" allow-clear placeholder="搜索专家名称" class="w-240" />
      <div class="expert__hint">
        <InfoCircleOutlined />
        专家可被「算法任务 · 大模型后处理规则」选为研判智能体；停用后不可再被新规则选择
      </div>
    </div>

    <a-empty v-if="!filteredExperts.length" class="expert__empty" description="暂无 RAG 专家，点击右上角创建" />

    <div v-else class="expert__grid">
      <article v-for="item in filteredExperts" :key="item.id" class="expert-card" :class="{ off: !item.is_enabled }">
        <header class="expert-card__head">
          <div class="expert-card__icon"><RobotOutlined /></div>
          <div class="expert-card__title-box">
            <h3 :title="item.name">{{ item.name }}</h3>
            <a-tag color="purple">{{ item.category }}</a-tag>
          </div>
          <a-switch
            size="small"
            :checked="item.is_enabled"
            :loading="togglingId === item.id"
            @change="(checked: any) => toggleEnabled(item, checked)"
          />
        </header>
        <div class="expert-card__sets">
          <a-tag v-for="name in item.knowledge_set_names" :key="name" class="expert-card__set">
            <FolderOutlined /> {{ name }}
          </a-tag>
          <span v-if="!item.knowledge_set_names.length" class="expert-card__nosets">未关联知识集</span>
        </div>
        <p class="expert-card__prompt">{{ item.system_prompt }}</p>
        <footer class="expert-card__foot">
          <div class="expert-card__main-actions">
            <a-button type="link" size="small" @click="openAsk(item)">
              <template #icon><MessageOutlined /></template>
              快速问答
            </a-button>
            <a-button type="link" size="small" @click="openEditor(item)">
              <template #icon><EditOutlined /></template>
              配置与调试
            </a-button>
          </div>
          <a-popconfirm
            title="确认删除专家？知识集与片段不会被删除。"
            ok-text="删除"
            cancel-text="取消"
            @confirm="removeExpert(item)"
          >
            <a-button danger type="text" size="small">
              <template #icon><DeleteOutlined /></template>
            </a-button>
          </a-popconfirm>
        </footer>
      </article>
    </div>

    <!-- 配置 + 调试 双栏抽屉 -->
    <a-drawer
      v-model:open="editorOpen"
      :width="1200"
      :title="editingId ? '配置与调试 RAG 专家' : '创建 RAG 专家'"
      destroy-on-close
    >
      <div class="expert-editor">
        <!-- 左：配置 -->
        <div class="expert-editor__config">
          <a-form layout="vertical">
            <div class="expert-editor__row">
              <a-form-item label="专家名称" required class="expert-editor__name">
                <a-input v-model:value="form.name" placeholder="如：皮带机故障处置专家" :maxlength="50" />
              </a-form-item>
              <a-form-item label="业务分类" required class="expert-editor__cat">
                <a-auto-complete
                  v-model:value="form.category"
                  :options="categoryOptions"
                  placeholder="选择或输入分类"
                  :filter-option="filterCategory"
                />
              </a-form-item>
            </div>

            <a-form-item required>
              <template #label>
                关联知识集
                <span class="expert-editor__label-hint">勾选后专家使用这些知识集的启用片段做检索</span>
              </template>
              <div class="expert-editor__sets">
                <label
                  v-for="set in sets"
                  :key="set.id"
                  class="expert-set-chip"
                  :class="{ active: form.knowledge_set_ids.includes(set.id) }"
                >
                  <a-checkbox
                    :checked="form.knowledge_set_ids.includes(set.id)"
                    @change="(e: any) => toggleSet(set.id, e.target.checked)"
                  />
                  <div class="expert-set-chip__body">
                    <div class="expert-set-chip__name" :title="set.name">{{ set.name }}</div>
                    <div class="expert-set-chip__meta">{{ set.segment_count }} 片段 · {{ set.document_count }} 文档</div>
                  </div>
                </label>
                <div v-if="!sets.length" class="expert-editor__nosets">
                  还没有知识集，请先到「知识集」页签创建
                </div>
              </div>
            </a-form-item>

            <a-form-item required>
              <template #label>
                专家指令（System Prompt）
                <a-select
                  :value="undefined"
                  size="small"
                  class="expert-editor__preset"
                  placeholder="套用预设模板"
                  :options="presetOptions"
                  @change="applyPreset"
                />
              </template>
              <a-textarea
                v-model:value="form.system_prompt"
                :rows="9"
                placeholder="定义专家角色、回答边界与输出格式；建议直接套用预设模板后微调"
              />
              <div class="expert-editor__prompt-help">
                专业建议：明确「仅依据资料回答」与拒答边界，可显著抑制大模型幻觉；引用格式建议统一为【资料 n】
              </div>
            </a-form-item>

            <a-form-item label="欢迎语">
              <a-textarea v-model:value="form.welcome_message" :rows="2" placeholder="调试对话的欢迎语（可选）" />
            </a-form-item>

            <div class="expert-editor__enable">
              <div>
                <div class="expert-editor__enable-label">启用专家</div>
                <div class="expert-editor__enable-desc">停用后不影响已有配置，但算法任务将无法选择该专家</div>
              </div>
              <a-switch v-model:checked="form.is_enabled" checked-children="启用" un-checked-children="停用" />
            </div>
          </a-form>
        </div>

        <!-- 右：调试 -->
        <div class="expert-editor__debug">
          <div class="expert-debug">
            <div class="expert-debug__head">
              <span class="expert-debug__title">调试对话</span>
              <div class="expert-debug__tools">
                <span class="expert-debug__tool-label">Top-K</span>
                <a-input-number v-model:value="topK" :min="1" :max="10" size="small" style="width: 70px" />
                <a-button size="small" type="text" :disabled="!messages.length" @click="clearChat">清空</a-button>
              </div>
            </div>

            <div ref="chatBoxRef" class="expert-debug__body">
              <template v-if="messages.length">
                <div v-for="(msg, index) in messages" :key="index" class="expert-msg" :class="`expert-msg--${msg.role}`">
                  <div class="expert-msg__bubble">{{ msg.content }}</div>
                  <template v-if="msg.role === 'assistant'">
                    <a-alert
                      v-if="msg.warning"
                      type="warning"
                      show-icon
                      class="expert-msg__warn"
                      message="模型暂不可用，已降级返回检索结果"
                    />
                    <div v-if="msg.sources?.length" class="expert-msg__sources">
                      <div class="expert-msg__sources-title">引用资料（{{ msg.sources.length }}）</div>
                      <div v-for="(src, srcIndex) in msg.sources" :key="src.segment_id" class="expert-msg__source">
                        <span class="expert-msg__source-rank">【资料 {{ srcIndex + 1 }}】</span>
                        <span class="expert-msg__source-doc">{{ src.document_name }}</span>
                        <span class="expert-msg__source-score">{{ scorePercent(src) }}%</span>
                      </div>
                    </div>
                  </template>
                </div>
              </template>
              <div v-else class="expert-debug__empty">
                <RobotOutlined />
                <p>{{ form.welcome_message || '输入问题开始调试：右侧回答将附带引用资料与相关度' }}</p>
                <span>保存专家后即可对话；未保存的配置修改不影响调试使用的线上版本</span>
              </div>
            </div>

            <div class="expert-debug__input">
              <a-input
                v-model:value="question"
                :disabled="!editingId"
                placeholder="输入测试问题，回车发送"
                @press-enter="send"
              />
              <a-button type="primary" :loading="chatting" :disabled="!editingId" @click="send">发送</a-button>
            </div>
            <div v-if="!editingId" class="expert-debug__tip">请先保存专家，再进行效果调试</div>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="expert-editor__footer">
          <a-button @click="editorOpen = false">取消</a-button>
          <a-button type="primary" :loading="saving" @click="handleSave">
            {{ editingId ? '保存配置' : '创建并调试' }}
          </a-button>
        </div>
      </template>
    </a-drawer>

    <!-- 快速问答：无需进入配置抽屉的轻量对话 -->
    <AskExpertModal v-model:open="askOpen" :expert="askingExpert" />
  </div>
</template>

<script lang="ts" setup>
import { computed, nextTick, ref } from 'vue';
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
  Switch as ASwitch,
  Checkbox as ACheckbox,
  Popconfirm as APopconfirm,
  Empty as AEmpty,
  Alert as AAlert,
} from 'ant-design-vue';
import {
  DeleteOutlined,
  EditOutlined,
  FolderOutlined,
  InfoCircleOutlined,
  MessageOutlined,
  RobotOutlined,
} from '@ant-design/icons-vue';
import { useMessage } from '@/hooks/web/useMessage';
import {
  chatWithRagExpert,
  createRagExpert,
  deleteRagExpert,
  updateRagExpert,
  type KnowledgeSet,
  type RagChatMessage,
  type RagExpert,
  type RagSource,
} from '@/api/device/rag';
import { formatApiErrorMessage } from '@/views/camera/utils/apiErrorMessage';
import { RAG_CATEGORIES, RAG_PROMPT_PRESETS } from './ragPresets';
import AskExpertModal from './AskExpertModal.vue';

defineOptions({ name: 'RagExpertPanel' });

interface ChatMsg extends RagChatMessage {
  sources?: RagSource[];
  warning?: string;
  model?: string | null;
}

const props = defineProps<{
  experts: RagExpert[];
  sets: KnowledgeSet[];
}>();

const emit = defineEmits(['changed']);

const { createMessage } = useMessage();
const RENDER_LIMIT = 60;

const keyword = ref('');
const editorOpen = ref(false);
const saving = ref(false);
const editingId = ref<number>();
const form = ref({
  name: '',
  category: '',
  knowledge_set_ids: [] as number[],
  system_prompt: '',
  welcome_message: '',
  is_enabled: true,
});

const topK = ref(5);
const question = ref('');
const chatting = ref(false);
const messages = ref<ChatMsg[]>([]);
const chatBoxRef = ref<HTMLElement>();
const togglingId = ref<number | null>(null);
const askOpen = ref(false);
const askingExpert = ref<RagExpert | null>(null);

function openAsk(item: RagExpert) {
  askingExpert.value = item;
  askOpen.value = true;
}

const filteredExperts = computed(() => {
  const key = keyword.value.trim().toLowerCase();
  return props.experts.filter((e) => !key || e.name.toLowerCase().includes(key)).slice(0, RENDER_LIMIT);
});
const categoryOptions = computed(() => {
  const known = new Set(props.experts.map((e) => e.category));
  return [...new Set([...RAG_CATEGORIES, ...known])].map((c) => ({ label: c, value: c }));
});
const presetOptions = computed(() =>
  RAG_PROMPT_PRESETS.map((p) => ({ label: p.label, value: p.key, title: p.description })),
);

function filterCategory(input: string, option: any) {
  return String(option?.label || '').toLowerCase().includes(input.toLowerCase());
}

function openEditor(item?: RagExpert) {
  editingId.value = item?.id;
  form.value = {
    name: item?.name || '',
    category: item?.category || '',
    knowledge_set_ids: [...(item?.knowledge_set_ids || [])],
    system_prompt: item?.system_prompt || '',
    welcome_message: item?.welcome_message || '',
    is_enabled: item?.is_enabled !== false,
  };
  messages.value = [];
  question.value = '';
  editorOpen.value = true;
}

function applyPreset(key: string) {
  const preset = RAG_PROMPT_PRESETS.find((p) => p.key === key);
  if (!preset) return;
  form.value.system_prompt = preset.prompt;
  createMessage.success(`已套用「${preset.label}」，可继续微调`);
}

function toggleSet(id: number, checked: boolean) {
  if (checked) {
    if (!form.value.knowledge_set_ids.includes(id)) form.value.knowledge_set_ids.push(id);
  } else {
    form.value.knowledge_set_ids = form.value.knowledge_set_ids.filter((v) => v !== id);
  }
}

async function toggleEnabled(item: RagExpert, checked: boolean) {
  togglingId.value = item.id;
  try {
    // 后端为整体覆盖语义，携带完整记录仅切换启用状态
    await updateRagExpert(item.id, { ...item, is_enabled: checked === true });
    item.is_enabled = checked === true;
    emit('changed');
    createMessage.success(checked ? '专家已启用' : '专家已停用，算法任务将无法选择它');
  } catch (error: any) {
    createMessage.error(formatApiErrorMessage(error, '更新专家状态失败'));
  } finally {
    togglingId.value = null;
  }
}

async function handleSave() {
  if (!form.value.name.trim()) return createMessage.warning('请填写专家名称');
  if (!form.value.category.trim()) return createMessage.warning('请填写业务分类');
  if (!form.value.knowledge_set_ids.length) return createMessage.warning('请至少关联一个知识集');
  if (!form.value.system_prompt.trim()) return createMessage.warning('请填写专家指令');
  saving.value = true;
  try {
    const payload = {
      name: form.value.name.trim(),
      category: form.value.category.trim(),
      knowledge_set_ids: form.value.knowledge_set_ids,
      system_prompt: form.value.system_prompt.trim(),
      welcome_message: form.value.welcome_message.trim() || undefined,
      is_enabled: form.value.is_enabled,
    };
    if (editingId.value) {
      await updateRagExpert(editingId.value, payload);
      createMessage.success('专家配置已保存');
    } else {
      const created: any = await createRagExpert(payload);
      const record = created?.data || created;
      if (record?.id) editingId.value = Number(record.id);
      createMessage.success('专家已创建，可在右侧直接调试');
      emit('changed');
    }
  } catch (error: any) {
    createMessage.error(formatApiErrorMessage(error, '保存专家失败'));
  } finally {
    saving.value = false;
  }
}

async function send() {
  const text = question.value.trim();
  if (!text) return;
  if (!editingId.value) return createMessage.warning('请先保存专家，再进行调试');
  const history: RagChatMessage[] = messages.value.map(({ role, content }) => ({ role, content }));
  messages.value.push({ role: 'user', content: text });
  question.value = '';
  scrollToBottom();
  chatting.value = true;
  try {
    const res: any = await chatWithRagExpert(editingId.value, text, { history, topK: topK.value });
    const data = res?.data || res || {};
    messages.value.push({
      role: 'assistant',
      content: data.response || '（空回复）',
      sources: data.sources || [],
      warning: data.degraded ? data.warning : undefined,
      model: data.model ?? null,
    });
  } catch (error: any) {
    messages.value.push({ role: 'assistant', content: `调用失败：${formatApiErrorMessage(error, '专家问答失败')}` });
  } finally {
    chatting.value = false;
    scrollToBottom();
  }
}

function clearChat() {
  messages.value = [];
}

function scrollToBottom() {
  nextTick(() => chatBoxRef.value?.scrollTo({ top: chatBoxRef.value.scrollHeight }));
}

async function removeExpert(item: RagExpert) {
  try {
    await deleteRagExpert(item.id);
    createMessage.success('专家已删除');
    emit('changed');
  } catch (error: any) {
    createMessage.error(formatApiErrorMessage(error, '删除专家失败'));
  }
}

function scorePercent(item: RagSource) {
  return Math.max(1, Math.min(100, Math.round(item.score * 100)));
}
</script>

<style lang="less" scoped>
@expert-primary: #722ed1;

.expert__toolbar {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.w-240 { width: 240px; }

.expert__hint {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
}

.expert__empty {
  padding: 60px 0;
}

.expert__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 14px;
}

.expert-card {
  display: flex;
  flex-direction: column;
  padding: 16px 18px;
  border: 1px solid #e8e8ec;
  border-radius: 10px;
  background: #fff;
  transition: border-color 0.2s, box-shadow 0.2s;

  &:hover {
    border-color: fade(@expert-primary, 50%);
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  }

  &.off {
    background: #fafafa;

    .expert-card__title-box,
    .expert-card__prompt {
      opacity: 0.55;
    }
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
    background: #f9f0ff;
    color: @expert-primary;
    font-size: 18px;
    flex-shrink: 0;
  }

  &__title-box {
    flex: 1;
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

  &__sets {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    margin-top: 10px;

    :deep(.ant-tag) {
      margin: 0;
      font-size: 11.5px;
    }
  }

  &__set {
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__nosets {
    font-size: 12px;
    color: rgba(0, 0, 0, 0.35);
  }

  &__prompt {
    display: -webkit-box;
    overflow: hidden;
    margin: 10px 0;
    color: rgba(0, 0, 0, 0.55);
    font-size: 12.5px;
    line-height: 1.7;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
  }

  &__main-actions {
    display: flex;
    align-items: center;
  }

  &__foot {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: auto;
    padding-top: 6px;
    border-top: 1px solid #f2f2f5;
  }
}

/* ===== 配置 + 调试 ===== */
.expert-editor {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 430px;
  gap: 20px;
  align-items: start;
}

.expert-editor__row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 220px;
  gap: 16px;
}

.expert-editor__label-hint {
  font-size: 12px;
  font-weight: 400;
  color: rgba(0, 0, 0, 0.4);
  margin-left: 8px;
}

.expert-editor__sets {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.expert-set-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border: 1px solid #e8e8ec;
  border-radius: 8px;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;

  &:hover {
    border-color: fade(@expert-primary, 50%);
  }

  &.active {
    border-color: @expert-primary;
    background: #faf5ff;

    .expert-set-chip__name {
      color: @expert-primary;
    }
  }

  &__body {
    min-width: 0;
  }

  &__name {
    font-size: 13px;
    font-weight: 500;
    color: rgba(0, 0, 0, 0.85);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__meta {
    font-size: 11.5px;
    color: rgba(0, 0, 0, 0.4);
    margin-top: 1px;
  }
}

.expert-editor__nosets {
  padding: 14px;
  font-size: 12.5px;
  color: rgba(0, 0, 0, 0.4);
  background: #fafbfc;
  border-radius: 8px;
  grid-column: 1 / -1;
}

.expert-editor__preset {
  width: 150px;
  margin-left: 8px;
}

.expert-editor__prompt-help {
  margin-top: 6px;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
  line-height: 1.6;
}

.expert-editor__enable {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 14px;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  background: #fafbfc;

  &-label {
    font-size: 14px;
    font-weight: 500;
    color: rgba(0, 0, 0, 0.85);
  }

  &-desc {
    font-size: 12px;
    color: rgba(0, 0, 0, 0.45);
    margin-top: 2px;
  }
}

/* 调试面板 */
.expert-debug {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 220px);
  min-height: 480px;
  border: 1px solid #e8e8ec;
  border-radius: 10px;
  overflow: hidden;

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

  &__tools {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  &__tool-label {
    font-size: 12px;
    color: rgba(0, 0, 0, 0.45);
  }

  &__body {
    flex: 1;
    overflow-y: auto;
    padding: 14px;
    background: #fcfcfd;
  }

  &__empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    padding: 60px 20px;
    text-align: center;
    color: rgba(0, 0, 0, 0.4);

    svg {
      font-size: 34px;
      color: #d3adf7;
    }

    p {
      margin: 0;
      font-size: 13.5px;
      color: rgba(0, 0, 0, 0.65);
      line-height: 1.7;
    }

    span {
      font-size: 12px;
    }
  }

  &__input {
    display: flex;
    gap: 8px;
    padding: 12px 14px;
    border-top: 1px solid #f0f1f5;

    .ant-input-affix-wrapper,
    .ant-input { flex: 1; }
  }

  &__tip {
    padding: 0 14px 10px;
    font-size: 12px;
    color: rgba(0, 0, 0, 0.4);
  }
}

.expert-msg {
  display: flex;
  flex-direction: column;
  margin-bottom: 14px;

  &--user {
    align-items: flex-end;

    .expert-msg__bubble {
      background: @expert-primary;
      color: #fff;
      border-radius: 10px 10px 2px 10px;
    }
  }

  &--assistant {
    align-items: flex-start;

    .expert-msg__bubble {
      background: #fff;
      border: 1px solid #eeeef2;
      border-radius: 10px 10px 10px 2px;
    }
  }

  &__bubble {
    max-width: 88%;
    padding: 9px 12px;
    font-size: 13px;
    line-height: 1.75;
    white-space: pre-wrap;
    word-break: break-word;
  }

  &__warn {
    margin-top: 8px;
    max-width: 88%;
  }

  &__sources {
    max-width: 88%;
    margin-top: 8px;
    padding: 8px 10px;
    border: 1px dashed #e3d5f7;
    border-radius: 8px;
    background: #fff;
  }

  &__sources-title {
    font-size: 11.5px;
    color: rgba(0, 0, 0, 0.4);
    margin-bottom: 6px;
  }

  &__source {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 3px 0;
    font-size: 12px;
    min-width: 0;
  }

  &__source-rank {
    color: @expert-primary;
    flex-shrink: 0;
  }

  &__source-doc {
    color: rgba(0, 0, 0, 0.65);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    min-width: 0;
  }

  &__source-score {
    margin-left: auto;
    color: @expert-primary;
    font-weight: 600;
    flex-shrink: 0;
  }
}

.expert-editor__footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
