<template>
  <BasicDrawer 
    v-bind="$attrs" 
    @register="register" 
    :title="modalTitle" 
    @ok="handleSubmit"
    width="1000"
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
      <a-tab-pane key="services" tab="算法服务" :disabled="!taskId">
        <AlgorithmServiceList
          v-if="taskId"
          :task-id="taskId"
          @refresh="handleServicesRefresh"
        />
        <a-empty v-else description="请先保存基础配置，然后才能配置算法服务" />
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
  listPushers,
  type AlgorithmTask,
} from '@/api/device/algorithm_task';
import { getDeviceList } from '@/api/device/camera';
import { getSnapSpaceList } from '@/api/device/snap';
import { getDeployServicePage } from '@/api/device/model';
import AlgorithmServiceList from './AlgorithmServiceList.vue';
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
const deployServiceOptions = ref<Array<{ label: string; value: number }>>([]);
const deployServiceMap = ref<Map<number, any>>(new Map()); // 存储完整的部署服务信息
const pusherOptions = ref<Array<{ label: string; value: number }>>([]);

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


// 加载部署服务列表（用于创建算法服务）
const loadDeployServices = async () => {
  try {
    const response = await getDeployServicePage({ pageNo: 1, pageSize: 1000 });
    if (response.code === 0 && response.data) {
      // 清空之前的映射
      deployServiceMap.value.clear();
      
      // 构建选项列表和完整服务信息映射
      deployServiceOptions.value = (response.data || []).map((item: any) => {
        // 保存完整的服务信息
        deployServiceMap.value.set(item.id, item);
        
        return {
          label: `${item.service_name}${item.model_name ? ` (${item.model_name})` : ''}`,
          value: item.id, // 部署服务ID
        };
      });
    }
  } catch (error) {
    console.error('加载部署服务列表失败', error);
  }
};

// 加载推送器列表
const loadPushers = async () => {
  try {
    // 将布尔值转换为整数：true -> 1
    const response = await listPushers({ pageNo: 1, pageSize: 1000, is_enabled: 1 });
    if (response.code === 0 && response.data) {
      pusherOptions.value = (response.data || []).map((item) => ({
        label: item.pusher_name,
        value: item.id,
      }));
    }
  } catch (error) {
    console.error('加载推送器列表失败', error);
  }
};

const [registerForm, { setFieldsValue, validate, resetFields, updateSchema, getFieldsValue }] = useForm({
  labelWidth: 120,
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
      field: 'pusher_id',
      label: '告警通知',
      component: 'Select',
      required: false,
      componentProps: {
        placeholder: '请选择告警通知推送器（可选）',
        options: pusherOptions,
        allowClear: true,
        showSearch: true,
        filterOption: (input: string, option: any) => {
          return option.label.toLowerCase().indexOf(input.toLowerCase()) >= 0;
        },
      },
      helpMessage: '选择告警通知推送器，不配置则不发送告警通知',
    },
    {
      field: 'selected_service_ids',
      label: '关联算法服务',
      component: 'Select',
      required: true,
      componentProps: {
        placeholder: '请选择部署服务（可多选，将自动创建算法服务）',
        options: deployServiceOptions,
        mode: 'multiple',
        showSearch: true,
        allowClear: true,
        filterOption: (input: string, option: any) => {
          return option.label.toLowerCase().indexOf(input.toLowerCase()) >= 0;
        },
      },
      helpMessage: '选择部署服务，创建任务时将自动创建对应的算法服务',
    },
    {
      field: 'is_enabled',
      label: '是否启用',
      component: 'Switch',
      componentProps: {
        checkedChildren: '是',
        unCheckedChildren: '否',
      },
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
  await Promise.all([loadDevices(), loadSpaces(), loadDeployServices(), loadPushers()]);
  
  if (modalData.value.record) {
    const record = modalData.value.record;
    taskId.value = record.id;
    // 从 algorithm_services 中提取部署服务ID列表（用于回显）
    // 通过 model_id 或 service_url 匹配部署服务
    const serviceIds: number[] = [];
    if (record.algorithm_services && record.algorithm_services.length > 0) {
      record.algorithm_services.forEach((service: any) => {
        // 通过 model_id 匹配
        if (service.model_id) {
          for (const [id, deployService] of deployServiceMap.value.entries()) {
            if (deployService.model_id === service.model_id) {
              serviceIds.push(id);
              break;
            }
          }
        }
        // 如果 model_id 匹配不到，尝试通过 service_url 匹配
        if (service.service_url && serviceIds.length === 0) {
          for (const [id, deployService] of deployServiceMap.value.entries()) {
            if (deployService.inference_endpoint === service.service_url || 
                deployService.service_url === service.service_url) {
              serviceIds.push(id);
              break;
            }
          }
        }
      });
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
    
    // 确保 is_enabled 是布尔值（Switch 组件需要布尔值）
    const isEnabled = typeof record.is_enabled === 'boolean' 
      ? record.is_enabled 
      : (record.is_enabled === 1 || record.is_enabled === '1');
    
    await setFieldsValue({
      task_name: record.task_name,
      task_type: record.task_type || 'realtime',
      device_ids: record.device_ids || [],
      space_id: record.space_id,
      cron_expression: record.cron_expression,
      frame_skip: record.frame_skip || 1,
      selected_service_ids: serviceIds,
      pusher_id: record.pusher_id,
      is_enabled: isEnabled,
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
        { field: 'pusher_id', componentProps: { disabled: true } },
        { field: 'is_enabled', componentProps: { disabled: true } },
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
      is_enabled: false,
      frame_skip: 1,
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
    
    // 将布尔值转换为整数：true -> 1, false -> 0
    if (values.is_enabled !== undefined) {
      values.is_enabled = values.is_enabled === true || values.is_enabled === 'true' ? 1 : 0;
    }
    
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
    
    // 如果选择了 selected_service_ids，构建 algorithm_services 数组
    if (values.selected_service_ids && values.selected_service_ids.length > 0) {
      const algorithmServices = values.selected_service_ids.map((serviceId: number) => {
        const deployService = deployServiceMap.value.get(serviceId);
        if (deployService) {
          return {
            service_name: deployService.service_name || `Service_${serviceId}`,
            service_url: deployService.inference_endpoint || deployService.service_url,
            service_type: deployService.service_type || null,
            model_id: deployService.model_id || null,
            threshold: deployService.threshold || null,
            request_method: deployService.request_method || 'POST',
            request_headers: deployService.request_headers || null,
            request_body_template: deployService.request_body_template || null,
            timeout: deployService.timeout || 30,
            is_enabled: deployService.is_enabled !== undefined ? deployService.is_enabled : true,
            sort_order: 0,
          };
        }
        return null;
      }).filter((service: any) => service !== null);
      
      // 使用 algorithm_services
      values.algorithm_services = algorithmServices;
      delete values.selected_service_ids; // 删除临时字段
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

const handleServicesRefresh = () => {
  emit('success');
};

// 重置表单
const handleReset = () => {
  resetFields();
  // 如果是新建模式，重置为默认值
  if (!modalData.value.record) {
    isFullDayDefense.value = true; // 默认全天布防
    setFieldsValue({
      task_type: 'realtime',
      is_enabled: false,
      frame_skip: 1,
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
      // 从 algorithm_services 中提取部署服务ID列表（用于回显）
      const serviceIds: number[] = [];
      if (record.algorithm_services && record.algorithm_services.length > 0) {
        record.algorithm_services.forEach((service: any) => {
          // 通过 model_id 匹配
          if (service.model_id) {
            for (const [id, deployService] of deployServiceMap.value.entries()) {
              if (deployService.model_id === service.model_id) {
                serviceIds.push(id);
                break;
              }
            }
          }
          // 如果 model_id 匹配不到，尝试通过 service_url 匹配
          if (service.service_url && serviceIds.length === 0) {
            for (const [id, deployService] of deployServiceMap.value.entries()) {
              if (deployService.inference_endpoint === service.service_url || 
                  deployService.service_url === service.service_url) {
                serviceIds.push(id);
                break;
              }
            }
          }
        });
      }
      
      // 判断是否全天布防
      const fullDayDefense = record.defense_mode === 'full';
      isFullDayDefense.value = fullDayDefense;
      
      // 确保 is_enabled 是布尔值（Switch 组件需要布尔值）
      const isEnabled = typeof record.is_enabled === 'boolean' 
        ? record.is_enabled 
        : (record.is_enabled === 1 || record.is_enabled === '1');
      
      setFieldsValue({
        task_name: record.task_name,
        task_type: record.task_type || 'realtime',
        device_ids: record.device_ids || [],
        space_id: record.space_id,
        cron_expression: record.cron_expression,
        frame_skip: record.frame_skip || 1,
        selected_service_ids: serviceIds,
        pusher_id: record.pusher_id,
        is_enabled: isEnabled,
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

