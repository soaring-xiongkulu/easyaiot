<template>
  <BasicDrawer
    v-bind="$attrs"
    @register="register"
    title="车牌入库确认"
    width="760px"
    placement="right"
    :showFooter="false"
    destroy-on-close
  >
    <div class="plate-enroll">
      <Steps :current="step" size="small" class="plate-enroll__steps">
        <Step title="修正标注框" description="调整 AI 识别的车牌区域" />
        <Step title="确认车牌号" description="核对识别结果并录入" />
      </Steps>

      <!-- 第一步：标注修正 -->
      <div v-show="step === 0" class="plate-enroll__body">
        <template v-if="record">
          <div class="editor-panel">
            <BoundingBoxEditor
              v-if="editorSrc"
              ref="editorRef"
              :src="editorSrc"
              :rect="currentRect"
              :ai-rect="aiRect"
              editable
              accent-color="#fa8c16"
              :loading-tip="record.frame_available ? '整帧加载中…' : '车牌图加载中…'"
              @change="onRectChange"
              @loaded="onEditorLoaded"
            />
            <div v-else class="editor-panel__empty">
              <Empty description="图像已过期，无法修正标注框" :image="Empty.PRESENTED_IMAGE_SIMPLE" />
            </div>
          </div>
          <Alert
            v-if="record.frame_available === false"
            class="plate-enroll__tip"
            type="warning"
            show-icon
            message="整帧已过期清理，仅能在车牌小图上微调提取范围"
          />
          <div class="plate-enroll__meta">
            <span>设备：{{ record.device_name || record.device_id }}</span>
            <span>AI 识别：{{ record.plate_no || '未识别' }}</span>
            <span v-if="record.detect_conf">置信度：{{ (record.detect_conf * 100).toFixed(1) }}%</span>
            <span>时间：{{ formatTime(record.created_at) }}</span>
          </div>
        </template>
        <div class="plate-enroll__footer">
          <Button @click="closeDrawer">取消</Button>
          <Button type="primary" :disabled="!currentRect" @click="goConfirm">下一步：确认车牌号</Button>
        </div>
      </div>

      <!-- 第二步：确认车牌号 + 录入信息 -->
      <div v-show="step === 1" class="plate-enroll__body">
        <div class="confirm-grid">
          <div class="confirm-grid__preview">
            <div class="preview-title">车牌提取区域预览</div>
            <div class="preview-frame">
              <Spin :spinning="previewLoading" tip="正在按标注框提取…" size="small">
                <img v-if="previewUrl" :src="previewUrl" alt="提取区域" class="preview-img" />
                <div v-else class="preview-placeholder">
                  <CarOutlined style="font-size: 32px; color: #bbb" />
                </div>
              </Spin>
            </div>
            <a-tag color="orange" class="preview-tip">此区域图片将随车牌一并存入车牌库</a-tag>
          </div>
          <div class="confirm-grid__form">
            <Form layout="vertical">
              <FormItem label="车牌号码" required>
                <Input
                  v-model:value="form.plateNo"
                  class="plate-input"
                  placeholder="例如：京A12345"
                  :maxlength="10"
                  allow-clear
                  @input="form.plateNo = form.plateNo.toUpperCase()"
                />
                <div class="ocr-origin" v-if="record?.plate_no">
                  AI 识别结果：{{ record.plate_no }}
                  <a v-if="form.plateNo !== record.plate_no" @click="form.plateNo = record.plate_no">还原</a>
                </div>
              </FormItem>
              <FormItem label="车牌颜色">
                <Select
                  v-model:value="form.plateColor"
                  style="width: 100%"
                  placeholder="选择车牌颜色"
                  :options="colorOptions"
                  allow-clear
                />
              </FormItem>
              <FormItem label="目标车牌库" required>
                <Select
                  v-model:value="form.libraryId"
                  placeholder="请选择车牌库"
                  :options="libraryOptions"
                  :loading="libraryLoading"
                  show-search
                  option-filter-prop="label"
                />
              </FormItem>
              <div class="owner-grid">
                <FormItem label="车主姓名">
                  <Input v-model:value="form.ownerName" placeholder="选填" :maxlength="50" allow-clear />
                </FormItem>
                <FormItem label="车主电话">
                  <Input v-model:value="form.ownerPhone" placeholder="选填" :maxlength="20" allow-clear />
                </FormItem>
              </div>
              <FormItem label="备注">
                <Textarea v-model:value="form.remark" placeholder="选填" :rows="2" :maxlength="200" />
              </FormItem>
            </Form>
          </div>
        </div>
        <div class="plate-enroll__footer">
          <Button @click="backToPrevStep">上一步</Button>
          <Button @click="closeDrawer">取消</Button>
          <Button type="primary" :loading="enrolling" :disabled="!canSubmit" @click="handleEnroll">
            确认入库
          </Button>
        </div>
      </div>
    </div>
  </BasicDrawer>
</template>

<script lang="ts" setup>
/**
 * 车牌两步入库抽屉：① 修正 AI 标注框 → ② 确认 OCR 车牌号并录入车牌库。
 */
import { computed, ref } from 'vue';
import { CarOutlined } from '@ant-design/icons-vue';
import { Alert, Empty, Form as AForm, Input as AInput, Select as ASelect, Spin, Steps as ASteps, Tag as ATag } from 'ant-design-vue';
import { BasicDrawer, useDrawerInner } from '@/components/Drawer';
import { Button } from '@/components/Button';
import BoundingBoxEditor, { type EditorRect } from './BoundingBoxEditor.vue';
import { useMessage } from '@/hooks/web/useMessage';
import {
  resolvePlateImageDisplayUrl,
  listPlateLibraries,
  type PlateLibrary,
} from '@/api/device/plate_library';
import {
  bboxToRect,
  enrollPendingRecord,
  fetchExtractPreviewUrl,
  rectToBbox,
  type PendingEnrollRecord,
} from '@/api/device/pending_enroll';

const Select = ASelect;
const Form = AForm;
const FormItem = AForm.Item;
const Input = AInput;
const Textarea = AInput.TextArea;
const Steps = ASteps;
const Step = ASteps.Step;

defineOptions({ name: 'PlateEnrollDrawer' });

const { createMessage } = useMessage();

const emit = defineEmits<{
  (e: 'success', record: PendingEnrollRecord): void;
}>();

const colorOptions = ['蓝', '黄', '绿', '渐变绿', '黄绿', '白', '黑'].map((c) => ({ label: c, value: c }));

const record = ref<PendingEnrollRecord | null>(null);
const step = ref(0);
const editorRef = ref<InstanceType<typeof BoundingBoxEditor> | null>(null);
const currentRect = ref<EditorRect | null>(null);
const previewUrl = ref('');
const previewLoading = ref(false);
const enrolling = ref(false);

const libraryOptions = ref<Array<{ label: string; value: number }>>([]);
const libraryLoading = ref(false);

const form = ref({
  plateNo: '',
  plateColor: undefined as string | undefined,
  libraryId: undefined as number | undefined,
  ownerName: '',
  ownerPhone: '',
  remark: '',
});

const [register, { closeDrawer }] = useDrawerInner(async (data) => {
  step.value = 0;
  currentRect.value = null;
  previewUrl.value = '';
  const r = (data?.record as PendingEnrollRecord) ?? null;
  record.value = r;
  form.value = {
    plateNo: r?.plate_no || '',
    plateColor: r?.plate_color || undefined,
    libraryId: undefined,
    ownerName: '',
    ownerPhone: '',
    remark: '',
  };
  if (r?.frame_available && r.bbox) {
    currentRect.value = bboxToRect(r.bbox);
  }
  void loadLibraries();
});

const editorSrc = computed(() => {
  const r = record.value;
  if (!r) return '';
  if (r.frame_available && r.frame_image_url) return resolvePlateImageDisplayUrl(r.frame_image_url);
  return resolvePlateImageDisplayUrl(r.crop_image_url);
});

const aiRect = computed(() => {
  const r = record.value;
  if (!r || !r.frame_available) return null;
  return bboxToRect(r.bbox);
});

function onEditorLoaded(natural: { width: number; height: number }) {
  if (!currentRect.value) {
    const rect = { x: 0, y: 0, w: natural.width, h: natural.height };
    currentRect.value = rect;
    editorRef.value?.setRect(rect, false);
  }
}

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
    const res = await listPlateLibraries({ is_enabled: true });
    const list = (res?.data || []) as PlateLibrary[];
    libraryOptions.value = list.map((l) => ({ label: `${l.name}（${l.plate_count ?? 0} 条）`, value: l.id }));
    if (libraryOptions.value.length === 1) {
      form.value.libraryId = libraryOptions.value[0].value;
    }
  } catch (e: any) {
    createMessage.error(e?.message || '加载车牌库失败');
  } finally {
    libraryLoading.value = false;
  }
}

function backToPrevStep() {
  step.value = 0;
}

async function goConfirm() {
  const r = record.value;
  const rect = currentRect.value;
  if (!r || !rect) return;
  step.value = 1;
  previewLoading.value = true;
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value);
  previewUrl.value = '';
  try {
    previewUrl.value = await fetchExtractPreviewUrl('plate', r.id, rectToBbox(rect));
  } catch (e: any) {
    createMessage.error(e?.message || '提取预览失败');
  } finally {
    previewLoading.value = false;
  }
}

const canSubmit = computed(() => !!form.value.libraryId && !!form.value.plateNo.trim());

async function handleEnroll() {
  const r = record.value;
  const rect = currentRect.value;
  if (!r || !canSubmit.value) return;
  enrolling.value = true;
  try {
    await enrollPendingRecord('plate', {
      record_id: r.id,
      library_id: form.value.libraryId!,
      plate_no: form.value.plateNo.trim().toUpperCase(),
      plate_color: form.value.plateColor || undefined,
      owner_name: form.value.ownerName.trim() || undefined,
      owner_phone: form.value.ownerPhone.trim() || undefined,
      remark: form.value.remark.trim() || undefined,
      bbox: rect ? rectToBbox(rect) : undefined,
    });
    createMessage.success(`已入库车牌：${form.value.plateNo.trim().toUpperCase()}`);
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
.plate-enroll {
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
  grid-template-columns: 320px 1fr;
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
  height: 120px;
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
  width: 100%;
  height: 100%;
}

.preview-tip {
  align-self: flex-start;
}

.plate-input {
  :deep(input) {
    font-weight: 600;
    font-size: 16px;
    letter-spacing: 2px;
  }
}

.ocr-origin {
  margin-top: 4px;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);

  a {
    margin-left: 8px;
  }
}

.owner-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

@media (max-width: 720px) {
  .confirm-grid {
    grid-template-columns: 1fr;
  }
}
</style>
