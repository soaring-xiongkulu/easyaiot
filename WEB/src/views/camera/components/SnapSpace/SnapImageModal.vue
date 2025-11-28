<template>
  <BasicModal 
    v-bind="$attrs" 
    @register="register" 
    title="抓拍图片管理" 
    :width="1200"
    :showOkBtn="false"
    :showCancelBtn="false"
  >
    <div class="snap-image-container">
      <!-- 工具栏 -->
      <div class="toolbar">
        <a-space>
          <a-input
            v-model:value="deviceIdFilter"
            placeholder="筛选设备ID"
            style="width: 200px"
            allow-clear
            @pressEnter="handleSearch"
          />
          <a-button type="primary" @click="handleSearch">搜索</a-button>
          <a-button @click="handleRefresh">刷新</a-button>
          <a-button 
            type="primary" 
            danger 
            :disabled="selectedRowKeys.length === 0"
            @click="handleBatchDelete"
          >
            批量删除 ({{ selectedRowKeys.length }})
          </a-button>
        </a-space>
      </div>

      <!-- 图片列表 -->
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
const deviceIdFilter = ref('');
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
      device_id: deviceIdFilter.value || undefined,
      pageNo: pagination.current,
      pageSize: pagination.pageSize,
    });
    
    if (response.code === 0) {
      imageList.value = response.data || [];
      pagination.total = response.total || 0;
    } else {
      createMessage.error(response.msg || '加载图片列表失败');
    }
  } catch (error) {
    console.error('加载图片列表失败', error);
    createMessage.error('加载图片列表失败');
  } finally {
    loading.value = false;
  }
};

const handleSearch = () => {
  pagination.current = 1;
  loadImageList();
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
  deviceIdFilter.value = '';
  selectedRowKeys.value = [];
  pagination.current = 1;
  setModalProps({ confirmLoading: false });
  await loadImageList();
});
</script>

<style lang="less" scoped>
.snap-image-container {
  .toolbar {
    margin-bottom: 16px;
    padding: 16px;
    background: #f5f5f5;
    border-radius: 4px;
  }
}
</style>

