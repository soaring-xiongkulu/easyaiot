<template>
  <BasicModal
    v-bind="$attrs"
    @register="register"
    title="批量入库到人脸库"
    :width="860"
    :canFullscreen="false"
    :showOkBtn="false"
    :showCancelBtn="false"
    destroy-on-close
  >
    <div class="face-batch">
      <Alert
        type="info"
        show-icon
        class="face-batch__tip"
        message="已选人脸将按 AI 标注框提取特征向量并录入目标库；需要修正标注框的请先在卡片上单独处理。"
      />
      <div class="face-batch__form">
        <Form layout="inline">
          <FormItem label="目标人脸库" required>
            <Select
              v-model:value="form.libraryId"
              style="width: 240px"
              placeholder="请选择人脸库"
              :options="libraryOptions"
              :loading="libraryLoading"
              show-search
              option-filter-prop="label"
              @change="onLibraryChange"
            />
          </FormItem>
          <FormItem label="归属">
            <RadioGroup v-model:value="form.mode">
              <Radio value="create">新建人员</Radio>
              <Radio value="attach">加入已有人员</Radio>
            </RadioGroup>
          </FormItem>
          <FormItem v-if="form.mode === 'create'" required>
            <Input
              v-model:value="form.personName"
              style="width: 180px"
              placeholder="人员姓名"
              :maxlength="50"
              allow-clear
            />
          </FormItem>
          <FormItem v-else>
            <Select
              v-model:value="form.personId"
              style="width: 200px"
              placeholder="选择已有人员"
              :options="personOptions"
              :loading="personLoading"
              show-search
              option-filter-prop="label"
            />
          </FormItem>
        </Form>
      </div>

      <div class="face-batch__list">
        <div class="face-batch__list-header">
          <span>已选 {{ records.length }} 张人脸</span>
        </div>
        <div class="face-batch__grid">
          <div v-for="item in records" :key="item.id" class="face-chip">
            <img
              :src="resolveFaceImageDisplayUrl(item.crop_image_url) || defaultFace"
              class="face-chip__img"
              alt="人脸"
              @error="onImgError"
            />
            <div class="face-chip__meta">
              <span class="face-chip__device" :title="item.device_name || item.device_id">
                {{ item.device_name || item.device_id }}
              </span>
              <span class="face-chip__time">{{ formatTime(item.created_at) }}</span>
            </div>
            <span class="face-chip__remove" title="移除" @click="removeRecord(item.id)">
              <CloseOutlined />
            </span>
          </div>
          <Empty
            v-if="!records.length"
            class="face-batch__empty"
            description="已全部移除"
            :image="Empty.PRESENTED_IMAGE_SIMPLE"
          />
        </div>
      </div>
    </div>

    <template #footer>
      <Button @click="closeModal">取消</Button>
      <Button type="primary" :loading="submitting" :disabled="!canSubmit" @click="handleSubmit">
        确认入库（{{ records.length }}）
      </Button>
    </template>
  </BasicModal>
</template>

<script lang="ts" setup>
/**
 * 人脸批量入库：多张未匹配人脸一次性录入同一目标库（新建或归属已有人员）。
 */
import { computed, ref } from 'vue';
import { CloseOutlined } from '@ant-design/icons-vue';
import { Alert, Empty, Form as AForm, Input as AInput, Radio as ARadio, Select as ASelect } from 'ant-design-vue';
import { BasicModal, useModalInner } from '@/components/Modal';
import { Button } from '@/components/Button';
import { useMessage } from '@/hooks/web/useMessage';
import {
  listFaceLibraries,
  listFacePersons,
  resolveFaceImageDisplayUrl,
  type FaceLibrary,
} from '@/api/device/face_library';
import {
  batchEnrollPendingRecords,
  type PendingEnrollRecord,
} from '@/api/device/pending_enroll';
import DEFAULT_FACE_IMAGE from '@/assets/images/video/snap-task.png';

const Select = ASelect;
const RadioGroup = ARadio.Group;
const Radio = ARadio;
const Form = AForm;
const FormItem = AForm.Item;
const Input = AInput;

defineOptions({ name: 'FaceBatchEnrollModal' });

const { createMessage } = useMessage();
const defaultFace = DEFAULT_FACE_IMAGE;

const emit = defineEmits<{
  (e: 'success'): void;
}>();

const records = ref<PendingEnrollRecord[]>([]);
const submitting = ref(false);
const libraryOptions = ref<Array<{ label: string; value: number }>>([]);
const libraryLoading = ref(false);
const personOptions = ref<Array<{ label: string; value: number }>>([]);
const personLoading = ref(false);

const form = ref({
  libraryId: undefined as number | undefined,
  mode: 'create' as 'create' | 'attach',
  personName: '',
  personId: undefined as number | undefined,
});

const [register, { closeModal }] = useModalInner(async (data) => {
  records.value = ((data?.records as PendingEnrollRecord[]) || []).filter(
    (r) => r.enroll_status === 'pending',
  );
  form.value = { libraryId: undefined, mode: 'create', personName: '', personId: undefined };
  personOptions.value = [];
  void loadLibraries();
});

function onImgError(e: Event) {
  const img = e.target as HTMLImageElement;
  if (img && img.src !== defaultFace) img.src = defaultFace;
}

function formatTime(value?: string) {
  if (!value) return '—';
  return String(value).replace('T', ' ').slice(5, 16);
}

function removeRecord(id: number) {
  records.value = records.value.filter((r) => r.id !== id);
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
    personOptions.value = (res?.data || []).map((p) => ({
      label: `${p.person_name}（${p.face_count} 张）`,
      value: p.id,
    }));
  } catch (e) {
    console.warn('加载人员失败', e);
  } finally {
    personLoading.value = false;
  }
}

const canSubmit = computed(() => {
  if (!records.value.length || !form.value.libraryId) return false;
  if (form.value.mode === 'create') return !!form.value.personName.trim();
  return !!form.value.personId;
});

async function handleSubmit() {
  if (!canSubmit.value) return;
  submitting.value = true;
  try {
    const items = records.value.map((r) => ({
      record_id: r.id,
      library_id: form.value.libraryId!,
      person_id: form.value.mode === 'attach' ? form.value.personId : undefined,
      person_name: form.value.mode === 'create' ? form.value.personName.trim() : undefined,
    }));
    const res = await batchEnrollPendingRecords('face', items);
    if (res.data?.failed_count) {
      createMessage.warning(res.msg || `成功 ${res.data.success_count} 条，失败 ${res.data.failed_count} 条`);
    } else {
      createMessage.success(res.msg || `已批量入库 ${res.data?.success_count ?? items.length} 条`);
    }
    emit('success');
    closeModal();
  } catch (e: any) {
    createMessage.error(e?.message || '批量入库失败');
  } finally {
    submitting.value = false;
  }
}
</script>

<style lang="less" scoped>
.face-batch {
  display: flex;
  flex-direction: column;
  gap: 14px;

  &__tip {
    margin: 0;
  }

  &__form {
    padding: 2px 0;
  }

  &__list {
    border: 1px solid #f0f0f0;
    border-radius: 8px;
    overflow: hidden;
  }

  &__list-header {
    padding: 8px 14px;
    font-size: 13px;
    font-weight: 500;
    color: rgba(0, 0, 0, 0.65);
    background: #fafafa;
    border-bottom: 1px solid #f0f0f0;
  }

  &__grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 12px;
    max-height: 300px;
    padding: 14px;
    overflow-y: auto;
  }

  &__empty {
    grid-column: 1 / -1;
    margin: 12px 0;
  }
}

.face-chip {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 8px;
  background: #fafafa;
  border: 1px solid #f0f0f0;
  border-radius: 8px;

  &__img {
    width: 100%;
    height: 88px;
    object-fit: cover;
    border-radius: 6px;
    background: #fff;
  }

  &__meta {
    display: flex;
    flex-direction: column;
    gap: 2px;
    min-width: 0;
  }

  &__device,
  &__time {
    font-size: 12px;
    color: rgba(0, 0, 0, 0.45);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  &__remove {
    position: absolute;
    top: -7px;
    right: -7px;
    z-index: 2;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 20px;
    height: 20px;
    color: #fff;
    background: rgba(0, 0, 0, 0.45);
    border-radius: 50%;
    cursor: pointer;
    font-size: 11px;
    transition: background 0.2s;

    &:hover {
      background: #ff4d4f;
    }
  }
}
</style>
