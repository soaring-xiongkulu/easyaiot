<template>
  <BasicDrawer 
    v-bind="$attrs" 
    @register="register" 
    :title="modalTitle" 
    @ok="handleSubmit"
    width="1400"
    placement="right"
    :showFooter="true"
    :showCancelBtn="false"
    :showOkBtn="false"
  >
    <template #footer>
      <div class="footer-buttons">
        <a-button v-if="!isViewMode" @click="handleReset" class="mr-2">重置</a-button>
        <a-button v-if="!isViewMode" type="primary" :loading="confirmLoading" @click="handleSubmit">提交</a-button>
      </div>
    </template>
    <a-tabs v-model:activeKey="activeTab">
      <a-tab-pane key="basic" tab="基础配置">
        <div class="basic-config-content">
          <BasicForm @register="registerForm" @field-value-change="handleFieldValueChange" />
          <div class="defense-schedule-wrapper" v-if="!isFullDayDefense">
            <a-divider orientation="left">布防时段配置</a-divider>
            <DefenseSchedulePicker
              v-model:modelValue="defenseSchedule"
              :disabled="isViewMode"
            />
          </div>
          <!-- 告警通知配置 -->
          <div class="alert-notification-wrapper" v-if="showAlertNotificationConfig">
            <!-- 告警抑制时间 -->
            <a-form-item label="告警抑制时间（秒）" help="防止频繁通知，默认300秒（5分钟）">
              <a-input-number
                :value="alertNotificationConfig.suppress_time"
                :min="0"
                :max="3600"
                :step="60"
                placeholder="300"
                :disabled="isViewMode"
                @change="(value) => { alertNotificationConfig.suppress_time = value || 300; }"
                style="width: 100%"
              />
            </a-form-item>
          </div>
        </div>
      </a-tab-pane>
      <a-tab-pane key="status" tab="服务状态" :disabled="!taskId">
        <ServiceStatusTab
          v-if="taskId && formValues"
          :task="formValues"
        />
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
import { Switch, Popover, Button, Select } from 'ant-design-vue';
import {
  createAlgorithmTask,
  updateAlgorithmTask,
  type AlgorithmTask,
} from '@/api/device/algorithm_task';
import { getDeviceList, getDeviceConflicts } from '@/api/device/camera';
import { getModelPage } from '@/api/device/model';
import { notifyTemplateQueryByType } from '@/api/device/notice';
import DefenseSchedulePicker from './DefenseSchedulePicker.vue';
import ServiceStatusTab from './ServiceStatusTab.vue';

defineOptions({ name: 'AlgorithmTaskModal' });

const { createMessage } = useMessage();
const emit = defineEmits(['success', 'register']);

const activeTab = ref('basic');
const taskId = ref<number | null>(null);
const formValues = ref<any>({});
const confirmLoading = ref(false);
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
];
const modelOptions = ref<Array<{ label: string; value: number }>>([...defaultModels]);
const modelMap = ref<Map<number, any>>(new Map()); // 存储完整的模型信息

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

// 加载设备列表
const loadDevices = async () => {
  try {
    // 并行加载设备列表和冲突列表
    const [deviceResponse, conflictResponse] = await Promise.all([
      getDeviceList({ pageNo: 1, pageSize: 1000 }),
      getDeviceConflicts('algorithm')
    ]);
    
    // 获取冲突的摄像头ID列表
    const conflictDeviceIds = conflictResponse.code === 0 && conflictResponse.data 
      ? new Set(conflictResponse.data) 
      : new Set();
    
    deviceOptions.value = (deviceResponse.data || []).map((item) => {
      const isDisabled = conflictDeviceIds.has(item.id);
      return {
        label: `${item.name || item.id}${isDisabled ? ' (已在推流转发任务中使用)' : ''}`,
        value: item.id,
        disabled: isDisabled,
      };
    });
    
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
    
    // 更新表单schema，设置模型选项
    updateSchema({
      field: 'model_ids',
      componentProps: {
        options: modelOptions.value,
      },
    });
  } catch (error) {
    console.error('加载模型列表失败', error);
    // 即使加载失败，也确保默认模型显示
    modelOptions.value = defaultModels;
    
    // 更新表单schema，设置默认模型选项
    updateSchema({
      field: 'model_ids',
      componentProps: {
        options: modelOptions.value,
      },
    });
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
      field: 'task_type',
      label: '任务类型',
      component: 'Select',
      required: true,
      componentProps: {
        placeholder: '请选择任务类型',
        options: [
          { label: '实时算法任务', value: 'realtime' },
          { label: '抓拍算法任务', value: 'snap' },
        ],
      },
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
      ifShow: ({ values }) => values.task_type === 'realtime' || values.task_type === 'snap',
    },
    {
      field: 'cron_expression',
      label: 'Cron表达式',
      component: 'Input',
      required: true,
      componentProps: {
        placeholder: '例如: 0 */5 * * * * (每5分钟)',
      },
      helpMessage: '标准Cron表达式，例如: 0 */5 * * * * 表示每5分钟执行一次',
      ifShow: ({ values }) => values.task_type === 'snap',
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
      ifShow: ({ values }) => values.task_type === 'snap',
    },
    {
      field: 'extract_interval',
      label: '抽帧间隔',
      component: 'InputNumber',
      componentProps: {
        placeholder: '每N帧抽一次',
        min: 1,
      },
      helpMessage: '实时算法任务中，每N帧抽一次进行检测（默认25）',
      ifShow: ({ values }) => values.task_type === 'realtime',
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
      ifShow: ({ values }) => values.task_type === 'realtime',
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
      ifShow: ({ values }) => values.task_type === 'realtime' && values.tracking_enabled,
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
      ifShow: ({ values }) => values.task_type === 'realtime' && values.tracking_enabled,
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
      ifShow: ({ values }) => values.task_type === 'realtime' && values.tracking_enabled,
    },
    {
      field: 'alert_event_enabled',
      label: '启用告警事件',
      component: 'Input',
      render: ({ model }) => {
        return h('div', { class: 'alert-event-enabled-wrapper' }, [
          h(Switch, {
            checked: model.alert_event_enabled,
        checkedChildren: '是',
        unCheckedChildren: '否',
            disabled: isViewMode.value,
            onChange: async (checked: boolean) => {
              model.alert_event_enabled = checked;
              // 立即更新 formValues，确保 AlertNotificationConfig 组件能够及时响应
              const currentValues = await getFieldsValue();
              formValues.value = { ...currentValues, alert_event_enabled: checked };
              // 如果关闭告警事件，同时关闭告警通知
              if (!checked) {
                alertNotificationEnabled.value = false;
                alertNotificationConfig.value = {
                  enabled: false,
                  channels: [],
                  suppress_time: 300,
                };
              }
            },
          }),
          h(Popover, {
            title: '算法任务占位符',
            trigger: 'hover',
            placement: 'rightTop',
            getPopupContainer: (triggerNode) => triggerNode.parentElement || document.body,
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
            default: () => h(Button, {
              type: 'text',
              size: 'small',
              class: 'placeholder-trigger-btn',
            }, {
              icon: () => h(QuestionCircleOutlined),
            }),
          }),
        ]);
      },
      helpMessage: '是否启用告警事件，启用后会记录告警信息',
      ifShow: ({ values }) => values.task_type === 'realtime' || values.task_type === 'snap',
    },
    {
      field: 'alert_notification_enabled',
      label: '启用告警通知',
      component: 'Input',
      render: ({ model }) => {
        return h('div', { class: 'alert-notification-enabled-wrapper' }, [
          h(Switch, {
            checked: model.alert_notification_enabled,
            checkedChildren: '是',
            unCheckedChildren: '否',
            disabled: isViewMode.value || !model.alert_event_enabled,
            onChange: async (checked: boolean) => {
              model.alert_notification_enabled = checked;
              alertNotificationEnabled.value = checked;
              // 立即同步更新 formValues，确保响应式更新
              formValues.value = {
                ...formValues.value,
                alert_notification_enabled: checked
              };
              // 异步更新完整表单值（用于提交）
              const currentValues = await getFieldsValue();
              formValues.value = { ...currentValues, alert_notification_enabled: checked };
              // 如果关闭告警通知，清空配置
              if (!checked) {
                notificationChannels.value = [];
                channelTemplates.value = {};
              }
            },
          }),
        ]);
      },
      helpMessage: '是否启用告警通知，启用后会在告警事件发生时发送通知',
      ifShow: ({ values }) => (values.task_type === 'realtime' || values.task_type === 'snap') && values.alert_event_enabled,
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
      ifShow: ({ values }) => (values.task_type === 'realtime' || values.task_type === 'snap') && values.alert_event_enabled && values.alert_notification_enabled,
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
      ifShow: ({ values }) => (values.task_type === 'realtime' || values.task_type === 'snap') && values.alert_event_enabled && values.alert_notification_enabled && values.notification_channels && values.notification_channels.length > 0,
    },
    {
      field: 'is_full_day_defense',
      label: '是否全天布防',
      component: 'Input',
      render: ({ model }) => {
        return h('div', { class: 'full-day-defense-wrapper' }, [
          h(Switch, {
            checked: model.is_full_day_defense,
            checkedChildren: '是',
            unCheckedChildren: '否',
            disabled: isViewMode.value,
            onChange: async (checked: boolean) => {
              model.is_full_day_defense = checked;
              // 使用 setFieldsValue 更新表单值，这会触发 field-value-change 事件
              await setFieldsValue({ is_full_day_defense: checked });
              // 手动触发 handleFieldValueChange 以确保 isFullDayDefense 状态立即更新
              handleFieldValueChange('is_full_day_defense', checked);
            },
          }),
          h(Popover, {
            trigger: 'hover',
            placement: 'rightTop',
            getPopupContainer: (triggerNode) => triggerNode.parentElement || document.body,
          }, {
            content: () => h('div', { class: 'defense-tip-content' }, [
              h('div', { class: 'tip-item' }, '全天布防模式下，系统将在24小时内持续监控并执行算法检测任务，不受时间限制。'),
              h('div', { class: 'tip-item' }, '关闭全天布防后，可配置自定义布防时段，仅在指定时间段内执行监控任务，有效节省系统资源。'),
            ]),
            default: () => h(Button, {
              type: 'text',
              size: 'small',
              class: 'placeholder-trigger-btn',
            }, {
              icon: () => h(QuestionCircleOutlined),
            }),
          }),
        ]);
      },
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

// 计算属性：是否显示告警通知配置
const showAlertNotificationConfig = computed(() => {
  return formValues.value?.alert_event_enabled && 
         (formValues.value?.alert_notification_enabled || alertNotificationEnabled.value) && 
         (formValues.value?.task_type === 'realtime' || formValues.value?.task_type === 'snap');
});

const [register, { setDrawerProps, closeDrawer }] = useDrawerInner(async (data) => {
  modalData.value = data || {};
  taskId.value = null;
  confirmLoading.value = false;
  resetFields();
  
  // 确保默认模型已初始化（在加载前）
  initDefaultModels();
  
  // 先更新表单schema，确保默认模型能立即显示
  updateSchema({
    field: 'model_ids',
    componentProps: {
      options: modelOptions.value,
    },
  });
  
  // 加载选项数据
  await Promise.all([loadDevices(), loadModels()]);
  
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
    
    await setFieldsValue({
      task_name: record.task_name,
      task_type: record.task_type || 'realtime',
      device_ids: record.device_ids || [],
      cron_expression: record.cron_expression,
      frame_skip: record.frame_skip || 25,
      model_ids: modelIds,
      extract_interval: record.extract_interval || 25,
      tracking_enabled: record.tracking_enabled || false,
      tracking_similarity_threshold: record.tracking_similarity_threshold || 0.2,
      tracking_max_age: record.tracking_max_age || 25,
      tracking_smooth_alpha: record.tracking_smooth_alpha || 0.25,
      alert_event_enabled: record.alert_event_enabled !== undefined ? record.alert_event_enabled : false,
      alert_notification_enabled: record.alert_notification_enabled !== undefined ? record.alert_notification_enabled : false,
      notification_channels: notificationChannels.value,
      is_full_day_defense: fullDayDefense,
    });
    
    // 更新告警通知启用状态
    alertNotificationEnabled.value = record.alert_notification_enabled !== undefined ? record.alert_notification_enabled : false;
    
    // 更新formValues以便AlertNotificationConfig组件响应
    formValues.value = { ...formValues.value, ...await getFieldsValue() };
    
    // 查看模式禁用表单和按钮
    if (modalData.value.type === 'view') {
      updateSchema([
        { field: 'task_name', componentProps: { disabled: true } },
        { field: 'task_type', componentProps: { disabled: true } },
        { field: 'device_ids', componentProps: { disabled: true } },
        { field: 'cron_expression', componentProps: { disabled: true } },
        { field: 'frame_skip', componentProps: { disabled: true } },
        { field: 'model_ids', componentProps: { disabled: true } },
        { field: 'extract_interval', componentProps: { disabled: true } },
        { field: 'tracking_enabled', componentProps: { disabled: true } },
        { field: 'tracking_similarity_threshold', componentProps: { disabled: true } },
        { field: 'tracking_max_age', componentProps: { disabled: true } },
        { field: 'tracking_smooth_alpha', componentProps: { disabled: true } },
        { field: 'alert_event_enabled', componentProps: { disabled: true } },
        { field: 'alert_notification_enabled', componentProps: { disabled: true } },
        { field: 'notification_channels', componentProps: { disabled: true } },
        { field: 'notification_templates', componentProps: { disabled: true } },
        { field: 'is_full_day_defense', componentProps: { disabled: true } },
      ]);
      setDrawerProps({ showOkBtn: false });
    } else {
      setDrawerProps({ showOkBtn: true });
    }
  } else {
    // 新建模式，设置默认值
    isFullDayDefense.value = true; // 默认全天布防
    await setFieldsValue({
      task_type: 'realtime',
      frame_skip: 25,
      extract_interval: 25,
      tracking_enabled: false,
      tracking_similarity_threshold: 0.2,
      tracking_max_age: 25,
      tracking_smooth_alpha: 0.25,
      alert_event_enabled: false, // 默认关闭告警事件
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
  if (key === 'is_full_day_defense') {
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
      values.alarm_suppress_time = alertNotificationConfig.value.suppress_time || 300;
    } else {
      values.alert_notification_enabled = false;
      values.alert_notification_config = null;
    }
    
    
    // 确保 model_ids 是数组格式
    if (values.model_ids && !Array.isArray(values.model_ids)) {
      values.model_ids = [values.model_ids];
    }
    
    // 算法任务（实时和抓拍）必须指定模型ID列表
    if ((values.task_type === 'realtime' || values.task_type === 'snap') && (!values.model_ids || values.model_ids.length === 0)) {
      createMessage.error('算法任务必须选择至少一个模型');
      confirmLoading.value = false;
      setDrawerProps({ confirmLoading: false });
      return;
    }
    
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
        task_type: 'realtime',
        frame_skip: 25,
        extract_interval: 25,
        tracking_enabled: false,
        tracking_similarity_threshold: 0.2,
        tracking_max_age: 25,
        tracking_smooth_alpha: 0.25,
      alert_event_enabled: false, // 默认关闭告警事件
        is_full_day_defense: true, // 默认全天布防
      });
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
      
      setFieldsValue({
        task_name: record.task_name,
        task_type: record.task_type || 'realtime',
        device_ids: record.device_ids || [],
        cron_expression: record.cron_expression,
        frame_skip: record.frame_skip || 25,
        model_ids: modelIds,
        extract_interval: record.extract_interval || 25,
        tracking_enabled: record.tracking_enabled || false,
        tracking_similarity_threshold: record.tracking_similarity_threshold || 0.2,
      tracking_max_age: record.tracking_max_age || 25,
      tracking_smooth_alpha: record.tracking_smooth_alpha || 0.25,
      alert_event_enabled: record.alert_event_enabled !== undefined ? record.alert_event_enabled : false,
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
  }
};
</script>

<style lang="less" scoped>
.basic-config-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
  
  .defense-schedule-wrapper {
    margin-top: 8px;
  }
  
    .alert-notification-wrapper {
    margin-top: 8px;
    
    :deep(.ant-divider) {
      margin: 16px 0;
    }
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

