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
          :description="`该算法任务未关联任何服务 (任务类型: ${taskInfo?.task_type || '未知'}, 服务列表长度: ${serviceList.length})`" 
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
            <template v-if="column.dataIndex === 'status'">
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
                  :disabled="!record.log_path && record.service_type !== 'realtime' && record.service_type !== 'snap'"
                  :title="'查看日志'"
                  class="action-btn"
                >
                  <template #icon>
                    <FileTextOutlined/>
                  </template>
                </Button>
                <Button
                  v-if="taskInfo && taskInfo.task_type === 'snap' && record.service_type === 'snap'"
                  type="text"
                  size="small"
                  @click="handleViewSnapSpaces(record)"
                  :title="'查看抓拍空间'"
                  class="action-btn"
                >
                  <template #icon>
                    <FolderOutlined/>
                  </template>
                </Button>
                <Button
                  v-if="taskInfo && taskInfo.is_enabled && record.status === 'running' && taskInfo.task_type === 'realtime'"
                  type="text"
                  size="small"
                  @click="handlePlayStream"
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
    <ServiceLogsModal @register="registerLogsModal"/>
    
    <!-- 视频播放模态框 -->
    <DialogPlayer @register="registerPlayerModal" />
    
    <!-- 抓拍空间查看模态框 -->
    <BasicModal
      v-model:open="snapSpacesVisible"
      title="查看抓拍空间"
      width="1000px"
      :footer="null"
    >
      <div v-if="snapSpacesLoading" style="text-align: center; padding: 40px;">
        <Spin />
      </div>
      <div v-else-if="snapSpacesList.length === 0" style="text-align: center; padding: 40px;">
        <Empty description="暂无抓拍空间" />
      </div>
      <div v-else class="snap-spaces-list">
        <div 
          v-for="item in snapSpacesList" 
          :key="item.device_id"
          class="snap-space-item"
        >
          <div class="device-info">
            <span class="device-name">{{ item.device_name || item.device_id }}</span>
            <span class="device-id">({{ item.device_id }})</span>
          </div>
          <div class="space-info" v-if="item.space">
            <span class="space-name">{{ item.space.space_name }}</span>
            <Button 
              type="primary" 
              size="small"
              @click="handleViewSnapImages(item.space.id, item.device_id, item.device_name)"
            >
              查看抓拍空间
            </Button>
          </div>
          <div v-else class="no-space">
            <span style="color: #999;">暂无抓拍空间</span>
          </div>
        </div>
      </div>
    </BasicModal>
    
    <!-- 抓拍图片查看模态框 -->
    <SnapImageModal @register="registerSnapImageModal"/>
    
    <!-- 摄像头选择模态框 -->
    <BasicModal
      v-model:open="cameraSelectVisible"
      title="选择摄像头"
      @ok="handleConfirmCamera"
      @cancel="cameraSelectVisible = false"
    >
      <div v-if="cameraStreams.length === 0" style="text-align: center; padding: 20px;">
        <Empty description="暂无可用推流地址" />
      </div>
      <RadioGroup v-else v-model:value="selectedCameraIndex" style="width: 100%;">
        <Radio
          v-for="(stream, index) in cameraStreams"
          :key="stream.device_id"
          :value="index"
          style="display: block; margin-bottom: 12px;"
        >
          <div>
            <div style="font-weight: 500;">{{ stream.device_name }}</div>
            <div style="font-size: 12px; color: #999; margin-top: 4px;">
              {{ stream.pusher_http_url || stream.http_stream || stream.pusher_rtmp_url || stream.rtmp_stream || '无推流地址' }}
            </div>
          </div>
        </Radio>
      </RadioGroup>
    </BasicModal>
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
  FolderOutlined,
} from '@ant-design/icons-vue';
import {Tag, Button, Empty, Spin, RadioGroup, Radio} from 'ant-design-vue';
import {Icon} from '@/components/Icon';
import {useMessage} from '@/hooks/web/useMessage';
import {
  type AlgorithmTask,
  type FrameExtractor,
  getAlgorithmTask,
  getFrameExtractor,
  getPusher,
  getSorter,
  getTaskServicesStatus,
  getTaskStreams,
  type Pusher,
  type RealtimeServiceStatus,
  restartAlgorithmTask,
  type Sorter,
  startAlgorithmTask,
  stopAlgorithmTask,
  type CameraStreamInfo,
} from '@/api/device/algorithm_task';
import ServiceLogsModal from './ServiceLogsModal.vue';
import {useModal} from '@/components/Modal';
import {BasicModal} from '@/components/Modal';
import DialogPlayer from '@/components/VideoPlayer/DialogPlayer.vue';
import SnapImageModal from '@/views/camera/components/SnapSpace/SnapImageModal.vue';
import {getSnapSpaceByDeviceId, type SnapSpace} from '@/api/device/snap';

defineOptions({name: 'ServiceManageDrawer'});

const emit = defineEmits(['close', 'success']);

const {createMessage} = useMessage();
const [registerLogsModal, {openModal: openLogsModal}] = useModal();
const [registerPlayerModal, {openModal: openPlayerModal}] = useModal();
const [registerSnapImageModal, {openModal: openSnapImageModal}] = useModal();

// 摄像头选择和播放相关
const cameraSelectVisible = ref(false);
const cameraStreams = ref<CameraStreamInfo[]>([]);
const selectedCameraIndex = ref<number>(0);

// 抓拍空间相关
const snapSpacesVisible = ref(false);
const snapSpacesLoading = ref(false);
const snapSpacesList = ref<Array<{
  device_id: string;
  device_name?: string;
  space: SnapSpace | null;
}>>([]);

const loading = ref(false);
const taskInfo = ref<AlgorithmTask | null>(null);
const extractorInfo = ref<FrameExtractor | null>(null);
const sorterInfo = ref<Sorter | null>(null);
const pusherInfo = ref<Pusher | null>(null);
const realtimeServiceInfo = ref<RealtimeServiceStatus | null>(null);
const snapServiceInfo = ref<RealtimeServiceStatus | null>(null);

const drawerTitle = computed(() => {
  return '帧管道管理器';
});

// 服务列表
const serviceList = computed(() => {
  const list: any[] = [];

  console.log('计算服务列表 - taskInfo:', taskInfo.value);
  console.log('计算服务列表 - realtimeServiceInfo:', realtimeServiceInfo.value);

  // 实时算法任务：显示统一服务（即使服务状态为空也显示）
  if (taskInfo.value && taskInfo.value.task_type === 'realtime') {
    // 获取关联的设备名称（多个设备用逗号分隔）
    const deviceNames = taskInfo.value.device_names || [];
    const deviceNameStr = deviceNames.length > 0 ? deviceNames.join(', ') : undefined;
    
    // 总是显示实时算法服务，即使服务状态信息为空
    if (realtimeServiceInfo.value) {
      // 有服务状态信息
      const serviceItem = {
        id: `realtime_${taskInfo.value.id}`,
        service_type: 'realtime',
        service_name: '实时算法服务',
        device_name: deviceNameStr,
        status: realtimeServiceInfo.value.status || realtimeServiceInfo.value.run_status || 'stopped',
        server_ip: realtimeServiceInfo.value.server_ip,
        port: realtimeServiceInfo.value.port,
        process_id: realtimeServiceInfo.value.process_id,
        last_heartbeat: realtimeServiceInfo.value.last_heartbeat,
        log_path: realtimeServiceInfo.value.log_path,
        raw_data: realtimeServiceInfo.value,
        actionLoading: false,
      };
      console.log('添加实时服务项:', serviceItem);
      list.push(serviceItem);
    } else {
      // 没有服务状态信息，显示默认项（服务未启动）
      const defaultItem = {
        id: `realtime_${taskInfo.value.id}`,
        service_type: 'realtime',
        service_name: '实时算法服务',
        device_name: deviceNameStr,
        status: 'stopped',
        server_ip: undefined,
        port: undefined,
        process_id: undefined,
        last_heartbeat: undefined,
        log_path: undefined,
        raw_data: null,
        actionLoading: false,
      };
      console.log('添加默认实时服务项:', defaultItem);
      list.push(defaultItem);
    }
  }

  // 抓拍算法任务：为每个关联的设备显示一条服务记录
  if (taskInfo.value && taskInfo.value.task_type === 'snap') {
    // 获取关联的设备列表
    const deviceIds = taskInfo.value.device_ids || [];
    const deviceNames = taskInfo.value.device_names || [];
    
    if (deviceIds.length > 0) {
      // 为每个设备创建一条服务记录
      deviceIds.forEach((deviceId: string, index: number) => {
        const deviceName = deviceNames[index] || deviceId;
        
    if (snapServiceInfo.value) {
      // 有服务状态信息
      const serviceItem = {
            id: `snap_${taskInfo.value.id}_${deviceId}`,
        service_type: 'snap',
            service_name: `抓拍算法服务 - ${deviceName}`,
            device_id: deviceId,
            device_name: deviceName,
        status: snapServiceInfo.value.status || snapServiceInfo.value.run_status || 'stopped',
        server_ip: snapServiceInfo.value.server_ip,
        port: snapServiceInfo.value.port,
        process_id: snapServiceInfo.value.process_id,
        last_heartbeat: snapServiceInfo.value.last_heartbeat,
        log_path: snapServiceInfo.value.log_path,
        raw_data: snapServiceInfo.value,
        actionLoading: false,
      };
      console.log('添加抓拍服务项:', serviceItem);
      list.push(serviceItem);
    } else {
      // 没有服务状态信息，显示默认项（服务未启动）
          const defaultItem = {
            id: `snap_${taskInfo.value.id}_${deviceId}`,
            service_type: 'snap',
            service_name: `抓拍算法服务 - ${deviceName}`,
            device_id: deviceId,
            device_name: deviceName,
            status: 'stopped',
            server_ip: undefined,
            port: undefined,
            process_id: undefined,
            last_heartbeat: undefined,
            log_path: undefined,
            raw_data: null,
            actionLoading: false,
          };
          console.log('添加默认抓拍服务项:', defaultItem);
          list.push(defaultItem);
        }
      });
    } else {
      // 没有关联设备，显示一条默认记录
      if (snapServiceInfo.value) {
        const serviceItem = {
          id: `snap_${taskInfo.value.id}`,
          service_type: 'snap',
          service_name: '抓拍算法服务',
          status: snapServiceInfo.value.status || snapServiceInfo.value.run_status || 'stopped',
          server_ip: snapServiceInfo.value.server_ip,
          port: snapServiceInfo.value.port,
          process_id: snapServiceInfo.value.process_id,
          last_heartbeat: snapServiceInfo.value.last_heartbeat,
          log_path: snapServiceInfo.value.log_path,
          raw_data: snapServiceInfo.value,
          actionLoading: false,
        };
        console.log('添加抓拍服务项（无设备）:', serviceItem);
        list.push(serviceItem);
      } else {
      const defaultItem = {
        id: `snap_${taskInfo.value.id}`,
        service_type: 'snap',
        service_name: '抓拍算法服务',
        status: 'stopped',
        server_ip: undefined,
        port: undefined,
        process_id: undefined,
        last_heartbeat: undefined,
        log_path: undefined,
        raw_data: null,
        actionLoading: false,
      };
        console.log('添加默认抓拍服务项（无设备）:', defaultItem);
      list.push(defaultItem);
      }
    }
  }

  // 添加算法模型服务（兼容旧版本）
  if (taskInfo.value && taskInfo.value.algorithm_services && Array.isArray(taskInfo.value.algorithm_services)) {
    taskInfo.value.algorithm_services.forEach((service: any) => {
      let server_ip: string | undefined;
      let port: string | undefined;

      // 尝试解析服务 URL
      if (service.service_url) {
        try {
          const url = new URL(service.service_url);
          server_ip = url.hostname;
          port = url.port || (url.protocol === 'https:' ? '443' : '80');
        } catch (e) {
          // URL 解析失败，尝试从字符串中提取
          const match = service.service_url.match(/https?:\/\/([^:]+)(?::(\d+))?/);
          if (match) {
            server_ip = match[1];
            port = match[2] || (service.service_url.includes('https') ? '443' : '80');
          }
        }
      }

      list.push({
        id: `algorithm_${service.id}`,
        service_type: 'algorithm',
        service_name: service.service_name || '算法服务',
        status: service.is_enabled ? 'running' : 'stopped',
        server_ip,
        port,
        process_id: undefined,
        last_heartbeat: undefined,
        log_path: undefined,
        raw_data: service,
        actionLoading: false,
      });
    });
  }

  console.log('最终服务列表:', list);
  return list;
});

// 表格列定义
const getColumns = () => [
  {
    title: '摄像头',
    dataIndex: 'device_name',
    width: 150,
    fixed: 'left',
    customRender: ({text}: { text: string }) => text || '--',
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
    width: 220,
  },
  {
    title: '操作',
    dataIndex: 'action',
    width: 140,
    fixed: 'right',
    align: 'center',
  },
];

const columns = getColumns();

// 获取服务图标
const getServiceIcon = (serviceType: string) => {
  const iconMap: Record<string, string> = {
    realtime: 'ant-design:thunderbolt-outlined',
    snap: 'ant-design:camera-outlined',
    algorithm: 'ant-design:robot-outlined',
    extractor: 'ant-design:file-image-outlined',
    sorter: 'ant-design:sort-ascending-outlined',
    pusher: 'ant-design:send-outlined',
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
    // 并行获取任务详情和服务状态
    const [taskResponse, servicesStatusResponse] = await Promise.all([
      getAlgorithmTask(taskId).catch((err) => {
        console.error('获取任务信息失败', err);
        return null;
      }),
      getTaskServicesStatus(taskId).catch((err) => {
        console.error('获取服务状态失败', err);
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
        taskInfo.value = taskResponse as AlgorithmTask;
      }
    }

    console.log('任务信息:', taskInfo.value);

    // 处理服务状态响应
    if (servicesStatusResponse) {
      if (servicesStatusResponse && typeof servicesStatusResponse === 'object' && 'code' in servicesStatusResponse) {
        // 完整响应对象
        if (servicesStatusResponse.code === 0 && servicesStatusResponse.data) {
          extractorInfo.value = servicesStatusResponse.data.extractor || null;
          sorterInfo.value = servicesStatusResponse.data.sorter || null;
          pusherInfo.value = servicesStatusResponse.data.pusher || null;
          // 即使 realtime_service 为 null，也要设置为 null（而不是 undefined）
          realtimeServiceInfo.value = servicesStatusResponse.data.realtime_service ?? null;
          snapServiceInfo.value = servicesStatusResponse.data.snap_service ?? null;
          console.log('服务状态数据:', servicesStatusResponse.data);
          console.log('实时服务信息:', realtimeServiceInfo.value);
          console.log('实时服务信息类型:', typeof realtimeServiceInfo.value);
          console.log('实时服务信息是否为null:', realtimeServiceInfo.value === null);
          console.log('实时服务信息是否为undefined:', realtimeServiceInfo.value === undefined);
        } else {
          console.warn('服务状态响应code不为0:', servicesStatusResponse);
        }
      } else {
        // 直接返回的数据对象（响应转换器已处理）
        const statusData = servicesStatusResponse as any;
        extractorInfo.value = statusData.extractor || null;
        sorterInfo.value = statusData.sorter || null;
        pusherInfo.value = statusData.pusher || null;
        realtimeServiceInfo.value = statusData.realtime_service ?? null;
        snapServiceInfo.value = statusData.snap_service ?? null;
        console.log('服务状态数据（已转换）:', statusData);
        console.log('实时服务信息（已转换）:', realtimeServiceInfo.value);
        console.log('实时服务信息类型（已转换）:', typeof realtimeServiceInfo.value);
      }
    } else {
      console.warn('服务状态响应为空');
      // 如果统一接口失败，回退到分别获取
      const promises: Promise<any>[] = [];

      if (taskInfo.value?.extractor_id) {
        promises.push(
          getFrameExtractor(taskInfo.value.extractor_id).catch((err) => {
            console.error('获取抽帧器信息失败', err);
            return null;
          })
        );
      } else {
        promises.push(Promise.resolve(null));
      }

      if (taskInfo.value?.sorter_id) {
        promises.push(
          getSorter(taskInfo.value.sorter_id).catch((err) => {
            console.error('获取排序器信息失败', err);
            return null;
          })
        );
      } else {
        promises.push(Promise.resolve(null));
      }

      if (taskInfo.value?.pusher_id) {
        promises.push(
          getPusher(taskInfo.value.pusher_id).catch((err) => {
            console.error('获取推送器信息失败', err);
            return null;
          })
        );
      } else {
        promises.push(Promise.resolve(null));
      }

      const results = await Promise.all(promises);

      // 处理抽帧器响应
      if (results[0]) {
        if (results[0] && typeof results[0] === 'object' && 'code' in results[0]) {
          extractorInfo.value = results[0].code === 0 ? results[0].data : null;
        } else {
          extractorInfo.value = results[0] as FrameExtractor;
        }
      } else {
        extractorInfo.value = null;
      }

      // 处理排序器响应
      if (results[1]) {
        if (results[1] && typeof results[1] === 'object' && 'code' in results[1]) {
          sorterInfo.value = results[1].code === 0 ? results[1].data : null;
        } else {
          sorterInfo.value = results[1] as Sorter;
        }
      } else {
        sorterInfo.value = null;
      }

      // 处理推送器响应
      if (results[2]) {
        if (results[2] && typeof results[2] === 'object' && 'code' in results[2]) {
          pusherInfo.value = results[2].code === 0 ? results[2].data : null;
        } else {
          pusherInfo.value = results[2] as Pusher;
        }
      } else {
        pusherInfo.value = null;
      }
    }
  } catch (error) {
    console.error('加载服务信息失败', error);
    createMessage.error('加载服务信息失败');
  } finally {
    loading.value = false;
    console.log('加载完成，loading状态:', loading.value);
    console.log('加载完成，taskInfo:', taskInfo.value);
    console.log('加载完成，serviceList长度:', serviceList.value.length);
    console.log('加载完成，serviceList内容:', serviceList.value);
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

  // 对于抓拍算法任务，使用 'snap' 作为服务类型，但实际调用 realtime 日志接口
  const serviceType = record.service_type === 'snap' ? 'realtime' : record.service_type;
  
  openLogsModal(true, {
    title: `${record.service_name} - 日志`,
    taskId: taskInfo.value.id,
    serviceType: serviceType,
  });
};

// 查看抓拍空间
const handleViewSnapSpaces = async (record: any) => {
  // 如果记录中有设备ID，直接使用该设备的抓拍空间
  if (record.device_id && record.device_name) {
    const deviceId = record.device_id;
    const deviceName = record.device_name;
    
    try {
      const response = await getSnapSpaceByDeviceId(deviceId);
      const space = response && typeof response === 'object' && 'code' in response 
        ? (response.code === 0 ? response.data : null)
        : (response as SnapSpace | null);
      
      if (space) {
        handleViewSnapImages(space.id, deviceId, deviceName);
      } else {
        createMessage.warning(`摄像头 ${deviceName} 暂无抓拍空间`);
      }
    } catch (error) {
      console.error(`获取设备 ${deviceId} 的抓拍空间失败:`, error);
      createMessage.error('获取抓拍空间失败');
    }
    return;
  }

  // 兼容旧逻辑：如果没有设备ID，使用任务的所有设备（这种情况应该不会出现）
  if (!taskInfo.value || !taskInfo.value.device_ids || taskInfo.value.device_ids.length === 0) {
    createMessage.warning('任务未关联摄像头');
    return;
  }

  // 如果只有一个摄像头，直接打开该摄像头的抓拍空间
  if (taskInfo.value.device_ids.length === 1) {
    const deviceId = taskInfo.value.device_ids[0];
    const deviceName = taskInfo.value.device_names?.[0] || deviceId;
    
    try {
      const response = await getSnapSpaceByDeviceId(deviceId);
      const space = response && typeof response === 'object' && 'code' in response 
        ? (response.code === 0 ? response.data : null)
        : (response as SnapSpace | null);
      
      if (space) {
        handleViewSnapImages(space.id, deviceId, deviceName);
      } else {
        createMessage.warning(`摄像头 ${deviceName} 暂无抓拍空间`);
      }
    } catch (error) {
      console.error(`获取设备 ${deviceId} 的抓拍空间失败:`, error);
      createMessage.error('获取抓拍空间失败');
    }
    return;
  }

  // 多个摄像头，显示列表（这种情况应该不会出现，因为每条记录都有device_id）
  snapSpacesVisible.value = true;
  snapSpacesLoading.value = true;
  snapSpacesList.value = [];

  try {
    // 获取所有设备的抓拍空间
    const promises = taskInfo.value.device_ids.map(async (deviceId: string) => {
      try {
        const response = await getSnapSpaceByDeviceId(deviceId);
        const space = response && typeof response === 'object' && 'code' in response 
          ? (response.code === 0 ? response.data : null)
          : (response as SnapSpace | null);
        
        // 获取设备名称
        const deviceName = taskInfo.value?.device_names?.find((name: string, index: number) => 
          taskInfo.value?.device_ids?.[index] === deviceId
        ) || deviceId;

        return {
          device_id: deviceId,
          device_name: deviceName,
          space: space,
        };
      } catch (error) {
        console.error(`获取设备 ${deviceId} 的抓拍空间失败:`, error);
        return {
          device_id: deviceId,
          device_name: taskInfo.value?.device_names?.find((name: string, index: number) => 
            taskInfo.value?.device_ids?.[index] === deviceId
          ) || deviceId,
          space: null,
        };
      }
    });

    const results = await Promise.all(promises);
    snapSpacesList.value = results;
  } catch (error) {
    console.error('加载抓拍空间失败:', error);
    createMessage.error('加载抓拍空间失败');
  } finally {
    snapSpacesLoading.value = false;
  }
};

// 查看抓拍图片
const handleViewSnapImages = (spaceId: number, deviceId: string, deviceName?: string) => {
  // 关闭抓拍空间列表模态框
  snapSpacesVisible.value = false;
  // 直接打开抓拍图片模态框
  openSnapImageModal(true, {
    space_id: spaceId,
    space_name: deviceName || `设备 ${deviceId} 的抓拍空间`,
  });
};

// 启动服务（通过启动算法任务来启动服务）
const handleStart = async (record: any) => {
  if (!taskInfo.value) {
    createMessage.warning('任务信息不存在');
    return;
  }

  // 设置加载状态
  record.actionLoading = true;

  try {
    const response = await startAlgorithmTask(taskInfo.value.id);
    // 处理响应（由于 isTransformResponse: true，成功时返回的是任务对象）
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
      // 完整响应对象（这种情况应该很少见）
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

// 停止服务（通过停止算法任务来停止服务）
const handleStop = async (record: any) => {
  if (!taskInfo.value) {
    createMessage.warning('任务信息不存在');
    return;
  }

  // 设置加载状态
  record.actionLoading = true;

  try {
    const response = await stopAlgorithmTask(taskInfo.value.id);
    // 由于 isTransformResponse: true，成功时返回的是任务对象，而不是包含 code 的响应对象
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

// 重启服务（通过重启算法任务来重启服务）
const handleRestart = async (record: any) => {
  if (!taskInfo.value) {
    createMessage.warning('任务信息不存在');
    return;
  }

  // 设置加载状态
  record.actionLoading = true;

  try {
    const response = await restartAlgorithmTask(taskInfo.value.id);
    // 由于 isTransformResponse: true，成功时返回的是任务对象，而不是包含 code 的响应对象
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

// 播放推流
const handlePlayStream = async () => {
  if (!taskInfo.value || !taskInfo.value.is_enabled) {
    createMessage.warning('任务未运行，无法播放推流');
    return;
  }
  
  try {
    // 获取推流地址列表
    // 注意：由于 isTransformResponse: true，响应转换器会直接返回 data.data
    // 所以 response 可能是数组，也可能是包含 code 的完整响应对象
    const response = await getTaskStreams(taskInfo.value.id);
    console.log('获取推流地址响应:', response);
    
    // 处理响应：可能是数组，也可能是包含 code 的对象
    let streams: CameraStreamInfo[] = [];
    if (Array.isArray(response)) {
      // 直接是数组
      streams = response;
      console.log('响应是数组，摄像头数量:', streams.length);
    } else if (response && typeof response === 'object' && 'code' in response) {
      // 完整响应对象
      if (response.code === 0 && response.data && Array.isArray(response.data)) {
        streams = response.data;
        console.log('响应是对象，摄像头数量:', streams.length);
      } else {
        console.warn('响应code不为0或data不是数组:', response);
        createMessage.warning(response.msg || '该任务未关联摄像头或暂无推流地址');
        return;
      }
    } else {
      console.warn('响应格式不正确:', response);
      createMessage.warning('该任务未关联摄像头或暂无推流地址');
      return;
    }
    
    if (streams.length === 0) {
      createMessage.warning('该任务未关联摄像头或暂无推流地址');
      return;
    }
    
    cameraStreams.value = streams;
    
    // 过滤出有推流地址的摄像头（优先检查RTMP地址）
    const availableStreams = cameraStreams.value.filter(s => 
      s.pusher_rtmp_url || s.rtmp_stream || s.pusher_http_url || s.http_stream
    );
    
    if (availableStreams.length === 0) {
      createMessage.warning('该任务关联的摄像头暂无推流地址');
      return;
    }
    
    // 如果只有一个摄像头，直接播放
    if (availableStreams.length === 1) {
      playCameraStream(availableStreams[0]);
    } else {
      // 多个摄像头，显示选择对话框
      cameraStreams.value = availableStreams;
      selectedCameraIndex.value = 0;
      cameraSelectVisible.value = true;
    }
  } catch (error) {
    console.error('获取推流地址失败', error);
    createMessage.error('获取推流地址失败');
  }
};

// 确认选择摄像头并播放
const handleConfirmCamera = () => {
  if (cameraStreams.value.length > 0 && selectedCameraIndex.value >= 0) {
    const selectedStream = cameraStreams.value[selectedCameraIndex.value];
    playCameraStream(selectedStream);
    cameraSelectVisible.value = false;
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
  // 优先使用推送器的RTMP地址，转换为HTTP地址
  // 其次使用摄像头的RTMP地址，转换为HTTP地址
  // 最后使用已有的HTTP地址
  let httpStream: string | null = null;
  
  // 1. 优先使用推送器的RTMP地址
  if (stream.pusher_rtmp_url) {
    httpStream = convertRtmpToHttp(stream.pusher_rtmp_url);
  }
  
  // 2. 如果没有，使用推送器的HTTP地址
  if (!httpStream && stream.pusher_http_url) {
    httpStream = stream.pusher_http_url;
  }
  
  // 3. 如果还没有，使用摄像头的RTMP地址
  if (!httpStream && stream.rtmp_stream) {
    httpStream = convertRtmpToHttp(stream.rtmp_stream);
  }
  
  // 4. 最后使用摄像头的HTTP地址
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

// 处理抽屉关闭事件
const handleClose = () => {
  emit('close');
  emit('success');
};

// 注册抽屉
const [register] = useDrawerInner(async (data) => {
  // 重置状态
  taskInfo.value = null;
  extractorInfo.value = null;
  sorterInfo.value = null;
  pusherInfo.value = null;
  realtimeServiceInfo.value = null;
  snapServiceInfo.value = null;

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

.snap-spaces-list {
  padding: 16px 0;
  
  .snap-space-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    margin-bottom: 8px;
    background: #fafafa;
    border-radius: 6px;
    border: 1px solid #e8e8e8;
    
    &:last-child {
      margin-bottom: 0;
    }
    
    .device-info {
      flex: 1;
      
      .device-name {
        font-weight: 500;
        color: #262626;
        margin-right: 8px;
      }
      
      .device-id {
        color: #8c8c8c;
        font-size: 12px;
      }
    }
    
    .space-info {
      display: flex;
      align-items: center;
      gap: 12px;
      
      .space-name {
        color: #595959;
        font-size: 14px;
      }
    }
    
    .no-space {
      color: #999;
      font-size: 14px;
    }
  }
}
</style>

