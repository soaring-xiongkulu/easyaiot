<template>
  <div>
    <PushTemplate pushType="feishu" :columns="columns" />
  </div>
</template>
<script lang="ts" setup>
  import PushTemplate from '../PushTemplate/index.vue';

  const columns = [
    {
      title: '通知方式',
      dataIndex: 'radioType',
    },
    {
      title: '消息类型',
      dataIndex: 'feishuMsgType',
    },
  ];
</script>

