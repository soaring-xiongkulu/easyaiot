<template>
  <BasicDrawer
    v-bind="$attrs"
    @register="register"
    :title="drawerTitle"
    width="1200"
    :maskClosable="true"
    @close="handleClose"
  >
    <div class="service-manage-container">
      <Spin :spinning="loading">
        <Empty v-if="!loading && !taskInfo" description="正在加载任务信息..." />
        <Empty 
          v-else-if="!loading && serviceList.length === 0"
          description="该推流转发任务未关联任何服务" 
        />
        <BasicTable
          v-else
          @register="registerTable"
          :data-source="serviceList"
          :columns="columns"
          :pagination="false"
          :loading="loading"
          row-key="id"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.dataIndex === 'service_name'">
              <div class="service-name-cell">
                <Icon :icon="getServiceIcon(record.service_type)" :size="20"/>
                <span class="service-name">{{ record.service_name }}</span>
              </div>
            </template>
            <template v-else-if="column.dataIndex === 'status'">
              <Tag :color="getStatusColor(record.status)">
                {{ getStatusText(record.status) }}
              </Tag>
            </template>
            <template v-else-if="column.dataIndex === 'server_info'">
              <div class="server-info">
                <div v-if="record.server_ip">
                  <span class="label">服务器:</span>
                  <span>{{ record.server_ip }}</span>
                  <span v-if="record.port">:{{ record.port }}</span>
                </div>
                <div v-if="record.process_id">
                  <span class="label">进程ID:</span>
                  <span>{{ record.process_id }}</span>
                </div>
                <div v-if="record.last_heartbeat">
                  <span class="label">最后心跳:</span>
                  <span>{{ formatDateTime(record.last_heartbeat) }}</span>
                </div>
              </div>
            </template>
            <template v-else-if="column.dataIndex === 'action'">
              <div class="action-buttons">
                <Button
                  type="text"
                  size="small"
                  @click="handleViewLogs(record)"
                  :disabled="!record.log_path"
                  :title="'查看日志'"
                  class="action-btn"
                >
                  <template #icon>
                    <FileTextOutlined/>
                  </template>
                </Button>
                <Button
                  v-if="taskInfo && taskInfo.is_enabled && record.status === 'running'"
                  type="text"
                  size="small"
                  @click="handlePlayStream(record)"
                  :title="'推流播放'"
                  class="action-btn"
                >
                  <template #icon>
                    <VideoCameraOutlined/>
                  </template>
                </Button>
                <Button
                  v-if="record.status === 'running'"
                  type="text"
                  size="small"
                  danger
                  @click="handleStop(record)"
                  :loading="record.actionLoading"
                  :title="'停止服务'"
                  class="action-btn"
                >
                  <template #icon>
                    <PauseCircleOutlined/>
                  </template>
                </Button>
                <Button
                  v-else
                  type="text"
                  size="small"
                  @click="handleStart(record)"
                  :loading="record.actionLoading"
                  :title="'启动服务'"
                  class="action-btn"
                >
                  <template #icon>
                    <PlayCircleOutlined/>
                  </template>
                </Button>
                <Button
                  v-if="record.status === 'running'"
                  type="text"
                  size="small"
                  @click="handleRestart(record)"
                  :loading="record.actionLoading"
                  :title="'重启服务'"
                  class="action-btn"
                >
                  <template #icon>
                    <ReloadOutlined/>
                  </template>
                </Button>
              </div>
            </template>
          </template>
        </BasicTable>
      </Spin>
    </div>

    <!-- 日志查看模态框 -->
    <StreamForwardLogsModal @register="registerLogsModal"/>
    
    <!-- 视频播放模态框 -->
    <DialogPlayer @register="registerPlayerModal" />
  </BasicDrawer>
</template>

<script lang="ts" setup>
import {computed, ref, nextTick} from 'vue';
import {BasicDrawer, useDrawerInner} from '@/components/Drawer';
import {BasicTable, useTable} from '@/components/Table';
import {
  FileTextOutlined,
  PauseCircleOutlined,
  PlayCircleOutlined,
  ReloadOutlined,
  VideoCameraOutlined,
} from '@ant-design/icons-vue';
import {Tag, Button, Empty, Spin} from 'ant-design-vue';
import {Icon} from '@/components/Icon';
import {useMessage} from '@/hooks/web/useMessage';
import {
  type StreamForwardTask,
  getStreamForwardTask,
  getStreamForwardTaskStatus,
  startStreamForwardTask,
  stopStreamForwardTask,
  restartStreamForwardTask,
  getStreamForwardTaskStreams,
} from '@/api/device/stream_forward';
import StreamForwardLogsModal from './StreamForwardLogsModal.vue';
import {useModal} from '@/components/Modal';
import DialogPlayer from '@/components/VideoPlayer/DialogPlayer.vue';

// 摄像头推流信息类型
interface CameraStreamInfo {
  device_id: string;
  device_name: string;
  rtmp_stream?: string;
  http_stream?: string;
  source?: string;
  cover_image_path?: string;
}

defineOptions({name: 'StreamForwardServiceManageDrawer'});

const emit = defineEmits(['close', 'success']);

const {createMessage} = useMessage();
const [registerLogsModal, {openModal: openLogsModal}] = useModal();
const [registerPlayerModal, {openModal: openPlayerModal}] = useModal();

const loading = ref(false);
const taskInfo = ref<StreamForwardTask | null>(null);
const serviceStatusInfo = ref<any>(null);
const cameraStreamsList = ref<CameraStreamInfo[]>([]); // 存储摄像头推流信息列表

const drawerTitle = computed(() => {
  return '推流转发服务管理';
});

// 服务列表
const serviceList = computed(() => {
  const list: any[] = [];

  // 推流转发任务：根据摄像头数量展示多条记录
  if (taskInfo.value) {
    const deviceIds = taskInfo.value.device_ids || [];
    const deviceNames = taskInfo.value.device_names || [];
    // 优先考虑 is_enabled 字段：如果 is_enabled=false，即使服务状态是 running 也应该显示为 stopped
    let status = 'stopped';
    if (taskInfo.value.is_enabled) {
      // is_enabled=true 时，再根据服务状态信息判断
      status = serviceStatusInfo.value 
        ? (serviceStatusInfo.value.status || serviceStatusInfo.value.run_status || 'stopped')
        : 'stopped';
    }
    
    // 为每个摄像头创建一条记录
    deviceIds.forEach((deviceId: string, index: number) => {
      const deviceName = deviceNames[index] || deviceId;
      const cameraStream = cameraStreamsList.value.find(s => s.device_id === deviceId);
      
      const serviceItem = {
        id: `stream_forward_${taskInfo.value!.id}_${deviceId}`,
        service_type: 'stream_forward',
        service_name: deviceName || `摄像头 ${index + 1}`,
        device_id: deviceId,
        device_name: deviceName,
        status: status,
        server_ip: serviceStatusInfo.value?.server_ip,
        port: serviceStatusInfo.value?.port,
        process_id: serviceStatusInfo.value?.process_id,
        last_heartbeat: serviceStatusInfo.value?.last_heartbeat,
        log_path: serviceStatusInfo.value?.log_path,
        total_streams: serviceStatusInfo.value?.total_streams || deviceIds.length,
        rtmp_stream: cameraStream?.rtmp_stream,
        http_stream: cameraStream?.http_stream,
        raw_data: serviceStatusInfo.value,
        actionLoading: false,
      };
      list.push(serviceItem);
    });
  }

  return list;
});

// 表格列定义
const getColumns = () => [
  {
    title: '服务名称',
    dataIndex: 'service_name',
    width: 150,
    fixed: 'left',
  },
  {
    title: '运行状态',
    dataIndex: 'status',
    width: 100,
  },
  {
    title: '服务器IP',
    dataIndex: 'server_ip',
    width: 140,
    customRender: ({text}: { text: string }) => text || '--',
  },
  {
    title: '端口',
    dataIndex: 'port',
    width: 80,
    customRender: ({text}: { text: number }) => text || '--',
  },
  {
    title: '进程ID',
    dataIndex: 'process_id',
    width: 100,
    customRender: ({text}: { text: number }) => text || '--',
  },
  {
    title: '最后心跳',
    dataIndex: 'last_heartbeat',
    width: 180,
    customRender: ({text}: { text: string }) => text ? formatDateTime(text) : '--',
  },
  {
    title: '服务器信息',
    dataIndex: 'server_info',
    width: 280,
  },
  {
    title: '操作',
    dataIndex: 'action',
    width: 180,
    fixed: 'right',
    align: 'center',
  },
];

const columns = getColumns();

// 获取服务图标
const getServiceIcon = (serviceType: string) => {
  const iconMap: Record<string, string> = {
    stream_forward: 'ant-design:thunderbolt-outlined',
  };
  return iconMap[serviceType] || 'ant-design:appstore-outlined';
};

// 获取状态颜色
const getStatusColor = (status: string) => {
  const colorMap: Record<string, string> = {
    running: 'green',
    stopped: 'default',
    error: 'red',
  };
  return colorMap[status] || 'default';
};

// 获取状态文本
const getStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    running: '运行中',
    stopped: '已停止',
    error: '错误',
  };
  return textMap[status] || status;
};

// 格式化时间
const formatDateTime = (dateString: string) => {
  if (!dateString) return '--';
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) {
      return dateString;
    }
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
  } catch (e) {
    return dateString;
  }
};

// 加载服务信息
const loadServiceInfo = async (taskId: number) => {
  loading.value = true;
  try {
    // 并行获取任务详情、服务状态和摄像头推流信息
    const [taskResponse, statusResponse, streamsResponse] = await Promise.all([
      getStreamForwardTask(taskId).catch((err) => {
        console.error('获取任务信息失败', err);
        return null;
      }),
      getStreamForwardTaskStatus(taskId).catch((err) => {
        console.error('获取服务状态失败', err);
        return null;
      }),
      getStreamForwardTaskStreams(taskId).catch((err) => {
        console.error('获取推流地址失败', err);
        return null;
      }),
    ]);

    // 处理任务详情响应
    if (taskResponse) {
      if (taskResponse && typeof taskResponse === 'object' && 'code' in taskResponse) {
        // 如果是完整响应对象（包含 code 字段）
        if (taskResponse.code !== 0) {
          createMessage.error(taskResponse.msg || '获取任务信息失败');
          return;
        }
        taskInfo.value = taskResponse.data;
      } else {
        // 如果直接返回的是数据对象（响应转换器已处理）
        taskInfo.value = taskResponse as StreamForwardTask;
      }
    }

    // 处理服务状态响应
    if (statusResponse) {
      if (statusResponse && typeof statusResponse === 'object' && 'code' in statusResponse) {
        // 完整响应对象
        if (statusResponse.code === 0 && statusResponse.data) {
          serviceStatusInfo.value = statusResponse.data;
        } else {
          console.warn('服务状态响应code不为0:', statusResponse);
        }
      } else {
        // 直接返回的数据对象（响应转换器已处理）
        serviceStatusInfo.value = statusResponse as any;
      }
    } else {
      console.warn('服务状态响应为空');
    }

    // 处理摄像头推流信息响应
    if (streamsResponse) {
      let streams: CameraStreamInfo[] = [];
      if (Array.isArray(streamsResponse)) {
        streams = streamsResponse;
      } else if (streamsResponse && typeof streamsResponse === 'object' && 'code' in streamsResponse) {
        if (streamsResponse.code === 0 && streamsResponse.data && Array.isArray(streamsResponse.data)) {
          streams = streamsResponse.data;
        }
      }
      cameraStreamsList.value = streams;
    }
  } catch (error) {
    console.error('加载服务信息失败', error);
    createMessage.error('加载服务信息失败');
  } finally {
    loading.value = false;
    // 更新表格数据
    await nextTick();
    if (serviceList.value.length > 0) {
      setTableData(serviceList.value);
    }
  }
};

// 查看日志
const handleViewLogs = async (record: any) => {
  if (!taskInfo.value) {
    createMessage.warning('任务信息不存在');
    return;
  }

  openLogsModal(true, {
    title: `${record.service_name} - 日志`,
    taskId: taskInfo.value.id,
  });
};

// 启动服务（通过启动推流转发任务来启动服务）
const handleStart = async (record: any) => {
  if (!taskInfo.value) {
    createMessage.warning('任务信息不存在');
    return;
  }

  // 设置加载状态
  record.actionLoading = true;

  try {
    const response = await startStreamForwardTask(taskInfo.value.id);
    // 处理响应
    let alreadyRunning = false;
    if (response && (response as any).id) {
      // 直接返回的是任务对象，检查 already_running 字段
      alreadyRunning = (response as any).already_running || false;
      if (alreadyRunning) {
        createMessage.warning('任务运行中');
      } else {
        createMessage.success('服务启动成功');
      }
      // 重新加载服务信息（延迟一下，等待服务启动和心跳上报）
      setTimeout(async () => {
        await loadServiceInfo(taskInfo.value!.id);
      }, 2000);
    } else if (response && typeof response === 'object' && 'code' in response) {
      // 完整响应对象
      if ((response as any).code === 0) {
        const data = (response as any).data || response;
        alreadyRunning = data?.already_running || false;
        if (alreadyRunning) {
          createMessage.warning('任务运行中');
        } else {
          createMessage.success('服务启动成功');
        }
        setTimeout(async () => {
          await loadServiceInfo(taskInfo.value!.id);
        }, 2000);
      } else {
        createMessage.error((response as any).msg || '服务启动失败');
      }
    } else {
      createMessage.error('服务启动失败');
    }
  } catch (error: any) {
    console.error('启动服务失败', error);
    createMessage.error(error?.message || '服务启动失败');
  } finally {
    record.actionLoading = false;
  }
};

// 停止服务（通过停止推流转发任务来停止服务）
const handleStop = async (record: any) => {
  if (!taskInfo.value) {
    createMessage.warning('任务信息不存在');
    return;
  }

  // 设置加载状态
  record.actionLoading = true;

  try {
    const response = await stopStreamForwardTask(taskInfo.value.id);
    // 由于 isTransformResponse: true，成功时返回的是任务对象
    if (response && (response as any).id) {
      createMessage.success('服务停止成功');
      // 重新加载服务信息
      await loadServiceInfo(taskInfo.value.id);
    } else if (response && typeof response === 'object' && 'code' in response) {
      // 如果返回的是完整响应对象（包含 code）
      if ((response as any).code === 0) {
        createMessage.success('服务停止成功');
        // 重新加载服务信息
        await loadServiceInfo(taskInfo.value.id);
      } else {
        createMessage.error((response as any).msg || '服务停止失败');
      }
    } else {
      createMessage.error('服务停止失败');
    }
  } catch (error: any) {
    console.error('停止服务失败', error);
    createMessage.error(error?.message || '服务停止失败');
  } finally {
    record.actionLoading = false;
  }
};

// 重启服务（通过重启推流转发任务来重启服务）
const handleRestart = async (record: any) => {
  if (!taskInfo.value) {
    createMessage.warning('任务信息不存在');
    return;
  }

  // 设置加载状态
  record.actionLoading = true;

  try {
    const response = await restartStreamForwardTask(taskInfo.value.id);
    // 由于 isTransformResponse: true，成功时返回的是任务对象
    if (response && (response as any).id) {
      createMessage.success('服务重启成功');
      // 重新加载服务信息
      await loadServiceInfo(taskInfo.value.id);
    } else if (response && typeof response === 'object' && 'code' in response) {
      // 如果返回的是完整响应对象（包含 code）
      if ((response as any).code === 0) {
        createMessage.success('服务重启成功');
        // 重新加载服务信息
        await loadServiceInfo(taskInfo.value.id);
      } else {
        createMessage.error((response as any).msg || '服务重启失败');
      }
    } else {
      createMessage.error('服务重启失败');
    }
  } catch (error: any) {
    console.error('重启服务失败', error);
    createMessage.error(error?.message || '服务重启失败');
  } finally {
    record.actionLoading = false;
  }
};

// 注册表格
const [registerTable, { setTableData }] = useTable({
  title: '',
  columns: columns,
  pagination: false,
  showIndexColumn: false,
  canResize: false,
  useSearchForm: false,
  showTableSetting: false,
  immediate: false,
  api: async () => {
    return {
      list: serviceList.value,
      total: serviceList.value.length,
    };
  },
});

// 处理抽屉关闭事件
const handleClose = () => {
  emit('close');
  emit('success');
};

// 播放推流
const handlePlayStream = async (record: any) => {
  if (!taskInfo.value || !taskInfo.value.is_enabled) {
    createMessage.warning('任务未运行，无法播放推流');
    return;
  }
  
  if (!record.device_id) {
    createMessage.warning('该记录未关联摄像头');
    return;
  }
  
  try {
    // 查找当前记录对应的摄像头推流信息
    const cameraStream = cameraStreamsList.value.find(s => s.device_id === record.device_id);
    
    if (cameraStream && (cameraStream.rtmp_stream || cameraStream.http_stream)) {
      // 直接播放当前摄像头的推流
      playCameraStream(cameraStream);
    } else {
      createMessage.warning(`摄像头 ${record.device_name || record.device_id} 暂无推流地址`);
    }
  } catch (error) {
    console.error('播放推流失败', error);
    createMessage.error('播放推流失败');
  }
};

// 将RTMP地址转换为HTTP FLV地址
const convertRtmpToHttp = (rtmpUrl: string): string | null => {
  if (!rtmpUrl || !rtmpUrl.startsWith('rtmp://')) {
    return null;
  }
  
  try {
    // 解析RTMP地址：rtmp://server:port/path
    const url = new URL(rtmpUrl);
    const server = url.hostname;
    const port = url.port || '1935';
    let path = url.pathname.substring(1); // 去掉开头的 /
    
    // 如果路径为空，使用默认路径
    if (!path) {
      path = 'live';
    }
    
    // 添加.flv后缀（如果还没有）
    if (!path.endsWith('.flv')) {
      path = `${path}.flv`;
    }
    
    // 生成HTTP FLV地址（默认使用8080端口）
    return `http://${server}:8080/${path}`;
  } catch (error) {
    console.error('RTMP地址转换失败:', error);
    return null;
  }
};

// 播放摄像头推流
const playCameraStream = (stream: CameraStreamInfo) => {
  // 优先使用RTMP地址，转换为HTTP地址
  // 其次使用已有的HTTP地址
  let httpStream: string | null = null;
  
  // 1. 优先使用RTMP地址
  if (stream.rtmp_stream) {
    httpStream = convertRtmpToHttp(stream.rtmp_stream);
  }
  
  // 2. 如果没有，使用HTTP地址
  if (!httpStream && stream.http_stream) {
    httpStream = stream.http_stream;
  }
  
  if (!httpStream) {
    createMessage.warning(`摄像头 ${stream.device_name} 暂无推流地址`);
    return;
  }
  
  // 打开播放器
  openPlayerModal(true, {
    id: stream.device_id,
    http_stream: httpStream,
  });
};

// 注册抽屉
const [register] = useDrawerInner(async (data) => {
  // 重置状态
  taskInfo.value = null;
  serviceStatusInfo.value = null;
  cameraStreamsList.value = [];

  if (data && data.taskId) {
    await loadServiceInfo(data.taskId);
  }
});
</script>

<style lang="less" scoped>
.service-manage-container {
  padding: 16px;
  min-height: 200px;
  background: #ffffff;

  :deep(.ant-table) {
    background: #ffffff;
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid #e8e8e8;

    .ant-table-thead > tr > th {
      background-color: #fafafa;
      font-weight: 500;
      padding: 12px 16px;
      color: #262626;
      border-bottom: 1px solid #e8e8e8;
    }

    .ant-table-tbody > tr > td {
      padding: 12px 16px;
      border-bottom: 1px solid #f0f0f0;
      color: #595959;
    }

    .ant-table-tbody > tr:hover > td {
      background-color: #f5f5f5;
    }

    .ant-table-tbody > tr:last-child > td {
      border-bottom: none;
    }
  }

  .service-name-cell {
    display: flex;
    align-items: center;
    gap: 8px;

    .service-name {
      font-weight: 500;
      color: #262626;
      font-size: 14px;
    }
  }

  .server-info {
    font-size: 12px;
    color: #595959;
    line-height: 1.6;

    .label {
      color: #8c8c8c;
      margin-right: 4px;
      font-weight: 400;
    }

    > div {
      margin-bottom: 4px;

      &:last-child {
        margin-bottom: 0;
      }
    }
  }

  .action-buttons {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 4px;

    .action-btn {
      padding: 4px 8px;
      min-width: 28px;
      height: 28px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 4px;
      transition: all 0.2s;
      color: #595959;

      &:hover:not(:disabled) {
        background-color: #f0f0f0;
        color: #262626;
      }

      &:disabled {
        opacity: 0.4;
        cursor: not-allowed;
      }

      .anticon {
        font-size: 16px;
      }
    }
  }

  // Tag样式优化
  :deep(.ant-tag) {
    border-radius: 6px;
    font-size: 12px;
    padding: 2px 10px;
    height: 24px;
    line-height: 20px;
    border: none;
    font-weight: 500;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  }
}
</style>
