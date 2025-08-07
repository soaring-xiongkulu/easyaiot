<script lang="ts" setup>
import type { Ref } from 'vue'
import { ref, watch } from 'vue'
import { Card } from 'ant-design-vue'
import { useECharts } from '@/hooks/web/useECharts'
import { propTypes } from '@/utils/propTypes'

// 定义组件的 props，接收 loading、width 和 height 属性
const props = defineProps({
  loading: Boolean, // loading: 布尔值，表示是否处于加载状态
  width: propTypes.string.def('100%'), // width: 字符串，默认值为 '100%'
  height: propTypes.string.def('300px'), // height: 字符串，默认值为 '300px'
})

// 创建一个引用，指向 HTMLDivElement 或 null，用于存储图表的 DOM 元素
const chartRef = ref<HTMLDivElement | null>(null)

// 使用 useECharts 钩子，传入 chartRef，设置图表的选项
const { setOptions } = useECharts(chartRef as Ref<HTMLDivElement>)

watch(
  () => props.loading,
  () => {
    if (props.loading)
      return

    setOptions({
      tooltip: {
        trigger: 'item',
      },

      series: [
        {
          name: '访问来源',
          type: 'pie',
          radius: '80%',
          center: ['50%', '50%'],
          color: ['#5ab1ef', '#b6a2de', '#67e0e3', '#2ec7c9'],
          data: [
            { value: 500, name: '电子产品' },
            { value: 310, name: '服装' },
            { value: 274, name: '化妆品' },
            { value: 400, name: '家居' },
          ].sort((a, b) => {
            return a.value - b.value
          }),
          roseType: 'radius',
          animationType: 'scale',
          animationEasing: 'exponentialInOut',
          animationDelay() {
            return Math.random() * 400
          },
        },
      ],
    })
  },
  { immediate: true },
)
</script>

<template>
  <Card title="成交占比" :loading="loading">
    <div ref="chartRef" :style="{ width, height }" />
  </Card>
</template>
