<template>
  <BasicModal v-bind="$attrs" @register="register" @ok="handleSubmit">
    <Form :model="validateInfos" :colon="false">
      <!-- <h2>请选择客户分配设备</h2> -->
      <FormItem label="客户" v-bind="validateInfos.customId">
        <Select
          placeholder="请选择客户"
          v-model:value="modelRef.customId"
          @focus="getDeviceList"
          @popup-scroll="handlePopupScroll"
          :options="customList"
          allowClear
        />
      </FormItem>
    </Form>
  </BasicModal>
</template>
<script setup lang="ts">
  import { ref, reactive, defineEmits } from 'vue';
  import { BasicModal, useModalInner } from '@/components/Modal';
  import { Form, FormItem, Select } from 'ant-design-vue';
  import { getDeviceCustomList, postAssignDeviceCustom } from '@/api/device/devices';
  import { useMessage } from '@/hooks/web/useMessage';

  const { createMessage } = useMessage();
  const useForm = Form.useForm;
  const emits = defineEmits(['success']);

  const customParams = reactive({
    pageSize: 10,
    page: 1,
  });
  const customList = ref([]);
  const [register, { closeModal, setModalProps }] = useModalInner((data) => {
    data && setModalProps({ okButtonProps: { disabled: false } });
    modelRef.deviceId = data.deviceId;
  });
  const modelRef = reactive({
    customId: null,
    deviceId: [],
  });
  const rulesRef = reactive({
    customId: [{ required: true, message: '请选择客户', trigger: 'blur' }],
  });

  const { resetFields, validate, validateInfos } = useForm(modelRef, rulesRef);

  // 下拉框下拉加载
  function handlePopupScroll(event) {
    const { scrollHeight, scrollTop, clientHeight } = event.target;
    if (scrollHeight - scrollTop === clientHeight) {
      customParams.pageSize += 10;
      getDeviceList();
    }
  }
  async function getDeviceList() {
    const { data } = await getDeviceCustomList(customParams);
    const tempList = data.map((item) => {
      return {
        label: item.name,
        value: item.id.id,
      };
    });
    customList.value = tempList;
  }

  async function handleSubmit() {
    await validate();
    // const { status } = await postAssignDeviceCustom(modelRef);
    try {
      const { customId, deviceId } = modelRef;
      await Promise.all([...deviceId.map((item) => postAssignDeviceCustom(item, customId))]);
      createMessage.success(`分配成功`);
      resetFields();
      closeModal();
      emits('success', {});
    }catch (error) {
    console.error(error)
      createMessage.error(`分配失败`);
    }
  }
</script>
