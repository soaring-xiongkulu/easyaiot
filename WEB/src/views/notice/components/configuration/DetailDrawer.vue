<!-- eslint-disable vue/v-on-event-hyphenation -->
<template>
  <BasicDrawer @register="register" title="消息设置" width="880px" @close="handleClose">
    <Tabs
      :animated="{ inkBar: true, tabPane: true }"
      :activeKey="activeKey"
      :tabBarGutter="80"
      @tabClick="handleTabClick"
    >
      <TabPane v-for="item in tabs" :key="item.key" :tab="item.tab" :disabled="_disabled">
        <component :is="item.component" :record="record" :activeKey="activeKey" page="config" />
      </TabPane>
    </Tabs>
  </BasicDrawer>
</template>
<script lang="ts" setup>
  import { ref, computed } from 'vue';
  import { BasicDrawer, useDrawerInner } from '@/components/Drawer';
  import { Tabs, TabPane } from 'ant-design-vue';
  import ConfigDetail from './ConfigDetail.vue';
  import Apply from '@/views/notice/components/msgPush/PushTemplate/components/Apply.vue';

  const activeKey = ref('detail');
  const record = ref(-1);
  const tabs = [
    { key: 'detail', component: ConfigDetail, tab: '详情' },
    { key: 'apply', component: Apply, tab: '应用' },
  ];

  const _disabled = computed(() => {
    return [1, 2, 3, 5].includes(+record.value?.msgType);
  });

  const [register] = useDrawerInner((data) => {
    // console.log('data ..', data);
    record.value = data;
  });
  const handleClose = () => {
    activeKey.value = 'detail';
  };
  const handleTabClick = (key) => {
    activeKey.value = key;
  };
</script>

<style lang="less" scoped></style>
