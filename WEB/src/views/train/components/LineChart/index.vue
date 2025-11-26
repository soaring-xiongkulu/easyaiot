<template>
  <div ref="chartDom" class="chart-container"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as echarts from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  DataZoomComponent
} from 'echarts/components'

// 按需注册所需组件 [2,6](@ref)
echarts.use([
  CanvasRenderer,
  LineChart,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  DataZoomComponent
])

const props = defineProps({
  data: {
    type: Array,
    required: true,
    default: () => []
  },
  title: {
    type: String,
    default: '训练指标变化趋势'
  },
  theme: {
    type: String,
    default: 'light'
  }
})

const chartDom = ref(null)
let chartInstance = null

// 初始化图表
const initChart = () => {
  if (!chartDom.value) return

  chartInstance = echarts.init(chartDom.value, props.theme)
  chartInstance.setOption(getChartOptions())

  // 添加窗口大小变化监听
  const resizeHandler = () => chartInstance.resize()
  window.addEventListener('resize', resizeHandler)

  // 返回清理函数
  return () => {
    window.removeEventListener('resize', resizeHandler)
    disposeChart()
  }
}

// 获取图表配置选项
const getChartOptions = () => {
  if (props.data.length === 0) return {}

  // 提取指标名称（排除timestamp字段）
  const metrics = Object.keys(props.data[0]).filter(key => key !== 'timestamp')

  // 准备系列数据
  const series = metrics.map(metric => ({
    name: metric,
    type: 'line',
    smooth: true,
    symbol: 'circle',
    symbolSize: 8,
    data: props.data.map(item => ({
      name: item.timestamp,
      value: item[metric]
    })),
    lineStyle: {
      width: 3,
      shadowColor: 'rgba(0,0,0,0.1)',
      shadowBlur: 10,
      shadowOffsetY: 8
    },
    emphasis: {
      focus: 'series',
      itemStyle: {
        color: '#c23531',
        borderWidth: 2
      }
    }
  }))

  return {
    title: {
      text: props.title,
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255,255,255,0.9)',
      borderWidth: 1,
      borderColor: '#ddd',
      padding: [10, 15],
      textStyle: {
        color: '#333'
      },
      axisPointer: {
        type: 'line',
        lineStyle: {
          color: 'rgba(200,200,200,0.3)',
          width: 2
        }
      },
      formatter: function(params) {
        const date = params[0].name
        let html = `<div style="margin-bottom: 5px; font-weight: bold">${date}</div>`
        params.forEach(param => {
          const color = param.color
          const name = param.seriesName
          const value = param.value
          html += `<div>
            <span style="display:inline-block;margin-right:5px;border-radius:50%;width:10px;height:10px;background-color:${color}"></span>
            ${name}: <span style="font-weight:bold">${value}</span>
          </div>`
        })
        return html
      }
    },
    legend: {
      type: 'scroll',
      bottom: 10,
      data: metrics,
      textStyle: {
        color: '#666'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: props.data.map(item => item.timestamp),
      axisLabel: {
        color: '#666',
        rotate: 30
      },
      axisLine: {
        lineStyle: {
          color: '#eaeaea'
        }
      }
    },
    yAxis: {
      type: 'value',
      name: '指标值',
      nameTextStyle: {
        color: '#666',
        padding: [0, 0, 0, 10]
      },
      axisLabel: {
        color: '#666'
      },
      splitLine: {
        lineStyle: {
          type: 'dashed',
          color: '#f0f0f0'
        }
      }
    },
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100
      },
      {
        type: 'slider',
        show: true,
        start: 0,
        end: 100,
        bottom: 25,
        height: 20,
        backgroundColor: '#f5f5f5',
        fillerColor: 'rgba(24, 144, 255, 0.2)',
        borderColor: '#e8e8e8',
        textStyle: {
          color: '#666'
        }
      }
    ],
    series
  }
}

// 销毁图表
const disposeChart = () => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
}

// 监听数据变化
watch(() => props.data, (newData) => {
  if (chartInstance && newData.length > 0) {
    chartInstance.setOption(getChartOptions())
  }
}, { deep: true })

onMounted(() => {
  const cleanup = initChart()
  // 清理函数
  onBeforeUnmount(() => {
    if (cleanup) cleanup()
    disposeChart()
  })
})
</script>

<style scoped>
.chart-container {
  width: 100%;
  height: 100%;
  min-height: 200px;
}
</style>
