<template>
  <div class="camera-container">
    <div class="camera-tab">
      <Tabs
        :activeKey="state.activeKey"
        :animated="{ inkBar: true, tabPane: true }"
        :tabBarGutter="60"
        @tabClick="handleTabClick"
      >
        <TabPane key="1" tab="设备列表">
          <!-- 列表模式 -->
          <BasicTable v-if="viewMode === 'table'" @register="registerTable">
            <template #toolbar>
              <div class="device-list-toolbar">
                <div class="toolbar-left">
                  <a-button type="primary" @click="handleScanOnvif">
                    <template #icon>
                      <ScanOutlined/>
                    </template>
                    扫描局域网ONVIF设备
                  </a-button>
                  <a-button @click="openAddModal('source')">
                    <template #icon>
                      <VideoCameraAddOutlined/>
                    </template>
                    新增视频源设备
                  </a-button>
                  <a-button @click="handleUpdateOnvifDevice">
                    <template #icon>
                      <SyncOutlined/>
                    </template>
                    更新ONVIF设备
                  </a-button>
                </div>
                <div class="toolbar-right">
                  <a-button @click="handleToggleViewMode" type="default">
                    <template #icon>
                      <SwapOutlined />
                    </template>
                    切换视图
                  </a-button>
                </div>
              </div>
            </template>
            <template #bodyCell="{ column, record }">
              <!-- 统一复制功能组件 -->
              <template
                v-if="['id', 'name', 'model', 'source', 'rtmp_stream', 'http_stream'].includes(column.key)">
          <span style="cursor: pointer" @click="handleCopy(record[column.key])"><Icon
            icon="tdesign:copy-filled" color="#4287FCFF"/> {{ record[column.key] }}</span>
              </template>

              <!-- 流媒体状态显示 -->
              <template v-else-if="column.dataIndex === 'stream_status'">
                <a-tag :color="getStreamStatusColor(record.stream_status)">
                  {{ getStreamStatusText(record.stream_status) }}
                </a-tag>
              </template>

              <template v-else-if="column.dataIndex === 'action'">
                <TableAction
                  :actions="getTableActions(record)"
                />
              </template>
            </template>
          </BasicTable>

          <!-- 卡片模式 -->
          <div v-else class="card-mode-wrapper">
            <VideoCardList
              ref="videoCardListRef"
              :api="getDeviceList"
              :params="{}"
              @view="handleCardView"
              @edit="handleCardEdit"
              @delete="handleCardDelete"
              @play="handleCardPlay"
              @toggleStream="handleCardToggleStream"
            >
              <template #toolbar>
                <div class="device-list-toolbar">
                  <div class="toolbar-left">
                    <a-button type="primary" @click="handleScanOnvif">
                      <template #icon>
                        <ScanOutlined/>
                      </template>
                      扫描局域网ONVIF设备
                    </a-button>
                    <a-button @click="openAddModal('source')">
                      <template #icon>
                        <VideoCameraAddOutlined/>
                      </template>
                      新增视频源设备
                    </a-button>
                    <a-button @click="handleUpdateOnvifDevice">
                      <template #icon>
                        <SyncOutlined/>
                      </template>
                      更新ONVIF设备
                    </a-button>
                  </div>
                  <div class="toolbar-right">
                    <a-button @click="handleToggleViewMode" type="default">
                      <template #icon>
                        <SwapOutlined />
                      </template>
                      切换视图
                    </a-button>
                  </div>
                </div>
              </template>
            </VideoCardList>
          </div>

          <DialogPlayer title="视频播放" @register="registerPlayerAddModel"
                        @success="handlePlayerSuccess"/>
          <VideoModal @register="registerAddModel" @success="handleSuccess"/>
        </TabPane>
        <TabPane key="2" tab="设备目录">
          <DirectoryManage
            ref="directoryManageRef"
            @view="handleCardView"
            @edit="handleCardEdit"
            @delete="handleCardDelete"
            @play="handleCardPlay"
            @toggleStream="handleCardToggleStream"
          />
        </TabPane>
        <TabPane key="3" tab="抓拍空间">
          <SnapSpace/>
        </TabPane>
        <TabPane key="4" tab="监控录像">
          <PlaybackList/>
        </TabPane>
        <TabPane key="5" tab="算法任务">
          <SnapTask/>
        </TabPane>
      </Tabs>
    </div>
  </div>
</template>

<script lang="ts" setup>
import {onMounted, onUnmounted, reactive, ref} from 'vue';
import {useRoute} from 'vue-router';
import {TabPane, Tabs} from 'ant-design-vue';
import {BasicTable, TableAction, useTable} from '@/components/Table';
import {useMessage} from '@/hooks/web/useMessage';
import {getBasicColumns, getFormConfig} from "./Data";
import {useModal} from "@/components/Modal";
import VideoModal from "./components/VideoModal/index.vue";
import {
  deleteDevice,
  DeviceInfo,
  getDeviceList,
  getStreamStatus,
  refreshDevices,
  startStreamForwarding,
  stopStreamForwarding,
  StreamStatusResponse
} from '@/api/device/camera';
import {ScanOutlined, SyncOutlined, VideoCameraAddOutlined, SwapOutlined} from '@ant-design/icons-vue';
import DialogPlayer from "@/components/VideoPlayer/DialogPlayer.vue";
import DirectoryManage from "./components/DirectoryManage/index.vue";
import SnapSpace from "./components/SnapSpace/index.vue";
import SnapTask from "./components/SnapTask/index.vue";
import PlaybackList from "./components/PlaybackList/index.vue";
import VideoCardList from "./components/VideoCardList/index.vue";

defineOptions({name: 'CAMERA'})

const route = useRoute();

const {createMessage} = useMessage();
const [registerAddModel, {openModal}] = useModal();

const [registerPlayerAddModel, {openModal: openPlayerAddModel}] = useModal();

// Tab状态
const state = reactive({
  activeKey: '1'
});

// 视图模式（默认卡片模式）
const viewMode = ref<'table' | 'card'>('card');

// 目录管理组件引用
const directoryManageRef = ref();

// 视频卡片列表组件引用
const videoCardListRef = ref();

// Tab切换
const handleTabClick = (activeKey: string) => {
  state.activeKey = activeKey;
};

// 切换视图模式
const handleToggleViewMode = () => {
  viewMode.value = viewMode.value === 'table' ? 'card' : 'table';
  if (viewMode.value === 'card' && videoCardListRef.value) {
    // 切换到卡片模式时刷新卡片列表
    videoCardListRef.value.fetch();
  }
};

// 设备流状态映射
const deviceStreamStatuses = ref<Record<string, string>>({});
// 状态检查定时器
const statusCheckTimer = ref<NodeJS.Timeout | null>(null);

// 获取流状态文本
const getStreamStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'running': '运行中',
    'stopped': '已停止',
    'error': '错误',
    'unknown': '未知'
  };
  return statusMap[status] || status;
};

// 获取流状态颜色
const getStreamStatusColor = (status: string) => {
  const colorMap: Record<string, string> = {
    'running': 'green',
    'stopped': 'red',
    'error': 'orange',
    'unknown': 'default'
  };
  return colorMap[status] || 'default';
};

// 检查单个设备的流状态
const checkDeviceStreamStatus = async (deviceId: string) => {
  try {
    // 确保 deviceStreamStatuses.value 始终是一个对象
    if (!deviceStreamStatuses.value) {
      deviceStreamStatuses.value = {};
    }
    const response: StreamStatusResponse = await getStreamStatus(deviceId);
    if (response.code === 0) {
      deviceStreamStatuses.value[deviceId] = response.data.status;
    } else {
      deviceStreamStatuses.value[deviceId] = 'error';
    }
  } catch (error) {
    console.error(`检查设备 ${deviceId} 流状态失败`, error);
    // 确保 deviceStreamStatuses.value 始终是一个对象
    if (!deviceStreamStatuses.value) {
      deviceStreamStatuses.value = {};
    }
    deviceStreamStatuses.value[deviceId] = 'error';
  }
};

// 检查所有设备的流状态
const checkAllDevicesStreamStatus = async (devices: DeviceInfo[]) => {
  try {
    const deviceIds = devices.map(device => device.id);
    for (const deviceId of deviceIds) {
      await checkDeviceStreamStatus(deviceId);
    }
  } catch (error) {
    console.error('检查设备流状态失败', error);
  }
};

const [registerTable, {reload}] = useTable({
  canResize: true,
  showIndexColumn: false,
  title: '摄像头列表',
  api: getDeviceList,
  columns: getBasicColumns(),
  useSearchForm: true,
  showTableSetting: false,
  pagination: true,
  formConfig: getFormConfig(),
  fetchSetting: {
    listField: 'data',
    totalField: 'total',
  },
  rowKey: 'id',
  // 添加成功回调，获取设备流状态
  onSuccess: (data) => {
    if (data && data.data) {
      // 确保 deviceStreamStatuses.value 始终是一个对象
      if (!deviceStreamStatuses.value) {
        deviceStreamStatuses.value = {};
      }
      // 初始化设备流状态
      data.data.forEach((device: DeviceInfo) => {
        if (!deviceStreamStatuses.value[device.id]) {
          deviceStreamStatuses.value[device.id] = 'unknown';
        }
      });

      // 开始检查设备流状态
      checkAllDevicesStreamStatus(data.data);
    }
  }
});

// 启动状态检查定时器
const startStatusCheckTimer = () => {
  if (statusCheckTimer.value) {
    clearInterval(statusCheckTimer.value);
  }

  statusCheckTimer.value = setInterval(() => {
    if (Object.keys(deviceStreamStatuses.value).length > 0) {
      Object.keys(deviceStreamStatuses.value).forEach(deviceId => {
        checkDeviceStreamStatus(deviceId);
      });
    }
  }, 10000); // 每10秒检查一次
};

// 获取表格操作按钮
const getTableActions = (record) => {
  const actions = [
    {
      icon: 'octicon:play-16',
      tooltip: '播放RTMP流',
      onClick: () => handlePlay(record)
    },
    {
      icon: 'ant-design:eye-filled',
      tooltip: '详情',
      onClick: () => openAddModal('view', record)
    },
    {
      icon: 'ant-design:edit-filled',
      tooltip: '编辑',
      onClick: () => openAddModal('edit', record)
    },
    {
      icon: 'material-symbols:delete-outline-rounded',
      tooltip: '删除',
      popConfirm: {
        title: '确定删除此设备？',
        confirm: () => handleDelete(record)
      }
    }
  ];

  // 根据流状态添加不同的操作按钮
  const currentStatus = (deviceStreamStatuses.value && deviceStreamStatuses.value[record.id]) || 'unknown';

  if (currentStatus === 'running') {
    actions.splice(1, 0, {
      icon: 'ant-design:pause-circle-outlined',
      tooltip: '停止RTSP转发',
      onClick: () => handleDisableRtsp(record)
    });
  } else {
    actions.splice(1, 0, {
      icon: 'ant-design:swap-outline',
      tooltip: '启用RTSP转发',
      onClick: () => handleEnableRtsp(record)
    });
  }

  return actions;
};

// 启用RTSP转发
const handleEnableRtsp = async (record) => {
  try {
    // 确保 deviceStreamStatuses.value 始终是一个对象
    if (!deviceStreamStatuses.value) {
      deviceStreamStatuses.value = {};
    }
    createMessage.loading({content: '正在启动RTSP转发...', key: 'rtsp'});

    const response = await startStreamForwarding(record.id);
    if (response.code === 0) {
      createMessage.success({content: 'RTSP转发已启动', key: 'rtsp'});
      // 更新设备状态
      deviceStreamStatuses.value[record.id] = 'running';
      // 更新卡片列表中的流状态
      if (videoCardListRef.value && videoCardListRef.value.deviceStreamStatuses) {
        videoCardListRef.value.deviceStreamStatuses[record.id] = 'running';
      }
      // 重新加载数据
      handleSuccess();
    } else {
      createMessage.error({content: `启动失败: ${response.data.msg}`, key: 'rtsp'});
      deviceStreamStatuses.value[record.id] = 'error';
    }
  } catch (error) {
    console.error('启动RTSP转发失败', error);
    createMessage.error({content: '启动RTSP转发失败', key: 'rtsp'});
    // 确保 deviceStreamStatuses.value 始终是一个对象
    if (!deviceStreamStatuses.value) {
      deviceStreamStatuses.value = {};
    }
    deviceStreamStatuses.value[record.id] = 'error';
  }
};

// 表格刷新
function handlePlayerSuccess() {
}

// 停止RTSP转发
const handleDisableRtsp = async (record) => {
  try {
    // 确保 deviceStreamStatuses.value 始终是一个对象
    if (!deviceStreamStatuses.value) {
      deviceStreamStatuses.value = {};
    }
    createMessage.loading({content: '正在停止RTSP转发...', key: 'rtsp'});

    const response = await stopStreamForwarding(record.id);
    if (response.code === 0) {
      createMessage.success({content: 'RTSP转发已停止', key: 'rtsp'});
      // 更新设备状态
      deviceStreamStatuses.value[record.id] = 'stopped';
      // 更新卡片列表中的流状态
      if (videoCardListRef.value && videoCardListRef.value.deviceStreamStatuses) {
        videoCardListRef.value.deviceStreamStatuses[record.id] = 'stopped';
      }
      // 重新加载数据
      handleSuccess();
    } else {
      createMessage.error({content: `停止失败: ${response.data.msg}`, key: 'rtsp'});
      deviceStreamStatuses.value[record.id] = 'error';
    }
  } catch (error) {
    console.error('停止RTSP转发失败', error);
    createMessage.error({content: '停止RTSP转发失败', key: 'rtsp'});
    // 确保 deviceStreamStatuses.value 始终是一个对象
    if (!deviceStreamStatuses.value) {
      deviceStreamStatuses.value = {};
    }
    deviceStreamStatuses.value[record.id] = 'error';
  }
};

//播放RTMP
function handlePlay(record) {
  openPlayerAddModel(true, record)
}

async function handleCopy(text: string) {
  if (navigator.clipboard) {
    await navigator.clipboard.writeText(text);
  } else {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
  }
  createMessage.success('复制成功');
}

// 打开模态框
const openAddModal = (type, record = null) => {
  openModal(true, {
    type,
    record,
    isEdit: type === 'edit',
    isView: type === 'view'
  });
};

// 扫描ONVIF设备
const handleScanOnvif = () => {
  openAddModal('onvif');
};

// 刷新数据
const handleSuccess = () => {
  if (viewMode.value === 'table') {
    reload();
  } else if (videoCardListRef.value) {
    videoCardListRef.value.fetch();
  }
};

// 删除设备
const handleDelete = async (record) => {
  try {
    await deleteDevice(record.id);
    createMessage.success('删除成功');
    handleSuccess();
  } catch (error) {
    console.error('删除失败', error);
    createMessage.error('删除失败');
  }
};

// 更新ONVIF设备
const handleUpdateOnvifDevice = async () => {
  try {
    await refreshDevices();
    createMessage.success('ONVIF设备更新成功');
    handleSuccess();
  } catch (error) {
    console.error('ONVIF设备更新失败', error);
    createMessage.error('ONVIF设备更新失败');
  }
};

// 卡片视图事件处理
const handleCardView = (record) => {
  openAddModal('view', record);
};

const handleCardEdit = (record) => {
  openAddModal('edit', record);
};

const handleCardDelete = async (record) => {
  await handleDelete(record);
};

const handleCardPlay = (record) => {
  handlePlay(record);
};

const handleCardToggleStream = async (record) => {
  const currentStatus = (deviceStreamStatuses.value && deviceStreamStatuses.value[record.id]) || 'unknown';
  if (currentStatus === 'running') {
    await handleDisableRtsp(record);
  } else {
    await handleEnableRtsp(record);
  }
  // 刷新卡片列表
  if (videoCardListRef.value) {
    videoCardListRef.value.fetch();
  }
};


// 组件挂载时启动状态检查定时器
onMounted(() => {
  startStatusCheckTimer();
  // 处理路由参数，自动切换到指定tab
  const tab = route.query.tab as string;
  if (tab) {
    state.activeKey = tab;
  }
});

// 组件卸载时清除定时器
onUnmounted(() => {
  if (statusCheckTimer.value) {
    clearInterval(statusCheckTimer.value);
    statusCheckTimer.value = null;
  }
});
</script>

<style lang="less" scoped>
.camera-container {
  :deep(.ant-form-item) {
    margin-bottom: 10px;
  }

  .camera-tab {
    padding: 16px 19px 0 15px;

    :deep(.ant-tabs-nav) {
      padding: 5px 0 0 25px;
    }

    :deep(.ant-tabs) {
      background-color: #FFFFFF;

      :deep(.ant-tabs-nav) {
        padding: 5px 0 0 25px;
      }
    }
  }

  .device-list-toolbar {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    gap: 8px;
    margin-bottom: 0;
    padding: 0;

    .toolbar-left {
      display: flex;
      gap: 8px;
    }

    .toolbar-right {
      display: flex;
      gap: 8px;
    }
  }

  // 列表模式：按钮在搜索表单下方
  :deep(.vben-basic-table) {
    .vben-basic-table-form-container {
      .device-list-toolbar {
        margin-bottom: 12px;
        padding: 0 4px;
      }
    }
  }

  // 卡片模式：按钮在搜索表单下方
  .card-mode-wrapper {
    .device-list-toolbar {
      padding: 12px 16px;
      margin-bottom: 0;
    }
  }
}
</style>
