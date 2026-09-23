<template>
  <BasicDrawer
    v-bind="$attrs"
    @register="register"
    :title="drawerTitle"
    width="1200"
    placement="right"
    :showFooter="true"
    :showCancelBtn="false"
    :showOkBtn="false"
  >
    <template #footer>
      <div class="footer-buttons">
        <Button @click="closeDrawer">{{ isViewMode ? '关闭' : '取消' }}</Button>
        <Button v-if="!isViewMode" @click="handleReset">重置</Button>
        <Button v-if="!isViewMode" type="primary" :loading="confirmLoading" @click="handleSubmit">
          {{ isEditMode ? '保存修改' : '确认录入' }}
        </Button>
      </div>
    </template>

    <div class="plate-entry-drawer">
      <div v-if="libraryInfo" class="library-banner">
        <div class="banner-icon">
          <CarOutlined />
        </div>
        <div class="banner-body">
          <span class="banner-label">录入至</span>
          <span class="banner-name">{{ libraryInfo.name }}</span>
          <span v-if="libraryInfo.code" class="banner-meta">{{ libraryInfo.code }}</span>
        </div>
      </div>

      <div class="entry-body">
        <section class="form-section">
          <div class="section-head">
            <CameraOutlined class="section-icon" />
            <span class="section-title">车牌照片</span>
            <a-tag v-if="!isViewMode && !isEditMode" color="processing" class="required-tag">选填</a-tag>
          </div>
          <div class="photo-area">
            <a-upload
              :show-upload-list="false"
              :before-upload="beforeUpload"
              accept="image/jpeg,image/png,image/webp"
              :disabled="isViewMode"
              class="photo-uploader"
            >
              <div
                class="photo-zone"
                :class="{
                  'has-image': !!previewUrl,
                  'is-view': isViewMode,
                  'is-dragover': isDragover,
                }"
                @dragover.prevent="onDragOver"
                @dragleave.prevent="onDragLeave"
                @drop.prevent="onDrop"
              >
                <template v-if="previewUrl">
                  <img :src="previewUrl" alt="车牌照片" class="photo-preview" />
                  <div v-if="!isViewMode" class="photo-mask">
                    <span class="mask-action">
                      <CameraOutlined />
                      更换照片
                    </span>
                  </div>
                </template>
                <template v-else-if="!isViewMode">
                  <div class="photo-placeholder">
                    <div class="placeholder-icon">
                      <CarOutlined />
                    </div>
                    <p class="placeholder-title">上传车牌照片</p>
                    <p class="placeholder-desc">点击选择或拖拽至此处，上传后可自动识别车牌号</p>
                    <p class="placeholder-formats">JPG / PNG / WebP · 最大 5MB</p>
                  </div>
                </template>
                <template v-else>
                  <div class="photo-placeholder empty">
                    <CarOutlined class="empty-icon" />
                    <span>暂无照片</span>
                  </div>
                </template>
              </div>
            </a-upload>
            <div class="form-side">
              <BasicForm @register="registerForm" />
              <a-alert
                v-if="recognizing"
                type="info"
                show-icon
                message="正在识别车牌…"
                class="recognize-alert"
              />
            </div>
          </div>
        </section>
      </div>
    </div>
  </BasicDrawer>
</template>

<script lang="ts" setup>
import { computed, ref } from 'vue';
import { CameraOutlined, CarOutlined } from '@ant-design/icons-vue';
import { Alert as AAlert, Tag as ATag, Upload as AUpload } from 'ant-design-vue';
import type { UploadProps } from 'ant-design-vue';
import { BasicDrawer, useDrawerInner } from '@/components/Drawer';
import { BasicForm, useForm } from '@/components/Form';
import { useMessage } from '@/hooks/web/useMessage';
import { Button } from '@/components/Button'
import {
addPlateEntry,
  isPlateLibraryApiOk,
  parsePlateApiError,
  recognizePlateImage,
  resolvePlateImageDisplayUrl,
  updatePlateEntry,
  type PlateEntry,
  type PlateLibrary,
} from '@/api/device/plate_library';

defineOptions({ name: 'PlateEntryModal' });

const { createMessage } = useMessage();
const emit = defineEmits(['success', 'register']);

const modalData = ref<{ type?: string; library?: PlateLibrary; record?: PlateEntry }>({});
const confirmLoading = ref(false);
const uploadFile = ref<File | null>(null);
const previewUrl = ref('');
const isDragover = ref(false);
const recognizing = ref(false);

const libraryInfo = computed(() => modalData.value.library ?? null);

const drawerTitle = computed(() => {
  if (modalData.value.type === 'view') return '查看车牌';
  if (modalData.value.type === 'edit') return '编辑车牌';
  return '录入车牌';
});

const isViewMode = computed(() => modalData.value.type === 'view');
const isEditMode = computed(() => modalData.value.type === 'edit');

const [registerForm, { setFieldsValue, validate, resetFields, updateSchema }] = useForm({
  labelWidth: 80,
  baseColProps: { span: 24 },
  schemas: [
    {
      field: 'plate_no',
      label: '车牌号',
      component: 'Input',
      required: true,
      colProps: { span: 12 },
      componentProps: {
        placeholder: '如：京A12345',
        maxlength: 12,
        style: { textTransform: 'uppercase' },
      },
    },
    {
      field: 'plate_color',
      label: '颜色',
      component: 'Input',
      colProps: { span: 12 },
      componentProps: { placeholder: '如：蓝牌、绿牌（可选）', maxlength: 20 },
    },
    {
      field: 'owner_name',
      label: '车主',
      component: 'Input',
      colProps: { span: 12 },
      componentProps: { placeholder: '车主姓名（可选）', maxlength: 50 },
    },
    {
      field: 'owner_phone',
      label: '电话',
      component: 'Input',
      colProps: { span: 12 },
      componentProps: { placeholder: '联系电话（可选）', maxlength: 20 },
    },
    {
      field: 'is_enabled',
      label: '状态',
      component: 'Switch',
      colProps: { span: 8 },
      componentProps: {
        checkedChildren: '启用',
        unCheckedChildren: '停用',
      },
      helpMessage: '停用后该车牌不参与库匹配',
    },
    {
      field: 'remark',
      label: '备注',
      component: 'InputTextArea',
      componentProps: {
        placeholder: '补充说明（可选）',
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
    { field: 'plate_no', componentProps: { disabled } },
    { field: 'plate_color', componentProps: { disabled } },
    { field: 'owner_name', componentProps: { disabled } },
    { field: 'owner_phone', componentProps: { disabled } },
    { field: 'remark', componentProps: { disabled } },
    { field: 'is_enabled', componentProps: { disabled } },
  ]);
}

function revokePreview() {
  if (previewUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(previewUrl.value);
  }
  previewUrl.value = '';
  uploadFile.value = null;
}

function setExistingImage(url?: string) {
  revokePreview();
  const resolved = resolvePlateImageDisplayUrl(url);
  if (resolved) previewUrl.value = resolved;
}

async function tryRecognizePlate(file: File) {
  recognizing.value = true;
  try {
    const fd = new FormData();
    fd.append('file', file);
    const res = await recognizePlateImage(fd);
    const list = (res as { data?: Array<{ plate_no?: string; plate_color?: string }> })?.data;
    const first = Array.isArray(list) ? list[0] : null;
    if (first?.plate_no) {
      const values: Record<string, unknown> = { plate_no: first.plate_no };
      if (first.plate_color) values.plate_color = first.plate_color;
      setFieldsValue(values);
      createMessage.success('已识别车牌号，请核对后保存');
    }
  } catch {
    /* 识别失败不影响手工录入 */
  } finally {
    recognizing.value = false;
  }
}

function acceptFile(file: File) {
  if (!file.type.startsWith('image/')) {
    createMessage.warning('只能上传图片文件');
    return false;
  }
  if (file.size / 1024 / 1024 >= 5) {
    createMessage.warning('图片大小不能超过 5MB');
    return false;
  }
  revokePreview();
  uploadFile.value = file;
  previewUrl.value = URL.createObjectURL(file);
  if (!isEditMode.value) {
    tryRecognizePlate(file);
  }
  return true;
}

const beforeUpload: UploadProps['beforeUpload'] = (file) => {
  acceptFile(file as File);
  return false;
};

function onDragOver() {
  if (!isViewMode.value) isDragover.value = true;
}

function onDragLeave() {
  isDragover.value = false;
}

function onDrop(e: DragEvent) {
  isDragover.value = false;
  if (isViewMode.value) return;
  const file = Array.from(e.dataTransfer?.files || []).find((f) => f.type.startsWith('image/'));
  if (file) acceptFile(file);
}

const [register, { setDrawerProps, closeDrawer }] = useDrawerInner(async (data) => {
  resetFields();
  revokePreview();
  isDragover.value = false;
  setDrawerProps({ confirmLoading: false });
  confirmLoading.value = false;
  modalData.value = data || {};

  if (data?.record) {
    setFieldsValue({
      plate_no: data.record.plate_no,
      plate_color: data.record.plate_color,
      owner_name: data.record.owner_name,
      owner_phone: data.record.owner_phone,
      remark: data.record.remark,
      is_enabled: data.record.is_enabled !== false,
    });
    setExistingImage(data.record.image_url);
    setFormDisabled(data.type === 'view');
  } else {
    setFieldsValue({ is_enabled: true });
    setFormDisabled(false);
  }
});

async function handleSubmit() {
  const libraryId = modalData.value.library?.id;
  if (!libraryId) return;

  try {
    const values = await validate();
    const plateNo = String(values.plate_no || '').trim();
    if (!plateNo) {
      createMessage.warning('请输入车牌号');
      return;
    }

    confirmLoading.value = true;
    setDrawerProps({ confirmLoading: true });

    const fd = new FormData();
    fd.append('plate_no', plateNo);
    if (values.plate_color) fd.append('plate_color', String(values.plate_color).trim());
    if (values.owner_name) fd.append('owner_name', String(values.owner_name).trim());
    if (values.owner_phone) fd.append('owner_phone', String(values.owner_phone).trim());
    if (values.remark) fd.append('remark', String(values.remark).trim());
    fd.append('is_enabled', values.is_enabled ? 'true' : 'false');
    if (uploadFile.value) fd.append('file', uploadFile.value);

    if (isEditMode.value && modalData.value.record) {
      const response = await updatePlateEntry(modalData.value.record.id, fd);
      if (isPlateLibraryApiOk(response) || (response as PlateEntry)?.id) {
        createMessage.success('保存成功');
        closeDrawer();
        emit('success');
      } else {
        createMessage.error(parsePlateApiError(response, '保存失败'));
      }
    } else {
      const response = await addPlateEntry(libraryId, fd);
      if (isPlateLibraryApiOk(response) || (response as PlateEntry)?.id) {
        createMessage.success('录入成功');
        closeDrawer();
        emit('success');
      } else {
        createMessage.error(parsePlateApiError(response, '录入失败'));
      }
    }
  } catch (error: unknown) {
    createMessage.error(parsePlateApiError(error, '提交失败'));
  } finally {
    confirmLoading.value = false;
    setDrawerProps({ confirmLoading: false });
  }
}

function handleReset() {
  resetFields();
  if (modalData.value.record) {
    setFieldsValue({
      plate_no: modalData.value.record.plate_no,
      plate_color: modalData.value.record.plate_color,
      owner_name: modalData.value.record.owner_name,
      owner_phone: modalData.value.record.owner_phone,
      remark: modalData.value.record.remark,
      is_enabled: modalData.value.record.is_enabled !== false,
    });
    setExistingImage(modalData.value.record.image_url);
  } else {
    revokePreview();
    setFieldsValue({ is_enabled: true });
  }
}
</script>

<style lang="less" scoped>
.plate-entry-drawer {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.library-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #f0f5ff 0%, #fafbff 100%);
  border: 1px solid #d6e4ff;
  border-radius: 8px;

  .banner-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    border-radius: 8px;
    background: #266cfb;
    color: #fff;
    font-size: 18px;
    flex-shrink: 0;
  }

  .banner-body {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
    min-width: 0;
  }

  .banner-label {
    font-size: 13px;
    color: rgba(0, 0, 0, 0.45);
  }

  .banner-name {
    font-size: 15px;
    font-weight: 600;
    color: rgba(0, 0, 0, 0.85);
  }

  .banner-meta {
    font-size: 12px;
    color: rgba(0, 0, 0, 0.45);
    padding: 2px 8px;
    background: rgba(255, 255, 255, 0.7);
    border-radius: 4px;
    border: 1px solid #e8e8e8;
  }
}

.entry-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-section {
  background: #fff;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  overflow: hidden;

  .section-head {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 16px;
    background: #fafafa;
    border-bottom: 1px solid #f0f0f0;

    .section-icon {
      font-size: 15px;
      color: #266cfb;
    }

    .section-title {
      font-size: 14px;
      font-weight: 600;
      color: rgba(0, 0, 0, 0.85);
    }

    .required-tag {
      margin-left: auto;
      font-size: 12px;
    }
  }
}

.photo-area {
  display: flex;
  gap: 24px;
  padding: 20px;

  @media (max-width: 768px) {
    flex-direction: column;
  }
}

.photo-uploader {
  flex-shrink: 0;

  :deep(.ant-upload) {
    display: block;
  }
}

.photo-zone {
  position: relative;
  width: 280px;
  height: 160px;
  border: 2px dashed #d9d9d9;
  border-radius: 10px;
  overflow: hidden;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s, box-shadow 0.2s;
  background: #fafafa;

  &:hover:not(.is-view) {
    border-color: #266cfb;
    background: #f0f5ff;
  }

  &.is-dragover:not(.is-view) {
    border-color: #266cfb;
    background: #e6f0ff;
    box-shadow: 0 0 0 3px rgba(38, 108, 251, 0.12);
  }

  &.has-image {
    border-style: solid;
    border-color: #e8e8e8;

    &:hover:not(.is-view) .photo-mask {
      opacity: 1;
    }
  }

  &.is-view {
    cursor: default;
  }

  .photo-preview {
    width: 100%;
    height: 100%;
    object-fit: contain;
    display: block;
    background: #f5f5f5;
  }

  .photo-mask {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(0, 0, 0, 0.45);
    opacity: 0;
    transition: opacity 0.2s;

    .mask-action {
      display: flex;
      align-items: center;
      gap: 6px;
      color: #fff;
      font-size: 14px;
      padding: 8px 16px;
      border: 1px solid rgba(255, 255, 255, 0.6);
      border-radius: 6px;
    }
  }

  .photo-placeholder {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    padding: 12px;
    text-align: center;

    .placeholder-icon {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 48px;
      height: 48px;
      border-radius: 50%;
      background: #e6f0ff;
      color: #266cfb;
      font-size: 22px;
      margin-bottom: 8px;
    }

    .placeholder-title {
      margin: 0 0 4px;
      font-size: 14px;
      font-weight: 600;
      color: rgba(0, 0, 0, 0.85);
    }

    .placeholder-desc,
    .placeholder-formats {
      margin: 0;
      font-size: 12px;
      color: rgba(0, 0, 0, 0.45);
      line-height: 1.5;
    }

    &.empty {
      color: rgba(0, 0, 0, 0.35);

      .empty-icon {
        font-size: 32px;
        margin-bottom: 8px;
      }
    }
  }
}

.form-side {
  flex: 1;
  min-width: 280px;
}

.recognize-alert {
  margin-top: 12px;
}

.footer-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
