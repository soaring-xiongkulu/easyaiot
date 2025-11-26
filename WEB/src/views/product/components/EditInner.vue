<template>
  <BasicForm
    @register="register"
    ref="formElRef"
    labelAlign="right"
    layout="horizontal"
    :rowProps="{
      gutter: 20,
    }"
    :showAdvancedButton="false"
    :showActionButtonGroup="false"
  />
</template>

<script lang="ts" setup name="EditInner">
import {BasicForm, useForm} from '@/components/Form';
import {FormSchema} from '@/components/Form/index';

import {
  BoolFormSchemas,
  EditFormSchemas,
  IntFormSchemas,
  SubuctSchemas,
  TextFormSchemas,
} from '../data/ProductData';
import {onMounted, withDefaults} from 'vue';
import {DebouncedFunc} from 'lodash-es';

interface Props {
    functionType: string;
    // 是否为结构体弹窗
    isInner?: boolean;
    disabled: boolean;
    // 是否校验标识符
    checkIdentifier?:
      | false
      | DebouncedFunc<(val: string) => Promise<void>>
      | ((val: string) => Promise<void>);
    // 校验结构体参数
    handleCheckSubuct: (field: string) => Promise<void>;
  }

  const props = withDefaults(defineProps<Props>(), {
    functionType: 'properties',
    isInner: false,
    disabled: false,
    checkIdentifier: false,
  });

  const emit = defineEmits(['showInner', 'afterShow']);

  const temp = {
    INT: IntFormSchemas,
    DOUBLE: IntFormSchemas,
    BOOL: BoolFormSchemas,
    TEXT: TextFormSchemas,
    SUBUCT: SubuctSchemas,
  };

  const allFields = Object.values(temp)
    .map((e) => e({}))
    .reduce((cur, item) => {
      return [...cur, ...item];
    }, [])
    .map((e) => e.field);

  const subuctClick = (field: string) => {
    // 展示结构体弹窗
    emit('showInner', field);
  };

  const handleChange = (val: string) => {
    removeSchemaByField(allFields);
    temp[val]({
      validateFields,
      btnClick: subuctClick,
      disabled: props.disabled,
      handleCheckSubuct: props.handleCheckSubuct,
    }).forEach((e) => {
      appendSchemaByField(e, 'datatype');
    });
  };

  const [
    register,
    {
      appendSchemaByField,
      validateFields,
      updateSchema,
      removeSchemaByField,
      getFieldsValue,
      validate,
      setFieldsValue,
      resetFields,
      setProps,
    },
  ] = useForm({
    schemas: EditFormSchemas(props.checkIdentifier, 'properties'),
    labelWidth: '90px',
    disabled: false,
  });

  const getData = () => {
    // alert(5656);
    return new Promise((resolve, reject) => {
      validate()
        .then(() => {
          //alert(JSON.stringify(getFieldsValue()));
          resolve(getFieldsValue());
        })
        .catch((err) => {
          reject(err);
        });
    });
  };

  const setData = (obj) => {
    setFieldsValue(obj);
  };

  const reset = () => {
    removeSchemaByField(allFields);
    resetFields();
  };

  /**
   * 设置新的表单
   * @param schemas 新增的字段
   * @param field 从这个字段后开始新增
   * @param removeField 需要移除的字段
   */
  const setSchemas = (
    schemas: Array<(e) => FormSchema[]>,
    field: string,
    removeField?: string[],
  ) => {
    removeSchemaByField(removeField ?? []);

    // alert(JSON.stringify(schemas));

    schemas.forEach((e) => {
      e({
        handleChange,
        validateFields,
        btnClick: subuctClick,
        isInner: props.isInner,
        handleCheckSubuct: props.handleCheckSubuct,
      })
        .reverse()
        .forEach((v) => {
          //alert(JSON.stringify(v));
          appendSchemaByField(v, field);
        });
    });
  };

  /**
   * 删除所有表单
   */
  const removeAllSchemas = () => {
    removeSchemaByField(allFields);
  };

  const setFormProps = (obj) => {
    setProps(obj);
  };

  onMounted(() => {
    emit('afterShow');
  });

  defineExpose({
    getData,
    updateSchema,
    setData,
    reset,
    setSchemas,
    removeAllSchemas,
    handleChangeDataType: handleChange,
    removeSchemaByField,
    setFormProps,
    validateFields,
  });
</script>

<style lang="less" scoped>
  :deep(.alert) {
    justify-content: space-between;
    width: 100%;
    padding: 0.5rem;
    border-radius: 2px;
    background-color: rgb(239 246 255);
  }
</style>
