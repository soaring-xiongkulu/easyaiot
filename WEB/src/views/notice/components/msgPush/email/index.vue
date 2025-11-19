<template>
  <div>
    <PushTemplate pushType="email" :columns="columns" />
  </div>
</template>
<script lang="ts" setup>
  import PushTemplate from '../PushTemplate/index.vue';

  const columns = [
    {
      title: '标题',
      dataIndex: 'title',
    },
    // {
    //   title: '抄送',
    //   dataIndex: 'cc',
    // },
    {
      title: '内容',
      dataIndex: 'content',
    },
  ];
</script>
