<template>
  <div class="go-config-item-box">
    <span class="item-left">
      {{ name }}
      <a-space :size="5">
        <slot name="name"></slot>
      </a-space>
    </span>
    <div
      class="item-right"
      :style="{
        gridTemplateColumns: alone ? '1fr' : '1fr 1fr',
        ...itemRightStyle
      }"
    >
      <slot></slot>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps({
  name: {
    type: String,
    required: false
  },
  alone: {
    type: Boolean,
    default: false,
    required: false
  },
  itemRightStyle: {
    type: Object,
    default: () => {},
    required: false
  }
})
</script>

<style lang="less" scoped>
@leftWidth: 60px;
.go-config-item-box {
  position: relative;
  display: flex;
  margin: 20px 0;
  .item-left {
    width: @leftWidth;
    text-align: left;
    margin-top: 4px;
    margin-left: 10px;
    font-size: 12px;
  }
  .item-right {
    display: grid;
    grid-column-gap: 10px;
    width: calc(100% - @leftWidth);
  }
}
</style>
