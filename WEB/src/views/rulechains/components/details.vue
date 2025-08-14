<template>
  <div class="details">
    <Description @register="register" layout="vertical" />
  </div>
</template>

<script lang="ts" setup name="Details">
  import { Description, useDescription } from '@/components/Description';
  import { detailSchmea } from '../tableData';
  import { watchEffect } from 'vue';

  const props = defineProps({
    id: { type: String, default: '' },
    info: { type: Object },
  });

  const [register, { setDescProps }] = useDescription({
    // title: '生产环境依赖',
    schema: detailSchmea(),
    column: 3,
  });

  watchEffect(() => {
    if (props.info?.label) {
      const params = {
        ...props.info,
      };
      console.log(params);
      setDescProps({
        data: params,
      });
    }
  });
</script>

<style lang="less" scoped></style>
