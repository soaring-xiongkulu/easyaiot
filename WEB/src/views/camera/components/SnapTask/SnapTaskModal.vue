<template>
  <BasicDrawer 
    v-bind="$attrs" 
    @register="register" 
    :title="modalTitle" 
    @ok="handleSubmit" 
    width="800"
    placement="right"
  >
    <a-tabs v-model:activeKey="activeTab">
      <a-tab-pane key="basic" tab="基础配置">
        <BasicForm @register="registerForm" />
      </a-tab-pane>
      <a-tab-pane key="regions" tab="检测区域" :disabled="!taskId">
        <RegionDrawer
          v-if="taskId"
          :device-id="formValues.device_id"
          :task-id="taskId"
          :initial-regions="initialRegions"
          :initial-image-id="initialImageId"
          :initial-image-path="initialImagePath"
          @save="handleRegionsSave"
          @image-captured="handleImageCaptured"
        />
        <a-empty v-else description="请先保存基础配置，然后才能配置检测区域" />
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
  createSnapTask,
  updateSnapTask,
  type SnapTask,
  getDetectionRegions,
  createDetectionRegion,
  updateDetectionRegion,
  deleteDetectionRegion,
  type DetectionRegion,
} from '@/api/device/snap';
import { getSnapSpaceList } from '@/api/device/snap';
import { getDeviceList } from '@/api/device/camera';
import { listPushers } from '@/api/device/algorithm_task';
import RegionDrawer from '../RegionDrawer/index.vue';

defineOptions({ name: 'SnapTaskModal' });

const { createMessage } = useMessage();
const emit = defineEmits(['success', 'register']);

const activeTab = ref('basic');
const taskId = ref<number | null>(null);
const formValues = ref<any>({});
const initialRegions = ref<DetectionRegion[]>([]);
const initialImageId = ref<number | null>(null);
const initialImagePath = ref<string | null>(null);

const spaceOptions = ref<Array<{ label: string; value: number }>>([]);
const deviceOptions = ref<Array<{ label: string; value: string }>>([]);
const pusherOptions = ref<Array<{ label: string; value: number }>>([]);

// 加载空间列表
const loadSpaces = async () => {
  try {
    const response = await getSnapSpaceList({ pageNo: 1, pageSize: 1000 });
    spaceOptions.value = (response.data || []).map((item) => ({
      label: item.space_name,
      value: item.id,
    }));
  } catch (error) {
    console.error('加载空间列表失败', error);
  }
};

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

// 加载推送器列表
const loadPushers = async () => {
  try {
    const response = await listPushers({ pageNo: 1, pageSize: 1000 });
    pusherOptions.value = (response.data || []).map((item) => ({
      label: item.pusher_name,
      value: item.id,
    }));
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
      field: 'space_id',
      label: '抓拍空间',
      component: 'Select',
      required: true,
      componentProps: {
        placeholder: '请选择抓拍空间',
        options: spaceOptions,
      },
    },
    {
      field: 'device_id',
      label: '设备',
      component: 'Select',
      required: true,
      componentProps: {
        placeholder: '请选择设备',
        options: deviceOptions,
      },
    },
    {
      field: 'capture_type',
      label: '抓拍类型',
      component: 'Select',
      required: true,
      componentProps: {
        options: [
          { label: '抽帧', value: 0 },
          { label: '抓拍', value: 1 },
        ],
      },
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
    },
    {
      field: 'algorithm_enabled',
      label: '启用算法',
      component: 'Switch',
      componentProps: {
        checkedChildren: '是',
        unCheckedChildren: '否',
      },
    },
    {
      field: 'algorithm_type',
      label: '算法类型',
      component: 'Select',
      componentProps: {
        placeholder: '请选择算法类型',
        options: [
          { label: '火焰烟雾检测', value: 'FIRE' },
          { label: '人群聚集计数', value: 'CROWD' },
          { label: '吸烟检测', value: 'SMOKE' },
        ],
      },
      ifShow: ({ values }) => values.algorithm_enabled,
    },
    {
      field: 'algorithm_model_id',
      label: '算法模型ID',
      component: 'InputNumber',
      componentProps: {
        placeholder: '请输入算法模型ID',
        min: 1,
      },
      ifShow: ({ values }) => values.algorithm_enabled,
    },
    {
      field: 'algorithm_threshold',
      label: '算法阈值',
      component: 'InputNumber',
      componentProps: {
        placeholder: '请输入算法阈值',
        min: 0,
        max: 1,
        step: 0.1,
      },
      ifShow: ({ values }) => values.algorithm_enabled,
    },
    {
      field: 'algorithm_night_mode',
      label: '仅夜间启用',
      component: 'Switch',
      componentProps: {
        checkedChildren: '是',
        unCheckedChildren: '否',
      },
      helpMessage: '仅在23:00-08:00启用算法',
      ifShow: ({ values }) => values.algorithm_enabled,
    },
    {
      field: 'alarm_enabled',
      label: '启用告警',
      component: 'Switch',
      componentProps: {
        checkedChildren: '是',
        unCheckedChildren: '否',
      },
    },
    {
      field: 'alarm_type',
      label: '告警类型',
      component: 'Select',
      componentProps: {
        options: [
          { label: '短信告警', value: 0 },
          { label: '邮箱告警', value: 1 },
          { label: '短信+邮箱', value: 2 },
        ],
      },
      ifShow: ({ values }) => values.alarm_enabled,
    },
    {
      field: 'phone_number',
      label: '告警手机号',
      component: 'Input',
      componentProps: {
        placeholder: '多个手机号用英文逗号分割',
      },
      ifShow: ({ values }) => values.alarm_enabled && (values.alarm_type === 0 || values.alarm_type === 2),
    },
    {
      field: 'email',
      label: '告警邮箱',
      component: 'Input',
      componentProps: {
        placeholder: '多个邮箱用英文逗号分割',
      },
      ifShow: ({ values }) => values.alarm_enabled && (values.alarm_type === 1 || values.alarm_type === 2),
    },
    {
      field: 'pusher_id',
      label: '推送器',
      component: 'Select',
      componentProps: {
        placeholder: '请选择推送器（可选）',
        options: pusherOptions,
        allowClear: true,
      },
    },
    {
      field: 'auto_filename',
      label: '自动命名',
      component: 'Switch',
      componentProps: {
        checkedChildren: '是',
        unCheckedChildren: '否',
      },
    },
    {
      field: 'custom_filename_prefix',
      label: '自定义前缀',
      component: 'Input',
      componentProps: {
        placeholder: '请输入自定义文件前缀',
      },
      ifShow: ({ values }) => values.auto_filename,
    },
  ],
  showActionButtonGroup: false,
});

const modalData = ref<{ type?: string; record?: SnapTask }>({});

const modalTitle = computed(() => {
  if (modalData.value.type === 'view') return '查看算法任务';
  if (modalData.value.type === 'edit') return '编辑算法任务';
  return '新建算法任务';
});

// 加载区域的检测区域
const loadRegions = async (taskId: number) => {
  try {
    const response = await getDetectionRegions(taskId);
    // API返回格式: { code: 0, data: [...], msg: 'success' } 或直接返回data
    const data = response.code !== undefined ? (response.code === 0 ? response.data : null) : response;
    if (data && Array.isArray(data)) {
      initialRegions.value = data;
      // 查找第一个区域的图片信息
      if (data.length > 0 && data[0].image_path) {
        initialImagePath.value = data[0].image_path;
        initialImageId.value = data[0].image_id || null;
      }
    } else {
      initialRegions.value = [];
    }
  } catch (error) {
    console.error('加载检测区域失败', error);
    initialRegions.value = [];
  }
};

const [register, { setDrawerProps, closeDrawer }] = useDrawerInner(async (data) => {
  resetFields();
  setDrawerProps({ confirmLoading: false });
  modalData.value = data;
  activeTab.value = 'basic';
  taskId.value = null;
  initialRegions.value = [];
  initialImageId.value = null;
  initialImagePath.value = null;
  
  // 加载选项数据
  await loadSpaces();
  await loadDevices();
  await loadPushers();
  
  if (data.type === 'edit' && data.record) {
    taskId.value = data.record.id;
    setFieldsValue({
      task_name: data.record.task_name,
      space_id: data.record.space_id,
      device_id: data.record.device_id,
      capture_type: data.record.capture_type,
      cron_expression: data.record.cron_expression,
      frame_skip: data.record.frame_skip,
      algorithm_enabled: data.record.algorithm_enabled,
      algorithm_type: data.record.algorithm_type,
      algorithm_model_id: data.record.algorithm_model_id,
      algorithm_threshold: data.record.algorithm_threshold,
      algorithm_night_mode: data.record.algorithm_night_mode,
      alarm_enabled: data.record.alarm_enabled,
      alarm_type: data.record.alarm_type,
      phone_number: data.record.phone_number,
      email: data.record.email,
      auto_filename: data.record.auto_filename,
      custom_filename_prefix: data.record.custom_filename_prefix,
    });
    // 加载检测区域
    await loadRegions(data.record.id);
  } else if (data.type === 'view' && data.record) {
    taskId.value = data.record.id;
    setFieldsValue({
      task_name: data.record.task_name,
      space_id: data.record.space_id,
      device_id: data.record.device_id,
      capture_type: data.record.capture_type,
      cron_expression: data.record.cron_expression,
      frame_skip: data.record.frame_skip,
      algorithm_enabled: data.record.algorithm_enabled,
      algorithm_type: data.record.algorithm_type,
      algorithm_model_id: data.record.algorithm_model_id,
      algorithm_threshold: data.record.algorithm_threshold,
      algorithm_night_mode: data.record.algorithm_night_mode,
      alarm_enabled: data.record.alarm_enabled,
      alarm_type: data.record.alarm_type,
      phone_number: data.record.phone_number,
      email: data.record.email,
      pusher_id: data.record.pusher_id,
      auto_filename: data.record.auto_filename,
      custom_filename_prefix: data.record.custom_filename_prefix,
    });
    setDrawerProps({ showOkBtn: false });
    // 加载检测区域
    await loadRegions(data.record.id);
  }
});

// 监听表单值变化
const updateFormValues = () => {
  try {
    const values = getFieldsValue();
    formValues.value = values;
  } catch (e) {
    // 表单可能还未初始化
  }
};

const handleSubmit = async () => {
  try {
    const values = await validate();
    setDrawerProps({ confirmLoading: true });
    
    if (modalData.value.type === 'edit' && modalData.value.record) {
      const response = await updateSnapTask(modalData.value.record.id, values);
      if (response.code === 0) {
        createMessage.success('更新成功');
        // 更新taskId（虽然不会变，但确保一致性）
        taskId.value = modalData.value.record.id;
        // 更新表单值
        updateFormValues();
      } else {
        createMessage.error(response.msg || '更新失败');
        return;
      }
    } else {
      const response = await createSnapTask(values);
      if (response.code === 0 && response.data) {
        taskId.value = response.data.id;
        createMessage.success('创建成功');
        // 更新表单值
        updateFormValues();
        // 创建成功后切换到区域配置标签页
        activeTab.value = 'regions';
      } else {
        createMessage.error(response.msg || '创建失败');
        return;
      }
    }
    
    // 如果是查看模式，不关闭模态框
    if (modalData.value.type === 'view') {
      // 查看模式不关闭
    } else {
      // 编辑或创建模式，可以选择关闭或继续配置区域
      // 这里不自动关闭，让用户决定
    }
  } catch (error) {
    console.error('提交失败', error);
    createMessage.error('提交失败');
  } finally {
    setDrawerProps({ confirmLoading: false });
  }
};

// 处理区域保存
const handleRegionsSave = async (regions: DetectionRegion[]) => {
  if (!taskId.value) {
    createMessage.error('任务ID不存在，请先保存基础配置');
    return;
  }

  try {
    // 获取现有的区域
    const existingRegionsResponse = await getDetectionRegions(taskId.value);
    // API返回格式: { code: 0, data: [...], msg: 'success' } 或直接返回data
    const existingRegionsData = existingRegionsResponse.code !== undefined 
      ? (existingRegionsResponse.code === 0 ? existingRegionsResponse.data : [])
      : existingRegionsResponse;
    const existingIds = (existingRegionsData || []).map((r: DetectionRegion) => r.id);

    // 保存或更新区域
    for (const region of regions) {
      if (region.id && existingIds.includes(region.id)) {
        // 更新现有区域
        const updateResponse = await updateDetectionRegion(region.id, {
          region_name: region.region_name,
          region_type: region.region_type,
          points: region.points,
          image_id: region.image_id,
          algorithm_type: region.algorithm_type,
          algorithm_model_id: region.algorithm_model_id,
          algorithm_threshold: region.algorithm_threshold,
          algorithm_enabled: region.algorithm_enabled,
          color: region.color,
          opacity: region.opacity,
          is_enabled: region.is_enabled,
          sort_order: region.sort_order,
        });
        if (updateResponse.code !== undefined && updateResponse.code !== 0) {
          createMessage.error(updateResponse.msg || '更新区域失败');
          return;
        }
      } else {
        // 创建新区域
        const createResponse = await createDetectionRegion({
          task_id: taskId.value,
          region_name: region.region_name,
          region_type: region.region_type,
          points: region.points,
          image_id: region.image_id,
          algorithm_type: region.algorithm_type,
          algorithm_model_id: region.algorithm_model_id,
          algorithm_threshold: region.algorithm_threshold,
          algorithm_enabled: region.algorithm_enabled,
          color: region.color,
          opacity: region.opacity,
          is_enabled: region.is_enabled,
          sort_order: region.sort_order,
        });
        if (createResponse.code !== undefined && createResponse.code !== 0) {
          createMessage.error(createResponse.msg || '创建区域失败');
          return;
        }
      }
    }

    // 删除不存在的区域
    const currentIds = regions.map(r => r.id).filter(id => id && typeof id === 'number');
    for (const existingId of existingIds) {
      if (!currentIds.includes(existingId)) {
        const deleteResponse = await deleteDetectionRegion(existingId);
        if (deleteResponse.code !== undefined && deleteResponse.code !== 0) {
          createMessage.error(deleteResponse.msg || '删除区域失败');
          return;
        }
      }
    }

    createMessage.success('区域保存成功');
    // 重新加载区域
    await loadRegions(taskId.value);
  } catch (error) {
    console.error('保存区域失败', error);
    createMessage.error('保存区域失败');
  }
};

// 处理图片抓拍
const handleImageCaptured = (imageId: number, imagePath: string) => {
  initialImageId.value = imageId;
  initialImagePath.value = imagePath;
};
</script>

