<template>
  <BasicDrawer v-bind="$attrs" @register="register" title="-规则链详情" width="880px">
    <Tabs v-model:activeKey="activeKey">
      <TabPane v-for="item in tabPaneList" :key="item.componentName" :tab="item.label">
        <component
          v-if="JSON.stringify(info) !== '{}'"
          :is="item.componentName"
          :id="id"
          :info="info"
          :scopeList="scopeList"
          :eventList="eventList"
          :eventType="eventType"
          @submit="RuleChainsInfo"
        />
      </TabPane>

      <!-- <template #tabBarExtraContent>
        <a-button>Extra Action</a-button>
      </template> -->
    </Tabs>
  </BasicDrawer>
</template>
<script lang="ts">
  import { defineComponent, ref } from 'vue';
  import { BasicDrawer, useDrawerInner } from '@/components/Drawer';
  import { Tabs, TabPane } from 'ant-design-vue';
  import DetailsInfo from './components/details.vue';
  import { Attribute, } from '@/components/EditDrawer';

  import { getFlows } from '@/api/device/rule-chains';

  export default defineComponent({
    components: {
      BasicDrawer,
      Tabs,
      TabPane,
      Attribute,
      Event,
    },
    setup(_, { emit }) {
      const [register, { setDrawerProps, closeDrawer }] = useDrawerInner((data) => {
        data && onDataReceive(data);
      });
      const id = ref<string>('');
      const info = ref<object>({});
      function onDataReceive(data) {
        console.log('Data Received', data);
        id.value = data.id;
        setDrawerProps({ title: data.data + '-规则链详情' });
        RulesInfo(id.value);
      }

      async function RulesInfo(id) {
        try {
          const ret = await getFlows(id);
          info.value = ret['data'];
        }catch (error) {
    console.error(error)
          console.log(error);
        }
      }

      function RuleChainsInfo() {
        closeDrawer();
        emit('success', {});
      }

      return {
        id,
        info,
        register,
        activeKey: ref('DetailsInfo'),
        tabPaneList: [
          { label: '详情', componentName: 'DetailsInfo' },
        ],
        RuleChainsInfo,
        scopeList: [{ label: '服务端属性', value: 'SERVER_SCOPE' }],
        eventList: [
          { label: '错误', value: 'ERROR' },
          { label: '生命周期事件', value: 'LC_EVENT' },
          { label: '类型统计', value: 'STATS' },
          { label: '调试', value: 'DEBUG_RULE_CHAIN' },
        ],
        eventType: 'DEBUG_RULE_CHAIN',
      };
    },
  });
</script>
