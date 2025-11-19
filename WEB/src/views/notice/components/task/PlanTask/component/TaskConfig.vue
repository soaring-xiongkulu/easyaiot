<template>
  <BasicModal
    @register="registerModal"
    @cancel="handleCancel"
    @ok="handleOk"
    :canFullscreen="false"
    wrapClassName="task-modal"
  >
    <BasicForm
      @register="registerForm"
      :showAdvancedButton="false"
      :showActionButtonGroup="false"
    />
  </BasicModal>
</template>
<script lang="ts" setup>
  import {} from 'vue';
  import { BasicModal, useModalInner } from '/@/components/Modal';
  import { BasicForm, useForm } from '/@/components/Form';
  import { useMessage } from '/@/hooks/web/useMessage';
  import { formSchemas } from '../Data.tsx';

  const emits = defineEmits(['success']);
  const { createMessage } = useMessage();

  const [registerModal, { closeModal, setModalProps }] = useModalInner((data) => {
    console.log(data);
    const { type } = data;
    setModalProps({
      title: type == 'add' ? '新增任务' : '编辑任务',
    });
  });

  const [
    registerForm,
    {
      // appendSchemaByField,
      // validateFields,
      // updateSchema,
      // removeSchemaByField,
      // getFieldsValue,
      validate,
      // setFieldsValue,
      resetFields,
      // setProps,
    },
  ] = useForm({
    schemas: formSchemas(),
    labelWidth: '280px',
    layout: 'vertical',
    baseColProps: { span: 24 },
  });

  const handleCancel = () => {
    resetFields();
  };

  const handleOk = () => {
    validate()
      .then(async () => {
        handleCancel();
        closeModal();
        emits('success');
        createMessage.success('添加成功');
      })
      .catch((err) => {
        createMessage.error('操作失败');
        console.error(err);
      });
  };
</script>
<style lang="less" scoped>
  :global(.task-modal .scrollbar__view > div) {
    height: auto !important;
    min-height: auto !important;
  }
  :deep(.checkbox-warpper) {
    flex-direction: row;
    align-items: center;
    .ant-form-item-label {
      padding: 0;
    }
    .ant-form-item-control {
      flex: 1;
    }
  }
  :deep(.picker-warpper .ant-picker) {
    width: 100%;
  }
  :deep(.week-wapper) {
    .ant-form-item-control-input-content {
      display: flex;
      align-items: center;
      & > div {
        flex: 1;
      }
    }
    .ant-form-item-control-input-content::before {
      content: '每周';
      display: inline-block;
      width: 40px;
    }
    .ant-form-item-control-input-content::after {
      content: '的';
      display: inline-block;
      padding: 5px;
    }
  }
</style>
