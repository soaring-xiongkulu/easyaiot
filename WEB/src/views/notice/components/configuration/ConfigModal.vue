<template>
  <BasicModal
    @register="registerModal"
    @cancel="handleCancel"
    @ok="handleOk"
    width="800px"
    :canFullscreen="false"
  >
    <div class="config-modal-box">
      <BasicForm
        @register="registerForm"
        :showAdvancedButton="false"
        :showActionButtonGroup="false"
      >
        <template #weixinApply>
          <FormItemRest>
            <EditTable
              :columns="weixinApplyColumns"
              v-model:list="formData.configuration.weixinApply"
            />
          </FormItemRest>
        </template>
        <template #dindinApply>
          <FormItemRest>
            <EditTable
              :columns="dindinApplyColumns"
              v-model:list="formData.configuration.dindinApply"
            />
          </FormItemRest>
        </template>
      </BasicForm>
    </div>
  </BasicModal>
</template>
<script lang="ts" setup>
import {ref} from 'vue';
import {BasicModal, useModalInner} from '@/components/Modal';
import {BasicForm, useForm} from '@/components/Form';
import {useMessage} from '@/hooks/web/useMessage';
import {
  aliyunSchemas,
  dindinApplyColumns,
  dindinSchemas,
  emailSchemas,
  formSchemas,
  httpSchemas,
  tenxunyunSchemas,
  weixinApplyColumns,
  weixinSchemas,
  feishuSchemas,
} from '../../Data';
import {messageConfigAdd, messageConfigUpdate} from '/@/api/modules/notice';
import EditTable from './EditTable.vue';
import {FormItemRest} from 'ant-design-vue';

const emits = defineEmits(['success']);
const {createMessage} = useMessage();
const opertionType = ref('add');

const formData = ref({
  configuration: {
    weixinApply: [],
    dindinApply: [],
  },
});

const [registerModal, {setModalProps, closeModal}] = useModalInner((data) => {
  if (data.type == 'add') {
    //  默认邮件
    changeNoticeType(3);
  } else {
    editConfigModal(data.record);
  }
  setModalProps({
    title: data.type == 'add' ? '新增设置' : '编辑设置',
  });
  opertionType.value = data.type;
});

const [
  registerForm,
  {
    appendSchemaByField,
    // validateFields,
    // updateSchema,
    removeSchemaByField,
    getFieldsValue,
    validate,
    setFieldsValue,
    resetFields,
    // setProps,
  },
] = useForm({
  schemas: formSchemas(handleNoticeType),
  labelWidth: '170px',
  layout: 'vertical',
  baseColProps: {span: 24},
});

function editConfigModal(record) {
  const configValue = {
    4: 'weixinApply',
    6: 'dindinApply',
  };
  const configKey = {
    4: 'wxCpApp',
    6: 'dingdingApp',
  };
  const {msgType, id, configurationMap} = record;
  const _msgType = +msgType;
  setFieldsValue({msgType: _msgType});
  setTimeout(() => {
    setFieldsValue({id, ...configurationMap});
    formData.value.configuration[configValue[_msgType]] = configurationMap[configKey[_msgType]];
  });
}

function handleNoticeType(type) {
  changeNoticeType(type);
  reset();
}

function changeNoticeType(type) {
  const config = {
    1: aliyunSchemas,
    2: tenxunyunSchemas,
    3: emailSchemas,
    4: weixinSchemas,
    5: httpSchemas,
    6: dindinSchemas,
    7: feishuSchemas,
  };
  const fields = Object.keys(config)
    .map((c) => {
      const item = config[c]({});
      return item;
    })
    .reduce((p, c) => [...p, ...c], [])
    .map((item) => item.field);

  removeSchemaByField(fields);
  config[type] &&
  appendSchemaByField(config[type]({getFieldsValue, setFieldsValue}), 'msgType');
}

const reset = () => {
  formData.value.configuration.dindinApply = [];
  formData.value.configuration.weixinApply = [];
};

const handleCancel = () => {
  reset();
  resetFields();
};

const handleOk = () => {
  validate()
    .then(async () => {
      const {msgType, id, ...configuration} = getFieldsValue();
      const _msgType = +msgType;
      const configValue = {
        4: 'weixinApply',
        6: 'dindinApply',
      };
      const configKey = {
        4: 'wxCpApp',
        6: 'dingdingApp',
      };
      configuration[configKey[_msgType]] = formData.value.configuration[configValue[_msgType]];
      // 微信
      if ([3].includes(_msgType)) {
        if (!configuration.starttlsEnable) {
          configuration['starttlsEnable'] = false;
        }
        if (!configuration.sslEnable) {
          configuration['sslEnable'] = false;
        }
      }
      const params = {
        id,
        msgType: _msgType,
        configuration: JSON.stringify(configuration),
      };
      opertionType.value == 'add'
        ? await messageConfigAdd(params)
        : await messageConfigUpdate(params);
      // console.log('ret ...', ret);
      handleCancel();
      closeModal();
      emits('success');
      createMessage.success(opertionType.value == 'add' ? '新增成功' : '编辑成功');
    })
    .catch((err) => {
      createMessage.error('操作失败');
      console.error(err);
    });
};
</script>
<style lang="less" scoped>
.config-modal-box {
  display: flex;

  form,
  .describe-wapper {
    flex: 1;
  }

  .describe-wapper {
    margin-left: 20px;
  }

  :deep(.message-warpper) {
    display: flex;
  }

  :deep(.message-item) {
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 140px;
    height: 140px;
    padding: 5px;
    border-radius: 3px;
    margin-right: 5px;

    span:nth-child(1) {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 100px;
      height: 100px;
      border-radius: 15px;
      background: #1d39c4;
      color: #fff;
      font-size: 67px;
    }

    span:nth-child(2) {
      margin-top: 6px;
    }
  }

  :deep(.active) {
    border: solid 1px #1d39c4;

    span:nth-child(2) {
      color: #1d39c4;
    }
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
}
</style>
