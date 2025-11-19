<!-- eslint-disable vue/v-on-event-hyphenation -->
<template>
  <BasicModal
    @register="registerModal"
    @cancel="handleCancel"
    @ok="handleOk"
    :canFullscreen="false"
    wrapClassName="user-modal"
    :confirm-loading="loading"
  >
    <BasicForm
      @register="registerForm"
      :showAdvancedButton="false"
      :showActionButtonGroup="false"
    />
  </BasicModal>
</template>
<script lang="ts" setup>
  import { ref } from 'vue';
  import { BasicModal, useModalInner } from '/@/components/Modal';
  import { BasicForm, useForm } from '/@/components/Form';
  import { useMessage } from '/@/hooks/web/useMessage';
  import { formSchemas } from '../Data';
  import { messagePreviewUserAdd, messagePreviewUserUpdate } from '/@/api/modules/user';
  import _ from 'lodash-es';

  const emits = defineEmits(['success', 'register']);
  const { createMessage } = useMessage();
  const opertionType = ref('add');
  const [registerModal, { setModalProps, closeModal }] = useModalInner((data) => {
    console.log(data);
    if (data.type == 'edit') {
      editUserConfig(data.record);
    }
    setModalProps({ title: data.type == 'add' ? '新增用户' : '编辑用户' });
    opertionType.value = data.type;
  });

  const loading = ref(false);

  // 检验手机号码
  const validator = (value, type, message) => {
    let reg = /\s/;
    switch (type) {
      case 'phone':
        reg = /^(13[0-9]|14[01456879]|15[0-35-9]|16[2567]|17[0-8]|18[0-9]|19[0-35-9])\d{8}$/;
        break;
      case 'email':
        reg = /^\w+([-+.]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*$/;
        break;
      case 'url':
        reg = /[a-zA-z]+:\/\/[^\s]*/;
        break;
      default:
        if (!value) return Promise.reject(message);
        return Promise.resolve();
    }
    if (reg.test(value)) return Promise.resolve();
    return Promise.reject(message.replace('请输入', '请输入正确的'));
  };

  const formatSubLabel = (val) => {
    let subLabel = '请输入';
    let rules: any = {};
    switch (val) {
      case 1:
      case 2:
        subLabel = '请输入手机号码';
        rules = { validator: (_rule, val) => validator(val, 'phone', subLabel) };
        break;
      case 3:
        subLabel = '请输入邮箱地址';
        rules = { validator: (_rule, val) => validator(val, 'email', subLabel) };
        break;
      case 4:
        subLabel = '请输入微信号';
        rules = { validator: (_rule, val) => validator(val, 'text', subLabel) };
        break;
      case 5:
        subLabel = '请输入HTTP地址';
        rules = { validator: (_rule, val) => validator(val, 'url', subLabel) };
        break;
      case 6:
        subLabel = '请输入钉钉号';
        rules = { validator: (_rule, val) => validator(val, 'text', subLabel) };
        break;
      default:
        rules = { validator: (_rule, val) => validator(val, 'text', '请输入') };
        break;
    }
    rules = Object.assign(
      {
        reqired: true,
        trigger: ['blur', 'change'],
      },
      rules,
    );
    // subLabel += '，多个用;隔开';
    return {
      rules,
      subLabel,
    };
  };

  const msgTypeChange = (val, _option) => {
    clearValidate();
    const { subLabel, rules } = formatSubLabel(val);
    updateSchema({
      field: 'previewUser',
      subLabel,
      labelWidth: 'auto',
      rules: [_.cloneDeep(rules)],
    });
  };

  const [
    registerForm,
    {
      // appendSchemaByField,
      // validateFields,
      updateSchema,
      // removeSchemaByField,
      getFieldsValue,
      validate,
      setFieldsValue,
      resetFields,
      // setProps,
      clearValidate,
    },
  ] = useForm({
    schemas: formSchemas(msgTypeChange),
    labelWidth: '100px',
    layout: 'vertical',
    baseColProps: { span: 24 },
  });

  function editUserConfig(record) {
    console.log(record);
    const { id, previewUser, msgType } = record;
    setFieldsValue({
      id,
      previewUser,
      msgType,
    });
  }

  const handleCancel = () => {
    resetFields();
    updateSchema({
      field: 'previewUser',
      subLabel: '',
      rules: [
        {
          required: true,
          validator: (_rule, val) => validator(val, 'text', '请输入'),
          trigger: ['change', 'blur'],
        },
      ],
    });
  };

  const handleOk = () => {
    validate()
      .then(async () => {
        const params = {
          ...getFieldsValue(),
        };
        loading.value = true;
        const ret =
          opertionType.value == 'add'
            ? await messagePreviewUserAdd(params)
            : await messagePreviewUserUpdate(params);
        if (ret.status == 500) {
          createMessage.error(ret.message);
          return;
        }
        closeModal();
        emits('success');
        handleCancel();
        createMessage.success(`${opertionType.value == 'add' ? '新增' : '更新'}成功`);
      })
      .finally(() => {
        loading.value = false;
      })
      .catch(() => {
        createMessage.success(`操作失败`);
      });
  };
</script>
<style lang="less" scoped>
  :global(.user-modal .scrollbar__view > div) {
    height: auto !important;
    min-height: auto !important;
  }
</style>
