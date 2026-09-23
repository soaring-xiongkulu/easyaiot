<template>
  <BasicDrawer
    v-bind="$attrs"
    @register="register"
    :title="modalTitle"
    width="900"
    placement="right"
    :showFooter="true"
    :showCancelBtn="false"
    :showOkBtn="false"
  >
    <template #footer>
      <div class="footer-buttons">
        <Button @click="closeDrawer">{{ isViewMode ? '关闭' : '取消' }}</Button>
        <Button v-if="!isViewMode" @click="handleReset">重置</Button>
        <Button v-if="!isViewMode" type="primary" :loading="confirmLoading" @click="handleSubmit">保存</Button>
      </div>
    </template>

    <div class="face-library-form-container">
      <BasicForm @register="registerForm" />

      <a-alert
        v-if="!isViewMode"
        type="info"
        show-icon
        :closable="false"
        :message="formTipMessage"
        class="form-tip"
      />
    </div>
  </BasicDrawer>
</template>

<script lang="ts" setup>
import { computed, ref } from 'vue';
import { BasicDrawer, useDrawerInner } from '@/components/Drawer';
import { BasicForm, useForm } from '@/components/Form';
import { useMessage } from '@/hooks/web/useMessage';
import { Alert as AAlert } from 'ant-design-vue';
import { Button } from '@/components/Button'
import {
createFaceLibrary,
  updateFaceLibrary,
  type FaceLibrary,
} from '@/api/device/face_library';

defineOptions({ name: 'FaceLibraryModal' });

const { createMessage } = useMessage();
const emit = defineEmits(['success', 'register']);

const modalData = ref<{ type?: string; record?: FaceLibrary }>({});
const confirmLoading = ref(false);

const modalTitle = computed(() => {
  if (modalData.value.type === 'view') return '查看人脸库';
  if (modalData.value.type === 'edit') return '编辑人脸库';
  return '新建人脸库';
});

const isViewMode = computed(() => modalData.value.type === 'view');
const isEditMode = computed(() => modalData.value.type === 'edit');

const formTipMessage = computed(() => {
  if (isEditMode.value) {
    return '相似度阈值推荐 0.50 ~ 0.70，越高匹配越严格；停用后不参与算法比对';
  }
  return '库编号将在保存后由系统自动生成。相似度阈值推荐 0.50 ~ 0.70，越高匹配越严格；停用后不参与算法比对';
});

/** 业务标签仅按英文逗号拆分 */
function normalizeBusinessTags(tags: unknown): string[] {
  if (tags == null || tags === '') return [];
  const items = Array.isArray(tags) ? tags : [String(tags)];
  const result: string[] = [];
  for (const item of items) {
    const text = String(item).trim();
    if (!text) continue;
    for (const part of text.split(',')) {
      const tag = part.trim();
      if (tag) result.push(tag);
    }
  }
  return [...new Set(result)];
}

const [registerForm, { setFieldsValue, validate, resetFields, updateSchema }] = useForm({
  labelWidth: 110,
  baseColProps: { span: 24 },
  schemas: [
    {
      field: 'name',
      label: '库名称',
      component: 'Input',
      required: true,
      colProps: { span: 12 },
      componentProps: {
        placeholder: '如：员工人脸库、访客人脸库',
        maxlength: 50,
        showCount: true,
      },
    },
    {
      field: 'code',
      label: '库编号',
      component: 'Input',
      colProps: { span: 12 },
      ifShow: () => isEditMode.value || isViewMode.value,
      componentProps: {
        disabled: true,
        placeholder: '系统自动生成',
      },
      helpMessage: '创建时由系统自动生成，不可修改',
    },
    {
      field: 'business_tags',
      label: '业务标签',
      component: 'Select',
      helpMessage: '多个标签请用英文逗号分隔，输入后回车确认',
      componentProps: {
        mode: 'tags',
        placeholder: '如 access,attendance',
        tokenSeparators: [','],
        open: false,
      },
    },
    {
      field: 'similarity_threshold',
      label: '相似度阈值',
      component: 'Slider',
      required: true,
      colProps: { span: 16 },
      componentProps: {
        min: 0.3,
        max: 0.95,
        step: 0.01,
        marks: { 0.5: '0.50', 0.55: '推荐', 0.7: '0.70' },
        tooltip: { formatter: (v: number) => v?.toFixed(2) },
      },
      helpMessage: '拖动滑块调整，值越高越严格',
    },
    {
      field: 'is_enabled',
      label: '启用',
      component: 'Switch',
      colProps: { span: 8 },
      componentProps: {
        checkedChildren: '启用',
        unCheckedChildren: '停用',
      },
    },
    {
      field: 'description',
      label: '描述',
      component: 'InputTextArea',
      componentProps: {
        placeholder: '可选，说明此人脸库的用途',
        rows: 3,
        maxlength: 200,
        showCount: true,
      },
    },
  ],
  showActionButtonGroup: false,
});

function setFormDisabled(disabled: boolean) {
  updateSchema([
    { field: 'name', componentProps: { disabled } },
    { field: 'code', componentProps: { disabled: true } },
    { field: 'business_tags', componentProps: { disabled } },
    { field: 'similarity_threshold', componentProps: { disabled } },
    { field: 'is_enabled', componentProps: { disabled } },
    { field: 'description', componentProps: { disabled } },
  ]);
}

function fillForm(record: FaceLibrary) {
  setFieldsValue({
    name: record.name,
    code: record.code,
    business_tags: record.business_tags || [],
    description: record.description,
    similarity_threshold: record.similarity_threshold ?? 0.55,
    is_enabled: record.is_enabled !== false,
  });
}

const [register, { setDrawerProps, closeDrawer }] = useDrawerInner(async (data) => {
  resetFields();
  setDrawerProps({ confirmLoading: false });
  confirmLoading.value = false;
  modalData.value = data || {};

  if (data?.record) {
    fillForm(data.record);
    setFormDisabled(data.type === 'view');
  } else {
    setFormDisabled(false);
    setFieldsValue({ business_tags: [], similarity_threshold: 0.55, is_enabled: true });
  }
});

async function handleSubmit() {
  try {
    const values = await validate();
    const { code: _code, ...payload } = values;
    payload.business_tags = normalizeBusinessTags(payload.business_tags);
    confirmLoading.value = true;
    setDrawerProps({ confirmLoading: true });

    if (modalData.value.type === 'edit' && modalData.value.record) {
      await updateFaceLibrary(modalData.value.record.id, payload);
      createMessage.success('保存成功');
      closeDrawer();
      emit('success');
    } else {
      await createFaceLibrary(payload);
      createMessage.success('创建成功');
      closeDrawer();
      emit('success');
    }
  } catch (error: any) {
    const errorMsg = error?.message || error?.response?.data?.msg || '';
    createMessage.error(errorMsg || '提交失败');
  } finally {
    confirmLoading.value = false;
    setDrawerProps({ confirmLoading: false });
  }
}

function handleReset() {
  resetFields();
  if (modalData.value.record) {
    fillForm(modalData.value.record);
  } else {
    setFieldsValue({ business_tags: [], similarity_threshold: 0.55, is_enabled: true });
  }
}
</script>

<style lang="less" scoped>
.face-library-form-container {
  :deep(.ant-form-item) {
    margin-bottom: 20px;
  }

  .form-tip {
    margin-top: 8px;
    border-radius: 6px;
  }
}

.footer-buttons {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
}
</style>
