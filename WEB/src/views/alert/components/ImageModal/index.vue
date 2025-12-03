<template>
  <BasicModal
    v-bind="$attrs"
    @register="register"
    title="告警图片"
    :width="1000"
    :showOkBtn="false"
    :showCancelBtn="false"
    :maskClosable="true"
  >
    <div class="image-viewer-container">
      <Spin :spinning="loading" tip="加载中...">
        <div v-if="imageUrl" class="image-wrapper">
          <img
            :src="imageUrl"
            alt="告警图片"
            style="max-width: 100%; max-height: 70vh; display: block; margin: 0 auto"
            @error="handleImageError"
            @load="handleImageLoad"
          />
        </div>
        <div v-else-if="!loading" class="no-image">
          <a-empty description="图片加载失败" />
        </div>
      </Spin>
    </div>
  </BasicModal>
</template>

<script lang="ts" setup>
import { ref } from 'vue';
import { BasicModal, useModalInner } from '@/components/Modal';
import { Spin, Empty as AEmpty } from 'ant-design-vue';
import { useMessage } from '@/hooks/web/useMessage';
import { getAlertImage } from '@/api/device/calculate';

const { createMessage } = useMessage();
const loading = ref(false);
const imageUrl = ref<string>('');

const [register, { setModalProps, closeModal }] = useModalInner(async (data) => {
  loading.value = true;
  imageUrl.value = '';
  
  try {
    const { image_path } = data;
    if (!image_path) {
      createMessage.error('图片路径为空');
      return;
    }

    // 获取图片
    const blob = await getAlertImage(image_path);
    imageUrl.value = window.URL.createObjectURL(blob);
  } catch (error: any) {
    console.error('加载图片失败:', error);
    const errorMsg = error?.response?.data?.message || error?.message || '加载图片失败';
    createMessage.error(errorMsg);
  } finally {
    loading.value = false;
  }
});

const handleImageError = (event: Event) => {
  console.error('图片加载错误:', event);
  createMessage.error('图片加载失败');
  imageUrl.value = '';
};

const handleImageLoad = () => {
  // 图片加载成功
};
</script>

<style lang="less" scoped>
.image-viewer-container {
  padding: 20px;
  text-align: center;
  
  .image-wrapper {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 400px;
  }
  
  .no-image {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 400px;
  }
}
</style>

