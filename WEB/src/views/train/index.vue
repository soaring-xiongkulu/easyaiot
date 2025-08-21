<template>
  <div class="train-wrapper">
    <div class="train-tab">
      <ModelCardList></ModelCardList>
    </div>
  </div>
</template>

<script lang="ts" setup name="TrainService">
import {reactive} from 'vue';
import ModelCardList from "@/views/train/components/ModelCardList/index.vue";

defineOptions({name: 'TRAIN'})

const state = reactive({
  activeKey: '1'
});
</script>

<style lang="less" scoped>
.train-wrapper {
  :deep(.ant-tabs-nav) {
    padding: 5px 0 0 25px;
  }

  .train-tab {
    padding: 16px 19px 0 15px;

    .ant-tabs {
      background-color: #FFFFFF;

      :deep(.ant-tabs-nav) {
        padding: 5px 0 0 25px;
      }
    }
  }
}
</style>
