<template>
  <div class="phsyical-modal-title">
    <Space direction="vertical">
      <div class="product-phsyical-model-tab">
        <Tabs
          :activeKey="state.activeKey"
          :tabBarGutter="80"
          @tabClick="handleTabClick"
        >
          <TabPane key="properties" tab="属性">
            <Alert type="info" show-icon>
              <template #message>
                <div v-show="!props.isEdit">
                  当前展示的是已发布到线上的属性定义,如需修改,请点击
                  <Button size="small" type="link" @click="handleClickEdit(true)">"编辑物模型"</Button>
                </div>

                <div v-show="props.isEdit"> 您正在编辑的是草稿,需点击发布后,物模型才会正式生效. </div>
              </template>
            </Alert>
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
import {Alert, Button, Space, TabPane, Tabs} from 'ant-design-vue';
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
    activeKey: 'properties'
  });

  const handleTabClick = (activeKey) => {
    state.activeKey = activeKey;
    emit('update:functionType', activeKey);
  };

  const handleClickEdit = (flag) => {
    emit('update:isEdit', flag);
  };

  // const handleShowTSL = () => {
  //   emit('showTsl');
  // };

  const handleAddPhsyical = () => {
    emit('addPhsyical');
  };

  const handleReload = () => {
    emit('reload');
  };

  const handleRelease = () => {
    emit('release');
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
