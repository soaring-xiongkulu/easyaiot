<template>
  <BasicDrawer
    v-bind="$attrs"
    @register="register"
    title="人脸入库确认"
    width="760px"
    placement="right"
    :showFooter="false"
    destroy-on-close
  >
    <div class="face-enroll">
      <Steps :current="step" size="small" class="face-enroll__steps">
        <Step title="修正标注框" description="调整 AI 识别的人脸区域" />
        <Step title="确认提取区域" description="核对特征提取范围并录入" />
      </Steps>

      <!-- 第一步：标注修正 -->
      <div v-show="step === 0" class="face-enroll__body">
        <template v-if="record">
          <div class="editor-panel">
            <BoundingBoxEditor
              v-if="editorSrc"
              ref="editorRef"
              :src="editorSrc"
              :rect="currentRect"
              :ai-rect="aiRect"
              editable
              accent-color="#266cfb"
              :loading-tip="record.frame_available ? '整帧加载中…' : '人脸图加载中…'"
              @change="onRectChange"
              @loaded="onEditorLoaded"
            />
            <div v-else class="editor-panel__empty">
              <Empty description="图像已过期，无法修正标注框" :image="Empty.PRESENTED_IMAGE_SIMPLE" />
            </div>
          </div>
          <Alert
            v-if="record.frame_available === false"
            class="face-enroll__tip"
            type="warning"
            show-icon
            message="整帧已过期清理，仅能在人脸小图上微调提取范围"
          />
          <div class="face-enroll__meta">
            <span>设备：{{ record.device_name || record.device_id }}</span>
            <span>任务：{{ record.task_name || '—' }}</span>
            <span>时间：{{ formatTime(record.created_at) }}</span>
          </div>
        </template>
        <div class="face-enroll__footer">
          <Button @click="closeDrawer">取消</Button>
          <Button type="primary" :disabled="!currentRect" @click="goConfirm">
            下一步：确认提取区域
          </Button>
        </div>
      </div>

      <!-- 第二步：确认提取区域 + 录入信息 -->
      <div v-show="step === 1" class="face-enroll__body">
        <div class="confirm-grid">
          <div class="confirm-grid__preview">
            <div class="preview-title">特征提取区域预览</div>
            <div class="preview-frame">
              <Spin :spinning="previewLoading" tip="正在按标注框提取…" size="small">
                <img
                  v-if="previewUrl"
                  :src="previewUrl"
                  alt="提取区域"
                  class="preview-img"
                />
                <div v-else class="preview-placeholder">
                  <UserOutlined style="font-size: 32px; color: #bbb" />
                </div>
              </Spin>
            </div>
            <a-tag color="blue" class="preview-tip">入库向量将按此区域提取</a-tag>
          </div>
          <div class="confirm-grid__form">
            <Form layout="vertical">
              <FormItem label="目标人脸库" required>
                <Select
                  v-model:value="form.libraryId"
                  placeholder="请选择人脸库"
                  :options="libraryOptions"
                  :loading="libraryLoading"
                  show-search
                  option-filter-prop="label"
                  @change="onLibraryChange"
                />
              </FormItem>
              <FormItem label="归属方式">
                <RadioGroup v-model:value="form.mode">
                  <Radio value="create">新建人员</Radio>
                  <Radio value="attach">加入已有人员</Radio>
                </RadioGroup>
              </FormItem>
              <FormItem v-if="form.mode === 'create'" label="人员姓名" required>
                <Input
                  v-model:value="form.personName"
                  placeholder="例如：张三"
                  :maxlength="50"
                  allow-clear
                />
              </FormItem>
              <FormItem v-else label="选择人员" required>
                <Select
                  v-model:value="form.personId"
                  placeholder="请选择已有人员"
                  :options="personOptions"
                  :loading="personLoading"
                  show-search
                  option-filter-prop="label"
                />
              </FormItem>
              <FormItem v-if="form.mode === 'create'" label="人员编号">
                <Input v-model:value="form.personCode" placeholder="选填，如工号" :maxlength="50" allow-clear />
              </FormItem>
              <FormItem label="备注">
                <Textarea v-model:value="form.remark" placeholder="选填" :rows="2" :maxlength="200" />
              </FormItem>
            </Form>
          </div>
        </div>
        <div class="face-enroll__footer">
          <Button @click="backToPrevStep">上一步</Button>
          <Button @click="closeDrawer">取消</Button>
          <Button
            type="primary"
            :loading="enrolling"
            :disabled="!canSubmit"
            @click="handleEnroll"
          >
            确认入库
          </Button>
        </div>
      </div>
    </div>
  </BasicDrawer>
</template>

<script lang="ts" setup>
/**
 * 人脸两步入库抽屉：① 修正 AI 标注框 → ② 确认特征提取区域并录入人脸库。
 */
import { computed, ref, unref } from 'vue';
import { UserOutlined } from '@ant-design/icons-vue';
import { Alert, Empty, Form as AForm, Input as AInput, Radio as ARadio, Select as ASelect, Spin, Steps as ASteps, Tag as ATag } from 'ant-design-vue';
import { BasicDrawer, useDrawerInner } from '@/components/Drawer';
import { Button } from '@/components/Button';
import BoundingBoxEditor, { type EditorRect } from './BoundingBoxEditor.vue';
import { useMessage } from '@/hooks/web/useMessage';
import { resolveFaceImageDisplayUrl, listFaceLibraries, listFacePersons, type FaceLibrary } from '@/api/device/face_library';
import {
  bboxToRect,
  enrollPendingRecord,
  fetchExtractPreviewUrl,
  rectToBbox,
  type PendingEnrollRecord,
} from '@/api/device/pending_enroll';

const Select = ASelect;
const RadioGroup = ARadio.Group;
const Radio = ARadio;
const Form = AForm;
const FormItem = AForm.Item;
const Input = AInput;
const Textarea = AInput.TextArea;
const Steps = ASteps;
const Step = ASteps.Step;

defineOptions({ name: 'FaceEnrollDrawer' });

const { createMessage } = useMessage();

const emit = defineEmits<{
  (e: 'success', record: PendingEnrollRecord): void;
}>();

const record = ref<PendingEnrollRecord | null>(null);
const step = ref(0);
const editorRef = ref<InstanceType<typeof BoundingBoxEditor> | null>(null);
const currentRect = ref<EditorRect | null>(null);
const previewUrl = ref('');
const previewLoading = ref(false);
const enrolling = ref(false);

const libraryOptions = ref<Array<{ label: string; value: number }>>([]);
const libraryLoading = ref(false);
const personOptions = ref<Array<{ label: string; value: number }>>([]);
const personLoading = ref(false);

const form = ref({
  libraryId: undefined as number | undefined,
  mode: 'create' as 'create' | 'attach',
  personName: '',
  personCode: '',
  personId: undefined as number | undefined,
  remark: '',
});

const [register, { closeDrawer }] = useDrawerInner(async (data) => {
  step.value = 0;
  currentRect.value = null;
  previewUrl.value = '';
  form.value = {
    libraryId: undefined,
    mode: 'create',
    personName: '',
    personCode: '',
    personId: undefined,
    remark: '',
  };
  record.value = (data?.record as PendingEnrollRecord) ?? null;
  void loadLibraries();
  const r = record.value;
  if (r?.frame_available && r.bbox) {
    currentRect.value = bboxToRect(r.bbox);
  }
});

const editorSrc = computed(() => {
  const r = record.value;
  if (!r) return '';
  if (r.frame_available && r.frame_image_url) return resolveFaceImageDisplayUrl(r.frame_image_url);
  return resolveFaceImageDisplayUrl(r.crop_image_url);
});

/** 无 AI 框（或整帧缺失导致框不可用）时，默认以整张图为提取区域 */
function onEditorLoaded(natural: { width: number; height: number }) {
  if (!currentRect.value) {
    const rect = { x: 0, y: 0, w: natural.width, h: natural.height };
    currentRect.value = rect;
    editorRef.value?.setRect(rect, false);
  }
}

const aiRect = computed(() => {
  const r = record.value;
  if (!r || !r.frame_available) return null;
  return bboxToRect(r.bbox);
});

function onRectChange(rect: EditorRect) {
  currentRect.value = rect;
}

function formatTime(value?: string) {
  if (!value) return '—';
  return String(value).replace('T', ' ').slice(0, 19);
}

async function loadLibraries() {
  libraryLoading.value = true;
  try {
    const res = await listFaceLibraries({ is_enabled: true });
    const list = (res?.data || []) as FaceLibrary[];
    libraryOptions.value = list.map((l) => ({ label: `${l.name}（${l.face_count ?? 0} 张）`, value: l.id }));
    if (libraryOptions.value.length === 1) {
      form.value.libraryId = libraryOptions.value[0].value;
      void onLibraryChange(form.value.libraryId);
    }
  } catch (e: any) {
    createMessage.error(e?.message || '加载人脸库失败');
  } finally {
    libraryLoading.value = false;
  }
}

async function onLibraryChange(libraryId: number) {
  personOptions.value = [];
  form.value.personId = undefined;
  if (form.value.mode !== 'attach' || !libraryId) return;
  personLoading.value = true;
  try {
    const res = await listFacePersons(libraryId, { page: 1, pageSize: 200 });
    const persons = res?.data || [];
    personOptions.value = persons.map((p) => ({
      label: `${p.person_name}（${p.face_count} 张）`,
      value: p.id,
    }));
  } catch (e: any) {
    console.warn('加载人员失败', e);
  } finally {
    personLoading.value = false;
  }
}

function backToPrevStep() {
  step.value = 0;
}

async function goConfirm() {
  const r = unref(record);
  const rect = unref(currentRect);
  if (!r || !rect) return;
  step.value = 1;
  previewLoading.value = true;
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value);
  previewUrl.value = '';
  try {
    previewUrl.value = await fetchExtractPreviewUrl('face', r.id, rectToBbox(rect));
  } catch (e: any) {
    createMessage.error(e?.message || '提取预览失败');
  } finally {
    previewLoading.value = false;
  }
}

const canSubmit = computed(() => {
  if (!form.value.libraryId) return false;
  if (form.value.mode === 'create') return !!form.value.personName.trim();
  return !!form.value.personId;
});

async function handleEnroll() {
  const r = unref(record);
  const rect = unref(currentRect);
  if (!r || !canSubmit.value) return;
  enrolling.value = true;
  try {
    await enrollPendingRecord('face', {
      record_id: r.id,
      library_id: form.value.libraryId!,
      bbox: rect ? rectToBbox(rect) : undefined,
      person_id: form.value.mode === 'attach' ? form.value.personId : undefined,
      person_name: form.value.mode === 'create' ? form.value.personName.trim() : undefined,
      person_code: form.value.mode === 'create' ? form.value.personCode.trim() || undefined : undefined,
      remark: form.value.remark.trim() || undefined,
    });
    createMessage.success(`已入库：${form.value.mode === 'create' ? form.value.personName : '所选人员'}`);
    emit('success', r);
    closeDrawer();
  } catch (e: any) {
    createMessage.error(e?.message || '入库失败');
  } finally {
    enrolling.value = false;
  }
}
</script>

<style lang="less" scoped>
.face-enroll {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 4px 4px 16px;

  &__steps {
    padding: 4px 8px 12px;
    border-bottom: 1px solid #f0f0f0;
  }

  &__body {
    display: flex;
    flex-direction: column;
    gap: 12px;
    min-height: 0;
  }

  &__tip {
    margin: 0;
  }

  &__meta {
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    font-size: 12px;
    color: rgba(0, 0, 0, 0.45);
  }

  &__footer {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    padding-top: 12px;
    border-top: 1px solid #f0f0f0;
  }
}

.editor-panel {
  height: 380px;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  overflow: hidden;

  &__empty {
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
  }
}

.confirm-grid {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 20px;
  align-items: start;

  &__preview {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
}

.preview-title {
  font-size: 13px;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.65);
}

.preview-frame {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 240px;
  background: #fafafa;
  border: 1px dashed #d9d9d9;
  border-radius: 8px;
  overflow: hidden;

  :deep(.ant-spin-nested-loading) {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
  }
}

.preview-img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.preview-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  width: 100%;
}

.preview-tip {
  align-self: flex-start;
}

@media (max-width: 720px) {
  .confirm-grid {
    grid-template-columns: 1fr;
  }
}
</style>
