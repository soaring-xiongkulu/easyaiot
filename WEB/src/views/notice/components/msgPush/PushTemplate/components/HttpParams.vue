<!-- eslint-disable vue/v-on-event-hyphenation -->
<template>
  <div class="http-params-tabs">
    <Tabs
      :animated="{ inkBar: true, tabPane: true }"
      :activeKey="activeKey"
      :tabBarGutter="80"
      @tabClick="handleTabClick"
    >
      <TabPane v-for="item in tabs" :key="item.key" :tab="item.tab">
        <component :is="item.component" :columns="item.columns" v-model:list="item.list" />
      </TabPane>
      <TabPane tab="Body" key="Body" :disabled="isGetRequest" />
    </Tabs>
  </div>
</template>
<script lang="ts" setup>
  import { computed, ref, shallowRef } from 'vue';
  import { Tabs, TabPane } from 'ant-design-vue';
  import EditTable from '@/views/notice/components/configuration/EditTable.vue';

  const Edit = shallowRef(EditTable);

  type Emits = {
    (e: 'update:value', data: string): void;
  };
  const emit = defineEmits<Emits>();

  const props = defineProps({
    requestType: {
      type: String,
      default: '',
    },
  });

  const isGetRequest = computed(() => props.requestType == 'GET');

  const operationFiled = [
    {
      title: '操作',
      dataIndex: 'operation',
      width: 80,
      fixed: 'right',
      align: 'center',
    },
  ];

  const paramsColumns = [
    {
      title: 'Name',
      dataIndex: 'name',
    },
    {
      title: 'Value',
      dataIndex: 'value',
    },
    ...operationFiled,
  ];

  const cookieColumns = [
    {
      title: 'Name',
      dataIndex: 'name',
      width: 100,
    },
    {
      title: 'Value',
      dataIndex: 'value',
      width: 100,
    },
    {
      title: 'Domain',
      dataIndex: 'domain',
      width: 100,
    },
    {
      title: 'Path',
      dataIndex: 'path',
      width: 100,
    },
    {
      title: 'Time',
      dataIndex: 'time',
      width: 100,
    },
    ...operationFiled,
  ];

  const tabs = ref([
    {
      key: 'params',
      component: Edit,
      tab: 'Params',
      list: [],
      columns: paramsColumns,
    },
    {
      key: 'headers',
      component: Edit,
      tab: 'Headers',
      list: [],
      columns: paramsColumns,
    },
    {
      key: 'cookies',
      component: Edit,
      tab: 'Cookies',
      list: [],
      columns: cookieColumns,
    },
  ]);

  const activeKey = computed({
    get: () => props.value,
    set: (val) => emit('update:value', val),
  });

  const handleTabClick = (key) => {
    activeKey.value = key;
  };

  const reset = () => {
    tabs.value.forEach((item) => {
      item.list = [];
    });
  };

  const setTabList = (data) => {
    tabs.value.forEach((element) => {
      element.list = JSON.parse(data[element.key]) || [];
    });
  };

  function getParams() {
    const params = tabs.value.reduce((pre, c) => {
      pre[c.key] = JSON.stringify(c.list);
      return pre;
    }, {});
    return params;
  }

  defineExpose({ getParams, reset, setTabList });
</script>
<style lang="less" scoped>
  .http-params-tabs {
    width: 870px;
    overflow: auto;
  }
  :deep(.content-type) {
    margin-bottom: 0 !important;
  }
</style>
