<template>
  <div>
    <BasicTable v-if="state.isTableMode" @register="registerTable">
      <template #toolbar>
        <div style="display: flex; align-items: center; gap: 8px;">
          <a-button type="default" @click="handleClickSwap"
                    preIcon="ant-design:swap-outlined">切换视图
          </a-button>
        </div>
      </template>
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'device_id'">
          <span style="cursor: pointer" @click="handleCopy(record['device_id'])"><Icon
            icon="tdesign:copy-filled" color="#4287FCFF"/> {{ formatDeviceId(record['device_id']) }}</span>
        </template>
        <template v-if="column.key === 'device_name'">
          <span style="cursor: pointer" @click="handleCopy(record['device_name'])"><Icon
            icon="tdesign:copy-filled" color="#4287FCFF"/> {{ record['device_name'] }}</span>
        </template>
        <template v-if="column.key === 'task_type'">
          <a-tag :color="getTaskTypeColor(record['task_type'])">
            {{ getTaskTypeText(record['task_type']) }}
          </a-tag>
        </template>
        <template v-if="column.dataIndex === 'action'">
          <TableAction
            :actions="[
              {
                icon: 'ion:image-sharp',
                tooltip: {
                  title: '查看告警图片',
                  placement: 'top',
                },
                onClick: handleViewImage.bind(null, record),
              },
              {
                icon: 'icon-park-outline:video',
                tooltip: {
                  title: '查看告警录像',
                  placement: 'top',
                },
                onClick: handleViewVideo.bind(null, record),
              },
            ]"
          />
        </template>
      </template>
    </BasicTable>
    <div v-else>
      <AlertCards
        :api="queryAlarmList"
        :params="params"
        @getMethod="getMethod"
        @viewImage="handleCardViewImage"
        @viewVideo="handleCardViewVideo"
      >
        <template #header>
          <div style="display: flex; align-items: center; gap: 8px;">
            <a-button type="default" @click="handleClickSwap"
                      preIcon="ant-design:swap-outlined">切换视图
            </a-button>
          </div>
        </template>
      </AlertCards>
    </div>
    <!-- 图片查看弹窗 -->
    <ImageModal @register="registerImageModal" />
    <!-- 视频播放弹窗 -->
    <DialogPlayer @register="registerVideoModal" />
  </div>
</template>
<script lang="ts" setup name="noticeSetting">
import {reactive, ref} from 'vue';
import {BasicTable, TableAction, useTable} from '@/components/Table';
import {useMessage} from '@/hooks/web/useMessage';
import {getBasicColumns, getFormConfig} from "./Data";
import {useRouter} from "vue-router";
import {queryAlarmList, queryAlertRecord} from "@/api/device/calculate";
import {Icon} from "@/components/Icon";
import AlertCards from "@/views/alert/components/AlertCards/index.vue";
import ImageModal from "@/views/alert/components/ImageModal/index.vue";
import DialogPlayer from "@/components/VideoPlayer/DialogPlayer.vue";
import { useModal } from '@/components/Modal';

const router = useRouter();
const [registerImageModal, { openModal: openImageModal }] = useModal();
const [registerVideoModal, { openModal: openVideoModal }] = useModal();

defineOptions({name: 'Alarm'})

const state = reactive({
  isTableMode: false,
  activeKey: '1',
});

// 请求api时附带参数
const params = {};

let cardListReload = () => {
};

// 获取内部fetch方法;
function getMethod(m: any) {
  cardListReload = m;
}

// 切换视图
function handleClickSwap() {
  state.isTableMode = !state.isTableMode;
}

// 表格刷新
function handleSuccess() {
  reload({
    page: 0,
  });
  cardListReload();
}

// 卡片视图事件处理
function handleCardViewImage(record) {
  handleViewImage(record);
}

function handleCardViewVideo(record) {
  handleViewVideo(record);
}

const {createMessage} = useMessage();
const [
  registerTable,
  {
    // setLoading,
    // setColumns,
    // getColumns,
    // getDataSource,
    // getRawDataSource,
    reload,
    // getPaginationRef,
    // setPagination,
    // getSelectRows,
    // getSelectRowKeys,
    // setSelectedRowKeys,
    // clearSelectedRowKeys,
  },
] = useTable({
  canResize: true,
  showIndexColumn: false,
  title: '告警事件列表',
  api: queryAlarmList,
  columns: getBasicColumns(),
  useSearchForm: true,
  showTableSetting: false,
  formConfig: getFormConfig(),
  fetchSetting: {
    listField: 'alert_list',
    totalField: 'total',
  },
  beforeFetch: (params) => {
    // 处理时间范围参数
    // RangePicker 字段名为 [begin_datetime, end_datetime] 时，返回的可能是数组格式
    const timeRangeKey = '[begin_datetime, end_datetime]';
    if (params[timeRangeKey] && Array.isArray(params[timeRangeKey])) {
      const [begin, end] = params[timeRangeKey];
      params.begin_datetime = begin;
      params.end_datetime = end;
      delete params[timeRangeKey];
    }
    return params;
  },
  rowKey: 'id',
});

// 封装下载工具函数
const downloadImage = (data, fileName = 'image.png') => {
  // 二进制数据处理
  if (data instanceof ArrayBuffer || data instanceof Uint8Array) {
    const blob = new Blob([data], {type: 'image/png'}) // 可指定具体MIME类型
    return downloadImage(blob, fileName)
  }

  // 处理Blob数据
  if (data instanceof Blob) {
    const url = URL.createObjectURL(data)
    const link = document.createElement('a')
    link.href = url
    link.download = fileName
    document.body.appendChild(link)
    link.click()
    URL.revokeObjectURL(url)
    document.body.removeChild(link)
    return
  }

  // 处理Base64数据
  if (data.startsWith('data:image')) {
    alert(333)
    const arr = data.split(',')
    const mime = arr[0].match(/:(.*?);/)[1]
    const bstr = atob(arr[1])
    let n = bstr.length
    const u8arr = new Uint8Array(n)
    while (n--) u8arr[n] = bstr.charCodeAt(n)
    downloadImage(new Blob([u8arr], {type: mime}), fileName)
  }
}

const handleViewImage = (record) => {
  if (record['image_path'] == null) {
    createMessage.warn('告警图片不存在');
    return;
  }
  openImageModal(true, {
    image_path: record['image_path'],
  });
};

// 防重复提示：记录最近提示的时间和内容
let lastVideoErrorTime = 0;
let lastVideoErrorMsg = '';

// 获取录像播放地址（参考录像空间的处理方式）
const getVideoUrl = (videoUrl: string): string => {
  if (!videoUrl) return '';
  // 如果是完整URL，直接返回
  if (videoUrl.startsWith('http://') || videoUrl.startsWith('https://')) {
    return videoUrl;
  }
  // 如果是相对路径（以/api/v1/buckets开头），添加前端启动地址前缀
  if (videoUrl.startsWith('/api/v1/buckets')) {
    return `${window.location.origin}${videoUrl}`;
  }
  // 其他相对路径，拼接API前缀
  if (videoUrl.startsWith('/')) {
    return `${import.meta.env.VITE_GLOB_API_URL || ''}${videoUrl}`;
  }
  // 其他情况直接返回
  return videoUrl;
};

const handleViewVideo = async (record) => {
  if (!record['device_id'] || !record['time']) {
    createMessage.warn('缺少必要信息：设备ID或告警时间');
    return;
  }
  
  try {
    // 查询录像URL
    const result = await queryAlertRecord({
      device_id: record['device_id'],
      alert_time: record['time'],
      time_range: 60, // 前后60秒
    });

    if (result && result.video_url) {
      // 处理录像URL，添加前缀
      const videoUrl = getVideoUrl(result.video_url);
      
      // 使用DialogPlayer播放，参数格式：{ id, http_stream }
      openVideoModal(true, {
        id: record['device_id'],
        http_stream: videoUrl,
      });
      // 重置错误记录
      lastVideoErrorTime = 0;
      lastVideoErrorMsg = '';
    } else {
      // 检查是否是业务错误（code=400）
      const errorMsg = result?.message || '暂未找到该时间段的录像文件';
      showVideoErrorOnce(errorMsg);
    }
  } catch (error: any) {
    console.error('查询录像失败:', error);
    // 处理业务错误（HTTP 200但code=400）
    const errorData = error?.response?.data || error?.data;
    if (errorData && errorData.code === 400) {
      const errorMsg = errorData.message || '暂未找到该时间段的录像文件';
      showVideoErrorOnce(errorMsg);
    } else {
      // 其他错误
      const errorMsg = error?.response?.data?.message || error?.message || '查询录像失败，请稍后重试';
      showVideoErrorOnce(errorMsg);
    }
  }
};

// 防重复提示函数：3秒内相同错误只提示一次
function showVideoErrorOnce(message: string) {
  const now = Date.now();
  // 如果3秒内提示过相同内容，则不再提示
  if (now - lastVideoErrorTime < 3000 && lastVideoErrorMsg === message) {
    return;
  }
  lastVideoErrorTime = now;
  lastVideoErrorMsg = message;
  createMessage.warn(message);
}

// 格式化设备ID显示（超过8个字符省略）
function formatDeviceId(deviceId: string | null | undefined): string {
  if (!deviceId) return '-';
  if (deviceId.length <= 8) return deviceId;
  return deviceId.substring(0, 8) + '...';
}

// 获取任务类型文本
function getTaskTypeText(taskType: string | null | undefined): string {
  if (!taskType) return '实时';
  // 兼容 'snap' 和 'snapshot' 两种值
  if (taskType === 'snap' || taskType === 'snapshot') {
    return '抓拍';
  } else if (taskType === 'realtime') {
    return '实时';
  }
  return taskType;
}

// 获取任务类型标签颜色
function getTaskTypeColor(taskType: string | null | undefined): string {
  if (!taskType) return 'blue';
  // 兼容 'snap' 和 'snapshot' 两种值
  if (taskType === 'snap' || taskType === 'snapshot') {
    return 'green';
  } else if (taskType === 'realtime') {
    return 'blue';
  }
  return 'default';
}

async function handleCopy(record: object) {
  if (navigator.clipboard) {
    await navigator.clipboard.writeText(record);
  } else {
    // 降级方案
    const textarea = document.createElement('textarea');
    textarea.value = record;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
  }
  createMessage.success('复制成功');
}
</script>
