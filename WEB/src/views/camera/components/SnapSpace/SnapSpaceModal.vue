<template>
  <BasicDrawer 
    v-bind="$attrs" 
    @register="register" 
    :title="modalTitle" 
    @ok="handleSubmit"
    width="800"
    placement="right"
    :showFooter="true"
    :showCancelBtn="false"
    :showOkBtn="!isViewMode"
  >
    <template #footer>
      <div class="footer-buttons">
        <a-button v-if="!isViewMode" @click="handleReset" class="mr-2">重置</a-button>
        <a-button v-if="!isViewMode" type="primary" :loading="confirmLoading" @click="handleSubmit">提交</a-button>
      </div>
    </template>
    
    <div class="snap-space-form-container">
      <a-divider orientation="left">
        <span class="section-title">
          <DatabaseOutlined class="section-icon" />
          基础信息
        </span>
      </a-divider>
      <BasicForm @register="registerForm" />
      
      <div class="form-tips" v-if="!isViewMode">
        <a-alert
          type="info"
          show-icon
          :closable="false"
        >
          <template #message>
            <div class="alert-content">
              <div class="alert-title">提示信息</div>
              <ul class="alert-list">
                <li>空间名称用于标识和管理抓拍图片的存储空间</li>
                <li>存储模式：标准存储适合频繁访问，归档存储成本更低</li>
                <li>保存时间：设置为0表示永久保存，>=7表示保存天数</li>
              </ul>
            </div>
          </template>
        </a-alert>
      </div>
    </div>
  </BasicDrawer>
</template>

<script lang="ts" setup>
import { ref, computed } from 'vue';
import { BasicDrawer, useDrawerInner } from '@/components/Drawer';
import { BasicForm, useForm } from '@/components/Form';
import { useMessage } from '@/hooks/web/useMessage';
import { DatabaseOutlined } from '@ant-design/icons-vue';
import { createSnapSpace, updateSnapSpace, type SnapSpace } from '@/api/device/snap';

defineOptions({ name: 'SnapSpaceModal' });

const { createMessage } = useMessage();
const emit = defineEmits(['success', 'register']);

const [registerForm, { setFieldsValue, validate, resetFields, updateSchema }] = useForm({
  labelWidth: 120,
  baseColProps: { span: 24 },
  schemas: [
    {
      field: 'space_name',
      label: '空间名称',
      component: 'Input',
      required: true,
      componentProps: {
        placeholder: '请输入空间名称，建议使用有意义的名称便于管理',
        maxlength: 50,
        showCount: true,
      },
      helpMessage: '用于标识和管理抓拍图片的存储空间，建议使用有意义的名称',
    },
    {
      field: 'save_mode',
      label: '存储模式',
      component: 'Select',
      required: true,
      componentProps: {
        placeholder: '请选择存储模式',
        options: [
          { label: '标准存储', value: 0 },
          { label: '归档存储', value: 1 },
        ],
      },
      helpMessage: '标准存储：适合频繁访问的场景，访问速度快；归档存储：成本更低，适合长期存储',
    },
    {
      field: 'save_time',
      label: '保存时间（天）',
      component: 'InputNumber',
      required: true,
      componentProps: {
        placeholder: '请输入保存天数',
        min: 0,
        precision: 0,
        style: { width: '100%' },
        addonAfter: '天',
      },
      helpMessage: '设置为0表示永久保存，>=7表示保存天数（单位：天）',
    },
    {
      field: 'description',
      label: '空间描述',
      component: 'InputTextArea',
      componentProps: {
        placeholder: '请输入空间描述信息，用于说明该空间的用途和特点',
        rows: 4,
        maxlength: 200,
        showCount: true,
      },
      helpMessage: '可选，用于记录空间的用途、特点等描述信息',
    },
  ],
  showActionButtonGroup: false,
});

const modalData = ref<{ type?: string; record?: SnapSpace }>({});
const confirmLoading = ref(false);

const modalTitle = computed(() => {
  if (modalData.value.type === 'view') return '查看抓拍空间';
  if (modalData.value.type === 'edit') return '编辑抓拍空间';
  return '新建抓拍空间';
});

const isViewMode = computed(() => modalData.value.type === 'view');

const [register, { setDrawerProps, closeDrawer }] = useDrawerInner(async (data) => {
  resetFields();
  setDrawerProps({ confirmLoading: false });
  confirmLoading.value = false;
  modalData.value = data;
  
  if (data.type === 'edit' && data.record) {
    // 编辑模式：所有字段可编辑
    updateSchema([
      {
        field: 'space_name',
        componentProps: { disabled: false },
      },
      {
        field: 'save_mode',
        componentProps: { disabled: false },
      },
      {
        field: 'save_time',
        componentProps: { disabled: false },
      },
      {
        field: 'description',
        componentProps: { disabled: false },
      },
    ]);
    setFieldsValue({
      space_name: data.record.space_name,
      save_mode: data.record.save_mode,
      save_time: data.record.save_time,
      description: data.record.description,
    });
    setDrawerProps({ showOkBtn: true });
  } else if (data.type === 'view' && data.record) {
    // 查看模式：所有字段禁用
    updateSchema([
      {
        field: 'space_name',
        componentProps: { disabled: true },
      },
      {
        field: 'save_mode',
        componentProps: { disabled: true },
      },
      {
        field: 'save_time',
        componentProps: { disabled: true },
      },
      {
        field: 'description',
        componentProps: { disabled: true },
      },
    ]);
    setFieldsValue({
      space_name: data.record.space_name,
      save_mode: data.record.save_mode,
      save_time: data.record.save_time,
      description: data.record.description,
    });
    setDrawerProps({ showOkBtn: false });
  } else {
    // 新建模式：所有字段可编辑
    updateSchema([
      {
        field: 'space_name',
        componentProps: { disabled: false },
      },
      {
        field: 'save_mode',
        componentProps: { disabled: false },
      },
      {
        field: 'save_time',
        componentProps: { disabled: false },
      },
      {
        field: 'description',
        componentProps: { disabled: false },
      },
    ]);
    setDrawerProps({ showOkBtn: true });
  }
});

const handleSubmit = async () => {
  try {
    const values = await validate();
    confirmLoading.value = true;
    setDrawerProps({ confirmLoading: true });
    
    if (modalData.value.type === 'edit' && modalData.value.record) {
      const response = await updateSnapSpace(modalData.value.record.id, values);
      if (response.code === 0) {
        createMessage.success('更新成功');
        closeDrawer();
        emit('success');
      } else {
        createMessage.error(response.msg || '更新失败');
      }
    } else {
      const response = await createSnapSpace(values);
      if (response.code === 0) {
        createMessage.success('创建成功');
        closeDrawer();
        emit('success');
      } else {
        createMessage.error(response.msg || '创建失败');
      }
    }
  } catch (error: any) {
    console.error('提交失败', error);
    // 如果错误已经有消息（比如axios拦截器已经显示了），就不再显示"提交失败"
    const errorMsg = error?.response?.data?.msg || error?.message || '';
    // 如果是业务错误（400等），axios拦截器已经显示了错误消息，不需要再显示
    const status = error?.response?.status;
    if (status && status >= 400 && status < 500 && errorMsg) {
      // 业务错误且已有错误消息，不重复显示
      return;
    }
    // 其他错误（网络错误等）才显示"提交失败"
    if (!errorMsg) {
      createMessage.error('提交失败');
    }
  } finally {
    confirmLoading.value = false;
    setDrawerProps({ confirmLoading: false });
  }
};

// 重置表单
const handleReset = () => {
  resetFields();
  if (modalData.value.type === 'edit' && modalData.value.record) {
    // 编辑模式：恢复到原始值
    setFieldsValue({
      space_name: modalData.value.record.space_name,
      save_mode: modalData.value.record.save_mode,
      save_time: modalData.value.record.save_time,
      description: modalData.value.record.description,
    });
  }
};
</script>

<style lang="less" scoped>
.snap-space-form-container {
  padding: 0;
  
  :deep(.ant-divider) {
    margin: 0 0 24px 0;
    border-color: #e8e8e8;
    
    .ant-divider-inner-text {
      padding: 0 16px;
    }
  }
  
  .section-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 16px;
    font-weight: 500;
    color: rgba(0, 0, 0, 0.85);
    
    .section-icon {
      color: #1890ff;
      font-size: 18px;
    }
  }
  
  .form-tips {
    margin-top: 24px;
    
    .alert-content {
      .alert-title {
        font-weight: 500;
        margin-bottom: 8px;
        color: rgba(0, 0, 0, 0.85);
      }
      
      .alert-list {
        margin: 0;
        padding-left: 20px;
        color: rgba(0, 0, 0, 0.65);
        line-height: 1.8;
        
        li {
          margin-bottom: 4px;
          
          &:last-child {
            margin-bottom: 0;
          }
        }
      }
    }
  }
  
  :deep(.ant-form-item-label) {
    font-weight: 500;
    
    > label {
      color: rgba(0, 0, 0, 0.85);
    }
  }
  
  :deep(.ant-input),
  :deep(.ant-input-number),
  :deep(.ant-select-selector) {
    border-radius: 4px;
    transition: all 0.3s;
    
    &:hover {
      border-color: #40a9ff;
    }
    
    &:focus,
    &.ant-input-focused,
    &.ant-select-focused .ant-select-selector {
      border-color: #1890ff;
      box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
    }
  }
  
  :deep(.ant-select-focused .ant-select-selector) {
    border-color: #1890ff;
    box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
  }
  
  :deep(.ant-input-number) {
    width: 100%;
  }
  
  :deep(.ant-form-item) {
    margin-bottom: 24px;
  }
  
  :deep(.ant-form-item-explain) {
    margin-top: 4px;
    font-size: 12px;
    line-height: 1.5;
  }
}

.footer-buttons {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
}

.mr-2 {
  margin-right: 8px;
}

:deep(.ant-drawer-body) {
  padding: 24px;
}

:deep(.ant-alert) {
  border-radius: 4px;
  
  .ant-alert-message {
    margin-bottom: 0;
  }
}
</style>

