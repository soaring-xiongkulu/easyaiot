<template>
  <Form :colon="false">
    <FormItem label="Object列表">
      <Select
        v-model:value="modelRef.objectLwm2m"
        placeholder="请选择"
        :options="lwmList"
        @focus="getLwmList"
      />
    </FormItem>
  </Form>
</template>

<script setup lang="ts">
  import { Form, FormItem, Select } from 'ant-design-vue';
  import { ref, reactive } from 'vue';
  import { getLwmInfosList } from '@/api/device/devices';

  const useForm = Form.useForm;
  const lwmList = ref<any>([]);
  const lwmParams = reactive({
    pageSize: 50,
    page: 0,
    sortProperty: 'id',
    sortOrder: 'ASC',
  });
  async function getLwmList() {
    const { data } = await getLwmInfosList(lwmParams);
    const tempList = data.map((item) => {
      return {
        label: item.name,
        value: item.id.id,
        id: item.id,
      };
    });
    lwmList.value = [...lwmList.value, ...tempList];
  }
  const modelRef = reactive({
    objectLwm2m: null,
  });
  useForm(modelRef);
</script>
