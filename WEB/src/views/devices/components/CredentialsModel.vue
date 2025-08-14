<template>
  <BasicModal v-bind="$attrs" @register="register" @ok="handleSubmit">
    <CredentialsForm ref="CredentialsFormRef"/>
  </BasicModal>
</template>
<script setup lang="ts">
import {BasicModal, useModalInner} from '@/components/Modal';
import {ref} from 'vue';
import {useMessage} from '@/hooks/web/useMessage';
import {postDeviceCredentials} from '@/api/device/devices';
import {CredentialsForm} from '../components';

const {createMessage} = useMessage();
const emits = defineEmits(['success']);

const CredentialsFormRef = ref();

const [register, {closeModal, setModalProps}] = useModalInner((data) => {
  data && setModalProps({okButtonProps: {disabled: false}});
  CredentialsFormRef.value.fetchData(data.deviceId);
});

async function handleSubmit() {
  const modelRef = await CredentialsFormRef.value.handleValidate();
  try {
    const {status} = await postDeviceCredentials(modelRef);
    if (status === 200) {
      createMessage.success(`分配成功`);
      closeModal();
      emits('success', {});
    } else {
      createMessage.error(`分配失败`);
    }
  }catch (error) {
    console.error(error)
    createMessage.error(`分配失败`);
  }
}
</script>
