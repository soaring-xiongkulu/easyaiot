<template>
  <div class="phsyical-modal-title">
    <Space direction="vertical">
      <div class="product-phsyical-model-tab">
        <Tabs
          :activeKey="state.activeKey"
          :tabBarGutter="80"
          @tabClick="handleTabClick"
        >
          <TabPane key="services" tab="服务">
          </TabPane>
        </Tabs>
      </div>

      <!-- <Button v-show="!isEdit" type="primary">物理模型TSL</Button> -->

      <div class="box">
        <Space v-show="props.isEdit">
<!--          <Button type="primary" @click="handleRelease">发布上线</Button>-->
          <Button v-show="props.isEdit" type="primary" @click="handleAddPhsyical">
            新增物模型
          </Button>
          <Button @click="handleClickEdit(false)">返回</Button>
        </Space>
      </div>
    </Space>

    <!-- <Space>
      <RedoOutlined :style="{ fontSize: '20px' }" class="cursor" @click="handleReload" />
    </Space> -->
  </div>
</template>

<script lang="ts" setup name="PhsyicalModalTitle">
import {Button, Space, TabPane, Tabs} from 'ant-design-vue';
import {reactive, withDefaults} from 'vue';

// import { RedoOutlined } from '@ant-design/icons-vue';

  interface Props {
    isEdit: boolean;
  }

  const props = withDefaults(defineProps<Props>(), {
    isEdit: false,
  });

  const emit = defineEmits(['showTsl', 'addPhsyical', 'update:isEdit', 'reload', 'release', 'update:functionType']);

  const state = reactive({
    activeKey: 'services'
  });

  const handleTabClick = (activeKey) => {
    state.activeKey = activeKey;
    emit('update:functionType', activeKey);
  };

  const handleClickEdit = (flag) => {
    emit('update:isEdit', flag);
  };

  const handleAddPhsyical = () => {
    emit('addPhsyical');
  };
</script>

<style lang="less" scoped>
  .phsyical-modal-title {
    display: flex;
    width: 100%;

    > .ant-space {
      &:first-child {
        flex: 1;
        justify-content: end;
        margin-right: 10px;
      }

      &:last-child {
        justify-content: center;
        min-width: 60px;
      }
    }

    .box {
      display: flex;
      justify-content: space-between;
    }

    .cursor {
      cursor: pointer;
    }
  }
</style>
