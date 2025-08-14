<template>
  <div class="train-view">
    <h1>模型训练</h1>
    
    <!-- 训练状态 -->
    <div class="card status-section">
      <h2>训练状态</h2>
      <div class="status-info">
        <p><strong>当前状态:</strong> {{ trainStatus }}</p>
        
        <!-- 训练进度条 -->
        <div v-if="trainStatus === 'training'" class="progress-container">
          <label>训练进度:</label>
          <div class="progress-bar">
            <div 
              class="progress-fill" 
              :style="{ width: trainingProgress + '%' }"
            ></div>
          </div>
          <span>{{ trainingProgress }}%</span>
        </div>
      </div>
      
      <div class="status-actions">
        <button 
          @click="startTraining" 
          :disabled="loading || trainStatus === 'training'"
          class="btn btn-primary"
        >
          {{ loading && trainStatus !== 'training' ? '启动中...' : '开始训练' }}Verification failed. Retrying...
        </button>
        <button 
          @click="stopTraining" 
          :disabled="loading || trainStatus === 'training'"
          class="btn btn-danger"
        >
          {{ loading && trainStatus === 'training' ? '停止中...' : '停止训练' }}
        </button>
        <button 
          @click="refreshStatus"
          :disabled="loading"
          class="btn btn-secondary"
        >
          刷新状态
        </button>
      </div>
    </div>

    <!-- 训练配置 -->
    <div class="card config-section">
      <h2>训练配置</h2>
      <form @submit.prevent="saveConfig" class="config-form">
        <div class="form-group">
          <label for="learning_rate">学习率:</label>
          <input 
            id="learning_rate"
            type="number" 
            v-model.number="trainConfig.learning_rate"
            step="0.001"
            :disabled="trainStatus === 'training'"
          />
        </div>
        <div class="form-group">
          <label for="batch_size">批次大小:</label>
          <input 
            id="batch_size"
            type="number" 
            v-model.number="trainConfig.batch_size"
            :disabled="trainStatus === 'training'"
          />
        </div>
        <div class="form-group">
          <label for="epochs">训练轮数:</label>
          <input 
            id="epochs"
            type="number" 
            v-model.number="trainConfig.epochs"
            :disabled="trainStatus === 'training'"
          />
        </div>
        <div class="form-group">
          <label for="optimizer">优化器:</label>
          <select 
            id="optimizer"
            v-model="trainConfig.optimizer"
            :disabled="trainStatus === 'training'"
          >
            <option value="adam">Adam</option>
            <option value="sgd">SGD</option>
            <option value="rmsprop">RMSprop</option>
          </select>
        </div>
        <button 
          type="submit" 
          :disabled="loading || trainStatus === 'training'"
          class="btn btn-primary"
        >
          保存配置
        </button>
      </form>
    </div>

    <!-- 训练结果 -->
    <div class="card result-section">
      <h2>训练结果</h2>
      <button 
        @click="getTrainResult" 
        :disabled="loading"
        class="btn btn-secondary"
      >
        获取训练结果
      </button>
      <div v-if="trainResult" class="result-content">
        <p><strong>准确率:</strong> {{ (trainResult.accuracy * 100).toFixed(2) }}%</p>
        <p><strong>损失值:</strong> {{ trainResult.loss.toFixed(4) }}</p>
        <p><strong>训练时间:</strong> {{ trainResult.training_time }} 秒</p>
      </div>
    </div>

    <!-- 训练日志 -->
    <div class="card logs-section">
      <h2>训练日志</h2>
      <div class="logs-controls">
        <button 
          @click="fetchTrainLogs" 
          :disabled="loading"
          class="btn btn-secondary"
        >
          刷新日志
        </button>
        <button 
          @click="clearLogs" 
          :disabled="trainLogs.length === 0"
          class="btn btn-warning"
        >
          清空日志
        </button>
      </div>
      <div class="logs-content">
        <div v-if="trainLogs.length > 0">
          <div 
            v-for="(log, index) in trainLogs" 
            :key="index" 
            class="log-entry"
          >
            [{{ log.timestamp }}] {{ log.message }}
          </div>
        </div>
        <p v-else class="no-logs">暂无日志信息</p>
      </div>
    </div>
  </div>
</template>

<script>
import {
  getTrainStatus,
  startTrain,
  stopTrain,
  getTrainResult,
  getTrainConfig,
  updateTrainConfig,
  getTrainLogs
} from '../services/api'

export default {
  name: 'TrainView',
  data() {
    return {
      trainStatus: 'idle',
      trainConfig: {
        learning_rate: 0.001,
        batch_size: 32,
        epochs: 10,
        optimizer: 'adam'
      },
      trainResult: null,
      trainLogs: [],
      loading: false,
      logInterval: null,
      trainingProgress: 0
    }
  },
  async mounted() {
    await this.fetchTrainStatus()
    await this.fetchTrainConfig()
  },
  beforeDestroy() {
    if (this.logInterval) {
      clearInterval(this.logInterval)
    }
  },
  methods: {
    async fetchTrainStatus() {
      try {
        this.loading = true
        const status = await getTrainStatus()
        this.trainStatus = status.status
        
        // 如果正在训练，则开始获取日志
        if (status.status === 'training') {
          this.startLogPolling()
        }
      } catch (error) {
        console.error('获取训练状态失败:', error)
        this.$message.error('获取训练状态失败: ' + error.message)
      } finally {
        this.loading = false
      }
    },
    
    async fetchTrainConfig() {
      try {
        this.loading = true
        const config = await getTrainConfig()
        this.trainConfig = config
      } catch (error) {
        console.error('获取训练配置失败:', error)
        this.$message.error('获取训练配置失败: ' + error.message)
      } finally {
        this.loading = false
      }
    },
    
    async fetchTrainLogs() {
      try {
        const logs = await getTrainLogs()
        this.trainLogs = logs
        
        // 模拟训练进度更新
        if (this.trainStatus === 'training') {
          this.trainingProgress = Math.min(this.trainingProgress + 10, 100)
        }
      } catch (error) {
        console.error('获取训练日志失败:', error)
        this.$message.error('获取训练日志失败: ' + error.message)
      }
    },
    
    startLogPolling() {
      if (!this.logInterval) {
        this.logInterval = setInterval(this.fetchTrainLogs, 3000)
      }
    },
    
    stopLogPolling() {
      if (this.logInterval) {
        clearInterval(this.logInterval)
        this.logInterval = null
      }
      this.trainingProgress = 0
    },
    
    async startTraining() {
      this.loading = true
      try {
        await startTrain(this.trainConfig)
        this.trainStatus = 'training'
        this.trainingProgress = 0
        this.startLogPolling()
        this.$message.success('训练已开始')
      } catch (error) {
        console.error('启动训练失败:', error)
        this.$message.error('启动训练失败: ' + error.message)
      } finally {
        this.loading = false
      }
    },
    
    async stopTraining() {
      this.loading = true
      try {
        await stopTrain()
        this.trainStatus = 'stopped'
        this.stopLogPolling()
        this.$message.success('训练已停止')
      } catch (error) {
        console.error('停止训练失败:', error)
        this.$message.error('停止训练失败: ' + error.message)
      } finally {
        this.loading = false
      }
    },
    
    async refreshStatus() {
      await this.fetchTrainStatus()
    },
    
    async saveConfig() {
      this.loading = true
      try {
        await updateTrainConfig(this.trainConfig)
        this.$message.success('配置保存成功')
      } catch (error) {
        console.error('保存配置失败:', error)
        this.$message.error('保存配置失败: ' + error.message)
      } finally {
        this.loading = false
      }
    },
    
    async getTrainResult() {
      this.loading = true
      try {
        const result = await getTrainResult()
        this.trainResult = result
      } catch (error) {
        console.error('获取训练结果失败:', error)
        this.$message.error('获取训练结果失败: ' + error.message)
      } finally {
        this.loading = false
      }
    },
    
    clearLogs() {
      this.trainLogs = []
    }
  }
}
</script>

<style scoped>
.train-view {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.train-view h1 {
  text-align: center;
  margin-bottom: 30px;
}

.card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  padding: 20px;
  margin-bottom: 20px;
}

.card h2 {
  margin-top: 0;
  border-bottom: 1px solid #eee;
  padding-bottom: 10px;
}

.status-info {
  margin-bottom: 20px;
}

.progress-container {
  margin: 15px 0;
}

.progress-container label {
  display: block;
  margin-bottom: 5px;
}

.progress-bar {
  width: 100%;
  height: 20px;
  background-color: #f0f0f0;
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 5px;
}

.progress-fill {
  height: 100%;
  background-color: #42b983;
  transition: width 0.3s ease;
}

.status-actions,
.config-form,
.result-content {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.form-group {
  display: flex;
  flex-direction: column;
  margin-bottom: 15px;
  width: 100%;
}

.form-group label {
  margin-bottom: 5px;
  font-weight: bold;
}

.form-group input,
.form-group select {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.logs-content {
  max-height: 300px;
  overflow-y: auto;
  margin-top: 15px;
  padding: 10px;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.log-entry {
  font-family: monospace;
  font-size: 14px;
  padding: 5px 0;
  border-bottom: 1px solid #eee;
}

.log-entry:last-child {
  border-bottom: none;
}

.no-logs {
  text-align: center;
  color: #999;
  font-style: italic;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.3s;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background-color: #42b983;
  color: white;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.btn-danger {
  background-color: #dc3545;
  color: white;
}

.btn-warning {
  background-color: #ffc107;
  color: #212529;
}

@media (min-width: 768px) {
  .status-actions,
  .config-form,
  .result-content {
    flex-wrap: nowrap;
  }
  
  .form-group {
    width: calc(50% - 10px);
  }
}
</style>