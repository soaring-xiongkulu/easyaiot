<template>
  <BasicModal 
    v-bind="$attrs" 
    @register="register" 
    title="抓拍图片管理" 
    :width="1500"
    :showOkBtn="false"
    :showCancelBtn="false"
    :maskClosable="true"
  >
    <div class="snap-image-container">
      <!-- 图片列表 -->
      <div class="table-wrapper">
        <a-table
          :columns="columns"
          :data-source="imageList"
          :loading="loading"
          :pagination="pagination"
          :row-selection="{ selectedRowKeys, onChange: onSelectChange }"
          row-key="object_name"
          @change="handleTableChange"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'preview'">
              <a-image
                :width="100"
                :src="getImageUrl(record)"
                :preview="false"
              />
            </template>
            <template v-else-if="column.key === 'size'">
              {{ formatSize(record.size) }}
            </template>
            <template v-else-if="column.key === 'action'">
              <a-space>
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
      <div class="snap-image-footer">
        <div class="snap-image-footer-left">
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

    <!-- 图片预览模态框 -->
    <a-modal
      v-model:open="previewVisible"
      :title="previewImage?.filename"
      :footer="null"
      :width="800"
    >
      <div style="text-align: center">
        <a-image
          :src="previewImage ? getImageUrl(previewImage) : ''"
          :preview="true"
        />
      </div>
    </a-modal>
  </BasicModal>
</template>

<script lang="ts" setup>
import { ref, reactive, computed } from 'vue';
import { BasicModal, useModalInner } from '@/components/Modal';
import { useMessage } from '@/hooks/web/useMessage';
import { getSnapImageList, deleteSnapImages, type SnapImage } from '@/api/device/snap';

defineOptions({ name: 'SnapImageModal' });

const { createMessage } = useMessage();
const emit = defineEmits(['register']);

const modalData = ref<{ space_id?: number; space_name?: string }>({});
const imageList = ref<SnapImage[]>([]);
const loading = ref(false);
const selectedRowKeys = ref<string[]>([]);
const previewVisible = ref(false);
const previewImage = ref<SnapImage | null>(null);

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showTotal: (total) => `共 ${total} 张图片`,
});

const columns = [
  {
    title: '预览',
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
    title: '修改时间',
    dataIndex: 'last_modified',
    key: 'last_modified',
    width: 180,
  },
  {
    title: '操作',
    key: 'action',
    width: 150,
    fixed: 'right',
  },
];

const getImageUrl = (record: SnapImage) => {
  // 优先使用后台返回的 url 字段，如果没有则使用 object_name 构建
  if (record.url) {
    return record.url;
  }
  if (!modalData.value.space_id) return '';
  return `/video/snap/space/${modalData.value.space_id}/image/${record.object_name}`;
};

const formatSize = (bytes: number) => {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
};

const loadImageList = async () => {
  if (!modalData.value.space_id) return;
  
  loading.value = true;
  try {
    const response = await getSnapImageList(modalData.value.space_id, {
      pageNo: pagination.current,
      pageSize: pagination.pageSize,
    });
    
    // 响应拦截器处理后的数据结构：{ code, data, msg, total }
    // 或者直接是数组（如果响应拦截器返回了 data.data）
    if (response && typeof response === 'object') {
      if (response.code === 0) {
        // 确保 data 是数组
        const data = Array.isArray(response.data) ? response.data : [];
        imageList.value = data;
        pagination.total = response.total || 0;
      } else {
        createMessage.error(response.msg || '加载图片列表失败');
        imageList.value = [];
        pagination.total = 0;
      }
    } else if (Array.isArray(response)) {
      // 如果响应拦截器直接返回了数组
      imageList.value = response;
      pagination.total = response.length;
    } else {
      console.error('意外的响应格式:', response);
      imageList.value = [];
      pagination.total = 0;
    }
  } catch (error) {
    console.error('加载图片列表失败', error);
    createMessage.error('加载图片列表失败');
    imageList.value = [];
    pagination.total = 0;
  } finally {
    loading.value = false;
  }
};

const handleRefresh = () => {
  loadImageList();
};

const handleTableChange = (pag: any) => {
  pagination.current = pag.current;
  pagination.pageSize = pag.pageSize;
  loadImageList();
};

const onSelectChange = (keys: string[]) => {
  selectedRowKeys.value = keys;
};

const handlePreview = (record: SnapImage) => {
  previewImage.value = record;
  previewVisible.value = true;
};

const handleDelete = async (record: SnapImage) => {
  if (!modalData.value.space_id) return;
  
  try {
    await deleteSnapImages(modalData.value.space_id, [record.object_name]);
    createMessage.success('删除成功');
    loadImageList();
  } catch (error: any) {
    console.error('删除失败', error);
    const errorMsg = error?.response?.data?.msg || error?.message || '删除失败';
    createMessage.error(errorMsg);
  }
};

const handleBatchDelete = async () => {
  if (!modalData.value.space_id || selectedRowKeys.value.length === 0) return;
  
  try {
    await deleteSnapImages(modalData.value.space_id, selectedRowKeys.value);
    createMessage.success(`成功删除 ${selectedRowKeys.value.length} 张图片`);
    selectedRowKeys.value = [];
    loadImageList();
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
  await loadImageList();
});
</script>

<style lang="less" scoped>
.snap-image-container {
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

  .snap-image-footer {
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

    .snap-image-footer-left {
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
}

// 响应式设计
@media (max-width: 768px) {
  .snap-image-container {
    height: 65vh;
    max-height: 600px;
    min-height: 500px;
  }

  .snap-image-footer {
    flex-direction: column;
    gap: 8px;

    .snap-image-footer-left {
      width: 100%;
      justify-content: center;
    }
  }
}
</style>

