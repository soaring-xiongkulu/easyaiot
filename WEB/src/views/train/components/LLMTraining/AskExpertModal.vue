<template>
  <a-modal
    :open="open"
    :width="680"
    :title="expert ? `与「${expert.name}」问答` : '专家问答'"
    :footer="null"
    destroy-on-close
    @cancel="handleClose"
  >
    <div class="ask-modal">
      <div ref="listRef" class="ask-modal__list">
        <a-empty v-if="!messages.length" class="ask-modal__empty" :description="emptyText" />
        <template v-else>
          <div v-for="(msg, index) in messages" :key="index" class="ask-msg" :class="msg.role">
            <div class="ask-msg__bubble">
              <p class="ask-msg__text">{{ msg.content }}</p>
              <template v-if="msg.role === 'assistant'">
                <a-alert
                  v-if="msg.warning"
                  class="ask-msg__warning"
                  type="warning"
                  show-icon
                  :message="`模型暂不可用，已降级返回检索结果：${msg.warning}`"
                />
                <div v-if="msg.sources?.length" class="ask-msg__sources">
                  <div class="ask-msg__sources-title">依据来源</div>
                  <div v-for="source in msg.sources" :key="source.segment_id" class="ask-msg__source">
                    <a-tag>【资料 {{ msg.sources.indexOf(source) + 1 }}】</a-tag>
                    <span class="ask-msg__source-name" :title="source.document_name">{{ source.document_name }}</span>
                    <span class="ask-msg__source-score">{{ scorePercent(source.score) }}%</span>
                  </div>
                </div>
              </template>
            </div>
          </div>
        </template>
        <div v-if="asking" class="ask-msg assistant">
          <div class="ask-msg__bubble ask-msg__bubble--pending">正在检索知识并生成回答…</div>
        </div>
      </div>
      <div class="ask-modal__input">
        <a-textarea
          v-model:value="question"
          :auto-size="{ minRows: 1, maxRows: 3 }"
          placeholder="输入业务问题，回车发送（Shift+回车换行）"
          @keydown.enter.exact.prevent="send"
        />
        <a-button type="primary" :loading="asking" :disabled="!question.trim()" @click="send">发送</a-button>
      </div>
    </div>
  </a-modal>
</template>

<script lang="ts" setup>
import { computed, nextTick, ref, watch } from 'vue';
import {
  Modal as AModal,
  Button as AButton,
  Textarea as ATextarea,
  Tag as ATag,
  Alert as AAlert,
  Empty as AEmpty,
} from 'ant-design-vue';
import { useMessage } from '@/hooks/web/useMessage';
import { chatWithRagExpert, type RagExpert, type RagSource } from '@/api/device/rag';
import { formatApiErrorMessage } from '@/views/camera/utils/apiErrorMessage';

defineOptions({ name: 'RagAskExpertModal' });

const props = defineProps<{
  open: boolean;
  expert: RagExpert | null;
}>();

const emit = defineEmits(['update:open']);

const { createMessage } = useMessage();

interface ChatMsg {
  role: 'user' | 'assistant';
  content: string;
  sources?: RagSource[];
  warning?: string;
}

const messages = ref<ChatMsg[]>([]);
const question = ref('');
const asking = ref(false);
const listRef = ref<HTMLElement>();

const emptyText = computed(() => props.expert?.welcome_message || '该专家还没有设置欢迎语，直接输入问题开始提问');

watch(
  () => props.open,
  (open) => {
    if (open) {
      messages.value = [];
      question.value = '';
    }
  },
);

async function scrollToBottom() {
  await nextTick();
  listRef.value?.scrollTo({ top: listRef.value.scrollHeight, behavior: 'smooth' });
}

function scorePercent(score: number) {
  return Math.min(100, Math.round(score * 100));
}

async function send() {
  const text = question.value.trim();
  if (!text || asking.value || !props.expert) return;
  question.value = '';
  messages.value.push({ role: 'user', content: text });
  scrollToBottom();
  asking.value = true;
  try {
    // 多轮上下文：只传 user/assistant 文本，不含来源等展示字段
    const history = messages.value
      .filter((m) => m.content)
      .slice(0, -1)
      .map((m) => ({ role: m.role, content: m.content }));
    const res: any = await chatWithRagExpert(props.expert.id, text, { history });
    const data = res?.data || res || {};
    messages.value.push({
      role: 'assistant',
      content: data.response || '（空回答）',
      sources: data.sources || [],
      warning: data.degraded ? data.warning || '模型调用失败' : '',
    });
  } catch (error: any) {
    createMessage.error(formatApiErrorMessage(error, '专家问答失败'));
    messages.value.push({ role: 'assistant', content: '（本次回答失败，请重试）' });
  } finally {
    asking.value = false;
    scrollToBottom();
  }
}

function handleClose() {
  emit('update:open', false);
}
</script>

<style lang="less" scoped>
.ask-modal {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ask-modal__list {
  height: 420px;
  overflow-y: auto;
  padding: 4px;
  background: #fafbfc;
  border-radius: 8px;
}

.ask-modal__empty {
  padding-top: 150px;
}

.ask-msg {
  display: flex;
  margin-bottom: 12px;

  &.user {
    justify-content: flex-end;

    .ask-msg__bubble {
      background: #e6f4ff;
      border-color: #91caff;
    }
  }

  &.assistant .ask-msg__bubble {
    background: #fff;
    border-color: #e8e8ec;
  }

  &__bubble {
    max-width: 82%;
    padding: 10px 14px;
    border: 1px solid transparent;
    border-radius: 10px;

    &--pending {
      color: rgba(0, 0, 0, 0.45);
      font-size: 13px;
    }
  }

  &__text {
    margin: 0;
    font-size: 13.5px;
    line-height: 1.75;
    white-space: pre-wrap;
    word-break: break-word;
  }

  &__warning {
    margin-top: 8px;
  }

  &__sources {
    margin-top: 10px;
    padding-top: 8px;
    border-top: 1px dashed #e8e8ec;
  }

  &__sources-title {
    margin-bottom: 6px;
    font-size: 12px;
    color: rgba(0, 0, 0, 0.45);
  }

  &__source {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 4px;
    font-size: 12px;

    :deep(.ant-tag) {
      margin: 0;
      font-size: 11px;
      line-height: 18px;
      padding: 0 6px;
    }
  }

  &__source-name {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: rgba(0, 0, 0, 0.65);
  }

  &__source-score {
    margin-left: auto;
    flex-shrink: 0;
    color: #1677ff;
    font-variant-numeric: tabular-nums;
  }
}

.ask-modal__input {
  display: flex;
  align-items: flex-end;
  gap: 10px;

  :deep(.ant-input) {
    resize: none;
  }
}
</style>
