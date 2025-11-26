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
  .train-tab {
    padding: 16px 19px 0 15px;
    background-color: #FFFFFF;
  }
}
</style>
