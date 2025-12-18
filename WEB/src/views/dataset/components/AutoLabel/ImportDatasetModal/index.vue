<template>
  <BasicModal
    @register="register"
    width="600px"
    @cancel="handleCancel"
    :canFullscreen="false"
    :showOkBtn="false"
    :showCancelBtn="false"
  >
    <template #title>
      <span class="modal-title-with-icon">
        <Icon icon="ant-design:upload-outlined" class="title-icon" />
        添加数据集
      </span>
    </template>
    <div class="modal-content">
      <Tabs v-model:activeKey="tabActive" class="import-tabs">
        <TabPane key="image" tab="图片文件夹">
          <div class="upload-section">
            <div class="upload-area" @click="triggerImageFolderUpload" @drop.prevent="handleImageFolderDrop" @dragover.prevent>
              <div class="upload-content">
                <Icon icon="ant-design:folder-outlined" class="upload-icon" />
                <p class="upload-text">拖拽图片文件到此处或点击选择文件夹</p>
              </div>
            </div>
            <input
              ref="imageFolderInput"
              type="file"
              multiple
              accept="image/*"
              style="display: none"
              @change="handleImageFolderSelect"
            />
            <Button type="primary" block @click="triggerImageFolderUpload" class="upload-btn">
              选择图片文件
            </Button>
            <div v-if="selectedImageFiles.length > 0" class="selected-files">
              已选择 {{ selectedImageFiles.length }} 个文件
            </div>
          </div>
        </TabPane>
        
        <TabPane key="video" tab="视频文件">
          <div class="upload-section">
            <div class="upload-area" @click="triggerVideoUpload" @drop.prevent="handleVideoDrop" @dragover.prevent>
              <div class="upload-content">
                <Icon icon="ant-design:video-camera-outlined" class="upload-icon" />
                <p class="upload-text">拖拽视频文件到此处或点击选择视频</p>
              </div>
            </div>
            <input
              ref="videoInput"
              type="file"
              accept="video/*"
              style="display: none"
              @change="handleVideoSelect"
            />
            <Button type="primary" block @click="triggerVideoUpload" class="upload-btn">
              选择视频文件
            </Button>
            <div v-if="selectedVideoFile" class="selected-files">
              已选择: {{ selectedVideoFile.name }}
            </div>
            <div class="frame-interval-section">
              <span class="frame-interval-label">抽帧间隔(帧):</span>
              <InputNumber
                v-model:value="frameInterval"
                :min="1"
                :max="100"
                class="frame-interval-input"
              />
              <div class="form-hint">每隔指定帧数保存一帧作为样本</div>
            </div>
          </div>
        </TabPane>
        
        <TabPane key="labelme" tab="labelme数据集">
          <div class="upload-section">
            <div class="upload-area" @click="triggerLabelmeUpload" @drop.prevent="handleLabelmeDrop" @dragover.prevent>
              <div class="upload-content">
                <Icon icon="ant-design:folder-outlined" class="upload-icon" />
                <p class="upload-text">拖拽LabelMe数据集文件到此处或点击选择文件夹</p>
              </div>
            </div>
            <input
              ref="labelmeInput"
              type="file"
              webkitdirectory
              style="display: none"
              @change="handleLabelmeSelect"
            />
            <Button type="primary" block @click="triggerLabelmeUpload" class="upload-btn">
              选择labelme数据集
            </Button>
            <div class="upload-hint">
              <p>说明:请选择包含图片和对应JSON标注文件的labelme数据集文件夹</p>
            </div>
          </div>
        </TabPane>
      </Tabs>
    </div>
    <template #footer>
      <div class="modal-footer-custom">
        <Button type="primary" @click="handleConfirm" :loading="loading">
          <template #icon><Icon icon="ant-design:upload-outlined" /></template>
          <span v-if="tabActive === 'image'">上传图片到数据集</span>
          <span v-else-if="tabActive === 'video'">抽帧并添加到数据集</span>
          <span v-else>上传labelme数据集</span>
        </Button>
        <Button @click="handleCancel">取消</Button>
      </div>
    </template>
  </BasicModal>
</template>

<script lang="ts" setup>
import { ref } from 'vue';
import { BasicModal, useModal } from '@/components/Modal';
import { Icon } from '@/components/Icon';
import { Tabs, TabPane, InputNumber, Button } from 'ant-design-vue';
import { useMessage } from '@/hooks/web/useMessage';
import { extractFramesFromVideo, importLabelmeDataset } from '@/api/device/auto-label';
import { uploadDatasetImage } from '@/api/device/dataset';

defineOptions({ name: 'ImportDatasetModal' });

const { createMessage } = useMessage();

const emits = defineEmits(['success']);

const loading = ref(false);
const tabActive = ref('image');
const selectedImageFiles = ref<File[]>([]);
const selectedVideoFile = ref<File | null>(null);
const selectedLabelmeFiles = ref<File[]>([]);
const frameInterval = ref(3);
const imageFolderInput = ref<HTMLInputElement | null>(null);
const videoInput = ref<HTMLInputElement | null>(null);
const labelmeInput = ref<HTMLInputElement | null>(null);

const [register, { openModal, closeModal }] = useModal();

// 暴露方法供父组件调用
defineExpose({
  openModal,
  closeModal,
});

// 触发图片文件夹上传
const triggerImageFolderUpload = () => {
  imageFolderInput.value?.click();
};

const handleImageFolderSelect = (e: Event) => {
  const target = e.target as HTMLInputElement;
  if (target.files) {
    selectedImageFiles.value = Array.from(target.files);
  }
};

const handleImageFolderDrop = (e: DragEvent) => {
  if (e.dataTransfer?.files) {
    const files = Array.from(e.dataTransfer.files).filter(file => file.type.startsWith('image/'));
    selectedImageFiles.value = files;
  }
};

// 触发视频上传
const triggerVideoUpload = () => {
  videoInput.value?.click();
};

const handleVideoSelect = (e: Event) => {
  const target = e.target as HTMLInputElement;
  if (target.files && target.files.length > 0) {
    selectedVideoFile.value = target.files[0];
  }
};

const handleVideoDrop = (e: DragEvent) => {
  if (e.dataTransfer?.files && e.dataTransfer.files.length > 0) {
    const file = e.dataTransfer.files[0];
    if (file.type.startsWith('video/')) {
      selectedVideoFile.value = file;
    }
  }
};

// 触发labelme上传
const triggerLabelmeUpload = () => {
  labelmeInput.value?.click();
};

const handleLabelmeSelect = (e: Event) => {
  const target = e.target as HTMLInputElement;
  if (target.files) {
    selectedLabelmeFiles.value = Array.from(target.files);
  }
};

const handleLabelmeDrop = (e: DragEvent) => {
  if (e.dataTransfer?.files) {
    selectedLabelmeFiles.value = Array.from(e.dataTransfer.files);
  }
};

// 上传图片
const handleUploadImages = async (datasetId: number) => {
  if (selectedImageFiles.value.length === 0) {
    createMessage.warning('请选择图片文件');
    return;
  }

  try {
    loading.value = true;
    // 逐个上传图片文件
    for (const file of selectedImageFiles.value) {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('datasetId', datasetId.toString());
      formData.append('isZip', 'false');
      await uploadDatasetImage(formData);
    }
    
    createMessage.success(`上传成功，共上传 ${selectedImageFiles.value.length} 个文件`);
    closeModal();
    selectedImageFiles.value = [];
    emits('success');
  } catch (error) {
    console.error('上传失败:', error);
    createMessage.error('上传失败');
  } finally {
    loading.value = false;
  }
};

// 抽帧
const handleExtractFrames = async (datasetId: number) => {
  if (!selectedVideoFile.value) {
    createMessage.warning('请选择视频文件');
    return;
  }

  try {
    loading.value = true;
    const formData = new FormData();
    formData.append('file', selectedVideoFile.value);
    formData.append('frame_interval', frameInterval.value.toString());
    
    const res = await extractFramesFromVideo(datasetId, formData);
    
    if (res.code === 0) {
      createMessage.success(res.msg || `抽帧完成，共提取 ${res.data?.extracted_count || 0} 帧`);
      closeModal();
      selectedVideoFile.value = null;
      emits('success');
    } else {
      createMessage.error(res.msg || '抽帧失败');
    }
  } catch (error) {
    console.error('抽帧失败:', error);
    createMessage.error('抽帧失败');
  } finally {
    loading.value = false;
  }
};

// 上传labelme
const handleUploadLabelme = async (datasetId: number) => {
  if (selectedLabelmeFiles.value.length === 0) {
    createMessage.warning('请选择labelme数据集文件夹');
    return;
  }

  try {
    loading.value = true;
    const formData = new FormData();
    selectedLabelmeFiles.value.forEach(file => {
      formData.append('files', file);
    });
    
    const res = await importLabelmeDataset(datasetId, formData);
    
    if (res.code === 0) {
      createMessage.success(res.msg || `导入完成，共导入 ${res.data?.imported_count || 0} 个文件`);
      closeModal();
      selectedLabelmeFiles.value = [];
      emits('success');
    } else {
      createMessage.error(res.msg || '导入失败');
    }
  } catch (error) {
    console.error('导入失败:', error);
    createMessage.error('导入失败');
  } finally {
    loading.value = false;
  }
};

// 确认导入
const handleConfirm = async () => {
  const datasetId = (window as any).__currentDatasetId__;
  if (!datasetId) {
    createMessage.warning('请先选择数据集');
    return;
  }

  if (tabActive.value === 'image') {
    await handleUploadImages(datasetId);
  } else if (tabActive.value === 'video') {
    await handleExtractFrames(datasetId);
  } else if (tabActive.value === 'labelme') {
    await handleUploadLabelme(datasetId);
  }
};

// 取消
const handleCancel = () => {
  closeModal();
  selectedImageFiles.value = [];
  selectedVideoFile.value = null;
  selectedLabelmeFiles.value = [];
};
</script>

<style lang="less" scoped>
.modal-content {
  padding: 24px;
}

.modal-title-with-icon {
  display: flex;
  align-items: center;
  gap: 8px;
  
  .title-icon {
    font-size: 18px;
  }
}

.modal-footer-custom {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #e8e8e8;
}

.frame-interval-section {
  margin-top: 16px;
  
  .frame-interval-label {
    display: inline-block;
    margin-right: 8px;
    font-size: 14px;
    color: #333;
  }
  
  .frame-interval-input {
    width: 80px;
    margin-right: 8px;
  }
  
  .form-hint {
    margin-top: 8px;
    font-size: 12px;
    color: #999;
    line-height: 1.5;
  }
}

.upload-section {
  .upload-area {
    border: 2px dashed #d9d9d9;
    border-radius: 6px;
    padding: 40px 20px;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s;
    background: #fafafa;
    margin-bottom: 16px;
    
    &:hover {
      border-color: #1890ff;
      background: #f0f7ff;
    }
    
    .upload-content {
      .upload-icon {
        font-size: 48px;
        color: #999;
        margin-bottom: 16px;
        display: block;
      }
      
      .upload-text {
        color: #666;
        font-size: 14px;
        margin: 0;
      }
    }
  }
  
  .upload-btn {
    margin-top: 16px;
    height: 40px;
    font-size: 14px;
  }
  
  .selected-files {
    margin-top: 12px;
    padding: 8px 12px;
    background: #f5f5f5;
    border-radius: 4px;
    font-size: 14px;
    color: #666;
    text-align: center;
  }
  
  .upload-hint {
    margin-top: 16px;
    padding: 12px;
    background: #f5f5f5;
    border-radius: 4px;
    
    p {
      margin: 4px 0;
      font-size: 12px;
      color: #666;
      line-height: 1.5;
    }
  }
}

.import-tabs {
  :deep(.ant-tabs-tab) {
    padding: 12px 16px;
  }
  
  :deep(.ant-tabs-content-holder) {
    padding-top: 16px;
  }
  
  :deep(.ant-tabs-tab-active) {
    .ant-tabs-tab-btn {
      color: #1890ff;
      font-weight: 500;
    }
  }
  
  :deep(.ant-tabs-ink-bar) {
    background: #1890ff;
  }
}
</style>
