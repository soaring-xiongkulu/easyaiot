<template>
  <BasicDrawer v-bind="$attrs" @register="register" :title="modalTitle" @ok="handleSubmit" width="1400"
    placement="right" :showFooter="true" :showCancelBtn="false" :showOkBtn="false">
    <template #footer>
      <div class="footer-buttons">
        <Button v-if="!isViewMode" @click="handleReset" class="mr-2">重置</Button>
        <Button v-if="!isViewMode" type="primary" :loading="confirmLoading" @click="handleSubmit">提交</Button>
      </div>
    </template>
    <a-tabs v-model:activeKey="activeTab">
      <a-tab-pane key="basic" tab="基础配置">
        <div class="basic-config-content">
          <a-alert
            v-if="showRuntimeVersionBanner"
            class="runtime-version-banner mb-3"
            type="info"
            show-icon
            :message="runtimeVersionBanner"
          />
          <BasicForm @register="registerForm" @field-value-change="handleFieldValueChange" />
          <div class="defense-schedule-wrapper" v-if="!isFullDayDefense">
            <a-divider orientation="left">布防时段配置</a-divider>
            <DefenseSchedulePicker v-model:modelValue="defenseSchedule" :disabled="isViewMode" />
          </div>
        </div>
      </a-tab-pane>
      <a-tab-pane key="status" tab="服务状态" :disabled="!taskId">
        <ServiceStatusTab v-if="taskId && formValues" :task="formValues" />
        <a-empty v-else description="请先保存基础配置" />
      </a-tab-pane>
    </a-tabs>
  </BasicDrawer>
</template>

<script lang="ts" setup>
import { ref, computed, nextTick, h, watch } from 'vue';
import { BasicDrawer, useDrawerInner } from '@/components/Drawer';
import { BasicForm, useForm } from '@/components/Form';
import { useMessage } from '@/hooks/web/useMessage';
import { QuestionCircleOutlined } from '@ant-design/icons-vue';
import { Popover, Select, Button as AntButton } from 'ant-design-vue';
import {
  createAlgorithmTask,
  updateAlgorithmTask,
  getRuntimeInfo,
  type AlgorithmTask,
} from '@/api/device/algorithm_task';
import { listFaceLibraries } from '@/api/device/face_library';
import { listPlateLibraries } from '@/api/device/plate_library';
import { listScenarioPoseLibraries } from '@/api/device/scenario_pose_library';
import { getDeviceList, getDeviceInfo, registerDevice, updateDevice } from '@/api/device/camera';
import { getModelPage } from '@/api/device/model';
import { getNodePage } from '@/api/device/node';
import { notifyTemplateQueryByType } from '@/api/device/notice';
import { getDeviceChannels, queryVideoList } from '@/api/device/gb28181';
import DefenseSchedulePicker from './DefenseSchedulePicker.vue';
import ServiceStatusTab from './ServiceStatusTab.vue';
import CronExpressionField from './CronExpressionField.vue';
import {
  DEFAULT_SNAP_CRON,
  getSnapCronHelpLines,
  validateSnapCronMinInterval,
} from '@/views/camera/utils/cronExpression';
import { Button } from '@/components/Button'
import {
collectMatchingTagsFromLibraries,
  type LibraryWithTags,
} from '@/views/camera/utils/libraryMatching';
import {
  buildAlertClassOptions,
  loadAlertClassNamesForModels,
  pruneAlertClassNames,
} from '@/views/camera/utils/modelAlertClasses';


defineOptions({ name: 'AlgorithmTaskModal' });

/** UI 六模式：task_mode ↔ task_type + executor */
function baseTaskType(modeOrType?: string): 'realtime' | 'snap' | 'patrol' {
  const raw = String(modeOrType || 'realtime');
  const v = raw.endsWith('_cpp') ? raw.slice(0, -4) : raw;
  if (v === 'snap' || v === 'patrol') return v;
  return 'realtime';
}
function toTaskMode(taskType?: string, executor?: string): string {
  const base = baseTaskType(taskType);
  const ex = String(executor || 'python').toLowerCase();
  return ex === 'cpp' || ex === 'c++' || ex === 'runtime' || ex === 'cxx' ? `${base}_cpp` : base;
}
function fromTaskMode(mode?: string): { task_type: 'realtime' | 'snap' | 'patrol'; executor: 'python' | 'cpp' } {
  const m = String(mode || 'realtime');
  if (m.endsWith('_cpp')) {
    return { task_type: baseTaskType(m), executor: 'cpp' };
  }
  return { task_type: baseTaskType(m), executor: 'python' };
}


const { createMessage } = useMessage();
const emit = defineEmits(['success', 'register']);

const faceLibraries = ref<LibraryWithTags[]>([]);
const plateLibraries = ref<LibraryWithTags[]>([]);
const poseLibraries = ref<LibraryWithTags[]>([]);

const activeTab = ref('basic');
const taskId = ref<number | null>(null);
const formValues = ref<any>({});
const confirmLoading = ref(false);
/** VIDEO 本机 RUNTIME 版本（高性能模式下展示） */
const runtimeInfo = ref<{ ready?: boolean; version?: string | null; binPath?: string | null } | null>(null);
const runtimeInfoTaskMode = ref<string>('realtime_cpp');

const showRuntimeVersionBanner = computed(() => {
  const mode = String(runtimeInfoTaskMode.value || formValues.value?.task_mode || '');
  return mode.endsWith('_cpp');
});

const runtimeVersionBanner = computed(() => {
  const info = runtimeInfo.value;
  if (!info) {
    return '本机 RUNTIME：正在查询版本…';
  }
  if (info.ready && info.version) {
    return `本机 RUNTIME 版本：${info.version}${info.binPath ? `（${info.binPath}）` : ''}`;
  }
  if (info.ready) {
    return '本机 RUNTIME 已就绪，但未找到 VERSION 文件（请重新编译以写入版本信息）';
  }
  return '本机 RUNTIME 未就绪：高性能任务将触发自动编译，或请先执行 RUNTIME/install_linux.sh';
});

async function loadRuntimeInfo() {
  try {
    const data = await getRuntimeInfo();
    // defHttp 可能返回 data 本体，也可能保留 { code, data }
    const info = (data as any)?.data && typeof (data as any).data === 'object'
      ? (data as any).data
      : data;
    runtimeInfo.value = info || { ready: false };
  } catch {
    runtimeInfo.value = { ready: false };
  }
}
const isFullDayDefense = ref<boolean>(true);
const alertNotificationEnabled = ref<boolean>(false); // 告警通知启用状态
const defenseSchedule = ref<{ mode: string; schedule: number[][] }>({
  mode: 'full',
  schedule: Array(7).fill(null).map(() => Array(24).fill(1)),
});
const alertNotificationConfig = ref<any>({
  enabled: false,
  channels: [],
  suppress_time: 300,
});

const deviceOptions = ref<Array<{ label: string; value: string }>>([]);
const nodeOptions = ref<Array<{ label: string; value: number }>>([]);

const schedulePolicyOptions = [
  { label: '本机部署', value: 'local' },
  { label: '自动调度节点', value: 'auto' },
  { label: '指定节点', value: 'node' },
];
const gbChannelOptionMap = ref<Map<string, { deviceId: string; channelId: string; name: string; label: string }>>(new Map());
// 初始化时就包含默认模型，确保始终显示
const defaultModels = [
  {
    label: 'yolo11n.pt',
    value: -1, // 使用 -1 表示 yolo11n.pt
  },
  {
    label: 'yolov8n.pt',
    value: -2, // 使用 -2 表示 yolov8n.pt
  },
  {
    label: 'yolo26n.pt',
    value: -3, // 使用 -3 表示 yolo26n.pt
  },
];
const modelOptions = ref<Array<{ label: string; value: number }>>([...defaultModels]);
const modelMap = ref<Map<number, any>>(new Map()); // 存储完整的模型信息
const alertClassOptions = ref<Array<{ label: string; value: string }>>([]);
const faceLibraryOptions = ref<Array<{ label: string; value: number }>>([]);
const plateLibraryOptions = ref<Array<{ label: string; value: number }>>([]);
const poseLibraryOptions = ref<Array<{ label: string; value: number }>>([]);

function normalizeLibraryIds(ids: unknown): number[] {
  if (Array.isArray(ids)) {
    return ids.map((id) => Number(id)).filter((id) => !Number.isNaN(id));
  }
  return [];
}

// 告警通知相关状态
const notificationChannels = ref<string[]>([]); // 选中的通知渠道
const channelTemplates = ref<Record<string, string | number>>({}); // 每个渠道的模板ID
const templates = ref<Record<string, any[]>>({}); // 模板列表（按渠道分组）
const templateLoading = ref<Record<string, boolean>>({}); // 模板加载状态

// 可用通知渠道
const availableChannels = [
  { label: '短信', value: 'sms' },
  { label: '邮件', value: 'email' },
  { label: '企业微信', value: 'wxcp' },
  { label: 'HTTP', value: 'http' },
  { label: '钉钉', value: 'ding' },
  { label: '飞书', value: 'feishu' },
];

// 通知渠道到消息类型的映射
const channelToMsgType: Record<string, number> = {
  sms: 1, // 阿里云短信
  email: 3, // 邮件
  wxcp: 4, // 企业微信
  http: 5, // HTTP
  ding: 6, // 钉钉
  feishu: 7, // 飞书
};

// 占位符列表（包含占位符和说明）
const placeholders = [
  { placeholder: '${object}', description: '检测对象' },
  { placeholder: '${event}', description: '事件类型' },
  { placeholder: '${region}', description: '区域信息' },
  { placeholder: '${information}', description: '详细信息' },
  { placeholder: '${device_id}', description: '设备ID' },
  { placeholder: '${device_name}', description: '设备名称' },
  { placeholder: '${time}', description: '时间' },
  { placeholder: '${image_path}', description: '图片路径' },
  { placeholder: '${record_path}', description: '录像路径' },
];

const GB28181_OPTION_PREFIX = 'gb28181:';
const GB28181_SOURCE_PREFIX = 'gb28181://';

const buildGb28181OptionValue = (deviceId: string, channelId: string) =>
  `${GB28181_OPTION_PREFIX}${deviceId}:${channelId}`;

const buildGb28181VirtualDeviceId = (deviceId: string, channelId: string) =>
  `gb28181_${deviceId}_${channelId}`;

const isGb28181OptionValue = (value: unknown): value is string =>
  typeof value === 'string' && value.startsWith(GB28181_OPTION_PREFIX);

const extractListData = (response: any) => {
  if (Array.isArray(response)) {
    return response;
  }
  if (Array.isArray(response?.data)) {
    return response.data;
  }
  if (Array.isArray(response?.data?.list)) {
    return response.data.list;
  }
  if (Array.isArray(response?.list)) {
    return response.list;
  }
  return [];
};

const normalizeGb28181Channel = (item: any) => {
  const deviceId = String(
    item?.parentId || item?.parentDeviceId || item?.gbParentId || item?.deviceIdentification || '',
  ).trim();
  const channelId = String(
    item?.channelId || item?.deviceChannelId || item?.gbDeviceId || item?.deviceId || item?.id || item?.gbId || '',
  ).trim();
  if (!deviceId || !channelId) {
    return null;
  }

  const channelName = item?.name || item?.channelName || item?.deviceName || item?.gbName || channelId;
  return {
    deviceId,
    channelId,
    name: channelName,
    label: `[GB28181] ${channelName} (${channelId})`,
  };
};

const buildDeviceOptionLabel = (item: any) => {
  const isGbVirtualDevice =
    typeof item?.source === 'string' && item.source.startsWith(GB28181_SOURCE_PREFIX);
  const prefix = isGbVirtualDevice ? '[GB28181]' : '[直连]';
  return `${prefix} ${item?.name || item?.id}`;
};

const ensureGb28181VideoDevice = async (optionValue: string) => {
  const channel = gbChannelOptionMap.value.get(optionValue);
  if (!channel) {
    throw new Error(`未找到国标通道映射: ${optionValue}`);
  }

  const mappedDeviceId = buildGb28181VirtualDeviceId(channel.deviceId, channel.channelId);
  const payload = {
    id: mappedDeviceId,
    name: channel.name,
    source: `${GB28181_SOURCE_PREFIX}${channel.deviceId}/${channel.channelId}`,
    cameraType: 'custom',
    manufacturer: 'GB28181',
    model: 'GB28181-Channel',
    serial_number: channel.deviceId,
    hardware_id: channel.channelId,
  };

  try {
    await getDeviceInfo(mappedDeviceId);
    await updateDevice(mappedDeviceId, payload);
  } catch (error: any) {
    const status = error?.response?.status;
    const code = error?.response?.data?.code;
    if (status === 404 || code === 400) {
      await registerDevice(payload as any);
    } else {
      throw error;
    }
  }

  return mappedDeviceId;
};

const syncSelectedDeviceIds = async (selectedValues: string[] = []) => {
  const normalizedIds = await Promise.all(
    (selectedValues || []).map(async (value) => {
      if (isGb28181OptionValue(value)) {
        return ensureGb28181VideoDevice(value);
      }
      return value;
    }),
  );
  return Array.from(new Set(normalizedIds.filter(Boolean)));
};

// 加载在线计算节点
const loadNodes = async () => {
  try {
    const res = await getNodePage({ pageNo: 1, pageSize: 200, status: 'online' });
    const page = res?.data || res;
    const list = (page?.list || []).filter(
      (node: any) => node.nodeRole === 'compute' || node.nodeRole === 'gpu' || node.nodeRole === 'hybrid',
    );
    nodeOptions.value = list.map((node: any) => ({
      label: `${node.name} (${node.host})`,
      value: node.id,
    }));
    updateSchema({
      field: 'target_node_id',
      componentProps: {
        options: nodeOptions.value,
      },
    });
  } catch (error) {
    console.error('加载节点列表失败', error);
    nodeOptions.value = [];
  }
};

// 加载设备列表
const loadDevices = async () => {
  try {
    // 设备来源包括：
    // 1. VIDEO 自身摄像头表
    // 2. GB28181 已注册但尚未同步为 VIDEO 设备的国标通道
    const [deviceResponse, gbDeviceResponse] = await Promise.all([
      getDeviceList({ pageNo: 1, pageSize: 1000 }),
      queryVideoList({ pageNum: 1, pageSize: 1000, status: true }),
    ]);

    const currentDevices = extractListData(deviceResponse);
    const currentDeviceIds = new Set(currentDevices.map((item) => String(item.id)));
    const directOptions = currentDevices.map((item) => ({
      label: buildDeviceOptionLabel(item),
      value: item.id,
      disabled: false,
    }));

    const gbDevices = extractListData(gbDeviceResponse);
    const gbChannelResults = await Promise.allSettled(
      gbDevices.map((device: any) => getDeviceChannels(device.deviceIdentification)),
    );
    const gbChannelList = gbChannelResults.flatMap((result: any) =>
      result.status === 'fulfilled' ? extractListData(result.value) : [],
    );

    gbChannelOptionMap.value.clear();
    const gbOptions = gbChannelList
      .map((item: any) => normalizeGb28181Channel(item))
      .filter((item: any) => !!item)
      .filter((item: any) => !currentDeviceIds.has(buildGb28181VirtualDeviceId(item.deviceId, item.channelId)))
      .map((item: any) => {
        const optionValue = buildGb28181OptionValue(item.deviceId, item.channelId);
        gbChannelOptionMap.value.set(optionValue, item);
        return {
          label: item.label,
          value: optionValue,
          disabled: false,
        };
      });

    deviceOptions.value = [...directOptions, ...gbOptions];

    // 更新表单schema，设置禁用选项
    updateSchema({
      field: 'device_ids',
      componentProps: {
        options: deviceOptions.value,
      },
    });
  } catch (error) {
    console.error('加载设备列表失败', error);
  }
};

// 初始化默认模型到映射中
const initDefaultModels = () => {
  modelMap.value.set(-1, {
    id: -1,
    name: 'yolo11n.pt',
    model_path: 'yolo11n.pt',
    version: undefined,
  });
  modelMap.value.set(-2, {
    id: -2,
    name: 'yolov8n.pt',
    model_path: 'yolov8n.pt',
    version: undefined,
  });
  modelMap.value.set(-3, {
    id: -3,
    name: 'yolo26n.pt',
    model_path: 'yolo26n.pt',
    version: undefined,
  });
};

// 加载模型列表（用于选择模型）
const loadModels = async () => {
  // 先初始化默认模型，确保它们始终存在
  initDefaultModels();

  try {
    const response = await getModelPage({ pageNo: 1, pageSize: 1000 });
    // 处理响应数据：可能是转换后的数组，也可能是包含 code/data 的对象
    let allModels: any[] = [];
    if (Array.isArray(response)) {
      allModels = response;
    } else if (response && response.code === 0 && response.data) {
      allModels = Array.isArray(response.data) ? response.data : [];
    } else if (response && response.data && Array.isArray(response.data)) {
      allModels = response.data;
    }

    // 构建选项列表和完整模型信息映射（不清空默认模型）
    const dbModelOptions = allModels.map((item: any) => {
      // 保存完整的模型信息
      modelMap.value.set(item.id, item);

      return {
        label: `${item.name}${item.version ? ` (v${item.version})` : ''}`,
        value: item.id, // 模型ID
      };
    });

    // 将默认模型放在最前面，然后添加数据库中的模型
    // 确保即使后端返回空列表，默认模型也会显示
    modelOptions.value = [...defaultModels, ...dbModelOptions];
  } catch (error) {
    console.error('加载模型列表失败', error);
    // 即使加载失败，也确保默认模型显示
    modelOptions.value = defaultModels;
  }
};

const refreshAlertClassOptions = async (modelIds: unknown, selectedNames?: string[]) => {
  const ids = Array.isArray(modelIds)
    ? modelIds.map((id) => Number(id)).filter((id) => !Number.isNaN(id))
    : [];
  if (ids.length === 0) {
    alertClassOptions.value = [];
    await setFieldsValue({ alert_class_names: [] });
    updateSchema({
      field: 'alert_class_names',
      componentProps: { options: [] },
    });
    return;
  }

  const classNames = await loadAlertClassNamesForModels(ids);
  alertClassOptions.value = buildAlertClassOptions(classNames);
  updateSchema({
    field: 'alert_class_names',
    componentProps: {
      options: alertClassOptions.value,
    },
  });

  const currentSelected = selectedNames ?? (await getFieldsValue()).alert_class_names;
  const pruned = pruneAlertClassNames(currentSelected, classNames);
  if (JSON.stringify(pruned) !== JSON.stringify(currentSelected || [])) {
    await setFieldsValue({ alert_class_names: pruned });
  }
};

const loadFaceLibraries = async () => {
  try {
    const res = await listFaceLibraries({ is_enabled: true });
    const rows = Array.isArray(res?.data) ? res.data : (res as any) || [];
    faceLibraries.value = rows;
    faceLibraryOptions.value = rows.map((item: LibraryWithTags) => ({
      label: item.name,
      value: item.id,
    }));
  } catch (error) {
    console.error('加载人脸库列表失败', error);
    faceLibraries.value = [];
    faceLibraryOptions.value = [];
  }
};

const loadPlateLibraries = async () => {
  try {
    const res = await listPlateLibraries({ is_enabled: true });
    const rows = Array.isArray(res?.data) ? res.data : (res as any) || [];
    plateLibraries.value = rows;
    plateLibraryOptions.value = rows.map((item: LibraryWithTags) => ({
      label: item.name,
      value: item.id,
    }));
  } catch (error) {
    console.error('加载车牌库列表失败', error);
    plateLibraries.value = [];
    plateLibraryOptions.value = [];
  }
};

const loadScenarioPoseLibraries = async () => {
  try {
    const res = await listScenarioPoseLibraries({ is_enabled: true });
    const rows = Array.isArray(res?.data) ? res.data : (res as any) || [];
    poseLibraries.value = rows;
    poseLibraryOptions.value = rows.map((item: LibraryWithTags) => ({
      label: item.name,
      value: item.id,
    }));
  } catch (error) {
    console.error('加载场景姿态库列表失败', error);
    poseLibraries.value = [];
    poseLibraryOptions.value = [];
  }
};

// 获取渠道标签
const getChannelLabel = (channel: string) => {
  return availableChannels.find((c) => c.value === channel)?.label || channel;
};

// 加载模板列表
const loadTemplates = async (channel: string) => {
  if (templates.value[channel]?.length) {
    return; // 已加载
  }

  templateLoading.value[channel] = true;
  try {
    const msgType = channelToMsgType[channel];
    if (!msgType) {
      console.warn(`未知的通知渠道: ${channel}`);
      return;
    }

    const response = await notifyTemplateQueryByType({ msgType });
    // 处理响应：可能是{code: 0, data: [...]}格式，也可能是直接返回数组
    if (response) {
      if (response.code === 0 && response.data) {
        templates.value[channel] = Array.isArray(response.data) ? response.data : [];
      } else if (Array.isArray(response)) {
        // 如果直接返回数组
        templates.value[channel] = response;
      } else {
        templates.value[channel] = [];
        console.warn(`加载${getChannelLabel(channel)}模板失败:`, response?.msg || '未知错误');
      }
    } else {
      templates.value[channel] = [];
      console.warn(`加载${getChannelLabel(channel)}模板失败: 响应为空`);
    }
  } catch (error) {
    console.error(`加载${getChannelLabel(channel)}模板失败:`, error);
    templates.value[channel] = [];
  } finally {
    templateLoading.value[channel] = false;
  }
};

const [registerForm, { setFieldsValue, validate, resetFields, updateSchema, getFieldsValue }] = useForm({
  transformDateToString: false,
  labelWidth: 150,
  baseColProps: { span: 24 },
  schemas: [
    {
      field: 'task_name',
      label: '任务名称',
      component: 'Input',
      required: true,
      componentProps: {
        placeholder: '请输入任务名称',
      },
    },
    {
      field: 'task_mode',
      label: '任务类型',
      component: 'Select',
      required: true,
      componentProps: {
        placeholder: '请选择任务类型',
        options: [
          { label: '实时算法任务（高性能）', value: 'realtime_cpp' },
          { label: '抓拍算法任务（高性能）', value: 'snap_cpp' },
          { label: '巡检算法任务（高性能）', value: 'patrol_cpp' },
          { label: '实时算法任务', value: 'realtime' },
          { label: '抓拍算法任务', value: 'snap' },
          { label: '巡检算法任务', value: 'patrol' },
        ],
      },
      helpMessage: '高性能：RUNTIME C++ 加速推理，适合大路数/低时延。可「本机」跑，或调度到已分发 RUNTIME 的计算节点（原子节点）；未标注项为 Python 完整能力集（人脸/车牌/后处理等）',
      defaultValue: 'realtime_cpp',
    },
    {
      field: 'patrol_interval_sec',
      label: '巡检间隔(秒)',
      component: 'InputNumber',
      defaultValue: 10,
      componentProps: { min: 3, max: 300 },
      ifShow: ({ values }) => baseTaskType(values.task_mode) === 'patrol',
    },
    {
      field: 'patrol_pool_size',
      label: '连接池大小',
      component: 'InputNumber',
      defaultValue: 4,
      componentProps: { min: 1, max: 16 },
      ifShow: ({ values }) => baseTaskType(values.task_mode) === 'patrol',
    },
    {
      field: 'schedule_policy',
      label: '调度策略',
      component: 'Select',
      defaultValue: 'local',
      componentProps: {
        placeholder: '请选择调度策略',
        options: schedulePolicyOptions,
      },
      helpMessage: '本机：当前 VIDEO 所在机拉起 RUNTIME/Python；自动/指定节点：经 iot-node 下发到远程 Agent。高性能(cpp)调度到节点前，请先在「节点管理 → 业务运行时分发」安装 RUNTIME',
    },
    {
      field: 'prefer_gpu',
      label: '优先 GPU 节点',
      component: 'Switch',
      defaultValue: true,
      componentProps: {
        checkedChildren: '是',
        unCheckedChildren: '否',
      },
      ifShow: ({ values }) => values.schedule_policy === 'auto',
      helpMessage: '自动调度时优先选择 GPU 节点；关闭则优先 CPU 计算节点',
    },
    {
      field: 'target_node_id',
      label: '目标节点',
      component: 'Select',
      componentProps: {
        placeholder: '选择在线计算节点',
        options: nodeOptions,
        showSearch: true,
        allowClear: true,
        filterOption: (input: string, option: any) => {
          return option.label.toLowerCase().indexOf(input.toLowerCase()) >= 0;
        },
      },
      ifShow: ({ values }) => values.schedule_policy === 'node',
      required: ({ values }) => values.schedule_policy === 'node',
    },
    {
      field: 'device_ids',
      label: '关联摄像头',
      component: 'Select',
      required: true,
      componentProps: {
        placeholder: '请选择摄像头（可多选）',
        options: deviceOptions,
        mode: 'multiple',
        showSearch: true,
        allowClear: true,
        filterOption: (input: string, option: any) => {
          return option.label.toLowerCase().indexOf(input.toLowerCase()) >= 0;
        },
      },
    },
    {
      field: 'model_ids',
      label: '关联模型',
      component: 'Select',
      required: true,
      componentProps: {
        placeholder: '请选择模型（可多选）',
        options: modelOptions,
        mode: 'multiple',
        showSearch: true,
        allowClear: true,
        filterOption: (input: string, option: any) => {
          return option.label.toLowerCase().indexOf(input.toLowerCase()) >= 0;
        },
      },
      helpMessage: '选择要使用的模型列表，模型文件本地没有会自动下载',
      ifShow: ({ values }) => baseTaskType(values.task_mode) === 'realtime' || baseTaskType(values.task_mode) === 'snap' || baseTaskType(values.task_mode) === 'patrol',
    },
    {
      field: 'cron_expression',
      label: 'Cron表达式',
      component: 'Input',
      required: true,
      helpMessage: getSnapCronHelpLines(),
      helpComponentProps: { maxWidth: '480px' },
      render: ({ model }) =>
        h(CronExpressionField, {
          modelValue: model.cron_expression,
          disabled: isViewMode.value,
          'onUpdate:modelValue': (value: string) => {
            model.cron_expression = value;
            setFieldsValue({ cron_expression: value });
          },
        }),
      ifShow: ({ values }) => baseTaskType(values.task_mode) === 'snap',
    },
    {
      field: 'frame_skip',
      label: '抽帧间隔',
      component: 'InputNumber',
      componentProps: {
        placeholder: '每N帧抓一次',
        min: 1,
      },
      helpMessage: '抽帧模式下，每N帧抓一次（默认25）',
      ifShow: ({ values }) => baseTaskType(values.task_mode) === 'snap',
    },
    {
      field: 'extract_interval',
      label: '检测间隔(帧)',
      component: 'InputNumber',
      componentProps: {
        placeholder: '每N帧检测一次',
        min: 1,
      },
      helpMessage: '12=25fps下约每秒2次(默认); 1=全帧检测; 25=约每秒1次。推流帧率不受影响，数值越小框越及时但GPU占用越高。',
      ifShow: ({ values }) => baseTaskType(values.task_mode) === 'realtime',
    },
    {
      field: 'detect_conf',
      label: '检测置信度',
      component: 'InputNumber',
      defaultValue: 0.5,
      componentProps: {
        min: 0.1,
        max: 0.95,
        step: 0.05,
        style: { width: '100%' },
      },
      helpMessage: 'YOLO 模型检测置信度阈值，默认 0.5。值越高误检越少，但可能增加漏检。',
      ifShow: ({ values }) =>
        baseTaskType(values.task_mode) === 'realtime' || baseTaskType(values.task_mode) === 'snap' || baseTaskType(values.task_mode) === 'patrol',
    },
    {
      field: 'motion_gate_enabled',
      label: '启用运动补检',
      component: 'Switch',
      defaultValue: false,
      componentProps: {
        checkedChildren: '是',
        unCheckedChildren: '否',
      },
      helpMessage: '在抽帧采样点评估画面变化；仅大面积持续变化时记录命中。风吹草动等局部抖动不会频繁触发额外检测。',
      ifShow: ({ values }) => baseTaskType(values.task_mode) === 'realtime',
    },
    {
      field: 'motion_sensitivity',
      label: '运动检测灵敏度',
      component: 'Select',
      defaultValue: 'conservative',
      componentProps: {
        options: [
          { label: '保守（户外/有植被，推荐）', value: 'conservative' },
          { label: '标准', value: 'standard' },
          { label: '灵敏（室内，慎用）', value: 'sensitive' },
        ],
      },
      helpMessage: '保守模式要求更大变化面积与连续确认，避免风吹草动误触发。',
      ifShow: ({ values }) => baseTaskType(values.task_mode) === 'realtime' && !!values.motion_gate_enabled,
    },
    {
      field: 'tracking_enabled',
      label: '启用目标追踪',
      component: 'Switch',
      componentProps: {
        checkedChildren: '是',
        unCheckedChildren: '否',
      },
      helpMessage: '是否启用目标追踪功能，启用后会记录对象出现时间、停留时间、离开时间等信息',
      ifShow: ({ values }) => baseTaskType(values.task_mode) === 'realtime',
    },
    {
      field: 'tracking_similarity_threshold',
      label: '追踪相似度阈值',
      component: 'InputNumber',
      componentProps: {
        placeholder: '0.2',
        min: 0,
        max: 1,
        step: 0.1,
      },
      helpMessage: '追踪相似度匹配阈值（0-1），值越小匹配越宽松',
      ifShow: ({ values }) => baseTaskType(values.task_mode) === 'realtime' && values.tracking_enabled,
    },
    {
      field: 'tracking_max_age',
      label: '追踪最大存活帧数',
      component: 'InputNumber',
      componentProps: {
        placeholder: '25',
        min: 1,
      },
      helpMessage: '追踪目标最大存活帧数（未匹配时保留的帧数）',
      ifShow: ({ values }) => baseTaskType(values.task_mode) === 'realtime' && values.tracking_enabled,
    },
    {
      field: 'tracking_smooth_alpha',
      label: '追踪平滑系数',
      component: 'InputNumber',
      componentProps: {
        placeholder: '0.25',
        min: 0,
        max: 1,
        step: 0.05,
      },
      helpMessage: '追踪平滑系数（0-1），值越大越平滑',
      ifShow: ({ values }) => baseTaskType(values.task_mode) === 'realtime' && values.tracking_enabled,
    },
    {
      field: 'alert_event_enabled',
      label: '启用告警事件',
      component: 'Switch',
      defaultValue: false,
      componentProps: {
        checkedChildren: '是',
        unCheckedChildren: '否',
      },
      suffix: () =>
        h(Popover, {
          title: '算法任务占位符',
          trigger: 'hover',
          placement: 'rightTop',
          getPopupContainer: () => document.body,
        }, {
          content: () => h('div', { class: 'placeholder-box-small' },
            placeholders.map((item) =>
              h('div', { class: 'placeholder-item-small' }, [
                h('span', { class: 'placeholder-text' }, item.placeholder),
                h('span', { class: 'placeholder-separator' }, ': '),
                h('span', { class: 'placeholder-desc' }, item.description),
              ])
            )
          ),
          default: () => h(AntButton, {
            type: 'text',
            size: 'small',
            class: 'placeholder-trigger-btn',
          }, {
            icon: () => h(QuestionCircleOutlined),
          }),
        }),
      helpMessage: '是否启用告警事件，启用后会记录告警信息',
      ifShow: ({ values }) => baseTaskType(values.task_mode) === 'realtime' || baseTaskType(values.task_mode) === 'snap' || baseTaskType(values.task_mode) === 'patrol',
    },
    {
      field: 'alert_class_names',
      label: '告警触发标签',
      component: 'Select',
      componentProps: {
        placeholder: '请选择触发告警的检测标签（可多选）',
        options: alertClassOptions,
        mode: 'multiple',
        showSearch: true,
        allowClear: true,
        filterOption: (input: string, option: any) =>
          (option?.label || '').toLowerCase().includes(input.toLowerCase()),
      },
      helpMessage: '仅当检测到所选标签时才触发告警，需至少选择一项',
      dynamicRules: ({ values }) => {
        if (!values.alert_event_enabled) return [];
        const names = Array.isArray(values.alert_class_names) ? values.alert_class_names : [];
        if (!names.length) {
          return [{ required: true, message: '启用告警事件时必须选择至少一个告警触发标签' }];
        }
        return [];
      },
      ifShow: ({ values }) =>
        (baseTaskType(values.task_mode) === 'realtime' || baseTaskType(values.task_mode) === 'snap' || baseTaskType(values.task_mode) === 'patrol')
        && !!values.alert_event_enabled,
    },
    {
      field: 'alert_event_suppress_time',
      label: '告警间隔（秒）',
      component: 'InputNumber',
      defaultValue: 5,
      componentProps: {
        placeholder: '5',
        min: 0,
        max: 3600,
        step: 1,
        style: { width: '100%' },
      },
      helpMessage:
        '同一摄像头两次上报告警事件的最小间隔，用于减轻 Kafka 积压。测试阶段可设为 0（不抑制）',
      ifShow: ({ values }) =>
        (baseTaskType(values.task_mode) === 'realtime' || baseTaskType(values.task_mode) === 'snap' || baseTaskType(values.task_mode) === 'patrol') && !!values.alert_event_enabled,
    },
    {
      field: 'face_matching_enabled',
      label: '启用人脸匹配',
      component: 'Switch',
      defaultValue: false,
      componentProps: {
        checkedChildren: '是',
        unCheckedChildren: '否',
      },
      helpMessage: '开启后裁剪人脸并异步投递 Kafka 进行 1:N 库匹配',
      ifShow: ({ values }) => baseTaskType(values.task_mode) === 'realtime' || baseTaskType(values.task_mode) === 'snap' || baseTaskType(values.task_mode) === 'patrol',
    },
    {
      field: 'face_library_ids',
      label: '人脸库',
      component: 'Select',
      componentProps: {
        placeholder: '请选择人脸库（可多选）',
        options: faceLibraryOptions,
        mode: 'multiple',
        showSearch: true,
        allowClear: true,
        filterOption: (input: string, option: any) =>
          (option?.label || '').toLowerCase().includes(input.toLowerCase()),
      },
      dynamicRules: ({ values }) => {
        if (!values.face_matching_enabled) return [];
        const ids = normalizeLibraryIds(values.face_library_ids);
        if (!ids.length) {
          return [{ required: true, message: '启用人脸匹配时必须选择至少一个人脸库' }];
        }
        return [];
      },
      ifShow: ({ values }) =>
        (baseTaskType(values.task_mode) === 'realtime' || baseTaskType(values.task_mode) === 'snap' || baseTaskType(values.task_mode) === 'patrol') && !!values.face_matching_enabled,
    },
    {
      field: 'plate_matching_enabled',
      label: '启用车牌匹配',
      component: 'Switch',
      defaultValue: false,
      componentProps: {
        checkedChildren: '是',
        unCheckedChildren: '否',
      },
      helpMessage: '开启后独立队列识别车牌并异步投递 Kafka 进行库匹配（默认关闭）',
      ifShow: ({ values }) => baseTaskType(values.task_mode) === 'realtime' || baseTaskType(values.task_mode) === 'snap' || baseTaskType(values.task_mode) === 'patrol',
    },
    {
      field: 'plate_library_ids',
      label: '车牌库',
      component: 'Select',
      componentProps: {
        placeholder: '请选择车牌库（可多选）',
        options: plateLibraryOptions,
        mode: 'multiple',
        showSearch: true,
        allowClear: true,
        filterOption: (input: string, option: any) =>
          (option?.label || '').toLowerCase().includes(input.toLowerCase()),
      },
      dynamicRules: ({ values }) => {
        if (!values.plate_matching_enabled) return [];
        const ids = normalizeLibraryIds(values.plate_library_ids);
        if (!ids.length) {
          return [{ required: true, message: '启用车牌匹配时必须选择至少一个车牌库' }];
        }
        return [];
      },
      ifShow: ({ values }) =>
        (baseTaskType(values.task_mode) === 'realtime' || baseTaskType(values.task_mode) === 'snap' || baseTaskType(values.task_mode) === 'patrol') && !!values.plate_matching_enabled,
    },
    {
      field: 'sam_supplement_enabled',
      label: 'SAM 补充识别',
      component: 'Switch',
      defaultValue: false,
      componentProps: { checkedChildren: '开', unCheckedChildren: '关' },
      helpMessage: '在 YOLO 主检基础上叠加 SAM：Pipeline 精修 mask 或开放词汇补检',
      ifShow: ({ values }) => baseTaskType(values.task_mode) === 'realtime' || baseTaskType(values.task_mode) === 'snap' || baseTaskType(values.task_mode) === 'patrol',
    },
    {
      field: 'sam_pipeline_mode',
      label: 'SAM 工作模式',
      component: 'Select',
      defaultValue: 'none',
      componentProps: {
        options: [
          { label: 'Pipeline 精修 mask', value: 'refine_mask' },
          { label: '开放词汇补充', value: 'open_vocab' },
          { label: '告警二次确认', value: 'alert_verify' },
        ],
      },
      ifShow: ({ values }) => !!values.sam_supplement_enabled,
    },
    {
      field: 'sam_text_prompts',
      label: 'SAM 文本类别',
      component: 'Select',
      componentProps: {
        mode: 'tags',
        placeholder: '英文类别，如 fire、helmet',
        tokenSeparators: [','],
      },
      ifShow: ({ values }) =>
        !!values.sam_supplement_enabled &&
        (values.sam_pipeline_mode === 'open_vocab' || values.sam_pipeline_mode === 'alert_verify'),
    },
    {
      field: 'sam_trigger',
      label: 'SAM 触发策略',
      component: 'Select',
      defaultValue: 'on_interval',
      componentProps: {
        options: [
          { label: '每 N 帧', value: 'on_interval' },
          { label: '仅告警帧', value: 'on_alert' },
          { label: 'YOLO 无检出时', value: 'on_yolo_empty' },
          { label: '每帧', value: 'always' },
        ],
      },
      ifShow: ({ values }) => !!values.sam_supplement_enabled,
    },
    {
      field: 'sam_interval_frames',
      label: 'SAM 间隔帧数',
      component: 'InputNumber',
      defaultValue: 25,
      componentProps: { min: 1, max: 300, style: { width: '100%' } },
      ifShow: ({ values }) => !!values.sam_supplement_enabled && values.sam_trigger === 'on_interval',
    },
    {
      field: 'sam_conf',
      label: 'SAM 置信度',
      component: 'InputNumber',
      defaultValue: 0.45,
      componentProps: { min: 0.1, max: 0.95, step: 0.05, style: { width: '100%' } },
      ifShow: ({ values }) => !!values.sam_supplement_enabled,
    },
    {
      field: 'pose_analysis_enabled',
      label: '人体姿态分析',
      component: 'Switch',
      defaultValue: false,
      componentProps: { checkedChildren: '开', unCheckedChildren: '关' },
      helpMessage: '开启后由 iot-sink Worker 异步分析人体骨骼（COCO-17），不占用算法任务算力；默认关闭',
      ifShow: ({ values }) =>
        baseTaskType(values.task_mode) === 'realtime' || baseTaskType(values.task_mode) === 'snap' || baseTaskType(values.task_mode) === 'patrol',
    },
    {
      field: 'pose_model_file_path',
      label: '姿态模型',
      component: 'Input',
      defaultValue: 'yolo26n-pose.pt',
      componentProps: { placeholder: '如 yolo26n-pose.pt' },
      ifShow: ({ values }) => !!values.pose_analysis_enabled,
    },
    {
      field: 'pose_trigger',
      label: '姿态触发策略',
      component: 'Select',
      defaultValue: 'on_interval',
      componentProps: {
        options: [
          { label: '按间隔帧', value: 'on_interval' },
          { label: '检测到人体时', value: 'on_person' },
          { label: '每帧', value: 'always' },
        ],
      },
      ifShow: ({ values }) => !!values.pose_analysis_enabled,
    },
    {
      field: 'pose_interval_frames',
      label: '姿态间隔帧数',
      component: 'InputNumber',
      defaultValue: 12,
      componentProps: { min: 1, max: 300, style: { width: '100%' } },
      ifShow: ({ values }) => !!values.pose_analysis_enabled && values.pose_trigger === 'on_interval',
    },
    {
      field: 'pose_conf',
      label: '姿态置信度',
      component: 'InputNumber',
      defaultValue: 0.25,
      componentProps: { min: 0.1, max: 0.95, step: 0.05, style: { width: '100%' } },
      ifShow: ({ values }) => !!values.pose_analysis_enabled,
    },
    {
      field: 'pose_intent_enabled',
      label: '姿态意图分析告警',
      component: 'Switch',
      defaultValue: false,
      componentProps: { checkedChildren: '开', unCheckedChildren: '关' },
      helpMessage: '开启后自动启用 YOLO Pose，并将检测姿态与场景姿态库匹配产生意图告警',
      ifShow: ({ values }) =>
        baseTaskType(values.task_mode) === 'realtime' || baseTaskType(values.task_mode) === 'snap' || baseTaskType(values.task_mode) === 'patrol',
    },
    {
      field: 'pose_library_ids',
      label: '场景姿态库',
      component: 'Select',
      componentProps: {
        placeholder: '请选择场景姿态库（可多选）',
        options: poseLibraryOptions,
        mode: 'multiple',
        showSearch: true,
        allowClear: true,
        filterOption: (input: string, option: any) =>
          (option?.label || '').toLowerCase().includes(input.toLowerCase()),
      },
      dynamicRules: ({ values }) => {
        if (!values.pose_intent_enabled) return [];
        const ids = normalizeLibraryIds(values.pose_library_ids);
        if (!ids.length) {
          return [{ required: true, message: '启用姿态意图分析时必须选择至少一个场景姿态库' }];
        }
        return [];
      },
      ifShow: ({ values }) =>
        (baseTaskType(values.task_mode) === 'realtime' || baseTaskType(values.task_mode) === 'snap' || baseTaskType(values.task_mode) === 'patrol') &&
        !!values.pose_intent_enabled,
    },
    {
      field: 'pose_intent_threshold',
      label: '意图匹配阈值',
      component: 'InputNumber',
      componentProps: { min: 0.1, max: 0.99, step: 0.01, placeholder: '空=库默认', style: { width: '100%' } },
      ifShow: ({ values }) => !!values.pose_intent_enabled,
    },
    {
      field: 'pose_intent_suppress_sec',
      label: '同意图抑制(秒)',
      component: 'InputNumber',
      defaultValue: 10,
      componentProps: { min: 0, max: 3600, style: { width: '100%' } },
      ifShow: ({ values }) => !!values.pose_intent_enabled,
    },
    {
      field: 'pose_intent_draw_skeleton',
      label: '告警图叠骨架',
      component: 'Switch',
      defaultValue: true,
      componentProps: { checkedChildren: '开', unCheckedChildren: '关' },
      ifShow: ({ values }) => !!values.pose_intent_enabled,
    },
    {
      field: 'pose_intent_temporal_dtw',
      label: '多帧 DTW 匹配',
      component: 'Switch',
      defaultValue: false,
      helpMessage: '开启后累积连续帧特征，与条目中 sequence_features 参考序列做 DTW 时序匹配',
      ifShow: ({ values }) => !!values.pose_intent_enabled,
    },
    {
      field: 'pose_intent_temporal_window',
      label: 'DTW 窗口帧数',
      component: 'InputNumber',
      defaultValue: 6,
      componentProps: { min: 3, max: 30, style: { width: '100%' } },
      ifShow: ({ values }) => !!values.pose_intent_enabled && !!values.pose_intent_temporal_dtw,
    },
    {
      field: 'post_process_enabled',
      label: '启用 AI 后处理',
      component: 'Switch',
      defaultValue: false,
      componentProps: { checkedChildren: '开', unCheckedChildren: '关' },
      helpMessage: '开启后检测结果将投递至后处理脚本进行业务判断；关闭时走默认告警逻辑',
      ifShow: ({ values }) => baseTaskType(values.task_mode) === 'realtime' || baseTaskType(values.task_mode) === 'snap' || baseTaskType(values.task_mode) === 'patrol',
    },
    {
      field: 'post_process_replicas',
      label: '后处理副本数',
      component: 'InputNumber',
      defaultValue: 1,
      componentProps: { min: 1, max: 8, style: { width: '100%' } },
      helpMessage: '后处理 Worker 水平扩展副本数，多副本可提升并发处理能力',
      ifShow: ({ values }) =>
        (baseTaskType(values.task_mode) === 'realtime' || baseTaskType(values.task_mode) === 'snap' || baseTaskType(values.task_mode) === 'patrol') &&
        !!values.post_process_enabled,
    },
    {
      field: 'alert_notification_enabled',
      label: '启用告警通知',
      component: 'Switch',
      defaultValue: false,
      componentProps: {
        checkedChildren: '是',
        unCheckedChildren: '否',
      },
      dynamicDisabled: ({ values }) => isViewMode.value || !values.alert_event_enabled,
      helpMessage: '是否启用告警通知，启用后会在告警事件发生时发送通知',
      ifShow: ({ values }) => (baseTaskType(values.task_mode) === 'realtime' || baseTaskType(values.task_mode) === 'snap' || baseTaskType(values.task_mode) === 'patrol') && values.alert_event_enabled,
    },
    {
      field: 'alarm_suppress_time',
      label: '通知间隔（秒）',
      component: 'InputNumber',
      defaultValue: 300,
      componentProps: {
        placeholder: '300',
        min: 0,
        max: 86400,
        step: 60,
        style: { width: '100%' },
      },
      helpMessage:
        '同一任务两次发送通知的最小间隔，默认 300 秒（5 分钟）。测试阶段可设为 0',
      ifShow: ({ values }) =>
        (baseTaskType(values.task_mode) === 'realtime' || baseTaskType(values.task_mode) === 'snap' || baseTaskType(values.task_mode) === 'patrol') &&
        !!values.alert_event_enabled &&
        !!values.alert_notification_enabled,
    },
    {
      field: 'notification_channels',
      label: '通知渠道',
      component: 'Select',
      componentProps: {
        placeholder: '请选择通知渠道（可多选）',
        options: availableChannels.map(c => ({ label: c.label, value: c.value })),
        mode: 'multiple',
        showSearch: true,
        allowClear: true,
        filterOption: (input: string, option: any) => {
          const label = option?.label || option?.children || '';
          return label.toLowerCase().indexOf(input.toLowerCase()) >= 0;
        },
      },
      helpMessage:
        '企业微信工作通知需先在通知中心配置消息配置、用户分组与消息模板；群机器人/Webhook 仅需模板填写 Webhook',
      ifShow: ({ values }) => (baseTaskType(values.task_mode) === 'realtime' || baseTaskType(values.task_mode) === 'snap' || baseTaskType(values.task_mode) === 'patrol') && values.alert_event_enabled && values.alert_notification_enabled,
    },
    {
      field: 'notification_templates',
      label: '通知模板',
      component: 'Input',
      render: ({ model, values }) => {
        const channels = values?.notification_channels || notificationChannels.value || [];
        if (!channels || channels.length === 0) {
          return h('div', { class: 'notification-templates-empty' }, '请先选择通知渠道');
        }
        return h('div', {
          class: 'notification-templates-wrapper',
          style: {
            display: 'flex',
            flexDirection: 'row',
            gap: '12px',
            alignItems: 'center',
            flexWrap: 'wrap',
            width: '100%',
          }
        }, [
          channels.map((channel: string) => {
            return h(Select, {
              key: channel,
              value: channelTemplates.value[channel],
              placeholder: `请选择${getChannelLabel(channel)}模板`,
              loading: templateLoading.value[channel],
              showSearch: true,
              allowClear: true,
              filterOption: (input: string, option: any) => {
                const label = option?.label || option?.children || '';
                return label.toLowerCase().indexOf(input.toLowerCase()) >= 0;
              },
              options: templates.value[channel]?.map(t => ({ label: t.name, value: t.id })) || [],
              onChange: (value: any) => {
                if (value) {
                  channelTemplates.value[channel] = value;
                } else {
                  delete channelTemplates.value[channel];
                }
              },
              onFocus: () => {
                if (!templates.value[channel]?.length) {
                  loadTemplates(channel);
                }
              },
              disabled: isViewMode.value,
              style: { flex: '1 1 auto', minWidth: '200px', maxWidth: '300px' },
            });
          }),
        ]);
      },
      ifShow: ({ values }) => (baseTaskType(values.task_mode) === 'realtime' || baseTaskType(values.task_mode) === 'snap' || baseTaskType(values.task_mode) === 'patrol') && values.alert_event_enabled && values.alert_notification_enabled && values.notification_channels && values.notification_channels.length > 0,
    },
    {
      field: 'is_full_day_defense',
      label: '是否全天布防',
      component: 'Switch',
      defaultValue: true,
      componentProps: {
        checkedChildren: '是',
        unCheckedChildren: '否',
      },
      suffix: () =>
        h(Popover, {
          trigger: 'hover',
          placement: 'rightTop',
          getPopupContainer: () => document.body,
        }, {
          content: () => h('div', { class: 'defense-tip-content' }, [
            h('div', { class: 'tip-item' }, '全天布防模式下，系统将在24小时内持续监控并执行算法检测任务，不受时间限制。'),
            h('div', { class: 'tip-item' }, '关闭全天布防后，可配置自定义布防时段，仅在指定时间段内执行监控任务，有效节省系统资源。'),
          ]),
          default: () => h(AntButton, {
            type: 'text',
            size: 'small',
            class: 'placeholder-trigger-btn',
          }, {
            icon: () => h(QuestionCircleOutlined),
          }),
        }),
      helpMessage: '开启后将在全天24小时执行监控任务，关闭后可配置自定义布防时段',
    },
  ],
  showActionButtonGroup: false,
});

const modalData = ref<{ type?: string; record?: AlgorithmTask }>({});

const modalTitle = computed(() => {
  if (modalData.value.type === 'view') return '查看算法任务';
  if (modalData.value.type === 'edit') return '编辑算法任务';
  return '新建算法任务';
});

const isViewMode = computed(() => modalData.value.type === 'view');

const [register, { setDrawerProps, closeDrawer }] = useDrawerInner(async (data) => {
  modalData.value = data || {};
  taskId.value = null;
  confirmLoading.value = false;
  resetFields();
  runtimeInfo.value = null;
  void loadRuntimeInfo();

  // 确保默认模型已初始化（在加载前）
  initDefaultModels();

  // 加载选项数据
  await Promise.all([loadDevices(), loadModels(), loadFaceLibraries(), loadPlateLibraries(), loadScenarioPoseLibraries(), loadNodes()]);

  if (modalData.value.record) {
    const record = modalData.value.record;
    taskId.value = record.id;
    // 从 model_ids 中提取模型ID列表（用于回显）
    const modelIds: number[] = [];
    if (record.model_ids && Array.isArray(record.model_ids)) {
      modelIds.push(...record.model_ids);
    } else if (record.model_ids && typeof record.model_ids === 'string') {
      try {
        const parsed = JSON.parse(record.model_ids);
        if (Array.isArray(parsed)) {
          modelIds.push(...parsed);
        }
      } catch (e) {
        console.error('解析model_ids失败', e);
      }
    }

    // 初始化告警通知配置
    if (record.alert_notification_config) {
      try {
        const config = typeof record.alert_notification_config === 'string'
          ? JSON.parse(record.alert_notification_config)
          : record.alert_notification_config;
        alertNotificationConfig.value = {
          enabled: record.alert_notification_enabled || false,
          channels: config.channels || [],
          suppress_time: record.alarm_suppress_time || 300,
        };
        // 恢复通知渠道和模板
        if (config.channels && Array.isArray(config.channels)) {
          notificationChannels.value = config.channels.map((c: any) => c.method);
          config.channels.forEach((channel: any) => {
            channelTemplates.value[channel.method] = channel.template_id;
            // 加载模板列表
            loadTemplates(channel.method);
          });
        }
      } catch (e) {
        console.error('解析告警通知配置失败', e);
        alertNotificationConfig.value = {
          enabled: false,
          channels: [],
          suppress_time: 300,
        };
        notificationChannels.value = [];
        channelTemplates.value = {};
      }
    } else {
      alertNotificationConfig.value = {
        enabled: false,
        channels: [],
        suppress_time: 300,
      };
      notificationChannels.value = [];
      channelTemplates.value = {};
    }

    // 判断是否全天布防（如果 defense_mode 为 'full'，则为全天布防）
    const fullDayDefense = record.defense_mode === 'full';
    isFullDayDefense.value = fullDayDefense;

    // 恢复布防时段配置
    if (fullDayDefense) {
      // 全天布防：设置为全防模式
      defenseSchedule.value = {
        mode: 'full',
        schedule: Array(7).fill(null).map(() => Array(24).fill(1)),
      };
    } else if (record.defense_mode && record.defense_schedule) {
      // 非全天布防：恢复保存的配置
      try {
        const schedule = typeof record.defense_schedule === 'string'
          ? JSON.parse(record.defense_schedule)
          : record.defense_schedule;
        defenseSchedule.value = {
          mode: record.defense_mode || 'half',
          schedule: schedule,
        };
      } catch (e) {
        console.error('解析布防时段配置失败', e);
        // 解析失败时，使用半防模式并清空
        defenseSchedule.value = {
          mode: 'half',
          schedule: Array(7).fill(null).map(() => Array(24).fill(0)),
        };
      }
    } else {
      // 没有配置时，使用半防模式并清空
      defenseSchedule.value = {
        mode: 'half',
        schedule: Array(7).fill(null).map(() => Array(24).fill(0)),
      };
    }

    const editTaskMode = toTaskMode(record.task_type, record.executor);
    runtimeInfoTaskMode.value = editTaskMode;
    await setFieldsValue({
      task_name: record.task_name,
      task_mode: editTaskMode,
      schedule_policy: record.schedule_policy || 'local',
      prefer_gpu: record.prefer_gpu !== false,
      target_node_id: record.target_node_id ?? undefined,
      device_ids: record.device_ids || [],
      cron_expression: record.cron_expression,
      frame_skip: record.frame_skip || 25,
      model_ids: modelIds,
      extract_interval: record.extract_interval ?? 12,
      detect_conf: record.detect_conf ?? 0.5,
      motion_gate_enabled: record.motion_gate_enabled === true,
      motion_sensitivity: record.motion_gate_config?.preset || 'conservative',
      tracking_enabled: record.tracking_enabled || false,
      tracking_similarity_threshold: record.tracking_similarity_threshold || 0.2,
      tracking_max_age: record.tracking_max_age || 25,
      tracking_smooth_alpha: record.tracking_smooth_alpha || 0.25,
      alert_event_enabled: record.alert_event_enabled !== undefined ? record.alert_event_enabled : false,
      alert_event_suppress_time: record.alert_event_suppress_time ?? 5,
      alert_class_names: Array.isArray(record.alert_class_names) ? record.alert_class_names : [],
      face_matching_enabled: record.face_matching_enabled === true,
      face_library_ids: normalizeLibraryIds(record.face_library_ids),
      plate_matching_enabled: record.plate_matching_enabled === true,
      plate_library_ids: normalizeLibraryIds(record.plate_library_ids),
      sam_supplement_enabled: record.sam_supplement_enabled === true,
      sam_pipeline_mode: record.sam_supplement_config?.pipeline_mode || 'open_vocab',
      sam_text_prompts: record.sam_supplement_config?.text_prompts || [],
      sam_trigger: record.sam_supplement_config?.trigger || 'on_interval',
      sam_interval_frames: record.sam_supplement_config?.interval_frames ?? 25,
      sam_conf: record.sam_supplement_config?.conf ?? 0.45,
      pose_analysis_enabled: record.pose_analysis_enabled === true,
      pose_model_file_path: record.pose_analysis_config?.model_file_path || 'yolo26n-pose.pt',
      pose_trigger: record.pose_analysis_config?.trigger || 'on_interval',
      pose_interval_frames: record.pose_analysis_config?.interval_frames ?? 12,
      pose_conf: record.pose_analysis_config?.conf ?? 0.25,
      pose_intent_enabled: record.pose_intent_enabled === true,
      pose_library_ids: normalizeLibraryIds(record.pose_library_ids),
      pose_intent_threshold: record.pose_intent_threshold ?? undefined,
      pose_intent_suppress_sec: record.pose_intent_config?.suppress_same_intent_sec ?? 10,
      pose_intent_draw_skeleton: record.pose_intent_config?.draw_skeleton_on_alert !== false,
      pose_intent_temporal_dtw: record.pose_intent_config?.temporal_dtw_enabled === true,
      pose_intent_temporal_window: record.pose_intent_config?.temporal_window_frames ?? 6,
      post_process_enabled: record.post_process_enabled === true,
      post_process_replicas: record.post_process_replicas ?? 1,
      alarm_suppress_time: record.alarm_suppress_time ?? 300,
      alert_notification_enabled: record.alert_notification_enabled !== undefined ? record.alert_notification_enabled : false,
      notification_channels: notificationChannels.value,
      is_full_day_defense: fullDayDefense,
    });

    // 更新告警通知启用状态
    alertNotificationEnabled.value = record.alert_notification_enabled !== undefined ? record.alert_notification_enabled : false;

    // 更新formValues以便AlertNotificationConfig组件响应
    formValues.value = { ...formValues.value, ...await getFieldsValue() };

    await refreshAlertClassOptions(modelIds, record.alert_class_names || []);

    // 查看模式禁用表单和按钮
    if (modalData.value.type === 'view') {
      updateSchema([
        { field: 'task_name', componentProps: { disabled: true } },
        { field: 'task_mode', componentProps: { disabled: true } },
        { field: 'schedule_policy', componentProps: { disabled: true } },
        { field: 'target_node_id', componentProps: { disabled: true } },
        { field: 'device_ids', componentProps: { disabled: true } },
        { field: 'cron_expression', componentProps: { disabled: true } },
        { field: 'frame_skip', componentProps: { disabled: true } },
        { field: 'model_ids', componentProps: { disabled: true } },
        { field: 'extract_interval', componentProps: { disabled: true } },
        { field: 'detect_conf', componentProps: { disabled: true } },
        { field: 'motion_gate_enabled', componentProps: { disabled: true } },
        { field: 'motion_sensitivity', componentProps: { disabled: true } },
        { field: 'tracking_enabled', componentProps: { disabled: true } },
        { field: 'tracking_similarity_threshold', componentProps: { disabled: true } },
        { field: 'tracking_max_age', componentProps: { disabled: true } },
        { field: 'tracking_smooth_alpha', componentProps: { disabled: true } },
        { field: 'alert_event_enabled', componentProps: { disabled: true } },
        { field: 'alert_class_names', componentProps: { disabled: true } },
        { field: 'alert_event_suppress_time', componentProps: { disabled: true } },
        { field: 'post_process_enabled', componentProps: { disabled: true } },
        { field: 'post_process_replicas', componentProps: { disabled: true } },
        { field: 'alarm_suppress_time', componentProps: { disabled: true } },
        { field: 'alert_notification_enabled', componentProps: { disabled: true } },
        { field: 'notification_channels', componentProps: { disabled: true } },
        { field: 'notification_templates', componentProps: { disabled: true } },
        { field: 'is_full_day_defense', componentProps: { disabled: true } },
      ]);
      setDrawerProps({ showOkBtn: false });
    } else {
      // 编辑模式，确保所有字段可编辑
      updateSchema([
        { field: 'task_name', componentProps: { disabled: false } },
        { field: 'task_mode', componentProps: { disabled: false } },
        { field: 'schedule_policy', componentProps: { disabled: false } },
        { field: 'target_node_id', componentProps: { disabled: false } },
        { field: 'device_ids', componentProps: { disabled: false } },
        { field: 'cron_expression', componentProps: { disabled: false } },
        { field: 'frame_skip', componentProps: { disabled: false } },
        { field: 'model_ids', componentProps: { disabled: false } },
        { field: 'extract_interval', componentProps: { disabled: false } },
        { field: 'detect_conf', componentProps: { disabled: false } },
        { field: 'tracking_enabled', componentProps: { disabled: false } },
        { field: 'tracking_similarity_threshold', componentProps: { disabled: false } },
        { field: 'tracking_max_age', componentProps: { disabled: false } },
        { field: 'tracking_smooth_alpha', componentProps: { disabled: false } },
        { field: 'alert_event_enabled', componentProps: { disabled: false } },
        { field: 'alert_class_names', componentProps: { disabled: false } },
        { field: 'alert_event_suppress_time', componentProps: { disabled: false } },
        { field: 'post_process_enabled', componentProps: { disabled: false } },
        { field: 'post_process_replicas', componentProps: { disabled: false } },
        { field: 'alarm_suppress_time', componentProps: { disabled: false } },
        { field: 'alert_notification_enabled', componentProps: { disabled: false } },
        { field: 'notification_channels', componentProps: { disabled: false } },
        { field: 'notification_templates', componentProps: { disabled: false } },
        { field: 'is_full_day_defense', componentProps: { disabled: false } },
      ]);
      setDrawerProps({ showOkBtn: true });
    }
  } else {
    // 新建模式，设置默认值，并确保所有字段可编辑
    // 先重置所有字段为可编辑状态，避免之前查看模式的disabled状态影响
    updateSchema([
      { field: 'task_name', componentProps: { disabled: false } },
      { field: 'task_mode', componentProps: { disabled: false } },
      { field: 'schedule_policy', componentProps: { disabled: false } },
      { field: 'target_node_id', componentProps: { disabled: false } },
      { field: 'device_ids', componentProps: { disabled: false } },
      { field: 'cron_expression', componentProps: { disabled: false } },
      { field: 'frame_skip', componentProps: { disabled: false } },
      { field: 'model_ids', componentProps: { disabled: false } },
      { field: 'extract_interval', componentProps: { disabled: false } },
      { field: 'detect_conf', componentProps: { disabled: false } },
      { field: 'tracking_enabled', componentProps: { disabled: false } },
      { field: 'tracking_similarity_threshold', componentProps: { disabled: false } },
      { field: 'tracking_max_age', componentProps: { disabled: false } },
      { field: 'tracking_smooth_alpha', componentProps: { disabled: false } },
      { field: 'alert_event_enabled', componentProps: { disabled: false } },
      { field: 'alert_class_names', componentProps: { disabled: false } },
      { field: 'alert_event_suppress_time', componentProps: { disabled: false } },
      { field: 'post_process_enabled', componentProps: { disabled: false } },
      { field: 'post_process_replicas', componentProps: { disabled: false } },
      { field: 'alarm_suppress_time', componentProps: { disabled: false } },
      { field: 'alert_notification_enabled', componentProps: { disabled: false } },
      { field: 'notification_channels', componentProps: { disabled: false } },
      { field: 'notification_templates', componentProps: { disabled: false } },
      { field: 'is_full_day_defense', componentProps: { disabled: false } },
    ]);
    isFullDayDefense.value = true; // 默认全天布防
    runtimeInfoTaskMode.value = 'realtime_cpp';
    await setFieldsValue({
      task_mode: 'realtime_cpp',
      schedule_policy: 'local',
      prefer_gpu: true,
      cron_expression: DEFAULT_SNAP_CRON,
      frame_skip: 25,
      extract_interval: 12,
      detect_conf: 0.5,
      motion_gate_enabled: false,
      motion_sensitivity: 'conservative',
      tracking_enabled: true,
      tracking_similarity_threshold: 0.2,
      tracking_max_age: 25,
      tracking_smooth_alpha: 0.25,
      alert_event_enabled: false, // 默认关闭告警事件
      alert_event_suppress_time: 5,
      alert_class_names: [],
      face_matching_enabled: false,
      plate_matching_enabled: false,
      pose_analysis_enabled: false,
      pose_intent_enabled: false,
      pose_library_ids: [],
      pose_intent_threshold: undefined,
      pose_intent_suppress_sec: 10,
      pose_intent_draw_skeleton: true,
      pose_intent_temporal_dtw: false,
      pose_intent_temporal_window: 6,
      pose_model_file_path: 'yolo26n-pose.pt',
      pose_trigger: 'on_interval',
      pose_interval_frames: 12,
      pose_conf: 0.25,
      post_process_enabled: false,
      post_process_replicas: 1,
      alarm_suppress_time: 300,
      notification_channels: [],
      is_full_day_defense: true, // 默认全天布防
    });
    // 初始化告警通知相关状态
    notificationChannels.value = [];
    channelTemplates.value = {};
    alertNotificationEnabled.value = false;
    alertNotificationConfig.value = {
      enabled: false,
      channels: [],
      suppress_time: 300,
    };
    // 更新formValues
    formValues.value = { ...formValues.value, ...await getFieldsValue() };
    // 重置布防时段为默认值（全天布防）
    defenseSchedule.value = {
      mode: 'full', // 默认全防模式
      schedule: Array(7).fill(null).map(() => Array(24).fill(1)), // 默认全部填充
    };
    setDrawerProps({ showOkBtn: true });
  }
});

// 处理表单字段值变化
const handleFieldValueChange = async (key: string, value: any) => {
  if (key === 'task_mode') {
    runtimeInfoTaskMode.value = String(value || '');
    if (String(value || '').endsWith('_cpp') && !runtimeInfo.value) {
      void loadRuntimeInfo();
    }
  } else if (key === 'is_full_day_defense') {
    isFullDayDefense.value = value !== undefined ? value : true;
    // 如果切换到非全天布防，默认设置为半防模式并清空表格，让用户自己选择
    if (!value) {
      // 半防模式：全部清空，让用户自己选择
      defenseSchedule.value = {
        mode: 'half',
        schedule: Array(7).fill(null).map(() => Array(24).fill(0)),
      };
    } else {
      // 如果切换到全天布防，设置为全防模式
      defenseSchedule.value = {
        mode: 'full',
        schedule: Array(7).fill(null).map(() => Array(24).fill(1)),
      };
    }
  } else if (key === 'alert_event_enabled') {
    // 如果关闭告警事件，同时关闭告警通知
    if (!value) {
      alertNotificationEnabled.value = false;
      alertNotificationConfig.value = {
        enabled: false,
        channels: [],
        suppress_time: 300,
      };
      notificationChannels.value = [];
      channelTemplates.value = {};
      await setFieldsValue({ alert_notification_enabled: false, alert_class_names: [] });
    } else {
      const currentValues = await getFieldsValue();
      await refreshAlertClassOptions(currentValues.model_ids, currentValues.alert_class_names);
    }
    // 立即更新 formValues，确保告警通知配置能够及时响应
    const currentValues = await getFieldsValue();
    formValues.value = { ...currentValues, alert_event_enabled: value };
  } else if (key === 'alert_notification_enabled') {
    // 告警通知启用状态变化时，立即更新 formValues
    alertNotificationEnabled.value = value;
    const currentValues = await getFieldsValue();
    formValues.value = { ...currentValues, alert_notification_enabled: value };
    // 如果关闭告警通知，清空配置
    if (!value) {
      notificationChannels.value = [];
      channelTemplates.value = {};
    }
  } else if (key === 'face_matching_enabled' && !value) {
    await setFieldsValue({ face_library_ids: [] });
  } else if (key === 'plate_matching_enabled' && !value) {
    await setFieldsValue({ plate_library_ids: [] });
  } else if (key === 'pose_intent_enabled' && value) {
    await setFieldsValue({ pose_analysis_enabled: true, pose_trigger: 'on_person' });
  } else if (key === 'pose_intent_enabled' && !value) {
    await setFieldsValue({ pose_library_ids: [] });
  } else if (key === 'pose_analysis_enabled' && !value) {
    await setFieldsValue({ pose_intent_enabled: false, pose_library_ids: [] });
  } else if (key === 'model_ids') {
    const currentValues = await getFieldsValue();
    await refreshAlertClassOptions(value, currentValues.alert_class_names);
  } else if (key === 'schedule_policy' && value !== 'node') {
    await setFieldsValue({ target_node_id: undefined });
    const currentValues = await getFieldsValue();
    formValues.value = { ...currentValues, schedule_policy: value, target_node_id: undefined };
  } else if (key === 'task_mode' && typeof value === 'string' && value.endsWith('_cpp')) {
    const currentValues = await getFieldsValue();
    if (value === 'snap_cpp' && !currentValues.cron_expression?.trim()) {
      await setFieldsValue({ cron_expression: DEFAULT_SNAP_CRON });
    }
    const after = await getFieldsValue();
    formValues.value = { ...after, task_mode: value };
  } else if (key === 'task_mode' && value === 'snap') {
    const currentValues = await getFieldsValue();
    if (!currentValues.cron_expression?.trim()) {
      await setFieldsValue({ cron_expression: DEFAULT_SNAP_CRON });
    }
    formValues.value = { ...currentValues, task_mode: value, cron_expression: currentValues.cron_expression || DEFAULT_SNAP_CRON };
  } else if (key === 'notification_channels') {
    // 通知渠道变化时，同步更新 notificationChannels
    notificationChannels.value = value || [];
    // 移除未选中渠道的模板
    Object.keys(channelTemplates.value).forEach((channel) => {
      if (!value || !value.includes(channel)) {
        delete channelTemplates.value[channel];
      }
    });
    // 加载新选中渠道的模板
    if (value && Array.isArray(value)) {
      value.forEach((channel: string) => {
        if (!templates.value[channel]?.length) {
          loadTemplates(channel);
        }
      });
    }
    // 同步更新 formValues
    const currentValues = await getFieldsValue();
    formValues.value = { ...currentValues, notification_channels: value };
  } else {
    // 其他字段变化时，也同步更新 formValues
    const currentValues = await getFieldsValue();
    formValues.value = { ...currentValues, [key]: value };
  }
};

const handleSubmit = async () => {
  try {
    const values = await validate();
    confirmLoading.value = true;
    setDrawerProps({ confirmLoading: true });

    values.device_ids = await syncSelectedDeviceIds(values.device_ids || []);

    // 六模式：先展开 task_type/executor，保留 task_mode 供后续 if 判断，提交前再删除
    {
      const mapped = fromTaskMode(values.task_mode || values.task_type);
      values.task_type = mapped.task_type;
      values.executor = mapped.executor;
      values.task_mode = toTaskMode(mapped.task_type, mapped.executor);
    }

    // 新建任务时，默认设置为未启用状态（需要通过启动按钮来启动）
    if (modalData.value.type !== 'edit') {
      values.is_enabled = 0;
    }
    // 编辑任务时，不修改 is_enabled 状态（保持原值，通过启动/停止按钮控制）

    // 根据是否全天布防设置布防时段配置
    const fullDayDefense = values.is_full_day_defense !== undefined ? values.is_full_day_defense : true;
    if (fullDayDefense) {
      // 全天布防：设置为全防模式
      values.defense_mode = 'full';
      values.defense_schedule = JSON.stringify(Array(7).fill(null).map(() => Array(24).fill(1)));
    } else {
      // 非全天布防：使用布防时段配置
      values.defense_mode = defenseSchedule.value.mode;
      const schedule = defenseSchedule.value.schedule;

      // 验证非全天布防模式下至少选择了一个时段
      const hasSelectedTime = schedule.some(day => day.some(hour => hour === 1));
      if (!hasSelectedTime) {
        createMessage.error('非全天布防模式下，请至少选择一个布防时段');
        confirmLoading.value = false;
        setDrawerProps({ confirmLoading: false });
        return;
      }

      values.defense_schedule = JSON.stringify(schedule);
    }

    // 移除前端字段，不发送到后端
    delete values.is_full_day_defense;

    // 处理告警通知配置
    // 获取所有已选择模板的渠道
    const selectedChannels = Object.keys(channelTemplates.value).filter(
      (method: string) => channelTemplates.value[method] !== undefined && channelTemplates.value[method] !== null
    );

    if (values.alert_event_enabled) {
      values.alert_event_suppress_time = values.alert_event_suppress_time ?? 5;
      values.alarm_suppress_time = values.alarm_suppress_time ?? 300;
      values.alert_class_names = Array.isArray(values.alert_class_names)
        ? values.alert_class_names.filter((name: string) => String(name || '').trim())
        : [];
      if (!values.alert_class_names.length) {
        createMessage.error('启用告警事件时必须选择至少一个告警触发标签');
        confirmLoading.value = false;
        setDrawerProps({ confirmLoading: false });
        return;
      }
    } else {
      values.alert_class_names = [];
    }

    if (values.alert_event_enabled && values.alert_notification_enabled && selectedChannels.length > 0) {
      values.alert_notification_enabled = true;
      // 构建通知渠道配置
      const channels = selectedChannels.map((method: string) => {
        const templateId = channelTemplates.value[method];
        const template = templates.value[method]?.find((t: any) => t.id === templateId);
        return {
          method,
          template_id: templateId,
          template_name: template?.name || '',
        };
      });
      values.alert_notification_config = {
        channels: channels,
      };
    } else {
      values.alert_notification_enabled = false;
      values.alert_notification_config = null;
    }

    // 人脸/车牌匹配：检测开关与匹配一致；业务标签从所选库透传
    values.face_detection_enabled = !!values.face_matching_enabled;
    values.plate_detection_enabled = !!values.plate_matching_enabled;

    values.face_library_ids = normalizeLibraryIds(values.face_library_ids);
    values.plate_library_ids = normalizeLibraryIds(values.plate_library_ids);

    if (values.face_matching_enabled && !values.face_library_ids.length) {
      createMessage.error('启用人脸匹配时必须选择至少一个人脸库');
      confirmLoading.value = false;
      setDrawerProps({ confirmLoading: false });
      return;
    }
    if (!values.face_matching_enabled) {
      values.face_library_ids = [];
    }
    values.face_matching_threshold = null;
    if (values.plate_matching_enabled && !values.plate_library_ids.length) {
      createMessage.error('启用车牌匹配时必须选择至少一个车牌库');
      confirmLoading.value = false;
      setDrawerProps({ confirmLoading: false });
      return;
    }
    if (!values.plate_matching_enabled) {
      values.plate_library_ids = [];
    }

    values.pose_library_ids = normalizeLibraryIds(values.pose_library_ids);
    if (values.pose_intent_enabled) {
      values.pose_analysis_enabled = true;
      if (!values.pose_library_ids.length) {
        createMessage.error('启用姿态意图分析时必须选择至少一个场景姿态库');
        confirmLoading.value = false;
        setDrawerProps({ confirmLoading: false });
        return;
      }
    } else {
      values.pose_library_ids = [];
      values.pose_intent_threshold = null;
    }

    const propagatedTags = collectMatchingTagsFromLibraries(
      faceLibraries.value,
      plateLibraries.value,
      values.face_library_ids,
      values.plate_library_ids,
      poseLibraries.value,
      values.pose_library_ids,
    );
    values.matching_business_tags = propagatedTags.length ? propagatedTags : undefined;
    if (!values.face_matching_enabled && !values.plate_matching_enabled && !values.pose_intent_enabled) {
      values.matching_business_tags = undefined;
    }
    // 确保 model_ids 是数组格式
    if (values.model_ids && !Array.isArray(values.model_ids)) {
      values.model_ids = [values.model_ids];
    }

    // 算法任务（实时和抓拍）必须指定模型ID列表
    if ((baseTaskType(values.task_mode) === 'realtime' || baseTaskType(values.task_mode) === 'snap' || baseTaskType(values.task_mode) === 'patrol') && (!values.model_ids || values.model_ids.length === 0)) {
      createMessage.error('算法任务必须选择至少一个模型');
      confirmLoading.value = false;
      setDrawerProps({ confirmLoading: false });
      return;
    }

    if (values.schedule_policy === 'node' && !values.target_node_id) {
      createMessage.error('指定节点部署时必须选择目标节点');
      confirmLoading.value = false;
      setDrawerProps({ confirmLoading: false });
      return;
    }
    if (values.schedule_policy !== 'node') {
      values.target_node_id = null;
    }
    if (values.schedule_policy !== 'auto') {
      values.prefer_gpu = true;
    }

    values.sam_supplement_config = values.sam_supplement_enabled
      ? {
          pipeline_mode: values.sam_pipeline_mode || 'open_vocab',
          text_prompts: values.sam_text_prompts || [],
          trigger: values.sam_trigger || 'on_interval',
          interval_frames: values.sam_interval_frames ?? 25,
          conf: values.sam_conf ?? 0.45,
          merge_iou: 0.5,
          return_masks: values.sam_pipeline_mode === 'refine_mask',
        }
      : null;
    delete values.sam_pipeline_mode;
    delete values.sam_text_prompts;
    delete values.sam_trigger;
    delete values.sam_interval_frames;
    delete values.sam_conf;

    values.pose_analysis_config = values.pose_analysis_enabled || values.pose_intent_enabled
      ? {
          model_file_path: values.pose_model_file_path || 'yolo26n-pose.pt',
          trigger: values.pose_trigger || (values.pose_intent_enabled ? 'on_person' : 'on_interval'),
          interval_frames: values.pose_interval_frames ?? 12,
          conf: values.pose_conf ?? 0.25,
        }
      : null;
    delete values.pose_model_file_path;
    delete values.pose_trigger;
    delete values.pose_interval_frames;
    delete values.pose_conf;

    values.pose_intent_config = values.pose_intent_enabled
      ? {
          require_person_detection: true,
          suppress_same_intent_sec: values.pose_intent_suppress_sec ?? 10,
          match_top_k: 1,
          draw_skeleton_on_alert: values.pose_intent_draw_skeleton !== false,
          temporal_dtw_enabled: values.pose_intent_temporal_dtw === true,
          temporal_window_frames: values.pose_intent_temporal_window ?? 6,
          temporal_dtw_threshold: 0.65,
        }
      : null;
    delete values.pose_intent_suppress_sec;
    delete values.pose_intent_draw_skeleton;
    delete values.pose_intent_temporal_dtw;
    delete values.pose_intent_temporal_window;

    if (baseTaskType(values.task_mode) === 'realtime') {
      values.motion_gate_enabled = values.motion_gate_enabled === true;
      values.motion_gate_config = values.motion_gate_enabled
        ? { preset: values.motion_sensitivity || 'conservative' }
        : null;
    } else {
      values.motion_gate_enabled = false;
      values.motion_gate_config = null;
    }
    delete values.motion_sensitivity;

    values.post_process_enabled = !!values.post_process_enabled;
    if (values.post_process_enabled) {
      values.post_process_replicas = Math.max(1, Number(values.post_process_replicas) || 1);
    } else {
      values.post_process_replicas = 1;
    }

    if (baseTaskType(values.task_mode) === 'snap' && values.cron_expression) {
      const cronCheck = validateSnapCronMinInterval(values.cron_expression);
      if (!cronCheck.valid) {
        createMessage.error(cronCheck.message || 'Cron 表达式无效');
        confirmLoading.value = false;
        setDrawerProps({ confirmLoading: false });
        return;
      }
      if (cronCheck.normalized) {
        values.cron_expression = cronCheck.normalized;
      }
    }

    if (baseTaskType(values.task_mode) === 'patrol') {
      values.patrol_mode = 'pool';
      values.focus_device_id = null;
    }

    delete values.task_mode;

    if (modalData.value.type === 'edit' && modalData.value.record) {
      const response = await updateAlgorithmTask(modalData.value.record.id, values);
      // 由于 isTransformResponse: true，成功时返回的是任务对象，而不是包含 code 的响应对象
      if (response && response.id) {
        createMessage.success('更新成功');
        taskId.value = modalData.value.record.id;
        emit('success');
        closeDrawer();
      } else {
        // 如果返回的不是任务对象，可能是错误响应（包含 code 和 msg）
        createMessage.error((response as any)?.msg || '更新失败');
      }
    } else {
      const response = await createAlgorithmTask(values);
      // 由于 isTransformResponse: true，成功时返回的是任务对象，而不是包含 code 的响应对象
      if (response && response.id) {
        taskId.value = response.id;
        createMessage.success('创建成功');
        emit('success');
        closeDrawer();
      } else {
        // 如果返回的不是任务对象，可能是错误响应（包含 code 和 msg）
        createMessage.error((response as any)?.msg || '创建失败');
      }
    }
  } catch (error: any) {
    console.error('提交失败', error);
    // 尝试从错误对象中提取错误消息
    let errorMsg = '提交失败';
    if (error?.response?.data?.msg) {
      errorMsg = error.response.data.msg;
    } else if (error?.data?.msg) {
      errorMsg = error.data.msg;
    } else if (error?.msg) {
      errorMsg = error.msg;
    } else if (typeof error === 'string') {
      errorMsg = error;
    } else if (error?.message) {
      errorMsg = error.message;
    }
    createMessage.error(errorMsg);
  } finally {
    confirmLoading.value = false;
    setDrawerProps({ confirmLoading: false });
  }
};

// 重置表单
const handleReset = () => {
  resetFields();
  // 如果是新建模式，重置为默认值
  if (!modalData.value.record) {
    isFullDayDefense.value = true; // 默认全天布防
    setFieldsValue({
      task_mode: 'realtime_cpp',
      schedule_policy: 'local',
      prefer_gpu: true,
      target_node_id: undefined,
      frame_skip: 25,
      extract_interval: 12,
      detect_conf: 0.5,
      motion_gate_enabled: false,
      motion_sensitivity: 'conservative',
      tracking_enabled: true,
      tracking_similarity_threshold: 0.2,
      tracking_max_age: 25,
      tracking_smooth_alpha: 0.25,
      alert_event_enabled: false, // 默认关闭告警事件
      alert_event_suppress_time: 5,
      alert_class_names: [],
      face_matching_enabled: false,
      plate_matching_enabled: false,
      pose_analysis_enabled: false,
      pose_intent_enabled: false,
      pose_library_ids: [],
      pose_intent_threshold: undefined,
      pose_intent_suppress_sec: 10,
      pose_intent_draw_skeleton: true,
      pose_intent_temporal_dtw: false,
      pose_intent_temporal_window: 6,
      pose_model_file_path: 'yolo26n-pose.pt',
      pose_trigger: 'on_interval',
      pose_interval_frames: 12,
      pose_conf: 0.25,
      post_process_enabled: false,
      post_process_replicas: 1,
      alarm_suppress_time: 300,
      is_full_day_defense: true, // 默认全天布防
    });
    alertNotificationConfig.value = { enabled: false, channels: [], suppress_time: 300 };
    // 重置布防时段为默认值（全天布防）
    defenseSchedule.value = {
      mode: 'full', // 默认全防模式
      schedule: Array(7).fill(null).map(() => Array(24).fill(1)), // 默认全部填充
    };
  } else {
    // 如果是编辑模式，恢复到原始值
    const record = modalData.value.record;
    // 从 model_ids 中提取模型ID列表（用于回显）
    const modelIds: number[] = [];
    if (record.model_ids && Array.isArray(record.model_ids)) {
      modelIds.push(...record.model_ids);
    } else if (record.model_ids && typeof record.model_ids === 'string') {
      try {
        const parsed = JSON.parse(record.model_ids);
        if (Array.isArray(parsed)) {
          modelIds.push(...parsed);
        }
      } catch (e) {
        console.error('解析model_ids失败', e);
      }
    }

    // 判断是否全天布防
    const fullDayDefense = record.defense_mode === 'full';
    isFullDayDefense.value = fullDayDefense;

    const viewTaskMode = toTaskMode(record.task_type, record.executor);
    runtimeInfoTaskMode.value = viewTaskMode;
    setFieldsValue({
      task_name: record.task_name,
      task_mode: viewTaskMode,
      schedule_policy: record.schedule_policy || 'local',
      prefer_gpu: record.prefer_gpu !== false,
      target_node_id: record.target_node_id ?? undefined,
      device_ids: record.device_ids || [],
      cron_expression: record.cron_expression,
      frame_skip: record.frame_skip || 25,
      model_ids: modelIds,
      extract_interval: record.extract_interval ?? 12,
      detect_conf: record.detect_conf ?? 0.5,
      motion_gate_enabled: record.motion_gate_enabled === true,
      motion_sensitivity: record.motion_gate_config?.preset || 'conservative',
      tracking_enabled: record.tracking_enabled || false,
      tracking_similarity_threshold: record.tracking_similarity_threshold || 0.2,
      tracking_max_age: record.tracking_max_age || 25,
      tracking_smooth_alpha: record.tracking_smooth_alpha || 0.25,
      alert_event_enabled: record.alert_event_enabled !== undefined ? record.alert_event_enabled : false,
      alert_event_suppress_time: record.alert_event_suppress_time ?? 5,
      alert_class_names: Array.isArray(record.alert_class_names) ? record.alert_class_names : [],
      post_process_enabled: record.post_process_enabled === true,
      post_process_replicas: record.post_process_replicas ?? 1,
      alarm_suppress_time: record.alarm_suppress_time ?? 300,
      alert_notification_enabled: record.alert_notification_enabled !== undefined ? record.alert_notification_enabled : false,
      is_full_day_defense: fullDayDefense,
    });

    // 恢复布防时段配置
    if (fullDayDefense) {
      // 全天布防：设置为全防模式
      defenseSchedule.value = {
        mode: 'full',
        schedule: Array(7).fill(null).map(() => Array(24).fill(1)),
      };
    } else if (record.defense_mode && record.defense_schedule) {
      // 非全天布防：恢复保存的配置
      try {
        const schedule = typeof record.defense_schedule === 'string'
          ? JSON.parse(record.defense_schedule)
          : record.defense_schedule;
        defenseSchedule.value = {
          mode: record.defense_mode || 'half',
          schedule: schedule,
        };
      } catch (e) {
        console.error('解析布防时段配置失败', e);
        // 解析失败时，使用半防模式并清空
        defenseSchedule.value = {
          mode: 'half',
          schedule: Array(7).fill(null).map(() => Array(24).fill(0)),
        };
      }
    } else {
      // 没有配置时，使用半防模式并清空
      defenseSchedule.value = {
        mode: 'half',
        schedule: Array(7).fill(null).map(() => Array(24).fill(0)),
      };
    }
    refreshAlertClassOptions(modelIds, record.alert_class_names || []);
  }
};
</script>

<style lang="less" scoped>
.basic-config-content {
  display: flex;
  flex-direction: column;
  gap: 12px;

  .runtime-version-banner {
    margin-bottom: 0;
  }

  .defense-schedule-wrapper {
    margin-top: 8px;
  }

  .notification-templates-wrapper {
    display: flex !important;
    flex-direction: row !important;
    gap: 12px !important;
    align-items: center !important;
    flex-wrap: wrap !important;
    width: 100% !important;

    :deep(.ant-select) {
      flex: 1 1 auto !important;
      min-width: 200px !important;
      max-width: 300px !important;
    }
  }

  .notification-templates-empty {
    color: rgba(0, 0, 0, 0.45);
    font-size: 14px;
  }
}

:deep(.ant-tabs-content-holder) {
  max-height: calc(100vh - 200px);
  overflow-y: auto;
}

:deep(.ant-tabs-tabpane) {
  padding: 0;
}

.footer-buttons {
  display: flex;
  justify-content: flex-end;
  align-items: center;
}

.alert-notification-enabled-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}

.alert-event-enabled-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}

.full-day-defense-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}

.defense-tip-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 280px;
  line-height: 1.6;
  color: #fff;

  .tip-item {
    font-size: 13px;
  }
}

.placeholder-trigger-btn {
  padding: 0;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #8c8c8c;

  &:hover {
    color: #1890ff;
  }
}

.placeholder-box-small {
  display: flex;
  flex-direction: column;
  gap: 8px;
  background-color: #000;
  padding: 12px;
  border-radius: 4px;
  min-width: 200px;
}

.placeholder-item-small {
  display: flex;
  align-items: center;
  line-height: 1.5;
  font-size: 12px;
  color: #fff;
  font-family: 'Courier New', 'Consolas', 'Monaco', monospace;
}

.placeholder-text {
  color: #52c41a;
  font-weight: 500;
}

.placeholder-separator {
  color: #fff;
  margin: 0 4px;
}

.placeholder-desc {
  color: #fff;
}

// Popover 样式覆盖
:deep(.ant-popover-inner) {
  background-color: #000;
}

:deep(.ant-popover-inner-content) {
  background-color: #000;
  color: #fff;
}

:deep(.ant-popover-title) {
  background-color: #000;
  color: #fff;
  border-bottom-color: #333;
}
</style>
