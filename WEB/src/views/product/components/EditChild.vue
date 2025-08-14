<template>
  <BasicModal @register="register" title="物模型参数" @cancel="handleCancel" @ok="handleSubmit">
    <EditInner
      ref="formRef"
      @show-inner="handleShowInner"
      @after-show="handleAfterShow"
      :isInner="isInner"
      :disabled="props.disabled"
      :handleCheckSubuct="props.handleCheckSubuct"
    />
  </BasicModal>
</template>

<script lang="ts" setup name="Edit">
  import { BasicModal, useModalInner } from '@/components/Modal';
  import EditInner from './EditInner.vue';
  import { ref, withDefaults, computed, nextTick } from 'vue';
  import {
    PropsSchemas,
    IntFormSchemas,
    BoolFormSchemas,
    TextFormSchemas,
    SubuctSchemas,
  } from '../data/ProductData';

  interface Props {
    // 当前激活tab
    tab: string;
    isInner?: boolean;
    //
    disabled: boolean;
    // 校验结构体参数
    handleCheckSubuct: (field: string, parnet?: string) => Promise<void>;
  }

  const props = withDefaults(defineProps<Props>(), {
    tab: '',
    isInner: false,
    disabled: false,
  });

  const emit = defineEmits(['showInside', 'register', 'submit', 'close']);
  // 外部表单ref
  const formRef = ref();

  const isInner = computed(() => {
    if (props.tab === 'properties') return true;
    return props.isInner;
  });

  const [register, { closeModal }] = useModalInner();

  // 展示结构体参数
  const handleShowInner = (field: string) => {
    emit('showInside', field);
  };

  // 结构体弹窗关闭初始化数据
  const handleCancel = () => {
    formRef.value.reset();
    const fields = [
      ...IntFormSchemas({}),
      ...BoolFormSchemas(),
      ...TextFormSchemas(),
      ...SubuctSchemas({}),
      ...PropsSchemas({}),
    ].map((e) => e.field);
    formRef.value.removeSchemaByField(fields);
    emit('close');
    closeModal();
  };

  const handleSubmit = () => {
    formRef.value.getData().then((res) => {
      emit('submit', res);
      nextTick(() => {
        handleCancel();
      });
    });
  };

  const handleAfterShow = (cb?: () => void) => {
    cb?.();
  };

  const setSchemas = async (...ext) => {
    await nextTick();
    formRef.value.setFormProps({
      disabled: props.disabled,
    });
    await nextTick();
    // alert(JSON.stringify(ext));
    formRef?.value?.setSchemas(...ext);
  };

  const setData = (...ext) => {
    formRef?.value?.setData(...ext);
  };

  const updateSchema = (...ext) => {
    formRef.value.updateSchema(...ext);
  };

  const handleChangeDataType = async (...ext) => {
    // alert(88888);

    await nextTick();
    formRef.value.handleChangeDataType(...ext);

    const [type] = ext;
    // 初始化弹窗 防止数据类型字段校验失败
    if (type === 'INT') {
      formRef.value.setData({
        datatype: 'INT',
      });
    }
  };

  const setFormProps = (...ext) => {
    formRef.value.setFormProps(...ext);
  };

  const validateFields = (...ext) => {
    formRef.value.validateFields(...ext);
  };

  defineExpose({
    setSchemas,
    setData,
    updateSchema,
    handleChangeDataType,
    setFormProps,
    validateFields,
  });
</script>

<style lang="less" scoped></style>
