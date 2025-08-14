<template>
  <div class="subDevice-wrapper">
    <Progress v-show="isShowProgress" :percent="progressPercentage" size="small"
              status="active"/>
    <BasicTable @register="registerTable" v-if="state.isTableMode">
      <template #toolbar>
        <a-button type="primary"
                  @click="openAddModal(true, { datasetId: route.params['id'], isImage: true, isZip: false, isVideo: false, isStream: false })">
          上传视频
        </a-button>
        <a-button type="default" @click="handleClickSwap" preIcon="ant-design:swap-outlined">
          切换视图
        </a-button>
        <PopConfirmButton
          placement="topRight"
          @confirm="handleDeleteAll"
          type="primary"
          color="error"
          :disabled="!checkedKeys.length"
          :title="`是否确认删除？`"
          preIcon="ant-design:delete-outlined"
        >
          批量删除
        </PopConfirmButton>
      </template>
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'action'">
          <TableAction
            :actions="[
             {
                icon: 'ant-design:eye-filled',
                tooltip: {
                  title: '详情',
                  placement: 'top',
                },
                onClick: openAddModal.bind(null, true, { datasetId: route.params['id'], isEdit: false, isView: true, record }),
              },
              {
                tooltip: {
                  title: '编辑',
                  placement: 'top',
                },
                icon: 'ant-design:edit-filled',
                onClick: openAddModal.bind(null, true, { datasetId: route.params['id'], isEdit: true, isView: false, record }),
              },
              {
                tooltip: {
                  title: '删除',
                  placement: 'top',
                },
                icon: 'material-symbols:delete-outline-rounded',
                popConfirm: {
                  placement: 'topRight',
                  title: '是否确认删除？',
                  confirm: handleDelete.bind(null, record),
                },
              },
            ]"
          />
        </template>
      </template>
    </BasicTable>
    <div v-else>
      <DatasetVideoCardList :params="params" :api="getDatasetVideoPage" @get-method="getMethod"
                            @delete="handleDel"
                            @view="handleView" @edit="handleEdit" @load-video="handleLoadVideo"
                            @frame="handleFrame">
        <template #header>
          <a-button type="primary" @click="openAddModal(true, { datasetId: route.params['id'] })">
            新增视频数据集
          </a-button>
          <a-button type="default" @click="handleClickSwap" preIcon="ant-design:swap-outlined">
            切换视图
          </a-button>
        </template>
      </DatasetVideoCardList>
    </div>
    <DatasetVideoModal @register="registerAddModel" @success="handleSuccess"/>
    <DatasetVideoPlayModal @register="registerPlayModel" @success="handleSuccess"/>
    <DatasetVideoFrameModal @register="registerFrameModel" @success="handleSetFrameParamSuccess"/>
  </div>
</template>

<script setup lang="ts" name="devicesPage">
import {getBasicColumns} from './data';
import {useMessage} from '@/hooks/web/useMessage';
import {BasicTable, TableAction, useTable} from '@/components/Table';
import {useRoute} from "vue-router";
import {useModal} from "@/components/Modal";
import {Progress} from 'ant-design-vue'
import {deleteDatasetVideo, getDatasetVideoPage} from "@/api/device/dataset";
import {PopConfirmButton} from "@/components/Button";
import {computed, reactive, ref} from "vue";
import DatasetVideoModal from "@/views/dataset/components/DatasetVideoModal/index.vue";
import DatasetVideoCardList from "@/views/dataset/components/DatasetVideoCardList/index.vue";
import DatasetVideoPlayModal from "@/views/dataset/components/DatasetVideoPlayModal/index.vue";
import JSZip from "jszip";
import DatasetVideoFrameModal from "@/views/dataset/components/DatasetVideoFrameModal/index.vue";

const {createMessage} = useMessage();

const [registerAddModel, {openModal: openAddModal}] = useModal();
const [registerPlayModel, {openModal: openPlayModal}] = useModal();
const [registerFrameModel, {openModal: openFrameModal}] = useModal();

defineOptions({name: 'DatasetVideo'})

const route = useRoute()
const checkedKeys = ref<Array<string | number>>([]);

// 状态
const videoLoaded = ref(false);
const frameInterval = ref(1);
const quality = ref(80);
const processing = ref(false);
const processedFrames = ref(0);
const totalFrames = ref(0);
const zipBlob = ref(null);
const zipSize = ref(0);
const videoDuration = ref(0);
const isShowProgress = ref(false);

const state = reactive({
  isTableMode: false,
  activeKey: '1',
  pushActiveKey: '1',
  historyActiveKey: '1',
  loadVideoUrl: '',
  frameVideoUrl: '',
});

// 请求api时附带参数
const params = {};

let cardListReload = () => {
};

// 获取内部fetch方法;
function getMethod(m: any) {
  cardListReload = m;
}

//删除按钮事件
function handleDel(record) {
  handleDelete(record);
  cardListReload();
}

//详情按钮事件
function handleView(record) {
  openPlayModal(true, {playUrl: record['videoPath']});
}

//编辑按钮事件
function handleEdit(record) {
  openAddModal(true, { datasetId: route.params['id'], isEdit: true, isView: false, record });
}

//视频抽帧
function handleLoadVideo(record) {
  openFrameModal(true, {videoPath: record['videoPath']});
}

function handleSetFrameParamSuccess(record) {
  const {videoPath, videoFrameInterval, videoQuality} = record;
  frameInterval.value = videoFrameInterval;
  quality.value = videoQuality;
  state.loadVideoUrl = videoPath;
  loadMinioVideo(videoPath);
}

//视频抽帧
function handleFrame(record) {
  state.frameVideoUrl = record['videoPath'];
  processFrames(record['videoPath']);
}

const [registerTable, {reload}] = useTable({
  title: '视频数据集列表',
  api: getDatasetVideoPage,
  columns: getBasicColumns(),
  // 添加beforeFetch钩子转换参数
  beforeFetch: (params) => {
    const {...rest} = params;
    rest['datasetId'] = route.params['id'];
    return rest;
  },
  useSearchForm: false,
  showTableSetting: false,
  tableSetting: {fullScreen: true},
  showIndexColumn: false,
  rowKey: 'id',
  fetchSetting: {
    listField: 'list',
    totalField: 'total',
  },
  rowSelection: {
    type: 'checkbox',
    selectedRowKeys: checkedKeys,
    onSelect: onSelect,
    onSelectAll: onSelectAll,
    getCheckboxProps(record) {
      // Demo: 第一行（id为0）的选择框禁用
      if (record.root) {
        return {disabled: true};
      } else {
        return {disabled: false};
      }
    },
  },
});

function onSelect(record, selected) {
  if (selected) {
    checkedKeys.value = [...checkedKeys.value, record.id];
  } else {
    checkedKeys.value = checkedKeys.value.filter((id) => id !== record.id);
  }
  console.log(checkedKeys);
}

function onSelectAll(selected, _, changeRows) {
  const changeIds = changeRows.map((item) => item.id);
  if (selected) {
    checkedKeys.value = [...checkedKeys.value, ...changeIds];
  } else {
    checkedKeys.value = checkedKeys.value.filter((id) => {
      return !changeIds.includes(id);
    });
  }
  console.log(checkedKeys);
}

// 表格刷新
function handleSuccess() {
  cardListReload()
  reload({
    page: 0,
  });
}

// 切换视图
function handleClickSwap() {
  state.isTableMode = !state.isTableMode;
}

const handleDelete = async (record) => {
  try {
    await deleteDatasetVideo(record['id']);
    createMessage.success('删除成功');
    handleSuccess();
  } catch (error) {
    console.error(error)
    createMessage.success('删除失败');
    console.log('handleDelete', error);
  }
};

async function handleDeleteAll() {
  // //console.log('checkedKeys ...', checkedKeys);
  try {
    await Promise.all([deleteDatasetVideo(checkedKeys.value)]);
    createMessage.success('批量删除成功');
  } catch (error) {
    console.error(error)
    //console.log(error);
    createMessage.error('批量删除失败');
  }
  reload();
}

// 计算属性
const progressPercentage = computed(() => {
  if (totalFrames.value === 0) return 0;
  return Math.round((processedFrames.value / totalFrames.value) * 100);
});

const loadMinioVideo = (minioUrl) => {
  videoLoaded.value = false;
  // 创建隐藏的视频元素
  const video = document.createElement('video');
  video.style.display = 'none';

  // 解决跨域问题 - 关键步骤
  video.crossOrigin = "Anonymous";

  document.body.appendChild(video);

  // 设置视频源
  video.src = minioUrl;

  // 静音以便自动播放
  video.muted = true;
  video.playsInline = true;

  video.onloadedmetadata = () => {
    videoDuration.value = video.duration;
    videoLoaded.value = true;
    totalFrames.value = Math.ceil(video.duration / frameInterval.value);
    createMessage.success(`视频加载成功，视频时长：${video.duration.toFixed(1)}秒，预计抽取：${totalFrames.value} 帧`)
    // 移除视频元素
    document.body.removeChild(video);
  };

  video.onerror = (e) => {
    console.info('视频加载失败，请检查URL和访问权限', 'error', 'fas fa-exclamation-triangle');
    console.info(`错误详情: ${e.target.error.message}`, 'error', 'fas fa-bug');
    document.body.removeChild(video);
  };
};

const processFrames = async (minioUrl) => {
  if (!videoLoaded.value || processing.value || state.loadVideoUrl == '') {
    createMessage.warning('抽帧开始前请先加载视频')
    return;
  }
  if (state.loadVideoUrl !== state.frameVideoUrl) {
    createMessage.warning('已加载的视频与抽帧视频不相同，请重新加载视频')
    return;
  }

  isShowProgress.value = true;
  videoLoaded.value = true;
  processing.value = true;
  processedFrames.value = 0;
  zipBlob.value = null;
  zipSize.value = 0;
  console.info('开始处理视频帧...', 'info', 'fas fa-play-circle');

  // 创建隐藏的视频元素
  const video = document.createElement('video');
  video.style.display = 'none';
  document.body.appendChild(video);

  // 设置视频源
  video.src = minioUrl;
  video.muted = true;
  video.playsInline = true;
  video.setAttribute('crossOrigin', 'anonymous');

  // 等待视频加载
  await new Promise((resolve) => {
    video.onloadedmetadata = resolve;
  });

  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');

  // 设置画布尺寸
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;

  // 创建JSZip实例
  const zip = new JSZip();

  try {
    // 按时间点抽帧
    for (let time = 0; time < video.duration; time += frameInterval.value) {
      await extractFrame(video, canvas, ctx, time);
      processedFrames.value++;

      // 转换为Blob
      const blob = await new Promise(resolve => {
        canvas.toBlob(blob => resolve(blob), 'image/jpeg', quality.value / 100);
      });

      // 添加到ZIP
      zip.file(`frame_${time.toFixed(1)}.jpg`, blob);
    }

    // 生成ZIP文件
    const content = await zip.generateAsync({
      type: 'blob',
      compression: 'DEFLATE',
      compressionOptions: {
        level: 6
      }
    });

    zipBlob.value = content;
    zipSize.value = content.size;

    createMessage.success('抽帧处理完成');

    // 自动下载
    setTimeout(downloadZip, 500);
  } catch (error) {
    console.info(`处理出错: ${error.message}`, 'error', 'fas fa-exclamation-circle');
  } finally {
    processing.value = false;
    isShowProgress.value = false;
    // 清理资源
    document.body.removeChild(video);
  }
};

const extractFrame = (video, canvas, ctx, time) => {
  return new Promise((resolve) => {
    video.currentTime = time;

    video.onseeked = () => {
      // 确保视频已准备好
      if (video.readyState < 2) {
        video.oncanplay = () => {
          drawFrame(video, canvas, ctx, time, resolve);
        };
      } else {
        drawFrame(video, canvas, ctx, time, resolve);
      }
    };
  });
};

const drawFrame = (video, canvas, ctx, time, resolve) => {
  // 清除画布并绘制新帧
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

  console.info(`已抽取 ${time.toFixed(1)} 秒帧`, 'info', 'fas fa-image');
  resolve();
};

const downloadZip = () => {
  if (!zipBlob.value) {
    console.info('没有可下载的ZIP文件', 'error', 'fas fa-exclamation-circle');
    return;
  }

  try {
    // 生成文件名
    const fileName = `frames_video_${Date.now()}_${Math.random().toString(36).slice(2, 8)}.zip`
    // 保存文件
    saveAs(zipBlob.value, fileName);
    console.info(`正在下载: ${fileName}`, 'success', 'fas fa-download');
  } catch (error) {
    console.info(`下载失败: ${error.message}`, 'error', 'fas fa-exclamation-circle');
  }
};

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
};
</script>

<style lang="less" scoped>
.device-wrapper {
  :deep(.ant-tabs-nav) {
    padding: 5px 0 0 25px;
  }
}
</style>
