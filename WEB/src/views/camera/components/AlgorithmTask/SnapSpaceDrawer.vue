<template>
  <BasicDrawer
    v-bind="$attrs"
    @register="register"
    title="抓拍空间"
    width="800"
    :maskClosable="true"
  >
    <div class="snap-space-drawer-container">
      <Spin :spinning="loading">
        <Empty 
          v-if="!loading && cameraList.length === 0"
          description="暂无关联摄像头" 
        />
        <div v-else class="camera-list">
          <div 
            v-for="(camera, index) in cameraList" 
            :key="camera.device_id || index"
            class="camera-item"
          >
            <div class="camera-info">
              <div class="camera-name">
                <Icon icon="ant-design:video-camera-outlined" :size="18" color="#3B82F6" />
                <span class="name-text">{{ camera.device_name || camera.device_id }}</span>
              </div>
              <div class="camera-id" v-if="camera.device_name">
                {{ camera.device_id }}
              </div>
            </div>
            <div class="camera-actions">
              <a-button 
                type="primary"
                :loading="camera.loading"
                @click="handleViewSnapSpace(camera)"
                :disabled="!camera.space"
              >
                <template #icon>
                  <FolderOutlined />
                </template>
                {{ camera.space ? '打开抓拍空间' : '暂无抓拍空间' }}
              </a-button>
            </div>
          </div>
        </div>
      </Spin>
    </div>
    
    <!-- 抓拍图片查看模态框 -->
    <SnapImageModal @register="registerSnapImageModal"/>
  </BasicDrawer>
</template>

<script lang="ts" setup>
import { ref, computed } from 'vue';
import { BasicDrawer, useDrawerInner } from '@/components/Drawer';
import { useModal } from '@/components/Modal';
import { Button, Empty, Spin } from 'ant-design-vue';
import { FolderOutlined } from '@ant-design/icons-vue';
import { Icon } from '@/components/Icon';
import { useMessage } from '@/hooks/web/useMessage';
import { getSnapSpaceByDeviceId, type SnapSpace } from '@/api/device/snap';
import SnapImageModal from '@/views/camera/components/SnapSpace/SnapImageModal.vue';

defineOptions({ name: 'SnapSpaceDrawer' });

const { createMessage } = useMessage();
const [registerSnapImageModal, { openModal: openSnapImageModal }] = useModal();

const loading = ref(false);
const cameraList = ref<Array<{
  device_id: string;
  device_name?: string;
  space: SnapSpace | null;
  loading: boolean;
}>>([]);

// 加载摄像头列表和抓拍空间
const loadCameraList = async (deviceIds: string[], deviceNames: string[] = []) => {
  loading.value = true;
  cameraList.value = [];
  
  try {
    // 初始化摄像头列表
    const cameras = deviceIds.map((deviceId, index) => ({
      device_id: deviceId,
      device_name: deviceNames[index] || deviceId,
      space: null as SnapSpace | null,
      loading: false,
    }));
    
    cameraList.value = cameras;
    
    // 并行获取每个摄像头的抓拍空间
    const promises = deviceIds.map(async (deviceId, index) => {
      try {
        const response = await getSnapSpaceByDeviceId(deviceId);
        const space = response && typeof response === 'object' && 'code' in response 
          ? (response.code === 0 ? response.data : null)
          : (response as SnapSpace | null);
        
        // 更新对应摄像头的抓拍空间
        if (cameraList.value[index]) {
          cameraList.value[index].space = space;
        }
      } catch (error) {
        console.error(`获取设备 ${deviceId} 的抓拍空间失败:`, error);
        // 保持 space 为 null
      }
    });
    
    await Promise.all(promises);
  } catch (error) {
    console.error('加载摄像头列表失败:', error);
    createMessage.error('加载摄像头列表失败');
  } finally {
    loading.value = false;
  }
};

// 查看抓拍空间 - 直接打开对应空间，不需要再次选择
const handleViewSnapSpace = async (camera: typeof cameraList.value[0]) => {
  if (!camera.space) {
    createMessage.warning(`摄像头 ${camera.device_name || camera.device_id} 暂无抓拍空间`);
    return;
  }
  
  // 直接打开对应摄像头的抓拍空间，不需要再次选择
  camera.loading = true;
  try {
    openSnapImageModal(true, {
      space_id: camera.space.id,
      space_name: camera.space.space_name || camera.device_name || `设备 ${camera.device_id} 的抓拍空间`,
    });
  } catch (error) {
    console.error('打开抓拍空间失败:', error);
    createMessage.error('打开抓拍空间失败');
  } finally {
    camera.loading = false;
  }
};

// 注册抽屉
const [register] = useDrawerInner(async (data) => {
  if (data && data.deviceIds && Array.isArray(data.deviceIds)) {
    await loadCameraList(data.deviceIds, data.deviceNames || []);
  } else {
    cameraList.value = [];
  }
});
</script>

<style lang="less" scoped>
.snap-space-drawer-container {
  padding: 16px;
  min-height: 200px;
  
  .camera-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
    
    .camera-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 16px;
      background: #fafafa;
      border-radius: 8px;
      border: 1px solid #e8e8e8;
      transition: all 0.3s;
      
      &:hover {
        border-color: #3B82F6;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1);
      }
      
      .camera-info {
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 4px;
        
        .camera-name {
          display: flex;
          align-items: center;
          gap: 8px;
          
          .name-text {
            font-weight: 500;
            font-size: 15px;
            color: #262626;
          }
        }
        
        .camera-id {
          font-size: 12px;
          color: #8c8c8c;
          margin-left: 26px;
        }
      }
      
      .camera-actions {
        flex-shrink: 0;
        margin-left: 16px;
      }
    }
  }
}
</style>
