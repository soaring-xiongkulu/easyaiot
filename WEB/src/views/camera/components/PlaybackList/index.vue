<template>
  <div class="playback-list-wrapper">
    <!-- 表格模式 -->
    <template v-if="viewMode === 'table'">
      <div class="p-4 bg-white" style="margin-bottom: 10px">
        <BasicForm @register="registerForm" />
      </div>
      <div class="p-2 bg-white">
        <BasicTable @register="registerTable">
          <template #toolbar>
            <a-button type="default" @click="handleClickSwap" preIcon="ant-design:swap-outlined">
              切换视图
            </a-button>
          </template>
          <template #bodyCell="{ column, record }">
            <template v-if="column.dataIndex === 'thumbnail_path'">
              <img
                v-if="record.thumbnail_path"
                :src="getThumbnailUrl(record.thumbnail_path)"
                alt="封面"
                class="thumbnail-img"
                @error="handleImageError"
              />
              <span v-else class="no-thumbnail">无封面</span>
            </template>
            <template v-else-if="column.dataIndex === 'duration'">
              {{ formatDuration(record.duration) }}
            </template>
            <template v-else-if="column.dataIndex === 'file_size'">
              {{ formatFileSize(record.file_size) }}
            </template>
            <template v-else-if="column.dataIndex === 'event_time'">
              {{ formatDateTime(record.event_time) }}
            </template>
            <template v-else-if="column.dataIndex === 'action'">
              <TableAction :actions="getTableActions(record)" />
            </template>
          </template>
        </BasicTable>
      </div>
    </template>

    <!-- 卡片模式 -->
    <PlaybackCardList
      v-else
      ref="cardListRef"
      :api="getPlaybackListApi"
      :params="searchParams"
      @play="handlePlay"
      @delete="handleDelete"
      @view="handleView"
    >
      <template #header>
        <a-button type="default" @click="handleClickSwap" preIcon="ant-design:swap-outlined">
          切换视图
        </a-button>
      </template>
    </PlaybackCardList>

    <DialogPlayer @register="registerPlayerAddModel" />
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive } from 'vue';
import { BasicTable, TableAction, useTable } from '@/components/Table';
import { BasicForm, useForm } from '@/components/Form';
import { useMessage } from '@/hooks/web/useMessage';
import { getPlaybackList, deletePlayback, type PlaybackInfo } from '@/api/device/playback';
import PlaybackCardList from './PlaybackCardList.vue';
import DialogPlayer from '@/components/VideoPlayer/DialogPlayer.vue';
import { useModal } from '@/components/Modal';

defineOptions({ name: 'PLAYBACK_LIST' });

const { createMessage } = useMessage();
const [registerPlayerAddModel, { openModal: openPlayerAddModel }] = useModal();

// 视图模式：table 列表模式，card 卡片模式
const viewMode = ref<'table' | 'card'>('card');

// 搜索参数
const searchParams = reactive({
  start_time: '',
  end_time: '',
  search: ''
});

// 卡片组件引用
const cardListRef = ref();

// 切换视图
function handleClickSwap() {
  viewMode.value = viewMode.value === 'table' ? 'card' : 'table';
}

// 获取封面图URL
const getThumbnailUrl = (thumbnailPath: string) => {
  if (!thumbnailPath) return '';
  // 如果是完整URL，直接返回
  if (thumbnailPath.startsWith('http://') || thumbnailPath.startsWith('https://')) {
    return thumbnailPath;
  }
  // 否则拼接API前缀
  return `${import.meta.env.VITE_GLOB_API_URL || ''}${thumbnailPath}`;
};

// 图片加载错误处理
const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement;
  img.style.display = 'none';
};

// 格式化时长
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

// 格式化文件大小
const formatFileSize = (bytes: number) => {
  if (!bytes) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
};

// 格式化日期时间
const formatDateTime = (dateTime: string) => {
  if (!dateTime) return '-';
  const date = new Date(dateTime);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
};

// 表格列定义
const getColumns = () => {
  return [
    {
      title: '封面',
      dataIndex: 'thumbnail_path',
      width: 120,
      align: 'center'
    },
    {
      title: '设备名称',
      dataIndex: 'device_name',
      width: 150
    },
    {
      title: '录制时间',
      dataIndex: 'event_time',
      width: 180
    },
    {
      title: '时长',
      dataIndex: 'duration',
      width: 120
    },
    {
      title: '文件大小',
      dataIndex: 'file_size',
      width: 120
    },
    {
      title: '文件路径',
      dataIndex: 'file_path',
      ellipsis: true
    },
    {
      title: '操作',
      dataIndex: 'action',
      width: 150,
      fixed: 'right'
    }
  ];
};

// 获取表格操作按钮
const getTableActions = (record: PlaybackInfo) => {
  return [
    {
      icon: 'octicon:play-16',
      tooltip: '播放',
      onClick: () => handlePlay(record)
    },
    {
      icon: 'ant-design:eye-filled',
      tooltip: '详情',
      onClick: () => handleView(record)
    },
    {
      icon: 'material-symbols:delete-outline-rounded',
      tooltip: '删除',
      popConfirm: {
        title: '确定删除此录像？',
        confirm: () => handleDelete(record)
      }
    }
  ];
};

// 表单getFieldsValue方法的引用（用于在表格beforeFetch中访问）
let formGetFieldsValue: (() => Recordable) | null = null;

// 表格配置（先定义，因为表单需要引用reload方法）
const [registerTable, { reload }] = useTable({
  canResize: true,
  showIndexColumn: false,
  title: '录像回放列表',
  api: getPlaybackList,
  columns: getColumns(),
  useSearchForm: false,
  showTableSetting: false,
  pagination: true,
  beforeFetch: (params) => {
    // 合并表单搜索参数
    if (formGetFieldsValue) {
      const formValues = formGetFieldsValue();
      return {
        ...params,
        ...formValues
      };
    }
    return params;
  },
  fetchSetting: {
    listField: 'data',
    totalField: 'total'
  },
  rowKey: 'id'
});

// 表单配置
const [registerForm, { validate, getFieldsValue, resetFields }] = useForm({
  schemas: [
    {
      field: 'search',
      label: '搜索',
      component: 'Input',
      componentProps: {
        placeholder: '设备名称/文件路径'
      }
    },
    {
      field: 'start_time',
      label: '开始时间',
      component: 'DatePicker',
      componentProps: {
        showTime: true,
        format: 'YYYY-MM-DD HH:mm:ss'
      }
    },
    {
      field: 'end_time',
      label: '结束时间',
      component: 'DatePicker',
      componentProps: {
        showTime: true,
        format: 'YYYY-MM-DD HH:mm:ss'
      }
    }
  ],
  labelWidth: 80,
  baseColProps: { span: 6 },
  actionColOptions: { span: 6, style: 'margin-left: 8px' },
  compact: true,
  autoSubmitOnEnter: true,
  submitFunc: handleFormSubmit,
  resetFunc: handleFormReset
});

// 保存表单getFieldsValue方法的引用
formGetFieldsValue = getFieldsValue;

// 表单提交
async function handleFormSubmit() {
  await validate();
  // 更新搜索参数
  const formData = getFieldsValue();
  Object.assign(searchParams, formData);
  // 重新加载表格（beforeFetch会自动获取表单值）
  reload();
}

// 表单重置
async function handleFormReset() {
  await resetFields();
  // 清空搜索参数
  Object.assign(searchParams, {
    start_time: '',
    end_time: '',
    search: ''
  });
  // 重新加载表格
  reload();
}

// 获取录像播放地址
const getPlaybackUrl = (filePath: string): string => {
  if (!filePath) return '';
  // 如果是完整URL，直接返回
  if (filePath.startsWith('http://') || filePath.startsWith('https://')) {
    return filePath;
  }
  // 如果是相对路径，拼接API前缀
  if (filePath.startsWith('/')) {
    return `${import.meta.env.VITE_GLOB_API_URL || ''}${filePath}`;
  }
  // 其他情况直接返回
  return filePath;
};

// 播放录像
const handlePlay = (record: PlaybackInfo) => {
  // 获取播放地址
  const httpStream = getPlaybackUrl(record.file_path);
  
  if (!httpStream) {
    createMessage.warning('录像文件地址无效，无法播放');
    return;
  }
  
  // 打开播放器，与算法任务保持一致
  openPlayerAddModel(true, {
    id: record.device_id,
    http_stream: httpStream,
  });
};

// 查看详情
const handleView = (record: PlaybackInfo) => {
  createMessage.info(`查看录像详情: ${record.device_name} - ${formatDateTime(record.event_time)}`);
  // 可以打开详情弹窗
};

// 删除录像
const handleDelete = async (record: PlaybackInfo) => {
  try {
    await deletePlayback(record.id);
    createMessage.success('删除成功');
    // 刷新列表
    if (viewMode.value === 'table') {
      reload();
    } else if (viewMode.value === 'card' && cardListRef.value) {
      cardListRef.value.fetch();
    }
  } catch (error) {
    console.error('删除失败', error);
    createMessage.error('删除失败');
  }
};

// API包装函数
const getPlaybackListApi = (params: any) => {
  return getPlaybackList(params);
};

// 暴露刷新方法
defineExpose({
  reload: () => {
    if (viewMode.value === 'table') {
      reload();
    } else if (viewMode.value === 'card' && cardListRef.value) {
      cardListRef.value.fetch();
    }
  }
});
</script>

<style lang="less" scoped>
.playback-list-wrapper {
  .thumbnail-img {
    width: 80px;
    height: 60px;
    object-fit: cover;
    border-radius: 4px;
    cursor: pointer;
  }

  .no-thumbnail {
    color: #999;
    font-size: 12px;
  }

  :deep(.ant-form-item) {
    margin-bottom: 0;
  }

  :deep(.ant-row) {
    margin-left: -4px !important;
    margin-right: -4px !important;
  }

  :deep(.ant-col) {
    padding-left: 4px !important;
    padding-right: 4px !important;
  }
}
</style>

