<template>
  <div class="page topo-page">
    <div class="page-head">
      <div>
        <h1>部署拓扑</h1>
        <p>服务依赖与运行状态；默认隐藏未部署节点</p>
      </div>
      <div class="toolbar" style="margin: 0">
        <a-checkbox v-model:checked="showMissing">显示未部署</a-checkbox>
        <a-checkbox v-model:checked="showOther">显示其他容器</a-checkbox>
        <a-button size="small" type="primary" :loading="loading" @click="reload">刷新</a-button>
      </div>
    </div>

    <div class="panel topo-wrap">
      <div class="panel-hd">
        <div class="sum">
          <span>节点 <b>{{ visibleSummary.total }}</b></span>
          <span class="ok">运行 <b>{{ visibleSummary.running }}</b></span>
          <span>停止 <b>{{ visibleSummary.stopped }}</b></span>
          <span v-if="showMissing">未部署 <b>{{ visibleSummary.missing }}</b></span>
        </div>
        <div class="legend">
          <span v-for="g in legend" :key="g.key"><i :style="{ background: g.color }" />{{ g.label }}</span>
        </div>
      </div>
      <div ref="chartRef" class="chart" />
      <div class="panel-bd tip muted">连线表示调用/依赖；流量来自 docker stats。可拖拽、滚轮缩放。</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { getTopology, type TopologyEdge, type TopologyNode } from '../api'

const chartRef = ref<HTMLDivElement | null>(null)
const loading = ref(false)
const showMissing = ref(false)
const showOther = ref(false)
const rawNodes = ref<TopologyNode[]>([])
const rawEdges = ref<TopologyEdge[]>([])
let chart: echarts.ECharts | null = null
let timer: number | undefined

const legend = [
  { key: 'middleware', label: '中间件', color: '#13c2c2' },
  { key: 'platform', label: '平台', color: '#1677ff' },
  { key: 'business', label: '业务', color: '#722ed1' },
  { key: 'ui', label: '前端', color: '#fa8c16' },
  { key: 'edge', label: '运维', color: '#2f54eb' },
]
const colors: Record<string, string> = Object.fromEntries(legend.map((l) => [l.key, l.color]))
colors.other = '#8c8c8c'

const visibleNodes = computed(() =>
  rawNodes.value.filter((n) => {
    if (!showMissing.value && n.state === 'missing') return false
    if (!showOther.value && n.group === 'other') return false
    return true
  }),
)
const visibleIds = computed(() => new Set(visibleNodes.value.map((n) => n.id)))
const visibleEdges = computed(() =>
  rawEdges.value.filter((e) => visibleIds.value.has(e.source) && visibleIds.value.has(e.target)),
)
const visibleSummary = computed(() => {
  const nodes = visibleNodes.value
  return {
    total: nodes.length,
    running: nodes.filter((n) => n.state === 'running').length,
    stopped: nodes.filter((n) => n.state !== 'running' && n.state !== 'missing').length,
    missing: nodes.filter((n) => n.state === 'missing').length,
  }
})

function layout(nodes: TopologyNode[]) {
  const order = ['middleware', 'platform', 'business', 'ui', 'edge', 'other']
  const by: Record<string, TopologyNode[]> = {}
  for (const n of nodes) (by[n.group || 'other'] ||= []).push(n)
  const pos: Record<string, { x: number; y: number }> = {}
  const width = 1100
  let row = 0
  order.forEach((g) => {
    const list = by[g] || []
    if (!list.length) return
    const y = 80 + row * 110
    list.forEach((n, i) => {
      pos[n.id] = {
        x: list.length === 1 ? width / 2 : 70 + (i * (width - 140)) / Math.max(list.length - 1, 1),
        y,
      }
    })
    row += 1
  })
  return pos
}

function render() {
  if (!chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value)
  const nodes = visibleNodes.value
  const edges = visibleEdges.value
  const positions = layout(nodes)

  chart.setOption(
    {
      backgroundColor: '#ffffff',
      tooltip: {
        backgroundColor: 'rgba(0,0,0,0.85)',
        borderWidth: 0,
        textStyle: { color: '#fff', fontSize: 12 },
      },
      series: [
        {
          type: 'graph',
          layout: 'none',
          roam: true,
          draggable: true,
          scaleLimit: { min: 0.5, max: 2.2 },
          data: nodes.map((n) => ({
            id: n.id,
            name: n.label,
            x: positions[n.id]?.x,
            y: positions[n.id]?.y,
            symbolSize: n.state === 'running' ? 42 : 34,
            itemStyle: {
              color: colors[n.group] || colors.other,
              borderColor: n.state === 'running' ? '#52c41a' : n.state === 'missing' ? '#d9d9d9' : '#faad14',
              borderWidth: 2,
              opacity: n.state === 'missing' ? 0.4 : 1,
            },
            label: {
              show: true,
              position: 'bottom',
              distance: 8,
              formatter: n.label,
              fontSize: 12,
              color: '#000000e0',
              fontWeight: 500,
            },
            tooltip: {
              formatter: () =>
                [
                  `<b>${n.label}</b>`,
                  `状态：${n.state}`,
                  n.containerName ? `容器：${n.containerName}` : '',
                  `CPU：${(n.cpuPercent || 0).toFixed(1)}%`,
                  `内存：${n.memUsage || '—'}`,
                  n.netIO?.raw ? `网络：${n.netIO.raw}` : '',
                ]
                  .filter(Boolean)
                  .join('<br/>'),
            },
          })),
          links: edges.map((e) => ({
            source: e.source,
            target: e.target,
            label: {
              show: false,
            },
            lineStyle: {
              color: e.active ? '#1677ff' : '#d9d9d9',
              width: e.active ? 1.5 : 1,
              curveness: 0.16,
              opacity: e.active ? 0.7 : 0.35,
            },
          })),
          edgeSymbol: ['none', 'arrow'],
          edgeSymbolSize: 6,
          emphasis: { focus: 'adjacency', lineStyle: { width: 2 } },
        },
      ],
    },
    true,
  )
}

async function reload() {
  loading.value = true
  try {
    const data = await getTopology()
    rawNodes.value = data.nodes || []
    rawEdges.value = data.edges || []
    await nextTick()
    render()
  } catch {
    rawNodes.value = []
    rawEdges.value = []
  } finally {
    loading.value = false
  }
}

watch([showMissing, showOther], async () => {
  await nextTick()
  render()
})

function onResize() {
  chart?.resize()
}

onMounted(() => {
  reload()
  window.addEventListener('resize', onResize)
  timer = window.setInterval(reload, 20000)
})
onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  if (timer) window.clearInterval(timer)
  chart?.dispose()
  chart = null
})
</script>

<style scoped>
.topo-page {
  display: flex;
  flex-direction: column;
}

.topo-wrap {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.sum {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: var(--c-text-3);
}

.sum b {
  color: var(--c-text);
  font-weight: 600;
  margin-left: 4px;
}

.sum .ok b {
  color: var(--c-success);
}

.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 12px;
  color: var(--c-text-3);
}

.legend i {
  width: 8px;
  height: 8px;
  border-radius: 2px;
  display: inline-block;
  margin-right: 6px;
}

.chart {
  height: calc(100vh - 260px);
  min-height: 480px;
  background: var(--c-white);
}

.tip {
  border-top: 1px solid var(--c-border);
}
</style>
