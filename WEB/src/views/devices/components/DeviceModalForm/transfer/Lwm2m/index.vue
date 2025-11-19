<template>
  <div class="LwnObject">
    <Tabs v-model:activeKey="activeKey" centered :tabBarGutter="150">
      <TabPane v-for="(item, index) in tabList" :key="index" :tab="item.title">
        <component ref="componentRef" v-if="item.componentName" :is="item.componentName" />
      </TabPane>
    </Tabs>
  </div>
</template>

<script setup lang="ts">
  import { ref, reactive, defineExpose, defineProps } from 'vue';
  import { Tabs, TabPane } from 'ant-design-vue';
  import LwnObject from './LwnObject.vue';
  import Bootstrap from './Bootstrap.vue';
  import OtherConfig from './OtherConfig.vue';

  const tabList = reactive([
    { title: 'LWM2M模式', componentName: LwnObject },
    { title: 'Bootstrap', componentName: Bootstrap },
    { title: '其它设置', componentName: OtherConfig },
    { title: '设备配置JSON' },
  ]);
  defineExpose({
    getTransferConfigFormData,
  });
  defineProps({
    type: {
      type: String,
    },
  });
  const componentRef = ref();
  const activeKey = ref(2);
  function getTransferConfigFormData() {
    return 'modelRef';
  }
</script>

<style lang="less" scoped>
  .LwnObject {
    margin-top: -20px;
  }
</style>
