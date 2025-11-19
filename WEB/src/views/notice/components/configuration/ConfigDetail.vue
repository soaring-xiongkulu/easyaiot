<template>
  <Description @register="register" />
</template>
<script lang="ts" setup>
  import { Description, useDescription } from '@/components/Description';
  import { watch } from 'vue';
  import {
    commonDetailSchema,
    emailDetailSchemas,
    aliyunDetailSchemas,
    tengxunyunDetailSchemas,
    weixinDetailSchemas,
    dingDetailSchemas,
    httpDetailSchemas,
  } from '../../Data.tsx';

  const props = defineProps({
    record: {
      type: Object,
      default: () => ({}),
    },
    activeKey: {
      type: String,
      default: '',
    },
  });

  const [register, { setDescProps }] = useDescription({
    column: 3,
    layout: 'vertical',
  });

  watch(
    () => props.record,
    (record) => {
      // console.log('watch .....', record);
      setDescription(record);
    },
  );

  function setDescription(record) {
    // console.log('setDescription ...', record);
    const { msgType, configurationMap } = record;
    const config = {
      1: aliyunDetailSchemas,
      2: tengxunyunDetailSchemas,
      3: emailDetailSchemas,
      4: weixinDetailSchemas,
      5: httpDetailSchemas,
      6: dingDetailSchemas,
    };
    const descSchema = config[msgType] || commonDetailSchema;
    const descData = {};
    descSchema.forEach((element) => {
      descData[element.field] = configurationMap[element.field];
    });
    descData.msgType = msgType;
    // console.log(descSchema, descData);
    setDescProps({
      data: descData,
      schema: descSchema,
    });
  }
</script>
<style lang="less" scoped></style>
