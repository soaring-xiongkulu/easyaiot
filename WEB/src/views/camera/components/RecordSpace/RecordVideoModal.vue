<template>
  <BasicModal 
    v-bind="$attrs" 
    @register="register" 
    title="录像管理" 
    :width="1500"
    :showOkBtn="false"
    :showCancelBtn="false"
    :maskClosable="true"
  >
    <div class="record-video-container">
      <!-- 顶部操作栏 -->
      <div class="record-video-header">
        <div class="header-actions">
          <a-button type="primary" @click="handleSelectAll">
            {{ isAllSelected ? '取消全选' : '全选' }}
          </a-button>
          <a-button type="primary" @click="handleRefresh">
            刷新
          </a-button>
          <a-button 
            type="primary" 
            danger 
            :disabled="selectedRowKeys.length === 0"
            @click="handleBatchDelete"
          >
            批量删除 ({{ selectedRowKeys.length }})
          </a-button>
        </div>
      </div>

      <!-- 录像卡片列表 -->
      <div class="card-wrapper">
        <Spin :spinning="loading">
          <List
            :grid="{ gutter: 16, xs: 2, sm: 3, md: 4, lg: 5, xl: 6, xxl: 6 }"
            :data-source="videoList"
            :pagination="paginationProp"
          >
            <template #renderItem="{ item }">
              <ListItem class="video-card-item">
                <div 
                  class="video-card-box"
                  @click="handleVideoClick(item)"
                >
                  <!-- 选择框 -->
                  <div 
                    class="card-checkbox"
                    :class="{ 'checked': selectedRowKeys.includes(item.object_name) }"
                    @click.stop="handleSelectChange(item.object_name, !selectedRowKeys.includes(item.object_name))"
                  >
                    <span class="checkbox-inner"></span>
                  </div>
                  
                  <!-- 封面展示 -->
                  <div class="img-box">
                    <img
                      v-if="item.thumbnail_url"
                      :src="item.thumbnail_url"
                      :alt="item.filename"
                      class="card-image"
                    />
                    <div v-else class="no-thumbnail">
                      <span>无封面</span>
                    </div>
                    <!-- 播放图标 -->
                    <div class="play-icon" @click.stop="handlePlay(item)">
                      <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="24" cy="24" r="24" fill="rgba(0, 0, 0, 0.5)"/>
                        <path d="M18 14L34 24L18 34V14Z" fill="white"/>
                      </svg>
                    </div>
                  </div>
                  
                  <!-- 卡片内容 -->
                  <div class="card-content">
                    <!-- 信息标签 -->
                    <div class="card-info">
                      <div class="info-item">
                        <span class="info-label">大小：</span>
                        <span class="info-value">{{ formatSize(item.size) }}</span>
                      </div>
                      <div class="info-item" v-if="item.duration">
                        <span class="info-label">时长：</span>
                        <span class="info-value">{{ formatDuration(item.duration) }}</span>
                      </div>
                      <div class="info-item" v-if="item.last_modified">
                        <span class="info-label">时间：</span>
                        <span class="info-value">{{ formatTime(item.last_modified) }}</span>
                      </div>
                    </div>
                    
                    <!-- 操作按钮 -->
                    <div class="card-actions" @click.stop>
                      <a-button type="link" size="small" @click="handlePlay(item)">
                        播放
                      </a-button>
                      <a-button type="link" size="small" @click="handlePreview(item)">
                        预览
                      </a-button>
                      <a-button type="link" size="small" danger @click="handleDelete(item)">
                        删除
                      </a-button>
                    </div>
                  </div>
                </div>
              </ListItem>
            </template>
          </List>
        </Spin>
      </div>
    </div>
    
    <!-- 视频播放器弹框 -->
    <DialogPlayer @register="registerPlayerModal" />
  </BasicModal>
</template>

<script lang="ts" setup>
import { ref, computed } from 'vue';
import { List, Spin } from 'ant-design-vue';
import { BasicModal, useModalInner, useModal } from '@/components/Modal';
import { useMessage } from '@/hooks/web/useMessage';
import { getRecordVideoList, deleteRecordVideos, type RecordVideo } from '@/api/device/record';
import DialogPlayer from '@/components/VideoPlayer/DialogPlayer.vue';

defineOptions({ name: 'RecordVideoModal' });

const { createMessage } = useMessage();
const emit = defineEmits(['register']);

const ListItem = List.Item;

const modalData = ref<{ space_id?: number; space_name?: string }>({});
const videoList = ref<RecordVideo[]>([]);
const loading = ref(false);
const selectedRowKeys = ref<string[]>([]);
const previewVisible = ref(false);
const previewVideo = ref<RecordVideo | null>(null);

// 播放器弹框
const [registerPlayerModal, { openModal: openPlayerModal }] = useModal();

// 分页相关
const page = ref(1);
const pageSize = ref(20);
const total = ref(0);
const paginationProp = computed(() => {
  // 如果没有数据，不显示分页组件
  if (total.value === 0) {
    return false;
  }
  return {
    showSizeChanger: true,
    showQuickJumper: true,
    pageSize: pageSize.value,
    current: page.value,
    total: total.value,
    showTotal: (total: number) => `共 ${total} 个录像`,
    onChange: pageChange,
    onShowSizeChange: pageSizeChange,
  };
});

function pageChange(p: number, pz: number) {
  page.value = p;
  pageSize.value = pz;
  loadVideoList();
}

function pageSizeChange(_current: number, size: number) {
  pageSize.value = size;
  page.value = 1;
  loadVideoList();
}

const getVideoUrl = (record: RecordVideo) => {
  // 优先使用后台返回的 url 字段，如果没有则使用 object_name 构建
  if (record.url) {
    // 如果是完整URL（以http://或https://开头），直接返回
    if (record.url.startsWith('http://') || record.url.startsWith('https://')) {
      return record.url;
    }
    // 如果是相对路径（以/api/v1/buckets开头），添加前端启动地址前缀
    if (record.url.startsWith('/api/v1/buckets')) {
      return `${window.location.origin}${record.url}`;
    }
    // 其他情况直接返回
    return record.url;
  }
  if (!modalData.value.space_id) return '';
  return `/video/record/space/${modalData.value.space_id}/video/${record.object_name}`;
};

const formatSize = (bytes: number) => {
  if (!bytes) return '0 B';
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
  if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB';
};

const formatDuration = (seconds: number) => {
  if (!seconds) return '0秒';
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  
  if (hours > 0) {
    return `${hours}小时${minutes}分钟${secs}秒`;
  } else if (minutes > 0) {
    return `${minutes}分钟${secs}秒`;
  } else {
    return `${secs}秒`;
  }
};

const formatTime = (timeStr: string) => {
  if (!timeStr) return '';
  const date = new Date(timeStr);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
};

const loadVideoList = async () => {
  if (!modalData.value.space_id) return;
  
  loading.value = true;
  try {
    const response = await getRecordVideoList(modalData.value.space_id, {
      pageNo: page.value,
      pageSize: pageSize.value,
    });
    
    // 响应拦截器处理后的数据结构：{ code, data, msg, total }
    // 或者直接是数组（如果响应拦截器返回了 data.data）
    if (Array.isArray(response)) {
      // 如果直接返回数组
      videoList.value = response;
      total.value = response.length;
    } else if (response && typeof response === 'object') {
      // 如果返回对象
      if (response.code === 0) {
        // 成功响应
        if (Array.isArray(response.data)) {
          // data是数组
          videoList.value = response.data;
          total.value = response.total || response.data.length;
        } else if (response.data && Array.isArray(response.data.items)) {
          // data.items是数组（某些接口可能这样返回）
          videoList.value = response.data.items;
          total.value = response.total || response.data.total || response.data.items.length;
        } else {
          videoList.value = [];
          total.value = 0;
        }
      } else {
        // 错误响应
        createMessage.error(response.msg || '加载录像列表失败');
        videoList.value = [];
        total.value = 0;
      }
    } else {
      videoList.value = [];
      total.value = 0;
    }
  } catch (error) {
    console.error('加载录像列表失败', error);
    createMessage.error('加载录像列表失败');
    videoList.value = [];
    total.value = 0;
  } finally {
    loading.value = false;
  }
};

const handleRefresh = () => {
  selectedRowKeys.value = [];
  page.value = 1;
  loadVideoList();
};

// 全选状态计算
const isAllSelected = computed(() => {
  return videoList.value.length > 0 && selectedRowKeys.value.length === videoList.value.length;
});

// 全选/取消全选
const handleSelectAll = () => {
  if (isAllSelected.value) {
    // 取消全选
    selectedRowKeys.value = [];
  } else {
    // 全选当前页所有录像
    selectedRowKeys.value = videoList.value.map(item => item.object_name);
  }
};

// 点击录像切换勾选状态
const handleVideoClick = (item: RecordVideo) => {
  const key = item.object_name;
  if (selectedRowKeys.value.includes(key)) {
    selectedRowKeys.value = selectedRowKeys.value.filter(k => k !== key);
  } else {
    selectedRowKeys.value.push(key);
  }
};

const handleSelectChange = (key: string, checked: boolean) => {
  if (checked) {
    if (!selectedRowKeys.value.includes(key)) {
      selectedRowKeys.value.push(key);
    }
  } else {
    selectedRowKeys.value = selectedRowKeys.value.filter(k => k !== key);
  }
};

const handlePlay = (record: RecordVideo) => {
  const videoUrl = getVideoUrl(record);
  
  if (!videoUrl) {
    createMessage.warning('录像文件地址无效，无法播放');
    return;
  }
  
  // 使用 DialogPlayer 组件打开播放器
  openPlayerModal(true, {
    id: modalData.value.space_id || 0,
    http_stream: videoUrl,
  });
};

const handlePreview = (record: RecordVideo) => {
  previewVideo.value = record;
  previewVisible.value = true;
};

const handleDelete = async (record: RecordVideo) => {
  if (!modalData.value.space_id) return;
  
  try {
    await deleteRecordVideos(modalData.value.space_id, [record.object_name]);
    createMessage.success('删除成功');
    loadVideoList();
  } catch (error: any) {
    console.error('删除失败', error);
    const errorMsg = error?.response?.data?.msg || error?.message || '删除失败';
    createMessage.error(errorMsg);
  }
};

const handleBatchDelete = async () => {
  if (!modalData.value.space_id || selectedRowKeys.value.length === 0) return;
  
  try {
    await deleteRecordVideos(modalData.value.space_id, selectedRowKeys.value);
    createMessage.success(`成功删除 ${selectedRowKeys.value.length} 个录像`);
    selectedRowKeys.value = [];
    loadVideoList();
  } catch (error: any) {
    console.error('批量删除失败', error);
    const errorMsg = error?.response?.data?.msg || error?.message || '批量删除失败';
    createMessage.error(errorMsg);
  }
};

const [register, { setModalProps, closeModal }] = useModalInner(async (data) => {
  modalData.value = data || {};
  selectedRowKeys.value = [];
  page.value = 1;
  setModalProps({ confirmLoading: false });
  await loadVideoList();
});
</script>

<style lang="less" scoped>
.record-video-container {
  display: flex;
  flex-direction: column;
  height: 70vh;
  max-height: 700px;
  min-height: 550px;
  position: relative;
  overflow: hidden;
  
  .record-video-header {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    padding: 16px 0;
    margin-bottom: 16px;
    border-bottom: 1px solid #e8e8e8;
    flex-shrink: 0;

    .header-actions {
      display: flex;
      align-items: center;
      gap: 12px;
    }
  }

  .card-wrapper {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    overflow-x: hidden;
    padding-right: 8px;
    display: flex;
    flex-direction: column;
    
    // 自定义滚动条样式
    &::-webkit-scrollbar {
      width: 8px;
    }
    
    &::-webkit-scrollbar-track {
      background: #fafafa;
      border-radius: 4px;
    }
    
    &::-webkit-scrollbar-thumb {
      background: #bfbfbf;
      border-radius: 4px;
      
      &:hover {
        background: #999;
      }
    }

    // Spin 组件也需要 flex 布局以支持居中
    :deep(.ant-spin-container) {
      flex: 1;
      display: flex;
      flex-direction: column;
      min-height: 100%;
      position: relative;
    }

    // 当没有数据时，让 List 和 Empty 组件居中显示
    :deep(.ant-list) {
      flex: 1;
      display: flex;
      flex-direction: column;
      min-height: 100%;
      
      &.ant-list-empty {
        justify-content: center;
        align-items: center;
        position: relative;
      }
    }

    :deep(.ant-list-empty-text) {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    :deep(.ant-empty) {
      margin: 0;
      text-align: center;
    }

    :deep(.ant-empty-image) {
      margin: 0 auto;
    }

    :deep(.ant-empty-description) {
      text-align: center;
      margin-top: 16px;
    }
  }

  :deep(.ant-list-item) {
    padding: 0;
  }

  .video-card-item {
    padding: 0;
  }

  .video-card-box {
    position: relative;
    background: #FFFFFF;
    box-shadow: 0px 0px 4px 0px rgba(24, 24, 24, 0.1);
    border-radius: 4px;
    overflow: hidden;
    height: 100%;
    cursor: pointer;

    .card-checkbox {
      position: absolute;
      top: 8px;
      left: 8px;
      z-index: 100;
      width: 20px;
      height: 20px;
      border: 2px solid #d9d9d9;
      border-radius: 3px;
      background: #ffffff;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      
      .checkbox-inner {
        width: 12px;
        height: 12px;
        border-radius: 2px;
        background: transparent;
      }
      
      &.checked {
        border-color: #ff4d4f;
        background: #ffffff;
        
        .checkbox-inner {
          background: #ff4d4f;
        }
      }
    }

    .img-box {
      display: block;
      width: 100%;
      height: 188px;
      overflow: hidden;
      background: #f5f5f5;
      position: relative;

      .card-image {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }

      .no-thumbnail {
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #999;
        font-size: 12px;
        background: #f5f5f5;
      }

      .play-icon {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        cursor: pointer;
        opacity: 0;
        transition: opacity 0.3s;
        z-index: 10;
      }

      &:hover .play-icon {
        opacity: 1;
      }
    }

    .card-content {
      padding: 12px;

      .card-info {
        margin-bottom: 8px;

        .info-item {
          font-size: 12px;
          line-height: 1.5;
          margin-bottom: 4px;
          color: #666;

          .info-label {
            color: #999;
          }

          .info-value {
            color: #333;
          }
        }
      }

      .card-actions {
        display: flex;
        justify-content: space-around;
        padding-top: 8px;
        border-top: 1px solid #f0f0f0;
        margin-top: 8px;
      }
    }
  }

  :deep(.ant-list-pagination) {
    margin: 16px 0;
    text-align: center;
  }
}

// 响应式设计
@media (max-width: 768px) {
  .record-video-container {
    height: 65vh;
    max-height: 600px;
    min-height: 500px;
  }

  .record-video-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;

    .header-actions {
      width: 100%;
      justify-content: flex-end;
    }
  }
}
</style>

