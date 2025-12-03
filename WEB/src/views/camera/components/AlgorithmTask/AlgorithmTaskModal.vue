<template>
  <BasicDrawer 
    v-bind="$attrs" 
    @register="register" 
    :title="modalTitle" 
    @ok="handleSubmit"
    width="1200"
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
import { ref, computed } from 'vue';
import { BasicDrawer, useDrawerInner } from '@/components/Drawer';
import { BasicForm, useForm } from '@/components/Form';
import { useMessage } from '@/hooks/web/useMessage';
import {
  createAlgorithmTask,
  updateAlgorithmTask,
  type AlgorithmTask,
} from '@/api/device/algorithm_task';
import { getDeviceList } from '@/api/device/camera';
import { getSnapSpaceList } from '@/api/device/snap';
import { getModelPage } from '@/api/device/model';
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
const defenseSchedule = ref<{ mode: string; schedule: number[][] }>({
  mode: 'full',
  schedule: Array(7).fill(null).map(() => Array(24).fill(1)),
});

const deviceOptions = ref<Array<{ label: string; value: string }>>([]);
const spaceOptions = ref<Array<{ label: string; value: number }>>([]);
const modelOptions = ref<Array<{ label: string; value: number }>>([]);
const modelMap = ref<Map<number, any>>(new Map()); // 存储完整的模型信息

// 加载设备列表
const loadDevices = async () => {
  try {
    const response = await getDeviceList({ pageNo: 1, pageSize: 1000 });
    deviceOptions.value = (response.data || []).map((item) => ({
      label: item.name || item.id,
      value: item.id,
    }));
  } catch (error) {
    console.error('加载设备列表失败', error);
  }
};

// 加载抓拍空间列表
const loadSpaces = async () => {
  try {
    const response = await getSnapSpaceList({ pageNo: 1, pageSize: 1000 });
    spaceOptions.value = (response.data || []).map((item) => ({
      label: item.space_name,
      value: item.id,
    }));
  } catch (error) {
    console.error('加载抓拍空间列表失败', error);
  }
};


// 加载模型列表（用于选择模型）
const loadModels = async () => {
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
    
    // 清空之前的映射
    modelMap.value.clear();
    
    // 构建选项列表和完整模型信息映射
    const dbModelOptions = allModels.map((item: any) => {
      // 保存完整的模型信息
      modelMap.value.set(item.id, item);
      
      return {
        label: `${item.name}${item.version ? ` (v${item.version})` : ''}`,
        value: item.id, // 模型ID
      };
    });
    
    // 添加默认模型选项（yolo11n.pt、yolov8n.pt）
    // 使用负数ID来标识默认模型，避免与数据库中的模型ID冲突
    const defaultModels = [
      {
        label: 'yolo11n.pt (默认模型)',
        value: -1, // 使用 -1 表示 yolo11n.pt
      },
      {
        label: 'yolov8n.pt (默认模型)',
        value: -2, // 使用 -2 表示 yolov8n.pt
      },
    ];
    
    // 保存默认模型信息到映射中
    modelMap.value.set(-1, {
      id: -1,
      name: 'yolo11n.pt',
      model_path: 'yolo11n.pt',
      version: '默认',
    });
    modelMap.value.set(-2, {
      id: -2,
      name: 'yolov8n.pt',
      model_path: 'yolov8n.pt',
      version: '默认',
    });
    
    // 将默认模型放在最前面，然后添加数据库中的模型
    modelOptions.value = [...defaultModels, ...dbModelOptions];
  } catch (error) {
    console.error('加载模型列表失败', error);
  }
};

const [registerForm, { setFieldsValue, validate, resetFields, updateSchema, getFieldsValue }] = useForm({
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
      field: 'space_id',
      label: '抓拍空间',
      component: 'Select',
      required: true,
      componentProps: {
        placeholder: '请选择抓拍空间',
        options: spaceOptions,
      },
      ifShow: ({ values }) => values.task_type === 'snap',
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
      helpMessage: '抽帧模式下，每N帧抓一次（默认1）',
      ifShow: ({ values }) => values.task_type === 'snap',
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
      ifShow: ({ values }) => values.task_type === 'realtime',
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
      field: 'alert_hook_enabled',
      label: '启用告警Hook',
      component: 'Switch',
      componentProps: {
        checkedChildren: '是',
        unCheckedChildren: '否',
      },
      helpMessage: '是否启用告警Hook接口，启用后会接收实时分析中的告警信息并存储到Kafka（默认开启，接口地址固定）',
      ifShow: ({ values }) => values.task_type === 'realtime',
    },
    {
      field: 'is_full_day_defense',
      label: '是否全天布防',
      component: 'Switch',
      componentProps: {
        checkedChildren: '是',
        unCheckedChildren: '否',
      },
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
  
  // 加载选项数据
  await Promise.all([loadDevices(), loadSpaces(), loadModels()]);
  
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
    
    // 恢复布防时段配置
    if (record.defense_mode && record.defense_schedule) {
      try {
        const schedule = typeof record.defense_schedule === 'string' 
          ? JSON.parse(record.defense_schedule) 
          : record.defense_schedule;
        defenseSchedule.value = {
          mode: record.defense_mode,
          schedule: schedule,
        };
      } catch (e) {
        console.error('解析布防时段配置失败', e);
        defenseSchedule.value = {
          mode: 'full',
          schedule: Array(7).fill(null).map(() => Array(24).fill(1)),
        };
      }
    } else {
      defenseSchedule.value = {
        mode: 'full',
        schedule: Array(7).fill(null).map(() => Array(24).fill(1)),
      };
    }
    
    // 判断是否全天布防（如果 defense_mode 为 'full'，则为全天布防）
    const fullDayDefense = record.defense_mode === 'full';
    isFullDayDefense.value = fullDayDefense;
    
    await setFieldsValue({
      task_name: record.task_name,
      task_type: record.task_type || 'realtime',
      device_ids: record.device_ids || [],
      space_id: record.space_id,
      cron_expression: record.cron_expression,
      frame_skip: record.frame_skip || 1,
      model_ids: modelIds,
      extract_interval: record.extract_interval || 25,
      tracking_enabled: record.tracking_enabled || false,
      tracking_similarity_threshold: record.tracking_similarity_threshold || 0.2,
      tracking_max_age: record.tracking_max_age || 25,
      tracking_smooth_alpha: record.tracking_smooth_alpha || 0.25,
      alert_hook_enabled: record.alert_hook_enabled !== undefined ? record.alert_hook_enabled : true,
      is_full_day_defense: fullDayDefense,
    });
    
    // 查看模式禁用表单和按钮
    if (modalData.value.type === 'view') {
      updateSchema([
        { field: 'task_name', componentProps: { disabled: true } },
        { field: 'task_type', componentProps: { disabled: true } },
        { field: 'device_ids', componentProps: { disabled: true } },
        { field: 'space_id', componentProps: { disabled: true } },
        { field: 'cron_expression', componentProps: { disabled: true } },
        { field: 'frame_skip', componentProps: { disabled: true } },
        { field: 'model_ids', componentProps: { disabled: true } },
        { field: 'extract_interval', componentProps: { disabled: true } },
        { field: 'tracking_enabled', componentProps: { disabled: true } },
        { field: 'tracking_similarity_threshold', componentProps: { disabled: true } },
        { field: 'tracking_max_age', componentProps: { disabled: true } },
        { field: 'tracking_smooth_alpha', componentProps: { disabled: true } },
        { field: 'alert_hook_enabled', componentProps: { disabled: true } },
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
      frame_skip: 1,
      extract_interval: 25,
      tracking_enabled: false,
      tracking_similarity_threshold: 0.2,
      tracking_max_age: 25,
      tracking_smooth_alpha: 0.25,
      alert_hook_enabled: true, // 默认开启告警Hook
      is_full_day_defense: true, // 默认全天布防
    });
    // 重置布防时段为默认值（全天布防）
    defenseSchedule.value = {
      mode: 'full', // 默认全防模式
      schedule: Array(7).fill(null).map(() => Array(24).fill(1)), // 默认全部填充
    };
    setDrawerProps({ showOkBtn: true });
  }
});

// 处理表单字段值变化
const handleFieldValueChange = (key: string, value: any) => {
  if (key === 'is_full_day_defense') {
    isFullDayDefense.value = value !== undefined ? value : true;
    // 如果切换到非全天布防，设置为半防模式并清空，让用户自己选择
    if (!value) {
      defenseSchedule.value = {
        mode: 'half',
        schedule: Array(7).fill(null).map(() => Array(24).fill(0)), // 清空，让用户自己选择
      };
    } else {
      // 如果切换到全天布防，设置为全防模式
      defenseSchedule.value = {
        mode: 'full',
        schedule: Array(7).fill(null).map(() => Array(24).fill(1)),
      };
    }
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
      values.defense_schedule = JSON.stringify(defenseSchedule.value.schedule);
    }
    
    // 移除前端字段，不发送到后端
    delete values.is_full_day_defense;
    
    // 确保 model_ids 是数组格式
    if (values.model_ids && !Array.isArray(values.model_ids)) {
      values.model_ids = [values.model_ids];
    }
    
    // 实时算法任务必须指定模型ID列表
    if (values.task_type === 'realtime' && (!values.model_ids || values.model_ids.length === 0)) {
      createMessage.error('实时算法任务必须选择至少一个模型');
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
  } catch (error) {
    console.error('提交失败', error);
    createMessage.error('提交失败');
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
        frame_skip: 1,
        extract_interval: 25,
        tracking_enabled: false,
        tracking_similarity_threshold: 0.2,
        tracking_max_age: 25,
        tracking_smooth_alpha: 0.25,
        alert_hook_enabled: true, // 默认开启告警Hook
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
        space_id: record.space_id,
        cron_expression: record.cron_expression,
        frame_skip: record.frame_skip || 1,
        model_ids: modelIds,
        extract_interval: record.extract_interval || 25,
        tracking_enabled: record.tracking_enabled || false,
        tracking_similarity_threshold: record.tracking_similarity_threshold || 0.2,
      tracking_max_age: record.tracking_max_age || 25,
      tracking_smooth_alpha: record.tracking_smooth_alpha || 0.25,
      alert_hook_enabled: record.alert_hook_enabled !== undefined ? record.alert_hook_enabled : true,
      is_full_day_defense: fullDayDefense,
      });
      
      // 恢复布防时段配置
      if (record.defense_mode && record.defense_schedule) {
        try {
          const schedule = typeof record.defense_schedule === 'string' 
            ? JSON.parse(record.defense_schedule) 
            : record.defense_schedule;
          defenseSchedule.value = {
            mode: record.defense_mode,
            schedule: schedule,
          };
        } catch (e) {
          console.error('解析布防时段配置失败', e);
        }
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
</style>

