<template>
  <div>
    <PushTemplate pushType="weixin" :columns="columns" />
  </div>
</template>
<script lang="ts" setup>
  import PushTemplate from '../PushTemplate/index.vue';

  const columns = [
    {
      title: '标题',
      dataIndex: 'title',
    },
    {
      title: '应用',
      dataIndex: 'agentId',
    },
    {
      title: '消息类型',
      dataIndex: 'cpMsgType',
    },
  ];
</script>
