<template>
  <a-divider style="margin: 10px 0;"></a-divider>
  <a-collapse-panel arrow-placement="right" :default-expanded-names="expanded ? name : null" accordion>
    <!-- 右侧 -->
    <template #header-extra>
      <div @click="click">
        <slot name="header"></slot>
      </div>
    </template>

    <div :title="name" :name="name">
      <slot></slot>
    </div>
  </a-collapse-panel>
</template>

<script setup lang="ts">
defineProps({
  name: {
    type: String,
    required: true
  },
  expanded: {
    type: Boolean,
    required: false,
    default: false
  }
})

// const name = new Date().getTime()

const click = (e:MouseEvent) => {
  e.preventDefault()
  e.stopPropagation()
}
</script>
