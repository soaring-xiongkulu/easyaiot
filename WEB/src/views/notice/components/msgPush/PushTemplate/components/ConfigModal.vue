<!-- eslint-disable vue/v-on-event-hyphenation -->
<template>
  <BasicModal
    @register="registerModal"
    @cancel="handleCancel"
    @ok="handleOk"
    width="900px"
    :canFullscreen="false"
  >
    <div class="config-modal-box">
      <BasicForm
        @register="registerForm"
        :showAdvancedButton="false"
        :showActionButtonGroup="false"
      >
        <!-- 应用 -->
        <template #agentId="{ model, field }">
          <FormItemRest>
            <Select
              v-model:value="model[field]"
              :options="formData.agent"
              @focus="getMessageConfigQuery"
              placeholder="请选择"
            />
          </FormItemRest>
        </template>
        <!-- 用户分组 -->
        <template #userGroupId="{ model, field }">
          <FormItemRest>
            <Select
              v-model:value="model[field]"
              :options="formData.userGroupList"
              @focus="getUserGroupQueryByMsgType"
              placeholder="请选择"
            />
          </FormItemRest>
        </template>
        <!-- 模版变量 -->
        <template #templateDataList>
          <FormItemRest>
            <EditTable :columns="templateColumns" v-model:list="formData.templateDataList" />
          </FormItemRest>
        </template>
        <!-- 附件 -->
        <template #attachments>
          <FormItemRest>
            <UploadAttachment v-model:attachment="formData.attachments" />
          </FormItemRest>
        </template>
        <!-- http参数 -->
        <template #tabActive="{ model, field }">
          <FormItemRest>
            <HttpParams
              ref="httpParamsRef"
              v-model:value="model[field]"
              :requestType="getFieldsValue()?.method"
            />
          </FormItemRest>
        </template>
        <template #message="{ model, field }">
          <Textarea v-model:value="model[field]" :rows="3" />
          <!-- <Textarea
            v-model:value="model[field]"
            placeholder="变量格式:\${name};
        示例:尊敬的\${name},\${time}有设备触发告警,请注意处理"
            :rows="3"
            @change="handleMessageChange"
          /> -->
        </template>
        <!-- 变量 -->
        <template #variableDefinitions>
          <FormItemRest>
            <VariableDefinitions v-model:variableDefinitions="formData.variableDefinitions" />
          </FormItemRest>
        </template>
      </BasicForm>
    </div>
  </BasicModal>
</template>
<script lang="ts" setup>
  import { computed, ref } from 'vue';
  import { BasicModal, useModalInner } from '/@/components/Modal';
  import { BasicForm, useForm } from '/@/components/Form';

  import { useMessage } from '/@/hooks/web/useMessage';
  import {
    formSchemas,
    emailSchemas,
    smsSchemas,
    weixinSchemas,
    dindinSchemas,
    httpSchemas,
    feishuSchemas,
    templateColumns,
  } from '../Data';
  import VariableDefinitions from './VariableDefinitions.vue';
  import {
    messagePrepareAdd,
    messagePrepareUpdate,
    messageConfigQuery,
  } from '/@/api/modules/notice';
  import { userGroupQueryByMsgType } from '/@/api/modules/user';
  import { Select, Textarea, FormItemRest } from 'ant-design-vue';
  import UploadAttachment from './UploadAttachment.vue';
  import HttpParams from './HttpParams.vue';
  import EditTable from '@/views/notice/components/configuration/EditTable.vue';
  // interface IVariableDefinitions {
  //   id: string;
  //   name: string;
  //   type: string;
  //   format: string;
  //   value?: string;
  // }

  const emits = defineEmits(['success']);
  const { createMessage } = useMessage();
  const httpParamsRef = ref(null);
  const opertionType = ref('add');

  const formData = ref({
    variableDefinitions: [],
    attachments: [],
    // smsTemplate: [],
    templateDataList: [],
    userGroupList: [],
    agent: [],
  });

  const isVariable = computed(() => {
    return formData.value?.variableDefinitions?.length > 0;
  });

  const [registerModal, { setModalProps, closeModal }] = useModalInner((data) => {
    handleNoticeType(data.pushType);
    if (data.type == 'edit') {
      editConfigModal(data?.record);
    }
    setModalProps({
      title: data.type == 'add' ? '新增推送' : '编辑推送',
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
    schemas: formSchemas({ isVariable }),
    labelWidth: '100px',
    layout: 'vertical',
    baseColProps: { span: 24 },
  });

  function editConfigModal(record) {
    const { files, templateDataList, cookies, params, headers, ...ret } = record;
    const _msgType = +ret.msgType;
    // email
    if ([3].includes(_msgType)) {
      if (files) {
        let _file = JSON.parse(files) || [];
        if (!Array.isArray(_file)) {
          _file = [{ id: '0', ..._file }];
        }
        formData.value.attachments = _file;
      }
      ret.cc = ret.cc ? ret.cc?.split(',') : '';
    }

    // sms
    if ([1, 2].includes(_msgType)) {
      formData.value.templateDataList = templateDataList || [];
    }

    // console.log('record ret...', ret);
    // console.log('record formData.value.attachments...', formData.value.attachments);
    setTimeout(() => {
      setFieldsValue({ ...ret });
      // http
      if ([5].includes(_msgType)) {
        httpParamsRef.value && httpParamsRef.value.setTabList({ cookies, params, headers });
      }
      getUserGroupQueryByMsgType();
    });
  }

  // 类型
  function handleNoticeType(type) {
    const msgType = {
      sms: 1,
      email: 3,
      weixin: 4,
      http: 5,
      ding: 6,
      feishu: 7,
    };
    changeNoticeType(type);
    setTimeout(() => {
      setFieldsValue({
        msgType: msgType[type],
        // 消息通知方式
        msgNoticeType: '0',
        // http:请求方式
        method: 'GET',
        //
        bodyType: 'text/plain',
        // tab
        tabActive: 'Params',
        // 消息类型
        messageType: 'textMsg',
        // 钉钉通知方式
        radioType: type === 'ding' ? '工作通知方式' : (type === 'feishu' ? '群机器人消息' : '工作通知方式'),
      });
    });
    reset();
  }

  function changeNoticeType(type) {
    const config = {
      email: emailSchemas,
      sms: smsSchemas,
      weixin: weixinSchemas,
      ding: dindinSchemas,
      http: httpSchemas,
      feishu: feishuSchemas,
    };
    const fields = Object.keys(config)
      .map((c) => {
        const item = config[c]({});
        return item;
      })
      .reduce((p, c) => [...p, ...c], [])
      .map((item) => item.field);
    const schemas = config[type]({ getFieldsValue, setFieldsValue });
    removeSchemaByField(fields);
    appendSchemaByField(schemas, 'userGroupId');
  }

  // function changeMessage(value) {
  //   variableReg(value);
  // }

  // const spliceStr = (value) => {
  //   let variableFieldsStr = value;
  //   return variableFieldsStr || '';
  // };

  // const variableReg = (value) => {
  //   const _val = spliceStr(value);
  //   // 已经存在的变量
  //   const oldKey = formData.value.variableDefinitions?.map((m) => m.id);
  //   // 正则提取${}里面的值
  //   const pattern = /(?<=\$\{).*?(?=\})/g;
  //   const titleList = _val.match(pattern)?.filter((f) => f);
  //   const newKey = [...new Set(titleList)];
  //   const result = newKey?.map((m) =>
  //     oldKey.includes(m)
  //       ? formData.value.variableDefinitions.find((item) => item.id === m)
  //       : {
  //           id: m,
  //           name: '',
  //           type: 'string',
  //           format: '%s',
  //         },
  //   );
  //   formData.value.variableDefinitions = result as IVariableDefinitions[];
  // };

  // const handleMessageChange = (e) => {
  //   const value = e?.target?.value || e;
  //   value && changeMessage(value);
  // };

  const reset = () => {
    formData.value.variableDefinitions = [];
    formData.value.attachments = [];
    formData.value.templateDataList = [];
    // http
    if (getFieldsValue().msgType == 5) {
      httpParamsRef.value.reset();
    }
  };

  const handleCancel = () => {
    resetFields();
    reset();
  };

  const handleOk = () => {
    validate()
      .then(async () => {
        const { attachments } = formData.value;
        // // 变量
        // const variableDefinitions = {
        //   variableDefinitions: JSON.stringify(formData.value.variableDefinitions),
        // };
        const configKey = {
          1: 't_Msg_Sms',
          2: 't_Msg_Sms',
          3: 't_Msg_Mail',
          4: 't_Msg_Wx_Cp',
          5: 't_Msg_Http',
          6: 't_Msg_Ding',
          7: 't_Msg_Feishu',
        };
        const { id, msgType, ...t_Msg } = getFieldsValue();
        const _msgType = +msgType;
        // msgType
        t_Msg.msgType = _msgType;
        // edit
        if (opertionType.value == 'edit') {
          t_Msg.id = id;
        }
        // email
        if ([3].includes(_msgType)) {
          const cc = t_Msg.cc || [];
          t_Msg.cc = cc.length > 0 ? t_Msg.cc.join(',') : '';
          t_Msg.files = attachments.length > 0 ? JSON.stringify({ ...attachments[0] }) : '';
        }
        // http
        if ([5].includes(_msgType)) {
          // 先保存body和bodyType，避免被httpParams覆盖
          // 使用 getFieldsValue() 确保获取所有字段值，包括隐藏的 body 和 bodyType
          const allFields = getFieldsValue();
          // 优先使用 allFields 中的值，因为 formModel 中可能包含最新的值
          let bodyValue = allFields.body !== undefined ? allFields.body : t_Msg.body;
          let bodyTypeValue = allFields.bodyType !== undefined ? allFields.bodyType : (t_Msg.bodyType || 'application/json');
          
          // 如果 bodyValue 是 undefined 或 null，设置为空字符串，确保 MyBatis 会更新该字段
          if (bodyValue === undefined || bodyValue === null) {
            bodyValue = '';
          }
          
          console.log('保存前 - allFields:', allFields, 't_Msg:', t_Msg, 'bodyValue:', bodyValue, 'bodyTypeValue:', bodyTypeValue);
          
          const httpParams = httpParamsRef.value.getParams();
          console.log('httpParams:', httpParams);
          
          // 只覆盖params、headers、cookies，保留body和bodyType
          Object.keys(httpParams).forEach((key) => {
            // 确保不会覆盖 body 和 bodyType
            if (key !== 'body' && key !== 'bodyType') {
              t_Msg[key] = httpParams[key];
            }
          });
          
          // get请求不需要body
          if (t_Msg.method == 'GET') {
            delete t_Msg['bodyType'];
            delete t_Msg['body'];
          } else {
            // POST/PUT/PATCH等请求，始终设置body和bodyType
            // 即使body是空字符串，也要设置，确保MyBatis会更新该字段
            t_Msg.body = bodyValue;
            t_Msg.bodyType = bodyTypeValue || 'application/json';
          }
          
          // 调试日志
          console.log('保存HTTP消息 - 最终数据:', {
            body: t_Msg.body,
            bodyType: t_Msg.bodyType,
            params: t_Msg.params,
            headers: t_Msg.headers,
            cookies: t_Msg.cookies,
            method: t_Msg.method,
            url: t_Msg.url
          });
        }

        // templateDataList
        const templateDataList = formData.value.templateDataList.map((item) => {
          item.msgType = _msgType;
          return item;
        });

        const params = {
          msgType: _msgType,
          [configKey[_msgType]]: t_Msg,
          // sms
          templateDataList,
        };

        const ret =
          opertionType.value == 'add'
            ? await messagePrepareAdd(params)
            : await messagePrepareUpdate(params);
        createMessage.success(opertionType.value == 'add' ? '添加成功' : '编辑成功');
        closeModal();
        emits('success');
        handleCancel();
        console.log(ret);
        // console.log('getFieldsValue() ...', getFieldsValue(), params);
      })
      .catch((error) => {
        console.log(error);
        createMessage.error('操作失败');
      });
  };

  // 目标用户
  async function getUserGroupQueryByMsgType() {
    try {
      const { msgType } = getFieldsValue();
      const ret = await userGroupQueryByMsgType({ msgType: +msgType });
      console.log('ret', ret);
      formData.value.userGroupList = ret.map((item) => {
        item.label = item.userGroupName;
        item.value = item.id;
        return item;
      });
    }catch (error) {
    console.error(error)
      console.log(error);
    }
  }

  // 应用
  async function getMessageConfigQuery() {
    try {
      const { msgType } = getFieldsValue();
      const ret = await messageConfigQuery({ msgType: +msgType });
      const configKey = {
        4: 'wxCpApp',
        6: 'dingdingApp',
      };
      formData.value.agent = ret.data[0]?.configurationMap[configKey[msgType]].map((item) => {
        item.label = item.appName;
        item.value = item.agentId;
        return item;
      });
    }catch (error) {
    console.error(error)
      console.log(error);
    }
  }
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

    :deep(.message-item) {
      display: flex;
      flex-direction: column;
      align-items: center;
      width: 140px;
      height: 140px;
      padding: 5px;
      border-radius: 3px;

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

    :deep(.server-port),
    :deep(.server-ssl) {
      display: flex;
      align-items: center;

      & > div {
        margin-top: 10px;
        margin-bottom: 0;
        margin-left: 5px;
      }
    }

    :deep(.server-ssl) {
      & > div {
        margin-top: 7px;
      }
    }

    :deep(.upload-attachment-warpper) {
      .uaw-add {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 5px;
        border: 1px dashed #d9d9d9;
        border-radius: 5px;
        background: #fff;
        color: rgb(0 0 0 / 85%);
      }

      .uaw-add:hover {
        border-color: #5c85ff;
        color: #5c85ff;
      }
    }

    .cmb-monaco-editor {
      height: 200px;
      padding: 3px 3px 3px 0;
      overflow: hidden;
      border: solid 1px #d9d9d9;
      border-radius: 3px;
    }

    .error {
      color: #ed6f6f;
    }

    :deep(.iot-basic-help .anticon-info-circle) {
      vertical-align: text-bottom !important;
    }

    :deep(.message-warpper) {
      display: flex;
    }
    :deep(.hidden-label) {
      .ant-form-item-label {
        visibility: hidden;
      }
    }

    :deep(.none-label) {
      .ant-form-item-label {
        display: none;
      }
    }
  }
</style>
