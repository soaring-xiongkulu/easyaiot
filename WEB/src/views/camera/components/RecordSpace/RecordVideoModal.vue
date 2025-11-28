<template>
  <BasicModal 
    v-bind="$attrs" 
    @register="register" 
    title="监控录像管理" 
    :width="1500"
    :showOkBtn="false"
    :showCancelBtn="false"
    :maskClosable="false"
  >
    <div class="record-video-container">
      <!-- 录像列表 -->
      <div class="table-wrapper">
        <a-table
          :columns="columns"
          :data-source="videoList"
          :loading="loading"
          :pagination="pagination"
          :row-selection="{ selectedRowKeys, onChange: onSelectChange }"
          row-key="object_name"
          @change="handleTableChange"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'preview'">
              <a-image
                v-if="record.thumbnail_url"
                :width="100"
                :src="record.thumbnail_url"
                :preview="false"
              />
              <span v-else class="no-thumbnail">无封面</span>
            </template>
            <template v-else-if="column.key === 'size'">
              {{ formatSize(record.size) }}
            </template>
            <template v-else-if="column.key === 'duration'">
              {{ formatDuration(record.duration) }}
            </template>
            <template v-else-if="column.key === 'action'">
              <a-space>
                <a-button type="link" size="small" @click="handlePlay(record)">
                  播放
                </a-button>
                <a-button type="link" size="small" @click="handlePreview(record)">
                  预览
                </a-button>
                <a-button type="link" size="small" danger @click="handleDelete(record)">
                  删除
                </a-button>
              </a-space>
            </template>
          </template>
        </a-table>
      </div>

      <!-- 底部按钮组 -->
      <div class="record-video-footer">
        <div class="record-video-footer-left">
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
    </div>

    <!-- 视频播放模态框 -->
    <a-modal
      v-model:open="playVisible"
      :title="playVideo?.filename"
      :footer="null"
      :width="1000"
    >
      <div style="text-align: center">
        <video
          v-if="playVideo"
          :src="getVideoUrl(playVideo)"
          controls
          style="width: 100%; max-height: 600px;"
        />
      </div>
    </a-modal>

    <!-- 视频预览模态框 -->
    <a-modal
      v-model:open="previewVisible"
      :title="previewVideo?.filename"
      :footer="null"
      :width="800"
    >
      <div style="text-align: center">
        <video
          v-if="previewVideo"
          :src="getVideoUrl(previewVideo)"
          controls
          style="width: 100%; max-height: 500px;"
        />
      </div>
    </a-modal>
  </BasicModal>
</template>

<script lang="ts" setup>
import { ref, reactive } from 'vue';
import { BasicModal, useModalInner } from '@/components/Modal';
import { useMessage } from '@/hooks/web/useMessage';
import { getRecordVideoList, deleteRecordVideos, type RecordVideo } from '@/api/device/record';
import { useModal } from '@/components/Modal';
import DialogPlayer from '@/components/VideoPlayer/DialogPlayer.vue';

defineOptions({ name: 'RecordVideoModal' });

const { createMessage } = useMessage();
const emit = defineEmits(['register']);

const modalData = ref<{ space_id?: number; space_name?: string }>({});
const videoList = ref<RecordVideo[]>([]);
const loading = ref(false);
const selectedRowKeys = ref<string[]>([]);
const previewVisible = ref(false);
const playVisible = ref(false);
const previewVideo = ref<RecordVideo | null>(null);
const playVideo = ref<RecordVideo | null>(null);

const [registerPlayerModal, { openModal: openPlayerModal }] = useModal();

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showTotal: (total) => `共 ${total} 个录像`,
});

const columns = [
  {
    title: '封面',
    key: 'preview',
    width: 120,
  },
  {
    title: '文件名',
    dataIndex: 'filename',
    key: 'filename',
    ellipsis: true,
  },
  {
    title: '大小',
    key: 'size',
    width: 100,
  },
  {
    title: '时长',
    key: 'duration',
    width: 100,
  },
  {
    title: '修改时间',
    dataIndex: 'last_modified',
    key: 'last_modified',
    width: 180,
  },
  {
    title: '操作',
    key: 'action',
    width: 200,
    fixed: 'right',
  },
];

const getVideoUrl = (record: RecordVideo) => {
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

const loadVideoList = async () => {
  if (!modalData.value.space_id) return;
  
  loading.value = true;
  try {
    const response = await getRecordVideoList(modalData.value.space_id, {
      pageNo: pagination.current,
      pageSize: pagination.pageSize,
    });
    
    if (response.code === 0) {
      videoList.value = response.data || [];
      pagination.total = response.total || 0;
    } else {
      createMessage.error(response.msg || '加载录像列表失败');
    }
  } catch (error) {
    console.error('加载录像列表失败', error);
    createMessage.error('加载录像列表失败');
  } finally {
    loading.value = false;
  }
};

const handleRefresh = () => {
  loadVideoList();
};

const handleTableChange = (pag: any) => {
  pagination.current = pag.current;
  pagination.pageSize = pag.pageSize;
  loadVideoList();
};

const onSelectChange = (keys: string[]) => {
  selectedRowKeys.value = keys;
};

const handlePlay = (record: RecordVideo) => {
  playVideo.value = record;
  playVisible.value = true;
  // 也可以使用 DialogPlayer 组件
  // openPlayerModal(true, {
  //   rtmp_stream: getVideoUrl(record),
  //   http_stream: getVideoUrl(record),
  // });
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
  pagination.current = 1;
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
  overflow: hidden; // 防止整个容器滚动
  
  .table-wrapper {
    flex: 1;
    min-height: 0; // 允许 flex 子元素收缩
    overflow-y: auto;
    overflow-x: hidden;
    padding-right: 8px;
    
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
  }

  .record-video-footer {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    margin-top: 12px;
    padding: 12px 0;
    border-top: 1px solid #e8e8e8;
    flex-shrink: 0; // 防止 footer 被压缩
    position: relative; // 确保 footer 在正常文档流中
    z-index: 10; // 确保 footer 在最上层
    background: #fff; // 确保 footer 有背景色，不会被内容遮挡

    .record-video-footer-left {
      display: flex;
      gap: 8px;
    }
  }

  :deep(.ant-table) {
    .ant-table-thead > tr > th {
      background: #fafafa;
      font-weight: 600;
      border-bottom: 2px solid #e8e8e8;
    }

    .ant-table-tbody > tr:hover > td {
      background: #f5f7fa;
    }
    
    .ant-table-pagination {
      margin: 16px 0;
    }
  }

  :deep(.ant-image) {
    border-radius: 4px;
    overflow: hidden;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  .no-thumbnail {
    color: #999;
    font-size: 12px;
  }
}

// 响应式设计
@media (max-width: 768px) {
  .record-video-container {
    height: 65vh;
    max-height: 600px;
    min-height: 500px;
  }

  .record-video-footer {
    flex-direction: column;
    gap: 8px;

    .record-video-footer-left {
      width: 100%;
      justify-content: center;
    }
  }
}
</style>

