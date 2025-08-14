<template>
  <div class="flex">
    <div
      v-for="(item, index) in tabList"
      :key="index"
      class="tab"
      :class="[value === index ? 'active' : '', index === 0 ? 'tabLeft' : 'tabRight']"
      @click="handleClickTab(index)"
      ><span class="iconify" :data-icon="item" data-inline="false"></span
    ></div>
  </div>
</template>

<script setup lang="ts">
  import { ref, defineProps, defineEmits } from 'vue';

  const props = defineProps({
    value: { type: Number, default: 0 },
  });
  const emits = defineEmits(['update:value']);
  const tabList = ref(['ant-design:appstore-outlined', 'material-symbols:format-list-bulleted']);
  function handleClickTab(index) {
    if (props.value === index) {
      return false;
    }
    emits('update:value', index);
  }
</script>

<style lang="less" scoped>
  .flex {
    display: flex;
  }

  .tab {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 24px;
    border: 1px solid #d9d9d9;

    svg {
      font-size: 18px;
    }
  }

  .tabLeft {
    border-radius: 2px 0 0 2px;
  }

  .tabRight {
    border-radius: 0 2px 2px 0;
  }

  .active {
    background: #0960bd;
    color: #fff;
  }
</style>
