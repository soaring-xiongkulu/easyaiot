<template>
  <div class="apply">
    <Table :dataSource="dataSource" :columns="columns" :pagination="false" bordered />
  </div>
</template>
<script lang="ts" setup>
  import { Table } from 'ant-design-vue';
  import { watch, onMounted, ref } from 'vue';

  const props = defineProps({
    record: {
      type: Object,
      default: () => ({}),
    },
    activeKey: {
      type: String,
      default: '',
    },
    page: {
      type: String,
      default: 'push',
    },
  });

  const dataSource = ref([]);
  const columns = ref([]);
  const common = [
    {
      title: 'Name',
      dataIndex: 'name',
    },
    {
      title: 'Value',
      dataIndex: 'value',
    },
  ];
  const weixinConfig = [
    {
      title: '应用名称',
      dataIndex: 'appName',
    },
    {
      title: 'AgentId',
      dataIndex: 'agentId',
    },
    {
      title: 'Secret',
      dataIndex: 'secret',
    },
  ];

  const dingMsgConfig = [
    {
      title: '应用名称',
      dataIndex: 'appName',
    },
    {
      title: 'AgentId',
      dataIndex: 'agentId',
    },
    {
      title: 'AppKey',
      dataIndex: 'appKey',
    },
    {
      title: 'AppSecret',
      dataIndex: 'appSecret',
    },
  ];

  const dxMsgPush = [
    {
      title: 'Name',
      dataIndex: 'name',
    },
    {
      title: 'Value',
      dataIndex: 'value',
    },
  ];

  const cookieMsgPush = [
    {
      title: 'Name',
      dataIndex: 'name',
    },
    {
      title: 'Value',
      dataIndex: 'value',
    },
    {
      title: 'Domain',
      dataIndex: 'domain',
    },
    {
      title: 'Path',
      dataIndex: 'path',
    },
    {
      title: 'Time',
      dataIndex: 'time',
    },
  ];

  const bodyMsgPush = [
    {
      title: '请求体类型',
      dataIndex: 'bodyType',
    },
    {
      title: '请求体',
      dataIndex: 'body',
    },
  ];

  const analysis = (strList) => {
    if (strList) {
      return JSON.parse(strList);
    }
    return [];
  };

  const msgConfig = (record) => {
    const msgType = +record?.msgType;
    let c = common;
    let d = [];
    if ([4].includes(msgType)) {
      c = weixinConfig;
      d = record?.configurationMap?.wxCpApp ?? [];
    } else if ([6].includes(msgType)) {
      c = dingMsgConfig;
      d = record?.configurationMap?.dingdingApp ?? [];
    }
    columns.value = c;
    dataSource.value = d;
  };

  const msgPush = (record) => {
    const msgType = +record?.msgType;
    let c = common;
    let d = [];
    if ([1, 2].includes(msgType)) {
      c = dxMsgPush;
      d = record?.templateDataList ?? [];
    } else if ([5].includes(msgType)) {
      const activeKey = props.activeKey;
      const { bodyType, body, params, headers, cookies } = record;
      switch (activeKey) {
        case 'params':
          d = analysis(params);
          break;
        case 'headers':
          d = analysis(headers);
          break;
        case 'cookies':
          d = analysis(cookies);
          c = cookieMsgPush;
          break;
        case 'body':
          c = bodyMsgPush;
          d = [{ bodyType, body }];
          break;
        default:
      }
    }
    columns.value = c;
    dataSource.value = d;
  };

  function setTable(record) {
    if (props.page == 'config') {
      msgConfig(record);
    } else {
      msgPush(record);
    }
  }

  watch(
    () => props.activeKey,
    () => {
      setTable(props.record);
    },
  );

  onMounted(() => {
    setTable(props.record);
  });
</script>
<style scoped lang="less">
  .apply {
    background-color: #f0f2f5;
  }
</style>
