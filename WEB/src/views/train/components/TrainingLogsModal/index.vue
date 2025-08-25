<template>
  <BasicModal
    @register="registerModal"
    :title="`${taskName} - 训练日志`"
    :width="900"
    :canFullscreen="true"
    :showCancelBtn="false"
    :showOkBtn="false"
    @cancel="closeModal"
  >
    <div class="modal-content">
      <div class="control-bar">
        <div class="filter-group">
          <label>日志级别：</label>
          <select v-model="filters.level" class="filter-select">
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
            class="search-input"
            @input="debouncedFilter"
          />
          <button @click="exportLogs" class="export-button">导出日志</button>
        </div>
      </div>

      <!-- 日志展示区 -->
      <div class="log-container">
        <!-- 指标可视化 -->
        <div class="metrics-visualization" v-if="metricsData.length">
          <div class="chart-container">
            <LineChart :data="metricsData" title="训练指标变化"/>
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

          <div v-if="filteredLogs.length === 0" class="empty-state">
            <i class="el-icon-document text-4xl text-blue-200 mb-2"></i>
            <p>暂无日志数据</p>
          </div>
        </div>
      </div>
    </div>
  </BasicModal>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { BasicModal, useModalInner } from '@/components/Modal'
import LineChart from '../LineChart/index.vue'
import { debounce } from 'lodash-es'

const props = defineProps({
  taskId: String,
  taskName: String
})

const emit = defineEmits(['close'])

// 使用useModalInner注册模态框
const [registerModal, { closeModal }] = useModalInner((data) => {
  // 当模态框打开时加载日志
  if (props.taskId) {
    loadLogs()
  }
})

// 日志数据
const logs = ref([])
// 筛选条件
const filters = reactive({
  level: 'all',
  keyword: ''
})
// 指标数据（用于可视化）
const metricsData = ref([])
const logContainer = ref(null)

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
const debouncedFilter = debounce(() => {
}, 300)

// 导出日志
const exportLogs = () => {
  const content = logs.value.map(log =>
    `${log.timestamp} [${log.level.toUpperCase()}] ${log.message}` +
    (log.metrics ? ` | METRICS: ${JSON.stringify(log.metrics)}` : '')
  ).join('\n')

  const blob = new Blob([content], {type: 'text/plain'})
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
    // 这里使用模拟数据
    const mockData = {
      logs: [
        {
          timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
          level: 'info',
          message: '训练任务开始初始化',
          metrics: null
        },
        {
          timestamp: new Date(Date.now() - 1000 * 60 * 4).toISOString(),
          level: 'info',
          message: '加载预训练模型完成',
          metrics: null
        },
        {
          timestamp: new Date(Date.now() - 1000 * 60 * 3).toISOString(),
          level: 'info',
          message: '开始第1轮训练',
          metrics: {epoch: 1, loss: 0.85, accuracy: 0.65}
        },
        {
          timestamp: new Date(Date.now() - 1000 * 60 * 2).toISOString(),
          level: 'info',
          message: '第1轮训练完成',
          metrics: {epoch: 1, loss: 0.72, accuracy: 0.72}
        },
        {
          timestamp: new Date(Date.now() - 1000 * 60 * 1).toISOString(),
          level: 'warning',
          message: '学习率调整: 0.01 -> 0.008',
          metrics: null
        },
        {
          timestamp: new Date().toISOString(),
          level: 'info',
          message: '开始第2轮训练',
          metrics: {epoch: 2, loss: 0.68, accuracy: 0.75}
        }
      ]
    };

    logs.value = mockData.logs.map(log => ({
      ...log,
      timestamp: new Date(log.timestamp).toLocaleTimeString()
    }))

    // 提取指标数据用于可视化
    metricsData.value = extractMetrics(mockData.logs)

    // 滚动到底部
    if (logContainer.value) {
      logContainer.value.scrollTop = logContainer.value.scrollHeight
    }
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
</script>

<style scoped>
.modal-content {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.control-bar {
  padding: 16px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  flex-wrap: wrap;
  gap: 16px;
}

.filter-group, .search-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.filter-group label {
  font-weight: 500;
  color: #374151;
}

.filter-select {
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: white;
  color: #374151;
}

.search-input {
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  width: 250px;
  font-size: 14px;
}

.search-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}

.export-button {
  background: #eff6ff;
  color: #1d4ed8;
  border: 1px solid #bfdbfe;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.export-button:hover {
  background: #dbeafe;
  border-color: #93c5fd;
}

.log-container {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
}

.metrics-visualization {
  padding: 16px 24px;
  border-bottom: 1px solid #e2e8f0;
  height: 250px;
  background: #fafafa;
}

.chart-container {
  height: 100%;
  background: white;
  border-radius: 8px;
  padding: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.log-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px 24px;
  max-height: 40vh;
  background: #fafafa;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: #9ca3af;
  text-align: center;
}

.log-item {
  padding: 12px 16px;
  border-bottom: 1px solid #f0f4f8;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.5;
  border-left: 3px solid transparent;
  background: white;
  margin-bottom: 8px;
  border-radius: 6px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.log-item:last-child {
  border-bottom: none;
}

.log-item.error {
  border-left-color: #ef4444;
  background-color: #fef2f2;
}

.log-item.warning {
  border-left-color: #f59e0b;
  background-color: #fffbeb;
}

.log-item.info {
  border-left-color: #3b82f6;
  background-color: #eff6ff;
}

.timestamp {
  color: #6b7280;
  margin-right: 15px;
  font-size: 12px;
}

.level-tag {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.75em;
  font-weight: 600;
  margin-right: 10px;
}

.level-tag.info {
  background-color: #dbeafe;
  color: #1d4ed8;
}

.level-tag.warning {
  background-color: #fef3c7;
  color: #d97706;
}

.level-tag.error {
  background-color: #fee2e2;
  color: #dc2626;
}

.metrics {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed #e5e7eb;
  color: #6b7280;
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
  font-size: 12px;
}

.metrics strong {
  color: #374151;
}

@media (max-width: 968px) {
  .modal-content {
    width: 95%;
    margin: 20px auto;
    max-height: 90vh;
  }

  .control-bar {
    flex-direction: column;
    align-items: flex-start;
  }

  .search-group {
    width: 100%;
  }

  .search-input {
    width: 100%;
  }

  .metrics-visualization {
    height: 200px;
  }
}

@media (max-width: 640px) {
  .control-bar {
    padding: 12px 16px;
  }

  .log-list {
    padding: 12px 16px;
  }

  .log-item {
    flex-direction: column;
    align-items: flex-start;
  }

  .timestamp {
    margin-bottom: 4px;
  }

  .metrics {
    flex-direction: column;
    gap: 4px;
  }
}
</style>
