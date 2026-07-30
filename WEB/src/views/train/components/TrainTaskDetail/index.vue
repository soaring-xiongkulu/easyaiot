<template>
  <div class="train-wrapper">
    <div class="train-tab">
      <TrainTaskList :modelId="modelId"></TrainTaskList>
    </div>
  </div>
</template>

<script lang="ts" setup name="TrainService">
import { useRoute } from 'vue-router';
import TrainTaskList from "@/views/train/components/TrainTaskList/index.vue";

defineOptions({ name: 'TrainDetail' })

const { query } = useRoute()

const modelId = query.modelId
</script>

<style lang="less" scoped>
.train-wrapper {
  background: #ffffff;

  .train-tab {
    padding: 0;
    background-color: #FFFFFF;
  }
}
</style>
