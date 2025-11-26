<template>
  <BasicModal v-bind="$attrs" @register="register" @ok="handleSubmit">
    <div class="pt-3px pr-3px">
      <template v-if="tplType === 'add' || tplType === 'edit'">
        <BasicForm @register="registerForm" :model="model" />
      </template>
      <!-- 导入规则 -->
      <template v-else-if="tplType === 'import'">
        <UploadDragger
          v-model:fileList="fileList"
          name="file"
          accept=".json"
          :multiple="false"
          :customRequest="httpRequest"
          @change="handleUploadChange"
        >
          <CloudUploadOutlined :style="{ fontSize: '50px', color: '#1890ff' }" />
          <p class="ant-upload-text">单击或拖动文件到此区域进行上传</p>
          <p class="ant-upload-hint"> 导入JSON格式的文件上传规则链 </p>
        </UploadDragger>
      </template>
    </div>
  </BasicModal>
</template>
<script lang="ts">
  import { defineComponent, ref } from 'vue';
  import { BasicModal, useModalInner } from '@/components/Modal';
  import { BasicForm, FormSchema, useForm } from '@/components/Form';
  import { updateflows, addFlows, getFlows } from '@/api/device/rule-chains';
  import { useMessage } from '@/hooks/web/useMessage';
  import { Upload } from 'ant-design-vue';
  import { CloudUploadOutlined } from '@ant-design/icons-vue';

  const schemas: FormSchema[] = [
    {
      field: 'label',
      component: 'Input',
      label: '名称',
      colProps: {
        span: 24,
      },
      rules: [
        {
          required: true,
          // @ts-ignore
          validator: async (rule, value) => {
            if (!value) {
              /* eslint-disable-next-line */
              return Promise.reject('值不能为空');
            }
            return Promise.resolve();
          },
          trigger: 'change',
        },
      ],
    },
    {
      field: 'disabled',
      component: 'Checkbox',
      label: '状态',
      colProps: {
        span: 24,
      },
      defaultValue: false,
    },
  ];
  const UploadDragger = Upload.Dragger;
  export default defineComponent({
    components: { BasicModal, BasicForm, UploadDragger, CloudUploadOutlined },
    props: {
      userData: { type: Object },
    },
    setup(_, { emit }) {
      const modelRef = ref({});
      const { createMessage } = useMessage();
      const tplType = ref<string>('add');
      // let fileData;
      const [
        registerForm,
        {
          validateFields,
          resetFields,
          setFieldsValue,
          // setProps
        },
      ] = useForm({
        labelWidth: 70,
        schemas,
        showActionButtonGroup: false,
        actionColOptions: {
          span: 24,
        },
      });

      const detail = ref({});
      const flowsId = ref('');

      const [register, { closeModal, setModalProps }] = useModalInner((data) => {
        detail.value = {};
        data && onDataReceive(data);
      });

      function onDataReceive(_data) {
        console.log('Data Received', _data);
        const { info, isEdit, data } = _data;
        resetFields();
        tplType.value = info;
        const ModalTitle = tplType.value === 'add' ? '添加规则' : isEdit ? '编辑规则' : '导入规则';
        if (isEdit) {
          flowsId.value = data.id;
          getFlows(data.id).then((res) => {
            detail.value = res;
          });
          setFieldsValue({
            ...data,
          });
        }
        setModalProps({ title: ModalTitle, okButtonProps: { disabled: false } });
      }

      async function handleSubmit() {
        try {
          let params = {};
          const res = await validateFields();
          params = { ...res, nodes: [], configs: [] };

          try {
            if (tplType.value === 'add') {
              await addFlows(params);
            } else if (tplType.value === 'edit') {
              await updateflows(flowsId.value, params);
            }
            // const result = await updateflows(flowsId.value, params);
            // const ruleChainId = result.id;
            // if (tplType.value === 'import') {
            //   await postRuleChainMetadata({
            //     ...metadata,
            //     ruleChainId,
            //   });
            // }
            createMessage.success('操作成功！');
            closeModal();
            emit('success', {});
          }catch (error) {
    console.error(error)
            createMessage.error('操作失败！');
          }
        }catch (error) {
    console.error(error)
          console.log('not passing', error);
        }
      }

      function handleChange(list: string[]) {
        console.log(`已上传文件${JSON.stringify(list)}`);
      }

      const handleUploadChange = (info) => {
        const status = info.file.status;
        if (status !== 'uploading') {
          console.log(info.file, info.fileList);
        }
        if (status === 'done') {
          console.log(`${info.file.name} file uploaded successfully.`);
        } else if (status === 'error') {
          console.log(`${info.file.name} file upload failed.`);
        }
      };

      function httpRequest(data) {
        const isJson = data.file.type === 'application/json';
        if (isJson) {
          const reader = new FileReader();
          reader.onload = (evt) => {
            try {
              console.log(evt);
              // this.form.file = JSON.parse(evt.target.result)
              // let result: any = evt?.target?.result ?? '';
              // fileData = JSON.parse(result);
              data.onSuccess();
            }catch (error) {
    console.error(error)
              createMessage.error(String(error));
              data.onError();
              // this.$refs.upload.clearFiles()
            }
          };
          reader.readAsText(data.file);
        } else {
          createMessage.error('应用库只能上传JSON文件');
        }
      }

      return {
        httpRequest,
        fileList: ref([]),
        handleUploadChange,
        handleChange,
        handleSubmit,
        register,
        schemas,
        registerForm,
        model: modelRef,
        tplType,
      };
    },
  });
</script>
