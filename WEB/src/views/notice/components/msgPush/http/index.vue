<template>
  <div>
    <PushTemplate pushType="http" :columns="columns" />
  </div>
</template>
<script lang="ts" setup>
  import PushTemplate from '../PushTemplate/index.vue';

  const columns = [
    {
      title: '请求方法',
      dataIndex: 'method',
    },
    {
      title: 'URL',
      dataIndex: 'url',
    },
  ];
</script>
