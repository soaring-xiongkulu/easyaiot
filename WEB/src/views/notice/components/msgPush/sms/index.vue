<template>
  <div>
    <PushTemplate pushType="sms" :columns="columns" :searchField="searchField" />
  </div>
</template>
<script lang="ts" setup>
  import PushTemplate from '../PushTemplate/index.vue';

  const columns = [
    {
      title: '模版ID',
      dataIndex: 'templateId',
    },
  ];

  const searchField = [
    {
      field: `msgType`,
      label: `消息类型`,
      component: 'Select',
      componentProps: {
        options: [
          { label: '阿里云短信', value: 1 },
          { label: '腾讯云短信', value: 2 },
        ],
      },
      defaultValue: 1,
    },
  ];
</script>
