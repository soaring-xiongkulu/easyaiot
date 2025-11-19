<template>
  <div>
    <PushTemplate pushType="ding" :columns="columns" />
  </div>
</template>
<script lang="ts" setup>
  import PushTemplate from '../PushTemplate/index.vue';

  const columns = [
    // {
    //   title: '标题',
    //   dataIndex: 'title',
    // },
    {
      title: '通知方式',
      dataIndex: 'radioType',
    },
    {
      title: '消息类型',
      dataIndex: 'dingMsgType',
    },
  ];
</script>
