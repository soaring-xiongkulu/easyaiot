<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div v-if="visible" class="modal-overlay" @click.self="closeModal">
        <div class="modal-content">
          <!-- 头部区域 -->
          <div class="modal-header">
            <h3>{{ taskName }} - 训练日志</h3>
            <button class="close-button" @click="closeModal">×</button>
          </div>

          <!-- 控制栏：筛选和搜索 -->
          <div class="control-bar">
            <div class="filter-group">
              <label>日志级别：</label>
              <select v-model="filters.level">
                <option value="all">全部</option>
                <option value="info">信息</option>
                <option value="warning">警告</option>
                <option value="error">错误</option>
              </select>
            </div>

            <div class="search-group">
              <input
                type="text"
                v-model="filters.keyword"
                placeholder="搜索日志关键词..."
                @input="debouncedFilter"
              />
              <button @click="exportLogs">导出日志</button>
            </div>
          </div>

          <!-- 日志展示区 -->
          <div class="log-container">
            <!-- 指标可视化 -->
            <div class="metrics-visualization" v-if="metricsData.length">
              <div class="chart-container">
                <LineChart :data="metricsData" title="训练指标变化" />
              </div>
            </div>

            <!-- 日志列表 -->
            <div class="log-list" ref="logContainer">
              <div
                v-for="(log, index) in filteredLogs"
                :key="index"
                class="log-item"
                :class="log.level"
              >
                <span class="timestamp">{{ log.timestamp }}</span>
                <span class="level-tag" :class="log.level">{{ log.level.toUpperCase() }}</span>
                <span class="message">{{ log.message }}</span>

                <!-- 指标数据展示 -->
                <div v-if="log.metrics" class="metrics">
                  <span v-for="(value, key) in log.metrics" :key="key">
                    {{ key }}: <strong>{{ value }}</strong>
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, reactive, watch, onMounted } from 'vue'
import LineChart from '../LineChart/index.vue' // 可视化图表组件
import { debounce } from 'lodash-es'

const props = defineProps({
  visible: Boolean,
  taskId: String,
  taskName: String
})

const emit = defineEmits(['close'])

// 日志数据
const logs = ref([])
// 筛选条件
const filters = reactive({
  level: 'all',
  keyword: ''
})
// 指标数据（用于可视化）
const metricsData = ref([])

// 筛选后的日志
const filteredLogs = computed(() => {
  return logs.value.filter(log => {
    // 日志级别筛选
    const levelMatch = filters.level === 'all' || log.level === filters.level
    // 关键词筛选
    const keywordMatch = !filters.keyword ||
      log.message.toLowerCase().includes(filters.keyword.toLowerCase()) ||
      (log.metrics && Object.keys(log.metrics).some(key =>
          key.toLowerCase().includes(filters.keyword.toLowerCase()))
      )
    return levelMatch && keywordMatch
  })
})

// 防抖搜索
const debouncedFilter = debounce(() => {}, 300)

// 关闭模态框
const closeModal = () => {
  emit('close')
}

// 导出日志
const exportLogs = () => {
  const content = logs.value.map(log =>
    `${log.timestamp} [${log.level.toUpperCase()}] ${log.message}` +
    (log.metrics ? ` | METRICS: ${JSON.stringify(log.metrics)}` : '')
  ).join('\n')

  const blob = new Blob([content], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)

  const a = document.createElement('a')
  a.href = url
  a.download = `${props.taskName}_logs_${new Date().toISOString().slice(0, 10)}.txt`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

// 加载日志数据
const loadLogs = async () => {
  try {
    // 模拟API请求：实际项目中替换为真实API调用
    const response = await fetch(`/api/training/logs/${props.taskId}`)
    const data = await response.json()

    logs.value = data.logs.map(log => ({
      ...log,
      timestamp: new Date(log.timestamp).toLocaleTimeString()
    }))

    // 提取指标数据用于可视化
    metricsData.value = extractMetrics(data.logs)
  } catch (error) {
    console.error('加载日志失败:', error)
    logs.value = [{
      timestamp: new Date().toLocaleTimeString(),
      level: 'error',
      message: '加载日志失败: ' + error.message
    }]
  }
}

// 从日志中提取指标数据
const extractMetrics = (logs) => {
  const metrics = []

  logs.forEach(log => {
    if (log.metrics) {
      metrics.push({
        timestamp: log.timestamp,
        ...log.metrics
      })
    }
  })

  return metrics
}

// 监听taskId变化
watch(() => props.taskId, (newId) => {
  if (newId) loadLogs()
})

// 监听可见状态
watch(() => props.visible, (visible) => {
  if (visible && props.taskId) {
    loadLogs()
  }
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  width: 800px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.modal-header {
  padding: 16px 24px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.control-bar {
  padding: 12px 24px;
  display: flex;
  justify-content: space-between;
  background: #f8f9fa;
  border-bottom: 1px solid #eee;
}

.filter-group, .search-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.search-group input {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  width: 250px;
}

.log-container {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
}

.metrics-visualization {
  padding: 16px;
  border-bottom: 1px solid #eee;
  height: 250px;
}

.chart-container {
  height: 100%;
}

.log-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  max-height: 50vh;
}

.log-item {
  padding: 12px;
  border-bottom: 1px solid #f0f0f0;
  font-family: monospace;
  font-size: 14px;
}

.log-item.error {
  background-color: #fff0f0;
}

.log-item.warning {
  background-color: #fff9e6;
}

.log-item.info {
  background-color: #f0f8ff;
}

.timestamp {
  color: #666;
  margin-right: 15px;
}

.level-tag {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.8em;
  margin-right: 10px;
}

.level-tag.info {
  background-color: #e6f4ff;
  color: #1890ff;
}

.level-tag.warning {
  background-color: #fff7e6;
  color: #fa8c16;
}

.level-tag.error {
  background-color: #fff1f0;
  color: #f5222d;
}

.metrics {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed #eee;
  color: #666;
  display: flex;
  gap: 15px;
}

.close-button {
  background: none;
  border: none;
  font-size: 1.5em;
  cursor: pointer;
  color: #999;
}

/* 过渡动画 */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.3s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
</style>
