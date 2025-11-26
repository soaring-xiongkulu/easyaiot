<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div v-if="visible" class="modal-overlay" @click.self="closeModal">
        <div class="modal-content">
          <!-- 头部区域 -->
          <div class="modal-header">
            <h3>{{ modelId ? '更新模型部署' : '部署新模型服务' }}</h3>
            <button class="close-button" @click="closeModal">×</button>
          </div>

          <!-- 表单区域 -->
          <div class="modal-body">
            <form @submit.prevent="submitForm">
              <!-- 模型ID -->
              <div class="form-group">
                <label>模型ID *</label>
                <input
                  type="text"
                  v-model="form.model_id"
                  required
                  :disabled="!!modelId"
                  placeholder="输入模型唯一标识"
                />
              </div>

              <!-- 模型名称 -->
              <div class="form-group">
                <label>模型名称 *</label>
                <input
                  type="text"
                  v-model="form.model_name"
                  required
                  placeholder="输入可识别的模型名称"
                />
              </div>

              <!-- 模型版本 -->
              <div class="form-group">
                <label>模型版本 *</label>
                <input
                  type="text"
                  v-model="form.model_version"
                  required
                  placeholder="格式如：v1.0.0"
                />
              </div>

              <!-- 模型路径 -->
              <div class="form-group">
                <label>MinIO模型路径 *</label>
                <div class="path-selector">
                  <input
                    type="text"
                    v-model="form.minio_model_path"
                    required
                    placeholder="minio://bucket/model-path"
                  />
                  <button type="button" @click="browseMinIO">
                    <i class="icon-folder"></i> 浏览
                  </button>
                </div>
              </div>

              <!-- 资源配置 -->
              <div class="form-group">
                <label>资源配置</label>
                <div class="resource-grid">
                  <div>
                    <label>GPU数量</label>
                    <input
                      type="number"
                      v-model="form.gpu_count"
                      min="1"
                      max="8"
                      placeholder="1-8"
                    />
                  </div>
                  <div>
                    <label>内存(GB)</label>
                    <input
                      type="number"
                      v-model="form.memory"
                      min="1"
                      max="64"
                      placeholder="1-64"
                    />
                  </div>
                </div>
              </div>

              <!-- 高级设置 -->
              <div class="advanced-section">
                <h4 @click="showAdvanced = !showAdvanced">
                  <i :class="['icon-arrow', { rotated: showAdvanced }]"></i>
                  高级设置
                </h4>
                <div v-if="showAdvanced" class="advanced-options">
                  <div class="form-group">
                    <label>推理超时(秒)</label>
                    <input
                      type="number"
                      v-model="form.timeout"
                      min="10"
                      max="300"
                      placeholder="10-300"
                    />
                  </div>
                  <div class="form-group">
                    <label>自动扩缩容</label>
                    <label class="switch">
                      <input type="checkbox" v-model="form.auto_scale">
                      <span class="slider"></span>
                    </label>
                  </div>
                </div>
              </div>

              <!-- 操作按钮 -->
              <div class="modal-footer">
                <button type="button" class="btn-cancel" @click="closeModal">取消</button>
                <button type="submit" class="btn-confirm">
                  {{ modelId ? '更新部署' : '立即部署' }}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'

const props = defineProps({
  visible: Boolean,
  modelId: String,
  initialData: Object
})

const emit = defineEmits(['close', 'submit'])

// 表单数据
const form = reactive({
  model_id: '',
  model_name: '',
  model_version: 'v1.0.0',
  minio_model_path: '',
  gpu_count: 1,
  memory: 4,
  timeout: 30,
  auto_scale: false
})

const showAdvanced = ref(false)

// 当传入初始数据时填充表单
watch(() => props.initialData, (data) => {
  if (data) {
    Object.keys(form).forEach(key => {
      if (data[key] !== undefined) {
        form[key] = data[key]
      }
    })
  }
}, { immediate: true })

// 浏览MinIO存储
const browseMinIO = () => {
  console.log('打开MinIO浏览器')
  // 实际项目中接入MinIO文件选择API
  form.minio_model_path = 'minio://models/yolov8s-best.pt'
}

// 提交表单
const submitForm = () => {
  emit('submit', { ...form })
  closeModal()
}

// 关闭模态框
const closeModal = () => {
  emit('close')
  // 重置表单
  Object.keys(form).forEach(key => {
    form[key] = props.initialData?.[key] ||
      (key === 'model_version' ? 'v1.0.0' :
        key === 'gpu_count' ? 1 :
          key === 'memory' ? 4 :
            key === 'timeout' ? 30 :
              key === 'auto_scale' ? false : '')
  })
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
  width: 600px;
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

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
}

.form-group input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.path-selector {
  display: flex;
  gap: 10px;
}

.path-selector input {
  flex: 1;
}

.path-selector button {
  padding: 10px 15px;
  background: #f5f7fa;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  cursor: pointer;
}

.resource-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}

.advanced-section {
  margin: 25px 0;
  padding-top: 15px;
  border-top: 1px solid #eee;
}

.advanced-section h4 {
  display: flex;
  align-items: center;
  cursor: pointer;
  margin-bottom: 15px;
}

.icon-arrow {
  display: inline-block;
  margin-right: 8px;
  transition: transform 0.3s;
}

.icon-arrow.rotated {
  transform: rotate(90deg);
}

.advanced-options {
  padding: 15px;
  background: #f9f9f9;
  border-radius: 4px;
}

.switch {
  position: relative;
  display: inline-block;
  width: 50px;
  height: 24px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: .4s;
  border-radius: 24px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 16px;
  width: 16px;
  left: 4px;
  bottom: 4px;
  background-color: white;
  transition: .4s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: #2196F3;
}

input:checked + .slider:before {
  transform: translateX(26px);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding-top: 20px;
}

.btn-cancel, .btn-confirm {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
}

.btn-cancel {
  background: #f0f0f0;
  color: #333;
}

.btn-confirm {
  background: #007bff;
  color: white;
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
