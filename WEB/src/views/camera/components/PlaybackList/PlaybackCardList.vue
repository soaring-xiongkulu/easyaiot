<template>
  <div class="playback-card-list-wrapper p-2">
    <div class="p-4 bg-white" style="margin-bottom: 10px">
      <BasicForm @register="registerForm" />
    </div>
    <div class="p-2 bg-white">
      <Spin :spinning="state.loading">
        <List
          :grid="{ gutter: 12, xs: 1, sm: 2, md: 3, lg: 4, xl: 4, xxl: 4 }"
          :data-source="data"
          :pagination="paginationProp"
        >
          <template #header>
            <div style="display: flex; align-items: center; justify-content: space-between; flex-direction: row;">
              <span style="padding-left: 7px; font-size: 16px; font-weight: 500; line-height: 24px;">录像回放列表</span>
              <div class="space-x-2">
                <slot name="header"></slot>
              </div>
            </div>
          </template>
          <template #renderItem="{ item }">
            <ListItem class="playback-item">
              <div class="playback-card">
                <!-- 封面图 -->
                <div class="playback-thumbnail" @click="handleView(item)">
                  <img
                    v-if="item.thumbnail_path"
                    :src="getThumbnailUrl(item.thumbnail_path)"
                    alt="封面"
                    class="thumbnail-img"
                    @error="handleImageError"
                  />
                  <div v-else class="no-thumbnail">
                    <Icon icon="ant-design:video-camera-outlined" :size="48" color="#999" />
                    <span>无封面</span>
                  </div>
                  <!-- 播放按钮遮罩 -->
                  <div class="play-overlay" @click.stop="handlePlay(item)">
                    <Icon icon="octicon:play-16" :size="32" color="#fff" />
                  </div>
                  <!-- 时长标签 -->
                  <div class="duration-badge">
                    {{ formatDuration(item.duration) }}
                  </div>
                </div>

                <!-- 信息区域 -->
                <div class="playback-info">
                  <div class="title" :title="item.device_name">
                    {{ item.device_name || item.device_id }}
                  </div>
                  <div class="props">
                    <div class="prop">
                      <div class="label">录制时间</div>
                      <div class="value">{{ formatDateTime(item.event_time) }}</div>
                    </div>
                    <div class="prop">
                      <div class="label">文件大小</div>
                      <div class="value">{{ formatFileSize(item.file_size) }}</div>
                    </div>
                  </div>
                  <!-- 操作按钮 -->
                  <div class="btns">
                    <div class="btn" @click="handlePlay(item)" title="播放">
                      <Icon icon="octicon:play-16" :size="15" color="#3B82F6" />
                    </div>
                    <div class="btn" @click="handleView(item)" title="详情">
                      <Icon icon="ant-design:eye-filled" :size="15" color="#3B82F6" />
                    </div>
                    <Popconfirm
                      title="是否确认删除？"
                      ok-text="是"
                      cancel-text="否"
                      @confirm="handleDelete(item)"
                    >
                      <div class="btn" title="删除">
                        <Icon icon="material-symbols:delete-outline-rounded" :size="15" color="#DC2626" />
                      </div>
                    </Popconfirm>
                  </div>
                </div>
              </div>
            </ListItem>
          </template>
        </List>
      </Spin>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { onMounted, reactive, ref, watch } from 'vue';
import { List, Popconfirm, Spin } from 'ant-design-vue';
import { BasicForm, useForm } from '@/components/Form';
import { propTypes } from '@/utils/propTypes';
import { isFunction } from '@/utils/is';
import { Icon } from '@/components/Icon';
import { useMessage } from '@/hooks/web/useMessage';
import type { PlaybackInfo } from '@/api/device/playback';

const ListItem = List.Item;

// 组件接收参数
const props = defineProps({
  // 请求API的参数
  params: propTypes.object.def({}),
  // api
  api: propTypes.func
});

const { createMessage } = useMessage();

// 暴露内部方法
const emit = defineEmits(['getMethod', 'delete', 'view', 'play']);

// 数据
const data = ref<PlaybackInfo[]>([]);
const state = reactive({
  loading: true
});

// 表单
const [registerForm, { validate }] = useForm({
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
  autoSubmitOnEnter: true,
  submitFunc: handleSubmit,
  compact: true
});

// 表单提交
async function handleSubmit() {
  const formData = await validate();
  await fetch(formData);
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
    return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  } else {
    return `${minutes}:${String(secs).padStart(2, '0')}`;
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
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

// 自动请求并暴露内部方法
onMounted(() => {
  fetch();
  emit('getMethod', fetch);
});

async function fetch(p = {}) {
  const { api, params } = props;
  if (api && isFunction(api)) {
    try {
      state.loading = true;
      // 转换表单参数为API需要的格式
      const apiParams: any = {
        ...params,
        pageNo: page.value,
        pageSize: pageSize.value
      };

      // 处理搜索参数
      if (p.search) {
        apiParams.search = p.search;
      }
      if (p.start_time) {
        apiParams.start_time = p.start_time;
      }
      if (p.end_time) {
        apiParams.end_time = p.end_time;
      }

      // 合并其他参数
      Object.keys(p).forEach(key => {
        if (!['search', 'start_time', 'end_time'].includes(key)) {
          apiParams[key] = p[key];
        }
      });

      const res = await api(apiParams);
      // 根据API返回格式，处理数据
      if (res && res.data) {
        data.value = res.data || [];
        total.value = res.total || 0;
      } else if (Array.isArray(res)) {
        data.value = res;
        total.value = res.length;
      } else {
        data.value = [];
        total.value = 0;
      }
    } catch (error) {
      console.error('获取数据失败:', error);
      data.value = [];
      total.value = 0;
    } finally {
      hideLoading();
    }
  }
}

function hideLoading() {
  state.loading = false;
}

// 分页相关
const page = ref(1);
const pageSize = ref(8);
const total = ref(0);
const paginationProp = ref({
  showSizeChanger: false,
  showQuickJumper: true,
  pageSize,
  current: page,
  total,
  showTotal: (total: number) => `总 ${total} 条`,
  onChange: pageChange,
  onShowSizeChange: pageSizeChange
});

function pageChange(p: number, pz: number) {
  page.value = p;
  pageSize.value = pz;
  fetch();
}

function pageSizeChange(_current, size: number) {
  pageSize.value = size;
  fetch();
}

async function handleView(record: PlaybackInfo) {
  emit('view', record);
}

async function handleDelete(record: PlaybackInfo) {
  emit('delete', record);
}

async function handlePlay(record: PlaybackInfo) {
  emit('play', record);
}

// 暴露刷新方法
defineExpose({
  fetch
});
</script>

<style lang="less" scoped>
.playback-card-list-wrapper {
  :deep(.ant-list-header) {
    border-block-end: 0;
  }
  :deep(.ant-list-header) {
    padding-top: 0;
    padding-bottom: 8px;
  }
  :deep(.ant-list) {
    padding: 6px;
  }
  :deep(.ant-list-item) {
    margin: 6px;
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

  .playback-item {
    overflow: hidden;
    box-shadow: 0 0 4px #00000026;
    border-radius: 8px;
    padding: 0;
    position: relative;
    background-color: #fff;
    transition: all 0.3s;

    &:hover {
      box-shadow: 0 4px 12px #00000033;
      transform: translateY(-2px);
    }

    .playback-card {
      display: flex;
      flex-direction: column;
      height: 100%;

      .playback-thumbnail {
        position: relative;
        width: 100%;
        height: 180px;
        background: #f5f5f5;
        overflow: hidden;
        cursor: pointer;

        .thumbnail-img {
          width: 100%;
          height: 100%;
          object-fit: cover;
          transition: transform 0.3s;
        }

        .no-thumbnail {
          width: 100%;
          height: 100%;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          color: #999;
          font-size: 12px;

          span {
            margin-top: 8px;
          }
        }

        .play-overlay {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.4);
          display: flex;
          align-items: center;
          justify-content: center;
          opacity: 0;
          transition: opacity 0.3s;
          cursor: pointer;

          &:hover {
            opacity: 1;
          }
        }

        .duration-badge {
          position: absolute;
          bottom: 8px;
          right: 8px;
          background: rgba(0, 0, 0, 0.7);
          color: #fff;
          padding: 2px 6px;
          border-radius: 4px;
          font-size: 12px;
        }

        &:hover .play-overlay {
          opacity: 1;
        }

        &:hover .thumbnail-img {
          transform: scale(1.05);
        }
      }

      .playback-info {
        padding: 12px;
        flex: 1;
        display: flex;
        flex-direction: column;

        .title {
          font-size: 14px;
          font-weight: 600;
          color: #050708;
          line-height: 20px;
          margin-bottom: 8px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .props {
          flex: 1;
          margin-bottom: 8px;

          .prop {
            margin-bottom: 6px;

            .label {
              font-size: 12px;
              font-weight: 400;
              color: #666;
              line-height: 14px;
            }

            .value {
              font-size: 12px;
              font-weight: 500;
              color: #050708;
              line-height: 16px;
              margin-top: 2px;
              overflow: hidden;
              text-overflow: ellipsis;
              white-space: nowrap;
            }
          }
        }

        .btns {
          display: flex;
          justify-content: space-around;
          align-items: center;
          padding-top: 8px;
          border-top: 1px solid #f0f0f0;

          .btn {
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            border-radius: 4px;
            transition: background-color 0.3s;

            &:hover {
              background-color: #f5f5f5;
            }
          }
        }
      }
    }
  }
}
</style>

