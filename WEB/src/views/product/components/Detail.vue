<template>
  <BasicDrawer @register="register" title="产品详情" width="60%">
    <Tabs v-model:activeKey="activeKey">
      <TabPane v-for="item in tabPaneList" :key="item.key" :tab="item.label">
        <component :is="item.componentName" />
      </TabPane>

      <!-- <template #tabBarExtraContent>
        <a-button>Extra Action</a-button>
      </template> -->
    </Tabs>
  </BasicDrawer>
</template>

<script lang="ts" setup name="Detail">
  import { BasicDrawer, useDrawerInner } from '@/components/Drawer';
  import { Tabs, TabPane } from 'ant-design-vue';
  import { ref } from 'vue';
  import PhsyicalModal from './PhsyicalModal.vue';

  const [register, { setDrawerProps, closeDrawer }] = useDrawerInner(() => {});

  const activeKey = ref('PhsyicalModal');
  const tabPaneList = [
    {
      label: '物理模型管理',
      key: 'PhsyicalModal',
      componentName: PhsyicalModal,
    },
  ];
</script>

<style lang="less" scoped></style>
