<template>
  <BasicModal
    @register="registerModal"
    @cancel="handleCancel"
    @ok="handleOk"
    title="计划推送"
    width="600px"
    :canFullscreen="false"
    wrapClassName="plan-modal"
  >
    <Form ref="formRef" layout="vertical" :model="formData">
      <FormItem
        label="任务"
        name="templateId"
        :rules="{ required: true, message: '该字段为必填字段' }"
      >
        <Select
          v-model:value="formData.templateId"
          :options="templateData.list"
          placeholder="请选择"
          @change="handleChangeNoticeTemplate"
        />
      </FormItem>
    </Form>
  </BasicModal>
</template>
<script lang="ts" setup>
  import { ref } from 'vue';
  import { BasicModal, useModalInner } from '/@/components/Modal';
  import { useMessage } from '/@/hooks/web/useMessage';
  import { Form, FormItem, Select } from 'ant-design-vue';

  const { createMessage } = useMessage();
  const formRef = ref(null);
  const formData = ref({
    templateId: undefined,
  });

  const templateData = ref({
    list: [],
  });
  const itemId = ref('');

  const [registerModal, { closeModal }] = useModalInner((data) => {
    console.log(data);
    itemId.value = data.id;
  });

  const handleCancel = () => {
    formData.value.templateId = '';
  };

  const handleOk = () => {
    formRef.value
      .validate()
      .then(async () => {
        closeModal();
        handleCancel();
        createMessage.success('推送成功');
      })
      .catch((err) => {
        console.error(err);
        createMessage.error('操作失败');
      });
  };
</script>
<style lang="less" scoped>
  :deep(.ant-form-item) {
    margin-bottom: 0;
  }

  :global(.plan-modal .scrollbar__view > div) {
    height: auto !important;
    min-height: auto !important;
  }
</style>
