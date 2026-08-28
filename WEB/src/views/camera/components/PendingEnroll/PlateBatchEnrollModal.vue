<template>
  <BasicModal
    v-bind="$attrs"
    @register="register"
    title="批量入库到车牌库"
    :width="920"
    :canFullscreen="false"
    :showOkBtn="false"
    :showCancelBtn="false"
    destroy-on-close
  >
    <div class="plate-batch">
      <Alert
        type="info"
        show-icon
        class="plate-batch__tip"
        message="已选车牌将按 AI 标注框提取区域图并录入目标库；车牌号已按识别结果预填，可在下方表格中逐条修正后再入库。"
      />
      <div class="plate-batch__form">
        <Form layout="inline">
          <FormItem label="目标车牌库" required>
            <Select
              v-model:value="form.libraryId"
              style="width: 260px"
              placeholder="请选择车牌库"
              :options="libraryOptions"
              :loading="libraryLoading"
              show-search
              option-filter-prop="label"
            />
          </FormItem>
          <FormItem label="统一车主">
            <Input
              v-model:value="form.ownerName"
              style="width: 140px"
              placeholder="选填，应用到全部"
              :maxlength="50"
              allow-clear
            />
          </FormItem>
          <FormItem label="联系电话">
            <Input
              v-model:value="form.ownerPhone"
              style="width: 150px"
              placeholder="选填，应用到全部"
              :maxlength="20"
              allow-clear
            />
          </FormItem>
        </Form>
      </div>

      <div class="plate-batch__table-wrap">
        <div class="plate-batch__table-header">
          <span>已选 {{ rows.length }} 条车牌</span>
        </div>
        <div class="plate-batch__table">
          <div class="plate-row plate-row--head">
            <span class="plate-row__img">图片</span>
            <span class="plate-row__no">车牌号</span>
            <span class="plate-row__color">颜色</span>
            <span class="plate-row__device">设备 / 时间</span>
            <span class="plate-row__op"></span>
          </div>
          <div v-for="row in rows" :key="row.id" class="plate-row">
            <span class="plate-row__img">
              <img :src="resolvePlateImageDisplayUrl(row.crop_image_url) || defaultPlate" alt="车牌" @error="onImgError" />
            </span>
            <span class="plate-row__no">
              <Input
                v-model:value="row.plateNo"
                placeholder="车牌号"
                :maxlength="10"
                allow-clear
                @input="row.plateNo = row.plateNo.toUpperCase()"
              />
            </span>
            <span class="plate-row__color">
              <Select
                v-model:value="row.plateColor"
                style="width: 100%"
                placeholder="颜色"
                :options="colorOptions"
                allow-clear
              />
            </span>
            <span class="plate-row__device">
              <span class="plate-row__device-name" :title="row.device_name || row.device_id">
                {{ row.device_name || row.device_id }}
              </span>
              <span class="plate-row__time">{{ formatTime(row.created_at) }}</span>
            </span>
            <span class="plate-row__op" title="移除" @click="removeRow(row.id)">
              <CloseOutlined />
            </span>
          </div>
          <Empty
            v-if="!rows.length"
            class="plate-batch__empty"
            description="已全部移除"
            :image="Empty.PRESENTED_IMAGE_SIMPLE"
          />
        </div>
      </div>
    </div>

    <template #footer>
      <Button @click="closeModal">取消</Button>
      <Button type="primary" :loading="submitting" :disabled="!canSubmit" @click="handleSubmit">
        确认入库（{{ validCount }}/{{ rows.length }}）
      </Button>
    </template>
  </BasicModal>
</template>

<script lang="ts" setup>
/**
 * 车牌批量入库：目标库统一选择，逐条可修正 OCR 车牌号与颜色后一次性入库。
 */
import { computed, ref } from 'vue';
import { CloseOutlined } from '@ant-design/icons-vue';
import { Alert, Empty, Form as AForm, Input as AInput, Select as ASelect } from 'ant-design-vue';
import { BasicModal, useModalInner } from '@/components/Modal';
import { Button } from '@/components/Button';
import { useMessage } from '@/hooks/web/useMessage';
import {
  listPlateLibraries,
  resolvePlateImageDisplayUrl,
  type PlateLibrary,
} from '@/api/device/plate_library';
import {
  batchEnrollPendingRecords,
  type PendingEnrollRecord,
} from '@/api/device/pending_enroll';
import DEFAULT_PLATE_IMAGE from '@/assets/images/video/snap-task.png';

const Select = ASelect;
const Form = AForm;
const FormItem = AForm.Item;
const Input = AInput;

const defaultPlate = DEFAULT_PLATE_IMAGE;

defineOptions({ name: 'PlateBatchEnrollModal' });

const { createMessage } = useMessage();

const emit = defineEmits<{
  (e: 'success'): void;
}>();

const colorOptions = ['蓝', '黄', '绿', '渐变绿', '黄绿', '白', '黑'].map((c) => ({ label: c, value: c }));

interface EditRow {
  id: number;
  plateNo: string;
  plateColor: string | undefined;
  crop_image_url: string | null;
  device_id: string;
  device_name?: string;
  created_at?: string;
}

const rows = ref<EditRow[]>([]);
const submitting = ref(false);
const libraryOptions = ref<Array<{ label: string; value: number }>>([]);
const libraryLoading = ref(false);

const form = ref({
  libraryId: undefined as number | undefined,
  ownerName: '',
  ownerPhone: '',
});

const [register, { closeModal }] = useModalInner(async (data) => {
  rows.value = (((data?.records as PendingEnrollRecord[]) || []) as PendingEnrollRecord[])
    .filter((r) => r.enroll_status === 'pending')
    .map((r) => ({
      id: r.id,
      plateNo: r.plate_no || '',
      plateColor: r.plate_color || undefined,
      crop_image_url: r.crop_image_url ?? null,
      device_id: r.device_id,
      device_name: r.device_name,
      created_at: r.created_at,
    }));
  form.value = { libraryId: undefined, ownerName: '', ownerPhone: '' };
  void loadLibraries();
});

const validCount = computed(() => rows.value.filter((r) => r.plateNo.trim()).length);

const canSubmit = computed(() => !!form.value.libraryId && validCount.value > 0);

function onImgError(e: Event) {
  const img = e.target as HTMLImageElement;
  if (img && img.src !== defaultPlate) img.src = defaultPlate;
}

function formatTime(value?: string) {
  if (!value) return '—';
  return String(value).replace('T', ' ').slice(5, 16);
}

function removeRow(id: number) {
  rows.value = rows.value.filter((r) => r.id !== id);
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

async function handleSubmit() {
  if (!canSubmit.value) return;
  const items = rows.value
    .filter((r) => r.plateNo.trim())
    .map((r) => ({
      record_id: r.id,
      library_id: form.value.libraryId!,
      plate_no: r.plateNo.trim().toUpperCase(),
      plate_color: r.plateColor || undefined,
      owner_name: form.value.ownerName.trim() || undefined,
      owner_phone: form.value.ownerPhone.trim() || undefined,
    }));
  submitting.value = true;
  try {
    const res = await batchEnrollPendingRecords('plate', items);
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
.plate-batch {
  display: flex;
  flex-direction: column;
  gap: 14px;

  &__tip {
    margin: 0;
  }

  &__form {
    padding: 2px 0;
  }

  &__table-wrap {
    border: 1px solid #f0f0f0;
    border-radius: 8px;
    overflow: hidden;
  }

  &__table-header {
    padding: 8px 14px;
    font-size: 13px;
    font-weight: 500;
    color: rgba(0, 0, 0, 0.65);
    background: #fafafa;
    border-bottom: 1px solid #f0f0f0;
  }

  &__table {
    max-height: 340px;
    overflow-y: auto;
  }

  &__empty {
    margin: 12px 0;
  }
}

.plate-row {
  display: grid;
  grid-template-columns: 96px minmax(150px, 1fr) 110px minmax(140px, 1fr) 32px;
  gap: 12px;
  align-items: center;
  padding: 8px 14px;
  border-bottom: 1px solid #f5f5f5;

  &:last-child {
    border-bottom: none;
  }

  &--head {
    padding: 6px 14px;
    font-size: 12px;
    color: rgba(0, 0, 0, 0.45);
    background: #fafafa;
    border-bottom: 1px solid #f0f0f0;
  }

  &__img img {
    display: block;
    width: 96px;
    height: 32px;
    object-fit: cover;
    background: #fff;
    border: 1px solid #f0f0f0;
    border-radius: 4px;
  }

  &__device {
    display: flex;
    flex-direction: column;
    gap: 2px;
    min-width: 0;
  }

  &__device-name,
  &__time {
    font-size: 12px;
    color: rgba(0, 0, 0, 0.45);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  &__op {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    color: rgba(0, 0, 0, 0.45);
    border-radius: 50%;
    cursor: pointer;
    transition: all 0.2s;

    &:hover {
      color: #fff;
      background: #ff4d4f;
    }
  }
}
</style>
