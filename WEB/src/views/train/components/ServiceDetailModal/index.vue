<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div v-if="visible" class="modal-overlay" @click.self="closeModal">
        <div class="modal-content">
          <!-- 头部区域 -->
          <div class="modal-header">
            <h3>模型服务详情 - {{ service.model_name }}</h3>
            <button class="close-button" @click="closeModal">×</button>
          </div>

          <!-- 详情内容 -->
          <div class="modal-body">
            <div class="detail-grid">
              <!-- 基本信息 -->
              <div class="detail-section">
                <h4>基本信息</h4>
                <div class="detail-row">
                  <span class="detail-label">服务ID:</span>
                  <span class="detail-value">{{ service.model_id }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">模型名称:</span>
                  <span class="detail-value">{{ service.model_name }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">模型版本:</span>
                  <span class="detail-value">{{ service.model_version }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">存储路径:</span>
                  <span class="detail-value">{{ service.minio_model_path }}</span>
                </div>
              </div>

              <!-- 状态信息 -->
              <div class="detail-section">
                <h4>状态信息</h4>
                <div class="detail-row">
                  <span class="detail-label">当前状态:</span>
                  <span class="status-badge" :class="service.status">
                    {{ formatStatus(service.status) }}
                  </span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">创建时间:</span>
                  <span class="detail-value">{{ service.created_at }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">更新时间:</span>
                  <span class="detail-value">{{ service.updated_at }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">运行时长:</span>
                  <span class="detail-value">{{ service.uptime }}</span>
                </div>
              </div>

              <!-- 资源使用 -->
              <div class="detail-section">
                <h4>资源使用</h4>
                <div class="resource-metrics">
                  <div class="metric">
                    <div class="metric-label">CPU使用率</div>
                    <div class="progress-bar">
                      <div
                        class="progress-fill"
                        :style="{ width: service.cpu_usage + '%' }"
                      ></div>
                      <span class="progress-text">{{ service.cpu_usage }}%</span>
                    </div>
                  </div>
                  <div class="metric">
                    <div class="metric-label">内存使用</div>
                    <div class="progress-bar">
                      <div
                        class="progress-fill"
                        :style="{ width: service.memory_usage + '%' }"
                      ></div>
                      <span class="progress-text">{{ service.memory_usage }}%</span>
                    </div>
                  </div>
                  <div class="metric">
                    <div class="metric-label">GPU使用率</div>
                    <div class="progress-bar">
                      <div
                        class="progress-fill"
                        :style="{ width: service.gpu_usage + '%' }"
                      ></div>
                      <span class="progress-text">{{ service.gpu_usage }}%</span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 服务端点 -->
              <div class="detail-section">
                <h4>服务端点</h4>
                <div class="endpoint-group">
                  <div class="endpoint">
                    <span class="endpoint-label">REST API:</span>
                    <div class="endpoint-value">
                      <code>{{ service.rest_endpoint }}</code>
                      <button
                        class="copy-btn"
                        @click="copyToClipboard(service.rest_endpoint)"
                      >
                        <i class="icon-copy"></i>
                      </button>
                    </div>
                  </div>
                  <div class="endpoint">
                    <span class="endpoint-label">gRPC端点:</span>
                    <div class="endpoint-value">
                      <code>{{ service.grpc_endpoint }}</code>
                      <button
                        class="copy-btn"
                        @click="copyToClipboard(service.grpc_endpoint)"
                      >
                        <i class="icon-copy"></i>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="modal-footer">
              <button
                v-if="service.status === 'running'"
                class="btn-action btn-stop"
                @click="stopService"
              >
                <i class="icon-stop"></i> 停止服务
              </button>
              <button
                v-else
                class="btn-action btn-start"
                @click="startService"
              >
                <i class="icon-play"></i> 启动服务
              </button>
              <button
                class="btn-action btn-delete"
                @click="deleteService"
              >
                <i class="icon-delete"></i> 删除服务
              </button>
              <button
                class="btn-action"
                @click="viewLogs"
              >
                <i class="icon-logs"></i> 查看日志
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  visible: Boolean,
  service: {
    type: Object,
    default: () => ({
      model_id: '',
      model_name: '',
      model_version: '',
      minio_model_path: '',
      status: 'stopped',
      created_at: '',
      updated_at: '',
      uptime: '',
      cpu_usage: 0,
      memory_usage: 0,
      gpu_usage: 0,
      rest_endpoint: '',
      grpc_endpoint: ''
    })
  }
})

const emit = defineEmits(['close', 'stop', 'start', 'delete', 'view-logs'])

// 格式化状态显示
const formatStatus = (status) => {
  const statusMap = {
    running: '运行中',
    stopped: '已停止',
    deploying: '部署中',
    error: '错误'
  }
  return statusMap[status] || status
}

// 复制到剪贴板
const copyToClipboard = (text) => {
  navigator.clipboard.writeText(text)
    .then(() => {
      console.log('已复制到剪贴板:', text)
      // 实际项目中可添加成功提示
    })
    .catch(err => {
      console.error('复制失败:', err)
    })
}

// 关闭模态框
const closeModal = () => {
  emit('close')
}

// 停止服务
const stopService = () => {
  emit('stop', props.service.model_id)
}

// 启动服务
const startService = () => {
  emit('start', props.service.model_id)
}

// 删除服务
const deleteService = () => {
  if (confirm(`确定要删除服务 ${props.service.model_name} 吗？`)) {
    emit('delete', props.service.model_id)
    closeModal()
  }
}

// 查看日志
const viewLogs = () => {
  emit('view-logs', props.service.model_id)
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  width: 800px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.modal-header {
  padding: 16px 24px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-body {
  padding: 20px;
}

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.detail-section {
  margin-bottom: 25px;
}

.detail-section h4 {
  border-bottom: 1px solid #eee;
  padding-bottom: 10px;
  margin-bottom: 15px;
}

.detail-row {
  display: flex;
  margin-bottom: 12px;
}

.detail-label {
  width: 120px;
  font-weight: 500;
  color: #666;
}

.detail-value {
  flex: 1;
}

.status-badge {
  padding: 3px 8px;
  border-radius: 12px;
  font-size: 0.85em;
}

.status-badge.running {
  background-color: #e6f4ff;
  color: #1890ff;
}

.status-badge.stopped {
  background-color: #fff2f0;
  color: #ff4d4f;
}

.status-badge.deploying {
  background-color: #fffbe6;
  color: #faad14;
}

.status-badge.error {
  background-color: #fff2f0;
  color: #ff4d4f;
}

.resource-metrics {
  display: grid;
  gap: 15px;
}

.metric {
  margin-bottom: 15px;
}

.metric-label {
  margin-bottom: 5px;
  font-size: 0.9em;
}

.progress-bar {
  height: 24px;
  background: #f5f5f5;
  border-radius: 4px;
  position: relative;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #1890ff;
  transition: width 0.3s;
}

.progress-text {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 0.85em;
}

.endpoint-group {
  display: grid;
  gap: 15px;
}

.endpoint {
  display: flex;
}

.endpoint-label {
  width: 90px;
  font-weight: 500;
  color: #666;
}

.endpoint-value {
  flex: 1;
  display: flex;
  align-items: center;
}

.endpoint-value code {
  flex: 1;
  padding: 5px 10px;
  background: #f5f7fa;
  border-radius: 4px;
  font-size: 0.9em;
  overflow: hidden;
  text-overflow: ellipsis;
}

.copy-btn {
  margin-left: 10px;
  padding: 5px 10px;
  background: none;
  border: none;
  cursor: pointer;
  color: #1890ff;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding-top: 20px;
  border-top: 1px solid #eee;
  margin-top: 20px;
}

.btn-action {
  padding: 8px 16px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
}

.btn-action:hover {
  background: #f5f5f5;
}

.btn-start {
  color: #52c41a;
  border-color: #52c41a;
}

.btn-stop {
  color: #ff4d4f;
  border-color: #ff4d4f;
}

.btn-delete {
  color: #ff4d4f;
  border-color: #ff4d4f;
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
