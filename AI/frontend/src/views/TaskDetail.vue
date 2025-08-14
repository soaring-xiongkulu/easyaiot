<template>
  <div class="task-detail">
    <div v-if="loading" class="loading">加载任务详情中...</div>
    <div v-else-if="task">
      <h1>{{ task.name }}</h1>
      <div class="task-info">
        <p><strong>描述:</strong> {{ task.description }}</p>
        <p><strong>模型:</strong> {{ task.modelName }} (v{{ task.modelVersion }})</p>
        <p><strong>状态:</strong> 
          <span class="status" :class="task.status">{{ task.status }}</span>
        </p>
        <p><strong>创建时间:</strong> {{ formatDate(task.createdTime) }}</p>
        <p><strong>更新时间:</strong> {{ formatDate(task.updatedTime) }}</p>
      </div>
      
      <div class="task-data">
        <div class="data-section">
          <h3>输入数据</h3>
          <pre>{{ task.inputData }}</pre>
        </div>
        
        <div v-if="task.outputData" class="data-section">
          <h3>输出数据</h3>
          <pre>{{ task.outputData }}</pre>
        </div>
      </div>
      
      <div class="task-actions">
        <button v-if="task.status === 'pending'" @click="startTask" class="start-btn">开始任务</button>
        <button @click="refreshTask" class="refresh-btn">刷新</button>
        <button @click="goBack" class="back-btn">返回任务列表</button>
      </div>
    </div>
    <div v-else class="error">
      未找到任务
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'TaskDetail',
  props: ['id'],
  data() {
    return {
      task: null,
      loading: true
    }
  },
  async mounted() {
    await this.fetchTask()
  },
  methods: {
    async fetchTask() {
      try {
        const response = await axios.get(`/tasks/${this.id}`)
        this.task = response.data
      } catch (error) {
        console.error('获取任务时出错:', error)
      } finally {
        this.loading = false
      }
    },
    async startTask() {
      try {
        await axios.post(`/tasks/${this.id}/start`)
        await this.fetchTask()
      } catch (error) {
        console.error('启动任务时出错:', error)
        alert('启动任务失败')
      }
    },
    async refreshTask() {
      this.loading = true
      await this.fetchTask()
    },
    goBack() {
      this.$router.push('/tasks')
    },
    formatDate(timestamp) {
      if (!timestamp) return 'N/A'
      return new Date(timestamp).toLocaleString()
    }
  }
}
</script>

<style scoped>
.task-detail {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.loading, .error {
  text-align: center;
  padding: 40px;
  font-size: 18px;
}

.task-info {
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

.task-info p {
  margin: 10px 0;
}

.status {
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 0.9em;
  font-weight: bold;
}

.status.pending {
  background-color: #ffc107;
  color: #212529;
}

.status.running {
  background-color: #17a2b8;
  color: white;
}

.status.completed {
  background-color: #28a745;
  color: white;
}

.status.failed {
  background-color: #dc3545;
  color: white;
}

.task-data {
  margin: 20px 0;
}

.data-section {
  margin-bottom: 30px;
}

.data-section h3 {
  border-bottom: 1px solid #ddd;
  padding-bottom: 5px;
  margin-bottom: 10px;
}

pre {
  background-color: #f1f1f1;
  padding: 15px;
  border-radius: 4px;
  overflow-x: auto;
  white-space: pre-wrap;
}

.task-actions {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.task-actions button {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
}

.start-btn {
  background-color: #28a745;
  color: white;
}

.refresh-btn {
  background-color: #17a2b8;
  color: white;
}

.back-btn {
  background-color: #6c757d;
  color: white;
}
</style>