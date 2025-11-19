<!-- eslint-disable vue/v-on-event-hyphenation -->
<template>
  <BasicDrawer @register="register" title="消息推送" width="880px" @close="handleClose">
    <Tabs
      :animated="{ inkBar: true, tabPane: true }"
      :activeKey="activeKey"
      :tabBarGutter="80"
      @tabClick="handleTabClick"
    >
      <TabPane v-for="item in tabs" :key="item.key" :tab="item.tab" :disabled="_disabled">
        <component :is="item.component" :record="record" :activeKey="activeKey" />
      </TabPane>
    </Tabs>
  </BasicDrawer>
</template>
<script lang="ts" setup>
  import { ref, computed, shallowRef } from 'vue';
  import { BasicDrawer, useDrawerInner } from '/@/components/Drawer';
  import { Tabs, TabPane } from 'ant-design-vue';
  import TemplageDetail from './TemplageDetail.vue';
  import Apply from './Apply.vue';

  const ApplyCom = shallowRef(Apply);
  const DetailCom = shallowRef(TemplageDetail);

  const activeKey = ref('detail');
  const record = ref(null);
  const tabs = ref(null);

  const _disabled = computed(() => {
    return [3, 4, 6].includes(record.value?.msgType);
  });

  const [register] = useDrawerInner((data) => {
    record.value = data.record;
    updateTab(data.record);
  });
  const handleClose = () => {
    activeKey.value = 'detail';
  };
  const handleTabClick = (key) => {
    activeKey.value = key;
  };

  const updateTab = (record) => {
    const detail = [{ key: 'detail', component: DetailCom, tab: '详情' }];
    const apply = [{ key: 'apply', component: ApplyCom, tab: '模版' }];
    const params = [
      { key: 'params', component: ApplyCom, tab: 'Params' },
      { key: 'headers', component: ApplyCom, tab: 'Headers' },
      { key: 'cookies', component: ApplyCom, tab: 'Cookies' },
      { key: 'body', component: ApplyCom, tab: 'Body' },
    ];
    if ([5].includes(+record?.msgType)) {
      tabs.value = [...detail, ...params];
    } else {
      tabs.value = [...detail, ...apply];
    }
  };
</script>

<style lang="less" scoped></style>
