<template>
  <BasicModal
    @register="registerModal"
    :title="`${state.taskName} - 训练日志`"
    :width="900"
    :canFullscreen="true"
    :showCancelBtn="false"
    :showOkBtn="false"
    @cancel="closeModal"
  >
    <div class="modal-content">
      <div class="control-bar">
        <div class="filter-group">
          <label class="filter-label">日志级别：</label>
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
        <div class="metrics-visualization" v-if="metricsData.length">
          <div class="chart-container">
            <LineChart :data="metricsData" theme="dark" title="训练指标变化"/>
          </div>
        </div>

        <!-- 日志列表 -->
        <div class="log-list" ref="logContainer">
          <pre class="message">{{ logs }}</pre>
          <div v-if="logs.length === 0" class="empty-state">
            <i class="el-icon-document text-4xl text-blue-200 mb-2"></i>
            <p>暂无日志数据</p>
          </div>
        </div>
      </div>
    </div>
  </BasicModal>
</template>

<script setup lang="ts">
import {computed, onMounted, reactive, ref, watch} from 'vue'
import {BasicModal, useModalInner} from '@/components/Modal'
import LineChart from '../LineChart/index.vue'
import {debounce} from 'lodash-es'
import {getTrainingDetail} from '@/api/device/model'

const state = reactive({
  taskId: '',
  taskName: ''
});

const emit = defineEmits(['close'])

// 使用useModalInner注册模态框
const [registerModal, {closeModal}] = useModalInner((data) => {
  const {record} = data;
  state.taskId = record.id;
  state.taskName = record.model_name;
  if (record.id) {
    loadLogs()
  }
})

// 日志数据
const logs = ref<Array<any>>([])
// 筛选条件
const filters = reactive({
  level: 'all',
  keyword: ''
})
// 指标数据（用于可视化）
const metricsData = ref<Array<any>>([])
const logContainer = ref<HTMLElement | null>(null)

// 筛选后的日志
const filteredLogs = computed(() => {
  return logs.value.filter(log => {
    const levelMatch = filters.level === 'all' || log.level === filters.level
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
  // 实际过滤由computed属性处理
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
  a.download = `${state.taskName}_logs_${new Date().toISOString().slice(0, 10)}.txt`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

// 加载日志数据
const loadLogs = async () => {
  try {
    if (!state.taskId) return

    // 实际API调用 - 确保路径匹配后端接口
    const data = await getTrainingDetail(state.taskId)

    console.log('日志数据:', JSON.stringify(data['train_log']))

    // 处理实际API返回的数据
    logs.value = data['train_log']

    // 滚动到底部
    scrollToBottom()
  } catch (error: any) {
    console.error('加载日志失败:', error)
    logs.value = [{
      timestamp: new Date().toLocaleTimeString(),
      level: 'error',
      message: '加载日志失败: ' + error.message
    }]
  }
}

// 滚动到底部
const scrollToBottom = () => {
  if (logContainer.value) {
    setTimeout(() => {
      logContainer.value!.scrollTop = logContainer.value!.scrollHeight
    }, 100)
  }
}

// 监听taskId变化
watch(() => state.taskId, (newId) => {
  if (newId) loadLogs()
})

onMounted(() => {
  if (state.taskId) {
    loadLogs()
  }
})
</script>

<style scoped>
/* 基础布局 */
.modal-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: #121212; /* 深空黑背景 */
  color: #e0e0e0; /* 浅灰文字 */
  font-family: 'Consolas', 'Monaco', monospace; /* 等宽字体 */
}

/* 控制栏样式 */
.control-bar {
  padding: 16px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #1e1e1e; /* 深灰背景 */
  border-bottom: 1px solid #333;
  flex-wrap: wrap;
  gap: 16px;
}

.filter-group, .search-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.filter-label {
  font-weight: 500;
  color: #a0a0a0;
}

.filter-select, .search-input {
  padding: 8px 12px;
  border: 1px solid #444;
  border-radius: 4px;
  background: #2d2d2d;
  color: #f0f0f0;
  outline: none;
}

.search-input {
  width: 250px;
}

.search-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3);
}

.export-button {
  background: #1e3a8a;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.export-button:hover {
  background: #3b82f6;
}

/* 日志容器 */
.log-container {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
}

.metrics-visualization {
  padding: 16px;
  border-bottom: 1px solid #333;
  height: 250px;
  background: #1a1a1a;
}

.chart-container {
  height: 100%;
  background: #0a0a0a;
  border-radius: 4px;
  overflow: hidden;
}

/* 日志列表 */
.log-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: #0a0a0a;
}

.log-list::-webkit-scrollbar {
  width: 8px;
  background: #1a1a1a;
}
.log-list::-webkit-scrollbar-thumb {
  background: #3b82f6;
  border-radius: 4px;
}

.log-item {
  padding: 12px 16px;
  margin-bottom: 8px;
  border-radius: 4px;
  background: #1a1a1a;
  border-left: 3px solid transparent;
  transition: all 0.2s;
}

.log-item:hover {
  background: #252525;
}

.log-item.info {
  border-left-color: #3b82f6; /* 信息蓝 */
}

.log-item.warning {
  border-left-color: #f59e0b; /* 警告黄 */
}

.log-item.error {
  border-left-color: #ef4444; /* 错误红 */
}

.timestamp {
  color: #9ca3af;
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
  background-color: rgba(59, 130, 246, 0.2);
  color: #93c5fd;
}

.level-tag.warning {
  background-color: rgba(245, 158, 11, 0.2);
  color: #fcd34d;
}

.level-tag.error {
  background-color: rgba(239, 68, 68, 0.2);
  color: #fca5a5;
}

.message {
  margin: 8px 0;
  white-space: pre-wrap;
  word-break: break-all;
  color: #d4d4d4;
  line-height: 1.5;
}

.metrics {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed #333;
  color: #9ca3af;
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
  font-size: 12px;
}

.metrics strong {
  color: #d4d4d4;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #6b7280;
  text-align: center;
}

/* 响应式调整 */
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
