<template>
  <a-drawer
    :open="open"
    :width="720"
    :title="isEdit ? '编辑知识片段' : '人工标注知识片段'"
    destroy-on-close
    @close="handleClose"
  >
    <div class="seg-drawer">
      <a-form layout="vertical">
        <a-form-item label="来源文档" required>
          <a-select
            v-model:value="form.document_id"
            :disabled="isEdit"
            placeholder="选择知识来源文档"
            :options="documentOptions"
          />
        </a-form-item>
        <a-form-item label="片段标题" required help="用一句话概括该知识，将作为检索命中的首要摘要">
          <a-input v-model:value="form.title" placeholder="如：3 号皮带机跑偏的调整步骤" :maxlength="80" show-count />
        </a-form-item>
        <a-form-item label="知识内容" required>
          <a-textarea
            v-model:value="form.content"
            :rows="10"
            placeholder="整理自文档原文或人工补充。内容完整、自成一体的片段检索效果最好"
            :maxlength="8000"
            show-count
          />
        </a-form-item>
        <a-form-item label="业务标签" help="用于知识治理筛选，也便于按场景组装知识集">
          <a-select
            v-model:value="form.tags"
            mode="tags"
            :token-separators="[',', '，']"
            placeholder="输入标签后回车，如：皮带机、故障处置"
            :options="tagOptions"
          />
        </a-form-item>
        <a-form-item>
          <div class="seg-enable">
            <div>
              <div class="seg-enable__label">参与检索</div>
              <div class="seg-enable__desc">停用后该片段不进入向量检索，知识集引用数不变</div>
            </div>
            <a-switch v-model:checked="form.is_enabled" checked-children="启用" un-checked-children="停用" />
          </div>
        </a-form-item>
      </a-form>
    </div>
    <template #footer>
      <div class="seg-drawer__footer">
        <a-popconfirm
          v-if="isEdit"
          title="删除后引用该片段的知识集将自动解除引用，确定删除？"
          ok-text="删除"
          cancel-text="取消"
          @confirm="handleDelete"
        >
          <a-button danger>删除片段</a-button>
        </a-popconfirm>
        <div class="seg-drawer__footer-main">
          <a-button @click="handleClose">取消</a-button>
          <a-button type="primary" :loading="saving" @click="handleSave">
            {{ isEdit ? '保存并向量化' : '创建并向量化' }}
          </a-button>
        </div>
      </div>
    </template>
  </a-drawer>
</template>

<script lang="ts" setup>
import { computed, reactive, ref, watch } from 'vue';
import {
  Drawer as ADrawer,
  Form as AForm,
  FormItem as AFormItem,
  Select as ASelect,
  Input as AInput,
  Textarea as ATextarea,
  Switch as ASwitch,
  Button as AButton,
  Popconfirm as APopconfirm,
} from 'ant-design-vue';
import { useMessage } from '@/hooks/web/useMessage';
import {
  createKnowledgeSegment,
  deleteKnowledgeSegment,
  updateKnowledgeSegment,
  type KnowledgeDocument,
  type KnowledgeSegment,
} from '@/api/device/rag';
import { formatApiErrorMessage } from '@/views/camera/utils/apiErrorMessage';

defineOptions({ name: 'RagSegmentEditorDrawer' });

const props = defineProps<{
  open: boolean;
  documents: KnowledgeDocument[];
  /** 编辑目标；为空表示新建 */
  segment?: KnowledgeSegment | null;
  /** 新建时预选的来源文档 */
  defaultDocumentId?: number;
  /** 已有业务标签，作为输入建议 */
  knownTags?: string[];
}>();

const emit = defineEmits(['update:open', 'saved']);

const { createMessage } = useMessage();
const saving = ref(false);

const form = reactive({
  document_id: undefined as number | undefined,
  title: '',
  content: '',
  tags: [] as string[],
  is_enabled: true,
});

const isEdit = computed(() => !!props.segment?.id);
const documentOptions = computed(() => props.documents.map((d) => ({ label: d.name, value: d.id })));
const tagOptions = computed(() => (props.knownTags || []).map((t) => ({ label: t, value: t })));

function fillForm() {
  if (props.segment) {
    Object.assign(form, {
      document_id: props.segment.document_id,
      title: props.segment.title,
      content: props.segment.content,
      tags: [...(props.segment.tags || [])],
      is_enabled: props.segment.is_enabled !== false,
    });
  } else {
    Object.assign(form, {
      document_id: props.defaultDocumentId,
      title: '',
      content: '',
      tags: [],
      is_enabled: true,
    });
  }
}

watch(
  () => props.open,
  (open) => {
    if (open) fillForm();
  },
);

function handleClose() {
  emit('update:open', false);
}

async function handleSave() {
  if (!form.document_id) return createMessage.warning('请选择来源文档');
  if (!form.title.trim()) return createMessage.warning('请填写片段标题');
  if (!form.content.trim()) return createMessage.warning('请填写知识内容');
  saving.value = true;
  try {
    const payload = {
      title: form.title.trim(),
      content: form.content.trim(),
      tags: form.tags.map((t) => t.trim()).filter(Boolean),
      is_enabled: form.is_enabled,
    };
    if (isEdit.value && props.segment) {
      await updateKnowledgeSegment(props.segment.id, payload);
      createMessage.success('片段已保存并向量化');
    } else {
      await createKnowledgeSegment(form.document_id, payload);
      createMessage.success('片段已创建并向量化');
    }
    emit('update:open', false);
    emit('saved');
  } catch (error: any) {
    createMessage.error(formatApiErrorMessage(error, '保存知识片段失败'));
  } finally {
    saving.value = false;
  }
}

async function handleDelete() {
  if (!props.segment) return;
  try {
    await deleteKnowledgeSegment(props.segment.id);
    createMessage.success('片段已删除');
    emit('update:open', false);
    emit('saved');
  } catch (error: any) {
    createMessage.error(formatApiErrorMessage(error, '删除知识片段失败'));
  }
}
</script>

<style lang="less" scoped>
.seg-drawer {
  padding: 0 4px;
}

.seg-enable {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 14px;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  background: #fafbfc;

  &__label {
    font-size: 14px;
    font-weight: 500;
    color: rgba(0, 0, 0, 0.85);
  }

  &__desc {
    font-size: 12px;
    color: rgba(0, 0, 0, 0.45);
    margin-top: 2px;
  }
}

.seg-drawer__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.seg-drawer__footer-main {
  display: flex;
  gap: 10px;
  margin-left: auto;
}
</style>
