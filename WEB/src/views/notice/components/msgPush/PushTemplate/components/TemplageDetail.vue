<template>
  <Spin :spinning="spinning">
    <Description @register="register" />
  </Spin>
</template>
<script lang="ts" setup>
  import { Description, useDescription } from '/@/components/Description/index';
  import { watch, ref, onMounted } from 'vue';
  import {} from '/@/api/modules/notice';
  import {
    commonDetailSchema,
    emailDetailSchemas,
    smsDetailSchemas,
    weixinDetailSchemas,
    dingDetailSchemas,
    httpDetailSchemas,
  } from '../Data.tsx';
  import { Spin } from 'ant-design-vue';

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

  const spinning = ref(false);
  const [register, { setDescProps }] = useDescription({
    column: 3,
    layout: 'vertical',
  });

  const setDetail = (record) => {
    const { msgType, ...ret } = record;
    const config = {
      1: smsDetailSchemas,
      2: smsDetailSchemas,
      3: emailDetailSchemas,
      4: weixinDetailSchemas,
      5: httpDetailSchemas,
      6: dingDetailSchemas,
    };
    const descSchema = config[msgType] || commonDetailSchema;
    const descData = {};
    descSchema.forEach((element) => {
      descData[element.field] = ret[element.field];
    });
    descData.msgType = msgType;
    setDescProps({
      data: descData,
      schema: descSchema,
    });
  };

  watch(
    () => props.record,
    (record) => {
      // console.log('watch ...', record);
      setDetail(record);
    },
  );

  onMounted(() => {
    // console.log('onMounted');
    setDetail(props.record);
  });
</script>
<style lang="less" scoped></style>
